param([Parameter(Mandatory=$true)][string]$Request)
$ErrorActionPreference='Stop'
$r=Get-Content -LiteralPath $Request -Raw | ConvertFrom-Json
$service=New-Object -ComObject 'Schedule.Service'
$service.Connect()
$task=$service.GetFolder('\').GetTask($r.task_name)
$actual=$task.Definition
[xml]$xml=$task.Xml
$ns=New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
$ns.AddNamespace('t','http://schemas.microsoft.com/windows/2004/02/mit/task')
$sid=$xml.SelectSingleNode('/t:Task/t:Principals/t:Principal/t:UserId',$ns).InnerText
if($sid -ne $r.sid){throw 'Actual definition SID differs'}
$interactiveUser=(Get-CimInstance Win32_ComputerSystem).UserName
if(-not $interactiveUser){throw 'No logged-in interactive user'}
$interactiveSid=([System.Security.Principal.NTAccount]::new($interactiveUser)).Translate([System.Security.Principal.SecurityIdentifier]).Value
if($interactiveSid -ne $sid){throw 'Task is not the logged-in interactive user'}
$xmlpath=Join-Path $r.runtime 'actual_task_definition.xml'
$querypath=Join-Path $r.runtime 'actual_task_query.json'
[System.IO.File]::WriteAllText($xmlpath,$task.Xml,[System.Text.Encoding]::Unicode)
$query=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');task_name=$task.Name;task_path=$task.Path;state=$task.State;
 sid=$sid;principal_query_account=$actual.Principal.UserId;interactive_user_sid=$interactiveSid;
 logon_type=$actual.Principal.LogonType;run_level=$actual.Principal.RunLevel;
 triggers_count=$actual.Triggers.Count;actions_count=$actual.Actions.Count;executable=$actual.Actions.Item(1).Path;
 arguments=$actual.Actions.Item(1).Arguments;cwd=$actual.Actions.Item(1).WorkingDirectory;
 multiple_instances=$actual.Settings.MultipleInstances;execution_time_limit=$actual.Settings.ExecutionTimeLimit;
 restart_count=$actual.Settings.RestartCount;allow_demand_start=$actual.Settings.AllowDemandStart;hidden=$actual.Settings.Hidden;
 last_run_time=$task.LastRunTime.ToString('o');last_task_result=$task.LastTaskResult;number_of_missed_runs=$task.NumberOfMissedRuns}
[System.IO.File]::WriteAllText($querypath,($query | ConvertTo-Json -Depth 6),[System.Text.UTF8Encoding]::new($false))
Write-Output 'ACTUAL_DEFINITION_AND_SID_QUERIED'
