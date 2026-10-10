"""Pure independent readback of an explicitly selected completed Stage5 spool.

Standard library only. No producer imports, WSL, networking, lock acquisition,
signals, registry access or source mutation. Writes one new review receipt.
"""
from pathlib import Path, PurePosixPath
import argparse, ast, datetime, hashlib, json, os, stat

WORK=Path(__file__).resolve().parent
OLD_LINUX_BOOT='64d6e318-170c-4bef-9538-90fd218881af'
LOCK={'volume_serial':2430728143,'file_index':844424932784519,'creation_filetime':134359335921635133,'locked_byte':0}
PYTHON=r'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
WSL=r'C:\Windows\System32\wsl.exe'
CHECKED={}

def require(value,message):
    if not value:raise ValueError(message)

def data(path):
    path=Path(path)
    require(WORK in path.parents and path==path.resolve(),'Explicit direct C work ancestry required')
    for parent in (path,*path.parents):
        info=parent.lstat()
        require(not parent.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400,'Aliased/reparse evidence path')
    info=path.stat();require(stat.S_ISREG(info.st_mode) and info.st_size<=32*1024**2,'Bounded regular evidence required')
    raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    CHECKED[str(path.relative_to(WORK))]={'bytes':len(raw),'sha256':digest}
    return raw

def sha(path):data(path);return CHECKED[str(Path(path).relative_to(WORK))]['sha256']
def read(path):return json.loads(data(path))

def pinned(path,digest):require(sha(path)==digest,'SHA256 differs: '+str(path));return read(path)

def cpath(value):
    pure=PurePosixPath(value)
    require(pure.parts[:3]==('/','mnt','c') and '..' not in pure.parts and pure.as_posix()==value,'Exact C-mounted evidence path required')
    path=Path('C:/').joinpath(*pure.parts[3:]);require(WORK in path.parents,'C evidence escapes work');return path

def lock(value):require(all(value.get(k)==v for k,v in LOCK.items()),'Original WorkflowLock identity differs')

def terminal(birth,end,boot_filetime,code=0,image=WSL):
    require(birth['pid']==end['pid'] and int(birth['creation_filetime'])==int(end['creation_filetime'])>=boot_filetime,
            'Windows retained process PID/birth differs or predates current boot')
    require(birth['executable']==end['executable']==image and birth['session_id']==end['session_id'],'Retained image/session differs')
    require(end['exited'] is True and int(end['exit_filetime'])>int(end['creation_filetime']) and end['exit_code']==code,'Retained terminal exit differs')

def source(name,authority):
    selected=[v for v in authority['sources'] if v['name']==name]
    require(len(selected)==1 and selected[0]['exact_published_locations'] and selected[0]['all_declared_pins_match'],'Source not accepted by immutable authority review')
    expected=selected[0]['sha256'];require(sha(WORK/name)==expected,'Current source drift: '+name)
    if name.endswith('.py'):
        for node in ast.parse(data(WORK/name)).body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PINS' for t in node.targets):
                for helper,pin in ast.literal_eval(node.value).items():require(sha(WORK/helper)==pin,'Declared dependency drift: '+helper)
    return expected

def native(directory,label,boot,expected_code=0):
    launch=read(directory/(label+'.launch.json'));intent=read(directory/(label+'.launch_intent.json'))
    close=read(directory/(label+'.closure.json'));command=read(directory/(label+'.command.json'))
    require(launch['boot_id']==command['boot_id']==close['boot_id']==boot!=OLD_LINUX_BOOT,'Linux native boot differs/stale')
    require(launch['command_nonce']==intent['command_nonce']==command['command_nonce']==close['command_nonce'],'Native command nonce differs')
    require(launch['argv']==intent['argv']==command['argv'],'Native command argv differs')
    require(all(launch[k]==command[k] for k in ('child_pid','child_start_ticks','pgid','sid','identity','cwd')),'Native birth/session/scope differs')
    require(launch['child_pid']==launch['pgid']==launch['sid'],'Native dedicated session differs')
    require(launch['signalling']==command['signalling']==close['signalling']=='VERIFIED_KERNEL_PIDFDS_ONLY','Native kernel identity signaling differs')
    require(close['root_exit_code']==command['exit_code']==expected_code and close['group_empty'] is True
            and close['tracked_descendants_empty'] is True and close['survivors']==[] and close['unexplained_pgid_members']==[],
            'Native root/group/descendant closure differs')
    require(command['group_closure_sha256']==sha(directory/(label+'.closure.json'))
            and command['stdout_sha256']==sha(directory/(label+'.stdout.txt'))
            and command['stderr_sha256']==sha(directory/(label+'.stderr.txt')),'Native exact closure/stdout/stderr bytes differ')
    require(any(v['pid']==launch['child_pid'] and v['start_ticks']==launch['child_start_ticks'] for v in close['tracked_descendants']),
            'Native retained root identity absent from closure')
    return {'label':label,'boot_id':boot,'argv':launch['argv'],'exit_code':expected_code,'closure_sha256':command['group_closure_sha256']}

def windows_job(directory,value,boot_filetime,unc_sha,api_sha):
    final=read(directory/'result.json');launch=read(directory/'launch.json');root=read(directory/'root_exit.json')
    require(value==final and final['schema']=='STAGE05_OWNED_WINDOWS_IO_JOB_V2'
            and final['state']=='PASS_EXACT_RETAINED_ROOT_EXIT0_AND_EMPTY_NAMED_JOB'
            and final['owned_closure_proven'] is True and final['created'] and final['assigned'],'Windows IO Job final receipt differs')
    require(final['source_sha256']==unc_sha and final['api_sha256']==api_sha,'Windows IO source differs')
    require(launch['birth']==root['birth']==final['birth'] and root['exit']==final['exit']
            and launch['job_name']==root['job_name']==final['job_name'],'Durable Windows lifecycle joins differ')
    terminal(final['birth'],final['exit'],boot_filetime,image=PYTHON)
    require(final['owned_job']['job_active_processes']==0 and final['owned_job']['job_pids']==[],'Full named Windows Job not empty')
    require(final['drain_samples'] and final['drain_samples'][-1]['root_wait']==0
            and final['drain_samples'][-1]['job']['job_active_processes']==0 and final['drain_samples'][-1]['job']['job_pids']==[],
            'Bounded full-Job drain did not conclude empty')

def setup(kind,directory,value,authority,boot_filetime,requested_boot):
    setup_sha=source('stage5_setup_windows.py',authority);linux_sha=source('stage5_setup_linux.py',authority)
    require(value['state']=='PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK' and value['step']==kind
            and value['source_sha256']==setup_sha and value['linux_source_sha256']==linux_sha
            and value['owned_closure_proven'] is True and value['unknown_closure_stop_preserved'] is False,'Actual setup success/source/closure differs')
    for name,pin in value['source_pins'].items():require(sha(WORK/name)==pin,'Setup actual source dependency differs')
    lock(value['workflow_lock']);held=read(directory/'actual_owner_lock.json');lock(held['workflow_lock'])
    require(held['owner']==value['actual_windows_owner'] and held['owner_nonce']==value['owner_nonce'],'Actual setup owner lock differs')
    require(value['actual_windows_owner']['executable']==PYTHON and int(value['actual_windows_owner']['creation_filetime'])>=boot_filetime,'Setup Windows owner image/boot differs')
    launch=read(directory/'launch.json');client=pinned(directory/'wsl_exit.json',value['wsl_exit_receipt_sha256'])
    require(client['owner_nonce']==launch['owner_nonce']==value['owner_nonce'] and client['step']==kind
            and client['source_sha256']==setup_sha and client['linux_source_sha256']==linux_sha
            and client['argv']==launch['argv'],'WSL receipt source/argv/nonce differs')
    require(client['birth']==launch['native_wsl_client'] and client['terminal']==value['actual_wsl_exit'],'WSL retained evidence differs')
    terminal(client['birth'],client['terminal'],boot_filetime)
    require(client['stdout_sha256']==sha(directory/'wsl.stdout.txt') and client['stderr_sha256']==sha(directory/'wsl.stderr.txt'),'WSL stream hashes differ')
    linux=pinned(directory/'linux_terminal.json',value['linux_terminal_sha256']);boot=linux['bootstrap']['boot_id']
    require(boot!=OLD_LINUX_BOOT and (not requested_boot or requested_boot==boot),'Stale or inconsistent Linux boot')
    require(linux['state']=='PASS_NONSCIENTIFIC_SETUP_STEP' and linux['step']==kind and linux['source_sha256']==linux_sha
            and linux['owner_nonce']==value['owner_nonce'] and linux['owned_closure_proven'] is True
            and linux['remaining_direct_children']==[],'Linux bootstrap terminal differs')
    count=linux['owned_command_count'];paths=list((directory/'commands').glob('*.launch.json'))
    require(count==len(paths) and count in (0,1) and (kind in ('toolchain','storage') or count==1),'Bounded native accounting differs')
    commands=[native(directory/'commands',p.name.removesuffix('.launch.json'),boot) for p in paths]
    candidate=None
    if kind=='toolchain':candidate=directory/'toolchain_proof.json';proof=pinned(candidate,linux['toolchain_proof_sha256']);require(proof['boot_id']==boot and proof['helper_sha256']==linux_sha and proof['mount']['filesystem']=='ext4','Toolchain proof differs')
    if kind in ('runtime','storage'):
        candidate=cpath(linux['candidate_path']);proof=pinned(candidate,linux['candidate_sha256'])
        if kind=='storage':require(proof['boot_id']==boot and proof['target_mount']['filesystem']=='ext4' and linux['storage']==proof
                                   and value['g_underlay_before']==value['g_underlay_after'],'Storage candidate/underlay differs')
        else:require(proof['schema']=='STAGE05_PINNED_RUNTIME_V1' and proof['scope']=='Hash/version discovery only; execution/interoperability NOT_RUN','Runtime candidate scope differs')
    if kind=='drivefs':
        windows_job(directory/'windows_readback_worker',value['windows_readback_worker'],boot_filetime,
                    source('stage5_unc_bind_probe.py',authority),source('atomic_iqtree_windows.py',authority))
        require(read(directory/'drivefs_windows_readback.json')==value['windows_readback'],'DriveFS readback result differs')
    return {'linux_boot_id':boot,'native_commands':commands,'candidate_path':None if candidate is None else str(candidate),
            'candidate_sha256':None if candidate is None else sha(candidate)}

def interop(directory,value,authority,boot_filetime,requested_boot):
    for name in ('stage5_interop_smoke_windows.py','stage5_interop_linux_fixture.py','stage5_atomic_process.py','atomic_iqtree_windows.py'):source(name,authority)
    require(value['state']=='PASS_NONSCIENTIFIC_INTEROP_ONLY' and [v['fixture'] for v in value['results']]==['exit0','lease_expiry','escaped_descendant'],'Interop fixtures differ')
    require(value['worker_sha256']==source('stage5_interop_linux_fixture.py',authority)
            and value['supervisor_sha256']==source('stage5_atomic_process.py',authority)
            and value['windows_api_sha256']==source('atomic_iqtree_windows.py',authority),'Interop recorded source pins differ')
    boot=None;commands=[]
    for item in value['results']:
        selected=directory/item['fixture'];require(read(selected/'result.json')==item,'Interop fixture/result join differs')
        launch=read(selected/'wsl.launch.json');terminal(launch['actual_client'],item['actual_wsl_client_exit'],boot_filetime)
        require(launch['owner_nonce']==item['owner_nonce'] and item['owned_closure_proven'] is True,'Interop owner/closure differs')
        linux=pinned(selected/'linux/terminal.json',item['terminal_sha256'])
        require(linux['owner_nonce']==item['owner_nonce'] and linux['fixture']==item['fixture'] and linux['owned_closure_proven'] is True,'Interop Linux terminal differs')
        require(linux['worker_sha256']==value['worker_sha256'] and linux['supervisor_sha256']==value['supervisor_sha256'],'Interop Linux source pin differs')
        lock(linux['actual_windows_owner']['workflow_lock'])
        require(linux['actual_windows_owner']['owner_pid']==value['actual_windows_owner']['pid']
                and int(linux['actual_windows_owner']['owner_creation_filetime'])==int(value['actual_windows_owner']['creation_filetime'])>=boot_filetime,'Interop actual owner birth/lock differs')
        for rel,pin in linux['files'].items():
            pure=PurePosixPath(rel);require(not pure.is_absolute() and '..' not in pure.parts,'Unsafe terminal file role');require(sha(selected/'linux'/rel)==pin,'Interop exact native evidence SHA differs')
        command=read(selected/'linux/attempt/synthetic.command.json');current=command['boot_id']
        require(current!=OLD_LINUX_BOOT and (not requested_boot or requested_boot==current) and (not boot or boot==current),'Interop Linux boot differs')
        boot=current;commands.append(native(selected/'linux/attempt','synthetic',boot,command['exit_code']))
        require(item['wsl_stdout_sha256']==sha(selected/'wsl.stdout.txt') and item['wsl_stderr_sha256']==sha(selected/'wsl.stderr.txt'),'Interop retained stream differs')
    return {'linux_boot_id':boot,'native_commands':commands}

def unc(directory,value,authority,boot_filetime,requested_boot):
    unc_sha=source('stage5_unc_bind_probe.py',authority);api_sha=source('atomic_iqtree_windows.py',authority)
    require(value['state']=='PASS_NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY' and value['source_sha256']==unc_sha
            and value['exact_owned_cleanup'] is True and value['windows_g_underlay_before']==value['windows_g_underlay_after'],'UNC success/source/underlay differs')
    lock(value['workflow_lock']);request=pinned(directory/'request.json',value['request_sha256'])
    for rel,pin in value['files'].items():require(Path(rel).name==rel and sha(directory/rel)==pin,'UNC exact leaf SHA differs')
    require([v['phase'] for v in value['steps']]==['linux-prepare','windows-io','linux-finalize'],'UNC phases differ')
    windows_job(directory/'windows_io_worker',{k:v for k,v in value['steps'][1].items() if k!='phase'},boot_filetime,unc_sha,api_sha)
    for step in (value['steps'][0],value['steps'][2]):terminal(step['birth'],step['exit'],boot_filetime)
    final=read(directory/'final.json');prepared=read(directory/'prepared.json')
    require(final['request_sha256']==prepared['request_sha256']==value['request_sha256'] and final['nonce']==prepared['nonce']==request['nonce']
            and final['script_sha256']==prepared['script_sha256']==unc_sha and final['exact_owned_sentinel_cleanup'] is True,'UNC request/source/cleanup receipt joins differ')
    proof=final['storage_after'];require(final['storage_before']==prepared['storage_before']==prepared['storage_after']==proof,'UNC storage changed during sentinel')
    boot=proof['boot_id'];require(boot!=OLD_LINUX_BOOT and (not requested_boot or boot==requested_boot),'UNC Linux boot differs')
    actual=pinned(cpath(proof['proof_path']),proof['proof_sha256']);require(all(proof[k]==v for k,v in actual.items()),'UNC selected storage proof differs')
    return {'linux_boot_id':boot,'exact_sentinel_cleanup':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind',required=True,choices=('toolchain','runtime','interop','storage','drivefs','unc'))
    p.add_argument('--spool',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--boot-receipt',required=True,type=Path);p.add_argument('--boot-receipt-sha256',required=True)
    p.add_argument('--authority-report-sha256',required=True);p.add_argument('--linux-boot-id')
    a=p.parse_args();require(not a.output.exists() and a.output.parent==WORK,'Fresh direct C-work review receipt required')
    result={'schema':'STAGE05_POSTBOOT_COMPLETED_GATE_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_GATE_READBACK',
      'source_sha256':sha(Path(__file__)),'kind':a.kind,'spool':str(a.spool),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'readonly_method':'Standard-library decoded receipts and SHA256; no producer imports, WSL, network, registry, signaling or lock mutation',
      'scientific_execution_or_acceptance':'NONE_NONSCIENTIFIC_GATE_ONLY','old_scope_retroactively_passed':False}
    try:
        authority=pinned(WORK/'postboot_authority_review01.json',a.authority_report_sha256)
        require(authority['state']=='PASS_CURRENT_AUTHORITY_AND_LOCAL_PUBLISHED_SOURCES' and authority['initial_remote_main']==authority['final_remote_main'],'Authority report differs')
        boot=pinned(a.boot_receipt,a.boot_receipt_sha256)
        require(boot['state']=='PASS_NEW_BOOT_CURRENT_SCOPE_RECONCILED_OLD_FAILURE_PRESERVED' and boot['old_scope_retroactively_passed'] is False
                and boot['old_STOP_removed'] is True and boot['original_lock_released'] is True,'New Windows boot reconciliation not qualified')
        last=datetime.datetime.fromisoformat(boot['current_boot']['last_boot_utc'])
        boot_filetime=int((last-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10_000_000)
        value=read(a.spool/'result.json');unlock=read(a.spool/'lock_released.json')
        require(unlock['released'] is True and unlock['state']==('EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK' if a.kind=='unc' else 'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'),'Explicit original unlock differs')
        fn=interop if a.kind=='interop' else unc if a.kind=='unc' else setup
        detail=fn(a.spool,value,authority,boot_filetime,a.linux_boot_id) if a.kind in ('interop','unc') else fn(a.kind,a.spool,value,authority,boot_filetime,a.linux_boot_id)
        result.update(state='PASS_COMPLETED_POSTBOOT_GATE_EXACT_SOURCE_CLOSURE_AND_BYTES',authority_commit=authority['final_remote_main'],
                      new_windows_boot=boot['current_boot']['last_boot_utc'],boot_receipt_sha256=a.boot_receipt_sha256,
                      actual_result_sha256=sha(a.spool/'result.json'),unlock_sha256=sha(a.spool/'lock_released.json'),detail=detail)
    except BaseException as error:result['error']={'kind':type(error).__name__,'message':str(error)}
    result['checked_files']=CHECKED
    with a.output.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':result['state'],'output':str(a.output),'error':result.get('error'),'checked_files':len(CHECKED)}))
    return 0 if result['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
