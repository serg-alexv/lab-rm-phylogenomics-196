# Single-use master continuation after a controlled Windows restart

Prepared only. No RunOnce entry, reboot, resumed session, WSL, STOP change or
scientific job has been performed by this helper. The old DriveFS02 STOP remains
SHA256 `3de7057780d280d5f204b535207a174e616ca425b5638fe9848a48cfca20838a`.
Root selected a normal Windows restart after the bounded census could not prove
the old Windows worker scope closed. The corrected benign worker fixture proves
only its own new retained root exit0 and empty named JobObject.

The installed `codex-cli 0.162.0-alpha.2` help supports explicit-ID
`exec resume [SESSION_ID] [PROMPT]`, stdin prompt, output-last-message and config
overrides. The candidate supplies `approval_policy="never"` and
`sandbox_mode="danger-full-access"`, matching current human-authorized execution,
and leaves the model setting unchanged. It never uses `--last`. Availability of
the exact stored session/authentication after reboot is not tested by CLI help.

The current-user RunOnce key opened writable without modification and had zero
values. `SeShutdownPrivilege` is present but disabled; no privilege was enabled.
Only CODEX_THREAD_ID presence was exposed during the feasibility audit. Root
separately authorized copying its exact value into a **private local** manifest.
No session stores, credentials, private event logs or other environment values
are inspected. The entire directory `work/private_master_boot_resume01/`, its
manifest, raw CLI stdout/stderr and last-message output must never be published
or included in cleanup/history archives.

Root's future sequence, after source/peer publication and exact remote readback:

1. **COMPLETED: do not repeat private preparation.** The retained C primary Python
   already ran `work/resume_master_after_boot_once.py --prepare-private` once,
   exit0. Its exact current session UUID, source/executable hashes, unchanged STOP
   and LastBootUpTime/GetTickCount64 bracket are saved privately. Public baseline
   projection `master_boot_resume_preboot_baseline.json` contains only the four
   safe boot-observation fields and must be remotely verified before restart.
   Preserve the existing private handoff across the restart; it is not a public
   payload. Preparation did not register or resume anything.
2. Register one explicit current-user RunOnce string named
   `LAB_RM_MasterBootResume_20261010` only if the name is absent. Do not change or
   replace any existing startup value. The exact candidate command is193 characters:

   ```text
   powershell.exe -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\Resume-MasterAfterBootOnce.ps1" -Run
   ```

3. Root performs a controlled normal Windows restart; the user must sign in as
   the same current user. This has no credential/autologon workaround. A plain
   RunOnce value is consumed before execution; no `!` retry prefix, Run key,
   recurring task, automation or auto-rearming is used. Microsoft documents the
   logon behavior and260-character limit in [Run and RunOnce Registry Keys](https://learn.microsoft.com/en-us/windows/win32/setupapi/run-and-runonce-registry-keys).
4. The launcher requires the exact C path and calls the fixed retained Python.
   The Python helper verifies source, executable, private-control ancestry and
   original STOP bytes, then requires LastBootUpTime to advance **and** uptime to
   reset. It accepts only the first2h of that new boot. A logoff/login in the same
   boot, Fast Startup/hibernation without a real kernel transition, stale marker
   or changed STOP fails closed before the single-use claim. Source-controlled
   preparation is insufficient evidence of a future reboot.
5. A durable exclusive `CONSUMED_SINGLE_USE.json` is created before network/CLI.
   It remains on failures; no automatic second attempt can occur. The helper
   reads public GitHub main and verifies it is identical to or descends from
   published anchor `e4f0fd84932f9a414abfb7b1439ee21b97a1a571`. It downloads immutable
   AGENTS/WORK_ORDER/STATUS/stages/master-status controls and both exact published
   launcher sources, then rechecks unchanged main. No G checkout/refs are altered.
6. Only after those gates does it launch the exact Codex executable once, with
   the private UUID in argv, a source-controlled public resume prompt via stdin,
   and exclusively created private output files. Actual new CLI birth/image are
   recorded from its retained Popen process handle. The helper performs no PID
   fallback, signals, old-scope adoption, STOP clear, WSL startup or native work.
7. The resumed master must first reconcile the old STOP using independently
   reviewed actual new-boot evidence and the original WorkflowLock. It must read
   latest remote main again and refresh boot-sensitive runtime/mount/storage/
   interop/resource proofs before any native search. Existing scientific source
   acceptance, serial owner guards and final tree/curation gates remain unchanged.

The helper controls one launch only; it is not another project execution
controller. Boot-query wait is15s, authority socket waits are at most20s and the
authority-copy budget is180s with a2MiB per-object cap. Synchronous filesystem,
process-creation and pipe syscalls do not have a hard cancellation guarantee.
After handing the small prompt to Codex, it records launch-only state and leaves
the ordinary Codex/project lifecycle in charge. It does not impose a short
timeout that could kill the resumed master while a real owner holds the project
lock. Its launch receipt proves neither CLI terminal/descendant closure nor any
scientific state. Authentication/session startup failure remains private,
consumed and requires explicit manual diagnosis/rearming; it never triggers a
fallback second session automatically. The bounded fallback is manual opening
of this same master conversation after sign-in, preserving STOP and all guards.

GitHub Copilot CLI is installed at the exact local GitHubCopilotCLI path and its
help reports version1.0.80. Earlier actual cleanup-policy advisory output is
`copilot_master_cleanup_review.txt`; its published document was independently
read back as `docs/master_run/COPILOT_CLEANUP_REVIEW.md`, SHA256
`55f494874e5c803549ce19bff6e4c21897255efd35f72688e47d23e9362cd4f1`.
The separate Stage5 source-split tools-disabled90s request timed out and provided
no acceptance. Neither is eSIM tooling. No redundant Copilot request or private
session export was made for this candidate.
