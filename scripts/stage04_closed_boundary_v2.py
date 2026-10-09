"""Fail-closed post-run gate. No science launch, retry, adoption or exit repair.

Unknown process absence is an observation only. Ordinary native receipts must
exist independently and bind actual launch/exit/job closure for every attempt.
The separate retained controller observer is supplementary process evidence;
it never substitutes for native JobObject closure. Publication callers must
also acquire the genuine shared C workflow byte lock before repository writes.
"""
from pathlib import Path
import argparse,json,os
import stage04_controller as C
import stage04_process_observation_v2 as O
import stage04_windows_validate_v6 as V

ROOT=V.ROOT;HISTORY=V.HISTORY
CONTROLLER_PID=8264
CONTROLLER_CREATION=134359651662914448
CONTROLLER_EXIT=HISTORY/'.work/stage04_controller_exit_observer_v2/exit.json'
CAP=3221225472

def check_ordinary_exit(launch_path,expected_argv,tool_sha):
    launch_path=Path(launch_path);exit_path=launch_path.parent/'exit.json'
    C.check(exit_path.is_file(),'UNRESOLVED_MISSING_ORDINARY_NATIVE_EXIT_NO_RETRY_AUTHORIZATION')
    launch=C.load(launch_path);exited=C.load(exit_path)
    C.check(type(exited.get('exit_code')) is int and 0<=exited['exit_code']<=0xffffffff,
            'UNRESOLVED_UNKNOWN_OR_NONINTEGER_EXIT_CODE_NO_RETRY_AUTHORIZATION')
    C.check(launch['argv']==exited['argv']==expected_argv,'Ordinary exact native argv differs')
    C.check(type(launch['child_pid']) is int and launch['child_pid']>0
            and launch['child_pid']==exited['child_pid']
            and type(launch['child_creation_filetime']) is int and launch['child_creation_filetime']>0
            and launch['child_creation_filetime']==exited['creation_filetime']==exited['child_creation_filetime'],
            'Ordinary launch/exit exact process identity differs')
    C.check(exited['actual_launch_receipt_sha256']==C.digest(launch_path),'Ordinary exit lacks actual launch hash binding')
    C.check(exited['process_exited'] is True and type(exited['job_active_processes']) is int
            and exited['job_active_processes']==0 and exited['actual_job_process_ids']==[]
            and type(exited['exit_filetime']) is int and exited['exit_filetime']>=launch['child_creation_filetime'],
            'UNRESOLVED_NATIVE_OR_JOB_DESCENDANT_CLOSURE_NO_RETRY_AUTHORIZATION')
    for record in (launch,exited):
        C.check(record['job_bound_before_resume'] is True
                and record['memory_kind']=='WINDOWS_COMMITTED_MEMORY_NOT_LINUX_RLIMIT_AS'
                and record['process_committed_memory_cap_bytes']==record['aggregate_job_committed_memory_cap_bytes']==CAP
                and record['job_limit_flags']==0x2310 and record['kill_child_job_on_owner_handle_close'] is True
                and type(record['affinity_mask']) is int and record['affinity_mask'].bit_count()==2
                and record['allowed_logical_processors']==2 and record['actual_executable_sha256']==tool_sha,
                'Ordinary native resource/tool identity differs')
    return {'launch_sha256':C.digest(launch_path),'exit_sha256':C.digest(exit_path),
            'exit_code':exited['exit_code'],'child_pid':launch['child_pid'],
            'creation_filetime':launch['child_creation_filetime']}

def require_completed_boundary():
    C.check(os.name=='nt' and Path.cwd().resolve()==ROOT,'Exact WD G Windows post-run boundary required')
    controller=O.observe(CONTROLLER_PID,CONTROLLER_CREATION)
    C.check(controller['state']!='ACTUAL_BOUND_PROCESS_RUNNING','ORIGINAL_CONTROLLER_STILL_LIVE_NO_ADOPTION_OR_PUBLICATION')
    C.check(CONTROLLER_EXIT.is_file(),'UNRESOLVED_MISSING_ACTUAL_CONTROLLER_EXIT_OBSERVATION')
    observed=C.load(CONTROLLER_EXIT);row=observed['actual_process_observation']
    C.check(observed['target_pid']==row['pid']==CONTROLLER_PID
            and observed['target_creation_filetime']==row['creation_filetime']==CONTROLLER_CREATION
            and row['state']=='ACTUAL_BOUND_PROCESS_EXIT_OBSERVED' and row['wait_result']==0
            and type(row['exit_code']) is int and row['exit_code']==0
            and row['exit_filetime']>=CONTROLLER_CREATION,
            'UNRESOLVED_OR_FAILED_ACTUAL_ORIGINAL_CONTROLLER_EXIT')
    C.check(observed['job_handle_owned'] is False and observed['termination_right_requested'] is False
            and observed['handle_access_mask']==O.ACCESS and observed['scientific_jobs_launched']==0
            and observed['job_closure']=='NOT_OBSERVED_BY_THIS_PROCESS','Read-only observer scope differs')
    freeze=C.load(V.INPUT/'inference_freeze.json')
    C.check(observed['inference_freeze_sha256']==C.digest(V.INPUT/'inference_freeze.json'),'Controller observation binds another native freeze')
    for name,digest in observed['source_sha256'].items():C.check(C.digest(ROOT/name)==digest,'Retained controller observer source changed')
    for name,digest in freeze['code_sha256'].items():C.check(C.digest(ROOT/name)==digest,'Adopted native source changed')
    results=[]
    for name in V.NAMES:
        directory=V.INPUT/'analyses'/name/'iqtree'
        C.check((directory/'tree_complete.json').is_file(),'Actual native scope incomplete; no recovery attempted')
        proof=C.load(directory/'tree_complete.json');attempts=sorted(directory.glob('attempt_*/launch.json'))
        C.check(attempts,'Native completed scope lacks actual attempts')
        successful=[]
        for path in attempts:
            launch=C.load(path);native=O.observe(launch['child_pid'],launch['child_creation_filetime'])
            C.check(native['state']!='ACTUAL_BOUND_PROCESS_RUNNING','ACTUAL_NATIVE_PROCESS_STILL_LIVE_NO_DUPLICATE')
            closed=check_ordinary_exit(path,V.expected_argv(freeze['executable'],name),freeze['tool_identity']['executable_sha256'])
            if closed['exit_code']==0:successful.append(path.parent.name)
            results.append({'analysis':name,'attempt':path.parent.name,**closed,'current_process_observation':native})
        C.check(successful==[proof['attempt']],'Exactly one ordinary actual successful attempt required')
    certificate=ROOT/'.work/stage04_final_validation_windows_v6/validation_summary.json'
    summary=V.INPUT/'phylogeny_summary.json'
    value=C.load(certificate);complete=C.load(summary)
    C.check(value['status']=='PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY'
            and value['analyses_verified']==4 and value['primary_tip_ids']==196
            and complete['execution']=='ALL_PRIMARY_AND_SENSITIVITY_INFERENCES_COMPLETED'
            and complete['independent_final_validation_sha256']==C.digest(certificate),
            'Actual four-tree completed independent certificate required')
    return {'status':'PASS_ACTUAL_POSTRUN_CONTROLLER_AND_ALL_ORDINARY_NATIVE_ATTEMPTS_CLOSED',
            'utc':C.now(),'controller_exit_observation_sha256':C.digest(CONTROLLER_EXIT),
            'native_attempts':results,'inference_freeze_sha256':C.digest(V.INPUT/'inference_freeze.json'),
            'independent_native_certificate_sha256':C.digest(certificate),
            'source_sha256':C.digest(__file__),'biological_jobs_launched':0,
            'missing_exit_repair':'FORBIDDEN_MISSING_REMAINS_UNRESOLVED',
            'writer_lock':'CALLER_MUST_HOLD_SHARED_C_BYTE_LOCK_BEFORE_WRITES'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inspect',action='store_true',required=True)
    parser.parse_args()
    # This command is read-only, with no waiter, output files or retry path.
    try:value=require_completed_boundary()
    except (ValueError,FileNotFoundError) as error:
        value={'utc':C.now(),'status':'BLOCKED_POSTRUN_BOUNDARY_NOT_ESTABLISHED','reason':str(error),
               'biological_jobs_launched':0,'ordinary_exit_repaired':False}
        print(json.dumps(value));raise SystemExit(2)
    print(json.dumps(value))

if __name__=='__main__':main()
