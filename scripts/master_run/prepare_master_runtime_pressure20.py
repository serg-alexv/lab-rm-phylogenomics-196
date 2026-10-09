"""Publish closed actual failures and Git FF evidence, excluding private backups."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/';extras={};binary=[]
g=W/'canonical_git_metadata_repair_20261009T230357Z_7bd50c6d'
assert hashlib.sha256((g/'receipt.json').read_bytes()).hexdigest()=='a147c8121b36897676f59c18cb7ad085dc75841c8e47c376dfa85902e5834ff8'
for p in sorted(g.iterdir()):
 if not p.is_file() or p.name=='original.index.bin':continue
 assert p.name in ('receipt.json','preserve_first.json') or p.name.endswith(('.command.json','.stdout.bin','.stderr.bin'))
 target=B+'git_metadata_repair18/actual01/'+p.name
 if p.suffix=='.bin':binary.append(dict(local_absolute_path=str(p),target=target,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),transport_encoding='base64'))
 else:extras[p.relative_to(W).as_posix()]=target
for name in ('stage5_memory_observation.py','stage5_memory_observation_before_limited_query.py','stage5_memory_observation_before_synchronize.py'):
 p=W/name
 if p.exists():extras[name]='scripts/master_run/'+name
for name in ('stage5_resource_pressure_diagnosis_preparation.json',
 'stage5_windows_memory_observation_20261009T230726Z_bad3973b.json',
 'stage5_windows_memory_observation_20261009T230816Z_5b4fd8ca.json',
 'stage5_windows_memory_observation_20261009T231114Z_1fa6f889.json',
 'stage5_windows_memory_observation_20261009T231301Z_700a25d7.json'):
 assert (W/name).is_file();extras[name]=B+'stage5/resource_observation20/'+name
extras.update({'master_git_repair19_git_objects.json':B+'publication/master_git_repair19_git_objects.json',
 'master_git_repair19_remote_readback.json':B+'publication/master_git_repair19_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name})
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','c76a46163af8b26057a113599f0524dfa0b0e94e',
 '--name','master_runtime_pressure20','--previous-status',str(W/'master_git_repair19/status.json'),
 '--previous-markdown',str(W/'master_git_repair19/STATUS.md'),
 '--phase','Preserve successful canonical FF with32 metadata entries pending and closed runtime04 reserve failure; collect paired guest memory evidence',
 '--spool','stage5_setup_runtime_actual_postiq_03','--spool','stage5_setup_runtime_actual_postiq_04']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
O=W/'master_runtime_pressure20';s=json.loads((O/'status.json').read_bytes())
s['local_checkout_note']='Actual canonical FF to c76a461 succeeded; all265 changed raw blobs and whole index objects/modes match target. Six genuine dirty files unchanged. Overall maintenance receipt FAILED_PRESERVED because32 new byte-identical DriveFS stat entries remain; exact source-only followup pending.'
s['stage5_runtime_discovery']='RUNTIME04_FAILED_RESOURCE_RETAINED_NATIVE_AND_WSL_CLOSED_NO_CANDIDATE; runtime03 rejected mistyped proof subdirectory before launch'
s['stage5_current_stop_sha256']='NO_UNPROVEN_STOP_AFTER_ACTUAL_RUNTIME04_RESOURCE_FAILURE_CLOSURE'
s['stage5_resource_pressure']='Repeated host commit drops during hashing; native RSS alone does not attribute cache/app cause. Windows snapshots published; paired Linux observation pending. Reserves unchanged.'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
with (O/'STATUS.md').open('a',encoding='utf-8') as f:
 f.write('\nCanonical FF to c76a461 exited0; all265 changed raw blobs and entire index objects/modes match the target. Six genuine local changes remain byte-identical. Overall repair remains FAILED_PRESERVED because32 new false-modified DriveFS entries appeared; no automatic scope expansion occurred. Private index and six raw backups remain local and excluded.\n')
 f.write('\nRuntime03 rejected an incorrect toolchain proof subdirectory before native launch; runtime04 used the correct proof and again failed the unchanged Windows commit reserve. Retained native/client closure, STOP removal and original unlock succeeded. No runtime candidate or detector output exists. Paired guest memory evidence is the next resource action; no reserve reduction or cause attribution.\n')
planpath=W/'master_runtime_pressure20_git_plan.json';plan=json.loads(planpath.read_bytes());plan['files']+=binary
for row in plan['files']:
 raw=Path(row['local_absolute_path']).read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
assert len({r['target'] for r in plan['files']})==len(plan['files'])
planpath.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
