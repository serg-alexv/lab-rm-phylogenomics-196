"""Pure synthetic metadata/byte-block contracts; no archive or runtime access."""
import copy
import hashlib
import unittest
import stage5_runtime_recovery_contract as C


def row(role, path='.', kind='directory', **extra):
    result = dict(role=role, path=path, kind=kind, mode=0o755, uid=1000, gid=1000,
                  mtime_ns=10**18, bytes=0, sha256=None, link_target=None, xattrs={},
                  source_dev=1, source_ino=int.from_bytes(hashlib.sha256((role+path).encode()).digest()[:6], 'big'),
                  source_nlink=1, source_ctime_ns=10**18)
    if kind == 'regular':
        result.update(bytes=3, sha256=C.digest(b'abc'))
    result.update(extra)
    return result


def fixture():
    rows = [row(role) for role in C.ROOTS]
    rows += [row('environment_dir', 'bin'), row('environment_dir', 'bin/python', 'regular')]
    rows.sort(key=lambda r: r['role'] + '/' + r['path'])
    runtime = dict(schema='STAGE05_PINNED_RUNTIME_V1', roots=C.ROOTS.copy(),
                   files={role: ({'bin/python': C.digest(b'abc')} if role == 'environment_dir' else {})
                          for role in C.ROOTS})
    return rows, runtime


class Contracts(unittest.TestCase):
    def test_three_roles_and_exact_scientific_bytes(self):
        rows, runtime = fixture()
        self.assertEqual(C.validate_manifest(rows, runtime)['entry_count'], 5)

    def test_pending_inputs_cannot_authorize(self):
        with self.assertRaises(ValueError):
            C.capture_gate(dict(schema='STAGE05_INSTALLED_RUNTIME_CAPTURE_INPUTS_V1', state='PENDING_NOT_AUTHORITY'))

    def test_ready_without_actual_pins_rejected(self):
        with self.assertRaises(ValueError):
            C.capture_gate(dict(schema='STAGE05_INSTALLED_RUNTIME_CAPTURE_INPUTS_V1', state='REVIEWED_COLD_CAPTURE_READY'))

    def test_all_actual_pins_and_no_equivalence(self):
        values = dict(schema='STAGE05_INSTALLED_RUNTIME_CAPTURE_INPUTS_V1', state='REVIEWED_COLD_CAPTURE_READY',
                      roots=C.ROOTS, original_prefix_required=True,
                      all_required_runtime_files_public_and_covered=True, all_special_metadata_resolved=True,
                      installed_build_equivalence='NOT_ESTABLISHED')
        for name in ['actual_runtime_manifest_sha256','complete_inventory_sha256','whole_file_public_review_sha256',
                     'cold_exclusive_capture_receipt_sha256','license_source_notice_review_sha256','published_capture_source_sha256']:
            values[name] = 'a'*64
        self.assertTrue(C.capture_gate(values))
        values['installed_build_equivalence'] = 'PASS'
        with self.assertRaises(ValueError): C.capture_gate(values)

    def test_noncanonical_paths(self):
        for value in ['/etc/passwd','../x','a/../b','a//b','a\\b','a\0b','a/./b']:
            with self.subTest(value=value), self.assertRaises(ValueError): C.relative(value)

    def test_relative_internal_symlink(self):
        rows, runtime = fixture()
        rows += [row('environment_dir','bin/python3','symlink',mode=0o777,link_target='python')]
        rows.sort(key=lambda r:r['role']+'/'+r['path'])
        runtime['files']['environment_dir']['bin/python3'] = C.digest(b'abc')
        self.assertTrue(C.validate_manifest(rows,runtime)['scientific_subset_covered'])

    def test_cross_role_original_absolute_symlink(self):
        rows, runtime = fixture()
        rows += [row('models_dir','python','symlink',mode=0o777,link_target=C.ROOTS['environment_dir']+'/bin/python')]
        rows.sort(key=lambda r:r['role']+'/'+r['path'])
        self.assertTrue(C.validate_manifest(rows,runtime)['scientific_subset_covered'])

    def test_external_symlink_held(self):
        for target in ['/etc/passwd','../../../../../../secret']:
            with self.subTest(target=target), self.assertRaises(ValueError):
                C.entry(row('environment_dir','bin/bad','symlink',link_target=target))

    def test_symlink_cycle_and_dangling_held(self):
        for target in ['python3','missing']:
            rows,runtime=fixture()
            rows += [row('environment_dir','bin/python3','symlink',link_target=target)]
            rows.sort(key=lambda r:r['role']+'/'+r['path'])
            with self.subTest(target=target), self.assertRaises(ValueError): C.validate_manifest(rows,runtime)

    def test_no_descendant_below_symlink(self):
        rows,runtime=fixture()
        rows += [row('environment_dir','link','symlink',link_target='bin'),
                 row('environment_dir','link/file','regular')]
        rows.sort(key=lambda r:r['role']+'/'+r['path'])
        with self.assertRaises(ValueError): C.validate_manifest(rows,runtime)

    def test_omitted_or_changed_scientific_dependency(self):
        rows,runtime=fixture()
        for candidate in [rows[:-1],copy.deepcopy(rows)]:
            if len(candidate)==len(rows): candidate[2]['sha256']='b'*64
            with self.assertRaises(ValueError): C.validate_manifest(candidate,runtime)

    def test_hardlink_graph_original_identity(self):
        rows,runtime=fixture(); source=next(r for r in rows if r['path']=='bin/python')
        source['source_nlink']=2
        other=copy.deepcopy(source);other.update(path='bin/python3',kind='hardlink',link_target='environment_dir/bin/python')
        rows.append(other);rows.sort(key=lambda r:r['role']+'/'+r['path'])
        self.assertTrue(C.validate_manifest(rows,runtime)['scientific_subset_covered'])
        other['source_ino']+=1
        with self.assertRaises(ValueError): C.validate_manifest(rows,runtime)

    def test_special_files_and_xattr_encoding(self):
        for changes in [dict(kind='fifo'),dict(xattrs={'user.test':'notbase64!'}),dict(source_ino=0)]:
            with self.subTest(changes=changes), self.assertRaises((ValueError,Exception)):
                C.entry(row('environment_dir',**changes))

    def test_private_path_hold(self):
        for value in ['.git/config','etc/.netrc','.config/gcloud/credentials.db']:
            self.assertIsNotNone(C.private_path_reason(value))
        self.assertIsNone(C.private_path_reason('lib/python3.11/site-packages/pkg/LICENSE'))

    def test_secret_across_blocks_and_no_matched_bytes(self):
        secret=b'-----BEGIN PRIVATE KEY-----'
        self.assertEqual(C.scan_secret_blocks([secret[:9],secret[9:]]),['PRIVATE_KEY'])
        self.assertEqual(C.scan_secret_blocks([b'ordinary scientific model data']),[])

    def test_bounded_secret_blocks(self):
        with self.assertRaises(ValueError): C.scan_secret_blocks([b'x'*(C.CHUNK_BYTES+1)])

    def test_shard_limit_exact_and_overflow(self):
        self.assertEqual(C.shard_lengths(C.SHARD_LIMIT+1),[C.SHARD_LIMIT,1])
        self.assertEqual(C.shard_lengths(C.SHARD_LIMIT),[C.SHARD_LIMIT])
        with self.assertRaises(ValueError): C.shard_lengths(1,C.SHARD_LIMIT+1)


if __name__ == '__main__':
    unittest.main()
