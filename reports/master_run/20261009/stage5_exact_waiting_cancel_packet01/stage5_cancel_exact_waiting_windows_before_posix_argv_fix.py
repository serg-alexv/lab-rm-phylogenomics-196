"""Opt-in retained WSL control client; existing science owner retains its lock."""
from pathlib import Path
import argparse, ctypes, hashlib, importlib, json, os, stat, subprocess, sys, uuid

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
WINDOWS_WORK=WORK
WSL=r'C:\Windows\System32\wsl.exe'
WSL_SHA='fcd08205b608b5c4831e0dcb1801dd274436cd2c8420815f18ae58a085891a18'
OUT=WORK/'stage5_cancel_exact_waiting_windows_01'
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
      'stage5_unc_bind_probe.py':'0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d',
      'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
      'stage5_cancel_exact_waiting_bootstrap.py':'7b02c2f05750371dbb9dca9026a86318054f41cdb0214aa22182bbf34da6c63b'}

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def load_pinned(name):
    require(sha(WORK/name)==PINS[name],'Exact published control dependency differs')
    module=importlib.import_module(Path(name).stem)
    require(Path(module.__file__).resolve()==WORK/name and sha(module.__file__)==PINS[name],'Imported control dependency differs')
    return module

def drain_windows_job(*args,**kwargs):
    return load_pinned('stage5_unc_bind_probe.py').drain_windows_job(*args,**kwargs)

def wsl_control_job(api, argv, owner, evidence):
    """One named job; persist exact birth/exit before finite full-job drain.

    A80 remains unchanged. Root exit is distinct from job emptiness. Only this
    newly created job/root can be terminated; unknown closure stays fatal.
    """
    evidence = Path(evidence)
    require(WINDOWS_WORK in evidence.parents and evidence == evidence.resolve()
            and not evidence.exists(), 'Fresh C Windows worker evidence required')
    for parent in evidence.parents:
        info=parent.lstat()
        require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                and not parent.is_symlink(), 'Windows worker evidence ancestry alias')
    evidence.mkdir()
    A=load_pinned('atomic_iqtree_windows.py')
    record={'schema':'STAGE05_OWNED_WINDOWS_IO_JOB_V2','state':'FAILED', 'argv':argv,
            'owner':owner,'source_sha256':sha(__file__),'api_sha256':PINS['atomic_iqtree_windows.py'],
            'job_name':'Local\\LAB_RM_STAGE5_IO_'+uuid.uuid4().hex,'drain_samples':[],
            'owned_closure_proven':True,'created':False,'assigned':False}
    def persist(value):A.atomic(evidence/'progress.json',value)
    job=None;process=api.PROCESS();birth=None;original=None;closure=None
    try:
        ctypes.set_last_error(0);job=api.create_job(None,record['job_name'])
        api.ok(job,'Create exact named Windows I/O job')
        require(ctypes.get_last_error()!=183,'Named owned job already exists; never adopt')
        persist(record)
        limits=api.EXTENDED();limits.BasicLimitInformation.LimitFlags=0x2000|0x8
        limits.BasicLimitInformation.ActiveProcessLimit=1
        api.ok(api.set_job(job,9,ctypes.byref(limits),ctypes.sizeof(limits)),'Set owned Windows I/O job')
        startup=api.STARTUP();startup.cb=ctypes.sizeof(startup)
        command=ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        api.ok(api.create(str(WSL),command,None,None,False,0x4|0x08000000,
                          None,str(WORK),ctypes.byref(startup),ctypes.byref(process)), 'Create suspended Windows I/O child')
        record.update(created=True,owned_closure_proven=False)
        birth=api.identity(process.hProcess,process.dwProcessId);record['birth']=birth
        # Persist even if subsequent image validation/assignment/resume fails.
        A.atomic(evidence/'launch.json',record)
        require(Path(birth['executable']).resolve()==Path(WSL).resolve(),'Actual Windows worker image differs')
        api.ok(api.assign(job,process.hProcess),'Assign exact Windows I/O child');record['assigned']=True
        persist(record)
        require(api.resume(process.hThread)==1,'Resume exact Windows I/O child suspend count differs')
        require(api.wait(process.hProcess,20000)==0,'Owned Windows I/O root exceeded20s')
        final=api.identity(process.hProcess,process.dwProcessId,birth['executable'],birth['session_id'])
        record['exit']=final;A.atomic(evidence/'root_exit.json',record)
        require(final['creation_filetime']==birth['creation_filetime'] and final['exited']
                and final['exit_filetime']>final['creation_filetime'],
                'Exact retained Windows worker root exit differs')
        closure=drain_windows_job(api,job,process.hProcess,record,persist)
        record.update(owned_closure_proven=True,owned_job=closure)
        require(final['exit_code']==0,'Owned Windows worker exited nonzero after closed scope')
        record['state']='PASS_EXACT_RETAINED_ROOT_EXIT0_AND_EMPTY_NAMED_JOB'
    except BaseException as error:
        original=error
        record['original_error']={'kind':type(error).__name__,'message':str(error),
                                  'winerror':getattr(error,'winerror',None)}
    finally:
        if record['created'] and not record['owned_closure_proven']:
            try:
                if record['assigned']:
                    api.ok(api.terminate_job(job,2),'Terminate only exact owned failed Windows job')
                else:
                    api.ok(api.terminate(process.hProcess,2),'Terminate exact unassigned suspended child')
                def failed_root_terminal():
                    final=api.identity(process.hProcess,process.dwProcessId,
                        birth['executable'] if birth else str(WSL),
                        birth['session_id'] if birth else owner['session_id'])
                    if birth:require(final['creation_filetime']==birth['creation_filetime'],'Failed retained root birth differs')
                    require(final['exited'] and final['exit_filetime']>final['creation_filetime'],
                            'Failed retained root terminal birth/exit time unproven')
                    record['exit']=final;A.atomic(evidence/'root_exit.json',record)
                closure=drain_windows_job(api,job,process.hProcess,record,persist,root_terminal=failed_root_terminal)
                record.update(owned_job=closure,owned_closure_proven=True)
            except BaseException as error:
                record['closure_error']={'kind':type(error).__name__,'message':str(error),
                                         'winerror':getattr(error,'winerror',None)}
        close_errors=[]
        for name,handle in [('thread',process.hThread),('process',process.hProcess),('job',job)]:
            if handle:
                try:api.ok(api.close(handle),'Close exact owned '+name+' handle')
                except BaseException as error:close_errors.append({'handle':name,'kind':type(error).__name__,'message':str(error)})
        if close_errors:record.update(state='FAILED',handle_close_errors=close_errors)
        try:A.atomic(evidence/'result.json',record)
        except BaseException as error:
            record['result_write_error']={'kind':type(error).__name__,'message':str(error)}
            if original is None:original=error
    if not record['owned_closure_proven']:
        raise A.OwnedClosureFailure('Owned Windows I/O closure unproven; see '+str(evidence/'result.json')) from original
    if original is not None:raise original
    require(not close_errors and 'result_write_error' not in record,'Owned Windows worker finalizer failed; see receipt')
    return record

def current_authority(A,C,P,api,handle):
    control=A.read_json(Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\status\run_control.json'))
    require(control.get('state')=='ACTIVE_DIRECT_USER_CONTINUATION' and control.get('automatic_resume') is False,
            'Fresh direct continuation authority absent')
    require(not A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json').exists(),'Original owner closure STOP present')
    require(not any((WORK/'stage5_owner_GCF_000009425_1_backing_01'/n).exists() for n in ('result.json','lock_released.json')),
            'Original science owner already terminal; await its existing closure')
    for name,pin in C.PINS.items():require(sha(WORK/name)==pin,'Pinned original science controls differ')
    config=C.read(WORK/'stage5_actual_backing_01.json')
    lease=P.check_lease(WORK/'stage5_owner_GCF_000009425_1_backing_01/owner_lease.json',C.NONCE,config['resource_policy']);C.owner_binding(lease)
    expected=C.read(WORK/'stage5_owner_GCF_000009425_1_backing_01/owner.json')['owner']
    actual=api.identity(handle,C.WINDOWS_OWNER[0],expected['executable'],expected['session_id'])
    require(not actual['exited'] and actual['pid']==C.WINDOWS_OWNER[0]
            and str(actual['creation_filetime'])==C.WINDOWS_OWNER[1] and actual['executable']==expected['executable']
            and actual['session_id']==expected['session_id'],'Retained original science Windows owner birth differs')
    return {'original_owner':actual,'original_lock_binding':lease['workflow_lock'],'owner_nonce':C.NONCE}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--source-sha256');args=ap.parse_args()
    if not args.run:
        print(json.dumps({'state':'PREPARED_NOT_RUN','WSL_clients_created':0,'second_workflow_lock':False,'fallback':'NATURAL_1800_SECOND_ADMISSION_EXPIRY'}));return 0
    require(os.name=='nt' and Path(__file__).resolve().parent==WORK and os.environ.get('COMPUTERNAME','').casefold()=='wd',
            'Exact WD Windows C control entry required')
    require(sha(__file__)==args.source_sha256 and sha(WSL)==WSL_SHA and not OUT.exists(),'Exact frozen control source/WSL and fresh spool required')
    for path in (OUT.parent,*OUT.parent.parents):
        require(not path.is_symlink() and not getattr(path.lstat(),'st_file_attributes',0)&0x400,'C control ancestry alias rejected')
    A=load_pinned('atomic_iqtree_windows.py');load_pinned('stage5_unc_bind_probe.py')
    C=load_pinned('stage5_cancel_exact_waiting_bootstrap.py');P=load_pinned('stage5_atomic_process.py')
    api=A.Win();owner=api.identity(api.current(),os.getpid());open_process=api.K.OpenProcess
    open_process.restype=ctypes.c_void_p;open_process.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32]
    handle=open_process(0x101000,False,C.WINDOWS_OWNER[0]);api.ok(handle,'Retain original Windows owner query-only handle')
    result={'schema':'STAGE05_EXACT_WAITING_CANCEL_WINDOWS_CONTROL_V1','state':'FAILED',
            'source_sha256':args.source_sha256,'source_pins':PINS,'original_owner_termination_or_unlock_proven':False,
            'second_workflow_lock':False,'original_science_owner_or_science_client_signaled':False,'WSL_clients_created':0}
    try:
        result.update(current_authority(A,C,P,api,handle))
        resources=api.resources([WORK]);require(resources['physical_available_bytes']>=512*1024**2
            and resources['commit_headroom_bytes']>=512*1024**2 and all(x>=16*1024**2 for x in resources['disk_available_bytes'].values()),
            'Small retained control client resource admission failed')
        OUT.mkdir();result['resources']=resources
        argv=[WSL,'-d','Ubuntu','-u','root','--exec',C.INTERPRETER,'-B',str(C.WORK/'stage5_cancel_exact_waiting_bootstrap.py'),
              '--run','--source-sha256',PINS['stage5_cancel_exact_waiting_bootstrap.py']]
        require(sha(__file__)==args.source_sha256 and sha(WSL)==WSL_SHA
                and all(sha(WORK/n)==pin for n,pin in PINS.items()),'Frozen control source changed before client launch')
        result.update(current_authority(A,C,P,api,handle));A.atomic(OUT/'intent.json',{**result,'argv':argv})
        result['WSL_clients_created']=1
        result['control_client']=wsl_control_job(api,argv,owner,OUT/'wsl_control_client')
        linux=OUT.parent/'stage5_cancel_exact_waiting_GCF_000009425_1_01/result.json'
        terminal=C.read(linux)
        require(terminal['source_sha256']==PINS['stage5_cancel_exact_waiting_bootstrap.py'] and terminal['boot_id']==C.BOOT
                and terminal['owner_nonce']==C.NONCE and terminal['signal_returned_successfully'] is True and terminal['pidfd_closed'] is True
                and terminal['target_termination_or_owner_unlock_proven'] is False,'Exact Linux signal-request receipt differs')
        result.update(state='PASS_CONTROL_CLIENT_CLOSED_SIGNAL_REQUESTED_ORIGINAL_OWNER_CLOSURE_REQUIRED',linux_result_sha256=sha(linux))
    except BaseException as error:
        result['error_kind']=type(error).__name__
        if isinstance(error,A.OwnedClosureFailure):result['state']='CONTROL_CLIENT_CLOSURE_UNPROVEN_ROOT_RECONCILIATION_REQUIRED'
    finally:
        try:api.ok(api.close(handle),'Close retained original owner query-only handle');result['original_owner_query_handle_closed']=True
        except BaseException as error:result.update(state='FAILED_QUERY_HANDLE_CLOSE',query_close_error_kind=type(error).__name__)
        if OUT.exists():A.atomic(OUT/'result.json',{**result,'utc':A.utc()})
    print(json.dumps({'state':result['state'],'result':str(OUT/'result.json')}))
    return 0 if result['state']=='PASS_CONTROL_CLIENT_CLOSED_SIGNAL_REQUESTED_ORIGINAL_OWNER_CLOSURE_REQUIRED' else 2

if __name__=='__main__':raise SystemExit(main())
