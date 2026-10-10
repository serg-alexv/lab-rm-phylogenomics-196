# Fresh Stage 5 gate commands from verified GitHub main

Authority read at immutable main `ac0e1f70010ed1af6b9f6d6dd5ef06bac108b610`.
All 17 continuation sources checked in `postboot_authority_review01.json` are
exact Git blob matches in that commit. These commands were derived by reading
those sources; this document does not claim they have executed.

Run only after the root independently reconciles the old STOP from a verified
new Windows boot and current quiescence under the original byte0 lock. Preserve
the original DriveFS02 failure as historical evidence. Use a new unique spool
for every actual invocation and preserve every failed attempt.

Set the execution variables in PowerShell:

```powershell
$stage5Python = 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$stage5Work = 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'
$stage5Controller = Join-Path $stage5Work 'iqtree_controller_closure_actual01\receipt.json'
$stage5ControllerSha = '7b6a6f78f2abfa833bc17f2767df1ae4e44ccc35de9ae35323461c5337481603'
$stage5ObserverSha = '483b5165d015dcea659d5e850187c79ff5e99c4c0efff1c9fb108cc9a59ab78a'
$stage5LinuxSetupSha = '24aab72b74dd0aab6c58cac4951c30e6b1bfc9462460486748b546e50ec92e27'
$stage5SupervisorSha = 'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e'
$stage5ApiSha = '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
$stage5UncSha = '0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d'
```

The setup command skeleton is an argument array, not a shell command string:

```powershell
$stage5SetupArgs = @('-B', (Join-Path $stage5Work 'stage5_setup_windows.py'),
  '--step', 'toolchain', '--output', '<NEW_ABSOLUTE_DIRECT_WORK_SPOOL>',
  '--controller-receipt', $stage5Controller,
  '--controller-receipt-sha256', $stage5ControllerSha,
  '--controller-observer-sha256', $stage5ObserverSha,
  '--linux-source-sha256', $stage5LinuxSetupSha, '--run')
& $stage5Python @stage5SetupArgs
```

For runtime, storage and drivefs change the step and unique spool, and add
`--toolchain-proof <ACTUAL_FRESH_TOOLCHAIN_PROOF_JSON>` with its exact
`--toolchain-proof-sha256`. Runtime and storage additionally require
`--candidate-output <NEW_ABSOLUTE_DIRECT_WORK_CANDIDATE_JSON>`.
The toolchain proof is `toolchain_proof.json` at the root of the actual setup
spool, not beneath `commands`.

Interop command after the fresh toolchain gate:

```powershell
& $stage5Python -B (Join-Path $stage5Work 'stage5_interop_smoke_windows.py') `
  --linux-python '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/detector_env/bin/python' `
  --distribution Ubuntu --output '<NEW_ABSOLUTE_WORK_SPOOL>' `
  --supervisor-sha256 $stage5SupervisorSha --windows-api-sha256 $stage5ApiSha --run
```

Before the storage step inspect the actual G mount and preserve its Windows
empty underlay. The separate `stage5_gdrive_view.py --mount --run` owner is only
appropriate if its strict actual-topology preconditions are met; it rejects an
existing/nested mount and must not be blindly repeated.

Build an explicit, non-scientific UNC config from the unchanged V2 template by
filling the fresh runtime manifest and storage proof path/SHA fields. The five
scientific capacity budgets may remain null for this sentinel-only gate.

```powershell
& $stage5Python -B (Join-Path $stage5Work 'stage5_unc_bind_probe.py') `
  --config '<NEW_ABSOLUTE_DIRECT_WORK_UNC_CONFIG_JSON>' `
  --config-sha256 '<ACTUAL_CONFIG_SHA256>' --script-sha256 $stage5UncSha `
  --output '<NEW_ABSOLUTE_DIRECT_WORK_SPOOL>' --run
```

The actual first-genome config builder requires all six gate `result.json`
files and exact `lock_released.json` SHA bindings. Its request also includes the
actual runtime manifest and storage proof, the five explicit positive integer
budgets and a documented capacity basis. A configured capacity allocation is
not a measured detector peak. The unchanged reserves are Windows 1.5 GiB,
Linux 1 GiB and two threads. Windows incremental allocation must cover the
Linux job allocation; Windows commit admission must include its reserve.

```powershell
& $stage5Python -B (Join-Path $stage5Work 'stage5_build_actual_config.py') `
  --request '<NEW_ABSOLUTE_DIRECT_WORK_REQUEST_JSON>' `
  --request-sha256 '<ACTUAL_REQUEST_SHA256>' `
  --output '<NEW_ABSOLUTE_DIRECT_WORK_ACTUAL_CONFIG_JSON>' --build

& $stage5Python -B (Join-Path $stage5Work 'stage5_windows_owner.py') `
  --config '<ACTUAL_CONFIG_JSON>' --linux-script (Join-Path $stage5Work 'stage5_atomic.py') `
  --output '<NEW_ABSOLUTE_WORK_OWNER_SPOOL>' --accession GCF_000009425.1 --run
```

The first genome is one checkpoint in the already approved full196 dataset.
After independent raw validation and four-cell curation, publish its closed raw
archive, obtain fresh GitHub payload readback and prove canonical rehydration
before eviction. Continue the full196 queue using the same accepted caches.
Final figures require the accepted full196 tree and all784 independently
validated explicit cells. No accepted Stage4 inference is rerun.

The remote work order authorizes automatic stage progression and excludes
routine approval pauses. The current direct human instructions additionally
authorize necessary cleanup, service and WSL repair. Those permissions do not
replace source, resource, closure, privacy or scientific validation gates.
