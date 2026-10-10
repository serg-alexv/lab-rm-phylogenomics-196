# First-genome config through qualified backing UNC

This packet contains source preparation only. Both new CLIs default to `PREPARED_NOT_RUN`; no actual request/config, lock, WSL command, native execution or Git ref was created/changed. Root must publish the reviewed source, complete and independently verify fresh backing UNC04, then perform actual bounded preparation/admission.

`stage5_build_backing_actual_config.py` preserves exact original builder `15dd2d4de4646d154ebfe503ae91f765d15f9f3cbd9e75099fbbfe703ffa2daa`. Five literal replacement rules change only the Windows-owner filename/SHA, UNC-probe filename/SHA (including its checked-gate lookup), and `resource_wait_seconds` from0 to1800. Reversing those rules restores every original byte. New pins are:

* `stage5_windows_backing_owner.py`: `296492aa4205f64058846b9901a7bb3a3458f99eda1c7ff388a6e33cdc38b834`
* `stage5_unc_backing_probe.py`: `779502c38c5db06b68e796abc6e1bd99db72d8f97b1129f9057a3f6b0c4221d5`

Every other dependency and guard remains unchanged. The builder still requires all six actual setup/interop/UNC gates and explicit unlock hashes, exact runtime08/storage06 candidate roles and gate-produced candidate joins, the UNC04 final proof-path/SHA join, original WorkflowLock/direct authority/no closure STOP, current Windows physical/commit/disk admission, final source/control rereads and a fresh direct-C output path. The backing probe retains the existing validated result schema/status/three phases; its distinct new source pin prevents the failed canonical UNC03 receipt from satisfying the builder.

`prepare_stage5_first_backing_actual_request.py` preserves exact v3 preimage `cf49f22430a0bfa435491c25ac73494b253acae53aac2ff3b8b910d4a65eaa09` with only one literal route change: `stage5_unc_bind_actual_postiq_03` becomes `stage5_unc_backing_actual_postiq_04`. Toolchain07/runtime08/interop05/storage06/drivefs04 paths, runtime08/storage06 candidates, original request template, five native resource budgets and the complete scientific method/basis remain unchanged.

Native budgets remain: incremental Windows1.5GiB (1610612736 bytes), commit3GiB (3221225472), Linux job1.5GiB (1610612736), process address space4GiB (4294967296), sampled descendant RSS1.25GiB (1342177280). Windows reserve1.5GiB, Linux reserve1GiB, two threads and serial owner remain unchanged. The preserved resource basis states these are conservative allocations, not measured detector requirements; full PADLOC5027 and all three DefenseFinder native families remain mandatory.

Correction to the earlier memory feasibility description: the original builder unconditionally forced wait0; it did not enable a bounded retry window. Only this new variant sets the explicit finite1800s native wait. This does not defer or waive the config builder's immediate Windows capacity check. Fresh Linux/Windows admissions still apply before native commands; expiration is deferred execution, not biological absence.

After all source peers/publication and actual UNC04 qualification, root may invoke the new preparer with `--prepare --output stage5_actual_request_<fresh_name>.json`, then the new builder with `--build --request <absolute-new-request> --request-sha256 <actual-SHA> --output <absolute-fresh-C-config>`. The existing backing Windows owner uses that actual config with unchanged runner/supervisor. Those operations are **NOT_RUN** for this packet; no sample actual request or config is fabricated.

Fifteen pure/synthetic tests pass: eight builder contracts and seven request contracts. They include exact reversible source changes, retained method/budgets, rejection of noninteger/infinite/missing/inconsistent budgets, failed/unclosed/replaced gates, old UNC source, missing cleanup or wrong phase, stale unlock, failed candidate role/template, deterministic request pins, exact route selection and no actual reads/writes/native imports on default NOOP. Both real Windows default-NOOP invocations passed. Tests use synthetic temporary-C gate fixtures and do not qualify production UNC, WSL, runtime or biology.

The architectural basis and actual read-only diagnosis are separately documented in `stage5_unc_backing_architecture01.md/json`. The original UNC03 failed receipt is preserved. Direct backing write/fsync/readback/exact cleanup must still pass under retained ownership before any first-genome native admission.
