"""Preserve the actual admitted controller failure before any biological launch."""
import hashlib,json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_recovery_controller_v10_admission_v1 as P
import stage04_windows_job_v10 as J

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock)
        proposal,review=P.acceptance()
        runtime=Path(proposal['production_task']['runtime'])
        path=S.REPORT/'production_admission_v1_pre_native_abort.json'
        C.check(not path.exists(),'Preserved abort certificate already exists; no replacement')
        owner=C.load(runtime/'controller_binding.json')['controller']
        observed=C.load(runtime/'independent_controller_exit.json')
        C.check(observed['process']['pid']==owner['pid'] and observed['process']['creation_filetime']==owner['creation_filetime'] and
          observed['process']['state']=='EXITED' and observed['process']['actual_exit_code']==1,'Actual bound controller exit1 required')
        native=C.load(runtime/'source_gate_process/exit.json')
        C.check(native['exit_code']==1 and native['job_active_processes']==0 and native['actual_job_process_ids']==[] and
          native['role']=='INDEPENDENT_SOURCE_GATE','Actual failed source gate and drained job required')
        stderr=(runtime/'source_gate_process/stderr.txt').read_text()
        C.check('Other matching live scientific runner found; no duplicate launch' in stderr,'Unexpected abort; do not substitute diagnosis')
        C.check(not S.OUT.exists() and not (runtime/'production_started.json').exists() and not (runtime/'analyses').exists(),
          'Pre-native boundary changed; require a different actual reconciliation')
        observer=C.load(runtime/'independent_controller_observer_binding.json')['actual_scheduler_observer']
        for actor in (owner,observer['actual_process']):
            C.check(S.process_identity(actor['pid'],actor['creation_filetime'])['state'] in
              ('ABSENT_WIN32_ERROR_INVALID_PARAMETER','EXITED','PID_REUSED_DIFFERENT_CREATION'),'Recorded controller/observer still live')
        tasks=[proposal['production_task'],proposal['production_readonly_observer_task']]
        query="$ErrorActionPreference='Stop'; $s=New-Object -ComObject Schedule.Service; $s.Connect(); @("
        query+=';'.join("$t=$s.GetFolder('\\').GetTask('"+r['task_name']+"'); $runs=@($s.GetRunningTasks(1) | Where-Object {$_.Name -eq $t.Name}); [pscustomobject]@{name=$t.Name;xml=$t.Xml;state=$t.State;last_task_result=$t.LastTaskResult;instances=$runs.Count}" for r in tasks)
        query+=") | ConvertTo-Json -Depth 4 -Compress"
        directory=runtime/'abort_reconciliation_task_query'
        result=J.run_job([r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe','-NoProfile','-NonInteractive','-Command',query],S.ROOT,
          directory,cap_bytes=256*1024**2,deadline_seconds=20,role='PRE_NATIVE_ABORT_READ_ONLY_TASK_QUERY')
        C.check(result['exit_code']==0 and result['job_active_processes']==0 and result['actual_job_process_ids']==[],'Actual query job not closed')
        actual=json.loads((directory/'stdout.txt').read_text(encoding='utf-8-sig'))
        C.check(isinstance(actual,list) and len(actual)==2,'Incomplete actual task query')
        for row,request,code in zip(actual,tasks,[1,0]):
            C.check(row['name']==request['task_name'] and row['state']==3 and row['last_task_result']==code and row['instances']==0 and
              hashlib.sha256(b'\xff\xfe'+row['xml'].encode('utf-16le')).hexdigest()==request['definition_sha256'],'Actual abort task identity/closure differs')
        files=[runtime/n for n in ['controller_binding.json','controller_exception.json','independent_controller_observer_binding.json',
          'independent_controller_exit.json','source_gate_process/launch.json','source_gate_process/exit.json','source_gate_process/stderr.txt',
          'outer_job_compatibility.json','isolation.json','task_start.json']]
        files += [directory/n for n in ['launch.json','exit.json','stdout.txt']]
        value={'utc':C.now(),'status':'NEGATIVE_PRE_NATIVE_ADMISSION_V1_ABORT_ACTUAL_CONTROLLER_EXIT1_SOURCE_JOB_EMPTY',
          'proposal_sha256':C.digest(P.PROPOSAL),'parent_acceptance_sha256':C.digest(P.ACCEPTANCE),
          'actual_controller_exit':observed['process'],'actual_source_gate_exit':native,
          'actual_closed_scheduler_tasks':[{k:r[k] for k in ['name','state','last_task_result','instances']} for r in actual],
          'actual_retained_workflow_lock_identity':S.lock_identity(lock),'scientific_jobs_launched':0,
          'scientific_zero_evidence':'Pinned controller failed source_gate_process before production_started, output mkdir or native loop; all three actual boundaries remain absent',
          'scientific_outputs':'ABSENT','ordinary_controller_closure':'NOT_EMITTED','ordinary_scientific_success':False,
          'failure':'LIVE_RUNNER_CLASSIFICATION_REJECTION','inventory_at_failure':'NOT_PERSISTED_UNKNOWN_ALL_CANDIDATES',
          'concrete_source_defect':'Accepted observer actual argv contains recovery_controller and satisfies the broad matcher; owner-only comparison rejects it',
          'old_v6_controller_outcome':'UNKNOWN','old_v6_final_job_closure':'UNKNOWN','old_v6_native_exit_code':1,
          'file_sha256':{'historical:'+p.relative_to(S.HISTORY).as_posix():C.digest(p) for p in files}}
        C.atomic(path,value)
        status=S.ROOT/'STATUS.md';C.atomic(status,status.read_text()+'\n\n'+C.now()+': Parent exact267-artifact acceptance verified; unique admission1 production/controller observer started once. Controller22112/creation134359851404203459 actually exited1 at FILETIME134359851573151189. Source gate rejected other matching runners before any IQ-TREE/output namespace/native invocation; actual source-checker job exit1 and active0/[] preserved. Accepted read-only observer argv also matches the broad runner predicate. The failure inventory was not persisted, so its full membership remains UNKNOWN. New versioned exact observer-role classification is required before another separately accepted single start. Stage04 scientific FAILED/INCOMPLETE;05–07 NOT_RUN. See reports/stage04/recovery_v10/production_admission_v1_pre_native_abort.json.\n')
        execution=S.ROOT/'status/stage04_execution.json';state=C.load(execution);state.update(utc=C.now(),execution='FAILED_PRE_NATIVE_SOURCE_GATE',
          native_production='NOT_LAUNCHED',running_native_job=None,parent_acceptance='HASH_BOUND_VERIFIED_SINGLE_START_CONSUMED',
          actual_controller_exit_code=1,pre_native_abort_certificate_sha256=C.digest(path),scientific_validation='INCOMPLETE',later_stages='NOT_RUN')
        C.atomic(execution,state)
        receipt=S.publish(['scripts/record_stage04_production_pre_native_abort_v1.py',path.relative_to(S.ROOT).as_posix(),
          'STATUS.md','status/stages.tsv','status/stage04_execution.json'],'Preserve accepted one-shot pre-native source-gate failure and actual closure')
        C.atomic(S.REPORT/'production_admission_v1_abort_publication_receipt.json',receipt)
        print(json.dumps({'status':receipt['status'],'commit':receipt['commit'],'certificate_sha256':C.digest(path),'biological_jobs':0}))

if __name__=='__main__':main()
