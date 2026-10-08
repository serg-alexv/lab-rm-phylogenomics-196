"""Create a suspended Windows child, bind committed-memory/affinity job, then run.

Windows job committed-memory limits are distinct from Linux address-space limits.
No pre-existing process is assigned, changed or terminated by this module.
"""
from pathlib import Path
import ctypes as c
from ctypes import wintypes as t
import msvcrt, os, subprocess, time
import stage04_controller as C

SIZE=c.c_size_t
class IO(c.Structure):
    _fields_=[(n,c.c_uint64) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
class BASIC(c.Structure):
    _fields_=[('PerProcessUserTimeLimit',c.c_int64),('PerJobUserTimeLimit',c.c_int64),('LimitFlags',t.DWORD),('MinimumWorkingSetSize',SIZE),('MaximumWorkingSetSize',SIZE),('ActiveProcessLimit',t.DWORD),('Affinity',SIZE),('PriorityClass',t.DWORD),('SchedulingClass',t.DWORD)]
class EXTENDED(c.Structure):
    _fields_=[('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',SIZE),('JobMemoryLimit',SIZE),('PeakProcessMemoryUsed',SIZE),('PeakJobMemoryUsed',SIZE)]
class STARTUP(c.Structure):
    _fields_=[('cb',t.DWORD),('lpReserved',t.LPWSTR),('lpDesktop',t.LPWSTR),('lpTitle',t.LPWSTR),('dwX',t.DWORD),('dwY',t.DWORD),('dwXSize',t.DWORD),('dwYSize',t.DWORD),('dwXCountChars',t.DWORD),('dwYCountChars',t.DWORD),('dwFillAttribute',t.DWORD),('dwFlags',t.DWORD),('wShowWindow',t.WORD),('cbReserved2',t.WORD),('lpReserved2',c.POINTER(c.c_byte)),('hStdInput',t.HANDLE),('hStdOutput',t.HANDLE),('hStdError',t.HANDLE)]
class PROCESS(c.Structure):
    _fields_=[('hProcess',t.HANDLE),('hThread',t.HANDLE),('dwProcessId',t.DWORD),('dwThreadId',t.DWORD)]
class MEMORY(c.Structure):
    _fields_=[('cb',t.DWORD),('PageFaultCount',t.DWORD)]+[(n,SIZE) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
class ACCOUNTING(c.Structure):
    _fields_=[(n,c.c_int64) for n in ('TotalUserTime','TotalKernelTime','ThisPeriodTotalUserTime','ThisPeriodTotalKernelTime')]+[(n,t.DWORD) for n in ('TotalPageFaultCount','TotalProcesses','ActiveProcesses','TotalTerminatedProcesses')]
class PIDS(c.Structure):
    _fields_=[('assigned',t.DWORD),('listed',t.DWORD),('ids',SIZE*64)]

K=c.WinDLL('kernel32',use_last_error=True)
P=c.WinDLL('psapi',use_last_error=True)
def bind(lib,name,restype,args):
    f=getattr(lib,name);f.restype=restype;f.argtypes=args;return f
create_job=bind(K,'CreateJobObjectW',t.HANDLE,[c.c_void_p,t.LPCWSTR])
set_job=bind(K,'SetInformationJobObject',t.BOOL,[t.HANDLE,c.c_int,c.c_void_p,t.DWORD])
query_job=bind(K,'QueryInformationJobObject',t.BOOL,[t.HANDLE,c.c_int,c.c_void_p,t.DWORD,c.c_void_p])
create_process=bind(K,'CreateProcessW',t.BOOL,[t.LPCWSTR,t.LPWSTR,c.c_void_p,c.c_void_p,t.BOOL,t.DWORD,c.c_void_p,t.LPCWSTR,c.POINTER(STARTUP),c.POINTER(PROCESS)])
assign_job=bind(K,'AssignProcessToJobObject',t.BOOL,[t.HANDLE,t.HANDLE])
resume_thread=bind(K,'ResumeThread',t.DWORD,[t.HANDLE])
wait=bind(K,'WaitForSingleObject',t.DWORD,[t.HANDLE,t.DWORD])
exit_code=bind(K,'GetExitCodeProcess',t.BOOL,[t.HANDLE,c.POINTER(t.DWORD)])
times=bind(K,'GetProcessTimes',t.BOOL,[t.HANDLE,c.POINTER(t.FILETIME),c.POINTER(t.FILETIME),c.POINTER(t.FILETIME),c.POINTER(t.FILETIME)])
affinity=bind(K,'GetProcessAffinityMask',t.BOOL,[t.HANDLE,c.POINTER(SIZE),c.POINTER(SIZE)])
current=bind(K,'GetCurrentProcess',t.HANDLE,[])
close=bind(K,'CloseHandle',t.BOOL,[t.HANDLE])
terminate=bind(K,'TerminateProcess',t.BOOL,[t.HANDLE,t.UINT])
memory=bind(P,'GetProcessMemoryInfo',t.BOOL,[t.HANDLE,c.POINTER(MEMORY),t.DWORD])

def ok(value,call):
    if not value:raise c.WinError(c.get_last_error(),call)

def filetime(value):return (value.dwHighDateTime<<32)|value.dwLowDateTime

def run_job(argv,cwd,directory,cap_bytes,threads=2,on_progress=None):
    C.check(os.name=='nt' and threads==2 and 0<cap_bytes<=3221225472,'Explicit Windows bounded child required')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    allowed,system=SIZE(),SIZE();ok(affinity(current(),c.byref(allowed),c.byref(system)),'GetProcessAffinityMask')
    bits=[1<<i for i in range(8*c.sizeof(SIZE)) if allowed.value&(1<<i)]
    C.check(len(bits)>=threads,'Insufficient actual CPU affinity')
    mask=sum(bits[:threads]);job=create_job(None,None);ok(job,'CreateJobObjectW')
    info=EXTENDED();info.BasicLimitInformation.LimitFlags=0x2000|0x100|0x200|0x10
    info.BasicLimitInformation.Affinity=mask;info.ProcessMemoryLimit=cap_bytes;info.JobMemoryLimit=cap_bytes
    process=PROCESS();resumed=False;start=time.monotonic()
    try:
        ok(set_job(job,9,c.byref(info),c.sizeof(info)),'SetInformationJobObject')
        verified=EXTENDED();ok(query_job(job,9,c.byref(verified),c.sizeof(verified),None),'QueryInformationJobObject')
        C.check(verified.BasicLimitInformation.LimitFlags==info.BasicLimitInformation.LimitFlags and verified.JobMemoryLimit==verified.ProcessMemoryLimit==cap_bytes and verified.BasicLimitInformation.Affinity==mask,'Actual Windows job controls differ')
        with open(os.devnull,'rb') as null, (directory/'stdout.txt').open('wb') as out, (directory/'stderr.txt').open('wb') as err:
            handles=[msvcrt.get_osfhandle(s.fileno()) for s in (null,out,err)]
            for h in handles:os.set_handle_inheritable(h,True)
            si=STARTUP();si.cb=c.sizeof(si);si.dwFlags=0x100;si.hStdInput,si.hStdOutput,si.hStdError=handles
            cmd=c.create_unicode_buffer(subprocess.list2cmdline([str(x) for x in argv]))
            ok(create_process(str(argv[0]),cmd,None,None,True,0x4|0x08000000,None,str(cwd),c.byref(si),c.byref(process)),'CreateProcessW suspended')
            for h in handles:os.set_handle_inheritable(h,False)
            try:ok(assign_job(job,process.hProcess),'AssignProcessToJobObject before resume')
            except BaseException:
                terminate(process.hProcess,125);raise
            created,ended,kernel,user=(t.FILETIME() for _ in range(4));ok(times(process.hProcess,c.byref(created),c.byref(ended),c.byref(kernel),c.byref(user)),'GetProcessTimes')
            launch={'utc':C.now(),'runner_pid':os.getpid(),'child_pid':process.dwProcessId,'child_creation_filetime':filetime(created),'argv':[str(x) for x in argv],
                    'actual_executable_sha256':C.digest(argv[0]),'job_bound_before_resume':True,'memory_kind':'WINDOWS_COMMITTED_MEMORY_NOT_LINUX_RLIMIT_AS',
                    'process_committed_memory_cap_bytes':cap_bytes,'aggregate_job_committed_memory_cap_bytes':cap_bytes,'affinity_mask':mask,'allowed_logical_processors':threads,
                    'job_limit_flags':verified.BasicLimitInformation.LimitFlags,'kill_child_job_on_owner_handle_close':True}
            C.atomic(directory/'launch.json',launch)
            C.check(resume_thread(process.hThread)==1,'Suspended child thread was not resumed exactly once');resumed=True
            close(process.hThread);process.hThread=None
            next_report=0
            while True:
                state=wait(process.hProcess,1000);C.check(state in (0,258),'WaitForSingleObject failed')
                if time.monotonic()>=next_report or state==0:
                    mem=MEMORY();mem.cb=c.sizeof(mem);ok(memory(process.hProcess,c.byref(mem),c.sizeof(mem)),'GetProcessMemoryInfo')
                    ok(times(process.hProcess,c.byref(created),c.byref(ended),c.byref(kernel),c.byref(user)),'GetProcessTimes')
                    peak=EXTENDED();account=ACCOUNTING();pids=PIDS()
                    ok(query_job(job,9,c.byref(peak),c.sizeof(peak),None),'Query actual job memory')
                    ok(query_job(job,1,c.byref(account),c.sizeof(account),None),'Query actual job accounting')
                    ok(query_job(job,3,c.byref(pids),c.sizeof(pids),None),'Query actual job process IDs')
                    row={'utc':C.now(),'child_pid':process.dwProcessId,'creation_filetime':filetime(created),'wall_seconds':time.monotonic()-start,
                         'cpu_seconds':(filetime(kernel)+filetime(user))/1e7,'working_set_bytes':mem.WorkingSetSize,'peak_working_set_bytes':mem.PeakWorkingSetSize,
                         'private_committed_bytes':mem.PrivateUsage,'peak_process_committed_bytes':peak.PeakProcessMemoryUsed,'peak_job_committed_bytes':peak.PeakJobMemoryUsed,
                         'job_cpu_seconds':(account.TotalUserTime+account.TotalKernelTime)/1e7,'job_active_processes':account.ActiveProcesses,'job_total_processes':account.TotalProcesses,
                         'actual_job_process_ids':list(pids.ids[:pids.listed]),'process_exited':state==0}
                    C.atomic(directory/'progress.json',row)
                    if on_progress:on_progress(row)
                    next_report=time.monotonic()+30
                if state==0:break
            code=t.DWORD();ok(exit_code(process.hProcess,c.byref(code)),'GetExitCodeProcess')
            # The process handle can signal before the job accounting count is
            # decremented. Re-query actual counts for a bounded interval; never
            # substitute an assumed zero or terminate a remaining descendant.
            deadline=time.monotonic()+5
            while account.ActiveProcesses and time.monotonic()<deadline:
                time.sleep(.1)
                ok(query_job(job,1,c.byref(account),c.sizeof(account),None),'Query final job accounting')
                ok(query_job(job,3,c.byref(pids),c.sizeof(pids),None),'Query final job process IDs')
            C.check(account.ActiveProcesses==0 and pids.listed==0,'Job descendants remain live after native exit; preserve evidence')
            row.update(job_active_processes=account.ActiveProcesses,actual_job_process_ids=list(pids.ids[:pids.listed]),
                       job_cpu_seconds=(account.TotalUserTime+account.TotalKernelTime)/1e7,wall_seconds=time.monotonic()-start)
            receipt={**launch,**row,'exit_code':code.value,'exit_filetime':filetime(ended),'actual_launch_receipt_sha256':C.digest(directory/'launch.json')}
            C.atomic(directory/'exit.json',receipt)
            return receipt
    finally:
        if process.hThread:close(process.hThread)
        if process.hProcess:
            if not resumed:terminate(process.hProcess,125)
            close(process.hProcess)
        close(job)
