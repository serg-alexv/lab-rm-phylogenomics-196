"""Measured waiting chosen by the user; only admitted boundary checks run."""
from pathlib import Path
import csv, io, json, os, subprocess, sys, time
import stage04_controller as C
import production_resume as w
from workflow_publication import commit
ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=ROOT/'reports/stage04/resource_wait_v5'
MINIMUM=4831838208

def publish(observation, execution, failure=None):
    with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
        C.reconcile(ROOT)
        value={'utc':C.now(),'execution':execution,'actual_waiter_pid':os.getpid(),
               'required_windows_available_bytes':MINIMUM,'required_linux_available_bytes':4294967296,
               'actual_windows_observation':observation,'failure':failure,
               'native_inference_started':False,'candidate_adoption':'NOT_ADOPTED',
               'full_stage04':'INCOMPLETE','stage05_stage06_stage07':'NOT_RUN',
               'user_instruction':'Keep waiting for headroom; no lower gates or unrelated termination; resets manual only'}
        w.js(OUT/'current.json',value)
        w.status('4_phylogeny',execution,'PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
                 'STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING',
                 'Actual G bootstrap/full196 source and argv mapping checks passed; V5 still requires real producer resource binding and code adoption. Measured waiterPID'+str(os.getpid())+
                 ' observes Windows'+str(observation['available_bytes'])+'bytes against unchanged4831838208-byte admission; no IQ-TREE process is running. Both detectors, figure and final handoff remain NOT_RUN.')
        head=commit(['scripts/wait_migration_v5_headroom.py','scripts/complete_migration_v5_resource_binding.py',
                     'reports/stage04/resource_wait_v5/current.json','reports/stage04/resource_wait_v5/observations.jsonl',
                     'STATUS.md','status/stages.tsv'],'Record actual measured WD headroom wait and pending scientific admission')
        print('RESOURCE_WAIT_PROGRESS_PUBLISHED '+head,flush=True)

def main():
    C.check(sys.platform=='win32' and Path.cwd().resolve()==ROOT,'Dedicated G Windows wait owner required')
    OUT.mkdir(parents=True,exist_ok=True)
    # Separate OS guard prevents duplicate waiters; science retains its stable
    # historical byte lock for every writer or actual boundary invocation.
    with C.WorkflowLock(HISTORY/'.work/v5_resource_wait.lock'):
        next_publish=0
        while True:
            observation=C.windows_snapshot(ROOT,pid=os.getpid())
            with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
                with (OUT/'observations.jsonl').open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps(observation)+'\n');stream.flush();os.fsync(stream.fileno())
            print('MEASURED_WINDOWS_AVAILABLE '+str(observation['available_bytes'])+' '+observation['utc'],flush=True)
            if time.monotonic()>=next_publish:
                publish(observation,'WAITING_MEASURED_WINDOWS_HEADROOM_V5');next_publish=time.monotonic()+300
            if observation['available_bytes']>=MINIMUM:
                # The invoked checker independently remeasures Windows before/
                # after WSL and Linux; this preliminary sample never admits IQ.
                result=subprocess.run([sys.executable,'-u','scripts/complete_migration_v5_resource_binding.py'],
                                      cwd=ROOT,capture_output=True)
                with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
                    attempt=OUT/('boundary_attempt_'+C.now().replace(':','').replace('+','_')+'.json')
                    w.js(attempt,{'utc':C.now(),'actual_command':['python','-u','scripts/complete_migration_v5_resource_binding.py'],
                                  'exit_code':result.returncode,'stdout':result.stdout.decode('utf-8',errors='replace'),
                                  'stderr':result.stderr.decode('utf-8',errors='replace'),'native_inference_started':False})
                if result.returncode==0:
                    ready=C.load(ROOT/'reports/stage04/migration_v5_ready_for_adoption.json')
                    C.check(ready['status']=='PASS_ACTUAL_G_SOURCE_BOOTSTRAP_ARGV_PRODUCER_RESOURCE_BOUNDARY_READY_FOR_CODE_ADOPTION',
                            'Boundary exit alone cannot establish readiness')
                    publish(observation,'ACTUAL_V5_PRODUCER_BOUNDARY_COMPLETE_ADOPTION_PENDING')
                    print('REAL_BOUNDARY_READY_FOR_ROOT_ADOPTION_NO_INFERENCE',flush=True);return
                error=result.stderr.decode('utf-8',errors='replace')
                if 'Measured current Windows/Linux headroom insufficient; no native launch' not in error:
                    publish(observation,'STOPPED_EXPLICIT_V5_BOUNDARY_BLOCKER',error[-2000:])
                    raise RuntimeError('Actual boundary failed beyond headroom; evidence preserved')
            time.sleep(30)

if __name__=='__main__':main()
