"""Capture a small public progress update; never alter the live checkout/job."""
from pathlib import Path
import base64, datetime, hashlib, json, subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
HEAD = '160498a6af156b563c7680910945da13b4d245c0'
ATTEMPT = HERE / 'iqtree_attempts/partitioned_20261009T162904Z'
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
prefix = 'reports/master_run/20261009/snapshots/' + stamp
files = {}
def add(path, value):
    files[path] = value if isinstance(value, bytes) else value.encode('utf-8')
def dump(value):
    return json.dumps(value, indent=2, sort_keys=True) + '\n'
def tracked(path):
    return subprocess.run(['git', '-C', str(ROOT), 'show', HEAD + ':' + path],
                          check=True, capture_output=True).stdout.decode('utf-8')

for name in ('progress.json', 'launch.json', 'admission.json', 'cache_import.json',
             'config.json', 'stdout.txt', 'stderr.txt'):
    add(prefix + '/' + name, (ATTEMPT / name).read_bytes())
progress = json.loads(files[prefix + '/progress.json'])
launch = json.loads(files[prefix + '/launch.json'])
assert progress['pid'] == launch['native']['pid'] == 4768
assert progress['creation_filetime'] == launch['native']['creation_filetime']
assert not progress['exited'] and progress['job_active_processes'] == 2
assert launch['authority']['canonical_commit'] == HEAD
manifest = {name: {'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}
            for name, value in files.items()}
add(prefix + '/snapshot_manifest.json', dump({'utc': now,
    'scope': 'RUNNING_OBSERVATION_ONLY_NOT_SCIENTIFIC_ACCEPTANCE',
    'mutable_log_note': 'Each log is a captured prefix; files were not frozen as one transaction.',
    'files': manifest}))
summary = {'schema': 'LAB_RM_MASTER_RUN_STATUS_V1', 'updated_utc': now,
    'master_run': 'master_20261009', 'authority': 'https://github.com/serg-alexv/lab-rm-phylogenomics-196',
    'launch_commit': HEAD, 'scientific_status': 'STAGE04_RUNNING_NO_ACCEPTED_TREE',
    'native_process': progress, 'stage5': 'NOT_RUN_BUILD_AND_SYNTHETIC_CHECKS_ONLY',
    'stage6': 'NOT_RUN_SYNTHETIC_VECTOR_PROOFS_ONLY',
    'latest_progress_snapshot': prefix, 'cleanup': 'INVENTORY_IN_PROGRESS_NO_FILES_PURGED',
    'archive_rule': 'Publish SHA256 manifests and verified full Release assets before purge; retain exact live dependencies.',
    'historical_V10_closure': 'UNKNOWN_PRESERVED', 'automatic_resume': False,
    'local_checkout_note': 'Live G checkout stays at launch commit while the production lock is held; reconcile remote main after exact native closure.'}
add('status/master_run_20261009.json', dump(summary))
old = tracked('STATUS.md')
intro = f'''# Current execution status

## Master run — {now}

**STAGE04 RUNNING.** The one partitioned native IQ-TREE 3.1.4 job launched at
{launch['utc']} uses all196 approved genomes and the accepted100-marker,
17,456-column Stage4a alignment. Model selection and initial tree searches have
finished; candidate-tree optimization is running. This observation is not final
tree acceptance. Actual retained process/job measurements and captured command,
admission, cache import and log prefixes are in `{prefix}`.

This is the master continuation. GitHub is the primary project storage and sole
source of truth; all reproducibility artifacts must be recoverable here before
the WD host is wiped. A local swarm is inventorying yesterday's project files.
Nothing has been purged. Active files, accepted inputs and pinned toolchain remain
in place until verified remote recovery permits cleanup. See
`docs/master_run/PLAN_20261009.md` and `status/master_run_20261009.json`.

Stages5–7 remain scientifically NOT_RUN. Prepared code and synthetic tests do not
constitute detector results or an accepted figure. Historical unknown outcomes
remain unchanged. Automatic scheduled continuation remains disabled.

'''
add('STATUS.md', intro + old.removeprefix('# Current execution status').lstrip())
stages = tracked('status/stages.tsv').splitlines()
stages = ['\t'.join(['4_phylogeny', 'RUNNING_PARTITIONED_NATIVE_PRIMARY196',
    'PASS_ACCEPTED_STAGE04A_INPUTS_FINAL_TREE_PENDING',
    'UPSTREAM_VERIFIED_LIVE_EVIDENCE_COMMITTED_FULL_STAGE04_RELEASE_PENDING',
    progress['utc'], str(progress['pid']), str(progress['creation_filetime'])])
    if line.startswith('4_phylogeny\t') else line for line in stages]
add('status/stages.tsv', '\n'.join(stages) + '\n')
old_execution = json.loads(tracked('status/stage04_execution.json'))
add(prefix + '/previous_stage04_execution.json', dump(old_execution))
add('status/stage04_execution.json', dump({'utc': progress['utc'],
    'state': 'RUNNING_PARTITIONED_NATIVE_PRIMARY196', 'scientific_status': 'INCOMPLETE_NO_ACCEPTED_TREE',
    'actual_native_pid': progress['pid'], 'native_creation_filetime': progress['creation_filetime'],
    'active_inference_found': True, 'new_biological_inference_launched': True,
    'previous_V10_outcome': 'UNKNOWN_PRESERVED', 'input_gate': 'PASS_ACCEPTED_STAGE04A_INPUTS',
    'launch_commit': HEAD, 'live_evidence': prefix,
    'final_acceptance_required': ['actual native exit0', 'owned job empty', 'explicit OS unlock',
        'independent full196 support/bootstrap/tree validation', 'verified standalone Release readback']}))
add('docs/master_run/PLAN_20261009.md', f'''# Master continuation and durable storage plan

Updated {now}. User instruction: this is the master run; GitHub is the sole
project authority and primary durable working/release store. The WD host will be
wiped after the scientific goal is reached. Publish each meaningful completed
step, including methods, commands, measured resources, checks, source, plans,
concise decision records, failures and results. No private sessions or credentials.

1. Preserve the one running partitioned full196 inference and its original lock,
   runner/config/executable/input identities. Publish immutable timestamped live
   observations labelled incomplete; never treat partial tree files as accepted.
2. Local swarm: inventory project-scoped yesterday/current caches and artifacts;
   identify exact live dependencies, unique history and remotely verified copies.
   Copilot supplies a bounded cleanup review. No broad user-directory cleanup.
3. Commit inventory, SHA-256 manifests and an exact proposed removal list first.
   Preserve unique raw evidence and source/history in standalone Release ZIP
   assets below500MiB. A separate verifier downloads each complete asset and
   checks SHA-256, ZIP membership, path safety and every member hash against the
   pre-upload source manifest. Verify reachable remote commit/release before purge.
4. Remove only explicitly inventoried inactive project artifacts with verified
   remote recovery. Recheck target absolute paths and bytes immediately before
   deletion; preserve any changed/unexpected item. Commit actual deletion receipts
   and reclaimed bytes immediately afterward. Never force-push or infer closure
   from missing PIDs. Historical UNKNOWN and raw failure evidence stay unchanged.
5. After exact native closure, independently validate/freeze/publish the accepted
   full196 tree and reopen its Release. Reconcile the live G checkout with newer
   remote main while preserving preexisting dirty files.
6. Then use the retained capped WSL environment for serial per-genome PADLOC and
   DefenseFinder searches. Verify real Linux/Windows process closure, physical
   C/G disk reserves and ext4 storage proof first. Native working files use an
   ext4 bind at the canonical Linux output path; export deterministic per-genome
   ZIP shards and compact receipts to GitHub. Actual searches are NOT_RUN now.
7. Execute and independently validate functional R-M curation, exact196x4 join,
   authoritative circular SVG/PDF and unchanged host topology/branch lengths.
   Rings inner-to-outer I, II includingIIG, III, IV; unknown remains explicit NA.
8. Final independent review and remote recovery audit must cover all raw,
   intermediate/final data, source, logs, tool/database versions, provenance and
   release indexes before final local cleanup or host-wipe readiness is claimed.

Only the root agent writes remote main. Every update uses an expected-head lease;
if main changes unexpectedly, stop that publication, inspect and reconcile.
The active G checkout is deliberately untouched while its production lock is held.
Remote progress publication is authorized by the user's current instruction and
does not launch another production writer or modify active scientific files.
WSL swap, toolchain, original locks, accepted inputs and live checkpoints are not
cleanup candidates. Archives remain evidence, never silently replace acceptance.
''')
review = (HERE / 'copilot_master_cleanup_review.txt').read_text(encoding='utf-8-sig')
add('docs/master_run/COPILOT_CLEANUP_REVIEW.md', '# Copilot cleanup review\n\n'
    'Executed GitHub Copilot CLI with supplied project facts and shell/write tools denied.\n'
    'This is advisory operational review, not scientific validation.\n\n' + review +
    '\nDisposition: apply explicit remote conflict, SHA-256 and recovery-before-delete gates.\n'
    'Commit proposed removal receipts before deletion and actual receipts after it.\n'
    'Open-handle exclusion has not been established; active pinned dependency trees\n'
    'remain excluded from removal. No deletion was authorized solely by this review.\n')
request = Path(r'C:\Users\wheel\.codex\attachments\f37f2904-3195-4741-9b7b-9e93f61e11b4\Pasted text.txt').read_bytes()
add('docs/master_run/WORK_REQUEST_20261009.md', request)
payload = {'expected_head': HEAD, 'base_tree': '6a4ad99d58ad67ad0fec40865ce4b0bdd20b8ec1',
    'message': 'Record master-run authority, live IQ-TREE progress and recoverable cleanup plan',
    'files': [{'path': name, 'content': value.decode('utf-8'),
               'sha256': hashlib.sha256(value).hexdigest()} for name, value in files.items()]}
(HERE / 'master_remote_update_payload.json').write_text(dump(payload), encoding='utf-8')
print(json.dumps({'files': len(files), 'bytes': sum(map(len, files.values())),
                  'snapshot': prefix, 'expected_head': HEAD}))
