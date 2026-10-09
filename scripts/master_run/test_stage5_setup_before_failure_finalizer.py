"""Nonscientific pure setup proof/readback negatives; no WSL, mounts or G I/O."""
from pathlib import Path
import copy, hashlib, json, tempfile, unittest, uuid
import stage5_setup_windows as V
import stage5_setup_linux as L


def closure_fixture():
    controller={'schema':'MASTER_IQTREE_CONTROLLER_RETAINED_EXIT_V1','state':'PASS_CONTROLLER_RETAINED_HANDLE_EXIT0',
                'source_sha256':'a'*64,'retained_live_identity':{'pid':27048,'creation_filetime':134360369803845506},
                'terminal':{'pid':27048,'creation_filetime':134360369803845506,'exited':True,'exit_code':0,'exit_filetime':134360369803845507}}
    birth={'pid':4768,'creation_filetime':134360369876207076}
    native={'native':{**birth,'exited':True,'exit_code':0,'exit_filetime':134360369876207077},'execution':'NATIVE_EXITED','job_active_processes':0,'job_pids':[]}
    return controller,{'native':birth},native,{'actual_api_success':True,'requested_flags':0x80000000},{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'}


def drivefs_fixture(root):
    relative='.work/stage05_atomic_filesystem_smoke_20261010T000000000001Z_abcdef12'
    directory=root/relative; directory.mkdir(parents=True)
    scope='NONSCIENTIFIC_DRIVEFS_FILESYSTEM_ONLY'; nonce='fixture'
    payload=('NONSCIENTIFIC DRIVEFS SMOKE\n'+nonce+'\n').encode()
    values={'ordinary.bin':payload,'replaced.bin':payload,'runner_atomic.json':json.dumps({'scope':scope,'nonce':nonce}).encode(),'.native_runner.guard':b''}
    for name,data in values.items(): (directory/name).write_bytes(data)
    record={'schema':'STAGE05_DRIVEFS_FILESYSTEM_SMOKE_V1','scope':scope,'state':'PASS_NONSCIENTIFIC_FILESYSTEM_ONLY',
            'nonce':nonce,'namespace_relative':relative,'scientific_adoption_authorized':False,
            'script_sha256':V.PINS['stage5_drivefs_filesystem_smoke.py'],'supervisor_sha256':V.PINS['stage5_atomic_process.py'],
            'caller_lock_receipt_sha256':'b'*64,
            'files':{n:{'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest()} for n,d in values.items()}}
    for flag in ('ordinary_write_fsync_readback','atomic_overwrite_readback','runner_atomic_json_readback',
                 'flock_contention_proven','flock_close_release_reacquire_proven'): record[flag]=True
    raw=json.dumps(record).encode(); (directory/'result.json').write_bytes(raw)
    stdout=root/'stdout.json'; stdout.write_text(json.dumps({**record,'result_sha256':hashlib.sha256(raw).hexdigest()}))
    return stdout,directory,record


def command_fixture(root):
    directory=root/'commands'; directory.mkdir()
    argv=['/usr/bin/mount','--bind','SOURCE','TARGET']; identity={'scope':V.SCOPE,'step':'storage'}
    native={'argv':argv,'identity':identity,'command_nonce':'nonce','boot_id':'boot','child_pid':123,
            'child_start_ticks':'456','pgid':123,'sid':123,'cwd':'/fixture'}
    close={'command_nonce':'nonce','boot_id':'boot','root_exit_code':0,'group_empty':True,
           'tracked_descendants_empty':True,'survivors':[],'unexplained_pgid_members':[],
           'tracked_descendants':[{'pid':123,'start_ticks':'456','pgid':123,'sid':123}],'termination_reason':None}
    for suffix,value in [('launch',native),('launch_intent',native),('closure',close)]:
        (directory/('bind_storage.'+suffix+'.json')).write_text(json.dumps(value))
    (directory/'bind_storage.stdout.txt').write_bytes(b'SYNTHETIC OUTPUT'); (directory/'bind_storage.stderr.txt').write_bytes(b'')
    command={**native,'exit_code':0,'group_closure_sha256':V.A.sha256(directory/'bind_storage.closure.json'),
             'stdout_sha256':V.A.sha256(directory/'bind_storage.stdout.txt'),'stderr_sha256':V.A.sha256(directory/'bind_storage.stderr.txt')}
    (directory/'bind_storage.command.json').write_text(json.dumps(command))
    return directory,argv


class Contracts(unittest.TestCase):
    def test_exact_previous_births_and_terminal_scope(self):
        controller,launch,native,power,unlock=closure_fixture()
        V.prior_closure(controller,'a'*64,launch,native,power,unlock)
        for field,value in [('exited',False),('creation_filetime',134360369803845505),('exit_code',1)]:
            changed=copy.deepcopy(controller); changed['terminal'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError): V.prior_closure(changed,'a'*64,launch,native,power,unlock)
        native['job_pids']=[789]
        with self.assertRaises(ValueError): V.prior_closure(controller,'a'*64,launch,native,power,unlock)

    def test_previous_power_unlock_and_source_are_required(self):
        args=closure_fixture()
        for index,key,value in [(0,'source_sha256','c'*64),(3,'actual_api_success',False),(3,'requested_flags',0x80000001),(4,'state','NOT_RELEASED')]:
            changed=copy.deepcopy(args); changed[index][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): V.prior_closure(changed[0],'a'*64,*changed[1:])
        changed=copy.deepcopy(args); changed[2]['native']['exit_code']=1
        with self.assertRaises(ValueError): V.prior_closure(changed[0],'a'*64,*changed[1:])

    def test_ubuntu_registration_binds_physical_c_volume(self):
        good={'distribution_name':'Ubuntu','version':2,'base_path':str(V.UBUNTU_BASE)}
        self.assertEqual(V.registration_contract(good),good)
        for key,value in [('distribution_name','Other'),('version',1),('base_path',r'D:\other\wsl')]:
            with self.subTest(key=key),self.assertRaises(ValueError): V.registration_contract({**good,key:value})

    def test_real_ext4_superblock_identity_not_empty_uuid(self):
        block=bytearray(120); block[56:58]=b'\x53\xef'; block[104:120]=uuid.UUID('12345678-1234-5678-1234-567812345678').bytes
        self.assertEqual(L.image_uuid(bytes(block)),'12345678-1234-5678-1234-567812345678')
        for bad in (b'',bytes(120),bytes(block[:104])+bytes(16)):
            with self.assertRaises(L.P.Fatal): L.image_uuid(bad)

    def test_exact_windows_readback_and_changed_payload_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); stdout,directory,_=drivefs_fixture(root)
            self.assertIn('PASS_',V.drivefs_readback(stdout,root)['state'])
            (directory/'ordinary.bin').write_bytes(b'CHANGED')
            with self.assertRaisesRegex(ValueError,'hash/size'): V.drivefs_readback(stdout,root)

    def test_self_consistent_false_fsync_and_unknown_partial_reject(self):
        for mode in ('false_flag','partial'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); stdout,directory,record=drivefs_fixture(root)
                if mode=='partial': (directory/'unexpected.partial').write_bytes(b'UNKNOWN')
                else:
                    record['ordinary_write_fsync_readback']=False
                    raw=json.dumps(record).encode(); (directory/'result.json').write_bytes(raw)
                    stdout.write_text(json.dumps({**record,'result_sha256':hashlib.sha256(raw).hexdigest()}))
                with self.assertRaises(ValueError): V.drivefs_readback(stdout,root)

    def test_traversal_namespace_rejected_before_target_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); stdout,_,record=drivefs_fixture(root)
            stdout.write_text(json.dumps({**record,'namespace_relative':'../../escape'}))
            with self.assertRaisesRegex(ValueError,'namespace'): V.drivefs_readback(stdout,root)

    def test_oversized_known_payload_rejected_before_large_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); stdout,directory,_=drivefs_fixture(root)
            (directory/'ordinary.bin').write_bytes(b'x'*4097)
            with self.assertRaisesRegex(ValueError,'bounded regular'): V.drivefs_readback(stdout,root)

    def test_actual_command_logs_and_root_birth_reopened(self):
        for mode in ('clean','changed_log','changed_birth','wrong_argv','extra_intent'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); directory,argv=command_fixture(root)
                if mode=='changed_log': (directory/'bind_storage.stdout.txt').write_bytes(b'OTHER')
                elif mode=='changed_birth':
                    path=directory/'bind_storage.closure.json'; value=json.loads(path.read_text()); value['tracked_descendants'][0]['start_ticks']='other'; path.write_text(json.dumps(value))
                elif mode=='wrong_argv': argv=['/bin/WRONG']
                elif mode=='extra_intent': (directory/'other.launch_intent.json').write_text('{}')
                if mode=='clean': self.assertEqual(len(V.command_readback(root,1,'storage',argv,True)),1)
                else:
                    with self.assertRaises(ValueError): V.command_readback(root,1,'storage',argv,True)

    def test_successful_runtime_cannot_pass_without_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): V.command_readback(Path(tmp),0,'runtime',[],True)
            self.assertEqual(V.command_readback(Path(tmp),0,'toolchain',[],True),[])

    def test_exact_retained_preexec_failure_is_failed_and_no_linux_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'wsl.stdout.txt').write_bytes(b'')
            error=b'<3>WSL (369 - Relay) ERROR: CreateProcessCommon:880: execvpe(/usr/bin/python3) failed: No such file or directory\r\n'
            (out/'wsl.stderr.txt').write_bytes(error)
            argv=[V.WSL,'-d','Ubuntu','-u','root','--exec','/usr/bin/python3','-B',V.LINUX_WORK+'/stage5_setup_linux.py']
            birth={'pid':123,'creation_filetime':456,'executable':V.WSL}
            terminal={**birth,'exited':True,'exit_code':1,'exit_filetime':789}
            value=V.exact_preexec_failure(out,argv,birth,terminal)
            self.assertEqual(value['state'],'FAILED_PREEXEC_NO_LINUX_PROGRAM_STARTED')
            self.assertFalse(value['linux_helper_started']);self.assertFalse((out/'linux_terminal.json').exists())
            for change in ('exit0','wrong_birth','stdout','extra_stderr','linux_artifact','wrong_program'):
                changed=copy.deepcopy(terminal);args=list(argv)
                if change=='exit0':changed['exit_code']=0
                elif change=='wrong_birth':changed['creation_filetime']=457
                elif change=='stdout':(out/'wsl.stdout.txt').write_bytes(b'Possible Linux output')
                elif change=='extra_stderr':(out/'wsl.stderr.txt').write_bytes(error+b'Unexpected second line\n')
                elif change=='linux_artifact':(out/'linux_terminal.json').write_bytes(b'{}')
                elif change=='wrong_program':args[6]='/OTHER/python'
                with self.subTest(change=change):self.assertIsNone(V.exact_preexec_failure(out,args,birth,changed))
                if change=='stdout':(out/'wsl.stdout.txt').write_bytes(b'')
                if change=='extra_stderr':(out/'wsl.stderr.txt').write_bytes(error)
                if change=='linux_artifact':(out/'linux_terminal.json').unlink()


if __name__=='__main__': unittest.main()
