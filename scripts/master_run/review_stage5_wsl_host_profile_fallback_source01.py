"""Independent C-only source review. Never invokes the maintenance owner."""
from pathlib import Path
import ast, contextlib, hashlib, importlib, io, json, runpy, sys, unittest
from datetime import datetime, timezone
sys.dont_write_bytecode=True
WORK=Path(__file__).resolve().parent
PINS={
 'stage5_wsl_host_profile_fallback_owner.py':'49596d3e9c0ef684978d0cbb05bc57d97b100f08ab77a7a4ece598abc2221299',
 'test_stage5_wsl_host_profile_fallback_owner.py':'9336b40b83ac6adf7ea9cd57436d8a8fda4a07ed6ec76901ee29c99026ab0135',
 'stage5_wsl_host_profile_before_fallback01.txt':'df394745d9cc85d8f4340e10b4620711b1ee497cadfb74199bb59288abc967db',
 'STAGE05_WSL_HOST_PROFILE_FALLBACK_PREPARATION01.md':'b5af97a4251294b4379e83c4ba45a41a3288c1b7ed4d105623da6ade81f49de1',
 'stage5_wsl_host_profile_fallback_source_preparation01.json':'6210d8932e232a85edab4b8c24ef801f09f3d5dbd193413f8c0670dbf6b06f6c',
 'stage5_wsl_host_profile_owner.py':'3e6c78c08265157b892a341087780f29dee58c5281d41f0fe49f6ff534248232',
 'stage5_wsl_config_owner.py':'4a6b42b11d63b7b41cba143cc0c5f5f3e0bf874ef09878ed0c0d6e805226f2bd',
 'stage5_closed_genome_archive_windows_checked_unlock_v2.py':'f0d3456dbfd02fa46e127f9dc93f8da7083cd777380561031de8c565cde738e4',
}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(value,message):
 if not value:raise ValueError(message)
def dump(node):return ast.dump(node,include_attributes=False)
def function(tree,name):return next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
def native_calls(tree):
 owner=function(tree,'windows_main')
 return [dump(x) for x in ast.walk(owner) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='run']
def main():
 checked={}
 for name,pin in PINS.items():
  raw=(WORK/name).read_bytes();need(sha(raw)==pin,'Frozen source packet differs: '+name)
  checked[name]={'bytes':len(raw),'sha256':pin}
 sys.path.insert(0,str(WORK))
 M=importlib.import_module('stage5_wsl_host_profile_fallback_owner')
 module=importlib.import_module('test_stage5_wsl_host_profile_fallback_owner')
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
 need(result.wasSuccessful() and result.testsRun==11,'Focused pure test failure: '+stream.getvalue())
 old=ast.parse((WORK/M.PRESERVED_SOURCE).read_bytes());new=ast.parse((WORK/'stage5_wsl_host_profile_fallback_owner.py').read_bytes())
 standalone=['need','digest','load_base','profile_identity','profile_read','failed_gate']
 nested=['snapshot','lease','save','finish_client','run']
 for name in standalone:need(dump(function(old,name))==dump(function(new,name)),'Standalone original function changed: '+name)
 for name in nested:need(dump(function(function(old,'windows_main'),name))==dump(function(function(new,'windows_main'),name)),'Retained owner helper changed: '+name)
 need(native_calls(old)==native_calls(new) and len(native_calls(new))==5,'Original fixed five-client phase invocations changed')
 raw=(WORK/M.PREIMAGE_NAME).read_bytes();after=M.transform_profile(raw)
 need(after==raw.replace(b'memory=3GB\n',b'memory=3584MB\n').replace(b'guiApplications=true\n',b'guiApplications=false\n'),'Profile transform differs')
 previous=sys.argv;sys.argv=['stage5_wsl_host_profile_fallback_owner.py'];capture=io.StringIO()
 try:
  with contextlib.redirect_stdout(capture):
   try:runpy.run_path(str(WORK/'stage5_wsl_host_profile_fallback_owner.py'),run_name='__main__')
   except SystemExit as error:need(error.code==0,'Actual-main NOOP exited nonzero')
 finally:sys.argv=previous
 need(json.loads(capture.getvalue())=={'state':'PREPARED_NOT_RUN','WSL_launches':0,'profile_changes':0,'shutdowns':0},'Actual-main default NOOP differs')
 for name,pin in PINS.items():need(sha((WORK/name).read_bytes())==pin,'Source changed during independent review')
 report={'schema':'STAGE05_WSL_HOST_PROFILE_FALLBACK_INDEPENDENT_SOURCE_REVIEW_V1',
  'state':'PASS_SOURCE_ONLY_BOUNDED_3584MB_GUI_OFF_FALLBACK_ACTUAL_NOT_RUN','utc':datetime.now(timezone.utc).isoformat(),
  'checked_files':checked,'reviewer_source_sha256':sha(Path(__file__).read_bytes()),'pure_tests_passed':11,
  'actual_main_default_noop':'PASS','original_functions_ast_identical':standalone,'original_retained_owner_helpers_ast_identical':nested,
  'original_five_retained_phase_invocations_ast_identical':True,
  'profile':{'before_bytes':len(raw),'before_sha256':sha(raw),'after_bytes':len(after),'after_sha256':sha(after),
   'memory_maximum_bytes':3758096384,'gui_applications':False,'other_bytes_exactly_preserved':True,
   'incremental_resident_host_memory':'NOT_ASSUMED_REQUIRES_ACTUAL_MEASUREMENT'},
  'prerequisite':{'fixed_peer':M.CLOSURE_PEER,'explicit_exact_peer_sha256_required':True,
   'expected_state':'PASS_CAPACITY02_NATURAL_ADMISSION_DEFER_NO_NATIVE_SCOPE_CLOSED_AND_ORIGINAL_UNLOCK',
   'actual_capacity02_closure':'PENDING_NOT_GENERATED_OR_ASSUMED','prepared_scientific_identity_and_execution_data':'PRESERVED',
   'checked_file_map_reopened':True,'strict_original_lock_and_retained_owner_client_birth_argv_exit75':'REQUIRED'},
  'closure_boundary':'Retained Windows clients only; fixed census has no external child commands. No Linux worker or relaunch.',
  'finalization':'Checked original unlock and durable/readback receipt precede exact owned STOP removal; final publication uncertainty stays FAILED with a bounded separate receipt.',
  'scientific_adoption':False,'actual_operations':'NOT_RUN_NO_WSL_UNC_PROFILE_OS_LOCK_REGISTRY_NATIVE_PROCESS_OR_GIT_EFFECTS',
  'required_after_actual_restart':'ALL_FRESH_TOOLCHAIN_RUNTIME_INTEROP_G_STORAGE_DRIVEFS_UNC_GATES_AND_CURRENT_BOOT_JOINS',
  'blockers':[],'actual_integration':'NOT_RUN_REQUIRES_PUBLISHED_SOURCE_EXACT_ACTUAL_CLOSURE_PEER_AND_ROOT_CONTROLLED_USE'}
 output=WORK/'stage5_wsl_host_profile_fallback_source_independent_review01.json'
 with output.open('x',encoding='utf-8',newline='\n') as target:json.dump(report,target,indent=2);target.write('\n')
 print(json.dumps({'state':report['state'],'report':str(output),'sha256':sha(output.read_bytes()),'checker_sha256':sha(Path(__file__).read_bytes())}))
 return 0
if __name__=='__main__':raise SystemExit(main())
