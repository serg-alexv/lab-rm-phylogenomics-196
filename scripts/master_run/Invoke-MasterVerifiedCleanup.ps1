param([Parameter(Mandatory=$true)][string]$Plan,
      [Parameter(Mandatory=$true)][string]$PlanSha256,
      [Parameter(Mandatory=$true)][string]$RemoteCommit,
      [Parameter(Mandatory=$true)][string]$Receipt,
      [switch]$Run)
$ErrorActionPreference='Stop'
if($env:COMPUTERNAME -ine 'WD'){throw 'Wrong host'}
if(Test-Path -LiteralPath $Receipt){throw 'Preserve prior cleanup receipt'}
if((Get-FileHash -LiteralPath $Plan -Algorithm SHA256).Hash.ToLowerInvariant() -ne $PlanSha256){throw 'Plan changed'}
$p=Get-Content -LiteralPath $Plan -Raw|ConvertFrom-Json
if($p.schema -ne 'MASTER_VERIFIED_EXACT_FILE_PURGE_V1' -or $p.files.Count -ne 224){throw 'Wrong batch'}
if(($p.files.path|Sort-Object -Unique).Count -ne 224){throw 'Duplicate targets'}
$head=gh api repos/serg-alexv/lab-rm-phylogenomics-196/git/ref/heads/main --jq .object.sha
if($LASTEXITCODE -ne 0 -or $head.Trim() -ne $RemoteCommit){throw 'Remote head changed; reconcile'}
$remote=gh api "repos/serg-alexv/lab-rm-phylogenomics-196/contents/$($p.remote_plan_path)?ref=$RemoteCommit"|ConvertFrom-Json
if($LASTEXITCODE -ne 0){throw 'Remote proposal unavailable'}
$sha=[Security.Cryptography.SHA256]::Create()
try{$actual=([BitConverter]::ToString($sha.ComputeHash([Convert]::FromBase64String($remote.content)))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
if($actual -ne $PlanSha256){throw 'Remote removal proposal differs'}
foreach($proof in $p.recovery_receipts){
 if((Get-FileHash -LiteralPath $proof.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.sha256){throw 'Recovery evidence drift'}
}
foreach($tag in @($p.assets.release_tag|Sort-Object -Unique)){
 $r=gh api "repos/serg-alexv/lab-rm-phylogenomics-196/releases/tags/$tag"|ConvertFrom-Json
 if($LASTEXITCODE -ne 0){throw 'Recovery release missing'}
 foreach($asset in @($p.assets|Where-Object release_tag -eq $tag)){
  $found=@($r.assets|Where-Object id -eq $asset.id)
  if($found.Count -ne 1 -or $found[0].name -ne $asset.name -or $found[0].size -ne $asset.bytes -or $found[0].digest -ne $asset.digest){throw 'Remote recovery asset changed'}
 }
}
$processes=@(Get-CimInstance Win32_Process)
$nativeProcess=[Diagnostics.Process]::GetProcessById(4768)
$controllerProcess=[Diagnostics.Process]::GetProcessById(27048)
$null=$nativeProcess.Handle;$null=$controllerProcess.Handle
function Check-Owners{
 $nativeProcess.Refresh();$controllerProcess.Refresh()
 if($nativeProcess.HasExited -or $nativeProcess.StartTime.ToUniversalTime().ToFileTimeUtc() -ne 134360369876207076 -or
    $controllerProcess.HasExited -or $controllerProcess.StartTime.ToUniversalTime().ToFileTimeUtc() -ne 134360369803845506){throw 'Retained native lifecycle changed; replan cleanup'}
}
Check-Owners
function Check-ExactFile($row){
 $target=(Resolve-Path -LiteralPath $row.path).ProviderPath
 if($target -ine $row.path){throw 'Target alias'}
 $root=@($p.allowed_roots|Where-Object {$target.StartsWith($_+'\',[StringComparison]::OrdinalIgnoreCase)})
 if($root.Count -ne 1){throw 'Target outside exact workspace roots'}
 foreach($protected in $p.protected_paths){
  if($target -ieq $protected -or $target.StartsWith($protected+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Active/protected target'}
 }
 $item=Get-Item -LiteralPath $target -Force
 if($item.PSIsContainer -or $item.Length -ne $row.bytes){throw 'Unexpected target type/size'}
 $cursor=$item
 while($null -ne $cursor -and $cursor.FullName.Length -ge $root[0].Length){
  if($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse point in target'}
  $cursor=if($cursor -is [IO.FileInfo]){$cursor.Directory}else{$cursor.Parent}
 }
 foreach($process in $processes){
  if($process.ProcessId -in @(4768,27048) -and $process.CommandLine -and
     $process.CommandLine.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'Active command references target'}
 }
 # Exclusive access also rejects currently open handles to a cold candidate.
 $stream=[IO.File]::Open($target,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::None)
 try{if((Get-FileHash -InputStream $stream -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256){throw 'Target bytes changed'}}finally{$stream.Dispose()}
 return $target
}
foreach($row in $p.files){$null=Check-ExactFile $row}
if(-not $Run){[pscustomobject]@{state='PREFLIGHT_ONLY_NO_DELETE';files=$p.files.Count}|ConvertTo-Json -Compress;exit 0}
$r=[ordered]@{schema='MASTER_EXACT_FILE_CLEANUP_RECEIPT_V1';state='DELETION_STARTED';started_utc=[DateTime]::UtcNow.ToString('o');
 plan_sha256=$PlanSha256;remote_proposal_commit=$RemoteCommit;deleted=@();deleted_bytes=0;recursive_deletes=0;scientific_status_changes=0}
function Save-Receipt{$r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $Receipt -Encoding utf8}
Save-Receipt
try{
 foreach($row in $p.files){
  Check-Owners
  $target=Check-ExactFile $row
  Check-Owners
  Remove-Item -LiteralPath $target -ErrorAction Stop
  if(Test-Path -LiteralPath $target){throw 'Target remains'}
  $r.deleted+=@{path=$target;bytes=$row.bytes;sha256=$row.sha256;recovery=$row.recovery}
  $r.deleted_bytes+=$row.bytes
  Save-Receipt
 }
 $r.state='PASS_EXACT_224_VERIFIED_INACTIVE_FILES_REMOVED'
 $r.completed_utc=[DateTime]::UtcNow.ToString('o')
}catch{$r.state='FAILED_PARTIAL_PRESERVE_REMAINDER';$r.error=$_.Exception.Message;throw}finally{Save-Receipt}
[pscustomobject]@{state=$r.state;deleted_bytes=$r.deleted_bytes;completed_utc=$r.completed_utc}|ConvertTo-Json -Compress
$nativeProcess.Dispose();$controllerProcess.Dispose()
