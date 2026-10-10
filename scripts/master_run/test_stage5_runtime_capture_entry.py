"""Pure source-owner/capacity tests; no Linux, mount, image or capture invocation."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('capture_entry',HERE/'stage5_runtime_capture_entry.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
I=M.load_inventory(HERE/M.INVENTORY_NAME)


class Tests(unittest.TestCase):
    def controls(self):
        boot='12345678-1234-1234-1234-123456789abc';nonce='a'*32;source='b'*64
        lease=dict(schema='STAGE05_WINDOWS_OWNER_LEASE_V1',workflow_lock_held=True,
                   workflow_lock=copy.deepcopy(I.ORIGINAL_LOCK),nonce=nonce,owner_pid=77,owner_creation_filetime='1234')
        proof=dict(schema='STAGE05_RUNTIME_COLD_CAPTURE_PROOF_V1',owner_nonce=nonce,workflow_lock=copy.deepcopy(I.ORIGINAL_LOCK),
                   original_workflow_lock_held=True,all_relevant_native_jobs_closed=True,backing_image_writer_exclusion_proven=True,
                   windows_owner=dict(pid=77,creation_filetime='1234'),boot_id=boot,
                   inventory_entry_source_sha256=M.INVENTORY_SHA,windows_api_source_sha256=I.PINS['atomic_iqtree_windows.py'],
                   capture_entry_source_sha256=source)
        return proof,lease,nonce,boot,source
    def test_both_source_pins_exact_and_owner_reused(self):
        args=self.controls();self.assertEqual(M.capture_owner_binding(I,*args),(77,'1234'))
        for key in ['inventory_entry_source_sha256','capture_entry_source_sha256']:
            proof,lease,nonce,boot,source=self.controls();proof[key]='0'*64
            with self.assertRaises(ValueError):M.capture_owner_binding(I,proof,lease,nonce,boot,source)
    def test_missing_arbitrary_or_mutated_lock_rejected(self):
        for replacement in [None,{},dict(arbitrary=True)]:
            proof,lease,nonce,boot,source=self.controls();proof['workflow_lock']=lease['workflow_lock']=replacement
            with self.assertRaises(ValueError):M.capture_owner_binding(I,proof,lease,nonce,boot,source)
    def test_owner_birth_currentboot_and_continuity_required(self):
        for field,bad in [('boot_id','0'*36),('windows_owner',dict(pid=77,creation_filetime='1235'))]:
            proof,lease,nonce,boot,source=self.controls();proof[field]=bad
            with self.assertRaises(ValueError):M.capture_owner_binding(I,proof,lease,nonce,boot,source)
        with self.assertRaises(ValueError):M.capture_owner_binding(I,*self.controls(),previous=(78,'1234'))
    def test_capacity_counts_original_regular_once_and_control_overhead(self):
        rows=[dict(kind='regular',bytes=100),dict(kind='hardlink',bytes=100),dict(kind='directory',bytes=0)]
        raw=''.join(json.dumps(row)+'\n' for row in rows).encode()
        self.assertEqual(M.output_capacity(raw,200),100+200+11*4096+64*1024**2)
    def test_capacity_rejects_special_negative_bool_empty_and_huge(self):
        for rows in [[],[dict(kind='special',bytes=1)],[dict(kind='regular',bytes=-1)],
                     [dict(kind='regular',bytes=True)],[dict(kind='regular',bytes=129*1024**3)]]:
            raw=''.join(json.dumps(row)+'\n' for row in rows).encode()
            with self.assertRaises(ValueError):M.output_capacity(raw,0)
    def test_remaining_capacity_preserves_reserve_without_double_count(self):
        reserve=10*1024**3
        self.assertEqual(M.remaining_disk_requirement(100,0),reserve+100)
        self.assertEqual(M.remaining_disk_requirement(100,30),reserve+70)
        self.assertEqual(M.remaining_disk_requirement(100,101),reserve)
        with self.assertRaises(ValueError):M.remaining_disk_requirement(100,True)


if __name__=='__main__':unittest.main()
