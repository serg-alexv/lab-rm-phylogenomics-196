"""Capture completed cold cleanup and current independent light-queue progress."""
from pathlib import Path
import datetime, hashlib, json

work = Path(__file__).resolve().parent
out = work / 'master_cleanup_completed_progress01'
out.mkdir(exist_ok=False)
post_path = work / 'master_batch03_postverify_20261009T200023Z_f95312bd/receipt.json'
raw_post = post_path.read_bytes()
assert hashlib.sha256(raw_post).hexdigest() == '84cb29ebcc04b444ea90ca0e10d5f7e6832d09f14f8f8285f1241b4cf3e71868'
post = json.loads(raw_post)
assert post['state'] == 'PASS_EXACT47429_REMOVED_838_ORIGINALS_AND12_PROTECTED_UNCHANGED'
now = datetime.datetime.now(datetime.timezone.utc)
raw = (work / 'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_bytes()
progress = json.loads(raw)
assert (now - datetime.datetime.fromisoformat(progress['utc'])).total_seconds() < 60
assert progress['exited'] is False and progress['job_active_processes'] == 2
(out / 'native_progress.json').write_bytes(raw)
source_lines = (work / 'stage5_source_readiness_actual_02.stdout.txt').read_bytes().splitlines()
source_events = []
for line in source_lines:
    try:
        event = json.loads(line)
    except (ValueError, UnicodeDecodeError):
        continue
    if isinstance(event, dict) and 'accessions_checked' in event:
        source_events.append(event)
assert source_events and source_events[-1]['failed'] == 0
queue = source_events[-1]
status = json.loads((work / 'master_recovery_progress01/status.json').read_text())
status['updated_utc'] = now.isoformat()
status['native_process'] = progress
status['latest_progress_snapshot'] = 'reports/master_run/20261009/snapshots/cleanup_completed_progress01/native_progress.json'
status['cleanup'].update(state='BATCH01_02_AND03_REMOVED_RECOVERY_VERIFIED',
    removed_files=47653, removed_bytes=8772927083,
    batch03={'state': post['state'], 'removed_files': 47429, 'removed_logical_bytes': 6565902818,
             'postverify_sha256': hashlib.sha256(raw_post).hexdigest(), 'verification_utc': post['finished_utc'],
             'receipt': 'reports/master_run/20261009/cleanup/batch03_purge01/INDEPENDENT_POSTVERIFY.json',
             'held_files_unchanged': 219, 'unmatched_files_unchanged': 619, 'protected_files_unchanged': 12,
             'execution_archive': 'LOCAL_ALL23_MEMBERS_VERIFIED_REMOTE_PENDING',
             'physical_disk_reclaimed_bytes': 'NOT_MEASURED'},
    new_public_recovery={'components01': 'FRESH_REMOTE_ALL29_MEMBERS_17_ORIGINALS_VERIFIED',
                        'history02': 'FRESH_REMOTE_3_SHARDS_882_MEMBERS_837_ORIGINALS_VERIFIED',
                        'excluded_vendor_fragment': 'ONE_1025_BYTE_ORIGINAL_PRESERVED_LOCALLY'})
status['stage5_light_queue'] = {'state': 'CURRENT_SOURCE_BYTES_CHECK_RUNNING', 'snapshot': queue,
    'observed_utc': now.isoformat(), 'native_searches': 'NOT_RUN',
    'first_attempt': 'CHECKER_SCOPE_ERROR_BEFORE_PAYLOAD_HASHING_PRESERVED_AND_CORRECTED',
    'support_modules': 'ALL9_CANONICAL_SOURCE_HASHES_VERIFIED', 'readers': 1, 'priority': 'BELOW_NORMAL'}
(out / 'status.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
md = f'''# Current execution status

Updated {now.isoformat()}. This master continuation is active. GitHub main and
Release assets are the sole durable project authority; automatic scheduled
continuation remains disabled.

Stage4: one partitioned IQ-TREE3.1.4 job remains active on all196 approved
genomes,100 accepted marker partitions and17,456 amino-acid columns. Global
candidate optimization has reached iteration60. Model selection and initial
searches finished; no final host tree or support is accepted. Current native
observation: `reports/master_run/20261009/snapshots/cleanup_completed_progress01/native_progress.json`.
Historical V10 closure remains UNKNOWN.

Stage5's accepted-genome-source dependency split is implemented in commit
`addf594d69990b4d4bc95d1e0fa38c76f59efdd6`. Detection and per-genome curation
do not need host-tree acceptance. One serial below-normal-priority source
reader is running now alongside Stage4; this snapshot observed
{queue['passed']}/196 exact source-bundle checks PASS and zero failures in the
corrected attempt. The first checker attempt stopped at a C-manifest scope
guard before payload hashing; its original source/receipts are preserved.
All nine retained canonical support modules match their source pins. Actual
detectors, runtime discovery, WSL lifecycle/storage/UNC proofs and production
curation remain NOT_RUN. The next heavy worker awaits exact current native
closure/unlock and fresh operational admission. See
`docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md` and
`reports/master_run/20261009/preparation/stage5_deployment_readiness.md`.

Stage6 final joining and authoritative SVG/PDF still require an independently
accepted and published full host tree, independent curation and exact196-by4
coverage. Candidate trees, synthetic figures, failed and not-run cells are not
accepted biological results or absence.

Cleanup completed:47,653 inactive files/8,772,927,083 logical bytes across
batches01–03, plus15 exact empty directories. Batch03 independently confirmed
all47,429 targets absent, all838 retained originals unchanged by full SHA and
identity, and all12 protected files unchanged. Native/controller exact
identities remained alive at postcheck. Its compact public proof is
`reports/master_run/20261009/cleanup/batch03_purge01/INDEPENDENT_POSTVERIFY.json`.
The full execution-journal archive has23 verified local members; its upload
and independent remote readback are pending. These counts are logical bytes;
physical reclaimed disk space is not measured.

The component archive and three historical-data shards have each passed fresh
GitHub download/full-member verification. The latter preserve837 original
files; one1,025-byte vendor fragment remains excluded and local. The remaining
837 files are only proposed for a separate exact-path purge. Active tools,
original lock, live checkpoints/inputs, six dirty G files and toolchain remain
protected. The live G checkout stays at launch commit160498a6 until exact
native closure allows reconciliation. Toolchain/image/base-runtime recovery
is incomplete. The host is not ready to wipe. See
`docs/master_run/STORAGE_LEDGER.md`.

| Stage | Current scientific state | Published acceptance |
|---|---|---|
|0 environment|Completed|Acquisition/preflight verified|
|1 panel|Completed|Approved full196 panel verified|
|2 sequences|Completed|Integrity verified with documented exceptions|
|3 markers|Completed|Host marker inventory verified|
|4 host tree|Running, no accepted tree|Accepted Stage4a; final Stage4 pending|
|5 R-M inventory|Not run|Prepared V2 source; light source check running|
|6 figure|Not run|Synthetic vector and negative-gate proofs only|
|7 final review|Not run|Pending scientific results|

Current master observations are in `status/master_run_20261009.json`.
Historical receipts keep their original dates and uncertainty. No accepted
upstream biological stage is being rerun. Raw private sessions/prompts/usage,
credentials and unrelated files are excluded from public preservation.
'''
(out / 'STATUS.md').write_text(md, encoding='utf-8')
ledger = '''# Master storage ledger

GitHub main and scientific/master Release assets are the durable project record.
Local working files are execution caches. The host is not ready to wipe until
the scientific goal and a final complete remote recovery audit pass.

| Material | Durable recovery and verification | Local state |
|---|---|---|
|Master source, tests, public reviews and synthetic proofs|3ac8527 source package; addf594 genome-source V2 split; subsequent incremental exact-blob readbacks|Current dependencies retained|
|Cold batch01,142 files|master_cleanup_batch01.zip; fresh download/all153 members verified|142 exact files removed|
|Previous Release staging,82 files|27 distinct assets across nine scientific Releases; remote digest/local SHA/all45,955 ZIP members verified|82 exact staging copies removed|
|Public history/inventory01|master_public_history_inventory01.zip; fresh all320 members,291 scientific copies,88,441 public metadata rows and historical validation records verified|Recovery available; metadata alone grants no deletion authority|
|Cold scientific batch03,47,429 files|Fresh mapping ZIP/all witness joins verified before purge; actual postverify84cb29eb confirmed every absence and838 retained originals/12 protected hashes|47,429 exact files removed;6,565,902,818 logical bytes; full execution ZIP remote verification pending|
|Historical remainder02,837 files|Three fresh downloaded shards/all882 members/837 originals and controls verified at2ad42f8|Still local; separate proposal only; one1,025-byte vendor fragment excluded and retained|
|Public component recovery01|Fresh downloaded ZIP/all29 members/17 originals, source notices and397 package records/339 distinct package pins verified|Live tools and source archives retained; installed image/package payload/base-runtime recovery not covered|
|Original component notice/source limits|Retained original archives/notices unchanged; standalone Intel runtime notice and full IQ-TREE corresponding-source gaps explicit|No complete runtime/source recovery claim|
|Exact empty directories|Published identity/emptiness plan and execution receipt|15 removed; no recursive directory purge claimed|
|Active inference and source inputs|Timestamped public source/config/command/admission/progress; accepted scientific Releases|Native scope, checkpoints, exact lock, six dirty G files and pinned toolchain protected|
|Retained toolchain/base Python|Public preservation plan; original8GiB image remains unmounted/protected|Actual file-level runtime/cache/model inventory, portable restoration and remote verification pending|

Completed file cleanup totals47,653 files/8,772,927,083 logical bytes. Physical
reclaimed space is NOT_MEASURED; downloads, new archives, filesystem allocation
and caches prevent attributing free-space deltas to these logical byte counts.

Every new purge needs exact checked absolute paths, original identity/link/size/
mtime and full SHA, independently verified remote recovery, active-dependency
exclusion, published proposal, and independently checked execution receipts.
Unexpected new/changed files remain local. The batch03 executor's brief gap
between closing its exclusive hash handle and literal PowerShell removal is
explicit; no atomic-delete claim is made. Historical failures and UNKNOWN
closures preserve their original states. Raw private sessions, Codex events,
prompts/usage, credentials and unrelated data are excluded from public assets.
'''
(out / 'STORAGE_LEDGER.md').write_text(ledger, encoding='utf-8')
print(json.dumps({'utc': now.isoformat(), 'removed_files': 47653, 'source_checks_observed': queue['passed']}))
