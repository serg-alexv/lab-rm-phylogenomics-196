# Local five-marker pilot, 2026-10-10

Latest direct user instructions authorize the exact attached `run_pipeline.sh`, local Bash loops in Ubuntu WSL, and five existing validated marker FASTAs. This request supersedes historical no-pilot/no-pause directions for this pilot only. The full pipeline needs a new confirmation after pilot completion. No full pipeline has been launched.

The existing master dataset has 100 core markers across 196 approved assemblies, not 196 loci. The first five marker names in lexical order are selected. Four contain 196 taxa; 5-FTHF_cyc-lig contains 189. Inputs are unchanged unaligned amino-acid sequences copied from the accepted stage03 marker collection. Input hashes and source paths are in input_manifest.json. Existing accepted Stage4 results are preserved.

The requested script is byte-identical to the attachment and passes `bash -n`. It uses MAFFT --auto, IQ-TREE -m MFP -bb 1000 -nt 2 -mem 3000, then ASTRAL -t 2. It activates /root/miniconda3/envs/phylogeny. Live conda metadata reports MAFFT 7.526, IQ-TREE 3.1.4, astral-tree 5.7.8, and SeqKit 2.14.0. Tool exit logs and result validation follow execution.

Working directory: canonical lab-rm-phylogenomics-196 checkout. Command: `PILOT_ONLY=1 bash run_pipeline.sh`. Outputs: pilot_output/ and reports/stage01/pilot_*.log. The script also creates empty pipeline_output directories. No existing output is overwritten. Stop on the first error. No rm/mv/overwrite without the user's permission.

Scientific status: pilot prepared, not run. This pilot is a five-gene ASTRAL methods check; it does not replace the accepted 100-marker Stage4 tree and does not complete R-M detector Stage5 or curated Stage6 results. No biological absence is inferred from incomplete work. Full run would require staging the remaining approved markers; a five-file input directory must never be called the full 100-marker dataset.

Previously completed current-boot G-drive diagnosis/mount closure evidence and reviewed recovery/cleanup sources are archived in this commit. Recovery and cleanup sources remain NOT RUN; the latest ask-before-delete instruction is in force. No VM image is split or removed.
