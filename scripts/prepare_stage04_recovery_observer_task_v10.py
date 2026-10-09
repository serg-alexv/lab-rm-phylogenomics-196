"""Register direct read-only exit observer via the exact zero-trigger mechanism."""
import argparse, json, shutil, subprocess, uuid
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

def main():
    p=argparse.ArgumentParser();p.add_argument('--target-config',required=True);a=p.parse_args()
    with C.WorkflowLock(S.LOCK):
        config=C.load(a.target_config);target=Path(config['runtime']);C.check(target.is_relative_to(S.RUNTIME),'Observer target not production/fixture C runtime')
        name='LAB_RM_Stage04_V10_readonly_observer_'+uuid.uuid4().hex[:12];runtime=S.RUNTIME/'observers'/name;runtime.mkdir(parents=True,exist_ok=False)
        sid=S.command(['powershell.exe','-NoProfile','-NonInteractive','-Command','[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value']).decode().strip()
        argv=['-u',str(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py'),'--runtime',str(target),'--observer-runtime',str(runtime)]
        request={'protocol':'V10_MANUAL_UNIQUE_ONESHOT_DIRECT_CONTROLLER','mode':'observer','task_name':name,'sid':sid,
          'executable':str(S.PYTHONW),'executable_sha256':C.digest(S.PYTHONW),'argv':argv,'arguments':subprocess.list2cmdline(argv),'cwd':str(S.ROOT),
          'runtime':str(runtime),'target_runtime':str(target),'target_task_name':config['task_name'],
          'xml_path':str(runtime/'task_definition.xml'),'query_path':str(runtime/'task_query.json'),'start_path':str(runtime/'task_start.json')}
        path=runtime/'task_request.json';C.atomic(path,request)
        for script in ['register_stage04_recovery_task_v10.ps1','query_stage04_recovery_task_v10.ps1']:
            S.command(['powershell.exe','-NoProfile','-NonInteractive','-File',str(S.ROOT/'scripts'/script),'-Request',str(path)])
        request['xml_path']=str(runtime/'actual_task_definition.xml');request['query_path']=str(runtime/'actual_task_query.json')
        query=C.load(request['query_path'])
        C.check(query['sid']==sid and query['logon_type']==3 and query['run_level']==0 and query['triggers_count']==0 and query['restart_count']==0 and
          query['multiple_instances']==2 and query['execution_time_limit']=='PT0S' and query['executable']==request['executable'] and
          query['arguments']==request['arguments'] and query['cwd']==request['cwd'],'Read-only observer actual task differs')
        request['definition_sha256']=C.digest(request['xml_path']);request['query_sha256']=C.digest(request['query_path']);C.atomic(path,request)
        report=S.REPORT/'observer_tasks'/name;report.mkdir(parents=True,exist_ok=False)
        for src,dst in [(path,'request.json'),(Path(request['xml_path']),'definition.xml'),(Path(request['query_path']),'query.json')]:shutil.copy2(src,report/dst)
        print(json.dumps({'task_name':name,'request':str(path),'target_runtime':str(target),'definition_sha256':request['definition_sha256']}))

if __name__=='__main__':main()
