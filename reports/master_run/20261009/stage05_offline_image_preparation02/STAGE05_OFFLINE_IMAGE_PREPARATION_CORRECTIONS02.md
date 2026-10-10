# Frozen corrected offline-image preparation

Actual installed-runtime inventory/capture, Windows image-handle acquisition, image split, upload, cold restore and eviction are NOT_RUN. Literal splitting of BOTH original toolchain.ext4 and Ubuntu ext4.vhdx remains pending. No current WSL, scientific source, original image, original lock or Git ref was changed here.

The historical route `STAGE05_OFFLINE_IMAGE_SPLIT_EXISTING_OWNER_ROUTE01.md` remains frozen. Its original source pins are preparation history, not the current adoption candidate. Independent review `stage5_frozen_capture_helpers_independent_review01.json`e3e2f5dfe5e612315e9ccc3f194375768334103f83a6e1c1a5b77d335c922b31 blocked original raw helper4f5caa4c and capture worker8b7ad2be for actual adoption. The review also found a proof-owner numeric-type gap inherited from inventory v2, despite its earlier source-only review PASS. No original revision was adopted or executed on production Linux/images.

The four issues were: audit-copy image identity accepted equal-valued numeric floats/bools; failed owned CloseHandle during `__enter__` could discard retained-handle evidence; proof Windows-owner PID equality accepted a float against an integer lease PID; capture control preflight preceded its worker deadline/admission/terminal coverage. Originals and their tests/reviews remain unchanged.

Separate corrected candidates are now frozen:

| Source | SHA256 | Authored validation |
|---|---|---|
| stage5_offline_image_read_parts_v2.py | f0bf9fe02597cdce26e337d1c40fda45763b5225ea9f240e1962be18acacc151 | Nine pure tests PASS |
| test_stage5_offline_image_read_parts_v2.py | 29d2b820a2abab8caa6f6d223a34ef99bfb5b4827d2c9e99c6255679eed53bfd | No actual image/handle/native action |
| stage5_runtime_inventory_entry_v3.py | dbfd181eaccd2db37857409c48a6ba6964c1db5154fd4d7e055058d18802e60e | Seven synthetic tests PASS |
| test_stage5_runtime_inventory_entry_v3.py | 3fb848814c625140278922df22a8c4b1034a428c78bd4ae2281224510ca32471 | Strict proof owner keys/types and existing v2 guards |
| stage5_runtime_capture_entry_v2.py | e5f50eb7beb9297dce8e6a9e160ea1aef564bf0f08379dc73b839210f182bdf5 | Eight synthetic/mocked tests PASS |
| test_stage5_runtime_capture_entry_v2.py | d97729d4f73bb126d836a4db34f781782204f93fbb1b8ed4cd46cdf48afb017c | Includes preflight capacity-failure/timeout terminal coverage |

Independent peer review of these corrected revisions is PENDING. They are not authorized as an actual cold owner merely because24 authored tests passed. Capturing Windows default no-op output is not production Linux execution. The test faults mock signals/limits/terminal writes; they do not set real process address limits or touch image handles.

Raw helper v2 applies exact numeric types to both image identity copies. It clears a retained handle only after actual successful CloseHandle. If closure fails, `ImageHandleClosureFailure.retained_image_lease` strongly retains the lease/handle for the existing owner's finalizer; that owner must retain STOP/evidence and must not emit guard-release acknowledgment until closure is actually proven. The function remains callable only by the same original Windows owner; real cross-DrvFS writer exclusion is not tested.

Inventory v3 adds exact keys/types to `proof.windows_owner`; the remaining inventory logic is the frozen v2 worker. It still depends on the existing outer owner for full-launch deadline/resource/lifecycle coverage, including its initial bounded control preflight. The future cold-only Linux bootstrap must admit and enforce the inherited finite per-process allocation before invoking this worker. The shared supervisor does not itself create a kernel address limit merely because its receipt describes an inherited limit.

Capture v2 uses exact inventory v3 source/bindings, covers source/control preflight with the worker alarm/result/try boundary, admits between bounded reads, and imposes/readbacks a512MiB per-process `RLIMIT_AS` before large control allocations. It does not raise an existing smaller inherited soft/hard limit. It clears its duplicate raw controls before the existing capture function rereads them. Actual kernel limit application is NOT_RUN here. The existing Windows/Linux owner still must cover complete process startup, supervision, final terminal-write/exit, descendant closure, actual backing writer exclusion and cleanup. The worker does not create that owner.

Current future inner command filenames become `stage5_runtime_inventory_entry_v3.py` and `stage5_runtime_capture_entry_v2.py`; the actual cold proof must pin the exact current inventory SHA and, for capture, the exact capture-entry SHA above. Current future Windows callable helper becomes `stage5_offline_image_read_parts_v2.py`. All other current logical capture, original canonical part names, independent full payload verifier, transport-alias source and safe extractor remain unchanged. No source/pin update was made to the scientific runner or current setup owner.

The minimum remaining implementation is still one cold-only branch in the EXISTING paired setup owner: same uninterrupted original WorkflowLock/fresh lease; actual original native/root/group/client closure; retained Linux existing guards; clean detach; actual Windows guard acquisition; actual read-only loop/mount/alias proof; exactly one supervised worker; RO detach; proven guard release; RW restoration; exact ordered per-phase utility/client closure; cold-only finite bounds; STOP retained if restoration or handle closure is unproven. Ordinary RW toolchain predicates and normal at-most-one-command checks stay unchanged. This branch and its real bounded cross-DrvFS fixture are NOT_IMPLEMENTED/NOT_RUN.

Whole-file public review still cannot be inferred from token regexes, successful logical-root inventory, or a readable VM. If Ubuntu/home/shadow/key/deleted/free-space content makes an original image unfit for public storage, a reviewed cold COPY or a fresh public reconstruction may be a later route. Sanitizing/rebuilding creates a new derivative image: record exact original and derivative identity/SHA, transformations, public-review basis, notices and restored public project coverage. Never describe derivative recovery as exact original-image preservation. Never upload original credentials or private state. Primary logical installed roles plus OS bootstrap may satisfy portable project recovery, but must not be reported as literal BOTH-images split.

First closed scientific genome remains the immediate priority. The root owner may publish this source/preparation packet incrementally, then revisit actual cold integration after that scientific checkpoint. No actual split, recovery, cleanup or wipe acceptance is claimed by this packet.
