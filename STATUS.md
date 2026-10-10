# Current master run status

Updated 2026-10-10T10:19:25.319810+00:00. The user-approved full 100-marker gene-tree/ASTRAL run is active locally in Ubuntu WSL.

| Component | Verified state |
|---|---|
| Full-run MAFFT alignments | COMPLETE_VALIDATED: 100 loci, 19,359 sequences, exact approved union of 196 genomes; 20,957 columns across loci |
| Full-run IQ-TREE | RUNNING: first marker `5-FTHF_cyc-lig`, ModelFinder; no completed gene tree at observation |
| Full-run ASTRAL | NOT_RUN; waits for all 100 gene trees |
| Five-marker pilot | COMPLETE_VALIDATED: five trees, 196 ASTRAL tips; raw and flat-q1 outputs preserved |
| Historical concatenated primary Stage 4 | Previously COMPLETE_VALIDATED and Release UPLOAD_VERIFIED; accepted outputs preserved |
| Stage 5 defense detection and curation | NOT_RUN |
| Final defense figure and biological review | NOT_RUN; host is not ready to wipe |

All input hashes match the approved manifest. Each alignment preserves its input IDs and exact amino-acid sequence after documented case/whitespace normalization and removal of alignment gaps. All sequences within each locus have equal aligned length; input and output hashes remained stable during the independent WSL audit. See [alignment results](reports/stage01/local_full100_20261010/alignment_complete89/ALIGNMENT_RESULT.md) and [native audit receipt](reports/stage01/local_full100_20261010/alignment_complete89/validation/receipt.json).

The full run began at 2026-10-10T09:31:05.9280558Z under the original workflow lock. The unchanged plain Bash script SHA256 is `5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b`. At the phase observation, the same owner and pipeline process identities were present, and IQ-TREE PID 15472 was running with `-m MFP -bb 1000 -nt 2 -mem 3000M`. The IQ-TREE process began at 10:06:25 UTC; native CPU usage subsequently advanced at approximately two cores. Full-run terminal receipts are absent because the pipeline is still running. `scripts/validate_pipeline.py` remains untouched.

Pilot visualization: [PDF](pilot_output/itol_visual_check_20261010/pilot_196_taxa.pdf), [SVG](pilot_output/itol_visual_check_20261010/pilot_196_taxa.svg), and [account tree](https://itol.embl.de/tree/15124432167298281791625397). Both exports contain all 196 labels. The ring represents operational taxonomic groups, not Host or defense calls. iTOL subscription restrictions prevent server-side annotation saving and batch API upload; the account tree is bare after reopening, while local exports preserve the styled draft. The legend overlaps some labels, so the layout remains a draft.

This update replaces stale top-level launch-pending and unapproved-run wording. Earlier evidence is preserved in Git history and [the previous status](https://github.com/serg-alexv/lab-rm-phylogenomics-196/blob/06918f30a83fb620908b0d29c34e688d8f69a890/STATUS.md). Scientific completion and GitHub byte verification are separate; the publisher records remote verification after this commit is created. No scientific output was overwritten, no active checkpoint was copied or modified, and no new pipeline was started.
