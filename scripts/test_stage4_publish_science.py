"""Synthetic ZIP/certificate binding tests; no Git, GitHub, G drive or biology.

Only verify_prepared_science is called. ROOT and the approved-panel pin refer
to disposable fixtures under work/. A self-consistent ZIP is not acceptance.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import unittest
import zipfile

import publish_stage4_primary as publisher


def sha(data):
    return hashlib.sha256(data).hexdigest()


class PublicationScienceBindings(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix='synthetic_stage4_publication_',
                                      dir=Path(__file__).resolve().parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.freeze = self.root / 'synthetic_accepted'
        self.report = self.root / 'synthetic_report'
        self.staging = self.root / 'synthetic_staging'
        for directory in (self.freeze, self.report, self.staging):
            directory.mkdir()
        approved = ''.join(f'SYNTHETIC_ONLY_{index:03}\n' for index in range(196)).encode()
        self.panel_sha = sha(approved)
        payload = {
            'primary196_host_tree.nwk': b'(SYNTHETIC_A:0.1,SYNTHETIC_B:0.2);\n',
            'primary196_host_tree.nex': b'#NEXUS\nSYNTHETIC BINDING FIXTURE ONLY\n',
            'accepted_primary196_concatenated.faa': b'>SYNTHETIC_ONLY\nACDE\n',
            'accepted_original_config.json': b'{"dataset_kind":"SYNTHETIC"}\n',
            'accepted_approved_accessions.txt': approved,
            'host.log': b'SYNTHETIC NOT EXECUTED\n',
        }
        for name, data in payload.items():
            (self.freeze/name).write_bytes(data)
        self.validation = {
            'dataset_kind': 'SYNTHETIC_BINDING_FIXTURE_ONLY',
            'schema': 'STAGE04_PRIMARY_ACCEPTANCE_V1',
            'state': 'COMPLETE_VALIDATED', 'scientific_state': 'COMPLETE_VALIDATED',
            'approved_accessions_sha256': self.panel_sha, 'unique_tips': 196,
            'branch_lengths_valid': True, 'support_completed': True,
            'mode': 'single_model', 'frozen_output_directory': str(self.freeze),
            'files': {(self.freeze/name).relative_to(self.root).as_posix():sha(data)
                      for name, data in payload.items()},
        }
        certificate = (json.dumps(self.validation, indent=2)+'\n').encode()
        for directory in (self.freeze, self.report):
            (directory/'independent_validation.json').write_bytes(certificate)
        members = sorted(p for p in self.freeze.iterdir() if p.is_file())
        distribution = 'path\tsha256\tbytes\n'+''.join(
            f'{p.name}\t{sha(p.read_bytes())}\t{p.stat().st_size}\n' for p in members)
        for directory in (self.freeze,self.report):
            (directory/'input_output_sha256_manifest.tsv').write_text(distribution, encoding='utf-8')
        self.build_zip()

    def build_zip(self, overrides=None, omit=()):
        payload = {'accepted/'+p.name:p.read_bytes() for p in self.freeze.iterdir()
                   if p.is_file() and 'accepted/'+p.name not in omit}
        payload.update(overrides or {})
        payload['README.txt'] = b'SYNTHETIC ZIP BINDING TEST; NO BIOLOGICAL ACCEPTANCE\n'
        checks = ''.join(f'{sha(data)}  {name}\n' for name, data in sorted(payload.items()))
        archive = self.staging/'stage04-primary196-accepted.zip'
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
            for name, data in sorted(payload.items()):
                zipped.writestr(name, data)
            zipped.writestr('SHA256SUMS.txt', checks.encode())
        self.manifest = {'scientific_state':'COMPLETE_VALIDATED',
                         'final_validation_summary_sha256':sha((self.report/'independent_validation.json').read_bytes()),
                         'assets':[{'asset_name':archive.name, 'sha256':sha(archive.read_bytes()),
                                    'bytes':archive.stat().st_size, 'payload_members':len(payload)}]}
        # Independently establish that even the negative regenerated archive
        # has valid CRCs and complete, correct internal SHA256 checksums.
        with zipfile.ZipFile(archive) as zipped:
            self.assertIsNone(zipped.testzip())
            observed = {}
            for line in zipped.read('SHA256SUMS.txt').decode().splitlines():
                digest, name = line.split('  ', 1)
                self.assertNotIn(name, observed)
                observed[name] = digest
            self.assertEqual(set(observed), set(zipped.namelist())-{'SHA256SUMS.txt'})
            for name, digest in observed.items():
                self.assertEqual(sha(zipped.read(name)), digest)

    def verify(self):
        with patch.object(publisher, 'ROOT', self.root), \
             patch.object(publisher.A, 'EXPECTED_PANEL', self.panel_sha):
            publisher.verify_prepared_science(self.report, self.staging,
                                              self.manifest, self.validation)

    def test_clean_bound_zip(self):
        self.verify()

    def test_regenerated_self_consistent_wrong_tree_rejected(self):
        self.build_zip({'accepted/primary196_host_tree.nwk':
                        b'(SYNTHETIC_A:9.9,SYNTHETIC_B:9.8);\n'})
        with self.assertRaisesRegex(ValueError, 'ZIP scientific member differs'):
            self.verify()

    def test_regenerated_self_consistent_wrong_certificate_rejected(self):
        changed = dict(self.validation, mode='partitioned')
        self.build_zip({'accepted/independent_validation.json':json.dumps(changed).encode()})
        with self.assertRaisesRegex(ValueError, 'ZIP scientific member differs'):
            self.verify()

    def test_missing_scientific_member_rejected(self):
        self.build_zip(omit=('accepted/host.log',))
        with self.assertRaisesRegex(ValueError, 'ZIP accepted member set differs'):
            self.verify()

    def test_authoritative_source_drift_rejected(self):
        (self.freeze/'primary196_host_tree.nwk').write_bytes(b'SYNTHETIC DRIFT\n')
        with self.assertRaisesRegex(ValueError, 'Authoritative accepted scientific member changed'):
            self.verify()

    def test_unknown_mode_rejected(self):
        self.validation['mode'] = 'unsupported'
        with self.assertRaisesRegex(ValueError, 'acceptance schema/panel/tree/support required'):
            self.verify()

    def change_distribution(self, transform, compact=True):
        name = 'input_output_sha256_manifest.tsv'
        changed = transform((self.freeze/name).read_text(encoding='utf-8'))
        (self.freeze/name).write_text(changed,encoding='utf-8')
        if compact:
            (self.report/name).write_text(changed,encoding='utf-8')
        # Regenerate the ZIP and all its internal/asset checksums: rejection
        # must come from acceptance-to-distribution binding, not a stale ZIP.
        self.build_zip()

    def test_regenerated_distribution_differs_from_compact_copy_rejected(self):
        self.change_distribution(lambda text:text+'\n',compact=False)
        with self.assertRaisesRegex(ValueError, 'Compact distribution manifest differs'):
            self.verify()

    def test_regenerated_distribution_omits_certificate_rejected(self):
        self.change_distribution(lambda text:'\n'.join(line for line in text.splitlines()
            if not line.startswith('independent_validation.json\t'))+'\n')
        with self.assertRaisesRegex(ValueError, 'does not exhaustively cover'):
            self.verify()

    def test_regenerated_distribution_wrong_member_hash_rejected(self):
        self.change_distribution(lambda text:'\n'.join(
            'host.log\t'+'0'*64+'\t'+line.split('\t')[2]
            if line.startswith('host.log\t') else line for line in text.splitlines())+'\n')
        with self.assertRaisesRegex(ValueError, 'hash/size differs'):
            self.verify()

    def test_regenerated_distribution_wrong_member_size_rejected(self):
        self.change_distribution(lambda text:'\n'.join(
            '\t'.join(line.split('\t')[:2]+['99999'])
            if line.startswith('host.log\t') else line for line in text.splitlines())+'\n')
        with self.assertRaisesRegex(ValueError, 'hash/size differs'):
            self.verify()


if __name__ == '__main__':
    unittest.main(verbosity=2)
