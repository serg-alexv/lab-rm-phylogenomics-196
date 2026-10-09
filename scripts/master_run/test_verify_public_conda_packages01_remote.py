"""Small synthetic integrity contracts; no network, package read or disk writes."""
import copy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import verify_public_conda_packages01_remote as v


def fixtures():
    row = dict(name='demo', version='1.0', build='abc_0', fn='demo-1.0-abc_0.conda',
               subdir='linux-64', url='https://conda.anaconda.org/conda-forge/linux-64/demo-1.0-abc_0.conda',
               size=4, sha256=hashlib.sha256(b'demo').hexdigest(), license='BSD-3-Clause')
    names = list(v.MANIFESTS)
    manifests = {name: json.dumps(dict(packages=[copy.deepcopy(row)])).encode() for name in names}
    pin = dict(name=row['name'], version=row['version'], build=row['build'], filename=row['fn'],
               subdir=row['subdir'], url=row['url'], bytes=row['size'], sha256=row['sha256'], license=row['license'],
               source_records=[dict(manifest=name, row_index=0) for name in names])
    index = dict(schema='MASTER_EXACT_PUBLIC_CONDA_PACKAGE_INDEX_V1',
                 original_records=[dict(manifest=name, row_index=0, original_record=copy.deepcopy(row)) for name in names],
                 packages=[pin], manifest_pins=v.MANIFESTS, total_distinct_bytes=4, recovery_plan_sha256=v.PLAN_SHA)
    return manifests, index


def check(manifests, index):
    return v.expected_packages(manifests, index, counts=(1, 1), unique=1, total=4)


def tiny_zip():
    member = 'packages/' + hashlib.sha256(b'demo').hexdigest() + '/demo.conda'
    payloads = {member: b'demo', 'control/notice.txt': b'unchanged original notice\n'}
    sums = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in sorted(payloads.items())).encode()
    payloads['SHA256SUMS.txt'] = sums
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in payloads.items():
            info = zipfile.ZipInfo(name, (2026, 10, 9, 0, 0, 0)); info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    data = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        pins = {i.filename: dict(member=i.filename, bytes=i.file_size, sha256=hashlib.sha256(payloads[i.filename]).hexdigest(),
            crc32=f'{i.CRC:08x}', crc_verified=True) for i in archive.infolist()}
    return data, pins


class Contracts(unittest.TestCase):
    def test_two_roles_share_one_exact_original_without_losing_license(self):
        manifests, index = fixtures(); expected = check(manifests, index)
        self.assertEqual(len(expected), 1)
        self.assertEqual(len(next(iter(expected.values()))['source_records']), 2)
        self.assertEqual(next(iter(expected.values()))['license'], 'BSD-3-Clause')

    def test_self_consistent_index_replacement_cannot_change_original_license(self):
        manifests, index = fixtures()
        index['packages'][0]['license'] = 'Different'
        for row in index['original_records']:
            row['original_record']['license'] = 'Different'
        with self.assertRaisesRegex(ValueError, 'exactly preserve'):
            check(manifests, index)

    def test_conflicting_same_sha_between_roles_rejected(self):
        manifests, index = fixtures(); name = list(manifests)[1]
        value = json.loads(manifests[name]); value['packages'][0]['license'] = 'Different'
        manifests[name] = json.dumps(value).encode()
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            check(manifests, index)

    def test_role_row_loss_rejected(self):
        manifests, index = fixtures(); index['packages'][0]['source_records'].pop()
        with self.assertRaisesRegex(ValueError, 'exactly preserve'):
            check(manifests, index)

    def test_nonofficial_or_aliased_urls_rejected(self):
        for url in ('http://conda.anaconda.org/conda-forge/linux-64/demo-1.0-abc_0.conda',
                    'https://evil.example/conda-forge/linux-64/demo-1.0-abc_0.conda',
                    'https://user:secret@conda.anaconda.org/conda-forge/linux-64/demo-1.0-abc_0.conda',
                    'https://conda.anaconda.org/conda-forge/linux-64/demo-1.0-abc_0.conda?token=secret'):
            manifests, index = fixtures(); name = next(iter(manifests))
            row = json.loads(manifests[name]); row['packages'][0]['url'] = url
            manifests[name] = json.dumps(row).encode()
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, 'Invalid original'):
                check(manifests, index)

    def test_package_coverage_missing_replacement_sha_or_size_rejected(self):
        manifests, index = fixtures(); expected = check(manifests, index)
        correct = {n: {k: p[k] for k in ('bytes', 'sha256')} for n, p in expected.items()}
        v.check_package_coverage(correct, expected)
        for mutation in ('missing', 'sha', 'size', 'name'):
            wrong = copy.deepcopy(correct); name = next(iter(wrong))
            if mutation == 'missing': wrong = {}
            elif mutation == 'sha': wrong[name]['sha256'] = '0' * 64
            elif mutation == 'size': wrong[name]['bytes'] += 1
            else: wrong[name + '.replacement'] = wrong.pop(name)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                v.check_package_coverage(wrong, expected)

    def test_actual_stored_member_eof_crc_sha_and_sums(self):
        data, pins = tiny_zip(); actual_class = zipfile.ZipFile
        asset = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        with (patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=len(data))),
                patch.object(v, 'file_sha', return_value=asset['sha256']),
                patch.object(v.zipfile, 'ZipFile', side_effect=lambda _: actual_class(io.BytesIO(data)))):
            self.assertEqual(set(v.verify_zip(Path('synthetic'), asset, pins)), set(pins))

    def test_corrupt_package_crc_rejected_even_with_regenerated_outer_sha(self):
        data, pins = tiny_zip(); actual_class = zipfile.ZipFile
        with actual_class(io.BytesIO(data)) as archive:
            info = next(i for i in archive.infolist() if i.filename.startswith('packages/'))
        header = info.header_offset
        position = header + 30 + int.from_bytes(data[header + 26:header + 28], 'little') + int.from_bytes(data[header + 28:header + 30], 'little')
        self.assertEqual(data[position:position + 4], b'demo')
        corrupted = data[:position] + b'X' + data[position + 1:]
        asset = dict(bytes=len(corrupted), sha256=hashlib.sha256(corrupted).hexdigest())
        with (patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=len(corrupted))),
                patch.object(v, 'file_sha', return_value=asset['sha256']),
                patch.object(v.zipfile, 'ZipFile', side_effect=lambda _: actual_class(io.BytesIO(corrupted))),
                self.assertRaisesRegex(zipfile.BadZipFile, 'Bad CRC-32')):
            v.verify_zip(Path('synthetic'), asset, pins)

    def test_original_lf_sidecar_is_exact_and_crlf_substitute_differs(self):
        for asset, side in zip(v.ASSETS, v.SIDECARS):
            raw = (asset['sha256'] + '  ' + asset['name'] + '\n').encode('ascii')
            self.assertEqual(len(raw), side['bytes']); self.assertEqual(hashlib.sha256(raw).hexdigest(), side['sha256'])
            self.assertNotEqual(hashlib.sha256(raw.replace(b'\n', b'\r\n')).hexdigest(), side['sha256'])

    def test_resource_failure_or_deadline_never_returns_a_verified_hash(self):
        reader = SimpleNamespace(read=lambda: dict(physical_available_bytes=0, commit_headroom_bytes=2 * v.RESERVE,
                                                   c_disk_free_bytes=20 * 1024**3))
        with patch.object(v, 'RESOURCE', reader), self.assertRaisesRegex(ValueError, 'reserve failed'):
            v.streamed_sha(io.BytesIO(b'synthetic'))
        with patch.object(v, 'DEADLINE', 0), self.assertRaisesRegex(ValueError, 'budget exceeded'):
            v.streamed_sha(io.BytesIO(b'synthetic'))


if __name__ == '__main__':
    unittest.main()
