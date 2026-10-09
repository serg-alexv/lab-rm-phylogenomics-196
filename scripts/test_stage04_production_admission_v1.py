"""Only new admission behavior; no old suite, guest start or biological job."""
import argparse,copy,json,unittest
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_production_admission_policy_v1 as A

class Guards(unittest.TestCase):
    def setUp(self):
        self.outer={'is_process_in_job_null':True,'actual_outer_job':dict.fromkeys(A.FIELDS,0)}
        self.baseline=dict.fromkeys(A.FIELDS,0)
        self.before={'Name':'wslservice.exe','ProcessId':1234,'creation_filetime_microsecond_precision':134359000000000000,
          'CommandLine':None,'ExecutablePath':None}
        self.services=[{'Name':'WSLService','ProcessId':1234,'State':'Running','StartName':'LocalSystem','PathName':'"'+A.CANONICAL+'"'}]
        self.after=[copy.deepcopy(self.before)]
    def service(self):return A.positively_identified_service(self.before,self.services,self.after)
    def test_exact_fixture_static_zero_controls_pass(self):self.assertIsNotNone(A.outer_decision(self.outer,self.baseline))
    def test_dynamic_pids_counts_are_not_compared(self):
        self.outer['actual_outer_job'].update(process_ids=[111,222],active_processes=2)
        self.assertEqual(A.outer_decision(self.outer,self.baseline)['actual_static_controls'],self.baseline)
    def test_each_changed_static_field_rejects(self):
        for key in A.FIELDS:
            value=copy.deepcopy(self.outer);value['actual_outer_job'][key]=1
            with self.subTest(key=key):self.assertRaises(ValueError,A.outer_decision,value,self.baseline)
    def test_missing_static_field_rejects(self):
        self.outer['actual_outer_job'].pop('limit_flags');self.assertRaises(ValueError,A.outer_decision,self.outer,self.baseline)
    def test_boolean_static_value_rejects(self):
        self.outer['actual_outer_job']['limit_flags']=False;self.assertRaises(ValueError,A.outer_decision,self.outer,self.baseline)
    def test_missing_membership_rejects(self):self.assertRaises(ValueError,A.outer_decision,{},self.baseline)
    def test_actual_false_membership_has_no_fabricated_controls(self):
        result=A.outer_decision({'is_process_in_job_null':False,'actual_outer_job':None},self.baseline)
        self.assertIsNone(result['actual_static_controls'])
    def test_false_membership_with_fake_zeros_rejects(self):
        self.outer['is_process_in_job_null']=False;self.assertRaises(ValueError,A.outer_decision,self.outer,self.baseline)
    def test_nonzero_review_baseline_rejects(self):
        self.baseline['affinity_mask']=5;self.assertRaises(ValueError,A.outer_decision,self.outer,self.baseline)
    def test_positive_exact_bracketed_service_role_keeps_unknown_image(self):
        result=self.service();self.assertIsNone(result['before_cim_process']['ExecutablePath']);self.assertFalse(result['configured_binary_is_observed_image'])
    def test_changed_scm_pid_rejects(self):self.services[0]['ProcessId']=5678;self.assertRaises(ValueError,self.service)
    def test_changed_bracketed_creation_rejects(self):self.after[0]['creation_filetime_microsecond_precision']+=10;self.assertRaises(ValueError,self.service)
    def test_changed_bracketed_pid_rejects(self):self.after[0]['ProcessId']=5678;self.assertRaises(ValueError,self.service)
    def test_wrong_service_name_rejects(self):self.services[0]['Name']='OTHER';self.assertRaises(ValueError,self.service)
    def test_wrong_process_basename_rejects(self):self.before['Name']='wsl.exe';self.assertRaises(ValueError,self.service)
    def test_wrong_account_rejects(self):self.services[0]['StartName']='wheel';self.assertRaises(ValueError,self.service)
    def test_wrong_configured_path_rejects(self):self.services[0]['PathName']=r'C:\elsewhere\wslservice.exe';self.assertRaises(ValueError,self.service)
    def test_nonrunning_service_rejects(self):self.services[0]['State']='Stopped';self.assertRaises(ValueError,self.service)
    def test_absent_association_rejects(self):self.services=[];self.assertRaises(ValueError,self.service)
    def test_ambiguous_association_rejects(self):self.services*=2;self.assertRaises(ValueError,self.service)
    def test_unreadable_python_remains_blocked(self):
        self.assertRaises(ValueError,A.classify_inventory,{'before':[{'Name':'python.exe','CommandLine':None}],'services':[],'after':[]})
    def test_unreadable_wsl_launcher_remains_blocked(self):
        self.assertRaises(ValueError,A.classify_inventory,{'before':[{'Name':'wsl.exe','CommandLine':None}],'services':[],'after':[]})
    def test_basename_only_exemption_rejected(self):
        self.assertRaises(ValueError,A.classify_inventory,{'before':[self.before],'services':[],'after':self.after})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--actual-read-only-output');a=parser.parse_args()
    if a.actual_read_only_output:
        target=Path(a.actual_read_only_output);C.check(target.is_relative_to(S.RUNTIME),'Read-only evidence must spool on stable C')
        inventory=A.fresh_runner_inventory();C.check(not inventory['matching_scientific_candidates'],'Other matching runner during new guard readback')
        value={'utc':C.now(),'status':'ACTUAL_FRESH_BRACKETED_SERVICE_ROLE_QUERY_COMPLETED_NO_SCIENCE',
          'inventory':inventory,'policy_source_sha256':C.digest(A.__file__),'script_sha256':C.digest(__file__),
          'biological_jobs':0,'lifetime_fixture_repeated':False,'old_suites_repeated':0}
        C.atomic(target,value);return
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guards))
    with C.WorkflowLock(S.LOCK) as lock:
        S.held_lock_matches_negative(lock)
        C.atomic(S.REPORT/'production_admission_v1_guard_tests.json',{'utc':C.now(),
          'status':'PASS_NEW_ADMISSION_ONLY_GUARDS' if result.wasSuccessful() else 'FAIL',
          'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
          'test_source_sha256':C.digest(__file__),'policy_source_sha256':C.digest(A.__file__),
          'old_suites_repeated':0,'lifetime_fixture_repeated':False,'biological_jobs':0})
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':main()
