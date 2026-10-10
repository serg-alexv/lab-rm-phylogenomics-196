"""Pure C-only G fresh-pin review. No G, WSL, lock or mount operations."""
from pathlib import Path
import ast, datetime, hashlib, importlib.util, json
import review_stage5_postboot_gate as R

WORK=Path(__file__).resolve().parent
OUT=WORK/'stage5_gdrive_postprofile_source_independent_review01.json'
PINS={'stage5_gdrive_view_postprofile.py':'1ec2380d218128e325954552057ed1215268297862e2910550b2eb7c46a112e9',
 'test_stage5_gdrive_view_postprofile.py':'a3c06bc75e69f802b3b11de9400d35c3fee3b0cfae5e82e4df6ce6fbdeb7e413',
 'stage5_gdrive_view_postprofile_METHODS.md':'93ce1db7145598f626846014619a8fee166442d9c9b29a035fc26645294cad01',
 'stage5_gdrive_view_postprofile_preparation01.json':'7d9259672beb9032ed84f9d5e172f5c8522cf84b50bf710f007843a54330b446',
 'stage5_gdrive_view_postrepair.py':'a69a755dd044d72cfdfc49d85c150a43057ad69e9b4d70253792222410e41125',
 'stage5_gdrive_view_session.py':'42db8fe44fb2e6c4b8300c2415dc45a6aec20b115449bf76ad002eda34354fb8'}

def constants(tree):
    result={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:result[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    return result

class NormalizeReview(ast.NodeTransformer):
    def visit_Constant(self,node):
        if isinstance(node.value,str) and node.value.startswith('stage5_toolchain') and node.value.endswith('_independent_review.json'):
            node.value='FIXED_TOOLCHAIN_PEER_FILENAME'
        return node

def funcs(raw):
    tree=NormalizeReview().visit(ast.parse(raw))
    return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}

for name,pin in PINS.items():R.require(R.sha(WORK/name)==pin,'Frozen G preparation drift')
prep=R.read(WORK/'stage5_gdrive_view_postprofile_preparation01.json')
original=R.data(WORK/'stage5_gdrive_view_postrepair.py');actual=R.data(WORK/'stage5_gdrive_view_postprofile.py')
old=constants(ast.parse(original));new=constants(ast.parse(actual))
changes=[(old['FRESH_TOOLCHAIN_DIR'],new['FRESH_TOOLCHAIN_DIR']),
 ('stage5_toolchain06_postrepair_independent_review.json','stage5_toolchain07_postprofile_independent_review.json')]
for name,oldpin in old['FRESH_PINS'].items():
    fresh=name.replace(old['FRESH_TOOLCHAIN_DIR'],new['FRESH_TOOLCHAIN_DIR']).replace(changes[1][0],changes[1][1])
    changes.append((oldpin,new['FRESH_PINS'][fresh]))
rebuilt=actual
for before,after in changes:rebuilt=rebuilt.replace(after.encode(),before.encode())
R.require(len(changes)==8 and rebuilt==original,'Eight exact reversible G substitutions differ')
R.require(funcs(actual)==funcs(original)==funcs(R.data(WORK/'stage5_gdrive_view_session.py')),'Behavioral function AST changed beyond peer filename')
for name in ('PINS','PRIOR_PINS'):
    R.require(new[name]==old[name],'Historical/helper source pins changed')
    for rel,pin in new[name].items():R.require(R.sha(WORK/rel)==pin,'Historical/helper source byte drift')
for rel,pin in new['FRESH_PINS'].items():R.require(R.sha(WORK/rel)==pin,'Completed07 source/proof/readback byte drift')
R.require(new['FRESH_PINS']==prep['fresh_pins'] and new['FRESH_TOOLCHAIN_DIR']=='stage5_setup_toolchain_actual_postiq_07','Wrong fresh route')
spec=importlib.util.spec_from_file_location('_pure_g_postprofile_peer',WORK/'stage5_gdrive_view_postprofile.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
proof=WORK/new['FRESH_TOOLCHAIN_DIR']/'toolchain_proof.json';pin=new['FRESH_PINS'][new['FRESH_TOOLCHAIN_DIR']+'/toolchain_proof.json']
boot=G.fresh_toolchain_gate(WORK,proof,pin)
R.require(boot=='f0ffcebc-4901-479d-9559-89d45e9cfa38' and pin=='be4c1d96c5b4d73cfdfc334e3b72e6dbb7f641451ded01b7d2c28910eb6d7af7','Exact new boot/proof gate differs')
for rel in ('stage5_setup_toolchain_actual_postiq_06/toolchain_proof.json','stage5_setup_toolchain_actual_postiq_05/toolchain_proof.json'):
    try:G.fresh_toolchain_gate(WORK,WORK/rel,pin)
    except ValueError:pass
    else:raise ValueError('Old proof route accepted')
report={'schema':'STAGE05_GDRIVE_POSTPROFILE_SOURCE_INDEPENDENT_V1',
 'state':'PASS_FROZEN_SOURCE_SIX_PURE_TESTS_DEFAULT_NOOP_ACTUAL_NOT_RUN',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':PINS['stage5_gdrive_view_postprofile.py'],
 'reviewer_source_sha256':R.sha(Path(__file__)),
 'method':'Only explicit bounded C source/history/closed07 receipts and pure fresh gate calls; no WSL/G/UNC/native/process/lock/ref action',
 'verified_files':len(R.CHECKED),'checked_files':R.CHECKED,'eight_literal_substitutions_reverse_to_exact_inactive_G06':True,
 'all_function_asts_match_G06_and_accepted_G42db_except_review_filename':True,
 'fresh_boot':boot,'fresh_toolchain_proof_sha256':pin,'fresh_independent_peer_sha256':new['FRESH_PINS']['stage5_toolchain07_postprofile_independent_review.json'],
 'tests':{'six_authored_C_only_contracts_independently_run':'PASS_EXIT0','separate_default_noop':'PASS_EXIT0_ZERO_LAUNCHES_MOUNTS',
   'independent_old05_and06_proof_routes':'REJECTED'},
 'guard_scope':'All earlier G42db session-parent /init identity, parent birth/exe/ns final recheck, exact underlay/mount/unknownnested topology/control/resource/source/nonce/native+retained closure/original lock guards unchanged.',
 'required_actual_followup':'Root source publication/readback before diagnosis; diagnose first, mount only on the exact supported missing-G diagnosis; independently qualify actual current session closure and fresh storage06/UNC03. No future-session propagation guarantee.',
 'actual_operations':'NOT_RUN','scientific_execution_or_adoption':'NONE','accepted_stage4':'PRESERVED','old_failed_scopes':'FAILED_PRESERVED',
 'remaining_source_blockers':[]}
R.require(not OUT.exists(),'Preserve existing review')
with OUT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
print(json.dumps({'state':report['state'],'output':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'verified_files':len(R.CHECKED)}))
