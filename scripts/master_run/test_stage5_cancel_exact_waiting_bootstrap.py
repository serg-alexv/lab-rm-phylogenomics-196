"""Synthetic C fixtures/mocked pidfd calls only; never signals a real process."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import ast, contextlib, copy, datetime, io, json, tempfile, unittest
import stage5_cancel_exact_waiting_bootstrap as V

HERE=Path(__file__).resolve().parent

def lease():
    return {'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1','workflow_lock_held':True,'nonce':V.NONCE,
            'owner_pid':V.WINDOWS_OWNER[0],'owner_creation_filetime':V.WINDOWS_OWNER[1],'workflow_lock':dict(V.LOCK)}

class Guards(unittest.TestCase):
    def test_exact_owner_lock_rejects_float_boolean_foreign_and_unheld(self):
        V.owner_binding(lease())
        mutations=[lambda x:x.update(owner_pid=float(V.WINDOWS_OWNER[0])),lambda x:x.update(nonce='b'*32),
                   lambda x:x.update(workflow_lock_held=False),lambda x:x['workflow_lock'].update(locked_byte=False),
                   lambda x:x['workflow_lock'].update(file_index=float(V.LOCK['file_index'])),
                   lambda x:x['workflow_lock'].update(extra='FOREIGN')]
        for mutate in mutations:
            value=lease();mutate(value)
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):V.owner_binding(value)

    def test_exact_identity_full_argv_exe_children_and_init_birth_chain(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            folder=Path(tmp);proc=folder/'proc';interpreter=folder/'python';interpreter.write_bytes(b'SYNTHETIC_EXE')
            target=proc/'22';(target/'task/22').mkdir(parents=True)
            (target/'task/22/children').write_text('');(target/'exe').write_bytes(interpreter.read_bytes())
            (target/'cmdline').write_bytes(b'\0'.join(x.encode() for x in V.ARGV)+b'\0')
            rows={22:{'pid':22,'ppid':8,'pgid':8,'sid':8,'start_ticks':'30','state':'S'},
                  8:{'pid':8,'ppid':1,'pgid':8,'sid':8,'start_ticks':'20','state':'S'},
                  1:{'pid':1,'ppid':0,'pgid':0,'sid':0,'start_ticks':'1','state':'S'}}
            P=SimpleNamespace(proc_record=lambda pid:copy.deepcopy(rows.get(pid)))
            def link(path):return str(interpreter.resolve()) if path.parent.name=='22' else '/init'
            with patch.object(V,'PROC',proc),patch.object(V,'INTERPRETER',str(interpreter)),patch.object(V,'INTERPRETER_SHA',V.sha(interpreter)),patch.object(V.os,'readlink',side_effect=link):
                value=V.identity(P,22);self.assertEqual([r['pid'] for r in value['init_ancestry']],[8,1])
                (target/'cmdline').write_bytes(b'OTHER\0')
                with self.assertRaises(ValueError):V.identity(P,22)
                (target/'cmdline').write_bytes(b'\0'.join(x.encode() for x in V.ARGV)+b'\0')
                (target/'task/22/children').write_text('77')
                with self.assertRaises(ValueError):V.identity(P,22)
                (target/'task/22/children').write_text('');rows[8]['start_ticks']='99'
                with self.assertRaises(ValueError):V.identity(P,22)
                rows[8]['start_ticks']='20';(target/'exe').write_bytes(b'CHANGED_EXE')
                with self.assertRaises(ValueError):V.identity(P,22)

    def test_discovery_never_selects_missing_or_ambiguous_exact_argv(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            proc=Path(tmp)
            with patch.object(V,'PROC',proc),self.assertRaises(ValueError):V.discover(SimpleNamespace())
            for pid in (20,21):
                (proc/str(pid)).mkdir();(proc/str(pid)/'cmdline').write_bytes(b'\0'.join(x.encode() for x in V.ARGV)+b'\0')
            with patch.object(V,'PROC',proc),self.assertRaises(ValueError):V.discover(SimpleNamespace())

    def test_waiting_rejects_admission_stale_policy_or_native_transition(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            folder=Path(tmp);genome=folder/'genome';trans=genome/'transactions/attempt_0001';trans.mkdir(parents=True)
            owner=folder/'owner';owner.mkdir();current=owner/'owner_lease.json';current.write_text(json.dumps(lease()))
            (trans/'initial_owner_lease.json').write_text(json.dumps(lease()));policy={'resource_wait_seconds':1800,'lease_max_age_seconds':30}
            latest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'admitted':False,'policy':policy,'wait_seconds':10,'windows_owner_lease':lease()}
            path=trans/'latest_admission.json';P=SimpleNamespace(check_lease=Mock(return_value=lease()))
            def write(value):path.write_text(json.dumps(value))
            with patch.object(V,'GENOME',genome),patch.object(V,'TRANSACTION',trans),patch.object(V,'OWNER_DIR',owner),patch.object(V,'LEASE',current):
                write(latest);self.assertFalse(V.waiting(P,policy)['admitted'])
                for changes in ({'admitted':True},{'wait_seconds':1800},{'wait_seconds':float('nan')},
                                {'utc':'2000-01-01T00:00:00+00:00'},{'policy':{'resource_wait_seconds':1800.0,'lease_max_age_seconds':30}}):
                    value=copy.deepcopy(latest);value.update(changes);write(value)
                    with self.subTest(changes=changes),self.assertRaises(ValueError):V.waiting(P,policy)
                write(latest)
                for forbidden in (genome/'execution',trans/'admission.json',owner/'result.json'):
                    forbidden.write_text('SYNTHETIC_TRANSITION')
                    with self.subTest(forbidden=forbidden),self.assertRaises(ValueError):V.waiting(P,policy)
                    forbidden.unlink()

    def test_default_noop_has_no_import_read_signal_or_write(self):
        stdout=io.StringIO()
        with patch('sys.argv',[V.__file__]),patch.object(V.importlib,'import_module',side_effect=AssertionError('No runtime import')),patch.object(V,'fixed_controls',side_effect=AssertionError('No controls read')),patch.object(V,'atomic',side_effect=AssertionError('No write')),contextlib.redirect_stdout(stdout):
            self.assertEqual(V.main(),0)
        self.assertEqual(json.loads(stdout.getvalue())['signal_count'],0)


class FakeMain(unittest.TestCase):
    def run_fake(self,folder,waiting_fail=None,pidfd=None,signal_error=False,identity_drift=False):
        proc=folder/'proc';(proc/'sys/kernel/random').mkdir(parents=True);(proc/'sys/kernel/random/boot_id').write_text(V.BOOT)
        out=folder/'fixed_out';observed={'runner':{'pid':22,'start_ticks':'30'},'synthetic':True}
        P=SimpleNamespace(verified_pidfd=Mock(return_value=202 if pidfd is None else pidfd),send_pidfd_signal=Mock())
        if signal_error:P.send_pidfd_signal.side_effect=OSError('Synthetic send uncertainty')
        W=SimpleNamespace(validate_storage=Mock())
        calls=0
        def waiting(*unused):
            nonlocal calls
            calls+=1
            if calls==waiting_fail:raise ValueError('Synthetic waiting precondition failed')
            return {'admitted':False,'synthetic':True}
        identity=Mock(return_value={'drift':True} if identity_drift else observed)
        stdout=io.StringIO()
        with patch('sys.argv',[str(folder/'entry.py'),'--run','--source-sha256','a'*64]),patch.object(V,'__file__',str(folder/'entry.py')),patch.object(V,'WORK',folder),patch.object(V,'OUT',out),patch.object(V,'PROC',proc),patch.object(V.sys,'platform','linux'),patch.object(V.os,'geteuid',return_value=0,create=True),patch.object(V.signal,'SIGALRM',14,create=True),patch.object(V.signal,'signal'),patch.object(V.signal,'alarm',create=True),patch.object(V,'fixed_controls'),patch.object(V,'read',return_value={'resource_policy':{}}),patch.object(V.importlib,'import_module',side_effect=lambda name:P if name=='stage5_atomic_process' else W),patch.object(V,'discover',return_value=observed),patch.object(V,'identity',identity),patch.object(V,'waiting',side_effect=waiting),patch.object(V.os,'close') as close,contextlib.redirect_stdout(stdout):
            code=V.main()
        result=json.loads((out/'result.json').read_bytes())
        return code,result,P,close,out

    def test_exact_mock_signal_only_is_request_not_closure(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            code,result,P,close,out=self.run_fake(Path(tmp))
            self.assertEqual(code,0);P.send_pidfd_signal.assert_called_once_with(202,V.signal.SIGTERM);close.assert_called_once_with(202)
            self.assertTrue((out/'signal_intent.json').is_file());self.assertFalse(result['target_termination_or_owner_unlock_proven'])

    def test_each_waiting_recheck_failure_never_signals(self):
        for check in (1,2,3):
            with self.subTest(check=check),tempfile.TemporaryDirectory(dir=HERE) as tmp:
                code,result,P,close,out=self.run_fake(Path(tmp),waiting_fail=check)
                self.assertEqual(code,2);P.send_pidfd_signal.assert_not_called();self.assertFalse(result['signal_attempted'])
                self.assertEqual(close.call_count,0 if check==1 else 1)

    def test_identity_drift_after_pidfd_retention_never_signals(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            code,result,P,close,out=self.run_fake(Path(tmp),identity_drift=True)
            self.assertEqual(code,2);P.send_pidfd_signal.assert_not_called();close.assert_called_once_with(202)

    def test_send_uncertainty_never_retries_or_claims_closure(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            code,result,P,close,out=self.run_fake(Path(tmp),signal_error=True)
            self.assertEqual(code,2);self.assertTrue(result['signal_attempted']);self.assertFalse(result['signal_returned_successfully'])
            P.send_pidfd_signal.assert_called_once();close.assert_called_once_with(202)
            self.assertFalse(result['target_termination_or_owner_unlock_proven'])

    def test_source_has_only_unchanged_verified_pidfd_signal_no_numeric_kill(self):
        tree=ast.parse(Path(V.__file__).read_bytes())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        attrs=[n.func.attr for n in calls if isinstance(n.func,ast.Attribute)]
        self.assertEqual(attrs.count('verified_pidfd'),1);self.assertEqual(attrs.count('send_pidfd_signal'),1)
        self.assertFalse(set(attrs)&{'kill','killpg','Popen','run','system','fork','WorkflowLock'})
        self.assertEqual(V.PINS['stage5_atomic_process.py'],'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e')

if __name__=='__main__':unittest.main()
