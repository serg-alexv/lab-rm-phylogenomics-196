"""Concrete immutable proposal for parent; completed V10 fixture is reused."""
import ast,json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_production_admission_policy_v1 as A
import stage04_recovery_controller_v10_admission_v1 as P

DELTA=[
 'stage04_production_admission_policy_v1.py','build_stage04_production_admission_v1.py',
 'test_stage04_production_admission_v1.py','prepare_stage04_production_tasks_admission_v1.py',
 'prepare_stage04_production_freeze_admission_v1.py','stage04_recovery_controller_v10_admission_v1.py',
 'stage04_recovery_validate_v10_admission_v1.py','final_check_stage04_recovery_v10_admission_v1.py',
 'check_stage04_recovery_acceptance_v10_admission_v1.py','activate_stage04_recovery_production_v10_admission_v1.ps1']

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        head=C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock)
        C.check(not P.PROPOSAL.exists() and not S.OUT.exists(),'Immutable proposal/output exists; no rewriting or duplicate start')
        preserved=C.load(S.ROOT/'config/host_inference_stage04_recovery_v10_preparation_snapshot_0002.json')
        required=dict(preserved['source_sha256'])
        for key,sha in required.items():C.check(C.digest(S.ROOT/key.split(':',1)[1])==sha,'Tested fixture source changed')
        fixture_path=S.REPORT/'scheduler_fixture.json';fixture=C.load(fixture_path)
        C.check(C.digest(fixture_path)==A.FIXTURE_SHA and fixture['status']=='PASS_THIS_ORIGINAL_CLI_EXIT_SAME_CREATIONS_ADVANCED_AND_ACTUAL_EMPTY_JOB_CONTROLLER_EXIT0',
          'Completed unchanged fixture certificate missing/different')
        required.update(fixture['file_sha256'])
        registered=C.load(S.REPORT/'production_admission_v1_registered_tasks.json')
        request_path=Path(registered['production_request']);observer_path=Path(registered['observer_request'])
        request=C.load(request_path);observer=C.load(observer_path)
        C.check(request['mode']=='production' and observer['mode']=='observer' and observer['target_runtime']==request['runtime'], 'Task roles differ')
        for value,path in ((request,request_path),(observer,observer_path)):
            C.check(path==Path(value['runtime'])/'task_request.json' and not Path(value['start_path']).exists(),'Task already started or wrong request path')
            query=C.load(value['query_path'])
            C.check(query['state']==3 and query['last_task_result']==267011 and query['triggers_count']==query['restart_count']==0 and
              query['actions_count']==1 and query['logon_type']==3 and query['run_level']==0 and query['multiple_instances']==2 and query['execution_time_limit']=='PT0S' and
              query['executable']==value['executable'] and query['arguments']==value['arguments'] and query['cwd']==value['cwd'] and
              C.digest(value['xml_path'])==value['definition_sha256'],'Unused actual task definition/result differs')
            for item in [path,Path(value['xml_path']),Path(value['query_path'])]:required['historical:'+item.relative_to(S.HISTORY).as_posix()]=C.digest(item)
        config=C.load(request['config'])
        C.check(config['production_admission_revision']=='V10_PRODUCTION_ADMISSION_V1' and config['analysis_names']==S.NAMES and
          request['argv']==['-u',str(S.ROOT/'scripts/stage04_recovery_controller_v10_admission_v1.py'),'--config',request['config']],
          'Production action/config differs from explicit new adapter')
        guard=C.load(S.REPORT/'production_admission_v1_guard_tests.json');actual=C.load(S.REPORT/'production_admission_v1_actual_service_guard.json')
        C.check(guard['status']=='PASS_NEW_ADMISSION_ONLY_GUARDS' and guard['tests']==23 and guard['failures']==guard['errors']==0 and
          guard['policy_source_sha256']==actual['policy_source_sha256']==C.digest(A.__file__) and actual['status']=='ACTUAL_FRESH_BRACKETED_SERVICE_ROLE_QUERY_COMPLETED_NO_SCIENCE',
          'New admission guard evidence/source binding differs')
        for name in DELTA:
            path=S.ROOT/'scripts'/name
            if path.suffix=='.py':ast.parse(path.read_text(encoding='utf-8-sig'),filename=name)
            required['data:scripts/'+name]=C.digest(path)
        old=C.load(S.OLD/'inference_freeze.json');required.update(old['source_identity']['file_sha256'])
        historical=C.load(S.ROOT/'reports/stage04/inference_v4_adoption.json')
        for source in historical['sources']:
            required['data:'+source['path']]=source['sha256'];required['historical:'+source['path']]=source['sha256']
        for rel,sha in S.FROZEN.items():required['data:'+rel]=sha
        for path in [Path(old['executable']),Path(old['executable']).parent/'libiomp5md.dll',S.HISTORY/'.tools/iqtree_windows_3_1_4/iqtree-3.1.4-Windows.zip']:
            required['historical:'+path.relative_to(S.HISTORY).as_posix()]=C.digest(path)
        order=S.ROOT/'WORK_ORDER.md';text=order.read_text(encoding='utf-8')
        C.check('## Production-only admission revision1' not in text,'Work-order revision already recorded')
        C.atomic(order,text+'\n## Production-only admission revision1 (2026-10-09)\n\nThe unchanged tested V10 lifetime mechanism survived original CLI15584 natural exit with exact retained creations, advancement and actual empty-job/controller/task exit0. Certificate ce77c4ce4882aa5c1d16bb69967d891c20b9625ba80c97924a7ecf14d1d55470 is preserved. A separately named production-only revision adds only fresh bracketed exact WSLService SCM/CIM role classification and comparison of actual four static anonymous outer controls with the reviewed zero baseline. Native WinError5/image/100ns identity remain UNKNOWN when denied; every other null-commandline runner remains blocked. Dynamic job membership/counts are not compared or assigned ownership. Actual no-outer membership remains separate, with unchanged inner controls required. No service stop/guest boot/privilege bypass. Tested33V10source bytes, scientific methods, exact four scopes, preserved14decision cache and historical UNKNOWN closures remain unchanged. Final proposal config/host_inference_stage04_recovery_v10_admission_v1_freeze.json needs independent PARENT_RECOVERY_V10_REVIEW.json naming its exact hash/map and explicit static-policy/lifetime review before one manual production start.23new guards plus one bounded fresh read-only service query are preparation, not scientific results. No repeated old suite/120s fixture.\n')
        public_reports=['scheduler_fixture.json','completed_fixture_preservation_receipt.json','production_admission_v1_build.json',
          'production_admission_v1_guard_tests.json','production_admission_v1_actual_service_guard.json','production_admission_v1_registered_tasks.json',
          'guard_tests.json','boundary_cache_delta_tests.json','stdio_overlap_fixture.json']
        files=[S.NEGATIVE,fixture_path,A.POLICY_PATH,Path(request['config']),S.OLD/'inference_freeze.json',S.OLD/'analyses/primary196/iqtree/host.model.gz',
          S.ROOT/'config/host_inference_stage04_recovery_v9_freeze.json',S.ROOT/'config/host_inference_stage04_recovery_v10_preparation_snapshot_0002.json',
          S.ROOT/'config/host_inference_stage04_recovery_v10_fixture.json',S.ROOT/'AGENTS.md',order,S.ROOT/'config/approval.json',S.ROOT/'config/approved_accessions.txt']
        files += [S.REPORT/name for name in public_reports]
        files += [S.ROOT/'.work/host_review'/name for name in ['PARENT_V10_MINIMAL_ADMISSION_POLICY_NOTE.md','PARENT_V10_SCIENTIFIC_PREPARATION0002_REVIEW.md',
          'PARENT_V10_LIFETIME_PREPARATION0002_REVIEW.md','PARENT_RECOVERY_V10_ORIGINAL_CLI_EXIT_FIXTURE.json']]
        for path in files:required['data:'+path.relative_to(S.ROOT).as_posix()]=C.digest(path)
        control=S.RUNTIME/'production_admission_v1_read_only_guard'
        for rel in ('actual_service_role.json','control_job/launch.json','control_job/exit.json'):
            path=control/rel;required['historical:'+path.relative_to(S.HISTORY).as_posix()]=C.digest(path)
        required['historical:.work/stage04_recovery_v10/completed_fixture_preservation_v1/scheduler_fixture.json']=A.FIXTURE_SHA
        # Recheck exact existing bytes only; no sequence, marker, alignment or tool job rerun.
        P.verify_artifacts(required)
        proposal={'schema':'V10_PRODUCTION_ADMISSION_V1_REVIEW_PROPOSAL_NOT_ADOPTION','utc':C.now(),'status':'HASH_BOUND_PARENT_ACCEPTANCE_REQUIRED_NOT_STARTED',
          'canonical_main_at_preparation':head,'required_review_artifacts':required,'old_immutable_freeze_sha256':S.FREEZE_SHA,
          'production_admission_revision':'V10_PRODUCTION_ADMISSION_V1','production_admission_policy_sha256':C.digest(A.POLICY_PATH),
          'negative_history_certificate_sha256':C.digest(S.NEGATIVE),'scheduler_fixture_sha256':A.FIXTURE_SHA,
          'preserved_tested_preparation_sha256':'4343339391306ddfde6eedae0337b4d6b75bf22eeb6759967e0c091a8d63b222',
          'tested_mechanism_source_sha256':preserved['source_sha256'],'production_delta_source_sha256':{name:C.digest(S.ROOT/'scripts'/name) for name in DELTA},
          'production_task':request,'production_readonly_observer_task':observer,'existing_accepted_source_identity':old['source_identity'],
          'fixed_external_interpreters':[{'path':str(p),'sha256':C.digest(p)} for p in [S.PYTHON,S.PYTHONW,S.VALIDATOR]],
          'native_contract':{'process_and_aggregate_committed_cap_bytes':3221225472,'affinity_mask':5,'threads':2,
            'windows_available_minimum_bytes':4831838208,'physical_C_and_data_namespace_free_disk_minimum_exclusive_bytes':5*1024**3,
            'root':'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP'},'scope_counts':[[196,100],[162,100],[196,88],[155,100]],
          'science_launches_this_preparation':0,'old_ordinary_controller_outcome':'UNKNOWN','old_job_closure':'UNKNOWN','lifetime_fixture_repeated':False,'old_suites_repeated':0}
        A.validate_policy(proposal);C.atomic(P.PROPOSAL,proposal)
        expected={**required,'data:'+P.PROPOSAL.relative_to(S.ROOT).as_posix():C.digest(P.PROPOSAL)}
        outer={'decision':'ACCEPT_OBSERVED_SCHEDULER_BOUND_OUTER_JOB_LIFETIME','fixture_sha256':A.FIXTURE_SHA,
          'production_task_definition_sha256':request['definition_sha256'],'native_controls':'NESTED_OWNED_JOB_3GIB_MASK5_NO_BREAKAWAY',
          'old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY','static_controls_policy_sha256':C.digest(A.POLICY_PATH)}
        C.atomic(S.REPORT/'production_admission_v1_parent_expected_artifacts.json',{'schema':'EXPECTED_EXACT_PARENT_RECORD_NOT_ACCEPTANCE',
          'required_parent_record':str(P.ACCEPTANCE),'required_schema':'PARENT_RECOVERY_V10_HASH_BOUND_ACCEPTANCE','required_reviewer':'INDEPENDENT_PARENT',
          'required_decision':'ACCEPTED_FOR_SINGLE_PRODUCTION_START','production_task_name':request['task_name'],
          'artifact_sha256':expected,'outer_job_lifetime_review':outer,'proposal_sha256':C.digest(P.PROPOSAL)})
        body='# Owner final production admission1 review request\n\n'
        body+='Production NOT_STARTED / NOT_ACCEPTED. Stage04 scientific FAILED/INCOMPLETE;05–07 NOT_RUN. Canonical main before preparation '+head+'.\n\n'
        body+='Immutable final proposal: config/host_inference_stage04_recovery_v10_admission_v1_freeze.json SHA256 '+C.digest(P.PROPOSAL)+'. Exact '+str(len(expected))+'-artifact expected parent record: reports/stage04/recovery_v10/production_admission_v1_parent_expected_artifacts.json. It is NOT acceptance.\n\n'
        body+='Completed fixture certificate '+A.FIXTURE_SHA+' passed the unchanged _v10_2 checker before any new source was added and is copied to stableC preservation_v1. Parent retained originalCLIexit0 and same controller15172/native30920/grandchild26600 creations advancing afterward, then actual native/controller/task exit0 and emptyjob. All33tested sources still match preparation0002 '+proposal['preserved_tested_preparation_sha256']+'. Anonymous outer ownership remains unidentified; this particular lifetime observation is not universal/scientific acceptance. No120s repeat/old suite rerun.\n\n'
        body+='Production-only deltas are listed in proposal.production_delta_source_sha256 and reports/stage04/recovery_v10/production_admission_v1_build.json with exact guarded text replacements. Unchanged V10 support/nativeJob/observer/outbox/publisher/cache parser and pinned V6/supplemental scientific checks are reused. New controller/source-checker/final-checker add only the two reviewed admission changes and their direct frozen receipt joins. Reuse prior independent reviews only on identical source hashes; review these new deltas.\n\n'
        body+='Fresh exact WSLService/LocalSystem/Running/canonical configuredbinary association is bracketed by identical CIM PID/creation; only that platform role is excluded before the null-commandline gate. Native WinError5/image/100ns creation remain UNKNOWN. Every other null/unknown runner and all recorded old-instance access errors still block. Actual read-only guard passed onWD with ownedcontrol exit0/emptyjob and no scientific runner.23focused new rejection tests passed. No service stop, guest boot, elevation or bypass.\n\n'
        body+='Before production and before each biological scope, fresh actual anonymousouter static fields must equal four reviewed fixture zeros (nonboolean integers); dynamic counts/PIDs ignored. Actual false membership remains separate with no invented zerojob. C outer_job_compatibility receipts bind actual isolation SHA, this policy/source SHA and completedfixture SHA; inference freeze and independent/final checks require these joins. All original exact scopes/methods remain196x100,162x100,196x88,155x100,IQTREE3.1.4 hash43c9bf3b0dc5e7d88c183a2582369d22c9d692b7585350038769334bb6fd9aed,MFP,-p,B1000,alrt1000,seed1961008,T2,keepident/boottrees. Byte-identical14decision cache import requires actual restoration messages and unchanged14/final100/86new records; actual reuse remains NOT_RUN.\n\n'
        body+='Two exact unique tasks are registered NEVER_STARTED: '+request['task_name']+' and '+observer['task_name']+'. Exported full definitions/SID/action/argv/cwd and request bytes are in the proposal map; zero triggers/restarts,limited InteractiveToken,IgnoreNew,PT0S. Shared stableC lock identity remains unchanged; session lock distinct. Native/exception receipts stayC; optional bounded publication cannot close science. No synchronous Git callback in nativewait.\n\n'
        body+='Parent alone writes .work/host_review/PARENT_RECOVERY_V10_REVIEW.json with required schema/reviewer/decision,exact artifact map including finalproposal SHA,production_task_name and exact outer_job_lifetime_review from expected JSON. A barePASS or staleV9 record is rejected. Parent acceptance currently absent; owner will WAIT and must not start science before all exact hashes validate.\n\n'
        body+='Accepted single-start command: scripts/activate_stage04_recovery_production_v10_admission_v1.ps1 -Request "'+str(request_path)+'" -ObserverRequest "'+str(observer_path)+'". First independently run scripts/check_stage04_recovery_acceptance_v10_admission_v1.py with those two arguments. Fresh actual admission≥4.5GiB Windows/freephysicalC>5GiB and same3GiB process+aggregate/mask5/twoPcores remain required at launch; no resource receipt fabricated. Serial four real scopes require actual ordinary exit0/emptyjobs and unchanged scientific validation. Final entrypoint is scripts/final_check_stage04_recovery_v10_admission_v1.py, then actual portable scope/report Releases with remote byteverification. Stage05 Linux ownership/G-WSL/nativeR/interoperability remains separate actual pending gate; no detector/model/figure preparation claimed as science.\n\n'
        body+='Historical V6 native actualexit1/CPU16131.484375s and UNKNOWN original controller/job closure remain negative; old B2 guard/source unchanged. No cause inferred. Old failed artifacts/cache and stage04c verified failureRelease retained.\n'
        C.atomic(S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_REVIEW_REQUEST.md',body)
        C.atomic(S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_ADMISSION_V1_REVIEW_REQUEST.md',body)
        C.atomic(S.REPORT/'OWNER_PRODUCTION_ADMISSION_V1_REVIEW_REQUEST.md',body)
        C.atomic(S.REPORT/'production_admission_v1_preparation_receipt.json',{'utc':C.now(),'status':'CONCRETE_IMMUTABLE_PROPOSAL_AND_UNUSED_TASKS_PARENT_ACCEPTANCE_PENDING',
          'proposal_sha256':C.digest(P.PROPOSAL),'expected_artifacts':len(expected),'actual_stable_lock_identity':S.lock_identity(lock),
          'biological_jobs':0,'native_production':'NOT_STARTED','parent_acceptance':'NOT_GRANTED','lifetime_fixture_repeated':False,'old_suites_repeated':0,
          'preparation_cpu_seconds':None,'preparation_peak_ram_bytes':None,'reason':'Whole preparation process tree not measured; actual narrow-control/nativefixture metrics retained separately'})
        status=S.ROOT/'STATUS.md';C.atomic(status,status.read_text()+'\n\nFinal admission1 proposal '+C.now()+': SHA256'+C.digest(P.PROPOSAL)+', '+str(len(expected))+' exact reviewed-artifact hashes; two unique manual production/observer tasks registered NEVER_STARTED. Completed tested V10 lifetime/source bytes preserved;23new admission guards and actual bounded service-role query passed. Parent hash-bound final acceptance remains REQUIRED/ABSENT; no new scientific job or production inference output exists. Stage04 science FAILED/INCOMPLETE;05–07 NOT_RUN. See reports/stage04/recovery_v10/OWNER_PRODUCTION_ADMISSION_V1_REVIEW_REQUEST.md.\n')
        execution=S.ROOT/'status/stage04_execution.json';value=C.load(execution);value.update(utc=C.now(),recovery='FINAL_PRODUCTION_ADMISSION_V1_PROPOSAL_PARENT_HASH_BOUND_ACCEPTANCE_PENDING',
          production_source_gate='PRODUCTION_ONLY_SERVICE_ROLE_REPAIR_TESTED_UNADOPTED',proposal_sha256=C.digest(P.PROPOSAL),native_production='NOT_STARTED',parent_acceptance='NOT_GRANTED');C.atomic(execution,value)
        paths=['scripts/'+n for n in DELTA]+[P.PROPOSAL.relative_to(S.ROOT).as_posix(),A.POLICY_PATH.relative_to(S.ROOT).as_posix(),
          'config/host_inference_stage04_recovery_v10_production.json','WORK_ORDER.md','STATUS.md','status/stages.tsv','status/stage04_execution.json']
        paths += ['reports/stage04/recovery_v10/'+n for n in ['production_admission_v1_parent_expected_artifacts.json','production_admission_v1_build.json',
          'production_admission_v1_guard_tests.json','production_admission_v1_actual_service_guard.json','production_admission_v1_registered_tasks.json',
          'production_admission_v1_preparation_receipt.json','OWNER_PRODUCTION_ADMISSION_V1_REVIEW_REQUEST.md']]
        for directory in [S.REPORT/'production_task'/request['task_name'],S.REPORT/'observer_tasks'/observer['task_name']]:
            paths += [p.relative_to(S.ROOT).as_posix() for p in directory.iterdir() if p.is_file()]
        receipt=S.publish(paths,'Freeze minimal production admission revision with completed lifetime proof; await exact parent acceptance')
        C.atomic(S.REPORT/'production_admission_v1_publication_receipt.json',receipt)
        C.atomic(S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_ADMISSION_V1_PUBLICATION.json',receipt)
        print(json.dumps({'status':receipt['status'],'commit':receipt['commit'],'files_verified':len(receipt['file_sha256']),
          'proposal_sha256':C.digest(P.PROPOSAL),'expected_parent_artifacts':len(expected),'parent_acceptance':'NOT_GRANTED','native_production':'NOT_STARTED'}))

if __name__=='__main__':main()
