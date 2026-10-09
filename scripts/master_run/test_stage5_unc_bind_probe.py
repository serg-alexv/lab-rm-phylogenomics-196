"""Pure request/scope/default safety checks; no WSL, UNC, mount or file writes."""
import contextlib
import copy
import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
import stage5_unc_bind_probe as p


def request():
    return dict(schema='STAGE05_UNC_BIND_PROBE_REQUEST_V1', scope=p.SCOPE, nonce='a' * 32,
                root=p.ROOT, target=p.TARGET, unc=str(p.UNC), expected_python=p.ENV + '/bin/python',
                source_pins=copy.deepcopy(p.PINS), sentinel_name='.unc_visibility_' + 'a' * 32,
                linux_payload_hex=(b'L' * 96).hex(), windows_payload_hex=(b'W' * 96).hex())


class Contracts(unittest.TestCase):
    def test_exact_endpoint_and_distinct_tiny_payloads(self):
        p.validate_request(request())
        self.assertEqual(str(p.UNC), r'\\wsl.localhost\Ubuntu\mnt\g\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage05_atomic_v1')

    def test_alias_outside_scope_or_runtime_rejected(self):
        for key, value in [('nonce', '../outside'), ('root', '/mnt/c'), ('target', p.TARGET + '/elsewhere'),
                           ('unc', r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage05_atomic_v1'),
                           ('expected_python', '/usr/bin/python3'), ('sentinel_name', '.unc_visibility_../outside'),
                           ('source_pins', {})]:
            value_request = request(); value_request[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                p.validate_request(value_request)

    def test_payload_bounds_and_bidirectional_difference(self):
        for raw in (b'', b'x' * 63, b'x' * 513, b'W' * 96):
            value = request(); value['linux_payload_hex'] = raw.hex()
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                p.validate_request(value)

    def test_default_plan_does_not_start_child_or_touch_unc(self):
        stdout = io.StringIO()
        with (patch('sys.argv', ['probe']), patch.object(p, 'windows_owner', side_effect=AssertionError('No execution')),
                patch.object(p.subprocess, 'Popen', side_effect=AssertionError('No WSL')),
                contextlib.redirect_stdout(stdout)):
            self.assertEqual(p.main(), 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result['state'], 'PREPARED_NOT_RUN')
        self.assertFalse(result['scientific_adoption_authorized'])

    def test_internal_steps_require_explicit_run_before_any_io(self):
        for mode in ('windows-io', 'linux-prepare', 'linux-finalize'):
            with (self.subTest(mode=mode), patch('sys.argv', ['probe', '--mode', mode]),
                    patch.object(p, 'read_request', side_effect=AssertionError('Must refuse before I/O')),
                    self.assertRaisesRegex(ValueError, 'explicit --run')):
                p.main()

    def test_nonempty_underlay_fails_after_first_entry_without_traversal(self):
        def entries():
            yield object()
            raise AssertionError('Must not enumerate any further unknown files')
        scanner = MagicMock(); scanner.__enter__.return_value = entries()
        with (patch.object(p.Path, 'lstat', return_value=SimpleNamespace(st_file_attributes=0)),
                patch.object(p.Path, 'is_symlink', return_value=False),
                patch.object(p.Path, 'is_dir', return_value=True),
                patch.object(p.os, 'scandir', return_value=scanner) as scan,
                self.assertRaisesRegex(ValueError, 'must be empty')):
            p.underlay_snapshot()
        scan.assert_called_once_with(p.G_UNDERLAY)

    def test_unavailable_underlay_is_never_accepted_as_empty(self):
        with (patch.object(p.Path, 'lstat', return_value=SimpleNamespace(st_file_attributes=0)),
                patch.object(p.Path, 'is_symlink', return_value=False),
                patch.object(p.Path, 'is_dir', return_value=True),
                patch.object(p.os, 'scandir', side_effect=OSError('Unavailable underlay')),
                self.assertRaises(OSError)):
            p.underlay_snapshot()


if __name__ == '__main__':
    unittest.main()
