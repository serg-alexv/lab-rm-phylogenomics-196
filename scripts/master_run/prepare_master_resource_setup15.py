"""Publish exact actual recovery proofs and reviewed scoped setup sources before execution."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/';extras={}
mapping=json.loads((W/'stage5_setup_resource_failure_finalizer_publication_files.json').read_bytes())
for row in mapping['files']:
 p=Path(row['local_path']);raw=p.read_bytes()
 if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Frozen finalizer source drift')
 extras[p.relative_to(W).as_posix()]=row['suggested_remote_path']
extras.update({
 'stage5_setup_resource_failure_finalizer_publication_files.json':B+'stage5/setup_resource_failure_finalizer/PUBLICATION_FILES.json',
 'STAGE5_CONFIG_FINALIZER_PIN_REFRESH.md':B+'stage5/setup_resource_failure_finalizer/STAGE5_CONFIG_FINALIZER_PIN_REFRESH.md',
 'stage5_failed_scope_diagnostic01/receipt.json':B+'stage5/failed_scope_diagnostic01/ACTUAL_RECEIPT.json',
 'stage5_failed_scope_diagnostic01/stdout.json':B+'stage5/failed_scope_diagnostic01/ACTUAL_LINUX_OBSERVATION.json',
 'stage5_failed_scope_diagnostic01/stderr.txt':B+'stage5/failed_scope_diagnostic01/ACTUAL_STDERR.txt',
 'directory_prune_execution01_readback_20261009T222435Z_b247fd3a/receipt.json':B+'cleanup/directory_prune_execution01/REMOTE_READBACK.json',
 'apply_scoped_wsl_resource_repair.py':'scripts/master_run/apply_scoped_wsl_resource_repair.py',
 'apply_scoped_wsl_resource_repair_review_draft83045.py':'scripts/master_run/apply_scoped_wsl_resource_repair_review_draft83045.py',
 'test_scoped_wsl_resource_repair.py':'scripts/master_run/test_scoped_wsl_resource_repair.py',
 'wsl_resource_repair15_independent_review.json':B+'stage5/wsl_resource_repair15/INDEPENDENT_SOURCE_REVIEW.json',
 'master_failure_closure14_git_objects.json':B+'publication/master_failure_closure14_git_objects.json',
 'master_failure_closure14_remote_readback.json':B+'publication/master_failure_closure14_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name,
})
for name in ('wslconfig.before.txt','wslconfig.after.txt','original_failed_stop.json','proposal.json'):
 extras['wsl_resource_repair15/'+name]=B+'stage5/wsl_resource_repair15/'+name
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','530446825d8cd9269a1e9cd72cf34bda2757173a',
 '--name','master_resource_setup15','--previous-status',str(W/'master_failure_closure14/status.json'),
 '--previous-markdown',str(W/'master_failure_closure14/STATUS.md'),
 '--phase','Publish fresh full cleanup-journal recovery PASS and reviewed Stage5 finalizer plus scoped WSL4GiB restart proposal']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
# Update only statuses supported by the exact actual receipts, before capturing Git bytes.
O=W/'master_resource_setup15';s=json.loads((O/'status.json').read_bytes())
r=json.loads((W/'directory_prune_execution01_readback_20261009T222435Z_b247fd3a/receipt.json').read_bytes())
if r['state']!='PASS_FRESH_REMOTE54_MEMBERS_5542_JOURNAL_POSTCHECK_JOIN':raise ValueError('Actual archive recovery PASS required')
s['cleanup']['empty_directory_proposal']['full_journal_remote_recovery']=r['state']
s['cleanup']['empty_directory_proposal']['full_journal_remote_receipt']=B+'cleanup/directory_prune_execution01/REMOTE_READBACK.json'
s['cleanup']['empty_directory_proposal']['execution_preparation']['production_execution']='EXIT0_INDEPENDENT_POSTVERIFY_PASS'
s['scientific_status']='STAGE04_COMPLETE_VALIDATED_FULL196_RELEASE_AND_INDEPENDENT_REMOTE_PASS_STAGE5_NOT_RUN'
s['recovery_preparation']['conda_originals']['remote_reader']='ACTUAL_FRESH_FULL_PAYLOAD_PASS_26_OWNED_COMMANDS_EXIT0'
s['stage5_setup_preparation']='FINALIZER_AND_CURRENT_CONFIG_PINS_PEER_PASS_19_PURE_TESTS_NEW_ACTUAL_SETUP_NOT_RUN'
s['stage5_wsl_resource_repair15']='REVIEWED_PREPARED_NOT_APPLIED_EXACT6TO4GIB_AND_ONE_AUTHORIZED_VM_STOP'
s['stage5_current_stop_sha256']='ef5e47644dc961ed1945d707c3dd993fe9f0370980f094ff741a3d1253d13462'
s['host_wipe_ready']=False
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
md=(O/'STATUS.md').read_text(encoding='utf-8')
md=md.replace('The full 5,542-directory execution journal now has a locally verified 54-member recovery ZIP; remote upload and fresh readback remain pending.',
 'The full 5,542-directory execution journal passes fresh GitHub recovery readback: all54ZIP members/53SUMS/50originals and16,628ordered journal records join to the independent postcheck; all25owned download commands exited0.')
md=md.replace('Those bounded setup sources pass independent review and ten synthetic checks; actual execution remains pending.',
 'The latest setup finalizer and current configuration source pins pass independent review and19pure checks. Actual replacement setup remains pending; previous failed scopes and their lost terminal uncertainty are preserved.')
md+='\nScoped WSL repair15 is reviewed and PREPARED_NOT_APPLIED: exact6-to4GiB RAM ceiling, CPU4/swap8GiB/houridle unchanged, one authorized Ubuntu/VM stop under the original lock, and two actual stopped readbacks before exact own-stop removal. The prior lost Windows terminal will remain NOT_RECONSTRUCTED.\n'
(O/'STATUS.md').write_text(md,encoding='utf-8')
planpath=W/'master_resource_setup15_git_plan.json';plan=json.loads(planpath.read_bytes())
for row in plan['files']:
 raw=Path(row['local_absolute_path']).read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
planpath.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
