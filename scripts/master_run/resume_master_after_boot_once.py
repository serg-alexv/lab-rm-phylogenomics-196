"""Default-noop, one-shot post-reboot Codex launch. No reboot/registration/STOP mutation.

Private manifest, stdin prompt and CLI output are deliberately NOT public inputs.
This launch-only helper never signals/waits for scientific processes or claims
their closure. Existing project owners retain their operational guards.
"""
from pathlib import Path
import argparse, ctypes, datetime, hashlib, json, os, re, subprocess, time, urllib.request, uuid

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PRIVATE=WORK/'private_master_boot_resume01'
MANIFEST=PRIVATE/'PRIVATE_HANDOFF_DO_NOT_PUBLISH.json'
CODEX=Path(r'C:\Users\wheel\AppData\Local\OpenAI\Codex\bin\9691020b546a15b2\codex.exe')
PYTHON=Path(r'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
POWERSHELL=Path(r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe')
STOP=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\stage05_owned_closure_unproven.json')
EXPECTED_STOP='3de7057780d280d5f204b535207a174e616ca425b5638fe9848a48cfca20838a'
REPO='serg-alexv/lab-rm-phylogenomics-196'
PUBLISHED_ANCHOR='e4f0fd84932f9a414abfb7b1439ee21b97a1a571'
CONTROLS=('AGENTS.md','WORK_ORDER.md','STATUS.md','status/stages.tsv','status/master_run_20261009.json')
PUBLIC_PROMPT='''Continue the human-authorized master LAB R-M phylogenomics project after a Windows restart.
GitHub serg-alexv/lab-rm-phylogenomics-196 main is the project authority. Read the
fresh immutable GitHub authority snapshot and new-boot receipt in work/private_master_boot_resume01;
re-read current remote main before any project mutation or biological compute.
Read AGENTS.md, WORK_ORDER.md, STATUS.md, status/stages.tsv and the master status.
The preserved old DriveFS02 Windows worker STOP is still authoritative until an
explicit independently reviewed new-boot reconciliation proves its scope closed.
The corrected benign fixture does not prove that old scope. Do not clear STOP,
start WSL, launch scientific work or repeat accepted stages merely because this
launcher resumed. Reconcile current boot, accepted scientific inputs, mounted
runtime/storage, exact resources and original WorkflowLock first. Continue the
same accepted stages and serial per-genome policy using current published code;
publish each completed step. Keep the session ID, private handoff and raw CLI
stdout/stderr private. This is one invocation, not a recurring automation; do not
alter the project's automatic_resume policy. Any missing authority/closure proof
must remain explicit. Existing per-job owner guards remain in force.
'''

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def no_alias(path):
    path=Path(path)
    require(path.is_absolute() and path==path.resolve(),'Absolute canonical path required')
    for item in (path,*path.parents):
        s=item.lstat()
        require(not item.is_symlink() and not getattr(s,'st_file_attributes',0)&0x400,'Reparse/alias rejected')

def write_new(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())

def boot_observation():
    require(os.name=='nt','Windows only')
    tick=ctypes.WinDLL('kernel32',use_last_error=True).GetTickCount64
    tick.argtypes=[];tick.restype=ctypes.c_ulonglong
    before=tick()
    result=subprocess.run([str(POWERSHELL),'-NoLogo','-NoProfile','-NonInteractive','-Command',
        "(Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).LastBootUpTime.ToUniversalTime().ToString('o')"],
        capture_output=True,text=True,timeout=15,creationflags=0x08000000,check=True)
    after=tick();stamp=result.stdout.strip()
    parsed=datetime.datetime.fromisoformat(stamp.replace('Z','+00:00'))
    require(parsed.tzinfo is not None and 0<=after-before<15000,'Boot query bracket invalid')
    return {'last_boot_utc':parsed.isoformat(),'tick_before_ms':before,'tick_after_ms':after,
        'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}

def new_boot(before,after):
    require(datetime.datetime.fromisoformat(after['last_boot_utc'])>
            datetime.datetime.fromisoformat(before['last_boot_utc']),'LastBootUpTime did not advance')
    require(after['tick_after_ms']<before['tick_before_ms'],'GetTickCount64 did not reset')
    require(0<=after['tick_before_ms']<=after['tick_after_ms']<2*60*60*1000,'New-boot handoff limited to first2h')

def exact_uuid(value):
    require(isinstance(value,str) and str(uuid.UUID(value))==value.lower(),'Explicit canonical thread UUID required')

def cli_command(thread):
    exact_uuid(thread)
    return [str(CODEX),'exec','-c','approval_policy="never"','-c','sandbox_mode="danger-full-access"',
        '-C',str(WORK.parent),'resume','--skip-git-repo-check','--json',
        '--output-last-message',str(PRIVATE/'PRIVATE_LAST_MESSAGE_DO_NOT_PUBLISH.txt'),thread,'-']

def retained_cli_birth(child):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    get_times=kernel.GetProcessTimes
    get_times.argtypes=[ctypes.c_void_p,*([ctypes.POINTER(ctypes.c_ulonglong)]*4)]
    get_times.restype=ctypes.c_int
    values=[ctypes.c_ulonglong() for _ in range(4)]
    require(get_times(int(child._handle),*(ctypes.byref(v) for v in values))!=0,'Retained CLI birth unavailable')
    query=kernel.QueryFullProcessImageNameW
    query.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_ulong)]
    query.restype=ctypes.c_int
    buffer=ctypes.create_unicode_buffer(32768);length=ctypes.c_ulong(len(buffer))
    require(query(int(child._handle),0,buffer,ctypes.byref(length))!=0,'Retained CLI image unavailable')
    require(Path(buffer.value)==CODEX and values[0].value>0,'Retained CLI image/birth differs')
    return {'pid':child.pid,'creation_filetime':values[0].value,'observed_exit_filetime':values[1].value,
        'executable':buffer.value,'retained_Popen_process_handle':True}

def fetch(url,deadline):
    require(time.monotonic()<deadline,'Authority deadline exceeded')
    request=urllib.request.Request(url,headers={'User-Agent':'LAB-RM-one-shot-resume-readonly','Accept':'application/vnd.github+json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request,timeout=min(20,max(1,deadline-time.monotonic()))) as response:
        require(response.status==200 and response.geturl()==url,'Unexpected authority response/redirect')
        data=bytearray()
        while block:=response.read(65536):
            require(time.monotonic()<deadline and len(data)+len(block)<=2*1024*1024,'Authority size/deadline exceeded')
            data.extend(block)
    return bytes(data)

def fresh_authority(manifest):
    deadline=time.monotonic()+180
    api='https://api.github.com/repos/'+REPO
    head=json.loads(fetch(api+'/git/ref/heads/main',deadline))['object']['sha']
    require(re.fullmatch('[0-9a-f]{40}',head) is not None,'Invalid remote main')
    comparison=json.loads(fetch(api+'/compare/'+manifest['published_anchor']+'...'+head,deadline))
    require(comparison['status'] in ('ahead','identical'),'Main is not published-anchor descendant')
    target=PRIVATE/'authority_snapshot';target.mkdir()
    files={}
    sources={
        'scripts/master_run/resume_master_after_boot_once.py':manifest['helper_sha256'],
        'scripts/master_run/Resume-MasterAfterBootOnce.ps1':manifest['launcher_sha256'],
    }
    for name in (*CONTROLS,*sources):
        data=fetch('https://raw.githubusercontent.com/'+REPO+'/'+head+'/'+name,deadline)
        digest=hashlib.sha256(data).hexdigest()
        if name in sources:require(digest==sources[name],'Current published resume source differs')
        path=target.joinpath(*name.split('/'));path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        files[name]={'bytes':len(data),'sha256':digest}
    require(json.loads(fetch(api+'/git/ref/heads/main',deadline))['object']['sha']==head,'Remote main changed during handoff')
    report={'schema':'MASTER_POSTBOOT_FRESH_AUTHORITY_V1','state':'PASS_READ_ONLY_IMMUTABLE_MAIN_SNAPSHOT',
        'commit':head,'files':files,'science_authority':False}
    write_new(PRIVATE/'authority.json',report)
    return report

def prepare_private():
    require(os.name=='nt' and Path(__file__).resolve().parent==WORK,'Exact C Windows preparation required')
    require(not PRIVATE.exists(),'Private namespace already exists; preserve it')
    no_alias(WORK);no_alias(STOP);no_alias(CODEX);no_alias(PYTHON)
    require(sha(STOP)==EXPECTED_STOP,'Original STOP drift')
    thread=os.environ.get('CODEX_THREAD_ID')
    exact_uuid(thread)
    # The value is copied directly into private local control, never stdout/public.
    baseline=boot_observation();PRIVATE.mkdir()
    manifest={'schema':'PRIVATE_MASTER_BOOT_RESUME_HANDOFF_V1','thread_id':thread,
        'baseline':baseline,'stop_sha256':EXPECTED_STOP,'published_anchor':PUBLISHED_ANCHOR,
        'codex_sha256':sha(CODEX),'python_sha256':sha(PYTHON),
        'helper_sha256':sha(__file__),'launcher_sha256':sha(WORK/'Resume-MasterAfterBootOnce.ps1')}
    write_new(MANIFEST,manifest)
    print(json.dumps({'state':'PRIVATE_HANDOFF_PREPARED_NOT_REGISTERED','session_identity_printed':False,
        'private_directory':str(PRIVATE),'actual_reboot_or_resume':False}))

def resume_once():
    require(os.name=='nt' and Path(__file__).resolve().parent==WORK,'Exact C Windows invocation required')
    for path in (MANIFEST,STOP,CODEX,PYTHON,Path(__file__),WORK/'Resume-MasterAfterBootOnce.ps1'):no_alias(path)
    require(MANIFEST.stat().st_size<=16384,'Private control size exceeded')
    manifest=json.loads(MANIFEST.read_bytes())
    require(manifest['schema']=='PRIVATE_MASTER_BOOT_RESUME_HANDOFF_V1','Private control schema')
    exact_uuid(manifest['thread_id'])
    require(re.fullmatch('[0-9a-f]{40}',manifest['published_anchor']) is not None,'Anchor invalid')
    for path,key in ((CODEX,'codex_sha256'),(PYTHON,'python_sha256'),(Path(__file__),'helper_sha256'),
                     (WORK/'Resume-MasterAfterBootOnce.ps1','launcher_sha256')):
        require(sha(path)==manifest[key],'Pinned launch dependency drift')
    current=boot_observation();new_boot(manifest['baseline'],current)
    require(manifest['stop_sha256']==EXPECTED_STOP and sha(STOP)==EXPECTED_STOP,'Original STOP changed/absent')
    # Durable before network or CLI: consumes on failure too; never auto-rearms.
    write_new(PRIVATE/'CONSUMED_SINGLE_USE.json',{'schema':'PRIVATE_MASTER_RESUME_CONSUMPTION_V1',
        'new_boot':current,'baseline':manifest['baseline'],'state':'CONSUMED_BEFORE_AUTHORITY_AND_LAUNCH'})
    child=None
    try:
        authority=fresh_authority(manifest)
        require(sha(STOP)==EXPECTED_STOP,'STOP changed before launch')
        command=cli_command(manifest['thread_id'])
        with (PRIVATE/'PRIVATE_STDOUT_DO_NOT_PUBLISH.jsonl').open('xb') as stdout, \
             (PRIVATE/'PRIVATE_STDERR_DO_NOT_PUBLISH.txt').open('xb') as stderr:
            child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,
                cwd=WORK.parent,creationflags=0x08000000)
            birth=retained_cli_birth(child)
            write_new(PRIVATE/'cli_birth.json',birth)
            # Source-controlled small public prompt only. Exact ID is argv-private.
            child.stdin.write(PUBLIC_PROMPT.encode('utf-8'));child.stdin.close()
        write_new(PRIVATE/'launch.json',{'schema':'PRIVATE_MASTER_CODEX_LAUNCH_V1',
            'state':'LAUNCHED_HANDOFF_ONLY_NOT_CLOSURE_OR_SCIENCE_ACCEPTANCE','birth':birth,
            'codex_executable':str(CODEX),'codex_sha256':manifest['codex_sha256'],
            'authority_commit':authority['commit'],'source_sha256':sha(__file__),
            'STOP_unchanged_sha256':sha(STOP),'single_use':True,
            'retained_cli_exit_or_descendant_closure_proven':False,
            'registration_or_reboot_by_this_helper':False})
    except BaseException as error:
        # Do not include argv, prompt history, session ID or arbitrary exception text.
        write_new(PRIVATE/'FAILED_PRESERVED.json',{'state':'FAILED_CONSUMED_NO_AUTOMATIC_RETRY',
            'exception_kind':type(error).__name__,'STOP_mutation_by_helper':False,
            'cli_created':child is not None,'cli_pid_if_created':child.pid if child else None,
            'cli_closure_or_science_acceptance':False})
        raise

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group();modes.add_argument('--prepare-private',action='store_true');modes.add_argument('--resume-once',action='store_true')
    args=parser.parse_args()
    if args.prepare_private:prepare_private()
    elif args.resume_once:resume_once()
    else:print(json.dumps({'state':'PREPARED_DEFAULT_NOOP','registration':False,'reboot':False,'resume':False}))

if __name__=='__main__':main()
