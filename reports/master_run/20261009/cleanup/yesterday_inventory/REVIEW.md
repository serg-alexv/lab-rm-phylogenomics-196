# Yesterday's LAB R-M history inventory and batch02 recommendation

Read-only inventory; actual cleanup, archive rebuild, move, push and WSL execution: **NOT_RUN**.

The bounded inventory found 89,241 files / 20,044,247,396 logical bytes under exactly
`C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196` and
`C:\Users\wheel\Documents\Codex\2026-10-08\referenced-chatgpt-conversation-this-is-an`.
Twelve other library chats had no bounded LAB R-M textual hits and were excluded;
the firmware task was excluded. Reparse directories were not followed. The original
inventory hashed 7,411 important small files under a 256 MiB I/O budget;
the focused public source/checkpoint supplement adds 291 files / 1,656,660 bytes.
Large runtime/data/image files are metadata-only. Sizes do not independently measure disk allocation.

GitHub main was captured at `83059864f424fc6db7beebaa898f1f0019bc4d51`. The remote comparison
proved old C HEAD `8ec0cee563848b75022bc464ad586d19b07b1ffe` is an ancestor (124 commits ahead,
0 behind at observation). Actual local bytes matched 281 current remote-main Git blobs
and two blobs in that reachable historical commit. Four checked tracked files differed;
there were 199 dirty/untracked entries. Local Git cleanliness or
local duplicate hashes were never treated as proof of remote asset recovery.

`files.jsonl` is the complete local metadata inventory, including private-control path
metadata; keep it local unless separately reviewed. `files_public_metadata.jsonl` excludes
private-control/raw Codex event/prompt/usage metadata (800 rows excluded), and does
not copy any file content. Public source/checkpoint supplement pins are in
`critical_public_history_pins.json`. Neither metadata manifest authorizes a recursive purge.

## Keep active dependencies and scientific history

- Keep old C `.work/workflow.lock` as the same original file, plus original controller,
  source guards, configuration/status and private control trees. No private content is
  selected for public archive or cleanup. Do not infer closure from this inventory.
- Keep old C `.tools/iqtree_windows_3_1_4/extracted/iqtree-3.1.4-Windows/bin/iqtree3.exe`:
  actual SHA256 `43c9bf3b0dc5e7d88c183a2582369d22c9d692b7585350038769334bb6fd9aed`,
  12,332,544 bytes. The current native job config binds that exact absolute path.
- Keep old C `.tools/toolchain.ext4` (8,589,934,592 bytes, not hashed here) and the mounted
  prefix `/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/`
  with `detector_env`, `defense_models` and `padloc_db`. Root's actual mounted Linux probe
  is pinned in `current_dependency_evidence.json`; the empty Windows mountpoint does not
  indicate missing runtime. Keep package/model source archives and notices pending a
  remotely verified reconstruction/archive. No 8 GB image was read.
- Keep old source-locus inputs (1,897,944,451 logical bytes), Stage2 validated payloads,
  Stage3 markers/search/curation, and accepted Stage4a derivatives until exact remote
  member coverage is proved. This pass does not rerun or replace accepted stages.
- Retained `host.model.gz` files, native commands/logs, failed attempts and UNKNOWN closure
  evidence remain historical evidence. Native failure ZIP bytes remain labeled failure;
  no biological absence, successful tree, closure or whole-project completion is inferred.
- Old synthetic/controller fixtures are historical archive candidates only. They have
  no scientific acceptance role and are not selected by the one batch below.

## ONE highest-yield currently verified batch: old release-staging duplicate files

Recommend the exact **82 individually allowlisted files / 2,190,829,648 bytes** in
`batch02/file_allowlist.json`: 28 ZIP copies of 27 distinct published ZIP assets and 54
`.zip.sha256` copies, confined to old C `release_staging/stage02`, `stage03`, `stage04a`
and `stage04b`. This is a candidate for root's reviewed cleanup; no deletion ran.
It is disjoint by path from old historical-chat output groups.

Actual local whole-file SHA256 and size matched the current GitHub asset digest and
accepted publication receipt for every ZIP. All 45,955 ZIP members were streamed
sequentially: CRC and exhaustive internal SHA256/size/member-set checks passed; the
checksum manifest itself is bound by the whole-archive SHA256 and its own CRC.
The 54 sidecar copies also matched current remote digests and exact ZIP hash lines.
The four releases' exact asset IDs/sizes/digests were unchanged before/after verification.
No assets were downloaded, rebuilt or re-published. Actual ZIP stream content totaled
6,512,011,781 uncompressed bytes; verification used 1 MiB streaming chunks and one process.

| Staging directory | Exact files | ZIP copies | Logical bytes |
|---|---:|---:|---:|
| stage02 | 36 | 12 | 1,485,497,407 |
| stage03 | 36 | 12 | 675,376,301 |
| stage04a | 6 | 2 | 29,667,422 |
| stage04b | 4 | 2 | 288,518 |

The allowlist excludes `.tools`, `.work`, current G scientific inputs, original source/
controller/lock paths, all private control history and `payload_paths.json`.
**Do not recursive-delete `release_staging` or its stage directories**: unselected files
remain. Root must commit these receipts remotely, retain the exact recovery mapping,
confirm the exact local paths/bytes still match and exclude active handles, then perform
only the individually listed removals. Preserve historical FAILED/UNKNOWN labels.
For recovery, download the exact published asset below and verify the allowlisted SHA256;
the sidecars are separately published at their exact `remote_url` in the JSON allowlist.

## Exact ZIP recovery mapping

| Asset | Bytes | SHA256 | Recovery |
|---|---:|---|---|
| stage02-full196-derived-tables.zip | 51,044,271 | `bb8095c0d8fa51f09b68c484eaaf578bbda047d9df29b92626065684e59f0423` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-full196-derived-tables.zip) |
| stage02-methods-and-reports.zip | 440,905 | `61d52851fb7ccb21c310200774dad06c4c1121ba73c7eca53ca3187be03c9981` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-methods-and-reports.zip) |
| stage02-raw-001-020.zip | 156,618,351 | `73a8abe1683fff12098530dfb4ac356ccbb1f136886e0b6ffee6084e1626ac35` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-001-020.zip) |
| stage02-raw-021-040.zip | 134,932,566 | `a3a5f75d2332508b8df577b58583f2f2d38c77a1ff318144b4d7cbe9c8f1f828` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-021-040.zip) |
| stage02-raw-041-060.zip | 137,758,632 | `d72f20c034e74a2df3f0fd3c37e17ef39394e57e06de21aacf90922ddd0b8736` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-041-060.zip) |
| stage02-raw-061-080.zip | 142,236,742 | `8b30ff368ca11ac8eee764cb768b137cfe798caad7518d373681c628aa262d0a` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-061-080.zip) |
| stage02-raw-081-100.zip | 133,281,830 | `85cffd5005059eb80fa2782f4a36ef979ea67f6cce1a0a85096e6f70f6f22f13` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-081-100.zip) |
| stage02-raw-101-120.zip | 156,402,383 | `00fa8793cdb6c1dee9221054c87583a73bfec2e256a13c8649f7563281a5c914` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-101-120.zip) |
| stage02-raw-121-140.zip | 157,220,094 | `9c3627ecd54bba30109fbc59bd45a1025ca56cadea2327e19f995d9447951eed` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-121-140.zip) |
| stage02-raw-141-160.zip | 155,379,441 | `15a462627327ca256674fe0029f76e31e2c7ee6bc2b32f6ff448af465e844c5d` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-141-160.zip) |
| stage02-raw-161-180.zip | 146,172,764 | `f06ad515376a06edc6688d7189e9b5bcaefffedc6b576955a959b60b42a3d175` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-161-180.zip) |
| stage02-raw-181-196.zip | 114,007,230 | `2ba6d12f9b99cf8a00d2c3757d386578e632c4aa0b030c360accfefb6f5b7010` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage02-sequences196-v1/stage02-raw-181-196.zip) |
| stage03-full196-original-and-curated-markers.zip | 19,678,446 | `ea162611e8ed4e49451ecddd683b869729b2e9a1a19f00ad831b1d24a7e6244c` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-full196-original-and-curated-markers.zip) |
| stage03-methods-and-reports.zip | 764,657 | `b049d3c6cd9152f4557d9b33d31cb7d141de81f21ef8b700865ca022ab510b30` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-methods-and-reports.zip) |
| stage03-source-and-search-001-020.zip | 71,373,388 | `a94a6fd4b888b2c4117a668b3bac2ddc5979dc27626e6744d4c30fd02a8513ca` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-001-020.zip) |
| stage03-source-and-search-021-040.zip | 60,831,575 | `5fb70e1036630f94e3e9beb3e08ccb624ad7e2a09206bc4015128c41d97fa445` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-021-040.zip) |
| stage03-source-and-search-041-060.zip | 63,398,469 | `91e9164dd67d858e00ca8495a70e7d5044c8f20ab7e88b97346b2ab5c5e514e2` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-041-060.zip) |
| stage03-source-and-search-061-080.zip | 65,709,395 | `71b6d173c54d3456cc92dfdc939ed93012aa0da9ce037f60f76067174b4722c8` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-061-080.zip) |
| stage03-source-and-search-081-100.zip | 61,656,135 | `6faf1a5f333bac349a8d725adc318f25474170b99caafcd78069ca8bb8476d1f` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-081-100.zip) |
| stage03-source-and-search-101-120.zip | 70,679,056 | `7554e648583f28fc23891553357a35537ab4d0ed3b2fb606a8301da81ed138c8` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-101-120.zip) |
| stage03-source-and-search-121-140.zip | 71,921,743 | `ddd1f4d9db864eb252ce831d4d48cd65979a20645272e02c375af71fc0a532f7` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-121-140.zip) |
| stage03-source-and-search-141-160.zip | 70,254,486 | `a58398116a9d91bde36ff83f845063e31e9af85e3c844d43cc962a0ec6fd52e6` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-141-160.zip) |
| stage03-source-and-search-161-180.zip | 67,289,794 | `3ad4c9dea41d4be6294d9ba9eac872fa2bc082c25d23178eac05323794f457d7` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-161-180.zip) |
| stage03-source-and-search-181-196.zip | 51,816,651 | `fc51ce0ca445ae98fcd21804d31f2d9090a891ba3d3417fdc63ff352cc366e1b` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage03-hostmarkers196-v1/stage03-source-and-search-181-196.zip) |
| stage04a-full196-validated-alignments.zip | 29,506,545 | `ec6c09ffe596869497f13d69389eb3345266f4b89b1edaa6ce7608e35cbe6739` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage04a-hostalignments196-v1/stage04a-full196-validated-alignments.zip) |
| stage04a-methods-and-independent-evidence.zip | 160,437 | `6395260ce715f1385a8a5cbc0fbace34bead88605046e2580f1c109272b00707` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage04a-hostalignments196-v1/stage04a-methods-and-independent-evidence.zip) |
| stage04b-full196-native-resource-failure.zip | 144,148 | `1d19c855b3c7fcea490c0484909b40c0ce47c8c5ee99ae2afbe75c5e67645d32` | [asset](https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/stage04b-inference-resource-failure196-v1/stage04b-full196-native-resource-failure.zip) |

## Actual evidence

- `batch02/summary.json`: PASS_CURRENT_REMOTE_SHA256_AND_ALL_LOCAL_ZIP_MEMBERS.
- `batch02/file_allowlist.json`: exact local paths, SHA256, size, remote IDs/URLs/digests
  and retained publication receipt pins; no private or active input path selected.
- `batch02/zip_member_validation.jsonl`: actual per-member SHA256, size and CRC evidence.
- `batch02/remote_assets_before.json` and `remote_assets_after.json`: immutable recovery
  identities observed around verification; no assumption from an old receipt alone.
- `batch02/evidence_sha256.json`: pins the verifier's output bytes.
- `verify_yesterday_release_batch02.py`: actual read-only checker, no removal functionality.

Residual source/data/checkpoint history needs separate exact member/blob proof or a public
scientific-history archive before host wipe. Private material stays local and excluded.
The ext4 runtime image and active absolute dependencies remain protected.
