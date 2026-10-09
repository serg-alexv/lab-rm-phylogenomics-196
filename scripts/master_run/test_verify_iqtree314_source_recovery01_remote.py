"""Tiny in-memory source/tar/gzip contracts; no upstream payload or network reads."""
import gzip
import hashlib
import io
import tarfile
import unittest
from unittest.mock import patch

import verify_iqtree314_source_recovery01_remote as v

COMMIT = 'a' * 40


def pin(data, mode='100644'):
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                git_blob=hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(), mode=mode)


def fixture(entries, name='demo', tail=b''):
    raw = io.BytesIO(); prefix = name + '-' + COMMIT
    with tarfile.open(fileobj=raw, mode='w') as archive:
        root = tarfile.TarInfo(prefix); root.type = tarfile.DIRTYPE; root.mode = 0o755; archive.addfile(root)
        for relative, data, mode in entries:
            info = tarfile.TarInfo(prefix + '/' + relative)
            if mode == '120000':
                info.type = tarfile.SYMTYPE; info.linkname = data.decode(); info.mode = 0o777; archive.addfile(info)
            else:
                info.size = len(data); info.mode = 0o755 if mode == '100755' else 0o644
                archive.addfile(info, io.BytesIO(data))
    return gzip.compress(raw.getvalue() + tail, mtime=0)


def check(data, expected, name='demo', directories=None, original=None):
    with patch.object(v.B, 'guard'):
        return v.source_tar(io.BytesIO(data), name, COMMIT, expected, directories or {''}, original)


class Contracts(unittest.TestCase):
    def test_exact_regular_executable_and_symlink_git_payloads(self):
        rows = [('source.c', b'project source\n', '100644'), ('script.sh', b'echo fixture\n', '100755'),
                ('link', b'source.c', '120000')]
        result = check(fixture(rows), {name: pin(data, mode) for name, data, mode in rows})
        self.assertEqual(result['blob_count'], 3); self.assertEqual(result['symbolic_links'], 1)
        self.assertTrue(result['gzip_crc_and_length_verified']); self.assertEqual(result['exact_export_exceptions'], 0)

    def test_changed_payload_with_valid_gzip_crc_rejected(self):
        expected = {'one.txt': pin(b'good')}
        with self.assertRaisesRegex(ValueError, 'Git SHA1/SHA256'):
            check(fixture([('one.txt', b'evil', '100644')]), expected)

    def test_missing_extra_duplicate_or_traversal_member_rejected(self):
        row = ('one.txt', b'good', '100644'); expected = {'one.txt': pin(b'good')}
        for rows in ([], [row, ('extra.txt', b'no', '100644')], [row, row], [('../escape', b'no', '100644')]):
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                check(fixture(rows), expected)

    def test_symlink_cannot_replace_regular_source(self):
        with self.assertRaisesRegex(ValueError, 'symlink mode'):
            check(fixture([('one.txt', b'target', '120000')]), {'one.txt': pin(b'target')})

    def test_gzip_trailer_crc_is_actually_checked(self):
        expected = {'one.txt': pin(b'good')}; data = fixture([('one.txt', b'good', '100644')])
        broken = data[:-8] + bytes([data[-8] ^ 1]) + data[-7:]
        with self.assertRaises(gzip.BadGzipFile):
            check(broken, expected)

    def test_hidden_nonzero_payload_after_tar_end_is_rejected(self):
        expected = {'one.txt': pin(b'good')}
        with self.assertRaisesRegex(ValueError, 'nonzero/oversized'):
            check(fixture([('one.txt', b'good', '100644')], tail=b'hidden payload'), expected)

    def test_actual_expanded_stream_has_finite_bound(self):
        with patch.object(v, 'MAX_EXPANDED_TAR_BYTES', 1024), self.assertRaisesRegex(ValueError, 'Expanded source tar'):
            check(fixture([('one.txt', b'good', '100644')]), {'one.txt': pin(b'good')})

    def test_only_exact_qualified_crlf_export_and_original_supplement_pass(self):
        original = b'x' * 234 + b'\n' * 15; exported = original.replace(b'\n', b'\r\n')
        original_pin = pin(original); expected = {v.EXCEPTION_PATH: {**original_pin, 'archive_bytes': 264,
            'archive_sha256': hashlib.sha256(exported).hexdigest(),
            'original_recovery_supplement': 'original_git_blobs/' + original_pin['git_blob'] + '.blob'}}
        with (patch.object(v, 'ORIGINAL_SHA', original_pin['sha256']), patch.object(v, 'ORIGINAL_GIT', original_pin['git_blob']),
                patch.object(v, 'EXPORTED_SHA', hashlib.sha256(exported).hexdigest())):
            result = check(fixture([(v.EXCEPTION_PATH, exported, '100644')], name='iqtree3'), expected,
                           name='iqtree3', directories={'', 'terraphast'}, original=original)
            self.assertEqual(result['exact_export_exceptions'], 1); self.assertEqual(result['original_git_blob_bytes'], 249)
            for bad_original in (None, b'wrong', original[:-1] + b'x'):
                with self.subTest(original=bad_original is None), self.assertRaises(ValueError):
                    check(fixture([(v.EXCEPTION_PATH, exported, '100644')], name='iqtree3'), expected,
                          name='iqtree3', directories={'', 'terraphast'}, original=bad_original)

    def test_exception_metadata_never_permits_general_line_ending_normalization(self):
        original = b'one\ntwo\n'; exported = original.replace(b'\n', b'\r\n')
        expected = {'other.yml': {**pin(original), 'archive_bytes': len(exported), 'archive_sha256': hashlib.sha256(exported).hexdigest()}}
        with self.assertRaisesRegex(ValueError, 'Unexpected blob exception metadata'):
            check(fixture([('other.yml', exported, '100644')]), expected)

    def test_original_source_sidecar_lf_exact_crlf_substitution_rejected(self):
        asset = v.ASSETS[0]; side = v.SIDECARS[0]
        raw = (asset['sha256'] + '  ' + asset['name'] + '\n').encode('ascii')
        self.assertEqual(len(raw), 105); self.assertEqual(hashlib.sha256(raw).hexdigest(), side['sha256'])
        self.assertNotEqual(hashlib.sha256(raw.replace(b'\n', b'\r\n')).hexdigest(), side['sha256'])


if __name__ == '__main__':
    unittest.main()
