"""Pure frozen v3 review; no actual future gate reads, request writes or owners."""
import ast
from datetime import datetime, timezone
import hashlib, importlib.util, json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
WORK=Path(__file__).resolve().parent
PREP='b9d7126b6d532a0c9da9dc285ed1ab38240c6ee8aaab5de69d9c1139d5b02269'
prep_path=WORK/'prepare_stage5_first_actual_request_v3_preparation01.json'
assert hashlib.sha256(prep_path.read_bytes()).hexdigest()==PREP
prep=json.loads(prep_path.read_bytes());files={}
for name,pin in prep['source_sha256'].items():
    raw=(WORK/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==pin
    files[name]={'bytes':len(raw),'sha256':pin}
files[prep_path.name]={'bytes':prep_path.stat().st_size,'sha256':PREP}
assert prep['source_sha256']['prepare_stage5_first_actual_request_v3.py']=='cf49f22430a0bfa435491c25ac73494b253acae53aac2ff3b8b910d4a65eaa09'
before=(WORK/'prepare_stage5_first_actual_request_v2.py').read_bytes()
after=(WORK/'prepare_stage5_first_actual_request_v3.py').read_bytes()
replacements={b'stage5_runtime_actual_postiq_07.json':b'stage5_runtime_actual_postiq_08.json',
 b'stage5_setup_toolchain_actual_postiq_06':b'stage5_setup_toolchain_actual_postiq_07',
 b'stage5_setup_runtime_actual_postiq_07':b'stage5_setup_runtime_actual_postiq_08',
 b'Keep the WSL global 4GB memory setting.':b'Keep the WSL global 3GB memory setting.'}
rebuilt=before
for old,new in replacements.items():
    assert rebuilt.count(old)==1
    rebuilt=rebuilt.replace(old,new)
assert rebuilt==after
def functions(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
assert functions(before)==functions(after)
spec=importlib.util.spec_from_file_location('_peer_first_request_v3',WORK/'prepare_stage5_first_actual_request_v3.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
expected={'toolchain':'stage5_setup_toolchain_actual_postiq_07','runtime':'stage5_setup_runtime_actual_postiq_08',
 'interop':'stage5_interop_actual_postiq_05','storage':'stage5_setup_storage_actual_postiq_06',
 'drivefs':'stage5_setup_drivefs_actual_postiq_04','unc':'stage5_unc_bind_actual_postiq_03'}
assert M.GATES==prep['exact_routes']==expected
assert M.CANDIDATES==prep['actual_candidates']=={'runtime_manifest':'stage5_runtime_actual_postiq_08.json','storage_proof':'stage5_storage_actual_postiq_06.json'}
values={}
for node in ast.walk(ast.parse((WORK/'prepare_stage5_first_actual_request.py').read_bytes())):
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Subscript) and isinstance(target.slice,ast.Constant) and target.slice.value in ('native_resource_bytes','resource_basis'):
                values[target.slice.value]=ast.literal_eval(node.value)
assert M.NATIVE_RESOURCE_BYTES==values['native_resource_bytes']
assert M.RESOURCE_BASIS==values['resource_basis'].replace('Keep the WSL global 4GB memory setting.','Keep the WSL global 3GB memory setting.')
assert all(type(value) is int and value>0 for value in M.NATIVE_RESOURCE_BYTES.values())
calls=[ast.unparse(node.func) for node in ast.walk(ast.parse(after)) if isinstance(node,ast.Call)]
assert not any(name in calls for name in ['subprocess.run','subprocess.Popen','os.system','A.WorkflowLock'])
report={'schema':'STAGE05_FIRST_ACTUAL_REQUEST_V3_SOURCE_INDEPENDENT_REVIEW_V1',
 'state':'PASS_FROZEN_SOURCE_SIX_PURE_TESTS_DEFAULT_NOOP_ACTUAL_REQUEST_NOT_RUN',
 'utc':datetime.now(timezone.utc).isoformat(),'source_sha256':prep['source_sha256']['prepare_stage5_first_actual_request_v3.py'],
 'reviewer_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'files':files,'verified_files':len(files),'exact_routes':expected,'exact_candidates':M.CANDIDATES,
 'native_resource_bytes':M.NATIVE_RESOURCE_BYTES,'four_literal_substitutions_reconstruct_exact_v3':True,
 'all_function_asts_identical_to_published_v2':True,'resource_basis_only_global_wsl_ceiling_changed_to3GB':True,
 'tests':{'command':'python -B work/test_prepare_stage5_first_actual_request_v3.py','count':6,'exit_code':0,
   'default_noop_command':'python -B work/prepare_stage5_first_actual_request_v3.py','default_noop_exit_code':0},
 'reviewed_contracts':['Preserved original/v2/template exact byte pins; schema, purpose, first accession, panel and scientific method unchanged.',
  'Exactly four constant substitutions: candidate runtime08, gate toolchain07, gate runtime08 and WSL global3GB basis sentence.',
  'Every function AST remains identical to published v2; exact six fixed routes and no caller-selected old evidence.',
  'Five conservative finite native budgets remain verbatim original; Windows/Linux reserves and fresh admission remain required.',
  'Pure deterministic construction hashes complete candidate/result/unlock bytes and rejects non-PASS or incorrect explicit unlock states.',
  'Explicit prepare keeps bounded plain single-link C reads, final byte reread and exclusive fsynced new output; default reads no actual gates or writes request.'],
 'limitations':['PASS prefix/unlock checks here are preliminary request construction; they do not establish full provenance or admit science.',
  'Unchanged actual config builder and native owner must reopen exact bytes, validate source/closure/current boot/storage/candidate joins and fresh resources.',
  'No future gate/candidate/UNC path was read, no actual request or config built and no native/scientific execution performed.'],
 'actual_operations':{'future_gate_reads':'NOT_RUN','request_write':'NOT_RUN','config_build':'NOT_RUN','native_admission':'NOT_RUN','scientific_execution':'NOT_RUN'},
 'review_actions':{'WSL_launches':0,'UNC_reads':0,'locks':0,'producer_source_edits':0,'Git_ref_writes':0},'remaining_source_blockers':[]}
out=WORK/'prepare_stage5_first_actual_request_v3_independent_review01.json'
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps({'state':report['state'],'review':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'verified_files':len(files)}))
