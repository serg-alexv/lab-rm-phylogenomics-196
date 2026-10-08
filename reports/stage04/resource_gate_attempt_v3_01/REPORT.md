# Actual prelaunch RAM gate rejection

The reviewed resumed inference was published in commit371f642. Windows controllerPID17688 exited1 at2026-10-08T15:58:08UTC on its resource gate. It created neither lifecycle state nor an inference freeze/native IQ-TREE attempt. The exact failure and current source/config hashes are preserved. All original validated/published alignments remain intact.

The preflight requires current Windows and Linux available RAM each greater than2147483648bytes. Rejected snapshots were not persisted by that controller; exact values at that instant are unavailable. The accompanying command log and follow-up JSON contain fresh actual measurements, labeled separately. An earlier follow-up at15:58:54UTC measured Windows2077696000bytes and Linux7200763904bytes; Windows was69987648bytes below the gate.

No unrelated processes were stopped, memory limits lowered, WSL/Windows restarted or biological scope changed. Natural resource recovery can permit the unchanged resume command in INFERENCE_V3.md. Until then, complete phylogeny validation, both production R-M detectors and the figure remain unexecuted dependent work.
