"""Focused synthetic contracts only; never invokes actual post-purge verification."""
import copy
import unittest
import verify_master_history02_leaf_purge as v

ROW = dict(path='C:\\synthetic\\leaf', bytes=3, sha256='a' * 64,
           device='17766949232488609743', file_id='844424932788104', mtime_ns='1791460058061945600')


def pair():
    intent = dict(event='VERIFIED_INTENT', index=1, **ROW)
    return [intent, {k: intent[k] for k in ('index', 'path', 'bytes', 'sha256')} |
            dict(event='REMOVED', deleted=1, deleted_bytes=3)]


def join(rows):
    iterator = iter(rows)
    return v.join_candidate(lambda: next(iterator), ROW, 1, 0, 0)


def terminal():
    return dict(event='COMPLETE', state='PASS_EXACT837_RECOVERED_HISTORY_LEAVES_REMOVED',
                deleted=837, deleted_bytes=983926424, excluded_preserved=1, excluded_bytes=1025,
                protected_hashes_unchanged=12, recursive_deletes=0)


class Contracts(unittest.TestCase):
    def test_ordered_exact_identity_pair(self):
        self.assertEqual(join(pair())[1]['event'], 'REMOVED')
        normalized = v.numeric_row(ROW)
        self.assertEqual(normalized['device'], 17766949232488609743)
        self.assertEqual(normalized['mtime_ns'], 1791460058061945600)

    def test_wrong_index_identity_or_payload_rejected(self):
        for key, value in [('index', 2), ('path', 'C:\\other'), ('sha256', 'b' * 64),
                           ('bytes', 4), ('device', '2430728143'), ('file_id', '1'), ('mtime_ns', '1')]:
            rows = pair(); rows[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                join(rows)

    def test_reordered_duplicate_or_detached_outcome_rejected(self):
        for rows in [list(reversed(pair())), [pair()[0], pair()[0]]]:
            with self.assertRaises(ValueError):
                join(rows)
        for key, value in [('index', 2), ('path', 'C:\\other'), ('sha256', 'b' * 64),
                           ('bytes', 4), ('deleted', 2), ('deleted_bytes', 4)]:
            rows = pair(); rows[1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                join(rows)

    def test_stop_preserved_before_or_after_intent(self):
        stop = dict(event='STOP', state='FAILED_PARTIAL_PRESERVE_REMAINDER')
        self.assertEqual(join([stop]), (None, stop))
        self.assertEqual(join([pair()[0], stop])[1], stop)

    def test_completion_requires_exact_scope_and_counts(self):
        v.check_complete(terminal(), 837, 983926424)
        for key, value in [('event', 'STOP'), ('state', 'PASS'), ('deleted', 836),
                           ('deleted_bytes', 983926423), ('excluded_preserved', 0),
                           ('excluded_bytes', 0), ('protected_hashes_unchanged', 11), ('recursive_deletes', 1)]:
            last = copy.deepcopy(terminal()); last[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.check_complete(last, 837, 983926424)
        with self.assertRaises(ValueError):
            v.check_complete(terminal(), 836, 983926424)


if __name__ == '__main__':
    unittest.main()
