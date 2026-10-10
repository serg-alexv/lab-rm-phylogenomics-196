"""Independent source-only G08 lifecycle recipe review; no actual preparation."""
from pathlib import Path
from types import SimpleNamespace
import ast, contextlib, datetime, hashlib, importlib, io, json, runpy, sys, tempfile, textwrap, time, unittest
sys.dont_write_bytecode=True
W=Path(__file__).resolve().parent
PINS={
 'prepare_stage5_gdrive_checked_unlock_source.py':'9e4051754c6ba41cedf120771a6dad46d3776537d8a200ee67bf6e6613e87b02',
 'test_stage5_gdrive_checked_unlock_source.py':'b037354e1f442465e771687199bfcad781021090b1f005a9df00603232ffc821',
 'STAGE05_G08_CHECKED_UNLOCK_SOURCE_PREPARATION01.md':'7b22d366f129c152b8ce839debd400ceedb704887c65c6165922c082a5976fd6',
 'prepare_stage5_gdrive_postfallback_source.py':'d8fb432cceb2d09e636d154de48b9f18b54a956ab8f2c722b5963f4c21724042',
 'stage5_wsl_host_profile_fallback_owner.py':'49596d3e9c0ef684978d0cbb05bc57d97b100f08ab77a7a4ece598abc2221299',
 'stage5_gdrive_view_postprofile.py':'1ec2380d218128e325954552057ed1215268297862e2910550b2eb7c46a112e9'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,message):
 if not ok:raise ValueError(message)
def function(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def calls(tree,name):return [ast.dump(n,include_attributes=False) for n in ast.walk(function(tree,'windows_main')) if isinstance(n,ast.Call) and ast.unparse(n.func)==name]
def tail_case(P,candidate,mode):
 with tempfile.TemporaryDirectory(dir=W) as folder:
  out=Path(folder);stop=out/'STOP.json';stop.write_text(json.dumps({'owner_nonce':'peer_fixture'}));events=[]
  for leaf in ('wsl.stdout.txt','wsl.stderr.txt'):(out/leaf).write_bytes(b'')
  namespace={'__name__':'_pure_generated_tail_peer','__file__':str(W/P.OUTPUT)};exec(compile(candidate,P.OUTPUT,'exec'),namespace)
  real_sha=namespace['sha']
  class Lock:
   released=False
   def __exit__(self,*args):
    need(stop.exists(),'STOP removed before checked unlock');events.append('unlock');self.released=True
  class API:
   @staticmethod
   def utc():return '2026-10-10T00:00:00+00:00'
   @staticmethod
   def atomic(path,value):
    if path.name=='lock_released.json':need(stop.exists(),'STOP removed before durable unlock receipt')
    if path.name=='result.json' and mode=='success':need(not stop.exists(),'Successful result precedes STOP clear')
    events.append(path.name);path.write_text(json.dumps(value))
   @staticmethod
   def read_json(path):return json.loads(path.read_bytes())
  class Handle:
   closed=False
   def Close(self):
    events.append('handle_close')
    if mode=='close_exception':raise OSError('Pure fixture Close failure')
    if mode!='close_unproven':self.closed=True
  def digest_path(path):
   if mode=='log_hash_error' and path.name=='wsl.stdout.txt':raise OSError('Pure fixture log read failure')
   return real_sha(path)
  record={'state':P.PENDING};lock=Lock()
  namespace.update(record=record,closed=True,terminal={'exited':True},start=time.monotonic(),A=API,lock=lock,
   out=out,stop=stop,stop_sha=real_sha(stop),nonce='peer_fixture',child=SimpleNamespace(_handle=Handle()),sha=digest_path)
  exec(compile(textwrap.dedent(P.TAIL),'_pure_tail_only','exec'),namespace)
  need(lock.released and record['original_unlock_receipt_proven'] is True,'TAIL skipped checked original unlock receipt')
  need(events.index('handle_close')<events.index('unlock')<events.index('lock_released.json')<events.index('result.json'),'Handle/unlock/receipt/result order changed')
  if mode=='success':need(record['state']==P.PASS and not stop.exists(),'Positive fake TAIL failed')
  else:need(record['state']=='FAILED' and stop.exists() and 'retained_client_finalizer_error' in record and record['owned_stop_cleared_after_unlock'] is False,'TAIL error granted STOP clear/PASS')
  return {'mode':mode,'state':record['state'],'STOP_preserved':stop.exists(),'events':events}
def main():
 checked={}
 for name,pin in PINS.items():
  raw=(W/name).read_bytes();need(sha(raw)==pin,'Frozen source packet differs: '+name);checked[name]={'bytes':len(raw),'sha256':pin}
 sys.path.insert(0,str(W));P=importlib.import_module('prepare_stage5_gdrive_checked_unlock_source');T=importlib.import_module('test_stage5_gdrive_checked_unlock_source')
 output=io.StringIO();result=unittest.TextTestRunner(stream=output,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(T))
 need(result.testsRun==9 and result.wasSuccessful(),'Authored pure tests failed: '+output.getvalue())
 recipe=importlib.import_module('prepare_stage5_gdrive_postfallback_source');base=(W/P.BASE).read_bytes();profile=(W/P.PROFILE).read_bytes()
 pins={recipe.NEW_DIR+'/'+leaf:format(i+1,'064x') for i,leaf in enumerate(recipe.LEAVES)}|{recipe.NEW_REVIEW:'f'*64}
 raw=recipe.render(base,pins);candidate=P.render(raw,base,profile,recipe);old=ast.parse(raw);new=ast.parse(candidate)
 native=['subprocess.Popen','api.identity','S.command_readback','terminal_gate','fresh_toolchain_gate','api.resources']
 for name in native:need(calls(old,name)==calls(new,name),'Existing native/admission/terminal subtree changed: '+name)
 modes=[tail_case(P,candidate,mode) for mode in ('success','close_exception','close_unproven','log_hash_error')]
 capture=io.StringIO();before=sys.argv;sys.argv=['prepare_stage5_gdrive_checked_unlock_source.py']
 try:
  with contextlib.redirect_stdout(capture):
   try:runpy.run_path(str(W/'prepare_stage5_gdrive_checked_unlock_source.py'),run_name='__main__')
   except SystemExit as error:need(error.code==0,'Actual-main default NOOP failed')
 finally:sys.argv=before
 need(json.loads(capture.getvalue())=={'state':'NO_OP_G08_CHECKED_UNLOCK_SOURCE_PREPARATION','source_written':False,'G_invocations':0,'WSL_launches':0},'Actual-main NOOP differs')
 for name,pin in PINS.items():need(sha((W/name).read_bytes())==pin,'Frozen source changed during review')
 report={'schema':'STAGE05_G08_CHECKED_UNLOCK_PREPARER_INDEPENDENT_SOURCE_REVIEW_V1','state':'PASS_SOURCE_ONLY_CHECKED_UNLOCK_RECIPE_ACTUAL_G08_SOURCE_NOT_GENERATED',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked_files':checked,'reviewer_source_sha256':sha(Path(__file__).read_bytes()),
  'authored_pure_tests_passed':9,'actual_main_default_noop':'PASS','independent_native_admission_terminal_AST_subtrees_unchanged':native,
  'independent_complete_fake_TAIL_cases':modes,'non_Windows_G_function_ASTs_and_six_fresh_pins':'UNCHANGED',
  'scope':'Only exact d8fb six-pin output, reviewed49596 finalizer and narrow Windows finalization/return delta. No actual08 receipt reads, derived file generation, WSL/G/UNC/OS-lock/process API/native/Git effects.',
  'actual_generated_source':'NOT_RUN_REQUIRES_REAL08_PROOF_AND_PEER_EXACT_HASHES_INDEPENDENT_SOURCE_PEER_AND_PUBLICATION',
  'finalization':'Retained handle/log errors veto STOP clear and PASS; checked original unlock and durable/readback receipt precede exact owned STOP clear; final publication failure remains failed while preserving proved closure facts.',
  'scientific_adoption':False,'source_recipe_blockers':[]}
 out=W/'stage5_gdrive_checked_unlock_preparer_source_independent_review01.json'
 with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps({'state':report['state'],'report':str(out),'sha256':sha(out.read_bytes()),'checker_sha256':sha(Path(__file__).read_bytes())}));return 0
if __name__=='__main__':raise SystemExit(main())
