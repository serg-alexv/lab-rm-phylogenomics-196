# Stage5 native file scope and ext4 storage review

2026-10-09; source review and synthetic contracts only. No WSL start, mount, detector search, installation, G write or purge occurred. Biology and actual storage/interop behavior remain **NOT_RUN**.

## Verified native scope

The pinned `native_df_family_scope.json` contains DefenseFinder559 definitions/1092 profiles, RM31/134 and Cas44/525: **1751 family-profile queries per task**, 1733 distinct profile names. The retained builder combines every assembly's multi-protein replicons into one boundary-aware gembase task; each singleton has its own ordered_replicon task. The accepted source accounting contains196 assemblies,1610 multi-protein replicons,239 singleton replicons and271 empty replicons. Every assembly has a gembase task, giving **196+239=435 tasks**,1305 family calls and761685 family-profile queries.1849 is the number of protein-bearing replicons, not this runner's task count. Separate replicon identifiers, ranks and topology still prevent cross-replicon systems; this storage option changes no scientific method or input.

Pinned MacSy sources open `*.search_hmm.out`, `*.search_hmm.err` for fresh searches and `*.res_hmm_extract` even when the extract has no hit. The retained adapter writes successful profile-cache JSON receipts and seed copies, then `copytree`s each completed family native directory into the post-treatment attempt. A cold full panel could therefore create approximately2.285million native files, approximately4.57million including post-treatment copies, plus up toapproximately0.754million profile-cache receipts, seeds, indexes, configs and other receipts. Exact overlap reuse, failed attempts and cohort-specific inputs change these totals. These are source-derived estimates, not observed file counts, byte sizes or timings. Logical reopen/hash volume does not establish physical disk I/O; page cache may serve repeated reads.

PADLOC remains one full5027-profile HMM search per assembly with its native classifier consuming retained domtbl. The compiled approximately984MB database is reopened, not copied per genome. No profile-scope or native-output pruning is recommended before first real measurement and independent raw acceptance.

## Minimal faithful storage strategy

Bind native ext4 `/var/tmp/lab_rm_stage05_atomic_v1` onto the exact Linux canonical project `.work/stage05_atomic_v1` before its first job. Linux `Path.resolve()` does not replace a bind mount with its backing path. Thus actual native argv/cwd, absolute profile-cache paths, native scope sequence_db, effective MacSy configuration, closure_path and root-relative inventory/curation paths keep their existing meanings. A direct copy to a different lexical execution root would invalidate several of those independently reopened bindings; rewriting raw provenance is not an acceptable relocation shortcut.

The Windows G view cannot see the overlay. The lock owner must read terminal/status/complete/raw evidence through `\\wsl.localhost\Ubuntu\mnt\g\...\.work\stage05_atomic_v1`. Canonical compact reports and compressed archives belong on actual G outside the mountpoint. Root owns the mount and Windows UNC changes. The proof helper has no mount or cleanup capability.

`stage5_work_storage.py --root ROOT record --output /mnt/c/.../work/NEW_PROOF.json` observes an already present mount and creates a new proof exclusively. Stdout returns `proof_path` and `proof_sha256`; put them in config `work_storage`. `stage5_work_storage.py --root ROOT validate --config CONFIG` verifies the proof against actual Linux mounts. It requires:

- Exact target ROOT/.work/stage05_atomic_v1 and fixed backing /var/tmp/lab_rm_stage05_atomic_v1; no symlink path components or nested storage mounts.
- Current boot, exact mountinfo target/backing identities, writable ext4, matching directory device/inode, correct bind mount root.
- Actual source block device rdev matching the filesystem device, ext4 superblock magic and nonzero UUID from120 read-only bytes; root WSL privileges are required.
- Exact SHA-pinned proof bytes and helper implementation bytes. Record never overwrites an existing proof; proof must be on C outside the execution overlay.

The runner checks before output/cache/closure access, every native launch, and cache/final completion. Helper SHA is scientific implementation identity; ephemeral proof SHA/boot/mount IDs are not. Reboot/remount requires a fresh verified proof while keeping unchanged scientific inputs/code and all actual prior closure evidence. Model/source locations remain unchanged. Actual mount/UNC equivalence and retained-root access to the block device must pass root's live storage smoke before any biological job.

## Export and limits

Before the mount, root must prove the actual G mountpoint is empty and contains no hidden accepted or unknown evidence. Before a batch/resume, prove ext4 device/inode equality for backing and canonical path, matching UNC view, distinct actual G view, and exact current proof. A missing overlay must fail, never silently resume on DriveFS. Do not unmount or shut down WSL during active native ownership.

After actual terminal exit and native closure, retain full raw evidence and failed/partial attempts. A G archive should include complete/scientific identity, every complete.files member, native cache/logs/closures, current status and transaction records; independently hash/member-check the archive and read it back before a compact receipt marks it available. Its export manifest can be relative for portability, while original raw bytes stay unchanged. Restoring existing absolute native bindings requires reconstruction at the same canonical Linux path through the same fixed backing/mount; a ZIP at another path alone does not constitute resumable evidence. Do not remove ext4 payload until verified remote publication and independent scientific acceptance satisfy the current human's cleanup authority. Archive size/compression/runtime and need for retained release split limits remain unmeasured.

The physical-disk gap is closed separately: the Windows lease must supply a nonempty volume→nonnegative integer free-byte mapping. Admission requires every supplied Windows volume (owner measures actual C and G) **and** the Linux output filesystem to meet the minimum reserve. Sparse WSL virtual free space cannot override physical Windows exhaustion. This is a reserve gate, not a promise that the full cohort fits.

## Source evidence and verification

Read-only retained sources: `.work/detector_review/{build_detector_bundles.py,stage05_detectors.py,native_df_scope.py,native_df_posttreat.py,stage05_inventory.py,native_df_family_scope.json,source_task_count_observation.json}`, vendor `13_macsypy_profile.py`, `06_macsypy_report.py`, `14_macsypy_search_genes.py`, and `scripts/validate_stage05_raw_v6.py`. Existing runner SOURCE_FILES pins bind the scientific adapters; no retained adapter was edited.

Focused Windows synthetic storage tests cover decoded mount paths, exact bind proof, absent/wrong filesystem/backing/inode, nested mounts, changed proof/boot/UUID/helper/mount identity, proof failure before any genome directory/cache access, every-command guard reopening, read-only matching block-device superblock UUID, and no proof overwrite. All actual Linux/WSL/storage/biology cases remain NOT_RUN.
