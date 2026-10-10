"""C-only actual second-attempt natural defer, preparation and scope closure review."""
from pathlib import Path
import argparse, ast, datetime, hashlib, json
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
SPOOL=W/'stage5_owner_GCF_000009425_1_backing_capacity_02'
NONCE='b54ed1b7012047edb0dcd4b68dc2d10c'
BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
PINS={
 'stage5_windows_backing_owner.py':'296492aa4205f64058846b9901a7bb3a3458f99eda1c7ff388a6e33cdc38b834',
 'stage5_actual_backing_capacity_02.json':'4c2d9812afd2dbabaa6ba3177395dee17511946966fb3b7491f579cfd3602d63',
 'stage5_atomic.py':'500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04',
 'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
 'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
 'stage5_owner_lease.py':'add2cbf12ee6d51bb10168b629a8befd2136f58e5194a6e7195fea25002620b8',
 'copy_stage5_capacity02_closed_evidence.py':'326156db364d49d8216678144d1cc1f2e939a0e9e89801fadfe5aa2a699ee2a5',
 'stage5_first_backing_capacity02_actual_config_independent_review01.json':'64313758aa815bd383271ea34840894a0caf0cec7154a4eed1b9de395380b3cd'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--copy',type=Path,required=True)
 p.add_argument('--snapshot-receipt',type=Path,required=True);p.add_argument('--copier-source',type=Path,required=True)
 p.add_argument('--copier-sha256',required=True);a=p.parse_args()
 out=W/'stage5_first_capacity02_closed_independent_review.json'
 R.require(not out.exists(),'Preserve exact independent capacity02 closure review')
 report={'schema':'STAGE05_FIRST_CAPACITY02_CLOSED_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_CLOSURE_JOINS',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
  'method':'C-only copied actual native bytes, unchanged source ordering, retained Windows client birth/exit, original inactive lease and explicit unlock. No WSL/UNC/G/native/API/process/lock/network/Git effects.',
  'scientific_adoption':False,'cancellation_success_claim':False}
 try:
  for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Current source/config/peer differs: '+name)
  R.require(a.copier_source==W/'copy_stage5_capacity02_closed_evidence.py'
   and R.sha(a.copier_source)==a.copier_sha256==PINS['copy_stage5_capacity02_closed_evidence.py'],'Explicit fixed root copier source differs')
  original=R.read(SPOOL/'owner.json');launch=R.read(SPOOL/'GCF_000009425.1.launch.json')
  result=R.read(SPOOL/'result.json');end=R.read(SPOOL/'GCF_000009425.1.exit.json')
  progress=R.read(SPOOL/'progress.json');lease=R.read(SPOOL/'owner_lease.json');unlock=R.read(SPOOL/'lock_released.json')
  R.require(result['state']==end['state']=='DEFERRED_RESOURCE' and result['scope']=='ONE_APPROVED_GENOME'
   and result['selected_accessions']==['GCF_000009425.1'] and type(result['approved_genomes']) is int and result['approved_genomes']==196
   and result['full_panel_complete'] is False and result['genome_results']==[end] and not result.get('error') and not result.get('finalizer_errors')
   and progress['latest']==end and progress['genome_results']==[end]
   and all(type(progress[k]) is int and progress[k]==1 for k in ('finished','total')),'Actual normal deferred owner result differs')
  owner=result['owner'];R.require(owner==original['owner'] and type(owner['pid']) is int and owner['pid']==25208
   and type(owner['creation_filetime']) is int and owner['creation_filetime']==134360788348328513 and owner['executable']==R.PYTHON,'Exact original Windows owner birth differs')
  for key,name in [('config_sha256','stage5_actual_backing_capacity_02.json'),('linux_script_sha256','stage5_atomic.py'),
   ('linux_supervisor_sha256','stage5_atomic_process.py'),('storage_helper_sha256','stage5_work_storage.py'),('lease_helper_sha256','stage5_owner_lease.py')]:
   R.require(result[key]==original[key]==PINS[name],'Actual frozen owner binding differs: '+key)
  R.lock(original['workflow_lock']);R.lock(lease['workflow_lock'])
  R.require(launch['owner_nonce']==lease['nonce']==NONCE and type(lease['owner_pid']) is int and lease['owner_pid']==25208
   and lease['owner_creation_filetime']=='134360788348328513' and lease['workflow_lock_held'] is False
   and lease['expires_unix']==lease['measured_unix'],'Original lease not explicitly inactive')
  R.terminal(launch['native_wsl_client'],end['actual_wsl_client_exit'],134360662075000000,code=75)
  R.require(type(end['actual_wsl_client_exit']['pid']) is int and end['actual_wsl_client_exit']['pid']==10272
   and type(end['actual_wsl_client_exit']['creation_filetime']) is int and end['actual_wsl_client_exit']['creation_filetime']==134360788351071808
   and 1800<=end['elapsed_seconds']<2200,'Exact retained deferred WSL identity/time differs')
  config=R.read(W/'stage5_actual_backing_capacity_02.json');prefix='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/'
  expected=[R.WSL,'-d','Ubuntu','-u','root','--exec',config['runtime']['environment_dir']+'/bin/python','-B',prefix+'stage5_atomic.py',
   '--config',prefix+'stage5_actual_backing_capacity_02.json','run','--accession','GCF_000009425.1',
   '--owner-lease',prefix+SPOOL.name+'/owner_lease.json','--owner-nonce',NONCE]
  R.require(launch['argv']==expected and type(launch['index']) is int and launch['index']==1,'Exact original runner argv differs')
  for suffix in ('stdout','stderr'):R.require(R.sha(SPOOL/('GCF_000009425.1.'+suffix+'.txt'))==end[suffix+'_sha256'],'Exact closed stream differs')
  R.require(R.data(SPOOL/'GCF_000009425.1.stderr.txt')==b'','Unexpected closed runner stderr')
  terminal_path=a.copy/'status.json';status=R.pinned(terminal_path,end['status_sha256'])
  R.require(status==R.read(SPOOL/'GCF_000009425.1.stdout.txt') and status['state']=='DEFERRED_RESOURCE'
   and status['accession']=='GCF_000009425.1' and status['owner_nonce']==NONCE and status['transaction']=='transactions/attempt_0002'
   and status['owned_closure_proven'] is True and status['no_native_launch_in_this_invocation'] is True
   and isinstance(status['scientific_identity'],dict) and status['outputs_preserved'] is True and status['curation']=='NOT_RUN'
   and status['biological_absence_claim']=='NONE' and status['error']=='Deferred: Bounded resource admission expired; no native child launched',
   'Prepared but no-native deferred actual terminal differs')
  R.require(unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['utc']>result['utc']>=lease['utc'],'Original explicit unlock/result/inactive lease ordering differs')
  snapshot=R.read(a.snapshot_receipt)
  R.require(snapshot['state']=='PASS_EXACT_C_COPY_CLOSED_CAPACITY02_WITH_PREPARED_BACKING_HASH_INVENTORY'
   and snapshot['source_sha256']==a.copier_sha256 and snapshot['owner_result_sha256']==R.sha(SPOOL/'result.json')
   and snapshot['native_launch_intents_observed']==0,'Exact native copy producer/owner binding differs')
  members=snapshot['members'];files=snapshot['files']
  R.require(isinstance(members,list) and len(members)==len(set(members)) and isinstance(files,dict) and 1<=len(files)<=100,'Bounded exact native member/file maps required')
  inventory=snapshot['backing_inventory'];R.require(isinstance(inventory,list) and 1<=len(inventory)<=10000,'Bounded backing inventory required')
  by_member={row['member']:row for row in inventory};R.require(len(by_member)==len(inventory),'Duplicate backing inventory member')
  R.require({Path(row['member']).parts[0] for row in inventory}=={'.native_runner.guard','GCF_000009425.1'}
   and members==[row['member'].split('/',1)[1] for row in inventory if row['member'].startswith('GCF_000009425.1/')],
   'Complete known-accession backing/genome membership join differs')
  for row in inventory:
   rel=Path(row['member']);R.require(not rel.is_absolute() and not rel.drive and all(p not in ('.','..') and ':' not in p for p in rel.parts),'Backing inventory member escapes')
   R.require(row['kind'] in ('file','directory') and row['metadata_scope']=='WINDOWS_UNC_PROJECTION_NOT_INDEPENDENT_PRIOR_LINUX_POSIX_ATTESTATION'
    and all(type(row[k]) is int for k in ('windows_unc_mode_projection','windows_unc_uid_projection','windows_unc_gid_projection','windows_unc_inode_projection','windows_unc_nlink_projection')),
    'Backing inventory projected metadata scope/type differs')
   if row['kind']=='file':R.require(type(row['bytes']) is int and 0<=row['bytes']<32*1024**2 and len(row['sha256'])==64,'Bounded backing file hash/size required')
  R.require(not any(name.endswith(('.launch_intent.json','.launch.json','.closure.json','.command.json')) for name in members)
   and not any(name in members for name in ('complete.json','inventory','raw_validation')),'Observed native launch/inventory/completion in deferred scope')
  for name,item in files.items():
   rel=Path(name);R.require(not rel.is_absolute() and not rel.drive and all(part not in ('.','..') and ':' not in part for part in rel.parts),'Copied file escapes C-work')
   raw=R.data(a.copy/rel);R.require(type(item['bytes']) is int and len(raw)==item['bytes'] and R.sha(a.copy/rel)==item['sha256'],'Copied native bytes differ')
   frozen=by_member['GCF_000009425.1/'+rel.as_posix()]
   R.require(frozen['kind']=='file' and frozen['bytes']==item['bytes'] and frozen['sha256']==item['sha256'],'Copied native file/full backing inventory differs')
  R.require(R.sha(a.copy/'transactions/attempt_0002/status.json')==end['status_sha256'],'Transaction/accession terminal bytes differ')
  identity=R.pinned(a.copy/'scientific_identity.json','bb9b7b355a55758a9085ca014eff4fbdb14a93ff5e795773b89a0e5d9ee8ee74')
  R.require(identity==status['scientific_identity'] and identity['runner_sha256']==PINS['stage5_atomic.py']
   and identity['runtime_manifest_sha256']=='f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1',
   'Prepared scientific identity differs')
  transaction=a.copy/'transactions/attempt_0002';initial=R.read(transaction/'initial_owner_lease.json');R.lock(initial['workflow_lock'])
  R.require(initial['nonce']==NONCE and initial['owner_pid']==25208 and initial['workflow_lock_held'] is True,'Initial active original lease differs')
  storage=R.read(transaction/'work_storage_proof.json');selected=R.read(W/'stage5_storage_actual_postiq_06.json')
  R.require(storage['boot_id']==BOOT and storage==dict(selected,proof_path=config['work_storage']['proof_path'],proof_sha256=config['work_storage']['proof_sha256']),'Copied storage/current boot differs')
  initial_admission=R.read(transaction/'latest_admission.json')
  R.require(initial_admission['admitted'] is True and initial_admission['policy']==config['resource_policy'],'Actual initial admission/preparation differs')
  presearch=a.copy/'execution/assemblies/GCF_000009425.1/padloc/hmm_attempt_0001/latest_admission.json'
  admission=R.read(presearch);policy=config['resource_policy']
  live_lease=admission['windows_owner_lease']
  failures=[name for name,failed in (
   ('LINUX_AVAILABLE',admission['linux_available_bytes']<policy['linux_job_requirement_bytes']+policy['linux_reserve_bytes']),
   ('WINDOWS_PHYSICAL',live_lease['windows_available_bytes']<policy['windows_reserve_bytes']+policy['incremental_windows_requirement_bytes']),
   ('WINDOWS_COMMIT',live_lease['windows_commit_headroom_bytes']<policy['commit_requirement_bytes']),
   ('LINUX_DISK',admission['disk_free_bytes']<policy['minimum_disk_free_bytes']),
   ('WINDOWS_DISK',admission['windows_disks_sufficient'] is False)) if failed]
  R.require(admission['admitted'] is False and admission['policy']==policy and 1800<=admission['wait_seconds']<1860
   and failures and live_lease['nonce']==NONCE,'Actual presearch bounded capacity defer differs')
  freeze=R.read(a.copy/'execution/execution_freeze.json')
  R.require(freeze['scientific_identity']==identity and len(freeze['padloc_profiles'])==5027 and freeze['threads']==2,'Full method prepared freeze differs')
  tree=ast.parse(R.data(W/'stage5_atomic_process.py'));cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Supervisor')
  execute=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='execute');body=ast.unparse(execute)
  R.require(body.index('self.admission(attempt)')<body.index('configuration_binding =')<body.index('subprocess.Popen(')
   and body.index('self.admission(attempt)')<body.index('self.native_launch_count += 1'),'Unchanged admission/native counter ordering differs')
  stop=Path(original['workflow_lock']['path']).with_name('stage05_owned_closure_unproven.json');R.require(not stop.exists(),'Current STOP exists; preserve and reconcile')
  report.update(state='PASS_CAPACITY02_NATURAL_ADMISSION_DEFER_NO_NATIVE_SCOPE_CLOSED_AND_ORIGINAL_UNLOCK',
   actual_state='DEFERRED_RESOURCE',actual_boot_id=BOOT,actual_result_sha256=R.sha(SPOOL/'result.json'),
   actual_unlock_sha256=R.sha(SPOOL/'lock_released.json'),actual_native_terminal_sha256=end['status_sha256'],
   terminal_copy_path=str(terminal_path),native_launch_count=0,no_native_launch_in_this_invocation=True,
   owned_closure_proven=True,original_lock_explicitly_released=True,retained_WSL_client=end['actual_wsl_client_exit'],
   original_owner_birth={'pid':25208,'creation_filetime':134360788348328513},prepared_scientific_identity_preserved=True,
   scientific_identity_sha256=R.sha(a.copy/'scientific_identity.json'),full_5027_profile_preparation_preserved=True,
   initial_admission_passed=True,first_PADLOC_presearch_admission_expired=True,last_actual_failed_resource_predicates=failures,point_in_time_C_STOP_absent=True,
   exact_copied_members=members,producer_copy_receipt_sha256=R.sha(a.snapshot_receipt),snapshot_receipt_path=str(a.snapshot_receipt),
   snapshot_receipt_sha256=R.sha(a.snapshot_receipt),supplemental_C_evidence={'producer_copy_receipt':{'sha256':R.sha(a.snapshot_receipt),'receipt':snapshot}},
   original_owner_process_exit='Separate retained controller observation required; this receipt does not infer owner self-exit.',
   next_action='Preserve prepared scientific identity/bundle/execution and deferred history. Separate published fallback still requires root original lock, exact closure peer SHA, former owner/client absence and fresh resources. All boot-sensitive gates must repeat after restart.')
 except BaseException as error:report['error']={'kind':type(error).__name__,'message':str(error)}
 report['checked_files']=R.CHECKED
 with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({'state':report['state'],'error':report.get('error'),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
 return 0 if report['state'].startswith('PASS_') else 1
if __name__=='__main__':raise SystemExit(main())
