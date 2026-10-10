# Current master run status

Updated 2026-10-10T10:52:19.880611+00:00. The user-approved full 100-marker gene-tree/ASTRAL run is active locally in Ubuntu WSL.

| Component | Verified state |
|---|---|
| Full-run MAFFT alignments | COMPLETE_VALIDATED: 100 loci, 19,359 sequences, exact approved union of 196 genomes; 20,957 columns across loci |
| Full-run IQ-TREE | 2/100 COMPLETE_VALIDATED: `5-FTHF_cyc-lig` and `ADK`; `ATP-synt_A` running, 97 pending at 10:51 UTC observation |
| Full-run ASTRAL | NOT_RUN; waits for all 100 gene trees |
| Five-marker pilot | COMPLETE_VALIDATED: five trees, 196 ASTRAL tips; raw and flat-q1 outputs preserved |
| Historical concatenated primary Stage 4 | Previously COMPLETE_VALIDATED and Release UPLOAD_VERIFIED; accepted outputs preserved |
| Stage 5 defense detection and curation | NOT_RUN |
| Final defense figure and biological review | NOT_RUN; host is not ready to wipe |

All input hashes match the approved manifest. Each alignment preserves its input IDs and exact amino-acid sequence after documented case/whitespace normalization and removal of alignment gaps. All sequences within each locus have equal aligned length; input and output hashes remained stable during the independent WSL audit. See [alignment results](reports/stage01/local_full100_20261010/alignment_complete89/ALIGNMENT_RESULT.md) and [native audit receipt](reports/stage01/local_full100_20261010/alignment_complete89/validation/receipt.json).

The first locus finished natively at 2026-10-10T10:39:17Z and passed independent local WSL validation. Its final tree and consensus each contain exactly the 189 taxa in that locus's input, with 1,000 bootstrap trees reported by IQ-TREE. Each has 153 numeric support labels in range 0-100 and 34 unlabeled internal nodes, which remain unlabeled. Native warnings about 338 parameters versus 210 sites and 17 near-zero internal branches are preserved. See [first-locus results](reports/stage01/local_full100_20261010/genes/5-FTHF_cyc-lig/RESULT.md) and [validation receipt](reports/stage01/local_full100_20261010/genes/5-FTHF_cyc-lig/validation/execution_receipt.json).

ADK finished natively at 2026-10-10T10:49:04Z and passed the same independent local WSL audit: 196 exact input taxa in each tree, 224 alignment columns, and 1,000 consensus bootstrap trees reported natively. Both trees have 150 numeric support labels and 44 unlabeled internal nodes. WAG+I+G4 was selected by BIC. Native warnings concerning 305 parameters versus 224 sites and 24 near-zero internal branches are retained. See [ADK results](reports/stage01/local_full100_20261010/genes/ADK/RESULT.md) and [its validation receipt](reports/stage01/local_full100_20261010/genes/ADK/validation/execution_receipt.json).

The original full run was observed active at 10:51:26 UTC under Windows owner 31816, wrapper bash 4019 and pipeline bash 4023, all with their original creation identities. Child IQ-TREE PID 15624, start ticks 2178131, parent 4023, was computing ATP-synt_A with the approved two-thread command. The unchanged script SHA256 is `5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b`. Overall terminal receipts were absent. The protected validator remains untouched. Both prior milestones were independently verified from GitHub: 115 alignment-publication files and 33 first-locus files; their verification receipts are retained.



Pilot visualization: [PDF](pilot_output/itol_visual_check_20261010/pilot_196_taxa.pdf), [SVG](pilot_output/itol_visual_check_20261010/pilot_196_taxa.svg), and [account tree](https://itol.embl.de/tree/15124432167298281791625397). Both exports contain all 196 labels. The ring represents operational taxonomic groups, not Host or defense calls. iTOL subscription restrictions prevent server-side annotation saving and batch API upload; the account tree is bare after reopening, while local exports preserve the styled draft. The legend overlaps some labels, so the layout remains a draft.

The two completed loci and their original model/checkpoint files are preserved. This update includes only completed ADK artifacts; active ATP-synt_A artifacts are excluded. The publisher checks this commit's remote bytes after advancing main. Earlier evidence remains in Git history. No new pipeline was started and no scientific output was overwritten.
