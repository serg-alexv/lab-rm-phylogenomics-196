"""Measured headroom wait with explicit serialization of preparation writers.

The prior fail-fast writer guard stopped the observer during authorized prep.
This successor waits for that same real byte lock; no lock is deleted/bypassed.
"""
from contextlib import contextmanager
from pathlib import Path
import json, os, subprocess, sys, time
import stage04_controller as C
import production_resume as w
from workflow_publication import commit
ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=ROOT/'reports/stage04/resource_wait_v5_v2'
MINIMUM=4831838208

@contextmanager
def serialized_writer():
    next_message=0
    while True:
        lock=C.WorkflowLock(HISTORY/'.work/workflow.lock')
        try:
            lock.__enter__()
            break
        except ValueError as error:
            if str(error)!='Actual workflow byte lock is held; no competing launch permitted':raise
            if time.monotonic()>=next_message:
                print('WAITING_EXISTING_WRITER_BYTE_LOCK; NO_WORK_LAUNCHED',flush=True)
                next_message=time.monotonic()+60
            time.sleep(2)
    try:yield
    finally:lock.__exit__(None,None,None)

def publish(observation, execution, failure=None):
    with serialized_writer():
        C.reconcile(ROOT)
        ready=execution=='ACTUAL_V5_PRODUCER_BOUNDARY_COMPLETE_ADOPTION_PENDING'
        w.js(OUT/'current.json',{'utc':C.now(),'execution':execution,'actual_waiter_pid':os.getpid(),
            'required_windows_available_bytes':MINIMUM,'required_linux_available_bytes':4294967296,
            'actual_windows_observation':observation,'failure':failure,'native_inference_started':False,
            'producer_resource_boundary':'PASSED' if ready else 'PENDING','candidate_adoption':'NOT_ADOPTED',
            'full_stage04':'INCOMPLETE','stage05_stage06_stage07':'NOT_RUN',
            'user_instruction':'Keep waiting for headroom; gates unchanged; no unrelated termination; resets manual only'})
        detail=('Actual G source/bootstrap/argv and actual resource-bound producer checks passed; code adoption and publication are pending.' if ready else
                'Actual G bootstrap/full196 source and argv checks passed; actual producer resource binding and code adoption remain pending.')
        detail+=' Measured waiter PID '+str(os.getpid())+' observed Windows '+str(observation['available_bytes'])+' bytes against '+str(MINIMUM)+' required. No IQ-TREE inference or detector production process is running.'
        w.status('4_phylogeny',execution,'PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
                 'STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING',detail)
        head=commit(['scripts/wait_migration_v5_headroom_v2.py','scripts/complete_migration_v5_resource_binding.py',
                     'reports/stage04/resource_wait_v5_v2/current.json','reports/stage04/resource_wait_v5_v2/observations.jsonl',
                     'STATUS.md','status/stages.tsv'],'Record measured WD headroom and serialized wait owner')
        print('RESOURCE_WAIT_PROGRESS_PUBLISHED '+head,flush=True)

def main():
    C.check(sys.platform=='win32' and Path.cwd().resolve()==ROOT,'Dedicated G Windows wait owner required')
    OUT.mkdir(parents=True,exist_ok=True)
    # This exact extra guard is shared with v1, so the successor cannot duplicate
    # a surviving observer. Scientific/preparation writes retain the C lock.
    with C.WorkflowLock(HISTORY/'.work/v5_resource_wait.lock'):
        next_publish=0
        while True:
            observation=C.windows_snapshot(ROOT,pid=os.getpid())
            with serialized_writer():
                with (OUT/'observations.jsonl').open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps(observation)+'\n');stream.flush();os.fsync(stream.fileno())
            print('MEASURED_WINDOWS_AVAILABLE '+str(observation['available_bytes'])+' '+observation['utc'],flush=True)
            if time.monotonic()>=next_publish:
                publish(observation,'WAITING_MEASURED_WINDOWS_HEADROOM_V5');next_publish=time.monotonic()+300
            if observation['available_bytes']>=MINIMUM:
                result=subprocess.run([sys.executable,'-u','scripts/complete_migration_v5_resource_binding.py'],cwd=ROOT,capture_output=True)
                error=result.stderr.decode('utf-8',errors='replace')
                with serialized_writer():
                    w.js(OUT/('boundary_attempt_'+C.now().replace(':','').replace('+','_')+'.json'),
                         {'utc':C.now(),'actual_command':[sys.executable,'-u','scripts/complete_migration_v5_resource_binding.py'],
                          'exit_code':result.returncode,'stdout':result.stdout.decode('utf-8',errors='replace'),
                          'stderr':error,'native_inference_started':False})
                if result.returncode==0:
                    ready=C.load(ROOT/'reports/stage04/migration_v5_ready_for_adoption.json')
                    C.check(ready['status']=='PASS_ACTUAL_G_SOURCE_BOOTSTRAP_ARGV_PRODUCER_RESOURCE_BOUNDARY_READY_FOR_CODE_ADOPTION',
                            'Boundary exit alone cannot establish readiness')
                    publish(observation,'ACTUAL_V5_PRODUCER_BOUNDARY_COMPLETE_ADOPTION_PENDING')
                    print('REAL_BOUNDARY_READY_FOR_ROOT_ADOPTION_NO_INFERENCE',flush=True);return
                if ('Measured current Windows/Linux headroom insufficient; no native launch' not in error
                        and 'Actual workflow byte lock is held; no competing launch permitted' not in error):
                    publish(observation,'STOPPED_EXPLICIT_V5_BOUNDARY_BLOCKER',error[-2000:])
                    raise RuntimeError('Actual boundary failed beyond memory/serialization; evidence preserved')
            time.sleep(30)

if __name__=='__main__':main()
