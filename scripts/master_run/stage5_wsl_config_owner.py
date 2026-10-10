"""Default-NOOP, bounded WSL configuration variant of the frozen G-session owner.

Changes exactly two pinned /etc/wsl.conf lines, records a C backup, sets the
registered Ubuntu default user to root, then shuts WSL down. No automatic
relaunch, detector, VM payload read, mount, deletion or scientific adoption.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, importlib.util, itertools, json, os, re, signal, stat, subprocess, sys, time, uuid

sys.dont_write_bytecode=True
WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
LWORK=PurePosixPath('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
BASE_NAME='stage5_gdrive_view_session.py'
BASE_SHA='42db8fe44fb2e6c4b8300c2415dc45a6aec20b115449bf76ad002eda34354fb8'
PREIMAGE_NAME='stage5_wsl_config_before_repair01.txt'
PREIMAGE_SHA='4b3281aa269bf8e8ecc8224431f389aa7c1c967cea10b95f608a6e4a237dce89'
SCOPE='NONSCIENTIFIC_WSL_CONFIG_AND_CONTROLLED_SHUTDOWN_ONLY'
UBUNTU_KEY=r'Software\Microsoft\Windows\CurrentVersion\Lxss\{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}'
UBUNTU_BASE=r'C:\Users\wheel\AppData\Local\wsl\{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}'
POWERSHELL=r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
WSL=r'C:\Windows\System32\wsl.exe'
RESERVE=1879048192
UNC_SHA='0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d'
FAILED_NONCE='29dd9c67cd0e4dc9b82fe5529d3a6210'
CLEANUP_PINS={'stage5_unc_bind_probe.py':UNC_SHA,
 'stage5_unc_bind_actual_postiq_02/request.json':'b32fceaaf4757d2bd59c44004f4cd3c8ac502441692e621c9c05c80f61908e1c',
 'stage5_unc_bind_actual_postiq_02/prepared.json':'e7cfad9a439e5aaf941ede965b0b599398e0c583ccb2a61d2293ad1005f85968',
 'stage5_unc_bind_actual_postiq_02/result.json':'303b681dadbe15c0ad86aeb59dced95ff08028dd0b68c53f63dcae61fa3beacc',
 'stage5_unc_bind_actual_postiq_02/lock_released.json':'f5c3222f1c568cff2a9852fcb89f0dd34caf6c55d83b12ca7f628fb658615373',
 'stage5_storage_actual_postiq_05.json':'47d23f11135f506d26892b40f1e0f684001970445cec1d166e69c6822578fc54',
 'stage5_unc_config_actual_postboot_02.json':'862d6a0917cd2ba2917814dd2b0bba7e3359bf48852215b644050a6e5a47b1f5'}


def need(value,message):
    if not value:raise ValueError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def load_base():
    base=Path(LWORK) if sys.platform=='linux' else WORK
    need(Path(__file__).resolve().parent==base,'Exact C source workspace required')
    path=base/BASE_NAME
    need(not path.is_symlink() and digest(path.read_bytes())==BASE_SHA,'Frozen G-session framework differs')
    spec=importlib.util.spec_from_file_location('_wsl_config_G42db',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    need(module.sha(path)==BASE_SHA,'Frozen G framework changed during import')
    return module


def transform_config(raw):
    need(isinstance(raw,bytes) and len(raw)==321 and digest(raw)==PREIMAGE_SHA,'Exact unchanged321B wsl.conf preimage required')
    replacements={('boot',b'systemd=true\n'):b'systemd=false\n',('user',b'default=gns3\n'):b'default=root\n'}
    section=None;seen=set();output=[]
    for line in raw.splitlines(keepends=True):
        if line.startswith(b'[') and line.endswith(b']\n'):section=line[1:-2].decode('ascii')
        key=(section,line)
        if key in replacements:
            need(key not in seen,'Duplicate target configuration line');seen.add(key);line=replacements[key]
        output.append(line)
    need(seen==set(replacements),'Two exact section-specific configuration lines required')
    result=b''.join(output)
    need(len(result)==322 and result!=raw,'Exact two-line transform differs')
    return result


def ubuntu_identity():
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,UBUNTU_KEY,0,winreg.KEY_QUERY_VALUE) as key:
        return {name:winreg.QueryValueEx(key,name)[0] for name in ('DistributionName','Version','DefaultUid','Flags','BasePath')}


def registry_gate(value,uid,before=None):
    need(set(value)=={'DistributionName','Version','DefaultUid','Flags','BasePath'}
         and value['DistributionName']=='Ubuntu' and type(value['Version']) is int and value['Version']==2
         and type(value['DefaultUid']) is int and value['DefaultUid']==uid
         and type(value['Flags']) is int and value['Flags']==15 and Path(value['BasePath'])==Path(UBUNTU_BASE),
         'Exact registered Ubuntu UUID/version/BasePath/default UID differs')
    if before is not None:need({k:v for k,v in value.items() if k!='DefaultUid'}=={k:v for k,v in before.items() if k!='DefaultUid'},'Ubuntu registration drift')
    return value


def running_gate(raw):
    need(isinstance(raw,bytes) and len(raw)<=65536,'Bounded running-distro readback required')
    if raw.startswith((b'\xff\xfe',b'\xfe\xff')):text=raw.decode('utf-16')
    elif b'\x00' in raw:text=raw.decode('utf-16-le')
    else:text=raw.decode('utf-8-sig')
    need(text.strip()=='','A WSL distro remains running; preserve effects and stop')
    return {'state':'NO_RUNNING_DISTROS_RETAINED_QUERY_EXIT0','decoded_names':[],'stdout_sha256':digest(raw),'stdout_bytes':len(raw)}


def census_gate(value):
    need(value['selected']==[] and value['helpers']==[],'Current native project job, competing owner or resume helper exists')
    tasks=value['tasks'];need(len(tasks)==18 and len({x['name'] for x in tasks})==18
        and all(x['name'].startswith('LAB_RM_') and x['state']=='Disabled' for x in tasks),'All18legacy LAB tasks must remain disabled')
    return value


def census_argv(owner_pid):
    need(type(owner_pid) is int and owner_pid>0,'Exact current owner PID required')
    script=r'''$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);$rows=@(Get-CimInstance Win32_Process);$selected=@();$helpers=@();
foreach($r in $rows){if($r.ProcessId -eq $PID -or $r.ProcessId -eq OWNER_PID){continue};$n=$r.Name.ToLowerInvariant();$a=$r.CommandLine;
if(($n -in @('iqtree.exe','iqtree2.exe','iqtree3.exe','hmmsearch.exe','hmmscan.exe','padloc.exe','defense-finder.exe','diamond.exe')) -or $n -eq 'wsl.exe' -or (($n -in @('python.exe','pythonw.exe','bash.exe','sh.exe')) -and ($null -eq $a -or $a -match '(?i)(stage0[45]_|stage5_|atomic_iqtree_windows\.py|resume_master_after_boot_once\.py)'))){$selected += [pscustomobject]@{pid=$r.ProcessId;name=$r.Name;born=$r.CreationDate.ToUniversalTime().ToString('o');unreadable_argv=($null -eq $a)}}
if((($n -in @('powershell.exe','pwsh.exe')) -and ($a -match '(?i)-File\s+"?C:[^\r\n"]+Resume-MasterAfterBootOnce\.ps1')) -or ($n -eq 'codex.exe' -and $a -match '(?i)\bexec\b.*\bresume\b')){$helpers += [pscustomobject]@{pid=$r.ProcessId;name=$r.Name}}}
$tasks=@(Get-ScheduledTask | Where-Object TaskName -like 'LAB_RM_*' | ForEach-Object {[pscustomobject]@{name=$_.TaskName;state=[string]$_.State}});[pscustomobject]@{selected=$selected;helpers=$helpers;tasks=$tasks;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth6 -Compress'''
    return [POWERSHELL,'-NoLogo','-NoProfile','-NonInteractive','-Command',script.replace('OWNER_PID',str(owner_pid)).replace('-Depth6','-Depth 6')]


def fixed_argv(phase):
    choices={'set_default_user':[WSL,'--manage','Ubuntu','--set-default-user','root'],
             'shutdown':[WSL,'--shutdown'],'running_after':[WSL,'--list','--running','--quiet']}
    need(phase in choices,'Unknown WSL maintenance command forbidden')
    return choices[phase]


def metadata(info):
    return {'device':info.st_dev,'inode':info.st_ino,'mode':info.st_mode,'uid':info.st_uid,'gid':info.st_gid,
            'nlink':info.st_nlink,'bytes':info.st_size,'mtime_ns':info.st_mtime_ns,'ctime_ns':info.st_ctime_ns}


def sentinel_guard(directory,names,files,request,prepared):
    need(request['nonce']==prepared['nonce']==FAILED_NONCE and request['sentinel_name']=='.unc_visibility_'+FAILED_NONCE
         and prepared['request_sha256']==CLEANUP_PINS['stage5_unc_bind_actual_postiq_02/request.json']
         and prepared['state']=='PASS_LINUX_SENTINEL_PREPARED','Exact failed UNC02 preparation required')
    need(all(type(directory[k]) is int and directory[k]>=0 for k in ('device','inode','mode','uid','gid','nlink','bytes','mtime_ns','ctime_ns'))
         and stat.S_ISDIR(directory['mode']) and stat.S_IMODE(directory['mode'])==0o700 and directory['uid']==directory['gid']==0
         and directory['device']==prepared['directory_device']==2096 and directory['inode']==prepared['directory_inode']==33554545,
         'Exact root0700 failed-sentinel directory identity required')
    need(set(names) in ({'linux.bin'},{'linux.bin','windows.bin'}) and len(names)==len(set(names)) and set(files)==set(names),
         'Unknown failed-sentinel contents; preserve all files')
    for name,value in files.items():
        key='linux_payload_hex' if name=='linux.bin' else 'windows_payload_hex';data=bytes.fromhex(value['payload_hex'])
        info=value['metadata'];receipt=value['tiny_read_receipt']
        need(all(type(info[k]) is int and info[k]>=0 for k in ('device','inode','mode','uid','gid','nlink','bytes','mtime_ns','ctime_ns'))
             and data==bytes.fromhex(request[key]) and len(data)<=512 and stat.S_ISREG(info['mode'])
             and info['nlink']==1 and info['device']==directory['device'] and info['bytes']==len(data)
             and receipt['sha256']==digest(data) and receipt['bytes']==len(data)
             and receipt['device']==info['device'] and receipt['inode']==info['inode'],'Known public sentinel bytes/identity differ; preserve')
        if name=='linux.bin':need(receipt==prepared['linux_file'],'Original prepared Linux sentinel metadata differs')
    return True


def exact_failed_sentinel_cleanup(G,P,W,out,supervisor,result):
    need(all(G.sha(LWORK/name)==pin for name,pin in CLEANUP_PINS.items()),'Failed UNC02 cleanup evidence/source changed')
    spec=importlib.util.spec_from_file_location('_wsl_config_U0664',LWORK/'stage5_unc_bind_probe.py')
    U=importlib.util.module_from_spec(spec);spec.loader.exec_module(U)
    need(G.sha(U.__file__)==UNC_SHA,'Unchanged U tiny_read source required')
    request=json.loads(G.tiny(LWORK/'stage5_unc_bind_actual_postiq_02/request.json'))
    prepared=json.loads(G.tiny(LWORK/'stage5_unc_bind_actual_postiq_02/prepared.json'))
    need(json.loads(G.tiny(LWORK/'stage5_unc_bind_actual_postiq_02/result.json'))['state']=='FAILED',
         'Original UNC02 failure must remain FAILED')
    config=json.loads(G.tiny(LWORK/'stage5_unc_config_actual_postboot_02.json'))
    proof=W.validate_storage(config);need(proof==prepared['storage_before']==prepared['storage_after'],'Exact current storage05 bind/proof required')
    directory=Path(proof['canonical_target'])/('.unc_visibility_'+FAILED_NONCE);backing=Path(proof['backing'])
    G.plain_chain(directory);G.plain_chain(backing)
    def members(path):
        with os.scandir(path) as entries:names=sorted(x.name for x in itertools.islice(entries,3))
        need(len(names)<=2,'Unknown extra sentinel/backing members; preserve');return names
    need(members(backing)==[directory.name],'Unknown populated backing contents; preserve')
    names=members(directory);info=metadata(directory.lstat());files={}
    for name in names:
        need(name in ('linux.bin','windows.bin'),'Unknown sentinel leaf; preserve')
        leaf=directory/name;before=metadata(leaf.lstat());data,receipt=U.tiny_read(leaf)
        need(metadata(leaf.lstat())==before and not leaf.is_symlink(),'Sentinel leaf metadata drift/alias')
        files[name]={'metadata':before,'tiny_read_receipt':receipt,'payload_hex':data.hex()}
    sentinel_guard(info,names,files,request,prepared)
    backup={'schema':'STAGE05_EXACT_FAILED_UNC02_PUBLIC_BACKUP_V1','state':'COMPLETE_BEFORE_ANY_UNLINK',
        'original_failed_scope_state':'FAILED_PRESERVED','fixed_nonce':FAILED_NONCE,'directory':str(directory),
        'directory_metadata':info,'files':files,'current_storage_proof':proof,'source_pins':CLEANUP_PINS,
        'recovery':'Recreate exact directory and listed original public leaves with saved UID/GID/mode and payload hex; original failed receipts remain unchanged.'}
    backup_path=out/'failed_unc02_public_backup.json';raw=(json.dumps(backup,indent=2,sort_keys=True)+'\n').encode('utf-8')
    with backup_path.open('xb') as stream:need(stream.write(raw)==len(raw),'Short sentinel backup write');stream.flush();os.fsync(stream.fileno())
    need(G.tiny(backup_path)==raw and json.loads(raw)==backup,'Durable C sentinel backup readback differs')
    result['failed_unc02_cleanup']={'backup_sha256':digest(raw),'backup_path':str(backup_path),'removed_leaves':[],
        'original_failed_receipts_unchanged':True,'actual_directory_metadata':info,'directory_removed':False}
    supervisor.admission(out);need(W.validate_storage(config)==proof and metadata(directory.lstat())==info
        and members(directory)==names,'Storage/directory changed before exact cleanup')
    for name in names:
        supervisor.check_owner();leaf=directory/name
        need(U.tiny_read(leaf)[1]==files[name]['tiny_read_receipt'] and metadata(leaf.lstat())==files[name]['metadata'],
             'Known sentinel changed before unlink; preserve remaining')
        current=metadata(directory.lstat());need(all(current[k]==info[k] for k in ('device','inode','mode','uid','gid','nlink')),
             'Sentinel directory identity changed before unlink')
        leaf.unlink();result['failed_unc02_cleanup']['removed_leaves'].append(name);U.fsync_directory(directory)
    supervisor.check_owner();need(members(directory)==[] and (directory.stat().st_dev,directory.stat().st_ino)==(info['device'],info['inode']),
        'Exact now-empty sentinel directory changed; preserve')
    directory.rmdir();U.fsync_directory(backing)
    need(not directory.exists() and G.empty_directory(backing)['entries']==[] and W.validate_storage(config)==proof,
         'Backing must be empty with exact bind/proof after cleanup')
    need(all(G.sha(LWORK/name)==pin for name,pin in CLEANUP_PINS.items()),'Preserved failed evidence/source drift')
    result['failed_unc02_cleanup'].update(directory_removed=True,backing_empty_verified=True)


def linux_main(args):
    need(sys.platform=='linux' and os.geteuid()==0,'Exact Linux root config worker required')
    G=load_base();P,W=G.imports(LWORK,['stage5_atomic_process','stage5_work_storage'])
    request=Path(args.request)
    need(request.parent.parent==LWORK and re.fullmatch('stage5_wsl_config_[a-f0-9]{32}',request.parent.name)
         and request.name=='request.json' and not request.is_symlink(),'Exact fresh C config request required')
    raw=G.tiny(request);need(digest(raw)==args.request_sha256,'Exact Windows request SHA required')
    value=json.loads(raw);out=request.parent;nonce=value['owner_nonce'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    need(value['schema']=='STAGE05_WSL_CONFIG_REQUEST_V1' and value['scope']==SCOPE and value['source_sha256']==G.sha(__file__)
         and value['base_source_sha256']==BASE_SHA and value['preimage_sha256']==PREIMAGE_SHA
         and re.fullmatch('[a-f0-9]{32}',nonce),'Exact config request/source contract differs')
    need(value['fresh_toolchain_pins']==G.FRESH_PINS and G.fresh_toolchain_gate(LWORK,value['fresh_toolchain_proof'],value['fresh_toolchain_proof_sha256'])==boot==value['boot_id'],'Current old-boot toolchain05 proof differs')
    held=json.loads(G.tiny(out/'actual_owner_lock.json'))
    need(G.sha(out/'actual_owner_lock.json')==value['owner_lock_sha256'] and held['owner_nonce']==nonce
         and held['workflow_lock']==value['workflow_lock'],'Current original-lock witness differs')
    result={'schema':'STAGE05_WSL_CONFIG_LINUX_TERMINAL_V1','scope':SCOPE,'state':'FAILED','owner_nonce':nonce,
            'source_sha256':G.sha(__file__),'request_sha256':args.request_sha256,'boot_id':boot,
            'bootstrap':{'argv':sys.argv,'executable':sys.executable,'identity':P.proc_record(os.getpid())},
            'scientific_adoption_authorized':False,'owned_closure_proven':True,'owned_command_count':0,
            'config_replaced':False,'configuration_path':'/etc/wsl.conf'}
    policy={'windows_reserve_bytes':1610612736,'incremental_windows_requirement_bytes':268435456,
        'commit_requirement_bytes':RESERVE,'linux_job_requirement_bytes':134217728,'linux_reserve_bytes':134217728,
        'minimum_disk_free_bytes':10737418240,'resource_wait_seconds':0,'lease_max_age_seconds':3,
        'command_timeout_seconds':30,'sampled_rss_stop_bytes':268435456,'termination_grace_seconds':2,'drain_timeout_seconds':4}
    supervisor=None;signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Config worker90s deadline')));signal.alarm(90)
    try:
        supervisor=P.Supervisor(out/'owner_lease.json',nonce,policy,out,G.sha);supervisor.admission(out)
        namespace=G.session_namespace_observation(P);result['mount_namespace']=namespace
        need(value['cleanup_pins']==CLEANUP_PINS,'Exact authorized failed-nonce cleanup pins required')
        path=Path('/etc/wsl.conf');G.plain_chain(path.parent);info=path.lstat()
        need(stat.S_ISREG(info.st_mode) and not path.is_symlink() and info.st_nlink==1 and info.st_uid==info.st_gid==0
             and not stat.S_IMODE(info.st_mode)&0o7022,'Config must be root-owned, single-link plain and not group/world writable')
        original=G.tiny(path,65536);after=transform_config(original)
        need(G.tiny(LWORK/PREIMAGE_NAME,65536)==original,'Pinned C preimage differs from actual Linux bytes')
        def save(name,data):
            with (out/name).open('xb') as stream:need(stream.write(data)==len(data),'Short C backup write');stream.flush();os.fsync(stream.fileno())
        save('wsl.conf.before.txt',original);save('wsl.conf.after.expected.txt',after)
        result.update(before_sha256=digest(original),after_sha256=digest(after),before_bytes=len(original),after_bytes=len(after),original_mode=stat.S_IMODE(info.st_mode))
        exact_failed_sentinel_cleanup(G,P,W,out,supervisor,result)
        temp=path.with_name('.wsl.conf.lab_rm_'+nonce+'.tmp');result['preserved_partial_temp_path']=str(temp)
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,stat.S_IMODE(info.st_mode))
        with os.fdopen(fd,'wb') as stream:
            os.fchown(stream.fileno(),info.st_uid,info.st_gid);os.fchmod(stream.fileno(),stat.S_IMODE(info.st_mode))
            need(stream.write(after)==len(after),'Short config staging write');stream.flush();os.fsync(stream.fileno())
        need(G.tiny(temp,65536)==after,'Staged config bytes differ')
        supervisor.admission(out);G.session_namespace_gate(G.session_namespace_observation(P),namespace)
        need(metadata(path.lstat())==metadata(info) and G.tiny(path,65536)==original,'Config metadata/bytes changed before atomic replacement')
        P.atomic_json(out/'linux_config_intent.json',{**result,'state':'EXACT_BACKUP_AND_STAGED_BYTES_BEFORE_ATOMIC_REPLACE'})
        supervisor.check_owner();os.replace(temp,path);result['config_replaced']=True
        dirfd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(dirfd)
        finally:os.close(dirfd)
        actual=G.tiny(path,65536);final=path.lstat()
        need(actual==after and stat.S_ISREG(final.st_mode) and final.st_nlink==1 and final.st_uid==info.st_uid
             and final.st_gid==info.st_gid and stat.S_IMODE(final.st_mode)==stat.S_IMODE(info.st_mode),'Atomic config byte/metadata readback differs')
        save('wsl.conf.after.actual.txt',actual);result['config_after_actual_sha256']=digest(actual)
        supervisor.check_owner();result['session_parent_final']=G.session_namespace_gate(G.session_namespace_observation(P),namespace)
        need(G.sha(request)==args.request_sha256 and G.sha(__file__)==value['source_sha256'] and G.sha(LWORK/BASE_NAME)==BASE_SHA
             and all(G.sha(LWORK/name)==pin for name,pin in CLEANUP_PINS.items())
             and G.fresh_toolchain_gate(LWORK,value['fresh_toolchain_proof'],value['fresh_toolchain_proof_sha256'])==boot,'Config final source/request/old-boot proof drift')
        result['state']='PASS_EXACT_TWO_LINE_CONFIG_REPLACED_READBACK'
    except BaseException as error:result['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        signal.alarm(0)
        if supervisor:result.update(owned_closure_proven=not supervisor.closure_unproven,owned_command_count=supervisor.native_launch_count)
        try:
            result['remaining_direct_children']=[int(x) for x in Path(f'/proc/self/task/{os.getpid()}/children').read_text().split()]
            if result['remaining_direct_children']:result['owned_closure_proven']=False
        except BaseException:result.update(owned_closure_proven=False,remaining_direct_children='UNPROVEN')
        P.atomic_json(out/'linux_terminal.json',result)
    return 0 if result['state'].startswith('PASS_') and result['owned_closure_proven'] else 2


def terminal_gate(value,nonce,request_sha,source_sha,boot,exit_code):
    need(value['schema']=='STAGE05_WSL_CONFIG_LINUX_TERMINAL_V1' and value['scope']==SCOPE and value['owner_nonce']==nonce
         and value['request_sha256']==request_sha and value['source_sha256']==source_sha and value['boot_id']==boot
         and value['owned_closure_proven'] is True and value['remaining_direct_children']==[]
         and type(value['owned_command_count']) is int and value['owned_command_count']==0
         and value['scientific_adoption_authorized'] is False,'Exact config worker scope/closure differs')
    need(value['state'] in ('FAILED','PASS_EXACT_TWO_LINE_CONFIG_REPLACED_READBACK')
         and exit_code==(0 if value['state'].startswith('PASS_') else 2)
         and not(value['state'].startswith('PASS_') and 'error' in value),'Config worker state/exit mismatch')
    return value['state'].startswith('PASS_')


def windows_main(args):
    need(os.name=='nt' and os.environ.get('COMPUTERNAME','').casefold()=='wd'
         and os.environ.get('USERNAME','').casefold()=='wheel','WD wheel Windows owner required')
    G=load_base();A,L,S=G.imports(WORK,['atomic_iqtree_windows','stage5_owner_lease','stage5_setup_windows'])
    need(all(G.sha(WORK/n)==h for n,h in G.PINS.items()) and all(G.sha(WORK/n)==h for n,h in G.PRIOR_PINS.items())
         and all(G.sha(WORK/n)==h for n,h in CLEANUP_PINS.items()),'Published source/history/failed-sentinel pins differ')
    oldboot=G.prior_gate({n:json.loads(G.tiny(WORK/n)) for n in G.PRIOR_PINS})
    boot=G.fresh_toolchain_gate(WORK,args.fresh_toolchain_proof,args.fresh_toolchain_proof_sha256)
    preimage=G.tiny(WORK/PREIMAGE_NAME,65536);expected=transform_config(preimage)
    out=WORK/('stage5_wsl_config_'+uuid.uuid4().hex);out.mkdir();G.plain_chain(out)
    api=A.Win();owner=api.identity(api.current(),os.getpid());nonce=uuid.uuid4().hex;source_sha=G.sha(__file__)
    lock=A.WorkflowLock(api);stop=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
    record={'schema':'STAGE05_WSL_CONFIG_WINDOWS_OWNER_RESULT_V1','scope':SCOPE,'state':'FAILED','source_sha256':source_sha,
        'base_source_sha256':BASE_SHA,'source_pins':G.PINS,'prior_pins':G.PRIOR_PINS,'fresh_toolchain_pins':G.FRESH_PINS,'cleanup_pins':CLEANUP_PINS,
        'owner_nonce':nonce,'actual_owner':owner,'old_linux_boot_id':boot,'historical_boot_id_preserved':oldboot,
        'preimage_sha256':PREIMAGE_SHA,'expected_after_sha256':digest(expected),'scientific_adoption_authorized':False,
        'commands':[],'lease_replace_stats':{},'automatic_relaunch':False,'effects_preserved_on_failure':True,
        'boot_sensitive_gates_after_restart':'TOOLCHAIN_INTEROP_G_STORAGE_UNC_RUNTIME_ALL_REQUIRE_NEW_ACTUAL_EVIDENCE'}
    active=None;closed=True;stop_sha=None;started=time.monotonic();held=None
    def snapshot():
        G.plain_chain(G.ROOT);raw={name:G.tiny(G.ROOT/name) for name in G.CONTROLS}
        return {'control_sha256':G.control_gate(raw),'empty_g_underlay':G.empty_directory(G.ROOT/'.work/stage05_atomic_v1'),
                'root_device':str(G.ROOT.lstat().st_dev)}
    def lease():
        need(time.monotonic()-started<300,'Whole config-owner300s deadline exceeded')
        need(snapshot()==before,'Windows authority/underlay drift')
        current=api.identity(api.current(),os.getpid());need(current['pid']==owner['pid'] and current['creation_filetime']==owner['creation_filetime'],'Retained owner birth changed')
        resources=api.resources([G.ROOT,out]);need(resources['physical_available_bytes']>=RESERVE
            and resources['commit_headroom_bytes']>=RESERVE and all(x>=10737418240 for x in resources['disk_available_bytes'].values()),'Fresh Windows config resources insufficient')
        need(G.sha(__file__)==source_sha and G.sha(WORK/BASE_NAME)==BASE_SHA,'Config/framework source drift')
        now=time.time();L.atomic_owner_lease(out/'owner_lease.json',{'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1','nonce':nonce,
            'workflow_lock_held':True,'workflow_lock':held.identity,'owner_pid':owner['pid'],'owner_creation_filetime':str(owner['creation_filetime']),
            'measured_unix':now,'expires_unix':now+3,'windows_available_bytes':resources['physical_available_bytes'],
            'windows_commit_headroom_bytes':resources['commit_headroom_bytes'],'disk_available_bytes':resources['disk_available_bytes']},record['lease_replace_stats'])
        record['latest_actual_resources']=resources
    def finish_client(item):
        nonlocal active,closed
        child=item['child'];need(child.poll() is not None,'Retained maintenance client still running')
        terminal=api.identity(int(child._handle),child.pid,item['argv'][0],owner['session_id']);birth=item['birth']
        need(terminal['exited'] is True and terminal['pid']==birth['pid'] and terminal['creation_filetime']==birth['creation_filetime']
             and terminal['exit_filetime']>terminal['creation_filetime'],'Retained maintenance terminal birth/exit differs')
        item['terminal']=terminal;receipt={k:v for k,v in item.items() if k!='child'}
        A.atomic(out/(item['phase']+'.exit.json'),receipt)
        record['commands'].append(receipt);child._handle.Close();active=None;closed=True
        return terminal
    def run(phase,argv,timeout):
        nonlocal active,closed,stop_sha
        lease();need(active is None and closed,'Previous retained client closure required')
        if stop_sha is None:
            A.atomic(stop,{'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1','owner_nonce':nonce,'utc':A.utc(),'evidence':str(out),
                'reason':'WSL config maintenance launch intent; current retained Linux/Windows clients require closure','automatic_resume':False});stop_sha=G.sha(stop)
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
        held=lock.__enter__();need(not G.exists(stop),'Existing unresolved STOP vetoes config maintenance')
        record['workflow_lock']=held.identity;before=snapshot();record['windows_before']=before
        record['registered_backing_before']=S.registered_backing();registration=registry_gate(ubuntu_identity(),1000);record['registry_before']=registration
        record['census_before']=census_gate(json.loads(run('census_before',census_argv(owner['pid']),25).decode('utf-8-sig')))
        A.atomic(out/'actual_owner_lock.json',{'owner_nonce':nonce,'owner':owner,'workflow_lock':held.identity})
        request={'schema':'STAGE05_WSL_CONFIG_REQUEST_V1','scope':SCOPE,'owner_nonce':nonce,'source_sha256':source_sha,
            'base_source_sha256':BASE_SHA,'preimage_sha256':PREIMAGE_SHA,'boot_id':boot,'workflow_lock':held.identity,'cleanup_pins':CLEANUP_PINS,
            'owner_lock_sha256':G.sha(out/'actual_owner_lock.json'),'fresh_toolchain_pins':G.FRESH_PINS,
            'fresh_toolchain_proof':str(LWORK/G.FRESH_TOOLCHAIN_DIR/'toolchain_proof.json'),'fresh_toolchain_proof_sha256':args.fresh_toolchain_proof_sha256}
        A.atomic(out/'request.json',request);request_sha=G.sha(out/'request.json')
        argv=[WSL,'-d','Ubuntu','-u','root','--exec','/usr/bin/python3','-B',str(LWORK/Path(__file__).name),
              '--linux','--request',str(LWORK/out.name/'request.json'),'--request-sha256',request_sha]
        run('linux_config',argv,110);actual=json.loads(G.tiny(out/'linux_terminal.json'))
        need(terminal_gate(actual,nonce,request_sha,source_sha,boot,record['commands'][-1]['terminal']['exit_code']),'Linux config worker did not pass')
        need(actual['bootstrap']['argv']==argv[8:] and actual['bootstrap']['executable']=='/usr/bin/python3'
             and actual['bootstrap']['identity']['pid']>0 and int(actual['bootstrap']['identity']['start_ticks'])>0,'Config Linux bootstrap identity differs')
        need(not list((out/'commands').glob('*')),'No Linux native child commands permitted')
        need(actual['config_replaced'] is True and actual['before_sha256']==PREIMAGE_SHA
             and actual['config_after_actual_sha256']==actual['after_sha256']==digest(expected)
             and G.tiny(out/'wsl.conf.before.txt',65536)==preimage and G.tiny(out/'wsl.conf.after.expected.txt',65536)==expected
             and G.tiny(out/'wsl.conf.after.actual.txt',65536)==expected,'Windows C config backup/readback differs')
        cleanup=actual['failed_unc02_cleanup'];backup=G.tiny(out/'failed_unc02_public_backup.json')
        need(cleanup['directory_removed'] is True and cleanup['backing_empty_verified'] is True and digest(backup)==cleanup['backup_sha256'],
             'Exact failed-sentinel cleanup or durable public backup differs')
        record['failed_unc02_cleanup']=cleanup
        record['linux_terminal_sha256']=G.sha(out/'linux_terminal.json');record['linux_config_verified']=True
        record['census_before_manage']=census_gate(json.loads(run('census_before_manage',census_argv(owner['pid']),25).decode('utf-8-sig')))
        registry_gate(ubuntu_identity(),1000,registration);run('set_default_user',fixed_argv('set_default_user'),30)
        record['registry_after_manage']=registry_gate(ubuntu_identity(),0,registration)
        run('shutdown',fixed_argv('shutdown'),60)
        record['running_after']=running_gate(run('running_after',fixed_argv('running_after'),20))
        record['registry_after_shutdown']=registry_gate(ubuntu_identity(),0,registration)
        record['census_after_shutdown']=census_gate(json.loads(run('census_after_shutdown',census_argv(owner['pid']),25).decode('utf-8-sig')))
        need(snapshot()==before and all(G.sha(WORK/n)==h for n,h in G.PINS.items())
             and all(G.sha(WORK/n)==h for n,h in G.PRIOR_PINS.items()) and all(G.sha(WORK/n)==h for n,h in CLEANUP_PINS.items())
             and G.fresh_toolchain_gate(WORK,args.fresh_toolchain_proof,args.fresh_toolchain_proof_sha256)==boot
             and G.sha(WORK/PREIMAGE_NAME)==PREIMAGE_SHA,'Final immutable old evidence/authority/source drift')
        record.update(state='PASS_NONSCIENTIFIC_WSL_CONFIG_CHANGED_AND_ALL_DISTROS_STOPPED',windows_after=snapshot(),new_linux_boot='NOT_OBSERVED_NO_RELAUNCH',old_boot_runtime_proofs_reusable=False)
    except BaseException as error:record['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        if active is not None:
            try:
                active['child'].wait(timeout=15);finish_client(active)
            except BaseException as error:record['retained_client_finalizer_error']={'kind':type(error).__name__,'message':str(error)}
        if closed and any(x['phase']=='linux_config' for x in record['commands']) and 'linux_config_verified' not in record:
            try:
                item=next(x for x in record['commands'] if x['phase']=='linux_config');actual=json.loads(G.tiny(out/'linux_terminal.json'))
                terminal_gate(actual,nonce,request_sha,source_sha,boot,item['terminal']['exit_code'])
            except BaseException as error:closed=False;record['linux_closure_finalizer_error']={'kind':type(error).__name__,'message':str(error)}
        if closed and stop_sha is not None:
            try:need(G.sha(stop)==stop_sha and json.loads(G.tiny(stop))['owner_nonce']==nonce,'Own marker changed');stop.unlink()
            except BaseException as error:record['own_stop_clear_error']=str(error);record['state']='FAILED'
        try:lock.__exit__(None,None,None)
        except BaseException as error:record['unlock_error']=str(error);record['state']='FAILED'
        record.update(owned_closure_proven=closed,original_lock_explicitly_released=lock.released,
            unknown_closure_stop_preserved=G.exists(stop),elapsed_seconds=time.monotonic()-started,utc=A.utc(),
            log_hash_scope='CLOSED_FULL_LOGS' if closed else 'PARTIAL_UNPROVEN_WRITER')
        for path in out.glob('*.txt'):
            if closed:record.setdefault('closed_log_sha256',{})[path.name]=G.sha(path)
        A.atomic(out/'result.json',record)
        if lock.released:A.atomic(out/'lock_released.json',{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True,'utc':A.utc()})
    print(json.dumps({'state':record['state'],'result':str(out/'result.json')}))
    return 0 if record['state'].startswith('PASS_') and closed and lock.released else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--linux',action='store_true')
    for name in ['request','request-sha256','fresh-toolchain-proof','fresh-toolchain-proof-sha256']:parser.add_argument('--'+name)
    args=parser.parse_args()
    if args.linux:return linux_main(args)
    if not args.run:print(json.dumps({'state':'PREPARED_NOT_RUN','WSL_launches':0,'config_changes':0,'shutdowns':0}));return 0
    return windows_main(args)


if __name__=='__main__':raise SystemExit(main())
