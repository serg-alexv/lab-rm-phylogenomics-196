# Validation and direct iTOL API integration

The existing five-marker pilot is still running from unchanged run_pipeline.sh
SHA256 5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b.
run_pipeline.with_validation_itol.sh is a prepared revision, not the active runner.
Activate it only after the current runner has a successful terminal receipt and
has released the original lock. Its source installation is user-authorized; a
full 100-marker execution still requires separate user confirmation.

The candidate validates after ASTRAL in both explicit modes. Full mode then
generates the two decoration files from the real cell_mapping.tsv and uploads
through scripts/upload_itol.py. All inference remains local. Existing outputs
are refused rather than overwritten. The five current FASTAs are not a complete
100-marker input set. root cell_mapping.tsv and final species_tree.newick are
currently absent; real dataset generation/upload have not happened.

Validation checks each locus against its own input taxon set and checks ASTRAL
against the selected marker union. A pilot may legitimately cover fewer than196
taxa; the actual current five-marker union contains all196. Full mode additionally
requires100 markers and equality with all196 approved IDs. Truncation, duplicate,
missing and extra tips fail. Unlabeled gene-tree supports are recorded, not filled.
This checks workflow/data integrity, not biological reliability or model adequacy.

Official API contract checked 2026-10-10:
https://itol.embl.de/help.cgi#batch
Upload uses https://itol.embl.de/batch_uploader.cgi with APIkey, projectName and
zipFile. The ZIP has a .tree member and two tab-separated datasets. The tree member
is the hash-verified flat q1-frequency derivative; the native ASTRAL source is
retained unchanged. q1 is a quartet frequency, not the pp1 local posterior.
Defense source accepts defense_systems.txt or the earlier defense_systems_heatmap.txt
name; both use DATASET_BINARY, and conflicting copies are rejected. Host strip is
required. Dataset identifiers must exactly match all196 validated tree tips.

The key is read only from /mnt/c/itol.api-key.txt, after local preflight. Requests
are authenticated only to the official HTTPS endpoint; redirects and automatic
retries are disabled. SUCCESS with a numeric tree ID is required. The permalink
is printed to stdout and saved. Circular SVG/PDF exports use batch_downloader.cgi
and display_mode=2; this does not assert a persistent circular setting in the UI.
Official batch upload requires an active standard iTOL subscription; account
eligibility has not been tested. No real upload was attempted.

pipeline_output/itol contains the ZIP, asset hashes, redacted response, permalink
and successful export files. A failed or ambiguous network request preserves
evidence and stops; the directory blocks blind resubmission. A permalink proves
upload acceptance only; both exports also need exit0 and their saved files.

requests and its dependencies were installed only into the existing local
phylogeny Conda environment. requirements-itol.txt pins installed versions;
requests_install.json/log retain the install receipt. Synthetic API tests use
dummy credentials and fake HTTP, never the real key or iTOL service.
