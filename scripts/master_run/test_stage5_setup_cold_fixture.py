"""Pure fixed-path/ledger/fake-handle checks; no Linux or native actions."""
import ast
import copy
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
from contextlib import redirect_stdout
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock
import stage5_setup_cold_fixture_linux as C
import stage5_setup_cold_fixture_windows as O
import stage5_offline_image_read_parts_v2 as H


NONCE='1'*32
LINUX_OUT=C.WORK.as_posix()+'/stage5_setup_cold_fixture_pure01'
REQUEST={'owner_nonce':NONCE,'fixture_uuid':'12345678-1234-1234-1234-123456789012',
         'rediscovery_output':C.WORK.as_posix()+'/stage5_runtime_fixture_'+NONCE+'.json'}


class FixedScopeAndSource(unittest.TestCase):
    def test_original_owner_function_asts_unchanged(self):
        for suffix in ('linux','windows'):
            old=ast.parse((O.WORK/('stage5_setup_cold_'+suffix+'_v2.py')).read_bytes())
            new=ast.parse((O.WORK/('stage5_setup_cold_fixture_'+suffix+'.py')).read_bytes())
            funcs=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
            a,b=funcs(old),funcs(new)
            for name,body in a.items():
                with self.subTest(suffix=suffix,name=name):self.assertEqual(body,b[name])

    def test_cli_guards_are_last_and_defaults_are_noop(self):
        for module in (C,O):
            tree=ast.parse(Path(module.__file__).read_bytes());self.assertIsInstance(tree.body[-1],ast.If)
            output=io.StringIO()
            with mock.patch('sys.argv',[str(module.__file__),'--fixture']),redirect_stdout(output):
                self.assertEqual(module.fixture_main(),0)
            self.assertEqual(json.loads(output.getvalue())['state'],'NO_OP_DISPOSABLE_COLD_FIXTURE')

    def test_exact_fresh_fixture_paths(self):
        image,mount=C.fixture_paths(LINUX_OUT,NONCE)
        self.assertEqual(str(image),LINUX_OUT+'/disposable.ext4')
        self.assertEqual(str(mount),'/var/tmp/lab_rm_cold_fixture_'+NONCE)
        self.assertNotEqual(str(image),str(C.IMAGE));self.assertNotEqual(str(mount),str(C.TOOLS))

    def test_foreign_noncanonical_or_traversing_paths_rejected(self):
        for path in ('/var/tmp/stage5_setup_cold_fixture_x',C.WORK.as_posix()+'/other',LINUX_OUT+'/../x',
                     LINUX_OUT.replace('/mnt/c/','/mnt/c//'),LINUX_OUT+'\\other'):
            with self.subTest(path=path),self.assertRaises(C.P.Fatal):C.fixture_paths(path,NONCE)
        with self.assertRaises(C.P.Fatal):C.fixture_paths(LINUX_OUT,'not_nonce')

    def test_exact_native_argv_and_no_original_image_mutations(self):
        for name in C.FIXTURE_COMMANDS:
            argv=C.fixture_argv(name,REQUEST,LINUX_OUT,'/dev/loop8','/dev/loop9')
            self.assertNotIn(str(C.IMAGE),argv)
            self.assertNotIn(str(C.TOOLS),argv)
            self.assertTrue(all(isinstance(x,str) for x in argv))
        self.assertEqual(C.fixture_argv('mount_ro',REQUEST,LINUX_OUT,'/dev/loop8','/dev/loop9'),
            ['/usr/bin/mount','-t','ext4','-o','ro,noload','/dev/loop9','/var/tmp/lab_rm_cold_fixture_'+NONCE])
        with self.assertRaises(C.P.Fatal):C.fixture_argv('detach_ro',REQUEST,LINUX_OUT,None,'/dev/sda')

    def test_strict_fixture_file_identity_types(self):
        path=O.WORK/'stage5_setup_cold_fixture_pure01'/'disposable.ext4'
        value=dict(path=str(path),volume_serial=9,file_index=37,creation_filetime=42,written_filetime=43,
                   bytes=C.FIXTURE_SIZE,links=1,attributes=128)
        self.assertEqual(O.fixture_file_identity(value,path,C.FIXTURE_SIZE),value)
        for key in ('volume_serial','file_index','creation_filetime','written_filetime','bytes','links','attributes'):
            with self.subTest(key=key),self.assertRaises(ValueError):
                O.fixture_file_identity({**value,key:float(value[key])},path,C.FIXTURE_SIZE)
        for changed in ({'links':True},{'attributes':0x400},{'bytes':C.FIXTURE_SIZE+1},{'path':'other'}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):O.fixture_file_identity({**value,**changed},path,C.FIXTURE_SIZE)

    def test_same_conservative_resource_policy_and_original_runtime_pin(self):
        self.assertEqual(C.cold_resource_policy()['incremental_windows_requirement_bytes'],1024*1024**2)
        self.assertEqual(C.COLD_WINDOWS_REQUIREMENT,2560*1024**2)
        self.assertEqual(C.COLD_RUNTIME_SHA,'f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1')
        self.assertEqual(len(C.FIXTURE_PHASES),25)


class FakeFunction:
    def __init__(self,call):self.call=call
    def __call__(self,*args):return self.call(*args)


class FakeInfo(ctypes.Structure):
    _fields_=[('volume',ctypes.c_uint32),('indexHigh',ctypes.c_uint32),('indexLow',ctypes.c_uint32),
              ('created',ctypes.c_uint64),('written',ctypes.c_uint64),('sizeHigh',ctypes.c_uint32),
              ('sizeLow',ctypes.c_uint32),('links',ctypes.c_uint32),('attributes',ctypes.c_uint32)]


class FakeImagePath:
    def __init__(self):
        self.parent=SimpleNamespace(parent=O.WORK,name='stage5_setup_cold_fixture_pure01')
        self.name='disposable.ext4';self.parents=[]
    def __str__(self):return str(O.WORK/'stage5_setup_cold_fixture_pure01'/'disposable.ext4')
    def is_absolute(self):return True
    def resolve(self):return self
    def lstat(self):return SimpleNamespace(st_file_attributes=128)
    def is_symlink(self):return False


class FakeAPI:
    FILEINFO=FakeInfo
    def __init__(self,path):
        self.calls=[];self.close_ok=True;self.path=path
        def create(*args):self.calls.append(('create',args));return 88
        def final(handle,buffer,length,flags):buffer.value='\\\\?\\'+str(path);return len(buffer.value)
        self.K=SimpleNamespace(CreateFileW=FakeFunction(create),GetFinalPathNameByHandleW=FakeFunction(final),
                               GetFileType=FakeFunction(lambda handle:1))
    def current(self):return 99
    def identity(self,*args):return {'pid':os.getpid(),'creation_filetime':42}
    def file_info(self,handle,ptr):
        row=ptr._obj;row.volume=9;row.indexLow=37;row.created=42;row.written=43
        row.sizeLow=C.FIXTURE_SIZE;row.links=1;row.attributes=128;return True
    def ft(self,value):return int(value)
    def ok(self,value,message):
        if not value:raise OSError(message)
    def close(self,handle):self.calls.append(('close',handle));return self.close_ok


class RetainedFixtureHandle(unittest.TestCase):
    def context(self):
        return {'workflow_lock_held':True,'workflow_lock':copy.deepcopy(C.COLD_LOCK),
                'owner_pid':os.getpid(),'owner_creation_filetime':'42','nonce':NONCE}
    def test_real_sharing_flags_and_checked_close_reused(self):
        path=FakeImagePath();api=FakeAPI(path);lease=O.fixture_image_lease(api,H,path,C.FIXTURE_SIZE,self.context)
        self.assertIs(type(lease).check,H.ImageReadLease.check)
        self.assertIs(type(lease).close_owned,H.ImageReadLease.close_owned)
        lease.__enter__();self.assertEqual(lease.handle,88)
        args=api.calls[0][1];self.assertEqual(args[1:3],(0x80000000,1));self.assertEqual(args[4],3)
        lease.close_owned();self.assertIsNone(lease.handle)
    def test_failed_close_retains_exact_handle(self):
        path=FakeImagePath();api=FakeAPI(path);lease=O.fixture_image_lease(api,H,path,C.FIXTURE_SIZE,self.context)
        lease.__enter__();api.close_ok=False
        with self.assertRaises(OSError):lease.close_owned()
        self.assertEqual(lease.handle,88)
    def test_post_acquisition_failure_and_close_failure_retains_lease(self):
        path=FakeImagePath();api=FakeAPI(path);calls=0
        def guard():
            nonlocal calls;calls+=1
            if calls>1:raise ValueError('fake lease loss')
            return self.context()
        lease=O.fixture_image_lease(api,H,path,C.FIXTURE_SIZE,guard);api.close_ok=False
        with self.assertRaises(H.ImageHandleClosureFailure) as caught:lease.__enter__()
        self.assertIs(caught.exception.retained_image_lease,lease);self.assertEqual(lease.handle,88)


class SyntheticLedger(unittest.TestCase):
    def setUp(self):
        self.out=Path(tempfile.mkdtemp(prefix='stage5_setup_cold_fixture_pure_',dir=O.WORK)).resolve()
        self.assertEqual(self.out.parent,O.WORK)
        self.nonce=NONCE;self.source='a'*64;self.request=copy.deepcopy(REQUEST)
        self.request_raw=json.dumps(self.request).encode();(self.out/'fixture_request.json').write_bytes(self.request_raw)
        self.phase_dir=self.out/'phases';self.phase_dir.mkdir()
        rw='/dev/loop8';ro='/dev/loop9';previous=None
        for number,name in enumerate(C.FIXTURE_PHASES,1):
            value={'phase':name,'ordinal':number,'source_sha256':self.source,'owner_nonce':self.nonce,
                'request_sha256':hashlib.sha256(self.request_raw).hexdigest(),'boot_id':'12345678-1234-1234-1234-123456789012',
                'previous_sha256':previous,'state':'DONE'}
            if name in ('rw_seeded','rw_restored'):value['view']={'loop':rw}
            if name in C.FIXTURE_COMMANDS:
                directory=self.phase_dir/name;directory.mkdir()
                value.update(argv=C.fixture_argv(name,self.request,O.LINUX_WORK+'/'+self.out.name,rw,ro),command_count=1)
                if name=='loop_ro':
                    (directory/'commands').mkdir();(directory/'commands/loop_ro.stdout.txt').write_bytes((ro+'\n').encode())
            if name in ('detached','detached_again','final_detached'):
                value.update(loop_aliases=[],process_exclusion={'relevant_references':0,'foreign_mount_namespaces':0},
                    clean_superblock={'state':1,'incompat':0,'ro_compat':0,'last_orphan':0,
                    'filesystem_uuid':self.request['fixture_uuid'],'superblock_sha256':'b'*64})
            if name=='detached':value.update(O_RDWR_before_guard_succeeded=True,write_called=False)
            if name=='drvfs_refused':value.update(state='ACTUAL_CROSS_DRVFS_WRITE_OPEN_REFUSED',errno=13,write_called=False)
            if name=='ro_readback':value.update(full_payload_metadata_link_xattr_verified=True,
                view={'loop_aliases':[{'read_only':True}]},EROFS_write_open_refusal=30,write_called=False)
            if name=='write_open_restored':value.update(O_RDWR_after_guard_release=True,write_called=False)
            if name=='rw_restored':value['unchanged_full_bytes_metadata_link_xattr']=True
            if name in ('windows_guard','windows_guard_released'):
                key='guard' if name=='windows_guard' else 'release'
                ack={'phase':key,'owner_nonce':self.nonce,'workflow_lock':copy.deepcopy(C.COLD_LOCK),
                    'linux_source_sha256':self.source,'retained_deny_write_delete_handle':True,'actual_close_handle_succeeded':True}
                (self.out/(key+'_ack.json')).write_text(json.dumps(ack));value['ack']=ack
            if name=='complete':value.update(original_RW_proof_unchanged=True,rediscovery_sha256=C.COLD_RUNTIME_SHA)
            p=self.phase_dir/f'{number:02d}_{name}.json';p.write_text(json.dumps(value));previous=O.A.sha256(p)
    def tearDown(self):
        self.assertEqual(self.out.resolve().parent,O.WORK)
        for root,dirs,files in os.walk(self.out,topdown=False):
            for name in files:(Path(root)/name).unlink()
            for name in dirs:(Path(root)/name).rmdir()
        self.out.rmdir()
    def read(self):
        with mock.patch.object(O,'command_readback',side_effect=lambda path,count,*args:[{'synthetic':True}]*count):
            return O.fixture_ledger_readback(C,self.out,self.request,self.source,self.nonce,True)
    def change(self,number,key,value):
        p=next(self.phase_dir.glob(f'{number:02d}_*.json'));row=json.loads(p.read_bytes());row[key]=value;p.write_text(json.dumps(row))
    def test_complete_exact_ledger(self):
        records,commands,total=self.read();self.assertEqual(len(records),25)
        self.assertEqual(total,len(C.FIXTURE_COMMANDS));self.assertEqual(len(commands),total)
    def test_count_float_and_bool_rejected(self):
        for value in (1.0,True):
            self.change(3,'command_count',value)
            with self.subTest(value=value),self.assertRaises(ValueError):self.read()
    def test_dirty_clean_bits_rejected(self):
        p=self.phase_dir/'08_detached.json';row=json.loads(p.read_bytes());row['clean_superblock']['state']=5;p.write_text(json.dumps(row))
        with self.assertRaises(ValueError):self.read()
    def test_argv_tamper_rejected(self):
        self.change(3,'argv',['/usr/bin/false'])
        with self.assertRaises(ValueError):self.read()
    def test_skipped_phase_and_hash_chain_rejected(self):
        self.change(2,'previous_sha256','f'*64)
        with self.assertRaises(ValueError):self.read()
    def test_unaccounted_command_directory_rejected(self):
        (self.phase_dir/'unknown').mkdir()
        with self.assertRaises(ValueError):self.read()


if __name__=='__main__':unittest.main()
