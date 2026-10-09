"""Synthetic readback contracts only; no remote calls, archive builds, or deletion."""
import copy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import verify_master_batch03_execution_remote as v


BEGIN = {'event': 'BEGIN', 'proposal_commit': '2b0edf16fe3224d33155ac67f2a8a0d2177d78a5'}
TOTAL = 6565902818


def pair(index=0):
    # Deliberately synthetic zero-byte later leaves keep the exact terminal budget.
    size = TOTAL if index == 0 else 0
    fields = {'line': index + 1, 'path': f'C:\\synthetic-cold\\leaf{index}',
              'bytes': size, 'sha256': 'a' * 64}
    return [dict(event='VERIFIED_INTENT', **fields),
            dict(event='REMOVED', **fields, deleted=index + 1, deleted_bytes=TOTAL)]


def terminal():
    return {'event': 'COMPLETE', 'state': 'PASS_EXACT_47429_COLD_LEAVES_REMOVED',
            'deleted': 47429, 'deleted_bytes': TOTAL, 'held_files': 219,
            'unmatched_preserved': 619, 'recursive_deletes': 0, 'utc': 'SYNTHETIC'}


def stream(events):
    return (json.dumps(row).encode() + b'\n' for row in events)


def full_events(last=None, after=None):
    yield copy.deepcopy(BEGIN)
    for index in range(47429):
        yield from pair(index)
    yield terminal() if last is None else last
    if after is not None:
        yield after


def controls():
    asset = v.ASSETS[0]
    common = {'postverify_sha256': v.POST_SHA, 'physical_disk_reclaimed_bytes': 'NOT_MEASURED',
              'logical_removed_bytes': TOTAL, 'raw_codex_events_prompts_usage_archived': False,
              'scientific_acceptance': 'NONE_EXECUTION_HISTORY_ONLY'}
    manifest = {'sha256': asset['sha256'], 'bytes': asset['bytes'], 'members': [{} for _ in range(23)],
                'source_binding_sha256': v.CONTROLS['source_bindings.json']}
    build = dict(common, sha256=asset['sha256'], bytes=asset['bytes'], members=23,
                 manifest_sha256=v.CONTROLS['manifest.json'])
    return {'manifest.json': manifest, 'source_bindings.json': common, 'build_receipt.json': build}


class JournalReadbackContracts(unittest.TestCase):
    def test_full_synthetic_ordered_journal(self):
        result = v.journal_check(stream(full_events()))
        self.assertEqual(result['records_including_begin'], 94860)
        self.assertEqual(result['removed_files'], 47429)
        self.assertEqual(result['logical_removed_bytes'], TOTAL)
        self.assertEqual(result['physical_disk_reclaimed_bytes'], 'NOT_MEASURED')

    def test_authority_or_detached_outcome_rejected(self):
        wrong = dict(BEGIN, proposal_commit='0' * 40)
        with self.assertRaisesRegex(ValueError, 'authority'):
            v.journal_check(stream([wrong]))
        with self.assertRaisesRegex(ValueError, 'binding'):
            v.journal_check(stream([BEGIN, pair()[1]]))

    def test_outcome_must_match_exact_intent(self):
        for key, value in [('line', 2), ('path', 'C:\\other'), ('bytes', 1), ('sha256', 'b' * 64)]:
            rows = pair(); rows[1][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'binding'):
                v.journal_check(stream([BEGIN, *rows]))

    def test_duplicate_or_overlapping_intents_rejected(self):
        for rows in [[BEGIN, pair()[0], pair()[0]], [BEGIN, *pair(), pair()[0]]]:
            with self.assertRaisesRegex(ValueError, 'Duplicate or unpaired'):
                v.journal_check(stream(rows))

    def test_cumulative_accounting_rejected(self):
        for key, value in [('deleted', 2), ('deleted_bytes', TOTAL + 1)]:
            rows = pair(); rows[1][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'Cumulative'):
                v.journal_check(stream([BEGIN, *rows]))

    def test_missing_or_partial_terminal_never_passes(self):
        for rows in [[BEGIN], [BEGIN, pair()[0]], [BEGIN, *pair()],
                     [BEGIN, {'event': 'STOP', 'state': 'FAILED_PARTIAL_PRESERVE_REMAINDER'}]]:
            with self.assertRaises(ValueError):
                v.journal_check(stream(rows))

    def test_terminal_scope_is_exact_after_valid_pairs(self):
        for key, value in [('state', 'PASS'), ('deleted', 47428), ('deleted_bytes', TOTAL - 1),
                           ('held_files', 0), ('unmatched_preserved', 618), ('recursive_deletes', 1)]:
            final = terminal(); final[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'Terminal accounting'):
                v.journal_check(stream(full_events(last=final)))

    def test_any_row_after_completion_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Rows after terminal'):
            v.journal_check(stream(full_events(after=pair()[0])))

    def test_evidence_scope_rejected_before_any_archive_read(self):
        changes = [('postverify_sha256', 'b' * 64), ('physical_disk_reclaimed_bytes', TOTAL),
                   ('logical_removed_bytes', TOTAL - 1), ('raw_codex_events_prompts_usage_archived', True),
                   ('scientific_acceptance', 'PASS')]
        for document in ('source_bindings.json', 'build_receipt.json'):
            for key, value in changes:
                records = controls(); records[document][key] = value
                raw = {v.PREFIX + name: json.dumps(row).encode() for name, row in records.items()}
                with self.subTest(document=document, key=key), \
                        patch.object(v.A, 'get_controls', return_value=raw), \
                        patch.object(v.A, 'digest', side_effect=AssertionError('Archive must not be read')), \
                        self.assertRaisesRegex(ValueError, 'Evidence scope'):
                    v.verify(SimpleNamespace(local_inspect=True), None, {})


if __name__ == '__main__':
    unittest.main()
