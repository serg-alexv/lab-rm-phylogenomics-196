# Exact 837 recovered history leaves: preparation only

The proposed cleanup removes exactly 837 old C scientific-history files, totaling
983,926,424 logical bytes, after their original bytes were independently downloaded
and verified from the three public history02 Release ZIPs. It retains the excluded
1,025-byte MacSyFinder source fragment whose package notices were unavailable.
This is recovery-based cold storage cleanup, with no biological acceptance claim.

Actual history02 remote readback is pinned to receipt SHA
`d83aaff2695920d475742ace6c710255a326642222a5db771b95ec2d809b0ecb`;
the independent successful batch03 post-check is pinned to
`84cb29ebcc04b444ea90ca0e10d5f7e6832d09f14f8f8285f1241b4cf3e71868`.
All 837 current file identities matched the recorded original metadata during
preparation. Frozen metadata also proved disjointness from the previous 47,429
cleanup targets. Current per-file content hashes are checked by the executor,
and are not claimed as an additional full hash pass by this preparation.

Before `-Run`, root must publish the proposal, source, and both actual receipts.
The exact canonical paths are:

- `reports/master_run/20261009/cleanup/history02_purge01/proposed.json`
- `reports/master_run/20261009/cleanup/history02/REMOTE_READBACK.json`
- `reports/master_run/20261009/cleanup/batch03_purge01/INDEPENDENT_POSTVERIFY.json`

The executor checks the current remote main commit, actual published proposal and
receipt bytes, all 16 immutable recovery source controls, and current identities
and digests of all six Release assets. It reopens the three freshly downloaded
ZIPs and the original member/identity mapping. It then requires exact retained
Windows handles for native PID 4768/birth 134360369876207076 and controller PID
27048/birth 134360369803845506. Any native/controller closure stops cleanup.

For each admitted file, retained directory handles prohibit parent rename/delete;
an exclusive leaf handle verifies final path, 64-bit volume/file ID, nanosecond
mtime, size, link count, and full SHA. The append journal records a flushed intent
and each actual literal removal. There is no recursion. The exclusive leaf handle
must close before `Remove-Item`; the resulting short leaf replacement interval
remains explicit, as in the previously reviewed cleanup. This is not an atomic
delete claim. Logical removed bytes are not a measurement of physical disk reclaim.

The excluded fragment and the exact 12 protected source/input/G hashes are checked
before cleanup and again before a successful terminal receipt. The original stable
workflow lock is never opened or changed. Only a new C-work journal is written.
The cooperative operational deadline is 900 seconds; checks occur between bounded
read/operation boundaries. GitHub read subprocesses have a 60-second timeout.

Preparation verification: five pure non-destructive contracts passed; PowerShell
source parsing passed. The native API primitives retain the previously reviewed
FILE_ID_INFO implementation; no native API fixture, target preflight, deletion,
WSL start, biological job, upload, or G write ran during this preparation.

Root's strict command after final independent source review and publication:

```powershell
& 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoProfile -NonInteractive -File 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\Invoke-MasterHistory02LeafPurge.ps1' -Plan 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\master_history02_leaf_purge_proposed.json' -PlanSha256 '6377f16835472951ccbe1bee5e15a25fb2d675d2a7edf24d656d34f008770b22' -RemoteCommit '<ROOT_PUBLISHED_PROPOSAL_COMMIT>' -RecoveryReceipt 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\public_history02_readback_20261009T195508Z_1f99201e\receipt.json' -RecoveryReceiptSha256 'd83aaff2695920d475742ace6c710255a326642222a5db771b95ec2d809b0ecb' -Receipt 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\master_history02_leaf_purge_20261009_receipt.jsonl' -Run
```

The placeholder commit must be replaced with the actual published proposal commit.
Omitting `-Run` checks authority/recovery and protected inputs only; it does not
claim an actual full content preflight for all candidate leaves.
