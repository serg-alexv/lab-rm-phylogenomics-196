# Full-run gene tree: ADK

State: COMPLETE_VALIDATED. Native completion was 2026-10-10T10:49:04Z. The same set-e pipeline advanced to ATP-synt_A, confirming this locus completed while the full run remains open.

Independent validation ran locally in Ubuntu WSL with the previously compiled and fixture-tested scripts/master_run/audit_completed_locus.py, unchanged at SHA256 3a0473c06478dbfa43589c7f8c7772d3488c90a277f074685dfa3bc12add98c3. See validation/execution_receipt.json for invocation, exit 0 and exact output hashes. The already accepted alignment manifest is pinned; the full alignment phase was not repeated.

| Check | Result |
|---|---|
| Input/alignment | 196 records, 224 columns, exact per-ID ungapped sequences |
| ML and consensus trees | Each has exactly all 196 input taxa; no duplicate, missing or extra tips |
| Selected model | WAG+I+G4, chosen by BIC |
| Bootstrap | Native reports state 1,000 requested and 1,000 consensus bootstrap trees |
| Numeric support | 150 labels each; ML 9-100, consensus 33-100 |
| Unlabeled internal nodes | 44 in each tree, including root; preserved without invented support |
| Native reduced data | 153 PHYLIP/split taxa, 806 splits; exact representative IDs and aligned sequences |
| Distinct exact aligned strings | 121; separate from the 153 native retained representatives |
| Total runtime | CPU 1161.243 seconds; wall 585.288 seconds |
| Stable artifacts | 12 audited: input, alignment and 10 native output files |

The approved IQ-TREE command does not save a separate .ufboot file, so the replicate count comes from the completed native report rather than independently counted replicate trees. All 196 taxa are restored in final tree outputs despite native identical-sequence reduction.

Native warnings are preserved verbatim: K=305 parameters versus n=224 sites, and 24 near-zero internal branches. These are computational integrity results; they do not establish strong biological resolution of this short locus.

The ten completed ADK artifacts include original model and checkpoint gzip files. No active ATP-synt_A scientific artifacts are published in this step. The process observation establishes the same original pipeline lineage; overall terminal/lock closure is still pending. ASTRAL awaits all 100 completed gene trees. The protected validator, pipeline source and scientific outputs were not modified.
