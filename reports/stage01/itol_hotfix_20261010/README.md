# iTOL decoration hotfix

The user approved DATASET_BINARY with six colored square columns after the official iTOL heatmap template was checked: heatmaps use a shared gradient and cannot assign each binary column its own presence hue using FIELD_COLORS.

`scripts/make_itol_decorations.py` is a standalone, standard-library Python program. Its default input is project-root cell_mapping.tsv, with required columns GenomeID, Host, RM, Cas, Abi2, CBASS, BREX, Septu. The user's final exact template fixes output field order to RM, Cas, Abi2, CBASS, BREX, Septu regardless of input header order. Colors, configuration order, comments, blank lines and six-entry legend match that template. Missing, unknown, or nonbinary defense states cause failure, never conversion to absence. Duplicate genome IDs, malformed TSV rows, control characters and blank hosts are rejected.

The program writes exactly two files: pipeline_output/defense_systems_heatmap.txt (filename retained as requested; header DATASET_BINARY) and pipeline_output/host_colorstrip.txt (DATASET_COLORSTRIP). All configuration/data fields are tab-delimited. Presence uses each system's FIELD_COLORS hue; zero is an empty square, white on a white canvas. This binary format does not independently force the background color. Host colors are deterministic unique hexadecimal colors, with matching legends. Both output paths are checked before writing, and exclusive creation refuses overwrite.

No real decoration datasets have been produced: the canonical project-root cell_mapping.tsv does not exist, and historical R-M render-geometry grids do not implement this new eight-column input contract. Synthetic test results establish program behavior only, not defense-system or host evidence. No new host classifications or defense calls are fabricated. No GUI directions or automatic upload are included.

Official format references:
- https://itol.embl.de/help/dataset_binary_template.txt
- https://itol.embl.de/help/dataset_color_strip_template.txt
- https://itol.embl.de/help/dataset_heatmap_template.txt

The corrected local five-marker pilot remains running separately under the original workflow lock; the full pipeline remains unapproved. Its first marker was still in ModelFinder at 07:17 UTC. This hotfix does not interrupt or alter its inference command.
