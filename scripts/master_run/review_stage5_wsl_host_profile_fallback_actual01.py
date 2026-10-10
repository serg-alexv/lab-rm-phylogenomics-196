"""C-only completed Windows host-profile repair review; no runtime operations."""
from pathlib import Path
import ast, datetime, hashlib, json, stat
import review_stage5_postboot_gate as R

WORK=Path(__file__).resolve().parent
SPOOL=WORK/'stage5_wsl_host_profile_fallback_ca17dc8e11c64357be0186b01a93439a'
OUT=WORK/'stage5_wsl_host_profile_fallback_actual01_independent_review.json'
SOURCE='49596d3e9c0ef684978d0cbb05bc57d97b100f08ab77a7a4ece598abc2221299'
COMMIT='fd0a30e46bd9e64f17a4b00c7dcdd76852bf04b6'
BEFORE='df394745d9cc85d8f4340e10b4620711b1ee497cadfb74199bb59288abc967db'
AFTER='e48eaf30b4da7cf75ec717f7a643235efbb9561f5e1680480ae14314f046d6e4'
PHASES=['census_before','census_before_shutdown','shutdown','running_after','census_after_shutdown']
TIMEOUTS=[25,25,60,20,25]
PS=r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'

def filetime(iso):
    stamp=datetime.datetime.fromisoformat(iso.replace('Z','+00:00'))
    return int((stamp-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10000000)

def main():
    R.require(not OUT.exists(),'Fresh independent actual report required')
    report={'schema':'STAGE05_WSL_HOST_PROFILE_FALLBACK_ACTUAL_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_ACTUAL_REVIEW',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'spool':str(SPOOL),
      'reviewer_source_sha256':R.sha(Path(__file__)),
      'method':'Only explicit bounded plain C source/receipt bytes and SHA256; no producer imports, host profile/registry/UNC/WSL access, signals, locks or ref mutation'}
    try:
        peer=R.pinned(WORK/'stage5_wsl_host_profile_fallback_source_independent_review01.json','ec87ef3d1ae54d86a5281996f4cbd5c7d911f3d50f73b0158069c10fc565b11a')
        R.require(peer['state']=='PASS_SOURCE_ONLY_BOUNDED_3584MB_GUI_OFF_FALLBACK_ACTUAL_NOT_RUN' and peer['checked_files']['stage5_wsl_host_profile_fallback_owner.py']['sha256']==SOURCE,'Frozen source peer differs')
        for name,row in peer['checked_files'].items():R.require(R.sha(WORK/name)==row['sha256'] and len(R.data(WORK/name))==row['bytes'],'Peer accepted source/evidence drift')
        publication=R.read(WORK/'master_readiness67_remote_readback.json')
        R.require(publication['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and publication['expected_commit']==COMMIT
          and publication['initial_remote_main']==publication['final_remote_main']==COMMIT
          and publication['required_files']==publication['verified_files']==28 and publication['failures']==[],'Source publication/readback differs')
        published=[r for r in publication['files'] if r['path']=='scripts/master_run/stage5_wsl_host_profile_fallback_owner.py']
        R.require(len(published)==1 and published[0]['sha256']==SOURCE and published[0]['actual_remote_bytes_read'] is True,'Published source bytes differ')
        owner=R.read(SPOOL/'result.json');unlock=R.read(SPOOL/'lock_released.json');intent=R.read(SPOOL/'profile_replace_intent.json')
        R.require(owner['schema']=='STAGE05_WSL_HOST_PROFILE_FALLBACK_WINDOWS_OWNER_RESULT_V1'
          and owner['state']=='PASS_NONSCIENTIFIC_WINDOWS_HOST_PROFILE_CHANGED_AND_ALL_DISTROS_STOPPED'
          and owner['scope']=='NONSCIENTIFIC_WINDOWS_WSL_HOST_PROFILE_AND_CONTROLLED_SHUTDOWN_ONLY'
          and owner['source_sha256']==SOURCE and owner['scientific_adoption_authorized'] is False
          and owner['owned_closure_proven'] is True and owner['original_lock_explicitly_released'] is True
          and owner['unknown_closure_stop_preserved'] is False and owner['automatic_relaunch'] is False
          and owner['effects_preserved_on_failure'] is True and owner['elapsed_seconds']<180
          and owner['log_hash_scope']=='CLOSED_FULL_LOGS','Actual source/scope/closure differs')
        R.lock(owner['workflow_lock']);R.require(owner['workflow_lock']['path']==r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock','Original lock path differs')
        R.require(unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['released'] is True
          and filetime(unlock['utc'])<=filetime(owner['utc']) and owner['original_unlock_receipt_proven'] is True
          and owner['owned_stop_cleared_after_unlock'] is True and owner['lock_release_receipt_sha256']==R.sha(SPOOL/'lock_released.json'),'Explicit original unlock differs')
        R.require(owner['base_source_sha256']==R.sha(WORK/'stage5_wsl_config_owner.py')
          and owner['framework_source_sha256']==R.sha(WORK/'stage5_gdrive_view_session.py'),'Actual frameworks drift')
        for name,pin in owner['source_pins'].items():R.require(R.sha(WORK/name)==pin,'Actual imported source differs')
        closed=R.pinned(WORK/'stage5_first_capacity02_closed_independent_review.json','e7cb6737c50e35c3119fe443d820b77174b2e0b8f3560c5303837b95e42ac2e9')
        R.require(closed['state']=='PASS_CAPACITY02_NATURAL_ADMISSION_DEFER_NO_NATIVE_SCOPE_CLOSED_AND_ORIGINAL_UNLOCK'
          and closed['owned_closure_proven'] is True and closed['original_lock_explicitly_released'] is True
          and closed['native_launch_count']==0 and closed['no_native_launch_in_this_invocation'] is True
          and closed['actual_boot_id']=='f0ffcebc-4901-479d-9559-89d45e9cfa38'
          and owner['capacity02_closure_peer_sha256']==R.sha(WORK/'stage5_first_capacity02_closed_independent_review.json')
          and owner['capacity02_closure_files']==closed['checked_files'] and owner['capacity02_state_preserved']=='DEFERRED_RESOURCE',
          'Exact actual current capacity02 closed prerequisite differs')
        for name,item in closed['checked_files'].items():
            R.require(R.sha(WORK/name)==item['sha256'] and len(R.data(WORK/name))==item['bytes'],'Actual capacity02 captured evidence changed')
        closure_publication=R.read(WORK/'master_previewclosed69_v2_remote_readback.json')
        R.require(closure_publication['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED'
          and closure_publication['expected_commit']=='13a847843077b9f399f76f86e734ce7720debe9d'
          and closure_publication['required_files']==closure_publication['verified_files']==65
          and closure_publication['failures']==[],'Current closure69 full publication differs')
        closure_rows=[row for row in closure_publication['files'] if row['path'].endswith('/stage5_first_capacity02_closed_independent_review.json')]
        R.require(len(closure_rows)==1 and closure_rows[0]['sha256']==owner['capacity02_closure_peer_sha256']
          and closure_rows[0]['actual_remote_bytes_read'] and closure_rows[0]['sha256_verified'],'Published closure peer differs')
        nonce=owner['owner_nonce'];before=R.data(SPOOL/'wslconfig.before.txt');expected=R.data(SPOOL/'wslconfig.after.expected.txt');actual=R.data(SPOOL/'wslconfig.after.actual.txt')
        R.require(before==R.data(WORK/'stage5_wsl_host_profile_before_fallback01.txt') and len(before)==681
          and expected==actual==before.replace(b'memory=3GB\n',b'memory=3584MB\n').replace(b'guiApplications=true\n',b'guiApplications=false\n')
          and len(actual)==685 and R.sha(SPOOL/'wslconfig.before.txt')==owner['preimage_sha256']==BEFORE
          and R.sha(SPOOL/'wslconfig.after.actual.txt')==owner['actual_after_sha256']==owner['expected_after_sha256']==AFTER
          and sum(a!=b for a,b in zip(before.splitlines(),actual.splitlines()))==2,'Exact two-line durable backup/replacement differs')
        R.require(owner['profile_replaced'] is True and owner['profile_path']==r'C:\Users\wheel\.wslconfig'
          and intent['owner_nonce']==nonce and intent['before']==owner['profile_before_identity']
          and intent['before_sha256']==BEFORE and intent['after_sha256']==AFTER
          and intent['staging_path']==owner['staging_path']==r'C:\Users\wheel\.wslconfig.lab_rm_'+nonce+'.tmp'
          and intent['durable_backup']=='wslconfig.before.txt','Atomic replacement intent/identity differs')
        for key,size in (('profile_before_identity',681),('profile_after_identity',685)):
            identity=owner[key];R.require(identity['bytes']==size and identity['nlink']==1
              and stat.S_ISREG(identity['mode']) and not identity['attributes']&0x400,'Profile regular/single-link metadata differs')
        R.require(owner['profile_before_identity']['device']==owner['profile_after_identity']['device']
          and owner['profile_before_identity']['mode']==owner['profile_after_identity']['mode']
          and owner['profile_before_identity']['inode']!=owner['profile_after_identity']['inode'],'Atomic identity or mode preservation differs')
        R.require(owner['windows_before']==owner['windows_after'] and owner['windows_before']['empty_g_underlay']['entries']==[]
          and owner['windows_before']['control_sha256']['status/run_control.json']=='c4184e2af9ea0ef81f652d4d1baed00b9742fa2a3efdb9fe87491911ab2242cd','Windows authority/underlay drift')
        R.require(owner['registry_before']==owner['registry_after_shutdown']=={
          'DistributionName':'Ubuntu','Version':2,'DefaultUid':0,'Flags':15,
          'BasePath':r'C:\Users\wheel\AppData\Local\wsl\{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}'},'Exact Ubuntu UID0 registration changed')
        registration=owner['registered_backing_before'];R.require(registration['registry_key']=='{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}'
          and registration['vhd_metadata']['payload_read'] is False,'Registration image metadata-only boundary differs')
        tree=ast.parse(R.data(WORK/'stage5_wsl_config_owner.py'))
        census=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='census_argv')
        script=next(n.value for n in ast.walk(census) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith("$ErrorActionPreference='Stop'"))
        census_argv=[PS,'-NoLogo','-NoProfile','-NonInteractive','-Command',script.replace('OWNER_PID',str(owner['actual_owner']['pid'])).replace('-Depth6','-Depth 6')]
        R.require([r['phase'] for r in owner['commands']]==PHASES,'Fixed retained phase order differs')
        previous=owner['actual_owner']['creation_filetime'];R.require(filetime(publication['finished_utc'])<previous
          and filetime(closure_publication['finished_utc'])<previous,'Actual owner predates full source or current closure publication readback')
        clients=[]
        for row,phase,timeout in zip(owner['commands'],PHASES,TIMEOUTS):
            launched=R.read(SPOOL/(phase+'.launch.json'));exit_row=R.read(SPOOL/(phase+'.exit.json'));launch_intent=R.read(SPOOL/(phase+'.intent.json'))
            R.require(exit_row==row and launched['birth']==row['birth'] and launched['argv']==row['argv']
              and launched['phase']==launch_intent['phase']==phase and launch_intent['argv']==row['argv']
              and launch_intent['timeout_seconds']==timeout and launched['owner_nonce']==launch_intent['owner_nonce']==row['owner_nonce']==nonce,'Retained phase lifecycle joins differ')
            birth,end=row['birth'],row['terminal'];image=PS if phase.startswith('census') else R.WSL
            R.terminal(birth,end,previous,code=0,image=image)
            R.require(birth['creation_filetime']>previous and birth['exited'] is False and end['session_id']==owner['actual_owner']['session_id'],'Nonsequential retained birth/session differs')
            elapsed=(end['exit_filetime']-birth['creation_filetime'])/10000000;R.require(elapsed<=timeout,'Retained phase exceeded fixed timeout')
            previous=end['exit_filetime'];clients.append({'phase':phase,'birth':birth,'exit':end,'elapsed_seconds':elapsed})
            R.require(R.data(SPOOL/(phase+'.stderr.txt'))==b'','Unexpected maintenance stderr')
            if phase.startswith('census'):
                R.require(row['argv']==census_argv,'Census argv differs from frozen no-external-command source')
                value=R.read(SPOOL/(phase+'.stdout.txt'));R.require(value==owner[phase] and value['selected']==value['helpers']==[]
                  and len(value['tasks'])==len({x['name'] for x in value['tasks']})==18
                  and all(x['name'].startswith('LAB_RM_') and x['state']=='Disabled' for x in value['tasks']),'Census competing jobs/tasks differ')
            else:R.require(row['argv']==([R.WSL,'--shutdown'] if phase=='shutdown' else [R.WSL,'--list','--running','--quiet']),'Unexpected maintenance WSL argv')
        R.require(previous<=filetime(unlock['utc']),'Original unlock predates final retained client exit')
        R.require(owner['memory_maximum_bytes']==3758096384 and owner['gui_applications'] is False,'Actual reviewed fallback fields differ')
        R.require(not (SPOOL/'publication_failure.json').exists() and not Path(owner['workflow_lock']['path']).with_name('stage05_owned_closure_unproven.json').exists(),
          'Publication uncertainty or current owned-closure STOP vetoes adoption')
        R.require(R.data(SPOOL/'running_after.stdout.txt')==b'' and owner['running_after']['decoded_names']==[]
          and owner['running_after']['stdout_bytes']==0 and owner['running_after']['stdout_sha256']==R.sha(SPOOL/'running_after.stdout.txt'),'No-running-distros retained query differs')
        R.require(owner['old_linux_boot_id']=='f0ffcebc-4901-479d-9559-89d45e9cfa38'
          and owner['new_linux_boot']=='NOT_OBSERVED_NO_RELAUNCH' and owner['old_boot_runtime_proofs_reusable'] is False,'Fresh boot required boundary differs')
        lease=R.read(SPOOL/'owner_lease.json');R.require(lease['nonce']==nonce and lease['workflow_lock']==owner['workflow_lock']
          and lease['owner_pid']==owner['actual_owner']['pid'] and int(lease['owner_creation_filetime'])==owner['actual_owner']['creation_filetime']
          and lease['expires_unix']-lease['measured_unix']==3,'Maintenance lease identity/window differs')
        resources=owner['latest_actual_resources'];R.require(resources['physical_available_bytes']==lease['windows_available_bytes']>=1610612736
          and resources['commit_headroom_bytes']==lease['windows_commit_headroom_bytes']>=1610612736
          and min(resources['disk_available_bytes'].values())>=10737418240,'Fresh maintenance reserve differs')
        R.require(not (SPOOL/'linux_terminal.json').exists() and not (SPOOL/'commands').exists(),'Unexpected Linux/native route evidence')
        R.require(set(owner['closed_log_sha256'])=={p.name for p in SPOOL.glob('*.txt')},'Closed log exact membership differs')
        for name,pin in owner['closed_log_sha256'].items():R.require(R.sha(SPOOL/name)==pin,'Closed log hash drift')
        for path in SPOOL.iterdir():
            R.require(path.is_file(),'Unexpected actual spool member');R.data(path)
        report.update(state='PASS_EXACT_HOST_PROFILE_BACKUPS_RETAINED_CLIENTS_REGISTRY_AND_STOPPED_QUERY_NEW_BOOT_GATES_PENDING',
          source_sha256=SOURCE,source_publication_commit=COMMIT,source_publication_readback_files=28,
          source_publication_method='Independently hashed C source plus root full remote byte readback receipt; this reviewer performed no new network read',
          actual_result_sha256=R.sha(SPOOL/'result.json'),owner_elapsed_seconds=owner['elapsed_seconds'],retained_clients=clients,
          profile_before_sha256=BEFORE,profile_after_sha256=AFTER,memory_maximum_bytes=3758096384,gui_applications=False,two_lines_changed_only=True,profile_bytes_before=681,profile_bytes_after=685,
          capacity02_state='DEFERRED_RESOURCE_NO_NATIVE_PREPARED_DATA_BYTE_IDENTICAL_PRESERVED',original_lock_identity=owner['workflow_lock'],
          original_explicit_unlock=True,original_unlock_receipt_readback_proven=True,owned_STOP_cleared_after_checked_unlock=True,owned_closure_proven=True,unknown_closure_STOP_absent_recorded=True,
          exact_Ubuntu_UID0_preserved=True,all18tasks_disabled_three_censuses=True,running_distro_names=[],
          Linux_worker_route='NONE_IN_FROZEN_OWNER_NO_LINUX_TERMINAL_OR_NATIVE_SPOOL',new_linux_boot='NOT_OBSERVED_NO_RELAUNCH',
          old_boot_sensitive_proofs_reusable=False,
          closure_boundary='All five exact retained Windows clients exited0 sequentially; fixed PowerShell census uses cmdlets with no external commands. No generic named-Job descendant claim. Final positive3s lease is a historical snapshot; explicit unlock and closed result govern closure.',
          resource_benefit='NOT_YET_QUALIFIED_AFTER_RESTART; 3584MB is maximum, not an assumed512MB additional resident host cost; actual capacity must be measured',
          required_next='Publish/readback this completed repair; freshly qualify toolchain08/runtime09/interop06/G08/storage07/DriveFS05/UNC05 under new boot. Keep all original native resource thresholds and reviewed3584MB maximum, GUI false and measured actual capacity.',
          scientific_stage5='PREPARED_DEFERRED_NO_NATIVE_SEARCH',accepted_stage4='PRESERVED',review_actions={'WSL_launches':0,'UNC_reads':0,'profile_reads_or_writes':0,'registry_accesses':0,'locks':0,'Git_ref_writes':0})
    except BaseException as error:report['error']={'kind':type(error).__name__,'message':str(error)}
    report['checked_files']=R.CHECKED
    with OUT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':report['state'],'output':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
      'checked_files':len(R.CHECKED),'error':report.get('error')}))
    return 0 if report['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
