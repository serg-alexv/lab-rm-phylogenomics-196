# Qualified backing-UNC transport proposal

The current read-only diagnosis establishes that Windows can reopen the Linux sentinel through the fixed ext4 backing UNC, while the canonical UNC below `/mnt/g` is denied. Use a separately reviewed Windows transport variant rooted at `\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1`; retain the canonical Linux scientific output path, source/method, ext4 bind and operational guards.

The scope is this exact diagnostic, not a completed replacement probe or native admission. The original UNC03 run remains FAILED. No WSL, UNC I/O, mount, lock or Git operation was performed by this source investigation.

## Primary WSL evidence

Official WSL tag `3.0.2` resolves to commit `0dc1bc1f545daa54976df7437d4432e9818cf86d`. Its Linux Plan9 server's `File::Walk` detects device transitions and rejects entry into `drvfs`, `9p` or `virtiofs` mounts with EACCES. Traversing `/mnt/g` can therefore fail before a deeper ext4 bind is reached. The upstream `TestMounts` test expects Windows UNC access to a DrvFS mount and its descendants to fail with access denied. [Plan9 implementation](https://github.com/microsoft/WSL/blob/0dc1bc1f545daa54976df7437d4432e9818cf86d/src/linux/plan9/p9file.cpp), [upstream mount test](https://github.com/microsoft/WSL/blob/0dc1bc1f545daa54976df7437d4432e9818cf86d/test/windows/Plan9Tests.cpp).

The server opens Linux `/` and exports that root. A direct ext4 backing path avoids traversal through the Windows-drive mount. Requests execute with the attached Linux user identity; changing the default UID does not remove the separate DrvFS traversal restriction. [Server initialization](https://github.com/microsoft/WSL/blob/0dc1bc1f545daa54976df7437d4432e9818cf86d/src/linux/init/plan9.cpp), [share identity](https://github.com/microsoft/WSL/blob/0dc1bc1f545daa54976df7437d4432e9818cf86d/src/linux/plan9/p9fs.cpp), [request user context](https://github.com/microsoft/WSL/blob/0dc1bc1f545daa54976df7437d4432e9818cf86d/src/linux/plan9/p9util.cpp).

WSL also places elevated and non-elevated Linux commands in separate Windows-drive mount namespaces. Thus a Linux command's mount observation cannot alone establish the UNC server's view. [Microsoft DrvFS architecture](https://github.com/microsoft/WSL/blob/0dc1bc1f545daa54976df7437d4432e9818cf86d/doc/docs/technical-documentation/drvfs.md).

The stronger claim that the Windows redirector reparses the canonical path directly into the Windows G underlay is **not established** here. Microsoft's architecture announcement identifies `p9rdr.sys` and `p9np.dll` as Windows-image components outside the open source release. No redirector trace was captured. Namespace differences also remain possible; they need not be repaired to qualify a direct ext4 transport. [Microsoft component boundary](https://blogs.windows.com/windowsdeveloper/2025/05/19/the-windows-subsystem-for-linux-is-now-open-source/).

## Actual diagnostic join

C-local receipts in `stage5_unc03_diagnostic_actual01` were reopened alongside UNC03 `request.json` and `prepared.json`. The original Linux prepared sentinel has 116 bytes, SHA256 `4a90f5d4c9fa4130234bfc121f1e1dd47cde726546840a3085d9e4b5875a0ff5`, inode `33554461`, Linux device `2096`, and directory inode `33554454`.

The diagnostic worker's unchanged original U `tiny_read` passed on backing `linux.bin`: exact bytes/hash/inode, nlink1, no Windows reparse point, stable metadata across its own open/read/reopen. The backing directory inode also matched. Windows exposes translated device0 and 100ns-rounded timestamps; equality of Windows and Linux device numbers or nanosecond timestamps is not a valid transport prerequisite. Canonical directory and both leaf paths returned Winerror5. Backing `windows.bin` returned Winerror2; this diagnosis performed no UNC writes or cleanup. Its owner receipt records retained worker exit0, empty named job, original lock released and no unknown-closure STOP.

Inference: these exact measurements agree with the upstream traversal restriction and support the direct backing bridge. They do not prove every internal redirector decision, establish bidirectional write/fsync behavior, adopt UNC03 as success, or qualify a native scientific run.

## Minimum change and qualification

Preserve original U and Windows-owner sources; create separate variants changing only Windows evidence transport to the fixed backing path. Leave Linux root/output paths, strict `stage5_work_storage.validate_storage`, runtime, runner, supervisor, panel and full native search unchanged. Validate the current frozen storage proof and reobserve canonical/backing equality of Linux ext4 UUID/device/inode/root/boot before and after operations. Reject path escapes, arbitrary UNC roots, aliases or source/control drift.

A fresh UNC04 probe must perform the existing bounded Linux prepare, retained Windows read/write/fsync/read, and Linux finalize/exact-cleanup phases, joining the exact storage proof and fresh random payloads. Keep original lock identity, owner/resource lease, finite deadlines, retained process identities, named-job/WSL/Linux descendant closure, positive exit receipts and durable STOP-on-unproven-closure behavior. Preserve UNC03's failed scope and files until separately authorized exact recovery/cleanup. A read-only diagnostic is not the qualification receipt.

After the probe and independent review pass and root publishes them, a separate C-only builder/request route may reference UNC04. Its native resource wait changes from the original builder's forced zero to explicitly finite 1800 seconds; all five resource budgets, reserves, two threads and fresh native admissions remain unchanged. Any memory feasibility report describing the old builder as already waiting was incorrect: only the new reviewed variant will provide that wait. Config creation itself still requires the builder's immediate Windows capacity gate; the Linux native owner may defer if fresh admission fails.
