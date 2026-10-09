"""Negative current-invocation/actual-exit binding checks; no native launches."""
import unittest
from unittest import mock
import stage5_windows_owner as O
from stage5_windows_owner import terminal_binding


class ApprovedQueueSelection(unittest.TestCase):
    def setUp(self):
        self.panel = ['GCF_'+str(index)+'.1' for index in range(196)]

    def test_default_preserves_entire_panel_and_order(self):
        self.assertEqual(O.selected_accessions(self.panel), self.panel)
        self.assertIsNot(O.selected_accessions(self.panel), self.panel)

    def test_one_checkpoint_keeps_approved_accession_identity(self):
        self.assertEqual(O.selected_accessions(self.panel, self.panel[19]), [self.panel[19]])

    def test_nonpanel_or_combined_accessions_rejected(self):
        for value in ('GCF_unknown.1', self.panel[0]+','+self.panel[1], '', '../escape'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                O.selected_accessions(self.panel, value)


class InvocationBinding(unittest.TestCase):
    def test_correct_current_complete(self):
        terminal_binding({'accession':'GCF_1.1','owner_nonce':'new','state':'COMPLETE_VALIDATED'},
                         'GCF_1.1','new',0)

    def test_stale_complete_cannot_be_adopted(self):
        with self.assertRaises(ValueError):
            terminal_binding({'accession':'GCF_1.1','owner_nonce':'old','state':'COMPLETE_VALIDATED'},
                             'GCF_1.1','new',0)

    def test_different_genome_cannot_be_adopted(self):
        with self.assertRaises(ValueError):
            terminal_binding({'accession':'GCF_2.1','owner_nonce':'new','state':'COMPLETE_VALIDATED'},
                             'GCF_1.1','new',0)

    def test_failed_client_cannot_adopt_complete(self):
        with self.assertRaises(ValueError):
            terminal_binding({'accession':'GCF_1.1','owner_nonce':'new','state':'COMPLETE_VALIDATED'},
                             'GCF_1.1','new',2)

    def test_fatal_client_cannot_be_treated_retryable(self):
        with self.assertRaises(ValueError):
            terminal_binding({'accession':'GCF_1.1','owner_nonce':'new','state':'FAILED_RETRYABLE'},
                             'GCF_1.1','new',2)

    def test_unknown_state_cannot_be_adopted(self):
        with self.assertRaises(ValueError):
            terminal_binding({'accession':'GCF_1.1','owner_nonce':'new','state':'UNKNOWN'},
                             'GCF_1.1','new',0)


class NativeEvidenceView(unittest.TestCase):
    def setUp(self):
        self.target = O.linux_path(O.ROOT) + '/.work/stage05_atomic_v1'
        self.config = {'output_root': self.target, 'work_storage':
                       {'proof_path': '/mnt/c/proof.json', 'proof_sha256': 'b'*64}}
        self.proof = {'schema': O.W.SCHEMA, 'canonical_root': O.linux_path(O.ROOT),
                      'canonical_target': self.target, 'backing': O.W.BACKING.as_posix(),
                      'helper_sha256': 'a'*64, 'filesystem_uuid': 'uuid', 'boot_id': 'boot',
                      'target_mount': {'filesystem': 'ext4'}}

    def view(self):
        with mock.patch.object(O.Path, 'is_file', return_value=True), \
             mock.patch.object(O.A, 'sha256', return_value='b'*64), \
             mock.patch.object(O.A, 'read_json', return_value=self.proof):
            return O.evidence_view(self.config, 'a'*64)

    def test_readback_uses_native_ubuntu_unc_not_covered_windows_g(self):
        self.assertEqual(str(self.view()), r'\\wsl.localhost\Ubuntu\mnt\g\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage05_atomic_v1')

    def test_different_target_or_helper_is_rejected(self):
        for field in ('canonical_target', 'helper_sha256', 'backing'):
            with self.subTest(field=field), mock.patch.dict(self.proof, {field: 'different'}), \
                 self.assertRaises(ValueError): self.view()

    def test_windows_proof_hash_drift_is_rejected(self):
        self.config['work_storage']['proof_sha256'] = 'c'*64
        with self.assertRaises(ValueError): self.view()

    def test_proof_path_escape_or_noncanonical_alias_is_rejected(self):
        for path in ('/mnt/c/../proof.json', '/mnt/g/proof.json', '/mnt/c//proof.json', r'/mnt/c/a\b'):
            with self.subTest(path=path):
                self.config['work_storage']['proof_path'] = path
                with self.assertRaises(ValueError): self.view()


if __name__ == '__main__':
    unittest.main()
