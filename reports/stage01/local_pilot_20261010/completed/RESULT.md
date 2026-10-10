# Five-marker pilot completed and validated

The original approved Bash attempt02 exited0 on2026-10-10 at08:36:34 UTC
(11:36:34 Europe/Moscow). All five IQ-TREE markers and ASTRAL completed locally.
No inference was restarted. The original lock was opened exclusively after exit
and released without changing its bytes; the owned runner processes are gone.

Species tree: pilot_output/species_tree.newick,196 unique approved accessions.
All973 input records retain their exact ungapped sequences through alignment.
Each gene tree matches its own FASTA taxa, and all_gene_trees.tre is their exact
byte concatenation. All five native reports confirm1000 UFBoot replicates.

The independent pre-existing v2 validator passed all193 informative ASTRAL splits.
Raw structured ASTRAL output is preserved. A separate iTOL Newick uses numeric q1
quartet frequencies and preserves topology and branch lengths; q1 is not pp1.
ASTRAL warns about limited effective gene counts (4-5), so this five-locus pilot
establishes workflow integrity, not production phylogenetic reliability.
Native terminal branch lengths are absent where ASTRAL did not estimate them.
Unlabeled IQ-TREE supports remain explicitly unlabeled in the validation report.

scripts/validate_pipeline.py was not accessed, changed, or executed. The existing
run_pipeline.sh was not replaced. Full100-marker execution remains unapproved;
only five input FASTAs are staged. Missing cell_mapping.tsv means host and defense
decorations cannot yet be generated. Pilot-tree iTOL upload is the next requested
step and will use a separate pilot name, preserving the production boundary.
