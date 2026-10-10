"""C-only actual capacity02 config/build joins after first01 closed admission defer."""
from pathlib import Path
import copy, datetime, hashlib, json
import review_stage5_postboot_gate as R
import stage5_build_backing_actual_config as B
import stage5_atomic as S

W=Path(__file__).resolve().parent
PINS={
 'stage5_actual_request_backing_capacity_02.json':'13cdeba557bf0042a4fe2e95bf0905734cdd4735b0c333f255838b3fdb7e9ccb',
 'stage5_actual_backing_capacity_02.json':'4c2d9812afd2dbabaa6ba3177395dee17511946966fb3b7491f579cfd3602d63',
 'stage5_actual_request_backing_01.json':'96fc9e6a9893fb56122f701378aa49eb3f50773b797d6cdf4c9130548be3cb44',
 'stage5_actual_backing_01.json':'30a86eb18cddc69eb0cfbdd3ae93473ec54812cd5a859ededd25af01fb737dfa',
 'stage5_build_backing_actual_config.py':'e1b7b4782be7cb4faa84cf546884075e860d2d010a1774ba7d61846bfff7905c',
 'stage5_first_capacity02_request_independent_review01.json':'48d18021fc0fed39f6a4d8f4e4bcb403000f1a6ef990f0ad95bc7450c4cdeef6',
 'stage5_first_waiting01_closed_independent_review.json':'84fdfd6b64d9e2468466884d1535723ac84835ca5332322717a3d707b4cf31a5',
 'stage5_first_backing_actual_config02_independent_review.json':'dfdcf5efc4444123f5e3829e3bbe7841c4d74e2c4f23af39c7679ac9190f7abc'}

def main():
    out=W/'stage5_first_backing_capacity02_actual_config_independent_review01.json'
    R.require(not out.exists(),'Preserve actual capacity02 review')
    value={'schema':'STAGE05_CAPACITY02_ACTUAL_CONFIG_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_ACTUAL_CONFIG_JOINS',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
      'method':'Bounded C-only actual request/config/build exact deltas, six existing gate/result/unlock/peer joins and closed waiting01 prerequisite; unchanged builder explicit_policy and scientific load_config only. No G/UNC/WSL/API/lock/process/network/Git effects.',
      'scientific_native_execution':'NOT_RUN','scientific_adoption':False}
    try:
        for name,pin in {**PINS,**B.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen capacity02 source/config/peer differs: '+name)
        request=R.read(W/'stage5_actual_request_backing_capacity_02.json');old_request=R.read(W/'stage5_actual_request_backing_01.json')
        config=R.read(W/'stage5_actual_backing_capacity_02.json');old=R.read(W/'stage5_actual_backing_01.json')
        receipt=R.read(W/'stage5_actual_backing_capacity_02_build_receipt.json')
        source_peer=R.read(W/'stage5_first_capacity02_request_independent_review01.json')
        expected_request=copy.deepcopy(old_request);expected_request['native_resource_bytes']['linux_job_requirement_bytes']=1476395008
        expected_request['resource_basis']=source_peer['resource_basis']
        R.require(request==expected_request and source_peer['state']=='PASS_EXPLICIT_LINUX_BOOKING02_REQUEST_SOURCE_AND_EXACT_DELTA_ONLY','Actual request has an unreviewed delta')
        expected=copy.deepcopy(old);expected['resource_policy']['linux_job_requirement_bytes']=1476395008
        R.require(config==expected and S.load_config(W/'stage5_actual_backing_capacity_02.json')==config,'Actual config has more than the single Linux capacity booking delta')
        constructed=B.explicit_policy(R.read(W/'stage5_atomic_config.template.json'),request)
        for key,section,pathkey in [('runtime_manifest','runtime','manifest_path'),('storage_proof','work_storage','proof_path')]:
            spec=request[key];path=Path(spec['path']);R.require(path.parent==W and R.sha(path)==spec['sha256'],'Selected runtime/storage bytes differ')
            constructed[section][pathkey]=B.linux_path(path);constructed[section][pathkey.replace('_path','_sha256')]=spec['sha256']
        R.require(config==constructed,'Actual config differs from unchanged exact builder policy/template')
        R.require(receipt['schema']=='STAGE05_FIRST_GENOME_CONFIG_BUILD_V1' and receipt['state']=='PASS_CONFIG_AND_WINDOWS_ADMISSION_ONLY'
          and receipt['config_path']==str(W/'stage5_actual_backing_capacity_02.json') and receipt['config_sha256']==PINS['stage5_actual_backing_capacity_02.json']
          and receipt['request_sha256']==PINS['stage5_actual_request_backing_capacity_02.json'] and receipt['resource_basis']==request['resource_basis']
          and receipt['source_sha256']==PINS['stage5_build_backing_actual_config.py'] and receipt['source_pins']==B.PINS
          and receipt['gate_pins']==request['gates'] and receipt['runtime_manifest']==request['runtime_manifest'] and receipt['storage_proof']==request['storage_proof']
          and receipt['explicit_original_byte_unlock'] is True and receipt['scientific_execution']=='NOT_RUN'
          and receipt['linux_fresh_admission']=='REQUIRED_AT_NATIVE_RUN' and receipt['actual_detector_peak']=='UNMEASURED_FIRST_APPROVED_GENOME_REQUIRED','Actual build scope/source/admission/unlock receipt differs')
        R.lock(receipt['workflow_lock']);joins={};prior=R.read(W/'stage5_first_backing_actual_config02_independent_review.json')
        R.require(prior['state']=='PASS_ACTUAL_FIRST_GENOME_BACKING_CONFIG_SIX_GATES_BYTES_AND_BUILD_ADMISSION','Prior independent full method/config acceptance differs')
        for kind,spec in request['gates'].items():
            path=Path(spec['path']);R.require(R.sha(path)==spec['sha256'] and R.sha(path.parent/'lock_released.json')==spec['unlock_sha256'],'Actual gate/result/unlock changed: '+kind)
            previous=prior['six_gate_joins'][kind];peer=R.pinned(W/previous['independent_peer'],previous['independent_peer_sha256'])
            R.require(peer['state'].startswith('PASS_') and peer['actual_result_sha256']==spec['sha256']
              and peer.get('unlock_sha256',peer.get('original_unlock_sha256'))==spec['unlock_sha256'],'Independent gate peer/result join differs: '+kind)
            B.checked_gate(kind,spec);joins[kind]=previous
        storage=R.read(Path(request['storage_proof']['path']));runtime=R.read(Path(request['runtime_manifest']['path']))
        R.require(storage['boot_id']==prior['linux_boot_id']=='f0ffcebc-4901-479d-9559-89d45e9cfa38'
          and storage['canonical_root']==config['root'] and storage['canonical_target']==config['output_root']
          and storage['backing']=='/var/tmp/lab_rm_stage05_atomic_v1' and runtime['roots']=={k:config['runtime'][k] for k in ('environment_dir','models_dir','padloc_db')},'Current storage boot and unchanged runtime roles differ')
        closed=R.read(W/'stage5_first_waiting01_closed_independent_review.json');old_spool=W/'stage5_owner_GCF_000009425_1_backing_01'
        R.require(closed['state']=='PASS_FIRST01_NATURAL_ADMISSION_DEFER_NO_NATIVE_SCOPE_CLOSED_AND_ORIGINAL_UNLOCK'
          and closed['actual_result_sha256']==R.sha(old_spool/'result.json') and closed['actual_unlock_sha256']==R.sha(old_spool/'lock_released.json')
          and closed['owned_closure_proven'] is True and closed['no_native_launch_in_this_invocation'] is True
          and closed['original_lock_explicitly_released'] is True,'Prior first01 genuine closure/unlock prerequisite differs')
        p=config['resource_policy'];res=receipt['actual_windows_resources'];old_unlock=R.read(old_spool/'lock_released.json')
        R.require(res['utc']>old_unlock['utc'] and res['physical_available_bytes']>=p['windows_reserve_bytes']+p['incremental_windows_requirement_bytes']
          and res['commit_headroom_bytes']>=p['commit_requirement_bytes'] and len(res['disk_available_bytes'])==2
          and all(v>=p['minimum_disk_free_bytes'] for v in res['disk_available_bytes'].values()),'Actual capacity02 build admission or ordering differs')
        pub=R.read(W/'master_capacityprep64_remote_readback.json')
        R.require(pub['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and pub['required_files']==pub['verified_files']==len(pub['files'])==24
          and all(x['actual_remote_bytes_read'] and x['sha256_verified'] and x['byte_count_verified'] for x in pub['files'])
          and PINS['stage5_actual_request_backing_capacity_02.json'] in {x['sha256'] for x in pub['files']},'Reviewed capacity02 request publication64 differs')
        value.update(state='PASS_ACTUAL_CAPACITY02_CONFIG_EXACT_SINGLE_BOOKING_DELTA_SIX_GATES_AND_PRIOR_CLOSED_SCOPE',
          actual_config_sha256=PINS['stage5_actual_backing_capacity_02.json'],actual_request_sha256=PINS['stage5_actual_request_backing_capacity_02.json'],
          actual_build_receipt_sha256=R.sha(W/'stage5_actual_backing_capacity_02_build_receipt.json'),original_lock_explicitly_released=True,
          original_waiting01_closure_peer_sha256=PINS['stage5_first_waiting01_closed_independent_review.json'],six_gate_joins=joins,
          linux_boot_id=storage['boot_id'],linux_job_requirement_bytes=1476395008,linux_reserve_bytes=p['linux_reserve_bytes'],
          repeated_linux_admission_requirement_bytes=p['linux_job_requirement_bytes']+p['linux_reserve_bytes'],sampled_aggregate_RSS_stop_bytes=p['sampled_rss_stop_bytes'],
          resource_wait_seconds=p['resource_wait_seconds'],recorded_Windows_build_admission=res,
          full_native_method_models_sources_paths_panel_accepted_stage4_and_all_other_policy_exact=True,actual_detector_peak='UNMEASURED_FIRST_APPROVED_GENOME_REQUIRED',
          capacity_basis='Explicit unmeasured allocation1.375GiB above unchanged1.25GiB sampled RSS stop and unchanged1GiB reserve. This does not prove native admission or runtime fit.',
          required_native_boundary='Publish/read back actual request/config/build/peer, then unchanged owner repeats live authority/STOP/storage/runtime/current resources and original lock. Existing repeated admission and execution limits remain mandatory; no further booking reduction if it does not fit.')
    except BaseException as error:value['error']={'kind':type(error).__name__,'message':str(error)}
    value['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'error':value.get('error'),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
    return 0 if value['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
