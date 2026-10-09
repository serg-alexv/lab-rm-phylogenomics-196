"""Non-destructive preparation contracts; no cleanup invocation or native API launch."""
from pathlib import Path
import copy,importlib.util,json,unittest

WORK=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('history_purge_preparation',WORK/'prepare_master_history02_leaf_purge.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def row():
    return dict(path=str(P.OLD/'data'/'fixture.txt'),relative_path='data/fixture.txt',scope='data',link_count=1,
        bytes=3,sha256='a'*64,device='17766949232488609743',file_id='123',mtime_ns='1791460058061945600')

class Contracts(unittest.TestCase):
    def test_exact_scope(self):self.assertEqual(P.validate_row(row()),row()['path'].casefold())
    def test_alias_traversal_protected_link(self):
        for rel in ('data/../file','data//file','/data/file','data/file:ads','data/file.','data/file ','data\\file',
                    'data/.tools/file','data/.git/file','data/.private_run/file','data/a.lock','data/a.guard'):
            with self.subTest(rel=rel):
                r=row();r['relative_path']=rel
                with self.assertRaises(ValueError):P.validate_row(r)
        r=row();r['link_count']=2
        with self.assertRaises(ValueError):P.validate_row(r)
    def test_wrong_scope_root(self):
        for key,value in [('scope','.work/not_approved'),('path',r'G:\data\fixture.txt')]:
            r=row();r[key]=value
            with self.assertRaises(ValueError):P.validate_row(r)
    def test_postverify_failure_partial_or_missing_rejected(self):
        for d in ({},{'schema':'MASTER_BATCH03_INDEPENDENT_POST_PURGE_VERIFY_V1','state':'PARTIAL_STOP'},
                  {'schema':'MASTER_BATCH03_INDEPENDENT_POST_PURGE_VERIFY_V1','state':'PREPARATION_PASS'}):
            with self.assertRaises(ValueError):P.validate_post(d,[],{})
    def test_actual_postverify_join_and_excluded_source_required(self):
        plan=json.loads((WORK/'master_history02_leaf_purge_proposed.json').read_bytes())
        post=json.loads(Path(plan['batch03_postverify']['path']).read_bytes())
        P.validate_post(post,plan['candidates'],plan['excluded_preserved'][0])
        bad=copy.deepcopy(post);bad['retained_originals'][0]['sha256']='f'*64
        with self.assertRaises(ValueError):P.validate_post(bad,plan['candidates'],plan['excluded_preserved'][0])
        bad=copy.deepcopy(post);bad['retained_originals'][0]['identity_equal']=False
        with self.assertRaises(ValueError):P.validate_post(bad,plan['candidates'],plan['excluded_preserved'][0])
        with self.assertRaises(ValueError):P.validate_post(post,plan['candidates'],plan['candidates'][0])

if __name__=='__main__':unittest.main()
