# Exact 32-path post-fast-forward index metadata repair

Preparation only. The canonical checkout is already at `c76a46163af8b26057a113599f0524dfa0b0e94e`; the preceding fast-forward exited zero. Its final receipt remained `FAILED_PRESERVED` because 32 additional status entries appeared after checkout. All 265 changed working files and the whole index matched the target Git objects, and the six original dirty files were unchanged. The underlying DriveFS cache mechanism is not established.

The pinned plan derives exactly 32 paths (1,820,806 bytes) from that receipt's 38 status entries minus the six preserved dirty paths. Each selected raw SHA-256, size and Git blob is bound to the preceding actual post-fast-forward proof. This helper does not fetch, merge or change refs.

An explicit run acquires the original stable C workflow lock, admits at least 1.5 GiB Windows physical and commit headroom and 10 GiB free on C and G, and checks the exact HEAD, branch, whole index and 38-path status scope. It preserves the raw index and six dirty files in a new C evidence directory before the sole Git write: `git add -- <exact 32 paths>`. Before that write, each selected raw file must already equal its HEAD/index blob, and effective attributes must disable text conversion and leave filter, working-tree-encoding and ident unspecified.

Afterward the whole index's object IDs and modes must still equal HEAD, all 32 raw files and six dirty files must remain unchanged, staging must be empty, and both the genuine content diff and final status must contain exactly the original six. Any additional status path fails without expanding scope. The source reuses the pinned prior helper's suspended process, assign-before-resume JobObject, retained identity, finite command timeout, actual exit and empty-job checks. It records the original lock's explicit release.

The memory admission is initial only. Every Git command has a 180-second bound, retained C stdout/stderr and bounded owned-job cleanup. Failure preserves the working files and backups; there is no automatic rollback, reset, restore, clean, retry or new scope. Original dirty-file backup bytes are private recovery evidence and are not included by the public preparation allowlist.

Five focused pure control tests passed during preparation; the default command returned `PREPARED_NOT_RUN`. Neither check reads G, acquires the original lock or launches Git/WSL. Independent source review is separate from an actual repair receipt.

Root-only invocation after source publication/readback and after other owners release the original lock:

```powershell
& 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\repair_canonical_post_ff_stat32.py' --run --expected-source-sha256 db73f926c09ab2d9d5d8e6b81309a8776049e46401426c0e67eeaf09e38cb245
```

An actual result is successful only with `PASS_EXACT32_REINDEX_HEAD_AND_SIX_DIRTY_UNCHANGED`, every created Git scope closed, and the original lock explicitly released. Prepared source, prior proof or test success alone cannot establish those facts.
