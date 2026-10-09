"""Guarded revision3 source generation; both earlier frozen candidates preserved."""
import ast,json
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_recovery_controller_v10_admission_v2 as P2

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock)
        previous=C.load(P2.PROPOSAL);P2.verify_artifacts(previous['required_review_artifacts'])
        C.check(not S.OUT.exists(),'Science/output already exists; no unreviewed revision')
        changes=[];generated={}
        def make(name,destination,patches):
            text=(S.ROOT/'scripts'/name).read_text(encoding='utf-8')
            for old,new in patches:
                n=text.count(old);C.check(n>0,'Missing guarded revision3 source fragment: '+old[:70])
                text=text.replace(old,new);changes.append({'source':name,'destination':destination,'old_fragment':old,'new_fragment':new,'occurrences':n})
            path=S.ROOT/'scripts'/destination
            if path.suffix=='.py':ast.parse(text)
            if path.exists():
                import hashlib
                C.check(C.digest(path)==hashlib.sha256(text.encode('utf-8')).hexdigest(),'Partial generated revision3 differs; preserve and choose new version')
            else:path.write_text(text,encoding='utf-8',newline='\n')
            generated[destination]=C.digest(path)
        common=[('_v10_admission_v2','_v10_admission_v3'),('V10_PRODUCTION_ADMISSION_V2','V10_PRODUCTION_ADMISSION_V3'),
          ('PARENT_RECOVERY_V10_ADMISSION_V2_REVIEW.json','PARENT_RECOVERY_V10_ADMISSION_V3_REVIEW.json'),
          ('host_inference_stage04_recovery_v10_production_admission_v2.json','host_inference_stage04_recovery_v10_production_admission_v3.json')]
        for name in ['stage04_recovery_controller_v10_admission_v2.py','stage04_recovery_validate_v10_admission_v2.py',
          'final_check_stage04_recovery_v10_admission_v2.py','check_stage04_recovery_acceptance_v10_admission_v2.py','activate_stage04_recovery_production_v10_admission_v2.ps1']:
            text=(S.ROOT/'scripts'/name).read_text();patches=[p for p in common if p[0] in text]
            if name in ['stage04_recovery_validate_v10_admission_v2.py','final_check_stage04_recovery_v10_admission_v2.py']:
                patches += [('import stage04_readonly_observer_role_v1 as R','import stage04_readonly_observer_role_v2 as R')]
            if name=='stage04_recovery_validate_v10_admission_v2.py':
                patches += [("'runner_inventory_sha256':inventory['runner_inventory_sha256'],","'runner_inventory_sha256':inventory['runner_inventory_sha256'],\n      'role_outcomes_sha256':inventory['role_outcomes_sha256'],")]
            make(name,name.replace('admission_v2','admission_v3'),patches)
        make('prepare_stage04_production_tasks_admission_v2.py','prepare_stage04_production_tasks_admission_v3.py',[
          ('admission_v2','admission_v3'),('ADMISSION_V2','ADMISSION_V3'),('ADMISSION2','ADMISSION3'),('revision2','revision3')])
        name='prepare_stage04_production_freeze_admission_v2.py';text=(S.ROOT/'scripts'/name).read_text()
        patches=[p for p in common if p[0] in text]
        patches += [('stage04_readonly_observer_role_v1.py','stage04_readonly_observer_role_v2.py'),
          ('build_stage04_production_admission_v2.py','build_stage04_production_admission_v3.py'),
          ('prepare_stage04_production_tasks_admission_v2.py','prepare_stage04_production_tasks_admission_v3.py'),
          ('prepare_stage04_production_freeze_admission_v2.py','prepare_stage04_production_freeze_admission_v3.py'),
          ('production_admission_v2_registered_tasks','production_admission_v3_registered_tasks'),
          ('production_admission_v2_build','production_admission_v3_build'),
          ('production_admission_v2_parent_expected','production_admission_v3_parent_expected'),
          ('production_admission_v2_preparation','production_admission_v3_preparation'),
          ('production_admission_v2_publication','production_admission_v3_publication'),
          ('OWNER_PRODUCTION_ADMISSION_V2','OWNER_PRODUCTION_ADMISSION_V3'),
          ('OWNER_RECOVERY_V10_ADMISSION_V2','OWNER_RECOVERY_V10_ADMISSION_V3'),
          ('Revision2','Revision3'),('revision2','revision3'),('admission2','admission3'),
          ("required=dict(previous['required_review_artifacts'])","required=dict(previous['required_review_artifacts'])\n        candidate2_path=S.ROOT/'config/host_inference_stage04_recovery_v10_admission_v2_freeze.json'\n        candidate2=C.load(candidate2_path);OLD.verify_artifacts(candidate2['required_review_artifacts'])\n        required.update(candidate2['required_review_artifacts'])\n        required['data:'+candidate2_path.relative_to(S.ROOT).as_posix()]=C.digest(candidate2_path)"),
          ("guard=C.load(S.REPORT/'production_admission_v2_role_tests.json')","guard=C.load(S.REPORT/'production_admission_v3_direct_join_tests.json')"),
          ("guard['status']=='PASS_NEW_EXACT_OBSERVER_ROLE_GUARDS' and guard['tests']==18","guard['status']=='PASS_NEW_DIRECT_JOINS_AND_FAILED_ROLE_PERSISTENCE' and guard['tests']==7"),
          ("guard['guard_source_sha256']","guard['role_guard_v2_source_sha256']"),
          ("'production_admission_v2_role_tests.json'","'production_admission_v3_direct_join_tests.json'"),
          ("'failure_inventory':'NOT_PERSISTED_UNKNOWN_ALL_CANDIDATES'","'superseded_unexecuted_candidate2_sha256':C.digest(candidate2_path),\n          'direct_role_policy':'ACTUAL_EXE_SOURCE_SHA_TARGET_CONFIG_DEFINITION_PLUS_EVERY_ROLE_OUTCOME_PERSISTED',\n          'failure_inventory':'NOT_PERSISTED_UNKNOWN_ALL_CANDIDATES'"),
          ("18focused synthetic rejection/argv fixtures passed","Seven new direct-target/hash/failure-persistence fixtures passed over the exact unchanged18 previously executed role-v1 fixtures"),
          ("18focused observer-role rejection fixtures passed","Seven new direct-target/hash/failure-persistence fixtures passed; old18 unchanged fixtures not rerun"),
          ("No substring/basename exemption.","Direct target config/definition, actual executable and accepted source SHA joins are also required; expected role requests and every PASS/FAIL evaluation are persisted onC before a rejection, with complete outcome digest required by boundary/final validation. Candidate2 remains preserved, unexecuted and superseded; its source bytes/18fixture report are inherited without rerunning. No substring/basename exemption.")]
        make(name,'prepare_stage04_production_freeze_admission_v3.py',patches)
        C.atomic(S.REPORT/'production_admission_v3_build.json',{'utc':C.now(),'status':'UNADOPTED_NARROW_DIRECT_ROLE_JOINS_OUTCOME_DELTA',
          'preserved_candidate2_proposal_sha256':C.digest(P2.PROPOSAL),'preserved_candidate2_source_sha256':previous['production_delta_source_sha256'],
          'generated_source_sha256':generated,'exact_text_changes':changes,
          'new_role_guard_source_sha256':C.digest(S.ROOT/'scripts/stage04_readonly_observer_role_v2.py'),
          'old18_role_guard_report_sha256':C.digest(S.REPORT/'production_admission_v2_role_tests.json'),
          'scientific_changes':0,'biological_jobs':0,'old_suite_or_lifetime_fixture_repeated':False})
        C.atomic(S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_ADMISSION_V2_SUPERSEDED.md',
          'Admission2 proposal and all bytes are preserved and NOT_STARTED. It is superseded by preparation of admission3 for the parent finding\'s direct config/definition/executable/source joins and mandatory retained per-role outcomes. Do not activate admission2. No science; same completed lifetime proof/methods/caps. New exact freeze/request follows.\n')
        print(json.dumps({'status':'ADMISSION3_NARROW_SOURCE_DELTA_BUILT_NOT_ADOPTED','sources':generated}))

if __name__=='__main__':main()
