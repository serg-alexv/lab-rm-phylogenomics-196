"""Default NOOP. Independent C-only review of the published storage recovery pair.

No producer imports, WSL, native handles, network, locks or original-file writes.
"""
from pathlib import Path
import argparse, datetime, hashlib, importlib.util, json, stat

WORK=Path(__file__).resolve().parent
GENERIC_SHA='d6f06b442c2a8be35bb4779355c99d61e9de72314215c02e3165c2dfd235a161'
_generic_path=WORK/'review_stage5_postboot_gate.py'
if hashlib.sha256(_generic_path.read_bytes()).hexdigest()!=GENERIC_SHA:
    raise ValueError('Pinned pure generic gate reader differs before import')
_spec=importlib.util.spec_from_file_location('_storage_recovery_generic_d6f06',_generic_path)
G=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(G)
if hashlib.sha256(_generic_path.read_bytes()).hexdigest()!=GENERIC_SHA:
    raise ValueError('Pinned pure generic gate reader changed during import')
WINDOWS='stage5_setup_storage_recovery_windows.py'
LINUX='stage5_setup_storage_recovery_linux.py'
WINDOWS_SHA='bdc7b95781950be54bd339c483f31bb8462b5b41ad76bbe21bb5fe37ccdcb7fa'
LINUX_SHA='edac2a12a8b1a72d2224264ad4913a79677168dc233ca796c733112b8e32fd8a'
SOURCE_REVIEW='stage5_storage_prepared_recovery_source_independent_review01.json'
SOURCE_REVIEW_SHA='d395278a500c49ba4e0c545a017229b419e2b8e3d49eb07edecbf5275245d76f'
SNAPSHOT='stage5_capacity02_closed_native_copy/snapshot.json'
SNAPSHOT_SHA='451c91caaf07d441452c4fccfaf3dfab5c488ee2b8b9988ee35cb0ceb9ac0f51'
CLOSURE_REVIEW='stage5_first_capacity02_closed_independent_review.json'
CLOSURE_SHA='e7cb6737c50e35c3119fe443d820b77174b2e0b8f3560c5303837b95e42ac2e9'
ACCESSION='GCF_000009425.1'
UUID='3370e495-79b5-4136-9c6b-d31c7cb6a6be'
INODE=33554542
OLD_BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
require=G.require
data=G.data
sha=G.sha
read=G.read
pinned=G.pinned
cpath=G.cpath
lock=G.lock
terminal=G.terminal
native=G.native


def source_review(expected):
    require(expected==SOURCE_REVIEW_SHA,
            'Explicit published source-review SHA required')
    peer=pinned(WORK/SOURCE_REVIEW,expected)
    require(peer['state']=='PASS_SOURCE_ONLY_PRESERVED_PREPARED_BACKING_RECOVERY_PAIR_ACTUAL_NOT_RUN' and isinstance(peer['checked_files'],dict),
            'Independent source-only recovery pair acceptance required')
    for name,pin in ((WINDOWS,WINDOWS_SHA),(LINUX,LINUX_SHA)):
        require(peer['checked_files'][name]['sha256']==pin and sha(WORK/name)==pin
                and peer['checked_files'][name]['bytes']==len(data(WORK/name)),'Exact reviewed storage recovery source differs')
    return peer


def recovery_join(before,after,proof,snapshot):
    require(before==after and before['state']=='PASS_EXACT_PREPARED_BACKING_CONTENTS_PRESERVED_FRESH_LINUX_OBSERVATION'
            and before['snapshot_sha256']==SNAPSHOT_SHA and before['closure_peer_sha256']==CLOSURE_SHA,
            'Independent before/after full recovery preservation join differs')
    require(before['old_boot_id']==OLD_BOOT and before['new_boot_id']==proof['boot_id']!=OLD_BOOT
            and before['filesystem_uuid']==proof['filesystem_uuid']==UUID
            and before['directory_inode']==proof['directory_inode']==INODE
            and before['fresh_directory_device']==proof['directory_device'], 'Fresh recovery boot/ext4 identity differs')
    for key in ('deletions','moves','detector_launches'):
        require(type(before[key]) is int and before[key]==0,'Recovery performed an out-of-scope content/science action')
    root=before['fresh_directory_metadata']
    require(all(type(root[k]) is int for k in ('uid','gid','mode','nlink')) and stat.S_ISDIR(root['mode']),
            'Fresh root POSIX metadata required')
    inventory=snapshot['backing_inventory'];names=[item['member'] for item in inventory]
    require(len(inventory)==52 and len(set(names))==52 and names==sorted(names)
            and {name.split('/')[0] for name in names}=={'.native_runner.guard',ACCESSION}
            and [name[len(ACCESSION)+1:] for name in names if name.startswith(ACCESSION+'/')]==snapshot['members'],
            'Exact complete approved52-object/50-member baseline differs')
    actual=before['members'];require(set(actual)==set(names),'Prepared full current membership differs')
    total=0
    for item in inventory:
        name=item['member'];row=actual[name]
        require(row['kind']==item['kind'] and all(type(row[k]) is int for k in ('device','inode','uid','gid','mode','nlink'))
                and row['device']==proof['directory_device'] and type(item['windows_unc_inode_projection']) is int
                and row['inode']==item['windows_unc_inode_projection'],'Fresh object identity/type/device differs')
        if row['kind']=='file':
            require(stat.S_ISREG(row['mode']) and row['nlink']==1 and type(row['bytes']) is int
                    and row['bytes']==item['bytes'] and row['sha256']==item['sha256'],'Prepared regular file bytes/hash changed')
            total+=row['bytes']
        else:require(row['kind']=='directory' and stat.S_ISDIR(row['mode']),'Prepared directory is not a fresh plain directory')
    require(type(before['file_bytes_read']) is int and before['file_bytes_read']==total<=128*1024**2,
            'Complete file hashing count/bound differs')
    return {'snapshot_sha256':SNAPSHOT_SHA,'closure_peer_sha256':CLOSURE_SHA,'members':52,'genome_members':50,
            'filesystem_uuid':UUID,'directory_inode':INODE,'file_bytes':total,'prepared_content_preserved':True,
            'prior_metadata_scope':'Windows UNC projection only; actual fresh Linux metadata separately observed'}


def storage(directory,value,authority,boot_filetime,requested_boot):
    """Original generic setup checks retained; only paired source selection changes."""
    kind='storage';setup_sha=WINDOWS_SHA;linux_sha=LINUX_SHA
    require(value['state']=='PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK' and value['step']==kind
            and value['source_sha256']==setup_sha and value['linux_source_sha256']==linux_sha
            and value['owned_closure_proven'] is True and value['unknown_closure_stop_preserved'] is False,'Actual setup success/source/closure differs')
    for name,pin in value['source_pins'].items():require(sha(WORK/name)==pin,'Setup actual source dependency differs')
    lock(value['workflow_lock']);held=read(directory/'actual_owner_lock.json');lock(held['workflow_lock'])
    require(held['owner']==value['actual_windows_owner'] and held['owner_nonce']==value['owner_nonce'],'Actual setup owner lock differs')
    require(value['actual_windows_owner']['executable']==G.PYTHON and int(value['actual_windows_owner']['creation_filetime'])>=boot_filetime,'Setup Windows owner image/boot differs')
    launch=read(directory/'launch.json');client=pinned(directory/'wsl_exit.json',value['wsl_exit_receipt_sha256'])
    require(client['owner_nonce']==launch['owner_nonce']==value['owner_nonce'] and client['step']==kind
            and client['source_sha256']==setup_sha and client['linux_source_sha256']==linux_sha
            and client['argv']==launch['argv'],'WSL receipt source/argv/nonce differs')
    require(client['birth']==launch['native_wsl_client'] and client['terminal']==value['actual_wsl_exit'],'WSL retained evidence differs')
    terminal(client['birth'],client['terminal'],boot_filetime)
    require(client['stdout_sha256']==sha(directory/'wsl.stdout.txt') and client['stderr_sha256']==sha(directory/'wsl.stderr.txt'),'WSL stream hashes differ')
    linux=pinned(directory/'linux_terminal.json',value['linux_terminal_sha256']);boot=linux['bootstrap']['boot_id']
    require(boot!=G.OLD_LINUX_BOOT and boot!=OLD_BOOT and requested_boot==boot,'Stale or inconsistent requested Linux boot')
    require(linux['state']=='PASS_NONSCIENTIFIC_SETUP_STEP' and linux['step']==kind and linux['source_sha256']==linux_sha
            and linux['owner_nonce']==value['owner_nonce'] and linux['owned_closure_proven'] is True
            and linux['remaining_direct_children']==[],'Linux bootstrap terminal differs')
    count=linux['owned_command_count'];paths=list((directory/'commands').glob('*.launch.json'))
    require(type(count) is int and count==len(paths) and count in (0,1),'Bounded native accounting differs')
    commands=[native(directory/'commands',p.name.removesuffix('.launch.json'),boot) for p in paths]
    for command in commands:
        require(command['label']=='bind_storage' and command['argv']==['/usr/bin/mount','--bind','/var/tmp/lab_rm_stage05_atomic_v1',
                '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/.work/stage05_atomic_v1'],'Only original exact bind command is accepted')
    candidate=cpath(linux['candidate_path']);proof=pinned(candidate,linux['candidate_sha256'])
    require(proof['boot_id']==boot and proof['target_mount']['filesystem']=='ext4' and linux['storage']==proof
            and value['g_underlay_before']==value['g_underlay_after'],'Storage candidate/underlay differs')
    require(proof['helper_sha256']==G.source('stage5_work_storage.py',authority)
            and proof['canonical_target']=='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/.work/stage05_atomic_v1'
            and proof['backing']=='/var/tmp/lab_rm_stage05_atomic_v1','Unchanged exact W7e06 storage roles required')
    snapshot=pinned(WORK/SNAPSHOT,SNAPSHOT_SHA);closure=pinned(WORK/CLOSURE_REVIEW,CLOSURE_SHA)
    require(closure['owned_closure_proven'] is True and closure['original_lock_explicitly_released'] is True
            and closure['native_launch_count']==0 and closure['actual_boot_id']==OLD_BOOT
            and closure['snapshot_receipt_sha256']==SNAPSHOT_SHA,'Closed previous detector-free scope differs')
    preservation=recovery_join(linux['prepared_backing_recovery_before'],linux['prepared_backing_recovery_after'],proof,snapshot)
    unlock=read(directory/'lock_released.json')
    require(value['original_lock_explicitly_released'] is True and value['original_unlock_receipt_proven'] is True
            and value['owned_stop_cleared_after_unlock'] is True and value['lock_release_receipt_sha256']==sha(directory/'lock_released.json')
            and unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['released'] is True,
            'Checked original unlock/durable receipt/owned STOP ordering not proven')
    require(not (directory/'publication_failure.json').exists()
            and not any(k in value for k in ('lease_finalizer_error','closure_finalizer_error','handle_close_error',
                        'outer_finalizer_error','unlock_or_receipt_error_kind','stop_finalizer_error_kind',
                        'final_result_persistence_error_kind','publication_failure_persistence_error_kind'))
            and datetime.datetime.fromisoformat(value['utc'])>=datetime.datetime.fromisoformat(unlock['utc']),
            'Finalizer/publication failure or result-before-unlock ordering differs')
    lease=read(directory/'owner_lease.json');lock(lease['workflow_lock'])
    require(lease['nonce']==value['owner_nonce'] and lease['workflow_lock_held'] is False
            and lease['expires_unix']==lease['measured_unix'] and lease['owner_pid']==value['actual_windows_owner']['pid']
            and lease['owner_creation_filetime']==str(value['actual_windows_owner']['creation_filetime'])
            and datetime.datetime.fromisoformat(lease['utc'])<=datetime.datetime.fromisoformat(unlock['utc']),
            'Final original lease was not invalidated before unlock')
    return {'linux_boot_id':boot,'native_commands':commands,'candidate_path':str(candidate),'candidate_sha256':sha(candidate),
            'prepared_backing_recovery':preservation,'checked_original_unlock_receipt':True}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--review',action='store_true')
    for name in ('spool','output','boot-receipt'):p.add_argument('--'+name,type=Path)
    for name in ('boot-receipt-sha256','authority-report-sha256','linux-boot-id','source-review-sha256'):p.add_argument('--'+name)
    a=p.parse_args()
    if not a.review:print(json.dumps({'state':'PREPARED_NOT_RUN','scope':'C_ONLY_STORAGE_RECOVERY_INDEPENDENT_REVIEW','actual_storage_recovery':'NOT_RUN'}));return 0
    require(all(getattr(a,name) is not None for name in ('spool','output','boot_receipt','boot_receipt_sha256','authority_report_sha256','linux_boot_id','source_review_sha256')),'Explicit current completed scope/pins required')
    require(not a.output.exists() and a.output.parent==WORK,'Fresh direct C work review required')
    result={'schema':'STAGE05_POSTBOOT_COMPLETED_GATE_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_GATE_READBACK','kind':'storage',
            'source_sha256':sha(Path(__file__)),'spool':str(a.spool),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'readonly_method':'Original pinned d6f06 closure helpers plus independent prepared-recovery joins; C-only standard-library reads',
            'scientific_execution_or_acceptance':'NONE_NONSCIENTIFIC_GATE_ONLY','old_scope_retroactively_passed':False}
    try:
        require(sha(WORK/'review_stage5_postboot_gate.py')==GENERIC_SHA,'Original generic helper source drift')
        source_review(a.source_review_sha256)
        authority=pinned(WORK/'postboot_authority_review01.json',a.authority_report_sha256)
        require(authority['state']=='PASS_CURRENT_AUTHORITY_AND_LOCAL_PUBLISHED_SOURCES' and authority['initial_remote_main']==authority['final_remote_main'],'Original authority report differs')
        boot=pinned(a.boot_receipt,a.boot_receipt_sha256)
        require(boot['state']=='PASS_NEW_BOOT_CURRENT_SCOPE_RECONCILED_OLD_FAILURE_PRESERVED' and boot['old_scope_retroactively_passed'] is False
                and boot['old_STOP_removed'] is True and boot['original_lock_released'] is True,'Original boot reconciliation differs')
        last=datetime.datetime.fromisoformat(boot['current_boot']['last_boot_utc'])
        filetime=int((last-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10_000_000)
        value=read(a.spool/'result.json');detail=storage(a.spool,value,authority,filetime,a.linux_boot_id)
        result.update(state='PASS_COMPLETED_POSTBOOT_GATE_EXACT_SOURCE_CLOSURE_AND_BYTES',authority_commit=authority['final_remote_main'],
                      new_windows_boot=boot['current_boot']['last_boot_utc'],boot_receipt_sha256=a.boot_receipt_sha256,
                      storage_source_review_sha256=a.source_review_sha256,actual_result_sha256=sha(a.spool/'result.json'),
                      unlock_sha256=sha(a.spool/'lock_released.json'),detail=detail)
    except BaseException as error:result['error']={'kind':type(error).__name__,'message':str(error)}
    result['checked_files']=dict(G.CHECKED)
    with a.output.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':result['state'],'output':str(a.output),'error':result.get('error'),'checked_files':len(G.CHECKED)}))
    return 0 if result['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
