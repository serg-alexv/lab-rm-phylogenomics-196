"""V9 owned JobObject runner: mandatory C launch/exit, observational outbox only.

Uses unchanged, hash-pinned V6 ctypes declarations. G/Git never occurs in this
module. Ordinary receipts are emitted only after actual native exit and empty
queried job accounting. A deadline, when supplied, is for control fixtures and
publisher/checker jobs; biological IQ-TREE has no wall deadline.
"""
import ctypes as c
from ctypes import wintypes as t
import msvcrt, os, subprocess, time, traceback
from pathlib import Path
import stage04_controller as C
import stage04_windows_job_v6 as J
import stage04_recovery_support_v9 as S

terminate_job=J.bind(J.K,'TerminateJobObject',t.BOOL,[t.HANDLE,t.UINT])

def job_state(job):
    peak=J.EXTENDED();account=J.ACCOUNTING();pids=J.PIDS()
    J.ok(J.query_job(job,9,c.byref(peak),c.sizeof(peak),None),'Query job memory')
    J.ok(J.query_job(job,1,c.byref(account),c.sizeof(account),None),'Query job accounting')
    J.ok(J.query_job(job,3,c.byref(pids),c.sizeof(pids),None),'Query exact job PID list')
    C.check(pids.assigned==pids.listed and pids.listed<=64,'Job PID list incomplete')
    return {'peak_process_committed_bytes':peak.PeakProcessMemoryUsed,'peak_job_committed_bytes':peak.PeakJobMemoryUsed,
      'job_cpu_seconds':(account.TotalUserTime+account.TotalKernelTime)/1e7,'job_active_processes':account.ActiveProcesses,
      'job_total_processes':account.TotalProcesses,'actual_job_process_ids':list(pids.ids[:pids.listed])}

def best_effort(path,value):
    try:C.atomic(path,value);return True
    except (OSError,ValueError):return False

def run_job(argv,cwd,directory,cap_bytes=3221225472,affinity_mask=5,offer=None,deadline_seconds=None,role='IQTREE_NATIVE'):
    S.pins();directory=Path(directory)
    C.check(directory.is_relative_to(S.RUNTIME) and 0<cap_bytes<=3221225472 and affinity_mask==5,'C mandatory spool/cap/mask contract violated')
    C.check(deadline_seconds is None or role!='IQTREE_NATIVE','No scientific wall deadline allowed')
    directory.mkdir(parents=True,exist_ok=False)
    allowed,system=J.SIZE(),J.SIZE();J.ok(J.affinity(J.current(),c.byref(allowed),c.byref(system)),'Allowed process affinity')
    C.check(allowed.value&affinity_mask==affinity_mask,'Mask5 unavailable to controller')
    job=J.create_job(None,None);J.ok(job,'Create owned job')
    controls=J.EXTENDED();controls.BasicLimitInformation.LimitFlags=0x2310;controls.BasicLimitInformation.Affinity=affinity_mask
    controls.ProcessMemoryLimit=controls.JobMemoryLimit=cap_bytes
    process=J.PROCESS();resumed=False;closed=False;start=time.monotonic();launch=None;last=None;observational_errors=0
    try:
        J.ok(J.set_job(job,9,c.byref(controls),c.sizeof(controls)),'Set owned job controls')
        queried=J.EXTENDED();J.ok(J.query_job(job,9,c.byref(queried),c.sizeof(queried),None),'Query controls before launch')
        C.check(queried.BasicLimitInformation.LimitFlags==0x2310 and queried.ProcessMemoryLimit==queried.JobMemoryLimit==cap_bytes and
          queried.BasicLimitInformation.Affinity==5,'Queried controls differ')
        with open(os.devnull,'rb') as null,(directory/'stdout.txt').open('wb') as out,(directory/'stderr.txt').open('wb') as err:
            handles=[msvcrt.get_osfhandle(s.fileno()) for s in (null,out,err)]
            try:
                for h in handles:os.set_handle_inheritable(h,True)
                si=J.STARTUP();si.cb=c.sizeof(si);si.dwFlags=0x100;si.hStdInput,si.hStdOutput,si.hStdError=handles
                cmd=c.create_unicode_buffer(subprocess.list2cmdline([str(x) for x in argv]))
                J.ok(J.create_process(str(argv[0]),cmd,None,None,True,0x4|0x08000000,None,str(cwd),c.byref(si),c.byref(process)),'Create owned suspended child')
            finally:
                for h in handles:os.set_handle_inheritable(h,False)
            J.ok(J.assign_job(job,process.hProcess),'Assign suspended child before resume')
            actual= S.handle_identity(process.hProcess,process.dwProcessId)
            cpu,sysmask=J.SIZE(),J.SIZE();J.ok(J.affinity(process.hProcess,c.byref(cpu),c.byref(sysmask)),'Query actual suspended child affinity')
            bound=t.BOOL();J.ok(S.in_job(process.hProcess,job,c.byref(bound)),'Query child in actual owned job')
            C.check(cpu.value==5 and bound.value,'Suspended assignment/affinity differs')
            controller=S.process_identity(os.getpid())
            launch={'utc':C.now(),'runner_pid':os.getpid(),'runner_creation_filetime':controller['creation_filetime'],
              'child_pid':process.dwProcessId,'child_creation_filetime':actual['creation_filetime'],'argv':[str(x) for x in argv],
              'cwd':str(cwd),'actual_executable_sha256':C.digest(argv[0]),'actual_executable':actual['executable'],
              'job_bound_before_resume':True,'actual_child_in_owned_job':True,'actual_suspended_child_affinity_mask':cpu.value,
              'memory_kind':'WINDOWS_COMMITTED_MEMORY_NOT_LINUX_RLIMIT_AS','process_committed_memory_cap_bytes':cap_bytes,
              'aggregate_job_committed_memory_cap_bytes':cap_bytes,'affinity_mask':5,'allowed_logical_processors':2,
              'job_limit_flags':0x2310,'kill_child_job_on_owner_handle_close':True,'spool_role':'historical:C_STABLE_RUNTIME',
              'role':role,'wall_deadline_seconds':deadline_seconds,'ordinary_receipt_protocol':'V9_ACTUAL_EXIT_AND_QUERIED_EMPTY_JOB'}
            C.atomic(directory/'launch.json',launch)
            C.check(J.resume_thread(process.hThread)==1,'Resume exactly once required');resumed=True
            J.close(process.hThread);process.hThread=None;next_report=0
            while True:
                state=J.wait(process.hProcess,500);C.check(state in (0,258),'Native wait failed')
                if deadline_seconds is not None and state!=0 and time.monotonic()-start>deadline_seconds:
                    raise TimeoutError('Owned '+role+' exceeded bounded deadline')
                if time.monotonic()>=next_report or state==0:
                    mem=J.MEMORY();mem.cb=c.sizeof(mem);J.ok(J.memory(process.hProcess,c.byref(mem),c.sizeof(mem)),'Actual native memory')
                    actual=S.handle_identity(process.hProcess,process.dwProcessId,launch['actual_executable'])
                    last={**job_state(job),'utc':C.now(),'child_pid':process.dwProcessId,'creation_filetime':actual['creation_filetime'],
                      'wall_seconds':time.monotonic()-start,'cpu_seconds':actual['cpu_seconds'],'working_set_bytes':mem.WorkingSetSize,
                      'peak_working_set_bytes':mem.PeakWorkingSetSize,'private_committed_bytes':mem.PrivateUsage,
                      'process_exited':state==0,'actual_exit_code':actual['actual_exit_code'],'exit_filetime':actual['exit_filetime']}
                    if not best_effort(directory/'progress.json',last):observational_errors+=1
                    # Queue.offer is bounded/nonblocking. All exceptions from optional reporting are swallowed here.
                    if offer:
                        try:offer(dict(last))
                        except Exception:observational_errors+=1
                    next_report=time.monotonic()+2 if role=='SYNTHETIC_FIXTURE' else time.monotonic()+30
                if state==0:break
            actual=S.handle_identity(process.hProcess,process.dwProcessId,launch['actual_executable']);final=job_state(job);deadline=time.monotonic()+10
            while (final['job_active_processes'] or final['actual_job_process_ids']) and time.monotonic()<deadline:
                time.sleep(.1);final=job_state(job)
            C.check(final['job_active_processes']==0 and final['actual_job_process_ids']==[],'Actual job descendants still live; ordinary closure rejected')
            closed=True
            receipt={**launch,**last,**final,'wall_seconds':time.monotonic()-start,'process_exited':True,
              'exit_code':actual['actual_exit_code'],'exit_filetime':actual['exit_filetime'],'observational_errors':observational_errors,
              'actual_launch_receipt_sha256':C.digest(directory/'launch.json'),'receipt_kind':'ORDINARY_ACTUAL_NATIVE_EXIT_AND_EMPTY_OWNED_JOB'}
            C.atomic(directory/'exit.json',receipt);return receipt
    except BaseException as error:
        exception={'utc':C.now(),'kind':type(error).__name__,'message':str(error),'role':role,'launch_present':launch is not None,
          'ordinary_exit_emitted':False,'last_actual_job_state':last,'native_disposition':'OWNED_JOB_TERMINATION_ON_CONTROL_FAILURE' if process.hProcess else 'NO_NATIVE_PROCESS_CREATED'}
        best_effort(directory/'exception.json',exception)
        if process.hProcess and not closed:
            # Only this function's owned job/process; never unrelated processes.
            terminate_job(job,125);J.terminate(process.hProcess,125);J.wait(process.hProcess,10000)
            try:
                actual=S.handle_identity(process.hProcess,process.dwProcessId);account=job_state(job)
                best_effort(directory/'exception_exit_observation.json',{'utc':C.now(),'process':actual,'job':account,
                  'receipt_kind':'EXCEPTION_PATH_ACTUAL_OBSERVATION_NOT_ORDINARY_SUCCESS'})
            except Exception:pass
        raise
    finally:
        if process.hThread:J.close(process.hThread)
        if process.hProcess:J.close(process.hProcess)
        J.close(job)
