"""Focused metadata contract tests; no archive payload, network or scientific jobs."""
from pathlib import Path
import copy, hashlib, importlib.util, json, unittest

PATH = Path(__file__).with_name('build_iqtree314_source_recovery01.py')
spec = importlib.util.spec_from_file_location('iqtree_recovery_builder_tests', PATH)
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

class Captured:
    def __init__(self, data, record=None): self.data, self.record = data, record
    def bytes(self): return self.data

def metadata():
    # Only fixed small public controls are reopened, never the three source archives.
    captures = {}
    for name, expected in B.SUCCESS.items():
        if name.endswith('.tar.gz'): continue
        data = (B.WORK / B.NEW / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected
        captures['success/' + name] = Captured(data)
    data = (B.WORK / B.OLD / 'receipt.json').read_bytes()
    assert hashlib.sha256(data).hexdigest() == B.FAILURE['receipt.json']
    captures['first_failure/receipt.json'] = Captured(data)
    receipt = json.loads(captures['success/receipt.json'].data)
    for row in receipt['repositories']:
        captures['success/' + row['archive']] = Captured(None, {'bytes': row['bytes'], 'sha256': row['sha256']})
    return captures

class Contracts(unittest.TestCase):
    def test_exact_captured_metadata_passes_qualified_1938_contract(self):
        binding = B.validate_controls(metadata())
        self.assertEqual(binding['original_git_blobs'], 1938)
        self.assertFalse(binding['all_archive_files_equal_git_bytes'])

    def test_commit_tree_substitution_rejected(self):
        rows = metadata(); key = 'success/iqtree3_git_commit.json'
        obj = json.loads(rows[key].data); obj['tree']['sha'] = '0' * 40
        rows[key] = Captured(json.dumps(obj).encode())
        with self.assertRaisesRegex(ValueError, 'commit/root-tree'): B.validate_controls(rows)

    def test_second_export_exception_rejected(self):
        rows = metadata(); key = 'success/cmaple_actual_blobs.json'
        obj = json.loads(rows[key].data); path = next(iter(obj))
        obj[path]['original_recovery_supplement'] = 'original_git_blobs/second.blob'
        rows[key] = Captured(json.dumps(obj).encode())
        with self.assertRaisesRegex(ValueError, 'Unapproved source export'): B.validate_controls(rows)

if __name__ == '__main__': unittest.main()
