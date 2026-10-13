# Stage 5 R-M system validation report

**Status: COMPLETED + VALIDATED**

## Scope
- Approved genome panel: 196 assemblies
- PADLOC: 2.0.0; PADLOC-DB: 2.0.0
- DefenseFinder: 3.0.0; models: 3.0.0
- HMMER: 3.4
- Prodigal: 2.6.3

## Reconciliation
- Raw detector system rows: 695
- PADLOC raw systems: 313
- DefenseFinder physical loci after duplicate/model reconciliation: 336
- Cross-detector shared physical loci: 213
- Final distinct candidate physical loci: 436
- COMPLETE_PREDICTED loci: 417
- PARTIAL_CANDIDATE loci: 17
- UNCERTAIN loci: 2

## Accepted systems
- Type I: 101 systems; 86 positive genomes
- Type II (including IIG): 162 systems; 112 positive genomes
- Type III: 33 systems; 30 positive genomes
- Type IV: 121 systems; 100 positive genomes

## Figure-level matrix
- Genome rows: 196
- Type fields per genome: 4
- Total cells: 784
- Positive cells: 328
- Negative cells: 454
- NA cells: 2
- Type II NA: GCF_001932615.1 (unresolved HNH candidate could affect Type II assignment)
- Type IV NA: GCF_041281755.1 (unresolved HNH candidate could affect Type IV assignment)

## Curation caveats
- Seventeen incomplete Type I loci were retained as PARTIAL_CANDIDATE and do not independently qualify as positive calls.
- Five of these partial Type I loci are PADLOC/DefenseFinder-shared R+M calls lacking a plausible local specificity component.
- Twelve additional partial Type I loci are DefenseFinder-only incomplete architectures.
- One origin-spanning Type I locus on circular plasmid NZ_CP178853 was rescued as COMPLETE_PREDICTED after circular-boundary validation.
- Type IIG/IIG_2 calls are preserved as subtypes and collapsed into broad Type II for the four-ring matrix.
- Single-protein detector-supported Type IV modification-dependent restriction systems are accepted without requiring a cognate MTase.
- Two PADLOC RM_type_HNH single-nuclease candidates remain UNCERTAIN and are retained in rm_unclassified.tsv.

## Validation
- 436/436 curated locus IDs unique.
- 417 accepted loci reproduce the four count-matrix totals exactly.
- Count, binary, and state tables contain the same 196 genome IDs.
- Binary matrix contains exactly 784 legal states.
- Matrix consistency errors: 0.
- Detector failures were not converted to biological absence.

The binary matrix is therefore frozen for downstream tree joining and figure construction.
