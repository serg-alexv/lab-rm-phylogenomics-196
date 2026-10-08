"""Publish executed preparation checks, preserved errors and observer repair."""
from pathlib import Path
import hashlib, subprocess
import stage04_controller as C
import production_resume as w
from workflow_publication import commit
ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
w.LOG=ROOT/'reports/stage04/postboot_review_publication_commands.jsonl'

def main():
    with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
        C.reconcile(ROOT)
        lock=C.load(ROOT/'reports/stage04/resource_wait_v5_v2/serialization_test.json')
        selection=C.load(ROOT/'reports/stage05/preparation_selection_v4/review.json')
        C.check(lock['status']=='PASS_ACTUAL_WINDOWS_BYTE_LOCK_CONTENTION_AND_DUPLICATE_GUARD_ISOLATED_ONLY'
                and lock['waiter_source_sha256']==C.digest(ROOT/'scripts/wait_migration_v5_headroom_v2.py'), 'Executed serialization proof differs')
        C.check(selection['status']=='PASS_SYNTHETIC_NATIVE_SELECTION_EQUIVALENCE_PREPARATION_ONLY'
                and selection['python_negative_and_regression_tests']==24 and selection['installed_native_R_cases']==17,'Executed selection preparation proof differs')
        for item in selection['sources']:
            C.check(C.digest(ROOT/item['path'])==item['sha256'],'Selection review source changed')
        failure=ROOT/'reports/stage04/resource_wait_v5_v2/prior_observer_stop.json'
        C.atomic(failure,{'utc':C.now(),'prior_actual_observer_pid':27640,'actual_session_exit_code':1,
            'actual_last_observation_utc':'2026-10-08T19:34:17.1631736Z',
            'actual_error':'Actual workflow byte lock is held; no competing launch permitted',
            'cause':'Authorized synthetic preparation writer held the same native C byte lock; fail-fast observation exited',
            'no_lock_bypassed':True,'replacement':'scripts/wait_migration_v5_headroom_v2.py',
            'replacement_actual_serialization_test_sha256':C.digest(ROOT/'reports/stage04/resource_wait_v5_v2/serialization_test.json'),
            'inference_started':False,'replacement_launch':'PENDING_AFTER_THIS_PUBLICATION'})
        (ROOT/'reports/stage05/preparation_selection_v4/README.md').write_text(
            '# Executed PADLOC selection preparation\n\n'
            'Full196 source coordinate audit: 411523 exact assembly/replicon/locus context rows; no coincident native coordinate groups. Raw identities remain separate from grouping geometry.\n\n'
            'A separate revision implements the installed PADLOC2 coordinate grouping and overlapping-role precedence. All24 Python negative/regression tests and17 evaluations of expressions parsed from the exact installed PADLOC R source passed. The oracle did not source the CLI, cluster systems or search biological sequences. Native wall2.32s, CPU1.48s, peakRSS112668672bytes, R address-space cap1GiB. Exact argv and /usr/bin/time output are retained.\n\n'
            'The first attempt exited125 before R because the historical tool wrapper did not mount G. Its command/stderr are preserved in preparation_selection_v3. The successor used the exact reviewed migration bootstrap and a separate explicit detector-environment entry, which mounted G and wrote the actual result there.\n\n'
            'This is preparation, not completed Stage05 or production adapter adoption. Role-aware controller/parser/adapter/checker integration, all196 native PADLOC and DefenseFinder searches, source/architecture review, independent784-cell validation and verified Release publication remain mandatory. No negative biological calls are derived from these synthetic tests.\n',encoding='utf-8')
        w.status('4_phylogeny','WAITING_HEADROOM_OBSERVER_SERIALIZATION_REPAIR_TESTED','PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
                 'STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING',
                 'Actual G full196 source and native argv checks passed. Producer resource binding and V5 adoption still await unchanged memory gates. Prior observer27640 exited during an authorized preparation writer; actual Windows lock-contention and duplicate-guard tests passed for the explicit successor, whose launch follows this verified publication. No IQ-TREE or Stage05 production result exists.')
        paths=['scripts/publish_postboot_review_progress.py','scripts/wait_migration_v5_headroom_v2.py','scripts/test_waiter_writer_serialization_v2.py',
               'scripts/stage05_padloc_selection_v3.py','scripts/test_stage05_padloc_selection_v3.py','scripts/check_stage05_padloc_selection_native_v3.R',
               'scripts/review_stage05_selection_v3.py','scripts/review_stage05_selection_v4.py','scripts/stage05_detector_env_v5.sh',
               'reports/stage04/resource_wait_v5_v2/serialization_test.json','reports/stage04/resource_wait_v5_v2/actual_contention_child.json',
               'reports/stage04/resource_wait_v5_v2/prior_observer_stop.json','reports/stage05/preparation_selection_v3',
               'reports/stage05/preparation_selection_v4','STATUS.md','status/stages.tsv']
        head=commit(paths,'Publish installed-native PADLOC selection checks and tested observer serialization repair')
        C.command(ROOT,['git','fetch','origin','main'])
        C.check(C.command(ROOT,['git','rev-parse','origin/main'])==head,'Canonical publication head differs')
        files=[]
        for name in paths:
            path=ROOT/name
            files.extend([path] if path.is_file() else [p for p in path.rglob('*') if p.is_file()])
        for path in files:
            name=path.relative_to(ROOT).as_posix()
            remote=subprocess.run(['git','show','origin/main:'+name],cwd=ROOT,capture_output=True,check=True).stdout
            C.check(hashlib.sha256(remote).hexdigest()==C.digest(path),'Published preparation bytes differ: '+name)
        C.atomic(ROOT/'status/postboot_review_publication_receipt.json',{'status':'REMOTE_ALL_ALLOWLIST_FILE_BYTES_VERIFIED',
            'utc':C.now(),'commit':head,'files_verified':len(files),'scientific_stage04':'INCOMPLETE','stage05':'NOT_RUN',
            'biological_jobs_started':0})
        print('REMOTE_ALL_PREPARATION_BYTES_VERIFIED '+head,flush=True)

if __name__=='__main__':main()
