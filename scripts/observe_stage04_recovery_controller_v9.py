"""Read-only retained-handle observer; missing observation never means success.

Must bind the actual Scheduler controller while it is live. Does not own a job,
request termination rights, launch science, change files in old attempts, or
replace ordinary native receipts. If this observer is interrupted, final
controller outcome remains UNKNOWN until actual independent evidence exists.
"""
import argparse, json, os, time
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v9 as S

def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--observer-runtime');a=p.parse_args();runtime=Path(a.runtime)
    C.check(runtime.is_relative_to(S.RUNTIME),'Wrong observer runtime role')
    deadline=time.monotonic()+15
    while not (runtime/'controller_binding.json').exists() and time.monotonic()<deadline:time.sleep(.1)
    actor=None
    if a.observer_runtime:
        observer_runtime=Path(a.observer_runtime);C.check(observer_runtime.is_relative_to(S.RUNTIME/'observers'),'Wrong durable observer role')
        start=C.load(observer_runtime/'task_start.json');actor=S.process_identity(os.getpid())
        C.check(start['engine_pid']==actor['pid'] and actor['executable'].lower()==str(S.PYTHONW).lower(),
          'Actual direct Scheduler observer identity differs')
        actor={'actual_process':actor,'scheduler_instance_guid':start['instance_guid'],'definition_sha256':start['definition_sha256'],
          'runtime':str(observer_runtime),'lifetime':'MANUAL_ZERO_TRIGGER_TASK_DIRECT_LONG_LIVED_READ_ONLY_OBSERVER'}
    binding=C.load(runtime/'controller_binding.json');expected=binding['controller'];h=S.process_handle(expected['pid'])
    C.check(h is not None,'Actual controller already absent; independent exit observation cannot be invented')
    try:
        first=S.handle_identity(h,expected['pid'])
        C.check(first['creation_filetime']==expected['creation_filetime'] and first['state']=='RUNNING','Controller identity reused/not live')
        C.atomic(runtime/'independent_controller_observer_binding.json',{'utc':C.now(),'actual_controller':first,
          'read_handle_access':1052672,'termination_rights':False,'source_sha256':C.digest(__file__),'actual_scheduler_observer':actor})
        while S.J.wait(h,1000)==258:pass
        actual=S.handle_identity(h,expected['pid'],first['executable'])
        C.atomic(runtime/'independent_controller_exit.json',{'utc':C.now(),'status':'ACTUAL_BOUND_CONTROLLER_EXIT_OBSERVED',
          'process':actual,'binding_sha256':C.digest(runtime/'independent_controller_observer_binding.json'),
          'scientific_validation':'NOT_PERFORMED_BY_OBSERVER','cause':'NOT_ESTABLISHED'})
        print(json.dumps({'status':'ACTUAL_BOUND_CONTROLLER_EXIT_OBSERVED','exit_code':actual['actual_exit_code']}))
    finally:S.J.close(h)

if __name__=='__main__':main()
