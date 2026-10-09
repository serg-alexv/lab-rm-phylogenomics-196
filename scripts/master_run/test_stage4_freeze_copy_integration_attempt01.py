"""Nonscientific, temporary-file integration tests for Stage4 freeze copying.

Runs the checker main() with synthetic196 tips and temporary synthetic input
hash pins. No executable is launched and no production path is opened. Only
the unrelated1000-bootstrap parser stream is replaced with1000 references to
one actually parsed synthetic tree, keeping fixture memory and runtime small.
Newick, NEXUS, source binding, receipts, copying and hashing use real code.
"""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import sys
import unittest

from Bio import Phylo
import independent_tree_check as checker


IDS = [f'SYNTHETIC_FREEZE_{index:03}' for index in range(196)]


def balanced(ids):
    if len(ids) == 1:
        return ids[0] + ':0.1'
    middle = len(ids) // 2
    return '(' + balanced(ids[:middle]) + ',' + balanced(ids[middle:]) + ')95/100:0.1'


TREE = '(' + ','.join(balanced(group) for group in (IDS[:65], IDS[65:130], IDS[130:])) + ');\n'
CORRUPTION_CASES = {
    'host.iqtree': 'Frozen native member differs from validated snapshot',
    'host.treefile': 'Frozen native member differs from validated snapshot',
    'primary196_host_tree.nwk': 'Authoritative Newick bytes differ from the actually parsed tree',
    'accepted_primary196_concatenated.faa': 'Frozen accepted input differs from validated source',
    'accepted_original_config.json': 'Frozen accepted input differs from validated source',
    'accepted_approved_accessions.txt': 'Frozen accepted input differs from validated source',
    'accepted_primary196_partitions.nex': 'Frozen accepted input differs from validated source',
    'original_input_model_cache.gz': 'Frozen accepted input differs from validated source',
}


class SyntheticFreezeCopyIntegration(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix='synthetic_stage4_freeze_', dir=Path(__file__).resolve().parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.attempt = self.root / 'synthetic_native_attempt'
        self.attempt.mkdir()
        self.freeze = self.root / 'synthetic_accepted'
        self.report = self.root / 'synthetic_external_validation.json'
        self.approved = self.root / 'synthetic_approved.txt'
        self.approved.write_text('\n'.join(IDS) + '\n', encoding='utf-8')
        self.alignment = self.root / 'synthetic_alignment.faa'
        self.alignment.write_text(''.join('>' + name + '\nACDEFGHIKLMNPQRSTVWY\n' for name in IDS), encoding='ascii')
        self.partitions = self.root / 'synthetic_partitions.nex'
        self.partitions.write_bytes(b'SYNTHETIC PARTITIONS ONLY; NO INFERENCE\n')
        self.exe = self.root / 'synthetic_nonexecutable.exe'
        self.exe.write_bytes(b'SYNTHETIC NONEXECUTABLE; NEVER LAUNCHED\n')
        self.cache = self.root / 'synthetic_nonmodel.gz'
        self.cache.write_bytes(b'SYNTHETIC CACHE; NEVER INTERPRETED\n')
        self.config_source = self.root / 'synthetic_original_config.json'
        pins = {'PANEL': checker.digest(self.approved), 'ALIGNMENT': checker.digest(self.alignment),
                'PARTITIONS': checker.digest(self.partitions), 'EXECUTABLE': checker.digest(self.exe)}
        self.pin_patch = patch.multiple(checker, **pins)
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)
        cfg = {'schema': 'LAB_RM_ATOMIC_IQTREE_V1', 'mode': 'partitioned',
               'canonical_commit': checker.CANONICAL_COMMIT, 'threads': 2, 'seed': 1961008,
               'output_directory': str(self.attempt), 'repository_path': str(self.root),
               'approved_accessions': {'path': str(self.approved), 'sha256': pins['PANEL']},
               'executable': {'path': str(self.exe), 'sha256': pins['EXECUTABLE']},
               'alignment': {'path': str(self.alignment), 'sha256': pins['ALIGNMENT']},
               'partitions': {'path': str(self.partitions), 'sha256': pins['PARTITIONS']},
               'cache_import': {'path': str(self.cache), 'sha256': checker.digest(self.cache)}}
        self.write(self.config_source, cfg)
        cfg['_config_sha256'] = checker.digest(self.config_source)
        self.write(self.attempt / 'config.json', cfg)
        argv = [str(self.exe), '-s', str(self.alignment), '--seqtype', 'AA', '-p', str(self.partitions),
                '-m', 'MFP', '-B', '1000', '--alrt', '1000', '--seed', '1961008', '-T', '2',
                '-keep-ident', '--boot-trees', '--prefix', str(self.attempt / 'host')]
        birth = {'pid': 12345, 'creation_filetime': 100, 'executable': str(self.exe)}
        launch = {'cwd': str(self.attempt), 'argv': argv, 'native': birth,
                  'authority': {'canonical_commit': checker.CANONICAL_COMMIT},
                  'config_sha256': cfg['_config_sha256'], 'executable_sha256': pins['EXECUTABLE']}
        self.write(self.attempt / 'launch.json', launch)
        self.write(self.attempt / 'exit.json', {'state': 'VALIDATION_REQUIRED',
                   'native': {**birth, 'exited': True, 'exit_code': 0, 'exit_filetime': 200},
                   'job_active_processes': 0, 'job_pids': [],
                   'launch_sha256': checker.digest(self.attempt / 'launch.json')})
        self.write(self.attempt / 'result.json', {'state': 'VALIDATION_REQUIRED'})
        self.write(self.attempt / 'lock_released.json', {'state': 'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'})
        self.write(self.attempt / 'cache_import.json', {'source': str(self.cache), 'sha256': checker.digest(self.cache)})
        (self.attempt / 'host.iqtree').write_text('IQ-TREE version 3.1.4\nSeed: 1961008\nSH-aLRT 1000 replicates\n',
                                                encoding='utf-8')
        (self.attempt / 'host.log').write_text('Restoring information from model checkpoint file\n', encoding='utf-8')
        (self.attempt / 'stdout.txt').write_text('SYNTHETIC RECEIPTS; NO NATIVE EXECUTION\n', encoding='utf-8')
        (self.attempt / 'host.treefile').write_text(TREE, encoding='utf-8', newline='\n')
        (self.attempt / 'host.ufboot').write_bytes(b'SYNTHETIC PARSER STREAM REPLACED IN TEST ONLY\n')
        self.native_before = {p.name: checker.digest(p) for p in self.attempt.iterdir() if p.is_file()}

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value) + '\n', encoding='utf-8', newline='\n')

    def run_checker(self, corrupt=None):
        actual_parse, actual_copy = checker.Phylo.parse, checker.shutil.copyfile
        parsed_synthetic = Phylo.read(StringIO(TREE), 'newick')
        corruption_hits = []

        def bounded_parse(source, format, *args, **kwargs):
            if isinstance(source, Path) and source == self.attempt / 'host.ufboot':
                return iter([parsed_synthetic] * 1000)
            return actual_parse(source, format, *args, **kwargs)

        def copy(source, destination, *args, **kwargs):
            result = actual_copy(source, destination, *args, **kwargs)
            destination = Path(destination)
            if corrupt is not None and destination.parent == self.freeze and destination.name == corrupt:
                with destination.open('ab') as stream:
                    stream.write(b'\nSYNTHETIC CORRUPTED COPY\n')
                corruption_hits.append(destination.name)
            return result

        argv = ['synthetic_checker', '--attempt', str(self.attempt), '--approved', str(self.approved),
                '--report', str(self.report), '--freeze', str(self.freeze),
                '--config-source', str(self.config_source)]
        with patch.object(sys, 'argv', argv), patch.object(checker.Phylo, 'parse', side_effect=bounded_parse), \
                patch.object(checker.shutil, 'copyfile', side_effect=copy), redirect_stdout(StringIO()):
            if corrupt is None:
                checker.main()
            else:
                with self.assertRaisesRegex(ValueError, CORRUPTION_CASES[corrupt]):
                    checker.main()
        self.assertEqual(corruption_hits, [] if corrupt is None else [corrupt])
        self.assertEqual(self.native_before, {p.name: checker.digest(p) for p in self.attempt.iterdir() if p.is_file()})

    def test_clean_synthetic_copy_control(self):
        self.run_checker()
        record = checker.load(self.report)
        self.assertEqual(record['state'], 'COMPLETE_VALIDATED')
        self.assertEqual(record['unique_tips'], 196)
        self.assertEqual(checker.digest(self.freeze / 'accepted_primary196_concatenated.faa'), checker.ALIGNMENT)
        self.assertEqual(checker.digest(self.freeze / 'primary196_host_tree.nwk'), checker.digest(self.attempt / 'host.treefile'))
        self.assertTrue((self.freeze / 'input_output_sha256_manifest.tsv').is_file())


def corruption_test(name):
    def test(self):
        self.run_checker(name)
        self.assertEqual(checker.load(self.report)['state'], 'FAILED_FATAL')
        self.assertEqual(checker.load(self.freeze / 'independent_validation.json')['state'], 'FAILED_FATAL')
        self.assertFalse((self.freeze / 'input_output_sha256_manifest.tsv').exists())
    return test


for member in CORRUPTION_CASES:
    setattr(SyntheticFreezeCopyIntegration, 'test_reject_corrupt_copy_' + member.replace('.', '_'), corruption_test(member))


if __name__ == '__main__':
    unittest.main()
