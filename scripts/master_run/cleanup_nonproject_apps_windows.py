"""Exact Chrome/Media Player retained-handle forced termination; default dry-run.

Project Win32 query/resource primitives retain their original source notices in
atomic_iqtree_windows.py. No HWND messages, taskkill, services or PID signalling.
Only --run acts, against the exact separately captured nine-process manifest.
"""
from __future__ import annotations
import argparse, ctypes as c, datetime as dt, hashlib, importlib.util, json, os
from ctypes import wintypes as w
from pathlib import Path
import stat, time

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
API_SHA='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
CHROME=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
MEDIA=r'C:\Program Files\WindowsApps\Microsoft.ZuneMusic_11.2607.16.0_x64__8wekyb3d8bbwe\Microsoft.Media.Player.exe'
# Exact read-only CIM observations; capture converts their microsecond dates to
# exact retained Windows FILETIME births, never discovers additional processes.
OBSERVED=[(14764,CHROME,'2026-10-09T21:14:35.721461+03:00'),
 (24252,CHROME,'2026-10-09T21:14:35.909834+03:00'),
 (7152,CHROME,'2026-10-09T21:14:36.215972+03:00'),
 (5760,CHROME,'2026-10-09T21:14:36.224940+03:00'),
 (13040,CHROME,'2026-10-09T21:14:36.264174+03:00'),
 (26248,CHROME,'2026-10-09T21:14:38.045246+03:00'),
 (20928,CHROME,'2026-10-09T21:14:38.567589+03:00'),
 (2320,CHROME,'2026-10-09T21:14:40.130057+03:00'),
 (25800,MEDIA,'2026-10-09T22:42:03.979480+03:00')]
SCHEMA='MASTER_EXACT_NONPROJECT_APP_CLEANUP_V1'

def need(ok,message):
    if not ok:raise ValueError(message)

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def local(path,fresh=False):
    p=Path(path)
    need(p.is_absolute() and p.parent==WORK and p.name not in ('','.','..'),'Exact direct C work file required')
    for parent in [WORK,*WORK.parents]:
        s=parent.lstat();need(stat.S_ISDIR(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Plain C ancestry required')
    if fresh:need(not os.path.lexists(p),'Fresh output only')
    elif os.path.lexists(p):
        s=p.lstat();need(stat.S_ISREG(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Plain C input required')
    return p

def write(path,value,create=False):
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    if create:
        with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    else:
        temp=path.with_name(path.name+'.owned.tmp')
        try:
            with temp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            os.replace(temp,path)
        finally:
            if temp.exists():temp.unlink()

def cim_microseconds(text):
    delta=dt.datetime.fromisoformat(text).astimezone(dt.timezone.utc)-dt.datetime(1601,1,1,tzinfo=dt.timezone.utc)
    return (delta.days*86400+delta.seconds)*1_000_000+delta.microseconds

def check_identity(actual,expected):
    for key in ('pid','creation_filetime','executable','session_id'):
        need(actual[key]==expected[key],'Retained process '+key+' changed; preserve')

def validate_plan(value,source_sha):
    need(value['schema']==SCHEMA and value['source_sha256']==source_sha and value['api_sha256']==API_SHA,'Pinned source/manifest differs')
    rows=value['processes'];need(type(rows) is list and len(rows)==len(OBSERVED)==9,'Exact nine original processes required')
    expected={pid:(exe,date) for pid,exe,date in OBSERVED}
    need(len({r['pid'] for r in rows})==9 and {r['pid'] for r in rows}==set(expected),'Original PID set differs')
    need(set(value['executables'])=={CHROME,MEDIA},'Exact two executable files required')
    for row in rows:
        exe,date=expected[row['pid']]
        need(row['executable']==exe and type(row['creation_filetime']) is int
             and row['creation_filetime']//10==cim_microseconds(date) and row['exited'] is False
             and type(row['session_id']) is int,'Original observed birth/image differs')
    return rows

class Native:
    def __init__(self):
        need(os.name=='nt','Windows only')
        base=WORK/'atomic_iqtree_windows.py';need(digest(base)==API_SHA,'Reviewed query API bytes differ')
        spec=importlib.util.spec_from_file_location('exact_app_cleanup_api',base)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.api=module.Win();self.K=self.api.K
        def bind(name,result,args):
            fn=getattr(self.K,name);fn.restype=result;fn.argtypes=args;return fn
        self.open=bind('OpenProcess',w.HANDLE,[w.DWORD,w.BOOL,w.DWORD])
        self.create_file=bind('CreateFileW',w.HANDLE,[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE])
        self.read_file=bind('ReadFile',w.BOOL,[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p])
        self.info_ex=bind('GetFileInformationByHandleEx',w.BOOL,[w.HANDLE,c.c_int,c.c_void_p,w.DWORD])
        class FileId(c.Structure):_fields_=[('volume',c.c_uint64),('identifier',c.c_ubyte*16)]
        self.FileId=FileId
    def process(self,pid,run=False):
        handle=self.open(0x1000|0x100000|(1 if run else 0),False,pid)
        self.api.ok(handle,'OpenProcess exact target');return handle
    def identity(self,handle,row):
        return self.api.identity(handle,row['pid'],row['executable'],row.get('session_id'))
    def memory(self,handle):
        data=self.api.MEMORY();data.cb=c.sizeof(data)
        self.api.ok(self.api.mem(handle,c.byref(data),data.cb),'Target memory query')
        return {'private_bytes':int(data.PrivateUsage),'working_set_bytes':int(data.WorkingSetSize)}
    def file_record(self,handle):
        data=self.api.FILEINFO();self.api.ok(self.api.file_info(handle,c.byref(data)),'Exe file identity')
        fid=self.FileId();self.api.ok(self.info_ex(handle,18,c.byref(fid),c.sizeof(fid)),'Exe FILE_ID_INFO')
        need(not data.attributes&0x400 and not data.attributes&0x10,'Plain executable required')
        return {'volume_serial64':str(fid.volume),'file_id128':bytes(fid.identifier).hex(),
            'bytes':(data.sizeHigh<<32)|data.sizeLow,'creation_filetime':self.api.ft(data.created),
            'mtime_filetime':self.api.ft(data.written)}
    def executable(self,path):
        for p in [Path(path).parent,*Path(path).parent.parents]:
            s=p.lstat();need(not getattr(s,'st_file_attributes',0)&0x400,'Executable ancestry alias; preserve')
        # READ share only retains identity against replacement, deletion and writes.
        handle=self.create_file(path,0x80000000,1,None,3,0x00200000,None)
        need(handle not in (None,c.c_void_p(-1).value),'Cannot retain executable READ handle')
        try:
            before=self.file_record(handle);need(before['bytes']<=64*1024**2,'Executable size bound exceeded')
            h=hashlib.sha256();buf=c.create_string_buffer(1024**2);total=0;deadline=time.monotonic()+15
            while True:
                need(time.monotonic()<deadline,'Executable hash deadline')
                count=w.DWORD();self.api.ok(self.read_file(handle,buf,len(buf),c.byref(count),None),'Read executable bytes')
                if not count.value:break
                total+=count.value;need(total<=before['bytes'],'Executable grew');h.update(buf.raw[:count.value])
            need(total==before['bytes'] and self.file_record(handle)==before,'Executable changed while reading')
            return handle,dict(before,sha256=h.hexdigest())
        except BaseException:self.api.close(handle);raise
    def terminate(self,handle):self.api.ok(self.api.terminate(handle,0xE0000001),'Exact retained app TerminateProcess')
    def wait(self,handle,ms):return self.api.wait(handle,ms)
    def close(self,handle):self.api.ok(self.api.close(handle),'Retained handle CloseHandle')
    def resources(self):return self.api.resources([WORK])

def capture(native,source_sha):
    processes=[];files={};handles=[]
    try:
        for pid,exe,date in OBSERVED:
            row={'pid':pid,'executable':exe};h=native.process(pid);handles.append(h)
            actual=native.identity(h,row)
            need(actual['exited'] is False and actual['executable']==exe and actual['creation_filetime']//10==cim_microseconds(date),'CIM target changed before capture')
            if exe not in files:
                fh,files[exe]=native.executable(exe);handles.append(fh)
            actual['memory']=native.memory(h);processes.append(actual)
        plan={'schema':SCHEMA,'source_sha256':source_sha,'api_sha256':API_SHA,'processes':processes,
            'executables':files,'capture_resources':native.resources(),'action':'FORCED_RETAINED_HANDLE_TERMINATION_ONLY',
            'scope':'EXACT_ORIGINAL9_ONLY_NO_DESCENDANT_ADOPTION','actual_termination':False}
        validate_plan(plan,source_sha);return plan
    finally:
        for h in reversed(handles):native.close(h)

def execute(native,plan,receipt,persist,clock=time.monotonic):
    handles=[];files=[];start=clock();receipt.update(state='FAILED_PRESERVED',targets=[],before=native.resources())
    try:
        for exe,expected in plan['executables'].items():
            h,actual=native.executable(exe);files.append(h);need(actual==expected,'Pinned executable bytes/identity differ')
        # Open and prove every exact target before any termination. A missing or
        # reused PID aborts the whole preflight; a newly spawned process is ignored.
        for row in plan['processes']:
            h=native.process(row['pid'],run=True);handles.append((h,row));actual=native.identity(h,row);check_identity(actual,row)
            need(actual['exited'] is False,'Original target already exited; capture a new reviewed plan')
        receipt['state']='EXACT_HANDLES_RETAINED_ACTION_PENDING';persist(receipt)
        # Browser parent last, so explicit child receipts do not depend on it.
        for h,row in sorted(handles,key=lambda item:item[1]['pid']==14764):
            need(clock()-start<25,'Cleanup action deadline reached; preserve remaining')
            actual=native.identity(h,row);check_identity(actual,row)
            record={'original':row,'before':actual,'termination_requested':False};receipt['targets'].append(record)
            persist(receipt)
            if not actual['exited']:
                native.terminate(h);record['termination_requested']=True;persist(receipt)
                state=native.wait(h,5000);need(state==0,'Exact retained target closure unproven after5s')
            terminal=native.identity(h,row);check_identity(terminal,row)
            need(terminal['exited'] is True and terminal['exit_filetime']>=terminal['creation_filetime'],'Exact target terminal not proven')
            record['terminal']=terminal;record['closure_proven']=True;persist(receipt)
        receipt['state']='PASS_EXACT_CAPTURED9_RETAINED_HANDLES_CLOSED'
    except BaseException as error:
        receipt.update(state='FAILED_PRESERVED',error={'kind':type(error).__name__,'message':str(error)})
    finally:
        receipt['after']=native.resources();receipt['elapsed_seconds']=clock()-start
        receipt['host_commit_headroom_delta_bytes']=receipt['after']['commit_headroom_bytes']-receipt['before']['commit_headroom_bytes']
        receipt['host_physical_available_delta_bytes']=receipt['after']['physical_available_bytes']-receipt['before']['physical_available_bytes']
        receipt['delta_attribution']='CONCURRENT_HOST_MEASUREMENT_NOT_EXCLUSIVE_APP_ATTRIBUTION'
        for h,_ in reversed(handles):native.close(h)
        for h in reversed(files):native.close(h)
        persist(receipt)
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-plan',type=Path);parser.add_argument('--plan',type=Path)
    parser.add_argument('--plan-sha256');parser.add_argument('--run',action='store_true');parser.add_argument('--receipt',type=Path)
    args=parser.parse_args();source_sha=digest(__file__)
    need(Path(__file__).resolve().parent==WORK,'Fixed C work source required')
    if args.capture_plan:
        need(not args.run and not args.plan and not args.receipt,'Capture is read-only and separate from action')
        path=local(args.capture_plan,True);value=capture(Native(),source_sha);write(path,value,True)
        print(json.dumps({'state':'CAPTURED_READ_ONLY_NO_TERMINATION','path':str(path),'sha256':digest(path),'targets':9}));return 0
    if not args.run:
        print(json.dumps({'state':'DRY_RUN_NO_ACTION','targets':9,'exact_executables':[CHROME,MEDIA]}));return 0
    need(args.plan and args.plan_sha256 and args.receipt,'Run requires pinned plan and fresh receipt')
    path=local(args.plan);need(path.stat().st_size<65536 and digest(path)==args.plan_sha256,'Exact captured plan bytes differ')
    plan=json.loads(path.read_bytes());validate_plan(plan,source_sha)
    receipt_path=local(args.receipt,True)
    receipt={'schema':'MASTER_EXACT_APP_CLEANUP_RECEIPT_V1','state':'STARTED','source_sha256':source_sha,
        'api_sha256':API_SHA,'plan_sha256':args.plan_sha256,'action':'FORCED_TERMINATION','no_pid_signalling':True,
        'no_descendant_adoption':True,'scientific_state_change':False}
    write(receipt_path,receipt,True)
    result=execute(Native(),plan,receipt,lambda value:write(receipt_path,value))
    print(json.dumps({'state':result['state'],'receipt':str(receipt_path)}))
    return 0 if result['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
