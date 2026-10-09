"""Capture a bounded public master status without changing the live workflow."""
from pathlib import Path
import datetime, hashlib, json

work = Path(__file__).resolve().parent
out = work / 'master_recovery_progress01'
out.mkdir(exist_ok=False)
raw = (work / 'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_bytes()
progress = json.loads(raw)
now = datetime.datetime.now(datetime.timezone.utc)
assert (now - datetime.datetime.fromisoformat(progress['utc'])).total_seconds() < 60
assert progress['exited'] is False and progress['job_active_processes'] == 2
(out / 'native_progress.json').write_bytes(raw)
journal = work / 'master_batch03_leaf_purge_20261009_receipt.jsonl'
with journal.open('rb') as stream:
    stream.seek(max(0, journal.stat().st_size - 65536))
    lines = stream.read().splitlines()
events = []
for line in lines[1:]:
    try:
        events.append(json.loads(line))
    except json.JSONDecodeError:
        pass  # The writer may be appending the final partial line.
latest = next(e for e in reversed(events) if e.get('event') == 'REMOVED')
assert not any(e.get('event') in {'COMPLETE', 'STOP'} for e in events)
status = json.loads((work / 'master_source_split_current_status.json').read_text())
status['updated_utc'] = now.isoformat()
status['native_process'] = progress
status['latest_progress_snapshot'] = 'reports/master_run/20261009/snapshots/recovery_progress01/native_progress.json'
status['cleanup']['batch03'] = {
    'state': 'RUNNING_EXACT_HASH_AND_IDENTITY_GATED_COLD_LEAF_PURGE',
    'proposal_commit': '2b0edf16fe3224d33155ac67f2a8a0d2177d78a5',
    'proposed_files': 47429, 'proposed_logical_bytes': 6565902818,
    'observed_removed_files': latest['deleted'], 'observed_removed_logical_bytes': latest['deleted_bytes'],
    'observation_utc': latest['utc'], 'final_verification': 'NOT_RUN',
    'preserved_hold_files': 219, 'preserved_unmatched_files': 619,
    'recovery': 'FRESH_REMOTE_MAPPING_ZIP_AND_RELEASE_MEMBER_WITNESSES_VERIFIED'}
status['cleanup']['new_public_recovery'] = {'components01': 'LOCAL_VERIFIED_REMOTE_PENDING',
    'history02': 'THREE_SHARDS_837_ORIGINAL_FILES_LOCAL_VERIFIED_REMOTE_PENDING',
    'excluded_vendor_fragment': 'ONE_1025_BYTE_ORIGINAL_PRESERVED_LOCALLY'}
(out / 'status.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
md = f'''# Current execution status

Updated {now.isoformat()}. GitHub is the sole project authority and durable storage.
This master continuation is active; automatic scheduled continuation remains disabled.

Stage4 runs the one partitioned IQ-TREE3.1.4 job on all196 approved genomes,
100 accepted marker partitions and17,456 amino-acid columns. Model selection
and initial searches finished; global candidate-tree optimization continues.
The latest retained native/job observation is in
`reports/master_run/20261009/snapshots/recovery_progress01/native_progress.json`.
No host tree or support values are accepted yet. Historical V10 closure stays
UNKNOWN; the current controller does not change that historical conclusion.

Stage5's genome-source dependency split is implemented and source-tested in
commit `addf594d69990b4d4bc95d1e0fa38c76f59efdd6`. Detection and per-genome
curation use the accepted accession/source bundles independently of final
Stage4 acceptance. The current exclusive owner still must close exactly before
another native job is admitted on WD. Actual WSL/runtime/resource/lifecycle
checks and actual Stage5 searches remain NOT_RUN. The accession queue preserves
pending, failed, unresolved and not-run states. Final exact196-by4 joining and
authoritative Stage6 SVG/PDF require an independently accepted and published
host tree plus independent curation checks. See
`docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md`.

Cleanup already completed:224 inactive files/2,207,024,265 logical bytes and15
exact empty directories. Batch03 is now executing the published exact47,429
cold-file proposal. At {latest['utc']}, its durable journal recorded
{latest['deleted']:,} removed files/{latest['deleted_bytes']:,} logical bytes;
this is progress, not final absence/protection verification. The219 held and
619 unmatched files remain outside this purge. Its fresh remote mapping ZIP,
source controls and historical Release member witnesses were verified first.
Active native inputs, runtime, checkpoints, original lock and six dirty G
files are protected. The live G checkout remains at launch commit160498a6
while its native owner holds the production lock; root will reconcile it with
remote main after exact closure.

Additional public recovery controls are being published: one component archive
(228,162,511 bytes) and three history shards (837 original files,120,674,497
compressed bytes). Their fresh remote byte verification is still pending.
Their scopes do not constitute complete environment recovery. One1,025-byte
vendor fragment is excluded and retained locally; component source/notice
coverage limitations are explicit. Raw private sessions/prompts/usage and
credentials are excluded. The ext4 toolchain and needed local runtime remain
protected. The host is not ready to wipe.

| Stage | Current scientific state | Published acceptance |
|---|---|---|
|0 environment|Completed|Verified acquisition/preflight|
|1 panel|Completed|Approved full196 panel verified|
|2 sequences|Completed|Integrity verified with documented exceptions|
|3 markers|Completed|Host marker inventory verified|
|4 host tree|Running, no accepted tree|Accepted Stage4a; final Stage4 pending|
|5 R-M inventory|Not run|Prepared V2 source and synthetic checks only|
|6 figure|Not run|Synthetic vector/negative-gate proofs only|
|7 final review|Not run|Pending scientific results|

Use `status/master_run_20261009.json` for this current master observation;
historical stage receipts retain their original dates and states. Recovery
assets are in the `master-run-storage-20261009-v1` Release. Source, decisions,
tests and public receipts are committed incrementally. No accepted upstream
stage is being rerun.
'''
(out / 'STATUS.md').write_text(md, encoding='utf-8')
print(json.dumps({'utc': now.isoformat(), 'removed_files_observed': latest['deleted'],
                  'native_progress_sha256': hashlib.sha256(raw).hexdigest()}))
