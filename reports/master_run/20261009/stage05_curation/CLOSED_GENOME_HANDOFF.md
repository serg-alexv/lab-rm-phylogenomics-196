# Closed-genome curation operational handoff

Source-only inspection of the frozen current package; actual production prepare/apply/curation remains NOT_RUN. No WSL, native detector, G write, source edit or new controller was used for this report. The raw native complete receipt stays an immutable raw-only checkpoint; curation outputs never rewrite it into a biological success receipt.

Current source pins: `stage05_curation_atomic.py`20e860b58737e74061a0e7a8b4c8ac21a8e6d95aa1a0685cfbc5bc54ced0deb0; `validate_atomic_curation.py`89a42d63401ef1ef3479690546a3c8cad4da679517aa2ed7da6b4e6716b6af0c; `build_audit_contract.py`72aedecb9549763622d5811e9179f91c0085bd8723f461a2ed4c9c2f79b6a1c6; `rm_matrix.py`7716f722f25b582af990469d4e5120d4de22828b87c89cf334d2d9f9723c7db9. The standalone accepted-source manifest remains a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84. Exact methods/biological predicates are in `stage05_curation/FOLLOW_ON_METHODS.md`383e85be903de4486d63ec8a57786c7ce5463f831474a03b6855385b09a36caf and `CLASSIFICATION_CONTRACT.md`28a5b85588a63ea6de0e16715a29366ad039995637c0602a38919cf520ce36ae.

## First closed genome

Root supplies the actual approved accession and an operationally closed native V2 checkpoint. `complete.json` must be `STAGE05_ATOMIC_GENOME_COMPLETE_V1` / `COMPLETE_VALIDATED`, validation scope `NATIVE_SEARCH_SOURCE_AND_RAW_INTEGRITY_ONLY`, curation `NOT_RUN`, biological absence claim `NONE`; V2 scientific identity pins actual accepted source/runtime/code. Its selected raw audit must be `PASS_FULL_NATIVE_SEARCH_AND_SOURCE_ACCOUNTING_ONLY`. Every payload hash, native launch/closure pair and source binding must remain exact. Neither detector nor curation input depends on a host tree.

Set the existing variables, with actual freshly verified runtime/model roots:

```bash
ROOT='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
PACKAGE='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage05_curation'
MOUNT='/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux'
RETAINED_PYTHON="$MOUNT/detector_env/bin/python"
GENOMES="$ROOT/.work/stage05_atomic_v1"
REVIEWS="$PACKAGE/reviewed"
# ACCESSION is one actual approved versioned accession, not a replacement panel.
"$RETAINED_PYTHON" -B "$PACKAGE/stage05_curation_atomic.py" prepare \
  --root "$ROOT" --genome "$GENOMES/$ACCESSION" --accession "$ACCESSION" \
  --approved "$ROOT/config/approved_accessions.txt" \
  --source "$ROOT/.work/source_locus_inputs_v1" \
  --policy-dir "$ROOT/.work/review2/stage05_policy" \
  --models "$MOUNT/defense_models" --padloc-db "$MOUNT/padloc_db" \
  --environment "$MOUNT/detector_env" --reviews "$REVIEWS" \
  --output "$REVIEWS/$ACCESSION/prepare"
```

This creates a hash-bound `prepared.json` queue. Actual scientific review must reopen every queued raw domain/native and rejected candidate/source context/unmapped model/edge or origin item. It must explicitly resolve or retain its uncertainty, deduplicate exact genomic loci/overlaps, and execute four type-specific full-scope coverage reviews. Generic protein annotations or native system names do not establish roles. Actual role/domain/family basis, exact model and AA/coordinates, competing interpretations, typed file/record references and reviewer attribution are required. Independent functional-role or multipart-family witnesses must be separately executed and attributed as the contract specifies. Review flags cannot be filled by a serializer to manufacture scientific acceptance. Existing full-scope native domain evidence is reused; no new biological search is part of these commands.

Apply the actual executed review with the identical preparation arguments, replacing phase/output and adding:

```bash
# Same required root/genome/accession/approved/source/policy/models/database/environment/reviews arguments.
"$RETAINED_PYTHON" -B "$PACKAGE/stage05_curation_atomic.py" apply \
  --root "$ROOT" --genome "$GENOMES/$ACCESSION" --accession "$ACCESSION" \
  --approved "$ROOT/config/approved_accessions.txt" --source "$ROOT/.work/source_locus_inputs_v1" \
  --policy-dir "$ROOT/.work/review2/stage05_policy" \
  --models "$MOUNT/defense_models" --padloc-db "$MOUNT/padloc_db" \
  --environment "$MOUNT/detector_env" --reviews "$REVIEWS" \
  --prepared "$REVIEWS/$ACCESSION/prepare/prepared.json" \
  --review "$REVIEWS/$ACCESSION/executed_review.json" \
  --output "$REVIEWS/$ACCESSION/apply"
```

The queue is rebuilt and must equal the prepared queue. `apply/curated_candidate.json` remains `INDEPENDENT_CURATED_VALIDATION_REQUIRED`. Reliable complete presence1 survives additional unresolved loci; without a reliable complete positive, partial/unresolved/not-run remains NA. Zero requires actual successful complete screening and no accepted or unresolved qualifying candidate. Counts/uncertainty and positive invalidation remain separate.

## Independent audit boundary

**Existing executable independent acceptance is full-panel only.** `build_audit_contract.py` requires all196 entries in frozen order, each actual prepared/review/result or genuine source-bound exception. `validate_atomic_curation.py` requires exact196/784 serialized cells, accepted source controls, producer/dependency pins, actual runtime manifest and runtime/model byte rehash, then independently reconstructs every cell. Use the existing settings template with actual paths/runtime manifest; its null runtime field is deliberately unfilled preparation.

```bash
"$RETAINED_PYTHON" -B "$PACKAGE/build_audit_contract.py" --settings "$SETTINGS" --output "$CONTRACT"
"$RETAINED_PYTHON" -B "$PACKAGE/rm_matrix.py" --approved "$ROOT/config/approved_accessions.txt" --contract "$CONTRACT" --output "$NEW_PANEL_OUTPUT"
"$RETAINED_PYTHON" -B "$PACKAGE/validate_atomic_curation.py" --contract "$CONTRACT" --output "$NEW_INDEPENDENT_AUDIT"
```

Concrete incremental-acceptance gap: the independent checker has internal `atomic_one(entry,contract,core)` returning four reconstructed cells and an audit, but no per-genome CLI/certificate. Calling it alone omits outer source-validation/producer/dependency/model-scope checks and `native_provenance(contract)`; it must not be represented as independent scientific acceptance. If root needs acceptance before the full panel, the minimum follow-on is one narrow wrapper around those same outer gates plus `atomic_one`, with a distinct four-cell/per-genome status that cannot authorize the final matrix/figure. No such wrapper or source/schema change was implemented here. Existing per-genome prepare/apply can proceed now after each actual closed checkpoint and actual review, with candidate state preserved. Do not invent195 NOT_RUN exceptions merely to disguise an unfinished active panel as final acceptance.

Genuine documented exceptions are allowed in the final196 accounting. Proven-closed exceptions may qualify `PASS_INDEPENDENT_RM_CURATION_WITH_DOCUMENTED_EXCEPTIONS`; unproven native closure yields accounting-only exit2 and vetoes acceptance/rendering/new launch. Reliable positives from independently reopenable frozen completed/curated checkpoints may survive exceptions; mutable unfinished attempt outputs cannot establish a new accepted positive.

## Per-genome preservation and rehydration

Preserve unchanged `complete.json` and **every selected `complete.files` member**, with original genome-relative POSIX names. This includes all bundle/execution/native profile and query outputs, execution freeze, selected inventory/bundle audit/raw-validation attempts, exact commands and all manifest-pinned `.launch.json`/`.closure.json` pairs. Keeping just normalized inventory tables is insufficient: both bridge and independent audit reopen the original raw report/domain/native row bytes and model/profile hashes. Closure evidence is scientific-adoption input, not a filename inferred from process absence.

Also preserve the exact prepared queue, executed review, curated candidate, every qualified review/domain/functional-role/family/primary-basis witness they reference, the current curation package/source pins and actual runtime manifest. Accepted canonical source inputs/policy/model/environment bytes may be recovered from separately verified source/component archives, but remain mandatory reopened dependencies. An archive must identify those recovery dependencies explicitly; a ZIP of one genome does not prove full toolchain restoration.

Current bridge/checker require resolved genome under canonical ROOT and exact prepared `evidence_roots`; `source_snapshot` contains canonical relative paths. The planned ext4 bind overlay on canonical `$ROOT/.work/stage05_atomic_v1` preserves those strings. Rehydrate to that exact canonical location before using the existing readers. Do not silently substitute `/var/tmp/...` or rewrite archived prepared references. Reviews are outside the immutable raw checkpoint; archive them as separate unchanged payloads with an explicit original-path mapping rather than editing the raw `complete.files` manifest.

Final `validate_rm_join.py` still requires the independently accepted host tree plus exact approved196×four cells. Production Stage6 also requires independent tree acceptance, independent curation/source manifest, applicable documented-exception manifest and operational closure. Tree-tip accounting and workflow publication acceptance remain separate gates. No real curation, runtime discovery, Linux bind/UNC proof or Stage5 native measurement was claimed by this source-only handoff.
