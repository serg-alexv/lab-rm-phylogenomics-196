"""Pure path/classification guards only; no metadata scan or cleanup."""
from pathlib import Path
import unittest
import prepare_old_scientific_emptydirs as P


class EmptyDirectoryContracts(unittest.TestCase):
    def test_causal_parents_stop_at_exact_scope_root(self):
        root = P.ROOTS[3]
        result = P.causal_parents(root / 'assemblies' / 'GCF_SYNTHETIC' / 'file.tsv')
        self.assertEqual(result[-1], root)
        self.assertNotIn(P.OLD / '.work', result)
        self.assertNotIn(P.OLD, result)

    def test_protected_and_outside_leaves_rejected(self):
        for path in [P.KEEP, P.OLD / '.work/workflow.lock', P.OLD / '.tools/file',
                     P.ROOTS[0] / '..' / 'outside']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                P.causal_parents(path)

    def test_unknown_files_or_reparse_children_preserve_parent(self):
        child = str(P.ROOTS[0] / 'child')
        self.assertTrue(P.eligible([], set()))
        self.assertTrue(P.eligible([{'path': child, 'kind': 'DIRECTORY'}], {child}))
        for kind in ['FILE_OR_OTHER_HELD', 'REPARSE_HELD', 'UNKNOWN_DIRECTORY_HELD_NO_TRAVERSAL']:
            self.assertFalse(P.eligible([{'path': child, 'kind': kind}], {child}))
        self.assertFalse(P.eligible([{'path': child, 'kind': 'DIRECTORY'}], set()))
        self.assertFalse(P.eligible([], set(), protected=True))

    def test_identity_birth_or_mutation_change_fails_stability(self):
        row = dict(volume_serial='1', file_id_128='01', creation_filetime='100',
                   last_write_filetime='200', change_filetime='201', attributes=16)
        self.assertTrue(P.stable(row, dict(row)))
        for key in row:
            changed = dict(row); changed[key] = 'different'
            self.assertFalse(P.stable(row, changed))


if __name__ == '__main__':
    unittest.main()
