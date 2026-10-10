"""Pure/fake exact-thirty cleanup contracts. Never opens native handles."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast,contextlib,copy,ctypes as c,io,json,tempfile,time,unittest
import cleanup_transport30_windows as C


def rows():
    return [{'path':str(Path(r'C:\fixture')/(str(i)+'.zip')),'bytes':i+1,'current_local_sha256':str(i)*64,
             'before':{'device':77,'inode':100+i,'bytes':i+1,'nlink':1,'birthtime_ns':1,
                       'mtime_ns':2,'file_attributes':32},'current_remote_asset':{},'expected_recovery':{}}
            for i in range(2)]


class Native:
    def __init__(self,values,bad=None):self.rows=values;self.bad=bad;self.next=1;self.held={};self.log=[];self.effects=[]
    def open(self,path,directory=False):
        self.log.append(('open',str(path),directory))
        if self.bad=='open' and not directory:raise OSError('fake sharing refusal')
        handle=self.next;self.next+=1;self.held[handle]=(str(path),directory);return handle
    def info(self,handle):
        path,directory=self.held[handle]
        if directory:return {'file_attributes':16}
        return copy.deepcopy(next(r['before'] for r in self.rows if r['path']==path))
    def hash(self,handle,size,deadline):
        path,_=self.held[handle];self.log.append(('hash',path))
        return 'x'*64 if self.bad=='hash' else next(r['current_local_sha256'] for r in self.rows if r['path']==path)
    def mark_delete(self,handle):
        path,directory=self.held[handle];assert not directory;self.log.append(('mark',path))
        self.effects.append({'path':path,'delete_disposition_returned':True,'handle_close_proven':False,'absence_verified':False})
    def close(self,handle):
        path,_=self.held[handle];self.log.append(('close',path))
        for e in self.effects:
            if e['path']==path:e['handle_close_proven']=True
        del self.held[handle]


class Contracts(unittest.TestCase):
    def test_real_frozen_controls_are_exact30_literals_and_2GB_only(self):
        proof,actual=C.controls()
        self.assertEqual(len(C.TARGETS),30);self.assertEqual(sum(r['bytes'] for r in actual),2048507163)
        self.assertEqual({r['path'] for r in actual},{str(C.WORK/p) for p in C.TARGETS})
        for target in C.TARGETS:
            self.assertEqual(len(Path(target).parts),2);self.assertNotIn('..',Path(target).parts)
            self.assertTrue(target.endswith(('.zip','.zip.sha256')))
        self.assertFalse(proof['rows'][0]['fresh_remote_asset_bytes_downloaded'])

    def test_target_swap_and_remote_metadata_digest_tamper_reject(self):
        original=C.exact_raw
        for field in ('path','digest'):
            def fake(path,pin,limit=2*1024**2):
                raw=original(path,pin,limit)
                if path.name==C.PROOF:
                    value=json.loads(raw)
                    if field=='path':value['rows'][0]['path']=str(C.WORK/'receipt.json')
                    else:value['rows'][0]['current_remote_asset']['digest']='sha256:'+'0'*64
                    return json.dumps(value).encode()
                return raw
            with self.subTest(field=field),patch.object(C,'exact_raw',side_effect=fake),self.assertRaises(ValueError):C.controls()

    def test_noop_never_reads_controls_or_imports_native(self):
        with patch('sys.argv',['no-op']),patch.object(C,'controls',side_effect=AssertionError('control read')),patch.object(C,'module',side_effect=AssertionError('native import')),patch.object(C,'NativeLeaves',side_effect=AssertionError('native construct')),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(C.main(),0)
        self.assertEqual(json.loads(out.getvalue())['effects'],0)

    def test_every_payload_verified_before_first_effect_and_intent_before_mark(self):
        values=rows();native=Native(values);events=[]
        def event(phase,details):events.append(phase);native.log.append(('event',phase))
        with patch.object(C,'absent',lambda path:native.log.append(('absent',str(path)))):
            deleted=C.purge_exact(values,native,event,lambda:None,time.monotonic()+10)
        self.assertEqual(len(deleted),2);self.assertTrue(all(e['absence_verified'] for e in native.effects))
        kinds=[x[0] for x in native.log];self.assertEqual(kinds[:kinds.index('mark')].count('hash'),2)
        for i,item in enumerate(native.log):
            if item[0]=='mark':self.assertEqual(native.log[i-1],('event','BEFORE_EXACT_RETAINED_HANDLE_DELETE_DISPOSITION'))

    def test_any_preflight_hash_or_open_failure_prevents_all_effects(self):
        for bad in ('hash','open'):
            native=Native(rows(),bad)
            with self.subTest(bad=bad),self.assertRaises((ValueError,OSError)):
                C.purge_exact(native.rows,native,lambda *_:None,lambda:None,time.monotonic()+10)
            self.assertFalse(any(x[0]=='mark' for x in native.log))

    def test_intent_publication_failure_prevents_effect(self):
        native=Native(rows())
        def event(phase,_):
            if phase=='BEFORE_EXACT_RETAINED_HANDLE_DELETE_DISPOSITION':raise OSError('fake durable intent failure')
        with self.assertRaises(OSError):C.purge_exact(native.rows,native,event,lambda:None,time.monotonic()+10)
        self.assertEqual(native.effects,[])

    def test_deadline_or_identity_replacement_veto(self):
        with self.assertRaises(ValueError):C.purge_exact(rows(),Native(rows()),lambda *_:None,lambda:None,time.monotonic()-1)
        row=rows()[0]
        for key,bad in [('inode',101),('nlink',2),('file_attributes',32|0x400),('device',77.0)]:
            actual=copy.deepcopy(row['before']);actual[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):C.match(actual,row)

    def test_checked_close_failure_retains_owned_handle_and_never_retries(self):
        native=C.NativeLeaves.__new__(C.NativeLeaves);native.api=SimpleNamespace(close=lambda handle:False)
        native.handles={9:{'path':'fixture','directory':False,'close_attempted':False}};native.close_errors=[];native.effects=[]
        with self.assertRaises(OSError):native.close(9)
        self.assertIn(9,native.handles);self.assertFalse(native.finalize())
        with self.assertRaises(ValueError):native.close(9)

    def test_mark_failure_retains_effect_attempt_for_reconciliation(self):
        native=C.NativeLeaves.__new__(C.NativeLeaves)
        class Disposition(c.Structure):_fields_=[('delete_file',c.c_ubyte)]
        self.assertEqual(c.sizeof(Disposition),1)
        native.Disposition=Disposition;native.handles={9:{'path':'fixture','directory':False,'close_attempted':False,'delete_disposition_attempted':False}}
        native.effects=[];native.set_info=lambda *_:False
        def fail(value,message):
            if not value:raise OSError(message)
        native.api=SimpleNamespace(ok=fail)
        with self.assertRaises(OSError):native.mark_delete(9)
        self.assertTrue(native.effects[0]['delete_disposition_attempted']);self.assertFalse(native.effects[0]['delete_disposition_returned'])
        self.assertIn(9,native.handles)

    def test_no_path_delete_tree_shell_wsl_or_github_apis(self):
        source=(C.WORK/'cleanup_transport30_windows.py').read_text();tree=ast.parse(source)
        calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        for name in calls:self.assertFalse(name.endswith(('.unlink','.rmdir','.rmtree','.Popen','.run','.remove')))
        self.assertNotIn('wsl.exe',source);self.assertNotIn('shutil',source)
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        lines={ast.unparse(n.func):n.lineno for n in ast.walk(main) if isinstance(n,ast.Call)}
        self.assertLess(lines['prepare_finalizer'],lines['api.identity'])

    def test_reviewed_finalizer_unlock_before_receipt_before_stopclear(self):
        self.finalizer_case()

    def test_reviewed_finalizer_unlock_or_receipt_failure_preserves_stop(self):
        for bad in ('unlock','receipt'):
            with self.subTest(bad=bad):self.finalizer_case(bad)

    def test_unclosed_native_handles_veto_stopclear_and_pass(self):
        self.finalizer_case('unclosed')

    def test_final_result_persistence_failure_never_fabricates_pass(self):
        self.finalizer_case('result')

    def finalizer_case(self,bad=None):
        fn=C.prepare_finalizer();events=[]
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);stop=out/'stop.json';stop.write_text(json.dumps({'owner_nonce':'test'}));pin=C.digest(stop.read_bytes())
            class Lock:
                released=False
                def __exit__(self,*_):
                    events.append('unlock')
                    if bad=='unlock':raise OSError('fake unlock failure')
                    self.released=True
            def atomic(path,value):
                events.append(path.name)
                if (bad=='receipt' and path.name=='lock_released.json') or (bad=='result' and path.name=='result.json'):raise OSError('fake persistence failure')
                path.write_text(json.dumps(value))
            api=SimpleNamespace(atomic=atomic,read_json=lambda p:json.loads(p.read_bytes()),utc=lambda:'test')
            value={'state':'TRANSPORT30_VALIDATED_PENDING_EXPLICIT_UNLOCK'}
            actual=fn(api,Lock(),out,value,stop,pin,'test',bad!='unclosed')
            self.assertEqual(events[:2],['unlock','lock_released.json'] if bad!='unlock' else ['unlock','result.json'])
            if bad is None:self.assertEqual(actual['state'],'PASS_EXACT30_RETAINED_TRANSPORT_LEAVES_REMOVED');self.assertFalse(stop.exists())
            else:
                self.assertEqual(actual['state'],'FAILED')
                self.assertEqual(stop.exists(),bad!='result')
                if bad=='result':self.assertTrue(actual['original_lock_explicitly_released']);self.assertTrue((out/'publication_failure.json').exists())


if __name__=='__main__':unittest.main()
