"""Exact public V2 implementation and verified recovery/cleanup records."""
from pathlib import Path
import datetime, hashlib, json

work=Path(__file__).resolve().parent
rows=[]
def add(local,target):
    p=work/local;b=p.read_bytes()
    assert len(b)<5*1024*1024
    rows.append({'local_absolute_path':str(p),'target':target,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})

for name in ['stage5_atomic.py','stage5_atomic_config.template.json','stage5_atomic_IMPLEMENTATION.md',
             'build_stage5_accepted_source_pins.py','stage5_accepted_source_pins.json','test_stage5_source_gate.py',
             'stage5_windows_owner.py','test_stage5_windows_owner.py','verify_stage5_accepted_source_pins_windows.py',
             'verify_master_public_history_inventory01_remote.py','Invoke-MasterEmptyDirectoryPrune.ps1',
             'prepare_master_source_split_plan.py']:
    add(name,'scripts/master_run/'+name)
for name in ['stage5_source_split_IMPLEMENTATION.md','stage5_source_split_preparation_checks.json',
             'stage5_canonical_source_pins_readback.json']:
    add(name,'reports/master_run/20261009/preparation/'+name)
curation=['CLASSIFICATION_CONTRACT.md','FOLLOW_ON_METHODS.md','accepted_source_pins.json',
          'stage05_curation_atomic.py','test_identity_v2.py','test_independent_curation.py',
          'validate_atomic_curation.py','IDENTITY_V2_COMPATIBILITY.json','IDENTITY_V2_REVIEW.md',
          'SHA256SUMS_IDENTITY_V2.txt']
for name in curation:
    add('stage05_curation/'+name,'scripts/master_run/stage05_curation/'+name)
add('public_history01_remote_readback_20261009T190807Z_9a59b51b/receipt.json',
    'reports/master_run/20261009/cleanup/HISTORY01_REMOTE_READBACK.json')
add('master_emptydir_prune_receipt.json','reports/master_run/20261009/cleanup/EMPTY_DIRECTORIES_EXECUTION_RECEIPT.json')
add('master_toolchain_preservation_plan.json','reports/master_run/20261009/cleanup/TOOLCHAIN_PRESERVATION_PLAN.json')
add('master_history_controls_git_objects.json','reports/master_run/20261009/publication/HISTORY_CONTROLS_GIT_OBJECTS.json')
add('master_history_controls_remote_readback.json','reports/master_run/20261009/publication/HISTORY_CONTROLS_REMOTE_READBACK.json')

decision=(work/'STAGE5_STAGE6_DEPENDENCY_DECISION.md').read_text()
decision+='''
## Implemented and checked — 2026-10-09

Prepared native configuration and scientific identity are now V2. The new gate
binds accepted released source receipts and actual source bytes. The optional
single-approved-accession owner mode enables one real checkpoint followed by
curation; the default queue remains full196. It cannot claim full-panel
completion after one genome. The separate curation producer and independent
checker now require the V2 identity and the same released source pins.

Native/source/owner/storage/interop checks:76 tests,73PASS,3actual Linux cases
skipped. Curation:66 synthetic tests PASS. Four Stage6 negative acceptance/join
gates PASS. Canonical G readback:202small acceptance/build receipts matched
their released-byte pins. No actual detector, WSL integration or production
curation was executed. See the exact source and test receipt in
`reports/master_run/20261009/preparation/stage5_source_split_preparation_checks.json`.

The renderer reads accepted tree, curation and join receipts. The root-owned
finalization workflow must separately invoke retained `validate_upstream`
before production join/render to require accepted Stage4 publication/readback.
This split changes no tree acceptance rule and creates no new native owner.
'''
(work/'master_source_split_DECISION.md').write_text(decision)
add('master_source_split_DECISION.md','docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md')
status=json.loads((work/'master_dependency_current_status.json').read_text())
status['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
status['native_process']=json.loads((work/'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_text())
status['stage5_dependency_decision']['state']='IMPLEMENTED_V2_SOURCE_AND_SYNTHETIC_CHECKS_PASS_ACTUAL_LINUX_NOT_RUN'
status['stage5_dependency_decision']['owner_scope']='Optional one approved checkpoint; default full196; exact exclusive lock unchanged'
status['cleanup']['public_history_archive']='FRESH_REMOTE_DOWNLOAD_ALL320_MEMBERS_AND291_SCIENTIFIC_COPIES_VERIFIED'
status['cleanup']['empty_directories_removed']=15
status['cleanup']['empty_directory_receipt']='reports/master_run/20261009/cleanup/EMPTY_DIRECTORIES_EXECUTION_RECEIPT.json'
(work/'master_source_split_current_status.json').write_text(json.dumps(status,indent=2)+'\n')
add('master_source_split_current_status.json','status/master_run_20261009.json')
prefix='''# Current execution status

## Stage 5 genome-source dependency split implemented — 2026-10-09

Prepared Stage 5 now uses accepted immutable genome sources independently of
Stage 4 tree success/publication. Config/identityV2 and curation compatibility
are implemented:76native/source/owner/storage/interop checks (73PASS,3actual
Linux cases skipped),66curation tests PASS and4Stage6 negative gates PASS.
All202canonical acceptance/build receipts match the released-byte source pins.
Default remains the full196 queue; optional single approved checkpoint mode
never claims full-panel completion. Actual Stage 5 searches, production
curation and Stage 6 production rendering remain NOT_RUN. See
`docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md`.

The sole full196 partitioned IQ-TREE job continues under its original exclusive
native owner; candidate optimization has reached iteration40. Actual Stage 5
execution awaits exact native closure/lock release and WSL resource/lifecycle
proofs, rather than Stage 4 scientific acceptance. Final tree join and figure
still require independent host-tree acceptance plus the separate workflow
publication/readback gate.

Cleanup:224inactive files/2,207,024,265bytes and15exact empty directories have
been removed after published recovery proposals. The public history archive
passed a fresh independent GitHub download:320members,291scientific copies,
88,441public metadata rows and all declared historical validation records.
Another47,648old scientific files match release members but remain local;
619unmatched files and active runtime/tools are preserved. The host is not
ready to wipe. Full toolchain preservation is planned separately.

'''
(work/'master_source_split_STATUS.md').write_text(prefix+(work/'master_dependency_STATUS.md').read_text())
add('master_source_split_STATUS.md','STATUS.md')
out=work/'master_source_split_git_plan.json';assert not out.exists()
out.write_text(json.dumps({'expected_head':'66d939a1bcfb399fa7fd5163c860d03c1aaf5c41',
 'message':'Implement source-gated Stage5 genome checkpoints and independent V2 curation; verify history recovery',
 'files':rows},indent=2)+'\n')
print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows)}))
