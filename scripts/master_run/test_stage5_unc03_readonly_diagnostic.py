"""Focused C-only tests; no actual UNC, WSL, job, or WorkflowLock access."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PureWindowsPath
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, WORK/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


D = load('stage5_unc03_readonly_diagnostic')
U = load('stage5_unc_bind_probe')


class DiagnosticTests(unittest.TestCase):
    def test_default_noop_does_not_import_or_launch(self):
        with patch.object(sys, 'argv', ['diagnostic']), patch.object(D, 'modules', side_effect=AssertionError), \
                patch.object(D, 'owner', side_effect=AssertionError), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(D.main(), 0)
        self.assertEqual(json.loads(out.getvalue()), {'state': 'PREPARED_READONLY_DIAGNOSTIC_NOT_RUN',
                                                     'WSL_launches': 0, 'UNC_writes': 0})

    def test_exact_four_targets_two_directories_and_source_pins(self):
        raw = (D.FAILED/'request.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), D.REQUEST_SHA)
        request = json.loads(raw)
        U.validate_request(request)
        rows = D.targets(request)
        self.assertEqual([row['role'] for row in rows],
                         ['canonical_linux', 'canonical_windows', 'backing_linux', 'backing_windows'])
        self.assertEqual(len(set(row['path'] for row in rows)), 4)
        directories = D.directory_targets(request)
        self.assertEqual(len(directories), 2)
        for index, row in enumerate(rows):
            self.assertEqual(str(PureWindowsPath(row['path']).parent), directories[index//2]['path'])
            self.assertEqual(PureWindowsPath(row['path']).name, ['linux.bin', 'windows.bin'][index%2])
        for name, pin in D.PINS.items():
            self.assertEqual(D.sha(WORK/name), pin)
        altered = {**request, 'sentinel_name': '../another'}
        with self.assertRaises(ValueError):
            D.targets(altered)

    def test_exact_failed03_nonce_is_immutable(self):
        request=json.loads((D.FAILED/'request.json').read_bytes())
        self.assertEqual(request['nonce'],'8ae35884653047348cfa688d4bf00b36')
        self.assertEqual(D.EXPECTED_NONCE,request['nonce'])
        wrong=dict(request,nonce='1'*32,sentinel_name='.unc_visibility_'+'1'*32)
        with self.assertRaises(ValueError):D.targets(wrong)

    def test_original_nlink_guard_error_retained_bounded_hash_and_no_mutation(self):
        payload = b'public-nonscientific-sentinel' * 3
        with tempfile.TemporaryDirectory(prefix='stage5_unc03_test_', dir=WORK) as directory:
            path = Path(directory)/'linux.bin'
            path.write_bytes(payload)
            before = path.stat()
            class ZeroLinkPath:
                def lstat(self):
                    info = path.lstat()
                    fields = {name: getattr(info, name) for name in
                              ('st_mode', 'st_uid', 'st_gid', 'st_dev', 'st_ino', 'st_size', 'st_mtime_ns')}
                    return SimpleNamespace(**fields, st_nlink=0, st_file_attributes=0)
                def is_symlink(self): return False
                def open(self, mode):
                    self_mode = mode
                    if self_mode != 'rb': raise AssertionError('Write forbidden')
                    return path.open(mode)
            row = {'role': 'canonical_linux', 'path': 'FIXTURE_ONLY', 'expected_bytes': len(payload),
                   'expected_sha256': hashlib.sha256(payload).hexdigest()}
            progress = []
            result = D.inspect_leaf(row, U.tiny_read, lambda *value: progress.append(value),
                                    path_factory=lambda _: ZeroLinkPath())
            self.assertEqual(result['metadata_before']['nlink'], 0)
            self.assertIn('Sentinel nonregular/linked/oversized', result['tiny_read_error']['message'])
            self.assertTrue(result['readonly_payload_observation']['matches_original_request_payload'])
            self.assertFalse(result['readonly_payload_observation']['scientific_or_UNC_adoption'])
            self.assertNotIn(payload.decode(), json.dumps(result))
            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
            self.assertEqual(len(progress), 4)

    def test_partial_windows_leaf_and_directory_permission_errors_preserved(self):
        with tempfile.TemporaryDirectory(prefix='stage5_unc03_test_', dir=WORK) as directory:
            path = Path(directory)/'windows.bin'
            partial = b'partial-public-payload'
            path.write_bytes(partial)
            error = PermissionError(13, 'fixture permission denial')
            error.winerror = 5
            def failing_read(_): raise error
            row = {'role': 'backing_windows', 'path': 'FIXTURE_ONLY', 'expected_bytes': 100,
                   'expected_sha256': '0'*64}
            result = D.inspect_leaf(row, failing_read, lambda *args: None, path_factory=lambda _: path)
            self.assertEqual(result['tiny_read_error']['winerror'], 5)
            self.assertFalse(result['readonly_payload_observation']['matches_original_request_payload'])
            self.assertEqual(path.read_bytes(), partial)
            class DeniedDirectory:
                def lstat(self): raise error
            directory_result = D.inspect_directory({'role': 'canonical_directory', 'path': 'FIXTURE_ONLY'},
                                                   lambda *args: None, path_factory=lambda _: DeniedDirectory())
            self.assertEqual(directory_result['metadata_error']['winerror'], 5)

    def test_authority_rejects_halt_without_canonical_access(self):
        with tempfile.TemporaryDirectory(prefix='stage5_unc03_test_', dir=WORK) as directory:
            root = Path(directory)
            (root/'status').mkdir()
            path = root/'status/run_control.json'
            for state, automatic, accepted in [('ACTIVE_DIRECT_USER_CONTINUATION', False, True),
                                                ('STOP', False, False),
                                                ('ACTIVE_DIRECT_USER_CONTINUATION', True, False)]:
                path.write_text(json.dumps({'state': state, 'automatic_resume': automatic}), encoding='utf-8')
                api = SimpleNamespace(read_json=lambda item: json.loads(item.read_bytes()))
                with patch.object(D, 'ROOT', root):
                    if accepted: self.assertEqual(D.authority(api), D.sha(path))
                    else:
                        with self.assertRaises(ValueError): D.authority(api)


if __name__ == '__main__':
    unittest.main(verbosity=2)
