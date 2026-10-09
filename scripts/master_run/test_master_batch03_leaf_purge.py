"""Non-destructive path/identity contracts. No cleanup invocation, network or G writes."""
from pathlib import Path
import copy, hashlib, json, os, subprocess, unittest, uuid
import prepare_master_batch03_leaf_purge as p

def row():
    rel = 'data/example/file.faa'
    return {'relative_path': rel, 'path': str(p.OLD.joinpath(*rel.split('/'))), 'scope': 'data',
            'bytes': 3, 'sha256': 'a'*64, 'link_count': 1, 'device': 17766949232488609743,
            'file_id': 844424932788104, 'mtime_ns': 1791460058061945600,
            'recovery': {'member_bytes': 3, 'member_sha256': 'a'*64, 'remote_asset_id': 1,
                         'remote_zip_sha256': 'b'*64, 'remote_zip_bytes': 20, 'release_tag': 'fixture',
                         'remote_asset_url': 'https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/fixture/a.zip'}}

class Contracts(unittest.TestCase):
    def test_exact_scope_passes(self): self.assertEqual(p.validate_row(row()), row()['path'].casefold())
    def test_traversal_and_aliases_rejected(self):
        for rel in ('data/../file', 'data//file', 'data/./file', '/data/file', 'data/file:ads', 'data/file.',
                    'data/file ', 'data\\file'):
            with self.subTest(rel=rel):
                r=row(); r['relative_path']=rel
                with self.assertRaises(ValueError): p.validate_row(r)
    def test_protected_and_hardlink_rejected(self):
        for rel in ('data/.tools/file', 'data/.git/file', 'data/.private_run/file', 'data/a.guard', 'data/a.lock'):
            r=row(); r['relative_path']=rel
            with self.assertRaises(ValueError): p.validate_row(r)
        r=row();r['link_count']=2
        with self.assertRaises(ValueError):p.validate_row(r)
    def test_other_scope_or_root_rejected(self):
        for key,value in [('scope','.work/not_approved'),('path',r'G:\data\example\file.faa')]:
            r=row();r[key]=value
            with self.assertRaises(ValueError):p.validate_row(r)
    def test_member_and_remote_recovery_rejected(self):
        for key,value in [('member_bytes',4),('member_sha256','c'*64),('remote_zip_sha256','bad'),
                          ('remote_asset_url','https://example.com/fixture/a.zip')]:
            r=row();r['recovery'][key]=value
            with self.assertRaises(ValueError):p.validate_row(r)
    @unittest.skipUnless(os.name=='nt','Windows native fixture only')
    def test_windows_actual_handle_and_negative_contracts(self):
        directory=Path(__file__).resolve().parent/('batch03_leaf_fixture_'+uuid.uuid4().hex[:10])
        directory.mkdir(); target=directory/'benign_fixture.txt';target.write_bytes(b'BENIGN_NONSCIENTIFIC_FIXTURE\n')
        s=target.stat()
        manifest={'path':str(target),'bytes':s.st_size,'device':s.st_dev,'file_id':s.st_ino,
                  'mtime_ns':s.st_mtime_ns,'link_count':s.st_nlink,
                  'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'row':row()}
        control=directory/'expected.json';control.write_text(json.dumps(manifest),encoding='utf-8')
        result=subprocess.run(['pwsh','-NoProfile','-File',str(Path(__file__).with_name('Test-MasterBatch03LeafPurge.ps1')),
                               '-Fixture',str(control)],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        receipt=json.loads(result.stdout)
        self.assertEqual(receipt['state'],'PASS_NONDESTRUCTIVE_WINDOWS_FIXTURE')
        self.assertEqual(receipt['actual_device'],str(s.st_dev))
        self.assertEqual(receipt['actual_file_id'],str(s.st_ino))
        self.assertTrue(target.exists())

if __name__=='__main__':unittest.main()
