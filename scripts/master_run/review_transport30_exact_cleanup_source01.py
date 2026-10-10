"""C-only source peer of fixed30 retained-handle transport cleanup; no native opens."""
from pathlib import Path
import ast,contextlib,datetime,hashlib,importlib,io,json,runpy,sys,unittest
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
PINS={
 'cleanup_transport30_windows.py':'9c3752316a2c9a7e585d7328c1bb7618e3b12dedbeb212f30bc378375d84aaa7',
 'test_cleanup_transport30_windows.py':'899b03c212e302565a8a8243b13ce7450ec844c811f49952b809a70539a5daa8',
 'TRANSPORT30_EXACT_RETAINED_CLEANUP_SOURCE01.md':'e76bcd77722318eee54956b53517959e2897af42e76977ef4cfd4f3f05e6d909',
 'transport30_current_requalification01.json':'f3d4b7eaafbf59ace779ab0ab187551e2013774793b441251dcc1894baa8d952',
 'transport30_current_remote_metadata01.json':'7ac947dc70dc64bcd301a72e702ff2e9ce1cef08d6e596e2fd5f7e042c2668e2',
 'stage5_wsl_host_profile_fallback_owner.py':'49596d3e9c0ef684978d0cbb05bc57d97b100f08ab77a7a4ece598abc2221299'}
def main():
 for n,p in PINS.items():R.require(R.sha(W/n)==p,'Frozen cleanup source/proof bytes differ: '+n)
 C=importlib.import_module('cleanup_transport30_windows');proof,rows=C.controls()
 R.require(len(rows)==30 and len(set(C.TARGETS))==30 and sum(r['bytes'] for r in rows)==2048507163,'Exact literal transport scope differs')
 tree=ast.parse(R.data(W/'cleanup_transport30_windows.py'))
 functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
 purge=functions['purge_exact'];body=purge.body
 first=next(i for i,n in enumerate(body) if isinstance(n,ast.For) and 'native.hash' in ast.unparse(n))
 effect=next(i for i,n in enumerate(body) if isinstance(n,ast.For) and 'native.mark_delete' in ast.unparse(n))
 R.require(first<effect and 'native.close(handle)' in ast.unparse(body[effect]) and 'absent(' in ast.unparse(body[effect]),'All payload verification before retained disposition/close/absence changed')
 native=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeLeaves')
 opening=next(n for n in native.body if isinstance(n,ast.FunctionDef) and n.name=='open')
 sharing=next(n.value for n in opening.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sharing' for t in n.targets))
 R.require(ast.unparse(sharing)=='3 if directory else 0','Ancestor delete sharing or exclusive leaf sharing changed')
 suite=unittest.defaultTestLoader.loadTestsFromName('test_cleanup_transport30_windows');result=unittest.TextTestRunner(verbosity=1).run(suite)
 R.require(result.wasSuccessful() and result.testsRun==14,'Focused exact target/ownership/effect/finalizer tests failed')
 cap=io.StringIO();old=sys.argv;sys.argv=['cleanup_transport30_windows.py']
 try:
  with contextlib.redirect_stdout(cap):
   try:runpy.run_path(str(W/'cleanup_transport30_windows.py'),run_name='__main__')
   except SystemExit as e:R.require(e.code==0,'Actual-main default NOOP failed')
 finally:sys.argv=old
 R.require(json.loads(cap.getvalue())['effects']==0,'Actual-main default emitted effect')
 for n,p in PINS.items():R.require(R.sha(W/n)==p,'Frozen cleanup bytes changed during peer')
 v={'schema':'MASTER_TRANSPORT30_EXACT_CLEANUP_SOURCE_INDEPENDENT_V1','state':'PASS_SOURCE_ONLY_EXACT30_RETAINED_HANDLE_CLEANUP_ACTUAL_NOT_RUN',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
  'source_sha256':PINS['cleanup_transport30_windows.py'],'focused_pure_fake_tests':14,'actual_main_default_NOOP':'PASS',
  'candidate_files':30,'candidate_logical_bytes':2048507163,'blockers':[],
  'guards':'Exactly fixed ZIP/sidecar leaves and dated full-recovery/current saved asset metadata; original single WorkflowLock; deny-delete ancestor handles plus all30 exclusive retained leaf identities and SHA256 before first effect; durable per-leaf intent/disposition/checked close/exact error2 absence evidence; failed handles/effects retained; original checked unlock/readback precedes exact owned STOP clear and final PASS.',
  'adoption_requirements':['Root must publish/read back exact source and peer, reconcile current remote asset/tag metadata with immutable dated evidence, and hold the original exclusive workflow lock with no active scientific owner.','Actual native identity/sharing compatibility is untested; any mismatch must refuse without effects. Review actual per-leaf effects/close/absence, final original unlock and complete closed scope before reporting reclamation.'],
  'limitations':['180s sampled monotonic checks and4MiB buffers bound observer work between synchronous Win32 calls; no kernel hard timeout is claimed.','No installed package/runtime, image, scientific artifact, directory, process, WSL or Git mutation is authorized by this fixed cleanup source. No actual delete or physical reclamation occurred in this review.'],
  'actual_native_handles_or_cleanup':'NOT_RUN','scientific_adoption':False,'checked_files':R.CHECKED}
 out=W/'transport30_exact_cleanup_source_independent_review01.json'
 with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({'state':v['state'],'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}));return 0
if __name__=='__main__':raise SystemExit(main())
