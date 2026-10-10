"""Pure/fake exact cleanup and tiny C backup checks; no UNC/native/WSL effects."""
import ast
import copy
import hashlib
import io
import json
import os
from pathlib import Path
from contextlib import redirect_stdout
from types import SimpleNamespace
import tempfile
from unittest import mock
import unittest
import stage5_unc03_exact_sentinel_cleanup_v2 as C


PAYLOAD = bytes.fromhex(json.loads((C.FAILED/'request.json').read_bytes())['linux_payload_hex'])


class FakeFS:
    def __init__(self):
        self.root = C.BACKING + '\\.unc_visibility_' + C.EXPECTED_NONCE
        self.leaf = self.root + '\\linux.bin'
        self.rows = {self.root: copy.deepcopy(C.EXPECTED_DIRECTORY), self.leaf: copy.deepcopy(C.EXPECTED_LEAF)}
        self.events = []

    def path(self, value):
        return FakePath(self, str(value))

    def listing(self, value):
        return sorted(key[len(self.root)+1:] for key in self.rows
                      if key.startswith(self.root+'\\') and '\\' not in key[len(self.root)+1:])

    def tiny_read(self, path):
        self.events.append('tiny_read')
        self.assert_leaf = str(path) == self.leaf
        if not self.assert_leaf: raise AssertionError('different target')
        return PAYLOAD, {'device': 0, 'inode': 33554461, 'bytes': 116,
            'sha256': hashlib.sha256(PAYLOAD).hexdigest(), 'mtime_ns': C.EXPECTED_LEAF['mtime_ns']}

    def backup(self, *unused):
        self.events.append('durable_backup')
        return {'fsync_and_readback_before_UNC_effects': True}


class FakePath:
    def __init__(self, fs, value): self.fs, self.value = fs, value
    def __truediv__(self, leaf): return FakePath(self.fs, self.value+'\\'+leaf)
    def __str__(self): return self.value
    def lstat(self):
        if self.value not in self.fs.rows:
            error = FileNotFoundError('fixed fake missing'); error.winerror = 2; raise error
        row = self.fs.rows[self.value]
        return SimpleNamespace(st_mode=row['mode'], st_uid=row['uid'], st_gid=row['gid'],
            st_nlink=row['nlink'], st_dev=row['device'], st_ino=row['inode'], st_size=row['bytes'],
            st_mtime_ns=row['mtime_ns'], st_file_attributes=row['file_attributes'], st_reparse_tag=row['reparse_tag'])
    def is_symlink(self): return False
    def unlink(self):
        if self.value != self.fs.leaf: raise AssertionError('not fixed leaf')
        self.fs.events.append('leaf_unlink'); del self.fs.rows[self.value]
        self.fs.rows[self.fs.root]['mtime_ns'] += 1
    def rmdir(self):
        if self.value != self.fs.root or self.fs.listing(self): raise AssertionError('not exact empty directory')
        self.fs.events.append('directory_rmdir'); del self.fs.rows[self.value]


class ExactCleanup(unittest.TestCase):
    def setUp(self):
        self.fs = FakeFS()
        self.original = {'nonce': C.EXPECTED_NONCE, 'sentinel_name': '.unc_visibility_'+C.EXPECTED_NONCE,
                         'linux_payload_hex': PAYLOAD.hex()}

    def run_cleanup(self, progress=None, backup=None, tiny_read=None):
        def default_progress(phase, details): self.fs.events.append(phase)
        return C.exact_cleanup(self.original, tiny_read or self.fs.tiny_read, 'FAKE_C_SPOOL',
            progress or default_progress, lambda *args: None, path_factory=self.fs.path,
            listing=self.fs.listing, backup=backup or self.fs.backup)

    def test_success_only_backup_then_known_leaf_then_empty_directory(self):
        value = self.run_cleanup()
        self.assertEqual(self.fs.rows, {})
        self.assertEqual([x for x in self.fs.events if x in ('durable_backup','leaf_unlink','directory_rmdir')],
                         ['durable_backup','leaf_unlink','directory_rmdir'])
        self.assertIs(value['exact_owned_cleanup'], True)
        self.assertIs(value['probe_success_claimed'], False)

    def test_other_nonce_or_payload_rejected_before_backup(self):
        for change in ({'nonce': '0'*32}, {'sentinel_name': '../other'}, {'linux_payload_hex': (b'X'*116).hex()}):
            with self.subTest(change=change), mock.patch.dict(self.original, change), self.assertRaises(ValueError):
                self.run_cleanup()
        self.assertEqual(self.fs.events, [])

    def test_changed_leaf_metadata_rejects_every_identity_boundary(self):
        for key, value in (('inode', 9), ('nlink', 2), ('bytes', 117), ('mtime_ns', 1),
                           ('file_attributes', 0x400), ('mode', 16895), ('inode', 33554461.0)):
            with self.subTest(key=key), mock.patch.dict(self.fs.rows[self.fs.leaf], {key:value}), self.assertRaises(ValueError):
                self.run_cleanup()
        self.assertNotIn('durable_backup', self.fs.events)

    def test_changed_directory_identity_is_rejected(self):
        for key, value in (('inode', 9), ('nlink', 3), ('mtime_ns', 1), ('file_attributes', 0x410)):
            with self.subTest(key=key), mock.patch.dict(self.fs.rows[self.fs.root], {key:value}), self.assertRaises(ValueError):
                self.run_cleanup()
        self.assertNotIn('leaf_unlink', self.fs.events)

    def test_unexpected_windows_or_other_entry_is_not_deleted(self):
        for leaf in ('windows.bin', 'other'):
            key = self.fs.root+'\\'+leaf; self.fs.rows[key] = copy.deepcopy(C.EXPECTED_LEAF)
            with self.subTest(leaf=leaf), self.assertRaises(ValueError): self.run_cleanup()
            del self.fs.rows[key]
        self.assertNotIn('leaf_unlink', self.fs.events)

    def test_original_tiny_read_payload_and_receipt_must_match(self):
        good, receipt = self.fs.tiny_read(self.fs.path(self.fs.leaf))
        for payload, changed in ((b'X'*116, receipt), (good, {**receipt, 'inode': 9})):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.run_cleanup(tiny_read=lambda path: (payload, changed))
        self.assertNotIn('durable_backup', self.fs.events)

    def test_backup_failure_or_missing_durability_blocks_both_effects(self):
        def fail(*unused): raise OSError('fake C backup failure')
        with self.assertRaises(OSError): self.run_cleanup(backup=fail)
        with self.assertRaises(ValueError):
            self.run_cleanup(backup=lambda *args: {'fsync_and_readback_before_UNC_effects': False})
        self.assertNotIn('leaf_unlink', self.fs.events)

    def test_intent_failure_prevents_leaf_unlink(self):
        def progress(phase, details):
            if phase == 'BEFORE_EXACT_LEAF_UNLINK': raise OSError('fake intent persistence failure')
        with self.assertRaises(OSError): self.run_cleanup(progress=progress)
        self.assertIn(self.fs.leaf, self.fs.rows)
        self.assertNotIn('directory_rmdir', self.fs.events)

    def test_leaf_change_after_intent_is_rejected(self):
        def progress(phase, details):
            if phase == 'BEFORE_EXACT_LEAF_UNLINK': self.fs.rows[self.fs.leaf]['inode'] = 9
        with self.assertRaises(ValueError): self.run_cleanup(progress=progress)
        self.assertNotIn('leaf_unlink', self.fs.events)

    def test_failure_after_unlink_preserves_empty_directory_and_backup_evidence(self):
        def progress(phase, details):
            if phase == 'EXACT_LEAF_UNLINK_RETURNED': raise OSError('fake publication failure')
        with self.assertRaises(OSError): self.run_cleanup(progress=progress)
        self.assertNotIn(self.fs.leaf, self.fs.rows)
        self.assertIn(self.fs.root, self.fs.rows)
        self.assertIn('durable_backup', self.fs.events)
        self.assertNotIn('directory_rmdir', self.fs.events)

    def test_directory_replacement_or_new_entry_prevents_rmdir(self):
        def progress(phase, details):
            if phase == 'BEFORE_EXACT_EMPTY_DIRECTORY_RMDIR': self.fs.rows[self.fs.root]['inode'] = 9
        with self.assertRaises(ValueError): self.run_cleanup(progress=progress)
        self.assertNotIn('directory_rmdir', self.fs.events)

    def test_non_missing_unc_error_is_never_accepted_as_absent(self):
        class BadPath:
            def lstat(self): raise PermissionError('fake access denial')
        with self.assertRaises(PermissionError): C.require_absent(BadPath())


class CBackupAndStaticBoundaries(unittest.TestCase):
    def test_cli_main_guard_follows_every_function_definition(self):
        tree = ast.parse(Path(C.__file__).read_bytes())
        guards = [index for index, node in enumerate(tree.body) if isinstance(node, ast.If)
                  and ast.dump(node.test) == ast.dump(ast.parse("__name__ == '__main__'", mode='eval').body)]
        self.assertEqual(guards, [len(tree.body)-1])
        resource = next(index for index, node in enumerate(tree.body)
                        if isinstance(node, ast.FunctionDef) and node.name == 'resources')
        self.assertLess(resource, guards[0])

    def test_v2_moves_guard_only_and_preserves_all_original_function_asts(self):
        old = (C.WORK/'stage5_unc03_exact_sentinel_cleanup.py').read_bytes()
        new = Path(C.__file__).read_bytes()
        guard = b"if __name__ == '__main__':\n    raise SystemExit(main())\n"
        self.assertEqual(new, old.replace(guard, b'').rstrip()+b'\n\n\n'+guard)
        def functions(raw):
            return {n.name:ast.dump(n, include_attributes=False) for n in ast.parse(raw).body
                    if isinstance(n,ast.FunctionDef)}
        self.assertEqual(functions(old),functions(new))

    def test_real_tiny_c_backup_fsync_and_readback(self):
        directory = Path(tempfile.mkdtemp(prefix='fixture_unc03_cleanup_', dir=C.WORK)).resolve()
        self.assertEqual(directory.parent, C.WORK)
        def atomic(path, value):
            with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
                json.dump(value, stream); stream.flush(); os.fsync(stream.fileno())
        try:
            receipt = C.save_backup(directory, PAYLOAD, {'inode':33554461}, C.EXPECTED_DIRECTORY, atomic)
            self.assertIs(receipt['fsync_and_readback_before_UNC_effects'], True)
            self.assertEqual((directory/'linux.bin.backup').read_bytes(), PAYLOAD)
            self.assertEqual(json.loads((directory/'backup_metadata.json').read_bytes())['payload_sha256'],
                             hashlib.sha256(PAYLOAD).hexdigest())
        finally:
            for name in ('linux.bin.backup','backup_metadata.json'):
                path = directory/name
                if path.exists(): path.unlink()
            directory.rmdir()

    def test_existing_diagnostic_guard_helper_asts_preserved(self):
        old = ast.parse((C.WORK/'stage5_unc03_readonly_diagnostic.py').read_bytes())
        new = ast.parse(Path(C.__file__).read_bytes())
        def functions(tree): return {n.name:ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
        a,b=functions(old),functions(new)
        for name in ('need','sha','error_record','plain_c','original_request','authority','resources','metadata'):
            with self.subTest(name=name): self.assertEqual(a[name],b[name])

    def test_fixed_original_dependency_and_prior_receipt_bytes(self):
        for name,pin in {**C.PINS,**C.RECEIPTS}.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((C.WORK/name).read_bytes()).hexdigest(),pin)
        self.assertIn('windows_job', Path(C.__file__).read_text())

    def test_default_noop_never_loads_modules_or_effects(self):
        output=io.StringIO()
        with mock.patch('sys.argv', [str(Path(C.__file__))]), \
             mock.patch.object(C,'modules',side_effect=AssertionError('actual modules forbidden')), redirect_stdout(output):
            self.assertEqual(C.main(),0)
        value=json.loads(output.getvalue())
        self.assertEqual(value['state'],'PREPARED_EXACT_FAILED03_CLEANUP_NOT_RUN')
        self.assertEqual(value['UNC_effects'],0)

    def test_worker_requires_explicit_run(self):
        with mock.patch('sys.argv',[str(Path(C.__file__)),'--worker']), self.assertRaises(ValueError): C.main()


if __name__ == '__main__': unittest.main()
