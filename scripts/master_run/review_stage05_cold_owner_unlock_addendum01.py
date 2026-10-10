"""Pure AST addendum for frozen cold-source STOP/unlock ordering."""
from pathlib import Path
import ast, datetime, hashlib, json
import review_stage5_postboot_gate as R
WORK=Path(__file__).resolve().parent
old=R.pinned(WORK/'stage05_cold_owner_source_independent_review01.json','53390992b3787fe39cae4415e00804ad40532adaf910c5a57fb369dfc735aef0')
source=WORK/'stage5_setup_cold_windows.py';R.require(R.sha(source)=='e81ca9b5f2b3402b1fa983270bf32fe60b16cdf2b1c4d1c9f043bf7164c4a2d1','Cold frozen source drift')
api=WORK/'atomic_iqtree_windows.py';R.require(R.sha(api)=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827','Frozen original lock API drift')
tree=ast.parse(R.data(source));owner=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cold_main')
scope=next(n for n in owner.body if isinstance(n,ast.With) and 'A.WorkflowLock' in ast.unparse(n.items[0].context_expr))
clear=[n for n in ast.walk(scope) if isinstance(n,ast.Call) and ast.unparse(n.func)=='STOP.unlink']
R.require(len(clear)==1 and clear[0].lineno==733,'Frozen cold STOP-clear location differs')
following=[n for n in owner.body if getattr(n,'lineno',0)>scope.end_lineno]
R.require(any("'lock_released.json'" in ast.unparse(n) for n in following),'Explicit unlock receipt not outside scope')
api_tree=ast.parse(R.data(api));lock=next(n for n in api_tree.body if isinstance(n,ast.ClassDef) and n.name=='WorkflowLock')
exit_=next(n for n in lock.body if isinstance(n,ast.FunctionDef) and n.name=='__exit__')
R.require('msvcrt.locking' in ast.unparse(exit_) and 'self.released = True' in ast.unparse(exit_),'Original explicit unlock implementation differs')
report={'schema':'STAGE05_COLD_OWNER_SOURCE_UNLOCK_ADDENDUM_V1',
 'state':'BLOCKED_ADDITIONAL_STOP_UNLOCK_ORDER_CORRECTION_REQUIRED_ACTUAL_NOT_RUN',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'prior_blocked_peer_sha256':'53390992b3787fe39cae4415e00804ad40532adaf910c5a57fb369dfc735aef0',
 'frozen_windows_source_sha256':R.sha(source),'reviewer_source_sha256':R.sha(Path(__file__)),
 'finding':{'priority':'P1','file':'stage5_setup_cold_windows.py','line':733,
   'problem':'Owned STOP is cleared and PASS state persisted inside the original WorkflowLock context before explicit OS unlock can succeed.',
   'failure_path':'If original WorkflowLock.__exit__ raises during msvcrt.LK_UNLCK, the owner leaves an already-cleared STOP and persisted PASS result, with no explicit unlock receipt. This contradicts its claimed fail-closed maintenance lifecycle.',
   'evidence':'AST locates STOP.unlink at733 inside with A.WorkflowLock; result write inside finally precedes context exit; lock_released receipt lies after context. Exact pinned A.__exit__ performs the OS unlock before released=True and may raise.',
   'required_correction':'Retain owned STOP through checked original WorkflowLock exit; persist explicit unlock receipt, then permit STOP clear and finalPASS only when native/WSL/guard/RW restoration and unlock all passed. Unlock failure must remain FAILED with durable ownedSTOP.'},
 'prior_three_findings':'UNCHANGED: exact s_state1; honest parent+worker allocation; strict terminal owned_command_count int',
 'actual_operations':'NOT_RUN','producer_source_edits':0,'scientific_execution_or_acceptance':'NONE',
 'checked_files':R.CHECKED}
out=WORK/'stage05_cold_owner_unlock_order_addendum01.json';R.require(not out.exists(),'Preserve previous addendum')
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
print(json.dumps({'state':report['state'],'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
