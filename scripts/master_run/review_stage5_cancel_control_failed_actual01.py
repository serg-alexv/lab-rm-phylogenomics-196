"""C-only failed control-client audit; preserves original-runner gate separately."""
from pathlib import Path
import ast, datetime, hashlib, json
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
PINS={'stage5_cancel_exact_waiting_windows.py':'42eb45458bbb6eee23262b548d2c6c04e695597e949790bf61f79dacfbfc328c',
      'stage5_cancel_exact_waiting_bootstrap.py':'7b02c2f05750371dbb9dca9026a86318054f41cdb0214aa22182bbf34da6c63b',
      'stage5_cancel_exact_waiting_windows_source_independent_review01.json':'7c24ea87872a1c21f8be9e09754b52e571205731175c2ecb5f3f7599133b9ca8',
      'stage5_cancel_exact_waiting_linux_source_independent_review01.json':'17b6a8f39cf8c628e007b094186115b0b4bd943779208bf8196eb1ccfe995431'}
def main():
    out=W/'stage5_cancel_control_failed_actual01_independent_review.json';R.require(not out.exists(),'Preserve failed control peer')
    value={'schema':'STAGE05_CANCEL_FAILED_CONTROL_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_READBACK','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only exact source/published readback/intent/retained Windows launch+exit+named Job receipts and point-in-time C namespace observations. No producer imports, G/UNC/WSL/API/lock/process effects/network/Git.',
           'actual_cancellation_state':'FAILED_PRESERVED','scientific_adoption':False,'original_owner_closure_or_unlock_accepted':False}
    try:
        for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Frozen control source/peer differs')
        folder=W/'stage5_cancel_exact_waiting_windows_01';jobdir=folder/'wsl_control_client'
        owner=R.read(folder/'result.json');intent=R.read(folder/'intent.json');launch=R.read(jobdir/'launch.json');end=R.read(jobdir/'root_exit.json');job=R.read(jobdir/'result.json');progress=R.read(jobdir/'progress.json')
        R.require(owner['schema']=='STAGE05_EXACT_WAITING_CANCEL_WINDOWS_CONTROL_V1' and owner['state']=='FAILED'
                  and owner['source_sha256']==PINS['stage5_cancel_exact_waiting_windows.py'] and owner['WSL_clients_created']==1
                  and owner['original_owner_termination_or_unlock_proven'] is False and owner['second_workflow_lock'] is False
                  and owner['original_science_owner_or_science_client_signaled'] is False and owner['original_owner_query_handle_closed'] is True,'Failed outer scope/handle receipt differs')
        for name,pin in owner['source_pins'].items():R.require(R.sha(W/name)==pin,'Actual source dependency differs')
        R.lock(owner['original_lock_binding']);R.require(owner['owner_nonce']=='1439a454dde8448f8f9606b6de6ac702' and owner['original_owner']['pid']==24488 and owner['original_owner']['creation_filetime']==134360766940521715 and owner['original_owner']['exited'] is False,'Original live-owner observation differs')
        R.require(job['schema']=='STAGE05_OWNED_WINDOWS_IO_JOB_V2' and job['state']=='FAILED' and job['source_sha256']==owner['source_sha256']
                  and job['api_sha256']==owner['source_pins']['atomic_iqtree_windows.py'] and job['created'] is True and job['assigned'] is True
                  and job['owned_closure_proven'] is True and not job.get('closure_error') and not job.get('handle_close_errors') and not job.get('result_write_error'),'Actual failed Job closure/finalization differs')
        R.terminal(job['birth'],job['exit'],134360662075000000,code=1)
        R.require(job['birth']['pid']==10492 and job['birth']['creation_filetime']==134360779468058303 and job['exit']['exit_filetime']==134360779468524432,'Exact retained failed client birth/exit differs')
        R.require(job['argv']==intent['argv']==launch['argv']==end['argv']==progress['argv'] and job['owner']==launch['owner']==end['owner']
                  and job['birth']==launch['birth']==end['birth'] and job['exit']==end['exit'] and job['job_name']==launch['job_name']==end['job_name']==progress['job_name'],'Retained failure receipt joins differ')
        R.require(job['argv'][:6]==[R.WSL,'-d','Ubuntu','-u','root','--exec'] and job['argv'][7:] == ['-B','/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_cancel_exact_waiting_bootstrap.py','--run','--source-sha256',PINS['stage5_cancel_exact_waiting_bootstrap.py']],'Exact helper request argv differs')
        empty=job['owned_job'];R.require(empty['job_active_processes']==0 and empty['job_pids']==[] and job['drain_samples'] and job['drain_samples'][-1]['root_wait']==0 and job['drain_samples'][-1]['job']==empty,'Named Job nonempty or unproven')
        R.require(job['original_error']=={'kind':'ValueError','message':'Owned Windows worker exited nonzero after closed scope','winerror':None} and owner['error_kind']=='ValueError','Failure classification differs')
        pub=R.read(W/'master_capacityprep64_remote_readback.json')
        R.require(pub['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and pub['expected_commit'].startswith('bd7cc38') and pub['required_files']==pub['verified_files']==len(pub['files'])==24 and all(r['actual_remote_bytes_read'] and r['byte_count_verified'] and r['sha256_verified'] for r in pub['files']),'Actual source publication64 readback differs')
        published={r['sha256'] for r in pub['files']};R.require(set(PINS.values())<=published,'Exact source/peer not covered by publication64')
        linux=W/'stage5_cancel_exact_waiting_GCF_000009425_1_01';R.require(not linux.exists() and not linux.is_symlink(),'Linux control namespace unexpectedly exists; re-audit instead')
        tree=ast.parse(R.data(W/'stage5_cancel_exact_waiting_bootstrap.py'));main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        statements=[ast.unparse(n) for n in main.body]
        R.require(any('OUT.mkdir()' in s for s in statements) and source_signal_order(R.data(W/'stage5_cancel_exact_waiting_bootstrap.py').decode()),'Source signal precondition ordering differs')
        observations={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'Linux_cancel_spool_exists':False,'original_science_owner_result_exists':(W/'stage5_owner_GCF_000009425_1_backing_01/result.json').exists(),'original_science_owner_unlock_exists':(W/'stage5_owner_GCF_000009425_1_backing_01/lock_released.json').exists(),'scope':'POINT_IN_TIME_C_ONLY'}
        value.update(state='PASS_FAILED_CANCEL_CONTROL_RETAINED_WINDOWS_SCOPE_CLOSED_SIGNAL_NOT_ESTABLISHED',actual_outer_result_sha256=R.sha(folder/'result.json'),actual_job_result_sha256=R.sha(jobdir/'result.json'),actual_source_publication={'commit':pub['expected_commit'],'readback_sha256':R.sha(W/'master_capacityprep64_remote_readback.json'),'verified_files':24},retained_control_client={'pid':10492,'creation_filetime':134360779468058303,'exit_filetime':134360779468524432,'exit_code':1},windows_control_job_empty=True,windows_control_handles_closed_without_recorded_error=True,original_owner_query_handle_closed=True,observations=observations,Linux_signal_request='NOT_ESTABLISHED_NO_LINUX_RECEIPT_OR_DURABLE_INTENT_OBSERVED',claim_limit='Published helper cannot enter its signal path before fixed OUT creation and durable signal intent. Their C namespace is absent now, which is consistent with failure before helper entry/preconditions; retained Windows exit1 without stdout/stderr does not establish the exact Linux/WSL startup exception or an unconditional historical no-signal claim.',failure_cause='UNRECORDED; unchanged copied U job does not capture control-client stdout/stderr',next_action='No control expansion, remediation or retry. Retain existing original science owner and await its bounded1800s admission expiry. Independently prove actual runner no-native terminal/owned closure, original retained WSL exit and explicit original lock release before config02 build/run.',old_science_waiting_scope_not_reclassified=True)
    except BaseException as error:value['error']={'kind':type(error).__name__,'message':str(error)}
    value['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'error':value.get('error'),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
    return 0 if value['state'].startswith('PASS_') else 1
def source_signal_order(source):
    return source.index('OUT.mkdir()')<source.index("atomic(OUT/'signal_intent.json',result)")<source.index('P.send_pidfd_signal(fd,signal.SIGTERM)')
if __name__=='__main__':raise SystemExit(main())
