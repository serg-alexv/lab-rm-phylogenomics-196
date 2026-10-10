"""Pure/synthetic contracts only; never WSL, processes, image handles or mounts."""
import ast
import contextlib
import copy
import errno
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

import stage5_setup_cold_linux_v2 as C
import stage5_setup_cold_windows_v2 as W

HERE=Path(__file__).resolve().parent
BOOT='01234567-89ab-cdef-0123-456789abcdef'
NONCE='1'*32
SOURCE='a'*64


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True)+'\n',encoding='utf-8')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class ColdContracts(unittest.TestCase):
    def test_ordinary_function_asts_unchanged(self):
        for name in ('linux','windows'):
            old=ast.parse((HERE/f'stage5_setup_{name}.py').read_text())
            new=ast.parse((HERE/f'stage5_setup_cold_{name}_v2.py').read_text())
            actual={node.name:ast.dump(node,include_attributes=False) for node in new.body if isinstance(node,ast.FunctionDef)}
            for node in old.body:
                if isinstance(node,ast.FunctionDef):self.assertEqual(actual[node.name],ast.dump(node,include_attributes=False))

    def test_exact_lock_types_and_identity(self):
        self.assertTrue(C.cold_strict_lock(dict(C.COLD_LOCK)))
        for value in (None,{},dict(C.COLD_LOCK,extra=1),dict(C.COLD_LOCK,locked_byte=False),
                      dict(C.COLD_LOCK,file_index=float(C.COLD_LOCK['file_index'])),dict(C.COLD_LOCK,path='other')):
            self.assertFalse(C.cold_strict_lock(value))

    def test_finite_ledger_deadlines(self):
        self.assertEqual(len(C.COLD_PHASES),17)
        self.assertEqual(len(set(C.COLD_PHASES)),17)
        self.assertEqual(set(C.COLD_DEADLINES),set(C.COLD_PHASES))
        self.assertLessEqual(sum(C.COLD_DEADLINES.values()),C.COLD_MAX_SECONDS)
        self.assertTrue(all(type(v) is int and 0<v<=1830 for v in C.COLD_DEADLINES.values()))

    def clean(self):
        raw=bytearray(1024);raw[56:58]=b'\x53\xef';struct.pack_into('<H',raw,0x3a,1)
        raw[104:120]=bytes.fromhex('0123456789abcdef0123456789abcdef');return raw

    def test_clean_superblock(self):
        value=C.cold_clean_superblock(bytes(self.clean()))
        self.assertEqual(value['state'],1);self.assertEqual(value['last_orphan'],0)
        self.assertEqual(len(value['superblock_sha256']),64)

    def test_dirty_recovery_orphans_rejected(self):
        for offset,fmt,value in ((0x3a,'<H',0),(0x3a,'<H',3),(0x3a,'<H',5),(0x3a,'<H',9),(0x60,'<I',4),(0x64,'<I',0x10000),(0xe8,'<I',9)):
            raw=self.clean();struct.pack_into(fmt,raw,offset,value)
            with self.assertRaises(C.P.Fatal):C.cold_clean_superblock(bytes(raw))

    def test_superblock_shape_rejected(self):
        for raw in (b'',b'\0'*1024,bytes(self.clean()[:120])):
            with self.assertRaises(C.P.Fatal):C.cold_clean_superblock(raw)

    def test_actual_write_open_refusal_contract(self):
        def refuse():raise PermissionError(errno.EACCES,'synthetic')
        result=C.cold_write_refusal(refuse,lambda _:self.fail('No descriptor was opened'))
        self.assertEqual(result['state'],'ACTUAL_CROSS_DRVFS_WRITE_OPEN_REFUSED')
        self.assertFalse(result['write_called'])

    def test_successful_write_open_closed_and_vetoed(self):
        closed=[]
        with self.assertRaises(C.P.Fatal):C.cold_write_refusal(lambda:77,closed.append)
        self.assertEqual(closed,[77])

    def test_refusal_unrelated_error_is_not_evidence(self):
        def missing():raise FileNotFoundError(errno.ENOENT,'synthetic')
        with self.assertRaises(C.P.Fatal):C.cold_write_refusal(missing,lambda _:None)

    def request(self,mode='inventory'):
        return {'mode':mode,'runtime':C.WORK.as_posix()+'/runtime.json','runtime_sha256':C.COLD_RUNTIME_SHA,
                'owner_nonce':NONCE,'worker_output':C.WORK.as_posix()+'/stage5_runtime_inventory_private_fake',
                'worker_terminal':C.WORK.as_posix()+'/stage5_runtime_capture_terminal_fake.json',
                'rediscovery_output':C.WORK.as_posix()+'/stage5_runtime_actual_cold_fake.json',
                'manifest':C.WORK.as_posix()+'/manifest.jsonl','manifest_sha256':'b'*64,
                'public_review':C.WORK.as_posix()+'/review.json','public_review_sha256':'c'*64,
                'notices':C.WORK.as_posix()+'/notices.json','notices_sha256':'d'*64}

    def test_exact_inventory_argv_is_posix(self):
        argv=C.cold_expected_argv('worker',self.request(),C.WORK.as_posix()+'/fake','/dev/loop0','/dev/loop0','e'*64)
        self.assertEqual(argv[0],C.ENV.as_posix()+'/bin/python')
        self.assertEqual(argv[3:6],['--run','--source-sha256',C.COLD_PINS['stage5_runtime_inventory_entry_v3.py']])
        self.assertIn('--output-private',argv);self.assertFalse(any('\\' in item for item in argv))

    def test_exact_capture_argv_and_sources(self):
        argv=C.cold_expected_argv('worker',self.request('capture'),C.WORK.as_posix()+'/fake',
                                 '/dev/loop0','/dev/loop1','e'*64,'f'*64)
        self.assertEqual(argv[5],C.COLD_PINS['stage5_runtime_capture_entry_v2.py'])
        self.assertIn('--inputs-sha256',argv);self.assertIn('--public-review-sha256',argv)
        self.assertEqual(argv[argv.index('--terminal')+1],self.request()['worker_terminal'])

    def test_no_lazy_force_rw_ro_mount_contract(self):
        request=self.request()
        ro=C.cold_expected_argv('mount_ro',request,'/fake','/dev/loop0','/dev/loop1')
        self.assertEqual(ro,['/usr/bin/mount','-t','ext4','-o','ro,noload','/dev/loop1',C.TOOLS.as_posix()])
        for name in ('unmount_rw','unmount_ro'):
            self.assertEqual(C.cold_expected_argv(name,request,'/fake','/dev/loop0','/dev/loop1'),
                             ['/usr/bin/umount',C.TOOLS.as_posix()])

    def test_ambiguous_loop_rejected(self):
        with self.assertRaises(C.P.Fatal):C.cold_expected_argv('mount_ro',self.request(),'/fake','/dev/sda','/dev/loop0')

    def test_default_noops(self):
        for module in (C,W):
            output=io.StringIO()
            with patch.object(sys,'argv',['synthetic']),contextlib.redirect_stdout(output):
                self.assertEqual(module.cold_main(),0)
            self.assertTrue(json.loads(output.getvalue())['state'].startswith('NO_OP'))

    def build_ledger(self,out,mode='inventory'):
        request=self.request(mode);put(out/'cold_request.json',request);put(out/'cold_proof.json',{'synthetic':True})
        if mode=='capture':put(out/'capture_inputs.json',{'synthetic':True})
        records=[];hashes=[]
        for index,name in enumerate(C.COLD_PHASES,1):
            row={'phase':name,'ordinal':index,'deadline_seconds':C.COLD_DEADLINES[name],
                 'owner_nonce':NONCE,'source_sha256':SOURCE,'request_sha256':digest(out/'cold_request.json'),
                 'boot_id':BOOT,'previous_sha256':hashes[-1] if hashes else None,'state':'DONE'}
            if name=='writer_closure':row.update(loop_aliases=[{'loop':'/dev/loop0','read_only':False}],
                process_exclusion={'relevant_references':0,'foreign_mount_namespaces':0})
            if name in ('backing_detached','backing_detached_again'):
                row.update(loop_aliases=[],process_exclusion={'relevant_references':0},
                           clean_superblock={'state':1,'incompat':0,'ro_compat':0,'last_orphan':0,'superblock_sha256':'c'*64})
            if name in ('windows_guard','windows_guard_released'):
                ack_name='guard' if name=='windows_guard' else 'release'
                ack={'owner_nonce':NONCE,'linux_source_sha256':SOURCE,'workflow_lock':dict(C.COLD_LOCK),
                     'retained_deny_write_delete_handle':True,'actual_close_handle_succeeded':True}
                put(out/(ack_name+'_ack.json'),ack);row['ack']=ack
            if name=='drvfs_write_refused':row.update(state='ACTUAL_CROSS_DRVFS_WRITE_OPEN_REFUSED',
                    attempt='O_RDWR|O_NOFOLLOW',write_called=False,errno=errno.EACCES)
            if name in C.COLD_COMMAND_PHASES:
                (out/'phases'/name/'commands').mkdir(parents=True)
                row.update(command_count=0 if name=='detach_rw' else 1,
                    argv=C.cold_expected_argv(name,request,W.LINUX_WORK+'/'+out.name,'/dev/loop0','/dev/loop1',
                         digest(out/'cold_proof.json'),digest(out/'capture_inputs.json') if mode=='capture' else None))
            if name=='loop_ro':
                stdout=out/'phases/loop_ro/commands/loop_ro.stdout.txt'
                stdout.write_bytes(b'/dev/loop1\n')
            path=out/'phases'/f'{index:02d}_{name}.json';put(path,row);hashes.append(digest(path));records.append(row)
        return request,records

    def read(self,out,request):
        calls=[]
        def reader(spool,count,step,argv,success):
            self.assertIn(count,(0,1));self.assertEqual(step,'toolchain')
            calls.append((spool.name,count,tuple(argv),success));return []
        with patch.object(W,'command_readback',reader):
            records,commands,total=W.cold_ledger_readback(C,out,request,SOURCE,NONCE,True)
        return records,total,calls

    def test_synthetic_full_ledger_reuses_single_command_reader(self):
        for mode in ('inventory','capture'):
            with tempfile.TemporaryDirectory() as temp:
                out=Path(temp)/'synthetic';out.mkdir();request,_=self.build_ledger(out,mode)
                records,total,calls=self.read(out,request)
                self.assertEqual(len(records),17);self.assertEqual(len(calls),9);self.assertEqual(total,8)

    def test_tampered_native_count_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'synthetic';out.mkdir();request,rows=self.build_ledger(out)
            rows[1]['command_count']=2;put(out/'phases/02_unmount_rw.json',rows[1])
            with self.assertRaises(Exception):self.read(out,request)

    def test_tampered_argv_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'synthetic';out.mkdir();request,rows=self.build_ledger(out)
            rows[1]['argv'].append('--lazy');put(out/'phases/02_unmount_rw.json',rows[1])
            with self.assertRaises(Exception):self.read(out,request)

    def test_skipped_or_extra_phase_fails(self):
        for name in ('02_unmount_rw.json','99_unexpected.json'):
            with tempfile.TemporaryDirectory() as temp:
                out=Path(temp)/'synthetic';out.mkdir();request,_=self.build_ledger(out)
                if name.startswith('02'):(out/'phases'/name).unlink()
                else:put(out/'phases'/name,{})
                with self.assertRaises(Exception):self.read(out,request)

    def test_hash_chain_tamper_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'synthetic';out.mkdir();request,rows=self.build_ledger(out)
            rows[2]['previous_sha256']='0'*64;put(out/'phases/03_detach_rw.json',rows[2])
            with self.assertRaises(Exception):self.read(out,request)

    def test_runtime06_exact_bytes_are_current_integration_target(self):
        self.assertEqual(digest(HERE/'stage5_runtime_actual_postiq_06.json'),C.COLD_RUNTIME_SHA)

    def test_capacity_books_parent512_and_worker512(self):
        policy=C.cold_resource_policy()
        self.assertEqual(C.COLD_ALLOCATION,512*1024**2)
        self.assertEqual(policy['incremental_windows_requirement_bytes'],2*C.COLD_ALLOCATION)
        self.assertEqual(policy['linux_job_requirement_bytes'],2*C.COLD_ALLOCATION)
        self.assertEqual(policy['windows_reserve_bytes']+policy['incremental_windows_requirement_bytes'],2560*1024**2)
        self.assertEqual(policy['commit_requirement_bytes'],C.COLD_WINDOWS_REQUIREMENT)
        self.assertEqual(policy['sampled_rss_stop_bytes'],C.COLD_ALLOCATION)

    def test_windows_clean_state5_unknown_and_bool_rejected(self):
        for row_index in (3,12):
            for state in (5,9,True):
                with tempfile.TemporaryDirectory() as temp:
                    out=Path(temp)/'synthetic';out.mkdir();request,rows=self.build_ledger(out)
                    rows[row_index]['clean_superblock']['state']=state
                    path=out/'phases'/f'{row_index+1:02d}_{rows[row_index]["phase"]}.json'
                    put(path,rows[row_index])
                    with self.assertRaisesRegex(Exception,'Actual clean ext4 state differs'):self.read(out,request)

    def test_terminal_count_strict_int(self):
        self.assertEqual(W.cold_terminal_count(8,8),8)
        for value in (8.0,'8',True,None,-1):
            with self.assertRaisesRegex(Exception,'Exact integer cold terminal command count differs'):
                W.cold_terminal_count(value,8)
        with self.assertRaises(Exception):W.cold_terminal_count(1,True)

    def finish_fixture(self,temp,lock_error=None,receipt_error=False,changed_stop=False,
                       retained=False,closed=True,extra_error=False,final_result_error=False,
                       all_publication_writes_error=False):
        out=Path(temp);stop=out/'owned_stop.json';put(stop,{'owner_nonce':NONCE})
        pin=digest(stop);events=[]
        class FakeLock:
            released=False
            def __exit__(self,*_):
                events.append('unlock')
                if lock_error=='before':raise OSError('synthetic unlock failure')
                self.released=True
                if lock_error=='after_flag':raise OSError('synthetic post-unlock close failure')
        lock=FakeLock();result={'state':'COLD_EFFECTS_RESTORED_PENDING_EXPLICIT_UNLOCK'}
        put(out/'result.json',result)
        if extra_error:result['exit_finalizer_error_kind']='SyntheticError'
        if changed_stop:put(stop,{'owner_nonce':'2'*32})
        synthetic={'synthetic_retained_handle':True}
        if retained:W.COLD_RETAINED_IMAGE_HANDLES.append(synthetic)
        original_atomic=W.A.atomic
        def writer(path,value):
            events.append(path.name)
            if path.name=='lock_released.json':
                self.assertTrue(stop.exists(),'STOP must remain during explicit unlock receipt')
                self.assertEqual(events[0],'unlock')
                if receipt_error:raise OSError('synthetic receipt failure')
            if path.name=='result.json' and final_result_error and value['state'].startswith('PASS_'):
                self.assertFalse(stop.exists(),'This fixture must reach the post-clear final publication boundary')
                raise OSError('synthetic final PASS result persistence failure')
            if all_publication_writes_error and path.name in ('result.json','publication_failure.json'):
                raise OSError('synthetic complete publication outage')
            return original_atomic(path,value)
        try:
            with patch.object(W,'STOP',stop),patch.object(W.A,'atomic',writer):
                if final_result_error or all_publication_writes_error:
                    with self.assertRaises(OSError):
                        W.cold_finish_after_unlock(lock,out,result,pin,NONCE,closed,True,True)
                else:W.cold_finish_after_unlock(lock,out,result,pin,NONCE,closed,True,True)
        finally:
            if retained:W.COLD_RETAINED_IMAGE_HANDLES.remove(synthetic)
        return result,stop,events

    def test_checked_unlock_receipt_precedes_stop_clear_and_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            result,stop,events=self.finish_fixture(temp)
            self.assertEqual(result['state'],'PASS_COLD_STEP_CLOSED_AND_RUNTIME06_RESTORED')
            self.assertFalse(stop.exists());self.assertTrue(result['original_unlock_receipt_proven'])
            self.assertEqual(events[:2],['unlock','lock_released.json'])
            self.assertEqual(digest(Path(temp)/'lock_released.json'),result['lock_release_receipt_sha256'])

    def test_unlock_failure_keeps_stop_and_failed(self):
        for error in ('before','after_flag'):
            with tempfile.TemporaryDirectory() as temp:
                result,stop,_=self.finish_fixture(temp,lock_error=error)
                self.assertEqual(result['state'],'FAILED');self.assertTrue(stop.exists())
                self.assertFalse(result['original_lock_explicitly_released'])
                self.assertFalse((Path(temp)/'lock_released.json').exists())

    def test_unlock_receipt_failure_keeps_stop(self):
        with tempfile.TemporaryDirectory() as temp:
            result,stop,_=self.finish_fixture(temp,receipt_error=True)
            self.assertEqual(result['state'],'FAILED');self.assertTrue(stop.exists())
            self.assertFalse(result['original_unlock_receipt_proven'])

    def test_changed_stop_not_removed_after_unlock(self):
        with tempfile.TemporaryDirectory() as temp:
            result,stop,_=self.finish_fixture(temp,changed_stop=True)
            self.assertEqual(result['state'],'FAILED');self.assertTrue(stop.exists())

    def test_incomplete_handle_scope_or_finalizer_cannot_clear_stop(self):
        for change in ({'retained':True},{'closed':False},{'extra_error':True}):
            with tempfile.TemporaryDirectory() as temp:
                result,stop,_=self.finish_fixture(temp,**change)
                self.assertEqual(result['state'],'FAILED');self.assertTrue(stop.exists())

    def test_final_result_failure_has_distinct_durable_publication_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            result,stop,events=self.finish_fixture(temp,final_result_error=True)
            self.assertEqual(result['state'],'FAILED');self.assertFalse(stop.exists())
            self.assertTrue(result['owned_closure_proven']);self.assertTrue(result['rw_restoration_proven'])
            self.assertTrue(result['original_lock_explicitly_released'])
            failure=json.loads((Path(temp)/'publication_failure.json').read_text())
            self.assertEqual(failure['state'],'FAILED_FINAL_RESULT_PUBLICATION_RECONCILE_REQUIRED')
            self.assertFalse(failure['closure_facts_reclassified_as_unknown'])
            self.assertFalse(failure['unknown_closure_or_restoration_stop_preserved'])
            self.assertEqual(json.loads((Path(temp)/'result.json').read_text())['state'],'FAILED')
            self.assertEqual(events.count('publication_failure.json'),1)
            self.assertEqual(events.count('result.json'),2)

    def test_total_publication_outage_is_bounded_and_never_returns_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            result,stop,events=self.finish_fixture(temp,all_publication_writes_error=True)
            self.assertEqual(result['state'],'FAILED');self.assertFalse(stop.exists())
            self.assertTrue(result['owned_closure_proven'])
            self.assertEqual(events.count('publication_failure.json'),1)
            self.assertEqual(events.count('result.json'),2)
            self.assertEqual(json.loads((Path(temp)/'result.json').read_text())['state'],
                             'COLD_EFFECTS_RESTORED_PENDING_EXPLICIT_UNLOCK')


if __name__=='__main__':unittest.main()
