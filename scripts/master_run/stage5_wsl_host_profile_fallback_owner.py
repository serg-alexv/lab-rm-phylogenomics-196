"""Default NOOP; exact 3.5 GiB Windows WSL fallback and retained shutdown only.

Separate Windows-only adaptation of reviewed WSL config owner4a6b. No Linux
worker, default-user change, sentinel cleanup, relaunch or scientific action.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, stat, subprocess, sys, time, uuid

sys.dont_write_bytecode=True
WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PROFILE=Path(r'C:\Users\wheel\.wslconfig')
BASE_NAME='stage5_wsl_config_owner.py'
BASE_SHA='4a6b42b11d63b7b41cba143cc0c5f5f3e0bf874ef09878ed0c0d6e805226f2bd'
PREIMAGE_NAME='stage5_wsl_host_profile_before_fallback01.txt'
PREIMAGE_SHA='df394745d9cc85d8f4340e10b4620711b1ee497cadfb74199bb59288abc967db'
PRESERVED_SOURCE='stage5_wsl_host_profile_owner.py'
PRESERVED_SHA='3e6c78c08265157b892a341087780f29dee58c5281d41f0fe49f6ff534248232'
CLOSURE_PEER='stage5_first_capacity02_closed_independent_review.json'
CAPACITY_DIR='stage5_owner_GCF_000009425_1_backing_capacity_02'
CAPACITY_NONCE='b54ed1b7012047edb0dcd4b68dc2d10c'
CAPACITY_BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
CAPACITY_PINS={
 'stage5_actual_backing_capacity_02.json':'4c2d9812afd2dbabaa6ba3177395dee17511946966fb3b7491f579cfd3602d63',
 'stage5_windows_backing_owner.py':'296492aa4205f64058846b9901a7bb3a3458f99eda1c7ff388a6e33cdc38b834',
 'stage5_atomic.py':'500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04',
 'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
 'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
 'stage5_owner_lease.py':'add2cbf12ee6d51bb10168b629a8befd2136f58e5194a6e7195fea25002620b8'}
ORIGINAL_LOCK={'path':r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock',
 'volume_serial':2430728143,'file_index':844424932784519,'creation_filetime':134359335921635133,'locked_byte':0}
SCOPE='NONSCIENTIFIC_WINDOWS_WSL_HOST_PROFILE_AND_CONTROLLED_SHUTDOWN_ONLY'
RESERVE=1610612736
FAILED_DIR='stage5_setup_runtime_actual_postiq_07'
FAILED_BOOT='f9be2168-b511-4a09-8f4d-bdb88934c414'
FAILED_PINS={
 'result.json':'62e660a1bc9377e218a62a6edad3a112b1d6a9d9a839e8575bfd9056444c0f4c',
 'lock_released.json':'3b85a42d46b677e1501af5e754bbd241f96bf5daea29488bb7c4eb3cf7a818a1',
 'linux_terminal.json':'22d3c947b7b60aaad56efe547d84826f4a437530543a02bb43d06d43dca4903b',
 'wsl_exit.json':'0c65f06c15b780f8e97a5ef7ff37f718ec0047fe8c0377ba49065be4c9dab026',
 'commands/runtime_discovery.launch.json':'62397247ccb12173a097c630d0f5f47f4341bbc2b6b7032927009f9152d151d7',
 'commands/runtime_discovery.launch_intent.json':'3c1139fb36c9464724e091e346867a7d173acf36317542e4de576eada37b89af',
 'commands/runtime_discovery.closure.json':'f118732ae8b23f8d47b9ce8b20e98cbf87049592ccddc3c32994e5e8384ca00a',
 'commands/runtime_discovery.command.json':'ccd4633eb9b0f6ea5d16df68cfce45ce909694ca34c1e80114b16a9d26d1d693',
 'commands/runtime_discovery.stdout.txt':'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
 'commands/runtime_discovery.stderr.txt':'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}


def need(value,message):
    if not value:raise ValueError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def load_base():
    need(Path(__file__).resolve().parent==WORK,'Exact C source workspace required')
    path=WORK/BASE_NAME
    need(not path.is_symlink() and digest(path.read_bytes())==BASE_SHA,'Reviewed WSL configuration framework differs')
    spec=importlib.util.spec_from_file_location('_wsl_profile_M4a6b',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    need(digest(path.read_bytes())==BASE_SHA,'Reviewed WSL framework changed during import')
    return module


def transform_profile(raw):
    need(isinstance(raw,bytes) and len(raw)==681 and digest(raw)==PREIMAGE_SHA,'Exact681B Windows profile preimage required')
    replacements={('wsl2',b'memory=3GB\n'):b'memory=3584MB\n',
                  ('wsl2',b'guiApplications=true\n'):b'guiApplications=false\n'}
    section=None;seen=set();output=[]
    for line in raw.splitlines(keepends=True):
        heading=line.rstrip(b'\r\n')
        if heading.startswith(b'[') and heading.endswith(b']'):section=heading[1:-1].decode('ascii')
        key=(section,line)
        if key in replacements:
            need(key not in seen,'Duplicate profile target line');seen.add(key);line=replacements[key]
        output.append(line)
    need(seen==set(replacements),'Two exact section-specific profile lines required')
    after=b''.join(output);need(len(after)==685 and after!=raw,'Exact two-line profile transform differs')
    return after


def profile_identity(info):
    return {'device':info.st_dev,'inode':info.st_ino,'bytes':info.st_size,'mode':info.st_mode,
            'nlink':info.st_nlink,'mtime_ns':info.st_mtime_ns,'ctime_ns':info.st_ctime_ns,
            'attributes':getattr(info,'st_file_attributes',0)}


def profile_read(G):
    need(PROFILE==Path(r'C:\Users\wheel\.wslconfig'),'Fixed Windows host profile path required')
    G.plain_chain(PROFILE.parent);info=PROFILE.lstat()
    need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and not PROFILE.is_symlink()
         and not getattr(info,'st_file_attributes',0)&0x400,'Single-link plain host profile required')
    raw=G.tiny(PROFILE,65536);need(profile_identity(PROFILE.lstat())==profile_identity(info),'Host profile metadata drift')
    return raw,profile_identity(info)


def failed_gate(values):
    result=values['result.json'];terminal=values['linux_terminal.json'];client=values['wsl_exit.json']
    unlock=values['lock_released.json'];close=values['commands/runtime_discovery.closure.json']
    need(result['state']=='FAILED' and result['step']=='runtime' and result['owned_closure_proven'] is True
         and result['failed_scope_closed'] is True and result['unknown_closure_stop_preserved'] is False
         and result['error']=={'kind':'ValueError','message':'Actual setup resource reserve insufficient'}
         and result['source_sha256']=='6aa21e4c43c3708abaea3d9fd07913222dee59d52093ddf96a24cddc6a205832'
         and result['linux_source_sha256']=='24aab72b74dd0aab6c58cac4951c30e6b1bfc9462460486748b546e50ec92e27',
         'Exact closed runtime07 resource failure must remain FAILED')
    need(terminal['state']=='FAILED' and terminal['step']=='runtime' and terminal['owned_closure_proven'] is True
         and terminal['remaining_direct_children']==[] and type(terminal['owned_command_count']) is int
         and terminal['owned_command_count']==1 and terminal['owner_nonce']==result['owner_nonce']==client['owner_nonce']
         and terminal['bootstrap']['boot_id']==FAILED_BOOT
         and result['linux_terminal_sha256']==FAILED_PINS['linux_terminal.json'],'Exact failed Linux terminal join differs')
    birth,end=client['birth'],client['terminal']
    need(end==result['actual_wsl_exit'] and end['exited'] is True and type(end['exit_code']) is int
         and end['exit_code']==2 and end['pid']==birth['pid'] and end['creation_filetime']==birth['creation_filetime']
         and end['exit_filetime']>end['creation_filetime'] and end['executable']==birth['executable']==r'C:\Windows\System32\wsl.exe'
         and result['wsl_exit_receipt_sha256']==FAILED_PINS['wsl_exit.json'],'Exact retained failed WSL client join differs')
    need(unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['released'] is True
         and close['boot_id']==FAILED_BOOT and type(close['root_exit_code']) is int and close['root_exit_code']==-15
         and close['group_empty'] is True and close['tracked_descendants_empty'] is True and close['survivors']==[]
         and close['unexplained_pgid_members']==[],'Failed runtime original unlock/group closure differs')
    return result


def exact_lock(value):
    need(isinstance(value,dict) and set(value)==set(ORIGINAL_LOCK)
         and all(type(value[k]) is type(v) and value[k]==v for k,v in ORIGINAL_LOCK.items()),
         'Exact original WorkflowLock identity and types required')


def capacity_contract(peer,values):
    """Only the actual current deferred, detector-free scope can authorize repair."""
    need(peer['state']=='PASS_CAPACITY02_NATURAL_ADMISSION_DEFER_NO_NATIVE_SCOPE_CLOSED_AND_ORIGINAL_UNLOCK'
         and peer['actual_state']=='DEFERRED_RESOURCE' and peer['scientific_adoption'] is False
         and peer['no_native_launch_in_this_invocation'] is True and type(peer['native_launch_count']) is int
         and peer['native_launch_count']==0 and peer['owned_closure_proven'] is True
         and peer['original_lock_explicitly_released'] is True and peer['actual_boot_id']==CAPACITY_BOOT,
         'Current capacity02 independent closed/no-native deferred review required')
    result=values['result.json'];original=values['owner.json'];launch=values['GCF_000009425.1.launch.json']
    end=values['GCF_000009425.1.exit.json'];lease=values['owner_lease.json'];unlock=values['lock_released.json']
    progress=values['progress.json'];terminal=values['terminal']
    need(result['state']==end['state']==terminal['state']=='DEFERRED_RESOURCE'
         and result['scope']=='ONE_APPROVED_GENOME' and result['selected_accessions']==['GCF_000009425.1']
         and type(result['approved_genomes']) is int and result['approved_genomes']==196
         and result['full_panel_complete'] is False and result['genome_results']==[end]
         and not result.get('error') and not result.get('finalizer_errors')
         and progress['latest']==end and progress['genome_results']==[end]
         and type(progress['finished']) is int and type(progress['total']) is int
         and progress['finished']==progress['total']==1,'Actual capacity02 deferred result/progress differs')
    owner=result['owner'];need(owner==original['owner'] and type(owner['pid']) is int and owner['pid']==25208
         and type(owner['creation_filetime']) is int and owner['creation_filetime']==134360788348328513,
         'Exact previous Windows owner birth required')
    for key,name in [('config_sha256','stage5_actual_backing_capacity_02.json'),('linux_script_sha256','stage5_atomic.py'),
        ('linux_supervisor_sha256','stage5_atomic_process.py'),('storage_helper_sha256','stage5_work_storage.py'),
        ('lease_helper_sha256','stage5_owner_lease.py')]:
        need(result[key]==original[key]==CAPACITY_PINS[name],'Previous capacity02 source/config binding differs')
    exact_lock(original['workflow_lock']);exact_lock(lease['workflow_lock'])
    need(launch['owner_nonce']==lease['nonce']==terminal['owner_nonce']==CAPACITY_NONCE
         and type(lease['owner_pid']) is int and lease['owner_pid']==owner['pid']
         and lease['owner_creation_filetime']==str(owner['creation_filetime'])
         and lease['workflow_lock_held'] is False and lease['expires_unix']==lease['measured_unix'],
         'Previous capacity02 original lease not invalidated')
    born=launch['native_wsl_client'];dead=end['actual_wsl_client_exit']
    need(dead==peer['retained_WSL_client'] and dead['exited'] is True and type(dead['exit_code']) is int
         and dead['exit_code']==75 and type(dead['pid']) is int and dead['pid']==born['pid']==10272
         and type(dead['creation_filetime']) is int and dead['creation_filetime']==born['creation_filetime']==134360788351071808
         and type(dead['exit_filetime']) is int and dead['exit_filetime']>dead['creation_filetime']
         and dead['executable']==born['executable']==r'C:\Windows\System32\wsl.exe'
         and dead['session_id']==born['session_id']==owner['session_id'],'Actual retained deferred WSL exit75 differs')
    prefix='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/'
    expected=[r'C:\Windows\System32\wsl.exe','-d','Ubuntu','-u','root','--exec',
        '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/detector_env/bin/python','-B',
        prefix+'stage5_atomic.py','--config',prefix+'stage5_actual_backing_capacity_02.json','run','--accession','GCF_000009425.1',
        '--owner-lease',prefix+CAPACITY_DIR+'/owner_lease.json','--owner-nonce',CAPACITY_NONCE]
    need(launch['argv']==expected and type(launch['index']) is int and launch['index']==1,'Exact capacity02 retained argv differs')
    need(terminal['accession']=='GCF_000009425.1' and terminal['transaction']=='transactions/attempt_0002'
         and terminal['owned_closure_proven'] is True and terminal['no_native_launch_in_this_invocation'] is True
         and terminal['outputs_preserved'] is True and terminal['curation']=='NOT_RUN'
         and terminal['biological_absence_claim']=='NONE' and isinstance(terminal['scientific_identity'],dict)
         and terminal['scientific_identity']['runner_sha256']==CAPACITY_PINS['stage5_atomic.py']
         and terminal['error']=='Deferred: Bounded resource admission expired; no native child launched',
         'Actual prepared but detector-free deferred terminal differs')
    need(unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['utc']>result['utc']>=lease['utc'],
         'Previous original explicit unlock/result/inactive lease ordering differs')
    return result


def capacity_read(G,peer_sha):
    need(isinstance(peer_sha,str) and len(peer_sha)==64 and all(c in '0123456789abcdef' for c in peer_sha),
         'Explicit published capacity02 closure-review SHA256 required')
    peer_path=WORK/CLOSURE_PEER;G.plain_chain(peer_path.parent)
    need(peer_path.lstat().st_nlink==1,'Single-link closure review required');raw=G.tiny(peer_path,2*1024**2)
    need(digest(raw)==peer_sha,'Exact independent capacity02 closure review differs');peer=json.loads(raw)
    entries=peer['checked_files'];need(isinstance(entries,dict) and 1<=len(entries)<=128,'Bounded closure file map required')
    captured={};total=0
    for name,item in entries.items():
        relative=Path(name);need(isinstance(name,str) and not relative.is_absolute() and not relative.drive
            and relative.parts and all(p not in ('.','..') and ':' not in p for p in relative.parts),'Plain relative C-work closure file required')
        path=WORK/relative;G.plain_chain(path.parent)
        need(path.lstat().st_nlink==1 and type(item['bytes']) is int and 0<=item['bytes']<=8*1024**2,
             'Single-link bounded closure evidence required')
        data=G.tiny(path,8*1024**2);total+=len(data);need(total<=32*1024**2,'Capacity closure evidence total exceeded')
        need(len(data)==item['bytes'] and digest(data)==item['sha256'],'Reviewed capacity02 evidence changed')
        captured[str(relative)]=data
    for name,pin in CAPACITY_PINS.items():need(name in captured and digest(captured[name])==pin,'Fixed capacity02 source/config pin differs')
    terminal_path=Path(peer['terminal_copy_path'])
    need(terminal_path.is_absolute() and WORK in terminal_path.parents,'Exact C-work terminal copy required')
    terminal_name=str(terminal_path.relative_to(WORK));need(terminal_name in captured,'Terminal absent from independent file map')
    names=['owner.json','result.json','GCF_000009425.1.launch.json','GCF_000009425.1.exit.json','progress.json',
           'owner_lease.json','lock_released.json']
    values={name:json.loads(captured[str(Path(CAPACITY_DIR)/name)]) for name in names}
    values['terminal']=json.loads(captured[terminal_name]);end=values['GCF_000009425.1.exit.json']
    need(digest(captured[str(Path(CAPACITY_DIR)/'result.json')])==peer['actual_result_sha256']
         and digest(captured[str(Path(CAPACITY_DIR)/'lock_released.json')])==peer['actual_unlock_sha256']
         and digest(captured[terminal_name])==peer['actual_native_terminal_sha256']==end['status_sha256'],
         'Independent actual result/unlock/native terminal hash joins differ')
    for suffix in ('stdout','stderr'):
        stream=captured[str(Path(CAPACITY_DIR)/('GCF_000009425.1.'+suffix+'.txt'))]
        need(digest(stream)==end[suffix+'_sha256'],'Closed capacity02 stream hash differs')
    need(json.loads(captured[str(Path(CAPACITY_DIR)/'GCF_000009425.1.stdout.txt')])==values['terminal'],
         'Actual runner terminal and retained stdout differ')
    capacity_contract(peer,values)
    need(G.sha(peer_path)==peer_sha,'Capacity02 independent review changed during capture')
    return peer,values,entries


def finish_after_unlock(A,lock,output,result,stop,stop_sha,nonce,closure):
    """Checked original unlock and durable receipt precede exact owned STOP clear."""
    unlocked=False;receipt_proven=False;stop_cleared=False
    try:
        lock.__exit__(None,None,None)
        need(lock.released is True,'Original explicit byte unlock did not complete')
        unlocked=True
        receipt={'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True,'utc':A.utc()}
        path=output/'lock_released.json';A.atomic(path,receipt)
        need(A.read_json(path)==receipt,'Original unlock receipt readback differs')
        result['lock_release_receipt_sha256']=digest(path.read_bytes());receipt_proven=True
    except BaseException as error:
        result.update(state='FAILED',unlock_or_receipt_error_kind=type(error).__name__)
    finalizers_ok='retained_client_finalizer_error' not in result
    if closure is True and unlocked and receipt_proven and finalizers_ok and stop_sha is not None:
        try:
            need(digest(stop.read_bytes())==stop_sha and A.read_json(stop)['owner_nonce']==nonce,'Profile-owned stop changed; preserve')
            stop.unlink();stop_cleared=True
        except BaseException as error:
            result.update(state='FAILED',stop_finalizer_error_kind=type(error).__name__)
    if result.get('state')=='HOST_PROFILE_VALIDATED_PENDING_EXPLICIT_UNLOCK':
        result['state']='PASS_NONSCIENTIFIC_WINDOWS_HOST_PROFILE_CHANGED_AND_ALL_DISTROS_STOPPED' if closure is True and unlocked and receipt_proven and finalizers_ok and stop_cleared else 'FAILED'
    result.update(owned_closure_proven=closure is True,original_lock_explicitly_released=unlocked,
                  original_unlock_receipt_proven=receipt_proven,owned_stop_cleared_after_unlock=stop_cleared,
                  unknown_closure_stop_preserved=stop.exists(),utc=A.utc())
    try:A.atomic(output/'result.json',result)
    except BaseException as error:
        result.update(state='FAILED',final_result_persistence_error_kind=type(error).__name__,
                      master_publication_reconciliation_required=True)
        failure={'schema':'STAGE05_HOST_PROFILE_FINAL_PUBLICATION_FAILURE_V1',
                 'state':'FAILED_FINAL_RESULT_PUBLICATION_RECONCILE_REQUIRED','owner_nonce':nonce,
                 'error_kind':type(error).__name__,'owned_closure_proven':closure is True,
                 'original_lock_explicitly_released':unlocked,'original_unlock_receipt_proven':receipt_proven,
                 'lock_release_receipt_sha256':result.get('lock_release_receipt_sha256'),
                 'owned_stop_cleared_after_unlock':stop_cleared,'unknown_closure_stop_preserved':stop.exists(),
                 'closure_facts_reclassified_as_unknown':False,'scientific_adoption_authorized':False,'utc':A.utc()}
        try:
            path=output/'publication_failure.json';A.atomic(path,failure)
            need(A.read_json(path)==failure,'Profile publication failure receipt readback differs')
            result['publication_failure_receipt_sha256']=digest(path.read_bytes())
        except BaseException as final_error:
            result['publication_failure_persistence_error_kind']=type(final_error).__name__
    return result


def windows_main(closure_review_sha256):
    need(os.name=='nt' and os.environ.get('COMPUTERNAME','').casefold()=='wd'
         and os.environ.get('USERNAME','').casefold()=='wheel','WD wheel Windows owner required')
    M=load_base();G=M.load_base();A,L,S=G.imports(WORK,['atomic_iqtree_windows','stage5_owner_lease','stage5_setup_windows'])
    def immutable():
        need(G.sha(__file__)==source_sha and G.sha(WORK/BASE_NAME)==BASE_SHA
             and G.sha(WORK/M.BASE_NAME)==M.BASE_SHA and G.sha(WORK/PREIMAGE_NAME)==PREIMAGE_SHA
             and G.sha(WORK/PRESERVED_SOURCE)==PRESERVED_SHA
             and all(G.sha(WORK/n)==h for n,h in G.PINS.items())
             and capacity_read(G,closure_review_sha256)[2]==closure_entries,'Profile/source/current closed scope evidence drift')
    source_sha=G.sha(__file__)
    closure_peer,values,closure_entries=capacity_read(G,closure_review_sha256);immutable()
    previous=values['result.json']
    preimage=G.tiny(WORK/PREIMAGE_NAME,65536);expected=transform_profile(preimage)
    out=WORK/('stage5_wsl_host_profile_fallback_'+uuid.uuid4().hex);out.mkdir();G.plain_chain(out)
    api=A.Win();owner=api.identity(api.current(),os.getpid());nonce=uuid.uuid4().hex
    lock=A.WorkflowLock(api);stop=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
    record={'schema':'STAGE05_WSL_HOST_PROFILE_FALLBACK_WINDOWS_OWNER_RESULT_V1','scope':SCOPE,'state':'FAILED',
        'source_sha256':source_sha,'base_source_sha256':BASE_SHA,'framework_source_sha256':M.BASE_SHA,
        'source_pins':G.PINS,'capacity02_closure_peer_sha256':closure_review_sha256,
        'capacity02_closure_files':closure_entries,'owner_nonce':nonce,'actual_owner':owner,
        'profile_path':str(PROFILE),'preimage_sha256':PREIMAGE_SHA,'expected_after_sha256':digest(expected),
        'capacity02_state_preserved':'DEFERRED_RESOURCE','old_linux_boot_id':CAPACITY_BOOT,'scientific_adoption_authorized':False,
        'preserved_original_owner_sha256':PRESERVED_SHA,'memory_maximum_bytes':3758096384,'gui_applications':False,
        'commands':[],'lease_replace_stats':{},'automatic_relaunch':False,'effects_preserved_on_failure':True,
        'boot_sensitive_gates_after_restart':'TOOLCHAIN_RUNTIME_INTEROP_G_STORAGE_UNC_ALL_REQUIRE_NEW_ACTUAL_EVIDENCE'}
    active=None;closed=True;stop_sha=None;held=None;started=time.monotonic()
    def snapshot():
        G.plain_chain(G.ROOT);raw={name:G.tiny(G.ROOT/name) for name in G.CONTROLS}
        return {'control_sha256':G.control_gate(raw),'empty_g_underlay':G.empty_directory(G.ROOT/'.work/stage05_atomic_v1'),
                'root_device':str(G.ROOT.lstat().st_dev)}
    def lease():
        need(time.monotonic()-started<180,'Whole Windows profile-owner180s deadline exceeded')
        need(snapshot()==before,'Windows authority/underlay drift');immutable()
        current=api.identity(api.current(),os.getpid())
        need(current['pid']==owner['pid'] and current['creation_filetime']==owner['creation_filetime'],'Retained owner birth changed')
        resources=api.resources([G.ROOT,out]);need(resources['physical_available_bytes']>=RESERVE
            and resources['commit_headroom_bytes']>=RESERVE and all(x>=10737418240 for x in resources['disk_available_bytes'].values()),
            'Fresh Windows maintenance1.5GiB reserve insufficient')
        now=time.time();L.atomic_owner_lease(out/'owner_lease.json',{'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1','nonce':nonce,
            'workflow_lock_held':True,'workflow_lock':held.identity,'owner_pid':owner['pid'],'owner_creation_filetime':str(owner['creation_filetime']),
            'measured_unix':now,'expires_unix':now+3,'windows_available_bytes':resources['physical_available_bytes'],
            'windows_commit_headroom_bytes':resources['commit_headroom_bytes'],'disk_available_bytes':resources['disk_available_bytes']},record['lease_replace_stats'])
        record['latest_actual_resources']=resources
    def save(name,raw):
        with (out/name).open('xb') as stream:
            need(stream.write(raw)==len(raw),'Short public profile backup write');stream.flush();os.fsync(stream.fileno())
        need(G.tiny(out/name,65536)==raw,'Durable profile backup readback differs')
    def finish_client(item):
        nonlocal active,closed
        child=item['child'];need(child.poll() is not None,'Retained maintenance client still running')
        terminal=api.identity(int(child._handle),child.pid,item['argv'][0],owner['session_id']);birth=item['birth']
        need(terminal['exited'] is True and terminal['pid']==birth['pid'] and terminal['creation_filetime']==birth['creation_filetime']
             and terminal['exit_filetime']>terminal['creation_filetime'],'Retained maintenance terminal birth/exit differs')
        item['terminal']=terminal;receipt={k:v for k,v in item.items() if k!='child'}
        A.atomic(out/(item['phase']+'.exit.json'),receipt);record['commands'].append(receipt)
        child._handle.Close();active=None;closed=True
        return terminal
    def run(phase,argv,timeout):
        nonlocal active,closed,stop_sha
        lease();need(active is None and closed,'Previous retained client closure required')
        if stop_sha is None:
            A.atomic(stop,{'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1','owner_nonce':nonce,'utc':A.utc(),'evidence':str(out),
                'reason':'Windows profile maintenance retained-client launch intent; closure required','automatic_resume':False});stop_sha=G.sha(stop)
        else:need(G.sha(stop)==stop_sha,'Own intent marker drift')
        A.atomic(out/(phase+'.intent.json'),{'phase':phase,'argv':argv,'owner_nonce':nonce,'timeout_seconds':timeout})
        closed=False
        with (out/(phase+'.stdout.txt')).open('xb') as stdout,(out/(phase+'.stderr.txt')).open('xb') as stderr:
            child=subprocess.Popen(argv,stdout=stdout,stderr=stderr,creationflags=0x08000000)
            active={'phase':phase,'argv':argv,'child':child,'birth':None,'owner_nonce':nonce}
            active['birth']=api.identity(int(child._handle),child.pid,argv[0],owner['session_id'])
            A.atomic(out/(phase+'.launch.json'),{k:v for k,v in active.items() if k!='child'})
            deadline=time.monotonic()+timeout
            while child.poll() is None:
                need(time.monotonic()<deadline,'Retained maintenance command deadline exceeded')
                need((out/(phase+'.stdout.txt')).stat().st_size<=2*1024**2
                     and (out/(phase+'.stderr.txt')).stat().st_size<=2*1024**2,'Maintenance command output exceeded bound')
                lease();time.sleep(0.5)
        terminal=finish_client(active);need(terminal['exit_code']==0,'Retained maintenance command failed; effects preserved')
        return G.tiny(out/(phase+'.stdout.txt'),2*1024**2)
    try:
        held=lock.__enter__();need(not G.exists(stop),'Existing unresolved STOP vetoes host profile maintenance')
        exact_lock(held.identity)
        record['workflow_lock']=held.identity;before=snapshot();record['windows_before']=before;lease()
        record['registry_before']=M.registry_gate(M.ubuntu_identity(),0)
        record['registered_backing_before']=S.registered_backing()
        S.reject_live_exact(api,previous['owner']);S.reject_live_exact(api,values['GCF_000009425.1.launch.json']['native_wsl_client'])
        record['census_before']=M.census_gate(json.loads(run('census_before',M.census_argv(owner['pid']),25).decode('utf-8-sig')))
        raw,identity=profile_read(G);need(raw==preimage,'Actual host profile preimage differs')
        record['profile_before_identity']=identity;save('wslconfig.before.txt',raw);save('wslconfig.after.expected.txt',expected)
        temp=PROFILE.with_name('.wslconfig.lab_rm_'+nonce+'.tmp');need(not G.exists(temp),'Exclusive profile staging name already exists')
        record['staging_path']=str(temp)
        with temp.open('xb') as stream:
            need(stream.write(expected)==len(expected),'Short profile staging write');stream.flush();os.fsync(stream.fileno())
        os.chmod(temp,stat.S_IMODE(identity['mode']));need(G.tiny(temp,65536)==expected,'Staged profile bytes differ')
        lease();need(profile_read(G)==(raw,identity),'Host profile changed before atomic replacement')
        need(M.registry_gate(M.ubuntu_identity(),0,record['registry_before'])==record['registry_before'],'Ubuntu registration drift')
        A.atomic(out/'profile_replace_intent.json',{'owner_nonce':nonce,'before':identity,'before_sha256':PREIMAGE_SHA,
            'after_sha256':digest(expected),'staging_path':str(temp),'durable_backup':'wslconfig.before.txt'})
        os.replace(temp,PROFILE);record['profile_replaced']=True
        actual,after_identity=profile_read(G);need(actual==expected,'Atomic host profile readback differs')
        save('wslconfig.after.actual.txt',actual);record['profile_after_identity']=after_identity
        record['actual_after_sha256']=digest(actual)
        record['census_before_shutdown']=M.census_gate(json.loads(run('census_before_shutdown',M.census_argv(owner['pid']),25).decode('utf-8-sig')))
        run('shutdown',M.fixed_argv('shutdown'),60)
        record['running_after']=M.running_gate(run('running_after',M.fixed_argv('running_after'),20))
        record['registry_after_shutdown']=M.registry_gate(M.ubuntu_identity(),0,record['registry_before'])
        record['census_after_shutdown']=M.census_gate(json.loads(run('census_after_shutdown',M.census_argv(owner['pid']),25).decode('utf-8-sig')))
        lease();need(profile_read(G)==(actual,after_identity),'Final host profile identity/bytes drift')
        need(G.tiny(out/'wslconfig.before.txt',65536)==preimage and G.tiny(out/'wslconfig.after.expected.txt',65536)==expected
             and G.tiny(out/'wslconfig.after.actual.txt',65536)==expected,'Final durable public profile backups differ')
        record.update(state='HOST_PROFILE_VALIDATED_PENDING_EXPLICIT_UNLOCK',windows_after=snapshot(),
            new_linux_boot='NOT_OBSERVED_NO_RELAUNCH',old_boot_runtime_proofs_reusable=False)
    except BaseException as error:record['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        if active is not None:
            try:active['child'].wait(timeout=15);finish_client(active)
            except BaseException as error:record['retained_client_finalizer_error']={'kind':type(error).__name__,'message':str(error)}
        record.update(elapsed_seconds=time.monotonic()-started,utc=A.utc(),
            log_hash_scope='CLOSED_FULL_LOGS' if closed else 'PARTIAL_UNPROVEN_WRITER')
        try:
            for path in out.glob('*.txt'):
                if closed:record.setdefault('closed_log_sha256',{})[path.name]=G.sha(path)
        except BaseException as error:record.update(state='FAILED',closed_log_finalizer_error_kind=type(error).__name__)
        if held is not None:finish_after_unlock(A,lock,out,record,stop,stop_sha,nonce,closed)
        else:
            record.update(state='FAILED',owned_closure_proven=closed,original_lock_explicitly_released=False,
                original_unlock_receipt_proven=False,unknown_closure_stop_preserved=G.exists(stop))
            A.atomic(out/'result.json',record)
    print(json.dumps({'state':record['state'],'result':str(out/'result.json')}))
    return 0 if record['state'].startswith('PASS_') and closed and lock.released and record.get('original_unlock_receipt_proven') is True else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    parser.add_argument('--closure-review-sha256');args=parser.parse_args()
    if not args.run:
        print(json.dumps({'state':'PREPARED_NOT_RUN','WSL_launches':0,'profile_changes':0,'shutdowns':0}));return 0
    return windows_main(args.closure_review_sha256)


if __name__=='__main__':raise SystemExit(main())
