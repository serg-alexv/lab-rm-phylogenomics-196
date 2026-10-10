"""Default-noop G-drive diagnosis and optional exact owned drvfs mount.

No detector, runtime payload, bind mount, unmount, deletion or configuration change.
Root must publish/review before explicit --run [--mount].
"""
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from contextlib import nullcontext
import argparse, ctypes, hashlib, importlib, json, os, re, signal, stat, subprocess, sys, time, uuid

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
LWORK=PurePosixPath('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
ROOT=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
LROOT=PurePosixPath('/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196')
MOUNTPOINT=PurePosixPath('/mnt/g')
WSL=r'C:\Windows\System32\wsl.exe'
MOUNT_ARGV=['/usr/bin/mount','-t','drvfs','G:','/mnt/g']
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
      'stage5_owner_lease.py':'add2cbf12ee6d51bb10168b629a8befd2136f58e5194a6e7195fea25002620b8',
      'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
      'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
      'stage5_setup_windows.py':'4e94a8cfcbf9264db677b8477720fbce5c52ed839af56bae21aa36cc5ff271aa'}
PRIOR_PINS={
 'stage5_setup_storage_actual_postiq_02/result.json':'6e6c70739fb79f0d6291d50190c9bcf07823a68eb61d3272a3ebc9d2901ea6e3',
 'stage5_setup_storage_actual_postiq_02/lock_released.json':'1b1084ace1bc6bbfd4ab0dbba9918cc53968de3b1a95f4e944cc6ae0621333b1',
 'stage5_setup_storage_actual_postiq_02/linux_terminal.json':'5a75f1087deb6ccb8bc69f544e9ccd951f057f7bc9d1ef5730a501b1cb7eae74',
 'stage5_setup_toolchain_actual_postiq_04/result.json':'edb490807bcf68917aa99148a78147e09a1a39c4ad0c65aaf91ad35cac5397a4',
 'stage5_setup_toolchain_actual_postiq_04/lock_released.json':'c75a74e260a0e96ed53ca2ed125baa9ae5ea08a02fc2ff329a29487ee19bfde2',
 'stage5_setup_toolchain_actual_postiq_04/toolchain_proof.json':'3ad8067a031c960c0b44a24a6d19c2eb29552d466b211c078df17beb1174cfcc'}
PANEL_SHA='85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'
CONTROLS=('status/run_control.json','config/approved_accessions.txt','config/approval.json')
SCOPE='NONSCIENTIFIC_G_DRIVE_VISIBILITY_ONLY'
RESERVE=1879048192


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def exists(path):
    try:Path(path).lstat();return True
    except FileNotFoundError:return False


def tiny(path,limit=1024**2):
    path=Path(path)
    before=path.lstat()
    need(stat.S_ISREG(before.st_mode) and not path.is_symlink()
         and not getattr(before,'st_file_attributes',0)&0x400 and before.st_size<=limit,'Bounded plain control required')
    with path.open('rb') as stream:
        opened=os.fstat(stream.fileno());raw=stream.read(limit+1);after=os.fstat(stream.fileno())
    def identity(i):return (i.st_dev,i.st_ino,i.st_size,i.st_mtime_ns)
    need(len(raw)==before.st_size and len(raw)<=limit and identity(before)==identity(opened)==identity(after)
         ==identity(path.lstat()),'Control identity/bytes changed during read')
    return raw


def control_gate(raw):
    need(set(raw)==set(CONTROLS),'Exact three small controls required')
    control=json.loads(raw[CONTROLS[0]])
    need(control['state']=='ACTIVE_DIRECT_USER_CONTINUATION' and control['automatic_resume'] is False,
         'Current explicit continuation authority required')
    panel=raw[CONTROLS[1]].decode('ascii').split()
    need(hashlib.sha256(raw[CONTROLS[1]]).hexdigest()==PANEL_SHA and len(panel)==len(set(panel))==196,
         'Exact approved196 panel differs')
    approval=json.loads(raw[CONTROLS[2]])
    need(approval['human_approval']=='APPROVED_FOR_SEQUENCE_ANALYSIS' and approval['approved_assembly_count']==196
         and approval['pilot'] is False and approval['panel_accessions_sha256']==PANEL_SHA,'Approval differs')
    return {name:hashlib.sha256(value).hexdigest() for name,value in raw.items()}


def plain_chain(path):
    for item in [Path(path),*Path(path).parents]:
        info=item.lstat();need(stat.S_ISDIR(info.st_mode) and not item.is_symlink()
            and not getattr(info,'st_file_attributes',0)&0x400,'Directory ancestry must be plain, never aliases')


def empty_directory(path):
    plain_chain(path);info=Path(path).lstat()
    with os.scandir(path) as entries:need(next(entries,None) is None,'Unknown underlay contents; preserve')
    after=Path(path).lstat()
    need((info.st_dev,info.st_ino,info.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_mtime_ns),'Underlay changed')
    return {'path':str(path),'device':str(info.st_dev),'inode':str(info.st_ino),'mtime_ns':str(info.st_mtime_ns),'entries':[]}


def drive_mount(rows):
    exact=[r for r in rows if r['mountpoint']==str(MOUNTPOINT)]
    need(len(exact)<=1 and not any(PurePosixPath('/mnt/g') in PurePosixPath(r['mountpoint']).parents for r in rows),
         'Unknown stacked or nested G mount; preserve')
    if not exact:return None
    row=exact[0]
    need(row['source'].upper().rstrip('\\/')=='G:' and row['root']=='/'
         and row['filesystem'] in ('drvfs','9p') and 'rw' in row['options'].split(',')
         and (row['filesystem']=='drvfs' or 'aname=drvfs' in row['super_options']),
         'Existing mount is not the exact G drive drvfs root; preserve')
    return row


def mount_prelaunch_gate(current_rows,expected_rows,current_underlay,expected_underlay,root_present):
    need(current_rows==expected_rows and current_underlay==expected_underlay and not root_present,
         'G topology/empty underlay/root changed during command admission; preserve')
    return {'state':'EXACT_EMPTY_G_UNDERLAY_RECHECKED_AFTER_ADMISSION','underlay':current_underlay}


def prior_gate(values):
    failed=values['stage5_setup_storage_actual_postiq_02/result.json']
    terminal=values['stage5_setup_storage_actual_postiq_02/linux_terminal.json']
    tool=values['stage5_setup_toolchain_actual_postiq_04/result.json']
    proof=values['stage5_setup_toolchain_actual_postiq_04/toolchain_proof.json']
    need(failed['state']=='FAILED' and failed['step']=='storage' and failed['owned_closure_proven'] is True
         and failed['unknown_closure_stop_preserved'] is False and failed['native_commands']==[]
         and terminal['owned_closure_proven'] is True and terminal['remaining_direct_children']==[]
         and terminal['owned_command_count']==0,'Storage02 must remain an actual closed failed scope')
    need(tool['state']=='PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK' and tool['step']=='toolchain'
         and tool['owned_closure_proven'] is True and tool['unknown_closure_stop_preserved'] is False,
         'Actual current toolchain04 closed proof required')
    for name in ['stage5_setup_storage_actual_postiq_02/lock_released.json','stage5_setup_toolchain_actual_postiq_04/lock_released.json']:
        need(values[name]['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and values[name]['released'] is True,'Original byte unlock required')
    need(proof['boot_id']==terminal['bootstrap']['boot_id'] and proof['schema']=='STAGE05_TOOLCHAIN_LOOP_PROOF_V1',
         'Current preparation boot proof differs')
    return proof['boot_id']


def imports(base,names):
    base=Path(base)
    need(Path(__file__).resolve().parent==base,'Exact source location required')
    for name in names:need(sha(base/(name+'.py'))==PINS[name+'.py'],'Reviewed helper source differs')
    sys.path.insert(0,str(base));result=[]
    for name in names:
        module=importlib.import_module(name)
        need(Path(module.__file__).resolve()==base/(name+'.py') and sha(module.__file__)==PINS[name+'.py'],
             'Helper import shadowing/source drift')
        result.append(module)
    return result


def linux_main(args):
    global LWORK,LROOT,MOUNTPOINT
    need(sys.platform=='linux' and os.geteuid()==0,'System Linux root bootstrap required')
    LWORK,LROOT,MOUNTPOINT=Path(LWORK),Path(LROOT),Path(MOUNTPOINT)
    P,W=imports(LWORK,['stage5_atomic_process','stage5_work_storage'])
    request=Path(args.request)
    need(request.parent.parent==LWORK and re.fullmatch('stage5_gdrive_view_[a-f0-9]{32}',request.parent.name)
         and request.name=='request.json' and not request.is_symlink(),'Exact fresh C request namespace required')
    raw=tiny(request);need(hashlib.sha256(raw).hexdigest()==args.request_sha256,'Original Windows request bytes differ')
    value=json.loads(raw);out=request.parent
    need(value['schema']=='STAGE05_GDRIVE_VIEW_REQUEST_V1' and value['scope']==SCOPE
         and value['source_sha256']==sha(__file__) and value['linux_root']==str(LROOT)
         and value['mount_argv']==MOUNT_ARGV and type(value['allow_mount']) is bool,'Exact mount request contract differs')
    nonce=value['owner_nonce'];need(re.fullmatch('[a-f0-9]{32}',nonce),'Owner nonce differs')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    need(boot==value['boot_id'],'Actual Linux boot differs from current closed setup')
    held=json.loads(tiny(out/'actual_owner_lock.json'))
    need(sha(out/'actual_owner_lock.json')==value['owner_lock_sha256'] and held['owner_nonce']==nonce
         and held['workflow_lock']==value['workflow_lock'],'Exact current original-lock witness differs')
    result={'schema':'STAGE05_GDRIVE_LINUX_TERMINAL_V1','scope':SCOPE,'state':'FAILED','owner_nonce':nonce,
            'source_sha256':sha(__file__),'request_sha256':args.request_sha256,'boot_id':boot,
            'bootstrap':{'argv':sys.argv,'executable':sys.executable,'identity':P.proc_record(os.getpid())},
            'scientific_adoption_authorized':False,'mount_performed':False,'mountpoint_created':False,
            'owned_closure_proven':True,'owned_command_count':0}
    policy={'windows_reserve_bytes':1610612736,'incremental_windows_requirement_bytes':268435456,
        'commit_requirement_bytes':RESERVE,'linux_job_requirement_bytes':134217728,'linux_reserve_bytes':134217728,
        'minimum_disk_free_bytes':10737418240,'resource_wait_seconds':0,'lease_max_age_seconds':3,
        'command_timeout_seconds':30,'sampled_rss_stop_bytes':268435456,'termination_grace_seconds':2,'drain_timeout_seconds':4}
    supervisor=None
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(P.Fatal('G view Linux90s deadline')));signal.alarm(90)
    try:
        supervisor=P.Supervisor(out/'owner_lease.json',nonce,policy,out,sha);supervisor.admission(out)
        # proc pseudo-files report size0, so mountinfo uses a separate bounded read.
        def rows():
            with Path('/proc/self/mountinfo').open('rb') as stream:data=stream.read(2*1024**2+1)
            need(len(data)<=2*1024**2,'Mount metadata exceeded bound');return W.mount_rows(data.decode())
        namespace={'self':os.readlink('/proc/self/ns/mnt'),'pid1':os.readlink('/proc/1/ns/mnt')}
        result['mount_namespace']=namespace;need(namespace['self']==namespace['pid1'],'Isolated mount namespace cannot establish future WSL view')
        before=rows();mount=drive_mount(before)
        result['observation_before']={'g_mount':mount,'g_mountpoint_present':exists(MOUNTPOINT),'g_root_present':exists(LROOT)}
        if mount is None and value['allow_mount']:
            need(not exists(LROOT),'Unknown G root exists without exact mount; preserve')
            if not exists(MOUNTPOINT):
                plain_chain(MOUNTPOINT.parent);os.mkdir(MOUNTPOINT);result['mountpoint_created']=True
            result['linux_empty_mount_underlay']=empty_directory(MOUNTPOINT)
            need(rows()==before and not exists(LROOT),'Mount topology/root changed before exact mount')
            supervisor.check_owner()
            supervisor.prelaunch_check=lambda *_: mount_prelaunch_gate(rows(),before,empty_directory(MOUNTPOINT),
                result['linux_empty_mount_underlay'],exists(LROOT))
            supervisor.execute(SimpleNamespace(output=out,environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')),
                out/'commands','gdrive',MOUNT_ARGV,LWORK,{'scope':'NONSCIENTIFIC_STAGE5_SETUP_ONLY','step':'gdrive'})
            result['mount_performed']=True;mount=drive_mount(rows());need(mount is not None,'Exact mount command did not establish G drive')
        if mount is None:
            result['state']='PASS_DIAGNOSIS_G_DRIVE_NOT_MOUNTED_NO_REPAIR'
        else:
            plain_chain(LROOT);raw={name:tiny(LROOT/name) for name in CONTROLS}
            need(control_gate(raw)==value['control_sha256'],'Linux actual G control/panel bytes differ from Windows')
            result['linux_control_sha256']=control_gate(raw)
            result['linux_g_underlay']=empty_directory(LROOT/'.work/stage05_atomic_v1')
            after=rows();need(drive_mount(after)==mount,'G mount changed during exact byte proof')
            result['g_mount']=mount;result['state']='PASS_EXACT_WINDOWS_LINUX_G_CONTROL_BYTES_AND_EMPTY_UNDERLAY'
        supervisor.check_owner()
        need(sha(request)==args.request_sha256 and sha(__file__)==value['source_sha256'],'Request/source changed')
    except BaseException as error:result.update(state='FAILED',error={'kind':type(error).__name__,'message':str(error)})
    finally:
        signal.alarm(0)
        if supervisor:result.update(owned_closure_proven=not supervisor.closure_unproven,owned_command_count=supervisor.native_launch_count)
        try:
            children=Path(f'/proc/self/task/{os.getpid()}/children').read_text().split()
            result['remaining_direct_children']=[int(v) for v in children]
            if children:result['owned_closure_proven']=False
        except BaseException:result.update(owned_closure_proven=False,remaining_direct_children='UNPROVEN')
        P.atomic_json(out/'linux_terminal.json',result)
    return 0 if result['state'].startswith('PASS_') and result['owned_closure_proven'] else 2


def terminal_gate(value,nonce,request_sha,source_sha,boot,exit_code,allow_mount):
    need(value['schema']=='STAGE05_GDRIVE_LINUX_TERMINAL_V1' and value['scope']==SCOPE
         and value['owner_nonce']==nonce and value['request_sha256']==request_sha and value['source_sha256']==source_sha
         and value['boot_id']==boot and value['owned_closure_proven'] is True and value['remaining_direct_children']==[]
         and value['scientific_adoption_authorized'] is False,'Actual Linux terminal scope/closure differs')
    count=value['owned_command_count'];need(type(count) is int and count in (0,1),'Unexpected helper command count')
    need(value['state'] in ('FAILED','PASS_DIAGNOSIS_G_DRIVE_NOT_MOUNTED_NO_REPAIR',
        'PASS_EXACT_WINDOWS_LINUX_G_CONTROL_BYTES_AND_EMPTY_UNDERLAY')
        and not (value['state'].startswith('PASS_') and 'error' in value),'Unknown or errored PASS terminal rejected')
    need(count==0 or allow_mount,'Diagnosis launched unexpected mount')
    need(exit_code==(0 if value['state'].startswith('PASS_') else 2),'Actual client terminal/result mismatch')
    return count


def windows_main(args):
    need(os.name=='nt','Windows owner required')
    A,L,S=imports(WORK,['atomic_iqtree_windows','stage5_owner_lease','stage5_setup_windows'])
    need(all(sha(WORK/n)==h for n,h in PINS.items()),'Current operative source pins differ')
    prior={n:json.loads(tiny(WORK/n)) for n in PRIOR_PINS}
    need(all(sha(WORK/n)==h for n,h in PRIOR_PINS.items()),'Actual closed setup evidence changed')
    boot=prior_gate(prior)
    out=WORK/('stage5_gdrive_view_'+uuid.uuid4().hex);out.mkdir()
    api=A.Win();owner=api.identity(api.current(),os.getpid());nonce=uuid.uuid4().hex
    lock=A.WorkflowLock(api);stop=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
    child=None;birth=None;closed=True;terminal=None;stop_sha=None;source_sha=sha(__file__);start=time.monotonic()
    record={'schema':'STAGE05_GDRIVE_WINDOWS_OWNER_RESULT_V1','scope':SCOPE,'state':'FAILED','source_sha256':source_sha,
        'source_pins':PINS,'prior_pins':PRIOR_PINS,'owner_nonce':nonce,'actual_owner':owner,'allow_mount':args.mount,
        'boot_id':boot,'scientific_adoption_authorized':False,'lease_replace_stats':{}}
    def snapshot():
        plain_chain(ROOT);raw={name:tiny(ROOT/name) for name in CONTROLS}
        api.K.GetDriveTypeW.argtypes=[ctypes.c_wchar_p];api.K.GetDriveTypeW.restype=ctypes.c_uint
        return {'control_sha256':control_gate(raw),'empty_g_underlay':empty_directory(ROOT/'.work/stage05_atomic_v1'),
            'drive_type':int(api.K.GetDriveTypeW('G:\\')),'root_device':str(ROOT.lstat().st_dev)}
    try:
        with nullcontext(lock.__enter__()) as held:
            need(not exists(stop),'Existing unknown closure stop vetoes launch')
            record['actual_ubuntu_registration']=S.registered_backing();before=snapshot();record['windows_before']=before
            record['workflow_lock']=held.identity
            def lease(active=True):
                need(snapshot()==before,'Actual Windows G authority/underlay changed')
                resources=api.resources([ROOT,out]);now=time.time()
                if active:need(resources['physical_available_bytes']>=RESERVE and resources['commit_headroom_bytes']>=RESERVE
                    and all(v>=10737418240 for v in resources['disk_available_bytes'].values()),'Actual mount helper resource reserve insufficient')
                L.atomic_owner_lease(out/'owner_lease.json',{'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1','nonce':nonce,
                    'workflow_lock_held':active,'workflow_lock':held.identity,'owner_pid':owner['pid'],
                    'owner_creation_filetime':str(owner['creation_filetime']),'measured_unix':now,'expires_unix':now+3 if active else now,
                    'windows_available_bytes':resources['physical_available_bytes'],'windows_commit_headroom_bytes':resources['commit_headroom_bytes'],
                    'disk_available_bytes':resources['disk_available_bytes']},record['lease_replace_stats'])
                record['latest_actual_resources']=resources
            lease();A.atomic(out/'actual_owner_lock.json',{'owner_nonce':nonce,'owner':owner,'workflow_lock':held.identity})
            request={'schema':'STAGE05_GDRIVE_VIEW_REQUEST_V1','scope':SCOPE,'owner_nonce':nonce,'source_sha256':source_sha,
                'boot_id':boot,'linux_root':str(LROOT),'allow_mount':args.mount,'mount_argv':MOUNT_ARGV,
                'control_sha256':before['control_sha256'],'workflow_lock':held.identity,
                'owner_lock_sha256':sha(out/'actual_owner_lock.json')}
            A.atomic(out/'request.json',request);request_sha=sha(out/'request.json')
            A.atomic(stop,{'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1','owner_nonce':nonce,'utc':A.utc(),
                'evidence':str(out),'reason':'G visibility helper launch intent requires actual Linux/WSL closure','automatic_resume':False})
            stop_sha=sha(stop);closed=False
            argv=[WSL,'-d','Ubuntu','-u','root','--exec','/usr/bin/python3','-B',str(LWORK/Path(__file__).name),
                '--linux','--request',str(LWORK/out.name/'request.json'),'--request-sha256',request_sha]
            record['argv']=argv
            with (out/'wsl.stdout.txt').open('xb') as stdout,(out/'wsl.stderr.txt').open('xb') as stderr:
                child=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
                birth=api.identity(int(child._handle),child.pid,WSL,owner['session_id'])
                A.atomic(out/'launch.json',{'argv':argv,'retained_client_birth':birth,'owner_nonce':nonce})
                deadline=time.monotonic()+110
                while child.poll() is None:
                    need(time.monotonic()<deadline,'G view retained client deadline exceeded');lease();time.sleep(0.5)
            terminal=api.identity(int(child._handle),child.pid,WSL,owner['session_id'])
            A.require(terminal['exited'] is True and terminal['pid']==birth['pid']
                and terminal['creation_filetime']==birth['creation_filetime'] and terminal['exit_filetime']>terminal['creation_filetime'],
                'Actual retained WSL exit differs')
            A.atomic(out/'wsl_exit.json',{'birth':birth,'terminal':terminal,'argv':argv,'owner_nonce':nonce})
            actual=json.loads(tiny(out/'linux_terminal.json'));count=terminal_gate(actual,nonce,request_sha,source_sha,boot,terminal['exit_code'],args.mount)
            need(actual['bootstrap']['argv']==argv[8:] and actual['bootstrap']['executable']=='/usr/bin/python3'
                and actual['bootstrap']['identity']['pid']>0 and int(actual['bootstrap']['identity']['start_ticks'])>0,
                'Actual Linux bootstrap argv/interpreter/birth differs')
            record['command_receipts']=S.command_readback(out,count,'gdrive' if count else 'diagnose',MOUNT_ARGV,actual['state'].startswith('PASS_'))
            closed=True;record['linux_terminal_sha256']=sha(out/'linux_terminal.json');record['linux_state']=actual['state']
            need(actual['state'].startswith('PASS_'),'Actual G view failed after closed scope')
            record['windows_after']=snapshot();need(record['windows_after']==before,'Windows source view changed')
            if args.mount:need(actual['state']=='PASS_EXACT_WINDOWS_LINUX_G_CONTROL_BYTES_AND_EMPTY_UNDERLAY','Requested G view not established')
            need(all(sha(WORK/n)==h for n,h in PINS.items()) and all(sha(WORK/n)==h for n,h in PRIOR_PINS.items())
                 and sha(__file__)==source_sha,'Source/closed evidence changed')
            record['state']='PASS_NONSCIENTIFIC_G_DRIVE_VIEW_HELPER'
    except BaseException as error:record['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        if child is not None and not closed:
            try:
                if child.poll() is None:child.wait(timeout=15)
                terminal=api.identity(int(child._handle),child.pid,WSL,owner['session_id'])
                need(terminal['exited'] is True and birth is not None and terminal['pid']==birth['pid']
                    and terminal['creation_filetime']==birth['creation_filetime'] and terminal['exit_filetime']>terminal['creation_filetime'],'Retained failed client exit unproven')
                A.atomic(out/'wsl_exit.json',{'birth':birth,'terminal':terminal,'argv':argv,'owner_nonce':nonce})
                actual=json.loads(tiny(out/'linux_terminal.json'));count=terminal_gate(actual,nonce,request_sha,source_sha,boot,terminal['exit_code'],args.mount)
                need(actual['bootstrap']['argv']==argv[8:] and actual['bootstrap']['executable']=='/usr/bin/python3'
                    and actual['bootstrap']['identity']['pid']>0 and int(actual['bootstrap']['identity']['start_ticks'])>0,
                    'Actual failed Linux bootstrap differs')
                record['command_receipts']=S.command_readback(out,count,'gdrive' if count else 'diagnose',MOUNT_ARGV,False)
                closed=True;record['linux_terminal_sha256']=sha(out/'linux_terminal.json')
            except BaseException as error:record['closure_finalizer_error']=str(error)
        if closed and stop_sha is not None:
            try:need(sha(stop)==stop_sha and json.loads(tiny(stop))['owner_nonce']==nonce,'Own intent marker changed');stop.unlink()
            except BaseException as error:record['own_stop_clear_error']=str(error);record['state']='FAILED'
        try:lock.__exit__(None,None,None)
        except BaseException as error:record['unlock_error']=str(error);record['state']='FAILED'
        record.update(owned_closure_proven=closed,retained_client_terminal=terminal,original_lock_explicitly_released=lock.released,
                      unknown_closure_stop_preserved=exists(stop),log_hash_scope='CLOSED_FULL_LOGS' if closed else 'PARTIAL_UNPROVEN_WRITER',
                      elapsed_seconds=time.monotonic()-start,utc=A.utc())
        for n in ['wsl.stdout.txt','wsl.stderr.txt']:
            if exists(out/n):record[n+'_sha256']=sha(out/n)
        if child is not None and terminal is not None and terminal['exited']:
            try:child._handle.Close()
            except BaseException as error:record['handle_close_error']=str(error);record['state']='FAILED'
        A.atomic(out/'result.json',record)
        if lock.released:A.atomic(out/'lock_released.json',{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True,'utc':A.utc()})
    print(json.dumps({'state':record['state'],'result':str(out/'result.json')}))
    return 0 if record['state'].startswith('PASS_') and closed and lock.released else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--mount',action='store_true')
    parser.add_argument('--linux',action='store_true');parser.add_argument('--request');parser.add_argument('--request-sha256')
    args=parser.parse_args()
    if args.linux:return linux_main(args)
    if not args.run:print(json.dumps({'state':'PREPARED_NOT_RUN','WSL_launches':0,'mounts':0}));return 0
    return windows_main(args)


if __name__=='__main__':raise SystemExit(main())
