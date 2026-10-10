"""Synthetic authority/boot/owner tamper cases; no Linux or private payload I/O."""
import copy
import unittest
import stage5_runtime_inventory_entry_v3 as I


class OwnerBindingTests(unittest.TestCase):
    def setUp(self):
        self.nonce = 'a'*32; self.boot = '00000000-0000-0000-0000-000000000001'; self.source = 'b'*64
        self.lease = {'schema': 'STAGE05_WINDOWS_OWNER_LEASE_V1', 'workflow_lock_held': True,
                      'nonce': self.nonce, 'workflow_lock': dict(I.ORIGINAL_LOCK),
                      'owner_pid': 123, 'owner_creation_filetime': '134360000000000001'}
        self.proof = {'schema': 'STAGE05_RUNTIME_COLD_CAPTURE_PROOF_V1', 'owner_nonce': self.nonce,
                      'workflow_lock': dict(I.ORIGINAL_LOCK), 'original_workflow_lock_held': True,
                      'all_relevant_native_jobs_closed': True, 'backing_image_writer_exclusion_proven': True,
                      'boot_id': self.boot, 'inventory_entry_source_sha256': self.source,
                      'windows_api_source_sha256': I.PINS['atomic_iqtree_windows.py'],
                      'windows_owner': {'pid': 123, 'creation_filetime': '134360000000000001'}}

    def bind(self, proof=None, lease=None, previous=None):
        return I.owner_binding(self.proof if proof is None else proof, self.lease if lease is None else lease,
                               self.nonce, self.boot, self.source, previous)

    def test_actual_exact_schema_binding_and_continuous_birth(self):
        identity = self.bind(); self.assertEqual(identity, (123, '134360000000000001'))
        self.assertEqual(self.bind(previous=identity), identity)

    def test_mutual_missing_none_and_arbitrary_lock_rejected(self):
        for wrong in [None, {}, {'locked_byte': 0}, {**I.ORIGINAL_LOCK, 'file_index': 1}]:
            proof = copy.deepcopy(self.proof); lease = copy.deepcopy(self.lease)
            proof['workflow_lock'] = lease['workflow_lock'] = wrong
            with self.assertRaises(ValueError): self.bind(proof, lease)
        proof = copy.deepcopy(self.proof); lease = copy.deepcopy(self.lease)
        del proof['workflow_lock']; del lease['workflow_lock']
        with self.assertRaises(ValueError): self.bind(proof, lease)

    def test_every_immutable_lock_field_is_mandatory(self):
        for key in I.ORIGINAL_LOCK:
            for side in ['proof', 'lease']:
                proof = copy.deepcopy(self.proof); lease = copy.deepcopy(self.lease)
                del (proof if side == 'proof' else lease)['workflow_lock'][key]
                with self.assertRaises(ValueError): self.bind(proof, lease)
        for key in ['volume_serial', 'file_index', 'creation_filetime', 'locked_byte']:
            proof = copy.deepcopy(self.proof); lease = copy.deepcopy(self.lease)
            proof['workflow_lock'][key] = lease['workflow_lock'][key] = float(I.ORIGINAL_LOCK[key])
            with self.assertRaises(ValueError): self.bind(proof, lease)

    def test_current_boot_source_api_and_owner_nonce_mandatory(self):
        for key, value in [('boot_id', '00000000-0000-0000-0000-000000000002'),
                           ('inventory_entry_source_sha256', 'c'*64), ('windows_api_source_sha256', 'd'*64),
                           ('owner_nonce', 'e'*32)]:
            proof = copy.deepcopy(self.proof); proof[key] = value
            with self.assertRaises(ValueError): self.bind(proof)

    def test_proof_owner_pid_birth_and_continuous_lease_identity_mandatory(self):
        for owner in [{'pid': 124, 'creation_filetime': '134360000000000001'},
                      {'pid': 123.0, 'creation_filetime': '134360000000000001'},
                      {'pid': 123, 'creation_filetime': '134360000000000001', 'extra': True},
                      {'pid': 123, 'creation_filetime': '134360000000000002'}, None]:
            proof = copy.deepcopy(self.proof); proof['windows_owner'] = owner
            with self.assertRaises(ValueError): self.bind(proof)
        with self.assertRaises(ValueError): self.bind(previous=(124, '134360000000000001'))

    def test_false_integer_true_and_missing_cold_attestations_rejected(self):
        for key in ['original_workflow_lock_held', 'all_relevant_native_jobs_closed', 'backing_image_writer_exclusion_proven']:
            for value in [False, None, 1]:
                proof = copy.deepcopy(self.proof); proof[key] = value
                with self.assertRaises(ValueError): self.bind(proof)

    def test_invalid_or_released_owner_lease_rejected(self):
        for key, value in [('workflow_lock_held', False), ('owner_pid', True), ('owner_creation_filetime', '0'),
                           ('owner_creation_filetime', 134360000000000001), ('nonce', 'f'*32)]:
            lease = copy.deepcopy(self.lease); lease[key] = value
            with self.assertRaises(ValueError): self.bind(lease=lease)


if __name__ == '__main__':
    unittest.main()
