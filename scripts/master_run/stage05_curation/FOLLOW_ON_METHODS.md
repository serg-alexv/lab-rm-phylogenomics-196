# Minimum Stage5 curation continuation

These commands are prepared and were not executed on production data. Root owns Stage4 completion/publication, the stable Windows resource lease, fresh ext4 mounting and the full196 native Stage5 run. No new DB, functional annotation download or accepted upstream rerun is needed. Use the mounted retained Python and exact original toolchain prefixes from `audit_settings.template.json`; the Windows empty mountpoint while WSL is stopped is expected.

1. After the actual Stage4 acceptance/publication gate, fresh runtime pin/configuration checks and Linux/DriveFS lifecycle fixtures, complete the full196 native raw jobs through the atomic runner. Preserve successes and immutable payloads. Record an actual source-pinned terminal exception when a genome cannot complete; do not rerun the other195 or synthesize a successful detector receipt.
2. For every successful accession in the unchanged approved196 list, prepare a native/source/domain queue using the command below. `ACCESSION` is one atomic unit within that full-panel iteration, never a reduced biological pilot. No omitted accession is silently ignored in the final contract.

```bash
"$RETAINED_PYTHON" -B "$PACKAGE/stage05_curation_atomic.py" prepare \
  --root "$ROOT" --genome "$GENOMES/$ACCESSION" --accession "$ACCESSION" \
  --approved "$ROOT/config/approved_accessions.txt" \
  --source "$ROOT/.work/source_locus_inputs_v1" \
  --policy-dir "$ROOT/.work/review2/stage05_policy" \
  --models "$MOUNT/defense_models" --padloc-db "$MOUNT/padloc_db" \
  --environment "$MOUNT/detector_env" --reviews "$REVIEWS" \
  --output "$REVIEWS/$ACCESSION/prepare"
```

The variables above are exact paths from the reviewed settings, with `$MOUNT=/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux`, `$GENOMES=$ROOT/.work/stage05_atomic_v1` and `$RETAINED_PYTHON=$MOUNT/detector_env/bin/python`. Output/review namespaces remain in the current chat work directory until root adopts verified results.

For TypeI, inspect actual R/M/S role profiles/source AA and neighborhood together; both native tools permit missing S. Do not map an XML exchangeable such as `PrrC__EcoprrI` to methylation without independent functional-domain evidence. TypeIII needs Mod and Res intact/compatible. Common exact native IIG candidates need a supported dual-function locus plus recognition basis. Independently supported RM-plus-separate-S families instead require the strict two-gene `type_ii_family_architecture` path in `CLASSIFICATION_CONTRACT.md`, including exact cognate S role, separately executed family membership/subtype basis and both source AA/domain bindings. [Furuta2011](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0018819) explicitly describes separate-S TypeIIG predicted families; [BsaXI2022](https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2022.888435/full) explicitly describes TypeIIB RM-plus-S. Fusion alone never assigns IIG. Native numbered/FAM IIG profiles have no established BcgI/BsaXI-specific mapping here; unresolved family identity remains a precise review limitation. Preserve native and reviewed subtype evidence while collapsing the binary cell intoII. TypeIV needs family-specific modification-dependent recognition/cleavage, McrBC or GmrSD partner/fusion review, and explicit TypeII/LlaJI competing-context resolution. TypeIV has no cognate-MTase requirement.

Existing fullscope native HMM evidence is the domain evidence: exact profile SHA, actual report section/domtbl domain, source AA SHA and coordinates. Reopen actual selected PADLOC CSV rows (native rounded selectors), or exact DF gene-level rows and model definitions. Never zip DF system-level independently sorted lists. All rejected, unselected, edge/partial/pseudo, unknown-model, untranslated and circular-origin contexts remain review items. Manual candidates can reuse existing fullscope domains with actual source/context evidence. Do not resolve missing function by annotation substring. If existing family/profile/domain evidence cannot establish a role, record the precise biological ambiguity for that candidate/type. Rounded-selector ambiguity or absent rotation proof remains a specific unresolved limitation, not a panel-wide adapter exception.

3. Actually execute and attribute every queued source/domain/context/candidate/coverage review. Functional roles require the separate `RM_FUNCTIONAL_DOMAIN_ROLE_REVIEW_V1` witness described in `CLASSIFICATION_CONTRACT.md`; no code fills those reviews. The exact model/source/domain references, interval, competing interpretation and functional family basis must support the assigned role. Review overlaps at exact assembly/replicon/locus resolution; repeated WP accessions and duplicate detector rows are not extra systems.

4. Apply each actual review using the same arguments as preparation, phase `apply`, plus `--prepared "$REVIEWS/$ACCESSION/prepare/prepared.json" --review "$REVIEWS/$ACCESSION/executed_review.json" --output "$REVIEWS/$ACCESSION/apply"`. The queue is rebuilt and must be exactly unchanged. Result remains a candidate awaiting independent audit.

5. Fill a copy of `audit_settings.template.json` with actual namespaces and the actual freshly generated `runtime_manifest` (deliberately null in the template). The contract builder records actual runner/supervisor/bridge source SHA and runtime-manifest SHA; those must match the native scientific identity. Its `exception_records` mapping explicitly names actual bounded exception JSON files; `retained_positive_entries` optionally names independently reopenable same-source completed/curated checkpoints for those accessions. All other approved accessions require actual prepare/review/apply files. Then:

```bash
"$RETAINED_PYTHON" -B "$PACKAGE/build_audit_contract.py" \
  --settings "$SETTINGS" --output "$PACKAGE/panel_audit_contract.json"
"$RETAINED_PYTHON" -B "$PACKAGE/rm_matrix.py" \
  --approved "$ROOT/config/approved_accessions.txt" \
  --contract "$PACKAGE/panel_audit_contract.json" --output "$PACKAGE/panel_candidate"
"$RETAINED_PYTHON" -B "$PACKAGE/validate_atomic_curation.py" \
  --contract "$PACKAGE/panel_audit_contract.json" --output "$PACKAGE/independent_curation_audit"
```

No existing output namespace is overwritten. The independent checker reopens every actual source/native/domain/review basis and reconstructs all784 states; the contract builder/serializer cannot confer acceptance. Ordinary PASS requires actual reviewed completion for all196. Qualified PASS allows independently checked, operationally closed documented exceptions. Closure-unproven exit2 is accounting only and vetoes publication/rendering and further native launches. A newly claimed complete positive from an unfinished native attempt requires a separate independent positive-only evidence-packet adapter before scientific acceptance; current support is for independently reopened retained completed/curated checkpoints, and no such incomplete-positive case has occurred here.

6. Only with accepted tree and scientific curation receipts, run `validate_rm_join.py --approved APPROVED --tree ACCEPTED_TREE --matrix MATRIX --state STATE --output NEW_JOIN_RECEIPT`. Require the exact196 tips/rows and784 accession/type cells. Stage6 additionally checks actual tree acceptance, independent curation/source manifest, documented exception manifest when applicable and operational closure. A join PASS alone never proves biology. Actual rendering and publication remain root-owned later stages.

Exception record fields: schema `RM_ATOMIC_CURATION_EXCEPTION_V1`; dataset_kind `PRODUCTION`; accession; approved_sha256; execution_state; bounded reason; source_receipt_sha256; source_input_files (every original source receipt output); current_terminal_receipt (actual `{path:"status.json",sha256}` or null only for an unattempted NOT_RUN); terminal_error copied exactly when attempted; launch_receipts (all retained `{path,sha256,closure_sha256}`; null closure only when genuinely unavailable); process_closure_state `NO_ATTEMPT`, `PROVEN_CLOSED` or `UNPROVEN_RECONCILIATION_REQUIRED`; closure_unresolved_reason when needed; retained_positive_result null or exact `{path,sha256}` matching its independently reopenable positive entry. Paths inside native payloads are genome-relative POSIX. These are real evidence fields, not templates to fill with invented hashes.
