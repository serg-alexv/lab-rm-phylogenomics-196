# Stage 5 release notes — R-M inventory196 v1

This release freezes the completed and validated restriction-modification inventory for the approved 196-genome LAB panel.

## Included in Git

- final curated locus table
- Type I-IV system counts
- Type I-IV primary presence/non-detection/NA matrix
- richer genome-level state table
- accepted subtype table
- unresolved/unclassified table
- raw normalized detector union tables
- DefenseFinder normalized physical-locus tables
- PADLOC/DefenseFinder physical-locus reconciliation
- detailed detector-only/shared curation tables
- Stage-5 validation report
- detector normalization/reconciliation scripts
- native-output manifest and archive checksum
- method and final report

## Release asset

`stage05_native_detector_outputs196.zip`

The ZIP preserves compact native detector evidence for every approved assembly:

- 196 PADLOC CSV files
- 196 PADLOC GFF files
- 196 DefenseFinder completion records
- 196 DefenseFinder genes tables
- 196 DefenseFinder HMMER tables
- 196 DefenseFinder systems tables
- 196 DefenseFinder generated-ID/source-locus mapping tables
- README
- SHA256 manifest

ZIP SHA256:

`b3d04d64f9f54d955ebe2e224d35b800509442e2549b7f7d892899072ea10947`

## Final accepted results

- Type I: 101 systems / 86 positive genomes
- Type II including IIG: 162 / 112
- Type III: 33 / 30
- Type IV: 121 / 100

Final candidate physical loci: 436.

Accepted complete systems: 417.

Partial candidates: 17.

Uncertain candidates: 2.

Primary genome/type matrix:

- 784 cells
- 328 positive
- 454 successful non-detections
- 2 NA
- validation errors: 0

## Scope limitation

This release records computationally predicted and curated genomic R-M architectures. Prediction does not by itself demonstrate expression, restriction activity, recognition motif, methylation phenotype or biochemical function.

Genome/protein/GFF/GBFF input files are not duplicated because they are already preserved by earlier repository stages.

Stage 6 consumes this frozen matrix and is released separately.
