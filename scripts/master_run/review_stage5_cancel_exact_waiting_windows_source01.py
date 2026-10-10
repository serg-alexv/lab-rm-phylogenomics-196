"""C-only retained cancellation-client source peer; no operational effects."""
from pathlib import Path
import ast, datetime, hashlib, json, subprocess, sys
import review_stage5_postboot_gate as R
import stage5_cancel_exact_waiting_windows as V
import stage5_cancel_exact_waiting_bootstrap as C
W=Path(__file__).resolve().parent
PINS={'stage5_cancel_exact_waiting_windows.py':'42eb45458bbb6eee23262b548d2c6c04e695597e949790bf61f79dacfbfc328c',
      'test_stage5_cancel_exact_waiting_windows.py':'6ecca26d2eeb2d375c14dc18f6f7c23f5f9cf957c98cdef82a450fb0c3e33f74',
      'stage5_cancel_exact_waiting_windows_before_posix_argv_fix.py':'9c6d786f49a4908f6abc333e2fd3bc72154e1ab855a2425c0b7dbbe0ecc7eb97',
      'stage5_cancel_exact_waiting_linux_source_independent_review01.json':'17b6a8f39cf8c628e007b094186115b0b4bd943779208bf8196eb1ccfe995431'}
def main():
    out=W/'stage5_cancel_exact_waiting_windows_source_independent_review01.json';R.require(not out.exists(),'Preserve cancellation-client peer')
    value={'schema':'STAGE05_EXACT_WAITING_CANCEL_WINDOWS_SOURCE_PEER_V1','state':'FAILED_SOURCE_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only complete frozen Windows source/pin/AST/reverse-delta review,5 pure fake-owner/default-NOOP/Windows-POSIX-argv tests and separate NOOP. No actual Win API/process handles, G/UNC/WSL/lock/signals/network/Git.',
           'actual_cancellation_or_WSL_client':'NOT_RUN','original_science_owner_closure_or_unlock_proven':False,'second_workflow_lock':False}
    try:
        for name,pin in {**PINS,**V.PINS,**C.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen cancellation-client source/control differs: '+name)
        raw=R.data(W/'stage5_cancel_exact_waiting_windows.py');old=R.data(W/'stage5_cancel_exact_waiting_windows_before_posix_argv_fix.py')
        R.require(raw.replace(b"C.WORK.as_posix()+'/stage5_cancel_exact_waiting_bootstrap.py'",b"str(C.WORK/'stage5_cancel_exact_waiting_bootstrap.py')")==old,'Wrapper correction differs beyond fixed POSIX argv expression')
        tree=ast.parse(raw);original=ast.parse(R.data(W/'stage5_unc_bind_probe.py'))
        local=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='wsl_control_job')
        before=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='windows_job')
        source=raw.decode();fragment='\n'.join(source.splitlines()[local.lineno-1:local.end_lineno])
        R.require(fragment.count('WSL')==3 and ast.dump(ast.parse(fragment.replace('def wsl_control_job(','def windows_job(').replace('WSL','sys.executable')).body[0],include_attributes=False)==ast.dump(before,include_attributes=False),'Local WSL Job differs beyond exact name/three image expressions')
        attrs=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        R.require(not set(attrs)&{'WorkflowLock','kill','killpg','Popen','run','system'},'Wrapper acquires another lock or adds uncontrolled process route')
        R.require(not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='executable' for t in n.targets) for n in ast.walk(tree)), 'Wrapper changes global executable')
        posix=C.WORK.as_posix()+'/stage5_cancel_exact_waiting_bootstrap.py'
        R.require(posix=='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_cancel_exact_waiting_bootstrap.py' and '\\' not in posix,'Windows-constructed Linux script argv differs')
        checks=[]
        for name,count in [('test_stage5_cancel_exact_waiting_windows.py',5),('stage5_cancel_exact_waiting_windows.py',0)]:
            p=subprocess.run([sys.executable,'-B',str(W/name)],cwd=W,capture_output=True,text=True,timeout=30)
            R.require(p.returncode==0,'Pure cancellation-client check failed: '+p.stderr[-2500:])
            if count:R.require('Ran 5 tests' in p.stderr,'Focused cancellation-client count differs')
            else:R.require(json.loads(p.stdout)['state']=='PREPARED_NOT_RUN' and json.loads(p.stdout)['WSL_clients_created']==0,'Default cancellation-client NOOP differs')
            checks.append({'name':name,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        for name,pin in {**PINS,**V.PINS,**C.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen cancellation-client bytes drifted')
        value.update(state='PASS_RETAINED_EXACT_CANCEL_WINDOWS_CONTROL_CLIENT_SOURCE_ONLY',frozen_sources=PINS,checks=checks,Windows_constructed_Linux_script_argument=posix,exact_original_U0664_job_reverse_AST=True,global_sys_executable_mutation=False,rejected_wrapper9c6d={'source_sha256':PINS['stage5_cancel_exact_waiting_windows_before_posix_argv_fix.py'],'state':'PRESERVED_BLOCKED_SOURCE_NOT_ACTUAL_FAILURE','blocker':'Imported Linux module Path is WindowsPath under this wrapper. str(C.WORK/script) emits backslashes, so the Linux interpreter receives an invalid script path. Only as_posix expression changed; exact Windows-built argv regression added.'},reviewed_contracts=['Same original U0664 suspended named Job, active-process1/kill-on-close, exact retained WSL root birth/exit,20s wait and unchanged5s full-Job drain/checked handle closes; only fixed application/image expressions differ from proven Windows worker','Original science owner retains its original workflow lock. Wrapper uses query-only OpenProcess0x101000 handle to exact PID24488/birth134360766940521715/exe/session and rechecks literal direct authority, STOP absent, source/config/launch pins and fresh exact owner lease','Only new WSL control client can be terminated by local copied Job finalizer; original Windows science owner/client are never signaled','Current resource512MiB physical/commit plus bounded16MiB disk required; exact current source/WSL binary SHA and owner proof rechecked before durable intent','Linux7b02 fixed helper handles the sole verified-pidfd SIGTERM request; Windows final PASS requires successful exact helper receipt and closed retained control Job, and still claims no original owner closure or unlock','No second lock, no global interpreter patch, no UNC repair, no new detector/source/config/native science launch','Unknown control-client closure, signal uncertainty, failed result or handle close requires master reconciliation; do not start a new science owner merely because a control request was sent'],required_actual_joins=['Root publishes exact paired source/peer packet and verifies remote bytes','If original waiting owner naturally expires first, skip cancellation and preserve source-only history','Independently inspect actual fixed helper target/intent/pidfd signal result and retained control client/root Job closure','Separately require original runner FAILED_RETRYABLE or DEFERRED_RESOURCE with actual no-native/owned closure, original retained science WSL terminal and original explicit byte unlock before config02 build/run'])
    except BaseException as error:value['error']={'kind':type(error).__name__,'message':str(error)}
    value['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'error':value.get('error'),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
    return 0 if value['state'].startswith('PASS_') else 1
if __name__=='__main__':raise SystemExit(main())
