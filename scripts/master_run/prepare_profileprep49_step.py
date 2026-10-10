"""Prepare reviewed exact host-profile source publication; no runtime/ref action."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;name='master_profileprep49'
source=W/'stage5_wsl_host_profile_owner.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='3e6c78c08265157b892a341087780f29dee58c5281d41f0fe49f6ff534248232'
peer='stage5_wsl_host_profile_owner_independent_review01.json'
assert json.loads((W/peer).read_bytes())['state'].startswith('PASS_')
patch={'stage5_wsl_resource_decision':'REVIEWED_EXACT_3GIB_CEILING_DROP_CACHE_SOURCE; ACTUAL_NOT_RUN',
 'stage5_current_stop_sha256':None,'stage5_native_execution_current':'NOT_RUN; HOST_PROFILE_ACTUAL_AND_NEW_BOOT_GATES_PENDING'}
extras=[]
for filename in ['stage5_wsl_host_profile_owner.py','test_stage5_wsl_host_profile_owner.py',
                 'stage5_gdrive_view_postrepair.py','test_stage5_gdrive_view_postrepair.py',Path(__file__).name]:
    extras.append(filename+'=scripts/master_run/'+filename)
for filename in ['stage5_wsl_host_profile_before_repair01.txt','stage5_wsl_host_profile_owner_METHODS.md',
 'stage5_wsl_host_profile_owner_preparation01.json',peer,
 'stage5_gdrive_view_postrepair_METHODS.md','stage5_gdrive_view_postrepair_preparation01.json']:
    extras.append(filename+'=reports/master_run/20261009/profileprep49/'+filename)
extras.append('master_runtimefailure48_remote_readback.json=reports/master_run/20261009/publication/master_runtimefailure48_remote_readback.json')
paragraph='Stage5 current execution: a separately named Windows-only host-profile repair has independent source review PASS. It preserves the exact679B preimage, changes only memory4GB to3GB and autoMemoryReclaimgradual to dropCache, retains current UID0/init configuration, original workflow-lock/lease, exact closed runtime07 failure and bounded retained census/shutdown/stopped-query clients. Actual profile mutation remains NOT_RUN at this source preparation step. Runtime07 remains FAILED with no candidate; native Stage5 and production curation remain NOT_RUN. The toolchain06-pinned G source is preserved as inactive preparation and will require a new-boot pin variant before use. Accepted Stage4 is unchanged; the cold-owner prototype is still inactive pending review corrections, actual writer-exclusion/inventory/capture/restoration and VM splitting.\n'
for suffix,value in [('_patch.json',patch),('_extras.json',extras)]:
    with (W/(name+suffix)).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')
with (W/(name+'_paragraph.md')).open('x',encoding='utf-8') as f:f.write(paragraph)
subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
 '--head','3ae4bc5b2c4828615f518c31b53d1203786e5802','--previous','master_runtimefailure48',
 '--phase','Prepare reviewed 3GiB WSL host profile and preserve inactive G source',
 '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json'],check=True)
