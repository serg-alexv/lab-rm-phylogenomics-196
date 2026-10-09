"""Preserve actual authorized WSL repair and the failed canonical fast-forward."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/';extras={
 'canonical_post_wsl_resource_repair15.json':B+'publication/CANONICAL_FAST_FORWARD_ATTEMPT15_FAILED.json',
 'master_resource_setup15_git_objects.json':B+'publication/master_resource_setup15_git_objects.json',
 'master_resource_setup15_remote_readback.json':B+'publication/master_resource_setup15_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name,
}
for stem in ('registered_before','fresh_observation','authorized_shutdown','registered_stopped01','registered_stopped02'):
 for suffix in ('.stdout.txt','.stderr.txt'):
  name=stem+suffix;extras['wsl_resource_repair15/'+name]=B+'stage5/wsl_resource_repair15/actual/'+name
extras['wsl_resource_repair15/execution_receipt.json']=B+'stage5/wsl_resource_repair15/ACTUAL_EXECUTION_RECEIPT.json'
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','24e2299ae5a118e99aeb9b52d8cf6f973127d9bb',
 '--name','master_resource_actual16','--previous-status',str(W/'master_resource_setup15/status.json'),
 '--previous-markdown',str(W/'master_resource_setup15/STATUS.md'),
 '--phase','Actual scoped WSL4GiB repair and aggregate VM closure PASS; preserve failed canonical fast-forward for read-only diagnosis']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
O=W/'master_resource_actual16';r=json.loads((W/'wsl_resource_repair15/execution_receipt.json').read_bytes())
if not (r['state']=='PASS_AUTHORIZED_VM_STOP_4GIB_CONFIG_AGGREGATE_SCOPE_CLOSED'
 and r['owned_stop_removed'] is True and r['original_lock_explicitly_released'] is True
 and len(r['commands'])==5 and all(c['retained_terminal']['exit_code']==0 for c in r['commands'])):raise ValueError('Actual authorized repair proof required')
s=json.loads((O/'status.json').read_bytes());s['stage5_wsl_resource_repair15']=r['state']
s['stage5_wsl_resource_repair15_receipt_sha256']=hashlib.sha256((W/'wsl_resource_repair15/execution_receipt.json').read_bytes()).hexdigest()
s['stage5_current_stop_sha256']='EXACT_PRIOR_STOP_REMOVED_AFTER_SEPARATE_ACTUAL_VM_CLOSURE'
s['local_checkout_note']='Canonical G fast-forward failed before HEAD update; preserve failure, independent read-only byte/index diagnosis pending; no reset/clean/force operation.'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
md=(O/'STATUS.md').read_text(encoding='utf-8')
md+='\nActual repair15 PASS: configuration SHA31b59c84, one actual owned WSL shutdown and two actual Ubuntu-Stopped readbacks, exact backed-up STOP removed, original byte lock released. Prior lost Windows terminal remains NOT_RECONSTRUCTED. New runtime/setup/science remains NOT_RUN. Canonical G fast-forward failed; its receipt is preserved and read-only diagnosis is pending. No reset/clean/force was used.\n'
(O/'STATUS.md').write_text(md,encoding='utf-8')
planpath=W/'master_resource_actual16_git_plan.json';plan=json.loads(planpath.read_bytes())
for row in plan['files']:
 raw=Path(row['local_absolute_path']).read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 if b'\0' in raw:row['transport_encoding']='base64'
planpath.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
