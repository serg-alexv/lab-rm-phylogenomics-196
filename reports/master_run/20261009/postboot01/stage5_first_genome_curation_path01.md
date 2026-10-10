# First closed-genome R-M curation path

Scope: C-only inspection and procedure for GCF_000009425.1. No detector, curation producer, independent production audit, WSL command, lock, Git operation or biological result was executed here. The exact frozen sources already support incremental four-cell acceptance; no new helper/controller is needed. `SINGLE_GENOME_AUDIT_METHODS.md` supersedes the earlier handoff's missing single-genome CLI note.

Source pins: producer `20e860b58737e74061a0e7a8b4c8ac21a8e6d95aa1a0685cfbc5bc54ced0deb0`; full independent checker `89a42d63401ef1ef3479690546a3c8cad4da679517aa2ed7da6b4e6716b6af0c`; incremental wrapper `cdd81d2870dbc7c03845721199a98d4f6b51a23fb94ebb19fa71311bb9e2ed66`. The accompanying JSON records the other exact inspected controls.

## Accepted upstream input and its limit

The accepted source pin names release `stage03-hostmarkers196-v1`, asset `stage03-source-and-search-001-020.zip` SHA256 `a94a6fd4b888b2c4117a668b3bac2ddc5979dc27626e6744d4c30fd02a8513ca`, member `source_locus_inputs/assemblies/GCF_000009425.1/build_receipt.json`, 3209 bytes, SHA256 `f2f21c9b73d9152be655d610254833f9a09aa19a6aa2288070eddd6831854413`.

The preserved source-readiness archive was reopened in C. Its exact second-attempt receipt and per-accession record previously reported 12 source payload files/11001775 bytes for this accession, passing the accepted source-byte check. This is historical byte-readiness evidence, not a fresh read of today's canonical source and not biological screening. Source/bundle/raw bytes must be reopened by the actual producer and independent checker. No current bundle or raw result is asserted by this procedure.

## Required closed raw checkpoint

Admit curation only after the existing runner produces the canonical accession directory `.work/stage05_atomic_v1/GCF_000009425.1` with `complete.json`: `STAGE05_ATOMIC_GENOME_COMPLETE_V1`, `COMPLETE_VALIDATED`, production accession and exact V2 scientific identity. Its scope remains `NATIVE_SEARCH_SOURCE_AND_RAW_INTEGRITY_ONLY`, curation `NOT_RUN`, biological absence claim `NONE`.

Preserve and reopen every exact `complete.files` entry. The manifest must cover the built bundle, bundle audit, execution freeze, all full native query/task outputs and native post-treatment reports, selected inventory attempt and raw audit. Do not substitute only the filtered positive rows. The native search covers all 5027 PADLOC profiles and all three DefenseFinder native families, including no-hit queries and rejected/native contextual candidates. Every manifest-pinned `.launch.json` needs its matching pinned `.closure.json`, exact nonce/boot binding, exit zero and empty owned descendants/groups before adoption.

The selected inventory assembly directory requires these eight files:

* `all_native_profile_domains.tsv`
* `all_native_filtered_profile_hits.tsv`
* `all_native_system_candidate_rows.tsv`
* `all_native_query_completion.tsv`
* `source_locus_crosswalk.tsv`
* `source_replicon_topology.tsv`
* `source_annotation_review.tsv`
* `replicon_search_states.tsv`

The selected `raw_validation/attempt_N/validation.json` must report `PASS_FULL_NATIVE_SEARCH_AND_SOURCE_ACCOUNTING_ONLY`, architecture curation `NOT_RUN`, and the exact source/freeze identity. The selected attempt paths must agree with `complete.inventory_directory` and `complete.raw_validation_file`; old or incomplete attempts cannot replace them.

## Existing prepare, review, apply and independent audit

Use these unchanged retained paths, agreeing with the actual runtime08 roots:

```bash
ROOT='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
PACKAGE='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage05_curation'
MOUNT='/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux'
PY="$MOUNT/detector_env/bin/python"
ACCESSION='GCF_000009425.1'
GENOME="$ROOT/.work/stage05_atomic_v1/$ACCESSION"
REVIEWS="$PACKAGE/reviewed"
```

Root must admit finite supervised operations under the existing operational owner/resource/storage framework; these scientific CLIs provide no host-wide ownership bypass. Each output directory must be fresh.

```bash
"$PY" -B "$PACKAGE/stage05_curation_atomic.py" prepare \
  --root "$ROOT" --genome "$GENOME" --accession "$ACCESSION" \
  --approved "$ROOT/config/approved_accessions.txt" \
  --source "$ROOT/.work/source_locus_inputs_v1" \
  --policy-dir "$ROOT/.work/review2/stage05_policy" \
  --models "$MOUNT/defense_models" --padloc-db "$MOUNT/padloc_db" \
  --environment "$MOUNT/detector_env" --reviews "$REVIEWS" \
  --output "$REVIEWS/$ACCESSION/prepare"
```

This creates a hash-bound pending queue, not scientific decisions. Execute the actual evidence review below and save `$REVIEWS/$ACCESSION/executed_review.json`. Then run the same arguments with phase `apply`, adding `--prepared "$REVIEWS/$ACCESSION/prepare/prepared.json" --review "$REVIEWS/$ACCESSION/executed_review.json"` and changing the output to `$REVIEWS/$ACCESSION/apply`. Apply rebuilds the queue and emits `curated_candidate.json` with `INDEPENDENT_CURATED_VALIDATION_REQUIRED`; this is not accepted curation.

Derive a new actual settings JSON from `audit_settings.template.json`, retaining production source/model/review paths and setting the previously null `runtime_manifest` to `/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_runtime_actual_postiq_08.json`, SHA256 `f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1`. Name the actual runner/supervisor sources used by the raw execution freeze; the independent checker requires exact agreement. Do not manufacture final matrix/state files for the incremental audit. A selected accession cannot be an exception record.

```bash
"$PY" -B "$PACKAGE/validate_one_atomic_curation.py" \
  --settings "$ACTUAL_SETTINGS" --accession "$ACCESSION" \
  --output "$REVIEWS/$ACCESSION/independent_audit"
```

The wrapper rehashes the full actual native/model/database runtime and executes the unchanged independent `atomic_one`; it does not launch biological searches or import the curation producer. It reopens source, bundle, full native evidence, closure receipts, typed scientific witnesses and all review decisions, reconstructs exactly four cells, compares them with the producer candidate, then rechecks immutable controls.

## Executed scientific review contract

`executed_review.json` must bind the prepared queue hash and source snapshot, declare `EXECUTED_FULL_REQUIRED_EVIDENCE_REVIEW`, and contain exactly one review for every queued item. Reopen all queued actual evidence references; each record binds queue ID/item hash/snapshot and declares `EXECUTED_HASH_BOUND_EVIDENCE_REVIEW`, nonempty rationale, evidence references and a resolved-with-executed-basis or unresolved decision for every affected type. Cover raw domains, accepted and rejected native candidates, unmapped native model context, source pseudo/untranslated/partial/fuzzy/edge context, empty replicons and circular-origin context. Annotation text alone cannot dismiss untranslated unknown context. Do not join architectures across replicons or infer circular adjacency without actual topology evidence.

Complete predicted architecture requires actual compatible intact roles and context:

| Cell | Required scientific basis |
| --- | --- |
| I | Restriction, methylation and specificity roles; actual R/M/S architecture or supported fusion. |
| II | Restriction plus protective methylation in a reviewed architecture; orphan MTase/generic nuclease is insufficient. IIG requires supported fusion and family-specific recognition evidence. |
| III | Compatible Mod and Res roles; generic methylase plus nuclease is insufficient. |
| IV | Family-specific modification-dependent restriction/cleavage evidence and required partners or supported fusion; explicitly resolve competing Type II/LlaJI interpretations. |

Each role binds its exact raw hit, locus, primary AA SHA, profile name/SHA, native model/component membership and aligned domain interval. The separate witness schema is `RM_FUNCTIONAL_DOMAIN_ROLE_REVIEW_V1`, execution `EXECUTED_INDEPENDENT_SOURCE_DOMAIN_ROLE_REVIEW`, decision `SUPPORTED_PREDICTED_ROLE`, with an independently attributed reviewer different from `curation_reviewer_id`, reopened functional-architecture basis references, an actual explanatory statement and zero unresolved competing role interpretations. Profile/model membership alone cannot establish the role, and a correctly serialized witness does not substitute for executing the scientific interpretation.

Use multipart Type II family fields only when actual evidence supports them. The architecture schema `RM_MULTIPART_TYPE_II_FAMILY_ARCHITECTURE_V1` binds distinct fused R-M and specificity loci. Its separate `RM_MULTIPART_TYPE_II_FAMILY_REVIEW_V1` witness requires execution `EXECUTED_INDEPENDENT_SOURCE_DOMAIN_FAMILY_REVIEW`, independent attribution, exact family/subtype/candidate/AA/hit/model/native-reference identity, reopened primary family evidence and zero unresolved competing architectures. IIG additionally needs reviewed family-specific recognition-domain evidence. Do not relabel BcgI/BsaXI-like multipart systems automatically as IIG. Native subtype conflicts need an executed supported resolution.

Every I/II/III/IV coverage record must declare `EXECUTED_HASH_BOUND_FULL_SCOPE_COVERAGE_REVIEW`, bind the same snapshot, reopen evidence, explain the decision and list exactly all applicable unique queue IDs. Count exact accepted locus sets once; overlapping native candidates require executed exact-locus counting review and evidence, never transitive union.

## Accepted product and stop boundaries

Only a genuine independent PASS writes all three: `independently_reconstructed_cells.json`, `single_genome_source_manifest.json`, and `single_genome_curation_validation.json`, status `PASS_INDEPENDENT_SINGLE_GENOME_RM_CURATION`. This accepts one accession/four cells. `full_panel_complete`, `final_matrix_acceptance` and `final_figure_acceptance` remain false; functional activity claim remains `NONE`.

Presence is 1 only from an independently accepted complete predicted locus. An additional unresolved copy does not erase a separately valid complete positive. Zero requires both complete successful detectors plus full source/domain/candidate/context accounting and no qualifying or unresolved candidate; it means method-bounded non-detection. Partial, unresolved, unreviewed, failed and not-run evidence remains NA unless an independently valid complete locus establishes presence. The four-cell accepted product can therefore legitimately include NA; do not force it to a binary result.

Publish the immutable raw manifest/payload, prepare queue, actual executed review and all referenced witness/basis files, producer candidate, independent source manifest/cells/receipt, exact source/settings/methods and operational closure evidence together with checksums. Verify remote recoverability before any local purge. The unchanged final196/784 independent audit, exact accepted host-tree join and Stage6 gates remain mandatory.
