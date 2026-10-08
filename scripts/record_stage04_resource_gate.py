"""Record an actual prelaunch resource rejection and follow-up measurements."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import stage04_controller as C
import production_resume as w
from workflow_publication import commit
OUTPUT=R/'reports/stage04/resource_gate_attempt_v3_01'
w.LOG=OUTPUT/'commands.jsonl'
with C.WorkflowLock(R/'.work/workflow.lock'):
 C.reconcile(R)
 failure=C.load(R/'.work/stage04_inference_controller_v3/controller_failure.json')
 C.check(failure['controller_pid']==17688 and 'headroom insufficient' in failure['error'],'Unexpected failed attempt')
 C.check(not (R/'.work/stage04_inference_controller_v3/state.json').exists()
         and not (R/'.work/stage04_inference_v3/inference_freeze.json').exists(),'A native phase may have started')
 ps="$r=Get-CimInstance Win32_OperatingSystem; [pscustomobject]@{utc=[DateTime]::UtcNow.ToString('o');host=$env:COMPUTERNAME;total_bytes=([int64]$r.TotalVisibleMemorySize*1024);available_bytes=([int64]$r.FreePhysicalMemory*1024);disk_bytes=(Get-PSDrive C).Free;threshold_bytes=2147483648;failed_pid_still_present=[bool](Get-Process -Id 17688 -ErrorAction SilentlyContinue)} | ConvertTo-Json -Compress"
 windows=json.loads(w.run(['pwsh','-NoProfile','-Command',ps],timeout=60))
 linux=json.loads(w.run(['wsl','-d','Ubuntu','--','bash','scripts/wsl_project.sh','host','python','scripts/stage04_linux_launcher.py','--mode','resources'],timeout=60))
 C.check(not windows['failed_pid_still_present'],'Failed process PID now present; inspect identity before resume')
 w.js(OUTPUT/'controller_failure.json',failure)
 w.js(OUTPUT/'resource_followup.json',{'windows':windows,'linux':linux,
  'measurement_scope':'Actual follow-up snapshots, not retrospective values at original gate failure',
  'required_available_bytes_each':2147483648,'actual_failed_controller_pid':17688,
  'native_ml_started':False,'inference_state_created':False,
  'original_gate_instant_numeric_measurement':'UNAVAILABLE; controller checked but did not persist rejected snapshots',
  'original_controller_source_sha256':C.digest(R/'scripts/stage04_inference_controller_v3.py'),
  'configuration_sha256':C.digest(R/'config/host_inference_stage04_v3.json')})
 report=('# Actual prelaunch RAM gate rejection\n\n'
  'The reviewed resumed inference was published in commit371f642. Windows controllerPID17688 exited1 at2026-10-08T15:58:08UTC on its resource gate. It created neither lifecycle state nor an inference freeze/native IQ-TREE attempt. The exact failure and current source/config hashes are preserved. All original validated/published alignments remain intact.\n\n'
  'The preflight requires current Windows and Linux available RAM each greater than2147483648bytes. Rejected snapshots were not persisted by that controller; exact values at that instant are unavailable. The accompanying command log and follow-up JSON contain fresh actual measurements, labeled separately. An earlier follow-up at15:58:54UTC measured Windows2077696000bytes and Linux7200763904bytes; Windows was69987648bytes below the gate.\n\n'
  'No unrelated processes were stopped, memory limits lowered, WSL/Windows restarted or biological scope changed. Natural resource recovery can permit the unchanged resume command in INFERENCE_V3.md. Until then, complete phylogeny validation, both production R-M detectors and the figure remain unexecuted dependent work.\n')
 w.atomic(OUTPUT/'REPORT.md',report.encode())
 w.status('4_phylogeny','RESOURCE_GATE_BLOCKED_NO_NATIVE_INFERENCE','PASS_ALIGNMENT_FORMATS_AND_PARTITIONS_PHYLOGENY_INCOMPLETE',
  'STAGE04A_UPLOAD_VERIFIED_FULL_STAGE04_PENDING','Resumed inference code published. Actual controllerPID17688 rejected current RAM headroom before any native ML launch. Preserved exact failure and follow-up resource evidence; all196 validated alignments remain published. Unchanged resume requires resource recovery.')
 paths=['scripts/record_stage04_resource_gate.py','STATUS.md','status/stages.tsv']
 paths += [p.relative_to(R).as_posix() for p in OUTPUT.iterdir() if p.is_file()]
 print(commit(paths,'Preserve actual Stage04 prelaunch RAM rejection and measured follow-up resources'))
