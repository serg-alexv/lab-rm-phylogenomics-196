"""Version the exact observer-role repair; preserve adopted admission1 bytes."""
import ast,json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_recovery_controller_v10_admission_v1 as OLD

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock);previous,_=OLD.acceptance()
        abort_path=S.REPORT/'production_admission_v1_pre_native_abort.json';abort=C.load(abort_path)
        C.check(abort['scientific_jobs_launched']==0 and abort['ordinary_scientific_success'] is False and
          abort['actual_controller_exit']['actual_exit_code']==1 and not S.OUT.exists(),'Actual preserved pre-native abort required')
        generated={};changes=[]
        def make(name,extra):
            source=S.ROOT/'scripts'/name;destination=name.replace('admission_v1','admission_v2');text=source.read_text(encoding='utf-8')
            common=[('_v10_admission_v1','_v10_admission_v2'),('V10_PRODUCTION_ADMISSION_V1','V10_PRODUCTION_ADMISSION_V2'),
              ('PARENT_RECOVERY_V10_REVIEW.json','PARENT_RECOVERY_V10_ADMISSION_V2_REVIEW.json'),
              ('host_inference_stage04_recovery_v10_production.json','host_inference_stage04_recovery_v10_production_admission_v2.json')]
            for old,new in common+extra:
                count=text.count(old)
                if (old,new) in extra:C.check(count>0,'Guarded new delta fragment absent')
                if count:
                    text=text.replace(old,new);changes.append({'source':name,'destination':destination,'old_fragment':old,'new_fragment':new,'occurrences':count})
            path=S.ROOT/'scripts'/destination;C.check(not path.exists(),'Revision2 source collision; preserve and version again')
            if path.suffix=='.py':ast.parse(text)
            path.write_text(text,encoding='utf-8',newline='\n');generated[destination]=C.digest(path)
        make('stage04_recovery_controller_v10_admission_v1.py',[
          ('Production-only admission revision1;','Production-only admission revision2: exact accepted read-only observer role;'),
          ('return proposal,value',"abort=C.load(S.REPORT/'production_admission_v1_pre_native_abort.json')\n    C.check(C.digest(S.REPORT/'production_admission_v1_pre_native_abort.json')==proposal['prior_pre_native_abort_sha256'] and\n      abort['ordinary_scientific_success'] is False and abort['scientific_jobs_launched']==0 and\n      abort['actual_controller_exit']['actual_exit_code']==1 and abort['actual_source_gate_exit']['exit_code']==1 and\n      abort['actual_source_gate_exit']['job_active_processes']==0 and abort['actual_source_gate_exit']['actual_job_process_ids']==[],\n      'Prior admission1 failure is negative pre-native history only')\n    return proposal,value")])
        make('stage04_recovery_validate_v10_admission_v1.py',[
          ('import stage04_production_admission_policy_v1 as A','import stage04_production_admission_policy_v1 as A\nimport stage04_readonly_observer_role_v1 as R'),
          ("inventory=A.fresh_runner_inventory()","proposal=C.load(S.ROOT/'config/host_inference_stage04_recovery_v10_admission_v2_freeze.json')\n    abort=C.load(S.REPORT/'production_admission_v1_pre_native_abort.json')\n    prior_runtime=Path(proposal['prior_admission_v1_runtime'])\n    prior_binding=C.load(prior_runtime/'independent_controller_observer_binding.json')\n    prior_instances=[]\n    for actor in [abort['actual_controller_exit'],prior_binding['actual_scheduler_observer']['actual_process'],\n      {'pid':abort['actual_source_gate_exit']['child_pid'],'creation_filetime':abort['actual_source_gate_exit']['child_creation_filetime']}]:\n        actual=S.process_identity(actor['pid'],actor['creation_filetime'])\n        C.check(actual['state'] in ('ABSENT_WIN32_ERROR_INVALID_PARAMETER','EXITED','PID_REUSED_DIFFERENT_CREATION'),\n          'Prior admission1 recorded instance remains live/unresolved')\n        prior_instances.append(actual)\n    inventory=R.source_inventory(proposal,runtime,owner)"),
          ("'fresh_positive_platform_service_roles':inventory['positive_platform_service_roles'],","'fresh_positive_platform_service_roles':inventory['positive_platform_service_roles'],\n      'fresh_positive_readonly_observer_roles':inventory['fresh_positive_readonly_observer_roles'],\n      'runner_inventory_sha256':inventory['runner_inventory_sha256'],'prior_admission1_instances':prior_instances,"),
          ("'Fresh boundary/negative/held-lock binding differs')","'Fresh boundary/negative/held-lock binding differs')\n    R.verify_stored_role(current,P.acceptance()[0],runtime)")])
        make('final_check_stage04_recovery_v10_admission_v1.py',[
          ('import stage04_production_admission_policy_v1 as A','import stage04_production_admission_policy_v1 as A\nimport stage04_readonly_observer_role_v1 as R'),
          ("'Final fresh exclusive boundary changed')","'Final fresh exclusive boundary changed')\n        R.verify_stored_role(current,proposal,runtime)")])
        make('check_stage04_recovery_acceptance_v10_admission_v1.py',[])
        make('activate_stage04_recovery_production_v10_admission_v1.ps1',[])
        C.atomic(S.REPORT/'production_admission_v2_build.json',{'utc':C.now(),'status':'UNADOPTED_MINIMAL_OBSERVER_ROLE_DELTA',
          'previous_adopted_proposal_sha256':C.digest(OLD.PROPOSAL),'previous_parent_acceptance_sha256':C.digest(OLD.ACCEPTANCE),
          'prior_pre_native_abort_sha256':C.digest(abort_path),'preserved_source_sha256':previous['production_delta_source_sha256'],
          'generated_source_sha256':generated,'exact_text_changes':changes,'new_role_source_sha256':C.digest(S.ROOT/'scripts/stage04_readonly_observer_role_v1.py'),
          'scientific_changes':0,'biological_jobs':0,'old_suite_or_lifetime_fixture_repeated':False})
        print(json.dumps({'status':'ADMISSION2_SOURCES_BUILT_NOT_ADOPTED','source_sha256':generated}))

if __name__=='__main__':main()
