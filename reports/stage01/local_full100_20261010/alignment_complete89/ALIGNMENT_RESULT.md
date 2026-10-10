# Full 100-marker alignment acceptance

Independent local WSL validation passed at 2026-10-10T10:16:26.894988+00:00 with native exit 0. It checked all 100 selected loci and 19,359 input records, yielding the exact approved union of 196 accessions. Aligned lengths range from 39 to 557 columns, totaling 20,957 columns across loci; this sum is not a claim that a new concatenated inference was run.

The finalized audit source is `audit_full100_alignments.py`; execution arguments, source hash and receipt hashes are recorded in `validation/receipt.json`. `validation/per_marker.tsv` contains all input and alignment hashes before and after validation. Each input SHA256 matches the pinned preparation manifest. Sequence comparison concatenates FASTA lines after whitespace removal, uppercases both sides, and removes only `-` alignment gaps before exact comparison. Headers are checked by accession identifier (the first FASTA header token).

Native phase completion is established by the unchanged script's `set -euo pipefail`, completion of its sequential 100-input MAFFT loop, and the observed same-owner transition to IQ-TREE. The first IQ-TREE process is PID 15472, parent 4023, start ticks 1922262, on boot `8cca020a-71b2-4163-92dc-6087df12dd45`. This proves alignment-phase completion, not full-run terminal closure. The final MAFFT log is stable. IQ-TREE log snapshots are explicitly in-progress evidence and do not establish marker completion.

Published files are allowlisted: the 100 validated alignments, stable MAFFT log, phase/progress snapshots, audit source and final receipts, and the previous publication's independent remote-byte verification. Active IQ-TREE model/checkpoint files are excluded. The initial unbound integrity receipt is retained separately as preliminary evidence; the final manifest-bound receipt is authoritative. No scientific inputs or outputs were changed by validation.

This is computational integrity evidence, not independent proof of orthology, biological function, or final species-tree reliability. The full 100-marker tree inference and ASTRAL consolidation remain in progress/not yet run, respectively.
