"""C-only exact saved-receipt review; no UNC/native/lock/effect calls."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import stat

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ACTUAL = WORK/'stage5_unc03_cleanup_actual01'
SOURCE = 'stage5_unc03_exact_sentinel_cleanup_v2.py'
SOURCE_SHA = '0984781820c8dd2b85a909b182902990e5c335c6e19187733dadbe3039ef77d4'
REQUEST_SHA = '7f28e209707483d1a50e25c7d35e5804f2b9ebb8ecf9bcc110714849228ce27d'
PAYLOAD_SHA = '4a90f5d4c9fa4130234bfc121f1e1dd47cde726546840a3085d9e4b5875a0ff5'
DEPENDENCIES = {
    'atomic_iqtree_windows.py': '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
    'stage5_unc_bind_probe.py': '0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d',
}
PRIOR = {
    'stage5_unc03_failed_scope_independent_review01.json': 'a3beba2bddf24c460c61dfe395caa680a600ffdc7314f06d3219bc8c457561cd',
    'stage5_unc03_diagnostic_actual01_independent_review.json': '320711555b317475cbe3242c20b28075ab08de2d67b832a00b906ac0dc25802f',
    'stage5_unc03_diagnostic_actual01/worker_result.json': 'c6b6dc469aa6ab725e36ca09c7c87ddaa8cd84ba7069c9b7fa48fc5ea264cae8',
    'stage5_unc03_diagnostic_actual01/result.json': 'c4e7f98bf174a3ddefbfc6ed9d3c7c0c910e907f6f775f2db12e3d500a3ec2a0',
    'stage5_unc_bind_actual_postiq_03/lock_released.json': 'f5c3222f1c568cff2a9852fcb89f0dd34caf6c55d83b12ca7f628fb658615373',
}
LOCK = {
    'path': r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock',
    'volume_serial': 2430728143, 'file_index': 844424932784519,
    'creation_filetime': 134359335921635133, 'locked_byte': 0,
}
TARGET = r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1\.unc_visibility_8ae35884653047348cfa688d4bf00b36'
LEAF = {'mode': 33206, 'regular': True, 'directory': False, 'uid': 0,
        'gid': 0, 'nlink': 1, 'device': 0, 'inode': 33554461, 'bytes': 116,
        'mtime_ns': 1791601426761082800, 'file_attributes': 128,
        'reparse_point': False, 'reparse_tag': 0}
DIRECTORY = {'mode': 16895, 'regular': False, 'directory': True, 'uid': 0,
             'gid': 0, 'nlink': 2, 'device': 0, 'inode': 33554454, 'bytes': 0,
             'mtime_ns': 1791601426758035500, 'file_attributes': 16,
             'reparse_point': False, 'reparse_tag': 0}


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    need(Path(__file__).resolve().parent == WORK, 'Exact C reviewer source required')
    captured = {}
    checks = []

    def raw(path, limit=65536, pin=None):
        path = Path(path)
        need(path.is_absolute() and WORK in path.parents and path.resolve() == path,
             'Only exact C-work saved files may be read')
        for node in (path, *path.parents):
            info = node.lstat()
            need(not node.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
                 'C receipt aliases rejected')
        info = path.stat()
        need(stat.S_ISREG(info.st_mode) and info.st_size <= limit, 'Bounded regular saved file required')
        value = path.read_bytes()
        need(len(value) == info.st_size and (pin is None or digest(value) == pin),
             'Saved bytes/expected pin differ')
        captured[path] = value
        return value

    def load(path, pin=None):
        return json.loads(raw(path, pin=pin))

    def typed_equal(value, expected):
        return (isinstance(value, dict) and set(value) == set(expected)
                and all(type(value[k]) is type(v) and value[k] == v for k, v in expected.items()))

    for name, pin in {SOURCE: SOURCE_SHA, **DEPENDENCIES}.items():
        raw(WORK/name, 2*1024**2, pin)
    for name, pin in PRIOR.items():
        load(WORK/name, pin)
    source_peer = load(WORK/'stage5_unc03_exact_cleanup_v2_source_independent_review01.json',
                       '4fa88de92f22fb44f75342b06ae0df9e01238015fec246aa65629c8addfe3a8d')
    need(source_peer['state'].startswith('PASS'), 'Reviewed source packet not accepted')
    checks.append('Frozen cleanup098478 source, original API/U and prior failed/diagnostic scope pins match.')

    expected_files = {'backup_metadata.json', 'cleanup_request.json', 'linux.bin.backup',
                      'lock_released.json', 'result.json', 'worker_progress.json', 'worker_result.json',
                      'windows_cleanup_worker/launch.json', 'windows_cleanup_worker/root_exit.json',
                      'windows_cleanup_worker/progress.json', 'windows_cleanup_worker/result.json'}
    need({p.relative_to(ACTUAL).as_posix() for p in ACTUAL.rglob('*') if p.is_file()} == expected_files,
         'Unexpected or missing actual receipt member')
    need({p.relative_to(ACTUAL).as_posix() for p in ACTUAL.rglob('*') if p.is_dir()} == {'windows_cleanup_worker'},
         'Unexpected actual receipt directory')
    data = {name: load(ACTUAL/name) for name in expected_files if name.endswith('.json')}
    original = load(WORK/'stage5_unc_bind_actual_postiq_03/request.json', REQUEST_SHA)
    prepared = load(WORK/'stage5_unc_bind_actual_postiq_03/prepared.json')
    payload = raw(ACTUAL/'linux.bin.backup', 116, PAYLOAD_SHA)
    need(len(payload) == 116 and payload == bytes.fromhex(original['linux_payload_hex']),
         'Raw durable backup differs from original known public request bytes')
    need(original['nonce'] == '8ae35884653047348cfa688d4bf00b36'
         and original['sentinel_name'] == '.unc_visibility_' + original['nonce'], 'Failed nonce differs')
    request = data['cleanup_request.json']; owner = data['result.json']; worker = data['worker_result.json']
    backup = data['backup_metadata.json']; unlock = data['lock_released.json']
    need(request['schema'] == 'STAGE05_UNC03_EXACT_CLEANUP_REQUEST_V1'
         and owner['schema'] == 'STAGE05_UNC03_EXACT_CLEANUP_OWNER_V1'
         and worker['schema'] == 'STAGE05_UNC03_EXACT_CLEANUP_WORKER_V1', 'Exact cleanup schemas differ')
    for row in (request, owner):
        need(row['source_sha256'] == SOURCE_SHA and row['source_pins'] == DEPENDENCIES
             and row['prior_control_pins'] == PRIOR and row['original_request_sha256'] == REQUEST_SHA
             and typed_equal(row['workflow_lock'], LOCK), 'Request/owner source/control/lock join differs')
    need(request['actual_windows_owner'] == owner['actual_windows_owner']
         and request['target_directory'] == TARGET and re.fullmatch('[a-f0-9]{64}', request['authority_sha256']),
         'Exact owner/target/current-authority pin differs')
    for row in (owner, worker, data['worker_progress.json']):
        need(type(row['WSL_launches']) is int and row['WSL_launches'] == 0
             and row['probe_success_claimed'] is False and row['scientific_adoption_authorized'] is False,
             'Cleanup scope expanded or probe/science success claimed')
    need(worker['source_sha256'] == SOURCE_SHA and worker['original_request_sha256'] == REQUEST_SHA
         and worker['cleanup_request_sha256'] == digest(captured[ACTUAL/'cleanup_request.json'])
         and owner['worker_result_sha256'] == digest(captured[ACTUAL/'worker_result.json']),
         'Actual request/worker/result raw SHA join differs')
    checks.append('Exact known failed03 nonce, two targets, source/request SHA chain and zero WSL launches agree.')

    receipt = worker['backup']
    need(receipt == data['worker_progress.json']['backup']
         and receipt['payload_path'] == str(ACTUAL/'linux.bin.backup')
         and receipt['metadata_path'] == str(ACTUAL/'backup_metadata.json')
         and receipt['payload_sha256'] == PAYLOAD_SHA
         and receipt['metadata_sha256'] == digest(captured[ACTUAL/'backup_metadata.json'])
         and receipt['fsync_and_readback_before_UNC_effects'] is True, 'Durable backup receipt join differs')
    need(backup['schema'] == 'STAGE05_UNC03_EXACT_SENTINEL_BACKUP_V1'
         and backup['source_sha256'] == SOURCE_SHA and backup['original_request_sha256'] == REQUEST_SHA
         and type(backup['payload_bytes']) is int and backup['payload_bytes'] == 116
         and backup['payload_sha256'] == PAYLOAD_SHA and backup['prior_control_pins'] == PRIOR
         and typed_equal(backup['Windows_projected_leaf_metadata'], LEAF)
         and typed_equal(backup['Windows_projected_directory_metadata'], DIRECTORY)
         and backup['restoration_requires_original_prepared_Linux_metadata'] is True
         and backup['failed_probe_state_unchanged'] is True
         and backup['scientific_adoption_authorized'] is False, 'Exact backup metadata differs')
    need(typed_equal(backup['original_tiny_read_receipt'],
                     {'device': 0, 'inode': 33554461, 'bytes': 116, 'sha256': PAYLOAD_SHA,
                      'mtime_ns': LEAF['mtime_ns']}), 'Original tiny_read saved receipt differs')
    need(prepared['request_sha256'] == REQUEST_SHA and prepared['nonce'] == original['nonce']
         and prepared['directory_inode'] == DIRECTORY['inode']
         and prepared['linux_file']['inode'] == LEAF['inode']
         and prepared['linux_file']['bytes'] == 116 and prepared['linux_file']['sha256'] == PAYLOAD_SHA
         and prepared['linux_file']['mtime_ns'] == 1791601426761082784,
         'Original Linux prepared evidence differs')
    need(LEAF['mtime_ns'] - prepared['linux_file']['mtime_ns'] == 16, 'Known Windows projection precision differs')
    need(worker['state'] == 'PASS_EXACT_FAILED03_SENTINEL_BACKUP_AND_TWO_OBJECT_CLEANUP_ONLY'
         and worker['exact_owned_cleanup'] is True and worker['leaf_unlink_returned'] is True
         and worker['empty_directory_rmdir_returned'] is True and worker['targets'] == [TARGET+'\\linux.bin', TARGET],
         'Exact two-effect final cleanup evidence differs')
    progress = data['worker_progress.json']
    need(progress['phase'] == 'EXACT_EMPTY_DIRECTORY_RMDIR_RETURNED'
         and progress['leaf_unlink_returned'] is True and progress['empty_directory_rmdir_returned'] is True
         and progress['intent'] == worker['intent'] and worker['intent']['effect'] == 'rmdir'
         and worker['intent']['target'] == TARGET, 'Final durable progress/intent join differs')
    expected_directory = dict(DIRECTORY)
    expected_directory['mtime_ns'] = worker['intent']['expected_identity']['mtime_ns']
    need(type(expected_directory['mtime_ns']) is int
         and expected_directory['mtime_ns'] >= DIRECTORY['mtime_ns']
         and typed_equal(worker['intent']['expected_identity'], expected_directory),
         'Only directory mtime may change after exact leaf unlink')
    checks.append('Raw116B backup SHA/payload, fsync/readback receipt, Windows object identities and original Linux prepared metadata agree; Windows mtime is projected +16ns.')
    checks.append('Exact leaf unlink and empty directory rmdir returned with final source-bound absence checks; no recursive cleanup or probe adoption.')

    job = data['windows_cleanup_worker/result.json']
    launch = data['windows_cleanup_worker/launch.json']; root_exit = data['windows_cleanup_worker/root_exit.json']
    job_progress = data['windows_cleanup_worker/progress.json']
    expected_argv = [owner['actual_windows_owner']['executable'], '-B', str(WORK/SOURCE), '--run', '--worker',
                     '--cleanup-request', str(ACTUAL/'cleanup_request.json'), '--cleanup-request-sha256',
                     digest(captured[ACTUAL/'cleanup_request.json']), '--source-sha256', SOURCE_SHA]
    need(job == owner['windows_worker'] and job['schema'] == 'STAGE05_OWNED_WINDOWS_IO_JOB_V2'
         and job['state'] == 'PASS_EXACT_RETAINED_ROOT_EXIT0_AND_EMPTY_NAMED_JOB'
         and job['owned_closure_proven'] is True and job['created'] is True and job['assigned'] is True,
         'Actual retained worker/Job PASS join differs')
    for row in (job, launch, root_exit, job_progress):
        need(row['argv'] == expected_argv and row['owner'] == owner['actual_windows_owner']
             and row['source_sha256'] == DEPENDENCIES['stage5_unc_bind_probe.py']
             and row['api_sha256'] == DEPENDENCIES['atomic_iqtree_windows.py']
             and row['job_name'] == job['job_name'] and row['birth'] == job['birth']
             and not any(k in row for k in ('original_error', 'closure_error', 'handle_close_errors', 'result_write_error')),
             'Retained worker common provenance or handle finalizer differs')
    need(re.fullmatch(r'Local\\LAB_RM_STAGE5_IO_[a-f0-9]{32}', job['job_name']), 'Owned named Job differs')
    birth = job['birth']; final = job['exit']; actual_owner = owner['actual_windows_owner']
    for row in (birth, final, actual_owner):
        need(all(type(row[k]) is int for k in ('pid', 'creation_filetime', 'exit_filetime', 'session_id'))
             and row['pid'] > 0 and row['creation_filetime'] > 0, 'Exact retained Windows birth types differ')
    need(birth['pid'] == final['pid'] == 15504 and birth['creation_filetime'] == final['creation_filetime']
         and birth['creation_filetime'] == 134360786449537574
         and birth['executable'] == final['executable'] == actual_owner['executable']
         and birth['session_id'] == final['session_id'] == actual_owner['session_id'] == 1
         and actual_owner['pid'] == 27356 and actual_owner['creation_filetime'] == 134360786448021902
         and actual_owner['creation_filetime'] < birth['creation_filetime'] < final['exit_filetime']
         and final['exit_filetime'] - final['creation_filetime'] < 20*10000000
         and birth['exited'] is False and final['exited'] is True
         and type(final['exit_code']) is int and final['exit_code'] == 0
         and root_exit['exit'] == final and job_progress['exit'] == final,
         'Exact retained root birth/terminal20s receipt differs')
    closure = job['owned_job']
    need(type(closure['job_active_processes']) is int and closure['job_active_processes'] == 0
         and closure['job_pids'] == [] and job['drain_samples'] == job_progress['drain_samples']
         and 1 <= len(job['drain_samples']) <= 256
         and type(job['drain_samples'][-1]['root_wait']) is int and job['drain_samples'][-1]['root_wait'] == 0
         and job['drain_samples'][-1]['job'] == closure, 'Positive retained root wait and empty named Job differ')
    need(owner['state'] == 'PASS_EXACT_FAILED03_CLEANUP_CLOSED_AND_ORIGINAL_UNLOCKED'
         and owner['original_lock_released'] is True and owner['unknown_closure_STOP_present'] is False
         and unlock['state'] == 'EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK'
         and unlock['released'] is True and unlock['stream_closed'] is True
         and typed_equal(unlock['workflow_lock'], LOCK), 'Checked original unlock/stream receipt differs')
    checks.append('Worker PID15504/birth134360786449537574 retained exit0 within20s, positive wait0 and exact named Job empty; no closure/handle/result finalizer errors.')
    checks.append('Original immutable WorkflowLock identity, explicit OS-byte unlock and stream-closed receipt join owner PASS; saved final STOP flag false.')

    for path, value in captured.items():
        need(path.read_bytes() == value, 'Saved C evidence changed during review')
    report = {
        'schema': 'STAGE05_UNC03_EXACT_CLEANUP_ACTUAL_PEER_V1',
        'state': 'PASS_ACTUAL_EXACT_UNC03_CLEANUP_BACKUP_RETAINED_WORKER_JOB_AND_UNLOCK',
        'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer_source_sha256': digest(Path(__file__).read_bytes()),
        'checks': checks,
        'saved_input_files': [{'path': str(path), 'bytes': len(value), 'sha256': digest(value)}
                              for path, value in sorted(captured.items(), key=lambda x: str(x[0]))],
        'exact_deleted_targets': [TARGET+'\\linux.bin', TARGET],
        'backup': {'local_path': str(ACTUAL/'linux.bin.backup'), 'public_name': 'linux_sentinel_backup.bin',
                   'bytes': 116, 'sha256': PAYLOAD_SHA,
                   'metadata_sha256': digest(captured[ACTUAL/'backup_metadata.json']),
                   'raw_payload_equals_original_public_failed_request': True,
                   'generic_text_extras_must_not_encode_this_binary': True},
        'owned_windows_worker_closure_proven': True, 'owned_job_empty': True,
        'original_lock_explicitly_released': True, 'exact_two_object_cleanup_source_bound_receipts': True,
        'WSL_launches_by_cleanup': 0, 'probe_success_claimed': False, 'scientific_adoption_authorized': False,
        'reviewer_effects': 'NONE_C_ONLY_SAVED_RECEIPTS',
        'limits': ['No live UNC absence, native handle, lock or STOP query was performed by this reviewer.',
                   'Owner identity is its prelaunch snapshot; this peer proves its explicit unlock and the owned worker terminal/Job, not an independent outer-owner process exit.',
                   'Intermediate progress/root_exit state FAILED is the pinned helper checkpoint placeholder before final success and Job drain.',
                   'Windows metadata is projected; original Linux prepared timestamp and receipt remain preserved for restoration context.',
                   'Deletion is the reviewed immediate-check path operation under the original owner, not an atomic compare-and-delete against unrelated writers.'],
        'actual_science_inventory_capture_raw_VM_split_restore_eviction': 'NOT_RUN',
    }
    output = WORK/'stage5_unc03_cleanup_actual01_independent_review.json'
    with output.open('xb') as stream:
        stream.write((json.dumps(report, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'state': report['state'], 'report': str(output),
                      'sha256': digest(output.read_bytes()), 'saved_inputs': len(captured)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
