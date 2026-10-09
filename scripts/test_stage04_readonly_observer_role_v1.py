"""Focused role rejection fixtures only; no process launch or biological work."""
import copy,hashlib,json,subprocess,unittest
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_readonly_observer_role_v1 as R

class RoleTests(unittest.TestCase):
    def setUp(self):
        xml='<synthetic-observer-definition/>';sha=hashlib.sha256(b'\xff\xfe'+xml.encode('utf-16le')).hexdigest()
        runtime=str(S.RUNTIME/'production/SYNTHETIC');observer=str(S.RUNTIME/'observers/SYNTHETIC')
        self.request={'mode':'observer','protocol':'V10_MANUAL_UNIQUE_ONESHOT_DIRECT_CONTROLLER','executable':str(S.PYTHONW),
          'argv':['-u',str(S.ROOT/'scripts/observe_stage04_recovery_controller_v10.py'),'--runtime',runtime,'--observer-runtime',observer],
          'target_runtime':runtime,'runtime':observer,'definition_sha256':sha,'task_name':'LAB_RM_Stage04_V10_SYNTHETIC'}
        self.argv=[self.request['executable'],*self.request['argv']]
        self.row={'ProcessId':101,'creation_filetime_microsecond_precision':134359800000000000,'CommandLine':subprocess.list2cmdline(self.argv)}
        self.before={'pid':101,'creation_filetime':134359800000000007,'state':'RUNNING','executable':str(S.PYTHONW)};self.after=copy.deepcopy(self.before)
        self.owner={'pid':202,'creation_filetime':134359700000000004};run={'engine_pid':101,'instance_guid':'SYNTHETIC-GUID','state':4}
        self.task={'xml':xml,'runs':[run]}
        self.binding={'controller_binding_sha256':'SYNTHETIC-CONTROLLER-SHA','actual_controller':self.owner,
          'actual_scheduler_observer':{'actual_process':self.before,'runtime':observer,'definition_sha256':sha,'scheduler_instance_guid':'SYNTHETIC-GUID',
          'actual_live_scheduler_binding':{'actual_process_argv':self.argv,'actual_task_definition_sha256':sha,
            'actual_request_sha256':'SYNTHETIC-REQUEST-SHA','actual_live_instance':run}}}
    def check(self):
        return R.check_role(self.row,self.argv,self.request,self.binding,self.task,self.before,self.after,self.owner,
          'SYNTHETIC-CONTROLLER-SHA','SYNTHETIC-REQUEST-SHA')
    def test_exact_role(self):self.assertEqual(self.check()['pid'],101)
    def test_actual_windows_argv_parser(self):self.assertEqual(R.parse_command_line(self.row['CommandLine']),self.argv)
    def test_old_broad_match_demonstrates_concrete_false_positive(self):self.assertIn('recovery_controller',self.row['CommandLine'])
    def test_wrong_pid(self):self.row['ProcessId']=999;self.assertRaises(ValueError,self.check)
    def test_reused_creation(self):self.after['creation_filetime']+=1;self.assertRaises(ValueError,self.check)
    def test_cim_creation_mismatch(self):self.row['creation_filetime_microsecond_precision']-=10;self.assertRaises(ValueError,self.check)
    def test_exited_observer(self):self.after['state']='EXITED';self.assertRaises(ValueError,self.check)
    def test_unknown_native_image(self):self.after['executable']='UNKNOWN';self.assertRaises(ValueError,self.check)
    def test_commandline_extra_arg(self):self.argv=[*self.argv,'--unaccepted'];self.assertRaises(ValueError,self.check)
    def test_wrong_readonly_script(self):self.request['argv'][1]=str(S.ROOT/'scripts/stage04_native_windows_v6.py');self.assertRaises(ValueError,self.check)
    def test_another_controller(self):self.owner={**self.owner,'pid':999};self.assertRaises(ValueError,self.check)
    def test_unbound_controller_sha(self):self.binding['controller_binding_sha256']='WRONG';self.assertRaises(ValueError,self.check)
    def test_wrong_request_sha(self):self.binding['actual_scheduler_observer']['actual_live_scheduler_binding']['actual_request_sha256']='WRONG';self.assertRaises(ValueError,self.check)
    def test_changed_task_definition(self):self.task['xml']='<changed/>';self.assertRaises(ValueError,self.check)
    def test_wrong_engine_pid(self):self.task['runs']=[{**self.task['runs'][0],'engine_pid':999}];self.assertRaises(ValueError,self.check)
    def test_wrong_instance_guid(self):self.task['runs']=[{**self.task['runs'][0],'instance_guid':'OTHER'}];self.assertRaises(ValueError,self.check)
    def test_no_running_instance(self):self.task['runs']=[];self.assertRaises(ValueError,self.check)
    def test_extra_running_instance(self):self.task['runs']=[*self.task['runs'],self.task['runs'][0]];self.assertRaises(ValueError,self.check)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(RoleTests);result=unittest.TextTestRunner(verbosity=1).run(suite)
    C.atomic(S.REPORT/'production_admission_v2_role_tests.json',{'utc':C.now(),'status':'PASS_NEW_EXACT_OBSERVER_ROLE_GUARDS' if result.wasSuccessful() else 'FAILED',
      'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'guard_source_sha256':C.digest(R.__file__),
      'test_source_sha256':C.digest(__file__),'biological_jobs':0,'source_fixture_only':True,'old_suite_or_lifetime_fixture_repeated':False})
    raise SystemExit(0 if result.wasSuccessful() else 1)
