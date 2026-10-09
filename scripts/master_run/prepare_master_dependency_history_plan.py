"""Pin exact public decision, history-archive preparation and cleanup proposals."""
from pathlib import Path
import datetime, hashlib, json

ROOT = Path(__file__).resolve().parent
EXPECTED = '114a7249b10008430f03a27cee16d2356013b624'
rows = []
def add(local, target):
    p = ROOT / local
    b = p.read_bytes()
    assert len(b) < 5*1024*1024
    rows.append({'local_absolute_path': str(p), 'target': target,
                 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()})

add('STAGE5_STAGE6_DEPENDENCY_DECISION.md', 'docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md')
add('stage5_decoupling_scope_audit.md', 'reports/master_run/20261009/preparation/stage5_decoupling_scope_audit.md')
for name in ['build_master_public_history_inventory01.py', 'prepare_master_emptydir_plan.py',
             'Invoke-MasterEmptyDirectoryPrune.ps1', 'prepare_master_dependency_history_plan.py']:
    add(name, 'scripts/master_run/' + name)
for name in ['master_public_history_inventory01_manifest.json',
             'master_public_history_inventory01_build_receipt.json',
             'master_emptydir_prune_proposed.json']:
    add(name, 'reports/master_run/20261009/cleanup/' + name)
for name in ['summary.json', 'REVIEW.md', 'PUBLIC_EVIDENCE_SHA256.json']:
    add('yesterday_inventory/' + name, 'reports/master_run/20261009/cleanup/yesterday_inventory/' + name)
for name in ['summary.json', 'REVIEW.md']:
    add('yesterday_inventory/batch03/' + name, 'reports/master_run/20261009/cleanup/batch03/' + name)
mapper = list(ROOT.glob('*batch03*.py'))
assert len(mapper) == 1, [str(x) for x in mapper]
add(mapper[0].name, 'scripts/master_run/' + mapper[0].name)

status = json.loads((ROOT/'master_current_status.json').read_text())
status['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
status['native_process'] = json.loads((ROOT/'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_text())
status['stage5_dependency_decision'] = {
    'state': 'IMPLEMENT_GENOME_SOURCE_GATE_SPLIT_PREPARED_CODE_IN_PROGRESS',
    'decision': 'docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md',
    'native_concurrency': 'ONE_NATIVE_OWNER_UNCHANGED',
    'actual_stage5_searches': 'NOT_RUN'}
status['cleanup']['public_history_archive'] = 'LOCAL_VERIFIED_UPLOAD_AND_REMOTE_READBACK_PENDING'
status['cleanup']['batch03'] = '47648_RELEASE_MATCHED_FILES_IDENTIFIED_NO_PURGE'
(ROOT/'master_dependency_current_status.json').write_text(json.dumps(status,indent=2)+'\n')
add('master_dependency_current_status.json', 'status/master_run_20261009.json')
prefix = '''# Current execution status

## Genome queue dependency split — 2026-10-09

Implementing independent accession-keyed Stage 5 detection and curation. The
approved genome sources are already available; the running tree search does not
emit finalized leaves. Final exact196-by4 join and authoritative Stage 6 figure
remain bound to an independently accepted/published host tree. See
`docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md`.

Prepared code is being changed and tested. Actual Stage 5 searches and Stage 6
production rendering remain NOT_RUN. The sole active partitioned IQ-TREE job
and exclusive lock are unchanged. Heavy detector execution requires exact
current native closure/lock release and actual WSL resource/lifecycle checks.

Verified cleanup has removed224 inactive files/2,207,024,265bytes. Another47,648
old C files/6,568,632,074logical bytes match published scientific Release
members; they are only identified, not yet removed. The619 unmatched files
remain preserved. A local5,529,652byte public history/inventory archive is
verified; remote upload/readback is pending. The host is not ready to wipe.

'''
(ROOT/'master_dependency_STATUS.md').write_text(prefix+(ROOT/'master_latest_STATUS.md').read_text())
add('master_dependency_STATUS.md','STATUS.md')
out = ROOT/'master_dependency_history_git_plan.json'
assert not out.exists()
out.write_text(json.dumps({'expected_head':EXPECTED,
 'message':'Decouple genome work from final host tree; preserve history and exact cleanup proposals',
 'files':rows},indent=2)+'\n')
print(json.dumps({'plan':str(out),'files':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
