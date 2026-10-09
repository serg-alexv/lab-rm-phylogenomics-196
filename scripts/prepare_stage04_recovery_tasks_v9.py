"""Register/export/query unique manual tasks; never start production science."""
import argparse, hashlib, json, shutil, subprocess, uuid
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v9 as S

def task(mode,finalize_existing=False,suffix=''):
    config=S.ROOT/'config'/('host_inference_stage04_recovery_v9_'+mode+suffix+'.json')
    if finalize_existing:
        value=C.load(config);runtime=Path(value['runtime']);path=runtime/'task_request.json';request=C.load(path)
        C.check(not (runtime/'task_start.json').exists(),'Started task cannot be finalized again')
        if not (runtime/'initial_query_rejection.json').exists():
            C.atomic(runtime/'initial_query_rejection.json',{'utc':C.now(),'status':'PRE_START_EVIDENCE_FINALIZATION_RETRY',
              'task_never_started':True,'old_query_sha256':C.digest(runtime/'task_query.json'),
              'correction':'Query XML SID independently; retain initial query and use unique evidence directory'})
        return finish(mode,runtime,path,request)
    sid=S.command(['powershell.exe','-NoProfile','-NonInteractive','-Command','[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value']).decode().strip()
    name='LAB_RM_Stage04_V9_'+mode+'_'+uuid.uuid4().hex[:12]
    runtime=S.RUNTIME/mode/name;runtime.mkdir(parents=True,exist_ok=False)
    C.check(not config.exists(),'Config already exists; explicit new revision required')
    value={'protocol':'V9_NEGATIVE_HISTORY_NEW_ORDINARY_CLOSURE','mode':mode,'runtime':str(runtime),'task_name':name,
      'analysis_names':S.NAMES if mode=='production' else [],'threads':2,'seed':1961008,
      'compute_affinity_mask':5,'data_root':str(S.ROOT),'historical_root':str(S.HISTORY),
      'allow_fixture_scheduler_outer_job_observation':mode=='fixture',
      'production_parent_review':str(S.ROOT/'.work/host_review/PARENT_RECOVERY_V9_REVIEW.json')}
    C.atomic(config,value)
    argv=['-u',str(S.ROOT/'scripts/stage04_recovery_controller_v9.py'),'--config',str(config)]
    request={'protocol':'V9_MANUAL_UNIQUE_ONESHOT_DIRECT_CONTROLLER','mode':mode,'task_name':name,'sid':sid,
      'executable':str(S.PYTHONW),'executable_sha256':C.digest(S.PYTHONW),'argv':argv,'arguments':subprocess.list2cmdline(argv),
      'cwd':str(S.ROOT),'config':str(config),'config_sha256':C.digest(config),'runtime':str(runtime),
      'xml_path':str(runtime/'task_definition.xml'),'query_path':str(runtime/'task_query.json'),'start_path':str(runtime/'task_start.json')}
    path=runtime/'task_request.json';C.atomic(path,request)
    S.command(['powershell.exe','-NoProfile','-NonInteractive','-File',str(S.ROOT/'scripts/register_stage04_recovery_task_v9.ps1'),'-Request',str(path)])
    return finish(mode,runtime,path,request)

def finish(mode,runtime,path,request):
    S.command(['powershell.exe','-NoProfile','-NonInteractive','-File',str(S.ROOT/'scripts/query_stage04_recovery_task_v9.ps1'),'-Request',str(path)])
    request['xml_path']=str(runtime/'actual_task_definition.xml');request['query_path']=str(runtime/'actual_task_query.json')
    xml=Path(request['xml_path']);query=C.load(request['query_path']);sid=request['sid']
    C.check(query['executable']==request['executable'] and query['arguments']==request['arguments'] and query['cwd']==request['cwd'] and
      query['sid']==sid and query['logon_type']==3 and query['run_level']==0 and query['triggers_count']==0 and
      query['actions_count']==1 and query['multiple_instances']==2 and query['execution_time_limit']=='PT0S' and query['restart_count']==0,
      'Actual registered definition/query differs')
    request['definition_sha256']=C.digest(xml);request['query_sha256']=C.digest(request['query_path']);C.atomic(path,request)
    report=S.REPORT/(mode+'_task')/request['task_name'];report.mkdir(parents=True,exist_ok=False)
    for src,name2 in [(path,'request.json'),(xml,'definition.xml'),(Path(request['query_path']),'query.json')]:shutil.copy2(src,report/name2)
    return {'task_name':request['task_name'],'request':str(path),'definition_sha256':request['definition_sha256'],'runtime':str(runtime)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['fixture','production'],required=True);p.add_argument('--finalize-existing',action='store_true');p.add_argument('--suffix',default='');a=p.parse_args()
    with C.WorkflowLock(S.LOCK):
        C.reconcile(S.ROOT);S.pins();S.topology()
        C.check(S.PYTHONW.exists(),'Direct pythonw executable missing')
        C.check(a.suffix in ('','_02','_03','_04','_05','_06','_07'),'Explicit fixture revision suffix required')
        print(json.dumps(task(a.mode,a.finalize_existing,a.suffix)))

if __name__=='__main__':main()
