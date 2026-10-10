"""C-only source peer of the narrow storage source-pair builder adaptation."""
from pathlib import Path
import ast,datetime,hashlib,importlib,json,sys,unittest
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
PINS={
 'stage5_build_storage_recovery_actual_config.py':'f53b85c860d33df4e2d387d0b4589086f09dc4e512eea293f5062ae87da5195f',
 'test_stage5_build_storage_recovery_actual_config.py':'1f9a4d0bc278a899fda8b179bd0f9d10c2348565700f57ebab73c8859f432865',
 'STAGE05_STORAGE_RECOVERY_BUILDER_SOURCE01.md':'e9d46d92c521dd8d8e1dae890b27f2f8b6679094d82bf7ce8fef3ea4fef7dc64',
 'stage5_build_backing_actual_config.py':'e1b7b4782be7cb4faa84cf546884075e860d2d010a1774ba7d61846bfff7905c',
 'stage5_storage_prepared_recovery_source_independent_review01.json':'d395278a500c49ba4e0c545a017229b419e2b8e3d49eb07edecbf5275245d76f'}
def funcs(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
def main():
 for n,p in PINS.items():R.require(R.sha(W/n)==p,'Frozen builder/source-peer byte pin differs: '+n)
 a=funcs(R.data(W/'stage5_build_backing_actual_config.py'));b=funcs(R.data(W/'stage5_build_storage_recovery_actual_config.py'))
 R.require(a.keys()==b.keys() and {n for n in a if a[n]!=b[n]}=={'checked_gate','main'},'Unexpected builder function delta')
 sys.path.insert(0,str(W));B=importlib.import_module('stage5_build_storage_recovery_actual_config');O=importlib.import_module('stage5_build_backing_actual_config')
 R.require(B.PINS==O.PINS and B.FIELDS==O.FIELDS,'Original source pins or explicit budget fields changed')
 for n,p in {**B.PINS,**B.STORAGE_RECOVERY_PINS}.items():R.require(R.sha(W/n)==p,'Actual pinned helper/template bytes differ: '+n)
 suite=unittest.defaultTestLoader.loadTestsFromName('test_stage5_build_storage_recovery_actual_config')
 result=unittest.TextTestRunner(verbosity=1).run(suite)
 R.require(result.wasSuccessful() and result.testsRun==16,'Focused source routing/budget/negative tests failed')
 for n,p in PINS.items():R.require(R.sha(W/n)==p,'Frozen source changed during peer review')
 v={'schema':'STAGE05_STORAGE_RECOVERY_BUILDER_SOURCE_INDEPENDENT_V1',
  'state':'PASS_SOURCE_ONLY_STORAGE_PAIR_ROUTING_AND_UNCHANGED_SCIENTIFIC_RESOURCE_CONTRACT_ACTUAL_NOT_RUN',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
  'source_sha256':PINS['stage5_build_storage_recovery_actual_config.py'],'focused_pure_tests':16,
  'actual_main_default_NOOP':'PASS','original_functions_changed':['checked_gate','main'],
  'original_PINS_unchanged':True,'explicit_policy_function_AST_identical':True,
  'storage_source_pair':B.STORAGE_RECOVERY_PINS,'six_gate_roles_unchanged':True,
  'guards':'Only storage uses reviewed new pair and exact nonscientific scope, checked unlock/readback pin and owned STOP cleared. Toolchain/runtime/DriveFS require original pair. All originals plus new pair rehashed initially and immediately before build. Existing UNC candidate/storage proof joins, original lock/fresh resources/S.load_config and 1800s admission remain unchanged.',
  'limitations':['Dedicated storage actual peer remains mandatory before selecting its actual gate; this builder checks existing exact result/candidate hashes and does not independently repeat full backing membership audit.','No actual request, gate operation, config build, native detector or scientific adoption occurred. Actual caller must verify existing returned build receipt original unlock and complete fresh admission.'],
  'blockers':[],'actual_operations':'NOT_RUN','scientific_adoption':False,'checked_files':R.CHECKED}
 out=W/'stage5_storage_recovery_builder_source_independent_review01.json'
 with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({'state':v['state'],'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}));return 0
if __name__=='__main__':raise SystemExit(main())
