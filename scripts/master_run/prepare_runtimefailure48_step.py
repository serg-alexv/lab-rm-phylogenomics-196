"""Preserve a closed resource refusal and inactive prepared sources in Git."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;name='master_runtimefailure48';spool='stage5_setup_runtime_actual_postiq_07'
r=json.loads((W/spool/'result.json').read_bytes())
assert r['state']=='FAILED' and r['failed_scope_closed'] and r['owned_closure_proven'] and not r['unknown_closure_stop_preserved']
assert r['error']['message']=='Actual setup resource reserve insufficient'
assert not (W/'stage5_runtime_actual_postiq_07.json').exists()
review='stage5_runtime07_failed_scope_independent_review01.json';peer=json.loads((W/review).read_bytes())
assert peer['state'].startswith('PASS_')
patch={'stage5_runtime_current':'FAILED_RESOURCE_REFUSAL_CURRENT_BOOT; NO_CANDIDATE; '+spool,
 'stage5_current_stop_sha256':None,'stage5_native_execution_current':'NOT_RUN; HOST_PROFILE_REPAIR_AND_FRESH_GATES_PENDING',
 'stage5_wsl_resource_decision':'PREPARE_EXACT_3GIB_CEILING_AND_DROP_CACHE; ACTUAL_NOT_RUN',
 'stage5_runtime07_independent_failed_scope_review_sha256':hashlib.sha256((W/review).read_bytes()).hexdigest()}
extras=[review+'=reports/master_run/20261009/runtimefailure48/'+review,
 'master_toolchain47_remote_readback.json=reports/master_run/20261009/publication/master_toolchain47_remote_readback.json',
 Path(__file__).name+'=scripts/master_run/'+Path(__file__).name]
packet=W/'stage05_cold_owner_source_preparation01/PUBLIC_MAPPING.json'
assert hashlib.sha256(packet.read_bytes()).hexdigest()=='9d378b458da0ef015990e17792c85bb5d7ee677dfd652d2aa4f2e396f6bcfbb8'
for row in json.loads(packet.read_bytes())['files']:
    q=Path(row.get('local_path',row.get('path'))).resolve();assert q.is_relative_to(W) and not q.is_symlink()
    assert q.stat().st_size==row['bytes'] and hashlib.sha256(q.read_bytes()).hexdigest()==row['sha256']
    target=row.get('repository_path',row.get('suggested_repository_path'))
    assert isinstance(target,str)
    extras.append(q.relative_to(W).as_posix()+'='+target)
extras.append(packet.relative_to(W).as_posix()+'=reports/master_run/20261009/runtimefailure48/COLD_OWNER_PUBLIC_MAPPING.json')
paragraph='Stage5 current execution: fresh runtime07 discovery FAILED on the Windows physical-memory reserve while hashing unchanged installed runtime content; no runtime candidate or detector result was produced. Actual retained WSL exit2, Linux supervised root -15, empty tracked descendants/direct children, original unlock and absence of current STOP are independently verified. The original failure remains FAILED. A separate exact Windows WSL host-profile repair is being prepared: memory ceiling4GB to3GB and gradual cache reclamation to dropCache, with other profile bytes retained; actual profile change remains NOT_RUN. Existing scientific guards and accepted Stage4 are unchanged. Previously prepared first-request v2 and G06 sources are inactive because new gates must follow the resource repair. Cold-owner paired source is preserved as preparation pending independent review and actual writer-exclusion/inventory/capture/restoration; VM splitting and local eviction remain NOT_RUN.\n'
for suffix,value in [('_patch.json',patch),('_extras.json',extras)]:
    with (W/(name+suffix)).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')
with (W/(name+'_paragraph.md')).open('x',encoding='utf-8') as f:f.write(paragraph)
subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
 '--head','823386fe0195519e9d416efd832b0d7609fb4e4d','--previous','master_toolchain47',
 '--phase','Preserve closed runtime memory refusal and inactive cold owner preparation',
 '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json','--spool',spool],check=True)
