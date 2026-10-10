"""C-only exact real08 derived G source joins. No G/WSL owner invocation."""
from pathlib import Path
import ast,contextlib,datetime,hashlib,importlib,io,json,runpy,sys
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
PINS={
 'stage5_gdrive_view_postfallback.py':'087e5c63ef41de34a4a2dfcc969f843ba697cb4a96bca585fa9d53bfabe96373',
 'stage5_gdrive_view_postfallback_checked_unlock.py':'a5efd24a17655324b8a03d13bf74e06f77195cb401ca9db8a3f73f94e1ab8ada',
 'prepare_stage5_gdrive_postfallback_source.py':'d8fb432cceb2d09e636d154de48b9f18b54a956ab8f2c722b5963f4c21724042',
 'prepare_stage5_gdrive_checked_unlock_source.py':'9e4051754c6ba41cedf120771a6dad46d3776537d8a200ee67bf6e6613e87b02',
 'stage5_gdrive_view_postprofile.py':'1ec2380d218128e325954552057ed1215268297862e2910550b2eb7c46a112e9',
 'stage5_wsl_host_profile_fallback_owner.py':'49596d3e9c0ef684978d0cbb05bc57d97b100f08ab77a7a4ece598abc2221299',
 'stage5_gdrive_postfallback_preparer_source_independent_review01.json':'24ef930422e3da925d80456d60b8a3fcc6099a9e8955ad05fff9f3b125c717ea',
 'stage5_gdrive_checked_unlock_preparer_source_independent_review01.json':'fc4c0766caa8b97d26da18ddd54239231084139402b09b3d30487283bcc306d4',
 'stage5_toolchain08_postfallback_independent_review.json':'af62d67c86aa3cfa42a1b24dd82ee2fc4aaa3ce7ae876aadd8a1fe60d078a742'}
BOOT='8cca020a-71b2-4163-92dc-6087df12dd45'
def main():
 for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Frozen source/recipe/peer differs: '+name)
 sys.path.insert(0,str(W));recipe=importlib.import_module('prepare_stage5_gdrive_postfallback_source')
 P=importlib.import_module('prepare_stage5_gdrive_checked_unlock_source')
 base=R.data(W/recipe.BASE);profile=R.data(W/P.PROFILE);pin_source=R.data(W/recipe.OUTPUT);checked=R.data(W/P.OUTPUT)
 pins=P.fresh_pins(pin_source)
 R.require(pins==P.fresh_pins(checked) and set(pins)=={recipe.NEW_DIR+'/'+leaf for leaf in recipe.LEAVES}|{recipe.NEW_REVIEW},'Exact actual six fresh08 pins differ')
 for name,pin in pins.items():R.require(R.sha(W/name)==pin,'Actual fresh08 pinned bytes differ: '+name)
 R.require(pins[recipe.NEW_DIR+'/toolchain_proof.json']=='2c306c3d2dab65cc4da996118ff521506e028cf3fdc0a8ff5d0a891d24b74cdf'
  and pins[recipe.NEW_REVIEW]==PINS[recipe.NEW_REVIEW],'Actual08 proof/peer pins differ')
 R.require(recipe.render(base,pins)==pin_source,'Actual pin-only source extends beyond reviewed deterministic recipe')
 R.require(P.render(pin_source,base,profile,recipe)==checked,'Actual checked source extends beyond reviewed deterministic lifecycle recipe')
 ns={'__name__':'_independent_real08_source_only','__file__':str(W/P.OUTPUT)};exec(compile(checked,P.OUTPUT,'exec'),ns)
 R.require(ns['fresh_toolchain_gate'](W,W/recipe.NEW_DIR/'toolchain_proof.json',pins[recipe.NEW_DIR+'/toolchain_proof.json'])==BOOT,'Pure actual fresh08 toolchain gate differs')
 old_funcs=P.functions(pin_source);new_funcs=P.functions(checked)
 R.require(set(new_funcs)==set(old_funcs)|{'finish_after_unlock'} and all(new_funcs[k]==v for k,v in old_funcs.items() if k!='windows_main'),
  'Linux/session/mount/topology/source/authority/terminal functions changed')
 capture=io.StringIO();old_argv=sys.argv;sys.argv=[P.OUTPUT]
 try:
  with contextlib.redirect_stdout(capture):
   try:runpy.run_path(str(W/P.OUTPUT),run_name='__main__')
   except SystemExit as error:R.require(error.code==0,'Actual derived-source default NOOP failed')
 finally:sys.argv=old_argv
 noop=json.loads(capture.getvalue());R.require(noop['state']=='PREPARED_NOT_RUN' and noop['WSL_launches']==0,'Derived actual source default NOOP differs')
 for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Frozen source/receipt changed during independent review')
 report={'schema':'STAGE05_G08_ACTUAL_DERIVED_SOURCE_INDEPENDENT_REVIEW_V1','state':'PASS_ACTUAL_C_SOURCE_PIN_DERIVATION_AND_CHECKED_UNLOCK_ACTUAL_G_NOT_RUN',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
  'source_sha256':PINS[P.OUTPUT],'pin_only_source_sha256':PINS[recipe.OUTPUT],'actual_boot_id':BOOT,'actual_fresh_toolchain_pins':pins,
  'exact_deterministic_two_recipe_outputs':'PASS','pure_actual_fresh_toolchain_gate':'PASS','actual_main_default_NOOP':noop,
  'all_non_Windows_G_functions_AST_identical':True,'checked_unlock_recipe_peer_sha256':PINS['stage5_gdrive_checked_unlock_preparer_source_independent_review01.json'],
  'retained_client_and_native_contract':'Unchanged G/Linux single-command session-parent, exact mount/control/underlay/source/closure gates; Windows handle/log failures veto STOP clear and PASS, checked original unlock/readback before exact owned STOP removal.',
  'actual_G_diagnosis_or_mount':'NOT_RUN','scientific_adoption':False,
  'next':'Root publishes and verifies exact derived checked source; separate actual diagnosis first, mount only if strict qualified missing mount/empty underlay. Independent actual storage and UNC remain required.'}
 report['checked_files']=R.CHECKED
 out=W/'stage5_gdrive_postfallback_derived_source_independent_review01.json'
 with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps({'state':report['state'],'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}));return 0
if __name__=='__main__':raise SystemExit(main())
