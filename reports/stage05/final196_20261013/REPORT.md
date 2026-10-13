# Stage 5 final report

**Execution state: COMPLETED**  
**Scientific validation: PASS_RM_INVENTORY196**

## Scope

The full approved 196-genome panel was screened and curated for R-M Types I-IV using PADLOC and DefenseFinder with replicon-aware physical-locus reconciliation.

## Final curated result

Candidate physical loci: **436**

- COMPLETE_PREDICTED: **417**
- PARTIAL_CANDIDATE: **17**
- UNCERTAIN: **2**

Accepted systems:

| Broad class | Systems | Positive genomes |
|---|---:|---:|
| Type I | 101 | 86 |
| Type II incl. IIG | 162 | 112 |
| Type III | 33 | 30 |
| Type IV | 121 | 100 |

## Detector reconciliation

PADLOC raw systems: 313.

DefenseFinder raw R-M-like rows: 382.

DefenseFinder normalized physical loci after duplicate/model reconciliation: 336.

Cross-detector physical reconciliation:

- shared PADLOC/DefenseFinder loci: 213
- exact component-set matches: 199
- partial component overlaps: 14
- broad-type conflicts: 0
- PADLOC-only loci: 100
- DefenseFinder-only loci: 123

Final candidate union: 436 physical loci.

## Figure-level state matrix

Rows: 196 genomes.

Broad R-M fields per genome: 4.

Total explicit states: 784.

- 1 / positive: 328
- 0 / successful non-detection: 454
- NA / unresolved: 2

Validation errors: 0.

The two unresolved matrix cells are:

- GCF_001932615.1 Type II
- GCF_041281755.1 Type IV

## Curated exceptions

Seventeen incomplete Type-I loci remain PARTIAL_CANDIDATE and do not independently generate positive Type-I calls.

One origin-spanning Type-I system on circular plasmid NZ_CP178853 was rescued by explicit circular-boundary validation.

Two PADLOC HNH single-nuclease candidates remain UNCERTAIN.

Type IIG/IIG_2 is preserved as subtype information and collapsed into broad Type II in the primary matrix.

Detector-supported single-protein modification-dependent Type-IV systems are accepted without requiring a cognate MTase.

## Native detector evidence

A separate GitHub Release asset preserves compact native PADLOC and DefenseFinder evidence for all 196 genomes.

Per assembly:

- PADLOC CSV
- PADLOC GFF
- DefenseFinder completion receipt
- DefenseFinder genes TSV
- DefenseFinder HMMER TSV
- DefenseFinder systems TSV
- generated-ID/source-locus mapping TSV

Per-genome evidence files: 1,372.

Archive entries including README and MANIFEST: 1,374.

Native evidence archive SHA256:

`b3d04d64f9f54d955ebe2e224d35b800509442e2549b7f7d892899072ea10947`

## Validation

The final master table contains 436 unique curated locus identifiers.

The count, binary-state and richer state matrices each contain the same 196 exact versioned assembly accessions.

Accepted locus totals reconstruct the count matrix exactly.

The 196 x 4 matrix contains only legal states and passed independent consistency validation with zero errors.

Stage 5 is therefore frozen for Stage-6 tree joining and visualization.
