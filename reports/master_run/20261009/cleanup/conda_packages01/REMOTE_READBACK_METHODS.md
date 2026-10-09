# Exact public Conda originals — independent readback preparation

The checker reopens the actual published Git control bytes at one immutable source commit, downloads the two original Release ZIPs and their original LF sidecars into a new C directory, and verifies every package without extraction or execution. This preparation has not downloaded or verified either production ZIP.

The fixed metadata contract is 397 original manifest records, 339 distinct package SHA256 objects totaling 660,114,049 bytes, two ZIPs containing 363 members, and 361 exhaustive internal SHA256SUMS entries. Each raw package filename, official HTTPS URL, size, SHA256, license, name/version/build and all detector/host manifest row roles must exactly match the two unchanged manifests. Identical package objects shared between environments occur once across the ZIPs. The original upstream archive bytes and notices remain inside those raw objects.

The checker also binds the exact initial resource-stop receipt, recovery plan, preserved-partial policy, 95 freshly reopened/copied source identities, 244 fresh zero-offset download ledger rows, admission observations and actual resource-log minima. These are archived evidence checks; it does not reread the original live package cache or partial file. It preserves the stated exclusions and makes no complete installed-runtime or complete corresponding-source coverage claim.

Required published controls under `reports/master_run/20261009/cleanup/conda_packages01/`:

- The 12 exact basenames in the fixed `public_conda_packages01_final_index.json` controls mapping.
- `final_index.json`, the exact 8,984-byte index SHA256 `f0b6f3a43909a43d5e409afb2f1edd5c04db6fc6f1eba00843534ac3ad9e503c`.
- `CONTINUATION_SOURCE_REVIEW.json`, the exact independent review SHA256 `9def755b2d8917b8c135df9b8498a6ef6075625ca9e4b220b9532b8a145e9c57`.

Required actual source blobs under `scripts/master_run/` are `verify_master_public_components01_remote.py`, `verify_master_original_sidecars.py`, `acquire_public_conda_packages01.py`, `continue_public_conda_packages01.py` and this verifier. The producer files are read as pinned provenance bytes and are never imported. Publish the separate test and preparation receipt alongside them for review.

After root has published the exact reviewed verifier and completed both ZIP/sidecar uploads:

```powershell
$CondaReadbackPython = 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$CondaReadbackWork = 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'
$ReviewedSourceCommit = '<immutable commit containing the exact reviewed reader and controls>'
& $CondaReadbackPython -B "$CondaReadbackWork\verify_public_conda_packages01_remote.py" `
  --source-commit $ReviewedSourceCommit `
  --tag master-run-storage-20261009-v1 `
  --expected-tag-commit 46c7089f906cce59afabaa4449b05df36ee124de
```

No production invocation is authorized by this document alone. Root remains sole publisher and selects the immutable source commit after source review. `--local-inspect` is separately labeled and cannot produce the fresh remote state.

The process lowers only its own priority and uses one 1 MiB streaming reader. Fresh Windows physical RAM and commit headroom must each remain at least 1.5 GiB; C free space must remain at least 10 GiB. Failure preserves the new namespace and stops without automatic retry. Each actual owned `gh` process is monitored at intervals of at most one second, including during network copying. Reserve failure or deadline triggers termination of only that retained child and a five-second closure wait; unproven closure is a failure requiring reconciliation. Bounded stdout/stderr files remain in the new C namespace and avoid pipe deadlocks. Each Git command is bounded, each Release download is limited to 300 seconds, and the aggregate budget is 1,800 seconds plus owned cleanup. Blocking local filesystem reads cannot promise hard kernel cancellation; the source checks the finite budget and resources between buffers. Release tag/asset IDs, uploaded state, digests and sizes are checked before and after full readback.

Only `PASS_FRESH_REMOTE_CONDA339_ORIGINALS_397_ROLES_363_MEMBERS`, actual process exit0, complete published-control readback and unchanged Release identities establish this exact remote package recovery. They grant no cleanup, prune, wipe, biological acceptance, installation or toolchain adoption authority.
