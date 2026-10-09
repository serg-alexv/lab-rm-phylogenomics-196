"""Independent read-only Scheduler fixture observer, bound retained handle.

Run from a SECOND tool invocation after the starter invocation returned. It
observes advancing child state and real controller exit; absence is not exit.
"""
import argparse, hashlib, json, os, time
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v9 as S
import stage04_windows_job_v6 as J

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);args=p.parse_args()
    config=C.load(args.config);runtime=Path(config['runtime'])
    start=C.load(runtime/'task_start.json');request=C.load(runtime/'task_request.json')
    first_utc=C.now();deadline=time.monotonic()+10
    while not (runtime/'controller_binding.json').exists() and time.monotonic()<deadline:time.sleep(.2)
    binding=C.load(runtime/'controller_binding.json');identity=binding['controller'];h=S.process_handle(identity['pid'])
    C.check(h is not None,'Controller absent before independent handle binding; fixture cannot prove exit by absence')
    try:
        actual=S.handle_identity(h,identity['pid']);C.check(actual['creation_filetime']==identity['creation_filetime'] and actual['state']=='RUNNING','Controller identity reused/not live')
        iso=C.load(runtime/'isolation.json');C.check(iso['codex_cli_ancestor'] is False and config['allow_fixture_scheduler_outer_job_observation'] is True,
          'Controller ancestor/synthetic-only observation contract differs')
        C.check(first_utc>start['utc'] and actual['executable'].lower()==str(S.PYTHONW).lower(),'Independent later invocation/task executable not bound')
        flag=__import__('ctypes').wintypes.BOOL();J.ok(S.in_job(h,None,__import__('ctypes').byref(flag)),'Independent controller IsProcessInJob NULL')
        C.check(bool(flag.value)==iso['is_process_in_job_null'],'Independent controller outer-job observation differs')
        C.check(start['engine_pid']==identity['pid'] and binding['scheduler_instance_guid']==start['instance_guid'],
          'Actual Scheduler instance does not bind exact controller')
        a=C.load(runtime/'fixture_ticks.json');launch=C.load(runtime/'native_attempt/launch.json');time.sleep(3)
        b=C.load(runtime/'fixture_ticks.json')
        C.check(b['tick']>a['tick'] and a['pid']==b['pid']==launch['child_pid'],'Fixture did not advance after initiating invocation returned')
        child=S.process_identity(launch['child_pid'],launch['child_creation_filetime'])
        C.check(child['state']=='RUNNING' and child['creation_filetime']==launch['child_creation_filetime'],'Exact child identity no longer live')
        while J.wait(h,500)==258:
            C.check(time.monotonic()<deadline+55,'Controller did not exit within short fixture bound')
        ended=S.handle_identity(h,identity['pid'],actual['executable']);C.check(ended['state']=='EXITED' and ended['actual_exit_code']==0,'Actual controller exit not zero')
        native=C.load(runtime/'native_attempt/exit.json');closure=C.load(runtime/'controller_closure.json')
        C.check(native['exit_code']==0 and native['exit_filetime']>native['child_creation_filetime'] and native['job_active_processes']==0 and
          native['actual_job_process_ids']==[] and native['job_total_processes']>=2,'Actual child/grandchild ordinary exit and empty job required')
        C.check(closure['status']=='ORDINARY_CONTROLLER_SCOPE_CLOSURE' and closure['mode']=='fixture' and closure['native_jobs_actual_empty'] is True and
          closure['scientific_jobs_completed']==0,'Ordinary controller closure invalid')
        publication=C.load(runtime/'outbox_publication_latest.json')
        C.check(publication['publisher_exit_code']==23 and publication['actual_empty_publisher_job'] is True,'Contained failed publisher closure missing')
        C.check(C.digest(request['xml_path'])==request['definition_sha256'],'Fixture task definition changed')
        files={}
        for member in ['actual_task_definition.xml','actual_task_query.json','task_start.json','controller_binding.json','isolation.json','topology.json',
          'native_attempt/launch.json','native_attempt/exit.json','controller_closure.json','fixture_grandchild.json','fixture_publisher_failure.json',
          'outbox_publication_latest.json','publishers/attempt_0001/launch.json','publishers/attempt_0001/exit.json']:
            files['historical:'+str((runtime/member).relative_to(S.HISTORY)).replace('\\','/')]=C.digest(runtime/member)
        value={'schema':'V9_ACTUAL_SCHEDULER_SHORT_SYNTHETIC_LIFETIME_FIXTURE','utc':C.now(),
          'status':'PASS_SHORT_SYNTHETIC_SCHEDULER_LIFETIME_AND_EMPTY_NATIVE_JOB_OUTER_JOB_PARENT_REVIEW_REQUIRED',
          'biological_jobs':0,'independent_observer_pid':os.getpid(),'independent_second_invocation_utc':first_utc,
          'starter_receipt_utc':start['utc'],'first_child_tick':a,'later_child_tick':b,'actual_controller_bound_exit':ended,
          'actual_native_exit':native,'scheduler_isolation':iso,'publication_failure':publication,'file_sha256':files,
          'source_sha256':{('data:scripts/'+n):C.digest(S.ROOT/'scripts'/n) for n in ['stage04_recovery_controller_v9.py','stage04_windows_job_v9.py',
            'stage04_recovery_support_v9.py','stage04_recovery_fixture_v9.py','stage04_recovery_outbox_v9.py','stage04_recovery_publisher_v9.py',
            'register_stage04_recovery_task_v9.ps1','start_stage04_recovery_task_v9.ps1','check_stage04_recovery_fixture_v9.py']},
          'scientific_acceptance':'NOT_ESTABLISHED_BY_SYNTHETIC_FIXTURE'}
        C.atomic(S.REPORT/'scheduler_fixture.json',value)
        print(json.dumps({'status':value['status'],'fixture_sha256':C.digest(S.REPORT/'scheduler_fixture.json'),'controller_actual_exit':ended['actual_exit_code']}))
    finally:J.close(h)

if __name__=='__main__':main()
