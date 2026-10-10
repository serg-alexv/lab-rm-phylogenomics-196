"""Opt-in four-step Stage5 setup owner. Prepared source only until prior IQ closure.

Owns the original Windows byte lock. Never wraps the other self-locking owners.
"""
from pathlib import Path, PurePosixPath
import argparse, ctypes, hashlib, json, os, re, stat, subprocess, time, uuid
import atomic_iqtree_windows as A
import stage5_owner_lease as L

WORK=Path(__file__).resolve().parent
EXACT_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
ATTEMPT=WORK/'iqtree_attempts/partitioned_20261009T162904Z'
WSL=r'C:\Windows\System32\wsl.exe'
STOP=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
G_TARGET=ROOT/'.work/stage05_atomic_v1'
LINUX_WORK='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work'
LINUX_ENV='/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/detector_env'
UBUNTU_BASE=Path(r'C:\Users\wheel\AppData\Local\wsl\{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}')
SCOPE='NONSCIENTIFIC_STAGE5_SETUP_ONLY'
CLOSURE_PINS={'launch.json':'4621af4a10eeaff8444ec11545bee1550bb891af18547dcfc15ecf6ba3009bcc',
              'exit.json':'7404524cc341af5ee19d04f9ca3f547765f2a1f274e4b891a5bcd409264b14c7',
              'execution_state_restored.json':'49f5923f592bafe890c4a784563dbfa2a90f3100a0a89a9938331daa1c71a851',
              'lock_released.json':'9c5df1cd99ace44e9f76a509aa8f21407dc76033c5ec8cdd444f30bc7a5a1ed3'}
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
      'stage5_owner_lease.py':'add2cbf12ee6d51bb10168b629a8befd2136f58e5194a6e7195fea25002620b8',
      'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
      'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
      'stage5_runtime_discovery.py':'11b2a1b64512e1eab3895db017323cc25de65d31b4734d08788e99d968f44dfb',
      'stage5_drivefs_filesystem_smoke.py':'d24d86c1910ac82514a2fb7c1819d5cd1ea175dea3c5df587e8c8be2282eab2a',
      'stage5_unc_bind_probe.py':'0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d',
      'observe_iqtree_controller_exit.py':'483b5165d015dcea659d5e850187c79ff5e99c4c0efff1c9fb108cc9a59ab78a'}


def linux_path(path):
    path=Path(path).resolve()
    A.require(path.drive.lower()=='c:' and WORK in path.parents,'Current C work path required')
    return '/mnt/c/'+'/'.join(path.parts[1:])


def prior_closure(controller,observer_sha,launch,native,power,unlock):
    A.require(controller['schema']=='MASTER_IQTREE_CONTROLLER_RETAINED_EXIT_V1'
              and controller['state']=='PASS_CONTROLLER_RETAINED_HANDLE_EXIT0'
              and controller['source_sha256']==observer_sha,'Independent retained controller closure receipt differs')
    terminal=controller['terminal']; retained=controller['retained_live_identity']
    for row in (terminal,retained):
        A.require(row['pid']==27048 and int(row['creation_filetime'])==134360369803845506,'Exact previous controller birth differs')
    A.require(terminal['exited'] is True and terminal['exit_code']==0
              and terminal['exit_filetime']>terminal['creation_filetime'],'Previous retained controller has not exited0')
    old=native['native']; born=launch['native']
    A.require(old['pid']==born['pid']==4768 and old['creation_filetime']==born['creation_filetime']==134360369876207076
              and old['exited'] is True and old['exit_code']==0 and old['exit_filetime']>old['creation_filetime']
              and native['execution']=='NATIVE_EXITED' and native['job_active_processes']==0 and native['job_pids']==[],
              'Exact previous native exit and empty owned job required')
    A.require(power['actual_api_success'] is True and power['requested_flags']==0x80000000
              and unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED',
              'Previous power restoration/explicit byte unlock proof absent')
    return terminal,old


def registration_contract(value):
    A.require(value['distribution_name']=='Ubuntu' and value['version']==2
              and Path(value['base_path'])==UBUNTU_BASE and UBUNTU_BASE.drive.lower()=='c:',
              'Exact Ubuntu WSL2 physical-C backing registration required')
    return value


def registered_backing():
    import winreg
    values=[]
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Lxss') as root:
        for index in range(winreg.QueryInfoKey(root)[0]):
            name=winreg.EnumKey(root,index)
            with winreg.OpenKey(root,name) as key:
                distribution=winreg.QueryValueEx(key,'DistributionName')[0]
                if distribution=='Ubuntu':
                    values.append({'distribution_name':distribution,'version':winreg.QueryValueEx(key,'Version')[0],
                                   'base_path':winreg.QueryValueEx(key,'BasePath')[0],'registry_key':name})
    A.require(len(values)==1,'Exactly one Ubuntu registration required')
    value=registration_contract(values[0]); image=UBUNTU_BASE/'ext4.vhdx'
    for path in (image,*image.parents):
        info=path.lstat()
        A.require(not path.is_symlink() and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,
                  'Ubuntu VHD backing or C ancestry is an alias/reparse')
    info=image.stat(); A.require(stat.S_ISREG(info.st_mode),'Registered Ubuntu VHD backing must be regular')
    value['vhd_metadata']={'path':str(image),'device':str(info.st_dev),'inode':str(info.st_ino),'bytes':info.st_size,
                           'payload_read':False}
    return value


def reject_live_exact(api,row):
    from ctypes import wintypes
    opened=api.K.OpenProcess; opened.restype=wintypes.HANDLE
    opened.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    handle=opened(0x1000|0x100000,False,row['pid'])
    if not handle:
        A.require(ctypes.get_last_error()==87,'Cannot prove previous PID is absent/exited')
        return
    try:
        current=api.identity(handle,row['pid'],row['executable'],row['session_id'])
        A.require(current['creation_filetime']!=row['creation_filetime'] or current['exited'],
                  'Exact prior owner is still alive')
    finally: api.close(handle)


def underlay(create=False):
    for path in (G_TARGET.parent,*G_TARGET.parent.parents):
        info=path.lstat()
        A.require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT and not path.is_symlink(),'G parent alias/reparse')
    if create and not G_TARGET.exists(): G_TARGET.mkdir()
    info=G_TARGET.lstat()
    A.require(stat.S_ISDIR(info.st_mode) and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
              and not G_TARGET.is_symlink(),'Exact G underlay directory required')
    with os.scandir(G_TARGET) as entries: A.require(next(entries,None) is None,'Unknown G underlay contents; preserve')
    return {'device':str(info.st_dev),'inode':str(info.st_ino),'mtime_ns':str(info.st_mtime_ns),'entries':[]}


def drivefs_readback(stdout,root=ROOT):
    def tiny(path,limit):
        info=path.lstat()
        A.require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
                  and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT and info.st_size<=limit,
                  'DriveFS fixture is not a bounded regular non-reparse file')
        with path.open('rb') as stream: data=stream.read(limit+1)
        A.require(len(data)<=limit,'DriveFS fixture grew beyond tiny read bound')
        return data
    value=json.loads(tiny(Path(stdout),65536))
    A.require(value['schema']=='STAGE05_DRIVEFS_FILESYSTEM_SMOKE_V1'
              and value['scope']=='NONSCIENTIFIC_DRIVEFS_FILESYSTEM_ONLY'
              and value['state']=='PASS_NONSCIENTIFIC_FILESYSTEM_ONLY'
              and value['scientific_adoption_authorized'] is False,'Actual DriveFS primitive scope/state differs')
    relative=value['namespace_relative']
    A.require(re.fullmatch(r'\.work/stage05_atomic_filesystem_smoke_[0-9]{8}T[0-9]{12}Z_[a-f0-9]{8}',relative),
              'Unsafe DriveFS result namespace')
    directory=root.joinpath(*PurePosixPath(relative).parts)
    for path in (root,root/'.work',directory):
        info=path.lstat()
        A.require(stat.S_ISDIR(info.st_mode) and not path.is_symlink()
                  and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,'DriveFS directory alias/reparse')
    raw=tiny(directory/'result.json',65536)
    A.require(hashlib.sha256(raw).hexdigest()==value['result_sha256'],'Independent Windows result SHA differs')
    record=json.loads(raw)
    A.require(all(record[k]==value[k] for k in ('schema','scope','state','nonce','namespace_relative','script_sha256',
                  'supervisor_sha256','caller_lock_receipt_sha256','scientific_adoption_authorized')),'Windows/Linux result metadata differs')
    expected={'ordinary.bin','replaced.bin','runner_atomic.json','.native_runner.guard'}
    A.require(set(record['files'])==expected,'Exact DriveFS payload member set differs')
    A.require(all(record[k] is True for k in ('ordinary_write_fsync_readback','atomic_overwrite_readback',
                  'runner_atomic_json_readback','flock_contention_proven','flock_close_release_reacquire_proven')),'Actual primitive evidence incomplete')
    A.require(record['script_sha256']==PINS['stage5_drivefs_filesystem_smoke.py']
              and record['supervisor_sha256']==PINS['stage5_atomic_process.py'],'Actual primitive source pins differ')
    payload=('NONSCIENTIFIC DRIVEFS SMOKE\n'+record['nonce']+'\n').encode('ascii')
    import itertools
    A.require(set(p.name for p in itertools.islice(directory.iterdir(),len(expected)+2))==expected|{'result.json'},
              'Unexpected DriveFS fixture payload')
    for name in expected:
        path=directory/name
        A.require(not path.is_symlink(),'DriveFS payload alias')
        content=tiny(path,4096); pin=record['files'][name]
        A.require(len(content)==pin['bytes'] and hashlib.sha256(content).hexdigest()==pin['sha256'],'Windows actual payload hash/size differs')
        if name in ('ordinary.bin','replaced.bin'): A.require(content==payload,'Actual ordinary/replaced bytes differ')
        if name=='runner_atomic.json':
            obj=json.loads(content); A.require(obj['nonce']==record['nonce'] and obj['scope']==record['scope'],'Actual atomic JSON differs')
    return {'state':'PASS_INDEPENDENT_WINDOWS_DRIVEFS_EXACT_BYTES','namespace_relative':relative,
            'result_sha256':hashlib.sha256(raw).hexdigest(),'files':record['files']}


def command_readback(out,count,step,expected_argv,success):
    directory=out/'commands'
    paths=list(directory.glob('*.launch.json')) if directory.exists() else []
    A.require(type(count) is int and 0<=count<=1 and len(paths)==count,'Exact bounded setup command accounting differs')
    for suffix in ('launch_intent','closure','command'):
        A.require(len(list(directory.glob('*.'+suffix+'.json')))==count,'Setup command closure receipt membership differs')
    if count==0:
        A.require(not success or step in ('diagnose','toolchain','storage'),'Successful step lacks actual native helper execution')
        return []
    launch=paths[0]; label=launch.name.removesuffix('.launch.json')
    native=A.read_json(launch); intent=A.read_json(directory/(label+'.launch_intent.json'))
    close=A.read_json(directory/(label+'.closure.json')); command=A.read_json(directory/(label+'.command.json'))
    A.require(native['argv']==intent['argv']==expected_argv and native['identity']=={'scope':SCOPE,'step':step}
              and native['command_nonce']==intent['command_nonce']==close['command_nonce']==command['command_nonce']
              and native['boot_id']==close['boot_id']==command['boot_id'],'Setup actual argv/nonce/source scope differs')
    A.require(all(command[k]==native[k] for k in ('child_pid','child_start_ticks','pgid','sid','argv','cwd','identity'))
              and native['pgid']==native['sid']==native['child_pid']
              and close['root_exit_code']==command['exit_code'] and close['group_empty'] is True
              and close['tracked_descendants_empty'] is True and not close['survivors']
              and not close['unexplained_pgid_members'],'Setup root/group/descendant closure differs')
    tracked=[r for r in close['tracked_descendants'] if r['pid']==native['child_pid'] and r['start_ticks']==native['child_start_ticks']]
    A.require(len(tracked)==1 and tracked[0]['pgid']==native['pgid'] and tracked[0]['sid']==native['sid'],
              'Setup retained root birth/group differs')
    A.require(command['group_closure_sha256']==A.sha256(directory/(label+'.closure.json'))
              and command['stdout_sha256']==A.sha256(directory/(label+'.stdout.txt'))
              and command['stderr_sha256']==A.sha256(directory/(label+'.stderr.txt')),'Setup actual closure/log SHA differs')
    if success: A.require(command['exit_code']==0 and close['termination_reason'] is None,'Successful setup command did not exit normally')
    return [{'label':label,'launch_sha256':A.sha256(launch),'closure_sha256':command['group_closure_sha256'],
             'command_sha256':A.sha256(directory/(label+'.command.json'))}]


def exact_preexec_failure(out,argv,birth,terminal,candidate=None):
    """A future retained-client failure boundary, never invented Linux success."""
    if not (argv[:6]==[WSL,'-d','Ubuntu','-u','root','--exec'] and argv[6]=='/usr/bin/python3'
            and argv[7:9]==['-B',LINUX_WORK+'/stage5_setup_linux.py']
            and terminal.get('creation_filetime')==birth.get('creation_filetime')
            and terminal.get('exited') is True and type(terminal.get('exit_code')) is int
            and terminal['exit_code']!=0 and terminal['exit_filetime']>terminal['creation_filetime']
            and terminal.get('pid')==birth.get('pid') and terminal.get('executable')==birth.get('executable')==WSL):
        return None
    allowed={'owner_lease.json','actual_owner_lock.json','launch.json','wsl.stdout.txt','wsl.stderr.txt','wsl_exit.json'}
    if any(p.name not in allowed for p in out.iterdir()) or (candidate is not None and candidate.exists()):return None
    stdout=out/'wsl.stdout.txt';stderr=out/'wsl.stderr.txt'
    if stdout.stat().st_size!=0 or not 0<stderr.stat().st_size<=4096:return None
    raw=stderr.read_bytes()
    pattern=(r'<3>WSL \([0-9]+ - Relay\) ERROR: CreateProcessCommon:[0-9]+: execvpe\('
             +re.escape(argv[6])+r'\) failed: No such file or directory\r?\n')
    if not re.fullmatch(pattern,raw.decode('utf-8',errors='strict')):return None
    return {'schema':'STAGE05_EXACT_WSL_PREEXEC_FAILURE_V1','state':'FAILED_PREEXEC_NO_LINUX_PROGRAM_STARTED',
            'actual_retained_wsl_client_exit':terminal,'argv':argv,'stdout_sha256':A.sha256(stdout),
            'stderr_sha256':A.sha256(stderr),'stderr_bytes':len(raw),'linux_helper_started':False,
            'native_helper_launches':0,'closure_basis':'Exact WSL Relay execvpe failure and retained client exit; no Linux receipt synthesized',
            'scientific_adoption_authorized':False}


def persist_wsl_exit(api,child,out,argv,birth,nonce,step,source_sha,linux_sha):
    """Save the actual retained client terminal before reading Linux evidence."""
    A.require(child.poll() is not None and birth is not None,'Retained setup client has not closed with a recorded birth')
    terminal=api.identity(int(child._handle),child.pid,birth['executable'],birth['session_id'])
    A.require(terminal['exited'] is True and terminal['pid']==birth['pid']
              and terminal['creation_filetime']==birth['creation_filetime']
              and terminal['exit_filetime']>terminal['creation_filetime']
              and terminal['executable']==birth['executable'] and terminal['session_id']==birth['session_id']
              and type(terminal['exit_code']) is int,'Actual retained setup client terminal differs')
    value={'schema':'STAGE05_SETUP_WSL_RETAINED_EXIT_V1','owner_nonce':nonce,'step':step,
           'source_sha256':source_sha,'linux_source_sha256':linux_sha,'argv':argv,'birth':birth,'terminal':terminal,
           'stdout_sha256':A.sha256(out/'wsl.stdout.txt'),'stderr_sha256':A.sha256(out/'wsl.stderr.txt')}
    path=out/'wsl_exit.json'
    if path.exists(): A.require(A.read_json(path)==value,'Existing retained client terminal changed')
    else: A.atomic(path,value)
    return terminal


def linux_closure_readback(out,argv,terminal,nonce,step,linux_sha,expected_command):
    linux=A.read_json(out/'linux_terminal.json')
    A.require(linux['schema']=='STAGE05_SETUP_LINUX_TERMINAL_V1' and linux['scope']==SCOPE
              and linux['owner_nonce']==nonce and linux['step']==step and linux['source_sha256']==linux_sha
              and linux['owned_closure_proven'] is True and linux['scientific_adoption_authorized'] is False
              and linux['state'] in ('FAILED','PASS_NONSCIENTIFIC_SETUP_STEP'),'Actual Linux setup terminal scope/closure differs')
    bootstrap=linux['bootstrap']
    A.require(bootstrap['argv']==argv[8:] and bootstrap['executable']==argv[6]
              and re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',bootstrap['boot_id'])
              and type(bootstrap['identity']['pid']) is int and bootstrap['identity']['pid']>0
              and str(bootstrap['identity']['start_ticks']).isdigit() and int(bootstrap['identity']['start_ticks'])>0
              and linux['remaining_direct_children']==[],'Actual Linux bootstrap argv/birth/empty-child proof differs')
    success=linux['state']=='PASS_NONSCIENTIFIC_SETUP_STEP'; count=linux['owned_command_count']
    A.require(terminal['exit_code']==(0 if success else 2) and linux['no_native_launch'] is (count==0),
              'Actual failed/successful client exit or native count differs')
    commands=command_readback(out,count,step,expected_command,success)
    return linux,commands


def failed_client_readback(api,child,out,argv,birth,nonce,step,source_sha,linux_sha,expected_command,candidate=None,progress=None):
    """One finite own-client drain, actual exit persistence, then closure only."""
    if child.poll() is None: child.wait(timeout=15)
    terminal=persist_wsl_exit(api,child,out,argv,birth,nonce,step,source_sha,linux_sha)
    value={'actual_wsl_exit':terminal,'wsl_exit_receipt_sha256':A.sha256(out/'wsl_exit.json')}
    if progress is not None: progress.update(value)
    if (out/'linux_terminal.json').exists():
        linux,commands=linux_closure_readback(out,argv,terminal,nonce,step,linux_sha,expected_command)
        value.update(native_commands=commands,linux_terminal_sha256=A.sha256(out/'linux_terminal.json'),
                     failed_scope_closed=True,closure_basis='RETAINED_WSL_EXIT_AND_ACTUAL_LINUX_TERMINAL')
    else:
        failure=exact_preexec_failure(out,argv,birth,terminal,candidate)
        A.require(failure is not None,'No independently checkable Linux or exact preexec closure receipt')
        path=out/'preexec_failure.json'
        if path.exists(): A.require(A.read_json(path)==failure,'Existing exact preexec receipt changed')
        else: A.atomic(path,failure)
        value['preexec_failure_sha256']=A.sha256(path)
    return value


def readback_worker():
    parser=argparse.ArgumentParser(description='Owned tiny Windows DriveFS readback only')
    parser.add_argument('--drivefs-readback-worker',action='store_true')
    parser.add_argument('--request',required=True,type=Path); parser.add_argument('--request-sha256',required=True)
    args=parser.parse_args(); request=args.request
    A.require(WORK==EXACT_WORK and os.name=='nt' and request.parent.parent==WORK
              and not request.is_symlink() and A.sha256(request)==args.request_sha256,'Exact C owned readback request differs')
    value=A.read_json(request)
    A.require(value['scope']==SCOPE and value['source_sha256']==A.sha256(__file__)
              and value['root']==str(ROOT),'Actual Windows readback source/root differs')
    stdout=Path(value['stdout']); A.require(stdout==request.parent/'commands/drivefs.stdout.txt','Readback source escapes owned spool')
    data={'scope':SCOPE,'request_sha256':args.request_sha256,'owner_nonce':value['owner_nonce'],
          'source_sha256':A.sha256(__file__),'readback':drivefs_readback(stdout)}
    with (request.parent/'drivefs_windows_readback.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(data,stream,indent=2,sort_keys=True); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    return 0


def main():
    import sys
    if '--drivefs-readback-worker' in sys.argv: return readback_worker()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--step',choices=('diagnose','toolchain','runtime','storage','drivefs'),required=True)
    parser.add_argument('--output',required=True,type=Path)
    for name in ('controller-receipt','controller-receipt-sha256','controller-observer-sha256',
                 'toolchain-proof','toolchain-proof-sha256','candidate-output','linux-source-sha256'):
        parser.add_argument('--'+name)
    parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    A.require(WORK==EXACT_WORK and os.name=='nt','Exact current Windows C setup required')
    A.require(all(A.sha256(WORK/name)==pin for name,pin in PINS.items()),'Reviewed setup helper bytes differ')
    linux_source=WORK/'stage5_setup_linux.py'
    plan={'scope':SCOPE,'state':'PREPARED_NOT_RUN','step':args.step,'source_sha256':A.sha256(__file__),
          'linux_source_sha256':A.sha256(linux_source),'source_pins':PINS,'scientific_adoption_authorized':False}
    if not args.run: print(json.dumps(plan,indent=2)); return 0
    A.require(A.SHA.fullmatch(args.linux_source_sha256 or '') and A.sha256(linux_source)==args.linux_source_sha256,
              'Explicit reviewed Linux setup SHA required')
    A.require(args.output.is_absolute() and args.output.parent==WORK and args.output==args.output.resolve()
              and not args.output.exists(),'New direct C work spool required')
    controller_path=Path(args.controller_receipt or '')
    A.require(WORK in controller_path.resolve().parents and controller_path.is_file()
              and A.sha256(controller_path)==args.controller_receipt_sha256
              and args.controller_observer_sha256==PINS['observe_iqtree_controller_exit.py'],'Pinned actual controller closure required')
    inputs={name:A.read_json(ATTEMPT/name) for name in ('launch.json','exit.json','execution_state_restored.json','lock_released.json')}
    A.require(all(A.sha256(ATTEMPT/name)==pin for name,pin in CLOSURE_PINS.items()),'Actual original closure bytes differ')
    controller=A.read_json(controller_path)
    previous=prior_closure(controller,args.controller_observer_sha256,inputs['launch.json'],inputs['exit.json'],
                           inputs['execution_state_restored.json'],inputs['lock_released.json'])
    A.require(inputs['exit.json']['launch_sha256']==A.sha256(ATTEMPT/'launch.json'),'Previous exit/launch bytes differ')
    args.output.mkdir(); api=A.Win(); owner=api.identity(api.current(),os.getpid()); nonce=uuid.uuid4().hex
    child=None; birth=None; argv=None; windows_worker_started=False
    closure=True; stop_sha=None; lease_path=args.output/'owner_lease.json'; result={**plan,'state':'FAILED','owner_nonce':nonce,
              'actual_windows_owner':owner,'controller_receipt_sha256':args.controller_receipt_sha256,'lease_replace_stats':{},
              'prior_native_files':{name:A.sha256(ATTEMPT/name) for name in inputs}}
    with A.WorkflowLock(api) as lock:
        def authority():
            control=A.read_json(ROOT/'status/run_control.json')
            A.require(control['state']=='ACTIVE_DIRECT_USER_CONTINUATION' and control['automatic_resume'] is False,'Current direct authority absent')
        def lease(active=True):
            authority(); resources=api.resources([ROOT,args.output]); now=time.time()
            if active:
                A.require(resources['physical_available_bytes']>=1879048192 and resources['commit_headroom_bytes']>=1879048192
                          and all(v>=10737418240 for v in resources['disk_available_bytes'].values()),'Actual setup resource reserve insufficient')
            L.atomic_owner_lease(lease_path,{'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1','nonce':nonce,'workflow_lock_held':active,
                     'workflow_lock':lock.identity,'owner_pid':owner['pid'],'owner_creation_filetime':str(owner['creation_filetime']),
                     'measured_unix':now,'expires_unix':now+3 if active else now,'utc':A.utc(),
                     'windows_available_bytes':resources['physical_available_bytes'],'windows_commit_headroom_bytes':resources['commit_headroom_bytes'],
                     'disk_available_bytes':resources['disk_available_bytes']},result['lease_replace_stats'])
            result['latest_actual_resources']=resources
        try:
            A.require(not STOP.exists(),'Existing unproven-closure stop requires reconciliation')
            for row in previous: reject_live_exact(api,row)
            result['actual_ubuntu_registration']=registered_backing()
            lease(); result['workflow_lock']=lock.identity
            if args.step=='storage': result['g_underlay_before']=underlay(create=True)
            held=args.output/'actual_owner_lock.json'; A.atomic(held,{'scope':SCOPE,'owner':owner,'workflow_lock':lock.identity,'owner_nonce':nonce})
            # Bootstrap always runs the system interpreter. It observes the
            # current mount before launching retained runtime helpers.
            interpreter='/usr/bin/python3'
            argv=[WSL,'-d','Ubuntu','-u','root','--exec',interpreter,'-B',linux_path(linux_source),
                  '--step',args.step,'--output',linux_path(args.output),'--owner-lease',linux_path(lease_path),
                  '--owner-nonce',nonce,'--source-sha256',args.linux_source_sha256,
                  '--owner-lock-receipt',linux_path(held),'--owner-lock-sha256',A.sha256(held)]
            if args.step not in ('diagnose','toolchain'):
                proof=Path(args.toolchain_proof or '')
                A.require(proof.is_file() and A.sha256(proof)==args.toolchain_proof_sha256,'Pinned toolchain proof required')
                argv+=['--toolchain-proof',linux_path(proof),'--toolchain-proof-sha256',args.toolchain_proof_sha256]
            if args.step in ('runtime','storage'):
                candidate=Path(args.candidate_output or '')
                A.require(candidate.is_absolute() and candidate.parent==WORK and not candidate.exists(),'Fresh direct C candidate output required')
                argv+=['--candidate-output',linux_path(candidate)]
            expected_commands={
                'diagnose':[],
                'toolchain':['/usr/bin/mount','-o','loop','/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/toolchain.ext4',
                             '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux'],
                'runtime':[LINUX_ENV+'/bin/python','-B',LINUX_WORK+'/stage5_runtime_discovery.py','--discover','--output',
                           linux_path(Path(args.candidate_output))] if args.step=='runtime' else [],
                'storage':['/usr/bin/mount','--bind','/var/tmp/lab_rm_stage05_atomic_v1',
                           '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/.work/stage05_atomic_v1'],
                'drivefs':[LINUX_ENV+'/bin/python','-B',LINUX_WORK+'/stage5_drivefs_filesystem_smoke.py',
                           '--owner-lock-receipt',linux_path(held),'--owner-lock-sha256',A.sha256(held),
                           '--supervisor-sha256',PINS['stage5_atomic_process.py'],'--run']}
            A.atomic(STOP,{'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1','owner_nonce':nonce,'utc':A.utc(),
                          'evidence':str(args.output),'reason':'Setup launch intent; require exact Linux and WSL closure before removal','automatic_resume':False})
            stop_sha=A.sha256(STOP); closure=False
            with (args.output/'wsl.stdout.txt').open('xb') as stdout,(args.output/'wsl.stderr.txt').open('xb') as stderr:
                child=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
                birth=api.identity(int(child._handle),child.pid,retained_image=WSL,retained_session=owner['session_id'])
                A.atomic(args.output/'launch.json',{'argv':argv,'native_wsl_client':birth,'owner_nonce':nonce})
                deadline=time.monotonic()+(960 if args.step=='runtime' else 120)
                while child.poll() is None:
                    A.require(time.monotonic()<deadline,'Bounded setup WSL client deadline expired')
                    lease(); time.sleep(0.5)
                terminal=persist_wsl_exit(api,child,args.output,argv,birth,nonce,args.step,
                                          plan['source_sha256'],args.linux_source_sha256)
                result.update(actual_wsl_exit=terminal,wsl_exit_receipt_sha256=A.sha256(args.output/'wsl_exit.json'))
                if not (args.output/'linux_terminal.json').exists():
                    failure=exact_preexec_failure(args.output,argv,birth,terminal,
                              Path(args.candidate_output) if args.candidate_output else None)
                    if failure is not None:
                        A.atomic(args.output/'preexec_failure.json',failure)
                        result['preexec_failure_sha256']=A.sha256(args.output/'preexec_failure.json')
                        closure=True
                        raise ValueError('Exact retained WSL preexec failure; intended Linux program did not start; setup failed')
                linux,result['native_commands']=linux_closure_readback(args.output,argv,terminal,nonce,args.step,
                     args.linux_source_sha256,expected_commands[args.step])
                closure=True; result.update(actual_wsl_exit=terminal,linux_terminal_sha256=A.sha256(args.output/'linux_terminal.json'))
                A.require(terminal['exit_code']==0 and linux['state']=='PASS_NONSCIENTIFIC_SETUP_STEP','Actual setup step failed after closed scope')
            if args.step=='storage':
                result['g_underlay_after']=underlay(); A.require(result['g_underlay_before']==result['g_underlay_after'],'Windows G underlay changed')
            if args.step=='drivefs':
                import stage5_unc_bind_probe as U
                request=args.output/'drivefs_readback_request.json'
                A.atomic(request,{'scope':SCOPE,'source_sha256':plan['source_sha256'],'root':str(ROOT),
                                 'stdout':str(args.output/'commands/drivefs.stdout.txt'),'owner_nonce':nonce})
                closure=False; windows_worker_started=True
                result['windows_readback_worker']=U.windows_job(api,[sys.executable,'-B',str(Path(__file__).resolve()),
                     '--drivefs-readback-worker','--request',str(request),'--request-sha256',A.sha256(request)],owner,
                     args.output/'windows_readback_worker')
                closure=True; readback=A.read_json(args.output/'drivefs_windows_readback.json')
                A.require(readback['request_sha256']==A.sha256(request) and readback['owner_nonce']==nonce
                          and readback['source_sha256']==plan['source_sha256'],'Actual Windows worker receipt differs')
                result['windows_readback']=readback
                A.require(A.read_json(args.output/'commands/drivefs.stdout.txt')['caller_lock_receipt_sha256']==A.sha256(held),'DriveFS probe used stale lock receipt')
            A.require(A.sha256(STOP)==stop_sha and A.read_json(STOP)['owner_nonce']==nonce,'Owned setup stop marker changed')
            STOP.unlink()
            result['state']='PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK'
        except BaseException as error:
            result['error']={'kind':type(error).__name__,'message':str(error)}
            if child is not None and child.poll() is None:
                try: lease(False)
                except BaseException: pass
        finally:
            try: lease(False)
            except BaseException as error: result['lease_finalizer_error']=str(error)
            # A resource/lease exception may bypass the normal post-poll path.
            # Reopen the same retained handle after the bounded own-child wait;
            # never renew positive admission or turn this failed setup into PASS.
            if child is not None and not closure and not windows_worker_started:
                try:
                    result.update(failed_client_readback(api,child,args.output,argv,birth,nonce,args.step,
                         plan['source_sha256'],args.linux_source_sha256,expected_commands[args.step],
                         Path(args.candidate_output) if args.candidate_output else None,progress=result))
                    closure=True
                except BaseException as error:
                    result['closure_finalizer_error']={'kind':type(error).__name__,'message':str(error)}
            if closure and stop_sha and STOP.exists():
                try:
                    A.require(A.read_json(STOP).get('owner_nonce')==nonce and A.sha256(STOP)==stop_sha,'Owned stop marker changed')
                    STOP.unlink()
                except BaseException as error: result['stop_finalizer_error']=str(error)
            result.update(owned_closure_proven=closure,unknown_closure_stop_preserved=STOP.exists(),utc=A.utc())
            A.atomic(args.output/'result.json',result)
    A.atomic(args.output/'lock_released.json',{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':lock.released,'utc':A.utc()})
    print(json.dumps({'state':result['state'],'result':str(args.output/'result.json')}))
    return 0 if result['state']=='PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK' else 2


# Separate opt-in cold branch. The original 6aa21e4c implementation above,
# including its RW observer/readers and <=1 command accounting, is preserved.
COLD_RETAINED_IMAGE_HANDLES = []  # Do not hide an unproven CloseHandle failure.


def cold_module(name, expected):
    import importlib.util
    path=WORK/name
    A.require(not path.is_symlink() and A.sha256(path)==expected,'Pinned cold owner component differs')
    spec=importlib.util.spec_from_file_location('_owned_cold_'+name[:-3],path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    A.require(A.sha256(path)==expected,'Cold component changed during import')
    return module


def cold_image_identity(api,H):
    """Metadata snapshot after Linux clean detach, immediately before guard.

    The temporary attributes handle is checked closed. The later read lease
    must match the exact snapshot, so a race changes admission to a failure.
    """
    from ctypes import wintypes as w
    create=api.K.CreateFileW;create.restype=w.HANDLE
    create.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
    handle=create(H.IMAGE_PATHS['toolchain_ext4'],0x80,7,None,3,0x00200000,None)
    A.require(handle not in (None,0,ctypes.c_void_p(-1).value),'Cold image attributes handle failed')
    retained={'kind':'METADATA_HANDLE','handle':handle};COLD_RETAINED_IMAGE_HANDLES.append(retained)
    try:
        info=api.FILEINFO();api.ok(api.file_info(handle,ctypes.byref(info)),'Cold image file identity')
        return H.image_identity('toolchain_ext4',{'path':H.IMAGE_PATHS['toolchain_ext4'],
            'volume_serial':info.volume,'file_index':(info.indexHigh<<32)|info.indexLow,
            'creation_filetime':api.ft(info.created),'written_filetime':api.ft(info.written),
            'bytes':(info.sizeHigh<<32)|info.sizeLow,'links':info.links,'attributes':info.attributes})
    finally:
        api.ok(api.close(handle),'Close cold image attributes handle')
        COLD_RETAINED_IMAGE_HANDLES.remove(retained)


def cold_read_json(path,maximum=65536):
    info=path.lstat()
    A.require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
              and not getattr(info,'st_file_attributes',0)&0x400 and info.st_size<=maximum,
              'Plain bounded cold receipt required')
    raw=path.read_bytes();A.require(len(raw)<=maximum,'Cold receipt grew beyond limit')
    return json.loads(raw)


def cold_ledger_readback(C,out,request,linux_sha,nonce,complete=False):
    """Actual fixed ledger, using unchanged single-command reader per phase."""
    phase_dir=out/'phases';records=[];digests=[];commands=[];loop_rw=None;loop_ro=None;total=0
    if not phase_dir.exists():
        A.require(not complete,'Missing actual cold ledger');return records,commands,total
    for index,name in enumerate(C.COLD_PHASES,1):
        path=phase_dir/f'{index:02d}_{name}.json'
        if not path.exists():break
        value=cold_read_json(path,4*1024**2)
        A.require(value.get('phase')==name and value.get('ordinal')==index
                  and value.get('deadline_seconds')==C.COLD_DEADLINES[name]
                  and value.get('owner_nonce')==nonce and value.get('source_sha256')==linux_sha
                  and value.get('request_sha256')==A.sha256(out/'cold_request.json')
                  and value.get('previous_sha256')==(digests[-1] if digests else None)
                  and re.fullmatch('[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',value.get('boot_id','')),
                  'Exact cold phase order/nonce/source/hash chain differs')
        A.require(not records or value['boot_id']==records[0]['boot_id'],'Cold Linux boot changed inside phase ledger')
        if name=='writer_closure':
            aliases=value['loop_aliases']
            A.require(len(aliases)==1 and aliases[0]['read_only'] is False
                      and value['process_exclusion']['relevant_references']==0
                      and value['process_exclusion']['foreign_mount_namespaces']==0,'Writer/native closure evidence differs')
            loop_rw=aliases[0]['loop']
        if name=='mount_ro':
            raw=(phase_dir/'loop_ro/commands/loop_ro.stdout.txt').read_bytes()
            A.require(re.fullmatch(rb'/dev/loop[0-9]+\n',raw),'RO loop exact stdout differs');loop_ro=raw.decode().strip()
        if name in C.COLD_COMMAND_PHASES:
            expected=C.cold_expected_argv(name,request,LINUX_WORK+'/'+out.name,loop_rw,loop_ro,
                proof_sha=A.sha256(out/'cold_proof.json') if name=='worker' else None,
                inputs_sha=A.sha256(out/'capture_inputs.json') if name=='worker' and request['mode']=='capture' else None)
            count=value.get('command_count');A.require(type(count) is int and count in (0,1),'Finite phase command count differs')
            A.require(value['argv']==expected and (count==1 or name=='detach_rw'), 'Exact cold phase argv/count differs')
            status=value.get('state');A.require(status=='DONE' or (name=='worker' and status=='FAILED_CLOSED'),
                                             'Unexpected actual cold native phase state')
            commands+=command_readback(phase_dir/name,count,'toolchain',expected,status=='DONE')
            total+=count
        if name in ('backing_detached','backing_detached_again'):
            A.require(value.get('loop_aliases')==[] and value['process_exclusion']['relevant_references']==0,
                      'Actual clean detached state differs')
            sb=value['clean_superblock']
            A.require(type(sb['state']) is int and sb['state']&1 and not sb['state']&2
                      and type(sb['incompat']) is int and not sb['incompat']&4
                      and type(sb['ro_compat']) is int and not sb['ro_compat']&0x10000
                      and type(sb['last_orphan']) is int and sb['last_orphan']==0
                      and A.SHA.fullmatch(sb['superblock_sha256']), 'Actual clean ext4 state differs')
        if name in ('windows_guard','windows_guard_released'):
            ack_name='guard' if name=='windows_guard' else 'release'
            ack=cold_read_json(out/(ack_name+'_ack.json'))
            A.require(value.get('ack')==ack and ack.get('owner_nonce')==nonce
                      and ack.get('linux_source_sha256')==linux_sha and C.cold_strict_lock(ack.get('workflow_lock')),
                      'Cold phase did not consume exact Windows-owned acknowledgement')
            A.require(ack.get('retained_deny_write_delete_handle') is True if ack_name=='guard'
                      else ack.get('actual_close_handle_succeeded') is True,'Actual Windows guard acquisition/release differs')
        if name=='drvfs_write_refused':
            A.require(value.get('state')=='ACTUAL_CROSS_DRVFS_WRITE_OPEN_REFUSED'
                      and value.get('attempt')=='O_RDWR|O_NOFOLLOW' and value.get('write_called') is False
                      and type(value.get('errno')) is int and value['errno'] in (1,13,16,26),
                      'Actual cross-DrvFS refusal fixture differs')
        records.append(value);digests.append(A.sha256(path))
    expected_files={f'{i+1:02d}_{row["phase"]}.json' for i,row in enumerate(records)}
    A.require({p.name for p in phase_dir.glob('[0-9][0-9]_*.json')}==expected_files,
              'Unexpected/skipped actual cold phase records')
    A.require({p.name for p in phase_dir.iterdir() if p.is_dir()}=={
                  r['phase'] for r in records if r['phase'] in C.COLD_COMMAND_PHASES},
              'Unexpected or unaccounted cold native phase namespace')
    A.require(not complete or len(records)==len(C.COLD_PHASES),'Incomplete actual cold ledger')
    return records,commands,total


def cold_main():
    import sys
    parser=argparse.ArgumentParser(description='Existing paired Stage5 owner cold branch; default NO_OP')
    parser.add_argument('--cold',action='store_true');parser.add_argument('--run',action='store_true')
    parser.add_argument('--mode',choices=('inventory','capture'));parser.add_argument('--output',type=Path)
    for name in ('controller-receipt','controller-receipt-sha256','controller-observer-sha256',
                 'linux-source-sha256','toolchain-proof','toolchain-proof-sha256','runtime','runtime-sha256',
                 'manifest','manifest-sha256','public-review','public-review-sha256','notices','notices-sha256'):
        parser.add_argument('--'+name)
    parser.add_argument('--all-required-runtime-files-public-and-covered',action='store_true')
    parser.add_argument('--all-special-metadata-resolved',action='store_true')
    args=parser.parse_args()
    if not args.run:
        print(json.dumps({'state':'NO_OP_EXISTING_OWNER_COLD_BRANCH_PREPARATION','actual_image_actions':'NOT_RUN',
                          'raw_vhdx_split':'NOT_RUN','cleanup_authority':False}));return 0
    A.require(args.cold and args.mode and args.output and WORK==EXACT_WORK and os.name=='nt',
              'Explicit actual Windows cold mode/output required')
    A.require(all(A.sha256(WORK/n)==p for n,p in PINS.items()),'Original reviewed owner dependency drift')
    linux_source=WORK/'stage5_setup_cold_linux.py'
    A.require(A.SHA.fullmatch(args.linux_source_sha256 or '') and A.sha256(linux_source)==args.linux_source_sha256,
              'Explicit independently reviewed cold Linux owner SHA required')
    C=cold_module(linux_source.name,args.linux_source_sha256)
    A.require(all(A.sha256(WORK/n)==p for n,p in C.COLD_PINS.items()),'Reviewed cold helper drift')
    H=cold_module('stage5_offline_image_read_parts_v2.py',C.COLD_PINS['stage5_offline_image_read_parts_v2.py'])
    A.require(args.output.is_absolute() and args.output.parent==WORK and args.output==args.output.resolve()
              and not args.output.exists() and re.fullmatch('stage5_setup_cold_[A-Za-z0-9_]+',args.output.name),
              'Fresh direct-C cold owner spool required')
    for path in (WORK,*WORK.parents):
        info=path.lstat();A.require(not path.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400,
                                   'Plain C source ancestry required')
    controller=Path(args.controller_receipt or '')
    A.require(WORK in controller.resolve().parents and A.sha256(controller)==args.controller_receipt_sha256
              and args.controller_observer_sha256==PINS['observe_iqtree_controller_exit.py'],
              'Actual retained original IQ controller closure required')
    original={n:A.read_json(ATTEMPT/n) for n in CLOSURE_PINS}
    A.require(all(A.sha256(ATTEMPT/n)==p for n,p in CLOSURE_PINS.items()),'Original actual native closure pins differ')
    previous=prior_closure(A.read_json(controller),args.controller_observer_sha256,original['launch.json'],
                           original['exit.json'],original['execution_state_restored.json'],original['lock_released.json'])
    A.require(original['exit.json']['launch_sha256']==A.sha256(ATTEMPT/'launch.json'),'Original exit/launch binding differs')
    paths={}; pins={}
    for role in ('runtime','toolchain_proof')+(('manifest','public_review','notices') if args.mode=='capture' else ()):
        value=getattr(args,role);pin=getattr(args,role+'_sha256');path=Path(value or '')
        A.require(path.is_absolute() and WORK in path.parents and path.resolve()==path
                  and not path.is_symlink() and A.SHA.fullmatch(pin or '') and A.sha256(path)==pin,
                  'Explicit exact C cold input pin required: '+role)
        paths[role]=path;pins[role]=pin
    A.require(pins['runtime']==C.COLD_RUNTIME_SHA,'Only unchanged scientific runtime06 is accepted')
    if args.mode=='capture':
        A.require(args.all_required_runtime_files_public_and_covered and args.all_special_metadata_resolved,
                  'Actual independent public scope/metadata review must precede capture')
    args.output.mkdir();out=args.output;api=A.Win();owner=api.identity(api.current(),os.getpid());nonce=uuid.uuid4().hex
    source_sha=A.sha256(__file__);lease_path=out/'owner_lease.json';lease_stats={};child=None;birth=None
    image_lease=None;guard_released=False;stop_sha=None;closed=False;restored=False
    result={'schema':'STAGE05_SETUP_COLD_WINDOWS_RESULT_V1','scope':SCOPE,'state':'FAILED',
            'source_sha256':source_sha,'linux_source_sha256':args.linux_source_sha256,'owner_nonce':nonce,
            'actual_windows_owner':owner,'scientific_adoption_authorized':False,
            'actual_raw_image_split':'NOT_RUN','remote_upload':'NOT_RUN','cold_restore':'NOT_RUN','cleanup_authority':False}
    request={'schema':'STAGE05_SETUP_COLD_REQUEST_V1','mode':args.mode,'owner_nonce':nonce,
             'runtime':linux_path(paths['runtime']),'runtime_sha256':pins['runtime'],
             'toolchain_proof':linux_path(paths['toolchain_proof']),'toolchain_proof_sha256':pins['toolchain_proof'],
             'worker_output':LINUX_WORK+('/stage5_runtime_inventory_private_' if args.mode=='inventory' else '/stage5_runtime_capture_')+nonce,
             'worker_terminal':LINUX_WORK+'/stage5_runtime_capture_terminal_'+nonce+'.json',
             'rediscovery_output':LINUX_WORK+'/stage5_runtime_actual_cold_'+nonce+'.json'}
    if args.mode=='capture':
        for role in ('manifest','public_review','notices'):request.update({role:linux_path(paths[role]),role+'_sha256':pins[role]})
        request.update(all_required_runtime_files_public_and_covered=True,all_special_metadata_resolved=True)
    A.atomic(out/'cold_request.json',request)
    argv=[WSL,'-d','Ubuntu','-u','root','--exec','/usr/bin/python3','-B',linux_path(linux_source),'--cold','--run',
          '--request',linux_path(out/'cold_request.json'),'--request-sha256',A.sha256(out/'cold_request.json'),
          '--output',linux_path(out),'--source-sha256',args.linux_source_sha256,'--windows-source-sha256',source_sha,
          '--owner-lease',linux_path(lease_path),'--owner-nonce',nonce]
    started=time.monotonic()
    with A.WorkflowLock(api) as lock:
        def lease(active=True):
            control=A.read_json(ROOT/'status/run_control.json')
            A.require(control['state']=='ACTIVE_DIRECT_USER_CONTINUATION' and control['automatic_resume'] is False,
                      'Current direct project authority absent')
            A.require(C.cold_strict_lock(lock.identity),'Exact immutable original WorkflowLock required')
            resources=api.resources([ROOT,out]);now=time.time()
            if active:
                A.require(time.monotonic()-started<C.COLD_MAX_SECONDS+60 and
                          resources['physical_available_bytes']>=2176*1024**2 and resources['commit_headroom_bytes']>=2176*1024**2
                          and all(v>=10*1024**3 for v in resources['disk_available_bytes'].values()),
                          'Cold owner deadline/current physical/commit/disk admission failed')
                A.require(A.sha256(__file__)==source_sha and A.sha256(linux_source)==args.linux_source_sha256
                          and all(A.sha256(WORK/n)==p for n,p in {**PINS,**C.COLD_PINS}.items()),'Cold owner/helper source drift')
            value={'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1','nonce':nonce,'workflow_lock_held':active,
                   'workflow_lock':lock.identity,'owner_pid':owner['pid'],'owner_creation_filetime':str(owner['creation_filetime']),
                   'measured_unix':now,'expires_unix':now+3 if active else now,'utc':A.utc(),
                   'windows_available_bytes':resources['physical_available_bytes'],
                   'windows_commit_headroom_bytes':resources['commit_headroom_bytes'],'disk_available_bytes':resources['disk_available_bytes']}
            L.atomic_owner_lease(lease_path,value,lease_stats);return value
        def ack(name,phase_name,extra):
            A.atomic(out/(name+'_ack.json'),{'schema':'STAGE05_SETUP_COLD_WINDOWS_ACK_V1','phase':name,
                'owner_nonce':nonce,'workflow_lock':lock.identity,
                'windows_owner':{'pid':owner['pid'],'creation_filetime':str(owner['creation_filetime'])},
                'windows_source_sha256':source_sha,'linux_source_sha256':args.linux_source_sha256,
                'linux_phase_sha256':A.sha256(out/'phases'/phase_name),**extra})
        try:
            A.require(not STOP.exists(),'Unproven closure/restoration STOP needs root reconciliation')
            for row in previous:reject_live_exact(api,row)
            result['actual_ubuntu_registration']=registered_backing();lease()
            A.atomic(out/'actual_owner_lock.json',{'owner':owner,'workflow_lock':lock.identity,'owner_nonce':nonce,'scope':SCOPE})
            A.atomic(STOP,{'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1','owner_nonce':nonce,'utc':A.utc(),
                          'evidence':str(out),'reason':'Cold detach intent; require actual owned closure AND RW/runtime06 restoration',
                          'automatic_resume':False})
            stop_sha=A.sha256(STOP)
            with (out/'wsl.stdout.txt').open('xb') as stdout,(out/'wsl.stderr.txt').open('xb') as stderr:
                child=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
                birth=api.identity(int(child._handle),child.pid,retained_image=WSL,retained_session=owner['session_id'])
                A.atomic(out/'launch.json',{'argv':argv,'native_wsl_client':birth,'owner_nonce':nonce})
                while child.poll() is None:
                    lease()
                    if image_lease is not None and image_lease.handle is not None:image_lease.check()
                    if (out/'phases/04_backing_detached.json').exists() and not (out/'guard_ack.json').exists():
                        records,_,_=cold_ledger_readback(C,out,request,args.linux_source_sha256,nonce)
                        A.require(len(records)==4,'Only exact detached prefix may acquire Windows guard')
                        identity=cold_image_identity(api,H)
                        # Private snapshot, never exposed to a caller that may mutate it.
                        image_lease=H.ImageReadLease(api,'toolchain_ext4',dict(identity),lease)
                        COLD_RETAINED_IMAGE_HANDLES.append(image_lease)
                        image_lease.__enter__()
                        ack('guard','04_backing_detached.json',{'image_identity':dict(identity),
                            'retained_deny_write_delete_handle':True,'helper_source_sha256':C.COLD_PINS['stage5_offline_image_read_parts_v2.py']})
                    if (out/'phases/13_backing_detached_again.json').exists() and not guard_released:
                        records,_,_=cold_ledger_readback(C,out,request,args.linux_source_sha256,nonce)
                        A.require(len(records)==13 and image_lease is not None and image_lease.handle is not None,
                                  'RO detached exact ledger required before image handle release')
                        image_lease.check();image_lease.close_owned()
                        COLD_RETAINED_IMAGE_HANDLES.remove(image_lease);guard_released=True
                        ack('release','13_backing_detached_again.json',{'actual_close_handle_succeeded':True})
                    time.sleep(0.2)
            terminal=persist_wsl_exit(api,child,out,argv,birth,nonce,'cold',source_sha,args.linux_source_sha256)
            result['actual_wsl_exit']=terminal;result['wsl_exit_receipt_sha256']=A.sha256(out/'wsl_exit.json')
            linux=cold_read_json(out/'linux_terminal.json',4*1024**2)
            A.require(linux.get('schema')=='STAGE05_SETUP_COLD_LINUX_TERMINAL_V1' and linux.get('scope')==SCOPE
                      and linux.get('owner_nonce')==nonce and linux.get('source_sha256')==args.linux_source_sha256
                      and linux.get('windows_source_sha256')==source_sha and linux.get('request_sha256')==A.sha256(out/'cold_request.json')
                      and linux.get('bootstrap',{}).get('argv')==argv[8:]
                      and linux['bootstrap']['executable']=='/usr/bin/python3'
                      and type(linux['bootstrap']['identity']['pid']) is int
                      and str(linux['bootstrap']['identity']['start_ticks']).isdigit()
                      and linux.get('remaining_direct_children')==[] and linux.get('owned_closure_proven') is True,
                      'Actual cold Linux/bootstrap/owned closure evidence differs')
            records,commands,total=cold_ledger_readback(C,out,request,args.linux_source_sha256,nonce,True)
            A.require(linux['completed_phases']==list(C.COLD_PHASES) and linux['owned_command_count']==total
                      and linux['phase_ledger_sha256s']==[A.sha256(out/'phases'/f'{i+1:02d}_{name}.json') for i,name in enumerate(C.COLD_PHASES)],
                      'Actual complete cold native command/phase accounting differs')
            closed=True
            rediscovery=WORK/PurePosixPath(request['rediscovery_output']).name
            A.require(guard_released and image_lease.handle is None and linux.get('rw_restoration_proven') is True
                      and linux['rediscovery_sha256']==A.sha256(rediscovery)==C.COLD_RUNTIME_SHA
                      and records[-1]['rediscovery_sha256']==C.COLD_RUNTIME_SHA
                      and records[-1]['toolchain_proof']['mount']['filesystem']=='ext4'
                      and 'rw' in records[-1]['toolchain_proof']['mount']['options'].split(','),
                      'Current scientific runtime06/RW restoration unproven')
            restored=True;result.update(native_commands=commands,linux_terminal_sha256=A.sha256(out/'linux_terminal.json'),
                                       phase_ledger_sha256s=linux['phase_ledger_sha256s'],rediscovery_sha256=A.sha256(rediscovery))
            A.require(terminal['exit_code']==0 and linux['state']=='PASS_COLD_STEP_AND_RUNTIME06_RESTORED',
                      'Cold worker failed despite actual restored/closed scope')
            A.require(A.sha256(STOP)==stop_sha and A.read_json(STOP)['owner_nonce']==nonce,'Owned cold STOP changed')
            STOP.unlink();result['state']='PASS_COLD_STEP_CLOSED_AND_RUNTIME06_RESTORED'
        except BaseException as error:
            result['error_kind']=type(error).__name__
        finally:
            # Positive admission is never renewed after failure. Do not launch
            # a second Linux owner or silently release a guard while RO loops
            # or Linux descendants remain uncertain.
            try:lease(False)
            except BaseException as error:result['lease_finalizer_error_kind']=type(error).__name__
            if child is not None and child.poll() is None:
                try:child.wait(timeout=15)
                except BaseException as error:result['client_finalizer_error_kind']=type(error).__name__
            if child is not None and child.poll() is not None and birth is not None:
                try:
                    persist_wsl_exit(api,child,out,argv,birth,nonce,'cold',source_sha,args.linux_source_sha256)
                    result['actual_retained_wsl_exit_recorded']=True
                except BaseException as error:result['exit_finalizer_error_kind']=type(error).__name__
            result.update(owned_closure_proven=closed,rw_restoration_proven=restored,
                          windows_guard_checked_released=guard_released,
                          retained_image_handles_unresolved=len(COLD_RETAINED_IMAGE_HANDLES),
                          unknown_closure_or_restoration_stop_preserved=STOP.exists(),lease_replace_stats=lease_stats,utc=A.utc())
            A.atomic(out/'result.json',result)
    A.atomic(out/'lock_released.json',{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':lock.released,'utc':A.utc()})
    print(json.dumps({'state':result['state'],'result':str(out/'result.json')}))
    return 0 if result['state']=='PASS_COLD_STEP_CLOSED_AND_RUNTIME06_RESTORED' else 2


if __name__=='__main__':
    import sys
    raise SystemExit(cold_main() if '--cold' in sys.argv or len(sys.argv)==1 else main())
