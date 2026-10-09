"""Produce immutable review proposal from executed evidence; no adoption/start."""
import hashlib, json, os, subprocess
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

SOURCES=['stage04_recovery_support_v10.py','reconcile_stage04_failed_attempt_v1.py','stage04_windows_job_v10.py',
 'stage04_recovery_controller_v10.py','stage04_recovery_outbox_v10.py','stage04_recovery_publisher_v10.py',
 'stage04_recovery_validate_v10.py','stage04_model_cache_evidence_v10.py','inspect_iqtree_model_cache_v10.py',
 'register_stage04_recovery_task_v10.ps1','query_stage04_recovery_task_v10.ps1','start_stage04_recovery_task_v10.ps1',
 'prepare_stage04_recovery_tasks_v10.py','check_stage04_recovery_fixture_v10.py','stage04_recovery_fixture_v10.py',
 'test_stage04_recovery_guards_v10.py','observe_stage04_recovery_controller_v10.py','final_check_stage04_recovery_v10.py',
 'check_stage04_recovery_acceptance_v10.py','activate_stage04_recovery_production_v10.ps1',
 'prepare_stage04_recovery_observer_task_v10.py','start_stage04_recovery_observer_v10.ps1','prepare_stage04_recovery_review_v10.py']

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        head=C.reconcile(S.ROOT);S.pins();fixture=C.load(S.REPORT/'scheduler_fixture.json')
        C.check(fixture['biological_jobs']==0 and fixture['actual_controller_bound_exit']['actual_exit_code']==0 and
          fixture['status']=='PASS_SHORT_SYNTHETIC_SCHEDULER_LIFETIME_AND_EMPTY_NATIVE_JOB_OUTER_JOB_PARENT_REVIEW_REQUIRED',
          'Actual synthetic Scheduler fixture did not complete')
        for key,sha in fixture['source_sha256'].items():C.check(C.digest(S.ROOT/key.split(':',1)[1])==sha,'Executed fixture source changed: '+key)
        for key,sha in fixture['file_sha256'].items():C.check(C.digest(S.HISTORY/key.split(':',1)[1])==sha,'Executed fixture payload changed')
        cfg=C.load(S.ROOT/'config/host_inference_stage04_recovery_v10_fixture_07.json');fr=Path(cfg['runtime'])
        obs=C.load(fr/'independent_controller_exit.json');binding=C.load(fr/'independent_controller_observer_binding.json')
        C.check(obs['process']['pid']==fixture['actual_controller_bound_exit']['pid'] and obs['process']['creation_filetime']==fixture['actual_controller_bound_exit']['creation_filetime'] and
          obs['process']['actual_exit_code']==0 and binding['actual_scheduler_observer'] is not None and binding['termination_rights'] is False,
          'Durable direct Scheduler observer did not independently record actual controller exit0')
        actors=binding['actual_scheduler_observer'];C.check(S.process_identity(actors['actual_process']['pid'],actors['actual_process']['creation_filetime'])['state'] in
          ('ABSENT_WIN32_ERROR_INVALID_PARAMETER','EXITED','PID_REUSED_DIFFERENT_CREATION'),'Fixture observer still alive')
        durable={'utc':C.now(),'status':'PASS_DIRECT_SCHEDULER_READ_ONLY_OBSERVER_ACTUAL_BOUND_CONTROLLER_EXIT0',
          'controller_actual_exit':obs,'observer_binding':binding,'scientific_jobs':0,
          'file_sha256':{'historical:'+str((fr/x).relative_to(S.HISTORY)).replace('\\','/'):C.digest(fr/x) for x in
            ['independent_controller_exit.json','independent_controller_observer_binding.json']}}
        C.atomic(S.REPORT/'durable_observer_fixture.json',durable)
        cache=C.load(S.REPORT/'model_cache_semantics.json');raw=Path(S.RUNTIME/'official_source/phylotesting_v3_1_4.cpp').read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        C.check(blob=='317908081d549f3d0a2e0a040b6fc5a74789ebe3','Official version-tagged source Git blob differs')
        C.atomic(S.REPORT/'model_cache_source_addendum.json',{'utc':C.now(),'official_github_api_url':'https://api.github.com/repos/iqtree/iqtree3/contents/main/phylotesting.cpp?ref=v3.1.4',
          'official_git_blob_sha1':blob,'downloaded_source_sha256':C.digest(S.RUNTIME/'official_source/phylotesting_v3_1_4.cpp'),
          'actual_source_references':{'separate_model_load':[1398,1403],'finished_fast_ml_restore':[811,815],
            'candidate_evaluate_early_return_on_saved_model':[1974,1977],'all_partition_checkpoint_job_pruning_returns_without_pruning':[4198,4203]},
          'interpretation':'The saved candidate restores before optimization and returns when present. Partition progress may still count restored candidates;14 completed best-model entries do not imply a blanket14-partition skip. Native new-prefix model-load and fast-ML restoration messages remain mandatory.',
          'actual_native_reuse':'NOT_RUN_REQUIRES_PARENT_ADOPTION_AND_ACTUAL_TOOL_OUTPUT'})
        # Private local metadata about unrelated members is intentionally omitted from public artifacts.
        outer=fixture['scheduler_isolation']['actual_outer_job'];local=[]
        for pid in outer['process_ids']:
            if pid!=fixture['actual_controller_bound_exit']['pid']:local.append(S.process_identity(pid))
        C.atomic(S.RUNTIME/'outer_job_member_local_review.json',{'utc':C.now(),'scope':'READ_ONLY_PARENT_REVIEW_UNRELATED_MEMBERS_NEVER_MODIFIED',
          'actual_outer_controls':outer,'current_member_identity':local,'no_ownership_inferred_from_membership':True})
        production=C.load(S.ROOT/'config/host_inference_stage04_recovery_v10_production.json');pr=Path(production['runtime']);request=C.load(pr/'task_request.json')
        C.check(not (pr/'task_start.json').exists() and not (pr/'production_started.json').exists() and not S.OUT.exists(),'Production already started; preparation-only proposal forbidden')
        observers=[]
        for p in (S.RUNTIME/'observers').glob('*/task_request.json'):
            r=C.load(p)
            if r['target_runtime']==str(pr):observers.append(r)
        C.check(len(observers)==1,'Exactly one retained production read-only observer definition required');observer=observers[0]
        C.check(not Path(observer['start_path']).exists(),'Production observer was started during preparation')
        # Query current actual production definitions again; their bytes must match pre-start exports.
        for r in [request,observer]:
            ps="$s=New-Object -ComObject Schedule.Service; $s.Connect(); $t=$s.GetFolder('\\').GetTask('"+r['task_name']+"'); [pscustomobject]@{state=$t.State;last_result=$t.LastTaskResult;xml=$t.Xml} | ConvertTo-Json -Depth 4 -Compress"
            actual=json.loads(S.command(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps]).decode('utf-8-sig'))
            C.check(actual['state']==3 and actual['last_result']==267011 and hashlib.sha256(b'\xff\xfe'+actual['xml'].encode('utf-16le')).hexdigest()==r['definition_sha256'],
              'Actual unused production/observer definition changed')
        method='''# Stage04 recovery V10 candidate\n\nProduction remains FAILED/INCOMPLETE; Stages05–07 are NOT_RUN. V10 is prepared and tested, not adopted or executed biologically. Direct user instruction requires an independent hash-bound parent record before production.\n\nThe separate failed_attempt_reconciliation_v1 certificate proves retained native PID29132/creation134359651870883542 exited1 at2026-10-08T23:30:02.6498313Z with16131.484375s native CPU. Old ordinary exit/tree-complete files are absent. Old controller outcome and final old job closure remain UNKNOWN; no cause is established. Copies and hashes preserve every retained primary attempt artifact/model cache. Missing creation tokens for three old helper/observer roles are explicit; no original token is invented. The unchanged B2 guard still rejects old missing ordinary closure.\n\nV10 instead requires known actual failed-native history, genuine stable-C byte0 lock ownership, old-instance reconciliation and no other matching scientific runner. Fresh access errors block. The existing lock file is never replaced; the private launcher session lock is distinct. Native receipts/logs/exceptions live on stable C, with actual PID/creation, launch tool/argv, exit/time and queried empty job accounting. Optional G/Git errors cannot propagate into the native wait. A one-slot nonblocking outbox uses separately bounded256MiB/90s publisher process trees and a dedicated delegated writer mutex.\n\nA unique manually started TaskScheduler action runs the actual long-lived controller directly through the pinned base pythonw executable. Same logged-in user SID, InteractiveToken, limited privilege, no triggers/restarts, IgnoreNew, unlimited time; actual exported UTF16 definition and queried action/cwd/SID are hashed before start. The short synthetic fixture survives natural return of its starter, then produces actual child/grandchild exit0, empty owned job and controller exit0. An intentionally nonzero publisher exits with an empty bounded publisher job while native computation continues. No biological panel is used. A separate direct one-shot read-only Scheduler observer holds a query/synchronize handle and recorded the exact fixture controller exit0.\n\nIsProcessInJob(controller,NULL) is TRUE. Actual outer controls have zero limit flags; controller ancestry leads through TaskScheduler service svchost/services/wininit, with no CodexCLI ancestor. WMI ancestry creation evidence has microsecond precision, explicitly different from native100ns tokens. The current outer job is unnamed/unowned by these APIs and includes unrelated older scheduled processes; membership alone does not prove ownership or lifetime. No breakaway is requested. Parent must explicitly review/hash-bind this observed shared outer-job lifetime; a generic PASS file is rejected. The production controller and read-only observer tasks are registered but never started.\n\nFour existing accepted matrices/partitions and exact cohorts196/162/196/155 remain unchanged; markers100/100/88/100. IQ-TREE3.1.4, MFP with -p/no merge,1000 UFBoot and1000 SH-aLRT, seed1961008, -T2, -keep-ident, --boot-trees, explicit unrooted policy remain. Fresh Windows physical availability≥4.5GiB and disk>5GiB precede each scientific launch.1GiB is admission reserve, not continuous enforcement. Suspended native child receives queried3GiB per-process and aggregate committed-memory limits, actual assigned-job membership and two distinct physical P-core logical CPUs mask5, then resumes once.\n\nPrimary cache remains418807B SHA2560aeefd2a1f1098e924ca06bdb785b7bff2ab0fff5939b3cd3df4ca90b3896b03,14 best_model_BIC entries and finishedFastMLTree:true, with no general ckp. Official v3.1.4 source blob317908081d549f3d0a2e0a040b6fc5a74789ebe3 independently matches downloaded bytes. Separate model loading and per-candidate early return permit reuse; copied bytes/progress counts alone are insufficient. New prefix imports byte-identical cache without redo and must show actual exact model-load/fast-ML restoration messages. Model reuse is currently NOT_RUN.\n\nNew independent checker explicitly redirects only the preserved V6 audit's INPUT namespace. All tip/support/bootstrap/model-partition checks remain; pinned supplemental exhaustive manifest/attempt/quoted-label/unrooted export checks are added. Every scope needs new real C ordinary exit0 plus actual empty exact job PID list. Final V10 boundary reuses four real certificates and requires actual independently observed new controller exit0; missing observation remains blocking. Verified portable scientific publication and Stage05 native runtime/interoperability still require actual execution. Fixture passes are never R-M/phylogeny/figure results.\n'''
        (S.REPORT/'RECOVERY_V10.md').write_text(method,encoding='utf-8',newline='\n')
        order=S.ROOT/'WORK_ORDER.md';text=order.read_text(encoding='utf-8')
        if '## Direct user recovery protocol V10' not in text:
            order.write_text(text+'\n## Direct user recovery protocol V10 (2026-10-09)\n\nThe user explicitly requires preservation of failed V6 history, an unchanged stable-C workflow byte0 lock, versioned negative-history reconciliation, actual one-shot TaskScheduler controller lifetime evidence, stable-C native receipts and isolated bounded publication. A TRUE outer-job observation requires explicit reviewed identity/lifetime reasoning. Production retry requires a hash-bound independent parent acceptance record at .work/host_review/PARENT_RECOVERY_V10_REVIEW.json naming every adopted source, freeze and fixture hash. No production inference may start before that acceptance. This is a specific recovery gate, not a return to routine stage approval pauses. Existing FULL196/seven-stage scope, exact four inputs, original scientific options, detector cross-checks and verified publication remain required. Missing old controller/job closure stays UNKNOWN. Manual quota resets only; no recurring automation, reboot or scientific restart.\n',encoding='utf-8',newline='\n')
        required={}
        for name in SOURCES:required['data:scripts/'+name]=C.digest(S.ROOT/'scripts'/name)
        for rel in [*S.FROZEN,'WORK_ORDER.md','AGENTS.md','config/approval.json','config/approved_accessions.txt',
          'config/host_inference_stage04_recovery_v10_production.json','config/host_inference_stage04_recovery_v10_fixture_07.json']:
            required['data:'+rel]=C.digest(S.ROOT/rel)
        for rel in ['failed_attempt_reconciliation_v1.json','scheduler_fixture.json','durable_observer_fixture.json','guard_tests.json',
          'source_reuse_check.json','model_cache_semantics.json','model_cache_source_addendum.json','RECOVERY_V10.md']:
            required['data:reports/stage04/recovery_v10/'+rel]=C.digest(S.REPORT/rel)
        required.update(fixture['file_sha256']);required.update(durable['file_sha256'])
        for r in [request,observer]:
            for field in ['xml_path','query_path']:
                path=Path(r[field]);required['historical:'+path.relative_to(S.HISTORY).as_posix()]=C.digest(path)
            path=Path(r['runtime'])/'task_request.json';required['historical:'+path.relative_to(S.HISTORY).as_posix()]=C.digest(path)
        for rel in ['.work/stage04_inference_windows_v6/inference_freeze.json',
          '.work/stage04_inference_windows_v6/analyses/primary196/iqtree/host.model.gz']:
            required['data:'+rel]=C.digest(S.ROOT/rel)
        old=C.load(S.OLD/'inference_freeze.json')
        for p in [Path(old['executable']),Path(old['executable']).parent/'libiomp5md.dll',S.HISTORY/'.tools/iqtree_windows_3_1_4/iqtree-3.1.4-Windows.zip']:
            required['historical:'+p.relative_to(S.HISTORY).as_posix()]=C.digest(p)
        required['historical:.work/stage04_recovery_v10/official_source/phylotesting_v3_1_4.cpp']=C.digest(S.RUNTIME/'official_source/phylotesting_v3_1_4.cpp')
        proposal={'schema':'V10_REVIEW_PROPOSAL_NOT_PRODUCTION_ADOPTION','utc':C.now(),'status':'PARENT_REVIEW_REQUIRED_NOT_ADOPTED_NOT_EXECUTED',
          'canonical_main_at_preparation':head,'required_review_artifacts':required,'old_immutable_freeze_sha256':S.FREEZE_SHA,
          'negative_history_certificate_sha256':C.digest(S.NEGATIVE),
          'scheduler_fixture_sha256':C.digest(S.REPORT/'scheduler_fixture.json'),'durable_observer_fixture_sha256':C.digest(S.REPORT/'durable_observer_fixture.json'),
          'production_task':request,'production_readonly_observer_task':observer,'existing_accepted_source_identity':old['source_identity'],
          'fixed_external_interpreters':[{'path':str(p),'sha256':C.digest(p)} for p in [S.PYTHON,S.PYTHONW,S.VALIDATOR]],
          'native_contract':{'process_and_aggregate_committed_cap_bytes':3221225472,'affinity_mask':5,'threads':2,
            'windows_available_minimum_bytes':4831838208,'root':'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP'},
          'science_launches_this_preparation':0,'old_ordinary_controller_outcome':'UNKNOWN','old_job_closure':'UNKNOWN',
          'parent_outer_job_lifetime_review':'REQUIRED_ACTUAL_TRUE_OUTER_JOB_NOT_SILENTLY_TREATED_FALSE'}
        freeze=S.ROOT/'config/host_inference_stage04_recovery_v10_freeze.json';C.check(not freeze.exists(),'Review freeze immutable; create a new revision for repairs')
        C.atomic(freeze,proposal)
        expectation={**required,'data:config/host_inference_stage04_recovery_v10_freeze.json':C.digest(freeze)}
        C.atomic(S.REPORT/'parent_review_expected_artifacts.json',{'schema':'EXPECTED_REVIEW_ARTIFACTS_NOT_AN_ACCEPTANCE',
          'parent_record':'data:.work/host_review/PARENT_RECOVERY_V10_REVIEW.json','artifact_sha256':expectation,
          'required_schema':'PARENT_RECOVERY_V10_HASH_BOUND_ACCEPTANCE','required_reviewer':'INDEPENDENT_PARENT',
          'required_decision':'ACCEPTED_FOR_SINGLE_PRODUCTION_START','production_task_name':request['task_name'],
          'required_outer_job_lifetime_review':{'decision':'ACCEPT_OBSERVED_SCHEDULER_BOUND_OUTER_JOB_LIFETIME',
            'fixture_sha256':proposal['scheduler_fixture_sha256'],'production_task_definition_sha256':request['definition_sha256'],
            'native_controls':'NESTED_OWNED_JOB_3GIB_MASK5_NO_BREAKAWAY','old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY'}})
        review='''# Owner recovery V10 review request\n\nStatus: concrete candidates and actual fixture evidence complete; production NOT_STARTED. Parent acceptance is REQUIRED and has not been written by the owner.\n\nRead reports/stage04/recovery_v10/RECOVERY_V10.md, config/host_inference_stage04_recovery_v10_freeze.json and reports/stage04/recovery_v10/parent_review_expected_artifacts.json in the G data repository. Required artifact map includes every adopted source/config/freeze/fixture hash, actual unused production controller and read-only observer definitions, original V6 freeze/cache and tool bytes. Main remains scientific FAILED/INCOMPLETE;05–07 NOT_RUN.\n\nReview the negative-history certificate174971a811977dd2d5ce0ed009d49539490131ad603d434266c64f7da00322d1. V6 controller outcome/final job closure remain UNKNOWN. Missing original helper creation tokens are explicit; fresh access errors block and a new token may only demonstrate PID reuse after certified absence. Old B2 source is unchanged.\n\nActual latest fixture controller/native/read-only-observer identities and actual exit0 evidence are recorded, with native jobActive0/empty exact PID list and bounded publisher exit23/empty job. No pilot or biological job ran.24 focused guards passed; four accepted input/source sets match retained certificates/hashes without biological re-execution.\n\nCRITICAL REVIEW: IsProcessInJob(controller,NULL) is TRUE. Actual outer controls have zero flags; ancestry is TaskScheduler service chain with no CodexCLI ancestor. It shares membership with two unrelated older tasks; no ownership is inferred from this API, and nothing was terminated or reconfigured. Local read-only member metadata is historical:.work/stage04_recovery_v10/outer_job_member_local_review.json. Explicit hash-bound outer-job lifetime review is required; do not accept merely because a file/string says PASS. A separate direct Scheduler read-only observer was also actually exercised after natural initiating-call return and recorded controller exit0.\n\nThe scientific checker uses unchanged V6 scientific audits plus pinned exhaustive supplemental/quoted-label checks in an explicit new namespace. Final V10 check requires actual new ordinary native exits, actual empty jobs, four immutable scope certificates and independently observed actual controller exit0. Cache reuse requires actual exact new-prefix model-load/fast-ML restoration messages, currently NOT_RUN.\n\nIf accepted, parent alone writes .work/host_review/PARENT_RECOVERY_V10_REVIEW.json with the exact expected artifact map, explicit lifetime-review object and required structural identity. Owner then validates all current hashes, reconciles canonical main and activates the two unique manual controller/readonly-observer tasks once. No recurring triggers/restarts, no breakaway, no CLI-managed native lifetime. Repairs require a new freeze revision, not rewriting this proposal or old evidence.\n\nNo production start, inference freeze/output namespace, detector searches, figure or final scientific PASS exists for V10. Stage04 portable successful publication and Stage05 runtime/interoperability/release binding remain dependent actual work.\n'''
        (S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_REVIEW_REQUEST.md').write_text(review,encoding='utf-8',newline='\n')
        (S.REPORT/'OWNER_REVIEW_REQUEST.md').write_text(review,encoding='utf-8',newline='\n')
        C.atomic(S.REPORT/'preparation_execution_receipt.json',{'utc':C.now(),'status':'ACTUAL_PREPARATION_AND_SYNTHETIC_LIFETIME_COMPLETE_PARENT_REVIEW_REQUIRED',
          'proposal_sha256':C.digest(freeze),'review_artifacts':len(expectation),'scientific_jobs_launched':0,
          'controller_task':'REGISTERED_NEVER_STARTED','readonly_observer_task':'REGISTERED_NEVER_STARTED',
          'parent_acceptance':'ABSENT' if not (S.ROOT/'.work/host_review/PARENT_RECOVERY_V10_REVIEW.json').exists() else 'PRESENT_NOT_ASSUMED_VALID',
          'actual_stable_lock_identity':S.lock_identity(lock),'fixture_native_usage':fixture['actual_native_exit'],
          'preparation_cpu_seconds':None,'preparation_peak_ram_bytes':None,'usage_unavailable_reason':'Whole preparation process tree was not measured',
          'old_original_controller_outcome':'UNKNOWN','old_job_closure':'UNKNOWN'})
        print(json.dumps({'status':'REVIEW_PACKET_WRITTEN_NOT_ADOPTED','proposal_sha256':C.digest(freeze),'review_artifacts':len(expectation),
          'owner_request':str(S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_REVIEW_REQUEST.md')}))

if __name__=='__main__':main()
