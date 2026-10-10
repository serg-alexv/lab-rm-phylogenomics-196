"""Opt-in original-lock owner for one raw recovery ZIP; no deletion or biology."""
from pathlib import Path
import argparse, base64, hashlib, importlib, json, os, re, stat, subprocess, time, uuid

WORK=Path(__file__).resolve().parent
EXACT_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
WSL=r'C:\Windows\System32\wsl.exe'
LINUX_WORK='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work'
SCOPE='ONE_CLOSED_GENOME_RAW_RECOVERY_ONLY'
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
      'stage5_atomic.py':'500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04',
      'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
      'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
      'stage5_setup_windows.py':'6aa21e4c43c3708abaea3d9fd07913222dee59d52093ddf96a24cddc6a205832',
      'stage5_windows_owner.py':'8851bc4fc48ad3069d4ffabe410e159004ef4fc8d6d0755213fc14c22fe0603d',
      'stage5_owner_lease.py':'add2cbf12ee6d51bb10168b629a8befd2136f58e5194a6e7195fea25002620b8',
      'stage5_closed_genome_archive_linux.py':'f6053d8e8ab1d21492a07b90f8c1a99ec3ab3332cde93115812ca55e375a05ef'}


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()


def c_file(path):
    path=Path(path)
    require(path.is_absolute() and path==path.resolve() and WORK in path.parents,'Canonical C-work file required')
    for item in (path,*path.parents):
        info=item.lstat();require(not item.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400,'C-work input alias/reparse forbidden')
    info=path.stat();require(stat.S_ISREG(info.st_mode) and info.st_size<=8*1024**2,'Bounded regular C metadata required')
    return path


def linux_path(path):
    path=Path(path);require(path.is_absolute() and path.drive.lower()=='c:' and WORK in path.parents,'Exact mounted C metadata path required')
    return '/mnt/c/'+'/'.join(path.parts[1:])


def captured_file(path):
    path=c_file(path);identity=lambda info:(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns)
    with path.open('rb') as stream:
        before=identity(os.fstat(stream.fileno()));require(before==identity(path.lstat()),'C owner metadata identity differs')
        raw=stream.read(8*1024**2+1)
        require(len(raw)<=8*1024**2 and identity(os.fstat(stream.fileno()))==before==identity(path.lstat()),
                'C owner metadata changed during capture')
    return raw,{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'source_identity':before,
                'base64_original_bytes':base64.b64encode(raw).decode('ascii')}


def prior_contract(config,accession,values):
    result=values['result.json'];launch=values[accession+'.launch.json'];exit_receipt=values[accession+'.exit.json']
    require(result['state']=='COMPLETE_VALIDATED' and result['scope']=='ONE_APPROVED_GENOME'
            and result['selected_accessions']==[accession] and result['approved_genomes']==196
            and result['full_panel_complete'] is False and len(result['genome_results'])==1
            and not result.get('finalizer_errors'),
            'One actual closed successful genome owner required')
    require(values['lock_released.json']['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','Previous original-lock release missing')
    row=result['genome_results'][0];born=launch['native_wsl_client'];terminal=exit_receipt['actual_wsl_client_exit']
    require(row==exit_receipt and row['accession']==accession and row['state']=='COMPLETE_VALIDATED'
            and terminal['exited'] is True and terminal['exit_code']==0
            and terminal['pid']==born['pid'] and terminal['creation_filetime']==born['creation_filetime']
            and terminal['exit_filetime']>terminal['creation_filetime']
            and terminal['executable']==born['executable']==WSL and terminal['session_id']==born['session_id'],
            'Previous retained WSL/native invocation exit differs')
    require(result['linux_script_sha256']==PINS['stage5_atomic.py']
            and result['linux_supervisor_sha256']==PINS['stage5_atomic_process.py']
            and result['storage_helper_sha256']==PINS['stage5_work_storage.py'],'Previous native/code/storage identities differ')
    nonce=launch['owner_nonce'];require(re.fullmatch('[a-f0-9]{32}',nonce),'Previous owner nonce missing')
    previous_owner=values['owner.json'];lease=values['owner_lease.json'];progress=values['progress.json']
    require(previous_owner['owner']==result['owner'] and previous_owner['selected_accessions']==[accession]
            and result['lease_helper_sha256']==PINS['stage5_owner_lease.py']
            and lease['nonce']==nonce and lease['owner_pid']==result['owner']['pid']
            and lease['owner_creation_filetime']==str(result['owner']['creation_filetime'])
            and lease['workflow_lock']==previous_owner['workflow_lock']
            and progress['finished']==progress['total']==1 and progress['approved_genomes']==196
            and progress['latest']==row and progress['genome_results']==[row],
            'Previous owner/nonce/lock/progress bindings differ')
    require(len(launch['argv'])==18 and launch['argv'][0:6]==[WSL,'-d','Ubuntu','-u','root','--exec']
            and launch['argv'][6:10]==[config['runtime']['environment_dir']+'/bin/python','-B',LINUX_WORK+'/stage5_atomic.py','--config']
            and launch['argv'][11:14]==['run','--accession',accession]
            and launch['argv'][16:]==['--owner-nonce',nonce] and launch['argv'][14]=='--owner-lease',
            'Previous actual native runner argv differs')
    return {'prior_owner_nonce':nonce,'status_sha256':row['status_sha256']}


def closed_terminal(value,argv,nonce,source_sha,exit_code):
    require(value['schema']=='STAGE05_CLOSED_GENOME_ARCHIVE_LINUX_TERMINAL_V1' and value['scope']==SCOPE
            and value['owner_nonce']==nonce and value['source_sha256']==source_sha
            and value['native_launch_count']==0 and value['owned_closure_proven'] is True
            and value['observed_prior_closure_unproven'] is False
            and (value['prior_scope_check_entered'] is False or value['prior_scope_check_complete'] is True)
            and value['remaining_direct_children']==[] and value['bootstrap']['argv']==argv[8:]
            and value['bootstrap']['executable']==argv[6]
            and re.fullmatch('[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}',value['bootstrap']['boot_id'])
            and value['bootstrap']['identity']['pid']>0 and int(value['bootstrap']['identity']['start_ticks'])>0,
            'Actual raw archive Linux identity/argv/no-child closure differs')
    require(value['state'] in ('FAILED','PASS_RAW_RECOVERY_ZIP_BYTES_ONLY')
            and exit_code==(0 if value['state']=='PASS_RAW_RECOVERY_ZIP_BYTES_ONLY' else 2),'Actual archive state/client exit differs')
    if value['state']=='PASS_RAW_RECOVERY_ZIP_BYTES_ONLY':
        require(value['prior_scope_check_entered'] is True and value['prior_scope_check_complete'] is True,
                'Successful archive lacks full prior native closure check')


def finish_after_unlock(A,lock,output,result,stop,stop_sha,nonce,closure):
    """Checked original unlock and durable receipt precede exact owned STOP clear."""
    unlocked=False;receipt_proven=False;stop_cleared=False
    try:
        lock.__exit__(None,None,None)
        require(lock.released is True,'Original explicit byte unlock did not complete')
        unlocked=True
        receipt={'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True,'utc':A.utc()}
        path=output/'lock_released.json';A.atomic(path,receipt)
        require(A.read_json(path)==receipt,'Original unlock receipt readback differs')
        result['lock_release_receipt_sha256']=sha(path);receipt_proven=True
    except BaseException as error:
        result.update(state='FAILED',unlock_or_receipt_error_kind=type(error).__name__)
    finalizers_ok=not any(key in result for key in ('lease_finalizer_error','power_finalizer_error','closure_finalizer_error'))
    if closure is True and unlocked and receipt_proven and finalizers_ok and stop_sha is not None:
        try:
            require(sha(stop)==stop_sha and A.read_json(stop)['owner_nonce']==nonce,'Archive-owned stop changed; preserve')
            stop.unlink();stop_cleared=True
        except BaseException as error:
            result.update(state='FAILED',stop_finalizer_error_kind=type(error).__name__)
    if result.get('state')=='RAW_RECOVERY_ZIP_BYTES_VALIDATED_PENDING_EXPLICIT_UNLOCK':
        result['state']='PASS_RAW_RECOVERY_ZIP_BYTES_ONLY' if closure is True and unlocked and receipt_proven and finalizers_ok and stop_cleared else 'FAILED'
    result.update(owned_closure_proven=closure is True,original_lock_explicitly_released=unlocked,
                  original_unlock_receipt_proven=receipt_proven,owned_stop_cleared_after_unlock=stop_cleared,
                  unknown_closure_stop_preserved=stop.exists(),utc=A.utc())
    try:A.atomic(output/'result.json',result)
    except BaseException as error:
        # One bounded failure publication; proven closure is not reclassified.
        result.update(state='FAILED',final_result_persistence_error_kind=type(error).__name__,
                      master_publication_reconciliation_required=True)
        failure={'schema':'STAGE05_RAW_ARCHIVE_FINAL_PUBLICATION_FAILURE_V1',
                 'state':'FAILED_FINAL_RESULT_PUBLICATION_RECONCILE_REQUIRED','owner_nonce':nonce,
                 'error_kind':type(error).__name__,'owned_closure_proven':closure is True,
                 'original_lock_explicitly_released':unlocked,'original_unlock_receipt_proven':receipt_proven,
                 'lock_release_receipt_sha256':result.get('lock_release_receipt_sha256'),
                 'owned_stop_cleared_after_unlock':stop_cleared,'unknown_closure_stop_preserved':stop.exists(),
                 'closure_facts_reclassified_as_unknown':False,'scientific_adoption_authorized':False,'utc':A.utc()}
        try:
            path=output/'publication_failure.json';A.atomic(path,failure)
            require(A.read_json(path)==failure,'Archive publication failure receipt readback differs')
            result['publication_failure_receipt_sha256']=sha(path)
        except BaseException as final_error:
            result['publication_failure_persistence_error_kind']=type(final_error).__name__
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('config','config-sha256','accession','prior-owner-result','prior-owner-result-sha256','complete-sha256','output'):
        parser.add_argument('--'+name)
    parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if not args.run:
        print(json.dumps({'state':'PREPARED_NOT_RUN','scope':SCOPE,'eviction_authorized':False,
                          'required_prior_owner_scope':'ONE_APPROVED_GENOME','maximum_compressed_asset_bytes':448*1024**2}));return 0
    require(os.name=='nt' and WORK==EXACT_WORK,'Exact Windows C archive owner required')
    require(all(sha(WORK/name)==pin for name,pin in PINS.items()),'Reviewed archive/shared helper bytes differ')
    A=importlib.import_module('atomic_iqtree_windows');S=importlib.import_module('stage5_atomic')
    O=importlib.import_module('stage5_windows_owner');T=importlib.import_module('stage5_setup_windows')
    L=importlib.import_module('stage5_owner_lease')
    config_path=c_file(args.config);require(sha(config_path)==args.config_sha256,'Explicit actual config SHA differs')
    config=S.load_config(config_path);S.approved_accession(ROOT,args.accession)
    prior=c_file(args.prior_owner_result);require(sha(prior)==args.prior_owner_result_sha256 and prior.name=='result.json','Actual previous owner receipt differs')
    require(prior.parent.parent==WORK,'Direct C previous single-genome owner spool required')
    selected=['result.json','owner.json','progress.json','lock_released.json','owner_lease.json',args.accession+'.launch.json',
              args.accession+'.exit.json',args.accession+'.stdout.txt',args.accession+'.stderr.txt']
    captured={};values={};total=0
    for name in selected:
        path=c_file(prior.parent/name);raw,captured[name]=captured_file(path);total+=len(raw)
        require(total<=16*1024**2,'Previous owner public metadata cap exceeded')
        if name.endswith('.json'):values[name]=json.loads(raw)
    proof=prior_contract(config,args.accession,values)
    require(values['result.json']['config_sha256']==args.config_sha256
            and values[args.accession+'.launch.json']['argv'][10]==linux_path(config_path)
            and values[args.accession+'.launch.json']['argv'][15]==linux_path(prior.parent/'owner_lease.json'),
            'Previous actual code/config/lease paths differ')
    for suffix in ('stdout','stderr'):
        require(captured[args.accession+'.'+suffix+'.txt']['sha256']==values[args.accession+'.exit.json'][suffix+'_sha256'],
                'Previous actual owner client log hash differs')
    require(re.fullmatch('[a-f0-9]{64}',args.complete_sha256 or ''),'Explicit successful complete SHA required')
    output=Path(args.output or '');require(output.is_absolute() and output==output.resolve() and output.parent==WORK
                                       and not output.exists(),'Fresh direct C archive spool required')
    output.mkdir();api=A.Win();owner=api.identity(api.current(),os.getpid());nonce=uuid.uuid4().hex
    lease_path=output/'owner_lease.json';stop=O.LOCAL_CLOSURE_STOP;policy=config['resource_policy'];child=None;birth=None
    closure=True;stop_sha=None;last=None;argv=None;idle_previous=None
    result={'schema':'STAGE05_CLOSED_GENOME_ARCHIVE_OWNER_V1','state':'FAILED','scope':SCOPE,'owner_nonce':nonce,
            'source_sha256':sha(__file__),'linux_source_sha256':PINS['stage5_closed_genome_archive_linux.py'],
            'accession':args.accession,'config_sha256':args.config_sha256,'complete_sha256':args.complete_sha256,
            'source_pins':PINS,'eviction_authorized':False,'owner':owner,'lease_replace_stats':{}}
    lock=A.WorkflowLock(api);lock_entered=False
    try:
        lock.__enter__();lock_entered=True
        def lease(active=True):
            nonlocal last
            if active:
                O.fresh_authority();last=api.resources([ROOT,output])
                require(last['physical_available_bytes']>=policy['windows_reserve_bytes']+policy['incremental_windows_requirement_bytes']
                        and last['commit_headroom_bytes']>=policy['commit_requirement_bytes']
                        and all(x>=policy['minimum_disk_free_bytes'] for x in last['disk_available_bytes'].values()),'Actual archive Windows resource admission failed')
            resources=last or {'physical_available_bytes':0,'commit_headroom_bytes':0,'disk_available_bytes':{}}
            now=time.time();L.atomic_owner_lease(lease_path,{'schema':'STAGE05_WINDOWS_OWNER_LEASE_V1','nonce':nonce,'workflow_lock_held':active,
                'workflow_lock':lock.identity,'owner_pid':owner['pid'],'owner_creation_filetime':str(owner['creation_filetime']),
                'measured_unix':now,'expires_unix':now+3 if active else now,'utc':A.utc(),
                'windows_available_bytes':resources['physical_available_bytes'],'windows_commit_headroom_bytes':resources['commit_headroom_bytes'],
                'disk_available_bytes':resources['disk_available_bytes']},result['lease_replace_stats'])
        try:
            O.fresh_authority();lease();result['workflow_lock']=lock.identity
            idle_previous=api.execution_state(0x80000001);require(idle_previous,'Transient archive idle-sleep prevention failed')
            require(sha(config_path)==args.config_sha256 and sha(prior)==args.prior_owner_result_sha256
                    and all(sha(prior.parent/n)==p['sha256'] for n,p in captured.items())
                    and all(sha(WORK/n)==p for n,p in PINS.items()),'Closed-owner/source controls drift before archive')
            proof.update(schema='STAGE05_CLOSED_GENOME_ARCHIVE_OWNER_SOURCE_V1',accession=args.accession,
                         config_sha256=args.config_sha256,complete_sha256=args.complete_sha256,original_owner_files=captured)
            proof_path=output/'prior_owner_proof.json';A.atomic(proof_path,proof)
            asset='release_staging/stage05_atomic_archives_v1/'+args.accession+'_'+args.complete_sha256[:12]+'_'+nonce[:8]+'.zip'
            argv=[WSL,'-d','Ubuntu','-u','root','--exec','/usr/bin/python3','-B',LINUX_WORK+'/stage5_closed_genome_archive_linux.py',
                  '--config',linux_path(config_path),'--config-sha256',args.config_sha256,'--accession',args.accession,
                  '--complete-sha256',args.complete_sha256,'--output',linux_path(output),'--owner-lease',linux_path(lease_path),
                  '--owner-nonce',nonce,'--source-sha256',PINS['stage5_closed_genome_archive_linux.py'],'--asset-relative',asset,
                  '--prior-owner-proof',linux_path(proof_path),'--prior-owner-proof-sha256',sha(proof_path)]
            A.atomic(stop,{'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1','owner_nonce':nonce,'evidence':str(output),
                           'utc':A.utc(),'reason':'Raw archive helper launch; verify retained client/Linux no-child closure','automatic_resume':False})
            stop_sha=sha(stop);closure=False
            with (output/'wsl.stdout.txt').open('xb') as stdout,(output/'wsl.stderr.txt').open('xb') as stderr:
                child=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
                birth=api.identity(int(child._handle),child.pid,WSL,owner['session_id'])
                A.atomic(output/'launch.json',{'argv':argv,'native_wsl_client':birth,'owner_nonce':nonce})
                deadline=time.monotonic()+1830
                while child.poll() is None:
                    require(time.monotonic()<deadline,'Finite raw archive client deadline expired')
                    lease();time.sleep(0.5)
                terminal=T.persist_wsl_exit(api,child,output,argv,birth,nonce,'closed-genome-archive',result['source_sha256'],result['linux_source_sha256'])
            linux=A.read_json(output/'archive_linux_terminal.json');closed_terminal(linux,argv,nonce,result['linux_source_sha256'],terminal['exit_code']);closure=True
            result.update(actual_wsl_exit=terminal,linux_terminal_sha256=sha(output/'archive_linux_terminal.json'))
            require(linux['state']=='PASS_RAW_RECOVERY_ZIP_BYTES_ONLY','Raw archive helper failed after closed scope')
            require(sha(output/'build_receipt.json')==linux['build_receipt_sha256'],'Actual raw archive build receipt hash differs')
            result['build_receipt']=A.read_json(output/'build_receipt.json');result['state']='RAW_RECOVERY_ZIP_BYTES_VALIDATED_PENDING_EXPLICIT_UNLOCK'
        except BaseException as error:result['error']={'kind':type(error).__name__,'message':str(error)}
        finally:
            try:lease(False)
            except BaseException as error:result['lease_finalizer_error']=str(error)
            if child is not None and not closure:
                try:
                    if child.poll() is None:child.wait(timeout=15)
                    terminal=T.persist_wsl_exit(api,child,output,argv,birth,nonce,'closed-genome-archive',result['source_sha256'],result['linux_source_sha256'])
                    result['actual_wsl_exit']=terminal
                    linux=A.read_json(output/'archive_linux_terminal.json');closed_terminal(linux,argv,nonce,result['linux_source_sha256'],terminal['exit_code'])
                    result['linux_terminal_sha256']=sha(output/'archive_linux_terminal.json');closure=True
                except BaseException as error:result['closure_finalizer_error']=str(error)
            if idle_previous is not None:
                try:
                    require(api.execution_state(idle_previous),'Transient archive power-state restoration failed')
                    result['power_restoration']={'requested_flags':idle_previous,'actual_api_success':True}
                except BaseException as error:result['power_finalizer_error']=str(error);result['state']='FAILED'
            result.update(owned_closure_proven=closure,unknown_closure_stop_preserved=stop.exists(),latest_actual_resources=last,utc=A.utc())
            A.atomic(output/'result.json',result)
    except BaseException as error:
        result.update(state='FAILED',owner_finalizer_error_kind=type(error).__name__)
    finally:
        if lock_entered:
            finish_after_unlock(A,lock,output,result,stop,stop_sha,nonce,closure)
        else:
            result.update(state='FAILED',original_lock_explicitly_released=False,original_unlock_receipt_proven=False,
                          owned_closure_proven=closure is True,unknown_closure_stop_preserved=stop.exists(),utc=A.utc())
            A.atomic(output/'result.json',result)
    return 0 if result['state']=='PASS_RAW_RECOVERY_ZIP_BYTES_ONLY' and closure else 2


if __name__=='__main__':raise SystemExit(main())
