# DriveFS primitive preflight — prepared, NOT_RUN

`stage5_drivefs_filesystem_smoke.py` is a 93-line filesystem probe. Preparation writes only this chat's C `work/` source. It has not booted WSL, touched G, launched a child, or certified scientific work. `--help` and the default plan work without Linux; `--run` fails before filesystem access on Windows.

Run only after the sole native tree process, owned JobObject and workflow byte lock have closed. The existing Windows root must hold the original stable C `WorkflowLock` throughout launch, actual retained WSL client exit, and Windows G readback. Do not reuse a receipt from a prior released lock: save a new C work receipt containing the actual current Windows owner birth, stable lock identity and scope, then pass its exact SHA256. Linux binds those receipt bytes; it does not independently prove the Windows lock.

The script requires the canonical existing `/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/.work`, checks the resolved mount record, and creates one new namespace:

`.work/stage05_atomic_filesystem_smoke_<UTC timestamp with microseconds>_<nonce8>`

It preserves four tiny payload files plus `result.json`; it never deletes a fixture. The operations are:

1. Exclusive ordinary file creation, write, flush, file `fsync`, and exact readback.
2. A flushed/fsynced `.partial` file replaces an existing target using `Path.replace`; the old bytes disappear and the exact new bytes reopen.
3. The actual reviewed `stage5_atomic_process.atomic_json` writes and replaces its `.partial`, followed by JSON readback. Its module bytes must match the explicit reviewed hash. No `Supervisor` is instantiated.
4. The Stage5 runner's exact `open('a+b')` plus `fcntl.flock(LOCK_EX | LOCK_NB)` primitive acquires an isolated `.native_runner.guard`. An independently opened handle must be excluded. Closing the first handle releases it; a fresh handle must then acquire and release it by close. No process or controller is spawned.

Example arguments within the already-held Windows root lock:

```text
C:\Windows\System32\wsl.exe -d Ubuntu -u root --exec <actual mounted retained Linux Python> -B
  /mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_drivefs_filesystem_smoke.py
  --owner-lock-receipt <new actual held-lock receipt under this C work bridge>
  --owner-lock-sha256 <exact fresh receipt SHA256>
  --supervisor-sha256 <reviewed current stage5_atomic_process.py SHA256>
  --run
```

The caller captures stdout/stderr on C and verifies actual retained WSL client exit0. The script uses a 30-second Linux alarm; root should use a bounded client wait, retain the writer lock while reconciling any still-live client, and stop on failure. A blocked filesystem system call may outlast a Python alarm, so the alarm alone is not a proven hard termination deadline. There are no Linux child processes to adopt or kill.

Windows readback must establish the actual G mapping, not merely trust Linux PASS:

- Require stdout schema `STAGE05_DRIVEFS_FILESYSTEM_SMOKE_V1`, scope `NONSCIENTIFIC_DRIVEFS_FILESYSTEM_ONLY`, state `PASS_NONSCIENTIFIC_FILESYSTEM_ONLY`, `scientific_adoption_authorized=false`, and the current script/supervisor/caller-lock receipt SHA256 pins.
- Accept only `namespace_relative` matching `^\.work/stage05_atomic_filesystem_smoke_[0-9]{8}T[0-9]{12}Z_[a-f0-9]{8}$`; reopen that exact namespace beneath `G:\My Drive\LAB_RM\lab-rm-phylogenomics-196`.
- Hash its `result.json` in Windows and require equality to stdout `result_sha256`. This external hash avoids a self-hash cycle. Reopen the JSON and require the same scope, nonce, namespace and source pins, plus all five primitive flags `true`.
- Require exactly these `files` keys: `ordinary.bin`, `replaced.bin`, `runner_atomic.json`, `.native_runner.guard`. For each, Windows file length and SHA256 must match the corresponding `bytes` and `sha256` fields. Restrict names to this literal set before joining paths.
- Require `ordinary.bin` and `replaced.bin` bytes both equal ASCII `NONSCIENTIFIC DRIVEFS SMOKE\n<nonce>\n`; reopen `runner_atomic.json` and require that same nonce and scope. No `.partial` should remain.
- Preserve the C client/lock/readback receipts and tiny G fixtures. Release the stable C lock only after actual client closure and readback are recorded.

Limitations: this tests immediate Windows/Linux visibility and same-kernel Linux `flock` semantics on the actual mounted G path. It does not prove cloud upload completion, crash/power-loss durability, directory `fsync`, cross-kernel or Windows/Linux lock interoperability, native detector availability, or scientific readiness. The runner's JSON primitive does not itself call `fsync`; the separate ordinary/replace tests do. Unsupported `flock`, file `fsync`, atomic overwrite, hashing or readback is a failure, never an omitted pass. Scientific adoption remains false even after a successful probe.
