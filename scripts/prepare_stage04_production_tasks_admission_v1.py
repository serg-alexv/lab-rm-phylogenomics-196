"""Register/query unused direct V10 admission1 production and proven observer."""
import json,shutil,subprocess,uuid
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import prepare_stage04_recovery_tasks_v10 as T

def register(request,report):
    runtime=Path(request['runtime']);runtime.mkdir(parents=True,exist_ok=False)
    path=runtime/'task_request.json';C.atomic(path,request)
    for name in ('register_stage04_recovery_task_v10.ps1','query_stage04_recovery_task_v10.ps1'):
        S.command(['powershell.exe','-NoProfile','-NonInteractive','-File',str(S.ROOT/'scripts'/name),'-Request',str(path)])
    request.update(xml_path=str(runtime/'actual_task_definition.xml'),query_path=str(runtime/'actual_task_query.json'))
    query=C.load(request['query_path'])
    C.check(query['sid']==request['sid'] and query['logon_type']==3 and query['run_level']==0 and query['triggers_count']==0 and
      query['actions_count']==1 and query['multiple_instances']==2 and query['execution_time_limit']=='PT0S' and query['restart_count']==0 and
      query['executable']==request['executable'] and query['arguments']==request['arguments'] and query['cwd']==request['cwd'] and
      query['state']==3 and query['last_task_result']==267011,'Actual unused direct task definition differs')
    request.update(definition_sha256=C.digest(request['xml_path']),query_sha256=C.digest(request['query_path']));C.atomic(path,request)
    report.mkdir(parents=True,exist_ok=False)
    for src,dst in [(path,'request.json'),(Path(request['xml_path']),'definition.xml'),(Path(request['query_path']),'query.json')]:shutil.copy2(src,report/dst)
    return request

def base(name,mode,runtime,argv,sid):
    return {'protocol':'V10_MANUAL_UNIQUE_ONESHOT_DIRECT_CONTROLLER','mode':mode,'task_name':name,'sid':sid,
      'executable':str(S.PYTHONW),'executable_sha256':C.digest(S.PYTHONW),'argv':argv,'arguments':subprocess.list2cmdline(argv),
      'cwd':str(S.ROOT),'runtime':str(runtime),'xml_path':str(runtime/'task_definition.xml'),
      'query_path':str(runtime/'task_query.json'),'start_path':str(runtime/'task_start.json')}

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock)
        C.check(not S.OUT.exists(),'Production output namespace already exists; no duplicate')
        config=S.ROOT/'config/host_inference_stage04_recovery_v10_production.json';C.check(not config.exists(),'Production config already exists; new version required')
        sid=S.command(['powershell.exe','-NoProfile','-NonInteractive','-Command','[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value']).decode().strip()
        name='LAB_RM_Stage04_V10_production_admission_v1_'+uuid.uuid4().hex[:12];runtime=S.RUNTIME/'production'/name
        value={'protocol':'V10_NEGATIVE_HISTORY_NEW_ORDINARY_CLOSURE','production_admission_revision':'V10_PRODUCTION_ADMISSION_V1',
          'mode':'production','runtime':str(runtime),'task_name':name,'analysis_names':S.NAMES,'threads':2,'seed':1961008,
          'compute_affinity_mask':5,'data_root':str(S.ROOT),'historical_root':str(S.HISTORY),
          'allow_fixture_scheduler_outer_job_observation':False,'production_parent_review':str(S.ROOT/'.work/host_review/PARENT_RECOVERY_V10_REVIEW.json')}
        C.atomic(config,value)
        argv=['-u',str(S.ROOT/'scripts/stage04_recovery_controller_v10_admission_v1.py'),'--config',str(config)]
        request={**base(name,'production',runtime,argv,sid),'config':str(config),'config_sha256':C.digest(config)}
        request=register(request,S.REPORT/'production_task'/name)
        observer_name='LAB_RM_Stage04_V10_readonly_observer_'+uuid.uuid4().hex[:12];observer_runtime=S.RUNTIME/'observers'/observer_name
        argv=['-u',str(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py'),'--runtime',str(runtime),'--observer-runtime',str(observer_runtime)]
        observer={**base(observer_name,'observer',observer_runtime,argv,sid),'target_runtime':str(runtime),'target_task_name':name}
        observer=register(observer,S.REPORT/'observer_tasks'/observer_name)
        receipt={'utc':C.now(),'status':'TWO_UNIQUE_ZERO_TRIGGER_MANUAL_TASKS_REGISTERED_NEVER_STARTED','production_request':str(runtime/'task_request.json'),
          'observer_request':str(observer_runtime/'task_request.json'),'production_definition_sha256':request['definition_sha256'],
          'observer_definition_sha256':observer['definition_sha256'],'scientific_jobs':0,'tested_lifetime_mechanism_sources':'UNCHANGED_V10',
          'production_only_controller_revision':'V10_PRODUCTION_ADMISSION_V1','parent_acceptance':'NOT_GRANTED'}
        C.atomic(S.REPORT/'production_admission_v1_registered_tasks.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':main()
