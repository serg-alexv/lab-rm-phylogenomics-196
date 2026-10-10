# G08 six-pin refresh and checked original unlock

This small C-only preparer consumes the future exact output of frozen recipe
`prepare_stage5_gdrive_postfallback_source.py` (`d8fb432cceb2d09e636d154de48b9f18b54a956ab8f2c722b5963f4c21724042`).
That recipe preserves G baseline `stage5_gdrive_view_postprofile.py`
(`1ec2380d218128e325954552057ed1215268297862e2910550b2eb7c46a112e9`)
and refreshes exactly five actual toolchain08 receipts and its independent peer.
Neither future source hash nor new boot ID is guessed.

The new preparer verifies the input is byte-for-byte exactly the original
six-pin transformation. It adds `finish_after_unlock` from the independently
reviewed profile source `49596d3e9c0ef684978d0cbb05bc57d97b100f08ab77a7a4ece598abc2221299`,
with only G pending/PASS/schema/message substitutions and equivalent existing
path-SHA calls. The Windows helper now leaves success pending until retained
client handle close, explicit original OS byte unlock, durable unlock receipt
and exact owned STOP clear complete. Every existing non-Windows function AST
and every fresh pin remain unchanged. Original Linux session-parent/mount,
single-command, full G-control/empty-underlay and current toolchain gates remain.

The retained client terminal is still verified by the original failed-scope
finalizer. Its handle closes before the new finalizer; a close or log readback
failure blocks STOP clear and PASS. The finalizer releases the original lock,
persists and reads back the unlock receipt, then clears only the exact owned
STOP when native closure and handle/log finalizers are proven. A final-result
write failure stays FAILED with a bounded distinct publication-failure receipt;
it retains already proven closure/unlock facts instead of fabricating PASS or
reclassifying closed processes as unknown.

The default invocation is NOOP and reads no inputs. After root obtains and
publishes actual toolchain08/peer, the two C-only source preparations are:

```powershell
python -B work/prepare_stage5_gdrive_postfallback_source.py --prepare --proof-sha256 <actual08-proof-sha> --review-sha256 <actual08-peer-sha>
python -B work/prepare_stage5_gdrive_checked_unlock_source.py --prepare --input-sha256 <exact-derived-pin-only-source-sha>
```

The second command creates only the fresh source
`work/stage5_gdrive_view_postfallback_checked_unlock.py`, with fsync and byte
readback. Before writing it, the preparer reopens all six actual receipt files,
executes only the existing read-only `fresh_toolchain_gate`, requires a new boot,
and rechecks all source/receipt bytes. Existing output is never overwritten.
Independent review of the actual derived source and root GitHub publication
remain prerequisites for any later root-owned G invocation. This preparer
itself invokes no G helper, WSL, native process, workflow lock or host effect.

Nine pure/disposable-C tests pass: default NOOP without reads, exact six pins,
unchanged non-Windows ASTs, altered source/baseline/profile/pin-gap rejection,
handle-close ordering, pending success, unlock/receipt/unclosed vetoes, bounded
publication failure facts and generated default NOOP. Synthetic pins occur only
inside tests. Actual08-derived source creation and G invocation are NOT_RUN.
