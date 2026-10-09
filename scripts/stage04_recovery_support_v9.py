"""Fixed-role Win32 identities for the separately reviewed V9 recovery protocol."""
from pathlib import Path
import ctypes as c
from ctypes import wintypes as t
import hashlib, json, msvcrt, os, subprocess, sys, time
import stage04_controller as C
import stage04_windows_job_v6 as J

ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
RUNTIME=HISTORY/'.work/stage04_recovery_v9'
LOCK=HISTORY/'.work/workflow.lock'
REPORT=ROOT/'reports/stage04/recovery_v9'
OLD=ROOT/'.work/stage04_inference_windows_v6'
OUT=ROOT/'.work/stage04_inference_windows_v9'
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

def handle_identity(h,pid):
    created,ended,kernel,user=(t.FILETIME() for _ in range(4))
    J.ok(J.times(h,*[c.byref(x) for x in (created,ended,kernel,user)]),'GetProcessTimes identity')
    buffer=c.create_unicode_buffer(32768);size=t.DWORD(len(buffer))
    J.ok(image_name(h,0,buffer,c.byref(size)),'QueryFullProcessImageNameW')
    wait=J.wait(h,0);C.check(wait in (0,258),'Process identity wait failed')
    code=t.DWORD();J.ok(J.exit_code(h,c.byref(code)),'Actual process exit code')
    return {'pid':int(pid),'creation_filetime':J.filetime(created),'exit_filetime':J.filetime(ended),
      'executable':buffer.value,'state':'EXITED' if wait==0 else 'RUNNING',
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

def isolation():
    identity=process_identity(os.getpid());flag=t.BOOL()
    J.ok(in_job(J.current(),None,c.byref(flag)),'IsProcessInJob(controller,NULL)')
    rows=process_table();chain=[];p=rows[os.getpid()]['parent_pid'];visited=set()
    while p and p in rows:
        C.check(p not in visited,'Cyclic ancestor snapshot');visited.add(p)
        row=rows[p];chain.append(row);p=row['parent_pid']
    C.check(not any('codex' in r['basename'].lower() for r in chain),'CodexCLI ancestor rejected')
    C.check(not flag.value,'Controller inherited an outer JobObject; explicit review required, no breakaway')
    return {'utc':C.now(),'controller':identity,'is_process_in_job_null':bool(flag.value),'ancestors':chain,
      'codex_cli_ancestor':False,'silent_breakaway':False}

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
