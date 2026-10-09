"""Opt-in retained-client owner for one read-only paired memory observation.

No WSL configuration/mount/cache mutation, native search, install or signals.
Default is a no-op. Root must publish/review before explicitly running it.
"""
from pathlib import Path
from contextlib import nullcontext
import argparse, hashlib, importlib.util, json, os, re, stat, subprocess, time, uuid

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
LINUX_WORK='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work'
WSL=r'C:\Windows\System32\wsl.exe'
API_SHA='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
OBS_SHA='55ab4f7c96589c599bfe2fed25165faea8817cefdbf8d4f8676655d5d12b1161'
PRIOR=WORK/'stage5_setup_runtime_actual_postiq_04'
PRIOR_PINS={'result.json':'77afc8f5382f4d75a49f395863399a7d962671a5ff681e4adc1f030815536c13',
            'lock_released.json':'f95fd622a6a418553688c05bcfee82fe7c50bf8b4977a8417d226faf8e0e88cc',
            'linux_terminal.json':'3e820a15e62d69ca37360adcc3bb6a7f5b080ed4f223c07422d44334f33cb48b',
            'wsl_exit.json':'68f67c3cd3f062f1e1b2670e237e8adb0b09efc46ad568c1d81bd71f728a65ce'}
RESERVE=1536*1024**2


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def pinned_json(path,expected):
    need(path.resolve()==path and not path.is_symlink(),'Exact original C control required')
    info=path.lstat();need(stat.S_ISREG(info.st_mode) and info.st_size<1024**2
        and not getattr(info,'st_file_attributes',0)&0x400,'Bounded plain C control required')
    raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==expected,'Pinned C control differs')
    return json.loads(raw)


def load(name,expected):
    path=WORK/(name+'.py');need(sha(path)==expected and not path.is_symlink(),'Reviewed source pin differs')
    spec=importlib.util.spec_from_file_location('readonly_memory_'+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    need(sha(path)==expected,'Reviewed source changed during import');return module


def absent(path):
    try:path.lstat()
    except FileNotFoundError:return True
    return False


def prior_gate(values):
    result=values['result.json'];unlock=values['lock_released.json']
    linux=values['linux_terminal.json'];exit_receipt=values['wsl_exit.json']
    need(result['scope']=='NONSCIENTIFIC_STAGE5_SETUP_ONLY' and result['step']=='runtime'
         and result['state']=='FAILED' and result['owned_closure_proven'] is True
         and result['failed_scope_closed'] is True and result['unknown_closure_stop_preserved'] is False,
         'Actual runtime04 must remain a closed failed scope')
    need(unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['released'] is True,
         'Actual runtime04 original lock release missing')
    need(linux['schema']=='STAGE05_SETUP_LINUX_TERMINAL_V1' and linux['state']=='FAILED'
         and linux['owner_nonce']==result['owner_nonce']==exit_receipt['owner_nonce']
         and linux['owned_closure_proven'] is True and linux['remaining_direct_children']==[]
         and linux['scientific_adoption_authorized'] is False,'Actual runtime04 Linux closure differs')
    terminal=exit_receipt['terminal'];birth=exit_receipt['birth']
    need(terminal==result['actual_wsl_exit'] and terminal['exited'] is True
         and terminal['exit_code']==2 and terminal['pid']==birth['pid']
         and terminal['creation_filetime']==birth['creation_filetime']
         and terminal['exit_filetime']>terminal['creation_filetime']
         and terminal['executable']==birth['executable']==WSL,'Actual runtime04 retained client closure differs')
    return linux['bootstrap']['boot_id']


def exit_gate(birth,terminal):
    need(terminal['pid']==birth['pid'] and terminal['creation_filetime']==birth['creation_filetime']
         and terminal['session_id']==birth['session_id'] and terminal['executable']==birth['executable']==WSL
         and terminal['exited'] is True and terminal['exit_filetime']>terminal['creation_filetime'],
         'Actual retained read-only client exit not proven')


def observation_gate(value,nonce):
    need(value['schema']=='STAGE05_READ_ONLY_LINUX_MEMORY_OBSERVATION_V1'
         and value['state']=='OBSERVATION_ONLY_NO_RECLAMATION' and value['nonce']==nonce
         and value['source_sha256']==OBS_SHA and value['cache_reclamation_calls']==0
         and value['native_children_launched']==0 and value['runtime_payload_bytes_read']==0
         and re.fullmatch('[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}',value['boot_id'])
         and value['self_pid']>0,'Actual Linux read-only observation binding differs')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run:
        print(json.dumps({'state':'PREPARED_NOT_RUN','WSL_launches':0,'cache_reclamation_calls':0}));return 0
    need(os.name=='nt' and Path(__file__).resolve().parent==WORK,'Exact Windows C owner required')
    A=load('atomic_iqtree_windows',API_SHA);M=load('stage5_memory_observation',OBS_SHA)
    values={name:pinned_json(PRIOR/name,pin) for name,pin in PRIOR_PINS.items()};prior_boot=prior_gate(values)
    out=WORK/('stage5_paired_memory_observation_'+uuid.uuid4().hex);out.mkdir()
    api=A.Win();lock=A.WorkflowLock(api);owner=api.identity(api.current(),os.getpid());nonce=uuid.uuid4().hex
    stop=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
    child=None;birth=None;terminal=None;closed=False;source_sha=sha(__file__);start=time.monotonic()
    record={'schema':'STAGE05_PAIRED_READ_ONLY_MEMORY_OBSERVATION_V1','state':'FAILED_PRESERVED',
        'source_sha256':source_sha,'observation_source_sha256':OBS_SHA,'api_sha256':API_SHA,
        'owner':owner,'nonce':nonce,'prior_runtime04_pins':PRIOR_PINS,'prior_runtime04_boot_id':prior_boot,
        'signals_sent':0,'cache_reclamation_calls':0,'WSL_configuration_changes':0,'G_accesses':0,
        'runtime_payload_bytes_read':0,'scientific_acceptance_created':False,'closure_stop_created':False}
    try:
        # Explicit final release follows any required unknown-closure stop write.
        with nullcontext(lock.__enter__()) as held:
            record['workflow_lock']=held.identity;need(absent(stop),'Existing closure stop vetoes observation launch')
            record['windows_before']=M.windows_observation()
            resources=api.resources([out]);record['actual_admission']=resources
            need(resources['physical_available_bytes']>=RESERVE and resources['commit_headroom_bytes']>=RESERVE,
                 'Read-only memory observation requires current physical and commit1536MiB reserve')
            need(all(sha(PRIOR/n)==p for n,p in PRIOR_PINS.items()) and sha(WORK/'stage5_memory_observation.py')==OBS_SHA
                 and sha(WORK/'atomic_iqtree_windows.py')==API_SHA and sha(__file__)==source_sha and absent(stop),
                 'Observation inputs changed before launch')
            argv=[WSL,'-d','Ubuntu','-u','root','--exec','/usr/bin/python3','-B',
                  LINUX_WORK+'/stage5_memory_observation.py','--linux-readonly','--nonce',nonce]
            record['argv']=argv
            with (out/'linux.stdout.json').open('xb') as stdout,(out/'linux.stderr.txt').open('xb') as stderr:
                child=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
                birth=api.identity(int(child._handle),child.pid,WSL,owner['session_id']);record['retained_client_birth']=birth
                A.atomic(out/'launch.json',{'argv':argv,'retained_client_birth':birth,'nonce':nonce})
                child.wait(timeout=20)
                terminal=api.identity(int(child._handle),child.pid,birth['executable'],birth['session_id'])
                exit_gate(birth,terminal);closed=True;record['retained_client_terminal']=terminal
            need(terminal['exit_code']==0,'Read-only Linux observation failed after actual retained exit')
            need((out/'linux.stdout.json').stat().st_size<=12*1024**2
                 and (out/'linux.stderr.txt').stat().st_size<=1024**2,'Bounded observation logs exceeded')
            observed=json.loads((out/'linux.stdout.json').read_bytes());observation_gate(observed,nonce)
            record['observed_linux_boot_id']=observed['boot_id'];record['same_boot_as_runtime04']=observed['boot_id']==prior_boot
            record['windows_after']=M.windows_observation()
            need(time.monotonic()-start<=60 and absent(stop),'Observation deadline/closure-stop state changed')
            need(sha(__file__)==source_sha and sha(WORK/'stage5_memory_observation.py')==OBS_SHA
                 and sha(WORK/'atomic_iqtree_windows.py')==API_SHA
                 and all(sha(PRIOR/n)==p for n,p in PRIOR_PINS.items()),'Observation source/prior evidence changed')
            record['state']='PASS_PAIRED_READ_ONLY_OBSERVATION_NO_CAUSAL_OR_SCIENTIFIC_ACCEPTANCE'
    except BaseException as error:
        record['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        if child is not None and not closed:
            try:
                if child.poll() is not None:
                    terminal=api.identity(int(child._handle),child.pid,WSL,owner['session_id'])
                    if birth is not None:exit_gate(birth,terminal);closed=True
                    record['retained_client_terminal_after_error']=terminal
            except BaseException as error:record['closure_observation_error']=str(error)
            if not closed:
                try:
                    with stop.open('x',encoding='utf-8',newline='\n') as stream:
                        json.dump({'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1','owner_nonce':nonce,'evidence':str(out),
                            'utc':A.utc(),'reason':'Read-only memory observation retained client closure unproven',
                            'automatic_resume':False},stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
                    record['closure_stop_created']=True
                except BaseException as error:record['closure_stop_write_error']=str(error)
        if 'windows_before' in record and 'windows_after' not in record:
            try:record['windows_after']=M.windows_observation()
            except BaseException as error:record['windows_after_error']=str(error)
        try:lock.__exit__(None,None,None)
        except BaseException as error:
            record['unlock_error']=str(error);record['state']='FAILED_PRESERVED'
        for name in ('linux.stdout.json','linux.stderr.txt'):
            if (out/name).is_file():record[name+'_sha256']=sha(out/name)
        record.update(owned_readonly_client_closure_proven=closed,original_lock_explicitly_released=lock.released,
                      log_hash_scope='CLOSED_FULL_LOGS' if closed else 'PARTIAL_UNPROVEN_WRITER',
                      elapsed_seconds=time.monotonic()-start,utc=A.utc())
        if child is not None and closed:
            try:child._handle.Close()
            except BaseException as error:
                record['retained_handle_close_error']=str(error);record['state']='FAILED_PRESERVED'
        A.atomic(out/'receipt.json',record)
        if lock.released:A.atomic(out/'lock_released.json',{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True,'utc':A.utc()})
    print(json.dumps({'state':record['state'],'receipt':str(out/'receipt.json'),'sha256':sha(out/'receipt.json')}))
    return 0 if record['state'].startswith('PASS_') and closed and lock.released else 2


if __name__=='__main__':raise SystemExit(main())
