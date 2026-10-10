"""Pure backing-UNC transport guards; no UNC access, WSL, locks or native calls."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
from contextlib import redirect_stdout
from unittest import mock
import unittest
import stage5_unc_backing_probe as U
import stage5_windows_backing_owner as O


WORK = Path(__file__).resolve().parent
BACKING_UNC = r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1'
CANONICAL_ROOT = '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
ORIGINAL_U = b"UNC = PureWindowsPath(r'\\\\wsl.localhost\\Ubuntu').joinpath(*PurePosixPath(TARGET).parts[1:])"
BACKING_U = b"UNC = PureWindowsPath(r'\\\\wsl.localhost\\Ubuntu\\var\\tmp\\lab_rm_stage05_atomic_v1')"
ORIGINAL_O = b"    return Path(r'\\\\wsl.localhost\\Ubuntu').joinpath(*PurePosixPath(target).parts[1:])"
BACKING_O = b"    return Path(r'\\\\wsl.localhost\\Ubuntu').joinpath(*PurePosixPath(frozen['backing']).parts[1:])"
PINS = {
    'stage5_unc_bind_probe.py': '0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d',
    'stage5_unc_backing_probe.py': '779502c38c5db06b68e796abc6e1bd99db72d8f97b1129f9057a3f6b0c4221d5',
    'stage5_windows_owner.py': '8851bc4fc48ad3069d4ffabe410e159004ef4fc8d6d0755213fc14c22fe0603d',
    'stage5_windows_backing_owner.py': '296492aa4205f64058846b9901a7bb3a3458f99eda1c7ff388a6e33cdc38b834',
    'stage5_atomic.py': '500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04',
    'stage5_atomic_process.py': 'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
}


class MinimalSourceDelta(unittest.TestCase):
    def test_exact_frozen_original_new_and_scientific_pins(self):
        for name, pin in PINS.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((WORK / name).read_bytes()).hexdigest(), pin)

    def test_probe_one_line_byte_reversible(self):
        old = (WORK / 'stage5_unc_bind_probe.py').read_bytes()
        new = (WORK / 'stage5_unc_backing_probe.py').read_bytes()
        self.assertEqual(old.count(ORIGINAL_U), 1)
        self.assertEqual(new.count(BACKING_U), 1)
        self.assertEqual(old.replace(ORIGINAL_U, BACKING_U), new)
        self.assertEqual(new.replace(BACKING_U, ORIGINAL_U), old)

    def test_owner_one_line_byte_reversible(self):
        old = (WORK / 'stage5_windows_owner.py').read_bytes()
        new = (WORK / 'stage5_windows_backing_owner.py').read_bytes()
        self.assertEqual(old.count(ORIGINAL_O), 1)
        self.assertEqual(new.count(BACKING_O), 1)
        self.assertEqual(old.replace(ORIGINAL_O, BACKING_O), new)
        self.assertEqual(new.replace(BACKING_O, ORIGINAL_O), old)

    def test_all_probe_function_asts_identical(self):
        def functions(name):
            return {node.name: ast.dump(node, include_attributes=False)
                    for node in ast.parse((WORK / name).read_bytes()).body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertEqual(functions('stage5_unc_bind_probe.py'),
                         functions('stage5_unc_backing_probe.py'))

    def test_owner_ast_only_evidence_return_changes(self):
        old = ast.parse((WORK / 'stage5_windows_owner.py').read_bytes())
        new = ast.parse((WORK / 'stage5_windows_backing_owner.py').read_bytes())
        old_view = next(n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == 'evidence_view')
        new_view = next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == 'evidence_view')
        self.assertIsInstance(old_view.body[-1], ast.Return)
        self.assertIsInstance(new_view.body[-1], ast.Return)
        self.assertNotEqual(ast.dump(old_view.body[-1]), ast.dump(new_view.body[-1]))
        new_view.body[-1] = copy.deepcopy(old_view.body[-1])
        self.assertEqual(ast.dump(old, include_attributes=False), ast.dump(new, include_attributes=False))


class ExactProbeRequest(unittest.TestCase):
    def setUp(self):
        nonce = '1' * 32
        self.request = dict(schema='STAGE05_UNC_BIND_PROBE_REQUEST_V1', scope=U.SCOPE,
            nonce=nonce, root=U.ROOT, target=U.TARGET, unc=str(U.UNC),
            expected_python=U.ENV + '/bin/python', source_pins=copy.deepcopy(U.PINS),
            sentinel_name='.unc_visibility_' + nonce,
            linux_payload_hex=(b'L' * 116).hex(), windows_payload_hex=(b'W' * 116).hex())

    def test_alias_only_and_canonical_target_preserved(self):
        self.assertEqual(str(U.UNC), BACKING_UNC)
        self.assertEqual(U.ROOT, CANONICAL_ROOT)
        self.assertEqual(U.TARGET, CANONICAL_ROOT + '/.work/stage05_atomic_v1')
        U.validate_request(self.request)

    def test_canonical_or_other_unc_rejected(self):
        for value in (r'\\wsl.localhost\Ubuntu\mnt\g\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage05_atomic_v1',
                      BACKING_UNC + '\\..', BACKING_UNC + '\\other',
                      BACKING_UNC.replace('Ubuntu', 'Other'), r'G:\My Drive\LAB_RM'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                U.validate_request({**self.request, 'unc': value})

    def test_backing_target_or_other_root_rejected(self):
        for key, value in (('target', '/var/tmp/lab_rm_stage05_atomic_v1'),
                           ('target', U.TARGET + '/other'), ('target', U.TARGET + '/../x'),
                           ('root', '/var/tmp'), ('expected_python', '/usr/bin/python3')):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                U.validate_request({**self.request, key: value})

    def test_source_nonce_and_two_way_payload_guards_unchanged(self):
        bad = [dict(source_pins={}), dict(nonce='other'), dict(sentinel_name='.other'),
               dict(windows_payload_hex=self.request['linux_payload_hex']),
               dict(linux_payload_hex=b'x'.hex())]
        for changed in bad:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                U.validate_request({**self.request, **changed})

    def test_probe_default_noop_has_exact_alias_and_no_science(self):
        output = io.StringIO()
        with mock.patch('sys.argv', [str(WORK / 'stage5_unc_backing_probe.py')]), redirect_stdout(output):
            self.assertEqual(U.main(), 0)
        value = json.loads(output.getvalue())
        self.assertEqual(value['state'], 'PREPARED_NOT_RUN')
        self.assertEqual(value['exact_unc'], BACKING_UNC)
        self.assertIs(value['scientific_adoption_authorized'], False)
        self.assertEqual(value['source_sha256'], PINS['stage5_unc_backing_probe.py'])


class ProvenBackingEvidenceView(unittest.TestCase):
    def setUp(self):
        self.target = CANONICAL_ROOT + '/.work/stage05_atomic_v1'
        self.config = {'output_root': self.target, 'work_storage':
                       {'proof_path': '/mnt/c/proof.json', 'proof_sha256': 'b' * 64}}
        self.proof = dict(schema=O.W.SCHEMA, canonical_root=CANONICAL_ROOT,
            canonical_target=self.target, backing=O.W.BACKING.as_posix(),
            helper_sha256='a' * 64, filesystem_uuid='uuid', boot_id='boot',
            target_mount={'filesystem': 'ext4'})

    def view(self):
        # All filesystem observations are fake; even G resolve and UNC read are avoided.
        with mock.patch.object(O, 'linux_path', return_value=CANONICAL_ROOT), \
             mock.patch.object(O.Path, 'is_file', return_value=True), \
             mock.patch.object(O.A, 'sha256', return_value='b' * 64), \
             mock.patch.object(O.A, 'read_json', return_value=self.proof):
            return O.evidence_view(self.config, 'a' * 64)

    def test_proven_backing_alias_return_and_canonical_config_unchanged(self):
        before = copy.deepcopy(self.config)
        self.assertEqual(str(self.view()), BACKING_UNC)
        self.assertEqual(self.config, before)

    def test_all_storage_identity_fields_reject_drift(self):
        for key in ('schema', 'canonical_root', 'canonical_target', 'backing', 'helper_sha256'):
            with self.subTest(key=key), mock.patch.dict(self.proof, {key: 'different'}), self.assertRaises(ValueError):
                self.view()

    def test_arbitrary_backing_escape_or_alias_rejected(self):
        for value in ('/var/tmp/other', '/var/tmp/lab_rm_stage05_atomic_v1/../x',
                      '/var//tmp/lab_rm_stage05_atomic_v1', self.target,
                      r'\\wsl.localhost\Ubuntu\var\tmp\other'):
            with self.subTest(value=value), mock.patch.dict(self.proof, {'backing': value}), self.assertRaises(ValueError):
                self.view()

    def test_missing_actual_ext4_identity_rejected(self):
        for changed in ({'filesystem_uuid': None}, {'boot_id': None},
                        {'target_mount': {'filesystem': 'drvfs'}}):
            with self.subTest(changed=changed), mock.patch.dict(self.proof, changed), self.assertRaises(ValueError):
                self.view()

    def test_config_target_cannot_move_to_backing_or_child(self):
        for value in (O.W.BACKING.as_posix(), self.target + '/child', '/other'):
            with self.subTest(value=value), mock.patch.dict(self.config, {'output_root': value}), self.assertRaises(ValueError):
                self.view()

    def test_proof_hash_and_path_guards_preserved(self):
        with mock.patch.dict(self.config['work_storage'], {'proof_sha256': 'c' * 64}), self.assertRaises(ValueError):
            self.view()
        for value in ('/mnt/c/../proof.json', '/mnt/g/proof.json', '/mnt/c//proof.json', r'/mnt/c/a\b'):
            with self.subTest(value=value), mock.patch.dict(self.config['work_storage'], {'proof_path': value}), self.assertRaises(ValueError):
                self.view()

    def test_absent_c_proof_rejected_without_reading_any_namespace(self):
        with mock.patch.object(O, 'linux_path', return_value=CANONICAL_ROOT), \
             mock.patch.object(O.Path, 'is_file', return_value=False), \
             mock.patch.object(O.A, 'read_json', side_effect=AssertionError('must not read')), self.assertRaises(ValueError):
            O.evidence_view(self.config, 'a' * 64)


if __name__ == '__main__':
    unittest.main()
