# Stage 5 native detector outputs — approved 196-genome panel

This archive preserves compact per-genome native evidence used for the final Stage-5 restriction-modification inventory.

## Per assembly

Each GCF_<version>/ directory contains:

### padloc/
- protein_padloc.csv — native PADLOC system/gene calls
- protein_padloc.gff — native PADLOC genomic-feature output

### defensefinder/
- .complete — local successful-run completion record
- defensefinder_gembase_defense_finder_genes.tsv — DefenseFinder system-component table
- defensefinder_gembase_defense_finder_hmmer.tsv — DefenseFinder profile/HMM evidence
- defensefinder_gembase_defense_finder_systems.tsv — DefenseFinder system-level output

### mapping/
- defensefinder_protein_map.tsv — reversible generated-ID to source locus/protein/coordinate mapping used to preserve physical locus identity and replicon-local order

## Scope

Genome/protein/GFF/GBFF input files are intentionally not duplicated here; they are preserved by earlier repository stages. This archive contains detector outputs and the mapping required to interpret them.

PADLOC: 2.0.0 / PADLOC-DB 2.0.0
DefenseFinder: 3.0.0 / models 3.0.0 / CasFinder 3.1.0
HMMER: 3.4
Panel size: 196 assemblies

Raw detector output is evidence, not automatically a curated complete R-M system. Final curated calls are published separately in the Stage-5 compact tables.
