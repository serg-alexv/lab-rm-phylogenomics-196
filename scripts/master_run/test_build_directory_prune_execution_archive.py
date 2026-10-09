"""Pure source/default/allowlist tests; no native source reads or archive build."""
from pathlib import Path
import contextlib
import importlib.util
import io
import json
import sys
import time
import unittest

SOURCE = Path(__file__).with_name('build_directory_prune_execution_archive.py')
spec = importlib.util.spec_from_file_location('execution_archive_prepared', SOURCE)
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


class BuildTests(unittest.TestCase):
    def test_each_resource_reserve_matches_live_job_policy(self):
        self.assertEqual(B.MIN_HEADROOM, 1536 * 1024**2)
        class Kernel:
            def __init__(self, physical, commit):
                self.physical, self.commit = physical, commit
            def GlobalMemoryStatusEx(self, pointer):
                pointer._obj.physical_available = self.physical
                pointer._obj.pagefile_available = self.commit
                return True
            def GetCurrentProcess(self):
                return 1
            def GetPriorityClass(self, handle):
                return 0x4000
        budget = B.Budget.__new__(B.Budget)
        budget.start = time.monotonic()
        for physical, commit in ((B.MIN_HEADROOM - 1, B.MIN_HEADROOM),
                                 (B.MIN_HEADROOM, B.MIN_HEADROOM - 1)):
            budget.k = Kernel(physical, commit)
            with self.assertRaises(ValueError):
                budget.check()
        budget.k = Kernel(B.MIN_HEADROOM, B.MIN_HEADROOM)
        self.assertEqual(budget.check()['physical_available_bytes'], B.MIN_HEADROOM)

    def test_default_does_not_instantiate_native_or_build(self):
        prior, budget, capture = sys.argv, B.Budget, B.Capture
        try:
            sys.argv = ['builder']
            B.Budget = B.Capture = lambda *args: self.fail('Default instantiated native capture')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(B.main(), 0)
            self.assertEqual(json.loads(output.getvalue())['state'], 'PREPARED_NO_BUILD_NO_DELETE')
        finally:
            sys.argv, B.Budget, B.Capture = prior, budget, capture

    def test_member_paths_are_literal_relative_posix(self):
        self.assertEqual(B.canonical('nested/receipt.json'), 'nested/receipt.json')
        for name in ('../file', '/file', 'C:/file', 'nested\\file', 'nested//file', 'nested/./file', 'name.', 'name '):
            with self.subTest(name=name), self.assertRaises(ValueError):
                B.canonical(name)

    def test_archive_namespace_is_exact_current_c(self):
        self.assertEqual(B.OUT.parent, B.WORK)
        self.assertEqual(B.OUT.name, 'master_directory_prune_execution01')

    def test_original_fixed_journal_plan_authority_are_frozen(self):
        self.assertEqual(B.FIXED[B.JOURNAL], '5ff92323b29af9a6620a251825ea6531e95bbf14ef2ff6c3d36279beb891f4a5')
        self.assertEqual(B.FIXED['master_old_scientific_emptydirs_proposed_02.json'], 'be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5')
        self.assertEqual(B.FIXED['master_directory_prune_root_authority01.json'], '0afeb4c2a06b4920765466474f354ed0638a228c450eb17a1c1acc9ee7bfbe63')

    def test_both_first_failures_are_in_selected_declarations(self):
        self.assertIn('directory_handle_pruner_preparation_completion_02.json', B.DECLARATIONS)
        self.assertIn('directory_prune_postverify_20261009T212934Z_35de2767/receipt.json', B.CORRECTION_NAMES)
        self.assertIn('verify_directory_handle_prune_attempt01.py', B.CORRECTION_NAMES)

    def test_zip_metadata_is_deterministic_regular_unencrypted(self):
        info = B.zip_info('fixed/file.json')
        self.assertEqual(info.date_time, (2026, 10, 9, 0, 0, 0))
        self.assertEqual(info.external_attr >> 16, 0o100644)
        self.assertFalse(info.extra or info.comment or info.flag_bits & 1)


if __name__ == '__main__':
    unittest.main()
