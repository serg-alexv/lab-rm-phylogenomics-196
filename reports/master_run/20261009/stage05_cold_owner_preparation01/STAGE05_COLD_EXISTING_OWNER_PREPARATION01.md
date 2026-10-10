# Existing paired owner cold branch: source preparation only

The new `stage5_setup_cold_windows.py` and `stage5_setup_cold_linux.py` are explicit variants of the existing 6aa21e4c/24aab72b setup pair. They retain all original function ASTs, including ordinary writable toolchain observation and the Windows reader that accepts at most one native command. They add one cold branch inside that pair, without invoking another workflow owner. Both files default to NO_OP. No actual cold launch, handle acquisition, mount, inventory, capture, split, remote transfer or cleanup has occurred.

The first closed Stage5 genome and its actual independent curation/archive remain the root owner's priority. This source packet does not adopt a scientific result or authorize local eviction. GitHub `main` and its verified recovery assets remain the primary project authority.

## Exact source pins

| File | SHA256 |
| --- | --- |
| stage5_setup_cold_windows.py | e81ca9b5f2b3402b1fa983270bf32fe60b16cdf2b1c4d1c9f043bf7164c4a2d1 |
| stage5_setup_cold_linux.py | d10faf17d42db44243f10fa1908fede549f3dd20ff58013fcaa37f36f3eeb9d5 |
| test_stage5_setup_cold_owner.py | 1a53d1182995d25e77740893de7fa98a7a5cadfe46475430d1e6cc10378d0fcd |

Twenty pure/synthetic tests pass, including unchanged ordinary function ASTs, strict immutable lock identity, dirty/journal/orphan rejection, write-open refusal semantics with no writes, exact POSIX worker argv, full ordered synthetic ledger, and count/argv/hash-chain/skipped-phase tamper rejection. Both default NOOP executions pass on Windows. These tests do not validate actual kernel behavior, Windows sharing across DrvFS, real mounts, the full Linux owner, resource sufficiency, or cold recovery. Independent integration source review is pending. The corrected underlying inventory/capture/image helper review is a separate PASS_SOURCE_ONLY report: `stage5_corrected_capture_helpers_independent_review01.json`, SHA256 `50585e236a8b3c49ecda1fd5273a7ead72bdae76252ec0565bd79610c1e98bac`.

## One lock, finite phases

The Windows variant acquires the original unchanged WorkflowLock once and renews the existing three-second owner lease. One retained `/usr/bin/python3` Linux bootstrap remains alive while the toolchain prefix is detached. It holds the existing tool-mount and global native-runner guards. Every native phase has its own fresh subspool, containing zero or one command as permitted by the unchanged ordinary reader. The extra ordered ledger validates the fixed phase membership, exact argv, source pins, owner nonce, boot, hash chain and complete native command accounting.

1. Validate current original 24aa RW toolchain proof, prior scientific native launch/intent closure receipts, global native guard, current process references and mount namespaces, and the sole exact image loop.
2. Clean unmount the original prefix; detach its exact loop if clean unmount did not already auto-detach it. No force or lazy unmount.
3. Prove no image-backed loop or old mount alias remains, inspect bounded clean ext4 superblock flags/UUID, and repeat process-reference exclusion.
4. Signal the Windows owner. It obtains an exact metadata snapshot, checks closure of its metadata handle, then retains the corrected helper's GENERIC_READ/FILE_SHARE_READ image handle, denying writes/deletes. Its expected identity is a private immutable snapshot. The same original owner checks identity on every renewal.
5. Linux attempts actual `O_RDWR|O_NOFOLLOW` against the exact DrvFS image path. Only an actual permission/sharing/busy refusal is accepted. No write is called. A successful write-open is immediately checked closed and vetoes the step.
6. Attach one kernel read-only loop, mount the original prefix as ext4 `ro,noload`, and validate loop identity, kernel read-only flag, UUID, mount device/root and every read-only alias.
7. Generate an actual source/boot/owner/immutable-lock-bound cold proof, then run exactly one inventory_v3 or capture_v2 child under the existing Supervisor.
8. Cleanly unmount RO, explicitly detach that loop, and prove detached state again.
9. Signal the same Windows owner. It checks and closes its retained image handle; only actual successful CloseHandle allows a release acknowledgement.
10. Restore the original RW toolchain mount and run the existing pinned runtime discovery again. Actual rediscovery bytes must hash to `f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1` before restoration is credited.

The source enforces a 3600-second Linux owner bound and a 3660-second Windows owner bound. Worker and rediscovery phases have separate finite bounds. Utilities have finite native timeouts. The Linux bootstrap sets a per-process inherited 512MiB RLIMIT_AS before control parsing; the existing Supervisor separately samples child-tree RSS and closes exact pidfd-tracked descendants. This is not an aggregate kernel memory cap. Windows physical/commit admission keeps a 1536MiB reserve plus a 640MiB parent/worker allocation and at least 10GiB free on each measured volume; capture_v2 additionally admits the full output capacity. Actual sufficiency is unmeasured.

The durable STOP is written before launch intent and is removed only after a successful worker, complete actual native/WSL closure, checked image-handle release, RW restoration and exact runtime06 rediscovery. A known closed worker failure can complete normal restoration, but still returns failure and retains STOP for reconciliation. Uncertain scope, writer exclusion, handle closure or restoration stops the branch. It does not create a second controller or automatically force repairs after uncertainty.

## Two actual sessions and required review

Inventory is the first later actual cold session. It creates a clearly private direct-C inventory/hold namespace and a sanitized public summary. After it restores RW, root must execute full original-byte/public-path/special-metadata/notice review. Pattern screening alone does not establish public scope. The inventory and all private matches must not be blindly published.

Capture is a second later actual session. It requires the exact inventory, public review and notice review byte pins and explicit scope/metadata approval flags. The owner binds those fixed controls to the fresh actual cold proof; capture_v2 independently checks the controls and every original node. Capture must fail if loop-device identity, source inode/ctime, contents, metadata, original link graph or coverage changed between inventory and capture. The owner does not relabel changed evidence to make an old inventory pass.

The three portable logical roles remain primary: the original `detector_env`, `defense_models` and `padloc_db` under their original prefixes, preserved with notices and complete metadata/link semantics in canonical parts no larger than 448MiB. Whole toolchain/VHDX raw parts are not produced by this branch. Ubuntu `ext4.vhdx` still needs its separate truly offline WSL boundary, whole allocated/unallocated/deleted-byte audit, and either independently public original bytes or a documented sanitized cold copy. Logical role archives and OS bootstrap do not count as literal splitting of both image files.

## Later exact entrypoint form

Root must first reconcile current GitHub authority, close the first genome, obtain fresh original 24aa toolchain and controller closure receipts, validate this new source review, and independently verify the published Windows/Linux source SHA256s. The reviewed Windows Python entrypoint is:

```powershell
& 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B `
  'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_setup_cold_windows.py' `
  --cold --mode inventory --output '<NEW_DIRECT_C_WORK_STAGE5_SETUP_COLD_SPOOL>' `
  --linux-source-sha256 d10faf17d42db44243f10fa1908fede549f3dd20ff58013fcaa37f36f3eeb9d5 `
  --controller-receipt '<ACTUAL_RETAINED_CONTROLLER_CLOSURE_JSON>' `
  --controller-receipt-sha256 '<ACTUAL_CONTROLLER_RECEIPT_SHA256>' `
  --controller-observer-sha256 483b5165d015dcea659d5e850187c79ff5e99c4c0efff1c9fb108cc9a59ab78a `
  --toolchain-proof '<FRESH_ACTUAL_ORIGINAL24AA_RW_PROOF_JSON>' `
  --toolchain-proof-sha256 '<ACTUAL_FRESH_RW_PROOF_SHA256>' `
  --runtime '<ACTUAL_RUNTIME06_OR_BYTE_IDENTICAL_SUCCESSOR_JSON>' `
  --runtime-sha256 f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1
```

This command deliberately omits `--run` and therefore remains NO_OP. Only root may add `--run` after actual admission. Capture uses `--mode capture` plus `--manifest/--manifest-sha256`, `--public-review/--public-review-sha256`, `--notices/--notices-sha256`, `--all-required-runtime-files-public-and-covered`, and `--all-special-metadata-resolved`. The source creates fresh nonce-labelled direct-C worker outputs, proof, and capture request; no arbitrary native argv is accepted.

## Remaining actual integration criteria

Independent source peer review and a disposable Linux fixture must precede original-image adoption. Real DrvFS sharing refusal, alias/writer exclusion, clean detach, actual no-journal RO access, all failure/retained-handle/STOP paths, exact native+WSL closure and RW restoration require actual owner evidence. Successful unchanged-byte restore to the original prefixes must reproduce the same scientific runtime manifest SHA; a new mount or boot alone must not change a deterministic content/ambient manifest. If runtime07 equals the same SHA it joins directly; if it differs the branch vetoes rather than silently migrating the scientific runtime pin.

After local logical capture, existing independent full payload, remote asset, fresh owned download and cold-tree validators still must run against actual bytes. Actual remote storage verification, canonical reader acceptance and a successful fresh cold restore are required before any local eviction or host wipe. No cleanup authority is granted by this source packet.
