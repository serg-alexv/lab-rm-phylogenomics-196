"""Freeze V10 only after actual CLI-exit fixture proof; never self-accept/launch."""
import argparse,json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fixture-config',required=True)
    parser.add_argument('--production-request',required=True);parser.add_argument('--observer-request',required=True);a=parser.parse_args()
    with C.WorkflowLock(S.LOCK) as lock:
        head=C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock)
        fixture_path=S.REPORT/'scheduler_fixture.json';fixture=C.load(fixture_path)
        C.check(fixture['status']=='PASS_THIS_ORIGINAL_CLI_EXIT_SAME_CREATIONS_ADVANCED_AND_ACTUAL_EMPTY_JOB_CONTROLLER_EXIT0',
          'Actual completed parent-bound original-CLI-exit fixture not validated')
        for key,sha in fixture['file_sha256'].items():
            role,rel=key.split(':',1);base=S.ROOT if role=='data' else S.HISTORY
            C.check(C.digest(base/rel)==sha,'Completed fixture artifact changed')
        request=C.load(a.production_request);observer=C.load(a.observer_request)
        C.check(request['mode']=='production' and observer['mode']=='observer' and observer['target_runtime']==request['runtime'],
          'Exact production/observer roles required')
        required=dict(fixture['file_sha256'])
        for value,supplied in ((request,a.production_request),(observer,a.observer_request)):
            C.check(Path(supplied)==Path(value['runtime'])/'task_request.json' and not Path(value['start_path']).exists(),'Unused exact task request required')
            query=C.load(value['query_path'])
            C.check(query['state']==3 and query['last_task_result']==267011 and query['triggers_count']==query['restart_count']==0 and
              C.digest(value['xml_path'])==value['definition_sha256'],'Unused production task definition/result evidence differs')
            for field in ('xml_path','query_path'):
                path=Path(value[field]);required['historical:'+path.relative_to(S.HISTORY).as_posix()]=C.digest(path)
            required['historical:'+Path(supplied).relative_to(S.HISTORY).as_posix()]=C.digest(supplied)
        source_names=[p.name for p in (S.ROOT/'scripts').glob('*v10*.py')]+[p.name for p in (S.ROOT/'scripts').glob('*v10*.ps1')]
        source_names+=['stage04_controller.py','workflow_publication.py','supplemental_native_v6_final_check.py']
        for name in sorted(set(source_names)):required['data:scripts/'+name]=C.digest(S.ROOT/'scripts'/name)
        for rel in [*S.FROZEN,'AGENTS.md','WORK_ORDER.md','config/approval.json','config/approved_accessions.txt']:
            required['data:'+rel]=C.digest(S.ROOT/rel)
        for path in [S.NEGATIVE,fixture_path,S.REPORT/'boundary_cache_delta_tests.json',S.REPORT/'guard_tests.json',
          S.REPORT/'stdio_overlap_fixture.json',Path(request['config']),Path(a.fixture_config).resolve(),
          S.OLD/'inference_freeze.json',S.OLD/'analyses/primary196/iqtree/host.model.gz']:
            required['data:'+path.relative_to(S.ROOT).as_posix()]=C.digest(path)
        old=C.load(S.OLD/'inference_freeze.json');required.update(old['source_identity']['file_sha256'])
        for path in [Path(old['executable']),Path(old['executable']).parent/'libiomp5md.dll']:
            required['historical:'+path.relative_to(S.HISTORY).as_posix()]=C.digest(path)
        proposal={'schema':'V10_REVIEW_PROPOSAL_NOT_PRODUCTION_ADOPTION','utc':C.now(),'status':'PARENT_REVIEW_REQUIRED_NOT_ADOPTED_NOT_EXECUTED',
          'canonical_main_at_preparation':head,'required_review_artifacts':required,'old_immutable_freeze_sha256':S.FREEZE_SHA,
          'negative_history_certificate_sha256':C.digest(S.NEGATIVE),'scheduler_fixture_sha256':C.digest(fixture_path),
          'production_task':request,'production_readonly_observer_task':observer,'existing_accepted_source_identity':old['source_identity'],
          'fixed_external_interpreters':[{'path':str(p),'sha256':C.digest(p)} for p in [S.PYTHON,S.PYTHONW,S.VALIDATOR]],
          'native_contract':{'process_and_aggregate_committed_cap_bytes':3221225472,'affinity_mask':5,'threads':2,
            'windows_available_minimum_bytes':4831838208,'root':'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP'},
          'science_launches_this_preparation':0,'old_ordinary_controller_outcome':'UNKNOWN','old_job_closure':'UNKNOWN'}
        freeze=S.ROOT/'config/host_inference_stage04_recovery_v10_freeze.json';C.check(not freeze.exists(),'Immutable proposal already exists; a repair requires a new revision')
        C.atomic(freeze,proposal)
        C.atomic(S.REPORT/'parent_review_expected_artifacts.json',{'schema':'EXPECTED_REVIEW_ARTIFACTS_NOT_AN_ACCEPTANCE',
          'artifact_sha256':{**required,'data:config/host_inference_stage04_recovery_v10_freeze.json':C.digest(freeze)},
          'required_parent_record':str(S.ROOT/'.work/host_review/PARENT_RECOVERY_V10_REVIEW.json'),
          'required_schema':'PARENT_RECOVERY_V10_HASH_BOUND_ACCEPTANCE','required_reviewer':'INDEPENDENT_PARENT',
          'required_decision':'ACCEPTED_FOR_SINGLE_PRODUCTION_START','production_task_name':request['task_name']})
        print(json.dumps({'status':'FROZEN_FOR_HASH_BOUND_PARENT_REVIEW_NOT_ADOPTED','proposal_sha256':C.digest(freeze),'artifacts':len(required)+1}))

if __name__=='__main__':main()
