# Inactive installed-runtime extraction preparation

This is a source and contract preparation. No installed-runtime inventory,
capture, remote recovery, Linux restore, native command, or original-prefix
runtime check was performed by this packet. Default invocation prints a pending
state and performs no extraction or download.

`stage5_runtime_safe_extract.extract()` has no standalone execution CLI. It
requires a separate reviewed Linux root owner, live resource admission callback,
finite lease and owned-process closure, and externally pinned actual fresh remote
and independent full-payload receipts. The remote downloader and its reviewed
receipt producer are not implemented here. `remote_plan()` and `remote_gate()`
describe the interface; they do not establish remote recovery. Synthetic gate
receipts use a distinct status and cannot authorize production extraction.

## Source and input binding

The immutable helper pins are the already reviewed pure contract `daf48ea1...`,
independent logical payload reader `9770354d...`, independent cold-tree checker
`cd64e0d4...`, and capture producer `21b33abc...`. The producer is never imported.
Actual archive index, public review, notices, full inventory, runtime subset,
exclusive-capture receipt, source commit, Release tag, asset identities, and
remote-verifier source must be supplied with explicit hashes. None exists as an
accepted actual installed-runtime recovery input in this packet.

The gate requires selected current asset IDs, names, sizes and SHA256 digests to
match before and after actual fresh downloads, exact original LF sidecars, actual
Git control-byte checks, complete local payload verification, and owned download
client closure. It accepts an actual remote receipt no more than 15 minutes old.
Receipt fields are a contract for a future independently reviewed wrapper; callers
must not mint a receipt from these predicates alone.

Verified control bytes are SHA256 checked and identity checked before parsing.
The manifest and four JSON decisions consume those exact captured byte snapshots.
Control snapshots are at most 64 MiB each; one manifest snapshot is indexed in
SQLite and released. JSON parsing and tar PAX parsing are not a fixed RSS proof.
The future owner must enforce an actual memory budget and resource reserve, in
addition to the per-block callback and 1,800-second internal deadline.

## Scoped writes and links

Only a new direct `/var/tmp/lab_rm_runtime_restore_<unique>` tree and new current
C-work evidence namespace can be created. The staging filesystem must be actual
ext4, have no nested mount of any device, and differ from every original source
device. Existing staging paths, source paths, unexpected members, duplicates,
conflicting parents, special files, sparse files, unsupported PAX keys, absolute
member paths, traversal, backslashes, colon/drive/ADS paths, and noncanonical
Unicode paths are rejected. A failed partial tree is preserved, never adopted.

Linux x86_64 `openat2` uses `RESOLVE_NO_XDEV | RESOLVE_NO_MAGICLINKS |
RESOLVE_NO_SYMLINKS | RESOLVE_BENEATH`, plus no-follow and close-on-exec. All opens
for restored payload paths are relative to retained new-tree descriptors. There
is no fallback if the kernel ABI or policy is unsupported. Hardlinks use
`linkat(..., AT_EMPTY_PATH)` from the exact retained prior regular-file descriptor;
the required capability or filesystem failure stops restoration. No
`tarfile.extract` or `extractall` call is used.

Files, empty directories, internal hardlink groups, exact reviewed symlink text,
ownership, modes, nanosecond mtime and xattrs are preserved. Metadata is applied
after creating children and aliases. Unexpected inherited xattrs fail closed;
the extractor does not silently remove or omit them. Linux symlink modes other
than 0777 are rejected before tree creation. Original dev/inode/ctime are source
provenance, not metadata that can be recreated.

Absolute symlink text is permitted only when the captured logical graph resolves
inside the three exact original runtime roots. That text is preserved and never
followed by this extractor. Relative links across original root basenames may
also be unresolved in the temporary role layout. The temporary tree therefore
does not establish a self-contained executable prefix, original-prefix runtime
equivalence, OS/ABI closure, installed build equivalence, or host-wipe authority.
There is no automatic link rewriting or copying of linked external bytes.

## Required later gates

The only successful extractor state is
`NEW_LOGICAL_TREE_EXTRACTED_PENDING_INDEPENDENT_COLD_CHECK`. It is not acceptance.
A separately invoked independent cold checker must rehash and compare the full
new tree, metadata, internal aliases, source-device exclusion and mount topology.
Original-prefix runtime tests and any recovery or eviction decision remain
separate. No actual Linux syscall, ext4 restore, xattr, hardlink or cold-prefix
fixture has run for this preparation. A bounded Linux fixture under a reviewed
owner is required before use with actual recovered payloads.

Fourteen actual Windows C-only tests exercise metadata contracts and small
synthetic files. Linux ABI calls and metadata are explicitly mocked; no `/proc`,
mount, runtime payload, shard, network or native command is accessed. They cover
unsafe paths, duplicate JSON, receipt/asset/source/age failures, synthetic receipt
rejection, inode-alias graph and empty-directory accounting, exact captured
control use after source-reopen change, reviewed absolute symlink text, mode
rejection, tar header/type/link/sparse mismatch, nested mount rejection, and ABI
serialization. They do not prove actual kernel behavior.

## ABI and library references

Only constants and ABI field names are used; no vendor implementation was copied.
The project retains its existing license. Frozen helper attribution is preserved
in the linked source packet.

- [Linux openat2 manual](https://man7.org/linux/man-pages/man2/openat2.2.html)
- [Linux 6.18 openat2 UAPI, GPL-2.0 WITH Linux-syscall-note](https://raw.githubusercontent.com/torvalds/linux/v6.18/include/uapi/linux/openat2.h)
- [Linux 6.18 x86-64 syscall table](https://raw.githubusercontent.com/torvalds/linux/v6.18/arch/x86/entry/syscalls/syscall_64.tbl)
- [Linux linkat manual](https://man7.org/linux/man-pages/man2/link.2.html)
- [Python 3.11 tarfile streaming API](https://docs.python.org/3.11/library/tarfile.html)
