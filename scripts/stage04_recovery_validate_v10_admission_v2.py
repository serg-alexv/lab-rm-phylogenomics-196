"""Independent V10 lifecycle adapter plus unchanged, pinned V6 scientific audit.

V6 audit functions are reused with an explicit new INPUT namespace only. V6
source bytes and all scientific conditions remain unchanged. Negative V6
history is never supplied as a new native exit or successful closure.
"""
import argparse, csv, gzip, hashlib, json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_production_admission_policy_v1 as A
import stage04_readonly_observer_role_v1 as R
import stage04_windows_validate_v6 as V
import supplemental_native_v6_final_check as EXTRA
from stage04_model_cache_evidence_v10 import check_cache_log,check_cache_records

def source_gate():
    S.pins();C.reconcile(S.ROOT)
    # This checker runs in the controller's owned bounded job while the actual
    # Scheduler controller holds the unchanged stable-C byte0 writer lock.
    cfg=C.load(S.ROOT/'config/host_inference_stage04_recovery_v10_production_admission_v2.json');runtime=Path(cfg['runtime'])
    owner=C.load(runtime/'controller_binding.json')['controller'];live=S.process_identity(owner['pid'],owner['creation_filetime'])
    C.check(live['state']=='RUNNING' and live['creation_filetime']==owner['creation_filetime'],'Bound workflow owner not live')
    owner_lock=C.load(runtime/'controller_binding.json')['lock_identity']
    C.check(owner_lock==C.load(S.NEGATIVE)['exclusive_writer_boundary'],'Actual retained lock identity differs from historical boundary')
    # Independent child must encounter the actual held byte0 lock; a path/sentinel is not ownership.
    try:
        acquired=C.WorkflowLock(S.LOCK);acquired.__enter__()
    except ValueError as error:C.check('byte lock is held' in str(error),'Unexpected lock probe error')
    else:
        acquired.__exit__();raise ValueError('Expected exclusive controller lock was not actually held')
    negative=C.load(S.NEGATIVE);reconciled=[]
    from datetime import datetime,timezone
    boundary=int((datetime.fromisoformat(negative['utc'])-datetime(1601,1,1,tzinfo=timezone.utc)).total_seconds()*10000000)
    for prior in negative['recorded_old_process_reconciliation']:
        row=S.process_identity(prior['pid'],prior['recorded_creation_filetime'])
        if prior['recorded_creation_filetime'] is None and row['state']=='RUNNING':
            C.check(prior['state']=='ABSENT_WIN32_ERROR_INVALID_PARAMETER' and row['creation_filetime']>boundary,
              'Unrecorded-token helper identity unresolved; launch blocked')
            row['state']='PID_REUSED_CREATED_AFTER_CERTIFIED_ABSENCE_BOUNDARY'
        C.check(row['state'] in ('ABSENT_WIN32_ERROR_INVALID_PARAMETER','EXITED','PID_REUSED_DIFFERENT_CREATION',
          'PID_REUSED_CREATED_AFTER_CERTIFIED_ABSENCE_BOUNDARY'),'Original recorded process remains live/unresolved')
        reconciled.append({**row,'role':prior['role']})
    proposal=C.load(S.ROOT/'config/host_inference_stage04_recovery_v10_admission_v2_freeze.json')
    abort=C.load(S.REPORT/'production_admission_v1_pre_native_abort.json')
    prior_runtime=Path(proposal['prior_admission_v1_runtime'])
    prior_binding=C.load(prior_runtime/'independent_controller_observer_binding.json')
    prior_instances=[]
    for actor in [abort['actual_controller_exit'],prior_binding['actual_scheduler_observer']['actual_process'],
      {'pid':abort['actual_source_gate_exit']['child_pid'],'creation_filetime':abort['actual_source_gate_exit']['child_creation_filetime']}]:
        actual=S.process_identity(actor['pid'],actor['creation_filetime'])
        C.check(actual['state'] in ('ABSENT_WIN32_ERROR_INVALID_PARAMETER','EXITED','PID_REUSED_DIFFERENT_CREATION'),
          'Prior admission1 recorded instance remains live/unresolved')
        prior_instances.append(actual)
    inventory=R.source_inventory(proposal,runtime,owner)
    candidates=inventory['matching_scientific_candidates']
    C.check(all(r['ProcessId']==owner['pid'] and 'stage04_recovery_controller_v10_admission_v2.py' in r['CommandLine'] for r in candidates),
      'Other matching live scientific runner found; no duplicate launch')
    C.atomic(runtime/'independent_current_boundary.json',{'utc':C.now(),'status':'PASS_EXCLUSIVE_BOUND_OWNER_OLD_INSTANCES_RECONCILED_NO_OTHER_RUNNER',
      'controller':owner,'actual_retained_workflow_lock_identity':owner_lock,
      'negative_history_certificate_sha256':C.digest(S.NEGATIVE),'live_runner_inventory':candidates,
      'fresh_positive_platform_service_roles':inventory['positive_platform_service_roles'],
      'fresh_positive_readonly_observer_roles':inventory['fresh_positive_readonly_observer_roles'],
      'runner_inventory_sha256':inventory['runner_inventory_sha256'],'prior_admission1_instances':prior_instances,
      'recorded_processes':reconciled,'old_ordinary_controller_outcome':'UNKNOWN','old_final_job_closure':'UNKNOWN',
      'unknown_token_rule':'Only actual new creation after certified PID absence may demonstrate reuse; old creation token is never invented',
      'native_jobs_launched_by_checker':0})
    proposal=C.load(S.ROOT/'config/host_inference_stage04_recovery_v10_admission_v2_freeze.json')
    external=proposal['fixed_external_interpreters']
    C.check([r['path'] for r in external]==[str(S.PYTHON),str(S.PYTHONW),str(S.VALIDATOR)],'Fixed external interpreter roles changed')
    for item in external:C.check(C.digest(item['path'])==item['sha256'],'Fixed interpreter on-disk bytes changed')
    for key,sha in proposal['required_review_artifacts'].items():
        role,rel=key.split(':',1);base=S.ROOT if role=='data' else S.HISTORY
        C.check(C.digest(base/rel)==sha,'Proposal source artifact changed: '+key)
    value=V.source_gate();old=C.load(S.OLD/'inference_freeze.json')
    C.check(value==old['source_identity'],'Accepted four matrices/source scopes changed')
    C.check(C.digest(old['executable'])==old['tool_identity']['executable_sha256'],'Official executable changed')
    C.atomic(S.RUNTIME/'independent_source_gate.json',{'utc':C.now(),'status':'PASS_REUSED_ACCEPTED_SOURCES_NO_BIOLOGICAL_RECOMPUTATION',
      'source_identity':value,'original_freeze_sha256':S.FREEZE_SHA})

def audit(name):
    S.pins();C.check(name in S.NAMES,'Unknown analysis')
    freeze=C.load(S.OUT/'inference_freeze.json');runtime=Path(freeze['stable_runtime'])
    original=S.original_freeze_fields(freeze)
    import stage04_recovery_controller_v10_admission_v2 as P
    P.acceptance()  # Independent current source/proposal hashes before output audit.
    C.check(runtime.is_relative_to(S.RUNTIME) and freeze['old_freeze_sha256']==S.FREEZE_SHA and
      freeze['recovery_protocol']=='V10_NEGATIVE_HISTORY_PLUS_NEW_REAL_ORDINARY_CLOSURE','Wrong new recovery identity')
    negative=C.load(S.NEGATIVE)
    C.check(negative['ordinary_success_receipt'] is False and negative['original_job_closure']=='UNKNOWN' and
      negative['original_controller_outcome']=='UNKNOWN' and negative['actual_native_exit']['exit_code_dword']==1,
      'Historical failure must remain negative/unknown')
    C.check(C.digest(S.NEGATIVE)==freeze['negative_history_certificate_sha256'],'Negative history changed')
    iso=C.load(runtime/'isolation.json');binding=C.load(runtime/'controller_binding.json')
    current=C.load(runtime/'independent_current_boundary.json')
    C.check(C.digest(runtime/'independent_current_boundary.json')==freeze['fresh_exclusive_boundary_sha256'] and
      current['controller']==binding['controller'] and current['actual_retained_workflow_lock_identity']==binding['lock_identity']==negative['exclusive_writer_boundary'] and
      current['negative_history_certificate_sha256']==freeze['negative_history_certificate_sha256'],'Fresh boundary/negative/held-lock binding differs')
    R.verify_stored_role(current,P.acceptance()[0],runtime)
    C.check(iso['codex_cli_ancestor'] is False and
      C.digest(runtime/'isolation.json')==freeze['scheduler_isolation_sha256'],'Scheduler isolation not established')
    parent=C.load(S.ROOT/'.work/host_review/PARENT_RECOVERY_V10_ADMISSION_V2_REVIEW.json');proposal=C.load(S.ROOT/'config/host_inference_stage04_recovery_v10_admission_v2_freeze.json')
    C.check(C.digest(S.ROOT/'.work/host_review/PARENT_RECOVERY_V10_ADMISSION_V2_REVIEW.json')==freeze['parent_acceptance_sha256'] and
      parent['outer_job_lifetime_review']=={'decision':'ACCEPT_OBSERVED_SCHEDULER_BOUND_OUTER_JOB_LIFETIME','fixture_sha256':proposal['scheduler_fixture_sha256'],
        'production_task_definition_sha256':proposal['production_task']['definition_sha256'],
        'native_controls':'NESTED_OWNED_JOB_3GIB_MASK5_NO_BREAKAWAY','old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY',
        'static_controls_policy_sha256':proposal['production_admission_policy_sha256']},
      'Independent checker requires explicit reviewed outer-job lifetime and negative history')
    C.check(freeze['production_admission_revision']=='V10_PRODUCTION_ADMISSION_V2' and
      freeze['production_admission_policy_sha256']==proposal['production_admission_policy_sha256'] and
      freeze['outer_job_compatibility_sha256']==C.digest(runtime/'outer_job_compatibility.json'),'Explicit admission revision/receipt differs')
    A.verify_compatibility_receipt(runtime/'outer_job_compatibility.json',proposal,binding['controller'])
    A.verify_compatibility_receipt(runtime/'analyses'/name/'outer_job_compatibility.json',proposal,binding['controller'])
    stable=runtime/'analyses'/name/'attempt_0001';copied=S.OUT/'analyses'/name/'iqtree/attempt_0001'
    before=C.load(runtime/'analyses'/name/'input_tool_binding_before.json');after=C.load(runtime/'analyses'/name/'input_tool_binding_after.json')
    C.check(before==after==S.scope_binding(name),'Independent scope input/tool before/after/current hashes differ')
    for member in ('launch.json','exit.json'):
        C.check(C.digest(stable/member)==C.digest(copied/member),'New ordinary C receipt copy changed')
    launch=C.load(stable/'launch.json');exit=C.load(stable/'exit.json')
    C.check(exit['receipt_kind']=='ORDINARY_ACTUAL_NATIVE_EXIT_AND_EMPTY_OWNED_JOB' and exit['exit_code']==0 and
      exit['job_active_processes']==0 and exit['actual_job_process_ids']==[] and exit['exit_filetime']>exit['child_creation_filetime'],
      'Real new ordinary exit0 and queried empty job mandatory')
    C.check(launch['runner_pid']==binding['controller']['pid'] and launch['runner_creation_filetime']==binding['controller']['creation_filetime'] and
      launch['affinity_mask']==launch['actual_suspended_child_affinity_mask']==5 and launch['actual_child_in_owned_job'] is True,
      'Actual new controller/native identity and assignment differ')
    # Every scope runs the exact existing scientific audit once; no fixture replaces it.
    C.check(C.digest(S.ROOT/'scripts/supplemental_native_v6_final_check.py')=='d65b89ff6d284a37b61debb370c33e488276c0fbb40eea139c2974c6d3a848c4',
      'Pinned supplemental manifest/portable parser changed')
    V.INPUT=S.OUT
    directory=S.OUT/'analyses'/name/'iqtree';proof=C.load(directory/'tree_complete.json')
    expected=V.expected_argv(freeze['executable'],name)
    attempts,required=EXTRA.attempt_audit(directory,proof,expected,freeze['tool_identity']['executable_sha256'])
    EXTRA.manifest_audit(directory,proof,EXTRA.REQUIRED_OUTPUTS|required)
    result=V.audit_analysis(name)
    with (V.ALIGN/'analyses'/name/'tip_label_map.tsv').open(encoding='utf-8',newline='') as f:labels=list(csv.DictReader(f,delimiter='\t'))
    ids=next(a['accessions'] for a in freeze['source_identity']['analyses'] if a['name']==name)
    portable=EXTRA.labeled_audit(directory,labels,ids,V.V)
    cache=None
    if name=='primary196':
        imported=C.load(runtime/'analyses'/name/'cache_import.json')
        C.check(imported['source_sha256']==imported['destination_sha256']==S.CACHE_SHA and imported['redo'] is False,'Cache import byte identity changed')
        log=(S.OUT/'analyses'/name/'iqtree/host.log').read_text()
        # Require actual IQ-TREE's own model-checkpoint reuse message, not copied-cache existence alone.
        observed=check_cache_log(log,S.OUT/'analyses'/name/'iqtree/host')
        with (V.ALIGN/'analyses'/name/'partitions.tsv').open(encoding='utf-8',newline='') as stream:
            partition_ids=[r['partition'] for r in csv.DictReader(stream,delimiter='\t')]
        records=check_cache_records(S.OLD/'analyses/primary196/iqtree/host.model.gz',directory/'host.model.gz',partition_ids,S.CACHE_SHA)
        cache={'import_sha256':C.digest(runtime/'analyses'/name/'cache_import.json'),'actual_log_sha256':C.digest(S.OUT/'analyses'/name/'iqtree/host.log'),
          'actual_tool_messages':observed,'completed_candidate_records':records,
          'state':'ACTUAL_NEW_PREFIX_MODEL_CACHE_LOAD_FAST_TREE_RESTORATION_AND14_INHERITED_86_NEW_DECISIONS_VERIFIED'}
    value={'utc':C.now(),'status':'PASS_V10_REAL_ORDINARY_LIFECYCLE_AND_UNCHANGED_SCIENTIFIC_OUTPUT_CHECKS',
      'checker_sha256':C.digest(__file__),'pinned_v6_scientific_checker_sha256':S.FROZEN['scripts/stage04_windows_validate_v6.py'],
      'negative_history_only':True,'cache_evidence':cache,'result':result,'portable_and_label_checks':portable,
      'new_actual_attempt_checks':attempts,'inference_freeze_sha256':C.digest(S.OUT/'inference_freeze.json')}
    C.atomic(S.REPORT/(name+'_independent_check.json'),value)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-gate',action='store_true');p.add_argument('--analysis',choices=S.NAMES);a=p.parse_args()
    C.check(a.source_gate != bool(a.analysis),'Choose exactly one independent gate')
    source_gate() if a.source_gate else audit(a.analysis)

if __name__=='__main__':main()
