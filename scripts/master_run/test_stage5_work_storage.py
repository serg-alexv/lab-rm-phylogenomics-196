"""Synthetic storage contracts only: no WSL, mount, block-device or G writes."""
from pathlib import Path
from types import SimpleNamespace
import json, stat, tempfile, unittest, uuid
from unittest import mock
import stage5_atomic as R
import stage5_work_storage as W
from stage5_atomic_process import Fatal


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.base = Path(self.temp.name)
        self.root = self.base / 'project'
        self.target = self.root / '.work/stage05_atomic_v1'
        self.backing = self.base / 'var_tmp'
        self.target.mkdir(parents=True); self.backing.mkdir()
        encode = lambda p: str(p).replace('\\', r'\134').replace(' ', r'\040')
        self.mountinfo = ('10 1 8:16 / ' + encode(self.base) + ' rw,relatime - ext4 /dev/sdb rw\n'
                          '20 10 8:16 /var_tmp ' + encode(self.target) + ' rw,relatime - ext4 /dev/sdb rw\n')
        self.real_read = Path.read_text
        self.real_stat = Path.stat

    def tearDown(self):
        self.temp.cleanup()

    def observed(self, text=None, same_inode=True):
        def reading(path, *args, **kwargs):
            if path.as_posix() == '/proc/self/mountinfo': return self.mountinfo if text is None else text
            if path.as_posix() == '/proc/sys/kernel/random/boot_id': return 'SYNTHETIC_BOOT'
            return self.real_read(path, *args, **kwargs)
        def stated(path, *args, **kwargs):
            if path in (self.target, self.backing):
                return SimpleNamespace(st_dev=100, st_ino=200 if same_inode or path == self.backing else 201)
            return self.real_stat(path, *args, **kwargs)
        with mock.patch.object(W.sys, 'platform', 'linux'), mock.patch.object(W, 'canonical', side_effect=Path), \
             mock.patch.object(W, 'BACKING', self.backing), mock.patch.object(W.Path, 'read_text', autospec=True, side_effect=reading), \
             mock.patch.object(W.Path, 'stat', autospec=True, side_effect=stated), \
             mock.patch.object(W.os, 'major', return_value=8, create=True), \
             mock.patch.object(W.os, 'minor', return_value=16, create=True), \
             mock.patch.object(W, 'ext4_uuid', return_value='11111111-2222-3333-4444-555555555555'):
            return W.observe(self.root, self.target)

    def test_mountinfo_decodes_paths_and_preserves_mount_identity(self):
        row = W.mount_rows('7 1 8:16 /var/tmp/a /mnt/g/My\\040Drive rw,relatime shared:1 - ext4 /dev/sdb rw\n')[0]
        self.assertEqual(row['mountpoint'], '/mnt/g/My Drive')
        self.assertEqual((row['mount_id'], row['major_minor'], row['optional_fields']), (7, '8:16', ['shared:1']))

    def test_exact_ext4_bind_observation(self):
        value = self.observed()
        self.assertEqual(value['schema'], W.SCHEMA)
        self.assertEqual(value['canonical_target'], str(self.target))
        self.assertEqual(value['directory_inode'], 200)
        self.assertEqual(value['helper_sha256'], W.sha(W.__file__))

    def test_missing_bind_wrong_filesystem_or_directory_rejected(self):
        cases = [self.mountinfo.splitlines()[0] + '\n', self.mountinfo.replace('- ext4', '- 9p'),
                 self.mountinfo.replace('/var_tmp ', '/unrelated ')]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(Fatal): self.observed(text)
        with self.assertRaises(Fatal): self.observed(same_inode=False)

    def test_nested_mount_rejected(self):
        text = self.mountinfo + '30 20 8:16 /other ' + str(self.target / 'hidden').replace('\\', r'\134').replace(' ', r'\040') + ' rw - ext4 /dev/sdb rw\n'
        with self.assertRaises(Fatal): self.observed(text)

    def test_proof_hash_and_current_boot_uuid_mount_helper_must_match(self):
        frozen = self.observed()
        path = self.base / 'proof.json'; path.write_text(json.dumps(frozen))
        config = {'root': str(self.root), 'output_root': str(self.target),
                  'work_storage': {'proof_path': str(path), 'proof_sha256': W.sha(path)}}
        with mock.patch.object(W, 'proof_location', return_value=path), mock.patch.object(W, 'observe', return_value=frozen):
            self.assertEqual(W.validate_storage(config)['proof_sha256'], W.sha(path))
        for field in ('boot_id', 'filesystem_uuid', 'directory_inode', 'helper_sha256', 'target_mount'):
            changed = dict(frozen, **{field: 'DIFFERENT_SYNTHETIC_VALUE'})
            with self.subTest(field=field), mock.patch.object(W, 'proof_location', return_value=path), \
                 mock.patch.object(W, 'observe', return_value=changed), self.assertRaises(Fatal): W.validate_storage(config)
        path.write_text(json.dumps(dict(frozen, boot_id='OTHER')))
        with mock.patch.object(W, 'proof_location', return_value=path), self.assertRaises(Fatal): W.validate_storage(config)

    def test_unfilled_storage_config_fails_before_output_creation_or_cache_read(self):
        config = {'root': str(self.root), 'output_root': str(self.target)}
        with mock.patch.dict(R.sys.modules, {'fcntl': SimpleNamespace(), 'resource': SimpleNamespace()}), \
             mock.patch.object(R.sys, 'platform', 'linux'), mock.patch.object(R, 'approved_accession') as approved:
            with self.assertRaises(Fatal): R.run_genome(config, 'GCF_000000001.1', self.base/'lease', 'nonce')
            approved.assert_not_called()
        self.assertFalse((self.target/'GCF_000000001.1').exists())

    def test_each_prelaunch_reopens_storage_before_configuration(self):
        configuration = mock.Mock(return_value={'configuration': 'SYNTHETIC'})
        guard = R.storage_configuration_guard({'synthetic': True}, configuration)
        with mock.patch.object(R, 'validate_storage', return_value={'proof': 'SYNTHETIC'}) as storage:
            for _ in range(2): self.assertIn('work_storage', guard(None, None, None))
            self.assertEqual(storage.call_count, 2)
        configuration.reset_mock()
        with mock.patch.object(R, 'validate_storage', side_effect=Fatal('SYNTHETIC_MOUNT_DRIFT')), self.assertRaises(Fatal):
            guard(None, None, None)
        configuration.assert_not_called()

    def test_uuid_requires_matching_block_device_and_ext4_superblock(self):
        block = bytearray(120); block[56:58] = b'\x53\xef'
        expected = uuid.UUID('11111111-2222-3333-4444-555555555555'); block[104:120] = expected.bytes
        with mock.patch.object(W.os, 'O_CLOEXEC', 0, create=True), mock.patch.object(W.os, 'O_NOFOLLOW', 0, create=True), \
             mock.patch.object(W.os, 'open', return_value=71), mock.patch.object(W.os, 'close') as close, \
             mock.patch.object(W.os, 'fstat', return_value=SimpleNamespace(st_mode=stat.S_IFBLK, st_rdev=100)), \
             mock.patch.object(W.os, 'pread', return_value=bytes(block), create=True) as read:
            self.assertEqual(W.ext4_uuid('/dev/SYNTHETIC_NOT_OPENED', 100), str(expected))
            close.assert_called_once_with(71); read.assert_called_once_with(71, 120, 1024)
            with self.assertRaises(Fatal): W.ext4_uuid('/dev/SYNTHETIC_NOT_OPENED', 101)
            read.return_value = b'\0' * 120
            with self.assertRaises(Fatal): W.ext4_uuid('/dev/SYNTHETIC_NOT_OPENED', 100)

    def test_record_never_overwrites_existing_proof(self):
        path = self.base/'existing.json'; path.write_bytes(b'PRESERVE_SYNTHETIC_PROOF')
        argv = ['stage5_work_storage.py', '--root', str(self.root), 'record', '--output', str(path)]
        with mock.patch.object(W.sys, 'argv', argv), mock.patch.object(W, 'proof_location', return_value=path), \
             mock.patch.object(W, 'observe', return_value={'synthetic': True}), self.assertRaises(FileExistsError): W.main()
        self.assertEqual(path.read_bytes(), b'PRESERVE_SYNTHETIC_PROOF')


if __name__ == '__main__': unittest.main()
