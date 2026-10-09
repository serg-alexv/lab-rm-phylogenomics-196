"""Direct target/hash joins and retained per-role outcomes over unchanged role-v1."""
import json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_readonly_observer_role_v1 as B

def direct_joins(proposal,binding,request,actual_executable_sha256,actual_source_sha256):
    target=proposal['production_task'];source=proposal['required_review_artifacts']['data:scripts/observe_stage04_recovery_controller_v10.py']
    fixed=next(x['sha256'] for x in proposal['fixed_external_interpreters'] if x['path']==str(S.PYTHONW))
    C.check(request==proposal['production_readonly_observer_task'] and request['target_runtime']==target['runtime'] and
      request['target_task_name']==target['task_name'],'Read-only observer accepted target/runtime/request differs')
    C.check(binding['controller_config_sha256']==target['config_sha256'] and
      binding['controller_definition_sha256']==target['definition_sha256'],'Read-only observer target config/definition joins differ')
    C.check(actual_executable_sha256==request['executable_sha256']==fixed,'Actual observer executable bytes differ from accepted fixed interpreter')
    C.check(binding['source_sha256']==actual_source_sha256==source,'Actual observer source differs from accepted exact source')
    return {'target_config_sha256':target['config_sha256'],'target_definition_sha256':target['definition_sha256'],
      'actual_observer_executable_sha256':actual_executable_sha256,'actual_observer_source_sha256':actual_source_sha256}

def source_inventory(proposal,runtime,owner):
    inventory=B.A.fresh_runner_inventory();roles=[];retained=[]
    C.atomic(runtime/'source_gate_runner_inventory.json',inventory)
    outcomes={'utc':C.now(),'status':'ROLE_EVALUATION_STARTED_NOT_A_BOUNDARY_PASS','expected_controller':owner,
      'expected_controller_request':proposal['production_task'],'expected_observer_request':proposal['production_readonly_observer_task'],
      'expected_observer_binding_path':str(runtime/'independent_controller_observer_binding.json'),
      'role_guard_v2_source_sha256':C.digest(__file__),'evaluations':[]}
    path=runtime/'source_gate_role_outcomes.json';C.atomic(path,outcomes)
    for row in inventory['matching_scientific_candidates']:
        try:
            if row['ProcessId']==owner['pid']:
                actual=S.process_identity(owner['pid'],owner['creation_filetime']);request=proposal['production_task']
                C.check(actual['state']=='RUNNING' and actual['creation_filetime']==owner['creation_filetime'] and
                  B.parse_command_line(row['CommandLine'])==[request['executable'],*request['argv']] and
                  row['creation_filetime_microsecond_precision']==actual['creation_filetime']//10*10,'Actual controller role/argv/creation differs')
                retained.append(row);role='EXACT_LIVE_ACCEPTED_CONTROLLER'
            else:
                proof=B.observer_proof(row,proposal,runtime,owner);request=proposal['production_readonly_observer_task']
                binding=C.load(runtime/'independent_controller_observer_binding.json')
                joins=direct_joins(proposal,binding,request,C.digest(request['executable']),
                  C.digest(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py'))
                roles.append({**proof,**joins,'role_guard_v2_source_sha256':C.digest(__file__)});role=proof['role']
            outcomes['evaluations'].append({'pid':row['ProcessId'],'status':'PASS_EXACT_ROLE','role':role})
            C.atomic(path,outcomes)
        except BaseException as error:
            outcomes['status']='ROLE_EVALUATION_FAILED_NO_BOUNDARY_CERTIFICATE'
            outcomes['evaluations'].append({'pid':row['ProcessId'],'status':'FAILED_CLOSED','kind':type(error).__name__,'reason':str(error)})
            C.atomic(path,outcomes);raise
    if len(roles)!=1 or len(retained)!=1:
        outcomes.update(status='ROLE_EVALUATION_FAILED_NO_BOUNDARY_CERTIFICATE',reason='Exactly one actual controller and read-only observer required')
        C.atomic(path,outcomes);raise ValueError(outcomes['reason'])
    outcomes['status']='PASS_TWO_EXACT_ROLES_NO_OTHER_MATCHING_RUNNER';C.atomic(path,outcomes)
    return {**inventory,'matching_scientific_candidates':retained,'fresh_positive_readonly_observer_roles':roles,
      'runner_inventory_sha256':C.digest(runtime/'source_gate_runner_inventory.json'),'role_outcomes_sha256':C.digest(path)}

def verify_stored_role(current,proposal,runtime):
    proof=B.verify_stored_role(current,proposal,runtime)
    joins=direct_joins(proposal,C.load(runtime/'independent_controller_observer_binding.json'),proposal['production_readonly_observer_task'],
      C.digest(proposal['production_readonly_observer_task']['executable']),C.digest(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py'))
    C.check(all(proof[k]==v for k,v in joins.items()) and proof['role_guard_v2_source_sha256']==C.digest(__file__),'Direct observer role/hash joins changed')
    path=runtime/'source_gate_role_outcomes.json';outcomes=C.load(path)
    C.check(C.digest(path)==current['role_outcomes_sha256'] and outcomes['status']=='PASS_TWO_EXACT_ROLES_NO_OTHER_MATCHING_RUNNER' and
      outcomes['role_guard_v2_source_sha256']==C.digest(__file__) and outcomes['expected_controller']==current['controller'] and
      outcomes['expected_controller_request']==proposal['production_task'] and outcomes['expected_observer_request']==proposal['production_readonly_observer_task'] and
      len(outcomes['evaluations'])==2 and all(x['status']=='PASS_EXACT_ROLE' for x in outcomes['evaluations']) and
      {x['pid'] for x in outcomes['evaluations']}=={current['controller']['pid'],proof['pid']},'Actual complete per-role outcomes changed/incomplete')
    return proof
