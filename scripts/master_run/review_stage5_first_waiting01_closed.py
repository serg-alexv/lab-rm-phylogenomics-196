"""C-only exact first01 admission-defer terminal, client and original unlock joins."""
from pathlib import Path
import argparse, ast, datetime, hashlib, json
import review_stage5_postboot_gate as R

W=Path(__file__).resolve().parent
SPOOL=W/'stage5_owner_GCF_000009425_1_backing_01'
NONCE='1439a454dde8448f8f9606b6de6ac702'
BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
PINS={
 'stage5_windows_backing_owner.py':'296492aa4205f64058846b9901a7bb3a3458f99eda1c7ff388a6e33cdc38b834',
 'stage5_actual_backing_01.json':'30a86eb18cddc69eb0cfbdd3ae93473ec54812cd5a859ededd25af01fb737dfa',
 'stage5_atomic.py':'500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04',
 'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
 'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
 'stage5_owner_lease.py':'add2cbf12ee6d51bb10168b629a8befd2136f58e5194a6e7195fea25002620b8',
 'stage5_first_backing_actual_config02_independent_review.json':'dfdcf5efc4444123f5e3829e3bbe7841c4d74e2c4f23af39c7679ac9190f7abc'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status-copy',type=Path,required=True)
    parser.add_argument('--admission-copy',type=Path)
    parser.add_argument('--storage-copy',type=Path)
    parser.add_argument('--snapshot-receipt',type=Path)
    args=parser.parse_args()
    out=W/'stage5_first_waiting01_closed_independent_review.json'
    R.require(not out.exists(),'Preserve independent waiting01 audit')
    value={'schema':'STAGE05_FIRST_WAITING01_CLOSED_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_CLOSURE_JOINS',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
      'method':'C-only frozen source, copied native terminal, retained WSL birth/exit, closed stdout/stderr, inactive lease, original explicit unlock and publication bytes. No producer imports, UNC/G/WSL/API/process/lock/network/Git effects.',
      'scientific_native_execution':'NOT_RUN','scientific_adoption':False,'cancellation_success_claim':False}
    try:
        for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Frozen first01 source/config/peer differs: '+name)
        original=R.read(SPOOL/'owner.json');launch=R.read(SPOOL/'GCF_000009425.1.launch.json')
        result=R.read(SPOOL/'result.json');end=R.read(SPOOL/'GCF_000009425.1.exit.json')
        progress=R.read(SPOOL/'progress.json');lease=R.read(SPOOL/'owner_lease.json');unlock=R.read(SPOOL/'lock_released.json')
        R.require(result['state']==end['state']=='DEFERRED_RESOURCE' and result['scope']=='ONE_APPROVED_GENOME'
          and result['selected_accessions']==['GCF_000009425.1'] and result['approved_genomes']==196
          and result['full_panel_complete'] is False and result['genome_results']==[end]
          and progress['latest']==end and progress['genome_results']==[end] and progress['finished']==progress['total']==1
          and not result.get('error') and not result.get('finalizer_errors'),'Actual first01 deferred scope/finalizer differs')
        R.require(result['owner']==original['owner'] and result['owner']['pid']==24488
          and result['owner']['creation_filetime']==134360766940521715 and result['owner']['executable']==R.PYTHON,'Original Windows owner birth differs')
        for key,name in [('config_sha256','stage5_actual_backing_01.json'),('linux_script_sha256','stage5_atomic.py'),
           ('linux_supervisor_sha256','stage5_atomic_process.py'),('storage_helper_sha256','stage5_work_storage.py'),('lease_helper_sha256','stage5_owner_lease.py')]:
            R.require(result[key]==original[key]==PINS[name],'Actual first01 frozen binding differs: '+key)
        R.lock(original['workflow_lock']);R.lock(lease['workflow_lock'])
        R.require(launch['owner_nonce']==lease['nonce']==NONCE and lease['owner_pid']==24488
          and lease['owner_creation_filetime']=='134360766940521715' and lease['workflow_lock_held'] is False
          and lease['expires_unix']==lease['measured_unix'],'Original lease not explicitly invalidated')
        R.terminal(launch['native_wsl_client'],end['actual_wsl_client_exit'],134360662075000000,code=75)
        R.require(end['actual_wsl_client_exit']['pid']==7468 and end['actual_wsl_client_exit']['creation_filetime']==134360766943374620
          and end['actual_wsl_client_exit']['exit_filetime']==134360784948613669 and 1800<=end['elapsed_seconds']<1860,'Exact retained deferred WSL/time differs')
        config=R.read(W/'stage5_actual_backing_01.json')
        expected=[R.WSL,'-d','Ubuntu','-u','root','--exec',config['runtime']['environment_dir']+'/bin/python','-B',
          '/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_atomic.py','--config',
          '/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_actual_backing_01.json','run','--accession','GCF_000009425.1',
          '--owner-lease','/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/'+SPOOL.name+'/owner_lease.json','--owner-nonce',NONCE]
        R.require(launch['argv']==expected and launch['index']==1,'Original science WSL argv differs')
        R.require(R.sha(SPOOL/'GCF_000009425.1.stdout.txt')==end['stdout_sha256'] and R.sha(SPOOL/'GCF_000009425.1.stderr.txt')==end['stderr_sha256']
          and len(R.data(SPOOL/'GCF_000009425.1.stderr.txt'))==0,'Exact retained closed streams differ')
        status=R.pinned(args.status_copy,end['status_sha256'])
        R.require(status==R.read(SPOOL/'GCF_000009425.1.stdout.txt') and status['state']=='DEFERRED_RESOURCE'
          and status['accession']=='GCF_000009425.1' and status['owner_nonce']==NONCE
          and status['transaction']=='transactions/attempt_0001' and status['owned_closure_proven'] is True
          and status['no_native_launch_in_this_invocation'] is True and status['scientific_identity'] is None
          and status['error']=='Deferred: Bounded resource admission expired; no native child launched'
          and status['outputs_preserved'] is True and status['curation']=='NOT_RUN' and status['biological_absence_claim']=='NONE','Exact native no-launch deferred terminal differs')
        R.require(unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['utc']>result['utc']
          and result['utc']>=lease['utc'],'Original explicit unlock/result/inactive-lease ordering differs')
        source=R.data(W/'stage5_atomic.py').decode();tree=ast.parse(source)
        run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_genome')
        body=ast.unparse(run)
        R.require(body.index('prior_closure_checked = True')<body.index('supervisor.admission(transaction)')<body.index('validate_genome_inputs(config, root, accession)')
          <body.index('validate_runtime(config)')<body.index('stable_identity = genome_scientific_identity')<body.index('native.run_padloc'), 'Initial admission/source/native ordering differs')
        supplements={}
        if args.admission_copy:
            admission=R.read(args.admission_copy)
            R.require(admission['admitted'] is False and admission['policy']==config['resource_policy']
              and admission['linux_available_bytes']<config['resource_policy']['linux_job_requirement_bytes']+config['resource_policy']['linux_reserve_bytes']
              and 1800<=admission['wait_seconds']<1860 and admission['windows_disks_sufficient'] is True
              and admission['windows_owner_lease']['nonce']==NONCE,'Copied actual initial admission is not failed Linux capacity')
            supplements['admission']={'sha256':R.sha(args.admission_copy),'receipt':admission}
        if args.storage_copy:
            storage=R.read(args.storage_copy)
            selected=R.read(W/'stage5_storage_actual_postiq_06.json')
            R.require(storage['boot_id']==BOOT and storage==dict(selected,proof_path=config['work_storage']['proof_path'],proof_sha256=config['work_storage']['proof_sha256']),'Copied transaction storage/current boot differs')
            supplements['storage_sha256']=R.sha(args.storage_copy)
        if args.snapshot_receipt:
            snapshot=R.read(args.snapshot_receipt)
            R.require(snapshot['state']=='PASS_EXACT_C_COPY_OF_CLOSED_INITIAL_RESOURCE_WAIT'
              and snapshot['source_sha256']==R.sha(W/'copy_stage5_waiting01_closed_evidence.py')
              and snapshot['owner_result_sha256']==R.sha(SPOOL/'result.json')
              and snapshot['no_execution_or_inventory_paths_observed'] is True
              and snapshot['members']==['.guard','status.json','transactions','transactions/attempt_0001',
              'transactions/attempt_0001/initial_owner_lease.json','transactions/attempt_0001/latest_admission.json',
              'transactions/attempt_0001/status.json','transactions/attempt_0001/work_storage_proof.json'],'Exact closed transaction member/copy binding differs')
            for relative,entry in snapshot['files'].items():
                copied=args.snapshot_receipt.parent/relative
                R.require(len(R.data(copied))==entry['bytes'] and R.sha(copied)==entry['sha256'],'Copied exact file bytes differ')
            R.require(R.sha(args.snapshot_receipt.parent/'transactions/attempt_0001/status.json')==end['status_sha256'],'Transaction and accession terminal bytes differ')
            initial=R.read(args.snapshot_receipt.parent/'transactions/attempt_0001/initial_owner_lease.json')
            R.lock(initial['workflow_lock']);R.require(initial['nonce']==NONCE and initial['owner_pid']==24488 and initial['workflow_lock_held'] is True,'Copied initial original lease differs')
            supplements['producer_copy_receipt']={'sha256':R.sha(args.snapshot_receipt),'receipt':snapshot}
        pub=R.read(W/'master_firstconfig62_remote_readback.json')
        R.require(pub['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and pub['expected_commit']=='8458cfca75b0d43404e2fd7e87237c228e0029b0'
          and pub['required_files']==pub['verified_files']==len(pub['files'])==13 and all(x['actual_remote_bytes_read'] and x['sha256_verified'] and x['byte_count_verified'] for x in pub['files']), 'First01 config publication62 differs')
        stop=Path(original['workflow_lock']['path']).with_name('stage05_owned_closure_unproven.json')
        R.require(not stop.exists(),'Current owned-closure STOP exists; preserve and reconcile')
        value.update(state='PASS_FIRST01_NATURAL_ADMISSION_DEFER_NO_NATIVE_SCOPE_CLOSED_AND_ORIGINAL_UNLOCK',actual_result_sha256=R.sha(SPOOL/'result.json'),
          actual_native_terminal_sha256=end['status_sha256'],actual_unlock_sha256=R.sha(SPOOL/'lock_released.json'),
          actual_state='DEFERRED_RESOURCE',no_native_launch_in_this_invocation=True,owned_closure_proven=True,original_lock_explicitly_released=True,
          initial_admission_precedes_runtime_validation_bundle_and_every_native_launch=True,retained_WSL_client=end['actual_wsl_client_exit'],
          original_owner_birth={'pid':24488,'creation_filetime':134360766940521715},original_owner_process_exit='Separate controller observation required; this owner result retains its initial birth record and does not assert its own exit.',
          source_PINS=PINS,point_in_time_C_STOP_absent=True,supplemental_C_evidence=supplements,
          next_action='Preserve deferred01 and failed cancellation control. Separate capacity02 build/run must acquire the unchanged original lock and repeat fresh authority/storage/runtime/resources. No further booking reduction; no biological absence claim.')
    except BaseException as error:value['error']={'kind':type(error).__name__,'message':str(error)}
    value['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'error':value.get('error'),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
    return 0 if value['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
