"""Opt-in actual Linux lifecycle fixture. NOT_RUN in the Windows BUILD audit.

No biological inputs, detectors, HMMs or model databases. Run after Stage4 only.
"""
from pathlib import Path
from types import SimpleNamespace
import json, os, subprocess, sys, tempfile, time, unittest
import stage5_atomic as R
from stage5_atomic_process import Supervisor, Retryable, atomic_json


@unittest.skipUnless(sys.platform == 'linux' and os.environ.get('STAGE5_LIVE_PROCESS_FIXTURE') == '1',
                     'Requires explicit Linux-only synthetic lifecycle execution')
class NativeLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stage5_live_synthetic_', dir=Path(__file__).parent)
        self.root = Path(self.temp.name)
        self.lease = self.root / 'lease.json'
        now = time.time()
        atomic_json(self.lease, {'schema': 'STAGE05_WINDOWS_OWNER_LEASE_V1', 'nonce': 'SYNTHETIC_ONLY',
                    'workflow_lock_held': True, 'owner_pid': 1, 'owner_creation_filetime': '1',
                    'measured_unix': now, 'expires_unix': now + 30,
                    'windows_available_bytes': 2**50, 'windows_commit_headroom_bytes': 2**50,
                    'disk_available_bytes': {'SYNTHETIC_ONLY_WINDOWS_VOLUME': 2**50},
                    'scope': 'Explicit synthetic lease; does not establish real Windows lock ownership'})
        self.policy = {'windows_reserve_bytes': 1, 'incremental_windows_requirement_bytes': 1,
                       'commit_requirement_bytes': 1, 'linux_job_requirement_bytes': 1,
                       'linux_reserve_bytes': 1, 'minimum_disk_free_bytes': 1, 'resource_wait_seconds': 0,
                       'lease_max_age_seconds': 30, 'command_timeout_seconds': 1,
                       'sampled_rss_stop_bytes': 2**30, 'termination_grace_seconds': 0.5, 'drain_timeout_seconds': 2}
        self.supervisor = Supervisor(self.lease, 'SYNTHETIC_ONLY', self.policy, self.root, R.sha)
        self.args = SimpleNamespace(output=self.root, environment=dict(os.environ))

    def tearDown(self):
        self.temp.cleanup()

    def execute(self, code):
        return self.supervisor.execute(self.args, self.root / 'attempt', 'synthetic',
                                       [sys.executable, '-B', '-c', code], self.root, {'fixture': True})

    def test_normal_actual_root_and_group_exit(self):
        receipt = self.execute("print('SYNTHETIC_NORMAL')")
        self.assertEqual(receipt['exit_code'], 0)
        self.supervisor.assert_closed(json.loads((self.root / 'attempt/synthetic.launch.json').read_text()))

    def test_root_exit_cleans_grandchild_and_preserves_unrelated_control(self):
        control = subprocess.Popen([sys.executable, '-B', '-c', 'import time; time.sleep(30)'], start_new_session=True)
        # It is an existing child when the supervised command's baseline is taken.
        try:
            with self.assertRaises(Retryable):
                self.execute("import subprocess,sys,time; subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(30)']); time.sleep(.1)")
            self.assertIsNone(control.poll())
            closure = json.loads((self.root / 'attempt/synthetic.closure.json').read_text())
            self.assertTrue(closure['group_empty'] and closure['tracked_descendants_empty'])
        finally:
            control.terminate(); control.wait(timeout=5)

    def test_runtime_timeout_drains_actual_group(self):
        with self.assertRaises(Retryable):
            self.execute('import time; time.sleep(30)')
        closure = json.loads((self.root / 'attempt/synthetic.closure.json').read_text())
        self.assertTrue(closure['group_empty'] and closure['tracked_descendants_empty'])
        self.assertIsNotNone(closure['root_exit_code'])


if __name__ == '__main__':
    unittest.main()
