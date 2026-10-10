"""Pure in-memory/C-temporary fallback contracts; no WSL, profile or OS-lock effects."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast, contextlib, copy, hashlib, io, json, tempfile, unittest
import stage5_wsl_host_profile_fallback_owner as M

HERE=Path(__file__).resolve().parent


def fixture():
    """Synthetic only: never an actual closure or biological result."""
    owner={'pid':25208,'creation_filetime':134360788348328513,'session_id':1}
    bindings={key:M.CAPACITY_PINS[name] for key,name in [
        ('config_sha256','stage5_actual_backing_capacity_02.json'),('linux_script_sha256','stage5_atomic.py'),
        ('linux_supervisor_sha256','stage5_atomic_process.py'),('storage_helper_sha256','stage5_work_storage.py'),
        ('lease_helper_sha256','stage5_owner_lease.py')]}
    original=dict(bindings,owner=owner,workflow_lock=copy.deepcopy(M.ORIGINAL_LOCK))
    born={'pid':10272,'creation_filetime':134360788351071808,'session_id':1,'executable':r'C:\Windows\System32\wsl.exe'}
    dead=dict(born,exit_filetime=134360806351071808,exited=True,exit_code=75)
    terminal={'state':'DEFERRED_RESOURCE','accession':'GCF_000009425.1','transaction':'transactions/attempt_0002',
        'owner_nonce':M.CAPACITY_NONCE,'owned_closure_proven':True,'no_native_launch_in_this_invocation':True,
        'outputs_preserved':True,'curation':'NOT_RUN','biological_absence_claim':'NONE',
        'scientific_identity':{'runner_sha256':M.CAPACITY_PINS['stage5_atomic.py']},
        'error':'Deferred: Bounded resource admission expired; no native child launched'}
    prefix='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/'
    launch={'native_wsl_client':born,'owner_nonce':M.CAPACITY_NONCE,'index':1,'argv':[
        r'C:\Windows\System32\wsl.exe','-d','Ubuntu','-u','root','--exec',
        '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/detector_env/bin/python','-B',
        prefix+'stage5_atomic.py','--config',prefix+'stage5_actual_backing_capacity_02.json','run','--accession','GCF_000009425.1',
        '--owner-lease',prefix+M.CAPACITY_DIR+'/owner_lease.json','--owner-nonce',M.CAPACITY_NONCE]}
    stdout=json.dumps(terminal).encode();end={'state':'DEFERRED_RESOURCE','actual_wsl_client_exit':dead,
        'status_sha256':M.digest(stdout),'stdout_sha256':M.digest(stdout),'stderr_sha256':M.digest(b'')}
    result=dict(bindings,state='DEFERRED_RESOURCE',owner=owner,scope='ONE_APPROVED_GENOME',
        selected_accessions=['GCF_000009425.1'],approved_genomes=196,full_panel_complete=False,genome_results=[end],utc='2')
    values={'owner.json':original,'result.json':result,'GCF_000009425.1.launch.json':launch,
        'GCF_000009425.1.exit.json':end,'progress.json':{'latest':end,'genome_results':[end],'finished':1,'total':1},
        'owner_lease.json':{'workflow_lock':copy.deepcopy(M.ORIGINAL_LOCK),'nonce':M.CAPACITY_NONCE,'owner_pid':25208,
            'owner_creation_filetime':'134360788348328513','workflow_lock_held':False,'expires_unix':1,'measured_unix':1,'utc':'1'},
        'lock_released.json':{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','utc':'3'},'terminal':terminal}
    peer={'state':'PASS_CAPACITY02_NATURAL_ADMISSION_DEFER_NO_NATIVE_SCOPE_CLOSED_AND_ORIGINAL_UNLOCK',
        'actual_state':'DEFERRED_RESOURCE','scientific_adoption':False,'no_native_launch_in_this_invocation':True,
        'native_launch_count':0,'owned_closure_proven':True,'original_lock_explicitly_released':True,
        'actual_boot_id':M.CAPACITY_BOOT,'retained_WSL_client':dead}
    return peer,values,stdout


class Tests(unittest.TestCase):
    def test_exact_two_line_transform_and_every_other_byte(self):
        raw=(HERE/M.PREIMAGE_NAME).read_bytes();after=M.transform_profile(raw)
        self.assertEqual(M.digest(raw),M.PREIMAGE_SHA);self.assertEqual(len(raw),681);self.assertEqual(len(after),685)
        self.assertEqual(after,raw.replace(b'memory=3GB\n',b'memory=3584MB\n').replace(b'guiApplications=true\n',b'guiApplications=false\n'))
        self.assertEqual(sum(a!=b for a,b in zip(raw.splitlines(),after.splitlines())),2)
        self.assertEqual(raw.count(b'\r\n'),after.count(b'\r\n'))
        for token in (b'swap=8GB',b'processors=4',b'autoMemoryReclaim=dropCache'):
            self.assertIn(token,after)
        for bad in (after,raw+b'\n',raw.replace(b'swap=8GB',b'swap=7GB')):
            with self.assertRaises(ValueError):M.transform_profile(bad)

    def test_transform_rejects_rebased_wrong_section_or_literal(self):
        raw=(HERE/M.PREIMAGE_NAME).read_bytes()
        for bad in (raw.replace(b'[wsl2]',b'[xxxx]'),raw.replace(b'memory=3GB',b'memory=3gb'),
                    raw.replace(b'guiApplications=true',b'guiApplications=truE')):
            with patch.object(M,'PREIMAGE_SHA',M.digest(bad)),self.assertRaises(ValueError):M.transform_profile(bad)

    def test_default_noop_never_loads_owner_or_reads_profile(self):
        with (patch('sys.argv',['fallback']),patch.object(M,'windows_main',side_effect=AssertionError('Owner forbidden')),
             patch.object(M,'load_base',side_effect=AssertionError('Reads forbidden')),contextlib.redirect_stdout(io.StringIO()) as out):
            self.assertEqual(M.main(),0)
        self.assertEqual(json.loads(out.getvalue()),{'state':'PREPARED_NOT_RUN','WSL_launches':0,'profile_changes':0,'shutdowns':0})

    def test_current_synthetic_defer_accepts_prepared_science_but_no_launch(self):
        peer,values,_=fixture();self.assertEqual(M.capacity_contract(peer,values)['state'],'DEFERRED_RESOURCE')
        self.assertIsInstance(values['terminal']['scientific_identity'],dict)

    def test_capacity_false_closure_native_unknown_inactive_lease_and_type_tamper_veto(self):
        changes=[('peer','native_launch_count',True),('peer','native_launch_count',1),('peer','owned_closure_proven',False),
            ('peer','actual_boot_id','old'),('peer','scientific_adoption',True),('peer','actual_state','COMPLETE_VALIDATED'),
            ('terminal','no_native_launch_in_this_invocation',False),('terminal','owned_closure_proven',False),
            ('terminal','curation','COMPLETE'),('owner_lease.json','workflow_lock_held',True),
            ('owner_lease.json','owner_pid',25208.0),('owner_lease.json','expires_unix',2),
            ('progress.json','finished',True),('lock_released.json','state','NOT_RELEASED')]
        for member,key,bad in changes:
            peer,values,_=fixture();target=peer if member=='peer' else values[member];target[key]=bad
            with self.subTest(member=member,key=key),self.assertRaises(ValueError):M.capacity_contract(peer,values)
        for key in M.ORIGINAL_LOCK:
            peer,values,_=fixture();value=values['owner_lease.json']['workflow_lock'][key]
            values['owner_lease.json']['workflow_lock'][key]=float(value) if type(value) is int else value+'x'
            with self.subTest(lock=key),self.assertRaises(ValueError):M.capacity_contract(peer,values)

    def test_capacity_retained_client_birth_exit_argv_and_config_tamper_veto(self):
        for member,key,bad in [('actual_wsl_client_exit','exit_code',0),('actual_wsl_client_exit','pid',10273),
            ('actual_wsl_client_exit','creation_filetime',134360788351071809),('actual_wsl_client_exit','exit_filetime',0),
            ('actual_wsl_client_exit','exited',False)]:
            peer,values,_=fixture();values['GCF_000009425.1.exit.json'][member][key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):M.capacity_contract(peer,values)
        peer,values,_=fixture();values['GCF_000009425.1.launch.json']['argv'][10]='wrong'
        with self.assertRaises(ValueError):M.capacity_contract(peer,values)

    def test_explicit_peer_sha_captured_file_coverage_and_actual_byte_tamper_veto(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);peer,values,stdout=fixture();entries={}
            def add(relative,raw):
                path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
                entries[str(Path(relative))]={'bytes':len(raw),'sha256':M.digest(raw)}
            for name in M.CAPACITY_PINS:add(name,(HERE/name).read_bytes())
            for name,value in values.items():
                if name!='terminal':add(str(Path(M.CAPACITY_DIR)/name),json.dumps(value).encode())
            for suffix,raw in [('stdout',stdout),('stderr',b'')]:
                add(str(Path(M.CAPACITY_DIR)/('GCF_000009425.1.'+suffix+'.txt')),raw)
            add('closed_copy/status.json',stdout)
            peer.update(checked_files=entries,terminal_copy_path=str(root/'closed_copy/status.json'),
                actual_result_sha256=entries[str(Path(M.CAPACITY_DIR)/'result.json')]['sha256'],
                actual_unlock_sha256=entries[str(Path(M.CAPACITY_DIR)/'lock_released.json')]['sha256'],
                actual_native_terminal_sha256=M.digest(stdout))
            path=root/M.CLOSURE_PEER;raw=json.dumps(peer).encode();path.write_bytes(raw)
            G=SimpleNamespace(plain_chain=lambda path:None,tiny=lambda path,limit=1024**2:Path(path).read_bytes(),
                              sha=lambda path:M.digest(Path(path).read_bytes()))
            with patch.object(M,'WORK',root):
                self.assertEqual(M.capacity_read(G,M.digest(raw))[1]['terminal'],values['terminal'])
                for wrong in (None,'0'*64,'ABC'):
                    with self.subTest(sha=wrong),self.assertRaises(ValueError):M.capacity_read(G,wrong)
                (root/'closed_copy/status.json').write_bytes(stdout+b' ')
                with self.assertRaises(ValueError):M.capacity_read(G,M.digest(raw))
                (root/'closed_copy/status.json').write_bytes(stdout)
                del peer['checked_files'][str(Path(M.CAPACITY_DIR)/'GCF_000009425.1.exit.json')]
                path.write_text(json.dumps(peer))
                with self.assertRaises(KeyError):M.capacity_read(G,M.digest(path.read_bytes()))
                peer['checked_files']['../escape.json']={'bytes':0,'sha256':M.digest(b'')};path.write_text(json.dumps(peer))
                with self.assertRaises(ValueError):M.capacity_read(G,M.digest(path.read_bytes()))
        peer,values,_=fixture();values['result.json']['config_sha256']='0'*64
        with self.assertRaises(ValueError):M.capacity_contract(peer,values)

    def final(self,folder,fail=None,closure=True,foreign=False):
        events=[];output=Path(folder);stop=output/'STOP.json';stop.write_text(json.dumps({'owner_nonce':'foreign' if foreign else 'own'}))
        stop_sha=M.digest(stop.read_bytes());result={'state':'HOST_PROFILE_VALIDATED_PENDING_EXPLICIT_UNLOCK'}
        class Lock:
            released=False
            def __exit__(self,*args):
                events.append('unlock')
                if fail=='unlock':raise OSError('Synthetic unlock failure')
                self.released=True
        class API:
            @staticmethod
            def utc():return 'test'
            @staticmethod
            def atomic(path,value):
                events.append(path.name)
                if fail==path.name:raise OSError('Synthetic persistence failure')
                path.write_text(json.dumps(value))
            @staticmethod
            def read_json(path):
                events.append('readback:'+path.name)
                if fail=='readback' and path.name=='lock_released.json':return {'wrong':True}
                return json.loads(path.read_bytes())
        value=M.finish_after_unlock(API,Lock(),output,result,stop,stop_sha,'own',closure)
        return value,stop,events

    def test_unlock_receipt_readback_before_stop_clear_and_success(self):
        with tempfile.TemporaryDirectory() as folder:
            result,stop,events=self.final(folder)
            self.assertTrue(result['state'].startswith('PASS_'));self.assertFalse(stop.exists())
            self.assertTrue(result['original_unlock_receipt_proven']);self.assertTrue(result['owned_stop_cleared_after_unlock'])
            self.assertLess(events.index('unlock'),events.index('lock_released.json'))
            self.assertLess(events.index('readback:lock_released.json'),events.index('readback:STOP.json'))
            self.assertLess(events.index('readback:STOP.json'),events.index('result.json'))

    def test_unlock_receipt_unknown_closure_or_foreign_stop_preserves_stop(self):
        for fail,closure,foreign in [('unlock',True,False),('lock_released.json',True,False),('readback',True,False),
                                      (None,False,False),(None,True,True)]:
            with self.subTest(fail=fail,closure=closure,foreign=foreign),tempfile.TemporaryDirectory() as folder:
                result,stop,_=self.final(folder,fail,closure,foreign)
                self.assertEqual(result['state'],'FAILED');self.assertTrue(stop.exists())
                self.assertFalse(result['owned_stop_cleared_after_unlock'])

    def test_final_publication_failure_has_finite_receipt_and_preserves_proven_facts(self):
        with tempfile.TemporaryDirectory() as folder:
            result,stop,events=self.final(folder,'result.json')
            self.assertEqual(result['state'],'FAILED');self.assertFalse(stop.exists())
            self.assertTrue(result['original_lock_explicitly_released']);self.assertTrue(result['owned_closure_proven'])
            receipt=json.loads((Path(folder)/'publication_failure.json').read_bytes())
            self.assertFalse(receipt['closure_facts_reclassified_as_unknown']);self.assertEqual(events.count('result.json'),1)

    def test_original_framework_and_retained_functions_preserved(self):
        self.assertEqual(M.digest((HERE/M.PRESERVED_SOURCE).read_bytes()),M.PRESERVED_SHA)
        old=ast.parse((HERE/M.PRESERVED_SOURCE).read_bytes());new=ast.parse(Path(M.__file__).read_bytes())
        for name in ('need','digest','load_base','profile_identity','profile_read','failed_gate'):
            a=next(x for x in old.body if isinstance(x,ast.FunctionDef) and x.name==name)
            b=next(x for x in new.body if isinstance(x,ast.FunctionDef) and x.name==name)
            self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
        def nested(tree,name):
            owner=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='windows_main')
            return next(x for x in owner.body if isinstance(x,ast.FunctionDef) and x.name==name)
        for name in ('snapshot','lease','save','finish_client','run'):
            self.assertEqual(ast.dump(nested(old,name),include_attributes=False),ast.dump(nested(new,name),include_attributes=False))
        text=Path(M.__file__).read_text();self.assertNotIn("fixed_argv('set_default_user')",text)
        self.assertNotIn('linux_main',text);self.assertEqual(M.RESERVE,1610612736)


if __name__=='__main__':unittest.main()
