# Exact837 history02 cleanup preparation. Native FILE_ID_INFO/ancestor/owner primitives adapted from
# Invoke-MasterBatch03LeafPurge.ps1 SHA94b5d9fb98c211b1c4915ff84de8d006ded9d01ec3d3bb11650657781f9d285c.
# No execution without published exact proposal, fresh recovery, and actual batch03 postverify PASS.
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
 Assert-True (-not $rel.ToLowerInvariant().EndsWith('.lock') -and -not $rel.ToLowerInvariant().EndsWith('.guard')) 'Protected lock/guard'
 Assert-True ($row.scope -cin $p.allowed_scopes -and $rel.StartsWith($row.scope+'/',[StringComparison]::Ordinal)) 'Wrong scope'
 $target=$p.old_root+'\'+$rel.Replace('/','\')
 Assert-True ($row.path -ceq $target -and [IO.Path]::GetFullPath($target) -ceq $target) 'Target alias/root escape'
 Assert-True ($row.link_count -eq 1 -and $row.bytes -ge 0 -and $row.sha256 -cmatch '^[a-f0-9]{64}$') 'Invalid leaf pin'
 return $target
}
function Initialize-LeafApi{
 if('History02LeafApi' -as [type]){return}
 Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public class History02LeafSnapshot {
 public string Device, FileId, FinalPath; public long Bytes, MtimeNs; public uint Links, Attributes;
}
public static class History02LeafApi {
 [StructLayout(LayoutKind.Sequential)] struct IdInfo {public ulong Volume, Low, High;}
 [StructLayout(LayoutKind.Sequential)] struct Info {
  public uint Attributes, CLo, CHi, ALo, AHi, WLo, WHi, Serial, SizeHi, SizeLo, Links, IndexHi, IndexLo;
 }
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle h,out Info i);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandleEx(SafeFileHandle h,int c,out IdInfo i,uint n);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern uint GetFinalPathNameByHandle(SafeFileHandle h,System.Text.StringBuilder p,uint n,uint f);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern SafeFileHandle CreateFile(string p,uint a,uint s,IntPtr x,uint d,uint f,IntPtr t);
 public static History02LeafSnapshot Snapshot(SafeFileHandle h) {
  Info i; IdInfo id;
  if(!GetFileInformationByHandle(h,out i)||!GetFileInformationByHandleEx(h,18,out id,24))throw new Win32Exception();
  if(id.High!=0)throw new IOException("128-bit file ID outside frozen 64-bit inventory");
  var b=new System.Text.StringBuilder(32768); uint n=GetFinalPathNameByHandle(h,b,32768,0);
  if(n==0||n>=32768)throw new Win32Exception();
  string p=b.ToString(); if(p.StartsWith(@"\\?\"))p=p.Substring(4);
  long ticks=checked((long)(((ulong)i.WHi<<32)|i.WLo));
  return new History02LeafSnapshot {Device=id.Volume.ToString(System.Globalization.CultureInfo.InvariantCulture),
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
  $snapshot.Bytes -eq $row.bytes -and $snapshot.MtimeNs.ToString() -ceq $row.mtime_ns -and $snapshot.Links -eq 1 -and $row.link_count -eq 1) 'Leaf identity/size/mtime/link drift'
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
 Check-Deadline
 $info=[Diagnostics.ProcessStartInfo]::new('gh');$info.UseShellExecute=$false;$info.CreateNoWindow=$true
 $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 foreach($a in @('api',$endpoint)){$info.ArgumentList.Add($a)}
 $proc=[Diagnostics.Process]::new();$proc.StartInfo=$info
 try{
  Assert-True ($proc.Start()) 'Cannot start owned GitHub read client'
  $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
  if(-not $proc.WaitForExit(60000)){$proc.Kill();$null=$proc.WaitForExit(5000);throw 'Bounded owned GitHub read timed out'}
  Assert-True ($proc.ExitCode -eq 0) ('GitHub read failed: '+$endpoint)
  Check-Deadline
  return ($stdout.GetAwaiter().GetResult()|ConvertFrom-Json -Depth 40)
 }finally{$proc.Dispose()}
}
function Read-EntryJson($zip,[string]$name){
 $s=$zip.GetEntry($name).Open(); $r=[IO.StreamReader]::new($s)
 try{return $r.ReadToEnd()|ConvertFrom-Json -Depth 40}finally{$r.Dispose()}
}


function Check-Preserved{
 foreach($row in $script:p.excluded_preserved){
  $target=Assert-Row $row $p;Check-Owners;Check-Deadline
  $stream=[IO.File]::Open($target,'Open','Read','None')
  try{
   Assert-Snapshot ([History02LeafApi]::Snapshot($stream.SafeFileHandle)) $row $target
   Assert-True ((Get-StreamSha $stream) -ceq $row.sha256) 'Excluded1025B fragment SHA drift'
   Assert-Snapshot ([History02LeafApi]::Snapshot($stream.SafeFileHandle)) $row $target
  }finally{$stream.Dispose()}
 }
}
function Check-Protected{
 Assert-True ((Get-FileSha $p.protected_baseline.path) -ceq $p.protected_baseline.sha256 -and
  $p.protected_baseline.sha256 -ceq '22d307f5bba8a98dbd060e3d1d091e22c7f70dc85b40e77ada04c0eef36ce1a7') 'Protected12 baseline drift'
 $baseline=Get-Content -LiteralPath $p.protected_baseline.path -Raw|ConvertFrom-Json -Depth 20
 Assert-True ($baseline.files.Count -eq 12) 'Exact12 protected baseline required'
 foreach($row in $baseline.files){
  Check-Owners;Check-Deadline
  Assert-True (([IO.FileInfo]::new($row.path)).Length -eq $row.bytes -and (Get-FileSha $row.path) -ceq $row.sha256) 'Protected active input/source/G state hash drift'
 }
}

if($LibraryOnly){return}
Assert-True ($PSVersionTable.PSVersion -ge [version]'7.5' -and $env:COMPUTERNAME -ieq 'WD') 'WD PowerShell7.5+ required'
Assert-True ($PSScriptRoot -ceq 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work') 'Exact C chat work executor namespace required'
foreach($v in @($Plan,$PlanSha256,$RemoteCommit,$RecoveryReceipt,$RecoveryReceiptSha256,$Receipt)){Assert-True (-not [string]::IsNullOrWhiteSpace($v)) 'Required argument missing'}
Assert-True ([IO.Path]::GetFullPath($Receipt) -ceq $Receipt -and $Receipt.StartsWith($PSScriptRoot+'\',[StringComparison]::OrdinalIgnoreCase)) 'Absolute C-work journal required'
Assert-True (-not (Test-Path -LiteralPath $Receipt)) 'Preserve existing journal'
Assert-True ($RemoteCommit -cmatch '^[a-f0-9]{40}$' -and $PlanSha256 -cmatch '^[a-f0-9]{64}$') 'Exact immutable proposal pins required'
Assert-True ((Get-FileSha $Plan) -ceq $PlanSha256) 'Proposal drift'
$script:p=Get-Content -LiteralPath $Plan -Raw|ConvertFrom-Json -Depth 40
Assert-True ($p.schema -ceq 'MASTER_HISTORY02_EXACT837_LEAF_PURGE_PROPOSAL_V1' -and $p.state -ceq 'BUILD_ONLY_NO_DELETE' -and $null -ne $p.batch03_postverify) 'Actual successful batch03 postverify pin required; blocked drafts cannot execute'
Assert-True ($p.old_root -ceq 'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196' -and
 ($p.allowed_scopes -join '|') -ceq 'data|.work/review2|.work/stage02_validated|.work/source_locus_inputs_v1|.work/stage03_markers_v1|.work/stage04a_windows_alignments_v1|.work/stage04_phylogeny_v2') 'Wrong exact root/scope'
Assert-True ($p.candidate_files -eq 837 -and $p.candidate_bytes -eq 983926424 -and $p.candidates.Count -eq 837 -and
 $p.excluded_files -eq 1 -and $p.excluded_bytes -eq 1025 -and $p.excluded_preserved.Count -eq 1 -and
 $p.previous47429_candidates_disjoint -eq $true -and $p.maximum_runtime_seconds -eq 900) 'Exact837 conservative accounting required'
Assert-True ($p.excluded_preserved[0].path -ceq 'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\review2\stage05_raw_review\installed_rejected_serializer.txt' -and
 $p.excluded_preserved[0].bytes -eq 1025 -and $p.excluded_preserved[0].sha256 -ceq '574547f9584dafce870492810ab02be990fe022939edd5a797292c473625027b') 'Exact unlicensed source fragment must remain excluded'
Assert-True ((Get-FileSha $PSCommandPath) -ceq $p.script_sha256) 'Executor source changed'
$script:clock=[Diagnostics.Stopwatch]::StartNew();$script:owners=@();Initialize-LeafApi
$script:journal=$null;$script:writer=$null;$directoryHandles=@{};$journalHandles=@()
try{
 Assert-True ($p.owners.Count -eq 2 -and $p.owners[0].pid -eq 4768 -and $p.owners[0].creation_filetime -ceq '134360369876207076' -and
  $p.owners[1].pid -eq 27048 -and $p.owners[1].creation_filetime -ceq '134360369803845506') 'Exact native/controller births required'
 foreach($o in $p.owners){$proc=[Diagnostics.Process]::GetProcessById($o.pid);$null=$proc.Handle;$script:owners+=@{process=$proc;birth=$o.creation_filetime}}
 Check-Owners
 Assert-True ($RecoveryReceipt -ceq $p.recovery_receipt.path -and $RecoveryReceiptSha256 -ceq $p.recovery_receipt.sha256 -and
  $RecoveryReceiptSha256 -ceq 'd83aaff2695920d475742ace6c710255a326642222a5db771b95ec2d809b0ecb' -and
  (Get-FileSha $RecoveryReceipt) -ceq $RecoveryReceiptSha256) 'Actual independent remote recovery drift'
 $recovery=Get-Content -LiteralPath $RecoveryReceipt -Raw|ConvertFrom-Json -Depth 40
 Assert-True ($recovery.schema -ceq 'MASTER_PUBLIC_HISTORY02_INDEPENDENT_READBACK_V1' -and
  $recovery.state -ceq 'PASS_FRESH_REMOTE_HISTORY02_3_SHARDS_882_MEMBERS_837_ORIGINALS_1_EXPLICIT_EXCLUSION' -and
  $recovery.source_commit -ceq '2ad42f8c3d78a974f22533a4f21ef1b5e8562a8b' -and
  $recovery.original_source_files -eq 837 -and $recovery.original_source_bytes -eq 983926424 -and
  $recovery.release_tag_and_assets_unchanged_before_after -eq $true) 'Full actual837 remote member recovery required'
 Assert-True ($p.batch03_postverify.sha256 -ceq '84cb29ebcc04b444ea90ca0e10d5f7e6832d09f14f8f8285f1241b4cf3e71868' -and
  (Get-FileSha $p.batch03_postverify.path) -ceq $p.batch03_postverify.sha256) 'Actual batch03 postverify receipt drift'
 $post=Get-Content -LiteralPath $p.batch03_postverify.path -Raw|ConvertFrom-Json -Depth 40
 Assert-True ($post.schema -ceq 'MASTER_BATCH03_INDEPENDENT_POST_PURGE_VERIFY_V1' -and
  $post.state -ceq 'PASS_EXACT47429_REMOVED_838_ORIGINALS_AND12_PROTECTED_UNCHANGED' -and
  $post.verifier_sha256 -ceq 'dbb0140fe2fac41940fa8d4838ffcbf1f6b72933d6d14a2011137ef4c401c56f' -and
  $post.removed_files -eq 47429 -and $post.removed_bytes -eq 6565902818 -and $post.held_files -eq 219 -and
  $post.unmatched_files -eq 619 -and $post.remaining_after_stop -eq 0 -and $post.unreceipted_absences.Count -eq 0 -and
  $post.retained_originals.Count -eq 838 -and $post.protected_files.Count -eq 12) 'Actual successful batch03 full closure/preservation proof required'
 $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);[long]$total=0
 foreach($row in @($p.candidates)+@($p.excluded_preserved)){
  $target=Assert-Row $row $p;Assert-True ($seen.Add($target)) 'Duplicate original path'
  $proof=@($post.retained_originals|Where-Object path -CEQ $target)
  Assert-True ($proof.Count -eq 1 -and $proof[0].bytes -eq $row.bytes -and $proof[0].sha256 -ceq $row.sha256 -and $proof[0].identity_equal -eq $true) 'Exact838 postverify source hash join differs'
  $total+=$row.bytes
 }
 Assert-True ($total -eq 983927449) 'Exact838 original bytes differ'
 $head=Invoke-GhJson 'repos/serg-alexv/lab-rm-phylogenomics-196/git/ref/heads/main'
 Assert-True ($head.object.sha -ceq $RemoteCommit) 'Remote main changed; replan'
 $remote=Invoke-GhJson ('repos/serg-alexv/lab-rm-phylogenomics-196/contents/'+$p.remote_plan_path+'?ref='+$RemoteCommit)
 $ms=[IO.MemoryStream]::new([Convert]::FromBase64String($remote.content))
 try{Assert-True ((Get-StreamSha $ms) -ceq $PlanSha256) 'Actual published proposal differs'}finally{$ms.Dispose()}
 Assert-True ($p.remote_plan_path -ceq 'reports/master_run/20261009/cleanup/history02_purge01/proposed.json' -and
  $p.remote_recovery_receipt_path -ceq 'reports/master_run/20261009/cleanup/history02/REMOTE_READBACK.json' -and
  $p.remote_postverify_receipt_path -ceq 'reports/master_run/20261009/cleanup/batch03_purge01/INDEPENDENT_POSTVERIFY.json') 'Declared canonical receipt paths differ'
 foreach($control in @(@{path=$p.remote_recovery_receipt_path;sha256=$RecoveryReceiptSha256},@{path=$p.remote_postverify_receipt_path;sha256=$p.batch03_postverify.sha256})){
  $remoteReceipt=Invoke-GhJson ('repos/serg-alexv/lab-rm-phylogenomics-196/contents/'+$control.path+'?ref='+$RemoteCommit)
  $ms=[IO.MemoryStream]::new([Convert]::FromBase64String($remoteReceipt.content))
  try{Assert-True ((Get-StreamSha $ms) -ceq $control.sha256) 'Actual published recovery/postverify receipt bytes differ'}finally{$ms.Dispose()}
 }
 Assert-True ($p.remote_source_controls.Count -eq 16) 'All16 source controls required'
 foreach($control in $p.remote_source_controls){
  $expected=@($recovery.authoritative_control_readback|Where-Object path -CEQ $control.path)
  Assert-True ($expected.Count -eq 1 -and $expected[0].remote_blob -ceq $control.remote_blob -and
   $expected[0].sha256 -ceq $control.sha256 -and $expected[0].bytes -eq $control.bytes) 'Pinned source proof table differs'
  Assert-True ($control.commit -ceq $p.recovery_receipt.source_commit -and $control.actual_remote_bytes_read -eq $true) 'Source proof commit changed'
  $blob=Invoke-GhJson ('repos/serg-alexv/lab-rm-phylogenomics-196/git/blobs/'+$control.remote_blob)
  $bytes=[Convert]::FromBase64String($blob.content);$ms=[IO.MemoryStream]::new($bytes)
  try{Assert-True ($bytes.Length -eq $control.bytes -and (Get-StreamSha $ms) -ceq $control.sha256) 'Current immutable recovery source blob changed'}finally{$ms.Dispose()}
 }
 $tag=Invoke-GhJson ('repos/serg-alexv/lab-rm-phylogenomics-196/commits/'+$p.recovery_receipt.tag)
 Assert-True ($tag.sha -ceq $p.recovery_receipt.tag_commit -and $tag.sha -ceq '46c7089f906cce59afabaa4449b05df36ee124de') 'Release tag target changed'
 $release=Invoke-GhJson ('repos/serg-alexv/lab-rm-phylogenomics-196/releases/tags/'+$p.recovery_receipt.tag)
 Assert-True ($p.recovery_assets.Count -eq 6) 'ThreeZIP+three sidecar recovery pins required'
 foreach($a in $p.recovery_assets){
  $expected=@($recovery.downloaded_assets|Where-Object name -CEQ $a.name)
  Assert-True ($expected.Count -eq 1 -and $expected[0].remote_asset_id -eq $a.remote_asset_id -and
   $expected[0].sha256 -ceq $a.sha256 -and $expected[0].bytes -eq $a.bytes) 'Recovery asset table differs from exact fresh receipt'
  $found=@($release.assets|Where-Object id -EQ $a.remote_asset_id)
  Assert-True ($found.Count -eq 1 -and $found[0].name -ceq $a.name -and $found[0].size -eq $a.bytes -and
   $found[0].digest -ceq $a.remote_digest -and $a.remote_digest -ceq ('sha256:'+$a.sha256)) 'Current recovered Release asset changed'
 }
 Assert-True ($p.local_archives.Count -eq 3) 'Three actual recovered local ZIPs required'
 foreach($a in $p.local_archives){
  Check-Owners;Check-Deadline;$expected=@($recovery.downloaded_assets|Where-Object name -CEQ $a.name)
  Assert-True ($expected.Count -eq 1 -and $a.name.EndsWith('.zip') -and $a.sha256 -ceq $expected[0].sha256 -and
   $a.bytes -eq $expected[0].bytes -and $a.path -ceq ([IO.Path]::GetDirectoryName($RecoveryReceipt)+'\'+$a.name)) 'Local archive must be exact fresh downloaded asset'
  Assert-True (([IO.FileInfo]::new($a.path)).Length -eq $a.bytes -and (Get-FileSha $a.path) -ceq $a.sha256) 'Fresh downloaded recovery ZIP drift'
 }
 # Independently reopen frozen original mapping+selection, rather than trust proposal row ordering.
 $first=@($p.local_archives|Where-Object name -CEQ 'master_public_history02-001.zip')
 Assert-True ($first.Count -eq 1) 'First recovered source archive missing'
 $fs=[IO.File]::Open($first[0].path,'Open','Read','Read');$zip=$null
 try{
  $zip=[IO.Compression.ZipArchive]::new($fs,[IO.Compression.ZipArchiveMode]::Read,$true)
  $ms=$zip.GetEntry('control/original_member_mapping.json').Open()
  try{Assert-True ((Get-StreamSha $ms) -ceq '014a540f8bfb11a31c9ea5d709562ea3669894b70fa2d300999b0a3df450c6cf') 'Original837 map hash differs'}finally{$ms.Dispose()}
  $map=Read-EntryJson $zip 'control/original_member_mapping.json';$selection=Read-EntryJson $zip 'control/selection.json'
  $native=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
  foreach($s in $selection.files){$native.Add($s.path,$s)}
  $mapped=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
  foreach($m in $map.files){$mapped.Add($m.original_path,$m)}
  Assert-True ($native.Count -eq 838 -and $mapped.Count -eq 837) 'Frozen original map/selection differs'
  foreach($row in $p.candidates){
   Assert-True ($mapped.ContainsKey($row.path) -and $native.ContainsKey($row.path)) 'Unrecovered candidate path'
   $m=$mapped[$row.path];$s=$native[$row.path]
   Assert-True ($m.asset_name -ceq $row.asset_name -and $m.member -ceq $row.member -and
    $m.member -ceq ('old_C_repo/'+$row.relative_path) -and $m.sha256 -ceq $row.sha256 -and $m.bytes -eq $row.bytes -and
    [string]$s.device -ceq $row.device -and [string]$s.file_id -ceq $row.file_id -and [string]$s.mtime_ns -ceq $row.mtime_ns -and $s.link_count -eq $row.link_count) 'Exact recovered original birth/content/member binding differs'
  }
 }finally{if($null -ne $zip){$zip.Dispose()};$fs.Dispose()}
 Check-Protected;Check-Preserved;Check-Owners
 if(-not $Run){[pscustomobject]@{state='AUTHORITY_RECOVERY_PREFLIGHT_NO_DELETE_LEAF_CONTENT_CHECKS_NOT_RUN';candidate_files=837;candidate_bytes=983926424}|ConvertTo-Json -Compress;return}
 $journalParent=[IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($Receipt));$journalChain=[Collections.Generic.List[string]]::new()
 while($null -ne $journalParent){$journalChain.Insert(0,$journalParent.FullName);$journalParent=$journalParent.Parent}
 foreach($d in $journalChain){$journalHandles+=([History02LeafApi]::LockDirectory($d))}
 $script:journal=[IO.FileStream]::new($Receipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read,4096,[IO.FileOptions]::WriteThrough)
 $script:writer=[IO.StreamWriter]::new($journal,[Text.UTF8Encoding]::new($false),4096,$true)
 Write-Event @{event='BEGIN';schema='MASTER_HISTORY02_LEAF_APPEND_RECEIPT_V1';plan_sha256=$PlanSha256;proposal_commit=$RemoteCommit;recovery_receipt_sha256=$RecoveryReceiptSha256;postverify_sha256=$p.batch03_postverify.sha256}
 $deleted=0;[long]$deletedBytes=0
 foreach($row in $p.candidates){
  Check-Owners;Check-Deadline;$target=Assert-Row $row $p
  $parent=[IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($target));$chain=[Collections.Generic.List[string]]::new()
  while($null -ne $parent){$chain.Insert(0,$parent.FullName);$parent=$parent.Parent}
  foreach($key in @($directoryHandles.Keys)){if(-not $chain.Contains($key)){$directoryHandles[$key].Dispose();$directoryHandles.Remove($key)}}
  foreach($d in $chain){if(-not $directoryHandles.ContainsKey($d)){$directoryHandles[$d]=[History02LeafApi]::LockDirectory($d)}}
  $stream=[IO.File]::Open($target,'Open','Read','None')
  try{
   Assert-Snapshot ([History02LeafApi]::Snapshot($stream.SafeFileHandle)) $row $target
   Assert-True ((Get-StreamSha $stream -WatchOwners) -ceq $row.sha256) 'Current actual leaf SHA drift'
   Assert-Snapshot ([History02LeafApi]::Snapshot($stream.SafeFileHandle)) $row $target;Check-Owners;Check-Deadline
   Write-Event @{event='VERIFIED_INTENT';index=($deleted+1);path=$target;bytes=$row.bytes;sha256=$row.sha256;device=$row.device;file_id=$row.file_id;mtime_ns=$row.mtime_ns}
  }finally{$stream.Dispose()}
  $verify=[IO.File]::Open($target,'Open','Read','None')
  try{Assert-Snapshot ([History02LeafApi]::Snapshot($verify.SafeFileHandle)) $row $target;Check-Owners;Check-Deadline}finally{$verify.Dispose()}
  # Explicit short close-to-literal-removal leaf race, matching previously reviewed discipline.
  Remove-Item -LiteralPath $target -ErrorAction Stop
  Assert-True (-not (Test-Path -LiteralPath $target)) 'Leaf remains/reappeared; preserve remainder'
  $deleted++;$deletedBytes+=$row.bytes
  Write-Event @{event='REMOVED';index=$deleted;path=$target;bytes=$row.bytes;sha256=$row.sha256;deleted=$deleted;deleted_bytes=$deletedBytes}
  if($deleted%25 -eq 0){[pscustomobject]@{state='PROGRESS';deleted=$deleted;deleted_bytes=$deletedBytes}|ConvertTo-Json -Compress}
 }
 Assert-True ($deleted -eq 837 -and $deletedBytes -eq 983926424) 'Final exact837 accounting differs'
 Check-Preserved;Check-Protected;Check-Owners;Check-Deadline
 Assert-True ((Get-FileSha $PSCommandPath) -ceq $p.script_sha256) 'Executor source changed before completion'
 Write-Event @{event='COMPLETE';state='PASS_EXACT837_RECOVERED_HISTORY_LEAVES_REMOVED';deleted=$deleted;deleted_bytes=$deletedBytes;excluded_preserved=1;excluded_bytes=1025;protected_hashes_unchanged=12;recursive_deletes=0}
}catch{
 if($null -ne $script:writer){Write-Event @{event='STOP';state='FAILED_PARTIAL_PRESERVE_REMAINDER';error=$_.Exception.Message}}
 throw
}finally{
 if($null -ne $script:writer){$script:writer.Dispose()};if($null -ne $script:journal){$script:journal.Dispose()}
 foreach($h in $directoryHandles.Values){$h.Dispose()};foreach($h in $journalHandles){$h.Dispose()}
 foreach($o in $script:owners){$o.process.Dispose()}
}
