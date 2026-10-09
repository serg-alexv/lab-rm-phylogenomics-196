"""Pin/publish the concrete fixture handoff; never launch or self-accept science."""
import ast,json,shutil
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

FIXTURE=S.RUNTIME/'fixture/LAB_RM_Stage04_V10_fixture_3f24a4052611'
OBSERVER=S.RUNTIME/'observers/LAB_RM_Stage04_V10_readonly_observer_a785f5509111'

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        head=C.reconcile(S.ROOT);S.pins();S.held_lock_matches_negative(lock)
        C.check(not (FIXTURE/'task_start.json').exists() and not (OBSERVER/'task_start.json').exists(),'Fixture/observer already started; no duplicate handoff')
        cli=S.process_identity(15584,134359775147405364);C.check(cli['state']=='RUNNING','Exact original CLI no longer live; different proof needed')
        current_tests={}
        for name,count in [('guard_tests.json',28),('boundary_cache_delta_tests.json',14)]:
            value=C.load(S.REPORT/name);C.check(value['status'].startswith('PASS_') and value['tests']==count and value['errors']==value['failures']==0,'Focused guards not passing')
            current_tests[name]=C.digest(S.REPORT/name)
        sources=sorted({p.relative_to(S.ROOT).as_posix() for pattern in ('*v10*.py','*v10*.ps1') for p in (S.ROOT/'scripts').glob(pattern)}|
          {'scripts/stage04_controller.py','scripts/workflow_publication.py','scripts/supplemental_native_v6_final_check.py',
            'scripts/prepare_stage04_v10_cli_exit_handoff_v1.py'})
        source_map={'data:'+name:C.digest(S.ROOT/name) for name in sources}
        for name in sources:
            if name.endswith('.py'):ast.parse((S.ROOT/name).read_text(encoding='utf-8-sig'),filename=name)
        guard=C.load(S.REPORT/'guard_tests.json');delta=C.load(S.REPORT/'boundary_cache_delta_tests.json')
        C.check(guard['adoption_source_sha256']==C.digest(S.ROOT/'scripts/stage04_recovery_controller_v10.py') and
          guard['cache_parser_sha256']==C.digest(S.ROOT/'scripts/stage04_model_cache_evidence_v10.py'),'Guard evidence does not bind current sources')
        for name,sha in delta['checked_source_sha256'].items():C.check(C.digest(S.ROOT/'scripts'/name)==sha,'Delta fixture source drifted')
        old_proposal=C.load(S.ROOT/'config/host_inference_stage04_recovery_v9_freeze.json')
        for key,sha in old_proposal['required_review_artifacts'].items():
            if key.startswith('data:scripts/'):C.check(C.digest(S.ROOT/key.split(':',1)[1])==sha,'Frozen V9 source changed')
        review_path=S.ROOT/'.work/host_review/PARENT_RECOVERY_V9_REVIEW.json';review=C.load(review_path)
        C.check(review['decision']=='REPAIR_REQUIRED','Parent review changed; reconcile before handoff')
        guidance=S.ROOT/'.work/host_review/PARENT_RECOVERY_V9_OUTER_JOB_FIXTURE_GUIDANCE_0001.md'
        snapshot={'schema':'V10_CANDIDATE_PRESTART_SNAPSHOT_NOT_ADOPTION','utc':C.now(),'status':'REGISTERED_NOT_STARTED_PARENT_AFTER_CLI_EXIT_PROOF_PENDING',
          'canonical_main_before_preparation':head,'source_sha256':source_map,'original_cli':cli,
          'negative_history_certificate_sha256':C.digest(S.NEGATIVE),'preserved_v9_freeze_sha256':C.digest(S.ROOT/'config/host_inference_stage04_recovery_v9_freeze.json'),
          'original_v6_freeze_sha256':S.FREEZE_SHA,'original_cache_sha256':S.CACHE_SHA,'actual_stable_lock_identity':S.lock_identity(lock),
          'parent_review_sha256':C.digest(review_path),'parent_guidance_sha256':C.digest(guidance),'focused_test_sha256':current_tests,
          'stdio_overlap_fixture_sha256':C.digest(S.REPORT/'stdio_overlap_fixture.json'),
          'tasks_before_source_pin':[C.load(p/'task_request.json') for p in (FIXTURE,OBSERVER)],
          'biological_jobs':0,'scientific_status':'STAGE04_FAILED_INCOMPLETE_STAGE05_07_NOT_RUN',
          'required_after_original_cli_exit':'Independent same-creation controller/native/grandchild advancing, actual native exit0/emptyownedjob, independently observed controller exit0 and actual Scheduler results0',
          'final_freeze':'NOT_WRITTEN_UNTIL_COMPLETED_LIFETIME_PROOF','parent_acceptance':'NOT_GRANTED'}
        target=S.ROOT/'config/host_inference_stage04_recovery_v10_preparation_snapshot_0002.json'
        C.check(not target.exists(),'Snapshot immutable; choose a new explicit revision')
        C.atomic(target,snapshot)
        for runtime in (FIXTURE,OBSERVER):
            path=runtime/'task_request.json';original=C.load(path)
            shutil.copy2(path,runtime/'task_request_before_source_pin_0001.json')
            pinned={**original,'candidate_source_sha256':source_map,'candidate_snapshot':str(target),'candidate_snapshot_sha256':C.digest(target)}
            C.atomic(path,pinned)
            report=S.REPORT/('fixture_task' if runtime==FIXTURE else 'observer_tasks')/original['task_name']
            shutil.copy2(path,report/'request_source_pinned_0002.json')
        responses={
          'FRESH_BOUNDARY_AND_LOCK_IDENTITY':'Held Win32 lock identity equality; fresh exact old-descendant/runner inventory certificate now binds owner, actual lock and negative SHA and is SHA-bound into new inference freeze/scope/final checks.',
          'ACTUAL_SCHEDULER_CONFIG_BINDING':'Live COM full XML/action/SID/actual GUID+EnginePID and actual process argv/config; supplied production/observer requests must exactly equal accepted proposal; final observer source/request/action/definition/closure joins and actual task results required.',
          'PER_SCOPE_FROZEN_SCIENTIFIC_BYTES':'Accepted per-scope inputs, partitions, labels, executable/DLL before/after native, independent check and final boundary; all original freeze fields equal old frozen values; current adopted sources checked before/after checker and last scope.',
          'EXACT_CACHE_REUSE_EVIDENCE':'Exact new-prefix load/fast-tree restoration; retained gzip read-only14 BIC decisions plus selected candidate logL/df/tree-length and BIC scores must remain literal-value identical in final exact100-partition cache,86 new decisions. Actual production reuse NOT_RUN.',
          'HONEST_TERMINAL_PUBLICATION':'All published states derive actual integer native exit and as-of UTC/PID/creation; exit0 awaiting validation and nonzero failed distinct; separate bounded post-native terminal attempt is preserved and cannot affect native lifetime.',
          'EXACT_PUBLICATION_OBSERVATION_ACK':'Every observation is an immutable SHA-bound publisher input; exact SHA acknowledgements require actual remote byte readback. Failed synthetic publisher is explicit remote-unverified.',
          'CONCURRENT_INHERITABLE_STDIO':'Parent snapshot0002 classified old flow informational/no reachable overlap; extra global inheritable-window lock and actual two-child foreign-file identity probe remain as tested defense.'}
        body='# Owner recovery V10 review / original-CLI-exit handoff\n\n'
        body+='Stage04 scientific FAILED/INCOMPLETE; Stage05–07 NOT_RUN. No biological job launched. V6/V9 frozen sources/configs/proposal and old failure/unknown receipts remain unchanged. V10 is a new unadopted repair candidate.\n\n'
        body+='The completed negative certificate remains '+C.digest(S.NEGATIVE)+'. Actual old native exit1/CPU16131.484375s are separate from UNKNOWN old controller outcome/final job closure; no cause inferred. Verified failure Release: stage04c-native-failure196-v1,467985B,SHA256bddcff6ad39c0a7cf78d4cb79be5be3b45e59906e02748d6f3c7c31734eec8f2.\n\n'
        body+='Read config/host_inference_stage04_recovery_v10_preparation_snapshot_0002.json (SHA256'+C.digest(target)+'), this versioned source map,14 new drift/cache fixtures,28 recovery guards, and the actual overlapping stdio fixture. These are code/lifetime preparation, never scientific PASS. Parent REVIEW remains REPAIR_REQUIRED.\n\n'
        body+='## Parent findings and candidate response\n\n'+ '\n\n'.join('**'+k+'**: '+v for k,v in responses.items())+'\n\n'
        body+='## Required bounded fixture proof\n\nThis follows .work/host_review/PARENT_RECOVERY_V9_OUTER_JOB_FIXTURE_GUIDANCE_0001.md (SHA256'+C.digest(guidance)+'). Same logged-in SID/interactive/limited direct pythonw controller; unique manual zero-trigger/restart tasks,IgnoreNew,PT0S. Actual exported definitions and all executable sources/configs/request bytes are pinned before start. Controller live COM/argv validation precedes the synthetic native child. Root120s and grandchild112s;128MiB owned cap,180s deadline; no biological data. TRUE outer-job membership stays anonymous/unproved, only allowed as this explicit synthetic observation; no breakaway or ownership inferred.\n\n'
        body+='Controller request: '+str(FIXTURE/'task_request.json')+'\n\nRead-only observer request: '+str(OBSERVER/'task_request.json')+'\n\nStarter: scripts/start_stage04_recovery_task_v10.ps1 -Request <controller request>, then scripts/start_stage04_recovery_observer_v10.ps1 -Request <observer request>. Before-exit checker: scripts/check_stage04_fixture_before_cli_exit_v10.py --config config/host_inference_stage04_recovery_v10_fixture.json. It records C runtime/before_original_cli_exit_handoff.json and reports/stage04/recovery_v10/before_original_cli_exit_handoff.json with exact live creations and advancing ticks.\n\n'
        body+='The owner ends ORIGINAL CLI15584/creation134359775147405364 NATURALLY immediately after that live check. Parent must retain its actual handle/exit and prove SAME three creations live/advancing AFTER exit, then actual child exit0/jobActive0/exactemptyPIDlist, independent retained-handle controller exit0 plus controller/observer Task result0. Do not accept absence/sentinel or an in-process closure alone. This tests one particular CLI-exit lifetime, not universal outer ownership. No unrelated poller or recurrent task.\n\n'
        body+='Parent evidence path requested: .work/host_review/PARENT_RECOVERY_V10_ORIGINAL_CLI_EXIT_FIXTURE.json, schema PARENT_V10_ORIGINAL_CLI_EXIT_LIFETIME_EVIDENCE, reviewer INDEPENDENT_PARENT, before_handoff_sha256, original_cli_exit (actual pid/creation/state/exitcode/exitFILETIME), controller_after_cli_exit/native_after_cli_exit/grandchild_after_cli_exit (same pid/creation,stateRUNNING), first_after_cli_exit_tick/later_after_cli_exit_tick (bothUTC after actual CLIexit, same nativepid, increasingtick). Preserve actual retained-handle/source evidence paths/hashes additionally. This evidence is NOT acceptance.\n\n'
        body+='After the parent proof and actual fixture closure, resume SAME external session through a fresh private attempt. Run scripts/check_stage04_recovery_fixture_v10_2.py --config config/host_inference_stage04_recovery_v10_fixture.json to independently validate actual completed evidence. Initial cloned v10 fixture/review scripts now reject CLI execution and point to _v10_2; no55s waiter. No production task/freezer/output exists yet forV10. Register unused exact V10 production/observer tasks, then scripts/prepare_stage04_recovery_review_v10_2.py with --fixture-config/--production-request/--observer-request binds completed proof and every adopted source/input/tool/fixture into immutable config/host_inference_stage04_recovery_v10_freeze.json.\n\n'
        body+='Parent alone then reviews all current exact bytes and writes .work/host_review/PARENT_RECOVERY_V10_REVIEW.json: schema PARENT_RECOVERY_V10_HASH_BOUND_ACCEPTANCE,decision ACCEPTED_FOR_SINGLE_PRODUCTION_START,reviewer INDEPENDENT_PARENT,exactartifact_sha256 map (including newfreeze),production_task_name and explicit outer_job_lifetime_review required by controller acceptance(). No barePASS/adoption by existence. If repairs required, use new versioned freeze/sources. Production remains blocked until this succeeds; afterwards serial unchanged four scientific scopes require new real ordinary exit0/emptyjob and unchanged scientific parsers/support checks, final actual controller closure, portable verified scientific release, then Stage05 actual lifetime/interoperability and both biological detectors, Stage06 real196tip/784cell figure, Stage07 real-data validation/handoff.\n'
        request=S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_REVIEW_REQUEST.md';C.atomic(request,body)
        report=S.REPORT/'OWNER_REVIEW_REQUEST_0002.md';C.atomic(report,body)
        previous=S.ROOT/'.work/host_review/OWNER_RECOVERY_V9_REVIEW_REQUEST.md'
        C.atomic(previous,previous.read_text(encoding='utf-8')+'\n\nV10 delta/original-CLI-exit handoff: OWNER_RECOVERY_V10_REVIEW_REQUEST.md; current candidate snapshot '+C.digest(target)+'. V9 preserved; NOT production acceptance.\n')
        C.atomic(S.REPORT/'repair_preparation_0002.json',{'utc':C.now(),'status':'PINNED_UNADOPTED_V10_REPAIR_CANDIDATE_120S_ORIGINAL_CLI_EXIT_PROOF_PENDING',
          'snapshot_sha256':C.digest(target),'source_sha256':source_map,'parent_findings_response':responses,'focused_tests':current_tests,
          'controller_request_sha256':C.digest(FIXTURE/'task_request.json'),'observer_request_sha256':C.digest(OBSERVER/'task_request.json'),
          'actual_stable_lock_identity':S.lock_identity(lock),'stage04':'FAILED_INCOMPLETE','stages05_07':'NOT_RUN','scientific_jobs':0,
          'parent_acceptance':'NOT_GRANTED','preparation_cpu_seconds':None,'preparation_peak_ram_bytes':None,
          'usage_unavailable_reason':'Whole preparation process tree was not measured; fixture/native metrics are recorded by actual job observers'})
        rows=(S.ROOT/'status/stages.tsv').read_text().splitlines()
        rows=[r.replace('STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING','STAGE04A_STAGE04B_STAGE04C_FAILURE_UPLOAD_VERIFIED_FULL_STAGE04_PENDING') if r.startswith('4_phylogeny\t') else r for r in rows]
        C.atomic(S.ROOT/'status/stages.tsv','\n'.join(rows)+'\n')
        table='\n'.join('| '+' | '.join(r.split('\t'))+' |' for r in rows[1:])
        status='# Current execution status\n\nUpdated '+C.now()+'. Full approved196 production; no pilot.\n\n'
        status+='Stage04 primary native PID29132/creation134359651870883542 actually exited1 at2026-10-08T23:30:02.6498313Z; CPU16131.484375s. Cause not established. Original controller outcome/final job closure remain UNKNOWN and missing ordinary receipts stay absent. All original outputs/model cache preserved. Completed stages0–3/04a retained.\n\n'
        status+='V10 recovery candidate '+C.digest(target)+' prepared, not adopted.28 focused guards,14 new drift/cache fixtures and actual overlapping stdio fixture passed; no biological job ran. New120-second fixture/observer tasks are REGISTERED_NOT_STARTED as of this update. Original-CLI-exit survival and actual final fixture closure remain pending parent observation; TRUE anonymous outer-job ownership is not inferred. Exact live start/identities will be retained in stableC and reports/stage04/recovery_v10/before_original_cli_exit_handoff.json.\n\n'
        status+='Native failed-attempt evidence is now separately published/read back in Windows-openable release stage04c-native-failure196-v1 (467985B,SHA256bddcff6ad39c0a7cf78d4cb79be5be3b45e59906e02748d6f3c7c31734eec8f2; everyZIPmember checked). This is failure evidence, not scientific completion.\n\n'
        status+='| Stage | Execution | Validation | Publication |\n|---|---|---|---|\n'+table+'\n\n'
        status+='Production retry is blocked by the user-required independent hash-bound parent recovery review, currently REPAIR_REQUIRED. Final V10 proposal/acceptance are not yet written; Stages05–07 remain NOT_RUN. See reports/stage04/recovery_v10/OWNER_REVIEW_REQUEST_0002.md.\n'
        C.atomic(S.ROOT/'STATUS.md',status)
        C.atomic(S.ROOT/'status/stage04_execution.json',{'utc':C.now(),'execution':'FAILED_INCOMPLETE_NATIVE_EXIT1','actual_failed_native_pid':29132,
          'actual_failed_native_creation_filetime':134359651870883542,'actual_failed_native_exit_utc':'2026-10-08T23:30:02.6498313Z',
          'native_cpu_seconds':16131.484375,'old_controller_outcome':'UNKNOWN','old_job_closure':'UNKNOWN',
          'recovery':'V10_CANDIDATE_PINNED_120S_ORIGINAL_CLI_EXIT_PROOF_PENDING','fixture_as_of_utc':C.now(),
          'fixture_execution':'REGISTERED_NOT_STARTED','snapshot_sha256':C.digest(target),'scientific_validation':'INCOMPLETE','stages05_07':'NOT_RUN'})
        order=S.ROOT/'WORK_ORDER.md';text=order.read_text(encoding='utf-8')
        C.check('## Recovery V10 original-CLI lifetime amendment' not in text,'Work order amendment already exists')
        C.atomic(order,text+'\n## Recovery V10 original-CLI lifetime amendment (2026-10-09)\n\nThe user-required V9 parent review requested repairs; preserve V6/V9 source/config/freeze and all negative history. A separate V10 candidate now binds the retained lock identity, fresh process boundary, actual live Scheduler action/instance, per-scope scientific bytes, inherited/new model-cache records and honest bounded SHA-bound publication. No scientific scope/options/tool/seed/resource-gate change. Parent specifically authorized one120-second synthetic direct-controller/grandchild fixture with natural ORIGINAL CLI exit while live, independent before/after exact creation/progress observation, actual native empty-job exit and independent controller/Task result0. This is not a biological pilot or proof of anonymous outer-job ownership. Final V10 freeze is prepared only after completed proof; production requires the independent parent hash-bound PARENT_RECOVERY_V10_REVIEW.json naming every adopted artifact and explicit actual outer-job lifetime review. Old V9 acceptance is not reused. No automatic reset/recurrent triggers/reboot. See reports/stage04/recovery_v10/OWNER_REVIEW_REQUEST_0002.md for actual paths/commands and unexecuted dependencies.\n')
        paths=[*sources,'config/host_inference_stage04_recovery_v10_fixture.json',target.relative_to(S.ROOT).as_posix(),
          report.relative_to(S.ROOT).as_posix(),'reports/stage04/recovery_v10/repair_preparation_0002.json',
          'reports/stage04/recovery_v10/guard_tests.json','reports/stage04/recovery_v10/boundary_cache_delta_tests.json',
          'STATUS.md','WORK_ORDER.md','status/stages.tsv','status/stage04_execution.json']
        for sub in ('fixture_task/LAB_RM_Stage04_V10_fixture_3f24a4052611','observer_tasks/LAB_RM_Stage04_V10_readonly_observer_a785f5509111'):
            paths += [p.relative_to(S.ROOT).as_posix() for p in (S.REPORT/sub).iterdir() if p.is_file()]
        receipt=S.publish(list(dict.fromkeys(paths)),'Bind V10 recovery repairs and original-CLI-exit fixture handoff; science remains incomplete')
        C.atomic(S.REPORT/'handoff_publication_receipt_0002.json',receipt)
        C.atomic(S.ROOT/'.work/host_review/OWNER_RECOVERY_V10_HANDOFF_PUBLICATION.json',receipt)
        print(json.dumps({'status':receipt['status'],'commit':receipt['commit'],'files_verified':len(receipt['file_sha256']),
          'snapshot_sha256':C.digest(target),'review_request':str(request),'fixture':'REGISTERED_NOT_STARTED','science':'NOT_ACCEPTED_NOT_LAUNCHED'}))

if __name__=='__main__':main()
