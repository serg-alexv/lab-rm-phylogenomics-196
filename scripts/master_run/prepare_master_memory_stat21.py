"""Publish source-reviewed paired memory owner and exact32 metadata followup."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/'
pins={'repair_canonical_post_ff_stat32.py':'f8b40188ab7ba25b6a44501008eae9472d2141c7ecc24f111618bb7d7941025d',
 'canonical_post_ff_stat32_plan.json':'00718bae82458ae0c238ac276e4fae134799c2f77d9caffd0da1f0ad7af7fb83',
 'stage5_memory_observation_owner.py':'9a49165c6809486d0bdbf6e2a9c297e943b8a738f148a54e1244a491f4d63cfd',
 'stage5_memory_observation.py':'55ab4f7c96589c599bfe2fed25165faea8817cefdbf8d4f8676655d5d12b1161'}
assert all(hashlib.sha256((W/n).read_bytes()).hexdigest()==p for n,p in pins.items())
review={'schema':'MASTER_ROOT_INDEPENDENT_SOURCE_REVIEW_V1','state':'PASS_SOURCE_PREPARATION_ONLY_ACTUAL_ACTIONS_NOT_RUN',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pins':pins,
 'actual_root_verification':'python -B -m unittest test_canonical_post_ff_stat32 test_stage5_memory_observation_owner:12 tests PASS0.015s',
 'memory_checks':['separate bounded nofork Linux observation','original retained byte lock and exact prior04 closure pins',
 'fresh1536MiB physical and commit reserve','actual retained client birth/exit plus full nonce/source-bound output',
 'Windows snapshots before/after','unknown-client stop written before unlock','no config/cache/signal/science action'],
 'metadata_checks':['fixed c76 HEAD/prior actual a147 FF proof','32 exact prior falseM paths joined to265 raw proofs',
 'all indexed modes/OIDs equal HEAD before/after','six dirty raw backups preserved before sole exact32 add',
 'effective no-conversion attribute gate','all raw bytes unchanged and finalstatus exactlysix',
 'reviewed owned Git lifecycle reuses17010 helper','no fetch/FF/reset/restore/clean/refwrite/automatic scope expansion'],
 'limitations':['Source review and12 pure tests are not actual WSL/G integration.',
 'Current interop02 local stop remains preserved; failed Conda pidfd capability occurs before native fixture launch.']}
r=W/'memory_stat21_independent_root_review.json'
with r.open('x',encoding='utf-8') as f:json.dump(review,f,indent=2);f.write('\n')
extras={n:('scripts/master_run/'+n if n.endswith('.py') else B+'git_metadata_postff32/'+n) for n in pins if n!='stage5_memory_observation.py'}
extras.update({'test_canonical_post_ff_stat32.py':'scripts/master_run/test_canonical_post_ff_stat32.py',
 'test_stage5_memory_observation_owner.py':'scripts/master_run/test_stage5_memory_observation_owner.py',
 r.name:B+'preparation/'+r.name,
 'master_runtime_pressure20_git_objects.json':B+'publication/master_runtime_pressure20_git_objects.json',
 'master_runtime_pressure20_remote_readback.json':B+'publication/master_runtime_pressure20_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name})
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','20ec0f73f0bfbf85ca9255862fe942a6c59edc96',
 '--name','master_memory_stat21','--previous-status',str(W/'master_runtime_pressure20/status.json'),
 '--previous-markdown',str(W/'master_runtime_pressure20/STATUS.md'),
 '--phase','Publish independently reviewed paired memory observation owner and exact32 unchanged-object metadata followup; preserve actual prelaunch pidfd interop failure',
 '--spool','stage5_interop_actual_postiq_02']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
O=W/'master_memory_stat21';s=json.loads((O/'status.json').read_bytes())
s['stage5_interop']='FAILED_BEFORE_NATIVE_LAUNCH_CONDA_STDLIB_PIDFD_UNAVAILABLE; local INTEROP_UNPROVEN_STOP preserved pending exact authorized VM shutdown'
s['stage5_resource_pressure']='Paired Windows/Linux observation owner independently source-reviewed; actual observation NOT_RUN. Exact4GB-to3GB proposal preparation pending evidence.'
s['stage5_pidfd_compatibility']='Minimal kernel-backed libc pidfd source remediation in preparation; no PID-only signalling fallback.'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
with (O/'STATUS.md').open('a',encoding='utf-8') as f:
 f.write('\nActual interop02 failed the retained Conda interpreter pidfd capability guard while constructing Supervisor, before any native fixture launch. System Python setup had this capability. The failed terminal and local INTEROP_UNPROVEN_STOP remain preserved; no actual integration pass is claimed. Minimal libc-backed kernel pidfd compatibility is in preparation, preserving handle-based signalling. The paired memory owner and exact32 metadata correction are independently source-reviewed; their actual executions are NOT_RUN.\n')
pp=W/'master_memory_stat21_git_plan.json';plan=json.loads(pp.read_bytes())
for row in plan['files']:
 raw=Path(row['local_absolute_path']).read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
pp.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
