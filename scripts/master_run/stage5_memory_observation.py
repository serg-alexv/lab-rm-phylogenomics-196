"""Read-only memory evidence. No WSL launcher, cache reclamation or job control.

Windows: --windows-only writes a new C snapshot (no original lock or G access).
Linux: --linux-readonly --nonce <32hex> prints one bounded observation; root
must invoke it through a reviewed retained-client owner under original lock.
Default does nothing. Counters are observations, not causal attribution.
"""
from pathlib import Path
import argparse
import ctypes as c
from ctypes import wintypes as w
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import signal
import time
import uuid

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
LINUX_WORK=Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
API_SHA='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'


def need(ok,message):
    if not ok:raise ValueError(message)


def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def utc():return dt.datetime.now(dt.timezone.utc).isoformat()


def read_small(path,limit=2*1024**2):
    with Path(path).open('rb') as f:raw=f.read(limit+1)
    need(len(raw)<=limit,'Diagnostic pseudo-file size limit')
    return raw.decode('utf-8')


def memory_kib(raw):
    result={}
    for line in raw.splitlines():
        match=re.fullmatch(r'([A-Za-z_()]+):\s+(\d+) kB',line)
        if match:result[match[1]]=int(match[2])*1024
    return result


def linux_observation(nonce):
    need(os.name=='posix' and Path(__file__).resolve().parent==LINUX_WORK
         and re.fullmatch('[a-f0-9]{32}',nonce or ''),'Exact mounted C diagnostic source/nonce required')
    prior=signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Read-only Linux observation deadline')))
    signal.alarm(10)
    start=time.monotonic()
    try:
        before=read_small('/proc/meminfo');processes=[];errors=[]
        for path in sorted(Path('/proc').iterdir(),key=lambda p:p.name):
            if not path.name.isdigit():continue
            need(len(processes)+len(errors)<4096 and time.monotonic()-start<8,'Finite process-observation bound')
            try:
                raw=read_small(path/'stat',16384);end=raw.rfind(')');fields=raw[end+2:].split()
                status=read_small(path/'status',65536);values=memory_kib(status)
                rows=[x for x in status.splitlines() if x.startswith('Uid:')]
                # No cmdline, environment, open-file names, or payload bytes.
                processes.append({'pid':int(path.name),'comm':raw[raw.index('(')+1:end],
                    'ppid':int(fields[1]),'start_ticks':fields[19], 'state':fields[0],
                    'uid_record':rows[0] if rows else None,
                    'memory_bytes':{k:values[k] for k in ('VmRSS','RssAnon','RssFile','RssShmem','VmSwap') if k in values}})
            except (FileNotFoundError,ProcessLookupError):errors.append({'pid':int(path.name),'state':'VANISHED_DURING_OBSERVATION'})
            except PermissionError:errors.append({'pid':int(path.name),'state':'UNREADABLE'})
        cgroup={}
        for name in ('memory.current','memory.peak','memory.stat','memory.events','memory.swap.current'):
            path=Path('/sys/fs/cgroup')/name
            if path.is_file():
                try:cgroup[name]=read_small(path,65536)
                except (FileNotFoundError,PermissionError) as e:cgroup[name]={'error':type(e).__name__}
        after=read_small('/proc/meminfo')
        return {'schema':'STAGE05_READ_ONLY_LINUX_MEMORY_OBSERVATION_V1','state':'OBSERVATION_ONLY_NO_RECLAMATION',
            'nonce':nonce,'utc':utc(),'source_sha256':digest(__file__),
            'boot_id':read_small('/proc/sys/kernel/random/boot_id',128).strip(),
            'self_pid':os.getpid(),'self_mount_namespace':os.readlink('/proc/self/ns/mnt'),
            'meminfo_before_raw':before,'meminfo_after_raw':after,
            'meminfo_before_bytes':memory_kib(before),'meminfo_after_bytes':memory_kib(after),
            'processes':processes,'process_observation_races':errors,'cgroup_memory':cgroup,
            'interpretation':'Cached/SReclaimable/Dirty/Writeback/Shmem are guest counters; they do not alone establish host commit attribution. Process RSS may share pages.',
            'cache_reclamation_calls':0,'native_children_launched':0,'runtime_payload_bytes_read':0}
    finally:signal.alarm(0);signal.signal(signal.SIGALRM,prior)


def windows_observation():
    need(os.name=='nt' and Path(__file__).resolve().parent==WORK,'Exact C Windows diagnostic source required')
    module=WORK/'atomic_iqtree_windows.py';need(digest(module)==API_SHA,'Pinned Windows observation API differs')
    spec=importlib.util.spec_from_file_location('memory_observation_pinned_api',module)
    A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    api=A.Win();before=api.resources([WORK])
    enum=api.P.EnumProcesses;enum.argtypes=[c.POINTER(w.DWORD),w.DWORD,c.POINTER(w.DWORD)];enum.restype=w.BOOL
    open_process=api.K.OpenProcess;open_process.argtypes=[w.DWORD,w.BOOL,w.DWORD];open_process.restype=w.HANDLE
    pids=(w.DWORD*8192)();used=w.DWORD()
    api.ok(enum(pids,c.sizeof(pids),c.byref(used)),'Bounded Windows process enumeration')
    need(used.value<c.sizeof(pids) and used.value%4==0,'Incomplete Windows process inventory')
    rows=[];unknown=[];start=time.monotonic()
    for pid in pids[:used.value//4]:
        need(time.monotonic()-start<10,'Finite read-only Windows inventory deadline')
        if pid==0:continue
        handle=open_process(0x1000|0x100000,False,pid)
        if not handle:unknown.append({'pid':pid,'stage':'OPEN','winerror':c.get_last_error()});continue
        try:
            values=[w.FILETIME() for _ in range(4)]
            api.ok(api.times(handle,*(c.byref(x) for x in values)),'Retained process birth')
            name=c.create_unicode_buffer(32768);size=w.DWORD(len(name))
            api.ok(api.image(handle,0,name,c.byref(size)),'Read process image basename')
            waited=api.wait(handle,0)
            row={'pid':pid,'creation_filetime':api.ft(values[0]),'image_basename':Path(name.value).name,
                 'retained_wait_result':waited,
                 'exited_at_observation':True if waited==0 else False if waited==258 else None}
            memory=api.MEMORY();memory.cb=c.sizeof(memory)
            if api.mem(handle,c.byref(memory),c.sizeof(memory)):
                row.update(working_set_bytes=memory.WorkingSetSize,private_commit_bytes=memory.PrivateUsage,
                           pagefile_usage_bytes=memory.PagefileUsage,memory_query_state='ACTUAL_COUNTERS')
            else:
                row.update(working_set_bytes=None,private_commit_bytes=None,pagefile_usage_bytes=None,
                           memory_query_state='UNAVAILABLE',memory_query_winerror=c.get_last_error())
            rows.append(row)
        except OSError as e:unknown.append({'pid':pid,'stage':'QUERY','winerror':e.winerror})
        finally:api.close(handle)
    after=api.resources([WORK]);rows.sort(key=lambda x:x['private_commit_bytes'] or 0,reverse=True)
    return {'schema':'STAGE05_READ_ONLY_WINDOWS_MEMORY_OBSERVATION_V1','state':'OBSERVATION_ONLY_NO_RECLAMATION',
        'utc':utc(),'source_sha256':digest(__file__),'before':before,'after':after,
        'processes':rows,'unreadable_processes':unknown,'known_process_private_commit_sum_bytes':sum(x['private_commit_bytes'] or 0 for x in rows),
        'known_process_working_set_sum_bytes':sum(x['working_set_bytes'] or 0 for x in rows),
        'vm_named_processes':[x for x in rows if any(t in x['image_basename'].lower() for t in ('vmmem','vmwp','wsl'))],
        'interpretation':'Per-process private commit is incomplete when processes are unreadable and is not equal to global commit; working sets may share pages. This single snapshot cannot attribute prior changes.',
        'G_accesses':0,'WSL_launches':0,'signals':0,'cache_reclamation_calls':0}


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group()
    g.add_argument('--windows-only',action='store_true');g.add_argument('--linux-readonly',action='store_true');p.add_argument('--nonce')
    args=p.parse_args()
    if args.linux_readonly:print(json.dumps(linux_observation(args.nonce),sort_keys=True));return
    if not args.windows_only:print(json.dumps({'state':'PREPARED_NOT_RUN','WSL_launches':0,'cache_reclamation_calls':0}));return
    value=windows_observation()
    out=WORK/('stage5_windows_memory_observation_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json')
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({'path':str(out),'sha256':digest(out),'state':value['state'],
        'physical_available_bytes':value['after']['physical_available_bytes'],'commit_headroom_bytes':value['after']['commit_headroom_bytes'],
        'readable_processes':len(value['processes']),'unreadable_processes':len(value['unreadable_processes'])}))


if __name__=='__main__':main()
