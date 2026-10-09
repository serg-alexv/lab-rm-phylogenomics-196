"""Publish actual accepted full tree certificate and reviewed nonscientific setup sources."""
from pathlib import Path
import datetime,hashlib,json
W=Path(__file__).resolve().parent;O=W/'master_acceptance_setup11';O.mkdir(exist_ok=False)
B='reports/master_run/20261009/';files=[]
def add(p,t):
 p=Path(p)
 if not p.is_absolute():p=W/p
 raw=p.read_bytes();assert len(raw)<5*1024**2
 files.append(dict(local_absolute_path=str(p),target=t,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
for name in ('independent_validation.json','driver_receipt.json','stdout.txt','stderr.txt'):
 add('stage04_acceptance_actual02/'+name,B+'stage04/acceptance_actual02/'+name)
cert=json.loads((W/'stage04_acceptance_actual02/independent_validation.json').read_bytes())
assert cert['state']=='COMPLETE_VALIDATED' and cert['unique_tips']==196 and cert['ufboot_replicates']==1000
for row in json.loads((W/'stage5_setup_publication_files.json').read_bytes())['files']:
 raw=Path(row['local_path']).read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 add(row['local_path'],row['suggested_remote_path'])
add('stage5_setup_publication_files.json',B+'stage5/post_iq_setup/PUBLICATION_FILES.json')
for name in ('reconcile_canonical_after_native.py',Path(__file__).name):add(name,'scripts/master_run/'+name)
for name in ('master_native_closure10_git_objects.json','master_native_closure10_remote_readback.json'):
 add(name,B+'publication/'+name)
s=json.loads((W/'master_native_closure10/status.json').read_bytes())
now=datetime.datetime.now(datetime.timezone.utc).isoformat();s['updated_utc']=now
s['scientific_status']='STAGE04_COMPLETE_VALIDATED_FULL196_RELEASE_PENDING'
s['stage04_acceptance']='PASS_ACTUAL02_COMPLETE_VALIDATED_EXACT196_389_BRANCHES_193_PAIRED1000_UFBOOT'
s['stage04_acceptance_receipt']=B+'stage04/acceptance_actual02/independent_validation.json'
s['stage04_tree_sha256']=cert['native_tree_sha256']
s['stage04_publication_preparation']['state']='INDEPENDENT_ACCEPTANCE_PASS_PORTABLE_RELEASE_NEXT'
s['stage5_setup_preparation']='PEER_REVIEW_PASS10_SYNTHETIC_TESTS_ACTUAL_WSL_NOT_RUN'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
md=(W/'master_native_closure10/STATUS.md').read_text(encoding='utf-8')
start=md.index('Independent acceptance is pending.');end=md.index('\n\nStage5 dependency',start)
md=md[:start]+'''Independent acceptance attempt02 PASS: exactly196approved tips,389finite nonnegative branches,193paired supported internal branches and1000actual approved-panel bootstrap trees. The full native outputs and accepted sources are frozen with exact SHA manifests. The initial checker format failure and corrected reviewed source/41tests remain preserved. Native composition/model and near-zero-branch warnings remain unchanged. Portable Release upload and fresh payload readback are next; publication is a separate gate.'''+md[end:]
md=md.replace('|4|Native completed; independent acceptance and Release pending|','|4|COMPLETE_VALIDATED; portable Release/readback pending|')
md=md.replace('Sources for those bounded gates are being reviewed now that Stage4 operational closure is established.','Those bounded setup sources pass independent review and ten synthetic checks; actual execution remains pending.')
md=md.replace(s.get('updated_utc','impossible'),now) if False else md
md=md.replace(json.loads((W/'master_native_closure10/status.json').read_bytes())['updated_utc'],now)
(O/'STATUS.md').write_text(md,encoding='utf-8')
add(O/'status.json','status/master_run_20261009.json');add(O/'STATUS.md','STATUS.md')
with (W/'master_acceptance_setup11_git_plan.json').open('x',encoding='utf-8') as f:
 json.dump({'expected_head':'854a13ccc1050307c6cd0daffe07c9f43d262885','message':'Accept independently validated full196 Stage4 host tree; publish reviewed Stage5 operational setup sources','files':files},f,indent=2);f.write('\n')
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
