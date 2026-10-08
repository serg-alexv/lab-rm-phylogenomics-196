# Native IQ-TREE option incompatibility

The full196 host alignment and all three frozen sensitivity concatenations passed the separate source/format/partition checker. Their verified portable release is stage04a-hostalignments196-v1.

After RAM headroom recovered, the unchanged controller resumed past both completed alignment phases. At2026-10-08T15:30:30UTC, actual IQ-TREE3.1.4 childPID950 rejected --mem1536M combined with -p. Native exit2 occurred after0.035352s; stderr: `-mem option does not work with partition models yet`. No native host.log/tree/checkpoint was produced. The Linux producer phase exited1 and the original controller stopped with honest incomplete status. Exact command/input/code/resource identities, stdout/stderr and native exit receipts are preserved here.

The individual flags are documented in the installed help. The [official memory-mode release note](https://www.iqtree.org/release/v1.5.1/) states its partition incompatibility; the actual3.1.4 execution is the version-specific evidence here. The [official partition documentation](https://www.iqtree.org/doc/Complex-Models) supports the selected edge-proportional model.

Repair is being prepared in a new inference namespace. It retains all original alignment/source proofs and freezes the new adapter before topology; only the unsupported CLI memory flag is removed. A native child helper will enforce soft and hard1536MiB address-space limits, with two threads/cores under the existing2GiB outer limit. This is an external cap, not a claim of equivalent IQ-TREE memory optimization. Actual inference/final validation must still execute; no topology, supports, detector result or completed Stage4 is claimed by the repair design. Existing original scripts/state/failures remain preserved.
