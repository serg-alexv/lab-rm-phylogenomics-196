"""Independent C-only frozen paired storage recovery source review; no owner calls."""
from pathlib import Path
import ast,datetime,hashlib,importlib,json,sys,unittest
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
PINS={
 'stage5_setup_storage_recovery_linux.py':'edac2a12a8b1a72d2224264ad4913a79677168dc233ca796c733112b8e32fd8a',
 'stage5_setup_storage_recovery_windows.py':'bdc7b95781950be54bd339c483f31bb8462b5b41ad76bbe21bb5fe37ccdcb7fa',
 'test_stage5_setup_storage_recovery.py':'00c8f5c19b37f14238fe106a8b04c9eecd12ae30a6de5f5b99748ae87cc92a79',
 'STAGE05_STORAGE_PREPARED_RECOVERY_SOURCE01.md':'ae6fd9fd30831b85211145d73ea1383f4df3f1199e09b5adc01671f474c402f1',
 'stage5_setup_linux.py':'24aab72b74dd0aab6c58cac4951c30e6b1bfc9462460486748b546e50ec92e27',
 'stage5_setup_windows.py':'6aa21e4c43c3708abaea3d9fd07913222dee59d52093ddf96a24cddc6a205832',
 'stage5_first_capacity02_closed_independent_review.json':'e7cb6737c50e35c3119fe443d820b77174b2e0b8f3560c5303837b95e42ac2e9',
 'stage5_capacity02_closed_native_copy/snapshot.json':'451c91caaf07d441452c4fccfaf3dfab5c488ee2b8b9988ee35cb0ceb9ac0f51'}
def funcs(raw):
 return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def main():
 out=W/'stage5_storage_prepared_recovery_source_independent_review01.json'
 R.require(not out.exists(),'Fresh independent source report required')
 for n,pin in PINS.items():R.require(R.sha(W/n)==pin,'Frozen byte pin differs: '+n)
 prep=R.read(W/'stage5_storage_prepared_recovery_source_preparation01.json')
 for n,v in prep['files'].items():R.require(R.sha(W/n)==v['sha256'] and len(R.data(W/n))==v['bytes'],'Preparation file join differs: '+n)
 R.require(prep['actual_operations']=='NOT_RUN' and prep['scientific_adoption'] is False,'Preparation scope differs')
 for stem,allowed in [('linux',{'main','toolchain_observe','verified_toolchain'}),('windows',{'main','exact_preexec_failure'})]:
  a=funcs(R.data(W/('stage5_setup_'+stem+'.py')));b=funcs(R.data(W/('stage5_setup_storage_recovery_'+stem+'.py')))
  R.require(all(k in b and b[k]==v for k,v in a.items() if k not in allowed),'Original standalone function changed: '+stem)
  R.require({k for k in a if a[k]!=b[k]}==allowed,'Unexpected original function delta: '+stem)
 sys.path.insert(0,str(W));S=importlib.import_module('stage5_setup_storage_recovery_windows')
 for n,pin in S.PINS.items():R.require(R.sha(W/n)==pin,'Windows original/recovery source dependency differs: '+n)
 F,values,entries=S.recovery_read()
 R.require(len(entries)==28 and values['result.json']['state']=='DEFERRED_RESOURCE','Independent actual C-only closed baseline join differs')
 suite=unittest.defaultTestLoader.loadTestsFromName('test_stage5_setup_storage_recovery')
 result=unittest.TextTestRunner(verbosity=1).run(suite)
 R.require(result.wasSuccessful() and result.testsRun==11,'Frozen focused pure/fault tests failed')
 linux=R.data(W/'stage5_setup_storage_recovery_linux.py').decode('utf-8')
 windows=R.data(W/'stage5_setup_storage_recovery_windows.py').decode('utf-8')
 R.require(linux.count("['/usr/bin/mount','--bind'")==1 and 'os.O_NOFOLLOW' in linux and 'recovery_member_check' in linux and 'supervisor.prelaunch_check' in linux,'Single bind/bounded fresh topology guard differs')
 for token in ('os.unlink(','.unlink(','.rmdir(','.rename(','.replace('):R.require(token not in linux,'Unexpected Linux mutation API: '+token)
 R.require(windows.index("lock.__exit__(None,None,None)")<windows.index("result['lock_release_receipt_sha256']")<windows.index('stop.unlink()'),'Checked unlock receipt/STOP order differs')
 for n,pin in PINS.items():R.require(R.sha(W/n)==pin,'Frozen bytes changed during review: '+n)
 report={'schema':'STAGE05_STORAGE_PREPARED_RECOVERY_SOURCE_INDEPENDENT_V1',
  'state':'PASS_SOURCE_ONLY_PRESERVED_PREPARED_BACKING_RECOVERY_PAIR_ACTUAL_NOT_RUN',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
  'source_sha256':PINS['stage5_setup_storage_recovery_windows.py'],'linux_source_sha256':PINS['stage5_setup_storage_recovery_linux.py'],
  'focused_pure_and_fault_tests':11,'both_actual_main_default_NOOP':'PASS',
  'independent_actual_C_closed_baseline_read':'PASS_28_FILES_NO_WSL_OR_UNC_READ',
  'original_standalone_AST_deltas':{'linux':['main','toolchain_observe','verified_toolchain'],'windows':['main','exact_preexec_failure']},
  'preserved_scientific_identity_and_execution_freeze':True,'full_backing_members':52,'accession_members':50,
  'guards':'Exact actual closed peer/snapshot/source pins; fresh Linux UUID/inode/full membership and regular-byte hashes before admission, immediately before one unchanged bind, and after; projected old Windows UID/GID/mode never treated as POSIX truth; fresh Linux metadata recorded. Original supervisor/native single-command/retained-client closure/resource/lock/authority guards retained. Checked unlock and read-back receipt precede exact owned STOP clear and PASS.',
  'limitations':['Actual fresh prepared-storage recovery and future UNC visibility have not run. Dedicated actual C reader and builder adapter required.','Metadata/hash comparison relies on the single authorized original workflow lock and exact topology; no atomic snapshot guarantee against arbitrary external concurrent writers.','Complete closed-scope Linux/retained Windows evidence and candidate proof required after actual bind; no detector or scientific adoption authorized.'],
  'blockers':[],'actual_operations':'NOT_RUN','scientific_adoption':False,'checked_files':R.CHECKED}
 with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({'state':report['state'],'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}));return 0
if __name__=='__main__':raise SystemExit(main())
