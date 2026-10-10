param([Parameter(Mandatory=$true)][string]$OutputJson)
# Read-only supplemental observations. The caller must own a finite child/job
# deadline; these provider cmdlets alone cannot bound every possible stall.
$ErrorActionPreference = 'Stop'
$taskWork = 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'
if ($PSScriptRoot -cne $taskWork) { throw 'Exact current C-work deployment required' }
$fullOutput = [IO.Path]::GetFullPath($OutputJson)
$pattern = '^' + [regex]::Escape($taskWork) + '\\stage5_process_census_[0-9a-f]{32}\\supplemental\.json$'
if ($OutputJson -cne $fullOutput -or $fullOutput -cnotmatch $pattern) { throw 'Exact fresh C census output required' }
if ([IO.File]::Exists($fullOutput) -or [IO.Directory]::Exists($fullOutput)) { throw 'Never overwrite supplemental output' }
$parentDirectory = [IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($fullOutput))
while ($null -ne $parentDirectory) {
    if (-not $parentDirectory.Exists -or ($parentDirectory.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Existing plain C ancestry required'
    }
    $parentDirectory = $parentDirectory.Parent
}
$startedUtc = [DateTime]::UtcNow
$report = [ordered]@{
    schema = 'STAGE05_PROCESS_CENSUS_CIM_CLOCK_SUPPLEMENT_V1'
    state = 'SUPPLEMENTAL_ONLY_NO_CLOSURE_AUTHORITY'
    observer_pid = $PID
    started_utc = $startedUtc.ToString('O')
    process_census = $null
    clock_events = $null
    historical_clock_continuity = 'NOT_ESTABLISHED'
    process_universe_completeness = 'NOT_ESTABLISHED_BY_CIM'
    stop_clear_authorized = $false
}
try {
    $observed = @(Get-CimInstance -ClassName Win32_Process -Property ProcessId,CreationDate,Name,SessionId `
        -OperationTimeoutSec 5 -ErrorAction Stop | Select-Object -First 4097)
    $truncated = $observed.Count -gt 4096
    $projection = [Collections.Generic.List[object]]::new()
    foreach ($item in ($observed | Select-Object -First 4096)) {
        $row = [ordered]@{ pid = $(if ($null -eq $item.ProcessId) { $null } else { [UInt32]$item.ProcessId });
            name = $(if ($null -eq $item.Name) { $null } else { [string]$item.Name });
            session_id = $(if ($null -eq $item.SessionId) { $null } else { [UInt32]$item.SessionId }); birth_utc = $null; birth_filetime = $null;
            birth_state = 'UNKNOWN'; birth_precision = 'CIM_PROVIDER_PRECISION_NOT_ESTABLISHED' }
        if ($null -eq $row.pid -or $null -eq $row.name -or $null -eq $row.session_id -or $row.name.Length -gt 260) {
            $row.name = $null; $row.birth_state = 'INVALID_PROVIDER_ROW'
        }
        try {
            if ($null -ne $item.CreationDate) {
                $birthUtc = ([DateTime]$item.CreationDate).ToUniversalTime()
                $birthFiletime = $birthUtc.ToFileTimeUtc()
                if ($birthFiletime -gt 0 -and $row.birth_state -ne 'INVALID_PROVIDER_ROW') {
                    $row.birth_utc = $birthUtc.ToString('O'); $row.birth_filetime = $birthFiletime
                    $row.birth_state = 'SUPPLEMENTAL_CIM_DATE_ONLY'
                }
            }
        } catch { $row.birth_state = 'INVALID_PROVIDER_DATE' }
        $projection.Add([pscustomobject]$row)
    }
    $report.process_census = [ordered]@{
        state = $(if ($truncated) { 'TRUNCATED_UNKNOWN_COMPLETENESS' } else { 'PROVIDER_QUERY_COMPLETED_SUPPLEMENTAL_ONLY' })
        operation_timeout_seconds = 5; maximum_projected_rows = 4096
        returned_rows_capped_at_4097 = $observed.Count; truncated = $truncated
        rows = @($projection.ToArray())
    }
} catch {
    $report.process_census = [ordered]@{ state = 'PROVIDER_OR_ACCESS_ERROR'; rows = @(); truncated = $null;
        error_type = $_.Exception.GetType().FullName; error_hresult = $_.Exception.HResult
        error_id = [string]$_.FullyQualifiedErrorId }
}

# Only clock-event fields are projected; no account, SID, domain, command line
# or ProcessName from the Security log is written. No-log/error/empty results
# never establish coverage of the historical interval or clock continuity.
$windowStartUtc = [DateTime]::FromFileTimeUtc([Int64]134360636630302864).AddSeconds(-60)
$windowEndUtc = [DateTime]::UtcNow
try {
    $events = @(Get-WinEvent -FilterHashtable @{ LogName='Security'; Id=4616;
        StartTime=$windowStartUtc; EndTime=$windowEndUtc } -MaxEvents 129 -ErrorAction Stop)
    $projectedEvents = [Collections.Generic.List[object]]::new()
    foreach ($eventRecord in ($events | Select-Object -First 128)) {
        $xmlText = $eventRecord.ToXml()
        if ($xmlText.Length -gt 65536) { throw 'Clock-event XML exceeds64KiB' }
        $settings = [Xml.XmlReaderSettings]::new(); $settings.DtdProcessing = [Xml.DtdProcessing]::Prohibit
        $settings.XmlResolver = $null; $settings.MaxCharactersInDocument = 65536
        $reader = [Xml.XmlReader]::Create([IO.StringReader]::new($xmlText), $settings)
        try { $document = [Xml.XmlDocument]::new(); $document.XmlResolver = $null; $document.Load($reader) }
        finally { $reader.Dispose() }
        $previousTime = $null; $newTime = $null
        foreach ($node in $document.SelectNodes('/*[local-name()="Event"]/*[local-name()="EventData"]/*[local-name()="Data"]')) {
            if ($node.GetAttribute('Name') -ceq 'PreviousTime') { $previousTime = [string]$node.InnerText }
            if ($node.GetAttribute('Name') -ceq 'NewTime') { $newTime = [string]$node.InnerText }
        }
        if (($null -ne $previousTime -and $previousTime.Length -gt 64) -or
            ($null -ne $newTime -and $newTime.Length -gt 64)) { throw 'Invalid bounded clock-event timestamp' }
        $projectedEvents.Add([pscustomobject][ordered]@{
            provider = [string]$eventRecord.ProviderName; event_id = [int]$eventRecord.Id
            record_id = [long]$eventRecord.RecordId
            time_created_utc = $(if ($null -eq $eventRecord.TimeCreated) { $null } else { $eventRecord.TimeCreated.ToUniversalTime().ToString('O') })
            previous_time = $previousTime; new_time = $newTime
        })
    }
    $report.clock_events = [ordered]@{
        state = $(if ($events.Count -gt 128) { 'TRUNCATED_UNKNOWN_COVERAGE' } else { 'QUERY_COMPLETED_COVERAGE_NOT_ESTABLISHED' })
        log = 'Security'; event_id = 4616; maximum_projected_rows = 128
        window_start_utc = $windowStartUtc.ToString('O'); window_end_utc = $windowEndUtc.ToString('O')
        truncated = ($events.Count -gt 128); coverage = 'NOT_ESTABLISHED'
        rows = @($projectedEvents.ToArray())
    }
} catch {
    $noEvents = ([string]$_.FullyQualifiedErrorId).StartsWith('NoMatchingEventsFound,')
    $report.clock_events = [ordered]@{
        state = $(if ($noEvents) { 'NO_MATCHING_EVENTS_COVERAGE_NOT_ESTABLISHED' } else { 'PROVIDER_ACCESS_OR_PARSE_ERROR' })
        log = 'Security'; event_id = 4616; window_start_utc = $windowStartUtc.ToString('O')
        window_end_utc = $windowEndUtc.ToString('O'); coverage = 'NOT_ESTABLISHED'; truncated = $null; rows = @()
        error_type = $_.Exception.GetType().FullName; error_hresult = $_.Exception.HResult
        error_id = [string]$_.FullyQualifiedErrorId
    }
}
$report.completed_utc = [DateTime]::UtcNow.ToString('O')
$bytes = [Text.UTF8Encoding]::new($false).GetBytes(($report | ConvertTo-Json -Depth 10) + "`n")
if ($bytes.Length -gt 4*1024*1024) { throw 'Supplemental output exceeds4MiB' }
$stream = [IO.FileStream]::new($fullOutput, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try { $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true) }
finally { $stream.Dispose() }
