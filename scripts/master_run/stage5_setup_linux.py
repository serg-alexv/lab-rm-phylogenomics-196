"""Four scoped nonscientific setup steps; Windows owns the original byte lock.

Never installs, updates, extracts, unmounts, shuts down WSL or runs detectors.
"""
from pathlib import Path
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
PINS = {'stage5_atomic_process.py':'fdcc8d3b4337209b64ffa3732a8182bf832f2fa05d1e95fcdfb32964d4ad4a34',
        'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
        'stage5_runtime_discovery.py':'32e85b6f0d58d7e2ce4d92b8aab74d103ff64fa7a08928299363f30fd04be6ad',
        'stage5_drivefs_filesystem_smoke.py':'d24d86c1910ac82514a2fb7c1819d5cd1ea175dea3c5df587e8c8be2282eab2a'}


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
    image = image_identity()
    rows = W.mount_rows(Path('/proc/self/mountinfo').read_text())
    matches = [row for row in rows if row['mountpoint'] == str(W.canonical(TOOLS))]
    P.require(len(matches) == 1, 'One exact retained toolchain mount required')
    row = matches[0]; info = TOOLS.stat()
    P.require(row['filesystem'] == 'ext4' and row['root'] == '/' and 'rw' in row['options'].split(',')
              and row['major_minor'] == f'{os.major(info.st_dev)}:{os.minor(info.st_dev)}', 'Toolchain filesystem/root/device differs')
    device = Path('/sys/dev/block')/row['major_minor']/'loop/backing_file'
    backing = Path(device.read_text().strip())
    P.require(backing == IMAGE and W.canonical(backing) == IMAGE, 'Loop backing is not the exact retained image')
    P.require(W.ext4_uuid(row['source'],info.st_dev) == image['filesystem_uuid'], 'Image/block ext4 UUID differs')
    for path in [ENV/'bin/python', TOOLS/'defense_models', TOOLS/'padloc_db']:
        P.require(path.exists() and TOOLS in path.resolve().parents and path.stat().st_dev == info.st_dev,
                  'Retained runtime/model role is missing or escapes toolchain')
    result = {'schema':'STAGE05_TOOLCHAIN_LOOP_PROOF_V1','scope':SCOPE,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'image':image,'mount':row,'directory_device':info.st_dev,'directory_inode':info.st_ino,
              'helper_sha256':sha(__file__),'runtime_file_hash_acceptance':'SEPARATE_RUNTIME_DISCOVERY_REQUIRED'}
    P.require([r for r in W.mount_rows(Path('/proc/self/mountinfo').read_text()) if r['mountpoint']==str(TOOLS)] == [row]
              and image_identity() == image, 'Toolchain changed during observation')
    return result


def verified_toolchain(path, expected):
    path = W.canonical(path)
    P.require(WORK in path.parents and sha(path) == expected, 'Pinned C toolchain proof missing/changed')
    frozen = P.read_json(path)
    P.require(frozen == toolchain_observe() and sha(path) == expected, 'Current toolchain/boot/loop/image proof differs')
    return frozen


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
    parser.add_argument('--step',choices=('toolchain','runtime','storage','drivefs'),required=True)
    for name in ('output','owner-lease','owner-nonce','owner-lock-receipt','owner-lock-sha256','source-sha256',
                 'toolchain-proof','toolchain-proof-sha256','candidate-output'):
        parser.add_argument('--'+name,required=name in ('output','owner-lease','owner-nonce','source-sha256'))
    args=parser.parse_args()
    P.require(sys.platform=='linux' and os.geteuid()==0 and Path(__file__).resolve().parent==WORK,
              'Exact root-owned mounted-C Linux setup required')
    P.require(sha(__file__)==args.source_sha256 and all(sha(WORK/name)==pin for name,pin in PINS.items()),'Reviewed setup/helper source differs')
    out=W.canonical(args.output)
    P.require(out.parent==WORK and out.is_dir(),'Windows-created direct C setup spool required')
    policy={'windows_reserve_bytes':1610612736,'incremental_windows_requirement_bytes':268435456,
            'commit_requirement_bytes':1879048192,'linux_job_requirement_bytes':134217728,'linux_reserve_bytes':134217728,
            'minimum_disk_free_bytes':10737418240,'resource_wait_seconds':0,'lease_max_age_seconds':3,
            'command_timeout_seconds':900 if args.step=='runtime' else 45,'sampled_rss_stop_bytes':536870912,
            'termination_grace_seconds':2,'drain_timeout_seconds':4}
    supervisor=None; result={'schema':'STAGE05_SETUP_LINUX_TERMINAL_V1','scope':SCOPE,'step':args.step,
                            'owner_nonce':args.owner_nonce,'source_sha256':sha(__file__),'state':'FAILED',
                            'owned_closure_proven':True,'scientific_adoption_authorized':False}
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(P.Fatal('Setup Linux wall-clock deadline expired')))
    signal.alarm(930 if args.step=='runtime' else 90)
    try:
        supervisor=P.Supervisor(Path(args.owner_lease),args.owner_nonce,policy,out,sha)
        supervisor.admission(out)
        native_args=SimpleNamespace(output=out,environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        def command(label,argv):
            return supervisor.execute(native_args,out/'commands',label,argv,WORK,{'scope':SCOPE,'step':args.step})
        if args.step=='toolchain':
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
                    if not backing.exists(): backing.mkdir(mode=0o700)
                    P.require(backing.is_dir() and next(backing.iterdir(),None) is None,'Unknown ext4 backing contents; preserve')
                    enclosing=[row for row in rows if Path(row['mountpoint'])==backing or Path(row['mountpoint']) in backing.parents]
                    P.require(enclosing,'Actual backing filesystem mount missing')
                    parent_mount=max(enclosing,key=lambda row:len(Path(row['mountpoint']).parts))
                    P.require(parent_mount['filesystem']=='ext4' and 'rw' in parent_mount['options'].split(',')
                              and parent_mount['major_minor']==f'{os.major(backing.stat().st_dev)}:{os.minor(backing.stat().st_dev)}',
                              'Backing must already be native writable ext4 before binding')
                    command('bind_storage',['/usr/bin/mount','--bind',str(backing),str(target)])
                candidate=fresh_output(args.candidate_output,'stage5_storage_actual_')
                value=W.observe(ROOT,target); write_new(candidate,value)
                P.require(W.observe(ROOT,target)==value,'Storage changed after proof write')
                result.update(candidate_path=str(candidate),candidate_sha256=sha(candidate),storage=value)
            else:
                receipt=W.canonical(args.owner_lock_receipt)
                P.require(WORK in receipt.parents and sha(receipt)==args.owner_lock_sha256,'Actual held-lock receipt differs')
                command('drivefs',[str(ENV/'bin/python'),'-B',str(WORK/'stage5_drivefs_filesystem_smoke.py'),
                                  '--owner-lock-receipt',str(receipt),'--owner-lock-sha256',args.owner_lock_sha256,
                                  '--supervisor-sha256',PINS['stage5_atomic_process.py'],'--run'])
                result['drivefs_stdout_path']=str(out/'commands/drivefs.stdout.txt')
            P.require(toolchain_observe()==proof,'Toolchain identity changed during setup step')
        supervisor.check_owner(); result['state']='PASS_NONSCIENTIFIC_SETUP_STEP'
    except BaseException as error:
        result['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        signal.alarm(0)
        if supervisor:
            result.update(owned_closure_proven=not supervisor.closure_unproven,
                          owned_command_count=supervisor.native_launch_count)
        write_new(out/'linux_terminal.json',result)
    return 0 if result['state']=='PASS_NONSCIENTIFIC_SETUP_STEP' and result['owned_closure_proven'] else 2


if __name__=='__main__':
    raise SystemExit(main())
