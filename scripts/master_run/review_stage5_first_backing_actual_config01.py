"""Bounded C-only actual first-genome request/config/build joins; no native actions."""
from pathlib import Path
import copy, datetime, hashlib, json
import review_stage5_postboot_gate as R
import stage5_build_backing_actual_config as B
import prepare_stage5_first_backing_actual_request as M
import stage5_atomic as S

W=Path(__file__).resolve().parent
BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
PINS={'stage5_actual_request_backing_01.json':'96fc9e6a9893fb56122f701378aa49eb3f50773b797d6cdf4c9130548be3cb44',
      'stage5_actual_backing_01.json':'30a86eb18cddc69eb0cfbdd3ae93473ec54812cd5a859ededd25af01fb737dfa',
      'stage5_build_backing_actual_config.py':'e1b7b4782be7cb4faa84cf546884075e860d2d010a1774ba7d61846bfff7905c',
      'prepare_stage5_first_backing_actual_request.py':'aed494a55de00bf719ce0827f4e45c66b2079203dd046bb49243e805b066c44a',
      'stage5_first_backing_actual_config_source_independent_review01.json':'a6ce87f95f343b4640d8081d8e924f67da04ac541403dd3f0f223979f430f2ab',
      'postboot_authority_review01.json':'4a0a307f4276b4babdcf9dedb44f080393638e888e8720354a647d502d49a143'}
PEERS={'toolchain':'stage5_toolchain07_postprofile_independent_review.json','runtime':'stage5_runtime08_postprofile_independent_review.json',
       'interop':'stage5_interop05_postprofile_independent_review.json','storage':'stage5_storage06_postprofile_independent_review.json',
       'drivefs':'stage5_drivefs04_postprofile_independent_review.json','unc':'stage5_unc_backing_actual04_independent_review01.json'}

def main():
    out=W/'stage5_first_backing_actual_config02_independent_review.json'
    R.require(not out.exists(),'Preserve independent actual review')
    result={'schema':'STAGE05_FIRST_BACKING_ACTUAL_CONFIG_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_ACTUAL_CONFIG_JOINS',
            'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
            'method':'C-only decoded actual request/config/build/source/publication and six completed-gate peer joins; unchanged scientific load_config only. No G/UNC/WSL/registry/lock/process effects/network/Git.',
            'scientific_execution':'NOT_RUN','scientific_acceptance':False}
    try:
        for name,pin in {**PINS,**B.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen actual/source bytes differ: '+name)
        request=R.read(W/'stage5_actual_request_backing_01.json');config=R.read(W/'stage5_actual_backing_01.json')
        receipt=R.read(W/'stage5_actual_backing_01_build_receipt.json')
        R.require(request==M.build_request(R.data(W/'stage5_actual_config_request.template.json'),lambda name:R.data(W/name)), 'Actual request differs from exact deterministic constructor')
        R.require(request['native_resource_bytes']==M.NATIVE_RESOURCE_BYTES and request['resource_basis']==M.RESOURCE_BASIS,'First-genome explicit budget/basis differs')
        template=R.read(W/'stage5_atomic_config.template.json');expected=copy.deepcopy(template)
        expected['resource_policy'].update(M.NATIVE_RESOURCE_BYTES);expected['resource_policy']['resource_wait_seconds']=1800
        for key,section,pathkey in [('runtime_manifest','runtime','manifest_path'),('storage_proof','work_storage','proof_path')]:
            spec=request[key];path=Path(spec['path']);R.require(path.parent==W and R.sha(path)==spec['sha256'],'Selected actual candidate differs')
            expected[section][pathkey]=B.linux_path(path);expected[section][pathkey.replace('_path','_sha256')]=spec['sha256']
        R.require(config==expected and S.load_config(W/'stage5_actual_backing_01.json')==config,'Whole actual config/template or unchanged scientific parser differs')
        R.require(receipt['schema']=='STAGE05_FIRST_GENOME_CONFIG_BUILD_V1' and receipt['state']=='PASS_CONFIG_AND_WINDOWS_ADMISSION_ONLY'
                  and receipt['config_path']==str(W/'stage5_actual_backing_01.json') and receipt['config_sha256']==PINS['stage5_actual_backing_01.json']
                  and receipt['request_sha256']==PINS['stage5_actual_request_backing_01.json'] and receipt['source_sha256']==PINS['stage5_build_backing_actual_config.py']
                  and receipt['source_pins']==B.PINS and receipt['gate_pins']==request['gates'] and receipt['resource_basis']==M.RESOURCE_BASIS
                  and receipt['runtime_manifest']==request['runtime_manifest'] and receipt['storage_proof']==request['storage_proof']
                  and receipt['explicit_original_byte_unlock'] is True and receipt['scientific_execution']=='NOT_RUN'
                  and receipt['linux_fresh_admission']=='REQUIRED_AT_NATIVE_RUN' and receipt['actual_detector_peak']=='UNMEASURED_FIRST_APPROVED_GENOME_REQUIRED','Actual build receipt binding differs')
        R.lock(receipt['workflow_lock']);joins={}
        for kind,name in PEERS.items():
            spec=request['gates'][kind];path=Path(spec['path']);peer=R.read(W/name)
            R.require(path==W/M.GATES[kind]/'result.json' and R.sha(path)==spec['sha256']
                      and R.sha(path.parent/'lock_released.json')==spec['unlock_sha256'],'Actual gate/unlock bytes differ: '+kind)
            R.require(peer['state'].startswith('PASS_') and peer['actual_result_sha256']==spec['sha256']
                      and peer.get('unlock_sha256',peer.get('original_unlock_sha256'))==spec['unlock_sha256']
                      and peer.get('linux_boot_id',peer.get('detail',{}).get('linux_boot_id'))==BOOT,'Closed gate independent peer differs: '+kind)
            for relative,row in peer['checked_files'].items():R.require(R.sha(W/relative)==row['sha256'] and len(R.data(W/relative))==row['bytes'],'Peer source/closure byte drift: '+relative)
            B.checked_gate(kind,spec)
            joins[kind]={'result_sha256':spec['sha256'],'unlock_sha256':spec['unlock_sha256'],'independent_peer':name,'independent_peer_sha256':R.sha(W/name)}
        runtime=R.read(Path(request['runtime_manifest']['path']));storage=R.read(Path(request['storage_proof']['path']))
        R.require(runtime['schema']=='STAGE05_PINNED_RUNTIME_V1' and runtime['roots']=={k:config['runtime'][k] for k in ('environment_dir','models_dir','padloc_db')},'Runtime roles differ')
        R.require(storage['boot_id']==BOOT and storage['canonical_target']==config['output_root'] and storage['canonical_root']==config['root']
                  and storage['backing']=='/var/tmp/lab_rm_stage05_atomic_v1' and storage['helper_sha256']=='7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f'
                  and storage['target_mount']['filesystem']==storage['backing_mount']['filesystem']=='ext4','Current canonical storage proof differs')
        for kind,key in [('runtime','runtime_manifest'),('storage','storage_proof')]:
            terminal=R.read(Path(request['gates'][kind]['path']).parent/'linux_terminal.json')
            R.require(terminal['bootstrap']['boot_id']==BOOT and terminal['candidate_path']==B.linux_path(Path(request[key]['path'])) and terminal['candidate_sha256']==request[key]['sha256'],'Actual candidate producer join differs')
        final=R.read(W/M.GATES['unc']/'final.json');unc=R.read(W/M.GATES['unc']/'result.json')
        R.require(R.sha(W/M.GATES['unc']/'final.json')==unc['files']['final.json'] and final['storage_after']['proof_path']==config['work_storage']['proof_path']
                  and final['storage_after']['proof_sha256']==config['work_storage']['proof_sha256'],'Actual backing qualification selected storage differs')
        p=config['resource_policy'];resources=receipt['actual_windows_resources']
        R.require(resources['physical_available_bytes']>=p['windows_reserve_bytes']+p['incremental_windows_requirement_bytes']
                  and resources['commit_headroom_bytes']>=p['commit_requirement_bytes'] and len(resources['disk_available_bytes'])==2
                  and all(v>=p['minimum_disk_free_bytes'] for v in resources['disk_available_bytes'].values()),'Recorded Windows build admission failed')
        publications={}
        for name,commit in [('master_backingprep60_remote_readback.json','9ca871ed25de7a108eb4086ec53a60a0f4cfe3af'),('master_backingactual61_remote_readback.json','2aa249403738f61ef67b2f52d29cb3ca209fe78f')]:
            pub=R.read(W/name);R.require(pub['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and pub['expected_commit']==commit
                  and pub['required_files']==pub['verified_files']==len(pub['files']) and all(row['actual_remote_bytes_read'] and row['sha256_verified'] and row['byte_count_verified'] for row in pub['files']),'Prior GitHub exact readback differs')
            publications[name]={'commit':commit,'sha256':R.sha(W/name),'verified_files':pub['verified_files']}
        result.update(state='PASS_ACTUAL_FIRST_GENOME_BACKING_CONFIG_SIX_GATES_BYTES_AND_BUILD_ADMISSION',request_sha256=PINS['stage5_actual_request_backing_01.json'],config_sha256=PINS['stage5_actual_backing_01.json'],build_receipt_sha256=R.sha(W/'stage5_actual_backing_01_build_receipt.json'),linux_boot_id=BOOT,six_gate_joins=joins,native_resource_bytes=M.NATIVE_RESOURCE_BYTES,resource_basis=M.RESOURCE_BASIS,resource_wait_seconds=1800,whole_template_method_paths_and_policy_exact=True,unchanged_load_config_passed=True,original_lock_explicitly_released=True,recorded_Windows_build_admission=resources,prior_publications=publications,authority_scope='C-only immutable authority/source and completed build evidence. The reviewed builder read ACTIVE_DIRECT_USER_CONTINUATION with automatic_resume false inside the original lock; this receipt does not separately retain that decoded control. Native owner must repeat live authority, STOP, storage, runtime, ownership and resources immediately before scientific execution.',actual_detector_peak='UNMEASURED_FIRST_APPROVED_GENOME_REQUIRED',accepted_stage4_approved196_and_full_native_method_preserved=True,old_failed_canonical_UNC03_preserved=True)
        for name,pin in {**PINS,**B.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen bytes changed during review: '+name)
    except BaseException as error:result['error']={'kind':type(error).__name__,'message':str(error)}
    result['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':result['state'],'error':result.get('error'),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
    return 0 if result['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
