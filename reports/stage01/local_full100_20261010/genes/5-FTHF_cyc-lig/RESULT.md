# First full-run gene tree: 5-FTHF_cyc-lig

State: COMPLETE_VALIDATED. IQ-TREE finished at 2026-10-10T10:39:17Z; the original set-e pipeline advanced to ADK. This establishes per-locus completion, not overall process or lock closure.

The independent Python audit ran locally in Ubuntu WSL and exited 0. It checked the exact locus input, alignment, final tree, consensus, reduced PHYLIP sequences, split file, native report/log and stable hashes. Its source hash and invocation are in validation/execution_receipt.json. The alignment manifest is pinned to the already accepted all-100-locus audit; that phase was not repeated.

| Check | Result |
|---|---|
| Input and alignment | 189 records; 210 aligned columns; exact IDs and ungapped sequences |
| ML tree and consensus tips | 189 each; zero missing, extra or duplicate taxa |
| Selected model | Q.PFAM+F+R6 (BIC) |
| Bootstrap | 1,000 requested and 1,000 used in consensus, according to native report |
| Numeric support labels | 153 in each tree; ML 5-100, consensus 6-100 |
| Unlabeled internal nodes | 34 in each tree, including root; left unchanged |
| Reduced native data | 156 PHYLIP/split taxa and 897 splits; exact representative IDs and sequences |
| Literal distinct aligned strings | 129; this differs from the 156 native retained representatives |
| Native total runtime | CPU 3918.038 seconds; wall 1968.485 seconds |
| Stable files audited | 12: input, alignment and 10 native artifacts |

The default approved command did not retain a separate .ufboot file. The replicate count is established by the native completion report, not an independent count of stored replicate trees. The reduced PHYLIP/splits use fewer representatives; the final tree and consensus restore all 189 input taxa. Seven of the approved 196 genomes lack this locus in the staged data, as already recorded by the input audit.

Native warnings are retained verbatim in validation/native_warnings.txt and the original report: parameter count K=338 exceeds site count n=210, and 17 near-zero internal branches require caution. Passing integrity checks does not establish that this individual short locus strongly resolves species relationships.

The separate audit parser was compiled and exercised with valid and malformed fixtures (missing semicolon, unterminated quote, nonfinite and negative branch lengths). The initial audit and source are retained under preliminary/; validation/ contains the final strict receipt. The main pipeline, scientific results and protected validator were not modified.

Publication includes only this completed prefix, its validation evidence, the observed transition to ADK and the previous alignment publication's verified remote hashes. Active ADK artifacts are excluded. ASTRAL remains pending all 100 completed gene trees.
