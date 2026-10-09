"""Freeze the narrowly repaired observer-role guard for a new parent decision."""
import ast,json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_production_admission_policy_v1 as A
import stage04_recovery_controller_v10_admission_v1 as OLD
import stage04_recovery_controller_v10_admission_v2 as P

DELTA=['stage04_readonly_observer_role_v1.py','build_stage04_production_admission_v2.py',
 'test_stage04_readonly_observer_role_v1.py','prepare_stage04_production_tasks_admission_v2.py',
 'prepare_stage04_production_freeze_admission_v2.py','stage04_recovery_controller_v10_admission_v2.py',
 'stage04_recovery_validate_v10_admission_v2.py','final_check_stage04_recovery_v10_admission_v2.py',
 'check_stage04_recovery_acceptance_v10_admission_v2.py','activate_stage04_recovery_production_v10_admission_v2.ps1']

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        head=C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock);previous,_=OLD.acceptance()
        C.check(not P.PROPOSAL.exists() and not S.OUT.exists(),'Immutable revision2 proposal/output already exists')
        abort_path=S.REPORT/'production_admission_v1_pre_native_abort.json';abort=C.load(abort_path)
        C.check(C.digest(abort_path)=='dbbc5ccf5f45b9ce858bbaedec315bf3d64a45ae78ac303f5d95037a75587276' and
          abort['scientific_jobs_launched']==0 and abort['ordinary_scientific_success'] is False and
          abort['actual_controller_exit']['actual_exit_code']==1,'Preserved real pre-native abort required')
        prior_runtime=Path(previous['production_task']['runtime'])
        prior_observer=C.load(prior_runtime/'independent_controller_observer_binding.json')['actual_scheduler_observer']['actual_process']
        for actor in [abort['actual_controller_exit'],prior_observer]:
            C.check(S.process_identity(actor['pid'],actor['creation_filetime'])['state'] in
              ('ABSENT_WIN32_ERROR_INVALID_PARAMETER','EXITED','PID_REUSED_DIFFERENT_CREATION'),'Previous exact controller/observer unresolved')
        required=dict(previous['required_review_artifacts'])
        for path in [OLD.PROPOSAL,OLD.ACCEPTANCE,abort_path,S.ROOT/'scripts/record_stage04_production_pre_native_abort_v1.py']:
            required['data:'+path.relative_to(S.ROOT).as_posix()]=C.digest(path)
        required.update(abort['file_sha256'])
        registered=C.load(S.REPORT/'production_admission_v2_registered_tasks.json')
        request_path=Path(registered['production_request']);observer_path=Path(registered['observer_request'])
        request=C.load(request_path);observer=C.load(observer_path)
        C.check(request['mode']=='production' and observer['mode']=='observer' and observer['target_runtime']==request['runtime'],'Wrong new task roles')
        for value,path in ((request,request_path),(observer,observer_path)):
            C.check(path==Path(value['runtime'])/'task_request.json' and not Path(value['start_path']).exists(),'Revision2 task already started')
            query=C.load(value['query_path'])
            C.check(query['state']==3 and query['last_task_result']==267011 and query['triggers_count']==query['restart_count']==0 and
              query['actions_count']==1 and query['logon_type']==3 and query['run_level']==0 and query['multiple_instances']==2 and
              query['execution_time_limit']=='PT0S' and query['executable']==value['executable'] and query['arguments']==value['arguments'] and
              query['cwd']==value['cwd'] and C.digest(value['xml_path'])==value['definition_sha256'],'Actual unused task definition differs')
            for item in [path,Path(value['xml_path']),Path(value['query_path'])]:required['historical:'+item.relative_to(S.HISTORY).as_posix()]=C.digest(item)
        config=C.load(request['config'])
        C.check(config['production_admission_revision']=='V10_PRODUCTION_ADMISSION_V2' and config['analysis_names']==S.NAMES and
          request['argv']==['-u',str(S.ROOT/'scripts/stage04_recovery_controller_v10_admission_v2.py'),'--config',request['config']],
          'Exact new production config/action differs')
        guard=C.load(S.REPORT/'production_admission_v2_role_tests.json')
        C.check(guard['status']=='PASS_NEW_EXACT_OBSERVER_ROLE_GUARDS' and guard['tests']==18 and guard['errors']==guard['failures']==0 and
          guard['guard_source_sha256']==C.digest(S.ROOT/'scripts/stage04_readonly_observer_role_v1.py'),'New guard fixture/source mismatch')
        for name in DELTA:
            path=S.ROOT/'scripts'/name
            if path.suffix=='.py':ast.parse(path.read_text(encoding='utf-8-sig'))
            required['data:scripts/'+name]=C.digest(path)
        public_reports=['production_admission_v2_build.json','production_admission_v2_role_tests.json','production_admission_v2_registered_tasks.json']
        for path in [Path(request['config']),*[(S.REPORT/name) for name in public_reports]]:
            required['data:'+path.relative_to(S.ROOT).as_posix()]=C.digest(path)
        # Prior independently READY delta reviews bind unchanged admission1 source and policy bytes.
        for name in ['PARENT_V10_ADMISSION_V1_LIFETIME_DELTA_REVIEW.md','PARENT_V10_ADMISSION_V1_SCIENTIFIC_DELTA_REVIEW.md']:
            path=S.ROOT/'.work/host_review'/name;required['data:'+path.relative_to(S.ROOT).as_posix()]=C.digest(path)
        P.verify_artifacts(required)
        proposal={**previous,'schema':'V10_PRODUCTION_ADMISSION_V2_REVIEW_PROPOSAL_NOT_ADOPTION','utc':C.now(),
          'status':'NEW_HASH_BOUND_PARENT_ACCEPTANCE_REQUIRED_NOT_STARTED','canonical_main_at_preparation':head,
          'required_review_artifacts':required,'production_admission_revision':'V10_PRODUCTION_ADMISSION_V2',
          'production_delta_source_sha256':{name:C.digest(S.ROOT/'scripts'/name) for name in DELTA},
          'production_task':request,'production_readonly_observer_task':observer,
          'prior_adopted_proposal_sha256':C.digest(OLD.PROPOSAL),'prior_parent_acceptance_sha256':C.digest(OLD.ACCEPTANCE),
          'prior_pre_native_abort_sha256':C.digest(abort_path),'prior_admission_v1_runtime':str(prior_runtime),
          'observer_role_policy':'EXACT_ACCEPTED_LIVE_PID_CREATION_ARGV_FULL_TASK_DEFINITION_GUID_ENGINE_PID_ONLY',
          'failure_inventory':'NOT_PERSISTED_UNKNOWN_ALL_CANDIDATES','science_launches_this_preparation':0,
          'lifetime_fixture_repeated':False,'old_suites_repeated':0}
        A.validate_policy(proposal);C.atomic(P.PROPOSAL,proposal)
        expected={**required,'data:'+P.PROPOSAL.relative_to(S.ROOT).as_posix():C.digest(P.PROPOSAL)}
        outer={'decision':'ACCEPT_OBSERVED_SCHEDULER_BOUND_OUTER_JOB_LIFETIME','fixture_sha256':A.FIXTURE_SHA,
          'production_task_definition_sha256':request['definition_sha256'],'native_controls':'NESTED_OWNED_JOB_3GIB_MASK5_NO_BREAKAWAY',
          'old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY','static_controls_policy_sha256':C.digest(A.POLICY_PATH)}
        C.atomic(S.REPORT/'production_admission_v2_parent_expected_artifacts.json',{'schema':'EXPECTED_EXACT_PARENT_RECORD_NOT_ACCEPTANCE',
          'required_parent_record':str(P.ACCEPTANCE),'required_schema':'PARENT_RECOVERY_V10_HASH_BOUND_ACCEPTANCE','required_reviewer':'INDEPENDENT_PARENT',
          'required_decision':'ACCEPTED_FOR_SINGLE_PRODUCTION_START','production_task_name':request['task_name'],
          'artifact_sha256':expected,'outer_job_lifetime_review':outer,'proposal_sha256':C.digest(P.PROPOSAL)})
        body='# Owner production admission2 exact observer-role review request\n\n'
        body+='Prior admission1 parent acceptance was verified, and its one-shot start was consumed. Controller22112/creation134359851404203459 actually exited1; its source-gate child9256 exited1 with queried active0/[] before production_started, output mkdir or biological loop. Read-only observer24508 retained the same controller actual exit1; fresh full COM definitions show controllerResult1/observerResult0, bothState3/noinstances. Genuine original stableC byte0 lock reacquired with unchanged identity. Negative abort certificate '+C.digest(abort_path)+' preserves all receipts; no scientific output/launch exists. OriginalV6 actualnativeexit1 and UNKNOWN old controller/job closure remain unchanged.\n\n'
        body+='The failed gate did not persist its matching inventory; all candidate membership at failure remains UNKNOWN. Its predicate definitely matches the accepted observer actual saved argv (contains recovery_controller), and the owner-only comparison rejects that role. No claim that it was the only candidate is made.\n\n'
        body+='New immutable proposal '+P.PROPOSAL.relative_to(S.ROOT).as_posix()+' SHA256 '+C.digest(P.PROPOSAL)+', '+str(len(expected))+' exact artifacts. Expected parent record reports/stage04/recovery_v10/production_admission_v2_parent_expected_artifacts.json is NOT acceptance. Parent alone writes '+P.ACCEPTANCE.relative_to(S.ROOT).as_posix()+' with the exact map and required six-entry outer review. Prior PARENT_RECOVERY_V10_REVIEW.json remains unchanged and authorizes no new start.\n\n'
        body+='Changed source delta: production_admission_v2_build.json contains exact v1→v2 namespace/config/acceptance transformations plus only source-gate readonly-role classification and stored-proof/final joins. stage04_readonly_observer_role_v1.py requires accepted request/target/controller-binding SHA, exact parsed actual command line, fresh retained-handle PID/100ns creation/image/state before and after, CIM microsecond floor join, unchanged observer source, fresh full UTF16 COM definition hash and exact live GUID/EnginePID/state4. Only this positively identified observer is excluded. Others/null/unknown runners and old-instance access errors remain failclosed. Raw matching inventory is now persisted onC before the decision; full actual observer-role query/binding hashes enter the exclusive-boundary certificate and its inherited freeze/final checks. No substring/basename exemption.\n\n'
        body+='18focused synthetic rejection/argv fixtures passed, including wrongPID/reusedcreation, changedargv/image/task/instance, duplicate/missinginstances and another retainedcontroller. These test the new guard only; no old23suite, original120s lifetime mechanism, panel/tool/source scientific job or biological pilot repeated. Fresh actual production role proof remains pending execution. All33fixture sources, policy/service/staticouter guards, support/job/observer/outbox/publisher/cache/scientific checks, all four matrices, officialIQTREE/DLL, seed/options/caps remain the same exact bytes. Prior READY reviews can be reused only on matching hashes; review this new delta.\n\n'
        body+='New unique manual production '+request['task_name']+' and read-only observer '+observer['task_name']+' are registered NEVER_STARTED; exact definitions/requests/config are in the map. Original G scientific OUT remains absent. Parent acceptance must precede any start; fresh4.5GiBWindows/freephysicalC>5GiB/3GiBprocess+aggregate/twoPcoresmask5 gates remain. No recurrence, breakaway, guest boot, privilege bypass, source deletion or anonymousjob ownership assertion.\n\n'
        body+='After actual acceptance run scripts/check_stage04_recovery_acceptance_v10_admission_v2.py --request "'+str(request_path)+'" --observer-request "'+str(observer_path)+'", then scripts/activate_stage04_recovery_production_v10_admission_v2.ps1 -Request "'+str(request_path)+'" -ObserverRequest "'+str(observer_path)+'" once. Actual final checker scripts/final_check_stage04_recovery_v10_admission_v2.py still requires retained controllerexit0 and all4actualscientificcertificates/emptyjobs. Full196/162/196x88/155 inference and14cache restoration evidence remain NOT_RUN; Stage04scienceincomplete/05–07NOT_RUN. Actual releases/scientific validation, bothdetectors/784reviewedstates, circularfigure/finalhandoff remain required.\n'
        C.atomic(S.REPORT/'OWNER_PRODUCTION_ADMISSION_V2_REVIEW_REQUEST.md',body)
        C.atomic(S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_ADMISSION_V2_REVIEW_REQUEST.md',body)
        C.atomic(S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_REVIEW_REQUEST.md',body)
        C.atomic(S.REPORT/'production_admission_v2_preparation_receipt.json',{'utc':C.now(),'status':'EXACT_NEW_PROPOSAL_AND_UNUSED_TASKS_REVIEW_PENDING',
          'proposal_sha256':C.digest(P.PROPOSAL),'expected_artifacts':len(expected),'actual_stable_lock_identity':S.lock_identity(lock),
          'biological_jobs':0,'production':'NOT_STARTED','parent_acceptance':'NOT_GRANTED','old_suites_repeated':0,'lifetime_fixture_repeated':False,
          'whole_preparation_usage':None,'reason':'Preparation process-tree usage not measured; actual previous ordinary controlled-job usage retained'})
        status=S.ROOT/'STATUS.md';C.atomic(status,status.read_text()+'\n\n'+C.now()+': Versioned production admission2 proposal '+C.digest(P.PROPOSAL)+' prepared after preserved pre-native admission1 failure.18focused observer-role rejection fixtures passed. New unique zero-trigger production/observer tasks registered NEVER_STARTED; exact new parent acceptance REQUIRED/ABSENT. All earlier frozen source/proposal/acceptance/cache/scientific bytes retained, no old fixture/suite repeated. Stage04science FAILED/INCOMPLETE;05–07NOT_RUN.\n')
        state_path=S.ROOT/'status/stage04_execution.json';state=C.load(state_path);state.update(utc=C.now(),recovery='ADMISSION_V2_EXACT_OBSERVER_ROLE_REPAIR_PARENT_REVIEW_PENDING',
          proposal_sha256=C.digest(P.PROPOSAL),parent_acceptance='NEW_V2_REQUIRED_NOT_GRANTED',native_production='NOT_STARTED_NEW_V2',running_native_job=None)
        C.atomic(state_path,state)
        paths=['scripts/'+name for name in DELTA]+[P.PROPOSAL.relative_to(S.ROOT).as_posix(),Path(request['config']).relative_to(S.ROOT).as_posix(),
          'STATUS.md','status/stages.tsv','status/stage04_execution.json']
        paths += ['reports/stage04/recovery_v10/'+name for name in public_reports+['production_admission_v2_parent_expected_artifacts.json',
          'production_admission_v2_preparation_receipt.json','OWNER_PRODUCTION_ADMISSION_V2_REVIEW_REQUEST.md']]
        for directory in [S.REPORT/'production_task'/request['task_name'],S.REPORT/'observer_tasks'/observer['task_name']]:
            paths += [p.relative_to(S.ROOT).as_posix() for p in directory.iterdir() if p.is_file()]
        receipt=S.publish(paths,'Freeze exact live read-only observer role repair after preserved pre-native failure')
        C.atomic(S.REPORT/'production_admission_v2_publication_receipt.json',receipt)
        C.atomic(S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_ADMISSION_V2_PUBLICATION.json',receipt)
        print(json.dumps({'status':receipt['status'],'commit':receipt['commit'],'files_verified':len(receipt['file_sha256']),
          'proposal_sha256':C.digest(P.PROPOSAL),'expected_parent_artifacts':len(expected),'parent_acceptance':'NOT_GRANTED','biological_jobs':0}))

if __name__=='__main__':main()
