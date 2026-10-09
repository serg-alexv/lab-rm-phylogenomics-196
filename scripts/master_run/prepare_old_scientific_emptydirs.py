"""Prepare only causal old-C empty directories; no deletion or payload reads.

One-level no-follow enumeration, retained non-delete-sharing directory handles,
full NTFS file ID and FILETIME metadata, exact seven roots, explicit postorder.
The resulting proposal never authorizes execution or follows unknown subtrees.
"""
from pathlib import Path, PureWindowsPath
from ctypes import wintypes as W
import argparse
import ctypes
import datetime
import hashlib
import json
import os
import stat
import sys

sys.dont_write_bytecode = True
WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
OLD = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
SCOPES = ('data', '.work/review2', '.work/stage02_validated', '.work/source_locus_inputs_v1',
          '.work/stage03_markers_v1', '.work/stage04a_windows_alignments_v1', '.work/stage04_phylogeny_v2')
ROOTS = tuple(OLD.joinpath(*scope.split('/')) for scope in SCOPES)
KEEP = OLD / '.work/review2/stage05_raw_review/installed_rejected_serializer.txt'
PROTECTED = {KEEP, *KEEP.parents}
PROOFS = (
    ('master_batch03_postverify_20261009T200023Z_f95312bd/receipt.json',
     '84cb29ebcc04b444ea90ca0e10d5f7e6832d09f14f8f8285f1241b4cf3e71868',
     'PASS_EXACT47429_REMOVED_838_ORIGINALS_AND12_PROTECTED_UNCHANGED',
     'master_batch03_leaf_purge_20261009_receipt.jsonl', 47429, 6565902818),
    ('master_history02_postverify_20261009T201921Z_f90337c5/receipt.json',
     'a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082',
     'PASS_EXACT837_REMOVED_EXCLUDED1025B_AND12_PROTECTED_UNCHANGED',
     'master_history02_leaf_purge_20261009_receipt.jsonl', 837, 983926424),
)


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def timestamp_filetime(value):
    stamp = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    epoch = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)
    delta = stamp - epoch
    return (delta.days * 86400 + delta.seconds) * 10_000_000 + delta.microseconds * 10


def scope_of(path):
    for root in ROOTS:
        if root in path.parents:
            return root
    raise ValueError('Removed leaf outside exact old C scopes')


def causal_parents(path):
    root = scope_of(path)
    pure = PureWindowsPath(str(path))
    require(pure.is_absolute() and '..' not in pure.parts and str(pure) == str(path)
            and not {'.git', '.tools', '.private_run', '.codex'}.intersection(p.casefold() for p in pure.parts)
            and path != KEEP, 'Unsafe/protected removed leaf')
    result = []
    parent = path.parent
    while True:
        result.append(parent)
        if parent == root:
            break
        parent = parent.parent
    return result


def derive():
    derived = {}
    proofs = []
    for name, pin, state, journal_name, count, size in PROOFS:
        proof = WORK / name
        require(sha(proof) == pin, 'Independent post-purge proof differs')
        receipt = json.loads(proof.read_text(encoding='utf-8'))
        require(receipt.get('state') == state and receipt.get('removed_files') == count
                and receipt.get('g_writes') == 0, 'Post-purge proof status/scope differs')
        journal = WORK / journal_name
        initial = journal.stat()
        require(stat.S_ISREG(initial.st_mode) and initial.st_nlink == 1
                and not initial.st_file_attributes & 0x400 and initial.st_size < 64 * 1024**2,
                'Journal is linked/unbounded/nonregular')
        digest = hashlib.sha256()
        removed = total = 0
        tail = None
        seen = set()
        with journal.open('rb') as stream:
            for index, line in enumerate(stream):
                digest.update(line)
                row = json.loads(line)
                if index == 0:
                    require(row.get('event') == 'BEGIN', 'Missing causal purge BEGIN')
                    began = timestamp_filetime(row['utc'])
                if row.get('event') == 'REMOVED':
                    path = Path(row['path'])
                    require(path not in seen, 'Duplicate removed leaf')
                    seen.add(path)
                    removed += 1
                    total += row['bytes']
                    for parent in causal_parents(path):
                        derived[parent] = min(derived.get(parent, began), began)
                tail = row
        final = journal.stat()
        require((initial.st_dev, initial.st_ino, initial.st_size, initial.st_mtime_ns)
                == (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns)
                and digest.hexdigest() == receipt['journal_sha256'], 'Causal journal changed')
        require(tail == receipt['journal_terminal'] and tail.get('event') == 'COMPLETE'
                and removed == count and total == size and tail['recursive_deletes'] == 0,
                'Exact causal leaf completion differs')
        proofs.append({'path': str(proof), 'sha256': pin, 'journal': str(journal),
                       'journal_sha256': digest.hexdigest(), 'removed_files': removed, 'removed_bytes': total})
    return derived, proofs


class BasicInfo(ctypes.Structure):
    _fields_ = [(n, ctypes.c_longlong) for n in ('CreationTime', 'LastAccessTime', 'LastWriteTime', 'ChangeTime')] + [('FileAttributes', W.DWORD)]


class FileIdInfo(ctypes.Structure):
    _fields_ = [('VolumeSerialNumber', ctypes.c_ulonglong), ('FileId', ctypes.c_ubyte * 16)]


class LegacyInfo(ctypes.Structure):
    _fields_ = [('attrs', W.DWORD), ('created', W.FILETIME), ('accessed', W.FILETIME),
                ('written', W.FILETIME), ('volume', W.DWORD), ('size_high', W.DWORD),
                ('size_low', W.DWORD), ('links', W.DWORD), ('index_high', W.DWORD), ('index_low', W.DWORD)]


class Directories:
    def __init__(self):
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        self.k.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
        self.k.CreateFileW.restype = W.HANDLE
        self.k.CloseHandle.argtypes = [W.HANDLE]
        self.k.GetFileInformationByHandleEx.argtypes = [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD]
        self.k.GetFileInformationByHandle.argtypes = [W.HANDLE, ctypes.POINTER(LegacyInfo)]
        self.k.GetFinalPathNameByHandleW.argtypes = [W.HANDLE, W.LPWSTR, W.DWORD, W.DWORD]
        self.k.GetVolumeInformationW.argtypes = [W.LPCWSTR, W.LPWSTR, W.DWORD, ctypes.POINTER(W.DWORD), ctypes.POINTER(W.DWORD), ctypes.POINTER(W.DWORD), W.LPWSTR, W.DWORD]
        filesystem = ctypes.create_unicode_buffer(32)
        require(self.k.GetVolumeInformationW('C:\\', None, 0, None, None, None, filesystem, 32)
                and filesystem.value == 'NTFS', 'Actual C NTFS volume required')
        self.ancestors = []

    def observe(self, handle, path):
        basic, file_id, legacy = BasicInfo(), FileIdInfo(), LegacyInfo()
        require(self.k.GetFileInformationByHandleEx(handle, 0, ctypes.byref(basic), ctypes.sizeof(basic))
                and self.k.GetFileInformationByHandleEx(handle, 18, ctypes.byref(file_id), ctypes.sizeof(file_id))
                and self.k.GetFileInformationByHandle(handle, ctypes.byref(legacy)), 'Directory metadata read failed')
        require(basic.FileAttributes & 0x10 and not basic.FileAttributes & 0x400, 'Plain non-reparse directory required')
        buffer = ctypes.create_unicode_buffer(32768)
        length = self.k.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        require(0 < length < len(buffer), 'Final directory path missing/too long')
        final = buffer.value
        require(final.startswith('\\\\?\\') and final[4:].casefold() == str(path).casefold(), 'Directory alias/outside literal path')
        return {'path': str(path), 'volume_serial': str(file_id.VolumeSerialNumber),
                'file_id_128': bytes(file_id.FileId).hex(),
                'legacy_file_id': str((legacy.index_high << 32) | legacy.index_low),
                'creation_filetime': str(basic.CreationTime), 'last_write_filetime': str(basic.LastWriteTime),
                'change_filetime': str(basic.ChangeTime), 'last_access_filetime': str(basic.LastAccessTime),
                'attributes': basic.FileAttributes, 'links': legacy.links,
                'final_handle_path': final, 'handle_share': 'READ_WRITE_DENY_DELETE_RENAME_DURING_OBSERVATION'}

    def open(self, path, expected_inode=None):
        handle = self.k.CreateFileW(str(path), 0x80, 3, None, 3, 0x02000000 | 0x00200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            row = self.observe(handle, path)
            require(expected_inode is None or int(row['legacy_file_id']) == expected_inode, 'Enumerated directory identity changed before open')
            return handle, row
        except BaseException:
            self.k.CloseHandle(handle)
            raise

    def hold_ancestors(self):
        for path in reversed(OLD.parents):
            handle, row = self.open(path)
            self.ancestors.append((handle, row))
        handle, row = self.open(OLD)
        self.ancestors.append((handle, row))
        work = OLD / '.work'
        handle, row = self.open(work)
        self.ancestors.append((handle, row))

    def close(self):
        for handle, _ in reversed(self.ancestors):
            self.k.CloseHandle(handle)
        self.ancestors = []


def stable(a, b):
    keys = ('volume_serial', 'file_id_128', 'creation_filetime', 'last_write_filetime', 'change_filetime', 'attributes')
    return all(a[k] == b[k] for k in keys)


def eligible(children, candidates, protected=False):
    return not protected and all(row['kind'] == 'DIRECTORY' and row['path'] in candidates for row in children)


def scan(derived):
    api = Directories()
    rows, held, absent = {}, [], []
    handles = []
    try:
        api.hold_ancestors()
        keep = KEEP.lstat()
        require(stat.S_ISREG(keep.st_mode) and not keep.st_file_attributes & 0x400 and keep.st_size == 1025,
                'Expected wholly preserved MacSy fragment missing/changed kind/size')
        for root in ROOTS:
            try:
                handle, initial = api.open(root)
            except FileNotFoundError:
                absent.append(str(root)); continue
            stack = [('ENTER', root, handle, initial, None)]
            handles.append(handle)
            while stack:
                phase, path, handle, initial, children = stack.pop()
                if phase == 'ENTER':
                    children = []
                    descend = []
                    with os.scandir(path) as entries:
                        for entry in entries:
                            child = path / entry.name
                            # Windows DirEntry caches FindFirstFile metadata and reports
                            # st_ino=0. Fresh no-follow path metadata supplies a real NTFS
                            # ID, then the retained handle must independently match it.
                            info = child.lstat()
                            reparse = bool(info.st_file_attributes & 0x400) or stat.S_ISLNK(info.st_mode)
                            kind = 'REPARSE_HELD' if reparse else 'DIRECTORY' if stat.S_ISDIR(info.st_mode) else 'FILE_OR_OTHER_HELD'
                            row = {'path': str(child), 'name': entry.name, 'kind': kind,
                                   'causal_deleted_file_ancestor': child in derived, 'bytes': info.st_size,
                                   'file_id': str(info.st_ino), 'attributes': info.st_file_attributes}
                            if kind == 'DIRECTORY' and child not in derived:
                                row['kind'] = 'UNKNOWN_DIRECTORY_HELD_NO_TRAVERSAL'
                            elif kind == 'DIRECTORY':
                                descend.append((child, info.st_ino))
                            children.append(row)
                    require(len(children) <= 100000 and len({r['name'].casefold() for r in children}) == len(children), 'Unbounded/aliased directory entries')
                    stack.append(('EXIT', path, handle, initial, children))
                    for child, inode in reversed(descend):
                        try:
                            child_handle, child_initial = api.open(child, inode)
                        except OSError as error:
                            held.append({'path': str(child), 'reason': 'DIRECTORY_OPEN_FAILED_PRESERVED', 'error': str(error)})
                            continue
                        handles.append(child_handle)
                        stack.append(('ENTER', child, child_handle, child_initial, None))
                else:
                    final = api.observe(handle, path)
                    candidate_children = set(map(str, rows))
                    reason = None
                    if path in PROTECTED:
                        reason = 'MACSY_FRAGMENT_ANCESTOR_ALWAYS_PRESERVED'
                    elif path not in derived:
                        reason = 'NO_CAUSAL_REMOVED_LEAF_ANCESTOR'
                    elif int(initial['creation_filetime']) > derived[path]:
                        reason = 'DIRECTORY_CREATED_AFTER_CAUSAL_PURGE_BEGIN'
                    elif not stable(initial, final):
                        reason = 'DIRECTORY_METADATA_CHANGED_DURING_OBSERVATION'
                    elif not eligible(children, candidate_children):
                        reason = 'NONEMPTY_HAS_FILE_REPARSE_UNKNOWN_OR_HELD_CHILD'
                    if reason:
                        held.append({'path': str(path), 'reason': reason, 'metadata': final, 'children': children})
                    else:
                        rows[path] = {**final, 'group_root': str(scope_of(path / '__literal_leaf_for_scope__')),
                                      'depth': len(path.parts), 'empty_at_observation': not children,
                                      'causal_purge_begin_filetime': str(derived[path]), 'observed_children': children,
                                      'future_rule': 'EXACT_SAME_NTFS_DIRECTORY_ID_AND_FULL_BIRTH;ACTUALLY_EMPTY;NO_FILES_OR_RECURSION'}
                    api.k.CloseHandle(handle); handles.remove(handle)
        for handle, expected in api.ancestors:
            require(stable(expected, api.observe(handle, Path(expected['path']))), 'Protected ancestor metadata changed during scan')
        return sorted(rows.values(), key=lambda row: (-row['depth'], row['path'].casefold())), held, absent, [row for _, row in api.ancestors]
    finally:
        for handle in reversed(handles):
            api.k.CloseHandle(handle)
        api.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scan', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    require(os.name == 'nt' and Path(__file__).resolve().parent == WORK and os.environ.get('COMPUTERNAME', '').casefold() == 'wd',
            'WD exact C work deployment required')
    if not args.scan:
        print(json.dumps({'state': 'PREPARED_NO_SCAN_NO_DELETE', 'roots': list(map(str, ROOTS))})); return
    require(args.output and args.output.absolute().parent == WORK and not args.output.exists(), 'New direct C-work plan file required')
    code_sha = sha(Path(__file__))
    derived, proofs = derive()
    rows, held, absent, ancestors = scan(derived)
    require(sha(Path(__file__)) == code_sha, 'Scanner source drift')
    value = {'schema': 'MASTER_OLD_SCIENTIFIC_EMPTY_DIRECTORY_PROPOSAL_V1',
             'state': 'PREPARED_NO_DELETE_PENDING_ROOT_POSTPROOF_PUBLICATION_AND_EXECUTOR_REVIEW',
             'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scanner_sha256': code_sha,
             'scope_roots': list(map(str, ROOTS)), 'causal_proofs': proofs, 'derived_ancestor_count': len(derived),
             'directories': rows, 'directory_count': len(rows), 'empty_now_count': sum(r['empty_at_observation'] for r in rows),
             'planned_children_only_count': sum(not r['empty_at_observation'] for r in rows),
             'held': held, 'absent_scope_roots': absent, 'protected_ancestors': ancestors,
             'always_preserved_fragment': str(KEEP), 'all_remaining_files_and_unknown_subtrees': 'PRESERVED_NOT_FOLLOWED',
             'execution_authorized': False, 'files_to_delete': 0, 'recursive_deletes': 0,
             'g_writes': 0, 'wsl_starts': 0, 'scientific_jobs': 0,
             'limits': ['Directory metadata is a snapshot; new entries/identity drift must veto actual removal.',
                        'Prior file-removal proofs do not authorize directory deletion.',
                        'A future published literal no-recursion executor needs separate root authority and exact identity/type/emptiness guards.',
                        'A plain check-then-Remove-Item path has a leaf replacement race; do not certify no-file-loss without a directory-only or exact-handle deletion primitive.']}
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'plan': str(args.output), 'sha256': sha(args.output), 'directories': len(rows),
                      'empty_now': value['empty_now_count'], 'parents_only': value['planned_children_only_count'],
                      'held': len(held), 'derived': len(derived)}))


if __name__ == '__main__':
    main()
