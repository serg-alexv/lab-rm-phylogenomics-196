"""One literal authorized Windows restart request; default no-op, no retries."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
import atomic_iqtree_windows as A
import register_master_boot_resume_once as R

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true');args=p.parse_args()
    if not args.run:print(json.dumps({'state':'PREPARED_NOT_REQUESTED'}));return
    assert os.name=='nt' and os.environ.get('COMPUTERNAME','').upper()=='WD'
    assert Path(__file__).resolve().parent==R.W
    assert sha(R.W/'atomic_iqtree_windows.py')==R.PINS['atomic_iqtree_windows.py']
    assert sha(R.W/'register_master_boot_resume_once.py')=='92996842ac877a9056c8f6ea0946e623d9da2a9ac826a77a0abe16b829740a2c'
    readback=json.loads((R.W/'master_registration31_remote_readback.json').read_bytes())
    assert readback['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and readback['expected_commit']=='3378b87998d826fff86db3407591ab7d4d774f74'
    manifest=json.loads((R.PRIVATE/'PRIVATE_HANDOFF_DO_NOT_PUBLISH.json').read_bytes())
    assert manifest['thread_id']==os.environ['CODEX_THREAD_ID']
    assert not (R.PRIVATE/'CONSUMED_SINGLE_USE.json').exists() and sha(R.STOP)==R.STOP_SHA
    for name,pin in R.PINS.items():assert sha(R.W/name)==pin
    with R.winreg.OpenKey(R.winreg.HKEY_CURRENT_USER,R.KEY,0,R.winreg.KEY_QUERY_VALUE) as key:
        value,kind=R.winreg.QueryValueEx(key,R.NAME);assert value==R.COMMAND and kind==R.winreg.REG_SZ
    out=R.W/'master_controlled_restart_request_actual01.json';assert not out.exists()
    command=[r'C:\Windows\System32\shutdown.exe','/r','/t','180','/d','p:4:1','/c',
        'LAB_RM authorized master-run scope reconciliation; same-user sign-in resumes the one-time master continuation.']
    api=A.Win();owner=api.identity(api.current(),os.getpid())
    record={'schema':'MASTER_CONTROLLED_WINDOWS_RESTART_REQUEST_V1','state':'REQUEST_RESULT_UNPROVEN',
        'source_sha256':sha(Path(__file__)),'argv':command,'requested_delay_seconds':180,
        'owner':owner,'utc':A.utc(),'baseline':manifest['baseline'],
        'published_handoff_commit':'3378b87998d826fff86db3407591ab7d4d774f74',
        'STOP_sha256_preserved':R.STOP_SHA,'one_time_registry_value_readback_exact':True,
        'actual_new_boot_or_resumed_session_proven':False,'scientific_authority':False}
    child=None
    try:
        child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
        birth=api.identity(int(child._handle),child.pid,command[0],owner['session_id']);record['request_process_birth']=birth
        stdout,stderr=child.communicate(timeout=10)
        final=api.identity(int(child._handle),child.pid,command[0],owner['session_id']);record['request_process_exit']=final
        record.update(stdout=stdout.decode('utf-8','replace'),stderr=stderr.decode('utf-8','replace'))
        assert final['creation_filetime']==birth['creation_filetime'] and final['exited']
        assert final['exit_code']==0 and final['exit_filetime']>final['creation_filetime']
        assert sha(R.STOP)==R.STOP_SHA
        record.update(state='WINDOWS_RESTART_REQUEST_ACCEPTED_EXIT0_ACTUAL_BOOT_NOT_YET_PROVEN',request_accepted_utc=A.utc())
    except BaseException as error:
        record['error_kind']=type(error).__name__
        if child is not None and child.poll() is None:
            child.kill();child.wait(timeout=5)
        raise
    finally:A.atomic(out,record)
    print(json.dumps({'state':record['state'],'receipt':str(out),'sha256':sha(out)}))

if __name__=='__main__':main()
