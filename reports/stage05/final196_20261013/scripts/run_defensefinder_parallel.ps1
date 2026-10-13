param(
    [int]$Parallel = 2,
    [int]$MaxGenomes = 0
)

$ErrorActionPreference = "Stop"

$ROOT  = "$env:USERPROFILE\LAB_RM_STAGE5"
$IMAGE = "lab-rm-stage5:2026-10-12"

$manifest = @(Import-Csv "$ROOT\reference\genome_manifest.tsv" -Delimiter "`t")

$todo = @(
    $manifest | Where-Object {
        -not (Test-Path "$ROOT\results\$($_.assembly_id)\defensefinder\.complete")
    }
)

if ($MaxGenomes -gt 0) {
    $todo = @($todo | Select-Object -First $MaxGenomes)
}

Write-Host "DefenseFinder jobs to run: $($todo.Count)"
Write-Host "Parallel containers: $Parallel"

$worker = {
    param($ROOT,$IMAGE,$acc)

    $ErrorActionPreference = "Stop"

    $input = "$ROOT\defensefinder_input\$acc\defensefinder_gembase.faa"
    $out   = "$ROOT\results\$acc\defensefinder"
    $log   = "$ROOT\logs\$acc.defensefinder.log"

    New-Item -ItemType Directory -Force $out | Out-Null
    New-Item -ItemType Directory -Force "$out\index" | Out-Null

    $args = @(
        "run","--rm",
        "--mount","type=bind,source=$ROOT\defensefinder_input,target=/input,readonly",
        "--mount","type=bind,source=$ROOT\results,target=/results",
        $IMAGE,
        "micromamba","run","-n","base",
        "defense-finder","run",
        "/input/$acc/defensefinder_gembase.faa",
        "--db-type","gembase",
        "--out-dir","/results/$acc/defensefinder",
        "--index-dir","/results/$acc/defensefinder/index",
        "--preserve-raw",
        "--workers","1",
        "--skip-model-version-check"
    )

    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & docker @args 2>&1 |
        ForEach-Object { $_.ToString() } |
        Tee-Object -FilePath $log
    $exit = $LASTEXITCODE
    $ErrorActionPreference = $oldEAP

    $systems = "$out\defensefinder_gembase_defense_finder_systems.tsv"
    $genes   = "$out\defensefinder_gembase_defense_finder_genes.tsv"
    $hmmer   = "$out\defensefinder_gembase_defense_finder_hmmer.tsv"

    $valid = (
        $exit -eq 0 -and
        (Test-Path $systems) -and
        (Test-Path $genes) -and
        (Test-Path $hmmer) -and
        ((Get-Item $systems).Length -gt 0) -and
        ((Get-Item $genes).Length -gt 0) -and
        ((Get-Item $hmmer).Length -gt 0)
    )

    if ($valid) {
        Set-Content "$out\.complete" @(
            "DEFENSEFINDER_EXIT=0"
            "SOFTWARE=DefenseFinder_3.0.0"
            "MODELS=defense-finder-models_3.0.0"
            "CASFINDER=3.1.0"
            "DBTYPE=gembase"
            "PRESERVE_RAW=true"
        )
        return [PSCustomObject]@{assembly=$acc;status="COMPLETE";exit=$exit}
    }

    return [PSCustomObject]@{assembly=$acc;status="FAILED";exit=$exit}
}

$running = @()
$next = 0

while ($next -lt $todo.Count -or $running.Count -gt 0) {

    while ($next -lt $todo.Count -and $running.Count -lt $Parallel) {
        $acc = $todo[$next].assembly_id
        Write-Host "[$acc] START"
        $job = Start-Job -ScriptBlock $worker -ArgumentList $ROOT,$IMAGE,$acc
        $running += [PSCustomObject]@{Job=$job;Acc=$acc}
        $next++
    }

    Start-Sleep -Seconds 2

    $finished = @($running | Where-Object { $_.Job.State -in @("Completed","Failed","Stopped") })

    foreach ($item in $finished) {
        $result = Receive-Job $item.Job
        Remove-Job $item.Job -Force

        if ($result) {
            $result | Select-Object -Last 1 | Format-Table -AutoSize
        } else {
            Write-Warning "[$($item.Acc)] JOB FAILED WITHOUT RESULT"
        }

        $running = @($running | Where-Object { $_.Job.Id -ne $item.Job.Id })
    }
}
