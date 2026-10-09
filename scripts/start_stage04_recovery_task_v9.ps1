param([Parameter(Mandatory=$true)][string]$Request)
$ErrorActionPreference='Stop'
$r=Get-Content -LiteralPath $Request -Raw | ConvertFrom-Json
if($r.protocol -ne 'V9_MANUAL_UNIQUE_ONESHOT_DIRECT_CONTROLLER'){throw 'Wrong Scheduler protocol'}
if(Test-Path -LiteralPath $r.start_path){throw 'Start receipt already exists; duplicate invocation rejected'}
$xmlhash=(Get-FileHash -LiteralPath $r.xml_path -Algorithm SHA256).Hash.ToLowerInvariant()
if($xmlhash -ne $r.definition_sha256){throw 'Pre-start exported definition changed'}
$service=New-Object -ComObject 'Schedule.Service'
$service.Connect()
$task=$service.GetFolder('\').GetTask($r.task_name)
$actualbytes=[System.Text.Encoding]::Unicode.GetPreamble()+[System.Text.Encoding]::Unicode.GetBytes($task.Xml)
$actualhash=([System.Security.Cryptography.SHA256]::Create().ComputeHash($actualbytes) | ForEach-Object {$_.ToString('x2')}) -join ''
if($actualhash -ne $xmlhash){throw 'Actual Scheduler definition changed'}
if($task.State -ne 3){throw 'Task is not ready'}
if($r.mode -eq 'production'){throw 'Production start requires separate hash-bound parent acceptance activator; this fixture-only starter cannot launch biology'}
if($r.mode -ne 'fixture'){throw 'Invalid fixture mode'}
$before=[DateTime]::UtcNow.ToString('o')
$instance=$task.Run($null)
$receipt=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');start_before_utc=$before;status='ONE_MANUAL_START_REQUESTED';
 task_name=$task.Name;instance_guid=$instance.InstanceGuid;engine_pid=$instance.EnginePID;definition_sha256=$xmlhash;
 launcher_pid=$PID;launch_only_helper_is_controller=$false;recurrent_triggers=0}
[System.IO.File]::WriteAllText($r.start_path,($receipt | ConvertTo-Json -Depth 5),[System.Text.UTF8Encoding]::new($false))
Write-Output ('STARTED_ONCE '+$task.Name)
