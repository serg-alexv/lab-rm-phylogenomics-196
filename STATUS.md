# Current master run status

Updated 2026-10-10T10:49:46.101161+00:00. The user-approved full 100-marker gene-tree/ASTRAL run is active locally in Ubuntu WSL.

| Component | Verified state |
|---|---|
| Full-run MAFFT alignments | COMPLETE_VALIDATED: 100 loci, 19,359 sequences, exact approved union of 196 genomes; 20,957 columns across loci |
| Full-run IQ-TREE | 1/100 COMPLETE_VALIDATED: `5-FTHF_cyc-lig`; `ADK` running, 98 pending at 10:45 UTC observation |
| Full-run ASTRAL | NOT_RUN; waits for all 100 gene trees |
| Five-marker pilot | COMPLETE_VALIDATED: five trees, 196 ASTRAL tips; raw and flat-q1 outputs preserved |
| Historical concatenated primary Stage 4 | Previously COMPLETE_VALIDATED and Release UPLOAD_VERIFIED; accepted outputs preserved |
| Stage 5 defense detection and curation | NOT_RUN |
| Final defense figure and biological review | NOT_RUN; host is not ready to wipe |

All input hashes match the approved manifest. Each alignment preserves its input IDs and exact amino-acid sequence after documented case/whitespace normalization and removal of alignment gaps. All sequences within each locus have equal aligned length; input and output hashes remained stable during the independent WSL audit. See [alignment results](reports/stage01/local_full100_20261010/alignment_complete89/ALIGNMENT_RESULT.md) and [native audit receipt](reports/stage01/local_full100_20261010/alignment_complete89/validation/receipt.json).

The first locus finished natively at 2026-10-10T10:39:17Z and passed independent local WSL validation. Its final tree and consensus each contain exactly the 189 taxa in that locus's input, with 1,000 bootstrap trees reported by IQ-TREE. Each has 153 numeric support labels in range 0-100 and 34 unlabeled internal nodes, which remain unlabeled. Native warnings about 338 parameters versus 210 sites and 17 near-zero internal branches are preserved. See [first-locus results](reports/stage01/local_full100_20261010/genes/5-FTHF_cyc-lig/RESULT.md) and [validation receipt](reports/stage01/local_full100_20261010/genes/5-FTHF_cyc-lig/validation/execution_receipt.json).

The same full run remains active under its original workflow lock. At 10:45:05 UTC, Windows owner 31816, wrapper bash 4019 and pipeline bash 4023 retained their original creation identities; IQ-TREE PID 15548 (start ticks 2119388, parent 4023) was computing ADK. The unchanged script SHA256 is `5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b`; the active command uses `-m MFP -bb 1000 -nt 2 -mem 3000M`. Full-run terminal receipts remain absent. The protected validator is untouched. All 115 files from the completed alignment publication were independently read back with matching hashes; its receipt is included in this update.


Pilot visualization: [PDF](pilot_output/itol_visual_check_20261010/pilot_196_taxa.pdf), [SVG](pilot_output/itol_visual_check_20261010/pilot_196_taxa.svg), and [account tree](https://itol.embl.de/tree/15124432167298281791625397). Both exports contain all 196 labels. The ring represents operational taxonomic groups, not Host or defense calls. iTOL subscription restrictions prevent server-side annotation saving and batch API upload; the account tree is bare after reopening, while local exports preserve the styled draft. The legend overlaps some labels, so the layout remains a draft.

Completed first-locus outputs and checkpoint/model files are preserved unchanged. No active ADK outputs are included. Scientific completion and remote byte verification are separate: the publisher verifies this commit after advancing main. Earlier status and evidence remain in Git history. No new pipeline was started and no scientific output was overwritten.
