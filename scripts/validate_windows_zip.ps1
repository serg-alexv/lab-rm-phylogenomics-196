param(
    [Parameter(Mandatory=$true)][string]$ZipPath,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedSha256,
    [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference = 'Stop'
$stageRepository = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$stageWorkspace = [IO.Path]::GetFullPath((Join-Path $stageRepository '.work')) + [IO.Path]::DirectorySeparatorChar
$stageArchive = [IO.Path]::GetFullPath($ZipPath)
$stageDestination = [IO.Path]::GetFullPath($Destination)
if (-not $stageDestination.StartsWith($stageWorkspace, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Extraction destination must be inside this repository .work directory.'
}
if (Test-Path -LiteralPath $stageDestination) { throw 'Preserve existing outputs: choose a new extraction destination.' }
$stageActualHash = (Get-FileHash -LiteralPath $stageArchive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($stageActualHash -ne $ExpectedSha256.ToLowerInvariant()) { throw 'ZIP bytes differ from expected published SHA256.' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$stageZip = [IO.Compression.ZipFile]::OpenRead($stageArchive)
$stageNames = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$stagePrefix = $stageDestination + [IO.Path]::DirectorySeparatorChar
try {
    foreach ($stageEntry in $stageZip.Entries) {
        $stageName = $stageEntry.FullName
        if ([string]::IsNullOrEmpty($stageName) -or $stageName.Contains('\') -or $stageName.StartsWith('/') -or $stageName.Contains(':')) {
            throw 'Unsafe ZIP member path.'
        }
        foreach ($stagePart in $stageName.Split('/')) {
            if ($stagePart -in @('', '.', '..') -or $stagePart.EndsWith('.') -or $stagePart.EndsWith(' ') -or
                $stagePart -match '[<>"|?*\x00-\x1f]' -or $stagePart -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)') {
                throw 'ZIP member is not a safe Windows file path.'
            }
        }
        $stageTarget = [IO.Path]::GetFullPath((Join-Path $stageDestination $stageName))
        if (-not $stageTarget.StartsWith($stagePrefix, [StringComparison]::OrdinalIgnoreCase) -or -not $stageNames.Add($stageName)) {
            throw 'ZIP member escapes the destination or collides on Windows.'
        }
    }
} finally { $stageZip.Dispose() }
[IO.Compression.ZipFile]::ExtractToDirectory($stageArchive, $stageDestination)
$stageUtf8 = [Text.UTF8Encoding]::new($false, $true)
$stageChecks = [IO.File]::ReadAllLines((Join-Path $stageDestination 'SHA256SUMS.txt'), $stageUtf8)
$stageChecked = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($stageLine in $stageChecks) {
    if ($stageLine -notmatch '^([a-f0-9]{64})  (.+)$') { throw 'Malformed member checksum manifest.' }
    $stageExpected = $Matches[1]
    $stageMember = $Matches[2]
    if (-not $stageNames.Contains($stageMember) -or $stageMember -eq 'SHA256SUMS.txt' -or -not $stageChecked.Add($stageMember)) {
        throw 'Member checksum accounting differs from the ZIP.'
    }
    $stageMemberHash = (Get-FileHash -LiteralPath (Join-Path $stageDestination $stageMember) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($stageMemberHash -ne $stageExpected) { throw ('Extracted member hash differs: ' + $stageMember) }
}
if ($stageChecked.Count -ne $stageNames.Count - 1) { throw 'Checksum manifest does not cover all extracted payload members.' }
$stageReadme = [IO.File]::ReadAllText((Join-Path $stageDestination 'README.txt'), $stageUtf8)
if ([string]::IsNullOrWhiteSpace($stageReadme)) { throw 'Portable UTF-8 README is empty.' }
[pscustomobject]@{
    utc = [DateTime]::UtcNow.ToString('o')
    status = 'PASS_NATIVE_WINDOWS_EXTRACTION_AND_ALL_MEMBER_HASHES'
    asset = [IO.Path]::GetFileName($stageArchive)
    sha256 = $stageActualHash
    zip_bytes = (Get-Item -LiteralPath $stageArchive).Length
    extracted_files = $stageNames.Count
    payload_members_hash_verified = $stageChecked.Count
    readme_utf8_readable = $true
    method = 'Windows System.IO.Compression.ZipFile.ExtractToDirectory and Get-FileHash; no WSL'
} | ConvertTo-Json
