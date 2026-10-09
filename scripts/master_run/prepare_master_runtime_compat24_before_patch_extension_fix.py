"""Publish independently reviewed runtime cache/pidfd sources and actual VM closure."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/';extras={};binary=[]
mapping=W/'stage5_pidfd_runtime_preparation.json'
assert hashlib.sha256(mapping.read_bytes()).hexdigest()=='cb52bf39e07d6c39e79d90ec8b19c0b4561e70553349ea448a07c7cab61a69c8'
m=json.loads(mapping.read_bytes())
for row in m['files']:
 p=Path(row['local_path']);raw=p.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 if p.suffix=='.diff':
  binary.append(dict(local_absolute_path=str(p),target=row['suggested_remote_path'],bytes=len(raw),sha256=row['sha256'],transport_encoding='base64'))
 else:extras[p.relative_to(W).as_posix()]=row['suggested_remote_path']
for row in m['active_source_pin_checks']:
 assert hashlib.sha256((W/row['member']).read_bytes()).hexdigest()==row['sha256']
 assert row['sha256'] in (W/row['consumer']).read_text()
actual=W/'stage5_interop_vm_scope_41cf1297c98748aeb0e02351814eb83c'
assert hashlib.sha256((actual/'receipt.json').read_bytes()).hexdigest()=='c474c48efa544d0f7451163172054ff81b22d9ff6eb7c9186992c6331b711343'
for p in sorted(actual.iterdir()):
 assert p.is_file() and p.suffix in ('.json','.txt');extras[p.relative_to(W).as_posix()]=B+'stage5/interop_scope23/actual/'+p.name
review={'schema':'MASTER_RUNTIME_COMPAT_ROOT_REVIEW_V1','state':'PASS_SOURCE_AND_PURE_TESTS_ACTUAL_LINUX_REQUIRED',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_map_sha256':hashlib.sha256(mapping.read_bytes()).hexdigest(),
 'root_actual_tests':'17 new pidfd/hash pure contracts PASS0.247s',
 'checks':['Full new pidfd wrapper/probe and targeted sha function read',
 'Typed exact libc symbols only when individual Python API absent; existing Python errors not bypassed',
 'Actual kernel fd birth/probe/closure semantics remain; no PID-only signal/syscall-number alternative',
 'Large plain canonical files within exact3 retained runtime roots only; readonly fd, bounded1MiB bytes, identical SHA',
 'Full identity/size/mtime/ctime checks, completed-page8MiB hints, final page retained, errors reject',
 '29 operative dependency hashes independently reread and present in consumer source',
 'Both independent reviews PASS; historical originals/receipts preserved'],
 'limitations':['No actual libc export/fadvise behavior or resource benefit accepted by this source review',
 'All new current actual operational gates must be rerun before first genome',
 'Detector argv/model bytes/coverage/curation/scientific accounting unchanged']}
r=W/'stage5_runtime_compat_root_review24.json'
if r.exists():
 old_review=json.loads(r.read_bytes());assert old_review['source_map_sha256']==review['source_map_sha256'] and old_review['state']==review['state']
else:
 with r.open('x',encoding='utf-8') as f:json.dump(review,f,indent=2);f.write('\n')
extras.update({mapping.name:m['report_suggested_remote_path'],r.name:B+'stage5/pidfd_runtime_compat/'+r.name,
 'master_scope_closure23_git_objects.json':B+'publication/master_scope_closure23_git_objects.json',
 'master_scope_closure23_remote_readback.json':B+'publication/master_scope_closure23_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name,
 'prepare_master_runtime_compat24_before_extension_fix.py':'scripts/master_run/prepare_master_runtime_compat24_before_extension_fix.py'})
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','95547b30a1f701977667b02c4dbbdfb404f1b66c',
 '--name','master_runtime_compat24b','--previous-status',str(W/'master_scope_closure23/status.json'),
 '--previous-markdown',str(W/'master_scope_closure23/STATUS.md'),
 '--phase','Publish peer-reviewed libc pidfd compatibility and bounded exact runtime hash cache hints; actual authorized WSL scope closure PASS config unchanged']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
O=W/'master_runtime_compat24b';s=json.loads((O/'status.json').read_bytes())
s['stage5_interop_scope_reconciliation']='ACTUAL_PASS_c474c48_AUTHORIZED_VM_SHUTDOWN_TWO_STOPPED_CONFIG31b_UNCHANGED_ALL_CLIENTS_CLOSED_ORIGINAL_UNLOCK_EXACT_LOCALSTOP_BACKED_AND_REMOVED'
s['stage5_pidfd_compatibility']='SOURCE_PEERS_AND_PURE_TESTS_PASS_e5be8997; actual retained Conda kernel ABI integration NOT_RUN'
s['stage5_runtime_discovery']='SOURCE500dc3f1 targeted readonly chunked hashes/cache hints peer PASS; actual effect unmeasured; new current setup/runtime gates NOT_RUN'
s['stage5_current_stop_sha256']='NO_UNPROVEN_STANDARD_OR_INTEROP_STOP_AFTER_ACTUAL_AUTHORIZED_VM_SCOPE_CLOSURE'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
with (O/'STATUS.md').open('a',encoding='utf-8') as f:
 f.write('\nAuthorized shutdown-only reconciliation actualPASSc474c48: exact local interop stop backed up, one retained WSLshutdown exit0, two fresh UbuntuStopped observations, all retained clients closed, unchanged4GiB config31b and original unlock. Only its exact local STOP was removed; prior failed receipts and lost-old-terminal qualification persist. Current pidfd e5be and bounded targeted hash500dc source/deltas/125 pure contracts/independent peers/current29 pins are published and reviewed; root independently ran17 new tests. Actual Linux compatibility/cache benefit and newboot toolchain/runtime/interop/storage/DriveFS/UNC gates remain required. No biological result yet.\n')
pp=W/'master_runtime_compat24b_git_plan.json';plan=json.loads(pp.read_bytes());plan['files']+=binary
for row in plan['files']:
 raw=Path(row['local_absolute_path']).read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
assert len({r['target'] for r in plan['files']})==len(plan['files'])
pp.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
