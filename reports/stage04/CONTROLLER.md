# WD Stage4 production controller

The root agent owns Git publication, the workflow lock and biological execution. The reviewed controller and checker sources have been adopted into `scripts/`; all58 preparation fixtures passed. Reviewers ran no biological alignment or inference. Actual production state and independent scientific gates are recorded separately in `progress.json` and the final stage reports.

Adopt `stage04_controller.py`, `stage04_linux_launcher.py`, updated `stage04_phylogeny.py` and `stage04_validate.py` into `scripts/`. Keep the controller and strict orthology synthetic check scripts beside them when invoking `--self-test`. The controller requires an explicit current marker view, independent marker validation and verified Stage03 publication. Original v1 source/HMM/fixed-filter integrity remains independently passed while its duplicated MiaA signal retains the scientific blocked status. Curated v2 must independently verify the exact whole-family IPT subtraction, original119/196 thresholds, additional unique-length96 recovery,100 retained profiles/19359 sequences and zero duplicated retained loci. The final Stage4 reader independently checks both certificates and actual source subtraction.

The single Stage03 verified release receipt must bind these four current bytes: `curated_validation_summary_sha256`, `original_validation_summary_sha256`, `orthology_curation_config_sha256`, `orthology_curation_receipt_sha256`. Existing asset readback fields remain mandatory. Stage4 cannot start using a generic or mismatched release receipt.

Run and resume with the same arguments from the dedicated repository:

```powershell
& .tools/validation_env/Scripts/python.exe scripts/stage04_controller.py `
  --markers .work/stage03_orthology_v2 `
  --marker-validation .work/stage03_curated_validation/validation_summary.json `
  --marker-publication reports/stage03/publication_receipt.json `
  --config config/host_primary_stage03_v1.json `
  --orthology-config config/host_orthology_stage03_v2.json `
  --original-markers .work/stage03_markers_v1 `
  --original-marker-validation .work/stage03_marker_validation/validation_summary.json `
  --output .work/stage04_phylogeny_v2 `
  --alignment-validation .work/stage04_alignment_validation `
  --final-validation .work/stage04_final_validation
```

This command acquires the real Windows byte lock at `.work/workflow.lock`, fetches/reconciles canonical main, measures current RAM/disk, freezes a separate resource receipt and publishes prompt sanitized progress. It then waits sequentially through actual alignment, independent alignment/partition validation, actual inference and independent final validation. At most two cores, two numerical-library threads and2GiB address space are applied to every native process; IQ-TREE requests1536MiB. Current free Windows/Linux RAM must exceed2GiB, and measured local disk must exceed5GiB. The immutable preflight is retained on resume; live snapshots are separate. Root may choose a lower256..1536MiB IQ-TREE setting before initial launch, with matching resource receipt; no automatic memory increase occurs.

The Linux observer writes exact launcher/job PID, kernel start ticks and boot ID before monitoring. It preserves actual argv, exits, elapsed/CPU, maximum child RSS and sampled concurrent process RSS, documenting the sampling/shared-page limits. Windows records actual WSL launcher PID/creation time. Every five minutes the same owner selects sanitized command/process/QC evidence and pushes only `STATUS.md`, `status/stages.tsv`, `status/stage04_execution.json`, `reports/stage04/progress.json`, `reports/stage04/resource_preflight.json`; it verifies the remote commit and all five fetched file hashes. Private scientific stdout/stderr and lifecycle receipts remain under `.work/`. No private model/session events are read or published.

Resume checks cached gate hashes and actual exit receipts. A verified existing Linux child is monitored through its current observer without a second job. A stale PID, missing exit receipt, changed source/code/config, lost observer or failed independent scientific gate is an explicit blocker. A progress-publish failure waits for the current actual child to exit, preserves its measured receipt and prevents a dependent phase. No unrelated process is stopped; no sentinels are treated as validation; no script forces a Git push or topology restart.

Once all four phases finish, Stage4 scientific validation is recorded and progress is verified. Portable Stage4 ZIP packaging, immutable release upload/readback and subsequent Stage5 remain separate mandatory root-owned actions; the controller does not claim their completion.

Reviewer checks:21 pure controller fixtures,17 strict orthology producer/independent-certificate fixtures and20 prior alignment/partition/format/support fixtures passed. The tiny native stdlib observer probe ran on WD with affinity[0,1],2GiB cap, exact PID/start/boot receipts and real exit0/CPU/elapsed/RSS; it used no sequences, HMMs, alignment or inference. An own-Windows-PID/CIM resource/path probe also passed. These are code/resource checks, not scientific PASS.
