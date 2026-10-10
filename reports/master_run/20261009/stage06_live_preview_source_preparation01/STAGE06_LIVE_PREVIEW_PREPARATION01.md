# Provisional Stage6 snapshots during the master queue

`stage06_live_preview.py` is a separate C-only adapter for the existing accepted
196-tip Stage4 tree and optional independently accepted closed-genome curations.
It reuses the unchanged `stage06_render.py` geometry, SVG/PDF and iTOL exporters,
and the unchanged `stage05_curation/rm_matrix.py` cell serializer. The final
renderer, its full-panel curation acceptance and `check_stage06_outputs.py` remain
unchanged and mandatory for final delivery. Source preparation and disposable C
tests establish no actual scientific or final figure acceptance.

The default invocation is NOOP and reads no inputs. Explicit use is:

```powershell
python -B work/stage06_live_preview.py --render --snapshot C:\...\work\preview_snapshot01.json --snapshot-sha256 <exact-sha256> --output C:\...\work\stage06_live_preview01
```

The output must be a fresh directory directly inside this C-work directory. All
inputs must be bounded ordinary files under C-work with plain ancestry and exact
SHA256 pins. The adapter reads no live G/UNC/Linux path, performs no detector or
tree inference, takes no workflow lock and changes no host configuration. The
master owner creates immutable C snapshots after each applicable accepted step;
this renderer itself is not a queue scheduler or an acceptance authority.

The input JSON uses schema `RM_LIVE_PREVIEW_SNAPSHOT_V1`:

```json
{
  "schema": "RM_LIVE_PREVIEW_SNAPSHOT_V1",
  "tree": {"path": "<absolute-C-work-accepted-tree>", "sha256": "<exact-sha256>"},
  "approved": {"path": "<absolute-C-work-approved-panel>", "sha256": "<exact-sha256>"},
  "tree_acceptance": {"path": "<absolute-C-work-independent-Stage4-readback>", "sha256": "<exact-sha256>"},
  "accepted_genomes": [],
  "pending": []
}
```

The real accepted tree SHA is
`f886c0134ab662a05aae2b1c1a26ed364749af250400f769ce6e63f1f7a8ba19`;
the approved panel SHA is
`85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6`.
The exact already accepted independent remote readback SHA is
`f14b097aac1705c2632307eaadf423febdc3154cafe370aace78dd8196044d49`.
Its positive remote gate and CRC/hash-verified tree/panel member records are
rechecked. No production flag can substitute a fixture tree or panel.

An accepted genome entry contains exactly `accession`, `receipt`, `cells` and
`source_manifest`; the latter three use the same exact path/SHA specification.
These are the three files from actual unchanged independent single-genome
curation: `single_genome_curation_validation.json`,
`independently_reconstructed_cells.json`, and `single_genome_source_manifest.json`.
The adapter checks the production acceptance schema/status, selected accession,
panel/wrapper/checker/complete-receipt pins, exact four cells, and verified native
closure. Raw native completion, producer candidates and unclosed scopes cannot
be accepted. The original serializer retains reviewed partial/uncertain cells as
NA and distinguishes reviewed successful-search nondetection from absence of
search. Predicted architecture makes no functional-activity claim.

Every unsupplied genome starts with all four cells `NOT_RUN`, displayed as `NA`.
Optional unique pending entries contain exactly `accession`, `execution_state`
and a bounded nonempty `reason`. Allowed reported execution states are NOT_RUN,
PREPARED, RUNNING, DEFERRED_RESOURCE, FAILED_RETRYABLE, FAILED_FATAL,
RAW_COMPLETE_PENDING_CURATION and CURATION_PENDING. These labels and reasons are
queue metadata, never biological acceptance; they are stored separately in
`preview_review_state.tsv`. An accepted accession cannot also be pending.

Each snapshot retains the exact input tree bytes and the existing unrooted
branch geometry and tip order. It emits a 196-row wide matrix, 784-row detailed
state table, separate 196-row review state, shared scene/cell/branch mappings,
SVG/PDF and the existing full-state/binary iTOL convenience exports. SVG/PDF and
all iTOL dataset labels visibly include
`PREVIEW_PENDING_SCIENTIFIC_COMPLETION`. Grey means pending, partial or unresolved;
white is reserved for reviewed successful-search nondetection. Binary iTOL
convenience strips omit NA. No iTOL server import is performed.

`preview_manifest.json` uses the distinct `RM_PROVISIONAL_STAGE06_EXPORT_V1`
schema and `dataset_kind=PROVISIONAL`, records input/output/helper hashes and
accepted counts, and keeps `full_panel_complete`, `final_matrix_acceptance` and
`final_figure_acceptance` false even if all 196 snapshots eventually arrive.
Producer serialization checks are explicit and require a separate independent
preview review. No final curation/provenance certificate is fabricated. A failed
export remains a partial preview directory without a successful manifest.

Six focused C-temporary tests cover a partial exact 196/784 join, pending NA,
independently curated positive/nondetection/partial/uncertain values, bad or
unclosed receipt/type vetoes, byte-pin/duplicate/tree vetoes, default NOOP and
visible vector/iTOL watermark with no final certificates. Test data are synthetic
only inside the unit-test process; the production CLI has no synthetic mode.
Actual master rendering has not been run by this producer. Root will publish
the independent source peer, then explicitly render a genuine accepted-tree
snapshot and publish its separately reviewed provisional outputs.
