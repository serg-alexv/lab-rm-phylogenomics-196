# BUILD preparation. No execution without an exact published proposal and remote recovery evidence.
param([string]$Plan, [string]$PlanSha256, [string]$RemoteCommit,
      [string]$RecoveryReceipt, [string]$RecoveryReceiptSha256, [string]$Receipt,
      [switch]$Run, [switch]$LibraryOnly)
$ErrorActionPreference='Stop'

function Assert-True($condition,[string]$message){if(-not $condition){throw $message}}
function Get-StreamSha($stream,[switch]$WatchOwners){
 $h=[Security.Cryptography.SHA256]::Create(); $buffer=[byte[]]::new(1048576); $blocks=0
 try{
  while(($n=$stream.Read($buffer,0,$buffer.Length)) -gt 0){
   $null=$h.TransformBlock($buffer,0,$n,$null,0); $blocks++
   if($WatchOwners -and $blocks%8 -eq 0){Check-Owners; Check-Deadline}
  }
  $null=$h.TransformFinalBlock([byte[]]::new(0),0,0)
  return [Convert]::ToHexString($h.Hash).ToLowerInvariant()
 }finally{$h.Dispose()}
}
function Get-FileSha([string]$path){
 $s=[IO.File]::Open($path,'Open','Read','Read')
 try{return Get-StreamSha $s}finally{$s.Dispose()}
}
function Assert-Row($row,$p){
 $rel=[string]$row.relative_path
 Assert-True ($rel -cmatch '^[^\\:]+$' -and -not $rel.StartsWith('/')) 'Noncanonical relative path'
 foreach($part in $rel.Split('/')){
  Assert-True ($part -notin @('','.','..') -and -not $part.EndsWith(' ') -and -not $part.EndsWith('.')) 'Path alias component'
  Assert-True ($part.ToLowerInvariant() -notin @('.git','.tools','.private_run','.codex')) 'Protected path'
 }
 Assert-True (-not $rel.ToLowerInvariant().EndsWith('.lock') -and -not $rel.ToLowerInvariant().EndsWith('.guard')) 'Protected lock or guard'
 Assert-True ($row.scope -cin $p.allowed_scopes -and $rel.StartsWith($row.scope+'/',[StringComparison]::Ordinal)) 'Wrong scope'
 $expected=$p.old_root+'\'+$rel.Replace('/','\')
 Assert-True ($row.path -ceq $expected -and [IO.Path]::GetFullPath($expected) -ceq $expected) 'Target alias/root escape'
 Assert-True ($row.link_count -eq 1 -and $row.bytes -ge 0 -and $row.sha256 -cmatch '^[a-f0-9]{64}$') 'Invalid leaf pin'
 Assert-True ($row.recovery.member_bytes -eq $row.bytes -and $row.recovery.member_sha256 -ceq $row.sha256) 'Member restoration mismatch'
 return $expected
}
function Initialize-LeafApi{
 if('Batch03LeafApi' -as [type]){return}
 Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public class Batch03LeafSnapshot {
 public string Device, FileId, FinalPath; public long Bytes, MtimeNs; public uint Links, Attributes;
}
public static class Batch03LeafApi {
 [StructLayout(LayoutKind.Sequential)] struct IdInfo {public ulong Volume, Low, High;}
 [StructLayout(LayoutKind.Sequential)] struct Info {
  public uint Attributes, CLo, CHi, ALo, AHi, WLo, WHi, Serial, SizeHi, SizeLo, Links, IndexHi, IndexLo;
 }
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle h,out Info i);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandleEx(SafeFileHandle h,int c,out IdInfo i,uint n);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern uint GetFinalPathNameByHandle(SafeFileHandle h,System.Text.StringBuilder p,uint n,uint f);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern SafeFileHandle CreateFile(string p,uint a,uint s,IntPtr x,uint d,uint f,IntPtr t);
 public static Batch03LeafSnapshot Snapshot(SafeFileHandle h) {
  Info i; IdInfo id;
  if(!GetFileInformationByHandle(h,out i)||!GetFileInformationByHandleEx(h,18,out id,24))throw new Win32Exception();
  if(id.High!=0)throw new IOException("128-bit file ID outside frozen 64-bit inventory");
  var b=new System.Text.StringBuilder(32768); uint n=GetFinalPathNameByHandle(h,b,32768,0);
  if(n==0||n>=32768)throw new Win32Exception();
  string p=b.ToString(); if(p.StartsWith(@"\\?\"))p=p.Substring(4);
  long ticks=checked((long)(((ulong)i.WHi<<32)|i.WLo));
  return new Batch03LeafSnapshot {Device=id.Volume.ToString(System.Globalization.CultureInfo.InvariantCulture),
   FileId=id.Low.ToString(System.Globalization.CultureInfo.InvariantCulture),FinalPath=p,
   Bytes=checked((long)(((ulong)i.SizeHi<<32)|i.SizeLo)),MtimeNs=checked((ticks-116444736000000000L)*100),Links=i.Links,Attributes=i.Attributes};
 }
 public static SafeFileHandle LockDirectory(string p) {
  // Read attributes, share readers/writers but not rename/delete; never follows a reparse endpoint.
  var h=CreateFile(p,0x80,3,IntPtr.Zero,3,0x02200000,IntPtr.Zero);
  if(h.IsInvalid)throw new Win32Exception();
  try {var i=Snapshot(h); if((i.Attributes&0x400)!=0||(i.Attributes&0x10)==0||!String.Equals(i.FinalPath,p,StringComparison.OrdinalIgnoreCase))throw new IOException("Directory alias/reparse");return h;}
  catch{h.Dispose();throw;}
 }
}
'@
}
function Assert-Snapshot($snapshot,$row,[string]$target){
 Assert-True ($snapshot.FinalPath -ieq $target -and ($snapshot.Attributes -band 0x410) -eq 0) 'Leaf alias/reparse/nonfile'
 Assert-True ($snapshot.Device -ceq [string]$row.device -and $snapshot.FileId -ceq [string]$row.file_id -and
  $snapshot.Bytes -eq $row.bytes -and $snapshot.MtimeNs -eq $row.mtime_ns -and $snapshot.Links -eq 1 -and $row.link_count -eq 1) 'Leaf identity/size/mtime/link drift'
}
function Check-Owners{
 foreach($o in $script:owners){
  $o.process.Refresh()
  Assert-True (-not $o.process.HasExited -and $o.process.StartTime.ToUniversalTime().ToFileTimeUtc().ToString() -ceq $o.birth) 'Retained IQ-TREE/controller closed or birth changed; stop and preserve'
 }
}
function Check-Deadline{Assert-True ($script:clock.Elapsed.TotalSeconds -lt $script:p.maximum_runtime_seconds) 'Finite cleanup deadline reached'}
function Write-Event($event){
 $event.utc=[DateTime]::UtcNow.ToString('o')
 $script:writer.WriteLine(($event|ConvertTo-Json -Compress -Depth 8)); $script:writer.Flush(); $script:journal.Flush($true)
}
function Invoke-GhJson([string]$endpoint){
 $raw=& gh api $endpoint
 Assert-True ($LASTEXITCODE -eq 0) ('GitHub read failed: '+$endpoint)
 return ($raw|ConvertFrom-Json -Depth 40)
}
function Read-EntryJson($zip,[string]$name){
 $s=$zip.GetEntry($name).Open(); $r=[IO.StreamReader]::new($s)
 try{return $r.ReadToEnd()|ConvertFrom-Json -Depth 40}finally{$r.Dispose()}
}

if($LibraryOnly){return}
Assert-True ($PSVersionTable.PSVersion -ge [version]'7.5') 'PowerShell 7.5+ required for exact large JSON integers'
Assert-True ($env:COMPUTERNAME -ieq 'WD') 'Wrong host'
foreach($v in @($Plan,$PlanSha256,$RemoteCommit,$RecoveryReceipt,$RecoveryReceiptSha256,$Receipt)){Assert-True (-not [string]::IsNullOrWhiteSpace($v)) 'Required argument missing'}
Assert-True ([IO.Path]::GetFullPath($Receipt) -ceq $Receipt -and $Receipt.StartsWith($PSScriptRoot+'\',[StringComparison]::OrdinalIgnoreCase)) 'Journal must be absolute beneath this C chat work directory'
Assert-True ($RemoteCommit -cmatch '^[a-f0-9]{40}$') 'Exact proposal commit required'
Assert-True (-not (Test-Path -LiteralPath $Receipt)) 'Preserve any existing journal'
Assert-True ((Get-FileSha $Plan) -ceq $PlanSha256) 'Proposal drift'
$script:p=Get-Content -LiteralPath $Plan -Raw|ConvertFrom-Json -Depth 40
Assert-True ($p.schema -ceq 'MASTER_BATCH03_STREAMING_LEAF_PURGE_PROPOSAL_V1' -and $p.state -ceq 'BUILD_ONLY_NO_DELETE') 'Wrong proposal'
Assert-True ($p.old_root -ceq 'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196') 'Wrong exact old root'
Assert-True (($p.allowed_scopes -join '|') -ceq 'data|.work/review2|.work/stage02_validated|.work/source_locus_inputs_v1|.work/stage03_markers_v1|.work/stage04a_windows_alignments_v1|.work/stage04_phylogeny_v2') 'Scope expansion'
Assert-True ($p.candidate_files -eq 47429 -and $p.candidate_bytes -eq 6565902818 -and $p.held_files -eq 219 -and $p.unmatched_preserved -eq 619) 'Wrong conservative accounting'
Assert-True ((Get-FileSha $PSCommandPath) -ceq $p.script_sha256) 'Cleanup helper changed'
Assert-True ($RecoveryReceipt -ceq $p.recovery_receipt.path -and $RecoveryReceiptSha256 -ceq $p.recovery_receipt.sha256) 'Recovery receipt differs from published proposal'
Assert-True ((Get-FileSha $RecoveryReceipt) -ceq $RecoveryReceiptSha256) 'Independent recovery receipt drift'
$recovery=Get-Content -LiteralPath $RecoveryReceipt -Raw|ConvertFrom-Json -Depth 40
Assert-True ($recovery.schema -ceq 'MASTER_BATCH03_MAPPING_INDEPENDENT_READBACK_V1' -and $recovery.state -ceq 'PASS_FRESH_REMOTE_MAPPING19_MEMBERS_47648_ROWS_219_HOLDS_619_PRESERVED') 'Independent actual remote archive/member readback required'
Assert-True ($recovery.archive_sha256 -ceq $p.archive.sha256 -and $recovery.archive_bytes -eq $p.archive.bytes) 'Wrong independently recovered archive'
Assert-True ($recovery.mapped_rows -eq 47648 -and $recovery.conservative_candidate_rows -eq 47429 -and
 $recovery.conservative_hold_rows -eq 219 -and $recovery.unmatched_preserved_rows -eq 619 -and
 $recovery.source_commit -ceq $p.recovery_receipt.source_commit -and $recovery.tag -ceq $p.recovery_receipt.tag -and
 $recovery.release_tag_and_assets_unchanged_before_after -eq $true) 'Recovery proposal accounting/authority mismatch'
$head=Invoke-GhJson 'repos/serg-alexv/lab-rm-phylogenomics-196/git/ref/heads/main'
Assert-True ($head.object.sha -ceq $RemoteCommit) 'Remote main changed; replan'
$remote=Invoke-GhJson ('repos/serg-alexv/lab-rm-phylogenomics-196/contents/'+$p.remote_plan_path+'?ref='+$RemoteCommit)
$ms=[IO.MemoryStream]::new([Convert]::FromBase64String($remote.content))
try{Assert-True ((Get-StreamSha $ms) -ceq $PlanSha256) 'Actual published proposal differs'}finally{$ms.Dispose()}
$mappingRelease=Invoke-GhJson ('repos/serg-alexv/lab-rm-phylogenomics-196/releases/tags/'+$recovery.tag)
foreach($a in $recovery.assets){
 $found=@($mappingRelease.assets|Where-Object id -EQ $a.remote_asset_id)
 Assert-True ($found.Count -eq 1 -and $found[0].name -ceq $a.name -and $found[0].size -eq $a.bytes -and
  $found[0].digest -ceq $a.remote_digest -and $a.remote_digest -ceq ('sha256:'+$a.sha256)) 'Current mapping recovery asset changed'
}
foreach($tag in @($p.assets.release_tag|Sort-Object -Unique)){
 $release=Invoke-GhJson ('repos/serg-alexv/lab-rm-phylogenomics-196/releases/tags/'+$tag)
 foreach($a in @($p.assets|Where-Object release_tag -CEQ $tag)){
  $found=@($release.assets|Where-Object id -EQ $a.id)
  Assert-True ($found.Count -eq 1 -and $found[0].name -ceq $a.name -and $found[0].size -eq $a.bytes -and
   $found[0].digest -ceq ('sha256:'+$a.sha256) -and $found[0].browser_download_url -ceq $a.url) 'Current recovery asset identity/digest changed'
 }
}
$script:owners=@(); $script:clock=[Diagnostics.Stopwatch]::StartNew(); Initialize-LeafApi
$archive=$null; $zip=$null; $script:journal=$null; $script:writer=$null; $directoryHandles=@{}; $journalHandles=@()
try{
 foreach($o in $p.owners){
  $proc=[Diagnostics.Process]::GetProcessById($o.pid); $null=$proc.Handle
  $script:owners+=@{process=$proc;birth=$o.creation_filetime}
 }
 Assert-True ($owners.Count -eq 2 -and $p.owners[0].pid -eq 4768 -and $p.owners[0].creation_filetime -ceq '134360369876207076' -and
  $p.owners[1].pid -eq 27048 -and $p.owners[1].creation_filetime -ceq '134360369803845506') 'Wrong retained process identity'
 Check-Owners
 $archive=[IO.File]::Open($p.archive.path,'Open','Read','Read')
 Assert-True ($archive.Length -eq $p.archive.bytes -and (Get-StreamSha $archive) -ceq $p.archive.sha256) 'Local published archive drift'
 $archive.Position=0; $zip=[IO.Compression.ZipArchive]::new($archive,[IO.Compression.ZipArchiveMode]::Read,$true)
 Assert-True ($zip.Entries.Count -eq $p.archive.members.Count) 'ZIP member count changed'
 $names=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 foreach($e in $zip.Entries){
  Assert-True ($names.Add($e.FullName)) 'Duplicate archive member'
  $pin=@($p.archive.members|Where-Object member -CEQ $e.FullName); Assert-True ($pin.Count -eq 1 -and $e.Length -eq $pin[0].bytes) 'ZIP member pin missing'
  $s=$e.Open(); try{Assert-True ((Get-StreamSha $s) -ceq $pin[0].sha256) 'Archive member SHA drift'}finally{$s.Dispose()}
 }
 $assessment=Read-EntryJson $zip 'control/conservative_leaf_assessment.json'
 $holds=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 foreach($h in $assessment.files_preserved){Assert-True ($holds.Add($h.path)) 'Duplicate hold'}
 Assert-True ($holds.Count -eq 219) 'Hold set changed'
 # Streaming metadata pass before any leaf reads/deletions. No 60MB JSONL deserialization.
 $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 $n=0; [long]$bytes=0; $held=0; [long]$heldBytes=0
 $reader=[IO.StreamReader]::new($zip.GetEntry($p.mapping_member).Open())
 try{while($null -ne ($line=$reader.ReadLine())){
  Check-Deadline; $row=$line|ConvertFrom-Json -Depth 15; $target=Assert-Row $row $p
  Assert-True ($seen.Add($target)) 'Duplicate target'; $n++; $bytes+=$row.bytes
  if($holds.Contains($target)){$held++;$heldBytes+=$row.bytes;continue}
  Assert-True (-not $row.relative_path.StartsWith('.work/review2/')) 'Unheld review2 path'
  $a=@($p.assets|Where-Object id -EQ $row.recovery.remote_asset_id)
  Assert-True ($a.Count -eq 1 -and $a[0].sha256 -ceq $row.recovery.remote_zip_sha256 -and $a[0].bytes -eq $row.recovery.remote_zip_bytes -and
   $a[0].url -ceq $row.recovery.remote_asset_url -and $a[0].release_tag -ceq $row.recovery.release_tag) 'Recovery asset mismatch'
 }}finally{$reader.Dispose()}
 Assert-True ($n -eq 47648 -and $bytes -eq 6568632074 -and $held -eq 219 -and $heldBytes -eq 2729256) 'Streaming accounting changed'
 Check-Owners
 if(-not $Run){[pscustomobject]@{state='METADATA_PREFLIGHT_ONLY_NO_DELETE';candidate_files=47429;candidate_bytes=6565902818}|ConvertTo-Json -Compress;return}
 $journalParent=[IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($Receipt)); $journalChain=[Collections.Generic.List[string]]::new()
 while($null -ne $journalParent){$journalChain.Insert(0,$journalParent.FullName);$journalParent=$journalParent.Parent}
 foreach($d in $journalChain){$journalHandles+=([Batch03LeafApi]::LockDirectory($d))}
 $script:journal=[IO.FileStream]::new($Receipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read,4096,[IO.FileOptions]::WriteThrough)
 $script:writer=[IO.StreamWriter]::new($journal,[Text.UTF8Encoding]::new($false),4096,$true)
 Write-Event @{event='BEGIN';schema='MASTER_BATCH03_LEAF_APPEND_RECEIPT_V1';plan_sha256=$PlanSha256;proposal_commit=$RemoteCommit;recovery_receipt_sha256=$RecoveryReceiptSha256;mapping_sha256=$p.mapping_sha256}
 $deleted=0; [long]$deletedBytes=0; $lineNumber=0; $lastProgress=$clock.Elapsed.TotalSeconds
 $reader=[IO.StreamReader]::new($zip.GetEntry($p.mapping_member).Open())
 try{while($null -ne ($line=$reader.ReadLine())){
  $lineNumber++; $row=$line|ConvertFrom-Json -Depth 15; $target=Assert-Row $row $p
  if($holds.Contains($target)){continue}
  Check-Owners; Check-Deadline
  # Keep every ancestor locked against rename/delete through each literal leaf removal.
  $parent=[IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($target)); $chain=[Collections.Generic.List[string]]::new()
  while($null -ne $parent){$chain.Insert(0,$parent.FullName);$parent=$parent.Parent}
  foreach($key in @($directoryHandles.Keys)){if(-not $chain.Contains($key)){$directoryHandles[$key].Dispose();$directoryHandles.Remove($key)}}
  foreach($d in $chain){if(-not $directoryHandles.ContainsKey($d)){$directoryHandles[$d]=[Batch03LeafApi]::LockDirectory($d)}}
  $stream=[IO.File]::Open($target,'Open','Read','None')
  try{
   Assert-Snapshot ([Batch03LeafApi]::Snapshot($stream.SafeFileHandle)) $row $target
   Assert-True ((Get-StreamSha $stream -WatchOwners) -ceq $row.sha256) 'Current actual leaf SHA drift'
   Assert-Snapshot ([Batch03LeafApi]::Snapshot($stream.SafeFileHandle)) $row $target
   Check-Owners; Check-Deadline
   Write-Event @{event='VERIFIED_INTENT';line=$lineNumber;path=$target;bytes=$row.bytes;sha256=$row.sha256;device=[string]$row.device;file_id=[string]$row.file_id;mtime_ns=[string]$row.mtime_ns}
   Assert-Snapshot ([Batch03LeafApi]::Snapshot($stream.SafeFileHandle)) $row $target
  }finally{$stream.Dispose()}
  # The exclusive handle must close for Remove-Item. This short leaf race is explicitly documented.
  $verify=[IO.File]::Open($target,'Open','Read','None')
  try{Assert-Snapshot ([Batch03LeafApi]::Snapshot($verify.SafeFileHandle)) $row $target;Check-Owners;Check-Deadline}finally{$verify.Dispose()}
  Remove-Item -LiteralPath $target -ErrorAction Stop
  Assert-True (-not (Test-Path -LiteralPath $target)) 'Leaf remains/reappeared; stop'
  $deleted++;$deletedBytes+=$row.bytes
  Write-Event @{event='REMOVED';line=$lineNumber;path=$target;bytes=$row.bytes;sha256=$row.sha256;deleted=$deleted;deleted_bytes=$deletedBytes}
  if($deleted%250 -eq 0 -or $clock.Elapsed.TotalSeconds-$lastProgress -ge 10){
   [pscustomobject]@{state='PROGRESS';deleted=$deleted;deleted_bytes=$deletedBytes;elapsed_seconds=[int]$clock.Elapsed.TotalSeconds}|ConvertTo-Json -Compress
   $lastProgress=$clock.Elapsed.TotalSeconds
  }
 }}finally{$reader.Dispose()}
 Check-Owners
 Assert-True ($deleted -eq 47429 -and $deletedBytes -eq 6565902818) 'Final exact count mismatch'
 Write-Event @{event='COMPLETE';state='PASS_EXACT_47429_COLD_LEAVES_REMOVED';deleted=$deleted;deleted_bytes=$deletedBytes;held_files=219;unmatched_preserved=619;recursive_deletes=0}
}catch{
 if($null -ne $writer){Write-Event @{event='STOP';state='FAILED_PARTIAL_PRESERVE_REMAINDER';error=$_.Exception.Message}}
 throw
}finally{
 if($null -ne $writer){$writer.Dispose()};if($null -ne $journal){$journal.Dispose()}
 foreach($h in $directoryHandles.Values){$h.Dispose()}
 foreach($h in $journalHandles){$h.Dispose()}
 if($null -ne $zip){$zip.Dispose()};if($null -ne $archive){$archive.Dispose()}
 foreach($o in $owners){$o.process.Dispose()}
}
