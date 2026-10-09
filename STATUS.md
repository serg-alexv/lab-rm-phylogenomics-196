# Current execution status

Updated 2026-10-09T19:44:04.314995+00:00. GitHub is the sole project authority and durable storage.
This master continuation is active; automatic scheduled continuation remains disabled.

Stage4 runs the one partitioned IQ-TREE3.1.4 job on all196 approved genomes,
100 accepted marker partitions and17,456 amino-acid columns. Model selection
and initial searches finished; global candidate-tree optimization continues.
The latest retained native/job observation is in
`reports/master_run/20261009/snapshots/recovery_progress01/native_progress.json`.
No host tree or support values are accepted yet. Historical V10 closure stays
UNKNOWN; the current controller does not change that historical conclusion.

Stage5's genome-source dependency split is implemented and source-tested in
commit `addf594d69990b4d4bc95d1e0fa38c76f59efdd6`. Detection and per-genome
curation use the accepted accession/source bundles independently of final
Stage4 acceptance. The current exclusive owner still must close exactly before
another native job is admitted on WD. Actual WSL/runtime/resource/lifecycle
checks and actual Stage5 searches remain NOT_RUN. The accession queue preserves
pending, failed, unresolved and not-run states. Final exact196-by4 joining and
authoritative Stage6 SVG/PDF require an independently accepted and published
host tree plus independent curation checks. See
`docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md`.

Cleanup already completed:224 inactive files/2,207,024,265 logical bytes and15
exact empty directories. Batch03 is now executing the published exact47,429
cold-file proposal. At 2026-10-09T19:44:04.3086104Z, its durable journal recorded
18,460 removed files/6,312,475,813 logical bytes;
this is progress, not final absence/protection verification. The219 held and
619 unmatched files remain outside this purge. Its fresh remote mapping ZIP,
source controls and historical Release member witnesses were verified first.
Active native inputs, runtime, checkpoints, original lock and six dirty G
files are protected. The live G checkout remains at launch commit160498a6
while its native owner holds the production lock; root will reconcile it with
remote main after exact closure.

Additional public recovery controls are being published: one component archive
(228,162,511 bytes) and three history shards (837 original files,120,674,497
compressed bytes). Their fresh remote byte verification is still pending.
Their scopes do not constitute complete environment recovery. One1,025-byte
vendor fragment is excluded and retained locally; component source/notice
coverage limitations are explicit. Raw private sessions/prompts/usage and
credentials are excluded. The ext4 toolchain and needed local runtime remain
protected. The host is not ready to wipe.

| Stage | Current scientific state | Published acceptance |
|---|---|---|
|0 environment|Completed|Verified acquisition/preflight|
|1 panel|Completed|Approved full196 panel verified|
|2 sequences|Completed|Integrity verified with documented exceptions|
|3 markers|Completed|Host marker inventory verified|
|4 host tree|Running, no accepted tree|Accepted Stage4a; final Stage4 pending|
|5 R-M inventory|Not run|Prepared V2 source and synthetic checks only|
|6 figure|Not run|Synthetic vector/negative-gate proofs only|
|7 final review|Not run|Pending scientific results|

Use `status/master_run_20261009.json` for this current master observation;
historical stage receipts retain their original dates and states. Recovery
assets are in the `master-run-storage-20261009-v1` Release. Source, decisions,
tests and public receipts are committed incrementally. No accepted upstream
stage is being rerun.
