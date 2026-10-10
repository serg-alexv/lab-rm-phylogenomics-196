# Full 100-marker local run authorized

On 2026-10-10 the user explicitly authorized the full 100-marker run in the
background, with iTOL independent of inference and validate_pipeline.py untouched.
This supersedes the earlier pilot-only approval boundary. Scientific execution
remains local on WD Ubuntu WSL. No pipeline source flags or science methods change.

All 100 unaligned per-marker FASTAs are byte-identical to validated Stage 3 v2
sources: 19,359 sequences across exactly 196 approved accessions. There are 241
missing marker/taxon combinations, handled per locus. Duplicate accession headers
are absent; identical protein sequences across distinct taxa are retained.
Five staged inputs are preserved; 95 missing inputs were created without overwrites.

The approved run_pipeline.sh SHA256 remains
5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b.
Its full branch runs MAFFT --auto per locus, IQ-TREE -m MFP -bb 1000 -nt 2
-mem 3000M per alignment, then concatenates all 100 gene trees for ASTRAL -t 2.
Scientific outputs are pipeline_output/ and the final root species_tree.newick;
pilot outputs remain unchanged. Source filename ordering is the Bash glob order.

The hidden Windows owner holds the original exclusive workflow.lock while the
foreground WSL nohup Bash runner waits for its pipeline child. Launch and terminal
receipts retain boot identity, process start identity, hashes, commands and exits.
The wrapper refuses existing science outputs and logs. Failure stops the run;
there is no automatic rerun or replacement of checkpoints. iTOL is not invoked by
the scientific script. Full-run result acceptance remains pending real execution.

The copied iTOL bundle contains LABELS and TREE_COLORS for display labels and ten
operational taxonomic groups. It contains no defense-system calls or host traits.
These templates do not use DATASET_BINARY or DATASET_COLORSTRIP. A rendered pilot
checks display compatibility, not biological reliability of the final result.
