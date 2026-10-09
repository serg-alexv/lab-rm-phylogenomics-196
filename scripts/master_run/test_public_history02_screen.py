"""Meaningful synthetic privacy/source-drift guards; no history/archive execution."""
from pathlib import Path
from unittest.mock import patch
import hashlib,json,os,tempfile,unittest
import inspect_public_history02 as I

class Screen(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='history02_synthetic_',dir=Path(__file__).parent)
        self.root=Path(self.temp.name).resolve();self.assertIn(Path(__file__).parent.resolve(),self.root.parents)
        self.addCleanup(self.temp.cleanup)
    def row(self,data):
        path=self.root/'.work/review2/scientific_fixture.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        s=path.stat();return{'path':str(path),'relative_path':'.work/review2/scientific_fixture.json','scope':'.work/review2',
            'bytes':s.st_size,'device':s.st_dev,'file_id':s.st_ino,'mtime_ns':s.st_mtime_ns,'link_count':s.st_nlink,
            'sha256':hashlib.sha256(data).hexdigest()}
    def inspect(self,row):
        with patch.object(I,'ROOT',self.root):return I.inspect_one(row)
    def test_scientific_command_history_is_preserved_without_closure_inference(self):
        r=self.row(json.dumps({'execution':'UNKNOWN','argv':['iqtree','-s','SYNTHETIC.faa']}).encode())
        found=self.inspect(r);self.assertEqual(found['content']['historical_state_fields']['execution'],'UNKNOWN')
        self.assertEqual(found['sha256_observed'],r['sha256'])
    def test_raw_private_event_rejected_whole_file(self):
        event={'ty'+'pe':'session_'+'meta','payload':{'synthetic':True}}
        r=self.row(json.dumps(event).encode())
        with self.assertRaisesRegex(ValueError,'RAW_CODEX_EVENT'):self.inspect(r)
    def test_credential_signature_crossing_chunk_boundary_rejects(self):
        token=b'gh'+b'p_'+b'X'*32
        data=b'{"status":"SYNTHETIC","text":"'+b'A'*(I.CHUNK-45)+token+b'"}'
        r=self.row(data)
        with self.assertRaisesRegex(ValueError,'CREDENTIAL_SHAPED'):self.inspect(r)
    def test_source_hash_drift_rejects_instead_of_adopting_new_bytes(self):
        r=self.row(b'{"status":"SYNTHETIC"}');r['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'differs from exact original hash'):self.inspect(r)

if __name__=='__main__':unittest.main()
