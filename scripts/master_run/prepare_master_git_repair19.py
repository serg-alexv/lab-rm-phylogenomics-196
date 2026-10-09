"""Publish the closed runtime resource failure and exact peer-reviewed Git repair."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/';extras={};binary=[]
mapfile=W/'canonical_git_metadata_repair_publication_files.json'
if hashlib.sha256(mapfile.read_bytes()).hexdigest()!='ec7150252a13507361864ff7d6e415a61bb33a929b1ccd94af56b0fea80abf1b':raise ValueError('Frozen public mapping differs')
for row in json.loads(mapfile.read_bytes())['files']:
 p=Path(row['local']);raw=p.read_bytes()
 if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Frozen Git repair source/proof differs')
 if p.suffix=='.bin':binary.append({'local_absolute_path':str(p),'target':row['target'],'bytes':len(raw),'sha256':row['sha256'],'transport_encoding':'base64'})
 else:extras[p.relative_to(W).as_posix()]=row['target']
extras.update({
 'canonical_git_metadata_repair_publication_files.json':B+'git_metadata_repair18/PUBLICATION_FILES.json',
 'master_toolchain_actual18_git_objects.json':B+'publication/master_toolchain_actual18_git_objects.json',
 'master_toolchain_actual18_remote_readback.json':B+'publication/master_toolchain_actual18_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name,
})
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','4c6e675cfd64c82e889f03c9320e92d8f12214a1',
 '--name','master_git_repair19','--previous-status',str(W/'master_toolchain_actual18/status.json'),
 '--previous-markdown',str(W/'master_toolchain_actual18/STATUS.md'),
 '--phase','Preserve closed runtime02 Windows commit-reserve failure; publish reviewed exact unchanged Git index re-add and fast-forward repair',
 '--spool','stage5_setup_runtime_actual_postiq_02']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
O=W/'master_git_repair19';s=json.loads((O/'status.json').read_bytes())
s['local_checkout_note']='Read-only diagnosis proves122 stale undersized stat entries but raw blobs and all index objects unchanged; six genuine dirty files unchanged. Exact preserve-first re-add/FF source peer-reviewed, actual repair NOT_RUN.'
s['stage5_current_stop_sha256']='NO_UNPROVEN_STOP_AFTER_ACTUAL_RUNTIME02_RESOURCE_FAILURE_CLOSURE'
s['stage5_runtime_discovery']='FAILED_RESOURCE_WINDOWS_COMMIT_1852510208_BELOW_UNCHANGED1879048192_RESERVE_NATIVE60MB_PEAK_RSS_CLOSED_NO_CANDIDATE'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
md=(O/'STATUS.md').read_text(encoding='utf-8')
md+='\nRuntime02 FAILED at Windows commit headroom1,852,510,208B below the unchanged1,879,048,192B setup gate. Actual discovery process peak sampled RSS60,133,376B; it was terminated through retained native scope after lease invalidation. Retained WSL exit2, empty native scope, STOP removal and original unlock are recorded; no runtime candidate or biological result exists. Host/cache causes require fresh evidence. Canonical Git repair is source-reviewed and prepared, not executed.\n'
(O/'STATUS.md').write_text(md,encoding='utf-8')
planpath=W/'master_git_repair19_git_plan.json';plan=json.loads(planpath.read_bytes());plan['files']+=binary
for row in plan['files']:
 raw=Path(row['local_absolute_path']).read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
if len({r['target'] for r in plan['files']})!=len(plan['files']):raise ValueError('Duplicate public target')
planpath.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
