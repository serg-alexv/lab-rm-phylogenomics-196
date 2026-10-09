"""Validate the actual120s fixture AFTER independent original-CLI-exit proof.

Do not wait in the original CLI for completion. Parent lifetime evidence is
separate from acceptance; ordinary actual exit/empty-job/task results are required.
"""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

PARENT=S.ROOT/'.work/host_review/PARENT_RECOVERY_V10_ORIGINAL_CLI_EXIT_FIXTURE.json'

def filetime_utc(value):
    return int((datetime.fromisoformat(value.replace('Z','+00:00'))-datetime(1601,1,1,tzinfo=timezone.utc)).total_seconds()*10000000)

def validate(config_path,parent_path=PARENT):
    config=C.load(config_path);runtime=Path(config['runtime'])
    C.check(config['mode']=='fixture' and runtime.is_relative_to(S.RUNTIME/'fixture'),'Only exact synthetic fixture role allowed')
    before=C.load(runtime/'before_original_cli_exit_handoff.json');parent=C.load(parent_path)
    C.check(Path(parent_path)==PARENT and parent['schema']=='PARENT_V10_ORIGINAL_CLI_EXIT_LIFETIME_EVIDENCE' and
      parent['reviewer']=='INDEPENDENT_PARENT' and parent['before_handoff_sha256']==C.digest(runtime/'before_original_cli_exit_handoff.json'),
      'Actual hash-bound independent parent original-CLI proof required')
    cli=parent['original_cli_exit'];expected=before['original_cli_before_natural_exit']
    C.check(cli['pid']==expected['pid']==15584 and cli['creation_filetime']==expected['creation_filetime']==134359775147405364 and
      cli['state']=='EXITED' and cli['actual_exit_code']==0 and cli['exit_filetime']>cli['creation_filetime'],
      'Real original CLI exact creation/ordinary natural exit0 evidence missing')
    C.check(S.process_identity(15584,134359775147405364)['state'] in ('EXITED','ABSENT_WIN32_ERROR_INVALID_PARAMETER','PID_REUSED_DIFFERENT_CREATION'),
      'Original CLI remains live; do not wait for final fixture in that CLI')
    for name in ('controller','native','grandchild'):
        row=parent[name+'_after_cli_exit'];old=before[name]
        C.check(row['pid']==old['pid'] and row['creation_filetime']==old['creation_filetime'] and row['state']=='RUNNING',
          'Parent after-exit process identity differs: '+name)
    first=parent['first_after_cli_exit_tick'];later=parent['later_after_cli_exit_tick']
    C.check(filetime_utc(first['utc'])>cli['exit_filetime'] and filetime_utc(later['utc'])>cli['exit_filetime'] and
      first['pid']==later['pid']==before['native']['pid'] and later['tick']>first['tick']>=before['later_tick']['tick'],
      'Same synthetic child must actually advance after original CLI exit')
    binding=C.load(runtime/'controller_binding.json');launch=C.load(runtime/'native_attempt/launch.json');native=C.load(runtime/'native_attempt/exit.json')
    observed=C.load(runtime/'independent_controller_exit.json');observer_binding=C.load(runtime/'independent_controller_observer_binding.json')
    closed=C.load(runtime/'controller_closure.json');actual=observed['process']
    C.check(binding['controller']['pid']==actual['pid']==before['controller']['pid'] and
      binding['controller']['creation_filetime']==actual['creation_filetime']==before['controller']['creation_filetime'] and
      actual['actual_exit_code']==0 and actual['state']=='EXITED' and actual['exit_filetime']>actual['creation_filetime'] and
      observed['binding_sha256']==C.digest(runtime/'independent_controller_observer_binding.json') and
      observer_binding['controller_binding_sha256']==C.digest(runtime/'controller_binding.json'), 'Actual independently retained controller exit0 binding differs')
    C.check(native['receipt_kind']=='ORDINARY_ACTUAL_NATIVE_EXIT_AND_EMPTY_OWNED_JOB' and native['exit_code']==0 and
      native['child_pid']==launch['child_pid']==before['native']['pid'] and
      native['child_creation_filetime']==launch['child_creation_filetime']==before['native']['creation_filetime'] and
      native['job_active_processes']==0 and native['actual_job_process_ids']==[] and native['job_total_processes']>=2 and
      native['role']=='SYNTHETIC_FIXTURE' and native['wall_deadline_seconds']==180 and native['process_committed_memory_cap_bytes']==128*1024**2 and
      native['actual_launch_receipt_sha256']==C.digest(runtime/'native_attempt/launch.json'), 'Actual synthetic child/grandchild ordinary exit0 and empty job required')
    C.check(closed['status']=='ORDINARY_CONTROLLER_SCOPE_CLOSURE' and closed['mode']=='fixture' and closed['scientific_jobs_completed']==0 and
      closed['controller']==binding['controller'] and closed['native_jobs_actual_empty'] is True and
      C.load(runtime/'fixture_child_complete.json')['status']=='SYNTHETIC_CHILD_AND_GRANDCHILD_EXIT0','Actual synthetic controller/tree closure invalid')
    source_binding=S.source_snapshot_binding(runtime)
    C.check(source_binding==C.load(runtime/'actual_candidate_source_binding.json')==before['candidate_source_binding'],
      'Fixture exact pre-start source snapshot drifted')
    observer=observer_binding['actual_scheduler_observer'];observer_runtime=Path(observer['runtime']);observer_request=C.load(observer_runtime/'task_request.json')
    C.check(observer_binding['source_sha256']==C.digest(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py') and
      observer['actual_live_scheduler_binding']['actual_request_sha256']==C.digest(observer_runtime/'task_request.json') and
      observer['definition_sha256']==observer_request['definition_sha256'],'Actual separate observer source/request/definition changed')
    request=C.load(runtime/'task_request.json');tasks=S.closed_scheduler_tasks(runtime,[request,observer_request])
    terminal=C.load(runtime/'terminal_publication.json');observation=Path(terminal['observation_path']);measurement=C.load(observation)
    token=observation.stem;publisher=C.load(runtime/'publishers'/token/'exit.json')
    C.check(terminal['status']=='PUBLICATION_UNVERIFIED_FAILED' and terminal['publisher_exit_code']==23 and
      terminal['actual_empty_publisher_job'] is True and terminal['terminal'] is True and terminal['remote_bytes_verified'] is False and
      terminal['observation_sha256']==C.digest(observation) and measurement['terminal'] is True and
      measurement['measurement']['exit_code']==0 and publisher['exit_code']==23 and publisher['job_active_processes']==0 and
      publisher['actual_job_process_ids']==[], 'Contained exact terminal observation/publication failure evidence missing')
    files={'data:'+Path(config_path).relative_to(S.ROOT).as_posix():C.digest(config_path),
      'data:'+PARENT.relative_to(S.ROOT).as_posix():C.digest(PARENT)}
    for directory in (runtime,observer_runtime):
        for path in directory.rglob('*'):
            if path.is_file():files['historical:'+path.relative_to(S.HISTORY).as_posix()]=C.digest(path)
    return {'schema':'V10_ACTUAL_SCHEDULER_ORIGINAL_CLI_EXIT_SYNTHETIC_LIFETIME_FIXTURE','utc':C.now(),
      'status':'PASS_THIS_ORIGINAL_CLI_EXIT_SAME_CREATIONS_ADVANCED_AND_ACTUAL_EMPTY_JOB_CONTROLLER_EXIT0',
      'biological_jobs':0,'parent_original_cli_proof_sha256':C.digest(PARENT),'actual_controller_bound_exit':actual,
      'actual_native_exit':native,'scheduler_isolation':C.load(runtime/'isolation.json'),'actual_closed_task_results':tasks,
      'actual_source_snapshot':source_binding,'publication_failure':terminal,'file_sha256':files,
      'limitation':'Proves this particular original CLI exit survival; anonymous outer-job ownership/universal lifetime and scientific acceptance are not established.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args()
    with C.WorkflowLock(S.LOCK) as lock:
        S.pins();S.held_lock_matches_negative(lock)
        value=validate(Path(a.config).resolve());C.atomic(S.REPORT/'scheduler_fixture.json',value)
        print(json.dumps({'status':value['status'],'fixture_sha256':C.digest(S.REPORT/'scheduler_fixture.json')}))

if __name__=='__main__':main()
