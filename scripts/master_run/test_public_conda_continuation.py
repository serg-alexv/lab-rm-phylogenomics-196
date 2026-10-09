"""Offline synthetic copy/admission guards; retain tiny fixtures, no network."""
from pathlib import Path
import hashlib,importlib.util,types,unittest,uuid

WORK=Path(__file__).resolve().parent
def module(name,file):
    s=importlib.util.spec_from_file_location(name,WORK/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=module('continuation','continue_public_conda_packages01.py')
A=module('prior_base','acquire_public_conda_packages01.py')

class Contracts(unittest.TestCase):
    def test_stronger_two_probe_admission_boundaries(self):
        row=dict(physical_available_bytes=C.ADMISSION_PHYSICAL,commit_headroom_bytes=C.ADMISSION_COMMIT,c_disk_free_bytes=A.MIN_DISK)
        self.assertTrue(C.admission_passes(A,row))
        for key in row:
            with self.subTest(resource=key):self.assertFalse(C.admission_passes(A,{**row,key:row[key]-1}))
    def fixture(self):
        root=WORK/('conda_continuation_SYNTHETIC_fixture_'+uuid.uuid4().hex[:8]);root.mkdir();source=root/'NONSCIENCE_SOURCE.bin'
        data=b'UNRELATED_SYNTHETIC_COPY_FIXTURE\n'*100;source.write_bytes(data);output=root/'new_namespace';output.mkdir();(output/'packages').mkdir()
        pin=dict(filename='NONSCIENCE_SOURCE.bin',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),url='SYNTHETIC_NOT_REQUESTED')
        old=dict(path=str(source),original_identity=A.signature(source.stat()))
        fake=types.SimpleNamespace(BLOCK=A.BLOCK,signature=A.signature,utc=lambda:'SYNTHETIC',resources=None,guard=lambda *x:None)
        return source,output,pin,old,fake
    def test_full_copy_reopen_and_original_preservation(self):
        source,out,pin,old,fake=self.fixture();before=source.read_bytes()
        row=C.copy_completed(fake,pin,old,out,0)
        self.assertEqual(source.read_bytes(),before);self.assertEqual(Path(row['path']).read_bytes(),before)
        self.assertEqual(row['sha256'],pin['sha256'])
    def test_wrong_identity_and_hash_preserve_sources_and_partial(self):
        source,out,pin,old,fake=self.fixture();before=source.read_bytes()
        bad={**old,'original_identity':(*old['original_identity'][:2],0,*old['original_identity'][3:])}
        with self.assertRaises(ValueError):C.copy_completed(fake,pin,bad,out,0)
        wrong={**pin,'sha256':'0'*64}
        with self.assertRaises(ValueError):C.copy_completed(fake,wrong,old,out,0)
        self.assertEqual(source.read_bytes(),before)
        partial=out/'packages'/wrong['sha256']/(wrong['filename']+'.unverified_copy')
        self.assertTrue(partial.is_file());self.assertFalse(partial.with_name(wrong['filename']).exists())

if __name__=='__main__':unittest.main()
