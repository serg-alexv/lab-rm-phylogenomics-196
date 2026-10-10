"""Default-noop exact UNC02 sentinel diagnosis under the existing U.windows_job.

Reads only four exact public sentinel leaves and stats their two directories.
Writes only a fresh C diagnostic spool. No WSL invocation, Linux process, UNC
write, cleanup, or probe relaxation. Lower-level bounded reads are diagnostics.
"""
from pathlib import Path, PureWindowsPath
import argparse
import hashlib
import importlib
import json
import os
import re
import stat
import sys

sys.dont_write_bytecode = True
WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
FAILED = WORK/'stage5_unc_bind_actual_postiq_02'
REQUEST_SHA = 'b32fceaaf4757d2bd59c44004f4cd3c8ac502441692e621c9c05c80f61908e1c'
PINS = {'atomic_iqtree_windows.py': '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
        'stage5_unc_bind_probe.py': '0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d'}
RESERVE = 1879048192
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
UBUNTU_KEY = r'Software\Microsoft\Windows\CurrentVersion\Lxss\{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}'


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def error_record(error):
    return {'kind': type(error).__name__, 'message': str(error)[:768],
            'errno': getattr(error, 'errno', None), 'winerror': getattr(error, 'winerror', None)}


def modules():
    need(os.name == 'nt' and Path(__file__).resolve().parent == WORK
         and os.environ.get('COMPUTERNAME', '').casefold() == 'wd', 'Exact WD Windows C diagnostic required')
    selected = []
    for name, pin in PINS.items():
        need(sha(WORK/name) == pin, 'Published diagnostic dependency drift')
        module = importlib.import_module(Path(name).stem)
        need(Path(module.__file__).resolve() == WORK/name and sha(module.__file__) == pin,
             'Diagnostic dependency import/location drift')
        selected.append(module)
    return selected


def plain_c(path):
    path = Path(path)
    need(path.is_absolute() and path == path.resolve() and (path == WORK or WORK in path.parents),
         'Exact diagnostic C-work path required')
    for item in (path, *path.parents):
        if item == path and not item.exists():
            continue
        info = item.lstat()
        need(not item.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'Diagnostic C ancestry aliases rejected')


def original_request(U):
    path = FAILED/'request.json'
    plain_c(path)
    need(path.stat().st_size <= 65536 and sha(path) == REQUEST_SHA, 'Exact failed UNC02 request required')
    value = U.read_request(path, REQUEST_SHA)
    need(value['script_sha256'] == PINS['stage5_unc_bind_probe.py'], 'Original probe source differs')
    return value


def targets(value):
    """Fixed request supplies the exact nonce; no caller-selected UNC path."""
    need(re.fullmatch('[a-f0-9]{32}', value['nonce']) and value['sentinel_name'] == '.unc_visibility_'+value['nonce'],
         'Exact public failed sentinel nonce required')
    canonical = PureWindowsPath(value['unc'])/value['sentinel_name']
    backing = PureWindowsPath(r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1')/value['sentinel_name']
    return [{'role': prefix+'_'+leaf[:-4], 'path': str(root/leaf),
             'expected_bytes': len(bytes.fromhex(value[key])),
             'expected_sha256': hashlib.sha256(bytes.fromhex(value[key])).hexdigest()}
            for prefix, root in [('canonical', canonical), ('backing', backing)]
            for leaf, key in [('linux.bin', 'linux_payload_hex'), ('windows.bin', 'windows_payload_hex')]]


def directory_targets(value):
    leaves = targets(value)
    return [{'role': prefix+'_directory', 'path': str(PureWindowsPath(leaves[index]['path']).parent)}
            for prefix, index in [('canonical', 0), ('backing', 2)]]


def authority(A):
    path = ROOT/'status/run_control.json'
    need(path.stat().st_size <= 65536, 'Bounded current authority required')
    value = A.read_json(path)
    need(value.get('state') == 'ACTIVE_DIRECT_USER_CONTINUATION' and value.get('automatic_resume') is False,
         'Current direct continuation authority absent')
    return sha(path)


def ubuntu_identity():
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UBUNTU_KEY, 0, winreg.KEY_QUERY_VALUE) as key:
        values = {name: winreg.QueryValueEx(key, name)[0]
                  for name in ('DistributionName', 'Version', 'DefaultUid', 'Flags', 'BasePath')}
    need(values['DistributionName'] == 'Ubuntu' and values['Version'] == 2
         and type(values['DefaultUid']) is int and values['DefaultUid'] >= 0
         and type(values['Flags']) is int
         and Path(values['BasePath']) == Path(r'C:\Users\wheel\AppData\Local\wsl\{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}'),
         'Exact Ubuntu default-user registration differs')
    return values


def metadata(info):
    return {'mode': info.st_mode, 'regular': stat.S_ISREG(info.st_mode),
            'directory': stat.S_ISDIR(info.st_mode), 'uid': info.st_uid, 'gid': info.st_gid,
            'nlink': info.st_nlink, 'device': info.st_dev, 'inode': info.st_ino,
            'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns,
            'file_attributes': getattr(info, 'st_file_attributes', None),
            'reparse_point': bool(getattr(info, 'st_file_attributes', 0) & 0x400),
            'reparse_tag': getattr(info, 'st_reparse_tag', None)}


def inspect_directory(row, progress, path_factory=Path):
    result = dict(row)
    progress(row['role'], 'before_directory_lstat')
    try:
        result['metadata'] = metadata(path_factory(row['path']).lstat())
    except BaseException as error:
        result['metadata_error'] = error_record(error)
    return result


def inspect_leaf(row, tiny_read, progress, path_factory=Path):
    """Record metadata and unchanged U.tiny_read failure independently; no writes."""
    result = dict(row)
    path = path_factory(row['path'])
    progress(row['role'], 'before_lstat')
    try:
        result['metadata_before'] = metadata(path.lstat())
    except BaseException as error:
        result['metadata_error'] = error_record(error)
    progress(row['role'], 'before_exact_original_tiny_read')
    try:
        payload, receipt = tiny_read(path)
        need(isinstance(payload, bytes) and len(payload) <= 513, 'Original tiny read returned unbounded/nonbinary data')
        result['tiny_read_receipt'] = receipt
        result['payload_bytes'] = len(payload)
        result['payload_sha256'] = hashlib.sha256(payload).hexdigest()
        result['matches_original_request_payload'] = (len(payload) == row['expected_bytes']
                                                      and result['payload_sha256'] == row['expected_sha256'])
    except BaseException as error:
        result['tiny_read_error'] = error_record(error)
    # Independent bounded read only. Never substitutes for U.tiny_read adoption.
    progress(row['role'], 'before_bounded_readonly_payload_observation')
    try:
        before = path.lstat()
        need(stat.S_ISREG(before.st_mode) and not path.is_symlink()
             and not getattr(before, 'st_file_attributes', 0) & 0x400 and before.st_size <= 512,
             'Diagnostic read requires a bounded regular non-reparse sentinel')
        with path.open('rb') as stream:
            opened = metadata(os.fstat(stream.fileno()))
            payload = stream.read(513)
            after = metadata(os.fstat(stream.fileno()))
        need(len(payload) <= 512, 'Diagnostic payload grew beyond the fixed read bound')
        result['readonly_payload_observation'] = {'metadata_before': metadata(before),
            'metadata_opened': opened, 'metadata_after_open': after, 'payload_bytes': len(payload),
            'payload_sha256': hashlib.sha256(payload).hexdigest(),
            'matches_original_request_payload': len(payload) == row['expected_bytes']
                 and hashlib.sha256(payload).hexdigest() == row['expected_sha256'],
            'scientific_or_UNC_adoption': False}
    except BaseException as error:
        result['readonly_payload_error'] = error_record(error)
    progress(row['role'], 'before_final_lstat')
    try:
        result['metadata_after'] = metadata(path.lstat())
    except BaseException as error:
        result['metadata_after_error'] = error_record(error)
    return result


def resources(api, output):
    value = api.resources([WORK, output])
    need(value['physical_available_bytes'] >= RESERVE and value['commit_headroom_bytes'] >= RESERVE
         and all(free >= 10737418240 for free in value['disk_available_bytes'].values()),
         'Current bounded diagnostic physical/commit/disk reserve insufficient')
    return value


def worker(args):
    A, U = modules()
    request = Path(args.diagnostic_request)
    plain_c(request)
    need(request.name == 'diagnostic_request.json' and request.parent.parent == WORK
         and re.fullmatch('stage5_unc02_diagnostic_[A-Za-z0-9_]+', request.parent.name)
         and request.stat().st_size <= 65536 and sha(request) == args.diagnostic_request_sha256,
         'Exact owned diagnostic request required')
    value = json.loads(request.read_bytes()); output = request.parent
    need(value['schema'] == 'STAGE05_UNC02_READONLY_DIAGNOSTIC_REQUEST_V1'
         and value['source_sha256'] == args.source_sha256 == sha(__file__)
         and value['source_pins'] == PINS and value['original_request_sha256'] == REQUEST_SHA,
         'Exact diagnostic source/request binding differs')
    original = original_request(U)
    need(value['targets'] == targets(original), 'Diagnostic targets differ from exact failed request')
    need(value['directories'] == directory_targets(original), 'Diagnostic directory targets differ')
    need(value['workflow_lock'] == {'path': str(A.ORIGINAL_LOCK), 'volume_serial': A.LOCK_IDENTITY[0],
         'file_index': A.LOCK_IDENTITY[1], 'creation_filetime': A.LOCK_IDENTITY[2], 'locked_byte': 0},
         'Original WorkflowLock witness differs')
    api = A.Win()
    need(not (output/'worker_progress.json').exists() and not (output/'worker_result.json').exists(),
         'Preserve prior diagnostic worker evidence')
    need(authority(A) == value['authority_sha256'] and ubuntu_identity() == value['Ubuntu_registration'],
         'Current authority or Ubuntu registration changed')
    record = {'schema': 'STAGE05_UNC02_READONLY_WORKER_V1', 'state': 'FAILED',
              'source_sha256': args.source_sha256, 'original_request_sha256': REQUEST_SHA,
              'diagnostic_request_sha256': args.diagnostic_request_sha256, 'observations': [],
              'directory_observations': [], 'Ubuntu_registration': value['Ubuntu_registration'],
              'UNC_writes': 0, 'WSL_launches': 0, 'cleanup_performed': False, 'scientific_adoption_authorized': False}
    def progress(role, phase):
        need(authority(A) == value['authority_sha256'], 'Current direct authority changed')
        need(not A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json').exists(),
             'Unproven closure STOP vetoes further diagnostic reads')
        resources(api, output)
        A.atomic(output/'worker_progress.json', {**record, 'active_role': role, 'active_phase': phase, 'utc': A.utc()})
    try:
        for row in value['directories']:
            record['directory_observations'].append(inspect_directory(row, progress))
        for row in value['targets']:
            record['observations'].append(inspect_leaf(row, U.tiny_read, progress))
        need(sha(__file__) == args.source_sha256 and sha(FAILED/'request.json') == REQUEST_SHA
             and all(sha(WORK/name) == pin for name, pin in PINS.items()), 'Final diagnostic source/request drift')
        need(authority(A) == value['authority_sha256'] and ubuntu_identity() == value['Ubuntu_registration'],
             'Final authority or Ubuntu registration changed')
        record['state'] = 'PASS_READONLY_DIAGNOSTIC_COMPLETE_NO_PROBE_ADOPTION'
    except BaseException as error:
        record['error'] = error_record(error)
    finally:
        A.atomic(output/'worker_result.json', {**record, 'utc': A.utc()})
    return 0 if record['state'].startswith('PASS_') else 2


def owner(args):
    A, U = modules()
    need(args.source_sha256 == sha(__file__), 'Explicit reviewed diagnostic source SHA required')
    output = Path(args.output); plain_c(output)
    need(output.parent == WORK and re.fullmatch('stage5_unc02_diagnostic_[A-Za-z0-9_]+', output.name)
         and not output.exists(), 'Fresh direct C diagnostic output required')
    original = original_request(U)
    output.mkdir()
    api = A.Win(); current = api.identity(api.current(), os.getpid()); lock = A.WorkflowLock(api)
    stop = A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
    record = {'schema': 'STAGE05_UNC02_READONLY_OWNER_V1', 'state': 'FAILED', 'source_sha256': args.source_sha256,
              'source_pins': PINS, 'original_request_sha256': REQUEST_SHA, 'actual_windows_owner': current,
              'UNC_writes': 0, 'WSL_launches': 0, 'cleanup_performed': False, 'scientific_adoption_authorized': False}
    try:
        with lock:
            need(not stop.exists(), 'Existing unproven closure STOP vetoes diagnostic launch')
            record['workflow_lock'] = lock.identity; record['resources'] = resources(api, output)
            record['authority_sha256'] = authority(A); record['Ubuntu_registration'] = ubuntu_identity()
            request = {'schema': 'STAGE05_UNC02_READONLY_DIAGNOSTIC_REQUEST_V1', 'source_sha256': args.source_sha256,
                       'source_pins': PINS, 'original_request_sha256': REQUEST_SHA, 'targets': targets(original),
                       'directories': directory_targets(original), 'authority_sha256': record['authority_sha256'],
                       'Ubuntu_registration': record['Ubuntu_registration'],
                       'workflow_lock': lock.identity, 'actual_windows_owner': current}
            path = output/'diagnostic_request.json'; A.atomic(path, request)
            try:
                record['windows_worker'] = U.windows_job(api, [sys.executable, '-B', str(Path(__file__).resolve()),
                    '--worker', '--diagnostic-request', str(path), '--diagnostic-request-sha256', sha(path),
                    '--source-sha256', args.source_sha256], current, output/'windows_readonly_worker')
            except A.OwnedClosureFailure:
                if not stop.exists():
                    A.atomic(stop, {'schema': 'STAGE05_UNC02_DIAGNOSTIC_CLOSURE_UNPROVEN_V1',
                        'state': 'BLOCK_NEW_STAGE5', 'evidence': str(output), 'utc': A.utc(), 'automatic_resume': False})
                raise
            worker_result = output/'worker_result.json'
            need(worker_result.stat().st_size <= 65536, 'Bounded worker result required')
            final = json.loads(worker_result.read_bytes())
            need(final['state'] == 'PASS_READONLY_DIAGNOSTIC_COMPLETE_NO_PROBE_ADOPTION'
                 and final['source_sha256'] == args.source_sha256 and final['original_request_sha256'] == REQUEST_SHA
                 and final['diagnostic_request_sha256'] == sha(path)
                 and len(final['observations']) == 4 and len(final['directory_observations']) == 2
                 and final['Ubuntu_registration'] == record['Ubuntu_registration'], 'Actual diagnostic worker result differs')
            need(sha(__file__) == args.source_sha256 and sha(FAILED/'request.json') == REQUEST_SHA
                 and all(sha(WORK/name) == pin for name, pin in PINS.items()), 'Final diagnostic source/request drift')
            need(authority(A) == record['authority_sha256'] and ubuntu_identity() == record['Ubuntu_registration'],
                 'Final owner authority or Ubuntu registration changed')
            need(not stop.exists(), 'Unproven closure STOP vetoes diagnostic acceptance')
            record['resources_after'] = resources(api, output)
            record['worker_result_sha256'] = sha(worker_result)
            record['state'] = 'PASS_READONLY_DIAGNOSTIC_AND_EXACT_OWNED_WINDOWS_CLOSURE'
    except BaseException as error:
        record['error'] = error_record(error)
    finally:
        record.update(original_lock_released=lock.released, unknown_closure_STOP_present=stop.exists(), utc=A.utc())
        A.atomic(output/'result.json', record)
    print(json.dumps({'state': record['state'], 'result': str(output/'result.json')}))
    return 0 if record['state'].startswith('PASS_') and lock.released else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--worker', action='store_true')
    parser.add_argument('--source-sha256'); parser.add_argument('--output')
    parser.add_argument('--diagnostic-request'); parser.add_argument('--diagnostic-request-sha256')
    args = parser.parse_args()
    if args.worker:
        need(args.diagnostic_request and args.diagnostic_request_sha256 and args.source_sha256, 'Explicit worker inputs required')
        return worker(args)
    if not args.run:
        print(json.dumps({'state': 'PREPARED_READONLY_DIAGNOSTIC_NOT_RUN', 'WSL_launches': 0, 'UNC_writes': 0})); return 0
    need(args.output and args.source_sha256, 'Explicit fresh output and source SHA required')
    return owner(args)


if __name__ == '__main__':
    raise SystemExit(main())
