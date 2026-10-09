"""Pure synthetic population gates; no WSL, host API, lock or configuration I/O."""
from pathlib import Path
from unittest.mock import patch
import contextlib, copy, hashlib, io, unittest
import apply_scoped_wsl_resource_repair as R

ROOT_UID = 'Uid:\t0\t0\t0\t0'


def row(pid, ppid, comm, executable, ticks=None, uid=ROOT_UID):
    return dict(pid=pid, ppid=ppid, comm=comm, executable=executable,
                start_ticks=str(ticks or pid * 10), uid_record=uid, state='S')


def fixture():
    baseline = [row(1, 0, 'systemd', '/usr/lib/systemd/systemd'),
                row(2, 1, 'init-systemd(Ub', '/init'),
                row(93, 1, 'systemd-udevd', '/usr/bin/udevadm'),
                row(223, 1, 'supervisord', '/usr/bin/python3.14'),
                row(371, 2, 'login', '/usr/bin/login'),
                row(448, 371, 'bash', '/usr/bin/bash')]
    prior = {'self_pid': 638, 'processes': baseline + [
        row(632, 2, 'SessionLeader', '/init'),
        row(634, 632, 'Relay(638)', '/init'),
        row(638, 634, 'python3', '/usr/bin/python3.14')]}
    fresh = {'self_pid': 1003, 'processes': copy.deepcopy(baseline) + [
        row(1001, 2, 'SessionLeader', '/init'),
        row(1002, 1001, 'Relay(1003)', '/init'),
        row(1003, 1002, 'python3', '/usr/bin/python3.14'),
        row(1004, 93, '(udev-worker)', '/usr/bin/udevadm')]}
    return fresh, prior


class PopulationContracts(unittest.TestCase):
    def test_exact_observer_transport_and_known_service_worker_pass(self):
        fresh, prior = fixture()
        value = R.guarded_population(fresh, prior)
        self.assertEqual(value['observation_transport_pids'], [1001, 1002, 1003])
        self.assertFalse(value['atomic_no_jobs_claim'])
        self.assertIn('login/bash', value['known_baseline_processes'])

    def test_extra_new_transport_or_session_is_not_exempt(self):
        for extra in (row(2001, 2, 'SessionLeader', '/init'),
                      row(2002, 1001, 'Relay(2003)', '/init')):
            fresh, prior = fixture(); fresh['processes'].append(extra)
            with self.subTest(comm=extra['comm']), self.assertRaises(ValueError):
                R.guarded_population(fresh, prior)

    def test_unknown_executable_or_compute_process_rejects(self):
        for extra in (row(2004, 1, 'SessionLeader', '/usr/bin/sleep'),
                      row(2005, 1, 'iqtree3', '/opt/SYNTHETIC/iqtree3')):
            fresh, prior = fixture(); fresh['processes'].append(extra)
            with self.subTest(comm=extra['comm']), self.assertRaises(ValueError):
                R.guarded_population(fresh, prior)

    def test_known_process_reparent_birth_and_uid_drift_reject(self):
        for key, value in (('ppid', 2), ('start_ticks', '999999'),
                           ('uid_record', 'Uid:\t1000\t1000\t1000\t1000')):
            fresh, prior = fixture()
            target = next(x for x in fresh['processes'] if x['pid'] == 448)
            target[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                R.guarded_population(fresh, prior)

    def test_observer_ancestry_uid_and_interpreter_drift_reject(self):
        for pid, key, value in ((1001, 'ppid', 1), (1002, 'comm', 'Relay(OTHER)'),
                               (1001, 'uid_record', 'Uid:\t1000\t1000\t1000\t1000'),
                               (1003, 'executable', '/OTHER/python')):
            fresh, prior = fixture()
            next(x for x in fresh['processes'] if x['pid'] == pid)[key] = value
            with self.subTest(pid=pid, field=key), self.assertRaises(ValueError):
                R.guarded_population(fresh, prior)

    def test_udev_worker_unknown_parent_uid_or_parent_birth_reject(self):
        for pid, key, value in ((1004, 'ppid', 999),
                               (1004, 'uid_record', 'Uid:\t1000\t1000\t1000\t1000'),
                               (93, 'start_ticks', '999999')):
            fresh, prior = fixture()
            next(x for x in fresh['processes'] if x['pid'] == pid)[key] = value
            with self.subTest(pid=pid, field=key), self.assertRaises(ValueError):
                R.guarded_population(fresh, prior)

    def test_prepared_configuration_changes_only_exact_memory_ceiling(self):
        before = (R.O/'wslconfig.before.txt').read_bytes()
        after = (R.O/'wslconfig.after.txt').read_bytes()
        self.assertEqual(before.count(b'memory=6GB'), 1)
        self.assertEqual(after, before.replace(b'memory=6GB', b'memory=4GB'))
        self.assertEqual(hashlib.sha256(before).hexdigest(), R.PINS[R.CONFIG])
        self.assertEqual(hashlib.sha256(after).hexdigest(), R.PINS[R.O/'wslconfig.after.txt'])

    def test_default_cannot_open_lock_query_host_or_launch(self):
        with patch('sys.argv', ['synthetic']), patch.object(R.A, 'Win', side_effect=AssertionError), \
             patch.object(R.A, 'WorkflowLock', side_effect=AssertionError), \
             patch.object(R.subprocess, 'Popen', side_effect=AssertionError), \
             contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(R.main(), 0)
        self.assertIn('PREPARED_NO_CONFIG_CHANGE', stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
