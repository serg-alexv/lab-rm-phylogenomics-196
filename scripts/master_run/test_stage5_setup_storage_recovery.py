"""Pure source/closed-C-baseline/finalizer tests; no WSL or original lock."""
from pathlib import Path
import ast, copy, hashlib, json, runpy, sys, tempfile, unittest
from unittest.mock import patch
import stage5_setup_storage_recovery_linux as L
import stage5_setup_storage_recovery_windows as W
import stage5_wsl_host_profile_fallback_owner as F

WORK=Path(__file__).resolve().parent


def functions(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}


def closed_values():
    peer=json.loads((WORK/L.RECOVERY_PEER).read_text());snapshot=json.loads((WORK/L.SNAPSHOT).read_text())
    directory=WORK/F.CAPACITY_DIR
    names=['owner.json','result.json','GCF_000009425.1.launch.json','GCF_000009425.1.exit.json','progress.json','owner_lease.json','lock_released.json']
    values={name:json.loads((directory/name).read_text()) for name in names}
    values['terminal']=json.loads((WORK/'stage5_capacity02_closed_native_copy/status.json').read_text())
    return peer,snapshot,values


class SourceTests(unittest.TestCase):
    def test_preserved_original_functions(self):
        a=functions(WORK/'stage5_setup_linux.py');b=functions(WORK/'stage5_setup_storage_recovery_linux.py')
        for name in a:
            if name not in ('main','toolchain_observe','verified_toolchain'):self.assertEqual(a[name],b[name],name)
        a=functions(WORK/'stage5_setup_windows.py');b=functions(WORK/'stage5_setup_storage_recovery_windows.py')
        for name in a:
            if name not in ('main','exact_preexec_failure'):self.assertEqual(a[name],b[name],name)

    def test_exact_preexec_filename_only(self):
        old=functions(WORK/'stage5_setup_windows.py')['exact_preexec_failure']
        new=functions(WORK/'stage5_setup_storage_recovery_windows.py')['exact_preexec_failure']
        self.assertEqual(old,new.replace('stage5_setup_storage_recovery_linux.py','stage5_setup_linux.py'))

    def test_toolchain_original_delegation_and_one_bind(self):
        code=(WORK/'stage5_setup_storage_recovery_linux.py').read_text()
        self.assertIn('return base.toolchain_observe()',code);self.assertIn('return base.verified_toolchain(path,expected)',code)
        tree=ast.parse(code)
        commands=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='command' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='bind_storage']
        self.assertEqual(len(commands),1)
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in ('unlink','rmdir','rename','replace') for n in ast.walk(tree)))
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        self.assertIn("args.step == 'storage'",ast.unparse(main))

    def test_immutable_source_pins(self):
        for mapping in (L.RECOVERY_PINS,W.PINS):
            for name,pin in mapping.items():self.assertEqual(hashlib.sha256((WORK/name).read_bytes()).hexdigest(),pin,name)

    def test_both_default_main_noop(self):
        for name in ('stage5_setup_storage_recovery_linux.py','stage5_setup_storage_recovery_windows.py'):
            with patch.object(sys,'argv',[name]):
                with self.assertRaises(SystemExit) as outcome:runpy.run_path(str(WORK/name),run_name='__main__')
                self.assertEqual(outcome.exception.code,0)


class BaselineTests(unittest.TestCase):
    def baseline(self,peer,snapshot,values):
        with patch.object(L,'WORK',WORK),patch.object(L,'recovery_sources',return_value=(None,F)):
            return L.recovery_baseline(peer,snapshot,values)

    def test_exact_actual_closed_baseline(self):
        peer,snapshot,values=closed_values();members,old=self.baseline(peer,snapshot,values)
        self.assertEqual(len(members),52);self.assertEqual(old['filesystem_uuid'],L.BACKING_UUID)
        actual={name:{**row,'inode':row['windows_unc_inode_projection']} for name,row in members.items()}
        self.assertTrue(L.recovery_member_check(members,actual))

    def test_changed_membership_file_inode_and_type_rejected(self):
        peer,snapshot,values=closed_values();members,_=self.baseline(peer,snapshot,values)
        good={name:{**row,'inode':row['windows_unc_inode_projection']} for name,row in members.items()}
        file=next(name for name,row in good.items() if row['kind']=='file')
        for key,value in [('sha256','0'*64),('bytes',good[file]['bytes']+1),('inode',good[file]['inode']+1),('inode',float(good[file]['inode'])),('kind','directory')]:
            bad=copy.deepcopy(good);bad[file][key]=value
            with self.assertRaises(Exception):L.recovery_member_check(members,bad)
        bad=copy.deepcopy(good);bad['unknown']={}
        with self.assertRaises(Exception):L.recovery_member_check(members,bad)

    def test_closure_and_projection_tamper_rejected(self):
        peer,snapshot,values=closed_values()
        for key,value in [('native_launch_count',1),('owned_closure_proven',False),('actual_boot_id','other')]:
            bad=copy.deepcopy(peer);bad[key]=value
            with self.assertRaises(Exception):self.baseline(bad,snapshot,values)
        bad=copy.deepcopy(snapshot);bad['backing_inventory'][0]['windows_unc_inode_projection']=float(bad['backing_inventory'][0]['windows_unc_inode_projection'])
        with self.assertRaises(Exception):self.baseline(peer,bad,values)
        bad=copy.deepcopy(snapshot);bad['members']=bad['members'][:-1]
        with self.assertRaises(Exception):self.baseline(peer,bad,values)


class FinalizerTests(unittest.TestCase):
    def invoke(self,fault=None):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup);out=Path(directory.name)
        stop=out/'STOP.json';stop.write_text(json.dumps({'owner_nonce':'n'}));pin=W.digest(stop.read_bytes());events=[]
        class Lock:
            released=False
            def __exit__(self,*_):
                events.append('unlock')
                if fault=='unlock':raise OSError('test')
                self.released=True
        class API:
            @staticmethod
            def require(value,message):
                if not value:raise ValueError(message)
            @staticmethod
            def utc():return 'UTC'
            @staticmethod
            def atomic(path,value):
                events.append('write:'+path.name)
                if fault==path.name:raise OSError('test')
                path.write_text(json.dumps(value))
            @staticmethod
            def read_json(path):
                events.append('read:'+path.name);return json.loads(path.read_text())
        result={'state':'STORAGE_RECOVERY_VALIDATED_PENDING_EXPLICIT_UNLOCK'}
        if fault=='handle':result['handle_close_error']={}
        lock=Lock();W.finish_after_unlock(API,lock,out,result,stop,pin,'n',fault!='closure')
        return result,stop.exists(),events

    def test_success_checked_unlock_receipt_precedes_stop_clear(self):
        result,exists,events=self.invoke()
        self.assertEqual(result['state'],'PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK');self.assertFalse(exists)
        self.assertLess(events.index('unlock'),events.index('write:lock_released.json'))
        self.assertLess(events.index('read:lock_released.json'),events.index('read:STOP.json'))
        self.assertTrue(result['original_unlock_receipt_proven'])

    def test_unlock_receipt_handle_or_closure_failure_preserves_stop(self):
        for fault in ('unlock','lock_released.json','handle','closure'):
            result,exists,_=self.invoke(fault)
            self.assertEqual(result['state'],'FAILED');self.assertTrue(exists)

    def test_result_publication_failure_retains_proven_closure_facts(self):
        result,exists,events=self.invoke('result.json')
        self.assertEqual(result['state'],'FAILED');self.assertFalse(exists)
        self.assertTrue(result['original_lock_explicitly_released']);self.assertTrue(result['original_unlock_receipt_proven'])
        self.assertTrue(result['master_publication_reconciliation_required']);self.assertIn('write:publication_failure.json',events)


if __name__=='__main__':unittest.main()
