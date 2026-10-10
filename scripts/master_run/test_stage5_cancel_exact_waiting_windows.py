"""Pure AST/default-noop/fake-owner tests; no real Windows API or WSL calls."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import ast,contextlib,copy,io,json,sys,unittest
import stage5_cancel_exact_waiting_windows as V
import stage5_cancel_exact_waiting_bootstrap as C

HERE=Path(__file__).resolve().parent

class Guards(unittest.TestCase):
    def test_original_U_job_reverse_literal_identical(self):
        source=(HERE/'stage5_unc_bind_probe.py').read_text();new=Path(V.__file__).read_text()
        old=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='windows_job')
        local=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='wsl_control_job')
        fragment='\n'.join(new.splitlines()[local.lineno-1:local.end_lineno])
        reverse=fragment.replace('def wsl_control_job(','def windows_job(').replace('WSL','sys.executable')
        self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(ast.parse(reverse).body[0],include_attributes=False))
        self.assertEqual(fragment.count('WSL'),3)

    def test_default_NOOP_has_no_read_import_API_or_WSL(self):
        with (patch.object(sys,'argv',[str(V.__file__)]),patch.object(V,'sha',side_effect=AssertionError('read')),
              patch.object(V,'load_pinned',side_effect=AssertionError('import')),contextlib.redirect_stdout(io.StringIO()) as output):
            self.assertEqual(V.main(),0)
        self.assertEqual(json.loads(output.getvalue())['WSL_clients_created'],0)

    def test_strict_existing_owner_authority_and_closed_scope(self):
        expected={'executable':'exact.exe','session_id':1}
        actual={'pid':C.WINDOWS_OWNER[0],'creation_filetime':int(C.WINDOWS_OWNER[1]),'exited':False,**expected}
        lease={'workflow_lock_held':True,'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1','nonce':C.NONCE,
               'owner_pid':C.WINDOWS_OWNER[0],'owner_creation_filetime':C.WINDOWS_OWNER[1],'workflow_lock':dict(C.LOCK)}
        api=SimpleNamespace(identity=Mock(return_value=actual))
        A=SimpleNamespace(read_json=Mock(return_value={'state':'ACTIVE_DIRECT_USER_CONTINUATION','automatic_resume':False}),
                          ORIGINAL_LOCK=HERE/'fake_original.lock')
        P=SimpleNamespace(check_lease=Mock(return_value=lease))
        fakeC=SimpleNamespace(PINS={'x':'pin'},read=Mock(side_effect=lambda p:{'owner':expected} if p.name=='owner.json' else {'resource_policy':{}}),
                              owner_binding=C.owner_binding,WINDOWS_OWNER=C.WINDOWS_OWNER,NONCE=C.NONCE)
        with patch.object(V,'sha',return_value='pin'),patch.object(Path,'exists',return_value=False):
            V.current_authority(A,fakeC,P,api,77)
            for mutate in (lambda x:x.update(exited=True),lambda x:x.update(creation_filetime=1),
                           lambda x:x.update(executable='other.exe'),lambda x:x.update(session_id=2)):
                row=copy.deepcopy(actual);mutate(row);api.identity.return_value=row
                with self.assertRaises(ValueError):V.current_authority(A,fakeC,P,api,77)
            api.identity.return_value=actual;A.read_json.return_value['automatic_resume']=True
            with self.assertRaises(ValueError):V.current_authority(A,fakeC,P,api,77)
            A.read_json.return_value['automatic_resume']=False;lease['workflow_lock']['locked_byte']=False
            with self.assertRaises(ValueError):V.current_authority(A,fakeC,P,api,77)
        with patch.object(V,'sha',return_value='pin'),patch.object(Path,'exists',return_value=True):
            with self.assertRaises(ValueError):V.current_authority(A,fakeC,P,api,77)

    def test_no_second_lock_global_executable_assignment_or_science_launch(self):
        tree=ast.parse(Path(V.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                self.assertNotIn(node.func.attr,('WorkflowLock','kill','killpg','Popen','run','system'))
            if isinstance(node,ast.Assign):
                for target in node.targets:self.assertFalse(isinstance(target,ast.Attribute) and target.attr=='executable')
        self.assertEqual(V.PINS['stage5_cancel_exact_waiting_bootstrap.py'],C.sha(C.__file__))

    def test_Windows_constructed_Linux_script_argv_is_exact_POSIX(self):
        self.assertEqual(C.WORK.as_posix()+'/stage5_cancel_exact_waiting_bootstrap.py',
            '/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_cancel_exact_waiting_bootstrap.py')
        node=next(n for n in ast.walk(ast.parse(Path(V.__file__).read_text()))
                  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='argv' for t in n.targets))
        self.assertEqual(ast.unparse(node.value.elts[8]),"C.WORK.as_posix() + '/stage5_cancel_exact_waiting_bootstrap.py'")

if __name__=='__main__':unittest.main()
