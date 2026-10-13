# Stage 6 final pipeline report

Execution state: COMPLETED
Validation: PASS_FIGURE_PIPELINE196
Final manuscript figure binaries: intentionally withheld pending submission

## Validated tree x R-M join

- tree tips: 196
- Stage-5 R-M rows: 196
- joined genome/type cells: 784
- missing accessions: 0
- duplicate accessions: 0
- validation errors: 0

## Accepted display variants

Primary manuscript candidates:
- midpoint-rooted true-arc cladogram
- midpoint-rooted true-arc square-root-compressed phylogram

Supplementary robustness variants:
- original unrooted true-arc cladogram
- original unrooted true-arc square-root-compressed phylogram

## Rendering design

Branches are colored by genus when descendant genus assignment is homogeneous; mixed-genus ancestral branches are black.

Four external rings report Type I, Type II including IIG, Type III and Type IV states from the frozen Stage-5 matrix.

True circular arcs use 48 interpolation points per angular segment.

Exact final palettes are published as machine-readable TSV files.

## Reproducibility

The Stage-6 package contains:
- tree/R-M join validation
- exact ring mapping
- accession-to-display-label mapping
- iTOL-compatible annotation datasets
- accepted midpoint display-tree Newicks
- winning midpoint and unrooted true-arc renderers
- plotting Docker definitions and version record
- Stage-4 tree dependency and hash
- supplementary genome-level R-M source table

No final manuscript SVG, PDF or PNG files are included in this release.
