"""Actual Win32 directory-only fixtures in one new fixed C-work namespace.

Default is no operation. No old-C/G/WSL access, process ownership APIs, path
deletion, recursive cleanup, or production pruner execution is called here.
All deliberately retained files, replacement directories and reparse points stay.
"""
from pathlib import Path
import argparse
import datetime
import importlib.util
import json
import os
import stat
import time
import uuid

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
SOURCE = WORK / 'prune_old_scientific_directories.py'


def run(expected):
    started = time.monotonic()
    assert os.name == 'nt' and Path(__file__).resolve().parent == WORK
    import hashlib
    def sha(path):
        with Path(path).open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    assert sha(SOURCE) == expected
    fixture_source_sha = sha(__file__)
    spec = importlib.util.spec_from_file_location('directory_pruner_fixture_target', SOURCE)
    P = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(P)
    assert P.WORK == WORK and sha(SOURCE) == expected
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    P.FIXTURES.mkdir(exist_ok=True)
    assert P.FIXTURES.lstat().st_file_attributes & 0x400 == 0
    base = P.FIXTURES / stamp
    base.mkdir()
    output = WORK / ('directory_handle_fixture_' + stamp + '.json')
    journal_path = WORK / ('directory_handle_fixture_' + stamp + '.jsonl')
    J = P.Journal(journal_path)
    api = P.DirectoryHandles()
    results, removed = [], set()
    J.append('FIXTURE_BEGIN', namespace=str(base), pruner_sha256=expected,
             fixture_source_sha256=fixture_source_sha, old_c_access=False,
             g_access=False, production_execute_called=False)

    def directory(name):
        path = base / name
        path.mkdir()
        return path

    def record(path, children=()):
        row = api.snapshot(path)
        row['observed_children'] = [{'path': str(child), 'kind': 'DIRECTORY'} for child in children]
        return row

    def absent(path):
        try:
            path.lstat()
        except FileNotFoundError:
            return True
        return False

    def rejected(name, call, verify):
        try:
            call()
        except (ValueError, OSError) as error:
            assert verify(), name + ': original fixture changed'
            result = {'name': name, 'status': 'PASS_REFUSED_AND_PRESERVED',
                      'error_kind': type(error).__name__, 'message': str(error),
                      'winerror': getattr(error, 'winerror', None)}
            results.append(result)
            J.append('FIXTURE_RESULT', **result)
        else:
            raise AssertionError(name + ': unexpectedly accepted')

    def delete(row):
        P.remove_one(api, row, {row['path']: row}, removed, J, fixture=True,
                     check=lambda: P.require(time.monotonic() - started < 60, 'Fixture deadline'))

    try:
        # 1. The actual empty original directory disappears only after the
        # exact checked DELETE handle is disposition-marked and closed.
        empty = directory('01_empty')
        empty_row = record(empty)
        delete(empty_row)
        assert absent(empty)
        results.append({'name': 'empty_handle_deletes', 'status': 'PASS',
                        'file_id_128': empty_row['file_id_128']})

        # 2. A nonempty directory at its original snapshot is refused by our
        # current-empty gate, preserving exact bytes.
        nonempty = directory('02_nonempty')
        retained = nonempty / 'retained.txt'
        retained.write_bytes(b'SYNTHETIC: preserve this unknown file.\n')
        retained_sha = sha(retained)
        nonempty_row = record(nonempty)
        rejected('nonempty_refused', lambda: delete(nonempty_row),
                 lambda: sha(retained) == retained_sha and nonempty.is_dir())

        # 3. A regular file cannot enter the native directory disposition path.
        regular = base / '03_regular.txt'
        regular.write_bytes(b'SYNTHETIC regular file must remain.\n')
        regular_sha = sha(regular)
        rejected('regular_file_refused', lambda: delete({'path': str(regular)}),
                 lambda: sha(regular) == regular_sha and stat.S_ISREG(regular.lstat().st_mode))

        # 4. A real newly created directory symlink is opened as the reparse
        # point itself and refused; its referenced sentinel remains unchanged.
        referent = directory('04_referent_preserved')
        sentinel = referent / 'sentinel.txt'
        sentinel.write_bytes(b'SYNTHETIC reparse referent preserved.\n')
        sentinel_sha = sha(sentinel)
        link = base / '04_reparse_link_preserved'
        os.symlink(referent, link, target_is_directory=True)
        assert link.lstat().st_file_attributes & 0x400
        rejected('reparse_held', lambda: delete({'path': str(link)}),
                 lambda: bool(link.lstat().st_file_attributes & 0x400) and sha(sentinel) == sentinel_sha)

        # 5. Same-name replacement after the snapshot has a different full ID.
        swapped = directory('05_identity_swap')
        original_row = record(swapped)
        saved_original = base / '05_original_preserved'
        swapped.rename(saved_original)  # Fixture-only creation/rename, no deletion.
        swapped.mkdir()
        replacement_row = record(swapped)
        assert not P.same_identity(original_row, replacement_row)
        rejected('identity_swap_refused', lambda: delete(original_row),
                 lambda: P.same_identity(api.snapshot(swapped), replacement_row)
                 and P.same_identity(api.snapshot(saved_original), original_row))

        # 6. Planned postorder child removal is the sole permitted reason for
        # parent timestamps to differ. Birth/full ID and actual emptiness hold.
        parent = directory('06_planned_parent')
        child = parent / 'planned_child'
        child.mkdir()
        child_row, parent_row = record(child), record(parent, (child,))
        delete(child_row)
        parent_after_child = api.snapshot(parent)
        assert any(parent_after_child[key] != parent_row[key]
                   for key in ('last_write_filetime', 'change_filetime'))
        delete(parent_row)
        assert absent(child) and absent(parent)
        results.append({'name': 'planned_postorder_parent_allowed', 'status': 'PASS',
                        'parent_birth_and_full_id_unchanged': P.same_identity(parent_after_child, parent_row),
                        'parent_timestamp_change_actually_observed': True})

        # 7. A new child after the snapshot is preserved, never recursively
        # adopted, regardless of whether timestamp or emptiness veto fires.
        changed = directory('07_unknown_child')
        changed_row = record(changed)
        unknown = changed / 'new_unknown.txt'
        unknown.write_bytes(b'SYNTHETIC appeared after the snapshot.\n')
        unknown_sha = sha(unknown)
        rejected('unknown_child_protected', lambda: delete(changed_row),
                 lambda: sha(unknown) == unknown_sha and changed.is_dir())

        # 8. Independently exercise the native kernel disposition API on a
        # checked nonempty directory; no path removal API is used.
        handle, current = api.open_delete(nonempty)
        try:
            rejected('kernel_nonempty_disposition_refused',
                     lambda: api.set_disposition(handle, nonempty, current),
                     lambda: sha(retained) == retained_sha and nonempty.is_dir())
            assert results[-1]['winerror'] == 145, 'Expected actual ERROR_DIR_NOT_EMPTY'
        finally:
            api.close(handle)

        # 9. A retained parent identity handle denies rename/delete while a
        # descendant could be checked; the attempted rename leaves both intact.
        ancestor = directory('09_retained_ancestor')
        nested = ancestor / 'nested_preserved'
        nested.mkdir()
        handle, ancestor_row = api.open_ancestor(ancestor)
        try:
            rejected('retained_ancestor_rename_refused',
                     lambda: ancestor.rename(base / '09_renamed_must_not_exist'),
                     lambda: P.same_identity(api.snapshot(ancestor), ancestor_row) and nested.is_dir())
            assert results[-1]['winerror'] == 32, 'Expected actual ERROR_SHARING_VIOLATION'
        finally:
            api.close(handle)

        assert len(results) == 9 and len(removed) == 3
        assert sha(SOURCE) == expected and sha(__file__) == fixture_source_sha
        receipt = {'schema': 'MASTER_DIRECTORY_HANDLE_FIXTURE_V1',
                   'state': 'PASS_NINE_ACTUAL_WINDOWS_DIRECTORY_HANDLE_FIXTURES',
                   'namespace': str(base), 'pruner_sha256': expected,
                   'fixture_source_sha256': fixture_source_sha,
                   'removed_synthetic_empty_directories': sorted(removed),
                   'remaining_fixture_payloads_preserved': True, 'results': results,
                   'elapsed_seconds': time.monotonic() - started,
                   'old_c_directories_removed': 0, 'old_c_payload_reads': 0,
                   'g_access': False, 'wsl_started': False, 'workflow_lock_accessed': False,
                   'production_execute_called': False, 'files_deleted': 0,
                   'path_removal_calls': 0, 'recursive_cleanup_calls': 0}
        J.append('FIXTURE_COMPLETE', **receipt)
        J.close()
        receipt['journal'] = str(journal_path)
        receipt['journal_sha256'] = sha(journal_path)
        output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps({'receipt': str(output), 'sha256': sha(output), 'state': receipt['state']}))
        return 0
    except BaseException as error:
        receipt = {'schema': 'MASTER_DIRECTORY_HANDLE_FIXTURE_V1', 'state': 'FAILED_FIXTURE_PRESERVED',
                   'namespace': str(base), 'pruner_sha256': expected,
                   'fixture_source_sha256': fixture_source_sha, 'results': results,
                   'removed_synthetic_empty_directories': sorted(removed),
                   'error_kind': type(error).__name__, 'message': str(error),
                   'old_c_directories_removed': 0, 'files_deleted': 0,
                   'production_execute_called': False}
        J.append('FIXTURE_FAILED', **receipt)
        J.close()
        receipt['journal'] = str(journal_path)
        receipt['journal_sha256'] = sha(journal_path)
        output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-fixture', action='store_true')
    parser.add_argument('--pruner-sha256')
    args = parser.parse_args()
    if not args.run_fixture:
        print(json.dumps({'state': 'PREPARED_NO_FIXTURE_EXECUTION', 'production_prune': False}))
        return 0
    return run(args.pruner_sha256)


if __name__ == '__main__':
    raise SystemExit(main())
