"""Fixed-role Win32 identities for the separately reviewed V10 recovery protocol."""
from pathlib import Path
import ctypes as c
from ctypes import wintypes as t
import hashlib, json, msvcrt, os, subprocess, sys, time
import stage04_controller as C
import stage04_windows_job_v6 as J

ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
RUNTIME=HISTORY/'.work/stage04_recovery_v10'
LOCK=HISTORY/'.work/workflow.lock'
REPORT=ROOT/'reports/stage04/recovery_v10'
NEGATIVE=ROOT/'reports/stage04/recovery_v9/failed_attempt_reconciliation_v1.json'
OLD=ROOT/'.work/stage04_inference_windows_v6'
OUT=ROOT/'.work/stage04_inference_windows_v10'
PYTHON=Path(r'C:\Users\wheel\AppData\Local\Python\pythoncore-3.14-64\python.exe')
PYTHONW=PYTHON.with_name('pythonw.exe')
VALIDATOR=HISTORY/'.tools/validation_env/Scripts/python.exe'
NAMES=['primary196','sensitivity162','sensitivity187_markers','sensitivity_complete155']
FROZEN={'scripts/stage04_native_windows_v6.py':'154b5236781f0380f5443a1ec3cff7b89aaa56743074afb6cafae388a24a7da7',
 'scripts/stage04_windows_job_v6.py':'eabda371999b484532878b2e1652034a63e1de3a8860472540202b229797e03c',
 'scripts/stage04_windows_validate_v6.py':'d075c4d53e506f10e328d627e2b2e24db19edb5256daa902ea610d5a06989d5d',
 'config/host_inference_stage04_windows_v6.json':'2b380e6f899571410f3d32d1770dc1f08b6618e48e22bfe1b582620af48355d1',
 'scripts/stage04_closed_boundary_v2.py':'9671634bd68764ee5167bf63b09f515f6836610e67c340b3f5c57e2e1d2e7c99'}
FREEZE_SHA='c3f903733c1bb1f37611ac43b221ff1c147dc063859759c814991fe750823369'
CACHE_SHA='0aeefd2a1f1098e924ca06bdb785b7bff2ab0fff5939b3cd3df4ca90b3896b03'
K=J.K
open_process=J.bind(K,'OpenProcess',t.HANDLE,[t.DWORD,t.BOOL,t.DWORD])
image_name=J.bind(K,'QueryFullProcessImageNameW',t.BOOL,[t.HANDLE,t.DWORD,t.LPWSTR,c.POINTER(t.DWORD)])
in_job=J.bind(K,'IsProcessInJob',t.BOOL,[t.HANDLE,t.HANDLE,c.POINTER(t.BOOL)])

class FILEINFO(c.Structure):
    _fields_=[('attributes',t.DWORD),('created',t.FILETIME),('accessed',t.FILETIME),('written',t.FILETIME),
      ('volume',t.DWORD),('sizeHigh',t.DWORD),('sizeLow',t.DWORD),('links',t.DWORD),('indexHigh',t.DWORD),('indexLow',t.DWORD)]
file_info=J.bind(K,'GetFileInformationByHandle',t.BOOL,[t.HANDLE,c.POINTER(FILEINFO)])

def lock_identity(lock):
    info=FILEINFO();J.ok(file_info(msvcrt.get_osfhandle(lock.stream.fileno()),c.byref(info)),'Actual workflow lock file identity')
    return {'path':str(LOCK),'volume_serial':info.volume,'file_index':(info.indexHigh<<32)|info.indexLow,
      'creation_filetime':J.filetime(info.created),'locked_byte':0,'lock_kind':'msvcrt.LK_NBLCK'}

def process_handle(pid):
    h=open_process(0x100000|0x1000,False,int(pid))
    if not h:
        error=c.get_last_error()
        if error==87:return None
        raise c.WinError(error,'Process query denied/failed; absence cannot be inferred')
    return h

def handle_identity(h,pid,retained_executable=None):
    created,ended,kernel,user=(t.FILETIME() for _ in range(4))
    J.ok(J.times(h,*[c.byref(x) for x in (created,ended,kernel,user)]),'GetProcessTimes identity')
    wait=J.wait(h,0);C.check(wait in (0,258),'Process identity wait failed')
    buffer=c.create_unicode_buffer(32768);size=t.DWORD(len(buffer));source='ACTUAL_HANDLE_IMAGE_QUERY'
    if not image_name(h,0,buffer,c.byref(size)):
        error=c.get_last_error()
        if error!=31 or J.wait(h,0)!=0:raise c.WinError(error,'QueryFullProcessImageNameW')
        buffer.value=retained_executable or '';source='RETAINED_SAME_HANDLE_LIVE_IMAGE_QUERY' if retained_executable else 'IMAGE_UNAVAILABLE_AFTER_ACTUAL_SIGNALED_EXIT'
        wait=0
    code=t.DWORD();J.ok(J.exit_code(h,c.byref(code)),'Actual process exit code')
    return {'pid':int(pid),'creation_filetime':J.filetime(created),'exit_filetime':J.filetime(ended),
      'executable':buffer.value,'executable_identity_source':source,'state':'EXITED' if wait==0 else 'RUNNING',
      'actual_exit_code':code.value if wait==0 else None,'cpu_seconds':(J.filetime(kernel)+J.filetime(user))/1e7}

def process_identity(pid,expected=None):
    h=process_handle(pid)
    if h is None:return {'pid':int(pid),'recorded_creation_filetime':expected,'state':'ABSENT_WIN32_ERROR_INVALID_PARAMETER'}
    try:
        row=handle_identity(h,pid)
        if expected is not None and row['creation_filetime']!=expected:row['state']='PID_REUSED_DIFFERENT_CREATION'
        return {**row,'recorded_creation_filetime':expected}
    finally:J.close(h)

def pins():
    for rel,sha in FROZEN.items():C.check(C.digest(ROOT/rel)==sha,'Retained source changed: '+rel)
    C.check(C.digest(OLD/'inference_freeze.json')==FREEZE_SHA,'Original immutable freeze changed')
    C.check(C.digest(OLD/'analyses/primary196/iqtree/host.model.gz')==CACHE_SHA,'Retained model cache changed')

class ENTRY(c.Structure):
    _fields_=[('size',t.DWORD),('usage',t.DWORD),('pid',t.DWORD),('heap',c.c_size_t),('module',t.DWORD),
      ('threads',t.DWORD),('parent',t.DWORD),('priority',t.LONG),('flags',t.DWORD),('exe',t.WCHAR*260)]
snapshot=J.bind(K,'CreateToolhelp32Snapshot',t.HANDLE,[t.DWORD,t.DWORD])
first=J.bind(K,'Process32FirstW',t.BOOL,[t.HANDLE,c.POINTER(ENTRY)])
next_entry=J.bind(K,'Process32NextW',t.BOOL,[t.HANDLE,c.POINTER(ENTRY)])

def process_table():
    h=snapshot(2,0);C.check(h not in (None,c.c_void_p(-1).value),'Process snapshot failed')
    rows={};e=ENTRY();e.size=c.sizeof(e)
    try:
        yes=first(h,c.byref(e));J.ok(yes,'Process32FirstW')
        while yes:
            rows[e.pid]={'pid':e.pid,'parent_pid':e.parent,'basename':e.exe}
            yes=next_entry(h,c.byref(e))
        C.check(c.get_last_error()==18,'Incomplete process snapshot')
        return rows
    finally:J.close(h)

def isolation(runtime):
    identity=process_identity(os.getpid());flag=t.BOOL()
    J.ok(in_job(J.current(),None,c.byref(flag)),'IsProcessInJob(controller,NULL)')
    # System ancestors do not grant this limited interactive account a process
    # handle. Read their identity metadata through the ordinary permitted WMI
    # provider, inside a bounded owned query job. This is an explicit alternative
    # evidence method, not an inference from access denied. Old-descendant
    # reconciliation still uses strict Win32 handles and rejects access errors.
    import stage04_windows_job_v10 as J9
    query=Path(runtime)/'ancestor_query'
    ps="$ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process | ForEach-Object { [pscustomobject]@{pid=$_.ProcessId;parent_pid=$_.ParentProcessId;basename=$_.Name;creation_filetime_microsecond_precision=if($_.CreationDate){$_.CreationDate.ToUniversalTime().ToFileTimeUtc()}else{$null}} }) | ConvertTo-Json -Depth 4 -Compress"
    result=J9.run_job(['C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe','-NoProfile','-NonInteractive','-Command',ps],
      ROOT,query,cap_bytes=256*1024**2,deadline_seconds=20,role='BOUNDED_WMI_ANCESTRY_IDENTITY_QUERY')
    C.check(result['exit_code']==0,'Permitted WMI ancestor evidence failed; isolation blocked')
    rows={r['pid']:r for r in json.loads((query/'stdout.txt').read_text(encoding='utf-8-sig'))}
    chain=[];p=rows[os.getpid()]['parent_pid'];visited=set();child_created=identity['creation_filetime'];terminal=None
    while p and p in rows:
        row=rows[p];created=row['creation_filetime_microsecond_precision']
        C.check(isinstance(created,int) and created>0,'Ancestor creation evidence unavailable; isolation blocked')
        if created>child_created:
            terminal={'pid':p,'reason':'RECORDED_PARENT_PID_REUSED_AFTER_CHILD_CREATION','actual_creation_filetime_microsecond_precision':created,
              'child_creation_filetime':child_created};break
        C.check(p not in visited,'Cyclic ancestry despite strictly earlier creation tokens');visited.add(p)
        chain.append(row);child_created=created;p=row['parent_pid']
    C.check(not any('codex' in r['basename'].lower() for r in chain),'CodexCLI ancestor rejected')
    outer=None
    if flag.value:
        controls=J.EXTENDED();account=J.ACCOUNTING();pids=J.PIDS()
        J.ok(J.query_job(None,9,c.byref(controls),c.sizeof(controls),None),'Actual current outer job controls')
        J.ok(J.query_job(None,1,c.byref(account),c.sizeof(account),None),'Actual current outer job accounting')
        J.ok(J.query_job(None,3,c.byref(pids),c.sizeof(pids),None),'Actual current outer job PIDs')
        C.check(pids.assigned==pids.listed and pids.listed<=64 and os.getpid() in list(pids.ids[:pids.listed]),'Incomplete outer job identity evidence')
        outer={'queried_using':'QueryInformationJobObject(NULL) in actual controller','name_or_owner_handle':'NOT_AVAILABLE_FROM_THIS_API',
          'limit_flags':controls.BasicLimitInformation.LimitFlags,'process_committed_cap_bytes':controls.ProcessMemoryLimit,
          'aggregate_job_committed_cap_bytes':controls.JobMemoryLimit,'affinity_mask':controls.BasicLimitInformation.Affinity,
          'active_processes':account.ActiveProcesses,'process_ids':list(pids.ids[:pids.listed]),
          'origin':'NOT_PROVED_BY_IsProcessInJob_ALONE','lifetime_review':'REQUIRED_HASH_BOUND_PARENT_ACCEPTANCE_BEFORE_PRODUCTION'}
    return {'utc':C.now(),'controller':identity,'is_process_in_job_null':bool(flag.value),'ancestors':chain,
      'codex_cli_ancestor':False,'silent_breakaway':False,'ancestry_terminal':terminal,
      'ancestor_identity_method':'Win32_Process permitted WMI metadata; creation precision is microseconds, not native100ns',
      'ancestor_query_real_exit_sha256':C.digest(query/'exit.json'),'actual_outer_job':outer}

def topology():
    f=J.bind(K,'GetLogicalProcessorInformationEx',t.BOOL,[c.c_int,c.c_void_p,c.POINTER(t.DWORD)])
    size=t.DWORD();f(0,None,c.byref(size));C.check(c.get_last_error()==122 and 0<size.value<65536,'CPU topology size failed')
    buf=c.create_string_buffer(size.value);J.ok(f(0,buf,c.byref(size)),'CPU topology query')
    raw=buf.raw[:size.value];offset=0;cores=[]
    while offset<len(raw):
        relation=int.from_bytes(raw[offset:offset+4],'little');length=int.from_bytes(raw[offset+4:offset+8],'little')
        C.check(length>=48 and relation==0 and offset+length<=len(raw),'Unsupported CPU topology record')
        C.check(int.from_bytes(raw[offset+30:offset+32],'little')==1 and int.from_bytes(raw[offset+40:offset+42],'little')==0,'Multi-group CPU topology needs review')
        cores.append({'physical_core':len(cores),'smt':bool(raw[offset+8]&1),'efficiency_class':raw[offset+9],
          'logical_mask':int.from_bytes(raw[offset+32:offset+40],'little')});offset+=length
    chosen=sorted(cores,key=lambda r:(-int(r['smt']),-r['efficiency_class'],r['physical_core']))[:2]
    mask=sum(r['logical_mask']&-r['logical_mask'] for r in chosen)
    allowed,system=J.SIZE(),J.SIZE();J.ok(J.affinity(J.current(),c.byref(allowed),c.byref(system)),'Controller allowed affinity')
    C.check(len(chosen)==2 and all(r['smt'] for r in chosen) and mask==5 and allowed.value&mask==mask and system.value&mask==mask,
      'Two distinct performance cores/mask5 not independently confirmed')
    return {'utc':C.now(),'physical_cores':cores,'chosen_cores':chosen,'affinity_mask':mask,'controller_allowed_mask':allowed.value,
      'system_mask':system.value,'threads':2,'selection':'Two SMT-capable highest-efficiency physical cores; one logical CPU from each'}

def command(argv,timeout=120,cwd=ROOT):
    r=subprocess.run([str(x) for x in argv],cwd=cwd,capture_output=True,timeout=timeout,creationflags=0x08000000)
    C.check(r.returncode==0,'Control command failed; exit='+str(r.returncode)+' executable='+str(argv[0]))
    C.check(not C.SECRET.search(r.stdout+r.stderr),'Credential-like output withheld')
    return r.stdout

def publish(paths,message):
    from workflow_publication import commit
    head=commit(paths,message);C.command(ROOT,['git','fetch','origin','main'])
    checks={}
    for rel in paths:
        raw=command(['git','show','origin/main:'+rel]);sha=hashlib.sha256(raw).hexdigest()
        C.check(sha==C.digest(ROOT/rel),'Published byte readback differs: '+rel);checks[rel]=sha
    return {'utc':C.now(),'status':'REMOTE_MAIN_BYTES_VERIFIED','commit':head,'file_sha256':checks}

def held_lock_matches_negative(lock):
    current=lock_identity(lock);expected=C.load(NEGATIVE)['exclusive_writer_boundary']
    C.check(current==expected,'Stable-C lock file identity differs from certified boundary; no retry')
    return current

def live_scheduler_binding(config_path,runtime):
    """Live COM definition/instance proves origin; saved start JSON is insufficient."""
    import stage04_windows_job_v10 as J10
    import xml.etree.ElementTree as ET
    request=C.load(Path(runtime)/'task_request.json');started=C.load(Path(runtime)/'task_start.json')
    config=C.load(config_path)
    C.check(C.digest(config_path)==request['config_sha256'] and str(Path(config_path))==request['config'] and
      config['runtime']==str(runtime)==request['runtime'] and config['task_name']==request['task_name'],
      'Actual loaded config/runtime/request identity differs')
    shell=c.WinDLL('shell32',use_last_error=True)
    parse=J.bind(shell,'CommandLineToArgvW',c.POINTER(t.LPWSTR),[t.LPCWSTR,c.POINTER(c.c_int)])
    getcmd=J.bind(K,'GetCommandLineW',t.LPWSTR,[]);free=J.bind(K,'LocalFree',t.HANDLE,[t.HANDLE])
    argc=c.c_int();args=parse(getcmd(),c.byref(argc));J.ok(args,'Actual process command line parse')
    try:actual_argv=[args[i] for i in range(argc.value)]
    finally:free(c.cast(args,t.HANDLE))
    C.check(actual_argv==[request['executable'],*request['argv']],'Actual direct action argv differs from requested Scheduler action')
    C.check(C.digest(request['executable'])==request['executable_sha256'],'Actual controller interpreter bytes differ')
    script="$ErrorActionPreference='Stop'; $s=New-Object -ComObject Schedule.Service; $s.Connect(); $t=$s.GetFolder('\\').GetTask('"+request['task_name']+"'); $d=$t.Definition; $runs=@($s.GetRunningTasks(1) | Where-Object {$_.Name -eq '"+request['task_name']+"'} | ForEach-Object {[pscustomobject]@{engine_pid=$_.EnginePID;instance_guid=$_.InstanceGuid;state=$_.State}}); [pscustomobject]@{xml=$t.Xml;user_id=$d.Principal.UserId;logon_type=$d.Principal.LogonType;run_level=$d.Principal.RunLevel;triggers=$d.Triggers.Count;restarts=$d.Settings.RestartCount;time_limit=$d.Settings.ExecutionTimeLimit;multiple_instances=$d.Settings.MultipleInstances;exe=$d.Actions.Item(1).Path;arguments=$d.Actions.Item(1).Arguments;cwd=$d.Actions.Item(1).WorkingDirectory;runs=$runs} | ConvertTo-Json -Depth 6 -Compress"
    directory=Path(runtime)/'live_scheduler_query'
    result=J10.run_job([r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe','-NoProfile','-NonInteractive','-Command',script],ROOT,
      directory,cap_bytes=256*1024**2,deadline_seconds=20,role='BOUNDED_LIVE_SCHEDULER_IDENTITY_QUERY')
    C.check(result['exit_code']==0,'Live Scheduler identity query failed')
    actual=json.loads((directory/'stdout.txt').read_text(encoding='utf-8-sig'))
    ns={'t':'http://schemas.microsoft.com/windows/2004/02/mit/task'}
    sid=ET.fromstring(actual['xml']).find('t:Principals/t:Principal/t:UserId',ns).text
    C.check(hashlib.sha256(b'\xff\xfe'+actual['xml'].encode('utf-16le')).hexdigest()==request['definition_sha256'] and
      sid==request['sid'] and actual['exe']==request['executable'] and actual['arguments']==request['arguments'] and actual['cwd']==request['cwd'] and
      actual['logon_type']==3 and actual['run_level']==0 and actual['triggers']==actual['restarts']==0 and
      actual['time_limit']=='PT0S' and actual['multiple_instances']==2,'Actual live principal/action/settings differ')
    matches=[r for r in actual['runs'] if r['engine_pid']==os.getpid() and r['instance_guid']==started['instance_guid']]
    C.check(len(matches)==1 and started['engine_pid']==os.getpid(),'Actual live Scheduler instance does not own this controller')
    return {'utc':C.now(),'actual_process_argv':actual_argv,'actual_task_definition_sha256':request['definition_sha256'],
      'actual_sid':sid,'live_instance':matches[0],'query_real_exit_sha256':C.digest(directory/'exit.json'),'config_sha256':C.digest(config_path)}

def scope_binding(name):
    C.check(name in NAMES,'Unknown production scope')
    old=C.load(OLD/'inference_freeze.json');prefix='data:.work/stage04_phylogeny_v2/analyses/'+name+'/'
    expected={k:v for k,v in old['source_identity']['file_sha256'].items() if k.startswith(prefix)}
    C.check(prefix+'concatenated.faa' in expected and prefix+'partitions.nex' in expected,'Missing original accepted scope input hashes')
    for key,sha in expected.items():C.check(C.digest(ROOT/key.split(':',1)[1])==sha,'Accepted per-scope input changed: '+key)
    tool=old['tool_identity'];exe=Path(old['executable']);dll=exe.parent/'libiomp5md.dll'
    C.check(C.digest(exe)==tool['executable_sha256'] and C.digest(dll)==tool['openmp_dll_sha256'],'Original official IQTREE executable/DLL changed')
    return {'scope':name,'original_freeze_sha256':FREEZE_SHA,'accepted_input_sha256':expected,
      'actual_iqtree_executable_sha256':C.digest(exe),'actual_runtime_dll_sha256':C.digest(dll)}
