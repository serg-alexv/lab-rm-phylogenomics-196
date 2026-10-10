"""Contingent Chrome-only Windows resource cleanup; default NO_OP.

No WSL, shell, process-tree kill, argv, URL, profile, service or Git operation.
Only the root owner may opt in after reviewed source and exact closed evidence.
"""
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
import re
import stat
import time
import uuid
import atomic_iqtree_windows as A

WORK=Path(__file__).resolve().parent
EXACT_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
API_SHA='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
CHROME_EXE=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
LOCK={'path':r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock',
      'volume_serial':2430728143,'file_index':844424932784519,
      'creation_filetime':134359335921635133,'locked_byte':0}
STOP=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
SCOPE='NONSCIENTIFIC_CURRENT_SESSION_EXACT_CHROME_RETAINED_HANDLE_CLEANUP_ONLY'
MAX_PROCESSES=4096
MAX_TARGETS=128
DEADLINE_SECONDS=180
WAIT_MILLISECONDS=5000
TERMINATION_EXIT_CODE=1223
RETAINED=[]  # Only checked CloseHandle removes an entry; failure remains visible.


def need(value,message):
    if not value:raise ValueError(message)


def positive_int(value):return type(value) is int and value>0


def lock_guard(value):
    need(isinstance(value,dict) and set(value)==set(LOCK) and all(
        type(value[k]) is type(v) and value[k]==v for k,v in LOCK.items()),'Original immutable WorkflowLock required')


def target_guard(value,session):
    """Exact executable and current owner session; never a name/PID heuristic."""
    need(isinstance(value,dict) and type(session) is int and session>=0
         and positive_int(value.get('pid')) and positive_int(value.get('creation_filetime'))
         and type(value.get('session_id')) is int and value['session_id']==session
         and isinstance(value.get('executable'),str)
         and value['executable'].casefold()==CHROME_EXE.casefold(),
         'Only exact Program Files Chrome in current owner SessionID is allowed')
    need(value.get('exited') is False or value.get('exited') is True,'Actual process state required')
    return value


def terminal_guard(birth,current,session):
    target_guard(birth,session);target_guard(current,session)
    need(all(type(current.get(k)) is type(birth[k]) and current[k]==birth[k]
             for k in ('pid','creation_filetime','session_id'))
         and current['executable'].casefold()==birth['executable'].casefold()
         and current['exited'] is True and type(current.get('exit_code')) is int
         and positive_int(current.get('exit_filetime'))
         and current['exit_filetime']>birth['creation_filetime'],
         'Positive exact retained-handle terminal birth/exit required')
    return current


def same_birth(birth,current,session):
    target_guard(birth,session);target_guard(current,session)
    need(all(type(current.get(k)) is type(birth[k]) and current[k]==birth[k]
             for k in ('pid','creation_filetime','session_id')),
         'Retained Chrome handle birth/session changed')


def prior_closed_guard(result,unlock):
    """Pinned root-supplied actual owner evidence; failure is not success."""
    need(isinstance(result,dict) and result.get('owned_closure_proven') is True
         and result.get('unknown_closure_stop_preserved') is False
         and isinstance(result.get('state'),str)
         and (result['state']=='FAILED' or result['state'].startswith('PASS_')),
         'Each supplied prior owner must have actual closed scope and no STOP')
    need(isinstance(unlock,dict) and unlock.get('state')=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'
         and unlock.get('released') is True,'Every prior owner needs explicit original byte unlock')
    if 'original_lock_explicitly_released' in result:
        need(result['original_lock_explicitly_released'] is True,'Prior original lock release unproven')


def bounded_pids(values,byte_count,capacity=MAX_PROCESSES):
    need(type(capacity) is int and 0<capacity<=MAX_PROCESSES
         and type(byte_count) is int and 0<=byte_count<capacity*ctypes.sizeof(w.DWORD)
         and byte_count%ctypes.sizeof(w.DWORD)==0,'Process enumeration truncated/invalid; preserve')
    result=list(values)[:byte_count//ctypes.sizeof(w.DWORD)]
    need(all(type(pid) is int and 0<=pid<=0xffffffff for pid in result)
         and len(result)==len(set(result)),'Actual PID enumeration membership differs')
    return sorted(pid for pid in result if pid)


def exact_control(path,pin,limit=2*1024**2):
    path=Path(path)
    need(path.is_absolute() and WORK in path.parents and path.resolve()==path
         and re.fullmatch('[a-f0-9]{64}',pin or ''),'Exact C control path and pin required')
    for node in (path,*path.parents):
        info=node.lstat();need(not node.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400,
                               'Plain C evidence ancestry required')
    info=path.stat();need(stat.S_ISREG(info.st_mode) and info.st_size<=limit,'Bounded actual owner evidence required')
    raw=path.read_bytes();need(len(raw)<=limit and hashlib.sha256(raw).hexdigest()==pin
                             and A.sha256(path)==pin,'Owner evidence changed')
    return json.loads(raw)


def close_owned(api,item):
    need(item in RETAINED,'Only an owned retained handle may close')
    api.ok(api.close(item['handle']),'Checked CloseHandle for owned cleanup handle')
    RETAINED.remove(item)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true');parser.add_argument('--source-sha256')
    parser.add_argument('--output',type=Path)
    for name in ('prior-result','prior-result-sha256','prior-unlock','prior-unlock-sha256'):
        parser.add_argument('--'+name,action='append',default=[])
    args=parser.parse_args()
    if not args.run:
        print(json.dumps({'state':'NO_OP_CONTINGENT_EXACT_CHROME_ONLY_CLEANUP','allowlist':[CHROME_EXE],
                          'actual_process_effects':'NOT_RUN','wsl':'NOT_RUN','git_mutation':'NOT_RUN'}));return 0
    need(os.name=='nt' and WORK==EXACT_WORK and re.fullmatch('[a-f0-9]{64}',args.source_sha256 or '')
         and A.sha256(__file__)==args.source_sha256 and A.sha256(WORK/'atomic_iqtree_windows.py')==API_SHA,
         'Explicit reviewed exact Windows cleanup/API source required')
    need(args.output and args.output.parent==WORK and args.output.is_absolute()
         and args.output.resolve()==args.output and not args.output.exists()
         and re.fullmatch('stage5_chrome_cleanup_[A-Za-z0-9_]+',args.output.name),'Fresh direct-C cleanup spool required')
    count=len(args.prior_result)
    need(0<count<=16 and all(len(getattr(args,name))==count
         for name in ('prior_result_sha256','prior_unlock','prior_unlock_sha256')),
         'Exact paired prior closed-owner result/unlock pins required')
    prior=[]
    for result_path,result_sha,unlock_path,unlock_sha in zip(args.prior_result,args.prior_result_sha256,args.prior_unlock,args.prior_unlock_sha256):
        value=exact_control(result_path,result_sha);unlock=exact_control(unlock_path,unlock_sha)
        prior_closed_guard(value,unlock)
        prior.append({'result_path':result_path,'result_sha256':result_sha,'unlock_path':unlock_path,'unlock_sha256':unlock_sha,
                      'prior_state_preserved':value['state']})
    out=args.output;out.mkdir();api=A.Win();owner=api.identity(api.current(),os.getpid());nonce=uuid.uuid4().hex
    started=time.monotonic();source_sha=args.source_sha256;stop_sha=None;complete=False;effects=[];skipped={}
    record={'schema':'STAGE05_EXACT_CHROME_RESOURCE_CLEANUP_WINDOWS_V1','scope':SCOPE,'state':'FAILED',
            'source_sha256':source_sha,'api_source_sha256':API_SHA,'actual_owner':owner,'owner_nonce':nonce,
            'allowlist':[CHROME_EXE],'target_session_id':owner['session_id'],'prior_closed_owner_evidence':prior,
            'process_payload_or_argv_read':False,'graceful_window_close_attempted':False,
            'graceful_skip_reason':'HWND ownership cannot be atomically retained through window reuse; use exact retained process handles',
            'maximum_enumeration':MAX_PROCESSES,'maximum_targets':MAX_TARGETS,'deadline_seconds':DEADLINE_SECONDS,
            'snapshot_targets_only':True,'process_tree_or_name_kill':False,'effects':effects,
            'scientific_adoption_authorized':False,'wsl':'NOT_RUN','services':'NOT_RUN','git_mutation':'NOT_RUN'}
    lock=A.WorkflowLock(api);lock_entered=False;handles_closed=False
    try:
        lock.__enter__();lock_entered=True
        def check():
            need(time.monotonic()-started<DEADLINE_SECONDS,'Finite Chrome cleanup deadline expired')
            lock_guard(lock.identity)
            need(A.sha256(__file__)==source_sha and A.sha256(WORK/'atomic_iqtree_windows.py')==API_SHA,'Cleanup/API source drift')
            control=A.read_json(ROOT/'status/run_control.json')
            need(control['state']=='ACTIVE_DIRECT_USER_CONTINUATION' and control['automatic_resume'] is False,
                 'Current direct project continuation authority required')
            current=api.identity(api.current(),os.getpid())
            need(current['pid']==owner['pid'] and current['creation_filetime']==owner['creation_filetime']
                 and current['session_id']==owner['session_id'],'Exact retained cleanup owner changed')
            resources=api.resources([WORK])
            need(resources['physical_available_bytes']>=256*1024**2 and resources['commit_headroom_bytes']>=256*1024**2,
                 'Windows cleanup256MiB metadata reserve insufficient')
            record['latest_actual_resources']=resources
            for item in prior:
                need(A.sha256(item['result_path'])==item['result_sha256']
                     and A.sha256(item['unlock_path'])==item['unlock_sha256'],'Prior closed owner evidence drift')
            if stop_sha is not None:need(A.sha256(STOP)==stop_sha and A.read_json(STOP)['owner_nonce']==nonce,'Own cleanup STOP changed')
        def acquire(pid,access):
            handle=api.K.OpenProcess(access,False,pid)
            if not handle:return None
            item={'handle':handle,'pid':pid,'effect_started':False,'terminal_verified':False}
            RETAINED.append(item);return item
        def actual_identity(item):
            birth=item.get('birth')
            return api.identity(item['handle'],item['pid'],
                retained_image=birth['executable'] if birth else None,
                retained_session=birth['session_id'] if birth else None)
        def wait_terminal(item):
            remaining=max(0,int((DEADLINE_SECONDS-(time.monotonic()-started))*1000))
            need(remaining>0,'Cleanup terminal wait budget expired')
            need(api.wait(item['handle'],min(WAIT_MILLISECONDS,remaining))==0,'Exact retained Chrome process terminal wait expired')
            terminal=terminal_guard(item['birth'],actual_identity(item),owner['session_id'])
            item['terminal_verified']=True;item['terminal']=terminal;return terminal
        try:
            need(not STOP.exists(),'Existing unproven closure STOP must be reconciled first');check()
            record['windows_before']=api.resources([WORK]);record['workflow_lock']=lock.identity
            A.atomic(out/'intent.json',dict(record,state='PRE_ENUMERATION_INTENT_NO_PROCESS_EFFECT'))
            # A checked metadata-handle closure failure also leaves a durable STOP.
            A.atomic(STOP,{'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1','owner_nonce':nonce,'utc':A.utc(),
                          'evidence':str(out),'reason':'Chrome cleanup handle intent; exact effects and owned handles must close',
                          'automatic_resume':False});stop_sha=A.sha256(STOP)
            opened=api.K.OpenProcess;opened.restype=w.HANDLE;opened.argtypes=[w.DWORD,w.BOOL,w.DWORD]
            enum=api.K.K32EnumProcesses;enum.restype=w.BOOL
            enum.argtypes=[ctypes.POINTER(w.DWORD),w.DWORD,ctypes.POINTER(w.DWORD)]
            buffer=(w.DWORD*MAX_PROCESSES)();used=w.DWORD()
            api.ok(enum(buffer,ctypes.sizeof(buffer),ctypes.byref(used)),'Bounded K32EnumProcesses')
            pids=bounded_pids(buffer,used.value);record['enumerated_pid_count']=len(pids);targets=[]
            for pid in pids:
                check();item=acquire(pid,0x1000|0x100000)
                if item is None:
                    code=ctypes.get_last_error();skipped[str(code)]=skipped.get(str(code),0)+1;continue
                try:
                    try:birth=actual_identity(item)
                    except (OSError,ValueError):
                        skipped['QUERY_UNAVAILABLE']=skipped.get('QUERY_UNAVAILABLE',0)+1;continue
                    if birth['executable'].casefold()!=CHROME_EXE.casefold() or birth['session_id']!=owner['session_id']:continue
                    target_guard(birth,owner['session_id'])
                    if birth['exited'] is True:continue
                    target=acquire(pid,0x1000|0x100000|0x1)
                    need(target is not None,'Exact Chrome terminate-capable retained handle unavailable')
                    target['birth']=dict(birth)
                    current=actual_identity(target);same_birth(birth,current,owner['session_id'])
                    targets.append(target)
                    need(len(targets)<=MAX_TARGETS,'Finite Chrome target bound exceeded')
                finally:close_owned(api,item)
            record.update(target_count=len(targets),skipped_metadata_counts=skipped)
            A.atomic(out/'target_snapshot.json',{'scope':SCOPE,'owner_nonce':nonce,'targets':[t['birth'] for t in targets],
                                               'no_argv_urls_profiles_read':True})
            A.atomic(out/'result.json',record)
            for index,item in enumerate(targets,1):
                check();current=actual_identity(item);same_birth(item['birth'],current,owner['session_id'])
                effect={'ordinal':index,'birth':item['birth'],'state':'INTENT_BEFORE_EFFECT',
                        'effect':'TERMINATE_RETAINED_CHROME_HANDLE_ONLY','requested_exit_code':TERMINATION_EXIT_CODE,
                        'owner_nonce':nonce,'source_sha256':source_sha}
                path=out/f'effect_{index:04d}.intent.json';A.atomic(path,effect)
                record['current_effect_intent_sha256']=A.sha256(path);A.atomic(out/'result.json',record)
                if current['exited'] is True:
                    terminal=terminal_guard(item['birth'],current,owner['session_id']);item['terminal_verified']=True
                    effect.update(state='NO_EFFECT_ALREADY_CLOSED',actual_terminate_process_called=False,terminal=terminal)
                else:
                    # Mark before the API; a crash/exception cannot erase an
                    # attempted effect or release its handle without terminal proof.
                    item['effect_started']=True
                    api.ok(api.terminate(item['handle'],TERMINATION_EXIT_CODE),'Terminate exact retained Chrome handle')
                    terminal=wait_terminal(item)
                    need(terminal['exit_code']==TERMINATION_EXIT_CODE,'Retained forced-termination exit code differs')
                    effect.update(state='TERMINATED_EXACT_HANDLE_AND_TERMINAL_VERIFIED',actual_terminate_process_called=True,terminal=terminal)
                close_owned(api,item);effect['actual_checked_close_handle_succeeded']=True
                effects.append(effect);A.atomic(out/f'effect_{index:04d}.result.json',effect);A.atomic(out/'result.json',record)
            check();need(not RETAINED,'All owned cleanup handles must be checked closed')
            record['windows_after']=api.resources([WORK]);complete=True
            record['state']='EFFECTS_CLOSED_PENDING_EXPLICIT_UNLOCK'
        except BaseException as error:record['error_kind']=type(error).__name__
        finally:
            finalizer=[]
            for item in list(RETAINED):
                try:
                    if item['effect_started'] and not item['terminal_verified']:
                        terminal=wait_terminal(item)
                        finalizer.append({'pid':item['pid'],'actual_retained_terminal':terminal})
                    close_owned(api,item)
                except BaseException as error:finalizer.append({'pid':item['pid'],'error_kind':type(error).__name__})
            handles_closed=not RETAINED
            record.update(owned_closure_proven=complete and handles_closed,
                          unknown_closure_stop_preserved=STOP.exists(),retained_handles_unresolved=len(RETAINED),
                          finalizer_evidence=finalizer,elapsed_seconds=time.monotonic()-started,utc=A.utc())
            A.atomic(out/'result.json',record)
    except BaseException as error:record.update(state='FAILED',owner_error_kind=type(error).__name__)
    finally:
        if lock_entered:
            try:lock.__exit__(None,None,None)
            except BaseException as error:record.update(state='FAILED',unlock_error_kind=type(error).__name__)
        record['original_lock_explicitly_released']=lock.released
        if lock.released:
            A.atomic(out/'lock_released.json',{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True,'utc':A.utc()})
        if complete and handles_closed and lock.released and stop_sha is not None:
            try:
                need(A.sha256(STOP)==stop_sha and A.read_json(STOP)['owner_nonce']==nonce,'Own cleanup STOP changed')
                STOP.unlink();record['state']='PASS_EXACT_CHROME_SNAPSHOT_EFFECTS_AND_HANDLES_CLOSED'
            except BaseException as error:record.update(state='FAILED',stop_clear_error_kind=type(error).__name__)
        elif record['state']=='EFFECTS_CLOSED_PENDING_EXPLICIT_UNLOCK':record['state']='FAILED'
        record.update(owned_closure_proven=complete and handles_closed and lock.released,
                      unknown_closure_stop_preserved=STOP.exists(),utc=A.utc())
        A.atomic(out/'result.json',record)
    print(json.dumps({'state':record['state'],'result':str(out/'result.json')}))
    return 0 if record['state']=='PASS_EXACT_CHROME_SNAPSHOT_EFFECTS_AND_HANDLES_CLOSED' and lock.released else 2


if __name__=='__main__':raise SystemExit(main())
