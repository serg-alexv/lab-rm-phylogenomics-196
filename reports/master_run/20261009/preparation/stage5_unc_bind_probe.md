# Exact UNC to ext4 bind visibility probe — prepared, NOT_RUN

This proves only the endpoint used by `stage5_windows_owner.py` to read native receipts:

`\\wsl.localhost\Ubuntu\mnt\g\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage05_atomic_v1`

The existing C lifecycle and ordinary G DriveFS probes do not establish this covered ext4 endpoint. The new probe is a single-purpose three-step sentinel check. No detector, model, genome, mount, unmount, shutdown, installation or recursive cleanup runs.

Actual execution must wait for root's proven IQ-TREE/controller/JobObject closure and release of the original stable workflow lock. Root must reconcile any previous owned-closure stop, start the intended Ubuntu instance, establish and prove the retained toolchain/storage mounts, and complete the existing lifecycle smoke first. This source preparation has done none of those operations.

The root-owned Windows process acquires the exact original `WorkflowLock` itself and retains it through all three steps, actual child exits, final readback, and C receipt creation:

1. A harmless Linux process validates the pinned storage proof against current boot, full mount identity, ext4 UUID and target/backing device/inode. It exclusively creates `.unc_visibility_<random32hex>` beneath the exact bind target and writes/fsyncs one random tiny Linux payload. It also fsyncs the owned directory and target directory. Current storage identity is checked again. A C prepared receipt records exact file and directory identities.
2. A single Windows Python I/O worker is created suspended, assigned to a new JobObject with kill-on-close and active-process limit one, then resumed. It reads the exact Linux payload through the fixed UNC alias, exclusively creates a different tiny Windows payload there, flushes/fsyncs it and independently reads/hashes it. The owner allows20 seconds plus5 seconds for owned closure. Only this newly owned Windows worker/job can be terminated. Its process birth, actual exit and empty JobObject are recorded.
3. A second harmless Linux process revalidates the same proof and original sentinel directory identity. It reads both exact payloads and requires their device to match the ext4 bind. It permits exactly the two owned filenames. After another storage check it verifies each exact file identity/hash again, unlinks only those two leaves, removes only their now-empty owned directory, fsyncs its parent and checks storage again. Linux children are forbidden. Root verifies actual retained WSL client exit0, C source/proof receipts, Linux-proven exact cleanup and unchanged Windows G underlay. No extra UNC absence query runs in the owner; every actual Windows UNC operation stays in the bounded worker.

The Windows G underlay must already exist and be empty before this first-genome probe. The source reads its identity and tests only the first directory entry before and after, without following or enumerating unknown contents, and never writes there. Unknown underlay or sentinel contents fail and are preserved. Payloads are at most512 bytes, distinct in both directions, and are never scientific inputs.

Each Linux step uses a30-second alarm and a40-second retained Windows client wait. Linux filesystem calls may outlast a Python alarm. A timed-out still-live WSL client is not killed or treated as closed: the source records exact evidence in the protected C `stage05_owned_closure_unproven.json` stop, which the Stage5 owner refuses. An unproven Windows worker closure uses the same stop. Root must manually reconcile any such stop before any further native work. Ordinary source/config/authority/G-underlay checks in the owner are synchronous reads and do not claim a hard kernel I/O cancellation bound.

Prepared command only, after all actual operational prerequisites:

```powershell
$ProbePython = 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$ProbeWork = 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'
$ProbeConfig = "$ProbeWork\stage5_actual_01.json"
$ProbeConfigSha = (Get-FileHash -LiteralPath $ProbeConfig -Algorithm SHA256).Hash.ToLowerInvariant()
# Require the independently reviewed probe SHA; never infer approval from current bytes.
$ReviewedProbeSha = '<published reviewed stage5_unc_bind_probe.py SHA256>'
& $ProbePython -B "$ProbeWork\stage5_unc_bind_probe.py"
& $ProbePython -B "$ProbeWork\stage5_unc_bind_probe.py" --run `
  --config $ProbeConfig --config-sha256 $ProbeConfigSha --script-sha256 $ReviewedProbeSha `
  --output "$ProbeWork\stage5_unc_bind_actual_01"
```

The configuration needs the exact canonical Linux root/output root, retained `runtime.environment_dir`, and filled `work_storage.proof_path/proof_sha256`. It may reuse the V2 config; this probe does not call genome-policy validation or invent a native detector budget. The proof must be directly beneath current C work and originate from `stage5_work_storage.py` after root establishes the actual mount. No old-boot proof is reusable.

Success is only `PASS_NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY` with three actual closed step records, exact request/source/config/proof hashes, final Linux cleanup receipt, unchanged G underlay and explicit original byte unlock. Preserve all C request/phase/log/result/unlock receipts. This does not certify cloud upload, native detector availability, biological acceptance, cross-kernel lock interoperability or crash/power-loss durability. It tests immediate Windows/Linux visibility, file/directory fsync support and this actual ext4/UNC mapping.

The exact-owned leaf cleanup is deliberately limited and nonrecursive. A short identity-check-to-unlink interval remains; there is no atomic handle-deletion claim. The random new namespace is protected by root's single writer lock. Unexpected drift or unknown files fail; there is no generalized cleanup of old data.
