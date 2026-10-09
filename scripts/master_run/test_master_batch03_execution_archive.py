"""Synthetic semantic gate checks only; never creates an archive or deletes files."""
import copy,unittest
import build_master_batch03_execution_archive as b

def post():
    rows=[{'path':f'C:/fixture/{i}','bytes':0,'sha256':'a'*64,'identity_equal':True} for i in range(838)]
    rows[0]['bytes']=983927449
    owners=[{'pid':p,'creation_filetime':t,'alive':True,'retained_handle':True} for p,t in b.OWNERS]
    return {'schema':'MASTER_BATCH03_INDEPENDENT_POST_PURGE_VERIFY_V1','state':'PASS_EXACT47429_REMOVED_838_ORIGINALS_AND12_PROTECTED_UNCHANGED',
            'verifier_sha256':b.VERIFIER_SHA,'removed_files':47429,'removed_bytes':6565902818,'held_files':219,'held_bytes':2729256,
            'unmatched_files':619,'unmatched_bytes':981198193,'remaining_after_stop':0,'unreceipted_absences':[],
            'retained_original_bytes_hashed':983927449,'source_deletions':0,'network_calls':0,'g_writes':0,'wsl_starts':0,'scientific_jobs':0,
            'retained_originals':rows,'protected_files':[{'unchanged':True} for _ in range(12)],'owners_before':owners,'owners_after':copy.deepcopy(owners),
            'journal_terminal':{'event':'COMPLETE','state':'PASS_EXACT_47429_COLD_LEAVES_REMOVED','deleted':47429,'deleted_bytes':6565902818,
                                'held_files':219,'unmatched_preserved':619,'recursive_deletes':0}}
class Gates(unittest.TestCase):
    def test_exact_semantic_receipt(self):b.validate_post(post())
    def test_partial_or_wrong_accounting_cannot_pass(self):
        for key,value in [('state','PARTIAL_STOP'),('removed_files',47428),('removed_bytes',1),('remaining_after_stop',1),('verifier_sha256','b'*64)]:
            r=post();r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):b.validate_post(r)
    def test_duplicate_original_or_unverified_protected_rejected(self):
        r=post();r['retained_originals'][1]['path']=r['retained_originals'][0]['path']
        with self.assertRaises(ValueError):b.validate_post(r)
        r=post();r['protected_files'][0]['unchanged']=False
        with self.assertRaises(ValueError):b.validate_post(r)
    def test_wrong_or_exited_owner_rejected(self):
        for key,value in [('alive',False),('creation_filetime','1'),('retained_handle',False)]:
            r=post();r['owners_after'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):b.validate_post(r)
    def test_terminal_stop_or_recursive_claim_rejected(self):
        for key,value in [('event','STOP'),('recursive_deletes',1),('deleted',47428)]:
            r=post();r['journal_terminal'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):b.validate_post(r)

if __name__=='__main__':unittest.main()
