param([Parameter(Mandatory=$true)][string]$Request)
$ErrorActionPreference='Stop'
$r=Get-Content -LiteralPath $Request -Raw | ConvertFrom-Json
if($r.mode -ne 'observer' -or $r.protocol -ne 'V10_MANUAL_UNIQUE_ONESHOT_DIRECT_CONTROLLER'){throw 'Read-only observer role required'}
if(Test-Path -LiteralPath $r.start_path){throw 'Observer already started once'}
$service=New-Object -ComObject 'Schedule.Service'
$service.Connect()
$task=$service.GetFolder('\').GetTask($r.task_name)
$bytes=[System.Text.Encoding]::Unicode.GetPreamble()+[System.Text.Encoding]::Unicode.GetBytes($task.Xml)
$sha=([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes) | ForEach-Object {$_.ToString('x2')}) -join ''
if($sha -ne $r.definition_sha256 -or $task.State -ne 3 -or $task.LastTaskResult -ne 267011){throw 'Unused exact observer task definition differs'}
if(-not (Test-Path -LiteralPath (Join-Path $r.target_runtime 'task_start.json'))){throw 'Actual target controller manual start receipt absent'}
$before=[DateTime]::UtcNow.ToString('o')
$instance=$task.Run($null)
$receipt=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');start_before_utc=$before;status='ONE_READ_ONLY_OBSERVER_START_REQUESTED';
 task_name=$task.Name;instance_guid=$instance.InstanceGuid;engine_pid=$instance.EnginePID;definition_sha256=$sha;launcher_pid=$PID;
 target_runtime=$r.target_runtime;termination_rights=$false;recurrent_triggers=0}
[System.IO.File]::WriteAllText($r.start_path,($receipt | ConvertTo-Json -Depth 5),[System.Text.UTF8Encoding]::new($false))
Write-Output ('READ_ONLY_OBSERVER_STARTED_ONCE '+$task.Name)
