# Storage-only builder adaptation

`stage5_build_storage_recovery_actual_config.py` is a separate, default-NOOP adaptation of preserved `stage5_build_backing_actual_config.py` (SHA256 `e1b7b4782be7cb4faa84cf546884075e860d2d010a1774ba7d61846bfff7905c`). It prepares a config only after the root has supplied the six actual closed gate receipts and an explicit request. No config was built by this source-preparation step.

The only accepted storage source pair is:

- `stage5_setup_storage_recovery_windows.py`, SHA256 `bdc7b95781950be54bd339c483f31bb8462b5b41ad76bbe21bb5fe37ccdcb7fa`.
- `stage5_setup_storage_recovery_linux.py`, SHA256 `edac2a12a8b1a72d2224264ad4913a79677168dc233ca796c733112b8e32fd8a`.

The existing `PINS` dictionary remains identical. A separate two-file `STORAGE_RECOVERY_PINS` dictionary is included alongside it in both initial and final all-file byte checks and recorded separately in the build receipt. For `checked_gate('storage', ...)` alone, the expected Windows/Linux source identities select the new pair. Storage additionally requires the exact existing nonscientific setup scope, retained-client closure, checked original unlock, durable unlock receipt bound to the requested unlock SHA, and owned STOP cleared after unlock. The Linux storage terminal keeps its exact setup scope and new Linux source identity. The old pair cannot qualify storage in this variant; the new pair cannot qualify toolchain, runtime or DriveFS.

Toolchain08, runtime09 and DriveFS05 continue to require original Windows6aa21 and Linux24aab. UNC continues to require the reviewed backing probe779502 and its complete two-way cleanup phases. The unchanged W7e06 storage proof, canonical target, backing path, actual selected candidate SHA and final UNC storage-proof join remain mandatory.

This builder does not replace the dedicated storage07 independent actual reader. Before root adoption, that reader must verify the complete freshly observed prepared backing before and after binding against the capacity02 closure peer e7cb6737 and snapshot451c91ca, all 52 objects, preserved scientific identity/execution freeze, the current boot, UUID3370e495 and root inode33554542, plus the actual checked unlock receipt. The builder retains the established gate-hash contract; it introduces no alternate closure or membership framework.

All standalone function ASTs are unchanged except `checked_gate` and `main`. The complete explicit-resource policy function is unchanged: all five positive byte budgets remain supplied by the request; Windows reserve1.5GiB, Linux reserve1GiB, two threads and bounded resource wait1800s remain exact. R500dc, P e5be, the config template941377, scientific inputs, full detection methods and fresh native admission remain unchanged. Existing native resource queries, original WorkflowLock and final config loader call ASTs remain identical. No detector or biological result is produced by config construction.

Root-owned CLI, only after the variant and its peer are published and all actual current-boot gates qualify:

```text
stage5_build_storage_recovery_actual_config.py --build
 --request <fresh-direct-C-work-request.json>
 --request-sha256 <actual-published-request-SHA256>
 --output <fresh-direct-C-work-config.json>
```

No placeholder request, source SHA, gate or future config is accepted by this preparation. The root remains sole owner of any later build, WorkflowLock, Windows query, WSL/UNC operation or Git action.

Validation completed: 16 pure tests, including the seven applicable inherited backing-builder contracts, source/function/native-call preservation, source pair routing in all four setup branches, storage source/scope/unlock tamper vetoes, exact terminal pin vetoes, unchanged admission budgets and both original-plus-pair source rechecks. Bare actual-main execution reports `PREPARED_NOT_RUN` and performs no gate reads or native imports. Actual storage recovery/config construction/science/cleanup remain NOT_RUN by this source-preparation step.
