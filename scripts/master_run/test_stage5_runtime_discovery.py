"""Control/dispatch tests only. No Linux runtime, WSL, native or G access."""
from pathlib import Path
from unittest import mock
import contextlib
import io
import json
import tempfile
import unittest
import stage5_runtime_discovery as D


class DiscoveryContracts(unittest.TestCase):
    def test_default_plan_never_imports_runner_or_dispatches(self):
        capture = io.StringIO()
        with mock.patch.object(D, 'discover', side_effect=AssertionError('No dispatch')), \
             mock.patch.object(D.importlib, 'import_module', side_effect=AssertionError('No import')), \
             contextlib.redirect_stdout(capture):
            self.assertEqual(D.main([]), 0)
        value = json.loads(capture.getvalue())
        self.assertEqual(value['state'], 'PREPARED_NOT_RUN')
        self.assertEqual(value['native_execution'], 'NOT_RUN')

    def test_modified_control_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(D, 'PINS', {'stage5_atomic.py': '0' * 64}):
                (root / 'stage5_atomic.py').write_text('raise RuntimeError("Do not import")')
                with self.assertRaisesRegex(ValueError, 'changed reviewed discovery input'):
                    D.controls(root)

    def test_discovery_is_linux_only_before_import_or_output(self):
        with mock.patch.object(D.sys, 'platform', 'win32'), \
             mock.patch.object(D.importlib, 'import_module', side_effect=AssertionError('No import')):
            with self.assertRaisesRegex(ValueError, 'mounted retained Linux'):
                D.discover(Path('.'), {}, '/forbidden/path.json')

    def test_output_rejects_other_roots_and_traversal(self):
        for path in ['/var/tmp/stage5_runtime_actual_01.json',
                     str(D.WORK / '..' / 'stage5_runtime_actual_01.json'),
                     str(D.WORK / 'nested' / 'stage5_runtime_actual_01.json'),
                     str(D.WORK / 'complete.json')]:
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'direct C-work'):
                D.output_path(path)


if __name__ == '__main__':
    unittest.main()
