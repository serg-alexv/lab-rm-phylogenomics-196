"""Publish completed source readiness and independently verified historical cleanup."""
from pathlib import Path
import argparse, datetime, hashlib, json

WORK = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-head', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = WORK / 'master_source_ready_progress01'
    out.mkdir(exist_ok=False)
    def pinned(name, sha):
        raw = (WORK / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == sha, name
        return json.loads(raw)
    post = pinned('master_history02_postverify_20261009T201921Z_f90337c5/receipt.json',
                  'a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082')
    ready = pinned('stage5_source_readiness_completion.json',
                   '0827820b33285a6f40e9ed5fa62970202f175228035189486f2183c21edc675e')
    execution = pinned('batch03_execution01_readback_20261009T201344Z_f55cdf6b/receipt.json',
                       'd0a9a8b926ce4495c3127473b1c7ad4954c68d134e4894a9ececa1d22ce32d3b')
    assert post['state'] == 'PASS_EXACT837_REMOVED_EXCLUDED1025B_AND12_PROTECTED_UNCHANGED'
    assert ready['detector_execution'] == ready['curation'] == 'NOT_RUN'
    assert execution['state'].startswith('PASS_FRESH_REMOTE')
    now = datetime.datetime.now(datetime.timezone.utc)
    raw = (WORK / 'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_bytes()
    native = json.loads(raw)
    assert 0 <= (now - datetime.datetime.fromisoformat(native['utc'])).total_seconds() < 60
    assert native['exited'] is False and native['job_active_processes'] == 2
    (out / 'native_progress.json').write_bytes(raw)
    status = json.loads((WORK / 'master_cleanup_completed_progress01/status.json').read_text())
    status.update(updated_utc=now.isoformat(), native_process=native,
                  latest_progress_snapshot='reports/master_run/20261009/snapshots/source_ready_progress01/native_progress.json')
    status['cleanup'].update(state='BATCH01_02_03_AND_HISTORY02_EXACT_FILES_REMOVED',
                             removed_files=48490, removed_bytes=9756853507)
    status['cleanup']['batch03']['execution_archive'] = 'FRESH_REMOTE_ALL23_MEMBERS_94860_JOURNAL_RECORDS_VERIFIED'
    status['cleanup']['batch03']['execution_remote_receipt'] = 'reports/master_run/20261009/cleanup/batch03_execution01/REMOTE_READBACK.json'
    status['cleanup']['history02'] = {'removed_files': 837, 'removed_logical_bytes': 983926424,
        'state': post['state'], 'postverify_sha256': 'a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082',
        'receipt': 'reports/master_run/20261009/cleanup/history02_purge01/INDEPENDENT_POSTVERIFY.json',
        'excluded_original_preserved_bytes': 1025, 'protected_hashes_unchanged': 12,
        'physical_disk_reclaimed_bytes': 'NOT_MEASURED'}
    status['stage5_light_queue'] = {'state': 'PASS_CURRENT196_SOURCE_BYTES_ONLY', 'passed': 196, 'failed': 0,
        'source_payload_files': 12812, 'source_payload_bytes': 1893101586,
        'canonical_support_modules': 9, 'canonical_support_bytes': 182212,
        'completion': 'reports/master_run/20261009/preparation/source_readiness01/completion.json',
        'source_checker_exit_code': 0, 'native_searches': 'NOT_RUN', 'runtime_discovery': 'NOT_RUN',
        'curation': 'NOT_RUN', 'stage4_tree_consumed': False, 'evidence_archive_remote_readback': 'PENDING',
        'first_attempt': 'CHECKER_SCOPE_ERROR_PRESERVED_CORRECTED_NO_SOURCE_CORRUPTION'}
    (out / 'status.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
    correction = {'schema': 'MASTER_HISTORY02_PREFLIGHT_COMMAND_CORRECTION_V1',
        'recorded_utc': now.isoformat(), 'state': 'CORRECTED_ARGUMENT_ONLY_NO_DATA_MUTATION',
        'attempt_timestamp': 'NOT_RECORDED_IN_SEPARATE_FILE', 'mode': 'NoRun',
        'initial_argument': 'Relative RecoveryReceipt path',
        'guard_message': 'Actual independent remote recovery drift',
        'actual_cause': 'Literal argument did not equal the absolute receipt path bound in the published proposal',
        'payload_hashing_or_deletion_started': False,
        'correction': 'Used the exact absolute RecoveryReceipt path and unchanged pinned SHA; NoRun passed, then authorized Run completed',
        'source_or_plan_change': False, 'recovery_data_drift': False,
        'execution_journal_sha256': 'da3ad3d819c11462eac8e9e5f9c18096706148ef9f10441274fff804d6e32a81'}
    (out / 'history02_preflight_correction.json').write_text(json.dumps(correction, indent=2) + '\n', encoding='utf-8')
    md = f'''# Current execution status

Updated {now.isoformat()}. Direct user continuation remains active; scheduled
automatic continuation stays disabled. GitHub main and Release assets are the
durable project authority.

Stage4: the sole partitioned IQ-TREE3.1.4 worker remains active on all196 approved
genomes,100 accepted marker partitions and17,456 amino-acid columns. Global
optimization reached iteration70. No final host tree or final supports are
accepted. Historical V10 closure remains UNKNOWN. The fresh observation is
`reports/master_run/20261009/snapshots/source_ready_progress01/native_progress.json`.

Stage5: genome-source dependency split V2 is implemented in addf594d. Detection
and per-genome curation need no host tree. The actual light reader finished with
exit0: all196 source bundles,12,812 payload files/1,893,101,586 bytes, and all nine
canonical support modules/182,212 bytes match accepted SHA/size pins. This is
current source readiness only. The first checker scope error, correction and
both receipts remain preserved. The26-member evidence ZIP passed independent
local integrity/accounting checks; its remote upload/readback is pending.
See `reports/master_run/20261009/preparation/source_readiness01/completion.json`.

Actual detectors, runtime discovery, WSL lifecycle/UNC storage proofs and
production curation remain NOT_RUN. The next native worker awaits exact IQ-TREE
closure/unlock, fresh runtime/storage/resource admission and measurement on one
real approved genome. The queue uses fixed approved accessions; live tree leaves
are not independently finalized work units. Final Stage6 joins/SVG/PDF still
require independently accepted and separately published host tree, independent
curation and exact196-by4 coverage. Failed, unresolved and not-run states cannot
be biological absence. See `docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md`.

Cleanup now totals48,490 exact inactive files/9,756,853,507 logical bytes and15
exact empty directories. After the47,429-file batch03, a separate published
837-file historical proposal ran and passed independent postverification. All837
are absent; the excluded1,025-byte vendor fragment and12 protected hashes remain
unchanged. Exact native/controller handles remained alive. Full batch03 journal
recovery has now passed fresh GitHub download/all23 ZIP members and94,860 ordered
journal records. Physical reclaimed bytes are NOT_MEASURED.

Active tools, original lock, live checkpoints/inputs, six dirty G files and
toolchain remain protected. G remains at launch160498a6 until exact native
closure permits reconciliation. Original installed runtime/image, package and
base-interpreter recovery remain incomplete. The host is not ready to wipe.
See `docs/master_run/STORAGE_LEDGER.md`.

| Stage | Current scientific state | Published acceptance |
|---|---|---|
|0 environment|Completed|Acquisition/preflight verified|
|1 panel|Completed|Approved full196 verified|
|2 sequences|Completed|Integrity verified with documented exceptions|
|3 markers|Completed|Marker inventory verified|
|4 host tree|Running; no accepted tree|Stage4a accepted; final Stage4 pending|
|5 R-M inventory|Not run; source readiness PASS|V2 source and synthetic checks only|
|6 figure|Not run|Synthetic vector and negative-gate proofs only|
|7 final review|Not run|Pending scientific results|

Detailed observations: `status/master_run_20261009.json`. Historical receipts
retain original dates and uncertainty. Raw private sessions/prompts/usage,
credentials and unrelated files are excluded from public recovery assets.
'''
    (out / 'STATUS.md').write_text(md, encoding='utf-8')
    ledger = (WORK / 'master_cleanup_completed_progress01/STORAGE_LEDGER.md').read_text(encoding='utf-8')
    ledger = ledger.replace('full execution ZIP remote verification pending',
        'full execution ZIP fresh GitHub download/all23 members and94,860 ordered records verified')
    ledger = ledger.replace('Still local; separate proposal only; one1,025-byte vendor fragment excluded and retained',
        '837 exact leaves removed under separately published plan; independent absence/protected-hash proof PASS; one1,025-byte vendor fragment retained')
    ledger = ledger.replace('Completed file cleanup totals47,653 files/8,772,927,083 logical bytes.',
        'Completed file cleanup totals48,490 files/9,756,853,507 logical bytes.')
    ledger += '\nStage5 current source readiness: all196 accepted bundles/12,812 payload files/' \
        '1,893,101,586 bytes and nine support modules match accepted pins. Evidence ZIP ' \
        'local checks PASS; remote readback pending. No detector or scientific acceptance ' \
        'is implied. All source files remain canonical execution dependencies.\n'
    (out / 'STORAGE_LEDGER.md').write_text(ledger, encoding='utf-8')
    files = []
    def add(local, target):
        path = WORK / local; raw = path.read_bytes()
        assert 0 < len(raw) < 5 * 1024 * 1024
        files.append({'local_absolute_path': str(path), 'target': target,
                      'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    for name in [Path(__file__).name, 'verify_master_history02_leaf_purge.py',
                 'test_master_history02_postverify.py', 'build_stage5_readiness_archive.py',
                 'verify_stage5_source_readiness_remote.py']:
        add(name, 'scripts/master_run/' + name)
    pairs = {
        'master_history02_leaf_purge_20261009_receipt.jsonl': 'cleanup/history02_purge01/EXECUTION_JOURNAL.jsonl',
        'master_history02_postverify_20261009T201921Z_f90337c5/receipt.json': 'cleanup/history02_purge01/INDEPENDENT_POSTVERIFY.json',
        'master_history02_postverify_checks.json': 'cleanup/history02_purge01/POSTVERIFY_CHECKS.json',
        'master_source_ready_progress01/history02_preflight_correction.json': 'cleanup/history02_purge01/PREFLIGHT_COMMAND_CORRECTION.json',
        'batch03_execution01_readback_20261009T201344Z_f55cdf6b/receipt.json': 'cleanup/batch03_execution01/REMOTE_READBACK.json',
        'master_batch03_execution_upload_plan.json': 'cleanup/batch03_execution01/UPLOAD_PLAN.json',
        'master_batch03_execution_upload_receipt.json': 'cleanup/batch03_execution01/UPLOAD_RECEIPT.json',
        'stage5_source_readiness01/build_receipt.json': 'preparation/source_readiness01/build_receipt.json',
        'stage5_source_readiness_completion.json': 'preparation/source_readiness01/completion.json',
        'stage5_source_readiness01_readback_20261009T201744Z_a03de7af/receipt.json': 'preparation/source_readiness01/LOCAL_READBACK.json',
        'stage5_source_readiness_readback_preparation.json': 'preparation/source_readiness01/READBACK_PREPARATION.json',
        'stage5_source_readiness_actual_02/receipt.json': 'preparation/source_readiness01/CURRENT196_SOURCE_RECEIPT.json',
        'stage5_source_readiness_actual_02/per_accession.jsonl': 'preparation/source_readiness01/PER_ACCESSION.jsonl',
        'master_completed_cleanup_git_objects.json': 'publication/COMPLETED_CLEANUP_GIT_OBJECTS.json',
        'master_completed_cleanup_remote_readback.json': 'publication/COMPLETED_CLEANUP_REMOTE_READBACK.json',
        'master_source_ready_progress01/native_progress.json': 'snapshots/source_ready_progress01/native_progress.json',
    }
    for local, target in pairs.items(): add(local, 'reports/master_run/20261009/' + target)
    add('master_source_ready_progress01/status.json', 'status/master_run_20261009.json')
    add('master_source_ready_progress01/STATUS.md', 'STATUS.md')
    add('master_source_ready_progress01/STORAGE_LEDGER.md', 'docs/master_run/STORAGE_LEDGER.md')
    assert len({x['target'] for x in files}) == len(files)
    with a.output.open('x', encoding='utf-8') as stream:
        json.dump({'expected_head': a.expected_head,
            'message': 'Verify all196 current source bundles and completed historical cleanup; preserve exact execution recovery',
            'files': files}, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'files': len(files), 'bytes': sum(r['bytes'] for r in files),
                      'removed_files': 48490, 'source_accessions_ready': 196}))

if __name__ == '__main__': main()
