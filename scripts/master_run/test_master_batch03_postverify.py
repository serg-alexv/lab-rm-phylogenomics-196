"""Focused synthetic journal contracts. No actual post-purge verification."""
import copy,os,subprocess,unittest
import verify_master_batch03_leaf_purge as v

ROW={'path':'C:\\fixture','bytes':3,'sha256':'a'*64,'device':17766949232488609743,'file_id':844424932788104,'mtime_ns':1791460058061945600}
def events():
    intent={'event':'VERIFIED_INTENT','line':4,**{k:ROW[k] for k in ('path','bytes','sha256')},
            **{k:str(ROW[k]) for k in ('device','file_id','mtime_ns')}}
    outcome={'event':'REMOVED','line':4,**{k:ROW[k] for k in ('path','bytes','sha256')},'deleted':1,'deleted_bytes':3}
    return [intent,outcome]
def join(rows):
    it=iter(rows);return v.join_candidate(lambda:next(it),ROW,4,0,0)

class JournalContracts(unittest.TestCase):
    def test_exact_pair(self):self.assertEqual(join(events())[1]['event'],'REMOVED')
    def test_forged_or_reordered_intent(self):
        for key,value in [('path','C:\\other'),('sha256','b'*64),('line',5),('device','2430728143')]:
            rows=events();rows[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):join(rows)
        with self.assertRaises(ValueError):join(list(reversed(events())))
    def test_outcome_cannot_detach_or_duplicate(self):
        for key,value in [('path','C:\\other'),('sha256','b'*64),('deleted',2),('deleted_bytes',4),('event','VERIFIED_INTENT')]:
            rows=events();rows[1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):join(rows)
    def test_stop_before_or_after_intent_preserves_uncertainty(self):
        stop={'event':'STOP','state':'FAILED_PARTIAL_PRESERVE_REMAINDER'}
        self.assertIsNone(join([stop])[0]);self.assertEqual(join([events()[0],stop])[1],stop)
    def test_complete_exact_accounting(self):
        t={'event':'COMPLETE','state':'PASS_EXACT_47429_COLD_LEAVES_REMOVED','deleted':1,'deleted_bytes':3,
           'held_files':219,'unmatched_preserved':619,'recursive_deletes':0}
        v.check_complete(t,1,3,1,3)
        for key,value in [('deleted',2),('deleted_bytes',4),('held_files',0),('recursive_deletes',1),('event','STOP')]:
            bad=copy.deepcopy(t);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):v.check_complete(bad,1,3,1,3)
    @unittest.skipUnless(os.name=='nt','Windows retained-handle fixture only')
    def test_actual_retained_self_process_birth(self):
        # Independent .NET birth readback confirms full-resolution Win32 handle identity.
        result=subprocess.run(['pwsh','-NoProfile','-Command',
            f'[Diagnostics.Process]::GetProcessById({os.getpid()}).StartTime.ToUniversalTime().ToFileTimeUtc().ToString()'],
            capture_output=True,text=True,check=True,timeout=20)
        birth=int(result.stdout.strip());owner=v.Owners(((os.getpid(),birth),))
        try:self.assertEqual(owner.check()[0]['creation_filetime'],str(birth))
        finally:owner.close()
        with self.assertRaises(ValueError):v.Owners(((os.getpid(),birth+1),))

if __name__=='__main__':unittest.main()
