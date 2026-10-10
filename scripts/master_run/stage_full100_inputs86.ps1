$ErrorActionPreference = 'Stop'
$project = 'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196'
$manifest = Join-Path $PSScriptRoot 'full100_input_audit86\marker_sources.tsv'
$receipt = Join-Path $PSScriptRoot 'full100_input_audit86\staging_receipt.json'
if (Test-Path -LiteralPath $receipt) { throw 'Preserve staging receipt' }
if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'c4f5d8c7c9a1622c4cad2ef943e3c03db0ee592aa9389d43bf28b206ff745a62') { throw 'Audit manifest changed' }
$rows = @(Import-Csv -LiteralPath $manifest -Delimiter "`t")
if ($rows.Count -ne 100) { throw 'Expected100 markers' }
$lockPath = 'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock'
$lock = [IO.File]::Open($lockPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$created = @()
try {
    foreach ($row in $rows) {
        $source = Join-Path $project $row.source_path
        $target = Join-Path $project ('input_genes\' + $row.marker + '.fasta')
        if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw "Source changed: $($row.marker)" }
        if (Test-Path -LiteralPath $target) {
            if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw "Existing input differs: $($row.marker)" }
        }
    }
    foreach ($row in $rows) {
        $target = Join-Path $project ('input_genes\' + $row.marker + '.fasta')
        if (-not (Test-Path -LiteralPath $target)) {
            $data = [IO.File]::ReadAllBytes((Join-Path $project $row.source_path))
            $stream = [IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
            try { $stream.Write($data,0,$data.Length) } finally { $stream.Dispose() }
            $created += $row.marker
        }
        if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw "Staged bytes differ: $($row.marker)" }
    }
    if (@(Get-ChildItem -LiteralPath (Join-Path $project 'input_genes') -Filter '*.fasta' -File).Count -ne 100) { throw 'Unexpected input count' }
} finally { $lock.Dispose() }
[ordered]@{state='PASS_100_INPUTS_STAGED';utc=[DateTime]::UtcNow.ToString('o');new_files=$created.Count;preserved_existing_files=(100-$created.Count);markers=100;records=19359;taxa=196;all_source_and_target_hashes_verified=$true;original_lock_released=$true;scientific_execution=$false} | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding utf8
Get-Content -LiteralPath $receipt
