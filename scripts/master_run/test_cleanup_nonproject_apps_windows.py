import copy, importlib.util, unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('cleanup',Path(__file__).with_name('cleanup_nonproject_apps_windows.py'))
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

def plan():
    return {'schema':M.SCHEMA,'source_sha256':'source','api_sha256':M.API_SHA,
        'executables':{M.CHROME:{'sha256':'a'},M.MEDIA:{'sha256':'b'}},
        'processes':[{'pid':pid,'executable':exe,'creation_filetime':M.cim_microseconds(date)*10,
            'session_id':1,'exited':False,'exit_filetime':0,'exit_code':None} for pid,exe,date in M.OBSERVED]}

class Fake:
    def __init__(self,p):self.p=p;self.killed=[];self.closed=[];self.live={r['pid']:True for r in p['processes']};self.bad=None;self.timeout=False
    def process(self,pid,run=False):return ('retained',pid)
    def executable(self,exe):return ('file',exe),copy.deepcopy(self.p['executables'][exe])
    def identity(self,h,row):
        out=copy.deepcopy(row);out.update(exited=not self.live[row['pid']],exit_filetime=0 if self.live[row['pid']] else row['creation_filetime']+100,exit_code=None if self.live[row['pid']] else 1)
        if self.bad and self.bad[0]==row['pid']:out[self.bad[1]]=self.bad[2]
        return out
    def terminate(self,h):self.killed.append(h);self.live[h[1]]=False
    def wait(self,h,ms):return 258 if self.timeout else 0
    def close(self,h):self.closed.append(h)
    def resources(self):return {'physical_available_bytes':1,'commit_headroom_bytes':2}

class Contracts(unittest.TestCase):
    def test_exact_plan(self):self.assertEqual(len(M.validate_plan(plan(),'source')),9)
    def test_wrong_source_and_added_target_rejected(self):
        p=plan()
        with self.assertRaises(ValueError):M.validate_plan(p,'wrong')
        p['processes'].append(dict(p['processes'][0],pid=5))
        with self.assertRaises(ValueError):M.validate_plan(p,'source')
    def test_unapproved_image_rejected(self):
        p=plan();p['processes'][0]['executable']='Codex.exe'
        with self.assertRaises(ValueError):M.validate_plan(p,'source')
    def test_reused_birth_aborts_before_any_action(self):
        p=plan();n=Fake(p);n.bad=(14764,'creation_filetime',1)
        out=M.execute(n,p,{},lambda _:None)
        self.assertEqual(out['state'],'FAILED_PRESERVED');self.assertEqual(n.killed,[])
    def test_changed_image_aborts_before_any_action(self):
        p=plan();n=Fake(p);n.bad=(25800,'executable','Codex.exe')
        M.execute(n,p,{},lambda _:None);self.assertEqual(n.killed,[])
    def test_success_only_exact_retained_handles_parent_last(self):
        p=plan();n=Fake(p);out=M.execute(n,p,{},lambda _:None)
        self.assertEqual(out['state'],'PASS_EXACT_CAPTURED9_RETAINED_HANDLES_CLOSED')
        self.assertEqual(set(n.killed),{('retained',r['pid']) for r in p['processes']})
        self.assertEqual(n.killed[-1],('retained',14764));self.assertTrue(all(r['closure_proven'] for r in out['targets']))
    def test_wait_timeout_stops_remaining_actions(self):
        p=plan();n=Fake(p);n.timeout=True;out=M.execute(n,p,{},lambda _:None)
        self.assertEqual(out['state'],'FAILED_PRESERVED');self.assertEqual(len(n.killed),1)
        self.assertNotIn('closure_proven',out['targets'][0])
    def test_wrong_executable_file_identity_prevents_actions(self):
        p=plan();n=Fake(p);n.executable=lambda exe:(('file',exe),{'sha256':'changed'})
        M.execute(n,p,{},lambda _:None);self.assertEqual(n.killed,[])
    def test_journal_failure_before_action_preserves_every_target(self):
        p=plan();n=Fake(p)
        def fail(_):raise OSError('fixture receipt failure')
        with self.assertRaises(OSError):M.execute(n,p,{},fail)
        self.assertEqual(n.killed,[])

if __name__=='__main__':unittest.main()
