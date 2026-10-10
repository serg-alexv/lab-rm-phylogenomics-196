# Checked original unlock before raw archive STOP release

This is a separate C-only source correction. Original Windows source `stage5_closed_genome_archive_windows.py` SHA256 `249b9de14219d8c0a5f1e7e88e48f6c80694bd04699c7c3e506b50a0980fab45` remains unchanged. Actual archive, WSL, native/runtime/API/OS-lock action, upload, deletion and scientific curation are NOT_RUN by this preparation.

The original owner cleared its own launch STOP inside the original WorkflowLock context, before `__exit__` performed the checked byte unlock. Its result could therefore precede the unlock, and an unlock failure could follow STOP removal. The separate `stage5_closed_genome_archive_windows_checked_unlock.py` keeps that same lock object, enters it explicitly and calls its checked original `__exit__` exactly once in the outer finally. All original top-level imports/constants/PINS and non-main function ASTs are unchanged. The same Linux helper, argv, deadlines, resources, original closed-genome/source/config/nonce checks, retained WSL exit/Linux closure, 448 MiB compressed asset cap and canonical storage path remain in use. No controller, retry scheduler or biological algorithm is added.

After validated Linux bytes the intermediate state is `RAW_RECOVERY_ZIP_BYTES_VALIDATED_PENDING_EXPLICIT_UNLOCK`. The owner invalidates its lease, completes the retained-client closure and power-restoration finalizers, preserves the pre-unlock result, then:

1. Calls the original checked byte unlock; requires `lock.released is True`.
2. Atomically writes `lock_released.json`, reopens the exact receipt and records its SHA256.
3. Requires proven native/client closure and successful lease/power/closure finalizers. Only then, and only when both STOP SHA256 and owner nonce still match this invocation, removes that exact STOP.
4. Marks PASS only after the preceding checks and persists the final result. A closed failed archive stays FAILED, even when its owned STOP can now be cleared. Unknown closure, failed unlock/receipt/finalizer or changed/foreign STOP preserves the STOP and cannot yield PASS.

If the final result publication fails after actual closure/unlock, the owner returns failure and makes one bounded attempt to write/read back `publication_failure.json`. That receipt separates publication reconciliation from process closure; the owner does not invent an unclosed-process STOP after closure was proven. A second persistence failure is recorded in memory and exits unsuccessfully without a retry loop. Root must reconcile retained terminal/build/unlock evidence before accepting any archive. A source test PASS does not establish actual Linux ZIP bytes, cloud durability, restore or cleanup eligibility.

There is no backing-alias change here. AST inspection finds the imported original Windows owner used only for `LOCAL_CLOSURE_STOP` and `fresh_authority`; this archive owner does not call `evidence_view` or read UNC. Linux continues to reopen the canonical ext4 genome path and validate current storage. Swapping its import to the backing owner would add an unnecessary source dependency.

Twelve authored pure tests passed using fake lock/API objects and small own C temporary JSON files. They cover STOP presence through unlock/receipt readback, unlock exception/unreleased return, receipt write/readback/hash faults, foreign nonce/changed STOP, closed failed archive, unproven closure, lease/power/closure finalizer faults, single/double publication failure, preserved original function/constants/PINS, finally wiring and default NOOP without any actual runtime/API import. A separate Windows default NOOP also passed.

Root's later actual CLI retains the original arguments and uses only the new filename:

```text
python -B work/stage5_closed_genome_archive_windows_checked_unlock.py --run --config EXACT_CONFIG --config-sha256 EXACT_SHA --accession GCF_000009425.1 --prior-owner-result EXACT_C_RESULT --prior-owner-result-sha256 EXACT_SHA --complete-sha256 EXACT_RAW_COMPLETE_SHA --output FRESH_DIRECT_C_WORK_SPOOL
```

This command is documentation, not execution. Publish/read back the independent source review first; actual complete/prior owner/config hashes must come from the genuinely closed full-method genome. ZIP byte acceptance is separate from executed scientific curation and from remote recovery/restore checks required before local purge.
