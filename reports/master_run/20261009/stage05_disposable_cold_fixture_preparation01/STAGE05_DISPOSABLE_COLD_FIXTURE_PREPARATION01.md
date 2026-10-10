# Disposable cold integration in the existing paired setup owner

This packet adds a disposable fixture branch to separate copies of the
existing Windows/Linux setup owner. Every original owner function AST,
ordinary RW check, original coldv2 behavior, at-most-one-command reader and
bounded final unlock/publication handling remain unchanged. The original
coldv2 a799/d734 sources stay frozen. No second workflow owner is launched.

Source pins:

| File | SHA256 |
| --- | --- |
| stage5_setup_cold_fixture_linux.py | 853fc5e0f354a61dc7332c5c8141423d845616f3cb3a71d60a2efaaa8e80f3ca |
| stage5_setup_cold_fixture_windows.py | f03c72327fd6ea0daf6b61cad49d4f59caa3342550fede9e25e2213df9c8002a |
| test_stage5_setup_cold_fixture.py | 7bf3b3bbe1c8217b0d8ca1f769dc7a3b183961c064ef284238bb263448ae00c4 |

The new entrypoint requires `--fixture --run` and explicit published source,
controller closure, runtime and original24aa toolchain proof pins. Without
`--run`, both variants return NO_OP before any native/kernel action. The root
owner must publish/read back this packet, complete independent source review,
close the first scientific owner and reconcile any STOP before actual use.

## Scope and actual test sequence

Only a fresh direct C-work `stage5_setup_cold_fixture_...` spool is eligible.
The only writable image is that spool's new `disposable.ext4`, exactly64MiB.
The only mount target is `/var/tmp/lab_rm_cold_fixture_<owned32hexnonce>`.
Existing toolchain.ext4, Ubuntu ext4.vhdx, original toolchain prefix and
scientific output are never detached, mounted over, rewritten or deleted by
the fixture branch. Current original RW proof is observed before and after;
original runtime discovery reads the installed three roles at completion.

One original WorkflowLock owns one retained `/usr/bin/python3` WSL bootstrap,
the existing three-second C lease and the original mount/native-runner guards.
Prior scientific native launch/intent closure is rechecked. The finite25-phase
ledger accounts for every native command through the unchanged Supervisor and
Windows one-command reader. No arbitrary native argv is accepted.

The owned Linux bootstrap creates and fsyncs a fresh64MiB image, formats it
with a request-bound UUID, mounts it RW and seeds only public fixture bytes.
It creates an internal hardlink, exact relative symlink and known user xattr,
then records full bytes, inode relations, POSIX metadata, ctime/mtime and all
xattrs. It cleanly unmounts/detaches the fixture and proves exact ext4 state1,
no journal/orphan recovery, no backing-loop/mount alias and no process image/
block-device references or foreign mount namespaces. A successful `O_RDWR`
open/checked close supplies the before-guard control without a write.

The same Windows owner then retains a GENERIC_READ/FILE_SHARE_READ image
handle, denying write/delete sharing. The fixture component inherits the
reviewed offline helper's current-owner check and checked close/failed-close
retention; its new path/identity code is restricted to the fresh disposable
image. It never changes the original helper's IMAGE_PATHS or source constants.
Acquisition and every renewal check the retained final Windows path, regular
single-link type, exact64MiB size and immutable file identity.

Linux must observe a real `O_RDWR|O_NOFOLLOW` permission/sharing/busy refusal
against the same C image while that handle remains retained. No write is
called; a successful write-open vetoes the fixture. It then attaches one kernel
RO loop, mounts ext4 `ro,noload`, rejects mount aliases, checks all public
fixture bytes/links/xattrs/metadata and requires actual EROFS from a payload
write-open (again no write). RO unmount/detach and clean/process exclusion
precede Windows checked CloseHandle and a release acknowledgement. A succeeding
`O_RDWR` open/close supplies the after-guard control.

Linux mounts the fixture RW again and verifies unchanged complete content/
metadata/link relations, then cleanly unmounts/detaches it. The empty fixture
mount directory and image are retained for review; there is no fixture cleanup
or raw-image publication. Original toolchain proof must still match exactly.
Original runtime rediscovery must reproduce
`f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1`.

## Closure, bounds and limitations

The bootstrap has a900-second wall bound and the Windows owner960 seconds.
Each phase has at most60 seconds except bounded runtime rediscovery600 seconds;
native command timeouts leave closure margin. Parent and worker conservatively
book512MiB each; inherited per-process RLIMIT_AS512 and the existing sampled
child-tree RSS512 control remain distinct. Windows physical and commit require
1536MiB reserve plus1024MiB allocation; Linux requires1024MiB plus256MiB reserve;
all measured volumes retain10GiB. No scientific reserve is weakened.

The original durable STOP precedes child intent. Uncertain phase, native/client
closure, retained handle or fixture detach leaves FAILED and STOP, preserving
the fixture for root reconciliation. The same original corrected finalizer
checks original unlock and its readback receipt before clearing exact owned
STOP/PASS, and preserves its bounded publication-failure handling. Results use
a distinct disposable fixture schema with `fixture_only=true`,
`original_image_effects=false`, `actual_inventory_capture=false` and no cleanup
authority. The reused final PASS state does not describe production inventory
or capture. Actual caller exit0, complete exact ledger, Linux terminal, checked
guard release, original proof/runtime equality, original unlock and absent
publication-failure receipt must all agree.

Sixteen pure/fake tests passed: original function ASTs; CLI ordering and NOOP;
fixed path/argv/type guards; conservative budgets; actual sharing flag values
through a fake API; inherited owner/close behavior and retained failed close;
complete25-phase synthetic ledger; and count/dirty-state/argv/hash-chain/extra
command namespace rejection. Test fixtures were bounded C metadata only and
removed after verifying their resolved path remained directly within work.
No actual Linux fixture, WSL/UNC/lock/native handle/image/mount or science action
ran during preparation. A test initially expected ValueError for the unchanged
P.Fatal guard; only that test expectation was corrected before the passing run.

This prepares a real kernel/DrvFS freeze-and-restoration test. It does not
exercise installed inventory/capture, whole-image privacy, raw splitting,
GitHub asset recovery, safe extractor Linux ABI or original-prefix cold restore.
Those remain separate gates. Passing this fixture provides actual disposable
evidence for root to review before the retained original-image coldv2 session.

## Root-only entrypoint

Use the existing current controller receipt, original24aa proof and f64 runtime
only if still freshly valid. The following deliberately omits `--run`:

```powershell
& 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B `
  'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_setup_cold_fixture_windows.py' `
  --fixture --output 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_setup_cold_fixture_actual01' `
  --linux-source-sha256 853fc5e0f354a61dc7332c5c8141423d845616f3cb3a71d60a2efaaa8e80f3ca `
  --controller-receipt 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\iqtree_controller_closure_actual01\receipt.json' `
  --controller-receipt-sha256 7b6a6f78f2abfa833bc17f2767df1ae4e44ccc35de9ae35323461c5337481603 `
  --controller-observer-sha256 483b5165d015dcea659d5e850187c79ff5e99c4c0efff1c9fb108cc9a59ab78a `
  --toolchain-proof 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_setup_toolchain_actual_postiq_07\toolchain_proof.json' `
  --toolchain-proof-sha256 be4c1d96c5b4d73cfdfc334e3b72e6dbb7f641451ded01b7d2c28910eb6d7af7 `
  --runtime 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_runtime_actual_postiq_08.json' `
  --runtime-sha256 f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1
```

Root may add `--run` only after exact source publication/readback, independent
review, current resource/authority/prior closure gates and no active science.
Publish sanitized actual command/phase/closure/runtime receipts after review;
do not publish the raw disposable image or any private inventory/VM bytes.
