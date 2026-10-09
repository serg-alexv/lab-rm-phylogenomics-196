# Stage4 primary196 host phylogeny

Stage4 primary196 accepted host phylogeny.

Exact approved196 taxa; accepted100-marker17456-aa Stage4a alignment.
IQ-TREE3.1.4; analysis mode partitioned; ModelFinder MFP;
1000 ultrafast bootstrap trees;1000 SH-aLRT replicates;
seed1961008;two threads;keep-ident;explicit unrooted tree.
The final selected model(s), fit statistics and warnings are in accepted/host.iqtree.
Native logs, exact command, source input hashes, actual native exit and
independent acceptance report are retained in accepted/.
The original partial model cache, when used, is a byte-preserved input;
it does not constitute a previously accepted complete tree.
All bootstrap trees and native support outputs are included.
Newick is authoritative; NEXUS preserves topology/length/support and unrooted state.
Composition/model warnings are retained; computational inference does not establish function.
Optional sensitivity analyses are separate and have not been used as completion gates.
R-M screening, curation, joining and final graphics belong to later stages.

The accepted alignment contains 182 distinct full aligned strings among all196 retained taxa. 8 exact-identity groups contain 22 taxa.
Within each exact-identity group, these host-marker data cannot resolve member ordering.
Displayed bifurcations or computed support do not supply distinguishing characters.
All196 genomes remain in the tree and subsequent genome-level R-M analysis.
The exact groups, checker, source review and source pins are in alignment_qa/.

Portable command, relative to the extracted ZIP root:
Create the new rerun directory and use the recorded IQ-TREE3.1.4 executable.
iqtree3 -s accepted/accepted_primary196_concatenated.faa --seqtype AA -p accepted/accepted_primary196_partitions.nex -m MFP -B 1000 --alrt 1000 --seed 1961008 -T 2 -keep-ident --boot-trees --prefix rerun/host
To reproduce the recorded cache recovery, copy accepted/original_input_model_cache.gz
unchanged to rerun/host.model.gz before launch; confirm its recorded SHA-256.

Scientific validation: COMPLETE_VALIDATED. Publication: prepared; upload/readback pending.
