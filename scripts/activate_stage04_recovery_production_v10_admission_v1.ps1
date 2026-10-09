param([Parameter(Mandatory=$true)][string]$Request,[Parameter(Mandatory=$true)][string]$ObserverRequest)
$ErrorActionPreference='Stop'
$r=Get-Content -LiteralPath $Request -Raw | ConvertFrom-Json
if($r.protocol -ne 'V10_MANUAL_UNIQUE_ONESHOT_DIRECT_CONTROLLER' -or $r.mode -ne 'production'){throw 'Wrong production role/protocol'}
if(Test-Path -LiteralPath $r.start_path){throw 'Production manual start already requested; no duplicate retry'}
$python='C:\Users\wheel\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$gate='G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\scripts\check_stage04_recovery_acceptance_v10_admission_v1.py'
& $python $gate --request $Request --observer-request $ObserverRequest
if($LASTEXITCODE -ne 0){throw 'Exact independent parent acceptance is not valid; no production start'}
$service=New-Object -ComObject 'Schedule.Service'
$service.Connect()
$task=$service.GetFolder('\').GetTask($r.task_name)
$o=Get-Content -LiteralPath $ObserverRequest -Raw | ConvertFrom-Json
if($o.mode -ne 'observer' -or $o.target_runtime -ne $r.runtime -or (Test-Path -LiteralPath $o.start_path)){throw 'Wrong/already-started read-only observer'}
$observer=$service.GetFolder('\').GetTask($o.task_name)
$observerbytes=[System.Text.Encoding]::Unicode.GetPreamble()+[System.Text.Encoding]::Unicode.GetBytes($observer.Xml)
$observersha=([System.Security.Cryptography.SHA256]::Create().ComputeHash($observerbytes) | ForEach-Object {$_.ToString('x2')}) -join ''
if($observersha -ne $o.definition_sha256 -or $observer.State -ne 3 -or $observer.LastTaskResult -ne 267011){throw 'Unused exact durable observer definition differs'}
$bytes=[System.Text.Encoding]::Unicode.GetPreamble()+[System.Text.Encoding]::Unicode.GetBytes($task.Xml)
$sha=([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes) | ForEach-Object {$_.ToString('x2')}) -join ''
if($sha -ne $r.definition_sha256 -or $task.State -ne 3 -or $task.LastTaskResult -ne 267011){throw 'Actual unused production task definition/state differs'}
$before=[DateTime]::UtcNow.ToString('o')
$instance=$task.Run($null)
$receipt=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');start_before_utc=$before;status='ONE_HASH_ACCEPTED_MANUAL_PRODUCTION_START_REQUESTED';
 task_name=$task.Name;instance_guid=$instance.InstanceGuid;engine_pid=$instance.EnginePID;definition_sha256=$sha;launcher_pid=$PID;
 launch_only_helper_is_controller=$false;recurrent_triggers=0}
[System.IO.File]::WriteAllText($r.start_path,($receipt | ConvertTo-Json -Depth 5),[System.Text.UTF8Encoding]::new($false))
& 'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\scripts\start_stage04_recovery_observer_v10.ps1' -Request $ObserverRequest
if($LASTEXITCODE -ne 0){throw 'Observer start command failed; preserve actual native/controller state, never infer observer completion'}
Write-Output ('PRODUCTION_STARTED_ONCE '+$task.Name)
