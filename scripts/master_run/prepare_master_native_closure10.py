"""Preserve actual native closure, checker correction and recovery preparation."""
from pathlib import Path
import datetime,hashlib,json
W=Path(__file__).resolve().parent
O=W/'master_native_closure10';O.mkdir(exist_ok=False)
B='reports/master_run/20261009/'
files=[]
def add(name,target):
 p=Path(name)
 if not p.is_absolute():p=W/p
 raw=p.read_bytes();assert len(raw)<5*1024**2
 files.append(dict(local_absolute_path=str(p),target=target,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
for name in ('independent_tree_check.py','independent_tree_check_attempt01.py',
 'accept_stage4_after_native_closure.py','accept_stage4_after_native_closure_attempt01.py',
 'test_stage4_support_execution.py','test_stage4_freeze_copy_integration.py',
 'test_stage4_freeze_copy_integration_attempt01.py','prepare_stage4_publication.py',
 'publish_stage4_primary.py','prepare_stage4_publication_before_support_test.py',
 'publish_stage4_primary_before_support_test.py','audit_stage04_actual_native_formats_executed_stdin.py',
 'audit_stage04_official_emission_executed_stdin.py',Path(__file__).name):
 add(name,'scripts/master_run/'+name)
for name in ('stage04_support_execution_regression.json','stage04_support_execution_independent_review.json',
 'stage04_actual_native_format_audit.json','stage04_sh_alrt_official_emission_evidence.json',
 'stage04_support_test_package_independent_review.json','stage04_read_only_audit_execution_history.json'):
 add(name,B+'stage04/acceptance_preparation/'+name)
for name in ('result.json','exit.json','launch.json','lock_released.json','execution_state_restored.json'):
 add('iqtree_attempts/partitioned_20261009T162904Z/'+name,B+'stage04/native_closure/'+name)
for name in ('retained_live.json','receipt.json'):
 add('iqtree_controller_closure_actual01/'+name,B+'stage04/controller_closure_actual01/'+name)
for name in ('independent_validation.json','stdout.txt','stderr.txt','driver_receipt.json'):
 add('stage04_acceptance_actual01/'+name,B+'stage04/acceptance_actual01_failed/'+name)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
terminal={'schema':'MASTER_ROOT_OBSERVED_NATIVE_TERMINALS_V1','utc':now,
 'native_owner_unified_session':9419,'native_owner_terminal_exit_code':0,
 'retained_controller_observer_unified_session':72951,'retained_controller_observer_terminal_exit_code':0,
 'scope':'Root observed actual unified-tool terminal returns; exact process birth, job closure, original unlock and power restore are separately retained.',
 'native_inference_rerun':False,'first_checker_failure_preserved':True,
 'scientific_acceptance':'PENDING_ACTUAL02_INDEPENDENT_CHECK','native_elapsed_seconds':19158.7126516}
(O/'root_terminal_observation.json').write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf-8')
add(O/'root_terminal_observation.json',B+'stage04/native_closure/ROOT_TERMINAL_OBSERVATION.json')
completion=json.loads((W/'directory_prune_execution_archive_completion.json').read_bytes())
assert completion['actual_builder_tool_exit_code']==0 and completion['member_count']==54
for row in completion['public_control_mapping']:
 p=Path(row['path']);raw=p.read_bytes()
 assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 add(p,row['suggested_repository_path'])
add('directory_prune_execution_archive_completion.json',B+'cleanup/directory_prune_execution01/PUBLIC_COMPLETION.json')
for name in ('master_verified_directory_publication09_git_objects.json','master_verified_directory_publication09_remote_readback.json'):
 add(name,B+'publication/'+name)
s=json.loads((W/'master_verified_directory_and_publication09/status.json').read_bytes())
s.update(updated_utc=now,stage04_execution='NATIVE_EXIT0_EXACT_JOB_CONTROLLER_UNLOCK_POWER_CLOSURE_VERIFIED',
 stage04_acceptance='FIRST_CHECKER_FORMAT_FAILURE_PRESERVED_CORRECTED_SOURCE_REVIEWED41_TESTS_PASS_ACTUAL02_PENDING')
s['scientific_status']='STAGE04_NATIVE_COMPLETED_INDEPENDENT_ACCEPTANCE_PENDING'
s['local_checkout_note']='Exact current native/controller/job/unlock/power closure established; reconcile G under original lock while preserving six dirty tracked hashes.'
s['stage04_publication_preparation']={'state':'TEXT_FORMAT_AND_SH_EXECUTION_FORMAT_CORRECTED_REVIEWED_TESTED_ACTUAL_PUBLICATION_PENDING','native_runner_unchanged':True}
s['native_process']={'state':'CLOSED','pid':4768,'creation_filetime':134360369876207076,'exit_code':0,'job_active_processes':0,
 'controller_pid':27048,'controller_creation_filetime':134360369803845506,'controller_exit_code':0}
s['cleanup']['empty_directory_proposal']['full_journal_remote_recovery']='LOCAL54_MEMBER_ARCHIVE_PASS_REMOTE_UPLOAD_READBACK_PENDING'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
md=f'''# Current execution status

Updated {now}. Direct continuation active; automatic resume disabled. GitHub main and independently verified Release assets are the durable project authority.

Stage4 native IQ-TREE 3.1.4 completed all 196 approved taxa, 100 partitions and 17,456 AA columns, including 1,000 SH-like aLRT replicates and 1,000 ultrafast bootstrap trees. Actual native and retained controller exit 0, empty Job, original byte unlock and power-state restoration are retained. No inference rerun is required.

Independent acceptance is pending. The first checker rejected the native phrase “SH-like aLRT” because its pattern expected “SH-aLRT”; that exact failure and original source are preserved. The corrected parser requires the completed native test in both streams, matching finite durations and the paired-support interpretation. It passes 41 regression checks and independent review. Actual acceptance attempt02 and full tree Release readback are next. Native warnings, including composition tests and near-zero branches, remain unchanged.

Stage5 dependency split V2 is implemented in addf594d: queue complete approved genomes and per-genome curation independently of host-tree acceptance. All 196 source bundles are verified. WD retains one native owner. Actual WSL/runtime/storage/interop/UNC setup and detectors remain NOT_RUN. Sources for those bounded gates are being reviewed now that Stage4 operational closure is established. Final Stage6 requires the accepted separately published full tree and independently curated 196-by-4 cells; failed, unresolved and not-run never mean absence. See `docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md`.

Cleanup: 48,490 exact files / 9,756,853,507 logical bytes and 5,557 exact directories removed with protected hashes and recovery evidence. Physical reclaimed bytes NOT_MEASURED. The full 5,542-directory execution journal now has a locally verified 54-member recovery ZIP; remote upload and fresh readback remain pending. The qualified DriveFS zero-link metadata limitation remains explicit.

Recovery: all 339 original Conda packages, 1,938 IQ-TREE/submodule Gitblob bindings, 194 public changed-history originals, and prior cleanup recovery assets pass fresh GitHub payload readback. Installed-runtime/local-modification recovery and actual cold restoration remain pending. Private data is excluded. Active tools, stable original lock, accepted inputs, six dirty G files and installed toolchain remain protected. G can now be reconciled under the original lock while preserving those hashes. The host is not ready to wipe.

| Stage | Scientific state |
|---|---|
|0–3|Accepted upstream results preserved|
|4|Native completed; independent acceptance and Release pending|
|5|Source readiness PASS; actual detectors/curation NOT_RUN|
|6|Production figure NOT_RUN; synthetic proofs only|
|7|Final scientific review NOT_RUN|

Evidence: `status/master_run_20261009.json` and `docs/master_run/STORAGE_LEDGER.md`.
'''
(O/'STATUS.md').write_text(md,encoding='utf-8')
add(O/'status.json','status/master_run_20261009.json');add(O/'STATUS.md','STATUS.md')
assert len({r['target'] for r in files})==len(files)
plan={'expected_head':'66369867feafd940298b11786bf972c5a55a6507','message':'Record actual Stage4 native closure; preserve and correct SH support checker before acceptance; archive full directory journal','files':files}
with (W/'master_native_closure10_git_plan.json').open('x',encoding='utf-8') as f:json.dump(plan,f,indent=2);f.write('\n')
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
