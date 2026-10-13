# Stage 5 method: R-M Types I-IV inventory and curation

## Scope

Stage 5 independently screened the approved 196-genome LAB panel for restriction-modification systems. The accepted Stage-4 host phylogeny was not used to detect or classify R-M systems. Phylogenetic inference and R-M annotation remained independent until Stage 6.

Stage 5 was executed on the user's personal Windows PC with Docker Desktop after Stage 4 had been completed and accepted separately. The approved 196-genome panel and previously acquired genome/protein/GFF/GBFF inputs were reused without modification.

## Software and detector resources

- PADLOC 2.0.0
- PADLOC-DB 2.0.0
- DefenseFinder 3.0.0
- DefenseFinder models 3.0.0
- CasFinder models 3.1.0
- MacSyFinder 2.1.4
- HMMER 3.4
- Prodigal 2.6.3
- Python 3.11.17
- Docker image: lab-rm-stage5:2026-10-12
- Docker image SHA256: f69121633fc9a872be6fa16696eaf0ad03035c44cd153af5111056a52fbbb0d5

All 196 PADLOC runs and all 196 DefenseFinder runs completed structural validation. Detector failure was never converted to biological absence.

## Genomic-context handling

Replicon identity, genomic ordering, locus tags, protein accessions, strand and coordinates were retained throughout Stage 5.

DefenseFinder input was reconstructed from GFF/protein mappings so that each physical protein-coding locus received a generated positional identifier. Reused WP accessions were therefore never treated as unique physical-locus identifiers.

The generated-ID-to-source mapping is included in the Stage-5 native-output release asset for every genome.

## PADLOC

PADLOC was the primary detector. The native per-genome outputs preserved for release are:

- protein_padloc.csv
- protein_padloc.gff

The raw union contains 313 PADLOC systems.

## DefenseFinder

DefenseFinder was run on replicon-aware Gembase-style protein inputs with raw/native output preserved.

The native per-genome outputs preserved for release are:

- .complete
- defensefinder_gembase_defense_finder_genes.tsv
- defensefinder_gembase_defense_finder_hmmer.tsv
- defensefinder_gembase_defense_finder_systems.tsv

DefenseFinder produced 382 R-M-like raw system rows.

Literal duplicate emissions were removed only in the normalized layer. Exact-deduplicated model calls numbered 342. Six same-broad-type overlapping Type-II model solutions were collapsed by connected-component reconciliation, yielding 336 physical DefenseFinder loci:

- Type I: 118
- Type II: 146
- Type III: 33
- Type IV: 39

No shared-protein connected component crossed broad R-M classes.

## Cross-detector reconciliation

PADLOC and DefenseFinder loci were matched using generated positional locus identifiers rather than protein accession alone.

The corrected full-model reconciliation yielded:

- 213 shared PADLOC/DefenseFinder physical loci
- 100 PADLOC-only loci
- 123 DefenseFinder-only loci
- 436 distinct candidate physical loci total

Among the 213 shared loci:

- 199 had identical protein/component sets
- 14 showed partial component overlap
- broad-type conflicts: 0
- PADLOC loci matching multiple DefenseFinder loci: 0
- DefenseFinder loci matching multiple PADLOC loci: 0

A neighborhood audit of unmatched loci identified one nearby cross-type pair in GCF_046109915.1. Gene-order inspection demonstrated that the loci were distinct and they were retained separately.

## Curation rules

### Type I

A qualifying Type-I system required compatible restriction, modification and specificity functionality (R/M/S), or equivalent detector-supported architecture.

Incomplete R+M, R+S or M+S architectures were retained as PARTIAL_CANDIDATE unless the missing functional component was rescued by strong local/domain evidence.

One GCF_047344935.1 Type-I locus was accepted as COMPLETE_PREDICTED after circular-boundary validation showed that the missing component was located across the origin of circular plasmid NZ_CP178853.

Five shared PADLOC/DefenseFinder Type-I R+M loci remained partial because no plausible local specificity subunit was found. Twelve additional detector-only incomplete Type-I loci also remained partial.

### Type II

Ordinary Type-II systems required compatible restriction and methylation architecture.

Single fused Type-IIG/IIG_2 systems were considered valid complete systems and were collapsed into broad Type II for the primary four-type matrix while retaining their subtype annotation.

All 67 detector-only Type-II loci satisfied accepted architecture rules.

### Type III

Qualifying Type-III systems required compatible Mod/Res architecture.

All four detector-only Type-III loci contained Mod+Res architecture and were accepted.

### Type IV

Modification-dependent Type-IV restriction systems were allowed to consist of a single detector-supported restriction protein; a cognate MTase was not required.

### HNH candidates

Two PADLOC RM_type_HNH single-nuclease calls remained unresolved. Both proteins had DefenseFinder Type-II REase HMM evidence but no DefenseFinder system-level call. They were retained as UNCERTAIN and were not automatically assigned to Type II or Type IV.

## Final locus curation

The final master locus table contains:

- 436 distinct candidate physical loci
- 417 COMPLETE_PREDICTED
- 17 PARTIAL_CANDIDATE
- 2 UNCERTAIN

Accepted complete systems:

- Type I: 101
- Type II including IIG: 162
- Type III: 33
- Type IV: 121

Genome-level positive calls:

- Type I: 86 genomes
- Type II: 112 genomes
- Type III: 30 genomes
- Type IV: 100 genomes

## Primary 196 x 4 matrix

The frozen Stage-5 matrix contains exactly 196 genomes x 4 broad R-M types = 784 explicit states:

- positive: 328
- successful non-detection: 454
- NA: 2

The two NA cells are:

- GCF_001932615.1 / Type II
- GCF_041281755.1 / Type IV

These cells remain unresolved because the corresponding HNH candidates could alter the broad-type assignment.

No failed or unresolved screening result was encoded as biological absence.

## Native detector evidence package

The Stage-5 release asset contains 196 per-genome directories and seven compact evidence files per assembly:

- 2 PADLOC files
- 4 DefenseFinder files
- 1 generated-ID/source-locus mapping file

Total per-genome evidence files: 1,372.

The package also contains README.md and MANIFEST.tsv.

Genome/protein/GFF/GBFF inputs are not duplicated because they are preserved by earlier repository stages.
