"""Only new direct-target joins and failure-outcome persistence; old18 not rerun."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_readonly_observer_role_v2 as R

class NewJoins(unittest.TestCase):
    def setUp(self):
        self.req={'target_runtime':'SYNTHETIC-TARGET','target_task_name':'SYNTHETIC-TASK','executable_sha256':'SYNTHETIC-EXE'}
        self.proposal={'production_readonly_observer_task':self.req,'production_task':{'runtime':'SYNTHETIC-TARGET','task_name':'SYNTHETIC-TASK',
          'config_sha256':'SYNTHETIC-CONFIG','definition_sha256':'SYNTHETIC-DEFINITION'},'fixed_external_interpreters':[{'path':str(S.PYTHONW),'sha256':'SYNTHETIC-EXE'}],
          'required_review_artifacts':{'data:scripts/observe_stage04_recovery_controller_v10.py':'SYNTHETIC-SOURCE'}}
        self.binding={'controller_config_sha256':'SYNTHETIC-CONFIG','controller_definition_sha256':'SYNTHETIC-DEFINITION','source_sha256':'SYNTHETIC-SOURCE'}
    def check(self):return R.direct_joins(self.proposal,self.binding,self.req,'SYNTHETIC-EXE','SYNTHETIC-SOURCE')
    def test_direct_positive(self):self.assertEqual(self.check()['target_config_sha256'],'SYNTHETIC-CONFIG')
    def test_wrong_target_config(self):self.binding['controller_config_sha256']='OTHER';self.assertRaises(ValueError,self.check)
    def test_wrong_target_definition(self):self.binding['controller_definition_sha256']='OTHER';self.assertRaises(ValueError,self.check)
    def test_wrong_executable_bytes(self):self.req['executable_sha256']='OTHER';self.assertRaises(ValueError,self.check)
    def test_wrong_loaded_source(self):self.binding['source_sha256']='OTHER';self.assertRaises(ValueError,self.check)
    def test_wrong_target_task(self):self.req['target_task_name']='OTHER';self.assertRaises(ValueError,self.check)
    def test_failed_role_preserves_inventory_expected_roles_and_reason(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC_ROLE_GUARD_') as d:
            runtime=Path(d);inventory={'matching_scientific_candidates':[{'ProcessId':303,'CommandLine':'SYNTHETIC-UNKNOWN-RUNNER'}],
              'positive_platform_service_roles':[]}
            with patch.object(R.B.A,'fresh_runner_inventory',return_value=inventory),patch.object(R.B,'observer_proof',side_effect=ValueError('SYNTHETIC_UNKNOWN_THIRD_RUNNER')):
                self.assertRaises(ValueError,R.source_inventory,self.proposal,runtime,{'pid':202})
            self.assertEqual(C.load(runtime/'source_gate_runner_inventory.json'),inventory)
            actual=C.load(runtime/'source_gate_role_outcomes.json')
            self.assertEqual(actual['expected_observer_request'],self.req)
            self.assertEqual(actual['status'],'ROLE_EVALUATION_FAILED_NO_BOUNDARY_CERTIFICATE')
            self.assertEqual(actual['evaluations'][0]['reason'],'SYNTHETIC_UNKNOWN_THIRD_RUNNER')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(NewJoins))
    C.atomic(S.REPORT/'production_admission_v3_direct_join_tests.json',{'utc':C.now(),'status':'PASS_NEW_DIRECT_JOINS_AND_FAILED_ROLE_PERSISTENCE' if result.wasSuccessful() else 'FAILED',
      'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'role_guard_v2_source_sha256':C.digest(R.__file__),
      'test_source_sha256':C.digest(__file__),'biological_jobs':0,'old18_role_guards_or_other_old_suites_repeated':False,'lifetime_fixture_repeated':False})
    raise SystemExit(0 if result.wasSuccessful() else 1)
