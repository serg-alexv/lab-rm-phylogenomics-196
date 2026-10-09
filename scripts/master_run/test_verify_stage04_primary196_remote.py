"""Small nonscientific contract fixtures; no actual data, G, network or WSL."""
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib, importlib.util, json, tempfile, unittest, zipfile
from Bio import Phylo
import verify_stage04_primary196_remote as V


class Contracts(unittest.TestCase):
    def test_distribution_duplicate_and_traversal_rejected(self):
        valid = b'path\tsha256\tbytes\nfile.txt\t'+b'a'*64+b'\t1\n'
        self.assertEqual(V.distribution_rows(valid)['file.txt']['bytes'],1)
        for bad in (valid+valid.splitlines(keepends=True)[1],valid.replace(b'file.txt',b'../file.txt'),valid.replace(b'\t1\n',b'\t-1\n')):
            with self.assertRaises(ValueError): V.distribution_rows(bad)

    def test_synthetic_supported_tree_and_nexus_signature(self):
        raw = '((SYN_A:0.1,SYN_B:0.1)95/100:0.2,SYN_C:0.1,SYN_D:0.1);'
        tree = Phylo.read(StringIO(raw),'newick'); panel = {'SYN_A','SYN_B','SYN_C','SYN_D'}
        facts = V.tree_facts(tree,panel,True)
        self.assertEqual((facts['edges'],facts['paired_supported_internal_edges']),(5,1))
        nexus = Phylo.read(StringIO('#NEXUS\nBegin trees;\nTree synthetic = [&U] '+raw+'\nEnd;'),'nexus')
        self.assertFalse(nexus.rooted); self.assertEqual(V.signature(nexus),V.signature(tree))
        for bad in (raw.replace('95/100','95/101'),raw.replace('95/100',''),raw.replace('SYN_A:0.1','SYN_A:-1'),raw.replace('SYN_A','SYN_B')):
            with self.assertRaises(ValueError): V.tree_facts(Phylo.read(StringIO(bad),'newick'),panel,True)

    def fixture(self, directory):
        path = directory/'synthetic.zip'; values = {f'fixture/{i:02d}.txt':f'SYNTHETIC {i}\n'.encode() for i in range(55)}
        values['SHA256SUMS.txt'] = ''.join(V.sha(b)+'  '+n+'\n' for n,b in values.items()).encode()
        with zipfile.ZipFile(path,'w') as z:
            for n,b in values.items(): z.writestr(n,b)
        with zipfile.ZipFile(path) as z:
            expected = {'asset':{'bytes':path.stat().st_size,'sha256':V.sha(path.read_bytes())},'total_members':56,
                        'logical_bytes':sum(i.file_size for i in z.infolist()),
                        'members':{i.filename:{'bytes':i.file_size,'sha256':V.sha(z.read(i)),'crc32':f'{i.CRC:08x}'} for i in z.infolist()}}
        helper = Path(__file__).with_name('verify_master_public_components01_remote.py')
        self.assertEqual(V.sha(helper.read_bytes()),V.HELPERS[helper.name])
        spec=importlib.util.spec_from_file_location('synthetic_safe_zip_only',helper); A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
        B=SimpleNamespace(A=A,file_sha=lambda p:V.sha(Path(p).read_bytes()),streamed_sha=lambda s:(lambda b:(len(b),V.sha(b)))(s.read()),guard=lambda:None)
        return path,expected,B,values

    def test_all56_members_crc_sha_and55_exhaustive_sums(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent,prefix='synthetic_stage4_readback_') as tmp:
            path,expected,B,_=self.fixture(Path(tmp))
            with patch.object(V,'science',return_value={'scope':'SYNTHETIC_ONLY'}):
                members,facts=V.inspect_zip(path,expected,B)
            self.assertEqual(len(members),56);self.assertEqual(facts['scope'],'SYNTHETIC_ONLY')

    def test_self_consistent_outer_rewrite_cannot_change_inner_accepted_pins(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent,prefix='synthetic_stage4_readback_') as tmp:
            path,expected,B,values=self.fixture(Path(tmp));values['fixture/00.txt']=b'WRONG ORIGINAL\n'
            with zipfile.ZipFile(path,'w') as z:
                for n,b in values.items():z.writestr(n,b)
            expected['asset']={'bytes':path.stat().st_size,'sha256':V.sha(path.read_bytes())}
            with patch.object(V,'science',side_effect=AssertionError('Must reject before science')),self.assertRaises(ValueError):
                V.inspect_zip(path,expected,B)

    def test_default_noop_never_loads_reader_or_reads_expected(self):
        with (patch.object(V,'load_reader',side_effect=AssertionError('No helper/native activity')),
              patch.object(V.sys,'argv',['verifier'])):
            self.assertEqual(V.main(),0)


if __name__ == '__main__': unittest.main()
