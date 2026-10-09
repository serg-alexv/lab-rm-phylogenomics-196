"""Exact-directory-handle pruning; default no operation, root execution only.

No path deletion API, recursive operation, file deletion, native-job control or
WorkflowLock access. Production requires a separately published root authority.
"""
from pathlib import Path
from ctypes import wintypes as W
import argparse
import ctypes
import datetime
import hashlib
import importlib.util
import json
import os
import stat
import threading
import time

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
FIXTURES = WORK / 'directory_handle_prune_fixtures'
SCANNER = WORK / 'prepare_old_scientific_emptydirs.py'
SCANNER_SHA = '7287809f47f912eddb21ba9f05d927872ef710d45ac6857837ae6689c320b21f'
PLAN = WORK / 'master_old_scientific_emptydirs_proposed_02.json'
PLAN_SHA = 'be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5'
REMOTE = WORK / 'old_scientific_emptydirs01_readback_20261009T205057Z_9c38bcce/receipt.json'
REMOTE_SHA = 'e71b02889d5443017ef5ab8be206b1fc4e5f9f81c3de14c602eeaeef70c68063'
PROTECTED = WORK / 'master_history02_postverify_20261009T201921Z_f90337c5/receipt.json'
PROTECTED_SHA = 'a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082'
ATOMIC_SHA = '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
FRAGMENT_SHA = '574547f9584dafce870492810ab02be990fe022939edd5a797292c473625027b'
IDENTITY = ('volume_serial', 'file_id_128', 'creation_filetime', 'attributes')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        value = hashlib.sha256()
        for block in iter(lambda: stream.read(256 * 1024), b''):
            value.update(block)
        return value.hexdigest()


def module(name, path, expected):
    require(sha(path) == expected, 'Pinned helper source differs')
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    require(Path(value.__file__).resolve() == path and sha(path) == expected, 'Helper import location/source differs')
    return value


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Journal:
    def __init__(self, path):
        require(path.parent == WORK and not path.exists(), 'Fresh direct C-work journal required')
        self.stream = path.open('x', encoding='utf-8', newline='\n')

    def append(self, event, **fields):
        self.stream.write(json.dumps({'event': event, 'utc': now(), **fields}, sort_keys=True) + '\n')
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


class DirectoryHandles:
    def __init__(self):
        self.source = module('reviewed_directory_metadata', SCANNER, SCANNER_SHA)
        self.read = self.source.Directories()
        self.kernel = self.read.k
        self.kernel.SetFileInformationByHandle.argtypes = [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD]
        self.kernel.SetFileInformationByHandle.restype = W.BOOL

    def open_delete(self, path):
        # DELETE + FILE_READ_ATTRIBUTES + FILE_LIST_DIRECTORY; no delete-on-close.
        # Share READ only prevents target rename/delete and generic-write opens.
        handle = self.kernel.CreateFileW(str(path), 0x10000 | 0x80 | 1, 1, None, 3,
                                         0x02000000 | 0x00200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return handle, self.read.observe(handle, path)
        except BaseException:
            self.close(handle)
            raise

    def close(self, handle):
        if not self.kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())

    def snapshot(self, path):
        handle, record = self.read.open(path)
        try:
            return record
        finally:
            self.close(handle)

    def set_disposition(self, handle, path, expected):
        require(same_identity(self.read.observe(handle, path), expected),
                'Disposition requires the same plain directory identity/birth/type')
        # FILE_DISPOSITION_INFO contains BOOLEAN (one byte), not four-byte BOOL.
        disposition = ctypes.c_ubyte(1)
        if not self.kernel.SetFileInformationByHandle(handle, 4, ctypes.byref(disposition), 1):
            raise ctypes.WinError(ctypes.get_last_error())


def same_identity(actual, expected):
    return all(actual[key] == expected[key] for key in IDENTITY)


def actually_empty(path):
    # Enumeration handle closes before disposition. The kernel independently
    # rejects nonempty directories even if a child appears after this observation.
    with os.scandir(path) as entries:
        require(next(entries, None) is None, 'Nonempty directory; every unknown child is preserved')


def remove_one(api, record, metadata, removed, journal, fixture=False, check=lambda: None):
    path = Path(record['path'])
    if fixture:
        require(FIXTURES in path.parents and path != FIXTURES and path == path.absolute(), 'Fixture outside fixed C-work namespace')
    else:
        require((path in api.source.ROOTS or any(root in path.parents for root in api.source.ROOTS))
                and path not in api.source.PROTECTED and path == path.absolute(), 'Outside exact seven roots or protected fragment ancestor')
    ancestors = []
    handle = None
    try:
        for parent in reversed(path.parents):
            ancestor, observed = api.read.open(parent)
            ancestors.append((ancestor, parent, observed))
            if str(parent) in metadata:
                require(same_identity(observed, metadata[str(parent)]), 'Ancestor NTFS identity/birth/type changed')
        check()
        handle, actual = api.open_delete(path)
        require(same_identity(actual, record), 'Target NTFS identity/birth/type changed')
        children = record.get('observed_children', [])
        require(all(child['kind'] == 'DIRECTORY' and child['path'] in removed for child in children),
                'An observed planned child has not been removed by this run')
        changed = any(actual[key] != record[key] for key in ('last_write_filetime', 'change_filetime'))
        require(not changed or children and all(child['path'] in removed for child in children),
                'Unexpected directory mutation without prior planned-child removals')
        actually_empty(path)
        final = api.read.observe(handle, path)
        require(same_identity(final, record), 'Target identity/birth/type changed before disposition')
        for ancestor, parent, expected in ancestors:
            require(same_identity(api.read.observe(ancestor, parent), expected), 'Retained ancestor changed before disposition')
        check()
        journal.append('BEFORE_DISPOSITION', path=str(path), expected=record, actual=final,
                       parent_time_change_allowed=bool(changed),
                       prior_planned_children_removed=[child['path'] for child in children],
                       directory_only=True, disposition_class=4, delete_on_close_flag=False)
        api.set_disposition(handle, path, record)
        journal.append('DISPOSITION_MARKED_ON_EXACT_DIRECTORY_HANDLE', path=str(path), file_id_128=final['file_id_128'])
        api.close(handle)
        handle = None
        try:
            path.lstat()
        except FileNotFoundError:
            pass
        else:
            raise ValueError('Original marked directory not proven absent; preserve all other paths')
        removed.add(str(path))
        journal.append('AFTER_REMOVED', path=str(path), file_id_128=final['file_id_128'],
                       creation_filetime=final['creation_filetime'], files_deleted=0, recursive_deletes=0)
    finally:
        if handle is not None:
            api.close(handle)
        for ancestor, _, _ in reversed(ancestors):
            api.close(ancestor)


def controls():
    for path, expected in ((PLAN, PLAN_SHA), (REMOTE, REMOTE_SHA), (PROTECTED, PROTECTED_SHA)):
        require(sha(path) == expected, 'Exact published plan/remote proof/protection receipt differs')
    plan = json.loads(PLAN.read_text())
    remote = json.loads(REMOTE.read_text())
    protected = json.loads(PROTECTED.read_text())
    require(remote['state'] == 'PASS_FRESH_REMOTE_METADATA19_MEMBERS_5542_PROPOSED_NO_PRUNE'
            and remote['mode'] == 'FRESH_REMOTE' and remote['source_commit'] == '25792aca769466123d7a5a3186e9c86bd97cd0f7'
            and remote['release_tag_and_assets_unchanged_before_after'] is True
            and remote['proposed_directories'] == plan['directory_count'] == len(plan['directories']) == 5542
            and len(remote['members']) == 19 and len(plan['held']) == 6, 'Fresh remote restoration/proposal counts differ')
    proof = [row for row in remote['members'] if row['member'] == PLAN.name]
    require(len(proof) == 1 and proof[0]['sha256'] == PLAN_SHA and proof[0]['crc_verified'], 'Remote exact plan member proof missing')
    require(len(protected['protected_files']) == 12 and len(protected['owners_after']) == 2, 'Exact protected12/owners2 required')
    return plan, protected


def protected_check(records):
    observed = []
    for row in records:
        path = Path(row['path'])
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and not before.st_file_attributes & 0x400
                and before.st_size == row['bytes'] and before.st_size < 16 * 1024**2, 'Protected source kind/size changed')
        actual = sha(path)
        after = path.lstat()
        fields = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
        require(fields(before) == fields(after) and actual == row['sha256'], 'Protected source identity/SHA changed')
        observed.append({'path': str(path), 'bytes': row['bytes'], 'sha256': actual, 'unchanged': True})
    return observed


def execute(args):
    require(os.name == 'nt' and Path(__file__).resolve().parent == WORK
            and os.environ.get('COMPUTERNAME', '').casefold() == 'wd', 'Exact WD C deployment required')
    require(args.source_sha256 == sha(__file__), 'Explicit reviewed execution-source SHA required')
    authorization_path = Path(args.authorization)
    require(authorization_path.parent == WORK and authorization_path == authorization_path.resolve()
            and sha(authorization_path) == args.authorization_sha256, 'Pinned direct C-work root authority required')
    authority = json.loads(authorization_path.read_text())
    require(authority == {'schema': 'MASTER_DIRECTORY_HANDLE_PRUNE_ROOT_AUTHORITY_V1',
                         'execution_authorized': True, 'root_only': True,
                         'source_sha256': args.source_sha256, 'plan_sha256': PLAN_SHA,
                         'fresh_remote_proof_sha256': REMOTE_SHA, 'deadline_seconds': 900,
                         'source_fixture_independent_review_and_publication_complete': True},
            'Separate exact root review/publication authority absent')
    journal = Journal(Path(args.journal))
    timer = threading.Timer(900, lambda: os._exit(124))
    timer.daemon = True
    timer.start()
    began = time.monotonic()
    owners = []
    api = None
    removed = set()
    try:
        plan, protected = controls()
        atomic = module('reviewed_process_identity_only', WORK / 'atomic_iqtree_windows.py', ATOMIC_SHA)
        process_api = atomic.Win()
        process_api.K.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
        process_api.K.OpenProcess.restype = W.HANDLE
        for expected in protected['owners_after']:
            handle = process_api.K.OpenProcess(0x1000 | 0x100000, False, expected['pid'])
            require(handle, 'Cannot retain protected native/controller query-only handle')
            owners.append((handle, expected, None))
            actual = process_api.identity(handle, expected['pid'])
            require(str(actual['creation_filetime']) == expected['creation_filetime'] and not actual['exited'], 'Protected process exact birth/liveness differs')
            owners[-1] = (handle, expected, actual)

        def check():
            require(time.monotonic() - began < 900 and sha(__file__) == args.source_sha256
                    and sha(SCANNER) == SCANNER_SHA, 'Deadline or execution/helper-source drift')
            for handle, expected, birth in owners:
                actual = process_api.identity(handle, expected['pid'], birth['executable'], birth['session_id'])
                require(not actual['exited'] and str(actual['creation_filetime']) == expected['creation_filetime'], 'Protected process birth/liveness changed; stop pruning')

        api = DirectoryHandles()
        require(plan['scope_roots'] == list(map(str, api.source.ROOTS)), 'Exact seven source roots differ')
        paths = {row['path'] for row in plan['directories']}
        require(len(paths) == 5542 and not paths.intersection(row['path'] for row in plan['held'])
                and not any(Path(path) in api.source.PROTECTED for path in paths), 'Duplicate/held/protected directory adopted')
        metadata = {row['path']: row for row in plan['directories']}
        metadata.update({row['path']: row['metadata'] for row in plan['held']})
        metadata.update({row['path']: row for row in plan['protected_ancestors']})
        require(sha(api.source.KEEP) == FRAGMENT_SHA and api.source.KEEP.lstat().st_size == 1025, 'Preserved fragment changed')
        before = protected_check(protected['protected_files'])
        check()
        journal.append('BEGIN', state='ROOT_AUTHORIZED_EXACT_DIRECTORY_HANDLES_ONLY', source_sha256=args.source_sha256,
                       plan_sha256=PLAN_SHA, fresh_remote_proof_sha256=REMOTE_SHA, authorization_sha256=args.authorization_sha256,
                       intended_directories=5542, protected_before=before, owners_before=[row[2] for row in owners],
                       deadline_seconds=900, workflow_lock='UNTOUCHED_NOT_OPENED', files_deleted=0, recursive_deletes=0)
        for record in plan['directories']:
            remove_one(api, record, metadata, removed, journal, check=check)
        check()
        after = protected_check(protected['protected_files'])
        require(sha(api.source.KEEP) == FRAGMENT_SHA and api.source.KEEP.lstat().st_size == 1025, 'Preserved fragment changed after pruning')
        controls()
        check()
        journal.append('COMPLETE', state='PASS_EXACT5542_EMPTY_DIRECTORY_HANDLES_REMOVED', removed_directories=len(removed),
                       protected_after=after, owners_after=[process_api.identity(handle, expected['pid'], birth['executable'], birth['session_id'])
                                                           for handle, expected, birth in owners],
                       fragment_unchanged=True, files_deleted=0, recursive_deletes=0, workflow_lock='UNTOUCHED_NOT_OPENED',
                       g_writes=0, wsl_starts=0, native_jobs_started=0)
        return 0
    except BaseException as error:
        journal.append('FAILED_PARTIAL_STOP', removed_directories=len(removed), kind=type(error).__name__, message=str(error),
                       adoption_or_resume_authorized=False, files_deleted=0, recursive_deletes=0)
        raise
    finally:
        for handle, _, _ in reversed(owners):
            process_api.close(handle)
        timer.cancel()
        journal.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--source-sha256')
    parser.add_argument('--authorization')
    parser.add_argument('--authorization-sha256')
    parser.add_argument('--journal')
    args = parser.parse_args()
    if not args.run:
        print(json.dumps({'state': 'PREPARED_NO_PRUNE', 'exact_directory_proposal': 5542, 'root_authority_required': True,
                          'files_deleted': 0, 'workflow_lock': 'UNTOUCHED'}))
        return 0
    return execute(args)


if __name__ == '__main__':
    raise SystemExit(main())
