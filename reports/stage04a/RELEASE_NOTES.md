# Validated host alignment substage

All100 source-validated host markers were aligned once with pinned MAFFT and trimAl. The separate BioPython checker independently verified every retained trim column, all four file formats, all source-locus blocks and exhaustive partitions for all four frozen analyses.

Primary196:196 tips,100 markers,17456 amino-acid columns. Sensitivity162:162 tips/100 markers/17456 columns. High-occupancy sensitivity:196 tips/88 markers/15174 columns. Complete Genome/Chromosome sensitivity:155 tips/100 markers/17456 columns. No primary genome was pruned.

Actual alignment elapsed954.60s, child CPU1343.42s, maximum child RSS102830080bytes, sampled concurrent RSS peak113598464bytes. Independent alignment audit elapsed25.11s, child CPU6.20s, maximum child RSS125972480bytes. These describe the recorded process scopes; sampling and shared-page limits remain in the native receipts.

At15:18:21UTC the controller stopped before IQ-TREE launch because the combined Windows/Linux headroom preflight failed. The original frozen threshold is greater than2147483648bytes available on both systems. The existing controller did not retain the failed-instant numeric snapshot; follow-up at15:19:05UTC showed Windows2132267008bytes and Linux7208030208bytes, identifying Windows below the threshold in that follow-up. At15:20:41UTC Windows free RAM measured4974198784bytes. No process was killed, no limit changed and no inference was launched on the failed preflight. The original failure and completed native exit receipts are preserved.

Scientific validation:PASS_ALIGNMENT_FORMATS_AND_PARTITIONS. Whole Stage4 phylogeny remains incomplete: no topology, UFBoot, SH-aLRT or sensitivity tree is claimed here. The unchanged controller can resume past completed align/check checkpoints only when its current resource gate passes.

No registered Geneious application or Geneious executable on PATH was found by the WD checks. Geneious import:NOT_RUN; formats were independently parser-tested.

Stage04a: independently validated full196 host alignments, not a completed phylogeny.
Extract this standalone ZIP with Windows Explorer or PowerShell. Every payload member is in SHA256SUMS.txt.
host_alignments/analyses contains primary196 and three sensitivity concatenations in FASTA/CLUSTAL/PHYLIP/NEXUS, partitions and exact source-block maps.
host_alignments/markers preserves raw and trimmed native alignments, column maps, four portable formats and scientific command/exit evidence.
Use exact versioned assembly IDs; missing marker blocks are gaps. Primary196 has100 markers/17456 amino-acid columns.
No IQ-TREE result, R-M inventory or figure is supplied or claimed by this substage. Those mandatory stages remain pending.
The actual executed Stage3 source/marker release is a separate dependency: stage03-hostmarkers196-v1.
