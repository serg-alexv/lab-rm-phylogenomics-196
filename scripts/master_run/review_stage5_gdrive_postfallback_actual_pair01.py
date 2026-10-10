"""C-only independent exact readback of the closed postfallback checked-unlock G diagnosis/mount pair."""
from pathlib import Path
import datetime, hashlib, json
import review_stage5_postboot_gate as R

W=Path(__file__).resolve().parent
SOURCE='a5efd24a17655324b8a03d13bf74e06f77195cb401ca9db8a3f73f94e1ab8ada'
BOOT='8cca020a-71b2-4163-92dc-6087df12dd45'
PROOF='2c306c3d2dab65cc4da996118ff521506e028cf3fdc0a8ff5d0a891d24b74cdf'
SPOOLS=('stage5_gdrive_view_481ac77a42d942f3824590d50831443d','stage5_gdrive_view_ca29c7355cb04f82985b015e303bb249')
MOUNT=['/usr/bin/mount','-t','drvfs','G:','/mnt/g']
CONTROL={'status/run_control.json':'c4184e2af9ea0ef81f652d4d1baed00b9742fa2a3efdb9fe87491911ab2242cd','config/approved_accessions.txt':'85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6','config/approval.json':'9e231457d39cd959942f38930a1f2b72cc391cabc86d0839a8adf8f5b6c94bdc'}

def run_one(name,mount,boot_ft):
    d=W/name;v=R.read(d/'result.json');q=R.read(d/'request.json')
    R.require(v['schema']=='STAGE05_GDRIVE_WINDOWS_OWNER_RESULT_V1' and v['state']=='PASS_NONSCIENTIFIC_G_DRIVE_VIEW_HELPER','Actual G result state differs')
    for item in (v,q):
        R.require(item['source_sha256']==SOURCE and item['boot_id']==BOOT and item['scope']=='NONSCIENTIFIC_G_DRIVE_VISIBILITY_ONLY' and item['allow_mount'] is mount,'G source/boot/scope/mode differs')
        R.lock(item['workflow_lock'])
        R.require(item['fresh_toolchain_proof_sha256']==PROOF,'Fresh toolchain08 proof differs')
    R.require(v['owner_nonce']==q['owner_nonce'] and q['mount_argv']==MOUNT and q['linux_root']=='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196','Request nonce or exact G target differs')
    for group in ('source_pins','prior_pins','fresh_toolchain_pins'):
        for rel,pin in v[group].items():
            R.require(not Path(rel).is_absolute() and '..' not in Path(rel).parts,'Unsafe selected pin path')
            R.require(R.sha(W/rel)==pin,'Recorded dependency/history/fresh byte pin differs: '+rel)
    R.require(q['fresh_toolchain_pins']==v['fresh_toolchain_pins'] and R.read(W/'stage5_setup_toolchain_actual_postiq_08/toolchain_proof.json')['boot_id']==BOOT,'Fresh request/toolchain boot differs')
    held=R.pinned(d/'actual_owner_lock.json',q['owner_lock_sha256']);R.lock(held['workflow_lock'])
    owner=v['actual_owner'];R.require(held['owner']==owner and held['owner_nonce']==q['owner_nonce'] and owner['executable']==R.PYTHON and int(owner['creation_filetime'])>=boot_ft,'Actual owner/lock/birth differs')
    launch=R.read(d/'launch.json');exit=R.read(d/'wsl_exit.json')
    R.require(launch['owner_nonce']==exit['owner_nonce']==q['owner_nonce'] and launch['argv']==exit['argv']==v['argv'],'WSL request/launch/exit join differs')
    R.require(launch['retained_client_birth']==exit['birth'] and exit['terminal']==v['retained_client_terminal'],'Retained WSL birth/terminal differs')
    R.terminal(exit['birth'],exit['terminal'],boot_ft)
    for leaf in ('wsl.stdout.txt','wsl.stderr.txt'):R.require(R.sha(d/leaf)==v[leaf+'_sha256'],'Closed WSL stream hash differs')
    l=R.pinned(d/'linux_terminal.json',v['linux_terminal_sha256'])
    R.require(l['request_sha256']==R.sha(d/'request.json') and l['owner_nonce']==q['owner_nonce'] and l['source_sha256']==SOURCE and l['boot_id']==BOOT,'Linux exact request/source/boot differs')
    R.require(l['bootstrap']['argv']==v['argv'][8:] and l['bootstrap']['executable']=='/usr/bin/python3','Bootstrap exact argv differs')
    R.require(v['owned_closure_proven'] is True and l['owned_closure_proven'] is True and l['remaining_direct_children']==[] and v['original_lock_explicitly_released'] is True and v['unknown_closure_stop_preserved'] is False and v['log_hash_scope']=='CLOSED_FULL_LOGS','Owned closure/unlock/log scope differs')
    R.require(v['scientific_adoption_authorized'] is False and l['scientific_adoption_authorized'] is False and l['future_storage_and_UNC_visibility']=='REQUIRES_SEPARATE_FRESH_GATES','Scientific/future propagation scope differs')
    R.require(v['windows_before']==v['windows_after'] and v['windows_before']['control_sha256']==q['control_sha256']==CONTROL and v['windows_before']['empty_g_underlay']['entries']==[] and v['windows_before']['drive_type']==3,'Windows controls/empty underlay changed')
    ns=l['mount_namespace'];final=l['session_parent_final'];record=ns['parent_record']
    R.require(ns==final and ns['parent_executable']=='/init' and ns['self']==ns['parent'] and ns['pid1_role']=='DIAGNOSTIC_ONLY_NOT_SESSION_IDENTITY' and ns['parent_pid']==record['pid']==l['bootstrap']['identity']['ppid'] and record['start_ticks'] and l['session_parent_final_verified'] is True and l['session_parent_initial_verified'] is True,'WSL session parent birth/executable/namespace or final recheck differs')
    R.require(l['mountpoint_created'] is False and l['mount_performed'] is mount and l['observation_before']['g_mount'] is None,'G repair scope differs')
    native=[]
    if mount:
        R.require(l['state']==v['linux_state']=='PASS_EXACT_WINDOWS_LINUX_G_CONTROL_BYTES_AND_EMPTY_UNDERLAY' and type(l['owned_command_count']) is int and l['owned_command_count']==1 and len(v['command_receipts'])==1,'Mount terminal/count differs')
        native=[R.native(d/'commands','gdrive',BOOT)];R.require(native[0]['argv']==MOUNT,'Native mount argv differs')
        receipt=v['command_receipts'][0]
        for key,suffix in (('launch_sha256','launch.json'),('closure_sha256','closure.json'),('command_sha256','command.json')):R.require(receipt[key]==R.sha(d/'commands'/('gdrive.'+suffix)),'Native result byte join differs')
        gm=l['g_mount'];R.require(gm['filesystem']=='9p' and gm['source']=='G:' and gm['mountpoint']=='/mnt/g' and gm['root']=='/' and 'aname=drvfs;path=G:;' in gm['super_options'],'Mounted exact G DrvFS route differs')
        R.require(l['linux_control_sha256']==CONTROL and l['linux_empty_mount_underlay']['entries']==[] and l['linux_empty_mount_underlay']['path']=='/mnt/g' and l['linux_g_underlay']['entries']==[] and l['linux_g_underlay']['path']==q['linux_root']+'/.work/stage05_atomic_v1','Linux exact controls or empty underlay differs')
    else:
        R.require(l['state']==v['linux_state']=='PASS_DIAGNOSIS_G_DRIVE_NOT_MOUNTED_NO_REPAIR' and type(l['owned_command_count']) is int and l['owned_command_count']==0 and v['command_receipts']==[],'Diagnosis performed unexpected native actions')
    for leaf in ('admission.json','latest_admission.json'):
        a=R.read(d/leaf);R.require(a['admitted'] is True and a['windows_disks_sufficient'] is True,'Resource admission failed')
        lease=a['windows_owner_lease'];R.lock(lease['workflow_lock'])
        R.require(lease['workflow_lock_held'] is True and lease['nonce']==q['owner_nonce'] and lease['owner_pid']==owner['pid'] and int(lease['owner_creation_filetime'])==int(owner['creation_filetime']),'Admitted original-owner lease differs')
    resources=v['latest_actual_resources'];R.require(resources['physical_available_bytes']>=1879048192 and resources['commit_headroom_bytes']>=1879048192 and all(n>=10737418240 for n in resources['disk_available_bytes'].values()),'Final unchanged resource guard differs')
    unlock=R.read(d/'lock_released.json');R.require(unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['released'] is True,'Original explicit unlock absent')
    R.require(v['retained_client_handle_closed'] is True and v['original_unlock_receipt_proven'] is True and v['owned_stop_cleared_after_unlock'] is True and v['lock_release_receipt_sha256']==R.sha(d/'lock_released.json'),'Checked retained-client handle/unlock receipt/STOP ordering facts differ')
    R.require(not (d/'publication_failure.json').exists() and not any(k in v for k in ('lease_finalizer_error','closure_finalizer_error','client_close_error','log_finalizer_error','unlock_or_receipt_error_kind','stop_finalizer_error_kind','final_result_persistence_error_kind')),'Actual finalizer or publication failure exists')
    R.require(datetime.datetime.fromisoformat(unlock['utc'])<=datetime.datetime.fromisoformat(v['utc']),'Final PASS predates explicit unlock')
    for p in sorted(d.rglob('*')):
        if p.is_file():R.data(p)
    return {'spool':name,'result_sha256':R.sha(d/'result.json'),'linux_terminal_sha256':v['linux_terminal_sha256'],'unlock_sha256':R.sha(d/'lock_released.json'),'unlock_utc':unlock['utc'],'owner_creation_filetime':owner['creation_filetime'],'owner_nonce':q['owner_nonce'],'linux_state':l['state'],'mount_performed':mount,'session_parent_initial_and_final_verified':True,'native_commands':native,'retained_wsl_exit_code':0}

def main():
    out=W/'stage5_gdrive_postfallback_actual_pair_independent_review01.json'
    R.require(not out.exists(),'Fresh independent report required')
    report={'schema':'STAGE05_GDRIVE_ACTUAL_PAIR_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_READBACK','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only decoded actual receipts and exact SHA256; no WSL, UNC, process, registry, lock, network, Git or producer imports','scientific_adoption':False,'future_storage_and_UNC_visibility':'REQUIRES_SEPARATE_FRESH_GATES'}
    try:
        R.require(R.sha(W/'review_stage5_postboot_gate.py')=='d6f06b442c2a8be35bb4779355c99d61e9de72314215c02e3165c2dfd235a161','Pure common reviewer differs')
        R.require(R.sha(W/'stage5_gdrive_view_postfallback_checked_unlock.py')==SOURCE,'G source drift')
        peer=R.pinned(W/'stage5_gdrive_postfallback_derived_source_independent_review01.json','5e0685a028df2645cd8fb43051e0f99432aa354412f8371dd7081b54f35e8525')
        R.require(peer['state'].startswith('PASS_'),'Published source peer differs')
        pub=R.read(W/'master_interopg72_remote_readback.json');R.require(pub['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and pub['expected_commit']=='1e51327a36cc6c1fff655ea3c533797288c9726e' and pub['verified_files']==pub['required_files'],'Source remote readback differs')
        selected=[p for p in pub['files'] if p['path'].endswith('/stage5_gdrive_view_postfallback_checked_unlock.py')]
        R.require(len(selected)==1 and selected[0]['sha256']==SOURCE and selected[0]['actual_remote_bytes_read'] is True and selected[0]['sha256_verified'] is True,'Exact G source not published')
        boot=R.pinned(W/'master_newboot_reconciliation_actual01.json','07a6546d3100bd979884b5a1e4d0c44952a4fc3cdd5a020087d4bbbc5e6d8cf3')
        stamp=datetime.datetime.fromisoformat(boot['current_boot']['last_boot_utc']);ft=int((stamp-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10_000_000)
        details=[run_one(n,i==1,ft) for i,n in enumerate(SPOOLS)]
        stamp=datetime.datetime.fromisoformat(details[0]['unlock_utc']);released=int((stamp-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10_000_000)
        R.require(released<details[1]['owner_creation_filetime'],'Diagnosis did not explicitly unlock before separate mount owner')
        R.require(details[0]['owner_nonce']!=details[1]['owner_nonce'],'Pair owner nonce reused')
        R.require(not Path(R.read(W/SPOOLS[-1]/'result.json')['workflow_lock']['path']).with_name('stage05_owned_closure_unproven.json').exists(),'Current closure STOP remains')
        report.update(state='PASS_CURRENT_BOOT_G_DIAGNOSIS_AND_EXACT_MOUNT_CHECKED_UNLOCK_CLOSED',source_sha256=SOURCE,linux_boot_id=BOOT,source_publication_commit=pub['expected_commit'],detail=details,old_failed_scopes_preserved=True,original_lock_explicitly_released=True,owned_closure_proven=True,unknown_closure_stop_preserved=False)
    except BaseException as e:report['error']={'kind':type(e).__name__,'message':str(e)}
    report['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'state':report['state'],'error':report.get('error'),'checked_files':len(R.CHECKED),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
    return 0 if report['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
