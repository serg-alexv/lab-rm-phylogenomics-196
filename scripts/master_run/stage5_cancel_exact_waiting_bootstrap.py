"""Opt-in one pidfd SIGTERM to the exact waiting first runner; no owner/lock kill."""
from pathlib import Path
import argparse, datetime, hashlib, importlib, json, math, os, signal, sys, time

WORK=Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
PROC=Path('/proc')
BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
NONCE='1439a454dde8448f8f9606b6de6ac702'
ACC='GCF_000009425.1'
CONFIG=WORK/'stage5_actual_backing_01.json'
OWNER_DIR=WORK/'stage5_owner_GCF_000009425_1_backing_01'
LEASE=OWNER_DIR/'owner_lease.json'
OUT=WORK/'stage5_cancel_exact_waiting_GCF_000009425_1_01'
GENOME=Path('/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/.work/stage05_atomic_v1')/ACC
TRANSACTION=GENOME/'transactions/attempt_0001'
INTERPRETER='/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/detector_env/bin/python'
INTERPRETER_SHA='4642463c684dc60366e0b15e31c16a3c350ab42720a5e4737757b82424b80f99'
ARGV=[INTERPRETER,'-B',str(WORK/'stage5_atomic.py'),'--config',str(CONFIG),'run','--accession',ACC,'--owner-lease',str(LEASE),'--owner-nonce',NONCE]
LOCK={'path':r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock',
      'volume_serial':2430728143,'file_index':844424932784519,'creation_filetime':134359335921635133,'locked_byte':0}
WINDOWS_OWNER=(24488,'134360766940521715')
PINS={'stage5_atomic.py':'500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04',
      'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
      'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
      'stage5_actual_backing_01.json':'30a86eb18cddc69eb0cfbdd3ae93473ec54812cd5a859ededd25af01fb737dfa',
      'stage5_owner_GCF_000009425_1_backing_01/owner.json':'37eeca75a126a5daae7b64b152542c49c8accf79afd3d9595aa458a0c728a58a',
      'stage5_owner_GCF_000009425_1_backing_01/GCF_000009425.1.launch.json':'e846cf1448074dacc7cd420eb2fdb850303c743a529c5235a6f3f97040f93995'}

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def read(path,cap=65536):
    with Path(path).open('rb') as f:data=f.read(cap+1)
    require(len(data)<=cap,'Bounded exact metadata required');return json.loads(data)

def atomic(path,value):
    tmp=path.with_name(path.name+'.partial')
    with tmp.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def fixed_controls(source_sha):
    require(sha(__file__)==source_sha and all(sha(WORK/n)==pin for n,pin in PINS.items()),'Exact frozen cancellation/source/config/owner controls differ')
    require((PROC/'sys/kernel/random/boot_id').read_text().strip()==BOOT,'Exact current Linux boot differs')
    launch=read(OWNER_DIR/(ACC+'.launch.json'))
    require(launch['owner_nonce']==NONCE and launch['argv'][6:]==ARGV,'Exact retained Windows launch differs')

def owner_binding(lease):
    require(lease.get('schema')=='STAGE05_WINDOWS_OWNER_LEASE_V1' and lease.get('workflow_lock_held') is True
            and lease['nonce']==NONCE and type(lease['owner_pid']) is int and type(lease['owner_creation_filetime']) is str
            and (lease['owner_pid'],lease['owner_creation_filetime'])==WINDOWS_OWNER,'Exact current original Windows owner differs')
    value=lease['workflow_lock']
    require(type(value) is dict and set(value)==set(LOCK) and all(type(value[k]) is type(v) and value[k]==v for k,v in LOCK.items()),'Exact original lock binding differs')

def waiting(P,policy):
    lease=P.check_lease(LEASE,NONCE,policy);owner_binding(lease)
    latest=read(TRANSACTION/'latest_admission.json');owner_binding(latest['windows_owner_lease'])
    stamp=datetime.datetime.fromisoformat(latest['utc']);require(stamp.tzinfo is not None,'Timezone-bound waiting timestamp required')
    age=time.time()-stamp.timestamp()
    wait=latest['wait_seconds']
    observed_policy=latest['policy']
    require(type(observed_policy) is dict and set(observed_policy)==set(policy)
            and all(type(observed_policy[k]) is type(v) and observed_policy[k]==v for k,v in policy.items()),'Exact waiting policy differs')
    require(latest['admitted'] is False and 0<=age<=6
            and type(wait) in (int,float) and math.isfinite(wait) and 0<=wait<1800,'Fresh exact waiting admission required')
    forbidden=[GENOME/n for n in ('execution','bundle','inventory','raw_validation','scientific_identity.json','complete.json','status.json')]
    forbidden += [TRANSACTION/'admission.json',TRANSACTION/'status.json',OWNER_DIR/'result.json',OWNER_DIR/'lock_released.json']
    require(not any(p.exists() or p.is_symlink() for p in forbidden),'Runner has left exact initial no-native waiting scope')
    require(sorted(p.name for p in TRANSACTION.parent.iterdir())==['attempt_0001'],'Exact first transaction scope differs')
    initial=read(TRANSACTION/'initial_owner_lease.json');owner_binding(initial)
    return {'latest_admission_sha256':sha(TRANSACTION/'latest_admission.json'),'admitted':False,'wait_seconds':wait,
            'observed_native_execution_paths_absent':True,'current_owner_lease_sha256':sha(LEASE)}

def identity(P,pid):
    row=P.proc_record(pid);require(row and pid>1 and pid!=os.getpid() and row['state'] not in ('Z','X'),'Live distinct runner required')
    with (PROC/str(pid)/'cmdline').open('rb') as f:raw=f.read(8193)
    require(raw==b'\0'.join(x.encode() for x in ARGV)+b'\0','Exact full Linux bootstrap argv differs')
    exe=os.readlink(PROC/str(pid)/'exe')
    require(exe==str(Path(INTERPRETER).resolve()) and sha(PROC/str(pid)/'exe')==INTERPRETER_SHA,'Exact retained interpreter/source identity differs')
    require(not (PROC/str(pid)/'task'/str(pid)/'children').read_text().split(),'Exact waiting bootstrap has children')
    chain=[];child=row
    for _ in range(8):
        parent=P.proc_record(child['ppid'])
        require(parent and parent['state'] not in ('Z','X') and int(parent['start_ticks'])<=int(child['start_ticks'])
                and os.readlink(PROC/str(parent['pid'])/'exe')=='/init','Live exact /init ancestry required')
        chain.append({k:parent[k] for k in ('pid','ppid','pgid','sid','start_ticks')})
        if parent['pid']==1:break
        child=parent
    require(chain and chain[-1]['pid']==1,'Bounded /init ancestry did not reach PID1')
    return {'runner':{k:row[k] for k in ('pid','ppid','pgid','sid','start_ticks')},'init_ancestry':chain,'executable':exe,'argv':ARGV}

def discover(P):
    entries=[p for p in PROC.iterdir() if p.name.isdigit()];require(len(entries)<=4096,'Bounded process inventory exceeded')
    found=[];wanted=b'\0'.join(x.encode() for x in ARGV)+b'\0'
    for p in entries:
        try:
            with (p/'cmdline').open('rb') as f:raw=f.read(8193)
            if raw==wanted:found.append(int(p.name))
        except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    require(len(found)==1,'Exactly one fixed full-argv bootstrap required; otherwise await natural expiry')
    return identity(P,found[0])

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--source-sha256');args=ap.parse_args()
    if not args.run:
        print(json.dumps({'state':'PREPARED_NOT_RUN','signal_count':0,'fallback':'NATURAL_1800_SECOND_ADMISSION_EXPIRY','owner_lock_or_Windows_kill':False}));return 0
    require(sys.platform=='linux' and os.geteuid()==0 and Path(__file__).resolve()==WORK/Path(__file__).name,'Exact root Linux cancellation entry required')
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Finite20second cancellation deadline expired')));signal.alarm(20)
    fixed_controls(args.source_sha256);require(not OUT.exists() and OUT.parent.resolve()==WORK,'Fresh fixed direct C cancellation spool required');OUT.mkdir()
    result={'schema':'STAGE05_EXACT_WAITING_BOOTSTRAP_CANCEL_V1','state':'NO_SIGNAL_PRECONDITION_FAILED_NATURAL_EXPIRY',
            'source_sha256':args.source_sha256,'boot_id':BOOT,'owner_nonce':NONCE,'signal_attempted':False,
            'signal_returned_successfully':False,'target_termination_or_owner_unlock_proven':False,'native_child_or_Windows_owner_signal':False,
            'scope':'ONE_EXACT_WAITING_LINUX_BOOTSTRAP_PIDFD_SIGTERM_ONLY','fallback':'NATURAL_1800_SECOND_ADMISSION_EXPIRY'}
    fd=None
    try:
        P=importlib.import_module('stage5_atomic_process');W=importlib.import_module('stage5_work_storage');config=read(CONFIG)
        W.validate_storage(config);result['waiting_observation']=waiting(P,config['resource_policy']);observed=discover(P)
        fd=P.verified_pidfd(observed['runner']);require(fd is not None,'Exact retained target birth vanished; no signal')
        require(identity(P,observed['runner']['pid'])==observed,'Target birth/argv/interpreter/ancestry changed after pidfd retention')
        fixed_controls(args.source_sha256);W.validate_storage(config);result['waiting_observation']=waiting(P,config['resource_policy'])
        require(identity(P,observed['runner']['pid'])==observed,'Exact target identity changed before signal')
        result['target']=observed;atomic(OUT/'signal_intent.json',result)
        result['pre_signal_waiting_observation']=waiting(P,config['resource_policy'])
        require(identity(P,observed['runner']['pid'])==observed and (PROC/'sys/kernel/random/boot_id').read_text().strip()==BOOT,
                'Exact target/current boot changed after durable intent; no signal')
        result['signal_attempted']=True;P.send_pidfd_signal(fd,signal.SIGTERM);result['signal_returned_successfully']=True
        result['state']='SIGTERM_REQUEST_SENT_ORIGINAL_OWNER_TERMINAL_AND_UNLOCK_REQUIRED'
    except BaseException as error:
        result['error_kind']=type(error).__name__
        if result['signal_attempted']:result['state']='SIGNAL_ATTEMPT_UNCERTAIN_ORIGINAL_OWNER_TERMINAL_REQUIRED'
    finally:
        signal.alarm(0)
        if fd is not None:
            try:os.close(fd);result['pidfd_closed']=True
            except BaseException as error:result.update(pidfd_closed=False,pidfd_close_error_kind=type(error).__name__)
        result['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();atomic(OUT/'result.json',result)
    print(json.dumps({'state':result['state'],'result':str(OUT/'result.json')}))
    return 0 if result['signal_returned_successfully'] and result.get('pidfd_closed') is True else 2

if __name__=='__main__':raise SystemExit(main())
