# iTOL pilot preparation and first preflight result

The five-marker pilot remains complete and independently validated: five gene
trees, 196 unique approved ASTRAL tips, and 193 informative splits. Its 81 published
files were independently read back and SHA-256 verified at ea1f094cb4a976ce3d95a855b3dea26c3c577394.
Raw scientific outputs, the original runner, and the original workflow lock remain unchanged.

The first upload client stopped before any HTTP request because it expected one
token in the local credential file. The user clarified the actual two-line format:
username, then API key. Only structure was reported; neither value is published.
The separate upload_itol_pilot_account.py client selects the second line. The original
client and credential file remain intact. The corrected client made one real request;
iTOL rejected it with ERR 0: No valid subscription detected for API key [REDACTED].
No tree URL or SVG/PDF export was created. Both attempts and the upload package
are preserved; further attempts require resolution of the account's batch API access.

The official endpoints are https://itol.embl.de/batch_uploader.cgi and
https://itol.embl.de/batch_downloader.cgi. The upload uses APIkey and zipFile;
SVG/PDF export uses the installed itolapi 4.1.6 writer with checked HTTP responses.
Documentation: https://itol.embl.de/help.cgi#batch and https://github.com/albertyw/itolapi.
The uploaded tree will be explicitly named as a five-marker pilot. Numeric internal
labels use q1 quartet frequencies; raw structured ASTRAL annotations remain preserved.

The user-provided scripts/prep_itol_files.py is preserved byte-for-byte. Its syntax
compiles and valid synthetic input generates the expected tab-separated templates.
It does not validate the schema, uniqueness, binary values or tree membership, and
its error and overwrite behavior require independent input checks before real use.
No canonical cell_mapping.tsv exists. Real NCBI source metadata was located for
the approved panel and is preserved separately without invented host categories.
Stage 5 production defense detection is NOT_RUN; no defensible six-system matrix
can be merged. Missing or unfinished detection is not biological absence.
The historical mapping under a synthetic
Stage 6 render directory is drawing geometry for test accessions, not biological
defense or host evidence. No decoration data has been fabricated or generated.

Full 100-marker execution remains unapproved. scripts/validate_pipeline.py was
not accessed or changed. The completed-pilot follow-up remains paused.
