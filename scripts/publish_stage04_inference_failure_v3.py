"""Publish actual failed full196 inference evidence, without scientific PASS."""
from pathlib import Path
from types import SimpleNamespace
import json,re,sys
import production_resume as w
import stage04_controller as C
from portable_release import make_zip,publish_frozen,verify_zip
from workflow_publication import check,commit
R=Path(__file__).resolve().parents[1]
OUT=R/'.work/stage04_inference_v3'
CONTROL=R/'.work/stage04_inference_controller_v3'
PUBLIC=R/'reports/stage04b'
STAGING=R/'release_staging/stage04b'
w.LOG=PUBLIC/'publication_commands.jsonl'
with C.WorkflowLock(R/'.work/workflow.lock'):
 C.reconcile(R)
 state=C.load(CONTROL/'state.json');current=state['current']
 C.check(state['completed']=={} and current['phase']=='trees','Unexpected resumed phase state')
 phase=R/current['receipt_directory'];exited=C.load(phase/'linux_exit_receipt.json')
 C.check(exited['exit_code']==1 and exited['invocation_id']==current['invocation_id'] and exited['identity']==state['identity'],
         'Actual native phase failure proof missing')
 native=OUT/'analyses/primary196/iqtree/attempt_0001'
 command=C.load(native/'iqtree3.command.json');limited=C.load(native/'iqtree3.limit.json')
 observed=C.load(native/'iqtree3.actual_exe.json');stderr=(native/'iqtree3.stderr.txt').read_text()
 C.check(command['exit_code']==2 and command['child_pid']==limited['pid']==observed['pid']==965
  and command['actual_native_executable_observed'] is True
  and command['limit_receipt_sha256']==C.digest(native/'iqtree3.limit.json')
  and command['identity']==limited['identity']==observed['identity']
  and limited['start_ticks']==observed['start_ticks'] and limited['boot_id']==observed['boot_id']
  and limited['native_address_space_soft_hard_bytes']==[1610612736,1610612736]
  and '-p' in command['argv'] and '--mem' not in command['argv'],'Independent failure PID/limit/argv join differs')
 allocation=re.findall(r'allocation of ([0-9]+) bytes failed',stderr)
 C.check(allocation==['2084933760'] and not (OUT/'phylogeny_summary.json').exists()
  and not list(OUT.glob('analyses/*/iqtree/tree_complete.json')),'Native failure/allocation/unfinished outputs differ')
 args=SimpleNamespace(root=R,distribution='Ubuntu',host_env=R/'.tools/linux/host_env',linux_launcher=R/'scripts/stage04_linux_launcher.py')
 inspect=C.native_inspect(args,phase)
 C.check(inspect['status']=='ACTUAL_EXIT_RECEIPT_AVAILABLE' and inspect['exit_code']==1
  and not inspect['job_alive'] and not inspect['launcher_alive'],'Failed exact job/observer still active')
 PUBLIC.mkdir(parents=True,exist_ok=True);STAGING.mkdir(parents=True,exist_ok=True)
 plan=R/'status/stage04b_publication_plan.json'
 if not plan.exists():
  evidence={'status':'ACTUAL_FAILED_INFERENCE_EVIDENCE_VERIFIED_ONLY','scientific_stage04':'INCOMPLETE',
   'approved_assemblies':196,'attempted_primary_tips':196,'primary_markers':100,'columns':17456,
   'native_pid':965,'native_exit':2,'native_elapsed_seconds':command['elapsed_seconds'],
   'native_child_cpu_seconds':command['child_cpu_seconds'],
   'native_children_peak_rss_bytes_cumulative':command['children_peak_rss_bytes_cumulative'],
   'native_address_space_cap_bytes':1610612736,'failed_single_allocation_bytes':2084933760,
   'native_limit_receipt_sha256':C.digest(native/'iqtree3.limit.json'),
   'native_command_receipt_sha256':C.digest(native/'iqtree3.command.json'),
   'actual_phase_exit_receipt_sha256':C.digest(phase/'linux_exit_receipt.json'),
   'exact_failed_job_and_observer_absent':True,'completed_native_trees':0,'sensitivity_inferences':'NOT_RUN',
   'supports':'NOT_RUN','rm_detectors':'NOT_RUN','figure':'NOT_RUN',
   'validation_scope':'Distinct receipt/error/source reader; not a phylogeny scientific PASS'}
  w.js(PUBLIC/'failure_evidence_validation.json',evidence)
  report=('# Actual full196 partition-inference resource failure\n\n'
   'All196 source-validated assemblies and100 host markers remain required. Stage03 is scientifically validated and its12 ZIP batches remotely verified; Stage04a preserves all raw/trimmed alignments and four concatenations, including native Windows extraction/hash verification.\n\n'
   'The separately frozen resumed partition command ran on WD at2026-10-08T16:01:40UTC. Native IQ-TREE3.1.4 PID965 exited2 after3.988825s, childCPU3.667675s, cumulative child peakRSS192413696bytes. Actual exec/PID/start/boot and soft/hard1536MiB limits were observed. It requested one2084933760-byte likelihood allocation, exceeding that address-space cap, and emitted bad_alloc. The producer/phase exited1. No completed ML tree, model allocation, bootstrap support or sensitivity tree is present. This is a resource failure, not scientific completion.\n\n'
   'The failed outputs, exact command, native streams, original/new frozen input identities, partial native model checkpoint, phase receipts, process measurements and adopted code are in the standalone ZIP. Raw private model/session transcripts and credentials are excluded. Each member has SHA256; use ordinary Windows ZIP extraction. The partial native checkpoint is ancillary restart evidence and is not a biological result.\n\n'
   'A3GiB native/3.5GiB outer budget is being assessed separately. It requires freshly measured Windows available RAM at least4.5GiB to reserve1GiB beyond the computation envelope, Linux available RAM at least4GiB, one job and two threads. Current Windows headroom is below that requirement; no increased-budget inference has run. Original bounded failure/control/source bytes remain unchanged. Resource recovery does not waive source, model, support, cohort, final validation or Release readback requirements.\n\n'
   'Whole Stage04 remains incomplete. Both production R-M detectors, source/domain/context/partial/literature review, the196-tip/784-cell figure and final handoff remain unrun dependent work. No missing data or failure is called absence.\n')
  w.atomic(PUBLIC/'REPORT.md',report.encode());w.atomic(PUBLIC/'RELEASE_NOTES.md',report.encode())
  public_paths=['scripts/publish_stage04_inference_failure_v3.py','reports/stage04b/failure_evidence_validation.json','reports/stage04b/REPORT.md','reports/stage04b/RELEASE_NOTES.md']
  script_names=['stage04_inference_v3.py','stage04_inference_controller_v3.py','stage04_inference_validate_v3.py','stage04_iqtree_limit_v3.py',
   'test_stage04_inference_v3.py','test_stage04_inference_validate_v3.py','stage04_controller.py','stage04_linux_launcher.py',
   'portable_release.py','workflow_publication.py','production_resume.py','validate_windows_zip.ps1','wsl_project.sh']
  methods=['scripts/'+n for n in script_names]+['config/host_inference_stage04_v3.json','reports/stage04/resumed_inference_resource_preflight_v3.json',
   'reports/stage04/INFERENCE_V3.md','reports/stage04/inference_v3_adoption.json','reports/stage04/inference_v3_synthetic_tests.json',
   'reports/stage04/inference_v3_review/synthetic_checker_tests.json','reports/stage04/inference_v3_review/retained_source_actual_probe.json']
  check(public_paths+methods)
  members=[(p,'failed_inference/'+p.relative_to(OUT).as_posix()) for p in sorted(OUT.rglob('*')) if p.is_file()]
  members += [(p,'actual_phase_receipts/'+p.name) for p in sorted(phase.iterdir()) if p.is_file()]
  for key in ('stdout_log','stderr_log'):members.append((R/current[key],'actual_phase_logs/'+key+'.txt'))
  members += [(CONTROL/'state.json','actual_control/state.json'),(CONTROL/'controller_failure.json','actual_control/controller_failure.json')]
  members += [(R/p,p) for p in public_paths+methods]
  for source,_ in members:C.check(not C.SECRET.search(source.read_bytes()),'Unsafe publication content')
  guide='Stage04b: actual failed full196 host inference evidence. No completed tree, R-M prediction or figure.\nExtract with Windows Explorer/PowerShell; SHA256SUMS.txt covers every member.\nFor validated alignments use stage04a-hostalignments196-v1; for validated marker/source evidence use stage03-hostmarkers196-v1.\n'
  assets=[make_zip(STAGING/'stage04b-full196-native-resource-failure.zip',members,guide)]
  w.js(PUBLIC/'asset_manifest.json',{'stage':'stage04b','scientific_validation':'INCOMPLETE_ACTUAL_RESOURCE_FAILURE',
   'approved_assemblies':196,'assets':assets,'mutable_publication_receipts_separate':True})
  public_paths += ['reports/stage04b/asset_manifest.json']
  w.atomic(PUBLIC/'SHA256SUMS.txt',''.join(C.digest(R/p)+'  '+p+'\n' for p in sorted(public_paths)).encode())
  public_paths += ['reports/stage04b/SHA256SUMS.txt'];w.js(STAGING/'payload_paths.json',public_paths)
 else:public_paths=C.load(STAGING/'payload_paths.json')
 receipt=publish_frozen('stage04b','stage04b-inference-resource-failure196-v1',STAGING,PUBLIC/'asset_manifest.json',public_paths,
  'Stage04b: actual failed full196 partition inference; no completed phylogeny',PUBLIC/'RELEASE_NOTES.md')
 receipt.update(scientific_validation='INCOMPLETE_ACTUAL_RESOURCE_FAILURE',approved_assemblies=196,whole_stage04_phylogeny='NOT_COMPLETED')
 w.js(PUBLIC/'publication_receipt.json',receipt)
 w.status('4_phylogeny','BLOCKED_NATIVE_INFERENCE_RESOURCE_ALLOCATION','PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
  'STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING',
  'Actual full196 partition inference failed on a2084933760-byte allocation under native1536MiB cap. Exact process/limits/error evidence published and read back. All196 marker/sequence and alignment ZIPs remain verified. Current Windows RAM is insufficient for the separately assessed larger bounded budget; dependent R-M/figure/final work remains unrun.')
 commit(['reports/stage04b/publication_receipt.json','reports/stage04b/publication_progress.json','reports/stage04b/publication_commands.jsonl','STATUS.md','status/stages.tsv'],
  'Verify portable actual inference failure evidence and preserve incomplete scientific status')
 print('ACTUAL_FAILED_INFERENCE_EVIDENCE_PORTABLE_RELEASE_VERIFIED; PHYLOGENY_INCOMPLETE',flush=True)
