"""C-only audit of retained UNC03 failed worker; does not retry or inspect UNC."""
from pathlib import Path
import datetime, hashlib, json
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
D=W/'stage5_unc_bind_actual_postiq_03'
BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
U='0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d'
SCOPE='NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY_ONLY'

def main():
    out=W/'stage5_unc03_failed_scope_independent_review01.json';R.require(not out.exists(),'Fresh failed-scope report required')
    result={'schema':'STAGE05_UNC03_CLOSED_FAILED_SCOPE_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_READBACK','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only exact source/config/request/retained lifecycle bytes; no producer imports, UNC, WSL, lock, registry, process effect or Git action','original_probe_gate':'FAILED_PRESERVED','scientific_adoption':False}
    try:
        v=R.read(D/'result.json');q=R.read(D/'request.json');p=R.read(D/'prepared.json');unlock=R.read(D/'lock_released.json')
        R.require(v['state']=='FAILED' and v['schema']=='STAGE05_EXACT_BIND_UNC_VISIBILITY_V1' and v['source_sha256']==q['script_sha256']==p['script_sha256']==R.sha(W/'stage5_unc_bind_probe.py')==U,'Original failed state/source differs')
        R.require(v['scope']==q['scope']==p['scope']==SCOPE and v['scientific_adoption_authorized'] is False,'Non-scientific failed scope differs')
        for name,pin in v['source_pins'].items():R.require(R.sha(W/name)==pin and q['source_pins'][name]==pin,'Exact dependency differs')
        R.lock(v['workflow_lock']);R.lock(q['workflow_lock'])
        R.require(q['actual_windows_owner']==v['actual_windows_owner'] and q['nonce']==p['nonce'] and q['sentinel_name']=='.unc_visibility_'+q['nonce'],'Owner/request/sentinel join differs')
        request_sha=R.sha(D/'request.json');R.require(p['request_sha256']==request_sha and p['state']=='PASS_LINUX_SENTINEL_PREPARED' and p['phase']=='prepared' and type(p['child_processes_spawned']) is int and p['child_processes_spawned']==0,'Linux preparation evidence differs')
        config=R.pinned(R.cpath(q['config_linux_path']),q['config_sha256']);R.require(q['config_sha256']==v['config_sha256'] and q['config_linux_path'].endswith('/stage5_unc_config_actual_postprofile_03.json'),'Actual UNC03 config route differs')
        proof=p['storage_before'];R.require(proof==p['storage_after'] and proof['boot_id']==BOOT and proof['target_mount']['filesystem']=='ext4' and proof['target_mount']['mountpoint']==q['target'],'Current ext4 storage before/after differs')
        storage=R.pinned(R.cpath(proof['proof_path']),proof['proof_sha256']);R.require(all(proof[k]==val for k,val in storage.items()) and config['work_storage']['proof_sha256']==proof['proof_sha256'] and proof['proof_path']==config['work_storage']['proof_path'],'Pinned actual storage proof differs')
        linux_payload=bytes.fromhex(q['linux_payload_hex']);windows_payload=bytes.fromhex(q['windows_payload_hex'])
        R.require(64<=len(linux_payload)<=512 and 64<=len(windows_payload)<=512 and linux_payload!=windows_payload and p['linux_file']['bytes']==len(linux_payload) and p['linux_file']['sha256']==hashlib.sha256(linux_payload).hexdigest() and p['directory_device']==proof['directory_device']==p['linux_file']['device'],'Exact bounded Linux sentinel bytes/device differ')
        boot=R.pinned(W/'master_newboot_reconciliation_actual01.json','07a6546d3100bd979884b5a1e4d0c44952a4fc3cdd5a020087d4bbbc5e6d8cf3');stamp=datetime.datetime.fromisoformat(boot['current_boot']['last_boot_utc']);ft=int((stamp-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10_000_000)
        R.require(len(v['steps'])==1 and v['steps'][0]['phase']=='linux-prepare','Unexpected completed Linux phase')
        prep=v['steps'][0];R.terminal(prep['birth'],prep['exit'],ft)
        R.require(prep['argv'][prep['argv'].index('--request-sha256')+1]==request_sha and prep['argv'][prep['argv'].index('--mode')+1]=='linux-prepare','Linux retained request/mode differs')
        jd=D/'windows_io_worker';job=R.read(jd/'result.json');launch=R.read(jd/'launch.json');root=R.read(jd/'root_exit.json')
        R.require(job['schema']=='STAGE05_OWNED_WINDOWS_IO_JOB_V2' and job['state']=='FAILED' and job['owned_closure_proven'] is True and job['created'] is True and job['assigned'] is True,'Failed named worker final closure differs')
        R.require(job['source_sha256']==U and job['api_sha256']==v['source_pins']['atomic_iqtree_windows.py'] and job['owner']==v['actual_windows_owner'],'Named worker source/owner differs')
        R.require(job['birth']==launch['birth']==root['birth'] and job['exit']==root['exit'] and job['job_name']==launch['job_name']==root['job_name'] and job['argv']==launch['argv']==root['argv'],'Named Job lifecycle joins differ')
        R.terminal(job['birth'],job['exit'],ft,code=1,image=R.PYTHON)
        R.require(job['birth']['creation_filetime']>prep['exit']['exit_filetime'] and job['argv'][job['argv'].index('--request-sha256')+1]==request_sha and job['argv'][job['argv'].index('--mode')+1]=='windows-io','Windows worker order/request/mode differs')
        R.require(job['owned_job']['job_active_processes']==0 and job['owned_job']['job_pids']==[] and job['drain_samples'] and job['drain_samples'][-1]['root_wait']==0 and job['drain_samples'][-1]['job']['job_active_processes']==0 and job['drain_samples'][-1]['job']['job_pids']==[],'Full named Job drain not empty')
        R.require(v['error']['message']==job['original_error']['message']=='Owned Windows worker exited nonzero after closed scope','Known closed failure reason differs')
        R.require(unlock['state']=='EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK' and unlock['released'] is True and unlock['scientific_adoption_authorized'] is False,'Explicit original unlock differs')
        R.require(not (D/'windows_io.json').exists() and not (D/'final.json').exists(),'Failed original scope unexpectedly has later success receipt')
        stop=Path(v['workflow_lock']['path']).parent/'stage05_owned_closure_unproven.json';observed=datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:stop.lstat()
        except FileNotFoundError:stop_absent=True
        else:stop_absent=False
        R.require(stop_absent,'Current STOP exists; additional root reconciliation required')
        for f in sorted(D.rglob('*')):
            if f.is_file():R.data(f)
        result.update(state='PASS_FAILED_UNC03_RETAINED_SCOPE_CLOSED_CAUSE_UNRECORDED',original_result_sha256=R.sha(D/'result.json'),request_sha256=request_sha,config_sha256=v['config_sha256'],source_sha256=U,linux_boot_id=BOOT,linux_prepare_retained_exit0=prep['exit'],linux_prepare_spawned_children=0,windows_worker_retained_exit1=job['exit'],full_named_job_empty=True,owned_closure_proven=True,original_lock_explicitly_released=True,current_STOP_observation={'utc':observed,'path':str(stop),'exists':False,'scope':'POINT_IN_TIME_ONLY'},failure_cause='UNRECORDED; U0664 windows-io has no retained exception/stdout/stderr receipt',windows_io_publication='NOT_EMITTED',linux_finalization_and_sentinel_cleanup='NOT_RUN',sentinel={'name':q['sentinel_name'],'linux_target':q['target'],'canonical_UNC':q['unc'],'linux_payload_bytes':len(linux_payload),'linux_payload_sha256':hashlib.sha256(linux_payload).hexdigest(),'windows_expected_payload_bytes':len(windows_payload),'windows_expected_payload_sha256':hashlib.sha256(windows_payload).hexdigest(),'partial_windows_bin_presence':'UNPROVEN'},limitations=['The failed gate remains FAILED; successful Linux storage preparation and closed worker do not prove UNC visibility.','No error trace locates the failing expression; do not assume path, permission, nlink, opened identity, exclusive write or fsync cause.','No windows_io.json cannot establish that windows.bin was never written. Preserve the exact nonce namespace until targeted read-only diagnosis and byte/identity-bound cleanup.'],diagnostic_route=['Use a separately reviewed default-NOOP bounded diagnostic under the original same lock and U.windows_job retained named Job; do not retry the UNC writer.','Read only the four fixed canonical/backing linux.bin/windows.bin paths and their exact nonce directories. Preserve before/open/after metadata, native error kind/winerror and bounded payload SHA; invoke unchanged U.tiny_read separately.','Record actual current default Ubuntu UID/Flags and source/request/config bindings; compare every U.tiny_read predicate without relaxing it.','Require a new complete reviewed three-phase UNC success and exact sentinel cleanup before science.'])
    except BaseException as error:result['error']={'kind':type(error).__name__,'message':str(error)}
    result['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':result['state'],'error':result.get('error'),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checked_files':len(R.CHECKED)}))
    return 0 if result['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
