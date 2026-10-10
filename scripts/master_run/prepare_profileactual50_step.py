"""Prepare completed profile checkpoint and reviewed future request source."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;name='master_profileactual50';spool='stage5_wsl_host_profile_1291e744938e4a1c8916857f199670b7'
r=json.loads((W/spool/'result.json').read_bytes())
assert r['state']=='PASS_NONSCIENTIFIC_WINDOWS_HOST_PROFILE_CHANGED_AND_ALL_DISTROS_STOPPED'
assert r['owned_closure_proven'] and r['original_lock_explicitly_released'] and not r['unknown_closure_stop_preserved']
peer='stage5_wsl_host_profile_actual01_independent_review.json'
assert json.loads((W/peer).read_bytes())['state'].startswith('PASS_')
v3='prepare_stage5_first_actual_request_v3_independent_review01.json'
assert json.loads((W/v3).read_bytes())['state'].startswith('PASS_')
patch={'stage5_wsl_resource_decision':r['state'],'stage5_wsl_host_profile_actual_spool':spool,
 'stage5_wsl_host_profile_sha256':r['actual_after_sha256'],'stage5_current_stop_sha256':None,
 'stage5_wsl_memory_ceiling_bytes':3221225472,'stage5_wsl_auto_memory_reclaim':'dropCache',
 'stage5_native_execution_current':'NOT_RUN; NEW_TOOLCHAIN07_RUNTIME08_INTEROP05_STORAGE06_DRIVEFS04_UNC03_REQUIRED',
 'stage5_wsl_host_profile_independent_actual_review_sha256':hashlib.sha256((W/peer).read_bytes()).hexdigest()}
extras=[peer+'=reports/master_run/20261009/profileactual50/'+peer,
 'master_profileprep49_remote_readback.json=reports/master_run/20261009/publication/master_profileprep49_remote_readback.json',
 Path(__file__).name+'=scripts/master_run/'+Path(__file__).name]
for filename in ['prepare_stage5_first_actual_request_v3.py','test_prepare_stage5_first_actual_request_v3.py',
                 'review_prepare_stage5_first_actual_request_v3.py']:
    extras.append(filename+'=scripts/master_run/'+filename)
for filename in ['prepare_stage5_first_actual_request_v3_METHODS.md',
                 'prepare_stage5_first_actual_request_v3_preparation01.json',v3]:
    extras.append(filename+'=reports/master_run/20261009/profileactual50/'+filename)
paragraph='Stage5 current execution: exact Windows host-profile repair and controlled WSL shutdown PASS with independent actual C-receipt review. The679B original and681B expected/actual public backups are retained; only memory4GB to3GB and autoMemoryReclaimgradual to dropCache changed. Five retained clients exited0, all18legacy tasks remainDisabled, Ubuntu UID0 is unchanged, all distros were verified stopped, no automatic relaunch occurred and the original lock is released with no current STOP. Runtime07 remains a preserved closed resource failure, with no candidate. Reviewed first-requestv3 requires fresh toolchain07/runtime08/interop05/storage06/DriveFS04/UNC03 and preserves all five native budgets. No detector or production curation has run. Accepted Stage4 is unchanged; cold-owner/image capture, splitting, remote recovery and local eviction remain pending.\n'
for suffix,value in [('_patch.json',patch),('_extras.json',extras)]:
    with (W/(name+suffix)).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')
with (W/(name+'_paragraph.md')).open('x',encoding='utf-8') as f:f.write(paragraph)
subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
 '--head','ad990668ed9a564f1f05bd014ab9d5fd89ae7eff','--previous','master_profileprep49',
 '--phase','Verify exact 3GiB host profile, controlled shutdown, and first genome request source',
 '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json','--spool',spool],check=True)
