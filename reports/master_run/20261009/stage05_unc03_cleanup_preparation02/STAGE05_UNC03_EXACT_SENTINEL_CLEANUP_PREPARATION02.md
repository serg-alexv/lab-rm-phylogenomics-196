# Exact failed UNC03 sentinel cleanup preparation, revision 2

This is a separate default-NOOP cleanup of the retained failed probe tail.
It cannot convert UNC03 to PASS and emits no `windows_io.json`, Linux final
receipt, successful UNC gate or scientific acceptance. Original failed probe,
read-only diagnostic and independent closure evidence remain intact.

The only eligible namespace is
`\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1\.unc_visibility_8ae35884653047348cfa688d4bf00b36`.
The only eligible leaf is its known `linux.bin`: 116 bytes, Windows-projected
inode 33554461, nlink1, SHA
`4a90f5d4c9fa4130234bfc121f1e1dd47cde726546840a3085d9e4b5875a0ff5`.
The directory must retain projected inode33554454/nlink2 and all initial
recorded metadata. `windows.bin` must still return exact Windows missing-file
error2 and the bounded entry listing must contain only `linux.bin`. Any extra,
changed, linked, symlink/reparse, replaced or unreadable object blocks cleanup.

`stage5_unc03_exact_sentinel_cleanup_v2.py` SHA
`0984781820c8dd2b85a909b182902990e5c335c6e19187733dadbe3039ef77d4`
uses unchanged `atomic_iqtree_windows.py`80a202 and
`stage5_unc_bind_probe.py`0664a9. One original WorkflowLock owns one unchanged
`U.windows_job`, with the existing20-second root and finite Job drain/checked
retained handle closure. There is no WSL launch, mount, new controller or
process-tree termination. The original diagnostic's C-path, current authority,
resource reserve, failed-request, error and metadata helpers are copied with
identical function ASTs.

The helper pins exact prior failed03/diagnostic review and actual receipt bytes,
including original request7f28 and explicit original unlock. It uses the
original `U.tiny_read` and requires exact known payload/receipt. It writes a new
C `linux.bin.backup` with exclusive create, flush and fsync, then atomically
writes metadata and reads back both files before eligibility for either UNC
effect. The metadata preserves the source/request/control pins and projected
object observations; original Linux POSIX metadata is retained by the original
prepared receipt rather than inferred from Windows' projected modes.

Before the fixed leaf unlink, it durably records the effect intent/backup pins
and rechecks the directory, exact entry list, absent Windows leaf, unchanged
original tiny read and leaf metadata. After unlink it records returned effect,
proves both leaves absent, checks the same directory identity (allowing the
expected mtime change), and requires emptiness. Before the exact rmdir it
durably records intent and rechecks identity and emptiness. It then proves the
directory absent. These are fixed path operations within the single master
workflow; no claim is made of a new kernel atomic compare-and-delete primitive
against unrelated concurrent writers. Root must retain exclusive workflow
ownership and the known prior scope closure throughout the actual operation.

Changed objects or failures preserve the C backup and truthful progress/result
receipts. A failure after an effect requires explicit reconciliation; there is
no automatic retry, broad deletion or fake rollback. Unknown owned worker or
original unlock closure leaves a durable STOP. A successful owner result
requires actual worker exit0/empty Job, exact two-object cleanup, final source/
authority/control readback, then original unlock and closed lock stream before
the separate success receipt. No STOP is cleared by this helper.

`test_stage5_unc03_exact_sentinel_cleanup_v2.py` SHA
`c96601fc1334706ed73124bc00de9e62281306f057d71383c279e42912396b33`
passed19 pure/fake tests, including a tiny real C-only fsync/readback backup.
Tests cover ordered backup/effects, nonce/payload/identity/extra-entry rejection,
changed objects after intent, backup/intent failures, truthful partial cleanup,
permission errors, original guard ASTs/pins and default-NOOP/explicit-run gates.
The C fixture's two known files were removed nonrecursively. A separate default
NOOP passed. No actual UNC, WSL, lock, native process, image or deletion action
was performed during source preparation.

Root-only next: publish/read back the exact reviewed source packet; verify
fresh authority, absence of unresolved STOP and exclusive master ownership;
invoke one new `stage5_unc03_cleanup_...` C spool with explicit source SHA and
`--run`; independently verify exact backup/effect, retained Job/client closure
and original unlock receipts; publish the honest cleanup result. A fresh full
UNC04 two-way qualification remains an independent prerequisite for science.

Revision 1 remains frozen as rejected source evidence: its resources function
was defined after the CLI main guard. Imports and the default NOOP passed, but
actual --run would have reached resources before its definition. Revision 2
only moves the main guard to the final top-level statement; every function AST
and all cleanup behavior remain identical. Two new pure regressions check
actual CLI definition order and the exact move-only source delta. No actual
revision 1 cleanup ran.

The root publisher must explicitly map the actual116-byte linux.bin.backup
into a public recoverable binary file regardless of extension filtering, and
include backup_metadata.json. Its payload is the public sentinel already
preserved as hex in the pinned original request. The actual backup SHA must be
verified after upload; this source preparation performs no publication.
