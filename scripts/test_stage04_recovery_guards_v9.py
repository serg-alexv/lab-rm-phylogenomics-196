"""Narrow negative adoption/cache tests; no biological tools or production writes."""
import copy, json, unittest
from unittest.mock import patch
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v9 as S
import stage04_recovery_controller_v9 as P
from stage04_model_cache_evidence_v9 import check_cache_log

class Guards(unittest.TestCase):
    def setUp(self):
        self.proposal={'required_review_artifacts':{'data:scripts/example.py':'a'*64},'scheduler_fixture_sha256':'b'*64,
          'production_task':{'task_name':'EXAMPLE_NOT_REGISTERED','definition_sha256':'c'*64}}
        self.review={'schema':'PARENT_RECOVERY_V9_HASH_BOUND_ACCEPTANCE','decision':'ACCEPTED_FOR_SINGLE_PRODUCTION_START',
          'reviewer':'INDEPENDENT_PARENT','production_task_name':'EXAMPLE_NOT_REGISTERED',
          'artifact_sha256':{**self.proposal['required_review_artifacts'],'data:config/host_inference_stage04_recovery_v9_freeze.json':'d'*64},
          'outer_job_lifetime_review':{'decision':'ACCEPT_OBSERVED_SCHEDULER_BOUND_OUTER_JOB_LIFETIME','fixture_sha256':'b'*64,
            'production_task_definition_sha256':'c'*64,'native_controls':'NESTED_OWNED_JOB_3GIB_MASK5_NO_BREAKAWAY',
            'old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY'}}
        self.negative={'ordinary_success_receipt':False,'original_job_closure':'UNKNOWN','original_controller_outcome':'UNKNOWN',
          'actual_native_exit':{'exit_code_dword':1}}
    def call(self,review=None,proposal=None,negative=None):
        review=self.review if review is None else review;proposal=self.proposal if proposal is None else proposal;negative=self.negative if negative is None else negative
        def read(path):
            if Path(path)==P.ACCEPTANCE:return review
            if Path(path)==P.PROPOSAL:return proposal
            return negative
        with patch.object(C,'load',side_effect=read),patch.object(C,'digest',return_value='d'*64),patch.object(P,'verify_artifacts') as hashes,patch.object(S,'pins'):
            result=P.acceptance();hashes.assert_called_once();return result
    def test_valid_structure_only_fixture_never_launches(self):self.call()
    def test_bare_pass_file_rejected(self):
        with self.assertRaises(ValueError):self.call(review={'status':'PASS'})
    def test_wrong_parent_schema_rejected(self):
        v=copy.deepcopy(self.review);v['schema']='ordinary_exit';self.assertRaises(ValueError,self.call,review=v)
    def test_wrong_task_rejected(self):
        v=copy.deepcopy(self.review);v['production_task_name']='another';self.assertRaises(ValueError,self.call,review=v)
    def test_non_parent_reviewer_rejected(self):
        v=copy.deepcopy(self.review);v['reviewer']='OWNER';self.assertRaises(ValueError,self.call,review=v)
    def test_missing_source_hash_rejected(self):
        v=copy.deepcopy(self.review);v['artifact_sha256'].pop('data:scripts/example.py');self.assertRaises(ValueError,self.call,review=v)
    def test_changed_freeze_hash_rejected(self):
        v=copy.deepcopy(self.review);v['artifact_sha256']['data:config/host_inference_stage04_recovery_v9_freeze.json']='0'*64;self.assertRaises(ValueError,self.call,review=v)
    def test_added_unreviewed_file_rejected(self):
        v=copy.deepcopy(self.review);v['artifact_sha256']['data:extra']='e'*64;self.assertRaises(ValueError,self.call,review=v)
    def test_missing_outer_job_review_rejected(self):
        v=copy.deepcopy(self.review);v.pop('outer_job_lifetime_review');self.assertRaises(ValueError,self.call,review=v)
    def test_other_fixture_outer_job_review_rejected(self):
        v=copy.deepcopy(self.review);v['outer_job_lifetime_review']['fixture_sha256']='0'*64;self.assertRaises(ValueError,self.call,review=v)
    def test_old_failure_cannot_be_success_receipt(self):
        v=copy.deepcopy(self.negative);v['ordinary_success_receipt']=True;self.assertRaises(ValueError,self.call,negative=v)
    def test_old_unknown_job_cannot_be_claimed_empty(self):
        v=copy.deepcopy(self.negative);v['original_job_closure']='EMPTY';self.assertRaises(ValueError,self.call,negative=v)
    def test_old_unknown_controller_cannot_be_claimed_zero(self):
        v=copy.deepcopy(self.negative);v['original_controller_outcome']=0;self.assertRaises(ValueError,self.call,negative=v)
    def test_none_native_exit_never_permits_retry(self):
        v=copy.deepcopy(self.negative);v['actual_native_exit']['exit_code_dword']=None;self.assertRaises(ValueError,self.call,negative=v)
    def test_old_native_exitzero_not_negative_retry(self):
        v=copy.deepcopy(self.negative);v['actual_native_exit']['exit_code_dword']=0;self.assertRaises(ValueError,self.call,negative=v)
    def test_actual_current_source_hash_accepted(self):
        key='data:scripts/stage04_recovery_support_v9.py';P.verify_artifacts({key:C.digest(S.ROOT/'scripts/stage04_recovery_support_v9.py')})
    def test_changed_actual_current_source_hash_rejected(self):
        self.assertRaises(ValueError,P.verify_artifacts,{'data:scripts/stage04_recovery_support_v9.py':'0'*64})
    def test_parent_artifact_traversal_rejected(self):self.assertRaises(ValueError,P.verify_artifacts,{'data:../outside':'0'*64})
    def test_parent_unknown_role_rejected(self):self.assertRaises(ValueError,P.verify_artifacts,{'anywhere:C:/outside':'0'*64})
    def test_parent_absolute_path_rejected(self):self.assertRaises(ValueError,P.verify_artifacts,{'data:C:/outside':'0'*64})
    def test_cache_copy_without_actual_messages_rejected(self):self.assertRaises(ValueError,check_cache_log,'checkpoint exists model copied',Path('new/host'))
    def test_old_prefix_cache_message_rejected(self):
        self.assertRaises(ValueError,check_cache_log,'NOTE: Restoring information from model checkpoint file old/host.model.gz\nCHECKPOINT: Tree restored, LogL: -123',Path('new/host'))
    def test_model_load_without_actual_tree_restore_rejected(self):
        self.assertRaises(ValueError,check_cache_log,'NOTE: Restoring information from model checkpoint file '+str(Path('new/host'))+'.model.gz',Path('new/host'))
    def test_exact_new_tool_messages_parse_only(self):
        prefix=Path('new/host');r=check_cache_log('NOTE: Restoring information from model checkpoint file '+str(prefix)+'.model.gz\nCHECKPOINT: Tree restored, LogL: -123',prefix)
        self.assertEqual(r['whole_partition_skip'],'NOT_INFERRED_FROM_PROGRESS_COUNTS')

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Guards);result=unittest.TextTestRunner(verbosity=2).run(suite)
    with C.WorkflowLock(S.LOCK):
        C.atomic(S.REPORT/'guard_tests.json',{'utc':C.now(),'status':'PASS_NARROW_ADOPTION_AND_CACHE_GUARDS' if result.wasSuccessful() else 'FAIL',
          'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'source_sha256':C.digest(__file__),
          'adoption_source_sha256':C.digest(S.ROOT/'scripts/stage04_recovery_controller_v9.py'),'cache_parser_sha256':C.digest(S.ROOT/'scripts/stage04_model_cache_evidence_v9.py'),
          'scientific_jobs':0,'fixture_scope':'Synthetic negative guards and read-only actual source hash check; no scientific PASS'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
