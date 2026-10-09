"""Synthetic Newick acceptance-gate tests; no biological inference or figure."""
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import sys
import unittest
from Bio import Phylo
import independent_tree_check as checker
from independent_tree_check import tree_check

IDS = ['SYNTHETIC_'+str(i).zfill(3) for i in range(196)]
def balanced(ids):
    if len(ids) == 1:
        return ids[0]+':0.1'
    split = len(ids)//2
    return '('+balanced(ids[:split])+','+balanced(ids[split:])+')95/100:0.1'
VALID = '('+balanced(IDS[:65])+','+balanced(IDS[65:130])+','+balanced(IDS[130:])+');'

class Gate(unittest.TestCase):
    def test_valid_full196_synthetic(self):
        tree, facts = tree_check(VALID,set(IDS),True)
        self.assertEqual(facts['tips'],196)
        self.assertEqual(facts['paired_supported_internal_branches'],193)

    def test_duplicate_and_missing_accession(self):
        with self.assertRaises(ValueError):
            tree_check(VALID.replace('SYNTHETIC_195','SYNTHETIC_194'),set(IDS),True)

    def test_extra_accession(self):
        with self.assertRaises(ValueError):
            tree_check(VALID.replace('SYNTHETIC_195','UNAPPROVED'),set(IDS),True)

    def test_negative_branch_length(self):
        with self.assertRaises(ValueError):
            tree_check(VALID.replace(':0.1',':-0.1',1),set(IDS),True)

    def test_missing_branch_length(self):
        with self.assertRaises(ValueError):
            tree_check(VALID.replace(':0.1','',1),set(IDS),True)

    def test_nonfinite_branch_length(self):
        with self.assertRaises(ValueError):
            tree_check(VALID.replace(':0.1',':1e309',1),set(IDS),True)

    def test_out_of_range_support(self):
        with self.assertRaises(ValueError):
            tree_check(VALID.replace('95/100','95/101',1),set(IDS),True)

    def test_missing_support(self):
        with self.assertRaises(ValueError):
            tree_check(VALID.replace('95/100','',1),set(IDS),True)

    def test_nexus_wrapper_preserves_unrooted_topology_lengths_supports(self):
        original,_ = tree_check(VALID,set(IDS),True)
        nexus = '#NEXUS\nBegin trees;\nTree synthetic_only = [&U] '+VALID+'\nEnd;\n'
        imported = Phylo.read(StringIO(nexus),'nexus')
        def signature(t):
            return sorted((tuple(sorted(x.name for x in n.get_terminals())),n.branch_length if n is not t.root else None,
                n.name or '',n.confidence) for n in t.find_clades())
        self.assertFalse(imported.rooted)
        self.assertEqual(signature(original),signature(imported))

class CommandBinding(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.attempt = self.root/'attempt'; self.attempt.mkdir()
        self.exe = self.root/'iqtree.exe'; self.exe.write_bytes(b'SYNTHETIC EXE')
        self.alignment = self.root/'alignment.faa'; self.alignment.write_bytes(b'SYNTHETIC ALIGNMENT')
        self.partitions = self.root/'partitions.nex'; self.partitions.write_bytes(b'SYNTHETIC PARTITIONS')
        self.approved = self.root/'approved.txt'; self.approved.write_text('\n'.join(IDS)+'\n')
        self.config_source = self.root/'original.json'
        self.cfg = {'schema':'LAB_RM_ATOMIC_IQTREE_V1','mode':'partitioned',
            'canonical_commit':checker.CANONICAL_COMMIT,'threads':2,'seed':1961008,
            'output_directory':str(self.attempt),'repository_path':str(self.root),
            'approved_accessions':{'path':str(self.approved),'sha256':checker.PANEL},
            'executable':{'path':str(self.exe),'sha256':checker.EXECUTABLE},
            'alignment':{'path':str(self.alignment),'sha256':checker.ALIGNMENT},
            'partitions':{'path':str(self.partitions),'sha256':checker.PARTITIONS}}
        self.launch = {'cwd':str(self.attempt),'authority':{'canonical_commit':checker.CANONICAL_COMMIT},
            'native':{'executable':str(self.exe)},'executable_sha256':checker.EXECUTABLE}
        self.refresh()
        actual_digest = checker.digest
        self.pins = {self.exe:checker.EXECUTABLE,self.alignment:checker.ALIGNMENT,self.partitions:checker.PARTITIONS}
        self.patch = patch.object(checker,'digest',side_effect=lambda p:self.pins[Path(p)] if Path(p) in self.pins else actual_digest(p))
        self.patch.start(); self.addCleanup(self.patch.stop)

    def refresh(self):
        source = {key:value for key,value in self.cfg.items() if key != '_config_sha256'}
        self.config_source.write_text(json.dumps(source),encoding='utf-8')
        self.cfg['_config_sha256'] = checker.digest(self.config_source)
        self.launch['config_sha256'] = self.cfg['_config_sha256']
        self.launch['argv'] = [str(self.exe),'-s',str(self.alignment),'--seqtype','AA']
        if self.cfg['mode'] == 'partitioned':
            self.launch['argv'] += ['-p',str(self.partitions)]
        self.launch['argv'] += ['-m','MFP','-B','1000','--alrt','1000','--seed','1961008','-T','2',
            '-keep-ident','--boot-trees','--prefix',str(self.attempt/'host')]
        if self.cfg['mode'] == 'single_model':
            self.launch['argv'] += ['--mem','2G','--thread-site']

    def check(self):
        return checker.command_binding(self.cfg,self.launch,self.attempt,self.approved,self.config_source)

    def test_exact_partitioned_command_and_input_pins(self):
        sources = self.check()
        self.assertEqual(sources['partitions']['sha256'],checker.PARTITIONS)
        self.assertEqual(sources['original_config']['sha256'],checker.digest(self.config_source))

    def test_exact_single_model_without_partition_cache(self):
        self.cfg['mode'] = 'single_model'; del self.cfg['partitions']; self.refresh()
        self.assertNotIn('partitions',self.check())

    def test_changed_partition_argv_rejected(self):
        self.launch['argv'][self.launch['argv'].index('-p')+1] = str(self.root/'other.nex')
        with self.assertRaises(ValueError): self.check()

    def test_duplicate_options_extra_aliases_and_redo_rejected(self):
        original = list(self.launch['argv'])
        for extra in [['-T','2'],['--threads','2'],['-redo'],['--redo'],['-redo=1'],['--redo=true']]:
            with self.subTest(extra=extra):
                self.launch['argv'] = original+extra
                with self.assertRaises(ValueError): self.check()

    def test_wrong_cwd_and_prefix_rejected(self):
        self.launch['cwd'] = str(self.root)
        with self.assertRaises(ValueError): self.check()
        self.launch['cwd'] = str(self.attempt)
        self.launch['argv'][-1] = str(self.root/'other')
        with self.assertRaises(ValueError): self.check()

    def test_actual_executable_and_retained_image_rejected(self):
        self.pins[self.exe] = '0'*64
        with self.assertRaises(ValueError): self.check()
        self.pins[self.exe] = checker.EXECUTABLE
        self.launch['native']['executable'] = str(self.root/'other.exe')
        with self.assertRaises(ValueError): self.check()

    def test_actual_partition_and_alignment_drift_rejected(self):
        for path in [self.partitions,self.alignment]:
            with self.subTest(path=path):
                old = self.pins[path]; self.pins[path] = '0'*64
                with self.assertRaises(ValueError): self.check()
                self.pins[path] = old

    def test_original_config_bytes_and_semantics_bound(self):
        self.config_source.write_text(self.config_source.read_text()+'\n')
        with self.assertRaises(ValueError): self.check()
        self.refresh(); self.cfg['threads'] = 4
        with self.assertRaises(ValueError): self.check()

    def test_canonical_commit_bound(self):
        self.cfg['canonical_commit'] = '0'*40; self.refresh()
        with self.assertRaises(ValueError): self.check()

    def test_cache_source_and_initial_copy_receipt_bound(self):
        cache = self.root/'old.model.gz'; cache.write_bytes(b'SYNTHETIC CACHE')
        self.cfg['cache_import'] = {'path':str(cache),'sha256':checker.digest(cache)}; self.refresh()
        receipt = self.attempt/'cache_import.json'
        receipt.write_text(json.dumps({'source':str(cache),'sha256':checker.digest(cache)}))
        self.assertIn('model_cache',self.check())
        receipt.write_text(json.dumps({'source':str(cache),'sha256':'0'*64}))
        with self.assertRaises(ValueError): self.check()

    def test_existing_freeze_not_modified_on_failed_validation(self):
        freeze = self.root/'accepted'; freeze.mkdir()
        receipt = freeze/'independent_validation.json'; receipt.write_bytes(b'EXISTING ACCEPTANCE')
        argv = ['checker','--attempt',str(self.attempt),'--approved',str(self.approved),
            '--report',str(self.root/'failed.json'),'--freeze',str(freeze),'--config-source',str(self.config_source)]
        with patch.object(sys,'argv',argv),self.assertRaises(ValueError): checker.main()
        self.assertEqual(receipt.read_bytes(),b'EXISTING ACCEPTANCE')

    def test_report_inside_existing_or_new_freeze_rejected_before_any_write(self):
        for existing in [False,True]:
            with self.subTest(existing=existing):
                freeze = self.root/('freeze_'+str(existing))
                receipt = freeze/'independent_validation.json'
                if existing:
                    freeze.mkdir(); receipt.write_bytes(b'PREVIOUS ACCEPTANCE')
                argv = ['checker','--attempt',str(self.attempt),'--approved',str(self.approved),
                    '--report',str(receipt),'--freeze',str(freeze),'--config-source',str(self.config_source)]
                with patch.object(sys,'argv',argv),self.assertRaises(ValueError): checker.main()
                if existing: self.assertEqual(receipt.read_bytes(),b'PREVIOUS ACCEPTANCE')
                else: self.assertFalse(freeze.exists())

    def test_existing_external_report_never_overwritten(self):
        report = self.root/'previous.json'; report.write_bytes(b'PREVIOUS REPORT')
        argv = ['checker','--attempt',str(self.attempt),'--approved',str(self.approved),
            '--report',str(report),'--config-source',str(self.config_source)]
        with patch.object(sys,'argv',argv),self.assertRaises(ValueError): checker.main()
        self.assertEqual(report.read_bytes(),b'PREVIOUS REPORT')

class FreezeManifest(unittest.TestCase):
    def test_manifest_includes_report_excludes_self_without_certificate_cycle(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            scientific = root/'primary196_host_tree.nwk'; scientific.write_bytes(b'SYNTHETIC;')
            record = {'files':{'.work/freeze/primary196_host_tree.nwk':checker.digest(scientific)},'state':'COMPLETE_VALIDATED'}
            checker.write_certificate_and_manifest(root,record)
            manifest = (root/'input_output_sha256_manifest.tsv').read_text()
            self.assertIn('independent_validation.json\t',manifest)
            self.assertNotIn('input_output_sha256_manifest.tsv\t',manifest)
            self.assertEqual(json.loads((root/'independent_validation.json').read_text())['files'],record['files'])

if __name__ == '__main__':
    unittest.main()
