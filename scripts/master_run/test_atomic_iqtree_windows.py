"""Focused configuration and scientific-argument guards; no native job launch."""
import copy
from pathlib import Path
import unittest

import atomic_iqtree_windows as runner


class AtomicGuards(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            'schema':'LAB_RM_ATOMIC_IQTREE_V1','mode':'partitioned',
            'canonical_commit':'a'*40,'run_control_state':'ACTIVE_DIRECT_USER_CONTINUATION',
            'threads':2,'seed':1961008,'budget':{'cap_bytes':runner.PREFERRED_CAP,'reserve_bytes':runner.RESERVE},
            'runtime_seconds':86400,'admission_seconds':1800,
            'expected_disabled_tasks':['LAB_RM_guard_fixture_'+str(i) for i in range(18)],
            'output_directory':r'C:\atomic_guard_fixture_directory_that_must_not_exist',
        }

    def reject(self, change):
        cfg = copy.deepcopy(self.cfg); change(cfg)
        with self.assertRaises(ValueError):
            runner.validate_config(cfg)

    def test_accepted_budget_and_exact_partition_command(self):
        runner.validate_config(self.cfg)
        argv = runner.scientific_argv(self.cfg,'iqtree3.exe','accepted.faa','unique/host','accepted.nex')
        self.assertEqual(argv[argv.index('-p')+1],'accepted.nex')
        self.assertNotIn('--mem',argv)
        self.assertNotIn('--redo',argv)
        self.assertEqual(argv[argv.index('-B')+1],'1000')
        self.assertEqual(argv[argv.index('--alrt')+1],'1000')
        self.assertEqual(argv[argv.index('--seed')+1],'1961008')
        self.assertIn('-keep-ident',argv)

    def test_old_cap_not_silently_reused(self):
        self.reject(lambda c:c['budget'].update(cap_bytes=3*runner.GIB))

    def test_halted_control_cannot_launch(self):
        self.reject(lambda c:c.update(run_control_state='HALTED_BY_USER'))

    def test_unbounded_wait_or_runtime_rejected(self):
        self.reject(lambda c:c.update(admission_seconds=1801))
        self.reject(lambda c:c.update(runtime_seconds=86401))

    def test_panel_reductions_cannot_be_extra_arguments(self):
        self.reject(lambda c:c.update(extra_args=['--subset','162']))

    def test_partition_mem_incompatibility_guard(self):
        self.reject(lambda c:c.update(iqtree_memory_mib=1536))

    def test_partial_cache_requires_compatibility_certificate(self):
        self.reject(lambda c:c.update(cache_import={'path':'cache','sha256':'a'*64}))

    def test_fallback_cannot_inherit_partition_cache(self):
        self.reject(lambda c:c.update(mode='single_model',cache_import={},cache_compatibility_evidence={}))

    def test_lower_fallback_cap_needs_pinned_estimate(self):
        self.reject(lambda c:c.update(mode='single_model',budget={'cap_bytes':2*runner.GIB,'reserve_bytes':runner.RESERVE}))

    def test_single_model_changes_model_structure_only(self):
        cfg = copy.deepcopy(self.cfg); cfg['mode'] = 'single_model'
        cfg['iqtree_memory_mib'] = 2048
        cfg['budget']['cap_bytes'] = 7*runner.GIB//2
        cfg['resource_estimate_evidence'] = {'path':'independently_reviewed.json','sha256':'a'*64}
        runner.validate_config(cfg)
        argv = runner.scientific_argv(cfg,'iqtree3.exe','accepted.faa','new/host')
        self.assertNotIn('-p',argv)
        self.assertEqual(argv[argv.index('-s')+1],'accepted.faa')
        self.assertEqual(argv[argv.index('-m')+1],'MFP')
        self.assertEqual(argv[argv.index('--mem')+1],'2G')
        self.assertIn('--thread-site',argv)

    def test_disabled_task_names_are_exact_and_complete(self):
        self.reject(lambda c:c.update(expected_disabled_tasks=c['expected_disabled_tasks'][:-1]))

    def test_resource_gate_requires_physical_commit_and_both_disks(self):
        row = {'physical_available_bytes':6*runner.GIB,'commit_headroom_bytes':6*runner.GIB,
               'disk_available_bytes':{'C:':6*runner.GIB,'G:':6*runner.GIB}}
        self.assertTrue(runner.admission_passes(self.cfg,row))
        for field in ('physical_available_bytes','commit_headroom_bytes'):
            bad = copy.deepcopy(row); bad[field] -= 1
            self.assertFalse(runner.admission_passes(self.cfg,bad))
        bad = copy.deepcopy(row); bad['disk_available_bytes']['G:'] = 5*runner.GIB
        self.assertFalse(runner.admission_passes(self.cfg,bad))


if __name__ == '__main__':
    unittest.main()
