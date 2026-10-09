"""Publish the preserved failed setup scope and the exact reviewed lease correction."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mapping',type=Path,required=True)
p.add_argument('--review',type=Path,required=True);a=p.parse_args();extras={}
for row in json.loads(a.mapping.read_bytes())['files']:
 q=Path(row['local_path']);raw=q.read_bytes()
 if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Frozen source mapping drift')
 extras[q.relative_to(W).as_posix()]=row['suggested_remote_path']
extras.update({
 a.mapping.relative_to(W).as_posix():B+'stage5/owned_lease_retry/CURRENT_PREPARATION.json',
 a.review.relative_to(W).as_posix():B+'stage5/owned_lease_retry/CURRENT_INDEPENDENT_ROOT_REVIEW.json',
 'stage5_owned_lease_retry_preparation.json':B+'stage5/owned_lease_retry/INITIAL_PREPARATION.json',
 'stage5_owned_lease_retry_independent_root_review.json':B+'stage5/owned_lease_retry/INITIAL_INDEPENDENT_ROOT_REVIEW.json',
 'review_stage5_owned_lease_retry.py':'scripts/master_run/review_stage5_owned_lease_retry.py',
 'review_stage5_owned_lease_retry_interop.py':'scripts/master_run/review_stage5_owned_lease_retry_interop.py',
 'master_resource_actual16_git_objects.json':B+'publication/master_resource_actual16_git_objects.json',
 'master_resource_actual16_remote_readback.json':B+'publication/master_resource_actual16_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name,
})
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','f9ca5802ec550ac2fe769aeed771a071a2e57056',
 '--name','master_lease_setup17','--previous-status',str(W/'master_resource_actual16/status.json'),
 '--previous-markdown',str(W/'master_resource_actual16/STATUS.md'),
 '--phase','Preserve actual closed failed toolchain02 scope; publish reviewed bounded own-lease replacement and current exact setup pins']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
O=W/'master_lease_setup17';s=json.loads((O/'status.json').read_bytes())
s['stage5_actual_setup']['stage5_setup_toolchain_actual_postiq_02']='FAILED_WINDOWS_LEASE_REPLACE_WITH_ACTUAL_LINUX_MOUNT_PASS_AND_PROVEN_SCOPE_CLOSURE'
s['stage5_setup_preparation']='CURRENT_SCOPED_LEASE_RETRY_PEER_PASS_ACTUAL_REPLACEMENT_SETUP_NOT_RUN'
s['stage5_current_stop_sha256']='NO_UNPROVEN_STOP_AFTER_ACTUAL_TOOLCHAIN02_CLOSURE'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
md=(O/'STATUS.md').read_text(encoding='utf-8')
md+='\nToolchain02 stays FAILED: Windows own-lease replacement returned WinError5; the actual Linux mount exited0, retained WSL exit0/native empty scope and original unlock are recorded, and no unproven STOP remains. Sharing contention is inferred. The bounded own-lease correction is reviewed and published before any replacement setup. Scientific searches remain NOT_RUN.\n'
(O/'STATUS.md').write_text(md,encoding='utf-8')
planpath=W/'master_lease_setup17_git_plan.json';plan=json.loads(planpath.read_bytes())
for row in plan['files']:
 raw=Path(row['local_absolute_path']).read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
planpath.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
