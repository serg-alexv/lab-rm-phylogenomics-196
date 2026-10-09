# Post-IQ Stage5 setup — prepared source, actual execution NOT_RUN

The actual previous IQ-TREE native and retained controller exited0 on 2026-10-09 at21:49:06UTC. Their empty JobObject, explicit original byte unlock and power restoration are recorded separately from scientific tree acceptance. The new setup sources use those exact operational records. No WSL boot, mount, discovery, interop, filesystem probe or detector has been run by this preparation.

The primary route is the four scoped setup steps below, then the existing self-locking interop, UNC and single-genome owner CLIs. The original WorkflowLock and single-heavy-job policy remain unchanged. Do not hold an outer WorkflowLock around any of these CLIs: each Windows entrypoint acquires the original byte lock itself. Root must reconcile current GitHub authority, disabled legacy tasks, existing stop markers and actual resources before execution. Publication and root authorization of these sources precede any actual setup.

## Scope and proofs

`stage5_setup_windows.py` owns the existing exact Windows byte lock, uses fresh GetPerformanceInfo physical/commit and physical C/G disk readings, and renews a3-second actual lease every0.5seconds. Nonscientific setup admission requires1.75GiB physical and commit headroom plus10GiB on each supplied Windows volume. Linux separately requires256MiB available and10GiB disk. These are setup limits, not a proposed detector budget. Runtime hash discovery has a900-second native deadline and960-second Windows wait; other setup commands have45-second native and120-second Windows waits. Mount-lock acquisition is nonblocking with a5-second maximum wait. Failed admission never waits for resources.

The wrapper checks exact retained native/controller births and actual exit0, native empty JobObject, four original closure-file hashes, and power flags2147483648. It requires the actual observer receipt SHA supplied below. It also reopens Ubuntu's exact WSL2 registry registration on C and checks the registered VHD path/ancestry for aliases/reparse points, without reading VHD payload bytes. This binds the selected distro and physical disk resource gate; it does not hash or certify the whole VHD.

The Linux toolchain step observes the exact retained8GiB regular `toolchain.ext4`,120 ext4 superblock bytes and UUID, current boot/mountinfo, mounted device and directory inode, and actual loop backing file through sysfs. A pre-existing mount is accepted only when that exact observation succeeds. If absent, only the empty original `.tools/linux` mountpoint may be mounted. Unknown mountpoint contents are preserved. The whole image is not hashed and runtime authenticity remains a separate actual file/model manifest check. The old0-byte `tool_mount.lock` is opened, never replaced.

Runtime discovery invokes only the reviewed hash/import/version discovery helper under the retained interpreter. It avoids inventing the template's five missing detector resource fields. The source manifest records the effective ambient and MacSy configuration, exact detector libraries/native extensions, models, databases and version metadata. Full hash reopens remain the first-production policy; no unmeasured read-only mount optimization is introduced.

Storage setup records the empty Windows G underlay first, creates only the fixed empty backing `/var/tmp/lab_rm_stage05_atomic_v1` if absent, proves its already writable native ext4 filesystem, then binds it onto exact canonical Linux `ROOT/.work/stage05_atomic_v1`. The existing independent storage helper records and immediately rechecks current boot, mount identity, ext4 UUID, device/inode, backing and target. Existing populated storage is reusable only behind the exact valid bind proof; unknown unbound contents are preserved. The Windows G underlay stays empty and unchanged.

The DriveFS step runs the retained fsync/replace/flock fixture in a separate ordinary G namespace. A separately owned Windows worker reopens actual result and four tiny file hashes/bytes. It is created suspended in a kill-on-close one-process JobObject and has20seconds plus5seconds owned cleanup. Result/stdout reads are capped at64KiB, payloads at4KiB, and directory inspection at six entries. It verifies actual ordinary fsync/readback, overwrite, runner atomic JSON, flock contention and close/reacquire evidence. Tiny ordinary G fixtures are preserved as evidence; this is not the covered ext4 endpoint test.

Before each WSL launch, the setup wrapper writes the protected C `stage05_owned_closure_unproven.json` stop marker. It removes only its own unchanged marker after actual retained WSL exit and all native pidfd/subreaper command closures are independently reopened; the DriveFS worker also needs actual empty JobObject closure. Any uncertainty preserves the marker and blocks new Stage5 owners. It never kills or shuts down WSL to manufacture closure. Synchronous registry/config/G metadata calls and kernel filesystem operations do not have a hard kernel cancellation guarantee; the finite client wait records uncertainty rather than treating timeout as closure. There is no new generalized controller, installation, unmount, extraction or scientific search.

## Exact proposed sequence

Use new output names; never reuse a failed or existing spool. These are proposed commands, not evidence that their operations ran. Confirm the published reviewed source hashes against `stage5_post_iq_setup_preparation.json` before `--run`.

```powershell
$Stage5Python = 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$Stage5Work = 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'
$Stage5LinuxEnv = '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/detector_env'
$Stage5LinuxSha = '8416a45a4dcc822784e465a4ad91236082fc97fec763d330a14006fd9f5af20e'
$Stage5Common = @('--controller-receipt', "$Stage5Work\iqtree_controller_closure_actual01\receipt.json",
  '--controller-receipt-sha256', '7b6a6f78f2abfa833bc17f2767df1ae4e44ccc35de9ae35323461c5337481603',
  '--controller-observer-sha256', '483b5165d015dcea659d5e850187c79ff5e99c4c0efff1c9fb108cc9a59ab78a',
  '--linux-source-sha256', $Stage5LinuxSha)

# 1. Default is a C-only plan; --run requires reviewed publication and root authorization.
& $Stage5Python -B "$Stage5Work\stage5_setup_windows.py" --step toolchain `
  --output "$Stage5Work\stage5_setup_toolchain_actual_postiq_01" @Stage5Common --run
$Stage5ToolProof = "$Stage5Work\stage5_setup_toolchain_actual_postiq_01\toolchain_proof.json"
$Stage5ToolSha = (Get-FileHash -LiteralPath $Stage5ToolProof -Algorithm SHA256).Hash.ToLowerInvariant()
$Stage5Mounted = @('--toolchain-proof', $Stage5ToolProof, '--toolchain-proof-sha256', $Stage5ToolSha)

# 2. Actual immutable runtime/model/ambient hash discovery; no detector search.
& $Stage5Python -B "$Stage5Work\stage5_setup_windows.py" --step runtime `
  --output "$Stage5Work\stage5_setup_runtime_actual_postiq_01" @Stage5Common @Stage5Mounted `
  --candidate-output "$Stage5Work\stage5_runtime_actual_postiq_01.json" --run

# 3. Existing actual cross-OS exit0 / real lease-expiry / escaped-descendant fixtures.
& $Stage5Python -B "$Stage5Work\stage5_interop_smoke_windows.py" `
  --linux-python "$Stage5LinuxEnv/bin/python" --distribution Ubuntu `
  --output "$Stage5Work\stage5_interop_actual_postiq_01" `
  --supervisor-sha256 fdcc8d3b4337209b64ffa3732a8182bf832f2fa05d1e95fcdfb32964d4ad4a34 `
  --windows-api-sha256 80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827 --run

# 4. Exact native-ext4 bind, preserving the Windows underlay.
& $Stage5Python -B "$Stage5Work\stage5_setup_windows.py" --step storage `
  --output "$Stage5Work\stage5_setup_storage_actual_postiq_01" @Stage5Common @Stage5Mounted `
  --candidate-output "$Stage5Work\stage5_storage_actual_postiq_01.json" --run

# 5. Ordinary DriveFS primitives plus independent bounded Windows actual-byte readback.
& $Stage5Python -B "$Stage5Work\stage5_setup_windows.py" --step drivefs `
  --output "$Stage5Work\stage5_setup_drivefs_actual_postiq_01" @Stage5Common @Stage5Mounted --run
```

Stop after any nonzero exit or qualified closure. Require each setup result `PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK`, actual native command receipts where required and its explicit byte unlock. Runtime and DriveFS cannot pass without actual native helper execution. Toolchain/storage may use zero native commands only when the current exact pre-existing mount is independently proved. Interop requires `PASS_NONSCIENTIFIC_INTEROP_ONLY`, all three fixture-specific actual native/lease/closure/log predicates, explicit unlock and no unproven stop. Preserve every C spool and failed candidate.

Next write a **new C** `stage5_mount_probe_01.json` from the unchanged V2 template. Fill `runtime.manifest_path/manifest_sha256` with the just-produced Linux C runtime manifest and actual SHA, and `work_storage.proof_path/proof_sha256` with the just-produced Linux C storage proof and actual SHA. Keep canonical root/output/runtime roles. Its five native resource fields may remain null for this nonscientific UNC check; the UNC source does not validate or invent detector policy.

```powershell
# 6. Existing exact ext4-bind UNC endpoint probe; it self-locks.
$Stage5ProbeConfig = "$Stage5Work\stage5_mount_probe_01.json"
$Stage5ProbeSha = (Get-FileHash -LiteralPath $Stage5ProbeConfig -Algorithm SHA256).Hash.ToLowerInvariant()
& $Stage5Python -B "$Stage5Work\stage5_unc_bind_probe.py" --run `
  --config $Stage5ProbeConfig --config-sha256 $Stage5ProbeSha `
  --script-sha256 70bbd9b0ae04ad90f3b1595d49d844ba899b93aefad6d2edf37ec675a99c9830 `
  --output "$Stage5Work\stage5_unc_bind_actual_postiq_01"
```

UNC success requires `PASS_NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY`, actual Windows UNC write/fsync/read and Linux exact readback, unchanged proof/Windows underlay, all three actual closed steps and Linux-proven exact two-leaf/directory cleanup. Every Windows UNC operation stays inside the bounded owned worker. This establishes immediate endpoint visibility and fsync support, not cloud upload, crash durability or science.

## First actual approved genome

After all six actual gates pass, root creates **new** `stage5_actual_01.json`, fills the same actual runtime/storage pins and supplies explicit finite values for the five missing native fields: incremental Windows requirement, commit requirement, Linux job requirement, per-process address-space limit and sampled process-tree RSS stop. Record the conservative basis and current actual admission; commit requirement is compared directly, so it must include the intended reserve. Keep threads2 and existing1.5GiB Windows/1GiB Linux reserves. RLIMIT_AS applies to each process and sampled tree RSS is a stop mechanism rather than a kernel aggregate memory cap. No detector peak is measured yet, and Stage4 memory does not determine detector demand.

```powershell
# 7. Prepared config/scope check, then ONE full-method approved genome after admission.
& $Stage5Python -B "$Stage5Work\stage5_windows_owner.py" `
  --config "$Stage5Work\stage5_actual_01.json" --linux-script "$Stage5Work\stage5_atomic.py" `
  --output "$Stage5Work\stage5_owner_GCF_000009425_1_postiq_01" --accession GCF_000009425.1
# Repeat the identical command with --run only after the actual prerequisite gate.
```

The first genome uses the full fixed native scope and counts toward196; it is not a reduced-profile biology run. Capture wall time, native CPU and `sampled_tree_peak_rss_bytes`, actual Windows RAM/commit and C disk leases, Linux memory/storage costs, file counts/bytes and hash time. Preserve raw native/config/launch/closure/log evidence and export verified bounded per-genome archives to GitHub. Do not start blind heavy parallel workers. Successful exact checkpoints resume individually; `complete.json` records native/source/raw integrity with V2 identity and `curation:NOT_RUN`, not biological absence.

Closed-genome curation can proceed independently of the host tree. Final matrix join and production figure require the independently accepted exact196 host tree and full-panel accepted curation; remote publication is a separate workflow gate. Stage5 detection no longer needs final Stage4 tree/publication.

The bounded fallback is stop/preserve and diagnose the exact failed operational/runtime gate. Public recovered339 Conda packages, model/source archives and original manifests help repair/reconstruct under root authority; they do not certify the exact installed environment or recover the complete8GiB image. Preserve the existing toolchain/lock/source guards until an actual accepted replacement and remote restore proof exist. No accepted upstream stage is rerun without concrete corruption evidence.
