"""Pure synthetic tests; no native handles, WSL, images, locks or disk writes."""
import copy
import hashlib
import importlib.util
import io
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('offline_parts', Path(__file__).with_name('stage5_offline_image_read_parts.py'))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)


def identity(role='toolchain_ext4'):
    return dict(path=M.IMAGE_PATHS[role], volume_serial=1, file_index=2, creation_filetime=3,
                written_filetime=4, bytes=11, links=1, attributes=0)


class Sink(io.BytesIO):
    def close(self):
        self.saved = self.getvalue()
        super().close()


class Tests(unittest.TestCase):
    def owner(self):
        return dict(workflow_lock_held=True, workflow_lock=copy.deepcopy(M.LOCK), owner_pid=101,
                    owner_creation_filetime='1234', nonce='a'*32)
    def test_exact_owner_identity_and_types(self):
        self.assertEqual(M.owner_context(self.owner()), (101, '1234', 'a'*32))
        for key in M.LOCK:
            value=self.owner(); value['workflow_lock'].pop(key)
            with self.assertRaises(ValueError):M.owner_context(value)
        value=self.owner(); value['workflow_lock']['volume_serial']=float(M.LOCK['volume_serial'])
        with self.assertRaises(ValueError):M.owner_context(value)
        value=self.owner(); value['workflow_lock']=None
        with self.assertRaises(ValueError):M.owner_context(value)
    def test_image_identity_rejects_alias_hardlink_and_zero(self):
        self.assertEqual(M.image_identity('toolchain_ext4', identity()), identity())
        for key,bad in [('path',M.IMAGE_PATHS['ubuntu_vhdx']),('links',2),('attributes',0x400),('bytes',0),('file_index',False)]:
            value=identity(); value[key]=bad
            with self.assertRaises(ValueError):M.image_identity('toolchain_ext4',value)
    def review(self):
        return dict(schema='STAGE05_OFFLINE_IMAGE_WHOLE_BYTE_PUBLIC_REVIEW_V1', role='toolchain_ext4',
                    source_identity=identity(), complete_file_bytes_reviewed=11,
                    allocated_and_unallocated_bytes_reviewed=True, private_or_unknown_bytes_remaining=0,
                    decision='PUBLIC_ORIGINAL_BYTES', reviewer_id='synthetic-reviewer', whole_file_sha256='b'*64)
    def test_logical_only_or_unknown_review_cannot_authorize_raw(self):
        self.assertEqual(M.public_review('toolchain_ext4',identity(),self.review()),'b'*64)
        for key,bad in [('allocated_and_unallocated_bytes_reviewed',False),('private_or_unknown_bytes_remaining',1),
                        ('private_or_unknown_bytes_remaining',False),('complete_file_bytes_reviewed',10),
                        ('decision','LOGICAL_ROOTS_ONLY'),('whole_file_sha256','bad')]:
            value=self.review();value[key]=bad
            with self.assertRaises(ValueError):M.public_review('toolchain_ext4',identity(),value)
    def run_stream(self,data,expected=None,size=None,limit=4,guard=lambda:None,reader=None):
        source=io.BytesIO(data);outputs={}
        def opened(name):
            self.assertNotIn(name,outputs); sink=Sink();outputs[name]=sink;return sink
        result=M.partition_stream(reader or source.read,opened,len(data) if size is None else size,
                                  expected or hashlib.sha256(data).hexdigest(),M.LABELS['toolchain_ext4'],'20261010-v1',guard,limit)
        return result,outputs
    def test_exact_parts_reassemble_with_original_outer_sha(self):
        data=b'abcdefghijk';result,outputs=self.run_stream(data)
        self.assertEqual([r['offset'] for r in result['parts']],[0,4,8])
        self.assertEqual([r['bytes'] for r in result['parts']],[4,4,3])
        self.assertEqual(b''.join(outputs[r['name']].saved for r in result['parts']),data)
        for row in result['parts']:
            self.assertEqual(hashlib.sha256(outputs[row['name']].saved).hexdigest(),row['sha256'])
        self.assertIn('toolchain-installed-runtime-whole-ext4',result['parts'][0]['name'])
    def test_truncation_growth_outer_sha_and_reader_overrun_fail(self):
        with self.assertRaises(ValueError):self.run_stream(b'abc',size=4)
        with self.assertRaises(ValueError):self.run_stream(b'abcd',size=3)
        with self.assertRaises(ValueError):self.run_stream(b'abc',expected='0'*64)
        with self.assertRaises(ValueError):self.run_stream(b'abc',reader=lambda n:b'x'*(n+1))
    def test_guard_failure_is_not_ignored(self):
        calls=[]
        def guard():
            calls.append(1)
            if len(calls)==3:raise RuntimeError('synthetic admission failed')
        with self.assertRaises(RuntimeError):self.run_stream(b'abcdefghijk',guard=guard)
    def test_part_cap_and_names_are_strict(self):
        with self.assertRaises(ValueError):self.run_stream(b'abc',limit=M.SHARD_LIMIT+1)
        with self.assertRaises(ValueError):M.partition_stream(None,None,3,'a'*64,'../bad','20261010-v1',lambda:None)
        with self.assertRaises(ValueError):M.partition_stream(io.BytesIO(b'a').read,lambda n:Sink(),1,'a'*64,
                                                             M.LABELS['toolchain_ext4'],'../bad',lambda:None)


if __name__=='__main__':unittest.main()
