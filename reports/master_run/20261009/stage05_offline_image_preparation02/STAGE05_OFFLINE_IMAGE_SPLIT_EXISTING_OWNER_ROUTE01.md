# Offline image split and installed-runtime route

Source-only preparation. No WSL, native process, Windows image handle, workflow lock, image read/mount/detach/split, upload, delete or restore was performed. Root owns all actual mutations. The current genome must first have its real retained-client/native/owner closure and the requested scientific review. The new files below are callable helpers/one supervised worker, not another controller or source of scientific acceptance.

## Primary implementation

Capture the installed `detector_env`, `defense_models` and `padloc_db` original bytes, metadata and full symlink/hardlink graph with the existing logical capture. Its gzip/tar stream is already partitioned at448MiB and internally names each content role. Preserve all original notices, authors, source/build manifests and actual runtime pins. Independently verify all payload bytes, publish GitHub release parts plus repository source/indices, fresh-download them into a unique owned namespace, verify again, safely restore into a new disposable ext4 tree, then compare all original bytes/metadata/links. Prove original-prefix runtime/model discovery and native compatibility before installed-build equivalence or local eviction.

Separately preserve the public Ubuntu/base bootstrap contract and every project byte stored in the Ubuntu disk. The project's native raw workspace is on that disk (`/var/tmp/lab_rm_stage05_atomic_v1`) even though its canonical bind path is on G. Closed-genome raw archives and unchanged curation review/source manifests must therefore precede WSL-disk cleanup. An Ubuntu reinstall alone cannot recover this workspace.

Literal raw `.ext4` and `.vhdx` splitting is a bounded fallback with its own admission: actual offline writer exclusion, exact file identity, complete source SHA, whole-file public-byte review including allocated and unallocated/deleted bytes, sufficient C disk, and independent recovery. Public review of the three logical roots does not authorize a whole VM image. A scan that finds no token pattern does not establish that unknown/free-space bytes are public. No private/raw images may be published on that basis. Keep raw payloads held if full public audit cannot be established; publish only sanitized inventory/control evidence and the independently public logical recovery components.

## Existing source and new minimal components

Current setup owners are unchanged: Windows `stage5_setup_windows.py`6aa21e4c43c3708abaea3d9fd07913222dee59d52093ddf96a24cddc6a205832 and Linux `stage5_setup_linux.py`24aab72b74dd0aab6c58cac4951c30e6b1bfc9462460486748b546e50ec92e27. Their normal toolchain proof is intentionally RW-only and each setup scope admits at most one exact native command. Their120s Windows/90s Linux ordinary deadlines do not admit an1800s cold inventory. Do not globally relax these predicates.

Prepared components:

- `stage5_runtime_inventory_entry_v2.py`dd3a68f0e1dc86399ca07f95a329f93b955e4e1b4082405a2cd72e8ee10f5363, independent source review8d57fd612967de062acd0ba57c5cff38f45de2cf7078d765a5156e4c07cc1bd1. Existing executable read-only full three-role inventory; raw candidates stay PRIVATE, sanitized summary only. Original v1 remains blocked and unchanged.
- `stage5_runtime_capture_entry.py` is the new opt-in child CLI around the existing capture function. It imports the exact v2 owner bindings and existing process/capture helpers; it creates no owner/lock/subprocess/mount. It binds every request/control/source/current-boot/owner field, limits itself to1800s and sampled512MiB, requires1536MiB current Windows physical+commit reserve and10GiB disk reserve plus remaining worst-case output. It emits local-parts-pending-independent-readback, never remote/cold-restore/eviction acceptance. Six pure tests and default Windows no-op passed. Peer source review is pending.
- `stage5_offline_image_read_parts.py` is the new same-Windows-owner callable component. `ImageReadLease(api,role,expected_identity,owner_guard)` opens the exact image with `GENERIC_READ`, `FILE_SHARE_READ`, `OPEN_EXISTING`, reparse-point handling, and retains the actual handle. It rejects incompatible existing writer/delete sharing rather than closing unknown processes; it checks exact final path, immutable file identity, current same owner PID/FILETIME/nonce and original lock through the callback. The owner supplies actual closure, current resources, deadline and source pins. Cross-DrvFS rejection still requires a real fixture; this helper does not manufacture that proof. Seven pure tests passed. Peer source review is pending.
- `split_public_image(lease,actual_review,new_C_output,snapshot,explicit_source_sha256)` writes fsynced <=448MiB content-labelled parts from that retained handle. It records exact original path/identity, sequential offsets, every part SHA and whole source SHA. It cannot run without the explicit whole-image public review gate. No CLI, upload, delete or eviction is supplied. Output namespace is `C-work/stage5_offline_image_parts_<unique>`.

Current new source/test pins are recorded separately by the publishing owner; preparation hashes are not actual execution receipts.

## Minimum change in the existing setup owner

Add a distinct cold-only branch for inventory or capture to the existing paired Windows/Linux setup owner. Keep all normal step behavior and pins unchanged. Use system `/usr/bin/python3` for the Linux bootstrap outside the toolchain being frozen. Keep the same uninterrupted original Windows WorkflowLock and fresh lease across the branch, plus the existing Linux `tool_mount.lock` and already-existing stable `.native_runner.guard` (open no-follow; never recreate missing guards). Independently verify actual previous selected-genome native/root/group/descendant/retained-WSL/log/unlock receipts before adopting the closed scope. A readable lock or absent PID is insufficient.

The minimum bounded handshake is:

1. **RW qualified.** Reopen the exact accepted toolchain/image/UUID/boot and current native closure. Enumerate relevant mount and same-backing loop aliases; unknown aliases or live users veto the transition. Record immutable initial identities and root-owned source/closure pins.
2. **RW detached.** Through the existing finite native supervisor, synchronize and cleanly unmount only the exact toolchain prefix, detach its expected loop if autoclear has not already done so, then prove all same-backing loop devices/aliases/writer handles are gone. No force or lazy unmount. The Linux bootstrap retains both existing guards and waits on a fresh nonce-bound C handshake, continuously checking the owner lease.
3. **Windows guard acquired.** The existing Windows owner opens `ImageReadLease` only after the real detached receipt, retains it, and publishes the bound handshake. Acquire expected Win32 file identity from actual `GetFileInformationByHandle` metadata; Python `st_dev` is not a substitute for Win32 volume serial. Never hard-code the mutable pre-reboot write time/size as fresh identity. The owner rechecks the real retained handle on every lease renewal. A source identity change between initial read and guard open is a veto.
4. **RO qualified.** While that Windows handle remains open, reopen the exact image with a read-only loop and `ro,noload` ext4 mount at its original prefix. Require actual clean synchronized-unmount/superblock evidence before using no-replay mode. Reobserve exact filesystem UUID, current mount ID/major:minor, kernel block-device read-only state, all same-backing loop mappings and every mount alias; nested/unknown/RW aliases veto. The owner must first run a bounded fixture proving writes through the actual WSL/DrvFS route are rejected by its retained Windows guard. A regular mount `ro` option alone is insufficient and may allow ext4 journal writes; [mount documentation](https://man7.org/linux/man-pages/man8/mount.8.html) describes `ro,noload`, and [ext4 superblock documentation](https://docs.kernel.org/filesystems/ext4/super.html) describes clean/recovery/orphan state.
5. **One worker.** Emit the actual v2 cold proof below and execute exactly one inventory or capture child through the existing supervisor. Inventory and capture are separate finite sessions, allowing whole-file public/notice review between sessions. Capture reopens exact previously reviewed manifest membership, bytes, metadata and links; any intervening drift fails rather than adopting stale inventory.
6. **RO detached.** Close the worker root/group/descendants and retain actual receipts. Unmount and detach only this RO runtime loop; prove it is no longer present. Signal the existing Windows owner to close only its own retained read guard. Wait for the exact same-owner release handshake.
7. **RW restored.** Recreate the original RW runtime mount only after the read guard is released; verify UUID/backing/original prefix, closure of every utility and actual retained WSL exit. Preserve all phase receipts. Rerun applicable fresh setup/runtime/interop/config gates before further scientific jobs because mount IDs/observations changed. Do not reuse stale toolchain proofs merely because file content looks unchanged.

Each native phase needs a finite exact argv/label ledger. Reuse the unchanged `command_readback` per dedicated phase subspool (at most one native command each), then require exact ordered phase membership/count/source/nonce/boot joins in the cold branch. Do not change normal `count<=1`. Use cold-only wall/command bounds sufficient for one1800s worker plus finite utilities/handshakes. Every failed prefix must preserve actual utility/client closure and describe the current mount state. Failure after a mount transition or failure to restore RW retains the durable STOP; owned process closure alone must not clear a filesystem-restoration stop. Expired lease is not permission to launch cleanup commands outside the existing owner. Retain originals and explicit recovery state when restoration cannot be proven.

This cold-only paired branch, its bounded real fixture and actual phase execution remain NOT_IMPLEMENTED/NOT_RUN. The worker and retained-handle functions cannot substitute for it. No currently frozen command safely performs the complete owned detach/guard/RO/worker/RW cycle yet.

## Actual cold proof and worker argv

Root must populate `STAGE05_RUNTIME_COLD_CAPTURE_PROOF_V1` from real same-owner observations:

```text
owner_nonce=current Windows32hex nonce
workflow_lock=exact original path/volume2430728143/index844424932784519/creation134359335921635133/byte0
windows_owner={pid: actual retained owner PID, creation_filetime: actual string FILETIME}
boot_id=current Linux UUID
inventory_entry_source_sha256=dd3a68f0e1dc86399ca07f95a329f93b955e4e1b4082405a2cd72e8ee10f5363
capture_entry_source_sha256=actual reviewed capture-entry SHA (for capture session)
windows_api_source_sha256=80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827
original_workflow_lock_held=true
all_relevant_native_jobs_closed=true (actual receipts, not a process scan inference)
backing_image_writer_exclusion_proven=true (real retained handle + actual cross-DrvFS fixture + all-writer closure)
mount_id=current exact RO mount ID
major_minor=current exact RO ext4 loop major:minor
```

Preserve actual Win32 guard identity, source/closure/phase receipt pins and kernel RO/alias observations as referenced evidence. The worker validates bindings and current mount metadata; it cannot independently discover whether an external Windows owner invented the freeze declarations.

Existing inventory child inner argv:

```bash
"$RETAINED_PYTHON" -B "$WORK/stage5_runtime_inventory_entry_v2.py" --run \
 --source-sha256 "$INVENTORY_SHA" --runtime "$RUNTIME" --runtime-sha256 "$RUNTIME_SHA" \
 --cold-proof "$COLD_PROOF" --cold-proof-sha256 "$COLD_PROOF_SHA" \
 --owner-lease "$LEASE" --owner-nonce "$NONCE" --output-private "$PRIVATE_NEW_OUTPUT"
```

Only publish its `PUBLIC_SUMMARY.json`. Entire `PRIVATE_MANIFEST_DO_NOT_PUBLISH.jsonl`, `PRIVATE_HOLDS_DO_NOT_PUBLISH.json` and any raw audit matches remain local/private until actual whole-file and original-notice review qualifies every required node. No serializer may fill that review to manufacture public eligibility.

New capture child inner argv, after actual whole-file public and notice review plus fresh cold session:

```bash
"$RETAINED_PYTHON" -B "$WORK/stage5_runtime_capture_entry.py" --run \
 --source-sha256 "$CAPTURE_ENTRY_SHA" --inputs "$INPUTS" --inputs-sha256 "$INPUTS_SHA" \
 --runtime "$RUNTIME" --runtime-sha256 "$RUNTIME_SHA" --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_SHA" \
 --public-review "$PUBLIC_REVIEW" --public-review-sha256 "$PUBLIC_REVIEW_SHA" \
 --notices "$NOTICES" --notices-sha256 "$NOTICES_SHA" \
 --cold-proof "$COLD_PROOF" --cold-proof-sha256 "$COLD_PROOF_SHA" \
 --owner-lease "$LEASE" --owner-nonce "$NONCE" --output "$NEW_CAPTURE_OUTPUT" --terminal "$NEW_CAPTURE_TERMINAL"
```

All actual controls must be exact bounded C-work files. Inputs schema is existing `STAGE05_INSTALLED_RUNTIME_CAPTURE_INPUTS_V1`, state `REVIEWED_COLD_CAPTURE_READY`; its six original pins/public/metadata predicates must genuinely qualify. Output parts retain canonical `stage5-installed-runtime-01.partNNNN` names for existing readers. The existing reviewed transport alias plan57a952ad can content-label remote assets while retaining canonical logical names, but an alias-aware actual remote verifier/extractor adapter remains necessary; do not relabel raw GitHub API evidence to satisfy the frozen canonical-name gate.

## Independent readback and cold restore entrypoints

These current APIs have no standalone owner/downloader CLI:

```python
# verify_stage5_runtime_logical_payload.py 9770354da6e9f8cbbab3735f78daadf458b18a86bfae7c90ce2492430c1a74ac
verify_payload(index_raw, expected_index_sha, shards_directory, output, admission)
# stage5_runtime_safe_extract.py beec0d3007da552d956f0d42434bd0ef1fa4ddac080834b0ed66f8aa581fac96
remote_gate(index_raw, remote_raw, expected_remote_sha, payload_raw, expected_payload_sha,
            source_commit, release_tag, tag_commit, remote_verifier_sha, ...)
# extract() additionally requires its exact remaining arguments/current owner.
# verify_stage5_runtime_cold_tree.py cd64e0d4da3ab2509f93d4295af891e0173ed9bef9d81007620bf1f4d872fcfe
validate_restored_tree(manifest_path, manifest_sha256, staging, admission)
```

The frozen remote gate requires real selected asset IDs/names/sizes/digests before/after, exact Git source/index/control bytes, full fresh owned download, closed download clients and receipt age <=15minutes. Current full-payload verification reads every shard, whole gzip CRC and stream SHA, tar inventory, regular file SHA, controls and complete internal symlink graph. Safe extraction uses a new disposable ext4 target, preserves metadata/links, and must not touch original roots. Read-only tree comparison independently verifies restored originals. An owned uploader/downloader and alias-aware remote adapter are still remaining integration; source preparation is not an actual remote proof.

## Ubuntu disk and literal two-file fallback

Collect a deliberately public bootstrap allowlist after current native work closes: OS/distribution/kernel/WSL versions, public package/version/repository digest metadata and notices, actual public bootstrap scripts, sanitized WSL configuration, original-prefix role maps, canonical bind reconstruction and exact project recovery manifests. Review every byte before publication. Exclude credentials, shells/history, homes/root state, service tokens, machine/host keys, authentication caches and unknown configuration. Fresh installation should create fresh machine identity and credentials. A package/version listing proves a reproduction recipe, not exact installed runtime equivalence; the original three-role logical archive supplies the installed bytes and independent cold-restore verification supplies equivalence evidence.

Toolchain literal raw parts require clean detach and the retained read guard above. Ubuntu VHDX requires all Linux/native/WSL clients proven closed, then an owned finite `wsl --shutdown` operation and actual retained Windows writer-exclusion handle on the registered exact VHDX. No Linux worker may be reading this live registered VHDX while Stage5 uses it. Preserve registration metadata and the exact offline image identity. Its raw contents include project workspace and potentially private/deleted state; only the separately executed complete whole-byte public review can admit `split_public_image`.

Actual helper call in the same original Windows owner, after these gates:

```python
with ImageReadLease(api, role, actual_win32_identity, existing_owner_guard) as retained:
    parts = split_public_image(retained, actual_whole_image_public_review,
                               fresh_direct_C_output, '20261010-v1', published_helper_sha)
```

Role is exactly `toolchain_ext4` or `ubuntu_vhdx`; no arbitrary target is accepted. Parts use content role plus snapshot and sequential offsets. Each raw part is at most448MiB, is an opaque portion of a disk image (not individually mountable), and must be concatenated unchanged in listed order. Raw reassembly must match the externally audited whole SHA. Source/canonical/raw names remain mapped; never rename active registered/backing disks. Independent fresh GitHub asset readback and full reassembly/cold import/restore verification precede local eviction or host wipe. No such raw image audit/split/upload/restore has run.
