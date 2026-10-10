# Contingent exact Chrome resource cleanup source preparation

State: source prepared and tested with pure/fake guards only. Actual process enumeration, handle acquisition, termination, resource reclamation, WSL operations, image processing, Git changes, and cleanup have not run through this candidate. The master owner decides whether the current measured resource gate requires this bounded cleanup.

The candidate is `stage5_chrome_resource_cleanup.py`, SHA256 `85c46761991c657ecc86f2dad8bcd5d75e40e29d37dc14d234cfed19806836bf`. Its only project dependency is original `atomic_iqtree_windows.py`, SHA256 `80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827`. Tests `test_stage5_chrome_resource_cleanup.py`, SHA256 `4bcb3cb825b54bd92bd43f7a5119a1727c9bc0c5697322201d53d52be4e54865`, pass eleven pure/fake checks, including default NOOP. Tests do not instantiate Windows APIs or affect actual processes.

## Effect boundary

The exact executable allowlist contains one entry: `C:\Program Files\Google\Chrome\Application\chrome.exe`, compared case-insensitively, in the cleanup owner's actual current SessionID. Each effect requires actual retained process-handle executable, PID, creation FILETIME, and session identity. A query handle remains owned until checked closure; a separate terminate-capable handle must prove the same birth before its query handle closes. No basename, PID-only, process-tree, command line, URL, browser profile, service, or unrelated application matching is used. Codex/ChatGPT, DriveFS, network, security, and other applications cannot match the allowlist.

The K32 process census has at most 4096 DWORD entries and rejects a full/truncated buffer. At most 128 matching handles may be retained for the snapshot. The owner has a 180-second deadline, at most five seconds per positive terminal wait, and a 256 MiB physical and commit reserve. Each actual TerminateProcess request uses only its retained verified Chrome handle and exit code 1223. Positive terminal evidence requires the same birth/session/executable, a signalled retained handle, an actual exit FILETIME later than creation, and the requested actual exit code. A target already closed before the effect is recorded as no effect. New or respawned Chrome processes are outside this snapshot and are not claimed closed.

A graceful HWND close is deliberately skipped: the candidate has no way to retain atomic HWND ownership through window reuse. The explicitly authorized fallback is exact retained-process-handle termination. This can discard unsaved Chrome session state; the human's current host-cleanup authorization is the effect authority. The candidate adds no interactive permission flow.

## Authority and closure

Actual opt-in requires source/API byte pins, a new direct C-work output namespace, and one to sixteen exact pairs of actual prior-owner result and explicit byte-unlock receipts. Each decoded evidence byte sequence is SHA-bound, then checked against a second path read. Prior results must retain their actual failed or passed state and prove owned closure and no STOP. They cannot convert an unsuccessful scientific step into success. The master owner supplies the complete current closure chain; the helper does not invent or search for missing proof.

The original single WorkflowLock is acquired and continuously checked against its exact immutable identity: volume serial 2430728143, file index 844424932784519, creation FILETIME 134359335921635133, and locked byte 0. Current project control must be `ACTIVE_DIRECT_USER_CONTINUATION` with `automatic_resume` false. An existing unproven-closure STOP vetoes the candidate.

Before enumeration, a C intent and the candidate's owned durable STOP are written. Before every process-state effect, its C intent and result checkpoint are durable. Successful effect receipt includes actual terminal identity and checked CloseHandle. Failed CloseHandle retains the owned handle entry; uncertain effects remain subject to bounded terminal finalization. The STOP remains until all effects and owned handles close and original WorkflowLock explicit unlock succeeds. Unlock uncertainty, unresolved handles, changed STOP, or failed finalization leaves failure evidence and a STOP. Final PASS requires the exact owned STOP to clear after explicit unlock.

## Invocation by the sole master owner

Default invocation is harmless and returns `NO_OP_CONTINGENT_EXACT_CHROME_ONLY_CLEANUP`:

```powershell
python.exe -B work/stage5_chrome_resource_cleanup.py
python.exe -B -m unittest discover -s work -p test_stage5_chrome_resource_cleanup.py -v
```

Actual invocation is intentionally not executed in this preparation. The master supplies real current receipt paths and hashes, repeats paired flags for every required closed owner, and uses a fresh direct child of the exact C-work directory:

```text
python.exe -B work/stage5_chrome_resource_cleanup.py --run
  --source-sha256 85c46761991c657ecc86f2dad8bcd5d75e40e29d37dc14d234cfed19806836bf
  --output <new absolute C-work/stage5_chrome_cleanup_NAME>
  --prior-result <absolute actual closed owner result.json>
  --prior-result-sha256 <actual SHA256>
  --prior-unlock <absolute actual lock_released.json>
  --prior-unlock-sha256 <actual SHA256>
```

Only actual final `PASS_EXACT_CHROME_SNAPSHOT_EFFECTS_AND_HANDLES_CLOSED`, explicit unlock receipt, absent STOP, and fresh host resource readings permit the master to consider the next scientific gate. This source preparation does not establish reclaimed RAM, scientific readiness, runtime adoption, VM splitting, remote recovery, or local eviction authority.

## Publication boundary

Publish the frozen source, pure tests, this method document, sanitized source peer receipt, and preparation report. No process payload, URL, profile contents, credentials, unrelated executable inventory, or raw private Copilot output belongs in this packet. Actual root-owned results are a later distinct completed step. Raw ext4/VHDX splitting and the cold three-role inventory/capture integration remain separate pending work.
