"""Pure syscall error contracts and C-only own temporary fixture; no WSL/G."""
from pathlib import Path
import json, os, tempfile, unittest
import stage5_owner_lease as V


def win_error(code):
    value=OSError('SYNTHETIC WINDOWS REPLACE ERROR');value.winerror=code;return value


class FakeClock:
    def __init__(self):self.now=0.;self.sleeps=[]
    def clock(self):return self.now
    def sleep(self,seconds):self.sleeps.append(seconds);self.now+=seconds


class Contracts(unittest.TestCase):
    def test_transient_5_32_33_retry_same_owned_pair_then_success(self):
        clock=FakeClock();stats={};calls=[];errors=[5,32,33]
        def replace(source,target):
            calls.append((source,target))
            if errors:raise win_error(errors.pop(0))
        V._replace_owned('OWN_TEMP','OWN_LEASE',stats,replace,clock.clock,clock.sleep)
        self.assertEqual(calls,[('OWN_TEMP','OWN_LEASE')]*4);self.assertEqual(stats['retries'],3)
        self.assertEqual(stats['transient_winerrors'],{'5':1,'32':1,'33':1});self.assertLess(clock.now,.250)

    def test_persistent_transient_stops_at_250ms_no_attempt_after_deadline(self):
        clock=FakeClock();stats={};attempt_times=[]
        def denied(*args):attempt_times.append(clock.now);raise win_error(5)
        with self.assertRaises(V.LeaseReplaceDeadlineExceeded):
            V._replace_owned('OWN_TEMP','OWN_LEASE',stats,denied,clock.clock,clock.sleep)
        self.assertLessEqual(clock.now,.250);self.assertTrue(all(t<.250 for t in attempt_times))
        self.assertEqual(stats['last_replace_attempts'],len(attempt_times));self.assertGreater(stats['transient_failures'],0)
        self.assertEqual(stats['retries'],len(attempt_times)-1)

    def test_fatal_errno_and_unrelated_winerror_never_retry(self):
        for error in (win_error(112),PermissionError('SYNTHETIC NO_WINERROR'),ValueError('SYNTHETIC SERIALIZER')):
            with self.subTest(error=error):
                clock=FakeClock();stats={};calls=[]
                def denied(*args):calls.append(args);raise error
                with self.assertRaises(type(error)):V._replace_owned('OWN_TEMP','OWN_LEASE',stats,denied,clock.clock,clock.sleep)
                self.assertEqual(len(calls),1);self.assertEqual(clock.sleeps,[]);self.assertEqual(stats['last_replace_retries'],0)

    def test_actual_c_owned_lease_bytes_and_no_orphan_temp(self):
        with tempfile.TemporaryDirectory(prefix='lease_fixture_',dir=V.WORK) as tmp:
            root=Path(tmp);path=root/'owner_lease.json';stats={}
            value={'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1','nonce':'SYNTHETIC_ONLY','workflow_lock_held':False}
            V.atomic_owner_lease(path,value,stats);value['measured_unix']=123.;V.atomic_owner_lease(path,value,stats)
            self.assertEqual(json.loads(path.read_bytes()),value);self.assertEqual(stats['successful_calls'],2)
            self.assertEqual([p.name for p in root.iterdir()],['owner_lease.json']);self.assertNotIn(b'\r',path.read_bytes())

    def test_other_filename_and_outside_work_refused_before_write(self):
        with tempfile.TemporaryDirectory(prefix='lease_fixture_',dir=V.WORK) as tmp:
            path=Path(tmp)/'other.json'
            with self.assertRaises(ValueError):V.atomic_owner_lease(path,{'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1'},{})
            self.assertFalse(path.exists())
        with self.assertRaises(ValueError):
            V.atomic_owner_lease(Path(r'G:\NOT_A_TARGET\owner_lease.json'),{'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1'},{})


if __name__=='__main__':unittest.main()
