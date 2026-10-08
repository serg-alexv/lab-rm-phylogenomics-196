$ErrorActionPreference='Stop'
$stageOutput=Join-Path $PSScriptRoot '../reports/stage04/repair_admission_v1/ngs_helper_closure.json'
$stagePaths=@('C:\Users\wheel\.codex\cache\ngs-analysis-workbench\venvs\0.2.10\Scripts\python.exe','C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
$stageBefore=[int64](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024
$stageCandidates=@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -in $stagePaths -and $_.CommandLine -match '\s-m\s+ngs_(app|compute|workbench)_mcp\s*$' })
Start-Sleep -Seconds 2
$stageRows=@()
foreach($stageOriginal in ($stageCandidates | Sort-Object { if($_.ExecutablePath -eq $stagePaths[1]){0}else{1} })){
  $stageCurrent=Get-CimInstance Win32_Process -Filter "ProcessId=$($stageOriginal.ProcessId)"
  $stageValid=$stageCurrent -and $stageCurrent.CreationDate -eq $stageOriginal.CreationDate -and $stageCurrent.ExecutablePath -eq $stageOriginal.ExecutablePath -and $stageCurrent.CommandLine -eq $stageOriginal.CommandLine
  $stageCpuDelta=if($stageValid){([int64]$stageCurrent.UserModeTime+[int64]$stageCurrent.KernelModeTime)-([int64]$stageOriginal.UserModeTime+[int64]$stageOriginal.KernelModeTime)}else{$null}
  $stageChildren=@(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($stageOriginal.ProcessId)")
  $stageSafeChildren=@($stageChildren | Where-Object { $_.ExecutablePath -notin $stagePaths -or $_.CommandLine -notmatch '\s-m\s+ngs_(app|compute|workbench)_mcp\s*$' }).Count -eq 0
  $stageStopped=$false
  if($stageValid -and $stageCpuDelta -eq 0 -and $stageSafeChildren){ Stop-Process -Id $stageOriginal.ProcessId -Force; $stageStopped=$true }
  $stageRows+=[pscustomobject]@{pid=$stageOriginal.ProcessId;parent_pid=$stageOriginal.ParentProcessId;created_utc=$stageOriginal.CreationDate.ToUniversalTime().ToString('o');executable=$stageOriginal.ExecutablePath;module=([regex]::Match($stageOriginal.CommandLine,'ngs_(app|compute|workbench)_mcp')).Value;exact_identity_verified=[bool]$stageValid;cpu_delta_100ns=$stageCpuDelta;children_are_only_allowed_helpers=$stageSafeChildren;stopped=$stageStopped}
}
Start-Sleep -Seconds 5
$stageAfter=[int64](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024
[pscustomobject]@{utc=[DateTime]::UtcNow.ToString('o');authority='Latest direct human scoped repair authorization';windows_available_before_bytes=$stageBefore;windows_available_after_bytes=$stageAfter;rows=$stageRows;scientific_processes_stopped=0;control_connections_stopped=0;files_deleted=0;security_changes=0} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $stageOutput -Encoding utf8NoBOM
Write-Output "SCOPED_HELPER_CLOSURE stopped=$(@($stageRows | Where-Object stopped).Count) available=$stageAfter"
