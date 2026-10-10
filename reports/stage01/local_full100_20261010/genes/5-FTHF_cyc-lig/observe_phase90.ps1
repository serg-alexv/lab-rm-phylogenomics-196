$ErrorActionPreference = 'Stop'
$outPath = Join-Path $PSScriptRoot 'phase_observation.json'
if (Test-Path -LiteralPath $outPath) { throw 'Preserve existing observation' }
$started = [DateTime]::UtcNow.ToString('o')
$owner = Get-CimInstance Win32_Process -Filter 'ProcessId=31816' | Select-Object ProcessId,CreationDate,CommandLine
if (-not $owner) { throw 'Expected pipeline owner absent' }
$linuxCode = @'
import json, pathlib
p = pathlib.Path('/proc')
ids = [4019, 4023]
children = (p / '4023/task/4023/children').read_text().split()
ids += [int(x) for x in children]
rows = []
for pid in ids:
    try:
        stat = (p / str(pid) / 'stat').read_text().strip()
        fields = stat[stat.rfind(')') + 2:].split()
        command = (p / str(pid) / 'cmdline').read_bytes().replace(b'\0', b' ').decode().strip()
        rows.append(dict(pid=pid, parent_pid=int(fields[1]), state=fields[0], start_ticks=int(fields[19]), cpu_ticks=int(fields[11])+int(fields[12]), command=command))
    except FileNotFoundError:
        rows.append(dict(pid=pid, state='EXITED_DURING_OBSERVATION'))
print(json.dumps(dict(boot_id=(p/'sys/kernel/random/boot_id').read_text().strip(), processes=rows)))
'@
$linuxOutput = & wsl.exe -d Ubuntu --exec python3 -c $linuxCode
if ($LASTEXITCODE -ne 0) { throw 'Native observation failed' }
$project = 'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196'
$attempt = Join-Path $project 'reports\stage01\local_full100_20261010\attempt01'
$record = [ordered]@{
  schema='full100_completed_marker_phase_observation_v1'; observed_utc=$started
  windows_owner=$owner; linux=($linuxOutput | ConvertFrom-Json)
  original_workflow_lock='Retained by the existing owner; not reopened or replaced by this observation'
  terminal_receipt_present=(Test-Path -LiteralPath (Join-Path $attempt 'terminal.json'))
  linux_terminal_receipt_present=(Test-Path -LiteralPath (Join-Path $attempt 'linux_terminal.json'))
  pipeline_sha256=(Get-FileHash -LiteralPath (Join-Path $project 'run_pipeline.sh') -Algorithm SHA256).Hash.ToLowerInvariant()
  completed_marker='5-FTHF_cyc-lig'; native_finished_local='Sat Oct 10 13:39:17 2026'; native_finished_utc='2026-10-10T10:39:17Z'
  completion_basis='Native IQ-TREE report and log finished, and original set-e pipeline advanced to a different marker. This is per-locus completion, not full-run closure.'
}
$bytes=[Text.Encoding]::UTF8.GetBytes(($record | ConvertTo-Json -Depth 10))
$stream=[IO.File]::Open($outPath,[IO.FileMode]::CreateNew)
try { $stream.Write($bytes,0,$bytes.Length) } finally { $stream.Dispose() }
$record | ConvertTo-Json -Depth 10
