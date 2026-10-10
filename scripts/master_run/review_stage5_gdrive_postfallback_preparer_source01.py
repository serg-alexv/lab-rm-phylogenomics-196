"""C-only source recipe review; never prepares or invokes an operative G source."""
from pathlib import Path
import ast, contextlib, datetime, hashlib, importlib, io, json, runpy, sys, unittest
sys.dont_write_bytecode=True
W=Path(__file__).resolve().parent
PINS={
 'prepare_stage5_gdrive_postfallback_source.py':'d8fb432cceb2d09e636d154de48b9f18b54a956ab8f2c722b5963f4c21724042',
 'test_prepare_stage5_gdrive_postfallback_source.py':'fe4adf99955873834825ebc45aca41e9634d3cb48883ca701350891f62220ac9',
 'STAGE05_POSTFALLBACK_GATE_ROUTE01.md':'e20da7e952102587e34616c1568542ed638368e4b6d72737c697b780d60e56dd',
 'stage5_postfallback_gate_route_source_preparation01.json':'c3a591f49956f2244ebcee107e857c8740918126f3758156ba8da4f108501a8f',
 'stage5_gdrive_view_postprofile.py':'1ec2380d218128e325954552057ed1215268297862e2910550b2eb7c46a112e9'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(x,message):
 if not x:raise ValueError(message)
def main():
 files={}
 for name,pin in PINS.items():
  raw=(W/name).read_bytes();need(sha(raw)==pin,'Frozen packet differs: '+name);files[name]={'bytes':len(raw),'sha256':pin}
 sys.path.insert(0,str(W));M=importlib.import_module('prepare_stage5_gdrive_postfallback_source')
 T=importlib.import_module('test_prepare_stage5_gdrive_postfallback_source');stream=io.StringIO()
 result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(T))
 need(result.testsRun==4 and result.wasSuccessful(),'Pure tests failed: '+stream.getvalue())
 before=sys.argv;sys.argv=['prepare_stage5_gdrive_postfallback_source.py'];capture=io.StringIO()
 try:
  with contextlib.redirect_stdout(capture):
   try:runpy.run_path(str(W/'prepare_stage5_gdrive_postfallback_source.py'),run_name='__main__')
   except SystemExit as error:need(error.code==0,'Actual-main NOOP failed')
 finally:sys.argv=before
 need(json.loads(capture.getvalue())=={'state':'PREPARED_NOT_RUN','source_written':False,'future_pins':'NOT_GUESSED','WSL_launches':0},'Actual-main NOOP differs')
 pins={M.NEW_DIR+'/'+leaf:format(i+1,'064x') for i,leaf in enumerate(M.LEAVES)}|{M.NEW_REVIEW:'f'*64}
 raw=(W/M.BASE).read_bytes();candidate=M.render(raw,pins)
 # Independently reverse every exact recipe substitution in memory only.
 old=next(ast.literal_eval(n.value) for n in ast.parse(raw).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FRESH_PINS' for t in n.targets))
 restored=candidate.decode()
 for name,pin in old.items():
  fresh=name.replace(M.OLD_DIR,M.NEW_DIR).replace(M.OLD_REVIEW,M.NEW_REVIEW)
  restored=restored.replace(repr(fresh)+':'+repr(pins[fresh]),repr(fresh)+':'+repr(pin))
 restored=restored.replace(M.NEW_DIR,M.OLD_DIR).replace(M.NEW_REVIEW,M.OLD_REVIEW)
 need(restored.encode()==raw,'Recipe changes extend beyond directory/review/six actual pin substitutions')
 for name,pin in PINS.items():need(sha((W/name).read_bytes())==pin,'Packet changed during review')
 report={'schema':'STAGE05_G_POSTFALLBACK_PREPARER_INDEPENDENT_SOURCE_REVIEW_V1','state':'PASS_SOURCE_ONLY_PIN_RECIPE_OPERATIVE_G_NOT_ADOPTED',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked_files':files,'reviewer_source_sha256':sha(Path(__file__).read_bytes()),
  'pure_tests_passed':4,'actual_main_default_noop':'PASS','independent_exact_byte_reversal':'PASS_IN_MEMORY_SYNTHETIC_FUTURE_PINS_ONLY',
  'actual_future_pins':'NOT_READ_NOT_GUESSED','actual_derived_G_source':'NOT_GENERATED','actual_G_operation':'NOT_RUN',
  'fresh_guard':'Exactly actual08 five receipts plus independent peer, explicit proof/review SHA, unchanged fresh_toolchain_gate, genuinely new boot and final input recheck required before exclusive fsynced source output.',
  'operative_lifecycle_boundary':'Recipe intentionally preserves original G1ec STOP-before-unlock behavior. Separate reviewed checked-unlock and durable receipt-before-owned-STOP-clear correction remains required before operative derived G adoption.',
  'other_route_changes':'Populated-backing storage recovery, null-budget UNC preparation and dedicated source-specific gate acceptance remain separate source preparations/actual gates.',
  'source_recipe_blockers':[],'scientific_adoption':False,'effects':'NO_WSL_UNC_G_OS_LOCK_PROCESS_API_GIT_OR_ACTUAL_SOURCE_PREPARATION'}
 out=W/'stage5_gdrive_postfallback_preparer_source_independent_review01.json'
 with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({'state':report['state'],'report':str(out),'sha256':sha(out.read_bytes()),'checker_sha256':sha(Path(__file__).read_bytes())}));return 0
if __name__=='__main__':raise SystemExit(main())
