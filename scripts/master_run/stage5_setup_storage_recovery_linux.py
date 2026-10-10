"""Four scoped nonscientific setup steps; Windows owns the original byte lock.

Never installs, updates, extracts, unmounts, shuts down WSL or runs detectors.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import SimpleNamespace
import argparse, hashlib, json, os, signal, stat, sys, time, uuid
import stage5_atomic_process as P
import stage5_work_storage as W

WORK = Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
ROOT = Path('/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196')
OLD = Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196')
IMAGE, TOOLS = OLD/'.tools/toolchain.ext4', OLD/'.tools/linux'
ENV = TOOLS/'detector_env'
MOUNT_LOCK = OLD/'.work/tool_mount.lock'
SCOPE = 'NONSCIENTIFIC_STAGE5_SETUP_ONLY'
PINS = {'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
        'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
        'stage5_runtime_discovery.py':'11b2a1b64512e1eab3895db017323cc25de65d31b4734d08788e99d968f44dfb',
        'stage5_drivefs_filesystem_smoke.py':'d24d86c1910ac82514a2fb7c1819d5cd1ea175dea3c5df587e8c8be2282eab2a'}
RECOVERY_PEER='stage5_first_capacity02_closed_independent_review.json'
RECOVERY_PEER_SHA='e7cb6737c50e35c3119fe443d820b77174b2e0b8f3560c5303837b95e42ac2e9'
SNAPSHOT='stage5_capacity02_closed_native_copy/snapshot.json'
SNAPSHOT_SHA='451c91caaf07d441452c4fccfaf3dfab5c488ee2b8b9988ee35cb0ceb9ac0f51'
RECOVERY_PINS={RECOVERY_PEER:RECOVERY_PEER_SHA,SNAPSHOT:SNAPSHOT_SHA,
 'stage5_setup_linux.py':'24aab72b74dd0aab6c58cac4951c30e6b1bfc9462460486748b546e50ec92e27',
 'stage5_wsl_host_profile_fallback_owner.py':'49596d3e9c0ef684978d0cbb05bc57d97b100f08ab77a7a4ece598abc2221299',
 'copy_stage5_capacity02_closed_evidence.py':'326156db364d49d8216678144d1cc1f2e939a0e9e89801fadfe5aa2a699ee2a5'}
ACCESSION='GCF_000009425.1'
BACKING_UUID='3370e495-79b5-4136-9c6b-d31c7cb6a6be'
BACKING_INODE=33554542


def recovery_sources():
    P.require(all(sha(WORK/name)==pin for name,pin in RECOVERY_PINS.items()),'Fixed closed recovery evidence/source drift')
    import stage5_setup_linux as base
    import stage5_wsl_host_profile_fallback_owner as contract
    P.require(Path(base.__file__).resolve()==WORK/'stage5_setup_linux.py'
              and Path(contract.__file__).resolve()==WORK/'stage5_wsl_host_profile_fallback_owner.py',
              'Original toolchain observer/closed-scope contract import differs')
    P.require(all(sha(WORK/name)==pin for name,pin in RECOVERY_PINS.items()),'Recovery imports changed pinned sources')
    return base,contract


def c_peer_path(value):
    path=PureWindowsPath(value);prefix=PureWindowsPath(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
    P.require(path.is_absolute() and path.drive=='C:' and prefix in path.parents
              and all(p not in ('.','..') for p in path.parts),'Exact fixed C-work peer path required')
    return WORK.joinpath(*path.relative_to(prefix).parts)


def recovery_baseline(peer,snapshot,values):
    _,contract=recovery_sources();contract.capacity_contract(peer,values)
    P.require(peer['snapshot_receipt_sha256']==SNAPSHOT_SHA and c_peer_path(peer['snapshot_receipt_path'])==WORK/SNAPSHOT
              and snapshot['state']=='PASS_EXACT_C_COPY_CLOSED_CAPACITY02_WITH_PREPARED_BACKING_HASH_INVENTORY'
              and snapshot['source_sha256']==RECOVERY_PINS['copy_stage5_capacity02_closed_evidence.py']
              and snapshot['owner_result_sha256']==peer['actual_result_sha256']
              and snapshot['native_launch_intents_observed']==0 and type(snapshot['native_launch_intents_observed']) is int,
              'Actual closed full backing snapshot binding differs')
    inventory=snapshot['backing_inventory'];P.require(isinstance(inventory,list) and len(inventory)==52,'Exact52-object baseline required')
    names=[item['member'] for item in inventory]
    P.require(names==sorted(names) and len(set(names))==len(names)
              and {PurePosixPath(name).parts[0] for name in names}=={'.native_runner.guard',ACCESSION},
              'Exact approved backing member roots differ')
    for item in inventory:
        member=PurePosixPath(item['member'])
        P.require(not member.is_absolute() and member.parts and '..' not in member.parts and '\\' not in item['member']
                  and item['kind'] in ('file','directory') and type(item['windows_unc_inode_projection']) is int
                  and item['windows_unc_inode_projection']>0,'Safe original backing member/type/inode projection required')
        P.require(not item['member'].endswith(('.launch.json','.launch_intent.json','.native_launch.json','.command.json','.closure.json')),
                  'Native execution evidence is outside this detector-free recovery scope')
        if item['kind']=='file':
            P.require(type(item['bytes']) is int and 0<=item['bytes']<32*1024**2
                      and isinstance(item['sha256'],str) and len(item['sha256'])==64
                      and all(c in '0123456789abcdef' for c in item['sha256']),'Bounded original backing file hash required')
    genome_names=[name[len(ACCESSION)+1:] for name in names if name.startswith(ACCESSION+'/')]
    P.require(genome_names==snapshot['members'] and len(genome_names)==50,'Complete50-member accession snapshot differs')
    by_name={item['member']:item for item in inventory}
    for relative,row in snapshot['files'].items():
        P.require(by_name[ACCESSION+'/'+relative]['kind']=='file'
                  and all(by_name[ACCESSION+'/'+relative][k]==row[k] for k in ('bytes','sha256')),
                  'Critical copied evidence not joined to full backing inventory')
        path=WORK/'stage5_capacity02_closed_native_copy'/relative
        P.require(sha(path)==row['sha256'] and path.stat().st_size==row['bytes'],'Copied closed preparation evidence drift')
    identity=P.read_json(WORK/'stage5_capacity02_closed_native_copy/scientific_identity.json')
    freeze=P.read_json(WORK/'stage5_capacity02_closed_native_copy/execution/execution_freeze.json')
    old_storage=P.read_json(WORK/'stage5_capacity02_closed_native_copy/transactions/attempt_0002/work_storage_proof.json')
    P.require(by_name[ACCESSION+'/scientific_identity.json']['sha256']=='bb9b7b355a55758a9085ca014eff4fbdb14a93ff5e795773b89a0e5d9ee8ee74'
              and by_name[ACCESSION+'/execution/execution_freeze.json']['sha256']=='8b0304a3489f47e181ca382d4b91f1efad65a5989953ce74b356dfb2e995f264'
              and freeze['scientific_identity']==identity==values['terminal']['scientific_identity']
              and freeze['threads']==identity['threads']==2 and len(freeze['padloc_profiles'])==5027,
              'Exact preserved scientific identity/full5027 execution freeze differs')
    P.require(old_storage['boot_id']==contract.CAPACITY_BOOT and old_storage['backing']==W.BACKING.as_posix()
              and old_storage['directory_inode']==BACKING_INODE and old_storage['filesystem_uuid']==BACKING_UUID
              and old_storage['helper_sha256']==PINS['stage5_work_storage.py'],'Original Linux backing inode/UUID/helper anchor differs')
    return by_name,old_storage


def recovery_read():
    _,contract=recovery_sources();peer=P.read_json(WORK/RECOVERY_PEER);snapshot=P.read_json(WORK/SNAPSHOT)
    directory=WORK/contract.CAPACITY_DIR
    names=['owner.json','result.json','GCF_000009425.1.launch.json','GCF_000009425.1.exit.json','progress.json',
           'owner_lease.json','lock_released.json']
    values={name:P.read_json(directory/name) for name in names}
    values['terminal']=P.read_json(c_peer_path(peer['terminal_copy_path']))
    for name,row in peer['checked_files'].items():
        relative=PureWindowsPath(name)
        P.require(not relative.is_absolute() and not relative.drive and '..' not in relative.parts,'Fixed C-work closure member required')
        path=WORK.joinpath(*relative.parts);W.canonical(path)
        P.require(path.is_file() and path.stat().st_nlink==1 and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],
                  'Independent closed file inventory drift')
    expected,old=recovery_baseline(peer,snapshot,values)
    return snapshot,expected,old


def recovery_member_check(expected,actual):
    P.require(set(actual)==set(expected),'Prepared backing full membership changed; preserve')
    for name,item in expected.items():
        row=actual[name]
        P.require(row['kind']==item['kind'],'Prepared backing object kind changed; preserve')
        if row['kind']=='file':
            P.require(row['bytes']==item['bytes'] and row['sha256']==item['sha256'],'Prepared backing payload changed; preserve')
        P.require(type(row['inode']) is int and row['inode']==item['windows_unc_inode_projection'],
                  'Prepared backing object inode differs from exact recorded projection')
    return True


def recovery_observe(expected,old):
    backing=W.canonical(W.BACKING);info=backing.lstat()
    P.require(stat.S_ISDIR(info.st_mode) and info.st_ino==BACKING_INODE,'Exact retained backing inode required')
    mountinfo=Path('/proc/self/mountinfo').read_text();rows=W.mount_rows(mountinfo)
    P.require(not any(backing in Path(row['mountpoint']).parents for row in rows),'Nested retained backing mount forbidden')
    enclosing=[row for row in rows if backing==Path(row['mountpoint']) or Path(row['mountpoint']) in backing.parents]
    parent=max(enclosing,key=lambda row:len(Path(row['mountpoint']).parts))
    P.require(parent['filesystem']=='ext4' and 'rw' in parent['options'].split(',') and 'ro' not in parent['options'].split(',')
              and parent['major_minor']==f'{os.major(info.st_dev)}:{os.minor(info.st_dev)}'
              and W.ext4_uuid(parent['source'],info.st_dev)==BACKING_UUID,'Fresh backing must retain original writable ext4 UUID')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    P.require(boot!=old['boot_id'],'Prepared recovery requires independently closed previous boot and genuinely new boot')
    actual={};pending=[backing];total=0
    while pending:
        directory=pending.pop()
        with os.scandir(directory) as entries:children=sorted(entries,key=lambda entry:entry.name)
        for entry in children:
            path=Path(entry.path);relative=path.relative_to(backing).as_posix();before=path.lstat()
            P.require(relative in expected and len(actual)<52 and before.st_dev==info.st_dev and not path.is_symlink(),
                      'Unknown, aliased or cross-device prepared backing object; preserve')
            item={'device':before.st_dev,'inode':before.st_ino,'uid':before.st_uid,'gid':before.st_gid,'mode':before.st_mode,'nlink':before.st_nlink}
            if stat.S_ISDIR(before.st_mode):item['kind']='directory';pending.append(path)
            else:
                P.require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<=before.st_size<32*1024**2,
                          'Bounded single-link plain prepared file required')
                digest=hashlib.sha256();size=0
                with os.fdopen(os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW),'rb') as stream:
                    opened=os.fstat(stream.fileno())
                    for block in iter(lambda:stream.read(1024*1024),b''):
                        size+=len(block);total+=len(block);P.require(size<32*1024**2 and total<=128*1024**2,'Prepared hashing bounds exceeded');digest.update(block)
                    after=os.fstat(stream.fileno())
                stable=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns,x.st_nlink)
                P.require(stable(before)==stable(opened)==stable(after)==stable(path.lstat()) and size==before.st_size,'Prepared file changed while hashing')
                item.update(kind='file',bytes=size,sha256=digest.hexdigest())
            actual[relative]=item
    recovery_member_check(expected,actual)
    P.require(Path('/proc/self/mountinfo').read_text()==mountinfo and backing.lstat().st_ino==BACKING_INODE
              and all(sha(WORK/name)==pin for name,pin in RECOVERY_PINS.items()),'Recovery topology/baseline/source drift')
    return {'state':'PASS_EXACT_PREPARED_BACKING_CONTENTS_PRESERVED_FRESH_LINUX_OBSERVATION',
            'snapshot_sha256':SNAPSHOT_SHA,'closure_peer_sha256':RECOVERY_PEER_SHA,'old_boot_id':old['boot_id'],'new_boot_id':boot,
            'filesystem_uuid':BACKING_UUID,'directory_inode':info.st_ino,'fresh_directory_device':info.st_dev,
            'fresh_directory_metadata':{'uid':info.st_uid,'gid':info.st_gid,'mode':info.st_mode,'nlink':info.st_nlink},
            'members':actual,'file_bytes_read':total,'prior_posix_metadata_scope':'Windows snapshot fields are projections; current UID/GID/mode are freshly observed Linux metadata',
            'deletions':0,'moves':0,'detector_launches':0}


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): digest.update(block)
    return digest.hexdigest()


def fresh_output(path, pattern):
    path = W.canonical(path)
    P.require(path.parent == WORK and path.name.startswith(pattern) and path.suffix == '.json'
              and not path.exists(), 'New direct C work JSON required')
    return path


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())


def image_uuid(block):
    P.require(len(block)==120 and block[56:58]==b'\x53\xef','Retained image ext4 magic differs')
    value=uuid.UUID(bytes=block[104:120]); P.require(value.int!=0,'Retained image UUID absent')
    return str(value)


def image_identity(path=IMAGE):
    path = W.canonical(path)
    with path.open('rb') as stream:
        a = os.fstat(stream.fileno())
        P.require(stat.S_ISREG(a.st_mode) and a.st_size == 8589934592, 'Exact retained 8GiB regular image required')
        block = os.pread(stream.fileno(), 120, 1024)
        b = os.fstat(stream.fileno())
    P.require((a.st_dev,a.st_ino,a.st_size) == (b.st_dev,b.st_ino,b.st_size), 'Retained image identity differs')
    filesystem_uuid = image_uuid(block)
    return {'path':str(path),'device':a.st_dev,'inode':a.st_ino,'bytes':a.st_size,'filesystem_uuid':filesystem_uuid,
            'whole_image_sha256':'NOT_READ_USED_RUNTIME_FILES_REQUIRE_SEPARATE_HASH_MANIFEST'}


def toolchain_observe():
    base,_=recovery_sources();return base.toolchain_observe()


def verified_toolchain(path, expected):
    base,_=recovery_sources();return base.verified_toolchain(path,expected)


def diagnostic_observation():
    """Read current boot/namespace/mount/interpreter metadata; no remediation."""
    rows=W.mount_rows(Path('/proc/self/mountinfo').read_text())
    def metadata(path):
        try:
            info=path.lstat()
            value={'path':str(path),'present':True,'device':info.st_dev,'inode':info.st_ino,
                   'bytes':info.st_size,'mode':info.st_mode,'symlink':path.is_symlink()}
            if path.is_symlink():value['link_target']=os.readlink(path)
            value['resolved_exists']=path.exists()
            return value
        except FileNotFoundError:return {'path':str(path),'present':False}
    matches=[row for row in rows if row['mountpoint']==str(TOOLS)]
    result={'schema':'STAGE05_READONLY_RUNTIME_MOUNT_DIAGNOSIS_V1','state':'OBSERVATION_ONLY_NO_RUNTIME_ACCEPTANCE',
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'self_mount_namespace':os.readlink('/proc/self/ns/mnt'),'pid1_mount_namespace':os.readlink('/proc/1/ns/mnt'),
            'pid1_identity':P.proc_record(1),'system_python_version':sys.version,'system_python_executable':sys.executable,
            'toolchain_mounts':matches,'mountpoint':metadata(TOOLS),'retained_python':metadata(ENV/'bin/python'),
            'image':image_identity(),'helper_sha256':sha(__file__),'mount_or_repair_performed':False}
    if matches:
        try:result['exact_current_toolchain_proof']=toolchain_observe()
        except Exception as error:result['toolchain_proof_error']={'kind':type(error).__name__,'message':str(error)}
    return result


def mount_lock():
    import fcntl
    descriptor = os.open(MOUNT_LOCK, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        P.require(stat.S_ISREG(os.fstat(descriptor).st_mode), 'Existing regular mount lock required')
        deadline = time.monotonic()+5
        while True:
            try:
                fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
                return descriptor
            except BlockingIOError:
                P.require(time.monotonic()<deadline,'Five-second tool mount lock wait expired')
                time.sleep(0.1)
    except BaseException:
        os.close(descriptor); raise


def main():
    import fcntl
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--step',choices=('diagnose','toolchain','runtime','storage','drivefs'),required=True)
    for name in ('output','owner-lease','owner-nonce','owner-lock-receipt','owner-lock-sha256','source-sha256',
                 'toolchain-proof','toolchain-proof-sha256','candidate-output'):
        parser.add_argument('--'+name,required=name in ('output','owner-lease','owner-nonce','source-sha256'))
    parser.add_argument('--recover-prepared',action='store_true')
    parser.add_argument('--closure-review-sha256');parser.add_argument('--recovery-snapshot-sha256')
    args=parser.parse_args()
    P.require(args.recover_prepared and args.step=='storage' and args.closure_review_sha256==RECOVERY_PEER_SHA
              and args.recovery_snapshot_sha256==SNAPSHOT_SHA,'Only exact published prepared storage recovery is permitted')
    P.require(sys.platform=='linux' and os.geteuid()==0 and Path(__file__).resolve().parent==WORK,
              'Exact root-owned mounted-C Linux setup required')
    P.require(sha(__file__)==args.source_sha256 and all(sha(WORK/name)==pin for name,pin in PINS.items()),'Reviewed setup/helper source differs')
    recovery_sources()
    out=W.canonical(args.output)
    P.require(out.parent==WORK and out.is_dir(),'Windows-created direct C setup spool required')
    policy={'windows_reserve_bytes':1610612736,'incremental_windows_requirement_bytes':268435456,
            'commit_requirement_bytes':1879048192,'linux_job_requirement_bytes':134217728,'linux_reserve_bytes':134217728,
            'minimum_disk_free_bytes':10737418240,'resource_wait_seconds':0,'lease_max_age_seconds':3,
            'command_timeout_seconds':900 if args.step=='runtime' else 45,'sampled_rss_stop_bytes':536870912,
            'termination_grace_seconds':2,'drain_timeout_seconds':4}
    supervisor=None; result={'schema':'STAGE05_SETUP_LINUX_TERMINAL_V1','scope':SCOPE,'step':args.step,
                            'owner_nonce':args.owner_nonce,'source_sha256':sha(__file__),'state':'FAILED',
                            'owned_closure_proven':False,'owned_command_count':0,'no_native_launch':True,
                            'bootstrap':{'argv':list(sys.argv),'executable':sys.executable,
                                         'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                                         'identity':P.proc_record(os.getpid())},
                            'scientific_adoption_authorized':False}
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(P.Fatal('Setup Linux wall-clock deadline expired')))
    signal.alarm(930 if args.step=='runtime' else 90)
    try:
        supervisor=P.Supervisor(Path(args.owner_lease),args.owner_nonce,policy,out,sha)
        supervisor.admission(out)
        snapshot,expected,old_storage=recovery_read()
        preserved=recovery_observe(expected,old_storage)
        result['prepared_backing_recovery_before']=preserved
        native_args=SimpleNamespace(output=out,environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        def command(label,argv):
            return supervisor.execute(native_args,out/'commands',label,argv,WORK,{'scope':SCOPE,'step':args.step})
        if args.step=='diagnose':
            observation=diagnostic_observation();write_new(out/'diagnostic_observation.json',observation)
            result['diagnostic_observation_sha256']=sha(out/'diagnostic_observation.json')
            result['diagnostic_scope']='Read-only observation, not runtime/mount acceptance'
        elif args.step=='toolchain':
            descriptor=mount_lock()
            try:
                image_identity(); W.canonical(TOOLS)
                P.require(TOOLS.is_dir(),'Existing retained mountpoint directory required')
                rows=W.mount_rows(Path('/proc/self/mountinfo').read_text())
                if not any(row['mountpoint']==str(TOOLS) for row in rows):
                    P.require(next(TOOLS.iterdir(),None) is None,'Unknown toolchain mountpoint contents; preserve')
                    command('mount_toolchain',['/usr/bin/mount','-o','loop',str(IMAGE),str(TOOLS)])
                proof=toolchain_observe(); write_new(out/'toolchain_proof.json',proof)
                result['toolchain_proof_sha256']=sha(out/'toolchain_proof.json')
            finally:
                fcntl.flock(descriptor,fcntl.LOCK_UN); os.close(descriptor)
        else:
            proof=verified_toolchain(args.toolchain_proof,args.toolchain_proof_sha256)
            if args.step=='runtime':
                candidate=fresh_output(args.candidate_output,'stage5_runtime_actual_')
                command('runtime_discovery',[str(ENV/'bin/python'),'-B',str(WORK/'stage5_runtime_discovery.py'),
                                             '--discover','--output',str(candidate)])
                value=P.read_json(candidate)
                P.require(value['schema']=='STAGE05_PINNED_RUNTIME_V1','Actual runtime candidate schema differs')
                result.update(candidate_path=str(candidate),candidate_sha256=sha(candidate))
            elif args.step=='storage':
                target=W.canonical(ROOT/'.work/stage05_atomic_v1'); backing=W.canonical(W.BACKING)
                P.require(target.is_dir(),'Windows must establish and record empty G underlay before bind')
                rows=W.mount_rows(Path('/proc/self/mountinfo').read_text())
                if not any(row['mountpoint']==str(target) for row in rows):
                    P.require(next(target.iterdir(),None) is None,'Unknown Linux G underlay contents; preserve')
                    P.require(backing.is_dir() and recovery_observe(expected,old_storage)==preserved,
                              'Prepared backing identity/content changed; preserve')
                    enclosing=[row for row in rows if Path(row['mountpoint'])==backing or Path(row['mountpoint']) in backing.parents]
                    P.require(enclosing,'Actual backing filesystem mount missing')
                    parent_mount=max(enclosing,key=lambda row:len(Path(row['mountpoint']).parts))
                    P.require(parent_mount['filesystem']=='ext4' and 'rw' in parent_mount['options'].split(',')
                              and parent_mount['major_minor']==f'{os.major(backing.stat().st_dev)}:{os.minor(backing.stat().st_dev)}',
                              'Backing must already be native writable ext4 before binding')
                    def prepared_prelaunch(*_):
                        supervisor.check_owner()
                        P.require(W.mount_rows(Path('/proc/self/mountinfo').read_text())==rows and next(target.iterdir(),None) is None,
                                  'Canonical empty target/topology changed before bind')
                        P.require(recovery_observe(expected,old_storage)==preserved,'Prepared backing changed after command admission')
                    supervisor.prelaunch_check=prepared_prelaunch
                    command('bind_storage',['/usr/bin/mount','--bind',str(backing),str(target)])
                    supervisor.prelaunch_check=None
                candidate=fresh_output(args.candidate_output,'stage5_storage_actual_')
                value=W.observe(ROOT,target); write_new(candidate,value)
                P.require(W.observe(ROOT,target)==value,'Storage changed after proof write')
                result.update(candidate_path=str(candidate),candidate_sha256=sha(candidate),storage=value)
                result['prepared_backing_recovery_after']=recovery_observe(expected,old_storage)
                P.require(result['prepared_backing_recovery_after']==preserved,'Prepared contents changed across bind; preserve')
            else:
                receipt=W.canonical(args.owner_lock_receipt)
                P.require(WORK in receipt.parents and sha(receipt)==args.owner_lock_sha256,'Actual held-lock receipt differs')
                command('drivefs',[str(ENV/'bin/python'),'-B',str(WORK/'stage5_drivefs_filesystem_smoke.py'),
                                  '--owner-lock-receipt',str(receipt),'--owner-lock-sha256',args.owner_lock_sha256,
                                  '--supervisor-sha256',PINS['stage5_atomic_process.py'],'--run'])
                result['drivefs_stdout_path']=str(out/'commands/drivefs.stdout.txt')
            P.require(toolchain_observe()==proof,'Toolchain identity changed during setup step')
        supervisor.check_owner();recovery_sources()
        P.require(sha(__file__)==args.source_sha256,'Recovery Linux source changed')
        result['state']='PASS_NONSCIENTIFIC_SETUP_STEP'
    except BaseException as error:
        result['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        signal.alarm(0)
        if supervisor:
            result.update(owned_closure_proven=not supervisor.closure_unproven,
                          owned_command_count=supervisor.native_launch_count,
                          no_native_launch=supervisor.native_launch_count==0)
        else: result['owned_closure_proven']=True  # constructor launches no native process
        try:
            children=Path(f'/proc/self/task/{os.getpid()}/children').read_text().split()
            result['remaining_direct_children']=[int(pid) for pid in children]
            if children: result['owned_closure_proven']=False
        except BaseException as error:
            result.update(owned_closure_proven=False,remaining_direct_children='UNPROVEN',
                          closure_readback_error={'kind':type(error).__name__,'message':str(error)})
        write_new(out/'linux_terminal.json',result)
    return 0 if result['state']=='PASS_NONSCIENTIFIC_SETUP_STEP' and result['owned_closure_proven'] else 2


def noop_main():
    print(json.dumps({'state':'PREPARED_NOT_RUN','scope':'EXACT_PRESERVED_CAPACITY02_BACKING_RECOVERY_ONLY',
                      'mounts':0,'deletions':0,'moves':0,'detector_launches':0}));return 0


if __name__=='__main__':
    raise SystemExit(main() if '--recover-prepared' in sys.argv else noop_main())
