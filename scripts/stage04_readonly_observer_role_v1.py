"""Exclude only the accepted live read-only observer, using exact actual identities.

This is a pre-start role guard, not a basename/substring exemption. All other
matching runners remain subject to the owner-only rejection; null command lines
are already rejected by the preserved admission policy.
"""
import ctypes as c,hashlib,json,time
from ctypes import wintypes as t
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_production_admission_policy_v1 as A

def parse_command_line(text):
    C.check(isinstance(text,str) and text,'Unreadable observer command line')
    shell=c.WinDLL('shell32',use_last_error=True)
    parse=S.J.bind(shell,'CommandLineToArgvW',c.POINTER(t.LPWSTR),[t.LPCWSTR,c.POINTER(c.c_int)])
    free=S.J.bind(S.K,'LocalFree',t.HANDLE,[t.HANDLE]);count=c.c_int()
    args=parse(text,c.byref(count));S.J.ok(args,'Actual observed command-line parse')
    try:return [args[i] for i in range(count.value)]
    finally:free(c.cast(args,t.HANDLE))

def check_role(row,argv,request,binding,task,before,after,owner,controller_binding_sha256,request_sha256):
    """Pure joins against evidence collected by fresh permitted native/COM queries."""
    actor=binding['actual_scheduler_observer'];identity=actor['actual_process'];saved=actor['actual_live_scheduler_binding']
    C.check(request['mode']=='observer' and request['protocol']=='V10_MANUAL_UNIQUE_ONESHOT_DIRECT_CONTROLLER' and
      request['executable']==str(S.PYTHONW) and request['argv']==['-u',str(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py'),
      '--runtime',request['target_runtime'],'--observer-runtime',request['runtime']],'Observer is not the exact preserved read-only action')
    C.check(row['ProcessId']==identity['pid']==before['pid']==after['pid'] and
      identity['creation_filetime']==before['creation_filetime']==after['creation_filetime'] and
      before['state']==after['state']=='RUNNING' and before['executable'].casefold()==after['executable'].casefold()==request['executable'].casefold(),
      'Fresh observer native PID/creation/state/image differs')
    C.check(type(row['creation_filetime_microsecond_precision']) is int and
      row['creation_filetime_microsecond_precision']==before['creation_filetime']//10*10,'Observer CIM/native creation join differs')
    C.check(argv==[request['executable'],*request['argv']]==saved['actual_process_argv'],'Observed actual observer argv differs')
    C.check(binding['controller_binding_sha256']==controller_binding_sha256 and
      binding['actual_controller']['pid']==owner['pid'] and binding['actual_controller']['creation_filetime']==owner['creation_filetime'],
      'Observer retains another controller')
    C.check(actor['runtime']==request['runtime'] and actor['definition_sha256']==saved['actual_task_definition_sha256']==request['definition_sha256'] and
      saved['actual_request_sha256']==request_sha256,'Observer request/runtime/definition differs')
    C.check(hashlib.sha256(b'\xff\xfe'+task['xml'].encode('utf-16le')).hexdigest()==request['definition_sha256'],'Fresh actual full observer definition differs')
    runs=task['runs'];matches=[r for r in runs if r['engine_pid']==identity['pid'] and r['instance_guid']==actor['scheduler_instance_guid'] and r['state']==4]
    C.check(len(runs)==len(matches)==1 and saved['actual_live_instance']==matches[0],'Fresh exact observer Scheduler instance differs')
    return {'role':'ACCEPTED_ACTUAL_LIVE_READ_ONLY_OBSERVER_NOT_SCIENTIFIC_RUNNER',
      'pid':before['pid'],'creation_filetime':before['creation_filetime'],'task_name':request['task_name'],
      'actual_argv':argv,'anonymous_outer_owner':'NOT_IDENTIFIED'}

def observer_proof(row,proposal,runtime,owner):
    request=proposal['production_readonly_observer_task'];path=Path(request['runtime'])/'task_request.json'
    C.check(Path(request['target_runtime'])==runtime and C.load(path)==request,'Observer request does not target actual accepted controller')
    bind_path=runtime/'independent_controller_observer_binding.json';deadline=time.monotonic()+10
    while not bind_path.exists() and time.monotonic()<deadline:time.sleep(.1)
    binding=C.load(bind_path);pid=binding['actual_scheduler_observer']['actual_process']['pid']
    before=S.process_identity(pid,binding['actual_scheduler_observer']['actual_process']['creation_filetime'])
    argv=parse_command_line(row['CommandLine'])
    name=request['task_name'];C.check(name.startswith('LAB_RM_Stage04_V10_') and name.replace('_','').isalnum(),'Invalid exact task name')
    query="$ErrorActionPreference='Stop'; $s=New-Object -ComObject Schedule.Service; $s.Connect(); $t=$s.GetFolder('\\').GetTask('"+name+"'); $runs=@($s.GetRunningTasks(1) | Where-Object {$_.Name -eq '"+name+"'} | ForEach-Object {[pscustomobject]@{engine_pid=$_.EnginePID;instance_guid=$_.InstanceGuid;state=$_.State}}); [pscustomobject]@{xml=$t.Xml;runs=$runs} | ConvertTo-Json -Depth 6 -Compress"
    task=json.loads(S.command(['powershell.exe','-NoProfile','-NonInteractive','-Command',query],timeout=20).decode('utf-8-sig'))
    task_path=runtime/'source_gate_readonly_observer_live_task.json';C.atomic(task_path,task)
    after=S.process_identity(pid,before.get('creation_filetime'))
    controller_sha=C.digest(runtime/'controller_binding.json')
    result=check_role(row,argv,request,binding,task,before,after,owner,controller_sha,C.digest(path))
    C.check(binding['source_sha256']==C.digest(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py'),'Actual observer source differs')
    return {**result,'row':row,'native_before':before,'native_after':after,'observer_binding_sha256':C.digest(bind_path),
      'controller_binding_sha256':controller_sha,'actual_task_query_path':str(task_path),'actual_task_query_sha256':C.digest(task_path),
      'observer_request_sha256':C.digest(path),'guard_source_sha256':C.digest(__file__),'utc':C.now()}

def source_inventory(proposal,runtime,owner):
    inventory=A.fresh_runner_inventory();roles=[];retained=[]
    # Persist the actual matching list before classification, including rejection.
    C.atomic(runtime/'source_gate_runner_inventory.json',inventory)
    for row in inventory['matching_scientific_candidates']:
        if row['ProcessId']==owner['pid']:
            retained.append(row)
        else:
            proof=observer_proof(row,proposal,runtime,owner)
            roles.append(proof)
    C.check(len(roles)==1,'Accepted live read-only observer missing/duplicated in actual matching inventory')
    return {**inventory,'matching_scientific_candidates':retained,'fresh_positive_readonly_observer_roles':roles,
      'runner_inventory_sha256':C.digest(runtime/'source_gate_runner_inventory.json')}

def verify_stored_role(current,proposal,runtime):
    C.check(C.digest(runtime/'source_gate_runner_inventory.json')==current['runner_inventory_sha256'],'Original runner inventory changed')
    roles=current['fresh_positive_readonly_observer_roles'];C.check(len(roles)==1,'Exactly one positive observer role required')
    proof=roles[0];query=Path(proof['actual_task_query_path']);bind=runtime/'independent_controller_observer_binding.json'
    C.check(query==runtime/'source_gate_readonly_observer_live_task.json' and C.digest(query)==proof['actual_task_query_sha256'] and
      C.digest(bind)==proof['observer_binding_sha256'] and C.digest(runtime/'controller_binding.json')==proof['controller_binding_sha256'] and
      proof['guard_source_sha256']==C.digest(__file__),'Actual stored observer role evidence/source changed')
    request=proposal['production_readonly_observer_task'];path=Path(request['runtime'])/'task_request.json'
    C.check(C.digest(path)==proof['observer_request_sha256'] and C.load(path)==request,'Exact stored observer request changed')
    result=check_role(proof['row'],proof['actual_argv'],request,C.load(bind),C.load(query),proof['native_before'],proof['native_after'],
      current['controller'],proof['controller_binding_sha256'],proof['observer_request_sha256'])
    C.check(all(proof[k]==v for k,v in result.items()),'Saved observer role decision differs')
    return proof
