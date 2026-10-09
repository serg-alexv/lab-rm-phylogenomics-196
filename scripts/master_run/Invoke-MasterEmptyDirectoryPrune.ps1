param([Parameter(Mandatory=$true)][string]$Plan,
      [Parameter(Mandatory=$true)][string]$PlanSha256,
      [Parameter(Mandatory=$true)][string]$RemoteCommit,
      [Parameter(Mandatory=$true)][string]$Receipt,[switch]$Run)
$ErrorActionPreference='Stop'
if($env:COMPUTERNAME -ine 'WD'){throw 'Wrong host'}
if($Run -and -not ([Environment]::GetCommandLineArgs() -icontains '-NonInteractive')){throw 'Run with powershell.exe or pwsh -NonInteractive -File; never adopt a child-confirmation prompt'}
if(Test-Path -LiteralPath $Receipt){throw 'Preserve prior receipt'}
if((Get-FileHash -LiteralPath $Plan -Algorithm SHA256).Hash.ToLowerInvariant() -ne $PlanSha256){throw 'Plan bytes changed'}
$p=Get-Content -LiteralPath $Plan -Raw|ConvertFrom-Json
if($p.schema -ne 'MASTER_EXACT_EMPTY_DIRECTORY_PRUNE_V1' -or $p.scope_roots.Count -ne 6 -or
   ($p.directories.path|Sort-Object -Unique).Count -ne $p.directories.Count){throw 'Unexpected plan scope'}
$head=gh api repos/serg-alexv/lab-rm-phylogenomics-196/git/ref/heads/main --jq .object.sha
if($LASTEXITCODE -ne 0 -or $head.Trim() -ne $RemoteCommit){throw 'Remote head changed'}
$remote=gh api "repos/serg-alexv/lab-rm-phylogenomics-196/contents/$($p.remote_plan_path)?ref=$RemoteCommit"|ConvertFrom-Json
if($LASTEXITCODE -ne 0){throw 'Published exact plan unavailable'}
$hash=[Security.Cryptography.SHA256]::Create()
try{$observed=([BitConverter]::ToString($hash.ComputeHash([Convert]::FromBase64String($remote.content)))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
if($observed -ne $PlanSha256){throw 'Published plan differs'}
$work='C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'
$old='C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196'
$Receipt=[IO.Path]::GetFullPath($Receipt)
if(-not $Receipt.StartsWith($work+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Receipt must stay inside current C work'}
$expectedRoots=@("$work\stage06_synthetic","$work\stage06_density_synthetic","$work\stage06_density_synthetic_final",
 "$work\__pycache__","$old\.work\waiter_serialization_fixture_1791488292423128600",
 "$old\.work\windows_zip_open_a594b80f28eb4a6f9dbd3e0f80eab201")
if(@(Compare-Object $expectedRoots @($p.scope_roots)).Count){throw 'Original six roots differ'}
if(-not $Run){[pscustomobject]@{state='PLAN_ONLY_NO_DELETE';directories=$p.directories.Count}|ConvertTo-Json -Compress;exit 0}
$r=[ordered]@{schema='MASTER_EMPTY_DIRECTORY_PRUNE_RECEIPT_V1';state='STARTED';plan_sha256=$PlanSha256;
 remote_proposal_commit=$RemoteCommit;removed=@();skipped=@();files_deleted=0;recursive_deletes=0;started_utc=[DateTime]::UtcNow.ToString('o')}
function Save-Receipt{$r|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $Receipt -Encoding utf8}
Save-Receipt
try{
 foreach($row in @($p.directories|Sort-Object @{Expression='depth';Descending=$true},path)){
  $reason=$null
  try{
   $target=[string]$row.path;$root=[string]$row.group_root
   if($root -notin $expectedRoots -or -not ($target -ieq $root -or $target.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Outside exact cold group'}
   if(-not (Test-Path -LiteralPath $target)){$reason='ALREADY_ABSENT'}
   else{
    if((Resolve-Path -LiteralPath $target).ProviderPath -ine $target){throw 'Target alias'}
    $item=Get-Item -LiteralPath $target -Force
    if(-not $item.PSIsContainer -or $item.CreationTimeUtc.ToFileTimeUtc() -ne $row.creation_filetime){throw 'Directory identity changed'}
    $cursor=$item
    while($null -ne $cursor){if($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse ancestor'};$cursor=$cursor.Parent}
    if(@(Get-ChildItem -LiteralPath $target -Force).Count){$reason='NONEMPTY'}
    else{
     # Never use -Recurse. -NonInteractive makes any concurrent-child
     # confirmation a terminating error, caught below and preserved.
     Remove-Item -LiteralPath $target -Confirm:$false -ErrorAction Stop
     if(Test-Path -LiteralPath $target){throw 'Directory remains'}
     $r.removed+=@{path=$target;creation_filetime=$row.creation_filetime}
    }
   }
  }catch{$reason='UNEXPECTED_PRESERVED: '+$_.Exception.Message}
  if($reason){$r.skipped+=@{path=$row.path;reason=$reason}}
  Save-Receipt
 }
 $r.state='COMPLETED_EXACT_EMPTY_DIRECTORIES_ONLY';$r.completed_utc=[DateTime]::UtcNow.ToString('o')
}finally{Save-Receipt}
$r|Select-Object state,files_deleted,recursive_deletes,@{n='removed_directories';e={$_.removed.Count}},@{n='skipped_directories';e={$_.skipped.Count}}|ConvertTo-Json -Compress
