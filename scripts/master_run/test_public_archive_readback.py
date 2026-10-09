"""Small nonbiological readback-contract fixtures; no network or source payload reads."""
from pathlib import Path
import hashlib, importlib.util, json, unittest, uuid, zipfile

WORK=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('readback',WORK/'verify_master_public_components01_remote.py')
V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)

class ReadbackContracts(unittest.TestCase):
    def fixture(self):
        root=WORK/('public_readback_synthetic_'+uuid.uuid4().hex[:10]);root.mkdir()
        path=root/'fixture.zip';payload=b'NONBIOLOGICAL_SYNTHETIC_BYTES\n'
        sums=(hashlib.sha256(payload).hexdigest()+'  payload.txt\n').encode()
        with zipfile.ZipFile(path,'x') as z:
            for n,b in [('payload.txt',payload),('SHA256SUMS.txt',sums)]:
                i=zipfile.ZipInfo(n,(2026,10,9,0,0,0));z.writestr(i,b)
        with zipfile.ZipFile(path) as z:
            expected={i.filename:dict(member=i.filename,bytes=i.file_size,sha256=hashlib.sha256(z.read(i)).hexdigest(),
                crc32=f'{i.CRC:08x}',crc_verified=True) for i in z.infolist()}
        return path,dict(name=path.name,bytes=path.stat().st_size,sha256=V.digest(path)),expected

    def test_complete_byte_and_crc_readback(self):
        path,asset,expected=self.fixture();z,observed=V.verify_zip(path,asset,expected)
        z.close();self.assertEqual(set(observed),set(expected));self.assertTrue(all(r['crc_verified'] for r in observed.values()))

    def test_independent_member_pin_rejects_self_consistent_zip(self):
        path,asset,expected=self.fixture();expected['payload.txt']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Build receipt/member bytes differ'):V.verify_zip(path,asset,expected)

    def test_omitted_member_rejected(self):
        path,asset,expected=self.fixture();del expected['payload.txt']
        with self.assertRaisesRegex(ValueError,'membership'):V.verify_zip(path,asset,expected)

    def test_outer_archive_pin_is_required(self):
        path,asset,expected=self.fixture();asset['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Outer archive'):V.verify_zip(path,asset,expected)

    def test_windows_alias_and_traversal_rejected(self):
        for names in (['../escape'],['A/x','a/y'],['a','a/b'],['CON.txt'],['x:stream'],['a\\b'],['a.'],['/absolute'],['a','a']):
            with self.subTest(names=names),self.assertRaises(ValueError):V.safe_names(names)

if __name__=='__main__':unittest.main()
