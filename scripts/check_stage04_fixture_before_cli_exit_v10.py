"""Bound live handoff only; parent performs post-original-CLI exit/final checks."""
import argparse, json, time
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();config=C.load(a.config);runtime=Path(config['runtime'])
    deadline=time.monotonic()+15
    needed=['controller_binding.json','native_attempt/launch.json','fixture_grandchild.json','fixture_ticks.json',
      'independent_controller_observer_binding.json']
    while not all((runtime/n).exists() for n in needed) and time.monotonic()<deadline:time.sleep(.1)
    controller=C.load(runtime/'controller_binding.json');launch=C.load(runtime/'native_attempt/launch.json')
    grandchild=C.load(runtime/'fixture_grandchild.json');first=C.load(runtime/'fixture_ticks.json');time.sleep(3);later=C.load(runtime/'fixture_ticks.json')
    states=[S.process_identity(x['pid'],x['creation_filetime']) for x in [controller['controller'],grandchild]]
    native=S.process_identity(launch['child_pid'],launch['child_creation_filetime'])
    original_cli=S.process_identity(15584,134359775147405364)
    C.check(original_cli['state']=='RUNNING','Original CLI exact creation is not live; this handoff cannot prove its natural exit')
    C.check(all(r['state']=='RUNNING' for r in states+[native]) and later['tick']>first['tick'],'Exact fixture tree not advancing/live before original CLI exit')
    value={'utc':C.now(),'status':'LIVE_BEFORE_ORIGINAL_CLI_EXIT_POST_EXIT_PROOF_PENDING','scientific_jobs':0,
      'original_cli_before_natural_exit':original_cli,'controller':states[0],'native':native,'grandchild':states[1],'first_tick':first,'later_tick':later,
      'candidate_source_binding':S.source_snapshot_binding(runtime),
      'independent_controller_observer_binding':C.load(runtime/'independent_controller_observer_binding.json'),
      'actual_live_scheduler_binding':C.load(runtime/'actual_live_scheduler_binding.json'),'outer_job':C.load(runtime/'isolation.json'),
      'config_sha256':C.digest(a.config),'core_source_sha256':{n:C.digest(S.ROOT/'scripts'/n) for n in ['stage04_recovery_controller_v10.py',
        'stage04_windows_job_v10.py','stage04_recovery_support_v10.py','stage04_recovery_fixture_v10.py','stage04_recovery_outbox_v10.py',
        'stage04_recovery_publisher_v10.py']},'required_parent_followup':'Retain actual original CLI creation/exit handle; verify SAME three process creations and advancing ticks AFTER natural CLI exit, then actual native/controller exit and empty owned job. No production acceptance from this live receipt.'}
    C.atomic(runtime/'before_original_cli_exit_handoff.json',value);C.atomic(S.REPORT/'before_original_cli_exit_handoff.json',value)
    print(json.dumps({'status':value['status'],'runtime':str(runtime),'controller_pid':states[0]['pid'],'native_pid':native['pid'],
      'grandchild_pid':states[1]['pid'],'ticks':[first['tick'],later['tick']]}))

if __name__=='__main__':main()
