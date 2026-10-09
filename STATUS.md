# Current execution status

Updated 2026-10-09T00:12:50.160292+00:00. Full approved196 production cohort; no pilot.

IQ-TREE primary196 exited1 at2026-10-08T23:30:02.6498313Z, independently observed for PID29132 and exact creation token. Native CPU16131.484375s. Original controller outcome and final JobObject closure remain UNKNOWN; ordinary exit/tree-complete receipts are absent. Model cache and all original outputs are preserved. No termination cause is established. V9 recovery preparation requires an actual one-shot Scheduler lifetime fixture and hash-bound parent acceptance before production. Stages05–07 remain NOT_RUN.

| Stage | Execution | Validation | Publication |
|---|---|---|---|
| 0_environment | COMPLETED | PASS_ACQUISITION_PREFLIGHT | UPLOAD_VERIFIED |
| 1_panel_freeze | COMPLETED | PASS_APPROVED_PANEL_FREEZE | UPLOAD_VERIFIED |
| 2_sequences | COMPLETED | PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS | UPLOAD_VERIFIED |
| 3_markers | COMPLETED | PASS_HOST_MARKER_INVENTORY | UPLOAD_VERIFIED |
| 4_phylogeny | FAILED_INCOMPLETE_NATIVE_EXIT1 | PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE | STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING |
| 5_rm_inventory | NOT_RUN | NOT_RUN | NOT_RUN |
| 6_figure | NOT_RUN | NOT_RUN | NOT_RUN |
| 7_final_review | NOT_RUN | NOT_RUN | NOT_RUN |

See reports/stage04/recovery_v9/failed_attempt_reconciliation_v1.json. Private session traces are excluded.

Recovery update 2026-10-09T01:00:01.702269+00:00: V9 preserved; parent decision REPAIR_REQUIRED. New V10 candidate repairs and28 guards/actual overlapping-stdio fixture completed. Required120-second original-CLI-exit lifetime proof and final hash-bound parent acceptance remain pending. Production remains FAILED/INCOMPLETE;05–07 NOT_RUN.
