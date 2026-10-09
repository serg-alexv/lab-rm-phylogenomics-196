"""Prepare an exact public source allowlist in C; no Git/remote/G mutation."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re

WORK = Path(__file__).resolve().parent
CHAT = WORK.parent
CODE = 'scripts/master_run/'
EVIDENCE = 'reports/master_run/20261009/preparation/'
LIMIT = 5*1024**2
items = []
targets = set()
patterns = [rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{30,}',
            rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            rb'(?i)authorization\s*[:=]\s*["\x27]?bearer\s+[A-Za-z0-9._-]{20,}']

def add(source,target,kind):
    source = Path(source)
    assert source.is_file() and not source.is_symlink(), source
    assert source.resolve().is_relative_to(CHAT.resolve()), source
    assert target not in targets and not any(x in target for x in ('.private','codex_events','session_transcript','token_cache'))
    data = source.read_bytes()
    assert len(data) < LIMIT, source
    assert not any(re.search(pattern,data) for pattern in patterns), source
    try:
        data.decode('utf-8-sig')
        encoding = 'utf-8'
    except UnicodeDecodeError:
        encoding = 'base64'
    items.append({'local_absolute_path':str(source.resolve()),'target':target,
                  'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
                  'git_blob_sha1':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),
                  'transport_encoding':encoding,'kind':kind,
                  'biological_acceptance':'NOT_ESTABLISHED_BY_SOURCE_PUBLICATION'})
    targets.add(target)

root_code = '''atomic_iqtree_windows.py test_atomic_iqtree_windows.py smoke_atomic_iqtree_windows.py
prepare_atomic_attempt.py resource_maintenance.py publish_bootstrap.py finalize_bootstrap.py
independent_tree_check.py test_independent_tree_check.py test_stage4_freeze_copy_integration.py
prepare_stage4_publication.py publish_stage4_primary.py test_stage4_publish_science.py
stage5_atomic_process.py stage5_atomic.py stage5_windows_owner.py stage5_work_storage.py
test_stage5_atomic.py test_stage5_atomic_live_linux.py test_stage5_windows_owner.py test_stage5_work_storage.py
stage5_drivefs_filesystem_smoke.py stage5_interop_linux_fixture.py stage5_interop_smoke_windows.py
test_stage5_interop_contracts.py stage06_render.py check_stage06_outputs.py test_stage06_render.py
make_stage06_density_fixture.py prepare_master_remote_update.py audit_remote_progress_readonly.py
prepare_master_source_plan.py'''.split()
for name in root_code:
    add(WORK/name,CODE+name,'PROJECT_SOURCE_OR_SYNTHETIC_TEST')
root_evidence = '''stage04_finalization_preparation_checks.json stage4_freeze_copy_checks.json
stage5_atomic_build_checks.json stage5_atomic_config.template.json stage5_atomic_IMPLEMENTATION.md
stage5_audit.md stage5_drivefs_filesystem_smoke.md stage5_drivefs_preparation_checks.json
stage5_interop_preparation_checks.json stage5_interop_smoke.md stage5_io_scope_review.md
stage5_runtime_readonly_assessment.md stage06_preparation_checks.json stage06_preparation.md
iqtree_identical_support_source_review.md rm_curation_methodological_review.md stage05_raw_export_review.md'''.split()
for name in root_evidence:
    add(WORK/name,EVIDENCE+name,'PREPARATION_EVIDENCE_NO_SCIENTIFIC_RESULT')
for source in sorted((WORK/'independent_inputs').iterdir()):
    if source.is_file() and source.suffix in ('.py','.json','.md','.tsv','.txt'):
        dest = (CODE if source.suffix == '.py' else EVIDENCE)+'independent_inputs/'+source.name
        add(source,dest,'ACCEPTED_INPUT_QA_OR_SOURCE_RESOURCE_REVIEW')
for folder in ('stage05_curation','stage05_curation_review','stage06_review'):
    for source in sorted((WORK/folder).rglob('*')):
        if source.is_file() and '__pycache__' not in source.parts and (source.suffix in ('.py','.json','.md','.tsv') or source.name == 'SHA256SUMS'):
            relative = source.relative_to(WORK).as_posix()
            # Preserve the complete curation package's relative data/docs layout.
            if folder == 'stage05_curation' or source.suffix == '.py':
                add(source,CODE+relative,'CURATION_OR_REVIEW_SOURCE_PACKAGE')
            if source.suffix != '.py':
                add(source,EVIDENCE+relative,'PREPARATION_REVIEW_OR_SYNTHETIC_CHECK')
add(WORK/'iqtree_3_1_4_source_review/source_pin.json',EVIDENCE+'iqtree_3_1_4_source_review/source_pin.json','PINNED_PRIMARY_SOURCE_REVIEW')
for name in ('WD_resource_configuration.md','wslconfig.before.txt','wslconfig.applied.txt'):
    add(CHAT/'outputs'/name,EVIDENCE+'resource_configuration/'+name,'EXECUTED_RESOURCE_CONFIGURATION_NOT_BIOLOGICAL_COMPLETION')
for name in ('wsl_toolchain_probe_final.txt','probe_wsl.sh','resource_cleanup_20261009T161511Z.json','scheduled_tasks.json'):
    add(WORK/'bootstrap'/name,EVIDENCE+'resource_configuration/'+name,'EXECUTED_SCOPED_OPERATIONAL_EVIDENCE')
for source in sorted((WORK/'stage06_density_synthetic_v4').rglob('*')):
    if source.is_file() and source.suffix in ('.json','.txt','.tsv','.nwk','.nex','.svg','.pdf','.png'):
        add(source,EVIDENCE+source.relative_to(WORK).as_posix(),'EXPLICIT_NONBIOLOGICAL_SYNTHETIC_PROOF_ONLY')
deferred = []
for folder in ('independent_inputs/iqtree314_source','iqtree_3_1_4_source_review'):
    for source in sorted((WORK/folder).iterdir()):
        if source.is_file() and source.suffix in ('.cpp','.h'):
            data = source.read_bytes()
            deferred.append({'local_absolute_path':str(source.resolve()),'sha256':hashlib.sha256(data).hexdigest(),
                             'bytes':len(data),'disposition':'SOURCE_REVIEW_SNAPSHOT_FOR_LATER_HASHED_RELEASE_WITH_ORIGINAL_NOTICES'})
plan = {'schema':'LAB_RM_MASTER_SOURCE_PUBLICATION_PLAN_V1','utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'expected_remote_head':'83059864f424fc6db7beebaa898f1f0019bc4d51',
        'state':'C_ONLY_PREPARED_NOT_PUBLISHED','actual_stage04_acceptance':'NOT_RUN',
        'actual_stage05_native_interoperability':'NOT_RUN','actual_stage05_biological_searches':'NOT_RUN',
        'actual_stage05_architecture_curation':'NOT_RUN','actual_stage06_scientific_figure':'NOT_RUN',
        'git_blob_limit_bytes_exclusive':LIMIT,'files':items,
        'total_files':len(items),'total_bytes':sum(i['bytes'] for i in items),
        'binary_blobs':[i['target'] for i in items if i['transport_encoding']=='base64'],
        'refresh_rule':'Rehash every source immediately before constructing Git objects; stop on any changed bytes. Checks may be refreshed only with corresponding executed evidence.',
        'execution_layout':'Source snapshots retain bytes and sibling imports. Curation subtree includes exact relative data. Entry points assuming original chat/work layout must be materialized in that layout or receive a separately reviewed runtime adaptation before execution elsewhere.',
        'exclusions':['live iqtree_attempts/','stage04_partitioned_config.json original launch config','raw Codex/session/private events','unrelated user files','unknown or unreviewed directories'],
        'deferred_release_inputs':deferred}
output=WORK/'master_source_publication_plan.json'
output.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'plan':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
                  'files':len(items),'bytes':plan['total_bytes'],'binary_blobs':plan['binary_blobs'],
                  'deferred_primary_source_files':len(deferred)},indent=2))
