"""V10 closed boundary: reuse four real audits; require actual controller exit0.

The immutable old B2 guard remains unchanged and still rejects missing V6
ordinary closure. This checker implements a distinct explicitly reviewed
negative-history protocol; missing new closure always blocks final PASS.
"""
import json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_recovery_controller_v10_admission_v1 as P
import stage04_production_admission_policy_v1 as A

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        S.pins();S.held_lock_matches_negative(lock);proposal,parent=P.acceptance()
        freeze=C.load(S.OUT/'inference_freeze.json');S.original_freeze_fields(freeze);runtime=Path(freeze['stable_runtime'])
        C.check(runtime.is_relative_to(S.RUNTIME),'Final runtime role differs')
        observed=C.load(runtime/'independent_controller_exit.json');binding=C.load(runtime/'controller_binding.json')
        observer_binding=C.load(runtime/'independent_controller_observer_binding.json')
        C.check(observed['binding_sha256']==C.digest(runtime/'independent_controller_observer_binding.json') and
          observer_binding['source_sha256']==C.digest(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py') and
          observer_binding['controller_binding_sha256']==C.digest(runtime/'controller_binding.json') and
          observer_binding['controller_config_sha256']==binding['config_sha256']==proposal['production_task']['config_sha256'] and
          observer_binding['controller_definition_sha256']==binding['scheduler_definition_sha256']==proposal['production_task']['definition_sha256'],
          'Final independent observer/controller/config/definition bindings differ')
        observer=observer_binding['actual_scheduler_observer'];observer_task=proposal['production_readonly_observer_task']
        C.check(observer['runtime']==observer_task['runtime'] and observer['definition_sha256']==observer_task['definition_sha256'] and
          observer['actual_live_scheduler_binding']['actual_request_sha256']==C.digest(Path(observer_task['runtime'])/'task_request.json') and
          observer['actual_live_scheduler_binding']['actual_process_argv']==[observer_task['executable'],*observer_task['argv']],
          'Final exact independent Scheduler observer role/action differs')
        C.check(C.digest(P.PROPOSAL)==freeze['recovery_proposal_sha256'] and C.digest(P.ACCEPTANCE)==freeze['parent_acceptance_sha256'] and
          C.digest(runtime/'controller_binding.json')==freeze['controller_binding_sha256'] and
          C.digest(runtime/'actual_live_scheduler_binding.json')==freeze['actual_live_scheduler_binding_sha256'],
          'Final proposal/acceptance/controller/live-instance bytes differ')
        current=C.load(runtime/'independent_current_boundary.json')
        C.check(C.digest(runtime/'independent_current_boundary.json')==freeze['fresh_exclusive_boundary_sha256'] and
          current['actual_retained_workflow_lock_identity']==S.lock_identity(lock) and current['controller']==binding['controller'] and
          current['negative_history_certificate_sha256']==C.digest(S.NEGATIVE),'Final fresh exclusive boundary changed')
        actual=observed['process'];owner=binding['controller']
        C.check(freeze['production_admission_revision']=='V10_PRODUCTION_ADMISSION_V1' and freeze['outer_job_compatibility_sha256']==C.digest(runtime/'outer_job_compatibility.json'),'Final explicit outer-policy receipt differs')
        A.verify_compatibility_receipt(runtime/'outer_job_compatibility.json',proposal,owner)
        C.check(observed['status']=='ACTUAL_BOUND_CONTROLLER_EXIT_OBSERVED' and actual['pid']==owner['pid'] and
          actual['creation_filetime']==owner['creation_filetime'] and actual['actual_exit_code']==0 and actual['state']=='EXITED' and
          actual['exit_filetime']>actual['creation_filetime'],'New actual ordinary controller exit0 required; missing/None cannot pass')
        C.check(S.process_identity(owner['pid'],owner['creation_filetime'])['state'] in ('ABSENT_WIN32_ERROR_INVALID_PARAMETER','EXITED','PID_REUSED_DIFFERENT_CREATION'),
          'Bound controller still alive')
        closed=C.load(runtime/'controller_closure.json');completed=C.load(runtime/'all_scope_checks_complete.json')
        C.check(closed['status']=='ORDINARY_CONTROLLER_SCOPE_CLOSURE' and closed['mode']=='production' and closed['scientific_jobs_completed']==4 and
          closed['controller']==owner and closed['lock_identity']==binding['lock_identity']==S.lock_identity(lock) and
          closed['native_jobs_actual_empty'] is True and completed['status']=='FOUR_ACTUAL_SCOPES_INDEPENDENTLY_VALIDATED_RELEASE_PENDING',
          'Actual controller four-scope closure absent')
        checks={}
        for name in S.NAMES:
            A.verify_compatibility_receipt(runtime/'analyses'/name/'outer_job_compatibility.json',proposal,owner)
            S.scope_binding(name);S.original_freeze_fields(freeze);P.verify_artifacts(proposal['required_review_artifacts'])
            path=S.REPORT/(name+'_independent_check.json');certificate=C.load(path)
            C.check(C.digest(path)==completed['scientific_certificates'][name] and certificate['checker_sha256']==C.digest(S.ROOT/'scripts/stage04_recovery_validate_v10_admission_v1.py') and
              certificate['status']=='PASS_V10_REAL_ORDINARY_LIFECYCLE_AND_UNCHANGED_SCIENTIFIC_OUTPUT_CHECKS' and
              certificate['inference_freeze_sha256']==C.digest(S.OUT/'inference_freeze.json'),'Real independent scope certificate changed/missing')
            directory=S.OUT/'analyses'/name/'iqtree'
            for member,sha in certificate['result']['file_sha256'].items():
                path2=directory/member;C.check(path2.resolve().is_relative_to(directory.resolve()) and C.digest(path2)==sha,'Validated immutable scope payload changed')
            for member in ('launch.json','exit.json'):
                C.check(C.digest(directory/'attempt_0001'/member)==C.digest(runtime/'analyses'/name/'attempt_0001'/member),'Final ordinary C/G receipt mismatch')
            checks[name]=C.digest(path)
        P.verify_artifacts(proposal['required_review_artifacts'])
        tasks=S.closed_scheduler_tasks(runtime,[proposal['production_task'],observer_task])
        value={'utc':C.now(),'status':'PASS_V10_ACTUAL_CONTROLLER_AND_ALL_FOUR_SCIENTIFIC_SCOPES_CLOSED_RELEASE_PENDING',
          'actual_final_task_results':tasks,'production_admission_revision':'V10_PRODUCTION_ADMISSION_V1',
          'outer_job_compatibility_sha256':C.digest(runtime/'outer_job_compatibility.json'),
          'scope_certificate_sha256':checks,'controller_actual_exit_sha256':C.digest(runtime/'independent_controller_exit.json'),
          'old_controller_outcome':'UNKNOWN','old_final_job_closure':'UNKNOWN','old_history_role':'NEGATIVE_ONLY',
          'shared_writer_lock_identity':S.lock_identity(lock),'inference_freeze_sha256':C.digest(S.OUT/'inference_freeze.json'),
          'checker_sha256':C.digest(__file__),'release':'NOT_VALIDATED_BY_THIS_CHECK'}
        C.atomic(S.REPORT/'final_closed_boundary.json',value);print(value['status'])

if __name__=='__main__':main()
