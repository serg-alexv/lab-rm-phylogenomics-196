"""Actual Windows byte-lock contention tests in an isolated C runtime."""
from pathlib import Path
import json, os, subprocess, sys, time
import stage04_controller as C
ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')

def main():
    C.check(sys.platform=='win32','Actual Windows lock test required')
    fixture=HISTORY/'.work'/('waiter_serialization_fixture_'+str(time.time_ns()))
    fixture.mkdir();(fixture/'.work').mkdir()
    out=ROOT/'reports/stage04/resource_wait_v5_v2';out.mkdir(parents=True,exist_ok=True)
    payload=out/'actual_contention_child.json'
    child_code="""import json,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import wait_migration_v5_headroom_v2 as W
W.HISTORY=Path(sys.argv[2])
started=time.monotonic()
with W.serialized_writer():
    Path(sys.argv[3]).write_text(json.dumps({'actual_wait_seconds':time.monotonic()-started,'byte_lock_acquired':True,'native_jobs_started':0})+'\\n')
print('ACTUAL_WAIT_THEN_BYTE_LOCK_ACQUIRED',flush=True)
"""
    with C.WorkflowLock(fixture/'.work/workflow.lock'):
        command=[sys.executable,'-u','-c',child_code,str(ROOT/'scripts'),str(fixture),str(payload)]
        child=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        first_line=child.stdout.readline().strip()
        C.check(first_line=='WAITING_EXISTING_WRITER_BYTE_LOCK; NO_WORK_LAUNCHED','Actual contention was not observed')
        C.check(child.poll() is None and not payload.exists(),'Child crossed held byte lock')
    stdout,stderr=child.communicate(timeout=10)
    C.check(child.returncode==0 and 'ACTUAL_WAIT_THEN_BYTE_LOCK_ACQUIRED' in stdout and not stderr,'Actual contention child did not resume cleanly')
    actual=C.load(payload);C.check(actual['byte_lock_acquired'] and actual['native_jobs_started']==0,'No actual acquisition proof')
    duplicate_code="""import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import stage04_controller as C
with C.WorkflowLock(Path(sys.argv[2])):print('DUPLICATE_ENTERED')
"""
    with C.WorkflowLock(fixture/'.work/v5_resource_wait.lock'):
        duplicate=subprocess.run([sys.executable,'-c',duplicate_code,str(ROOT/'scripts'),str(fixture/'.work/v5_resource_wait.lock')],cwd=ROOT,capture_output=True,text=True)
        C.check(duplicate.returncode!=0 and 'Actual workflow byte lock is held' in duplicate.stderr and 'DUPLICATE_ENTERED' not in duplicate.stdout,'Duplicate observer guard failed')
    C.atomic(out/'serialization_test.json',{'status':'PASS_ACTUAL_WINDOWS_BYTE_LOCK_CONTENTION_AND_DUPLICATE_GUARD_ISOLATED_ONLY',
        'utc':C.now(),'actual_fixture_runtime':str(fixture),'contending_child_argv':command,
        'actual_contention_exit_code':child.returncode,'actual_contention_proof':actual,
        'actual_duplicate_exit_code':duplicate.returncode,'production_lock_touched':False,'native_biological_jobs':0,
        'waiter_source_sha256':C.digest(ROOT/'scripts/wait_migration_v5_headroom_v2.py'),'test_source_sha256':C.digest(__file__)})
    print('ACTUAL_WINDOWS_SERIALIZATION_AND_DUPLICATE_GUARD_PASSED',flush=True)

if __name__=='__main__':main()
