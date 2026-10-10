# Evidence used to review the five-marker pilot

The review is of execution, data integrity and output format. It does not establish
biological reliability of a species topology inferred from only five loci.

| Check | Required evidence |
| --- | --- |
| Execution closure | attempt02/terminal.json exit0, original launcher/process identities and original lock release |
| Inputs and alignments | Five selected FASTAs; each alignment has exactly its own input identifiers and identical ungapped sequences |
| Per-gene inference | Native .log completion, .iqtree report, 1000 UFBoot replicates and parseable .treefile with exact input tips |
| Missing taxa | Each locus has its own expected set; ASTRAL must equal the union of selected marker taxa, with no duplicates or extra tips |
| Supports | Finite numeric values in their documented range; every unlabeled IQ-TREE branch recorded explicitly without imputation |
| ASTRAL | Exact concatenation of five accepted trees; native version/completion evidence; structured -t2 annotations validated |
| iTOL derivative | Preserve native ASTRAL bytes; separate flat q1-frequency tree must preserve topology and branch lengths |
| Publication | Sources, native artifacts, validation receipts, SHA256 values and independent readback of actual GitHub bytes |

Use explicit --mode pilot or --mode full. Both output folders exist in either
mode, so folder existence cannot identify scope. Pilot requires five selected
markers and their actual union; full mode requires100 markers and all196 approved
accessions. The currently staged five-marker union is196. A 189-tip gene tree is
valid when that marker's FASTA contains189 taxa.

At 2026-10-10 07:58 UTC, two markers were completed and independently validated:

| Marker | Tips | Aligned columns | Selected model | Numeric support labels | Unlabeled internal branches |
| --- | ---: | ---: | --- | --- | ---: |
| 5-FTHF_cyc-lig | 189 | 210 | Q.PFAM+F+I+R5 | 153; range5-100 | 33 |
| ADK | 196 | 224 | WAG+I+G4 | 150; range6-100 | 43 |

Both preserve every input sequence and have native evidence of1000 bootstrap
replicates and finite nonnegative branch lengths. ATP-synt is running. The last
two markers and ASTRAL remain pending. Intermediate treefile presence alone is
not native completion. No real GLOBAL_PIPELINE_STATUS: PASS is claimed yet.

Validator positive and truncation-negative tests use isolated synthetic fixtures.
Their PASS proves the test expectations; it is not a PASS for this unfinished pilot.
The original scientific files are never corrupted for a validator test.

Only after successful closure, final validation and remote readback will the user
be asked to approve a full100-marker run. Five staged input files cannot stand in
for that full dataset. Decoration input cell_mapping.tsv remains absent, so no
defense-system presence/absence or host categories have been fabricated.
