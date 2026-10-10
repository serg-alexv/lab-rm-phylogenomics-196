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
PINS = {'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
        'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
        'stage5_runtime_discovery.py':'11b2a1b64512e1eab3895db017323cc25de65d31b4734d08788e99d968f44dfb',
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


# Separate opt-in cold branch of the same paired owner. Everything above this
# line is the preserved 24aab72b normal setup implementation.
COLD_PHASES = ('writer_closure', 'unmount_rw', 'detach_rw', 'backing_detached',
               'windows_guard', 'drvfs_write_refused', 'loop_ro', 'mount_ro',
               'frozen_proof', 'worker', 'unmount_ro', 'detach_ro',
               'backing_detached_again', 'windows_guard_released', 'mount_rw',
               'runtime_rediscovery', 'rw_restored')
COLD_PINS = {
    'stage5_runtime_inventory_entry_v3.py':'dbfd181eaccd2db37857409c48a6ba6964c1db5154fd4d7e055058d18802e60e',
    'stage5_runtime_capture_entry_v2.py':'e5f50eb7beb9297dce8e6a9e160ea1aef564bf0f08379dc73b839210f182bdf5',
    'stage5_runtime_logical_capture.py':'21b33abc389efe9bbfdcf8048737f2d7f10ce60b52d6e1c6f3678b24568b8220',
    'stage5_runtime_recovery_contract.py':'daf48ea1c8cc96312519b1ab22f2d41216494773e5e345e3e5e0417139588bb6',
    'stage5_offline_image_read_parts_v2.py':'f0bf9fe02597cdce26e337d1c40fda45763b5225ea9f240e1962be18acacc151',
}
COLD_RUNTIME_SHA = 'f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1'
COLD_LOCK = {'path':r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock',
             'volume_serial':2430728143,'file_index':844424932784519,
             'creation_filetime':134359335921635133,'locked_byte':0}
COLD_MAX_SECONDS = 3600
COLD_ALLOCATION = 512*1024**2  # per-process inherited RLIMIT_AS, not aggregate RAM
COLD_DEADLINES = {name:45 for name in COLD_PHASES}
COLD_DEADLINES.update(writer_closure=180, worker=1830, runtime_rediscovery=930,
                      windows_guard=30, windows_guard_released=30)
COLD_COMMAND_PHASES = {'unmount_rw','detach_rw','loop_ro','mount_ro','worker',
                       'unmount_ro','detach_ro','mount_rw','runtime_rediscovery'}


def cold_strict_lock(value):
    return isinstance(value,dict) and set(value)==set(COLD_LOCK) and all(
        type(value[k]) is type(v) and value[k]==v for k,v in COLD_LOCK.items())


def cold_expected_argv(phase, request, out, loop_rw, loop_ro, proof_sha=None, inputs_sha=None):
    """Pure finite argv contract, shared with the existing Windows reader."""
    from pathlib import PurePosixPath
    out=PurePosixPath(out); tools=TOOLS.as_posix(); image=IMAGE.as_posix()
    env=ENV.as_posix(); work=WORK.as_posix()
    for loop in (loop_rw,loop_ro):
        P.require(loop is None or __import__('re').fullmatch('/dev/loop[0-9]+',loop), 'Exact loop device required')
    values={
        'unmount_rw':['/usr/bin/umount',tools],
        'detach_rw':['/usr/sbin/losetup','--detach',loop_rw],
        'loop_ro':['/usr/sbin/losetup','--find','--show','--read-only',image],
        'mount_ro':['/usr/bin/mount','-t','ext4','-o','ro,noload',loop_ro,tools],
        'unmount_ro':['/usr/bin/umount',tools],
        'detach_ro':['/usr/sbin/losetup','--detach',loop_ro],
        'mount_rw':['/usr/bin/mount','-o','loop',image,tools],
        'runtime_rediscovery':[env+'/bin/python','-B',work+'/stage5_runtime_discovery.py',
                               '--discover','--output',request['rediscovery_output']],
    }
    if phase!='worker':return values[phase]
    proof=out/'cold_proof.json'; proof_sha=proof_sha or sha(proof)
    common=['--run','--source-sha256',COLD_PINS['stage5_runtime_inventory_entry_v3.py'],
            '--runtime',request['runtime'],'--runtime-sha256',request['runtime_sha256'],
            '--cold-proof',str(proof),'--cold-proof-sha256',proof_sha,
            '--owner-lease',str(out/'owner_lease.json'),'--owner-nonce',request['owner_nonce']]
    if request['mode']=='inventory':
        return [env+'/bin/python','-B',work+'/stage5_runtime_inventory_entry_v3.py',
                *common,'--output-private',request['worker_output']]
    common[2]=COLD_PINS['stage5_runtime_capture_entry_v2.py']
    result=[env+'/bin/python','-B',work+'/stage5_runtime_capture_entry_v2.py',*common,
            '--inputs',str(out/'capture_inputs.json'),'--inputs-sha256',inputs_sha or sha(out/'capture_inputs.json'),
            '--output',request['worker_output'],'--terminal',request['worker_terminal']]
    for key in ('manifest','public_review','notices'):
        flag=key.replace('_','-')
        result+=['--'+flag,request[key],'--'+flag+'-sha256',request[key+'_sha256']]
    return result


def cold_clean_superblock(raw):
    """Clean unmount plus exact ext4 flags; ro alone must not replay a journal."""
    import struct
    P.require(len(raw)==1024 and raw[56:58]==b'\x53\xef', 'Exact ext4 superblock required')
    state=struct.unpack_from('<H',raw,0x3a)[0]
    incompat=struct.unpack_from('<I',raw,0x60)[0]
    rocompat=struct.unpack_from('<I',raw,0x64)[0]
    orphan=struct.unpack_from('<I',raw,0xe8)[0]
    P.require(state&1 and not state&2 and not incompat&4 and not rocompat&0x10000 and orphan==0,
              'Ext4 is dirty/recovery/orphan pending; preserve without repair')
    return {'filesystem_uuid':str(uuid.UUID(bytes=raw[104:120])), 'state':state,
            'incompat':incompat,'ro_compat':rocompat,'last_orphan':orphan,
            'superblock_sha256':hashlib.sha256(raw).hexdigest()}


def cold_loop_aliases():
    """Enumerate every configured loop by backing inode, not filename alone."""
    image=IMAGE.stat(); result=[]
    for node in sorted(Path('/sys/block').glob('loop*')):
        backing=node/'loop/backing_file'
        if not backing.exists():continue
        text=backing.read_text().strip()
        if not text:continue
        path=Path(text)
        if not path.is_absolute():path=Path('/')/path
        try:info=path.stat()
        except FileNotFoundError:
            raise P.Fatal('Configured loop backing cannot be identified; preserve unknown alias')
        if (info.st_dev,info.st_ino)==(image.st_dev,image.st_ino):
            P.require(path==IMAGE and path.resolve()==IMAGE, 'Image backing alias differs')
            dev=(node/'dev').read_text().strip()
            result.append({'loop':'/dev/'+node.name,'major_minor':dev,
                           'read_only':(node/'ro').read_text().strip()=='1',
                           'backing_file':text})
    return result


def cold_process_exclusion(tool_dev, supervisor):
    """Fail closed on inaccessible metadata/foreign mount namespaces/references.

    No process is killed or adopted and no private file payload is read.
    Native guards, prior owned receipts, clean unmount and the later Windows
    deny-write handle supply complementary evidence; this scan alone is not a
    whole-system lock and it does not close another process.
    """
    image=IMAGE.stat(); ns=os.readlink('/proc/self/ns/mnt'); seen=[]
    for pid,record in sorted(P.proc_table().items()):
        supervisor.check_owner()
        base=Path('/proc')/str(pid)
        try:
            P.require(os.readlink(base/'ns/mnt')==ns,'Foreign mount namespace; writer exclusion unproven')
            for name in ('cwd','root','exe'):
                try:info=(base/name).stat()
                except FileNotFoundError:continue  # kernel thread / no userspace executable
                P.require(info.st_dev!=tool_dev,'Process executable/cwd/root still references toolchain')
            for fd in (base/'fd').iterdir():
                try:info=fd.stat()
                except FileNotFoundError:continue  # closed between enumeration/readback
                P.require(info.st_dev!=tool_dev and (info.st_dev,info.st_ino)!=(image.st_dev,image.st_ino),
                          'Open process descriptor references toolchain/backing image')
                P.require(not (stat.S_ISBLK(info.st_mode) and info.st_rdev==tool_dev),
                          'Open block-device descriptor references toolchain')
            with (base/'maps').open() as stream:
                total=0
                for line in stream:
                    total+=len(line);P.require(total<=8*1024**2,'Bounded process map scan exceeded')
                    fields=line.split(None,5)
                    if len(fields)<5:continue
                    a,b=fields[3].split(':');device=os.makedev(int(a,16),int(b,16));inode=int(fields[4])
                    P.require(device!=tool_dev and (device,inode)!=(image.st_dev,image.st_ino),
                              'Process mapping references toolchain/backing image')
            after=P.proc_record(pid)
            if after and after['start_ticks']==record['start_ticks']:seen.append({'pid':pid,'start_ticks':record['start_ticks']})
        except FileNotFoundError:
            after=P.proc_record(pid)
            P.require(after is None or after['start_ticks']!=record['start_ticks'],
                      'Live process metadata vanished; exclusion unproven')
    return {'mount_namespace':ns,'observed_process_births':seen,'relevant_references':0,
            'foreign_mount_namespaces':0,'scope':'METADATA_SCAN_PLUS_GUARDS_NOT_A_GLOBAL_KERNEL_LOCK'}


def cold_write_refusal(open_image, close_image):
    """Real O_RDWR refusal fixture. Never invokes write; success is a veto."""
    import errno
    try:descriptor=open_image()
    except OSError as error:
        P.require(error.errno in (errno.EACCES,errno.EPERM,errno.ETXTBSY,errno.EBUSY),
                  'Image O_RDWR failed for an unrelated reason; exclusion unproven')
        return {'attempt':'O_RDWR|O_NOFOLLOW','errno':error.errno,'write_called':False,
                'state':'ACTUAL_CROSS_DRVFS_WRITE_OPEN_REFUSED'}
    close_image(descriptor)
    raise P.Fatal('Windows guard did not refuse real DrvFS O_RDWR; no bytes written; preserve and stop')


def cold_read_control(path, expected, maximum=64*1024**2):
    path=W.canonical(path)
    P.require(WORK in path.parents and not path.is_symlink() and path.is_file()
              and path.stat().st_size<=maximum and __import__('re').fullmatch('[a-f0-9]{64}',expected or ''),
              'Bounded exact C cold control required')
    before=path.stat();raw=path.read_bytes();after=path.stat()
    P.require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
              (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
              and hashlib.sha256(raw).hexdigest()==expected,'Cold control changed')
    return json.loads(raw)


def cold_main():
    parser=argparse.ArgumentParser(description='Cold-only branch of existing paired setup owner; default NO_OP')
    parser.add_argument('--cold',action='store_true');parser.add_argument('--run',action='store_true')
    for name in ('request','request-sha256','output','source-sha256','windows-source-sha256','owner-lease','owner-nonce'):
        parser.add_argument('--'+name)
    args=parser.parse_args()
    if not args.run:
        print(json.dumps({'state':'NO_OP_COLD_EXISTING_OWNER_REQUIRED','actual_image_actions':'NOT_RUN'}));return 0
    import fcntl, resource
    P.require(all(vars(args).values()) and sys.platform=='linux' and os.geteuid()==0
              and Path(__file__).resolve().parent==WORK,'Exact root-owned C cold bootstrap required')
    out=W.canonical(args.output)
    P.require(out.parent==WORK and out.is_dir(),'Existing Windows-created cold spool required')
    # Whole bootstrap is bounded before control parsing; children inherit the
    # per-process address-space limit, including inventory's initial preflight.
    soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    P.require((soft==resource.RLIM_INFINITY or soft>=COLD_ALLOCATION)
              and (hard==resource.RLIM_INFINITY or hard>=COLD_ALLOCATION),'Preexisting lower AS limit')
    resource.setrlimit(resource.RLIMIT_AS,(COLD_ALLOCATION,COLD_ALLOCATION))
    result={'schema':'STAGE05_SETUP_COLD_LINUX_TERMINAL_V1','scope':SCOPE,'state':'FAILED',
            'source_sha256':args.source_sha256,'windows_source_sha256':args.windows_source_sha256,
            'owner_nonce':args.owner_nonce,'request_sha256':args.request_sha256,
            'bootstrap':{'argv':list(sys.argv),'executable':sys.executable,
                         'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                         'identity':P.proc_record(os.getpid())},
            'owned_closure_proven':False,'rw_restoration_proven':False,
            'owned_command_count':0,'scientific_adoption_authorized':False,
            'raw_image_split':'NOT_RUN','remote_upload':'NOT_RUN','cleanup_authority':False}
    supervisor=None;guards=[];ledger=[];request=None;initial_owner=None
    started=time.monotonic()
    def deadline(*_):raise P.Fatal('Finite cold bootstrap deadline expired')
    for signum in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT):signal.signal(signum,deadline)
    signal.alarm(COLD_MAX_SECONDS)
    policy={'windows_reserve_bytes':1536*1024**2,'incremental_windows_requirement_bytes':640*1024**2,
            'commit_requirement_bytes':2176*1024**2,'linux_job_requirement_bytes':128*1024**2,
            'linux_reserve_bytes':256*1024**2,'minimum_disk_free_bytes':10*1024**3,
            'resource_wait_seconds':0,'lease_max_age_seconds':3,'command_timeout_seconds':45,
            'sampled_rss_stop_bytes':512*1024**2,'termination_grace_seconds':2,'drain_timeout_seconds':4}
    def check():
        nonlocal initial_owner
        P.require(time.monotonic()-started<COLD_MAX_SECONDS,'Cold owner total deadline expired')
        lease=supervisor.check_owner()
        P.require(cold_strict_lock(lease.get('workflow_lock')) and type(lease['owner_pid']) is int,
                  'Exact original immutable WorkflowLock/owner required')
        identity=(lease['owner_pid'],lease['owner_creation_filetime'])
        P.require(initial_owner is None or identity==initial_owner,'Cold Windows owner birth changed')
        initial_owner=identity
        P.require(sha(__file__)==args.source_sha256 and all(sha(WORK/n)==p for n,p in {**PINS,**COLD_PINS}.items()),
                  'Cold source/helper drift')
        return lease
    def phase(name,action):
        P.require(name==COLD_PHASES[len(ledger)],'Exact cold phase order required')
        check();signal.alarm(min(COLD_DEADLINES[name],max(1,int(COLD_MAX_SECONDS-(time.monotonic()-started)))))
        record={'phase':name,'ordinal':len(ledger)+1,'deadline_seconds':COLD_DEADLINES[name],
                'owner_nonce':args.owner_nonce,'source_sha256':args.source_sha256,
                'request_sha256':args.request_sha256,'boot_id':supervisor.boot_id,
                'previous_sha256':sha(out/'phases'/f'{len(ledger):02d}_{ledger[-1]["phase"]}.json') if ledger else None}
        payload=action();check();record.update(payload)
        path=out/'phases'/f'{len(ledger)+1:02d}_{name}.json';write_new(path,record);ledger.append(record)
        signal.alarm(max(1,int(COLD_MAX_SECONDS-(time.monotonic()-started))))
        return record
    def command(name,argv,optional=False,worker=False):
        directory=out/'phases'/name;directory.mkdir()
        before=supervisor.native_launch_count
        supervisor.policy['command_timeout_seconds']=COLD_DEADLINES[name]-15 if name in ('worker','runtime_rediscovery') else 25
        try:
            if not optional:
                native=SimpleNamespace(output=out,environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
                supervisor.execute(native,directory/'commands',name,argv,WORK,{'scope':SCOPE,'step':'toolchain'})
            return {'state':'DONE','argv':argv,'command_count':supervisor.native_launch_count-before}
        except BaseException as error:
            if not worker or supervisor.closure_unproven:raise
            # A known failed worker is still closed, so restore the installation.
            return {'state':'FAILED_CLOSED','argv':argv,'command_count':supervisor.native_launch_count-before,
                    'error_kind':type(error).__name__}
        finally:supervisor.policy['command_timeout_seconds']=45
    def wait_ack(name,phase_record):
        path=out/(name+'_ack.json');end=time.monotonic()+25
        while not path.exists():check();P.require(time.monotonic()<end,'Cold Windows handshake deadline expired');time.sleep(0.1)
        raw=path.read_bytes();P.require(len(raw)<=65536,'Bounded cold ack required');ack=json.loads(raw)
        P.require(ack.get('schema')=='STAGE05_SETUP_COLD_WINDOWS_ACK_V1' and ack.get('phase')==name
                  and ack.get('owner_nonce')==args.owner_nonce and ack.get('windows_source_sha256')==args.windows_source_sha256
                  and ack.get('linux_source_sha256')==args.source_sha256 and cold_strict_lock(ack.get('workflow_lock'))
                  and ack.get('linux_phase_sha256')==sha(out/'phases'/phase_record)
                  and ack.get('windows_owner')=={'pid':initial_owner[0],'creation_filetime':initial_owner[1]},
                  'Exact retained Windows handshake/source/phase differs')
        check();P.require(path.read_bytes()==raw,'Cold ack changed');return ack
    try:
        P.require(sha(__file__)==args.source_sha256,'Explicit reviewed cold Linux source required')
        supervisor=P.Supervisor(Path(args.owner_lease),args.owner_nonce,policy,out,sha);check();supervisor.admission(out)
        P.require(sys.executable=='/usr/bin/python3' and TOOLS not in Path(sys.executable).resolve().parents,
                  'System Python must remain usable while retained prefix detached')
        request=cold_read_control(args.request,args.request_sha256,65536)
        P.require(request.get('schema')=='STAGE05_SETUP_COLD_REQUEST_V1' and request.get('mode') in ('inventory','capture')
                  and request.get('owner_nonce')==args.owner_nonce and request.get('runtime_sha256')==COLD_RUNTIME_SHA,
                  'Exact cold request/runtime06 required')
        cold_read_control(request['runtime'],COLD_RUNTIME_SHA)
        proof=cold_read_control(request['toolchain_proof'],request['toolchain_proof_sha256'])
        current=toolchain_observe()
        # Adopt the original 24aa observer's already pinned proof without
        # rewriting it; the separate variant records its own source elsewhere.
        P.require(proof.get('helper_sha256')=='24aab72b74dd0aab6c58cac4951c30e6b1bfc9462460486748b546e50ec92e27',
                  'Original reviewed RW observer proof required')
        current['helper_sha256']=proof['helper_sha256']
        P.require(proof==current,'Current RW toolchain predicate differs from original proof')
        loop_rw=proof['mount']['source'];loop_ro=None;device=proof['directory_device']
        P.require(__import__('re').fullmatch('/dev/loop[0-9]+',loop_rw),'Original exact loop source required')
        output=Path(request['worker_output']);rediscovery=Path(request['rediscovery_output'])
        P.require(output.parent==WORK and not output.exists() and output.resolve()==output
                  and rediscovery.parent==WORK and not rediscovery.exists(),'Fresh bounded cold outputs required')
        (out/'phases').mkdir()
        def writer_closure():
            guards.append(mount_lock())
            guard=ROOT/'.work/stage05_atomic_v1/.native_runner.guard'
            fd=os.open(guard,os.O_RDWR|os.O_CLOEXEC|os.O_NOFOLLOW);guards.append(fd)
            P.require(stat.S_ISREG(os.fstat(fd).st_mode),'Existing native guard regular file required')
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            closed=[]
            for suffix in ('launch_intent','launch'):
                for path in sorted((ROOT/'.work/stage05_atomic_v1').glob('*/execution/**/*.'+suffix+'.json')):
                    check()
                    if suffix=='launch_intent':supervisor.assert_intent_closed(path)
                    else:supervisor.assert_closed(P.read_json(path))
                    closed.append({'path':str(path),'sha256':sha(path)})
            aliases=cold_loop_aliases()
            P.require(len(aliases)==1 and aliases[0]['loop']==loop_rw and not aliases[0]['read_only'],
                      'One original RW loop only; additional backing aliases veto')
            return {'state':'DONE','prior_owned_native_receipts':closed,'process_exclusion':cold_process_exclusion(device,supervisor),
                    'loop_aliases':aliases,'original_toolchain_proof_sha256':request['toolchain_proof_sha256']}
        phase('writer_closure',writer_closure)
        phase('unmount_rw',lambda:command('unmount_rw',cold_expected_argv('unmount_rw',request,out,loop_rw,loop_ro)))
        aliases=cold_loop_aliases()
        P.require(not aliases or (len(aliases)==1 and aliases[0]['loop']==loop_rw),'Unexpected post-unmount loop alias')
        phase('detach_rw',lambda:command('detach_rw',cold_expected_argv('detach_rw',request,out,loop_rw,loop_ro),not aliases))
        def detached():
            P.require(not cold_loop_aliases() and not any(r['major_minor']==proof['mount']['major_minor'] or
                      r['mountpoint']==str(TOOLS) for r in W.mount_rows(Path('/proc/self/mountinfo').read_text())),
                      'Original toolchain/loop writer remains')
            P.require(next(TOOLS.iterdir(),None) is None,'Unknown unmounted prefix contents; preserve')
            with IMAGE.open('rb') as stream:superblock=cold_clean_superblock(os.pread(stream.fileno(),1024,1024))
            P.require(superblock['filesystem_uuid']==proof['image']['filesystem_uuid'],'Detached filesystem UUID differs')
            return {'state':'DONE','loop_aliases':[],'clean_superblock':superblock,
                    'process_exclusion':cold_process_exclusion(device,supervisor)}
        phase('backing_detached',detached)
        guard_ack=phase('windows_guard',lambda:{'state':'DONE','ack':wait_ack('guard','04_backing_detached.json')})
        phase('drvfs_write_refused',lambda:cold_write_refusal(
            lambda:os.open(IMAGE,os.O_RDWR|os.O_CLOEXEC|os.O_NOFOLLOW),os.close))
        ro_record=phase('loop_ro',lambda:command('loop_ro',cold_expected_argv('loop_ro',request,out,loop_rw,loop_ro)))
        raw=(out/'phases/loop_ro/commands/loop_ro.stdout.txt').read_bytes()
        P.require(len(raw)<=64 and __import__('re').fullmatch(rb'/dev/loop[0-9]+\n',raw),'One exact read-only loop result required')
        loop_ro=raw.decode().strip()
        phase('mount_ro',lambda:command('mount_ro',cold_expected_argv('mount_ro',request,out,loop_rw,loop_ro)))
        def frozen():
            aliases=cold_loop_aliases();P.require(len(aliases)==1 and aliases[0]['loop']==loop_ro and aliases[0]['read_only'],
                                               'One kernel read-only image loop required')
            rows=W.mount_rows(Path('/proc/self/mountinfo').read_text());matches=[r for r in rows if r['mountpoint']==str(TOOLS)]
            P.require(len(matches)==1 and matches[0]['source']==loop_ro and matches[0]['filesystem']=='ext4'
                      and matches[0]['root']=='/' and 'ro' in matches[0]['options'].split(','),'Exact RO toolchain mount required')
            mount=matches[0]
            P.require(mount['major_minor']==aliases[0]['major_minor']
                      and mount['major_minor']==f'{os.major(TOOLS.stat().st_dev)}:{os.minor(TOOLS.stat().st_dev)}'
                      and W.ext4_uuid(loop_ro,TOOLS.stat().st_dev)==proof['image']['filesystem_uuid'],
                      'RO loop/mount/current block UUID differs')
            value={'schema':'STAGE05_RUNTIME_COLD_CAPTURE_PROOF_V1','owner_nonce':args.owner_nonce,
                   'workflow_lock':COLD_LOCK,'windows_owner':{'pid':initial_owner[0],'creation_filetime':initial_owner[1]},
                   'original_workflow_lock_held':True,'all_relevant_native_jobs_closed':True,
                   'backing_image_writer_exclusion_proven':True,'boot_id':supervisor.boot_id,
                   'inventory_entry_source_sha256':COLD_PINS['stage5_runtime_inventory_entry_v3.py'],
                   'capture_entry_source_sha256':COLD_PINS['stage5_runtime_capture_entry_v2.py'],
                   'windows_api_source_sha256':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
                   'mount_id':mount['mount_id'],'major_minor':mount['major_minor'],
                   'windows_guard_ack_sha256':sha(out/'guard_ack.json'),
                   'actual_write_refusal_sha256':sha(out/'phases/06_drvfs_write_refused.json'),
                   'clean_detached_phase_sha256':sha(out/'phases/04_backing_detached.json'),
                   'loop_aliases':aliases,'owner_entry_source_sha256':args.windows_source_sha256,
                   'linux_owner_source_sha256':args.source_sha256}
            import stage5_runtime_logical_capture as R
            R.check_ro_mount(value);write_new(out/'cold_proof.json',value)
            if request['mode']=='capture':
                # These flags come from the explicit request, not inferred from
                # regex screening. capture() independently checks all originals.
                value_inputs={'schema':'STAGE05_INSTALLED_RUNTIME_CAPTURE_INPUTS_V1','state':'REVIEWED_COLD_CAPTURE_READY',
                    'actual_runtime_manifest_sha256':request['runtime_sha256'],
                    'complete_inventory_sha256':request['manifest_sha256'],
                    'whole_file_public_review_sha256':request['public_review_sha256'],
                    'license_source_notice_review_sha256':request['notices_sha256'],
                    'cold_exclusive_capture_receipt_sha256':sha(out/'cold_proof.json'),
                    'published_capture_source_sha256':COLD_PINS['stage5_runtime_logical_capture.py'],
                    'roots':R.C.ROOTS,'original_prefix_required':True,
                    'all_required_runtime_files_public_and_covered':request.get('all_required_runtime_files_public_and_covered'),
                    'all_special_metadata_resolved':request.get('all_special_metadata_resolved'),
                    'installed_build_equivalence':'NOT_ESTABLISHED'}
                R.C.capture_gate(value_inputs);write_new(out/'capture_inputs.json',value_inputs)
            return {'state':'DONE','cold_proof_sha256':sha(out/'cold_proof.json'),'loop_ro':loop_ro,'mount':mount}
        phase('frozen_proof',frozen)
        worker=phase('worker',lambda:command('worker',cold_expected_argv('worker',request,out,loop_rw,loop_ro),worker=True))
        phase('unmount_ro',lambda:command('unmount_ro',cold_expected_argv('unmount_ro',request,out,loop_rw,loop_ro)))
        phase('detach_ro',lambda:command('detach_ro',cold_expected_argv('detach_ro',request,out,loop_rw,loop_ro)))
        phase('backing_detached_again',detached)
        phase('windows_guard_released',lambda:{'state':'DONE','ack':wait_ack('release','13_backing_detached_again.json')})
        phase('mount_rw',lambda:command('mount_rw',cold_expected_argv('mount_rw',request,out,loop_rw,loop_ro)))
        restored=toolchain_observe()
        P.require(restored['image']==proof['image'],'Restored RW image identity differs')
        phase('runtime_rediscovery',lambda:command('runtime_rediscovery',cold_expected_argv('runtime_rediscovery',request,out,loop_rw,loop_ro)))
        phase('rw_restored',lambda:{'state':'DONE','toolchain_proof':toolchain_observe(),
              'rediscovery_sha256':sha(rediscovery),'runtime06_sha256':COLD_RUNTIME_SHA})
        P.require(sha(rediscovery)==COLD_RUNTIME_SHA and sha(Path(request['runtime']))==COLD_RUNTIME_SHA,
                  'RW restoration changed scientific runtime06 bytes/ambient; fatal STOP')
        result.update(rw_restoration_proven=True,loop_rw=loop_rw,loop_ro=loop_ro,
                      rediscovery_sha256=sha(rediscovery),phase_ledger_sha256s=[
                          sha(out/'phases'/f'{i+1:02d}_{name}.json') for i,name in enumerate(COLD_PHASES)],
                      state='PASS_COLD_STEP_AND_RUNTIME06_RESTORED' if worker['state']=='DONE' else 'FAILED_WORKER_CLOSED_RUNTIME06_RESTORED')
        check()
    except BaseException as error:result['error_kind']=type(error).__name__
    finally:
        signal.alarm(0)
        # No unsafe automatic detach/remount after an uncertain scope. Preserve
        # the STOP and original image for root-owned reconciliation instead.
        result.update(owned_command_count=supervisor.native_launch_count if supervisor else 0,
                      owned_closure_proven=not supervisor.closure_unproven if supervisor else True,
                      completed_phases=[r['phase'] for r in ledger],elapsed_seconds=time.monotonic()-started)
        try:
            result['remaining_direct_children']=[int(p) for p in Path(f'/proc/self/task/{os.getpid()}/children').read_text().split()]
            if result['remaining_direct_children']:result['owned_closure_proven']=False
        except BaseException:result.update(remaining_direct_children='UNPROVEN',owned_closure_proven=False)
        failures=[]
        for fd in reversed(guards):
            try:fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)
            except BaseException as error:failures.append(type(error).__name__)
        result['guard_release_errors']=failures
        if failures:result['owned_closure_proven']=False
        write_new(out/'linux_terminal.json',result)
    return 0 if result['state']=='PASS_COLD_STEP_AND_RUNTIME06_RESTORED' and result['owned_closure_proven'] else 2


if __name__=='__main__':
    raise SystemExit(cold_main() if '--cold' in sys.argv or len(sys.argv)==1 else main())
