"""Publish exact completed WSL repair evidence; no WSL or ref mutations."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
name='master_wslactual46';spool='stage5_wsl_config_e169045dc0634577be5e041d922d44a7'
r=json.loads((W/spool/'result.json').read_bytes())
assert r['state']=='PASS_NONSCIENTIFIC_WSL_CONFIG_CHANGED_AND_ALL_DISTROS_STOPPED'
assert r['owned_closure_proven'] and r['original_lock_explicitly_released'] and not r['unknown_closure_stop_preserved']
review='stage5_wsl_config_actual01_independent_review.json'
peer=json.loads((W/review).read_bytes());assert peer['state'].startswith('PASS_')
patch={'stage5_wsl_reconfiguration':r['state'],'stage5_wsl_config_actual_spool':spool,
       'stage5_wsl_default_uid':0,'stage5_current_stop_sha256':None,
       'stage5_native_execution_current':'NOT_RUN; NEW_LINUX_BOOT_AND_ALL_FRESH_GATES_PENDING',
       'stage5_wsl_config_actual_independent_review_sha256':hashlib.sha256((W/review).read_bytes()).hexdigest()}
extras=[review+'=reports/master_run/20261009/wsl_repair46/'+review,
 'stage5_wsl_config_owner_independent_review01.json=reports/master_run/20261009/wsl_repair46/stage5_wsl_config_owner_independent_review01.json',
 'master_wslprep45_remote_readback.json=reports/master_run/20261009/publication/master_wslprep45_remote_readback.json',
 Path(__file__).name+'=scripts/master_run/'+Path(__file__).name]
paragraph='Stage5 current execution: exact WSL repair and controlled shutdown PASS. The unchanged original workflow-lock retained Linux configuration and Windows maintenance client exits; public backups preserve both configuration versions and the exact failed UNC02 sentinel before its verified removal. Ubuntu now uses init/default root (registered UID0), all18legacy tasks remain Disabled, all distros were verified stopped, no automatic relaunch occurred and no current STOP remains. Independent actual receipt review PASS. All boot-sensitive gates require fresh actual evidence on a new Linux boot before the first approved full-method genome; Stage5 native execution and curation remain NOT_RUN. Accepted Stage4 is unchanged; VM payload splitting, cold restore and final host eviction remain pending.\n'
for suffix,value in [('_patch.json',patch),('_extras.json',extras)]:
    with (W/(name+suffix)).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')
with (W/(name+'_paragraph.md')).open('x',encoding='utf-8') as f:f.write(paragraph)
subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
 '--head','c4a12a2b5bc54aca023d98e1f814b76eb5f5c468','--previous','master_wslprep45',
 '--phase','Apply exact WSL init/root repair, recover failed sentinel, and verify stopped distros',
 '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json','--spool',spool],check=True)
plan=W/(name+'_git_plan.json');value=json.loads(plan.read_bytes())
for row in value['files']:
    raw=Path(row['local_absolute_path']).read_bytes()
    try:raw.decode('utf-8')
    except UnicodeDecodeError:row['transport_encoding']='base64'
plan.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'state':'EXACT_COMPLETED_REPAIR_PLAN_ONLY','files':len(value['files'])}))
