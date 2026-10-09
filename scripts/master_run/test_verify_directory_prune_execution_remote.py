"""Focused pure readback tests: no network, native APIs, producer or old-C/G reads."""
from pathlib import Path
import argparse
import contextlib
import copy
import importlib.util
import io
import json
import sys
import unittest

spec = importlib.util.spec_from_file_location('directory_execution_reader', Path(__file__).with_name('verify_directory_prune_execution_remote.py'))
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)


class Tests(unittest.TestCase):
    def test_default_no_resource_network_archive_or_cleanup(self):
        prior, resource, verify = sys.argv, V.B.ResourceReader, V.verify
        try:
            sys.argv = ['reader']
            V.B.ResourceReader = V.verify = lambda *a: self.fail('Default attempted readback')
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(V.main(), 0)
            self.assertEqual(json.loads(out.getvalue())['state'], 'PREPARED_NO_READBACK_NO_NETWORK_NO_DELETE')
        finally:
            sys.argv, V.B.ResourceReader, V.verify = prior, resource, verify

    def test_exact_frozen_originals_and_producer_not_loaded(self):
        self.assertEqual(len(V.ORIGINAL_PINS), 50)
        self.assertEqual(V.ORIGINAL_PINS[V.JOURNAL], '5ff92323b29af9a6620a251825ea6531e95bbf14ef2ff6c3d36279beb891f4a5')
        self.assertEqual(V.ORIGINAL_PINS[V.POST], '7820c5048722f517c291f7eab74ea7199197c1ed354b90f3bdfe4df5a35889dd')
        self.assertNotIn('build_directory_prune_execution_archive', sys.modules)

    def test_owner_birth_and_recorded_liveness_both_required(self):
        rows=[dict(pid=p,creation_filetime=t,exited=False) for p,t in V.OWNERS]
        V.owner_identity(rows)
        for key,value in [('creation_filetime',0),('exited',True)]:
            changed=copy.deepcopy(rows);changed[0][key]=value
            with self.assertRaises(ValueError):V.owner_identity(changed)

    def test_ordered_journal_full_identity_mark_after_and_no_tail(self):
        owners=[dict(pid=p,creation_filetime=t,exited=False) for p,t in V.OWNERS]
        row=dict(path='SYNTHETIC',volume_serial='1',file_id_128='00'*16,creation_filetime='2',legacy_file_id='3',
                 attributes=16,links=1,final_handle_path='SYNTHETIC',last_write_filetime='4',change_filetime='5',observed_children=[])
        events=[dict(event='BEGIN',state='ROOT_AUTHORIZED_EXACT_DIRECTORY_HANDLES_ONLY',source_sha256=V.ORIGINAL_PINS['prune_old_scientific_directories.py'],
                     plan_sha256=V.ORIGINAL_PINS[V.PLAN],authorization_sha256=V.ORIGINAL_PINS[V.AUTHORITY],fresh_remote_proof_sha256=V.ORIGINAL_PINS[V.REMOTE_PROPOSAL],
                     intended_directories=1,protected_before=[],files_deleted=0,recursive_deletes=0,workflow_lock='UNTOUCHED_NOT_OPENED',deadline_seconds=900,owners_before=owners),
                dict(event='BEFORE_DISPOSITION',path=row['path'],expected=row,actual=row,directory_only=True,disposition_class=4,delete_on_close_flag=False,
                     prior_planned_children_removed=[],parent_time_change_allowed=False),
                dict(event='DISPOSITION_MARKED_ON_EXACT_DIRECTORY_HANDLE',path=row['path'],file_id_128=row['file_id_128']),
                dict(event='AFTER_REMOVED',path=row['path'],file_id_128=row['file_id_128'],creation_filetime='2',files_deleted=0,recursive_deletes=0),
                dict(event='COMPLETE',state='PASS_EXACT5542_EMPTY_DIRECTORY_HANDLES_REMOVED',removed_directories=1,protected_after=[],fragment_unchanged=True,
                     workflow_lock='UNTOUCHED_NOT_OPENED',files_deleted=0,recursive_deletes=0,g_writes=0,wsl_starts=0,native_jobs_started=0,owners_after=owners)]
        V.check_journal(events,[row],[])
        for index,key,value in [(1,'directory_only',False),(2,'file_id_128','11'*16),(3,'creation_filetime','9'),(4,'removed_directories',0)]:
            changed=copy.deepcopy(events);changed[index][key]=value
            with self.assertRaises(ValueError):V.check_journal(changed,[row],[])
        with self.assertRaises(ValueError):V.check_journal(events+[events[-1]],[row],[])

    def test_journal_lines_reject_oversized_or_unterminated_records(self):
        for payload in (b'{}',b'x'*(1024*1024+1)+b'\n'):
            with self.assertRaises(ValueError):list(V.journal_rows(io.BytesIO(payload)))

    def test_journal_requires_exact_record_total(self):
        with self.assertRaises(ValueError):list(V.journal_rows(io.BytesIO(b'{}\n')))

    def test_postcheck_rejects_pending_or_false_complete(self):
        for value in ({'state':'FAILED'}, {'state':'PASS_EXACT5542_REMOVED_AND_PROTECTED_IDENTITIES_UNCHANGED','complete_prune_verified':False}):
            with self.assertRaises((ValueError,KeyError)):
                V.check_post(value,[],[],{})

    def test_expected_zip_rejects_unsafe_aliases(self):
        for names in (['../x'],['A/x','a/x'],['file','file/child'],['x','x']):
            with self.assertRaises(ValueError):V.A.safe_names(names)


if __name__=='__main__':unittest.main()
