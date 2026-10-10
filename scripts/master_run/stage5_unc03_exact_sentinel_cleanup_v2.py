"""Default-NOOP exact failed UNC03 sentinel cleanup; one existing owned Windows Job.

No WSL launch, science, arbitrary target, recursive deletion or probe adoption.
Durable C payload/metadata backup precedes exact known leaf unlink and empty rmdir.
"""
from pathlib import Path
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
FAILED = WORK/'stage5_unc_bind_actual_postiq_03'
REQUEST_SHA = '7f28e209707483d1a50e25c7d35e5804f2b9ebb8ecf9bcc110714849228ce27d'
EXPECTED_NONCE = '8ae35884653047348cfa688d4bf00b36'
BACKING = r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1'
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
RESERVE = 1879048192
PINS = {'atomic_iqtree_windows.py': '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
        'stage5_unc_bind_probe.py': '0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d'}
RECEIPTS = {
    'stage5_unc03_failed_scope_independent_review01.json': 'a3beba2bddf24c460c61dfe395caa680a600ffdc7314f06d3219bc8c457561cd',
    'stage5_unc03_diagnostic_actual01_independent_review.json': '320711555b317475cbe3242c20b28075ab08de2d67b832a00b906ac0dc25802f',
    'stage5_unc03_diagnostic_actual01/worker_result.json': 'c6b6dc469aa6ab725e36ca09c7c87ddaa8cd84ba7069c9b7fa48fc5ea264cae8',
    'stage5_unc03_diagnostic_actual01/result.json': 'c4e7f98bf174a3ddefbfc6ed9d3c7c0c910e907f6f775f2db12e3d500a3ec2a0',
    'stage5_unc_bind_actual_postiq_03/lock_released.json': 'f5c3222f1c568cff2a9852fcb89f0dd34caf6c55d83b12ca7f628fb658615373',
}
EXPECTED_LEAF = {'mode': 33206, 'regular': True, 'directory': False, 'uid': 0, 'gid': 0, 'nlink': 1, 'device': 0, 'inode': 33554461, 'bytes': 116, 'mtime_ns': 1791601426761082800, 'file_attributes': 128, 'reparse_point': False, 'reparse_tag': 0}
EXPECTED_DIRECTORY = {'mode': 16895, 'regular': False, 'directory': True, 'uid': 0, 'gid': 0, 'nlink': 2, 'device': 0, 'inode': 33554454, 'bytes': 0, 'mtime_ns': 1791601426758035500, 'file_attributes': 16, 'reparse_point': False, 'reparse_tag': 0}

def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def error_record(error):
    return {'kind': type(error).__name__, 'message': str(error)[:768],
            'errno': getattr(error, 'errno', None), 'winerror': getattr(error, 'winerror', None)}


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
    need(path.stat().st_size <= 65536 and sha(path) == REQUEST_SHA, 'Exact failed UNC03 request required')
    value = U.read_request(path, REQUEST_SHA)
    need(value['script_sha256'] == PINS['stage5_unc_bind_probe.py'], 'Original probe source differs')
    return value


def authority(A):
    path = ROOT/'status/run_control.json'
    need(path.stat().st_size <= 65536, 'Bounded current authority required')
    value = A.read_json(path)
    need(value.get('state') == 'ACTIVE_DIRECT_USER_CONTINUATION' and value.get('automatic_resume') is False,
         'Current direct continuation authority absent')
    return sha(path)


def metadata(info):
    return {'mode': info.st_mode, 'regular': stat.S_ISREG(info.st_mode),
            'directory': stat.S_ISDIR(info.st_mode), 'uid': info.st_uid, 'gid': info.st_gid,
            'nlink': info.st_nlink, 'device': info.st_dev, 'inode': info.st_ino,
            'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns,
            'file_attributes': getattr(info, 'st_file_attributes', None),
            'reparse_point': bool(getattr(info, 'st_file_attributes', 0) & 0x400),
            'reparse_tag': getattr(info, 'st_reparse_tag', None)}


def modules():
    need(os.name == 'nt' and Path(__file__).resolve().parent == WORK
         and os.environ.get('COMPUTERNAME', '').casefold() == 'wd', 'Exact WD C cleanup required')
    result = []
    for name, pin in PINS.items():
        need(sha(WORK/name) == pin, 'Published cleanup dependency drift')
        module = importlib.import_module(Path(name).stem)
        need(Path(module.__file__).resolve() == WORK/name and sha(module.__file__) == pin,
             'Cleanup dependency location/bytes differ')
        result.append(module)
    return result


def controls():
    result = {}
    for name, pin in RECEIPTS.items():
        path = WORK/name; plain_c(path)
        need(path.stat().st_size <= 65536, 'Cleanup control exceeds bound')
        raw = path.read_bytes()
        need(hashlib.sha256(raw).hexdigest() == pin, 'Exact prior cleanup control bytes differ')
        result[name] = json.loads(raw)
    failed = result['stage5_unc03_failed_scope_independent_review01.json']
    diagnostic = result['stage5_unc03_diagnostic_actual01_independent_review.json']
    owner = result['stage5_unc03_diagnostic_actual01/result.json']
    need(failed['state'] == 'PASS_FAILED_UNC03_RETAINED_SCOPE_CLOSED_CAUSE_UNRECORDED'
         and failed['owned_closure_proven'] is True and failed['original_lock_explicitly_released'] is True
         and diagnostic['state'] == 'PASS_EXACT_UNC03_DIAGNOSTIC_BYTES_AND_RETAINED_CLOSURE_UNC_GATE_STILL_FAILED'
         and diagnostic['owned_closure_proven'] is True and diagnostic['owned_job_empty'] is True
         and owner['original_lock_released'] is True and owner['unknown_closure_STOP_present'] is False
         and result['stage5_unc_bind_actual_postiq_03/lock_released.json']['released'] is True,
         'Earlier failed/diagnostic scopes are not explicitly closed')
    return result


def fixed_directory(original, path_factory=Path):
    need(original['nonce'] == EXPECTED_NONCE
         and original['sentinel_name'] == '.unc_visibility_' + EXPECTED_NONCE,
         'Only the exact failed UNC03 nonce is eligible')
    payload = bytes.fromhex(original['linux_payload_hex'])
    need(len(payload) == 116 and hashlib.sha256(payload).hexdigest()
         == '4a90f5d4c9fa4130234bfc121f1e1dd47cde726546840a3085d9e4b5875a0ff5',
         'Only the exact known public Linux payload is eligible')
    return path_factory(BACKING)/original['sentinel_name']


def check_metadata(path, expected, ignore=()):
    current = metadata(path.lstat())
    need(all(type(current[key]) is type(value) and current[key] == value
             for key, value in expected.items() if key not in ignore),
         'Known sentinel object/metadata differs')
    need(not path.is_symlink() and current['reparse_point'] is False, 'Sentinel alias rejected')
    return current


def entry_names(path):
    names = []
    with os.scandir(path) as stream:
        for item in stream:
            need(len(names) < 2, 'Unexpected extra entries; never recursively clean')
            names.append(item.name)
    return sorted(names)


def require_absent(path):
    try:
        path.lstat()
    except FileNotFoundError as error:
        need(getattr(error, 'winerror', None) == 2, 'Exact Windows missing-leaf result required')
        return
    raise ValueError('Known absent sentinel unexpectedly exists')


def save_backup(output, payload, receipt, directory_metadata, atomic):
    """Both fsynced files are read back before either UNC deletion is eligible."""
    plain_c(output)
    payload_path = output/'linux.bin.backup'
    with payload_path.open('xb') as stream:
        need(stream.write(payload) == len(payload), 'Incomplete C sentinel backup')
        stream.flush(); os.fsync(stream.fileno())
    value = {'schema': 'STAGE05_UNC03_EXACT_SENTINEL_BACKUP_V1',
        'original_request_sha256': REQUEST_SHA, 'source_sha256': sha(__file__),
        'payload_bytes': len(payload), 'payload_sha256': hashlib.sha256(payload).hexdigest(),
        'original_tiny_read_receipt': receipt, 'Windows_projected_leaf_metadata': EXPECTED_LEAF,
        'Windows_projected_directory_metadata': directory_metadata,
        'prior_control_pins': RECEIPTS, 'restoration_requires_original_prepared_Linux_metadata': True,
        'failed_probe_state_unchanged': True, 'scientific_adoption_authorized': False}
    metadata_path = output/'backup_metadata.json'
    need(not metadata_path.exists(), 'Preserve prior backup metadata')
    atomic(metadata_path, value)
    raw = metadata_path.read_bytes()
    need(payload_path.read_bytes() == payload and json.loads(raw) == value,
         'C payload/metadata backup readback differs')
    return {'payload_path': str(payload_path), 'payload_sha256': sha(payload_path),
            'metadata_path': str(metadata_path), 'metadata_sha256': hashlib.sha256(raw).hexdigest(),
            'fsync_and_readback_before_UNC_effects': True}


def exact_cleanup(original, tiny_read, output, progress, atomic, path_factory=Path,
                  listing=entry_names, backup=save_backup):
    """Two fixed effects; failures preserve C backup and never adopt probe success."""
    directory = fixed_directory(original, path_factory)
    leaf = directory/'linux.bin'; absent = directory/'windows.bin'
    progress('PRECHECK_EXACT_DIRECTORY_AND_SINGLE_LEAF', {})
    before_directory = check_metadata(directory, EXPECTED_DIRECTORY)
    check_metadata(leaf, EXPECTED_LEAF)
    require_absent(absent)
    need(listing(directory) == ['linux.bin'], 'Only the known single Linux leaf may be removed')
    payload, receipt = tiny_read(leaf)
    expected = bytes.fromhex(original['linux_payload_hex'])
    need(payload == expected and receipt == {'device': 0, 'inode': 33554461, 'bytes': 116,
         'sha256': hashlib.sha256(expected).hexdigest(), 'mtime_ns': EXPECTED_LEAF['mtime_ns']},
         'Original tiny_read exact payload/object receipt differs')
    backup_receipt = backup(output, payload, receipt, before_directory, atomic)
    need(backup_receipt['fsync_and_readback_before_UNC_effects'] is True, 'Durable C backup missing')
    progress('BEFORE_EXACT_LEAF_UNLINK', {'backup': backup_receipt,
             'intent': {'effect': 'unlink', 'target': str(leaf), 'expected': EXPECTED_LEAF}})
    check_metadata(directory, EXPECTED_DIRECTORY); check_metadata(leaf, EXPECTED_LEAF)
    require_absent(absent)
    need(listing(directory) == ['linux.bin'], 'Entries changed before exact leaf unlink')
    payload_again, receipt_again = tiny_read(leaf)
    need(payload_again == payload and receipt_again == receipt, 'Leaf changed immediately before unlink')
    check_metadata(leaf, EXPECTED_LEAF)
    leaf.unlink()
    progress('EXACT_LEAF_UNLINK_RETURNED', {'backup': backup_receipt, 'leaf_unlink_returned': True})
    require_absent(leaf); require_absent(absent)
    current_directory = check_metadata(directory, EXPECTED_DIRECTORY, ignore=('mtime_ns',))
    need(listing(directory) == [], 'Exact directory is not empty; no recursive cleanup')
    progress('BEFORE_EXACT_EMPTY_DIRECTORY_RMDIR', {'backup': backup_receipt,
             'leaf_unlink_returned': True, 'intent': {'effect': 'rmdir', 'target': str(directory),
             'expected_identity': current_directory}})
    check_metadata(directory, current_directory); need(listing(directory) == [], 'Directory changed before rmdir')
    directory.rmdir(); require_absent(directory)
    progress('EXACT_EMPTY_DIRECTORY_RMDIR_RETURNED', {'backup': backup_receipt,
             'leaf_unlink_returned': True, 'empty_directory_rmdir_returned': True})
    return {'backup': backup_receipt, 'leaf_unlink_returned': True,
            'empty_directory_rmdir_returned': True, 'exact_owned_cleanup': True,
            'targets': [str(leaf), str(directory)], 'probe_success_claimed': False}


def lock_identity(A):
    return {'path': str(A.ORIGINAL_LOCK), 'volume_serial': A.LOCK_IDENTITY[0],
            'file_index': A.LOCK_IDENTITY[1], 'creation_filetime': A.LOCK_IDENTITY[2], 'locked_byte': 0}


def worker(args):
    A, U = modules()
    path = Path(args.cleanup_request); plain_c(path)
    need(path.name == 'cleanup_request.json' and path.parent.parent == WORK
         and re.fullmatch('stage5_unc03_cleanup_[A-Za-z0-9_]+', path.parent.name)
         and path.stat().st_size <= 65536, 'Exact fresh C cleanup request required')
    raw = path.read_bytes(); need(hashlib.sha256(raw).hexdigest() == args.cleanup_request_sha256,
                               'Exact cleanup request bytes differ')
    value = json.loads(raw); output = path.parent
    need(value['schema'] == 'STAGE05_UNC03_EXACT_CLEANUP_REQUEST_V1'
         and value['source_sha256'] == args.source_sha256 == sha(__file__)
         and value['source_pins'] == PINS and value['prior_control_pins'] == RECEIPTS
         and value['workflow_lock'] == lock_identity(A) and value['original_request_sha256'] == REQUEST_SHA,
         'Exact reviewed cleanup request/lock/source differs')
    controls(); original = original_request(U)
    need(value['target_directory'] == str(fixed_directory(original)), 'Fixed failed nonce target differs')
    api = A.Win(); stop = A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
    record = {'schema': 'STAGE05_UNC03_EXACT_CLEANUP_WORKER_V1', 'state': 'FAILED',
        'source_sha256': args.source_sha256, 'cleanup_request_sha256': args.cleanup_request_sha256,
        'original_request_sha256': REQUEST_SHA, 'WSL_launches': 0,
        'probe_success_claimed': False, 'scientific_adoption_authorized': False}
    def progress(phase, details):
        need(not stop.exists() and authority(A) == value['authority_sha256'], 'STOP or changed authority vetoes cleanup')
        resources(api, output)
        record.update(details)
        A.atomic(output/'worker_progress.json', {**record, 'phase': phase, 'utc': A.utc()})
    try:
        result = exact_cleanup(original, U.tiny_read, output, progress, A.atomic)
        record.update(result)
        need(sha(__file__) == args.source_sha256 and authority(A) == value['authority_sha256']
             and all(sha(WORK/name) == pin for name, pin in PINS.items()), 'Final cleanup source/authority drift')
        controls(); original_request(U)
        record['state'] = 'PASS_EXACT_FAILED03_SENTINEL_BACKUP_AND_TWO_OBJECT_CLEANUP_ONLY'
    except BaseException as error:
        record['error'] = error_record(error); record['cleanup_reconciliation_required'] = True
    finally:
        A.atomic(output/'worker_result.json', {**record, 'utc': A.utc()})
    return 0 if record['state'].startswith('PASS_') else 2


def owner(args):
    A, U = modules()
    need(args.source_sha256 == sha(__file__), 'Explicit reviewed cleanup source pin required')
    output = Path(args.output); plain_c(output)
    need(output.parent == WORK and re.fullmatch('stage5_unc03_cleanup_[A-Za-z0-9_]+', output.name)
         and not output.exists(), 'Preserve prior receipts; use fresh direct C cleanup spool')
    controls(); original = original_request(U); output.mkdir()
    api = A.Win(); current = api.identity(api.current(), os.getpid()); lock = A.WorkflowLock(api)
    stop = A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
    record = {'schema': 'STAGE05_UNC03_EXACT_CLEANUP_OWNER_V1', 'state': 'FAILED',
        'source_sha256': args.source_sha256, 'source_pins': PINS, 'prior_control_pins': RECEIPTS,
        'original_request_sha256': REQUEST_SHA, 'actual_windows_owner': current,
        'WSL_launches': 0, 'probe_success_claimed': False, 'scientific_adoption_authorized': False}
    try:
        with lock:
            need(not stop.exists(), 'Unproven closure STOP vetoes cleanup')
            record['workflow_lock'] = lock.identity; resources(api, output)
            authority_sha = authority(A)
            request = {'schema': 'STAGE05_UNC03_EXACT_CLEANUP_REQUEST_V1', 'source_sha256': args.source_sha256,
                'source_pins': PINS, 'prior_control_pins': RECEIPTS, 'original_request_sha256': REQUEST_SHA,
                'workflow_lock': lock.identity, 'actual_windows_owner': current,
                'authority_sha256': authority_sha, 'target_directory': str(fixed_directory(original))}
            path = output/'cleanup_request.json'; A.atomic(path, request)
            try:
                record['windows_worker'] = U.windows_job(api, [sys.executable, '-B', str(Path(__file__).resolve()),
                    '--run', '--worker', '--cleanup-request', str(path), '--cleanup-request-sha256', sha(path),
                    '--source-sha256', args.source_sha256], current, output/'windows_cleanup_worker')
            except A.OwnedClosureFailure:
                if not stop.exists():
                    A.atomic(stop, {'schema': 'STAGE05_UNC03_CLEANUP_CLOSURE_UNPROVEN_V1', 'state': 'BLOCK_NEW_STAGE5',
                        'evidence': str(output), 'utc': A.utc(), 'automatic_resume': False})
                raise
            result = output/'worker_result.json'; need(result.stat().st_size <= 65536, 'Bounded cleanup result required')
            final = json.loads(result.read_bytes())
            need(final['state'] == 'PASS_EXACT_FAILED03_SENTINEL_BACKUP_AND_TWO_OBJECT_CLEANUP_ONLY'
                 and final['exact_owned_cleanup'] is True and final['source_sha256'] == args.source_sha256
                 and final['cleanup_request_sha256'] == sha(path) and final['original_request_sha256'] == REQUEST_SHA
                 and final['probe_success_claimed'] is False, 'Actual cleanup worker receipt differs')
            need(authority(A) == authority_sha and sha(__file__) == args.source_sha256 and not stop.exists(),
                 'Final cleanup authority/source/STOP differs')
            controls(); original_request(U)
            record['worker_result_sha256'] = sha(result)
            record['state'] = 'CLEANUP_COMPLETE_PENDING_ORIGINAL_UNLOCK'
        need(lock.released and lock.stream.closed, 'Original cleanup unlock/stream closure unproven')
        A.atomic(output/'lock_released.json', {'state': 'EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK',
            'released': True, 'stream_closed': True, 'workflow_lock': lock.identity})
        record['state'] = 'PASS_EXACT_FAILED03_CLEANUP_CLOSED_AND_ORIGINAL_UNLOCKED'
    except BaseException as error:
        record['state'] = 'FAILED'; record['error'] = error_record(error)
        record['cleanup_reconciliation_required'] = True
        if getattr(lock, 'identity', None) is not None and not (lock.released and lock.stream.closed) and not stop.exists():
            A.atomic(stop, {'schema': 'STAGE05_UNC03_CLEANUP_UNLOCK_UNPROVEN_V1', 'state': 'BLOCK_NEW_STAGE5',
                'evidence': str(output), 'utc': A.utc(), 'automatic_resume': False})
    finally:
        record.update(original_lock_released=lock.released, unknown_closure_STOP_present=stop.exists(), utc=A.utc())
        A.atomic(output/'result.json', record)
    print(json.dumps({'state': record['state'], 'result': str(output/'result.json')}))
    return 0 if record['state'].startswith('PASS_') and lock.released else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--worker', action='store_true')
    parser.add_argument('--source-sha256'); parser.add_argument('--output')
    parser.add_argument('--cleanup-request'); parser.add_argument('--cleanup-request-sha256')
    args = parser.parse_args()
    if not args.run:
        need(not args.worker, 'Actual cleanup worker requires explicit --run')
        print(json.dumps({'state': 'PREPARED_EXACT_FAILED03_CLEANUP_NOT_RUN', 'WSL_launches': 0,
              'UNC_effects': 0, 'probe_success_claimed': False})); return 0
    need(args.source_sha256, 'Explicit reviewed cleanup source required')
    if args.worker:
        need(args.cleanup_request and args.cleanup_request_sha256, 'Explicit exact cleanup worker request required')
        return worker(args)
    need(args.output, 'Explicit fresh C cleanup output required')
    return owner(args)




def resources(api, output):
    value = api.resources([WORK, output])
    need(value['physical_available_bytes'] >= RESERVE and value['commit_headroom_bytes'] >= RESERVE
         and all(free >= 10737418240 for free in value['disk_available_bytes'].values()),
         'Current bounded diagnostic physical/commit/disk reserve insufficient')
    return value


if __name__ == '__main__':
    raise SystemExit(main())
