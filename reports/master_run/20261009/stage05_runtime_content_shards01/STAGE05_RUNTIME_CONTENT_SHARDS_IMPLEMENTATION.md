# Content-labelled runtime recovery implementation

The current reusable loop image is the installed scientific toolchain. The
registered Ubuntu VHDX is the distribution OS. Both must retain their working
paths while Stage5 runs: installed Conda and R prefixes and the WSL registration
refer to those paths. Snapshot shards are transport files; splitting a registered
backing disk in place would prevent it from being mounted.

`postboot_vm_recovery_review01.json` is an actual bounded Windows/registry/Release
metadata observation. No image payload was read. It records the8GiB toolchain,
15.81GiB logical VHDX, current filesystem allocation and the30 current recovery
Release assets. Installed-runtime capture and OS/bootstrap restoration remain
unverified. Keep both originals.

`stage5_runtime_transport_alias.py` implements content labels without changing
the already reviewed capture, independent reader or extractor. Given the exact
capture index, it produces one immutable alias map. For example, the original
`stage5-installed-runtime-01.part0001` is uploaded with the name
`stage05-runtime-detector-env-defense-models-padloc-db-20261010-v1.part0001`.
The map retains both names, exact bytes/SHA and unchanged original LF sidecar
bytes. A sidecar's remote filename receives the same content label; its contents
still name the canonical original part, deliberately preserving its exact bytes.
The existing owned uploader supplies the alias as the Release asset name while
streaming the canonical original file. The existing owned downloader requests
the pinned asset ID and saves its bytes directly under the canonical local name
in a fresh namespace. No additional full payload copy or image rename is needed.

The plan command is ready once actual capture creates its index:

```powershell
& $primaryPython -B work/stage5_runtime_transport_alias.py --plan `
  --index C:/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_runtime_capture_ACTUAL/index.json `
  --index-sha256 ACTUAL_INDEX_SHA256 --snapshot 20261010-v1 `
  --output C:/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/stage5_runtime_alias_actual01.json
```

`bind_assets` checks the complete selected actual Release metadata set before
and after the owned downloads; it returns actual remote asset IDs and names
alongside canonical local names. `verify_stream` checks every byte with bounded
reads and the caller's continuous ownership/deadline/resource callback. Preserve
the raw API asset witnesses and alias-map SHA in the final remote receipt. Do not
rename those raw witnesses to look like canonical filenames. The old extractor's
`remote_gate` expects canonical asset names: use a separately reviewed alias-aware
remote adapter to bind the actual alias witnesses and supply derived canonical
bindings, or add that explicit binding to the gate. The pure alias implementation
does not itself establish a fresh remote recovery gate. Full gzip/member/manifest
verification and actual cold restoration are still mandatory.

The seven authored synthetic tests passed. An independent reviewer also passed
those tests plus11 extra in-memory two-part/tamper cases. No actual payloads were
created, uploaded, downloaded or removed by these tests.

## Actual inventory entry point and existing-owner integration

Before this change, the only inventory entry point was
`stage5_runtime_logical_capture.inventory_frozen_roots(runtime, proof, admission)`;
there was no inventory CLI. `stage5_runtime_inventory_entry.py` now supplies an
opt-in CLI worker that calls that pinned function. Its default invocation is a
NOOP. It introduces no owner, lock, supervisor, subprocess or mount operation.

The worker requires an actual current `STAGE05_PINNED_RUNTIME_V1` candidate, an
exact `STAGE05_RUNTIME_COLD_CAPTURE_PROOF_V1` file, the existing owner lease/nonce,
and an explicit source SHA. The proof must additionally contain `owner_nonce`
and `workflow_lock` matching the fresh lease. The existing original owner must
first close detector/native writers and qualify the exact image/mount UUID and
read-only mount with no writable aliases or backing-file writer. The worker
checks current read-only mount metadata itself; a boolean proof cannot perform
the freeze. No current setup source was edited or repinned by this preparation.

The existing Linux supervisor should execute this exact argv as one new
`runtime_inventory` command, after the reviewed cold freeze and with the
existing Windows owner renewing the same lease:

```text
<retained detector_env>/bin/python -B <current C Linux work>/stage5_runtime_inventory_entry.py
 --run --source-sha256 <published entry SHA>
 --runtime <actual runtime JSON> --runtime-sha256 <actual SHA>
 --cold-proof <actual cold proof JSON> --cold-proof-sha256 <actual SHA>
 --owner-lease <same Windows-created lease> --owner-nonce <same owner nonce>
 --output-private <current C Linux work>/stage5_runtime_inventory_private_actual01
```

Extend the existing setup owner's allowed step/arguments/expected-command
binding and deadlines for this command, and publish/review its coordinated
source pins first. Use a1900-second owner deadline around the worker's1800-second
deadline and retain the existing native/WSL/Windows closure checks and original
unlock. The worker's capacity allocation is512MiB sampled self RSS plus1536MiB
current Windows physical and commit reserve, not a measured full-inventory
requirement. The existing supervisor must enforce the same allocation for the
worker; an admission failure preserves partial files and never authorizes retry
or cleanup. Do not overlap the cold freeze/inventory with Stage5 detector work.

The new private output contains `PRIVATE_MANIFEST_DO_NOT_PUBLISH.jsonl` and
`PRIVATE_HOLDS_DO_NOT_PUBLISH.json`, plus a public counts/digest-only
`PUBLIC_SUMMARY.json`. Whole-file public review and notice/source mapping must
qualify the complete required inventory before any original payload is uploaded.
A required private or unresolved file blocks complete public recovery. The
entry worker has only been syntax/no-op checked on Windows; actual Linux
inventory and existing-owner integration are NOT_RUN and require independent
review before adoption.

## Public OS/bootstrap reproducibility boundaries

Use a separate explicit allowlist for Ubuntu context. Collect distribution
identity from `/etc/os-release`, kernel/WSL versions, architecture, package
name/version/architecture/status tuples from `/var/lib/dpkg/status`, locale names,
required system ELF-loader/glibc/libstdc++/libgcc/R dependency identities and
hashes, runtime environment-variable *names* and selected reviewed non-secret
values, and exact reviewed `/etc/wsl.conf`/loader configuration. Bind every item
to its original-byte hash, corresponding original package/source/notices and a
restore command. Inspect dependency resolution under the same controlled native
fixtures after restoring the original runtime prefixes.

Do not recursively export `/home`, `/root`, `/mnt`, `/proc`, `/sys`, `/dev`,
authentication stores, SSH keys, shell histories, agent sessions, cloud/browser
caches, `/etc/shadow`, machine identity, live networking secrets, free blocks or
the complete raw VHDX. Treat apt source URLs, proxy environment values, network
configuration, shell startup files and runtime `.dist-info/direct_url.json` as
PRIVATE candidates until whole-file review; publish accepted originals or
explicit excluded-file hashes, never redacted bytes presented as originals.

The primary project recovery is the complete reviewed installed-runtime logical
archive plus OS/bootstrap dependency data, original sources/packages/notices and
project results. The bounded fallback is a cold, offline byte-exact snapshot in
448MiB parts only if the full payload scope is accepted for its destination.
Public GitHub is not an accepted destination for unreviewed whole-machine or
free-block contents. Neither approach currently grants local eviction or host
wipe readiness.
