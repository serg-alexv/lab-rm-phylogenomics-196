"""Publish honest prepared repair evidence; never adopts or starts native biology."""
import json, shutil
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        head=C.reconcile(S.ROOT);S.held_lock_matches_negative(lock)
        old=S.ROOT/'config/host_inference_stage04_recovery_v9_freeze.json';prior=C.load(old)
        for key,sha in prior['required_review_artifacts'].items():
            if key.startswith('data:scripts/'):C.check(C.digest(S.ROOT/key.split(':',1)[1])==sha,'Frozen V9 source changed')
        review=C.load(S.ROOT/'.work/host_review/PARENT_RECOVERY_V9_REVIEW.json')
        C.check(review['decision']=='REPAIR_REQUIRED','Unexpected parent review decision; reread before preparation publication')
        repairs={'FRESH_BOUNDARY_AND_LOCK_IDENTITY':'Actual retained byte0 lock volume/index/creation equals immutable negative certificate; source-gate child verifies held lock plus fresh exact old-instance/runner reconciliation.',
          'ACTUAL_SCHEDULER_CONFIG_BINDING':'Controller parses own Win32 argv and queries live COM definition/SID/action/config and actual running instance EnginePID/GUID; production config equals accepted request.',
          'PER_SCOPE_FROZEN_SCIENTIFIC_BYTES':'Exact accepted per-scope input/executable/DLL hashes before and after native and checker; independent audit compares inherited original freeze fields and current hashes.',
          'CONCURRENT_INHERITABLE_STDIO':'One process-wide lock spans set-inheritable/CreateProcess/reset; two concurrent prepared child fixtures probe exact foreign stdout/stderr file identities.',
          'EXACT_CACHE_REUSE_EVIDENCE':'Exact new-prefix model-load and fast-tree restoration messages, byte-identical import;0/100 progress allowed; inherited cache14 records preserved.',
          'HONEST_TERMINAL_PUBLICATION':'Exit0 is validation pending; nonzero is failed; terminal publication attempted boundedly after native closes, with local remote-unverified failure isolated.',
          'EXACT_PUBLICATION_OBSERVATION_ACK':'Immutable individual observation files and SHA passed to publisher; each ack binds exact observation and actual verified remote bytes.'}
        fixture=S.REPORT/'stdio_overlap_fixture.json';C.check(C.load(fixture)['status'].startswith('PASS_OVERLAPPING'),'Meaningful handle overlap fixture failed')
        tests=S.REPORT/'guard_tests.json';C.check(C.load(tests)['tests']==28 and C.load(tests)['status'].startswith('PASS_'),'Repair guards failed')
        public_sources=sorted(p.relative_to(S.ROOT).as_posix() for p in (S.ROOT/'scripts').glob('*v10.*') if p.suffix in ('.py','.ps1'))
        core={p:C.digest(S.ROOT/p) for p in public_sources}
        C.atomic(S.REPORT/'repair_preparation.json',{'utc':C.now(),'status':'V10_REPAIR_CANDIDATES_TESTED_NOT_ADOPTED_NOT_BIOLOGICALLY_EXECUTED',
          'parent_prior_review_sha256':C.digest(S.ROOT/'.work/host_review/PARENT_RECOVERY_V9_REVIEW.json'),
          'old_v9_freeze_sha256':C.digest(old),'source_sha256':core,'parent_findings_response':repairs,
          'stdio_fixture_sha256':C.digest(fixture),'guard_tests_sha256':C.digest(tests),'actual_stable_lock_identity':S.lock_identity(lock),
          'post_original_cli_exit_lifetime_proof':'PENDING_REQUIRED_120_SECOND_SYNTHETIC_HANDOFF',
          'scientific_jobs':0,'stage04':'FAILED_INCOMPLETE','stages05_07':'NOT_RUN','parent_production_acceptance':'NOT_GRANTED'})
        doc='# V10 repair of preserved V9 candidate\n\nParent early V9 review requires repairs. V9 source/config/proposal and all prior fixtures remain unchanged; V6 failure/unknown closure remain separate negative history. V10 is a new candidate, not adoption.\n\n'+ '\n\n'.join('**'+k+'**: '+v for k,v in repairs.items())+'\n\n28 focused guards and the actual overlapping synthetic handle fixture passed. No biological job ran. The required120-second direct Scheduler child/grandchild fixture must survive the ORIGINAL external CLI natural exit with independent parent before/after exact creation observations; proof is currently pending. IsProcessInJob(NULL) TRUE remains explicit anonymous shared outer-job membership, not inferred ownership. Parent production acceptance still required.\n'
        (S.REPORT/'REPAIR_RESPONSE.md').write_text(doc,encoding='utf-8',newline='\n')
        status=S.ROOT/'STATUS.md';text=status.read_text();text+='\nRecovery update '+C.now()+': V9 preserved; parent decision REPAIR_REQUIRED. New V10 candidate repairs and28 guards/actual overlapping-stdio fixture completed. Required120-second original-CLI-exit lifetime proof and final hash-bound parent acceptance remain pending. Production remains FAILED/INCOMPLETE;05–07 NOT_RUN.\n';status.write_text(text,encoding='utf-8',newline='\n')
        C.atomic(S.ROOT/'status/stage04_execution.json',{'utc':C.now(),'execution':'FAILED_INCOMPLETE_NATIVE_EXIT1','old_controller_outcome':'UNKNOWN',
          'old_job_closure':'UNKNOWN','recovery':'V10_PREPARATION_NOT_ADOPTED_120S_LIFETIME_PROOF_PENDING','stages05_07':'NOT_RUN'})
        v9sources=[k.split(':',1)[1] for k in prior['required_review_artifacts'] if k.startswith('data:scripts/')]
        reports=[p.relative_to(S.ROOT).as_posix() for p in (S.ROOT/'reports/stage04/recovery_v9').rglob('*') if p.is_file()]
        reports += [p.relative_to(S.ROOT).as_posix() for p in S.REPORT.rglob('*') if p.is_file()]
        configs=[p.relative_to(S.ROOT).as_posix() for p in (S.ROOT/'config').glob('host_inference_stage04_recovery_v9*.json')]
        paths=list(dict.fromkeys(['STATUS.md','WORK_ORDER.md','status/stages.tsv','status/stage04_execution.json','scripts/build_stage04_recovery_v10.py',
          'scripts/supplemental_native_v6_final_check.py','scripts/stage04_closed_boundary_v2.py',*v9sources,*public_sources,*reports,*configs]))
        receipt=S.publish(paths,'Preserve V9 recovery candidate and record tested V10 repairs; production remains blocked')
        C.atomic(S.REPORT/'preparation_publication_receipt.json',receipt)
        print(json.dumps({'status':receipt['status'],'commit':receipt['commit'],'files_verified':len(receipt['file_sha256'])}))

if __name__=='__main__':main()
