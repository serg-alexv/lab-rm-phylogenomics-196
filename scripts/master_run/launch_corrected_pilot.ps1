$ErrorActionPreference = 'Stop'
$projectPath = 'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196'
$receiptDir = Join-Path $projectPath 'reports\stage01\local_pilot_20261010\attempt02'
$lockPath = 'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock'
if ((Get-FileHash -LiteralPath (Join-Path $projectPath 'run_pipeline.sh') -Algorithm SHA256).Hash.ToLowerInvariant() -ne '5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b') { throw 'Approved script hash changed' }
if (Test-Path -LiteralPath $receiptDir) { throw 'Preserve previous attempt receipts' }
if (@(Get-ChildItem -LiteralPath (Join-Path $projectPath 'pilot_output\trees') -File).Count -ne 0) { throw 'Unexpected existing tree outputs' }
if (Test-Path -LiteralPath (Join-Path (Split-Path $lockPath) 'stage05_owned_closure_unproven.json')) { throw 'Unresolved STOP' }
$lockHandle = [System.IO.File]::Open($lockPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
$started = [DateTime]::UtcNow.ToString('o')
$returnCode = $null
try {
    [System.IO.Directory]::CreateDirectory($receiptDir) | Out-Null
    @{state='RUNNING'; started_utc=$started; powershell_pid=$PID; cwd=$projectPath; command='PILOT_ONLY=1 bash run_pipeline.sh'; script_sha256='5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b'; approved_change='User approved -mem 3000M correction and pilot rerun'; original_lock_opened_exclusively=$true; full_pipeline_authorized=$false} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $receiptDir 'launch.json') -Encoding utf8
    & wsl.exe -d Ubuntu -u root --cd '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196' --exec /usr/bin/env PILOT_ONLY=1 /bin/bash run_pipeline.sh 2>&1 | Tee-Object -FilePath (Join-Path $receiptDir 'console.log')
    $returnCode = $LASTEXITCODE
} finally {
    $lockHandle.Dispose()
    @{state=$(if ($returnCode -eq 0) {'SCRIPT_EXITED_ZERO_VALIDATION_PENDING'} else {'SCRIPT_FAILED_STOPPED'}); started_utc=$started; finished_utc=[DateTime]::UtcNow.ToString('o'); exit_code=$returnCode; original_lock_handle_disposed=$true; full_pipeline_started=$false} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $receiptDir 'terminal.json') -Encoding utf8
}
exit $returnCode
