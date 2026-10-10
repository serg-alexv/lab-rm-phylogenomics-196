$ErrorActionPreference = 'Stop'
$project = 'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196'
$receiptDir = Join-Path $project 'reports\stage01\local_full100_20261010\attempt01'
$runner = Join-Path $project 'scripts\master_run\full100_runner86.sh'
$lockPath = 'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock'
$expected = '5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b'
if ((Get-FileHash -LiteralPath (Join-Path $project 'run_pipeline.sh') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Approved pipeline hash changed' }
if (Test-Path -LiteralPath $receiptDir) { throw 'Refusing previous full-run attempt' }
foreach ($path in @('full_run.log','species_tree.newick','pipeline_output\all_gene_trees.tre','reports\stage01\mafft_align.log','reports\stage01\iqtree_progress.log','reports\stage01\astral_run.log')) {
    if (Test-Path -LiteralPath (Join-Path $project $path)) { throw "Refusing existing output: $path" }
}
foreach ($folder in @('pipeline_output\alignments','pipeline_output\trees')) {
    $fullFolder = Join-Path $project $folder
    if ((Test-Path -LiteralPath $fullFolder) -and @(Get-ChildItem -LiteralPath $fullFolder -Force).Count -gt 0) { throw "Refusing nonempty $folder" }
}
$manifestPath = Join-Path $project 'reports\stage01\local_full100_20261010\preparation\marker_sources.tsv'
if ((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'c4f5d8c7c9a1622c4cad2ef943e3c03db0ee592aa9389d43bf28b206ff745a62') { throw 'Audited manifest hash changed' }
$rows = @(Import-Csv -LiteralPath $manifestPath -Delimiter "`t")
$inputFiles = @(Get-ChildItem -LiteralPath (Join-Path $project 'input_genes') -Filter '*.fasta' -File)
if ($rows.Count -ne 100 -or $inputFiles.Count -ne 100 -or @($rows.marker | Sort-Object -Unique).Count -ne 100) { throw 'Full run requires exactly100 unique audited inputs' }
if (@(Compare-Object @($rows | ForEach-Object { $_.marker + '.fasta' }) @($inputFiles.Name)).Count -ne 0) { throw 'FASTA filenames differ from audited manifest' }
foreach ($row in $rows) {
    if ($row.marker -notmatch '^[A-Za-z0-9_.-]+$' -or $row.sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Malformed audited marker or digest' }
    if ((Get-FileHash -LiteralPath (Join-Path $project ('input_genes\' + $row.marker + '.fasta')) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw "Input changed: $($row.marker)" }
}
if (Test-Path -LiteralPath (Join-Path (Split-Path $lockPath) 'stage05_owned_closure_unproven.json')) { throw 'Unresolved native STOP' }
$lock = [IO.File]::Open($lockPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$started = [DateTime]::UtcNow.ToString('o')
$returnCode = $null
try {
    [IO.Directory]::CreateDirectory($receiptDir) | Out-Null
    $identity = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"
    [ordered]@{state='RUNNING';started_utc=$started;powershell_pid=$PID;powershell_creation_utc=$identity.CreationDate.ToUniversalTime().ToString('o');command='nohup bash scripts/master_run/full100_runner86.sh';pipeline_command='PILOT_ONLY=0 bash run_pipeline.sh';script_sha256=$expected;runner_sha256=(Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash.ToLowerInvariant();original_lock_opened_exclusively=$true;full_pipeline_authorized=$true;markers=100;taxa=196;itol_dependency=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $receiptDir 'launch.json') -Encoding utf8
    & wsl.exe -d Ubuntu -u root --cd '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196' --exec /usr/bin/nohup /bin/bash scripts/master_run/full100_runner86.sh 2>&1 | Tee-Object -FilePath (Join-Path $receiptDir 'launcher_console.log')
    $returnCode = $LASTEXITCODE
} finally {
    $lock.Dispose()
    [ordered]@{state=$(if ($returnCode -eq 0) {'SCRIPT_EXITED_ZERO_VALIDATION_PENDING'} else {'SCRIPT_FAILED_STOPPED'});started_utc=$started;finished_utc=[DateTime]::UtcNow.ToString('o');exit_code=$returnCode;original_lock_handle_disposed=$true;full_pipeline_started=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $receiptDir 'terminal.json') -Encoding utf8
}
exit $returnCode
