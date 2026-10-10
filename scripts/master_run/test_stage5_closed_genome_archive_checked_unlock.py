"""Pure fake-lock/fault checks and own C metadata; no WSL, Win API or OS lock."""
from pathlib import Path
from unittest.mock import patch
import ast, contextlib, copy, hashlib, io, json, tempfile, unittest
import stage5_closed_genome_archive_windows_checked_unlock as V

NONCE='a'*32
PENDING='RAW_RECOVERY_ZIP_BYTES_VALIDATED_PENDING_EXPLICIT_UNLOCK'


class FakeAPI:
    def __init__(self,stop,events,fail=(),tamper_receipt=False):
        self.stop=stop;self.events=events;self.fail=set(fail);self.tamper_receipt=tamper_receipt
    def utc(self):return 'SYNTHETIC_TEST_ONLY'
    def atomic(self,path,value):
        self.events.append(('write',path.name,self.stop.exists()))
        if path.name in self.fail:raise OSError('Synthetic publication failure')
        path.write_text(json.dumps(copy.deepcopy(value)),encoding='utf-8')
    def read_json(self,path):
        self.events.append(('read',path.name,self.stop.exists()))
        value=json.loads(path.read_bytes())
        if path.name=='lock_released.json' and self.tamper_receipt:value['released']=False
        return value


class FakeLock:
    def __init__(self,stop,events,fail=False,release=True):
        self.stop=stop;self.events=events;self.fail=fail;self.release=release;self.released=False
    def __exit__(self,*unused):
        self.events.append(('unlock',self.stop.exists()))
        if self.fail:raise OSError('Synthetic checked unlock failure')
        self.released=self.release


class FinishTests(unittest.TestCase):
    def fixture(self,folder,**api_options):
        stop=folder/'STOP.json';stop.write_text(json.dumps({'owner_nonce':NONCE,'synthetic':True}))
        events=[];api=FakeAPI(stop,events,**api_options);lock=FakeLock(stop,events)
        result={'state':PENDING}
        return stop,events,api,lock,result,V.sha(stop)

    def finish(self,folder,items,closure=True):
        stop,events,api,lock,result,pin=items
        return V.finish_after_unlock(api,lock,folder,result,stop,pin,NONCE,closure)

    def test_success_stop_survives_unlock_and_receipt_readback(self):
        with tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
            folder=Path(tmp);items=self.fixture(folder);result=self.finish(folder,items)
            self.assertEqual(items[1][:3],[('unlock',True),('write','lock_released.json',True),('read','lock_released.json',True)])
            self.assertEqual(result['state'],'PASS_RAW_RECOVERY_ZIP_BYTES_ONLY')
            self.assertEqual(items[1][-1],('write','result.json',False))
            self.assertTrue(result['original_lock_explicitly_released'] and result['original_unlock_receipt_proven'])
            self.assertTrue(result['owned_stop_cleared_after_unlock']);self.assertFalse(items[0].exists())
            self.assertEqual(result['lock_release_receipt_sha256'],V.sha(folder/'lock_released.json'))

    def test_unlock_exception_or_unreleased_return_preserves_stop(self):
        for fail,release in ((True,True),(False,False)):
            with self.subTest(fail=fail),tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
                folder=Path(tmp);items=self.fixture(folder);items[3].fail=fail;items[3].release=release
                result=self.finish(folder,items)
                self.assertEqual(result['state'],'FAILED');self.assertTrue(items[0].exists())
                self.assertTrue(result['owned_closure_proven'])
                self.assertFalse(result['original_lock_explicitly_released'] or result['original_unlock_receipt_proven'])
                self.assertFalse((folder/'lock_released.json').exists())

    def test_receipt_write_or_readback_failure_preserves_stop(self):
        for options in ({'fail':('lock_released.json',)},{'tamper_receipt':True}):
            with self.subTest(options=options),tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
                folder=Path(tmp);items=self.fixture(folder,**options);result=self.finish(folder,items)
                self.assertTrue(items[0].exists());self.assertEqual(result['state'],'FAILED')
                self.assertTrue(result['original_lock_explicitly_released'])
                self.assertFalse(result['original_unlock_receipt_proven'])

    def test_receipt_hash_failure_preserves_stop(self):
        with tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
            folder=Path(tmp);items=self.fixture(folder);original=V.sha
            def hash_fault(path):
                if Path(path).name=='lock_released.json':raise OSError('Synthetic receipt read failure')
                return original(path)
            with patch.object(V,'sha',side_effect=hash_fault):result=self.finish(folder,items)
            self.assertEqual(result['state'],'FAILED');self.assertTrue(items[0].exists())
            self.assertFalse(result['original_unlock_receipt_proven'])

    def test_foreign_nonce_or_changed_owned_stop_preserved(self):
        for foreign_nonce in (True,False):
            with self.subTest(foreign_nonce=foreign_nonce),tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
                folder=Path(tmp);items=list(self.fixture(folder))
                items[0].write_text(json.dumps({'owner_nonce':'b'*32 if foreign_nonce else NONCE,'changed':True}))
                if foreign_nonce:items[5]=V.sha(items[0])
                result=self.finish(folder,items)
                self.assertEqual(result['state'],'FAILED');self.assertTrue(items[0].exists())
                self.assertFalse(result['owned_stop_cleared_after_unlock'])

    def test_failed_but_closed_archive_can_clear_only_after_unlock(self):
        with tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
            folder=Path(tmp);items=self.fixture(folder);items[4]['state']='FAILED';result=self.finish(folder,items)
            self.assertEqual(result['state'],'FAILED');self.assertFalse(items[0].exists())
            self.assertEqual(items[1][0],('unlock',True));self.assertTrue(result['owned_closure_proven'])

    def test_unproven_closure_never_clears_stop_or_becomes_pass(self):
        with tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
            folder=Path(tmp);items=self.fixture(folder);result=self.finish(folder,items,False)
            self.assertEqual(result['state'],'FAILED');self.assertTrue(items[0].exists())
            self.assertFalse(result['owned_closure_proven']);self.assertTrue(result['original_unlock_receipt_proven'])

    def test_finalizer_errors_veto_stop_clear_and_pass(self):
        for key in ('lease_finalizer_error','power_finalizer_error','closure_finalizer_error'):
            with self.subTest(key=key),tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
                folder=Path(tmp);items=self.fixture(folder);items[4][key]='Synthetic finalizer fault'
                result=self.finish(folder,items)
                self.assertTrue(items[0].exists());self.assertEqual(result['state'],'FAILED')

    def test_result_publication_fault_has_one_distinct_failure_receipt(self):
        with tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
            folder=Path(tmp);items=self.fixture(folder,fail=('result.json',));result=self.finish(folder,items)
            self.assertEqual(result['state'],'FAILED');self.assertFalse(items[0].exists())
            failure=json.loads((folder/'publication_failure.json').read_bytes())
            self.assertTrue(failure['owned_closure_proven'] and failure['original_unlock_receipt_proven'])
            self.assertFalse(failure['closure_facts_reclassified_as_unknown'] or failure['scientific_adoption_authorized'])
            self.assertEqual([e[1] for e in items[1] if e[0]=='write'].count('publication_failure.json'),1)

    def test_double_publication_fault_is_bounded_without_fake_unclosed_stop(self):
        with tempfile.TemporaryDirectory(dir=V.WORK) as tmp:
            folder=Path(tmp);items=self.fixture(folder,fail=('result.json','publication_failure.json'))
            result=self.finish(folder,items)
            self.assertEqual(result['state'],'FAILED');self.assertFalse(items[0].exists())
            self.assertEqual(result['publication_failure_persistence_error_kind'],'OSError')
            self.assertTrue(result['owned_closure_proven'] and result['original_lock_explicitly_released'])
            self.assertEqual(len([e for e in items[1] if e[0]=='write']),3)

    def test_original_functions_and_pins_preserved_no_alias_needed(self):
        before=V.WORK/'stage5_closed_genome_archive_windows.py';after=Path(V.__file__)
        self.assertEqual(hashlib.sha256(before.read_bytes()).hexdigest(),'249b9de14219d8c0a5f1e7e88e48f6c80694bd04699c7c3e506b50a0980fab45')
        old=ast.parse(before.read_bytes());new=ast.parse(after.read_bytes())
        functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
        a=functions(old);b=functions(new)
        for name in a:
            if name!='main':self.assertEqual(a[name],b[name],name)
        assignments=lambda tree:[ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.Assign,ast.Import,ast.ImportFrom))]
        self.assertEqual(assignments(old),assignments(new))
        owner_attrs={n.attr for n in ast.walk(new) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='O'}
        self.assertEqual(owner_attrs,{'LOCAL_CLOSURE_STOP','fresh_authority'})
        main=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='unlink' for n in ast.walk(main)))
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='finish_after_unlock' for t in ast.walk(main) if isinstance(t,ast.Try) for f in t.finalbody for n in ast.walk(f)))

    def test_default_noop_imports_no_runtime_or_api(self):
        output=io.StringIO()
        with patch('sys.argv',[str(V.__file__)]),patch.object(V.importlib,'import_module',side_effect=AssertionError('Actual import forbidden')),contextlib.redirect_stdout(output):
            self.assertEqual(V.main(),0)
        result=json.loads(output.getvalue());self.assertEqual(result['state'],'PREPARED_NOT_RUN')
        self.assertFalse(result['eviction_authorized'])


if __name__=='__main__':unittest.main()
