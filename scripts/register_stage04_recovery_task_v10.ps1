param([Parameter(Mandatory=$true)][string]$Request)
$ErrorActionPreference='Stop'
$r=Get-Content -LiteralPath $Request -Raw | ConvertFrom-Json
if($r.protocol -ne 'V10_MANUAL_UNIQUE_ONESHOT_DIRECT_CONTROLLER'){throw 'Wrong Scheduler protocol'}
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
if($sid -ne $r.sid){throw 'User SID differs'}
$service=New-Object -ComObject 'Schedule.Service'
$service.Connect()
$folder=$service.GetFolder('\')
$existing=@($folder.GetTasks(1) | Where-Object {$_.Name -eq $r.task_name})
if($existing.Count -ne 0){throw 'Unique task already exists; no replacement or second start'}
$definition=$service.NewTask(0)
$definition.RegistrationInfo.Description='Authorized LAB FULL196 V10 manual one-shot controller; no automatic trigger or restart.'
$definition.Principal.UserId=$sid
$definition.Principal.LogonType=3
$definition.Principal.RunLevel=0
$settings=$definition.Settings
$settings.Enabled=$true
$settings.Hidden=$true
$settings.AllowDemandStart=$true
$settings.DisallowStartIfOnBatteries=$false
$settings.StopIfGoingOnBatteries=$false
$settings.MultipleInstances=2
$settings.ExecutionTimeLimit='PT0S'
$settings.RestartCount=0
$settings.RunOnlyIfIdle=$false
$settings.RunOnlyIfNetworkAvailable=$false
$settings.WakeToRun=$false
$action=$definition.Actions.Create(0)
$action.Path=$r.executable
$action.Arguments=$r.arguments
$action.WorkingDirectory=$r.cwd
$task=$folder.RegisterTaskDefinition($r.task_name,$definition,2,$sid,$null,3,$null)
[System.IO.File]::WriteAllText($r.xml_path,$task.Xml,[System.Text.UTF8Encoding]::new($false))
$actual=$task.Definition
$query=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');task_name=$task.Name;task_path=$task.Path;state=$task.State;
 sid=$actual.Principal.UserId;logon_type=$actual.Principal.LogonType;run_level=$actual.Principal.RunLevel;
 triggers_count=$actual.Triggers.Count;actions_count=$actual.Actions.Count;executable=$actual.Actions.Item(1).Path;
 arguments=$actual.Actions.Item(1).Arguments;cwd=$actual.Actions.Item(1).WorkingDirectory;
 multiple_instances=$actual.Settings.MultipleInstances;execution_time_limit=$actual.Settings.ExecutionTimeLimit;
 restart_count=$actual.Settings.RestartCount;allow_demand_start=$actual.Settings.AllowDemandStart;hidden=$actual.Settings.Hidden;
 last_run_time=$task.LastRunTime.ToString('o');last_task_result=$task.LastTaskResult;number_of_missed_runs=$task.NumberOfMissedRuns}
[System.IO.File]::WriteAllText($r.query_path,($query | ConvertTo-Json -Depth 6),[System.Text.UTF8Encoding]::new($false))
if($actual.Triggers.Count -ne 0 -or $actual.Actions.Count -ne 1 -or $actual.Settings.RestartCount -ne 0 -or
 $actual.Settings.ExecutionTimeLimit -ne 'PT0S' -or $actual.Settings.MultipleInstances -ne 2 -or
 $actual.Principal.LogonType -ne 3 -or $actual.Principal.RunLevel -ne 0 -or
 $actual.Actions.Item(1).Path -ne $r.executable -or $actual.Actions.Item(1).Arguments -ne $r.arguments -or
 $actual.Actions.Item(1).WorkingDirectory -ne $r.cwd){throw 'Actual one-shot definition differs'}
[xml]$registeredXml=$task.Xml
$namespace=New-Object System.Xml.XmlNamespaceManager($registeredXml.NameTable)
$namespace.AddNamespace('t','http://schemas.microsoft.com/windows/2004/02/mit/task')
if($registeredXml.SelectSingleNode('/t:Task/t:Principals/t:Principal/t:UserId',$namespace).InnerText -ne $sid){throw 'Actual registered SID differs'}
Write-Output ('REGISTERED_NOT_STARTED '+$task.Name)
