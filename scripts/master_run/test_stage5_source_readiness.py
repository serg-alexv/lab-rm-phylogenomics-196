"""Small local source-readiness scope/identity fixtures; no G/WSL/runtime reads."""
from pathlib import Path
from unittest import mock
import tempfile
import unittest
import stage5_source_readiness as V


class SourceReadinessContracts(unittest.TestCase):
    def test_transplanted_checker_rejected_before_directory_creation(self):
        with mock.patch.object(V, 'WORK', Path(r'G:\unexpected')), \
             mock.patch.object(Path, 'mkdir', side_effect=AssertionError('No writes')):
            with self.assertRaisesRegex(ValueError, 'Exact current C chat'):
                V.checked_output(Path(r'G:\unexpected\report'))

    def test_stream_hash_binds_exact_bytes_and_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'scientific_fixture.faa'
            path.write_bytes(b'>SYNTHETIC_ONLY\nACDE\n')
            rows = []
            with mock.patch.object(V, 'ROOT', root):
                self.assertEqual(V.bounded_sha(path, rows), V.digest(path))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['bytes'], 21)

    def test_changed_identity_during_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'fixture'
            path.write_bytes(b'fixture')
            with mock.patch.object(V, 'ROOT', root), \
                 mock.patch.object(V, 'file_identity', side_effect=[{'inode': 1}, {'inode': 2}]):
                with self.assertRaisesRegex(ValueError, 'changed while hashing'):
                    V.bounded_sha(path, [])

    def test_only_exact_sha_pinned_active_c_control_is_permitted(self):
        rows = []
        exact = V.WORK / 'stage5_accepted_source_pins.json'
        self.assertEqual(V.bounded_sha(exact, rows), V.PINS[exact.name])
        self.assertEqual(rows[0]['role'], 'ACTIVE_C_ACCEPTED_SOURCE_PIN_CONTROL')
        with self.assertRaisesRegex(ValueError, 'escaped canonical G'):
            V.bounded_sha(V.WORK / 'stage5_atomic.py', [])
        with mock.patch.dict(V.PINS, {'stage5_accepted_source_pins.json': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'source pin control changed'):
                V.bounded_sha(exact, [])


if __name__ == '__main__':
    unittest.main()
