# Controlled Windows WSL memory profile repair

Runtime07 remains an actual failed scope. Its Windows resource observation fell
below the setup reserve; the retained WSL client exited2, the Linux terminal
reports no remaining direct children, the native child exited-15 with empty
group/descendants, and the original byte lock was explicitly released. The
Windows maintenance owner pins those existing bytes and calls unchanged
`stage5_setup_windows.command_readback` for their exact native-command joins.
It requires the prior Windows owner and WSL client identities to be exited or
absent, then obtains a fresh competing-owner/task census under the original lock.

`stage5_wsl_host_profile_owner.py` is a separate Windows-only adaptation of the
reviewed WSL config owner4a6b. It imports that exact source and its frozen G42db
framework; it reuses their census, exact Ubuntu registration, no-running-distro
decoder and fixed shutdown/list commands. Its retained-client launch, timeout,
terminal and handle-close functions are AST-identical to4a6b apart from the
launch-intent reason text. There is no Linux worker, default-user operation,
sentinel cleanup or automatic relaunch. No scientific stage is executed.

Only these two exact lines in `C:\Users\wheel\.wslconfig` change:

```ini
[wsl2]
memory=3GB
[experimental]
autoMemoryReclaim=dropCache
```

The exact679B preimage SHA256 is
`31b59c84adf6bf7b0fdf0cd42ee6298cd9dc7c20032ab30d97c3f22dbb3b6982`.
Both section-specific replacements retain every other byte, including mixed
newline style and comments. The unchanged comment about gradually releasing
cache is historical descriptive text; the executable setting is dropCache.
Memory is an upper bound, and the current Microsoft settings documentation
describes dropCache under [experimental WSL settings](https://learn.microsoft.com/en-us/windows/wsl/wsl-config#experimental-settings).
This profile change does not substitute for later Linux/Windows admission.

Under the existing exclusive WorkflowLock, the owner requires current direct
continuation controls, unchanged empty G underlay, exact Ubuntu UID0/version2/
UUID/BasePath/Flags15, no competing scientific/WSL/resume owner, and18 unique
disabled legacy LAB_RM tasks. The small maintenance reserve is1.5GiB physical
and commit headroom, with10GiB free on each used volume; the native scientific
budgets remain unchanged. It pins the failure/source evidence throughout.

The owner durably saves and rechecks the exact public preimage and expected
bytes in a fresh C spool. The actual host profile and ancestry must be plain,
single-link and non-reparse. It opens an exclusive nonce staging file beside
the profile, writes/fsyncs the681B result, preserves the writable mode, rechecks
the original full identity/bytes and authority, publishes replacement intent,
atomically replaces the profile and records exact readback/identity plus backup.
Failures preserve effects and any owned staging file for recovery.

It then runs only retained `wsl.exe --shutdown` (60s) and
`wsl.exe --list --running --quiet` (20s), with census clients25s and a180s whole
owner deadline. Each client has explicit retained birth/terminal/exit0 evidence.
Its existing owned STOP intent is cleared only on proved retained closure;
unknown closure preserves it. No arbitrary process termination occurs. The
original byte lock is explicitly released, and final logs are hashed only when
closed. A final census, exact profile and backups, source/failure pins and Ubuntu
registration must all recheck before PASS.

Default invocation is NOOP. Seven source/pure C-only tests and a separate
default NOOP exercise exact two-line bytes, wrong sections, failed-scope tamper,
framework/no-Linux boundaries and retained-client AST equivalence. Source
preparation changes no actual host profile, process, WSL state, lock or Git ref.
Root must independently review/publish before explicit `--run`.

After actual shutdown, every boot-sensitive gate needs new actual evidence:
toolchain07/runtime08/interop05/G/storage06/drivefs04/UNC03. Earlier closed
failures remain failed; accepted Stage4 remains preserved. The fresh first
genome request must retain all five native budgets with its WSL basis updated
to3GB. The host is not yet ready for wiping.
