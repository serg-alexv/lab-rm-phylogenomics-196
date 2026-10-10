"""Derived C-only aggregate closure receipt; original native receipts unchanged."""
from pathlib import Path
import datetime, hashlib, json
import review_stage5_postboot_gate as R
WORK=Path(__file__).resolve().parent
SPOOL=WORK/'stage5_interop_actual_postiq_05'
PEER='d1edbd9970f7f2427ce3abae563231e1b0c7e5a8421420ddba35cec8fe18a07a'
STOP=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\stage05_owned_closure_unproven.json')
OUT=WORK/'stage5_interop05_actual_closed_derived_receipt01.json'
peer=R.pinned(WORK/'stage5_interop05_postprofile_independent_review.json',PEER)
R.require(peer['state']=='PASS_COMPLETED_POSTBOOT_GATE_EXACT_SOURCE_CLOSURE_AND_BYTES'
  and peer['kind']=='interop' and peer['detail']['linux_boot_id']=='f0ffcebc-4901-479d-9559-89d45e9cfa38','Completed independent fixture peer differs')
for name,row in peer['checked_files'].items():
    R.require(R.sha(WORK/name)==row['sha256'] and len(R.data(WORK/name))==row['bytes'],'Peer-qualified bytes changed')
value=R.read(SPOOL/'result.json');unlock=R.read(SPOOL/'lock_released.json');held=R.read(SPOOL/'actual_owner_lock.json')
R.lock(held['workflow_lock'])
R.require(value['state']=='PASS_NONSCIENTIFIC_INTEROP_ONLY' and value['scientific_adoption_authorized'] is False
  and unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['released'] is True
  and value['fixtures']==['exit0','lease_expiry','escaped_descendant'],'Original aggregate/unlock differs')
evidence=[]
for item in value['results']:
    path=SPOOL/item['fixture'];R.require(R.read(path/'result.json')==item,'Fixture join differs')
    linux=R.pinned(path/'linux/terminal.json',item['terminal_sha256']);launch=R.read(path/'wsl.launch.json')
    R.require(item['owned_closure_proven'] is True and linux['owned_closure_proven'] is True
      and item['state']=='PASS_NONSCIENTIFIC_INTEROP_FIXTURE' and item['owner_nonce']==linux['owner_nonce']==launch['owner_nonce'],'Actual fixture closure differs')
    R.terminal(launch['actual_client'],item['actual_wsl_client_exit'],value['actual_windows_owner']['creation_filetime'])
    evidence.append({'fixture':item['fixture'],'result_sha256':R.sha(path/'result.json'),
      'linux_terminal_sha256':item['terminal_sha256'],'wsl_launch_sha256':R.sha(path/'wsl.launch.json'),
      'actual_retained_wsl_exit_in_original_fixture_result':item['actual_wsl_client_exit'],
      'native_closure_sha256':R.sha(path/'linux/attempt/synthetic.closure.json'),
      'native_command_sha256':R.sha(path/'linux/attempt/synthetic.command.json')})
R.require(len(evidence)==3,'Exact three fixture closure records required')
# Check only the explicitly named current STOP and its plain ancestry. Do not
# acquire a lock, signal any process, or read any runtime/native payload.
for parent in STOP.parents:
    info=parent.lstat();R.require(not parent.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400,'Aliased STOP ancestry')
try:STOP.lstat()
except FileNotFoundError:pass
else:raise ValueError('Current owned-closure STOP exists; derived noSTOP receipt refused')
observed=datetime.datetime.now(datetime.timezone.utc).isoformat()
report={'schema':'STAGE05_ACTUAL_INTEROP_AGGREGATE_DERIVED_CLOSURE_V1',
 'state':'PASS_NONSCIENTIFIC_INTEROP_CLOSED_DERIVED_RECEIPT',
 'scope':'DERIVED_READONLY_AGGREGATE_OF_ORIGINAL_ACTUAL_INTEROP05_CLOSURE_NOT_NEW_NATIVE_EVIDENCE',
 'utc':observed,'source_sha256':R.sha(Path(__file__)),
 'owned_closure_proven':True,'original_lock_explicitly_released':True,
 'unknown_closure_stop_preserved':False,'scientific_adoption_authorized':False,
 'actual_windows_owner':value['actual_windows_owner'],'workflow_lock':held['workflow_lock'],
 'outer_result_path':str(SPOOL/'result.json'),'outer_result_sha256':R.sha(SPOOL/'result.json'),
 'original_unlock_path':str(SPOOL/'lock_released.json'),'original_unlock_sha256':R.sha(SPOOL/'lock_released.json'),
 'original_actual_owner_lock_sha256':R.sha(SPOOL/'actual_owner_lock.json'),
 'independent_peer_path':str(WORK/'stage5_interop05_postprofile_independent_review.json'),
 'independent_peer_sha256':PEER,'peer_byte_pins_reverified':len(peer['checked_files']),
 'linux_boot_id':peer['detail']['linux_boot_id'],'fixtures':evidence,
 'current_STOP_check':{'path':str(STOP),'observed_utc':observed,'plain_ancestry_checked':True,
   'lstat_result':'FILE_NOT_FOUND','read_only':True},
 'retained_wsl_evidence_location':'Actual exit is embedded in each original fixture result.json and joined to its wsl.launch.json. No standalone wsl_exit.json is fabricated.',
 'closure_limit':'Exact owned fixture native groups/descendants and retained WSL clients plus explicit original unlock; current STOP absence is a timestamped observation, not future admission.',
 'original_artifacts_modified':False,'actual_execution_or_adoption':'NONE_READONLY_DERIVATION_ONLY'}
R.require(not OUT.exists(),'Preserve prior derived proof')
with OUT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
print(json.dumps({'state':report['state'],'output':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()}))
