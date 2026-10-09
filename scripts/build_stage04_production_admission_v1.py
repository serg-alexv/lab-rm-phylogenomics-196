"""Hash-guarded production-only delta from the unchanged tested V10 sources."""
import json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

NAME='stage04_recovery_controller_v10_admission_v1.py'
CHECK='stage04_recovery_validate_v10_admission_v1.py'
FREEZE='host_inference_stage04_recovery_v10_admission_v1_freeze.json'

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock)
        snapshot=C.load(S.ROOT/'config/host_inference_stage04_recovery_v10_preparation_snapshot_0002.json')
        for key,sha in snapshot['source_sha256'].items():C.check(C.digest(S.ROOT/key.split(':',1)[1])==sha,'Tested V10 source changed')
        certificate=S.REPORT/'scheduler_fixture.json'
        C.check(C.digest(certificate)=='ce77c4ce4882aa5c1d16bb69967d891c20b9625ba80c97924a7ecf14d1d55470','Completed fixture certificate not preserved')
        patches=[];outputs={}
        def make(original,destination,changes):
            source=(S.ROOT/'scripts'/original).read_text(encoding='utf-8');text=source
            for old,new in changes:
                count=text.count(old);C.check(count>0,'Expected guarded delta absent: '+old[:80]);text=text.replace(old,new)
                patches.append({'source':original,'destination':destination,'old_fragment':old,'new_fragment':new,'occurrences':count})
            path=S.ROOT/'scripts'/destination;C.check(not path.exists(),'New delta source collision; choose explicit next revision')
            path.write_text(text,encoding='utf-8',newline='\n');outputs[destination]=C.digest(path)
        common=[('host_inference_stage04_recovery_v10_freeze.json',FREEZE)]
        make('stage04_recovery_controller_v10.py',NAME,[
          ('"""The actual long-lived Scheduler action;', '"""Production-only admission revision1; unchanged tested V10 lifetime mechanism.\n\nThe actual long-lived Scheduler action;'),
          ('import stage04_recovery_outbox_v10 as Q','import stage04_recovery_outbox_v10 as Q\nimport stage04_production_admission_policy_v1 as A'),
          *common,('stage04_recovery_validate_v10.py',CHECK),
          ("'old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY'}","'old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY',\n      'static_controls_policy_sha256':proposal['production_admission_policy_sha256']}"),
          ("verify_artifacts(required);S.pins()","verify_artifacts(required);S.pins();A.validate_policy(proposal)"),
          ("'Production configuration differs')","'Production configuration differs')\n    C.check(config.get('production_admission_revision')=='V10_PRODUCTION_ADMISSION_V1','Missing explicit production-only admission revision')\n    A.record_compatibility(isolation,proposal,runtime/'outer_job_compatibility.json',runtime/'isolation.json')"),
          ("'fresh_exclusive_boundary_sha256':C.digest(runtime/'independent_current_boundary.json'),","'fresh_exclusive_boundary_sha256':C.digest(runtime/'independent_current_boundary.json'),\n      'production_admission_revision':'V10_PRODUCTION_ADMISSION_V1',\n      'production_admission_policy_sha256':proposal['production_admission_policy_sha256'],\n      'outer_job_compatibility_sha256':C.digest(runtime/'outer_job_compatibility.json'),"),
          ('admission(scope)\n        before=',"admission(scope)\n        A.record_compatibility(A.actual_outer_observation(),proposal,scope/'outer_job_compatibility.json')\n        before="),
          ("mode in ('fixture','production')","mode=='production'")])
        start="    ps=\"$ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process"
        original=(S.ROOT/'scripts/stage04_recovery_validate_v10.py').read_text();left=original.index(start);right=original.index("    C.check(all(r['ProcessId']==owner['pid']",left)
        old=original[left:right]
        replacement="    inventory=A.fresh_runner_inventory()\n    candidates=inventory['matching_scientific_candidates']\n"
        make('stage04_recovery_validate_v10.py',CHECK,[
          ('import stage04_recovery_support_v10 as S','import stage04_recovery_support_v10 as S\nimport stage04_production_admission_policy_v1 as A'),
          *common,('import stage04_recovery_controller_v10 as P','import stage04_recovery_controller_v10_admission_v1 as P'),
          (old,replacement),('stage04_recovery_controller_v10.py',NAME),
          ("'negative_history_certificate_sha256':C.digest(S.NEGATIVE),'live_runner_inventory':candidates,","'negative_history_certificate_sha256':C.digest(S.NEGATIVE),'live_runner_inventory':candidates,\n      'fresh_positive_platform_service_roles':inventory['positive_platform_service_roles'],"),
          ("'old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY'},","'old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY',\n        'static_controls_policy_sha256':proposal['production_admission_policy_sha256']},"),
          ("stable=runtime/'analyses'/name/'attempt_0001'","C.check(freeze['production_admission_revision']=='V10_PRODUCTION_ADMISSION_V1' and\n      freeze['production_admission_policy_sha256']==proposal['production_admission_policy_sha256'] and\n      freeze['outer_job_compatibility_sha256']==C.digest(runtime/'outer_job_compatibility.json'),'Explicit admission revision/receipt differs')\n    A.verify_compatibility_receipt(runtime/'outer_job_compatibility.json',proposal,binding['controller'])\n    A.verify_compatibility_receipt(runtime/'analyses'/name/'outer_job_compatibility.json',proposal,binding['controller'])\n    stable=runtime/'analyses'/name/'attempt_0001'")])
        make('final_check_stage04_recovery_v10.py','final_check_stage04_recovery_v10_admission_v1.py',[
          ('import stage04_recovery_controller_v10 as P','import stage04_recovery_controller_v10_admission_v1 as P\nimport stage04_production_admission_policy_v1 as A'),
          ('stage04_recovery_validate_v10.py',CHECK),
          ("actual=observed['process'];owner=binding['controller']","actual=observed['process'];owner=binding['controller']\n        C.check(freeze['production_admission_revision']=='V10_PRODUCTION_ADMISSION_V1' and freeze['outer_job_compatibility_sha256']==C.digest(runtime/'outer_job_compatibility.json'),'Final explicit outer-policy receipt differs')\n        A.verify_compatibility_receipt(runtime/'outer_job_compatibility.json',proposal,owner)"),
          ("S.scope_binding(name);S.original_freeze_fields(freeze);","A.verify_compatibility_receipt(runtime/'analyses'/name/'outer_job_compatibility.json',proposal,owner)\n            S.scope_binding(name);S.original_freeze_fields(freeze);"),
          ("'actual_final_task_results':tasks,","'actual_final_task_results':tasks,'production_admission_revision':'V10_PRODUCTION_ADMISSION_V1',\n          'outer_job_compatibility_sha256':C.digest(runtime/'outer_job_compatibility.json'),")])
        make('check_stage04_recovery_acceptance_v10.py','check_stage04_recovery_acceptance_v10_admission_v1.py',[
          ('import stage04_recovery_controller_v10 as P','import stage04_recovery_controller_v10_admission_v1 as P')])
        make('activate_stage04_recovery_production_v10.ps1','activate_stage04_recovery_production_v10_admission_v1.ps1',[
          ('check_stage04_recovery_acceptance_v10.py','check_stage04_recovery_acceptance_v10_admission_v1.py')])
        note=S.ROOT/'.work/host_review/PARENT_V10_MINIMAL_ADMISSION_POLICY_NOTE.md';C.check(note.exists(),'READY parent policy note missing')
        policy={'schema':'V10_PRODUCTION_ONLY_ADMISSION_POLICY_V1','completed_lifetime_fixture_sha256':C.digest(certificate),
          'tested_preparation_sha256':'4343339391306ddfde6eedae0337b4d6b75bf22eeb6759967e0c091a8d63b222',
          'reviewed_static_outer_controls':dict.fromkeys(['limit_flags','process_committed_cap_bytes','aggregate_job_committed_cap_bytes','affinity_mask'],0),
          'false_outer_job':'HONEST_NO_OUTER_OBSERVATION_INNER_CONTROLS_STILL_REQUIRED','anonymous_outer_owner':'NOT_IDENTIFIED',
          'platform_service_exception':'FRESH_BRACKETED_EXACT_WSLService_LOCALSystem_RUNNING_SAME_PID_CIM_CREATION_CANONICAL_CONFIGURED_BINARY_ONLY',
          'other_unreadable_candidates':'FAIL_CLOSED','parent_policy_note_sha256':C.digest(note),
          'native_policy':'UNCHANGED_3GIB_PROCESS_AND_AGGREGATE_COMMITTED_MASK5_TWO_THREADS_WINDOWS_AVAILABLE4_5GIB_PHYSICAL_DISK5GIB'}
        path=S.ROOT/'config/host_inference_stage04_production_admission_policy_v1.json';C.check(not path.exists(),'Policy immutable; new version required')
        C.atomic(path,policy)
        C.atomic(S.REPORT/'production_admission_v1_build.json',{'utc':C.now(),'status':'PRODUCTION_ONLY_UNADOPTED_DELTA_FROM_UNCHANGED_TESTED_V10',
          'preserved_tested_source_sha256':snapshot['source_sha256'],'completed_fixture_sha256':C.digest(certificate),
          'generated_source_sha256':outputs,'exact_text_changes':patches,'policy_config_sha256':C.digest(path),
          'parent_policy_note_sha256':C.digest(note),'scientific_jobs':0,'old_suites_repeated':0,'lifetime_fixture_repeated':False})
        print(json.dumps({'status':'PRODUCTION_ONLY_DELTA_BUILT_NOT_ADOPTED','sources':outputs,'policy_sha256':C.digest(path)}))

if __name__=='__main__':main()
