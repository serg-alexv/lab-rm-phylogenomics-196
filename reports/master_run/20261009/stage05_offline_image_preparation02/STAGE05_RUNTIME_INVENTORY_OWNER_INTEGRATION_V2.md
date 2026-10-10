# Current inventory worker and minimal existing-owner integration

The original inventory worker `stage5_runtime_inventory_entry.py` is preserved
as preparation history and **blocked for actual adoption**. Independent review
found that matching two missing or arbitrary lock objects could pass its owner
binding. It was never invoked on Linux. Its default no-op and metadata-only
preparation did not authorize any capture, image split, eviction or host wipe.

The separate `stage5_runtime_inventory_entry_v2.py` fixes that defect and the
review's accompanying proof gaps. It requires the complete exact original lock
path/volume/index/creation/byte with exact field types in both proof and lease,
the retained Windows owner PID/string FILETIME birth in the proof matching the
fresh lease throughout, current Linux boot, exact entry/API source pins, and
final entry/runtime/cold-proof/boot rechecks. Seven synthetic authority tamper
tests and the Windows default no-op passed. Actual Linux fixtures and owner
integration remain NOT_RUN.

The current cold-proof schema must include these fields, populated from actual
retained owner and Linux witnesses, without guessing or reconstructing old
closure:

```text
schema = STAGE05_RUNTIME_COLD_CAPTURE_PROOF_V1
owner_nonce = current Windows owner's32hex nonce
workflow_lock = exact original WorkflowLock identity
windows_owner = {pid: current retained owner PID,
                 creation_filetime: current retained owner FILETIME as string}
boot_id = current Linux /proc/sys/kernel/random/boot_id
inventory_entry_source_sha256 = published current v2 source SHA
windows_api_source_sha256 =80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827
original_workflow_lock_held = true, from actual owner receipt
all_relevant_native_jobs_closed = true, from actual terminal/Job/group receipts
backing_image_writer_exclusion_proven = true, only after actual writer exclusion
mount_id = current exact frozen mount ID
major_minor = current exact ext4 loop device major:minor
```

The v2 worker checks these declarations against the current lease/mount but does
not create a freeze or prove that an external backing-image writer was closed.
Keep the original Windows byte lock across the complete cold operation. Retain
the existing `.work/tool_mount.lock` Linux lock and native runner guard while
changing runtime mounts. The system `/usr/bin/python3` bootstrap must run outside
the retained toolchain mount so that a controlled unmount is possible.

The existing setup owner imposes two constraints that require explicit code
changes: its toolchain proof currently requires anRW mount, and its native
command reader permits at most one command per setup scope. Do not relax either
predicate globally. Add a distinct cold-inventory branch and either an exact
ordered label/argv list for its owned native commands, or one allowed supervised
worker per retained phase under the same uninterrupted original owner.

The proposed operational phases are:

1. Qualify current Stage5 native closure and the exact loop image/mount, hold
   both existing guards, and preserve theRW proof. Synchronize and unmount only
   the exact toolchain prefix; require the expected loop mapping/aliases to be
   detached and no unknown native users. Every native utility must be launched
   through the existing finite supervisor with exact argv and terminal receipt.
2. With the loop's write handle closed, the Windows owner opens the exact image
   for read with sharing that denies writes/deletion, checks its immutable file
   identity and retains that handle through inventory/capture. An existing
   writer/sharing failure is a veto, not permission to force close unknown
   processes. Reopen the Linux loop image read-only and mount the ext4 filesystem
   at its original prefix read-only, without journal replay only after a clean
   synchronized unmount. Prove block-device read-only status, exact UUID/backing,
   all mount aliases read-only, original Windows identity and the retained
   Windows write-exclusion handle. This combination needs a real bounded
   fixture; mountRO alone does not establish backing-writer exclusion.
3. Emit the actual cold proof bound to this owner and launch exactly one v2
   worker using the existing Linux supervisor:

   `<retained env>/bin/python -B <work>/stage5_runtime_inventory_entry_v2.py --run`
   with the existing documented runtime/SHA, cold-proof/SHA, same lease/nonce,
   published v2 source SHA and a new `stage5_runtime_inventory_private_*` output.
   Retain the worker's raw private manifest/holds and only publish its small
   counts/digest summary. Do not mark public scope accepted automatically.
4. After actual private inventory review and complete public/notice acceptance,
   run the existing pinned logical capture function under the same finite owner
   admission. Otherwise preserve the original image and private candidates;
   no capture may omit a required private dependency. No Stage5 detector runs
   concurrently with this cold operation.
5. Obtain native/WSL closure, detach the read-only loop, release only the owned
   Windows backing-file read handle, restore the originalRW runtime mount and
   qualify fresh boot-sensitive Stage5 mount/runtime/storage controls before
   resuming detectors. Failure preserves all originals and STOP where closure
   remains unknown; it never forces a second owner or retries automatically.

Use a1900-second Windows owner deadline around an1800-second worker deadline,
512MiB sampled worker RSS allocation and current1536MiB Windows physical and
commit reserves in addition to that allocation. The sampled RSS stop is not a
kernel memory cap. Preserve the existing supervisor's process/group/descendant
closure and resource enforcement. This is an integration proposal with an
implemented inventory worker; the cold transition, Windows exclusion handle,
owner step changes and actual full capture are not executed or accepted yet.
