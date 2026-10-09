"""Pure synthetic inventory normalization/screening; no runtime or archive I/O."""
import copy
import unittest
import stage5_runtime_logical_capture as L
import verify_stage5_runtime_cold_tree as T
from test_stage5_runtime_recovery_contract import fixture,row


class InventoryMetadata(unittest.TestCase):
    def test_dfs_hardlink_canonical_path_reversal(self):
        rows,runtime=fixture();parent=row('environment_dir','a')
        original=row('environment_dir','a/z','regular',source_nlink=2)
        alias=copy.deepcopy(original);alias.update(path='a-b',kind='hardlink',link_target='environment_dir/a/z')
        rows.extend([parent,original,alias]);holds={'environment_dir/a/z':['PRIVATE_KEY']}
        L.canonicalize_hardlinks(rows,holds)
        first=next(r for r in rows if r['path']=='a-b')
        second=next(r for r in rows if r['path']=='a/z')
        self.assertEqual((first['kind'],first['link_target']),('regular',None))
        self.assertEqual((second['kind'],second['link_target']),('hardlink','environment_dir/a-b'))
        self.assertEqual(holds['environment_dir/a-b'],['PRIVATE_KEY'])
        self.assertTrue(L.C.validate_manifest(rows,runtime)['scientific_subset_covered'])

    def test_same_inode_changed_metadata_rejected(self):
        original=row('environment_dir','a','regular',source_nlink=2)
        alias=copy.deepcopy(original);alias.update(path='b',bytes=4)
        with self.assertRaises(ValueError):L.canonicalize_hardlinks([original,alias],{})

    def test_cross_role_canonical_hardlink(self):
        rows,runtime=fixture();original=next(r for r in rows if r['path']=='bin/python')
        original['source_nlink']=2;alias=copy.deepcopy(original);alias.update(role='models_dir',path='shared')
        rows.append(alias);L.canonicalize_hardlinks(rows,{})
        self.assertEqual(alias['link_target'],'environment_dir/bin/python')
        self.assertTrue(L.C.validate_manifest(rows,runtime)['scientific_subset_covered'])

    def test_symlink_target_secret_screened_without_disclosing_match(self):
        value=row('models_dir','link','symlink',link_target='https://name:abcdefghijklmnopqrstuv@example.invalid/file')
        self.assertEqual(L.metadata_reason_codes(value),['URL_USER_PASSWORD'])

    def test_path_and_xattr_name_value_screened(self):
        value=row('models_dir','password=abcdefghijklmnopqrstuv')
        value['xattrs']={'user.password=abcdefghijklmnopqrstuv':'QmVhcmVyIGFiY2RlZmdoaWprbG1ub3BxcnN0dXY='}
        self.assertEqual(L.metadata_reason_codes(value),['ASSIGNED_SECRET','BEARER_VALUE'])

    def test_disposable_ext4_mount_metadata_only(self):
        raw=b'1 0 8:1 / / rw - ext4 /dev/sda rw\n2 1 0:42 / /mnt/c rw - 9p C: rw\n'
        result=T.mount_topology(raw,'/var/tmp/lab_rm_runtime_restore_SYNTHETIC')
        self.assertEqual((result['filesystem_type'],result['major_minor']),('ext4','8:1'))

    def test_nested_mount_rejected_even_on_same_device(self):
        base=b'1 0 8:1 / / rw - ext4 /dev/sda rw\n'
        for device in (b'8:1',b'7:0'):
            raw=base+b'2 1 '+device+b' / /var/tmp/lab_rm_runtime_restore_SYNTHETIC/environment_dir rw - ext4 /dev/loop0 rw\n'
            with self.assertRaisesRegex(ValueError,'Nested mount'):
                T.mount_topology(raw,'/var/tmp/lab_rm_runtime_restore_SYNTHETIC')

    def test_non_ext4_disposable_target_rejected(self):
        raw=b'1 0 0:42 / / rw - 9p C: rw\n'
        with self.assertRaisesRegex(ValueError,'ext4'):
            T.mount_topology(raw,'/var/tmp/lab_rm_runtime_restore_SYNTHETIC')


if __name__=='__main__':unittest.main()
