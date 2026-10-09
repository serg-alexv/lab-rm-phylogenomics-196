"""New unique never-started tasks; admission1 requests/sources remain immutable."""
import json,uuid
import stage04_controller as C
import stage04_recovery_support_v10 as S
from prepare_stage04_production_tasks_admission_v1 import register,base

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock)
        abort=C.load(S.REPORT/'production_admission_v1_pre_native_abort.json')
        C.check(abort['scientific_jobs_launched']==0 and not S.OUT.exists(),'Actual pre-native abort/no output namespace required')
        config=S.ROOT/'config/host_inference_stage04_recovery_v10_production_admission_v2.json'
        C.check(not config.exists(),'Unique revision2 config already exists')
        sid=S.command(['powershell.exe','-NoProfile','-NonInteractive','-Command','[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value']).decode().strip()
        name='LAB_RM_Stage04_V10_production_admission_v2_'+uuid.uuid4().hex[:12];runtime=S.RUNTIME/'production'/name
        value={'protocol':'V10_NEGATIVE_HISTORY_NEW_ORDINARY_CLOSURE','production_admission_revision':'V10_PRODUCTION_ADMISSION_V2',
          'mode':'production','runtime':str(runtime),'task_name':name,'analysis_names':S.NAMES,'threads':2,'seed':1961008,
          'compute_affinity_mask':5,'data_root':str(S.ROOT),'historical_root':str(S.HISTORY),
          'allow_fixture_scheduler_outer_job_observation':False,'production_parent_review':str(S.ROOT/'.work/host_review/PARENT_RECOVERY_V10_ADMISSION_V2_REVIEW.json')}
        C.atomic(config,value)
        argv=['-u',str(S.ROOT/'scripts/stage04_recovery_controller_v10_admission_v2.py'),'--config',str(config)]
        request={**base(name,'production',runtime,argv,sid),'config':str(config),'config_sha256':C.digest(config)}
        request=register(request,S.REPORT/'production_task'/name)
        observer_name='LAB_RM_Stage04_V10_readonly_observer_'+uuid.uuid4().hex[:12];observer_runtime=S.RUNTIME/'observers'/observer_name
        argv=['-u',str(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py'),'--runtime',str(runtime),'--observer-runtime',str(observer_runtime)]
        observer={**base(observer_name,'observer',observer_runtime,argv,sid),'target_runtime':str(runtime),'target_task_name':name}
        observer=register(observer,S.REPORT/'observer_tasks'/observer_name)
        receipt={'utc':C.now(),'status':'TWO_UNIQUE_ADMISSION2_TASKS_REGISTERED_NEVER_STARTED','production_request':str(runtime/'task_request.json'),
          'observer_request':str(observer_runtime/'task_request.json'),'production_definition_sha256':request['definition_sha256'],
          'observer_definition_sha256':observer['definition_sha256'],'scientific_jobs':0,'lifetime_mechanism':'UNCHANGED_TESTED_V10',
          'parent_acceptance':'NOT_GRANTED','prior_abort_sha256':C.digest(S.REPORT/'production_admission_v1_pre_native_abort.json')}
        C.atomic(S.REPORT/'production_admission_v2_registered_tasks.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':main()
