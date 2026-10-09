"""Independent read-only production directory-prune post-verifier.

Default no-op. Never imports a producer, removes a path, tests/acquires a byte
lock, starts WSL/native inference, or writes G. Actual --verify is root-owned.
"""
from pathlib import Path
from ctypes import wintypes as W
import argparse
import ctypes
import datetime
import hashlib
import json
import os
import stat
import threading
import time
import uuid

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
OLD = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
G = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
SCOPES = ('data', '.work/review2', '.work/stage02_validated', '.work/source_locus_inputs_v1',
          '.work/stage03_markers_v1', '.work/stage04a_windows_alignments_v1', '.work/stage04_phylogeny_v2')
ROOTS = tuple(OLD.joinpath(*name.split('/')) for name in SCOPES)
KEEP = OLD / '.work/review2/stage05_raw_review/installed_rejected_serializer.txt'
LOCK = OLD / '.work/workflow.lock'
LOCK_BASELINE = (2430728143, 844424932784519, 134359335921635133)
SOURCE_SHA = '9b64d17bb2612ce35051b87d77863709d875c1f910865fd6a4db2f6ddd265381'
PLAN_NAME = 'master_old_scientific_emptydirs_proposed_02.json'
REMOTE_NAME = 'old_scientific_emptydirs01_readback_20261009T205057Z_9c38bcce/receipt.json'
PROTECTION_NAME = 'master_history02_postverify_20261009T201921Z_f90337c5/receipt.json'
PINS = {
    PLAN_NAME: 'be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5',
    REMOTE_NAME: 'e71b02889d5443017ef5ab8be206b1fc4e5f9f81c3de14c602eeaeef70c68063',
    PROTECTION_NAME: 'a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082',
    'directory_handle_fixture_20261009T211154Z_9cf77be3.json': '348ee7030d49d14524290f0ec27302e67d67d216f342c97a1fb44e83526cc0ac',
    'directory_handle_fixture_20261009T211154Z_9cf77be3.jsonl': '73a0978d42e5f106d60888187611eb0218314b9aeb016d5b47e4f3cfb48b0a23',
    'prune_old_scientific_directories_attempt01.py': '2f608bd1f11b3aac9223c7c751b9a9d8f5cb5c02568861bd6cfeadfff9304604',
    'test_directory_handle_prune_fixture_attempt01.py': '72e3a86e28f08e845cb37a9ef62f6ea056d220902e7074b4fdc63dbcb8e4d0c7',
    'directory_handle_pruner_corrected_independent_review.json': 'c0bc38628a140885211a397af9e23bbe10f9f432b2c682c13d44c03cd1d1b20b',
}
OWNERS = ((4768, 134360369876207076), (27048, 134360369803845506))
DIRTY_SIX = tuple(G / name for name in ('reports/stage00/commands.jsonl', 'reports/stage02/retrieval_progress.json',
    'reports/stage02/retrieval_progress_resume.json', 'reports/stage04/resource_wait_v5/observations.jsonl',
    'reports/stage04/resource_wait_v5_v2/observations.jsonl', 'status/continuation_execution_receipt.json'))
ID_KEYS = ('volume_serial', 'file_id_128', 'creation_filetime', 'attributes')


def require(value, message):
    if not value:
        raise ValueError(message)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def same_identity(left, right):
    return all(left[key] == right[key] for key in ID_KEYS)


def validate_plan(plan):
    rows = plan['directories']
    paths = [row['path'] for row in rows]
    require(plan['directory_count'] == len(rows) == len(set(paths)) == 5542
            and plan['scope_roots'] == list(map(str, ROOTS)) and len(plan['held']) == 6
            and plan['always_preserved_fragment'] == str(KEEP), 'Exact published scope/counts differ')
    protected = {KEEP, *KEEP.parents}
    held = {row['path'] for row in plan['held']}
    seen = set()
    for row in rows:
        path = Path(row['path'])
        require(path.is_absolute() and str(path) == str(path.absolute()) and '..' not in path.parts
                and (path in ROOTS or any(root in path.parents for root in ROOTS))
                and path not in protected and row['path'] not in held, 'Protected/unsafe planned path')
        require(row['attributes'] & 0x10 and not row['attributes'] & 0x400, 'Planned type is not plain directory')
        for child in row['observed_children']:
            require(child['kind'] == 'DIRECTORY' and child['path'] in seen
                    and Path(child['path']).parent == path, 'Planned child missing from exact postorder')
        seen.add(row['path'])
    return rows


def owner_rows(rows):
    require(len(rows) == 2, 'Two exact owner records required')
    require({(row['pid'], int(row['creation_filetime'])) for row in rows} == set(OWNERS)
            and all(row.get('exited') is False for row in rows), 'Journal owner identity/liveness differs')


def analyze_journal(events, rows, protected, authority_sha):
    """Pure ordered accounting; verify() separately fixes actual production5542."""
    events = iter(events)
    first = next(events, None)
    require(first is not None, 'Empty journal')
    expected_protected = [{'path': row['path'], 'bytes': row['bytes'], 'sha256': row['sha256'], 'unchanged': True}
                          for row in protected]
    removed, pending = [], None
    terminal = first
    if first.get('event') == 'BEGIN':
        require(first.get('state') == 'ROOT_AUTHORIZED_EXACT_DIRECTORY_HANDLES_ONLY'
                and first.get('source_sha256') == SOURCE_SHA and first.get('plan_sha256') == PINS[PLAN_NAME]
                and first.get('fresh_remote_proof_sha256') == PINS[REMOTE_NAME]
                and first.get('authorization_sha256') == authority_sha and first.get('intended_directories') == len(rows)
                and first.get('deadline_seconds') == 900 and first.get('workflow_lock') == 'UNTOUCHED_NOT_OPENED'
                and first.get('files_deleted') == first.get('recursive_deletes') == 0
                and first.get('protected_before') == expected_protected, 'BEGIN source/recovery/protection binding differs')
        owner_rows(first['owners_before'])
        terminal = None
        for row in rows:
            before = next(events, None)
            require(before is not None, 'No terminal journal record; partial timeout needs separate reconciliation')
            if before.get('event') == 'FAILED_PARTIAL_STOP':
                terminal = before
                break
            require(before.get('event') == 'BEFORE_DISPOSITION' and before.get('path') == row['path']
                    and before.get('expected') == row and same_identity(before['actual'], row)
                    and before['actual']['path'] == row['path'] and before.get('directory_only') is True
                    and before.get('disposition_class') == 4 and before.get('delete_on_close_flag') is False,
                    'Exact ordered BEFORE identity/type binding differs')
            children = [child['path'] for child in row['observed_children']]
            changed = any(before['actual'][key] != row[key] for key in ('last_write_filetime', 'change_filetime'))
            require(before.get('prior_planned_children_removed') == children and all(path in removed for path in children)
                    and before.get('parent_time_change_allowed') is changed and (not changed or children),
                    'Parent mutation/postorder allowance differs')
            pending = {'path': row['path'], 'stage': 'BEFORE_ONLY'}
            mark = next(events, None)
            require(mark is not None, 'Missing disposition outcome/terminal')
            if mark.get('event') == 'FAILED_PARTIAL_STOP':
                terminal = mark
                break
            require(mark.get('event') == 'DISPOSITION_MARKED_ON_EXACT_DIRECTORY_HANDLE'
                    and mark.get('path') == row['path'] and mark.get('file_id_128') == row['file_id_128'],
                    'Exact disposition mark join differs')
            pending['stage'] = 'MARKED_NO_AFTER'
            after = next(events, None)
            require(after is not None, 'Missing AFTER/terminal')
            if after.get('event') == 'FAILED_PARTIAL_STOP':
                terminal = after
                break
            require(after.get('event') == 'AFTER_REMOVED' and after.get('path') == row['path']
                    and after.get('file_id_128') == row['file_id_128']
                    and after.get('creation_filetime') == row['creation_filetime']
                    and after.get('files_deleted') == after.get('recursive_deletes') == 0, 'Exact AFTER identity join differs')
            removed.append(row['path'])
            pending = None
        if terminal is None:
            terminal = next(events, None)
    require(terminal and terminal.get('event') in ('COMPLETE', 'FAILED_PARTIAL_STOP'), 'No recognized terminal')
    require(next(events, None) is None, 'Trailing/duplicate journal records')
    if terminal['event'] == 'COMPLETE':
        require(len(removed) == len(rows) and pending is None
                and terminal.get('state') == 'PASS_EXACT5542_EMPTY_DIRECTORY_HANDLES_REMOVED'
                and terminal.get('removed_directories') == len(rows) and terminal.get('protected_after') == expected_protected
                and terminal.get('fragment_unchanged') is True and terminal.get('files_deleted') == terminal.get('recursive_deletes') == 0
                and terminal.get('g_writes') == terminal.get('wsl_starts') == terminal.get('native_jobs_started') == 0
                and terminal.get('workflow_lock') == 'UNTOUCHED_NOT_OPENED', 'COMPLETE accounting/protection differs')
        owner_rows(terminal['owners_after'])
    else:
        require(terminal.get('files_deleted') == terminal.get('recursive_deletes') == 0
                and terminal.get('adoption_or_resume_authorized') is False
                and terminal.get('removed_directories') in (len(removed), len(removed) + int(pending is not None)),
                'FAILED_PARTIAL terminal accounting differs')
    return {'terminal': terminal, 'documented_removed': removed, 'pending': pending,
            'complete_journal': terminal['event'] == 'COMPLETE'}


class Basic(ctypes.Structure):
    _fields_ = [(name, ctypes.c_longlong) for name in ('birth', 'access', 'write', 'change')] + [('attributes', W.DWORD)]


class FileID(ctypes.Structure):
    _fields_ = [('volume', ctypes.c_ulonglong), ('identifier', ctypes.c_ubyte * 16)]


class Legacy(ctypes.Structure):
    _fields_ = [('attributes', W.DWORD), ('birth', W.FILETIME), ('access', W.FILETIME), ('write', W.FILETIME),
                ('volume', W.DWORD), ('size_hi', W.DWORD), ('size_lo', W.DWORD), ('links', W.DWORD),
                ('index_hi', W.DWORD), ('index_lo', W.DWORD)]


class WindowsReads:
    """Independent query/read-only Win32 path; no delete/lock/job APIs exist."""
    def __init__(self):
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        self.k.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
        self.k.CreateFileW.restype = W.HANDLE
        self.k.CloseHandle.argtypes = [W.HANDLE]
        self.k.CloseHandle.restype = W.BOOL
        self.k.GetFileInformationByHandleEx.argtypes = [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD]
        self.k.GetFileInformationByHandle.argtypes = [W.HANDLE, ctypes.POINTER(Legacy)]
        self.k.GetFinalPathNameByHandleW.argtypes = [W.HANDLE, W.LPWSTR, W.DWORD, W.DWORD]
        self.k.ReadFile.argtypes = [W.HANDLE, W.LPVOID, W.DWORD, ctypes.POINTER(W.DWORD), W.LPVOID]
        self.k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
        self.k.OpenProcess.restype = W.HANDLE
        self.k.GetProcessTimes.argtypes = [W.HANDLE, *([ctypes.POINTER(W.FILETIME)] * 4)]
        self.k.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
        self.k.WaitForSingleObject.restype = W.DWORD
        self.handles, self.parents, self.owners = [], {}, []
        self.started = time.monotonic()

    def close(self):
        for handle in reversed(self.handles):
            self.k.CloseHandle(handle)
        self.handles = []

    def open(self, path, directory=False, data=False):
        access = (0x80 | 1) if directory else (0x80000000 if data else 0x80)
        share = 1 if data else 3
        handle = self.k.CreateFileW(str(path), access, share, None, 3, 0x00200000 | (0x02000000 if directory else 0), None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        self.handles.append(handle)
        return handle, self.observe(handle, path, directory)

    def observe(self, handle, path, directory):
        basic, ident, legacy = Basic(), FileID(), Legacy()
        require(self.k.GetFileInformationByHandleEx(handle, 0, ctypes.byref(basic), ctypes.sizeof(basic))
                and self.k.GetFileInformationByHandle(handle, ctypes.byref(legacy)), 'Native metadata query failed')
        id128 = bool(self.k.GetFileInformationByHandleEx(handle, 18, ctypes.byref(ident), ctypes.sizeof(ident)))
        require(id128 or (not directory and path.drive.casefold() == G.drive.casefold()),
                'Full128 ID unavailable for required C-directory/control identity')
        require(bool(basic.attributes & 0x10) is directory and not basic.attributes & 0x400
                and (directory or legacy.links == 1), 'Wrong type/reparse/hardlinked regular file')
        buffer = ctypes.create_unicode_buffer(32768)
        length = self.k.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        require(0 < length < len(buffer) and buffer.value.startswith('\\\\?\\')
                and buffer.value[4:].casefold() == str(path).casefold(), 'Native handle literal path/alias differs')
        return {'path': str(path), 'volume_serial': str(ident.volume if id128 else legacy.volume),
                'file_id_128': bytes(ident.identifier).hex() if id128 else None, 'file_id_128_supported': id128,
                'creation_filetime': str(basic.birth), 'attributes': basic.attributes,
                'legacy_volume_serial': legacy.volume, 'legacy_file_id': (legacy.index_hi << 32) | legacy.index_lo,
                'bytes': (legacy.size_hi << 32) | legacy.size_lo,
                'last_write_filetime': str(basic.write), 'change_filetime': str(basic.change)}

    def guard(self):
        require(time.monotonic() - self.started < 900, 'Verifier deadline exceeded')
        return self.owner_check() if self.owners else []

    def owner_open(self):
        for pid, birth in OWNERS:
            handle = self.k.OpenProcess(0x1000 | 0x100000, False, pid)
            require(handle, 'Cannot open exact owner query-only handle')
            self.handles.append(handle)
            self.owners.append((handle, pid, birth))
        return self.owner_check()

    def owner_check(self):
        result = []
        for handle, pid, birth in self.owners:
            times = [W.FILETIME() for _ in range(4)]
            require(self.k.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)), 'Owner birth query failed')
            actual = times[0].dwHighDateTime * 2**32 + times[0].dwLowDateTime
            require(actual == birth and self.k.WaitForSingleObject(handle, 0) == 258, 'Native/controller birth or liveness differs')
            result.append({'pid': pid, 'creation_filetime': str(actual), 'alive': True, 'retained_query_handle': True})
        return result

    def data(self, path, maximum, retain=True):
        handle, before = self.open(path, data=True)
        require(before['bytes'] <= maximum, 'Read-only file budget exceeded')
        digest_value, chunks, count = hashlib.sha256(), [], 0
        buffer, got = ctypes.create_string_buffer(256 * 1024), W.DWORD()
        while True:
            require(self.k.ReadFile(handle, buffer, len(buffer), ctypes.byref(got), None), 'Native read failed')
            if not got.value:
                break
            block = buffer.raw[:got.value]
            count += len(block)
            require(count <= maximum, 'Growing read exceeded bound')
            if retain:
                chunks.append(block)
            digest_value.update(block)
            self.guard()
        after = self.observe(handle, path, False)
        require(before == after and count == before['bytes'], 'Read-only retained file changed')
        return b''.join(chunks), digest_value.hexdigest(), before

    def journal_events(self, path, evidence):
        handle, before = self.open(path, data=True)
        require(before['bytes'] <= 64 * 1024**2, 'Journal byte budget exceeded')
        value, count, total, tail = hashlib.sha256(), 0, 0, None
        buffer, got, pending = ctypes.create_string_buffer(256 * 1024), W.DWORD(), b''
        while True:
            require(self.k.ReadFile(handle, buffer, len(buffer), ctypes.byref(got), None), 'Native journal read failed')
            if not got.value:
                break
            block = buffer.raw[:got.value]
            total += len(block)
            require(total <= 64 * 1024**2, 'Growing journal exceeded budget')
            value.update(block)
            pending += block
            while b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                require(len(line) <= 1024**2, 'Unbounded journal line')
                count += 1
                require(count <= 3 * 5542 + 2, 'Journal record budget exceeded')
                tail = json.loads(line)
                yield tail
            require(len(pending) <= 1024**2, 'Unbounded journal line remainder')
            self.guard()
        require(not pending and before == self.observe(handle, path, False) and total == before['bytes'],
                'Journal missing final newline or changed native identity/size/times')
        evidence.update(sha256=value.hexdigest(), records=count, terminal=tail, identity=before, handle=handle)

    def presence(self, path):
        """A first missing plain component proves qualified absence, not an error."""
        temporary = []
        try:
            for part in [*reversed(path.parents), path]:
                if part in self.parents:
                    handle, expected = self.parents[part]
                    require(same_identity(self.observe(handle, part, True), expected), 'Retained parent identity changed')
                    continue
                try:
                    handle, row = self.open(part, directory=True)
                except OSError as error:
                    if error.winerror in (2, 3):
                        return {'present': False, 'first_missing_component': str(part)}
                    raise
                temporary.append(handle)
            return {'present': True, 'identity': row}
        finally:
            for handle in reversed(temporary):
                self.k.CloseHandle(handle)
                self.handles.remove(handle)


def verify(args, result):
    api = WindowsReads()
    try:
        # Native READ/share-READ-only journal handle rejects any still-open writer.
        journal_check = {}
        for _ in api.journal_events(args.journal, journal_check):
            pass
        require(journal_check['sha256'] == args.journal_sha256
                and journal_check['terminal'].get('event') in ('COMPLETE', 'FAILED_PARTIAL_STOP'),
                'No terminal closed-writer journal; no source payload check/acceptance')
        _, loaded_source_sha, _ = api.data(Path(__file__), 256 * 1024, retain=False)
        require(loaded_source_sha == args.source_sha256, 'Verifier source changed at retained read-only reopen')
        controls = {}
        for name, expected in PINS.items():
            value, actual, _ = api.data(WORK / name, 16 * 1024**2)
            require(actual == expected, 'Pinned independent control differs: ' + name)
            controls[name] = value
        plan = json.loads(controls[PLAN_NAME])
        rows = validate_plan(plan)
        remote = json.loads(controls[REMOTE_NAME])
        require(remote['mode'] == 'FRESH_REMOTE' and remote['state'] == 'PASS_FRESH_REMOTE_METADATA19_MEMBERS_5542_PROPOSED_NO_PRUNE'
                and remote['source_commit'] == '25792aca769466123d7a5a3186e9c86bd97cd0f7'
                and remote['release_tag_and_assets_unchanged_before_after'] is True
                and any(row['member'] == PLAN_NAME and row['sha256'] == PINS[PLAN_NAME] and row['crc_verified'] for row in remote['members']),
                'Independent exact plan fresh remote proof differs')
        protections = json.loads(controls[PROTECTION_NAME])['protected_files']
        require(len(protections) == 12 and {str(path) for path in DIRTY_SIX}.issubset(row['path'] for row in protections),
                'Exact protected12/six dirty G files differ')
        authority, authority_sha, _ = api.data(args.authorization, 64 * 1024)
        require(authority_sha == args.authorization_sha256, 'Actual root authority SHA differs')
        require(json.loads(authority) == {'schema': 'MASTER_DIRECTORY_HANDLE_PRUNE_ROOT_AUTHORITY_V1',
            'execution_authorized': True, 'root_only': True, 'source_sha256': SOURCE_SHA,
            'plan_sha256': PINS[PLAN_NAME], 'fresh_remote_proof_sha256': PINS[REMOTE_NAME],
            'deadline_seconds': 900, 'source_fixture_independent_review_and_publication_complete': True},
            'Actual reviewed production root authority differs')
        journal_join = {}
        accounting = analyze_journal(api.journal_events(args.journal, journal_join), rows, protections, authority_sha)
        require(journal_join['sha256'] == journal_check['sha256'] and journal_join['records'] == journal_check['records']
                and journal_join['identity'] == journal_check['identity'], 'Independent journal join pass differs')
        result.update(journal_sha256=journal_check['sha256'], journal_records=journal_check['records'], journal_identity=journal_check['identity'],
                      journal_terminal=accounting['terminal'], pending_disposition=accounting['pending'])
        result['owners_before'] = api.owner_open()
        for row in [*plan['protected_ancestors'], *(held['metadata'] for held in plan['held'])]:
            path = Path(row['path'])
            handle, actual = api.open(path, directory=True)
            require(same_identity(actual, row), 'Protected ancestor/held-directory full identity differs')
            api.parents[path] = (handle, actual)
        lock_handle, lock_before = api.open(LOCK)
        require((lock_before['legacy_volume_serial'], lock_before['legacy_file_id'], int(lock_before['creation_filetime'])) == LOCK_BASELINE,
                'Original stable workflow.lock legacy volume/file ID/full birth differs')
        removed = set(accounting['documented_removed'])
        states, unproven, retained = [], [], []
        for row in rows:
            api.guard()
            observed = api.presence(Path(row['path']))
            if row['path'] in removed:
                require(not observed['present'], 'Journal AFTER directory currently exists')
                state = 'DOCUMENTED_REMOVED_AND_CURRENTLY_ABSENT'
            elif observed['present']:
                require(same_identity(observed['identity'], row), 'Undeleted planned directory identity replaced')
                state = 'FAILED_RUN_OR_UNATTEMPTED_ORIGINAL_DIRECTORY_RETAINED'
                retained.append(row['path'])
            else:
                state = 'ABSENT_WITHOUT_COMPLETE_AFTER_REQUIRES_RECONCILIATION'
                unproven.append(row['path'])
            states.append({'path': row['path'], 'state': state, 'presence_evidence': observed})
        fragment, fragment_sha, _ = api.data(KEEP, 1025)
        require(len(fragment) == 1025 and fragment_sha == '574547f9584dafce870492810ab02be990fe022939edd5a797292c473625027b',
                'Excluded MacSyFinder fragment changed')
        checked = []
        for row in protections:
            # Bounds <16MiB for every exact scientific/source input; no toolchain image.
            require(row['bytes'] < 16 * 1024**2, 'Unexpected protected payload size')
            _, actual_sha, identity = api.data(Path(row['path']), row['bytes'], retain=False)
            require(identity['bytes'] == row['bytes'] and actual_sha == row['sha256'], 'Protected12/six dirty G actual bytes changed')
            checked.append({'path': row['path'], 'bytes': identity['bytes'], 'sha256': actual_sha,
                            'identity': identity, 'unchanged': True})
        for path, (handle, before) in api.parents.items():
            require(same_identity(api.observe(handle, path, True), before), 'Retained ancestor/held identity changed during verifier')
        lock_after = api.observe(lock_handle, LOCK, False)
        require(same_identity(lock_before, lock_after), 'Retained original workflow.lock identity changed')
        second_lock, current_lock = api.open(LOCK)
        require(same_identity(lock_before, current_lock), 'Current original workflow.lock path replaced')
        require(api.observe(journal_check['handle'], args.journal, False) == journal_check['identity']
                and digest(Path(__file__)) == args.source_sha256, 'Closed journal or retained verifier source changed during verification')
        complete = accounting['complete_journal'] and len(removed) == 5542 and not unproven and not retained
        result.update(state='PASS_EXACT5542_REMOVED_AND_PROTECTED_IDENTITIES_UNCHANGED' if complete else
                      'PARTIAL_FAILED_PRUNE_ACCOUNTED_RECONCILIATION_REQUIRED', all5542_accounted=True,
                      complete_prune_verified=complete, documented_removed_directories=len(removed),
                      retained_planned_directories=len(retained), unproven_absences=unproven, directory_states=states,
                      held_directories_preserved=6, excluded_fragment_sha256=fragment_sha,
                      protected_files=checked, six_dirty_g_files_unchanged=[row for row in checked if Path(row['path']) in DIRTY_SIX],
                      workflow_lock_identity_before=lock_before, workflow_lock_identity_after=lock_after,
                      workflow_lock_metadata_only=True, lock_contents_read=False, lock_acquired=False,
                      owners_after=api.owner_check(), preserved_first_fixture_failure=True,
                      new_execution_authorized=False, physical_disk_reclaimed_bytes='NOT_MEASURED')
        return 0 if complete else 2
    finally:
        api.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--source-sha256')
    parser.add_argument('--journal', type=Path)
    parser.add_argument('--journal-sha256')
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--authorization-sha256')
    args = parser.parse_args()
    if not args.verify:
        print(json.dumps({'state': 'PREPARED_NO_PRODUCTION_POST_VERIFY', 'source_deletions': 0}))
        return 0
    require(os.name == 'nt' and os.environ.get('COMPUTERNAME', '').casefold() == 'wd'
            and Path(__file__).resolve().parent == WORK and digest(Path(__file__)) == args.source_sha256,
            'Exact reviewed WD/current C verifier deployment required')
    for path, expected in ((args.journal, args.journal_sha256), (args.authorization, args.authorization_sha256)):
        require(path and path.parent == WORK and path == path.absolute() and path == path.resolve()
                and isinstance(expected, str) and len(expected) == 64 and all(char in '0123456789abcdef' for char in expected),
                'Exact direct C-work journal/authority path and actual SHA required')
    output = WORK / ('directory_prune_postverify_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8])
    output.mkdir()
    result = {'schema': 'MASTER_DIRECTORY_HANDLE_PRUNE_INDEPENDENT_POST_VERIFY_V1', 'state': 'IN_PROGRESS_READ_ONLY',
              'verifier_sha256': args.source_sha256, 'control_pins': PINS, 'started_utc': utc(),
              'deadline_seconds': 900, 'source_deletions': 0, 'g_writes': 0, 'network_calls': 0,
              'wsl_starts': 0, 'native_scientific_launches': 0, 'producer_imports': 0}
    (output / 'started.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    timer = threading.Timer(900, lambda: os._exit(124))
    timer.daemon = True
    timer.start()
    try:
        return verify(args, result)
    except BaseException as error:
        result.update(state='FAILED_INDEPENDENT_DIRECTORY_POST_VERIFY_NO_NEW_CLEANUP_AUTHORITY',
                      error={'kind': type(error).__name__, 'message': str(error)}, complete_prune_verified=False)
        raise
    finally:
        timer.cancel()
        result['finished_utc'] = utc()
        (output / 'receipt.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps({'state': result['state'], 'receipt': str(output / 'receipt.json')}))


if __name__ == '__main__':
    raise SystemExit(main())
