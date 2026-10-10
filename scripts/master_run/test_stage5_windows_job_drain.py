"""C-only synthetic Windows worker lifetime contracts; no actual Win32 calls."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ctypes, json, sys, tempfile, unittest
import stage5_unc_bind_probe as U

class Clock:
    def __init__(self):self.now=0
    def read(self):return self.now
    def sleep(self,seconds):self.now+=max(seconds,.001)

EMPTY={'job_active_processes':0,'job_pids':[]}
class ClosedError(RuntimeError):pass

def atomic(path,value):
    Path(path).write_text(json.dumps(value),encoding='utf-8')

class Process(ctypes.Structure):
    _fields_=[('hProcess',ctypes.c_void_p),('hThread',ctypes.c_void_p),('dwProcessId',ctypes.c_uint32)]
class Basic(ctypes.Structure):
    _fields_=[('LimitFlags',ctypes.c_uint32),('ActiveProcessLimit',ctypes.c_uint32)]
class Extended(ctypes.Structure):_fields_=[('BasicLimitInformation',Basic)]
class Startup(ctypes.Structure):_fields_=[('cb',ctypes.c_uint32)]

class Fake:
    PROCESS=Process;EXTENDED=Extended;STARTUP=Startup
    def __init__(self,evidence,states=None):
        self.evidence=evidence;self.states=list(states or [EMPTY]);self.closed=[];self.terminated=[];self.identities=0;self.exitcode=0
    def ok(self,okay,message):
        if not okay:raise OSError(message)
    def create_job(self,*args):return 5
    def set_job(self,*args):return True
    def create(self,*args):
        target=args[-1]._obj;target.hProcess=11;target.hThread=12;target.dwProcessId=99;return True
    def identity(self,*args):
        self.identities+=1
        return dict(pid=99,creation_filetime=1,exit_filetime=2 if self.identities>1 else 0,
            exited=self.identities>1,exit_code=self.exitcode if self.identities>1 else None,
            executable=sys.executable,session_id=1)
    def assign(self,*args):return True
    def resume(self,*args):return 1
    def wait(self,*args):return 0
    def job_state(self,*args):
        if self.evidence:assert (self.evidence/'root_exit.json').is_file(),'Root terminal must precede first job drain'
        value=self.states.pop(0) if len(self.states)>1 else self.states[0]
        if isinstance(value,BaseException):raise value
        return value
    def terminate_job(self,*args):self.terminated.append(args[0]);return True
    def terminate(self,*args):self.terminated.append(args[0]);return True
    def close(self,handle):self.closed.append(handle);return True

class Contracts(unittest.TestCase):
    def drain(self,states,timeout=.1):
        api=Fake(None,states);clock=Clock();record={'drain_samples':[]}
        out=U.drain_windows_job(api,5,11,record,lambda _:None,timeout,clock.read,clock.sleep)
        return out,record
    def test_root_exit_with_surviving_descendant_then_empty(self):
        result,record=self.drain([{'job_active_processes':1,'job_pids':[21836]},EMPTY])
        self.assertEqual(result,EMPTY);self.assertEqual(len(record['drain_samples']),2)
    def test_query_error_diagnostic_preserved_then_full_empty(self):
        result,record=self.drain([OSError('Synthetic query failure'),EMPTY])
        self.assertIn('error',record['drain_samples'][0]);self.assertEqual(result,EMPTY)
    def test_accounting_empty_with_nonempty_pid_list_is_not_closure(self):
        _,record=self.drain([{'job_active_processes':0,'job_pids':[99]},EMPTY])
        self.assertEqual(len(record['drain_samples']),2)
    def test_deadline_rejects_nonempty_job(self):
        with self.assertRaisesRegex(ValueError,'drain exceeded'):
            self.drain([{'job_active_processes':1,'job_pids':[99]}])
    def fixture(self,callback):
        with tempfile.TemporaryDirectory(dir=U.WINDOWS_WORK,prefix='windows_job_pure_') as d:
            evidence=Path(d)/'worker';api=Fake(evidence,[{'job_active_processes':1,'job_pids':[98]},EMPTY])
            module=SimpleNamespace(atomic=atomic,OwnedClosureFailure=ClosedError)
            with patch.object(U,'load_pinned',return_value=module):return callback(api,evidence)
    def test_launch_terminal_and_empty_receipts_durable_before_close(self):
        def run(api,path):
            result=U.windows_job(api,[sys.executable,'-B','-c','pass'],{'session_id':1},path)
            self.assertTrue((path/'launch.json').is_file());self.assertTrue((path/'root_exit.json').is_file())
            self.assertTrue(result['owned_closure_proven']);self.assertTrue(result['job_name'].startswith('Local\\LAB_RM_STAGE5_IO_'))
            self.assertEqual(api.closed,[12,11,5]);self.assertEqual(len(result['drain_samples']),2)
        self.fixture(run)
    def test_closed_nonzero_preserves_original_error_and_failed_receipt(self):
        def run(api,path):
            api.exitcode=2
            with self.assertRaisesRegex(ValueError,'exited nonzero'):
                U.windows_job(api,[sys.executable],{'session_id':1},path)
            value=json.loads((path/'result.json').read_bytes())
            self.assertEqual(value['state'],'FAILED');self.assertTrue(value['owned_closure_proven'])
            self.assertIn('nonzero',value['original_error']['message'])
        self.fixture(run)
    def test_unknown_job_raises_fatal_and_preserves_primary_error(self):
        def run(api,path):
            with patch.object(U,'drain_windows_job',side_effect=OSError('Synthetic underlying job query failure')):
                with self.assertRaises(ClosedError):U.windows_job(api,[sys.executable],{'session_id':1},path)
            value=json.loads((path/'result.json').read_bytes())
            self.assertFalse(value['owned_closure_proven']);self.assertEqual(api.terminated,[5])
            self.assertIn('underlying',value['original_error']['message']);self.assertIn('closure_error',value)
        self.fixture(run)
    def test_result_write_failure_does_not_mask_unknown_closure(self):
        def run(api,path):
            def failing(p,value):
                if p.name=='result.json':raise OSError('Synthetic final disk failure')
                atomic(p,value)
            module=SimpleNamespace(atomic=failing,OwnedClosureFailure=ClosedError)
            with patch.object(U,'load_pinned',return_value=module),patch.object(U,'drain_windows_job',side_effect=OSError('query')):
                with self.assertRaises(ClosedError):U.windows_job(api,[sys.executable],{'session_id':1},path)
        self.fixture(run)
    def test_unexpected_resume_count_never_accepted(self):
        def run(api,path):
            api.resume=lambda *_:0
            with self.assertRaisesRegex(ValueError,'suspend count'):
                U.windows_job(api,[sys.executable],{'session_id':1},path)
            value=json.loads((path/'result.json').read_bytes())
            self.assertEqual(value['state'],'FAILED');self.assertTrue(value['owned_closure_proven'])
            self.assertEqual(api.terminated,[5])
        self.fixture(run)
    def test_missing_actual_exit_time_is_fatal_unproven(self):
        def run(api,path):
            original=api.identity
            def bad(*args):
                value=original(*args)
                if value['exited']:value['exit_filetime']=0
                return value
            api.identity=bad
            with self.assertRaises(ClosedError):U.windows_job(api,[sys.executable],{'session_id':1},path)
            self.assertFalse(json.loads((path/'result.json').read_bytes())['owned_closure_proven'])
        self.fixture(run)

if __name__=='__main__':unittest.main()
