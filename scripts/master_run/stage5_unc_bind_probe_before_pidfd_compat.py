"""Opt-in exact WSL ext4-bind/Windows-UNC sentinel proof; default NOT_RUN.

Three bounded owned steps: Linux prepare, Windows UNC I/O, Linux readback/cleanup.
No detector, mounting, unmounting, shutdown, installation or recursive cleanup.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse
import ctypes
import hashlib
import importlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parent
WINDOWS_WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
LINUX_WORK = '/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work'
ROOT = '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
TARGET = ROOT + '/.work/stage05_atomic_v1'
ENV = '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/detector_env'
G_UNDERLAY = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage05_atomic_v1')
UNC = PureWindowsPath(r'\\wsl.localhost\Ubuntu').joinpath(*PurePosixPath(TARGET).parts[1:])
WSL = r'C:\Windows\System32\wsl.exe'
SCOPE = 'NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY_ONLY'
PINS = {
    'atomic_iqtree_windows.py': '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
    'stage5_atomic_process.py': 'fdcc8d3b4337209b64ffa3732a8182bf832f2fa05d1e95fcdfb32964d4ad4a34',
    'stage5_work_storage.py': '7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())


def load_pinned(name):
    require(sha(WORK / name) == PINS[name], 'Reviewed helper source changed: ' + name)
    module = importlib.import_module(Path(name).stem)
    require(Path(module.__file__).resolve() == WORK / name, 'Imported helper location differs')
    return module


def linux_path(path):
    path = Path(path)
    require(path.is_absolute() and path.drive.casefold() == 'c:' and WINDOWS_WORK in path.parents
            and path == path.resolve(), 'Exact C work bridge file required')
    return '/mnt/c/' + '/'.join(path.parts[1:])


def validate_request(value):
    require(value.get('schema') == 'STAGE05_UNC_BIND_PROBE_REQUEST_V1' and value.get('scope') == SCOPE
            and re.fullmatch('[a-f0-9]{32}', value.get('nonce', '')) is not None, 'Invalid probe request identity')
    require(value.get('root') == ROOT and value.get('target') == TARGET and value.get('unc') == str(UNC)
            and value.get('expected_python') == ENV + '/bin/python' and value.get('source_pins') == PINS,
            'Exact bind/UNC/runtime/helper roles differ')
    require(value.get('sentinel_name') == '.unc_visibility_' + value['nonce'], 'Sentinel name differs')
    for key in ('linux_payload_hex', 'windows_payload_hex'):
        payload = bytes.fromhex(value[key])
        require(64 <= len(payload) <= 512, 'Tiny exact sentinel payload required')
    require(value['linux_payload_hex'] != value['windows_payload_hex'], 'Bidirectional payloads must differ')


def read_request(path, expected):
    require(Path(path).parent.parent == WORK and Path(path) == Path(path).resolve()
            and not any(p.is_symlink() for p in (Path(path), *Path(path).parents)) and sha(path) == expected,
            'Exact new C bridge request/SHA required')
    value = json.loads(Path(path).read_bytes()); validate_request(value)
    require(value['script_sha256'] == sha(__file__), 'Executed probe source differs')
    return value


def tiny_read(path):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_nlink == 1
            and before.st_size <= 512, 'Sentinel nonregular/linked/oversized')
    with path.open('rb') as stream:
        require(os.fstat(stream.fileno()).st_ino == before.st_ino, 'Sentinel opened identity differs')
        data = stream.read(513)
        after = os.fstat(stream.fileno())
    end = path.lstat()
    fields = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink)
    require(fields(before) == fields(after) == fields(end), 'Sentinel identity changed during read')
    return data, dict(device=before.st_dev, inode=before.st_ino, bytes=len(data),
                      sha256=hashlib.sha256(data).hexdigest(), mtime_ns=before.st_mtime_ns)


def fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def linux_step(args):
    require(sys.platform == 'linux' and str(WORK) == LINUX_WORK, 'Exact mounted-C Linux probe required')
    request = Path(args.request); value = read_request(request, args.request_sha256)
    require(Path(sys.executable).resolve() == Path(value['expected_python']).resolve(), 'Retained interpreter differs')
    load_pinned('stage5_atomic_process.py')
    storage = load_pinned('stage5_work_storage.py')
    config_path = Path(value['config_linux_path'])
    require(config_path.parent == WORK and sha(config_path) == value['config_sha256'], 'Pinned C storage config differs')
    config = json.loads(config_path.read_bytes())
    proof = storage.validate_storage(config)
    directory = Path(TARGET) / value['sentinel_name']
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('Linux sentinel step exceeded30s')))
    signal.alarm(30)
    phase = 'prepared' if args.mode == 'linux-prepare' else 'final'
    result = dict(schema='STAGE05_UNC_BIND_LINUX_STEP_V1', scope=SCOPE, phase=phase,
                  state='FAILED', request_sha256=args.request_sha256, script_sha256=sha(__file__),
                  nonce=value['nonce'], storage_before=proof, child_processes_spawned=0)
    try:
        if phase == 'prepared':
            directory.mkdir(mode=0o700)
            payload = bytes.fromhex(value['linux_payload_hex'])
            with (directory / 'linux.bin').open('xb') as stream:
                stream.write(payload); stream.flush(); os.fsync(stream.fileno())
            fsync_directory(directory); fsync_directory(directory.parent)
            actual, record = tiny_read(directory / 'linux.bin')
            require(actual == payload and record['device'] == proof['directory_device'], 'Linux sentinel write/device differs')
            result.update(directory_device=directory.stat().st_dev, directory_inode=directory.stat().st_ino,
                          linux_file=record, state='PASS_LINUX_SENTINEL_PREPARED')
        else:
            prepared = json.loads((request.parent / 'prepared.json').read_bytes())
            io = json.loads((request.parent / 'windows_io.json').read_bytes())
            require(prepared['request_sha256'] == io['request_sha256'] == args.request_sha256
                    and prepared['state'] == 'PASS_LINUX_SENTINEL_PREPARED' and io['state'] == 'PASS_WINDOWS_UNC_WRITE_FSYNC_READ',
                    'Actual preceding phase receipts differ')
            require(proof == prepared['storage_before'] == prepared['storage_after']
                    and (directory.stat().st_dev, directory.stat().st_ino) ==
                    (prepared['directory_device'], prepared['directory_inode'])
                    and directory.stat().st_dev == proof['directory_device'] and not directory.is_symlink(),
                    'Bound sentinel directory/mount identity changed')
            require({p.name for p in directory.iterdir()} == {'linux.bin', 'windows.bin'}, 'Unknown sentinel contents; preserve')
            records = {}
            for name, key in (('linux.bin', 'linux_payload_hex'), ('windows.bin', 'windows_payload_hex')):
                data, record = tiny_read(directory / name)
                require(data == bytes.fromhex(value[key]) and record['device'] == proof['directory_device'],
                        'Actual Linux cross-OS payload/device differs')
                records[name] = record
            require(records['linux.bin'] == prepared['linux_file'], 'Original Linux sentinel identity changed')
            require(storage.validate_storage(config) == proof, 'Storage changed before exact owned cleanup')
            # Only our two exact byte/identity-checked leaves; no recursive deletion.
            for name, record in records.items():
                require(tiny_read(directory / name)[1] == record, 'Owned sentinel changed before cleanup')
                (directory / name).unlink()
            directory.rmdir(); fsync_directory(directory.parent)
            result.update(files=records, exact_owned_sentinel_cleanup=True, state='PASS_LINUX_UNC_READBACK_AND_EXACT_CLEANUP')
        result['storage_after'] = storage.validate_storage(config)
        require(result['storage_after'] == proof, 'Storage identity changed during sentinel operation')
        require(not any(p.read_text().strip() for p in Path('/proc/self/task').glob('*/children')),
                'Unexpected Linux child processes; closure requires reconciliation')
        result['linux_process'] = load_pinned('stage5_atomic_process.py').proc_record(os.getpid())
        write(request.parent / (phase + '.json'), result)
        return 0
    except BaseException as error:
        result['error'] = dict(kind=type(error).__name__, message=str(error))
        write(request.parent / (phase + '.failed.json'), result)
        raise
    finally:
        signal.alarm(0)


def windows_io(args):
    require(os.name == 'nt' and WORK == WINDOWS_WORK, 'Exact Windows C probe required')
    request = Path(args.request); value = read_request(request, args.request_sha256)
    directory = Path(value['unc']) / value['sentinel_name']
    data, linux = tiny_read(directory / 'linux.bin')
    require(data == bytes.fromhex(value['linux_payload_hex']), 'Windows UNC cannot read exact Linux bytes')
    payload = bytes.fromhex(value['windows_payload_hex'])
    with (directory / 'windows.bin').open('xb') as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    actual, windows = tiny_read(directory / 'windows.bin')
    require(actual == payload, 'Windows UNC fsync/readback differs')
    write(request.parent / 'windows_io.json', dict(schema='STAGE05_UNC_BIND_WINDOWS_IO_V1', scope=SCOPE,
          state='PASS_WINDOWS_UNC_WRITE_FSYNC_READ', request_sha256=args.request_sha256,
          script_sha256=sha(__file__), linux_file=linux, windows_file=windows))
    return 0


def windows_job(api, argv, owner):
    """One suspended, assigned, then resumed I/O child; active-process limit1."""
    job = api.create_job(None, None); require(job, 'Cannot create owned UNC I/O job')
    process = api.PROCESS(); created = False
    try:
        limits = api.EXTENDED(); limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x8
        limits.BasicLimitInformation.ActiveProcessLimit = 1
        api.ok(api.set_job(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)), 'Set owned UNC I/O job')
        startup = api.STARTUP(); startup.cb = ctypes.sizeof(startup)
        command = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        api.ok(api.create(str(sys.executable), command, None, None, False, 0x4 | 0x08000000,
                          None, str(WORK), ctypes.byref(startup), ctypes.byref(process)), 'Create suspended UNC I/O child')
        created = True
        birth = api.identity(process.hProcess, process.dwProcessId)
        require(Path(birth['executable']).resolve() == Path(sys.executable).resolve(), 'Actual UNC worker image differs')
        api.ok(api.assign(job, process.hProcess), 'Assign exact UNC I/O child')
        require(api.resume(process.hThread) != 0xffffffff, 'Resume exact UNC I/O child failed')
        if api.wait(process.hProcess, 20000) != 0:
            api.ok(api.terminate_job(job, 2), 'Terminate only owned timed-out UNC I/O job')
            require(api.wait(process.hProcess, 5000) == 0, 'Owned UNC I/O child closure unproven')
            raise TimeoutError('Owned Windows UNC I/O exceeded20s; stopped owned job')
        final = api.identity(process.hProcess, process.dwProcessId, birth['executable'], birth['session_id'])
        closure = api.job_state(job)
        require(final['creation_filetime'] == birth['creation_filetime'] and final['exited']
                and final['exit_code'] == 0 and closure['job_active_processes'] == 0 and not closure['job_pids'],
                'Exact Windows UNC child exit/job closure differs')
        return dict(argv=argv, birth=birth, exit=final, owned_job=closure)
    finally:
        closure_proven = True
        if created:
            try:
                if api.wait(process.hProcess, 0) != 0:
                    api.terminate(process.hProcess, 2); api.wait(process.hProcess, 5000)
                closure_proven = api.wait(process.hProcess, 0) == 0 and api.job_state(job)['job_active_processes'] == 0
            except BaseException:
                closure_proven = False
            api.close(process.hThread); api.close(process.hProcess)
        api.close(job)
        if not closure_proven:
            raise load_pinned('atomic_iqtree_windows.py').OwnedClosureFailure('Owned Windows UNC worker closure unproven')


def underlay_snapshot():
    for path in (G_UNDERLAY, *G_UNDERLAY.parents):
        info = path.lstat()
        require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT and not path.is_symlink(), 'G underlay alias/reparse')
    require(G_UNDERLAY.is_dir(), 'First-job Windows G underlay must already be a directory')
    with os.scandir(G_UNDERLAY) as entries:
        require(next(entries, None) is None, 'First-job Windows G underlay must be empty; preserve unknown data')
    info = G_UNDERLAY.stat()
    return dict(device=str(info.st_dev), inode=str(info.st_ino), mtime_ns=str(info.st_mtime_ns), entries=[])


def windows_owner(args):
    require(os.name == 'nt' and WORK == WINDOWS_WORK and os.environ.get('COMPUTERNAME', '').casefold() == 'wd', 'Exact WD C probe required')
    api_module = load_pinned('atomic_iqtree_windows.py')
    for name in PINS:
        require(sha(WORK / name) == PINS[name], 'Reviewed source drift')
    require(args.script_sha256 == sha(__file__), 'Explicit reviewed probe source SHA required')
    config_path = Path(args.config)
    require(config_path.parent == WORK and not config_path.is_symlink() and sha(config_path) == args.config_sha256, 'Exact pinned C config required')
    config = json.loads(config_path.read_bytes())
    require(config['root'] == ROOT and config['output_root'] == TARGET
            and config['runtime']['environment_dir'] == ENV, 'Exact storage/runtime config roles differ')
    proof_path = PurePosixPath(config['work_storage']['proof_path'])
    require(proof_path.parts[:3] == ('/', 'mnt', 'c') and '..' not in proof_path.parts, 'C-mounted storage proof required')
    proof_file = Path('C:/').joinpath(*proof_path.parts[3:])
    require(proof_file.parent == WORK and sha(proof_file) == config['work_storage']['proof_sha256'], 'Actual C storage proof differs')
    proof = json.loads(proof_file.read_bytes())
    require(proof['canonical_target'] == TARGET and proof['canonical_root'] == ROOT
            and proof['backing'] == '/var/tmp/lab_rm_stage05_atomic_v1'
            and proof['helper_sha256'] == PINS['stage5_work_storage.py'], 'Exact frozen bind proof differs')
    output = Path(args.output)
    require(output.is_absolute() and output.parent == WORK and output == output.resolve() and not output.exists(), 'Fresh direct C work spool required')
    stop_path = api_module.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
    require(not stop_path.exists(), 'Existing owned-closure stop requires reconciliation')
    output.mkdir()
    api = api_module.Win(); owner = api.identity(api.current(), os.getpid())
    result = dict(schema='STAGE05_EXACT_BIND_UNC_VISIBILITY_V1', scope=SCOPE, state='FAILED',
                  scientific_adoption_authorized=False, source_sha256=sha(__file__), source_pins=PINS,
                  config_sha256=args.config_sha256, actual_windows_owner=owner, steps=[])
    active = None
    with api_module.WorkflowLock(api) as lock:
        result['workflow_lock'] = lock.identity
        def authority():
            control = api_module.read_json(G_UNDERLAY.parents[1] / 'status/run_control.json')
            require(control.get('state') == 'ACTIVE_DIRECT_USER_CONTINUATION' and control.get('automatic_resume') is False,
                    'Fresh current direct authority absent')
        try:
            authority(); before = underlay_snapshot(); result['windows_g_underlay_before'] = before
            resources = api.resources([output, G_UNDERLAY])
            require(resources['physical_available_bytes'] >= api_module.RESERVE + 256 * 1024**2
                    and resources['commit_headroom_bytes'] >= api_module.RESERVE + 256 * 1024**2
                    and all(v >= 16 * 1024**2 for v in resources['disk_available_bytes'].values()), 'Tiny probe resource admission failed')
            result['resources'] = resources
            nonce = uuid.uuid4().hex
            value = dict(schema='STAGE05_UNC_BIND_PROBE_REQUEST_V1', scope=SCOPE, nonce=nonce,
                         root=ROOT, target=TARGET, unc=str(UNC), expected_python=ENV + '/bin/python',
                         sentinel_name='.unc_visibility_' + nonce, source_pins=PINS, script_sha256=sha(__file__),
                         config_linux_path=linux_path(config_path), config_sha256=args.config_sha256,
                         linux_payload_hex=(b'NONSCIENTIFIC LINUX\n' + os.urandom(96)).hex(),
                         windows_payload_hex=(b'NONSCIENTIFIC WINDOWS UNC\n' + os.urandom(96)).hex(),
                         actual_windows_owner=owner, workflow_lock=lock.identity)
            request = output / 'request.json'; write(request, value); request_sha = sha(request)
            for phase in ('linux-prepare', 'windows-io', 'linux-finalize'):
                authority()
                require(all(sha(WORK / n) == p for n, p in PINS.items()) and sha(__file__) == args.script_sha256
                        and sha(config_path) == args.config_sha256 and underlay_snapshot() == before, 'Source/config/G underlay drift')
                if phase == 'windows-io':
                    result['steps'].append(dict(phase=phase, **windows_job(api,
                        [sys.executable, '-B', str(Path(__file__)), '--mode', phase, '--request', str(request),
                         '--request-sha256', request_sha, '--run'], owner)))
                    continue
                argv = [WSL, '-d', 'Ubuntu', '-u', 'root', '--exec', ENV + '/bin/python', '-B', linux_path(Path(__file__)),
                        '--mode', phase, '--request', linux_path(request), '--request-sha256', request_sha, '--run']
                with (output / (phase + '.stdout.txt')).open('wb') as stdout, (output / (phase + '.stderr.txt')).open('wb') as stderr:
                    active = subprocess.Popen(argv, stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
                    birth = api.identity(int(active._handle), active.pid, WSL, owner['session_id'])
                    require(Path(birth['executable']).resolve() == Path(WSL).resolve(), 'Actual WSL client image differs')
                    try:
                        active.wait(timeout=40)
                    except subprocess.TimeoutExpired:
                        write(stop_path, dict(schema='STAGE05_UNC_PROBE_CLOSURE_UNPROVEN_V1', state='BLOCK_NEW_STAGE5',
                              scope=SCOPE, actual_wsl_client=birth, request_sha256=request_sha, spool=str(output)))
                        raise RuntimeError('WSL sentinel closure unproven; durable Stage5 stop written')
                    final = api.identity(int(active._handle), active.pid, birth['executable'], birth['session_id'])
                    require(final['creation_filetime'] == birth['creation_filetime'] and final['exited']
                            and final['exit_filetime'] > final['creation_filetime'] and final['exit_code'] == 0,
                            'Actual retained WSL client exit differs')
                    result['steps'].append(dict(phase=phase, argv=argv, birth=birth, exit=final))
                    active = None
                receipt = json.loads((output / ('prepared.json' if phase == 'linux-prepare' else 'final.json')).read_bytes())
                require(receipt['scope'] == SCOPE and receipt['request_sha256'] == request_sha
                        and receipt['script_sha256'] == args.script_sha256 and receipt['nonce'] == nonce
                        and receipt['storage_before'] == receipt['storage_after'] == {'proof_path': config['work_storage']['proof_path'],
                            'proof_sha256': config['work_storage']['proof_sha256'], **proof}, 'Actual Linux source/storage receipt differs')
            final_receipt = json.loads((output / 'final.json').read_bytes())
            require(final_receipt['state'] == 'PASS_LINUX_UNC_READBACK_AND_EXACT_CLEANUP'
                    and final_receipt['exact_owned_sentinel_cleanup'] is True
                    and underlay_snapshot() == before,
                    'Actual Linux cleanup/G underlay preservation failed')
            result.update(state='PASS_NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY', request_sha256=request_sha,
                          windows_g_underlay_after=underlay_snapshot(), exact_owned_cleanup=True,
                          cleanup_proof='PINNED_LINUX_EXACT_TWO_LEAF_UNLINK_AND_DIRECTORY_RMDIR_CURRENT_STORAGE_PROOF',
                          final_windows_unc_absence_query=False,
                          files={p.name: sha(p) for p in output.iterdir() if p.is_file()})
        except BaseException as error:
            result['error'] = dict(kind=type(error).__name__, message=str(error))
            if ((active is not None and active.poll() is None) or isinstance(error, api_module.OwnedClosureFailure)) and not stop_path.exists():
                write(stop_path, dict(schema='STAGE05_UNC_PROBE_CLOSURE_UNPROVEN_V1', state='BLOCK_NEW_STAGE5',
                      scope=SCOPE, actual_wsl_client_pid=None if active is None else active.pid, spool=str(output)))
        finally:
            write(output / 'result.json', result)
    write(output / 'lock_released.json', dict(scope=SCOPE, released=lock.released,
          state='EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK', scientific_adoption_authorized=False))
    print(json.dumps(dict(state=result['state'], result=str(output / 'result.json'))))
    return 0 if result['state'].startswith('PASS_') else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('owner', 'linux-prepare', 'windows-io', 'linux-finalize'), default='owner')
    parser.add_argument('--request'); parser.add_argument('--request-sha256')
    parser.add_argument('--config'); parser.add_argument('--config-sha256'); parser.add_argument('--script-sha256')
    parser.add_argument('--output'); parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.mode != 'owner':
        require(args.run, 'Actual internal sentinel step requires explicit --run and current owner request')
        return windows_io(args) if args.mode == 'windows-io' else linux_step(args)
    if not args.run:
        print(json.dumps(dict(state='PREPARED_NOT_RUN', scope=SCOPE, source_sha256=sha(__file__), source_pins=PINS,
                              exact_unc=str(UNC), maximum_linux_step_seconds=40, maximum_windows_io_seconds=25,
                              scientific_adoption_authorized=False)))
        return 0
    return windows_owner(args)


if __name__ == '__main__':
    raise SystemExit(main())
