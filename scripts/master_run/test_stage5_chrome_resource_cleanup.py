"""Small pure/fake cleanup guards; never enumerate or close actual processes."""
import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch
import stage5_chrome_resource_cleanup as C


class CleanupGuards(unittest.TestCase):
    def birth(self):
        return {'pid':77,'creation_filetime':1234,'executable':C.CHROME_EXE,
                'session_id':3,'exited':False,'exit_code':None,'exit_filetime':0}

    def test_exact_current_session_chrome(self):
        self.assertEqual(C.target_guard(self.birth(),3)['pid'],77)
        self.assertEqual(C.target_guard(dict(self.birth(),executable=C.CHROME_EXE.lower()),3)['pid'],77)

    def test_other_executables_and_sessions_veto(self):
        for exe in ('chrome.exe',r'C:\Users\wheel\chrome.exe',r'C:\Program Files\ChatGPT\ChatGPT.exe',
                    r'C:\Program Files\Google\Drive File Stream\DriveFS.exe',C.CHROME_EXE+'.other'):
            with self.assertRaises(ValueError):C.target_guard(dict(self.birth(),executable=exe),3)
        with self.assertRaises(ValueError):C.target_guard(self.birth(),4)

    def test_birth_identity_types_veto(self):
        for key,value in (('pid',True),('pid',77.0),('creation_filetime',1234.0),('creation_filetime',0),('session_id',True)):
            with self.assertRaises(ValueError):C.target_guard(dict(self.birth(),**{key:value}),3)

    def test_positive_terminal(self):
        terminal=dict(self.birth(),exited=True,exit_code=1223,exit_filetime=1235)
        self.assertEqual(C.terminal_guard(self.birth(),terminal,3),terminal)

    def test_reused_pid_or_missing_positive_terminal_veto(self):
        terminal=dict(self.birth(),exited=True,exit_code=1223,exit_filetime=1235)
        for key,value in (('creation_filetime',1233),('exited',False),('exit_filetime',1234),('exit_code',True),('session_id',4)):
            with self.assertRaises(ValueError):C.terminal_guard(self.birth(),dict(terminal,**{key:value}),3)

    def test_bounded_census(self):
        self.assertEqual(C.bounded_pids([0,3,7,9],12,4),[3,7])
        for values,size in (([1]*4,16),([1,1,0,0],8),([1,2,3,4],3)):
            with self.assertRaises(ValueError):C.bounded_pids(values,size,4)

    def test_prior_closed_result_unlock(self):
        result={'state':'FAILED','owned_closure_proven':True,'unknown_closure_stop_preserved':False}
        unlock={'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True}
        C.prior_closed_guard(result,unlock)
        for changed in (dict(result,owned_closure_proven=False),dict(result,unknown_closure_stop_preserved=True)):
            with self.assertRaises(ValueError):C.prior_closed_guard(changed,unlock)
        with self.assertRaises(ValueError):C.prior_closed_guard(result,dict(unlock,released=False))

    def test_lock_identity_exact(self):
        C.lock_guard(dict(C.LOCK))
        with self.assertRaises(ValueError):C.lock_guard(dict(C.LOCK,locked_byte=False))

    def test_failed_close_retains_owned_handle(self):
        class Fake:
            def close(self,_):return False
            def ok(self,value,_):
                if not value:raise OSError('synthetic CloseHandle failure')
        item={'handle':991};C.RETAINED.append(item)
        try:
            with self.assertRaises(OSError):C.close_owned(Fake(),item)
            self.assertIn(item,C.RETAINED)
        finally:C.RETAINED.remove(item)

    def test_successful_close_removes_owned_handle(self):
        class Fake:
            def close(self,_):return True
            def ok(self,value,_):assert value
        item={'handle':992};C.RETAINED.append(item);C.close_owned(Fake(),item)
        self.assertNotIn(item,C.RETAINED)

    def test_default_noop(self):
        output=io.StringIO()
        with patch.object(sys,'argv',['synthetic']),contextlib.redirect_stdout(output):self.assertEqual(C.main(),0)
        self.assertEqual(json.loads(output.getvalue())['actual_process_effects'],'NOT_RUN')


if __name__=='__main__':unittest.main()
