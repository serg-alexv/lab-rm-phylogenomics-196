# G-drive helper with explicit WSL session-parent provenance

The failed prior diagnosis is preserved. Its PID1 namespace-equality rule fired
before G topology inspection, so that attempt establishes no G visibility.
`stage5_gdrive_view_session.py` is a separately named revision; the published
postboot source remains byte-identical at SHA256
`a0b903970844e33d1e938a9d388b62981333e54991d4b5e86f8129651e3b4f06`.

Microsoft documents that, with systemd, WSL's init process becomes a child of
systemd rather than PID1. That documented distinction explains why PID1 is not
a sufficient identity for the WSL launch session. See [Microsoft Learn's WSL
systemd documentation](https://learn.microsoft.com/en-us/windows/wsl/systemd)
and [Microsoft's WSL technical systemd
documentation](https://github.com/microsoft/WSL/blob/master/doc/docs/technical-documentation/systemd.md).
These sources do not prove this host's current mount propagation or future
visibility; the following checks are an explicit local policy.

The Linux helper now records its current process birth and direct parent's
process record, exact `/init` executable and mount namespace. Admission requires
the current PPID to equal that parent's PID, positive process start ticks, a
live parent and equal current/parent mount namespaces. PID1's namespace is
retained as diagnostic evidence. Immediately before an optional mount and at
final readback, the helper rechecks the same parent PID, birth, executable and
namespace, plus its own PID/birth/PPID. Unknown identity or any drift is fatal.

All exact-G mount, unknown/empty underlay, nested/stacked mount, control-byte,
source/resource/nonce, fresh toolchain05 and retained closure guards remain.
The original storage02 history is preserved. This helper qualifies its actual
WSL session only; separate fresh storage and UNC gates remain mandatory before
scientific execution. A later WSL invocation must independently prove the same
storage identity. No general future-visibility claim is made.

Default invocation remains a no-op, including `--mount` without `--run`.
After independent source review and publication, diagnose first:

```powershell
& 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B `
  'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_gdrive_view_session.py' `
  --fresh-toolchain-proof 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_setup_toolchain_actual_postiq_05\toolchain_proof.json' `
  --fresh-toolchain-proof-sha256 106e1bc310f11d34d78f0d7bdc2b311a2b457e5c68c0e32aad3f8fc0a718446c --run
```

Only a qualified actual missing-G result permits a separate explicit `--mount`
run. The existing Stage5 ext4 bind must still be absent before this helper.

Three focused pure contracts passed using fake process/namespace records:
different PID1 is diagnostic and default remains no-op; wrong/unknown `/init`
parent or mismatched namespace rejects; parent/current birth, parent PID or
namespace drift at final readback rejects. No WSL or actual mount ran during
source preparation.
