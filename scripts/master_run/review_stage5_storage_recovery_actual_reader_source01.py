"""C-only source peer and synthetic finalization fault checks of actual storage reader."""
from pathlib import Path
from unittest.mock import patch
import copy,datetime,hashlib,importlib,json,tempfile,unittest
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
PINS={
 'review_stage5_storage_recovery_actual.py':'e7788e03c3e4b269c1aa0582973d003f728988bed1297ba18963d542885e824c',
 'test_review_stage5_storage_recovery_actual.py':'cbf657fafa31f7f72ce94b035d44dae22b13aee1a69eedb24d3932865d053d78',
 'STAGE05_STORAGE_RECOVERY_ACTUAL_READER_SOURCE01.md':'714af17e4ae126dfeb9937f6fe89fd0e77ab547e9ea10b0ab00fbd0fc0309081',
 'review_stage5_postboot_gate.py':'d6f06b442c2a8be35bb4779355c99d61e9de72314215c02e3165c2dfd235a161'}
def synthetic_finalization_checks(A,T):
 outcomes=[]
 for case in ('positive','publication','error','final_before_unlock','lease_after_unlock','unlock_hash'):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);(d/'commands').mkdir();pin='1'*64
   before,after,proof,snapshot=T.fixture();boot=proof['boot_id']
   proof.update(target_mount={'filesystem':'ext4'},helper_sha256='w-helper',canonical_target='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/.work/stage05_atomic_v1',backing='/var/tmp/lab_rm_stage05_atomic_v1')
   owner={'executable':A.G.PYTHON,'creation_filetime':1,'pid':1};nonce='test'
   value={'state':'PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK','step':'storage','source_sha256':A.WINDOWS_SHA,'linux_source_sha256':A.LINUX_SHA,
    'owned_closure_proven':True,'unknown_closure_stop_preserved':False,'source_pins':{},'workflow_lock':{},'actual_windows_owner':owner,'owner_nonce':nonce,
    'wsl_exit_receipt_sha256':pin,'actual_wsl_exit':{},'linux_terminal_sha256':pin,'g_underlay_before':{},'g_underlay_after':{},
    'original_lock_explicitly_released':True,'original_unlock_receipt_proven':True,'owned_stop_cleared_after_unlock':True,'lock_release_receipt_sha256':pin,'utc':'2026-10-10T01:00:02+00:00'}
   client={'owner_nonce':nonce,'step':'storage','source_sha256':A.WINDOWS_SHA,'linux_source_sha256':A.LINUX_SHA,'argv':[],'birth':{},'terminal':{},'stdout_sha256':pin,'stderr_sha256':pin}
   linux={'bootstrap':{'boot_id':boot},'state':'PASS_NONSCIENTIFIC_SETUP_STEP','step':'storage','source_sha256':A.LINUX_SHA,'owner_nonce':nonce,
    'owned_closure_proven':True,'remaining_direct_children':[],'owned_command_count':0,'candidate_path':'candidate.json','candidate_sha256':pin,
    'storage':proof,'prepared_backing_recovery_before':before,'prepared_backing_recovery_after':after}
   docs={'actual_owner_lock.json':{'workflow_lock':{},'owner':owner,'owner_nonce':nonce},'launch.json':{'owner_nonce':nonce,'argv':[],'native_wsl_client':{}},
    'wsl_exit.json':client,'linux_terminal.json':linux,'candidate.json':proof,'snapshot.json':snapshot,
    A.CLOSURE_REVIEW:{'owned_closure_proven':True,'original_lock_explicitly_released':True,'native_launch_count':0,'actual_boot_id':A.OLD_BOOT,'snapshot_receipt_sha256':A.SNAPSHOT_SHA},
    'lock_released.json':{'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED','released':True,'utc':'2026-10-10T01:00:01+00:00'},
    'owner_lease.json':{'workflow_lock':{},'nonce':nonce,'workflow_lock_held':False,'expires_unix':1,'measured_unix':1,'owner_pid':1,'owner_creation_filetime':'1','utc':'2026-10-10T01:00:00+00:00'}}
   if case=='publication':(d/'publication_failure.json').write_text('{}')
   if case=='error':value['handle_close_error']={}
   if case=='final_before_unlock':value['utc']='2026-10-10T01:00:00+00:00'
   if case=='lease_after_unlock':docs['owner_lease.json']['utc']='2026-10-10T01:00:03+00:00'
   if case=='unlock_hash':value['lock_release_receipt_sha256']='2'*64
   def read(path):return copy.deepcopy(docs[Path(path).name])
   failed=False
   with patch.object(A,'read',side_effect=read),patch.object(A,'pinned',side_effect=lambda p,*_:read(p)),patch.object(A,'sha',return_value=pin),patch.object(A,'lock',return_value=None),patch.object(A,'terminal',return_value=None),patch.object(A,'cpath',return_value=d/'candidate.json'),patch.object(A.G,'source',return_value='w-helper'):
    try:A.storage(d,value,{},0,boot)
    except ValueError:failed=True
   R.require(failed is (case!='positive'),'Synthetic storage finalization branch failed: '+case)
   outcomes.append({'case':case,'expected':'PASS' if case=='positive' else 'REJECT','observed':'REJECT' if failed else 'PASS'})
 return outcomes
def main():
 for n,p in PINS.items():R.require(R.sha(W/n)==p,'Frozen reader byte pin differs: '+n)
 prep=R.read(W/'stage5_storage_recovery_actual_reader_source_preparation01.json')
 for n,v in prep['files'].items():R.require(R.sha(W/n)==v['sha256'] and len(R.data(W/n))==v['bytes'],'Preparation exact file join differs')
 A=importlib.import_module('review_stage5_storage_recovery_actual');T=importlib.import_module('test_review_stage5_storage_recovery_actual')
 R.require(A.native is A.G.native and A.lock is A.G.lock and A.terminal is A.G.terminal,'Original immutable closure helpers not reused')
 peer=A.source_review('d395278a500c49ba4e0c545a017229b419e2b8e3d49eb07edecbf5275245d76f')
 R.require(peer['state']=='PASS_SOURCE_ONLY_PRESERVED_PREPARED_BACKING_RECOVERY_PAIR_ACTUAL_NOT_RUN','Exact original source peer acceptance differs')
 suite=unittest.defaultTestLoader.loadTestsFromModule(T);result=unittest.TextTestRunner(verbosity=1).run(suite)
 R.require(result.wasSuccessful() and result.testsRun==8,'Frozen reader focused pure tests failed')
 extra=synthetic_finalization_checks(A,T)
 for n,p in PINS.items():R.require(R.sha(W/n)==p,'Reader/source drift during peer')
 v={'schema':'STAGE05_STORAGE_RECOVERY_ACTUAL_READER_SOURCE_INDEPENDENT_V1','state':'PASS_SOURCE_ONLY_STORAGE_ACTUAL_READER_ORIGINAL_CLOSURE_AND_FULL_PRESERVATION_JOINS',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
  'source_sha256':PINS['review_stage5_storage_recovery_actual.py'],'focused_pure_tests':8,'independent_finalization_cases':extra,
  'actual_main_default_NOOP':'PASS','original_d6f06_lock_terminal_native_helpers_identical':True,
  'exact_current_producer_source_peer':'d395278a500c49ba4e0c545a017229b419e2b8e3d49eb07edecbf5275245d76f',
  'guards':'Exact pair/source peer and closed e7cb/451c baseline; unchanged generic native/retained-client/source/boot/lock joins; complete52-object hashes/types/inodes/freshPOSIX metadata and current ext4 proof; zero content/science actions; inactive lease then checked unlock/readback then final PASS; finalizer/publication failures veto.',
  'blockers':[],'actual_storage_recovery_or_review':'NOT_RUN','scientific_adoption':False,'checked_files':R.CHECKED}
 out=W/'stage5_storage_recovery_actual_reader_source_independent_review01.json'
 with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({'state':v['state'],'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}));return 0
if __name__=='__main__':raise SystemExit(main())
