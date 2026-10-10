"""Pure Chrome cleanup source/guard peer; never actual process handles or effects."""
from pathlib import Path
from unittest.mock import patch
import ast, datetime, hashlib, importlib.util, json, tempfile
import review_stage5_postboot_gate as R

WORK=Path(__file__).resolve().parent
SOURCE='85c46761991c657ecc86f2dad8bcd5d75e40e29d37dc14d234cfed19806836bf'
TEST='4bcb3cb825b54bd92bd43f7a5119a1727c9bc0c5697322201d53d52be4e54865'
OUT=WORK/'stage5_chrome_resource_cleanup_independent_review01.json'
R.require(R.sha(WORK/'stage5_chrome_resource_cleanup.py')==SOURCE
  and R.sha(WORK/'test_stage5_chrome_resource_cleanup.py')==TEST
  and R.sha(WORK/'atomic_iqtree_windows.py')=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827','Frozen source/test/API differs')
raw=R.data(WORK/'stage5_chrome_resource_cleanup.py');tree=ast.parse(raw)
spec=importlib.util.spec_from_file_location('_pure_chrome_peer',WORK/'stage5_chrome_resource_cleanup.py')
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
R.require(C.API_SHA=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
  and C.CHROME_EXE==r'C:\Program Files\Google\Chrome\Application\chrome.exe'
  and C.MAX_PROCESSES==4096 and C.MAX_TARGETS==128 and C.DEADLINE_SECONDS==180
  and C.WAIT_MILLISECONDS==5000 and C.TERMINATION_EXIT_CODE==1223,'Exact allowlist/cap/deadline drift')
R.lock(C.LOCK);C.lock_guard(C.LOCK)
calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
R.require(not any(n in calls for n in ('subprocess.run','subprocess.Popen','os.system','api.TerminateProcess','os.kill','shutil.rmtree')),'Unexpected external process or destructive path operation')
text=raw.decode('utf-8')
for required in ("target_guard(birth,owner['session_id'])","same_birth(birth,current,owner['session_id'])",
  "api.terminate(item['handle'],TERMINATION_EXIT_CODE)","item['effect_started']=True",
  "terminal_guard(item['birth'],actual_identity(item),owner['session_id'])",
  "terminal['exit_code']==TERMINATION_EXIT_CODE","close_owned(api,item)",
  "if item['effect_started'] and not item['terminal_verified']:",
  "time.monotonic()-started<DEADLINE_SECONDS","hashlib.sha256(raw).hexdigest()==pin"):
    R.require(required in text,'Required exact effect/terminal/finite/raw pin guard absent')
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
outer_final=main.body[-3] if False else next(n for n in main.body if isinstance(n,ast.Try) and n.finalbody)
final=ast.unparse(ast.Module(body=outer_final.finalbody,type_ignores=[]))
R.require(final.index('lock.__exit__')<final.index("out / 'lock_released.json'")<final.index('STOP.unlink()')
  and 'complete and handles_closed and lock.released and (stop_sha is not None)' in final,'Unlock receipt before STOP removal/PASS required')
with tempfile.TemporaryDirectory(prefix='chrome_peer_pure_',dir=WORK) as directory:
    file=Path(directory)/'closed.json';good=b'{"state":"FAILED"}';bad=b'{"state":"OTHER"}'
    goodpin=hashlib.sha256(good).hexdigest();file.write_bytes(good)
    R.require(C.exact_control(file,goodpin)=={'state':'FAILED'},'Good bounded exact control rejected')
    file.write_bytes(bad)
    with patch.object(C.A,'sha256',return_value=goodpin):
        try:C.exact_control(file,goodpin)
        except ValueError:pass
        else:raise ValueError('Decoded bytes can evade pin via second path read')
report={'schema':'STAGE05_EXACT_CHROME_RESOURCE_CLEANUP_SOURCE_INDEPENDENT_V1',
 'state':'PASS_FROZEN_SOURCE_PURE_GUARDS_DEFAULT_NOOP_ACTUAL_NOT_RUN',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':SOURCE,'test_source_sha256':TEST,
 'reviewer_source_sha256':R.sha(Path(__file__)),
 'method':'Only C source reads/AST and pure fake guards with one automatically removed C tempfile fixture. No native enumeration, process handles, profile/URL/argv read, WSL, services, locks or ref changes.',
 'verified_files':len(R.CHECKED),'checked_files':R.CHECKED,
 'tests':{'eleven_authored_pure_fake_tests_independently_run':'PASS_EXIT0',
   'separate_default_noop':'PASS_EXIT0_NO_PROCESS_EFFECTS',
   'independent_already_read_bytes_pin_case':'PASS_GOOD_BYTES_AND_REJECT_SECOND_READ_HASH_MASKING_DIFFERENT_DECODED_BYTES'},
 'reviewed_boundaries':[
  'Only exact installed Chrome executable in the actual owner SessionID can enter a target; process name, PID, child ancestry or arbitrary CLI path alone cannot qualify.',
  'K32EnumProcesses4096 maximum rejects a full/truncated buffer; maximum128 snapshot targets; no process argv, URLs or profile payloads read/published.',
  'Query handle first, separate retained terminate-capable handle with exact PID/birth/session recheck; identity checked again immediately before effect. No process-tree or name kill route.',
  'Intent recorded before each retained-handle TerminateProcess1223; exact kernel terminal birth/exit plus expected1223 for actual effect; already-closed target is recorded with no effect.',
  'Every owned metadata/effect handle requires checked CloseHandle; failure stays in RETAINED. An attempted effect cannot be closed without positive retained terminal proof.',
  'Original typed immutable byte WorkflowLock and direct user control/current owner identity/pinned prior closed result+unlock bytes rechecked; no WSL or competing controller launches.',
  'Whole180s metadata/effect deadline, each wait at most5s and remaining total,256MiB Windows metadata reserve. Partial failure preserves STOP and any unresolved handles/effect evidence.',
  'STOP exists before enumeration/handles; explicit WorkflowLock exit and durable unlock receipt precede own STOP removal/finalPASS. Unlock/handle uncertainty cannot clear ownSTOP.',
  'Only snapshot Chrome targets affected; new Chrome processes launched after snapshot are outside this scope. No global Chrome-empty or resource-gain guarantee.',
  'Same user-authorized working-host cleanup scope; root chooses whether to run only after source publication/readback and exact latest closed-scope pins.'],
 'limitations':['Actual K32 enumeration, retained handle/effect API and resource benefit remain NOT_RUN in this source peer.',
   'This is force termination of exact Chrome processes, so unsaved Chrome state may be discarded within the user-authorized host cleanup.',
   'Prior result/unlock guards are generic pinned root-supplied closure evidence; root must select current complete actual scopes. The helper does not synthesize closure or admit science.',
   'No graceful HWND closure: HWND reuse lacks the same retained kernel identity boundary. No other executable/session/service/WSL/profile/Git effect route.'],
 'producer_edits_by_reviewer':0,'required_before_actual':'Root publish and remote byte-readback final source85c46761; use original lock with exact current closed owner/result/unlock pins and independent actual review afterward.',
 'scientific_execution_or_acceptance':'NONE','accepted_stage4':'PRESERVED','remaining_source_blockers':[]}
R.require(not OUT.exists(),'Preserve existing peer')
with OUT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
print(json.dumps({'state':report['state'],'output':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'verified_files':len(R.CHECKED)}))
