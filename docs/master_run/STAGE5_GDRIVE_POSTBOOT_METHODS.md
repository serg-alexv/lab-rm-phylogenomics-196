# Fresh-boot G-drive view owner

`stage5_gdrive_view_postboot.py` is a separate revision of the existing reviewed
G-view helper. The original `stage5_gdrive_view.py` remains byte-identical at
SHA256 `edc02834f889cdd9bed8bce350d2b9fe2bbd79347f65a0ae124afdaec9f4dfa8`.

The new source adds `--fresh-toolchain-proof` and
`--fresh-toolchain-proof-sha256`. Actual Windows invocation requires the exact
published toolchain05 proof at `work/stage5_setup_toolchain_actual_postiq_05/`.
Six immutable pins bind its result, unlock, proof, Linux terminal, retained WSL
terminal and independent actual acceptance. Both the Windows owner and Linux
bootstrap re-read those pins; the Linux current boot must match the fresh proof.
Final source/proof readbacks prevent adopting changed evidence after admission.

The original closed storage02 and toolchain04 historical checks remain intact.
Their old boot is recorded as historical provenance and is no longer the boot
required for a new helper execution. The historical failure is not relabeled.
All operative source pins retain setup6aa21e4c and its existing dependencies.

Default invocation remains a no-op, even with `--mount`. After independent
source review and GitHub publication, the root may run a diagnosis first:

```powershell
& 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B `
  'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_gdrive_view_postboot.py' `
  --fresh-toolchain-proof 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_setup_toolchain_actual_postiq_05\toolchain_proof.json' `
  --fresh-toolchain-proof-sha256 106e1bc310f11d34d78f0d7bdc2b311a2b457e5c68c0e32aad3f8fc0a718446c --run
```

Diagnosis does not mount. Only an actual qualified missing-G observation can
justify a later explicit `--mount` invocation. The existing strict exact-G,
empty-underlay, namespace, nested/stacked-mount, control-byte and prelaunch
checks remain unchanged. The helper must precede creation of the nested Stage5
ext4 bind; an existing bind causes its conservative nested-mount veto.

Three focused C-only contracts passed: default no-op; exact fresh toolchain05
selection with old04/wrong/missing SHA rejection; rejection of altered receipt
joins even when their local file hashes are consistently updated. No WSL,
mount, native API owner, detector or actual G view action ran in preparation.
