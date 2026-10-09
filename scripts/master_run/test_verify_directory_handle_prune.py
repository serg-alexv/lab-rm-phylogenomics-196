"""Pure synthetic accounting/default tests; no native/source payload queries."""
from pathlib import Path
import ast
import contextlib
import copy
import importlib.util
import io
import json
import sys
import unittest

SOURCE = Path(__file__).with_name('verify_directory_handle_prune.py')
spec = importlib.util.spec_from_file_location('independent_directory_postcheck', SOURCE)
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)


def fixture(parent=False):
    base = V.OLD / 'data/SYNTHETIC_NEVER_CREATED'
    row = {'path': str(base / 'child' if parent else base), 'volume_serial': '123',
           'file_id_128': '11' * 16, 'creation_filetime': '1', 'attributes': 16,
           'last_write_filetime': '1', 'change_filetime': '1', 'observed_children': []}
    rows = [row]
    if parent:
        rows.append({**row, 'path': str(base), 'file_id_128': '22' * 16,
                     'observed_children': [{'path': row['path'], 'kind': 'DIRECTORY'}]})
    owners = [{'pid': pid, 'creation_filetime': birth, 'exited': False} for pid, birth in V.OWNERS]
    begin = {'event': 'BEGIN', 'state': 'ROOT_AUTHORIZED_EXACT_DIRECTORY_HANDLES_ONLY',
             'source_sha256': V.SOURCE_SHA, 'plan_sha256': V.PINS[V.PLAN_NAME],
             'fresh_remote_proof_sha256': V.PINS[V.REMOTE_NAME], 'authorization_sha256': 'a' * 64,
             'intended_directories': len(rows), 'deadline_seconds': 900,
             'workflow_lock': 'UNTOUCHED_NOT_OPENED', 'files_deleted': 0, 'recursive_deletes': 0,
             'protected_before': [], 'owners_before': owners}
    events = [begin]
    for item in rows:
        actual = copy.deepcopy(item)
        if item['observed_children']:
            actual['last_write_filetime'] = actual['change_filetime'] = '2'
        events += [
            {'event': 'BEFORE_DISPOSITION', 'path': item['path'], 'expected': copy.deepcopy(item), 'actual': actual,
             'directory_only': True, 'disposition_class': 4, 'delete_on_close_flag': False,
             'prior_planned_children_removed': [child['path'] for child in item['observed_children']],
             'parent_time_change_allowed': bool(item['observed_children'])},
            {'event': 'DISPOSITION_MARKED_ON_EXACT_DIRECTORY_HANDLE', 'path': item['path'], 'file_id_128': item['file_id_128']},
            {'event': 'AFTER_REMOVED', 'path': item['path'], 'file_id_128': item['file_id_128'],
             'creation_filetime': item['creation_filetime'], 'files_deleted': 0, 'recursive_deletes': 0},
        ]
    events.append({'event': 'COMPLETE', 'state': 'PASS_EXACT5542_EMPTY_DIRECTORY_HANDLES_REMOVED',
                   'removed_directories': len(rows), 'protected_after': [], 'fragment_unchanged': True,
                   'files_deleted': 0, 'recursive_deletes': 0, 'g_writes': 0, 'wsl_starts': 0,
                   'native_jobs_started': 0, 'workflow_lock': 'UNTOUCHED_NOT_OPENED', 'owners_after': owners})
    return rows, events


def failure(count):
    return {'event': 'FAILED_PARTIAL_STOP', 'removed_directories': count, 'files_deleted': 0,
            'recursive_deletes': 0, 'adoption_or_resume_authorized': False, 'kind': 'SYNTHETIC', 'message': 'fixture'}


class JournalTests(unittest.TestCase):
    def check(self, rows, events):
        return V.analyze_journal(iter(events), rows, [], 'a' * 64)

    def test_complete_exact_pairs(self):
        rows, events = fixture()
        result = self.check(rows, events)
        self.assertTrue(result['complete_journal'])
        self.assertEqual(result['documented_removed'], [rows[0]['path']])

    def test_failure_before_begin_is_not_complete(self):
        rows, _ = fixture()
        result = self.check(rows, [failure(0)])
        self.assertFalse(result['complete_journal'])
        self.assertEqual(result['documented_removed'], [])

    def test_failure_after_before_keeps_pending(self):
        rows, events = fixture()
        result = self.check(rows, events[:2] + [failure(0)])
        self.assertEqual(result['pending']['stage'], 'BEFORE_ONLY')
        self.assertFalse(result['complete_journal'])

    def test_failure_after_mark_keeps_pending(self):
        rows, events = fixture()
        result = self.check(rows, events[:3] + [failure(0)])
        self.assertEqual(result['pending']['stage'], 'MARKED_NO_AFTER')

    def test_failure_after_last_after_stays_partial(self):
        rows, events = fixture()
        result = self.check(rows, events[:-1] + [failure(1)])
        self.assertEqual(len(result['documented_removed']), 1)
        self.assertFalse(result['complete_journal'])

    def test_missing_terminal_rejected(self):
        rows, events = fixture()
        with self.assertRaises(ValueError):
            self.check(rows, events[:-1])

    def test_duplicate_trailing_terminal_rejected(self):
        rows, events = fixture()
        with self.assertRaises(ValueError):
            self.check(rows, events + [events[-1]])

    def test_after_birth_replacement_rejected(self):
        rows, events = fixture()
        events[3]['creation_filetime'] = '9'
        with self.assertRaises(ValueError):
            self.check(rows, events)

    def test_mark_identity_replacement_rejected(self):
        rows, events = fixture()
        events[2]['file_id_128'] = '99' * 16
        with self.assertRaises(ValueError):
            self.check(rows, events)

    def test_wrong_order_rejected(self):
        rows, events = fixture(parent=True)
        events[1]['path'] = rows[1]['path']
        with self.assertRaises(ValueError):
            self.check(rows, events)

    def test_parent_actual_time_change_allowed_after_child(self):
        rows, events = fixture(parent=True)
        result = self.check(rows, events)
        self.assertEqual(len(result['documented_removed']), 2)

    def test_leaf_time_change_rejected(self):
        rows, events = fixture()
        events[1]['actual']['change_filetime'] = '2'
        events[1]['parent_time_change_allowed'] = True
        with self.assertRaises(ValueError):
            self.check(rows, events)

    def test_complete_count_overclaim_rejected(self):
        rows, events = fixture()
        events[-1]['removed_directories'] = 5542
        with self.assertRaises(ValueError):
            self.check(rows, events)

    def test_wrong_owner_birth_rejected(self):
        rows, events = fixture()
        events[-1]['owners_after'] = copy.deepcopy(events[-1]['owners_after'])
        events[-1]['owners_after'][0]['creation_filetime'] += 1
        with self.assertRaises(ValueError):
            self.check(rows, events)

    def test_protection_replacement_rejected(self):
        rows, events = fixture()
        events[-1]['protected_after'] = [{'path': 'fake', 'sha256': '0' * 64}]
        with self.assertRaises(ValueError):
            self.check(rows, events)

    def test_other_root_authority_hash_rejected(self):
        rows, events = fixture()
        events[0]['authorization_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.check(rows, events)

    def test_default_noop_never_instantiates_windows(self):
        before, old_args = V.WindowsReads, sys.argv
        try:
            V.WindowsReads = lambda: self.fail('Native reader instantiated by default')
            sys.argv = ['verifier']
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(V.main(), 0)
            self.assertEqual(json.loads(output.getvalue())['state'], 'PREPARED_NO_PRODUCTION_POST_VERIFY')
        finally:
            V.WindowsReads, sys.argv = before, old_args

    def test_no_producer_import_or_delete_lock_launch_apis(self):
        tree = ast.parse(SOURCE.read_text())
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        names = [alias.name for node in imports for alias in node.names]
        self.assertFalse(set(names).intersection({'importlib', 'subprocess', 'shutil'}))
        blocked = {'SetFileInformationByHandle', 'LockFileEx', 'UnlockFileEx', 'CreateProcessW',
                   'TerminateProcess', 'TerminateJobObject', 'unlink', 'rmdir'}
        self.assertFalse({node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}.intersection(blocked))


if __name__ == '__main__':
    unittest.main()
