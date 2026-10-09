# Stage5 V2 deployment readiness — source audit, 2026-10-09

Stage5 remains **NOT_RUN**. The native detector dependency split is coherent: an accepted host tree is not a detector input. No hidden runtime dependency on the purged old C scientific caches was found. This audit neither starts WSL nor measures/invents detector resources, mounts storage, acquires the workflow lock, runs native tools, or writes scientific inputs. Root owns the actual admission, closure reconciliation and publication.

## Protected dependencies and current source gate

- Native source inputs, the six accepted Stage2/3 controls, per-accession released source receipts, and nine retained helper modules are reopened beneath `G:\My Drive\LAB_RM\lab-rm-phylogenomics-196`. `load_modules` prepends the canonical G helper directories, checks source hashes/import locations, and passes source/bundle/execution/inventory/model paths explicitly. `native_df_posttreat.py` is resolved beside the G detector module. Old standalone CLI defaults are not invoked by the wrapper.
- The curation template also uses canonical G source and `G/.work/review2/stage05_policy`; its old C-looking model paths refer to the intentionally retained toolchain, not purged scientific caches. Source acceptance is the standalone manifest SHA `a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84`; its old paths are recovery/derivation witnesses, not runtime reads.
- **Keep** the original old C `.work/workflow.lock` file/identity, `.tools/toolchain.ext4`, its exact `.tools/linux` mount prefix, current controller/code/config/guard/receipt files, and current C curation package. The empty Windows `.tools/linux` underlay while unmounted does not establish missing packages. Do not replace or recreate the stable lock file.
- Root previously checked the 202 canonical control/receipt pins. The separate newly authorized current source-byte check covers all 196 accepted source manifests, which declare **12,812 files / 1,893,101,586 bytes**. Its `stage5_source_readiness.py` calls only the exact pinned V2 `validate_genome_inputs`, using Windows canonical G path roles, one serial below-normal-priority reader, retained-file/path identity checks and hashes. Its receipt is source readiness only, never new upstream/native/curation acceptance. Results will be bound separately when the actual check finishes.

## Exact ordering before the first approved genome

1. Reconcile the current native IQ-TREE retained process/JobObject, actual terminal exit, descendants, exact writer-lock release and power restoration. A free-looking lock or missing PID is insufficient. Reconcile any existing `stage05_owned_closure_unproven.json` or interop unproven-stop evidence before any additional native launch. Host-tree scientific acceptance is not needed for Stage5 detection; operational closure is.
2. Under root's owned writer lock and fresh admission, boot the intended Ubuntu instance and remount the retained ext4 toolchain at its original prefix. Freshly inspect actual Linux package/import/executable paths and mount identity. Do not install or infer package absence from the Windows underlay. Keep the actual WSL client handle/exit evidence.
3. Capture runtime and ambient configuration using the narrow discovery helper below. This **only** hashes installed files/models and package metadata and writes a new C manifest. The original `stage5_atomic.py --config ... pin-runtime` CLI calls job-policy validation first and rejects the template's **five** null job-resource fields; the separate helper avoids inventing a detector budget for hash discovery. No production run gate is changed.
4. Run the prepared actual cross-OS lifecycle smoke under its owned original lock. Require all three harmless Python fixtures and independently reopened intent/launch/closure/command/exit bindings; `PASS_NONSCIENTIFIC_INTEROP_ONLY` is not scientific adoption. Run the separate three live Linux lifecycle fixtures if required by the integration audit; their synthetic owner lease cannot replace actual Windows/WSL interop. All actual fixtures remain **NOT_RUN** in this audit.
5. With root holding the original lock, establish the exact ext4 backing `/var/tmp/lab_rm_stage05_atomic_v1` bound onto canonical Linux `ROOT/.work/stage05_atomic_v1`. Inspect/preserve the actual G underlay first; do not cover unknown data. Record a **fresh-boot** storage proof with `stage5_work_storage.py`; it verifies canonical no-symlink paths, rw ext4, bind directory device/inode, exact mount root, UUID and stable mountinfo. The helper never mounts anything. Keep the binding unchanged while native jobs or curation readers use it.
6. Run the prepared DriveFS primitive probe with a new receipt of the **currently held** original Windows lock and its SHA. Independently read the exact tiny fixture/result bytes through Windows G. Separately prove the bound ext4 endpoint is visible through `\\wsl.localhost\Ubuntu\mnt\g\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage05_atomic_v1`, with a small exact-byte/hash readback under the held lock. The existing smoke probes C lifecycle and an ordinary G namespace; neither alone establishes the ext4/UNC alias. The owner requires that UNC directory and reads native receipts there, rather than the covered Windows G underlay.
7. Fill a **new** V2 job config using measured current Windows physical/commit headroom, Linux available memory, filesystem free space and a conservative explicit first-genome policy. The five null resource fields are `incremental_windows_requirement_bytes`, `commit_requirement_bytes`, `linux_job_requirement_bytes`, `process_address_space_limit_bytes`, `sampled_rss_stop_bytes`. Record the actual basis/limits; no value is inferred here. Also fill `runtime.manifest_path/manifest_sha256` and `work_storage.proof_path/proof_sha256`. Keep threads=2, finite timeouts, lease10–60seconds for the Windows owner, and the exact canonical source/output/runtime roles. `RLIMIT_AS` is per process; sampled RSS is a stop mechanism, not a kernel aggregate job-memory cap.
8. Require current canonical `status/run_control.json` state `ACTIVE_DIRECT_USER_CONTINUATION`, `automatic_resume:false`, all current code/config/helper pins, resource admission and an uncontested original stable lock. Run the Windows owner first without `--run` as the prepared config/scope check, then its explicit single-approved-accession command below. The completed first genome counts toward the full 196 queue. Measure actual elapsed time, native process tree/RSS/address-space, Windows commit/physical headroom, Linux memory and storage costs before expanding the queue; do not claim an unmeasured detector budget.

## Prepared commands, not executed here

Linux variables refer to the existing mounted retained paths:

```sh
WORK='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work'
ROOT='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
ENV='/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/detector_env'

# Hash discovery only; new output; root owns admission/lock/mount context.
"$ENV/bin/python" -B "$WORK/stage5_runtime_discovery.py" --discover \
  --output "$WORK/stage5_runtime_actual_01.json"

# Observe an already established exact bind; no mount is performed by helper.
"$ENV/bin/python" -B "$WORK/stage5_work_storage.py" --root "$ROOT" record \
  --output "$WORK/stage5_storage_actual_01.json"
"$ENV/bin/python" -B "$WORK/stage5_work_storage.py" --root "$ROOT" validate \
  --config "$WORK/stage5_actual_01.json"
```

Windows first-genome command, only after all actual prerequisites pass:

```powershell
$Stage5Python = 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$Stage5Work = 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'
& $Stage5Python -B "$Stage5Work\stage5_windows_owner.py" `
  --config "$Stage5Work\stage5_actual_01.json" `
  --linux-script "$Stage5Work\stage5_atomic.py" `
  --output "$Stage5Work\stage5_owner_GCF_000009425_1_attempt_01" `
  --accession GCF_000009425.1
# Repeat the exact prepared command with --run after the actual prerequisite gate.
```

Use the reviewed command and SHA arguments in `stage5_interop_smoke.md` for actual lifecycle smoke, and `stage5_drivefs_filesystem_smoke.md` for the actual held-lock DriveFS probe. Current reviewed Supervisor SHA is `fdcc8d3b4337209b64ffa3732a8182bf832f2fa05d1e95fcdfb32964d4ad4a34`; Windows API SHA is `80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827`. Capture actual source hashes again before execution; source drift requires review, not updated expected pins by inference.

## Effective config, checkpoints, curation and final gates

Runtime discovery records actual `HOME`, `VIRTUAL_ENV`, `MACSY_CONF`, `PYTHONPATH`, `PYTHONHOME`, actual Linux home and MacSy configuration presence/resolved path/hash for prefix-etc, the selected system override, user-home and canonical project-root CWD. Relative HOME/VIRTUAL_ENV/MACSY_CONF overrides are rejected and project-root `macsyfinder.conf` must be absent. Installed imports must resolve inside the retained environment. A hash manifest does not demonstrate a successful native search.

Per-task `macsyfinder.conf` is generated in the source-bound bundle and independently bundle-audited before any native command. The native prelaunch guard rechecks runtime ambient configuration, the exact CWD config hash, HMMER resolution, storage and owner lease. The actual raw checker reopens the preserved effective native configs and compares scientific sections. Preserve those configs, exact argv/command/intent/launch/closure/log receipts and native raw/profile outputs; do not amend a completed native config to make a receipt pass.

`complete.json` remains `STAGE05_ATOMIC_GENOME_COMPLETE_V1` with V2 scientific identity, exact files manifest, inventory directory and raw-validation file. It means native search/source/raw integrity only, with `curation:NOT_RUN` and no biological absence claim. Reuse an exact verified checkpoint; a failure on one genome need not rerun others. Curation can consume each **closed** genome checkpoint and source-bound architecture/domain evidence without a host tree. Independent full-panel curation accounts all196 and 784 cells, including explicitly validated documented exceptions; only frozen closed retained positives can support1 in an exception. Unproven active native closure blocks new launches and final scientific acceptance.

The final exact196×4 join and production Stage6 renderer remain bound to the independently accepted host tree, full-panel independently accepted curation, exact hashes and validated join. The workflow's release/publication gate is separate from the renderer's accepted-tree gate. Ext4 raw files should be preserved/exported using the reviewed per-genome bounded archive method; do not make millions of loose UNC copies or claim remote recovery before actual archive readback.

Independent source review by stage5_audit found no concrete hidden-cache dependency or narrow runtime-helper blocker. Actual current canonical support-source check also passed all nine required modules, 182,212 bytes: `stage5_support_code_readback_01.json`, SHA `b69abf3b05547af575b0b6badd97d870cc077b73a3a3697444ce14efe49db28c`. New synthetic checks: runtime discovery4 PASS; final source-reader scope/identity4 PASS. These are preparation checks only; actual Linux/runtime/storage/native/interop remain NOT_RUN.

The source-byte check's first invocation failed at its own scope guard before any genome payload hash: the existing V2 function also hashes the deliberately standalone active C accepted-source pin manifest. The original reader (`stage5_source_readiness_attempt01.py`, SHA `126c2012271a86217179384d42d1980afc531b094f9a0fdbf553bf400826a16e`) and complete attempt01 evidence are preserved. The corrected reader admits only that exact non-symlink C manifest and its independent SHA; every other C path remains forbidden. A focused regression also observed that Windows `fstat` and path `stat` expose differing `ctime_ns` for the unchanged same file (3 ms), so stability uses exact device/inode/size/mtime plus the full accepted SHA instead. Source identity drift aborts the whole pass and retains a failed/partial receipt. The production source gate is unchanged. Attempt02 is a new namespace; neither failed checker preparation nor a successful source-only pass is a biological result.
