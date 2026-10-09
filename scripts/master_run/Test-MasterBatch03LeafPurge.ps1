param([Parameter(Mandatory=$true)][string]$Fixture)
$ErrorActionPreference='Stop'
. "$PSScriptRoot\Invoke-MasterBatch03LeafPurge.ps1" -LibraryOnly
Initialize-LeafApi
$f=Get-Content -LiteralPath $Fixture -Raw|ConvertFrom-Json -Depth 20
$count=0
function Expect-Failure([scriptblock]$action){
 $failed=$false;try{$null=&$action}catch{$failed=$true}
 Assert-True $failed 'Expected negative fixture rejection';$script:count++
}
$stream=[IO.File]::Open($f.path,'Open','Read','None')
try{
 $snapshot=[Batch03LeafApi]::Snapshot($stream.SafeFileHandle)
 Assert-Snapshot $snapshot $f $f.path
 Assert-True ((Get-StreamSha $stream) -ceq $f.sha256) 'Actual fixture SHA differs';$count++
 foreach($key in @('device','file_id','bytes','mtime_ns','link_count')){
  $bad=$f|ConvertTo-Json -Depth 20|ConvertFrom-Json -Depth 20
  $bad.$key=if($key -eq 'device' -or $key -eq 'file_id'){'1'}else{0}
  Expect-Failure {Assert-Snapshot $snapshot $bad $f.path}
 }
 Expect-Failure {$other=[IO.File]::Open($f.path,'Open','Read','None');$other.Dispose()}
}finally{$stream.Dispose()}
$dir=[Batch03LeafApi]::LockDirectory([IO.Path]::GetDirectoryName($f.path))
try{Assert-True (-not $dir.IsInvalid) 'Directory handle invalid';$count++}finally{$dir.Dispose()}
Expect-Failure {$bad=[Batch03LeafApi]::LockDirectory([IO.Path]::GetDirectoryName($f.path)+'\.');$bad.Dispose()}
$fixturePlan=[pscustomobject]@{old_root='C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196';allowed_scopes=@('data')}
Assert-True ((Assert-Row $f.row $fixturePlan) -ceq $f.row.path) 'Valid pure row rejected';$count++
foreach($rel in @('data/../file','data//file','data/file:ads','data/file.','data/.tools/file','data/a.lock')){
 $bad=$f.row|ConvertTo-Json -Depth 20|ConvertFrom-Json -Depth 20;$bad.relative_path=$rel
 Expect-Failure {Assert-Row $bad $fixturePlan}
}
$self=[Diagnostics.Process]::GetProcessById($PID);$null=$self.Handle
try{
 $script:owners=@(@{process=$self;birth=$self.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()})
 Check-Owners;$count++
 $script:owners[0].birth='1';Expect-Failure {Check-Owners}
}finally{$self.Dispose()}
[pscustomobject]@{state='PASS_NONDESTRUCTIVE_WINDOWS_FIXTURE';checks=$count;actual_device=$snapshot.Device;
 actual_file_id=$snapshot.FileId;actual_mtime_ns=$snapshot.MtimeNs;source_deletions=0;network_calls=0;g_writes=0}|ConvertTo-Json -Compress
