# Stage 6 method: circular host phylogeny with four R-M annotation rings

## Input freeze

Stage 6 joins two independently validated products:
- accepted Stage-4 primary196 host phylogeny
- frozen Stage-5 196 x 4 R-M state matrix

Accepted Stage-4 tree SHA256:
f886c0134ab662a05aae2b1c1a26ed364749af250400f769ce6e63f1f7a8ba19

The join validation confirmed:
- tree tips: 196
- Stage-5 matrix rows: 196
- duplicate tree tips: 0
- duplicate matrix genomes: 0
- tree tips missing from matrix: 0
- matrix genomes missing from tree: 0
- joined genome x R-M-type cells: 784
- validation errors: 0

## Taxon labels and genus coloring

Exact versioned GCF accessions remain the canonical machine keys. Human-readable organism and strain labels were extracted from GenBank metadata and stored separately.

A branch receives a genus color only when all descendant tips belong to the same figure genus. Mixed-genus ancestral branches are black and are intentionally omitted from the genus legend.

The historical NCBI label [Lactobacillus] timonensis is retained in source metadata, while GCF_900240275.1 is assigned to Limosilactobacillus for figure branch coloring.

## R-M rings

Four concentric binary annotation rings are displayed, inner to outer:
1. Type I
2. Type II including IIG
3. Type III
4. Type IV

Figure states:
- accepted system: type-specific saturated color
- successful non-detection: white
- unresolved or NA: grey

The frozen Stage-5 matrix contains 328 positive, 454 successful non-detection and 2 NA cells.

## Rooting and branch-length display

The accepted Stage-4 host tree is explicitly unrooted.

Two midpoint-rooted manuscript display candidates were generated:
- cladogram
- square-root-compressed phylogram

Midpoint rooting is a display convention. For the square-root-compressed phylogram, the original accepted branch lengths are square-root transformed after midpoint-root placement solely for visualization; topology is unchanged.

Two supplementary robustness views retain the original unrooted Stage-4 tree:
- unrooted cladogram
- unrooted square-root-compressed phylogram

## True-arc rendering

Direct circular-coordinate rendering produced visibly polygonal angular joins. The final renderer therefore constructs angular branch components as explicit interpolated circular arcs.

Arc resolutions of 12, 48 and 160 interpolation points were compared visually. They were indistinguishable at publication scale, and 48 was retained as a conservative intermediate setting.

## Final styling

The accepted genus and R-M palettes are preserved as TSV files in the Stage-6 package. Winning render scripts also encode the final branch width, legend styling, ring geometry and black mixed-genus backbone.

## Publication policy

Final manuscript SVG, PDF and PNG figure binaries are intentionally withheld from this repository release until manuscript submission. This release publishes the exact compact inputs, display trees, palettes, environment and scripts needed to reproduce them.
