$ErrorActionPreference = 'Stop'
$projectPath = 'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196'
$receiptDir = Join-Path $projectPath 'reports\stage01\local_pilot_20261010'
$lockPath = 'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock'
$scriptPath = Join-Path $projectPath 'run_pipeline.sh'
if ((Get-FileHash -LiteralPath $scriptPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne '12f01df5050679c27d8acde1607d53753042e5946a3a958613d89e7479ad33c0') { throw 'Exact script hash changed' }
foreach ($relative in @('pilot_output', 'pipeline_output', 'reports\stage01\pilot_mafft.log', 'reports\stage01\pilot_iqtree.log', 'reports\stage01\pilot_astral.log', 'reports\stage01\pilot_console.log')) {
    if (Test-Path -LiteralPath (Join-Path $projectPath $relative)) { throw "Refusing overwrite: $relative" }
}
if (Test-Path -LiteralPath $receiptDir) { throw 'Preserve existing receipt directory' }
if (Test-Path -LiteralPath (Join-Path (Split-Path $lockPath) 'stage05_owned_closure_unproven.json')) { throw 'Unresolved STOP' }
$lockHandle = [System.IO.File]::Open($lockPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
$started = [DateTime]::UtcNow.ToString('o')
$returnCode = $null
try {
    [System.IO.Directory]::CreateDirectory($receiptDir) | Out-Null
    $launch = @{state='RUNNING'; started_utc=$started; powershell_pid=$PID; cwd=$projectPath; command='PILOT_ONLY=1 bash run_pipeline.sh'; script_sha256='12f01df5050679c27d8acde1607d53753042e5946a3a958613d89e7479ad33c0'; lock_path=$lockPath; original_lock_opened_exclusively=$true; full_pipeline_authorized=$false}
    $launch | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $receiptDir 'launch.json') -Encoding utf8
    & wsl.exe -d Ubuntu -u root --cd '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196' --exec /usr/bin/env PILOT_ONLY=1 /bin/bash run_pipeline.sh 2>&1 | Tee-Object -FilePath (Join-Path $projectPath 'reports\stage01\pilot_console.log')
    $returnCode = $LASTEXITCODE
} finally {
    $lockHandle.Dispose()
    $terminal = @{state=$(if ($returnCode -eq 0) {'SCRIPT_EXITED_ZERO_VALIDATION_PENDING'} else {'SCRIPT_FAILED_STOPPED'}); started_utc=$started; finished_utc=[DateTime]::UtcNow.ToString('o'); exit_code=$returnCode; original_lock_handle_disposed=$true; full_pipeline_started=$false}
    $terminal | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $receiptDir 'terminal.json') -Encoding utf8
}
exit $returnCode
