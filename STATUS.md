# Current execution status

## Master run — 2026-10-09T18:26:52.287162+00:00

**STAGE04 RUNNING.** The one partitioned native IQ-TREE 3.1.4 job launched at
2026-10-09T16:29:47.628911+00:00 uses all196 approved genomes and the accepted100-marker,
17,456-column Stage4a alignment. Model selection and initial tree searches have
finished; candidate-tree optimization is running. This observation is not final
tree acceptance. Actual retained process/job measurements and captured command,
admission, cache import and log prefixes are in `reports/master_run/20261009/snapshots/20261009T182652Z`.

This is the master continuation. GitHub is the primary project storage and sole
source of truth; all reproducibility artifacts must be recoverable here before
the WD host is wiped. A local swarm is inventorying yesterday's project files.
Nothing has been purged. Active files, accepted inputs and pinned toolchain remain
in place until verified remote recovery permits cleanup. See
`docs/master_run/PLAN_20261009.md` and `status/master_run_20261009.json`.

Stages5–7 remain scientifically NOT_RUN. Prepared code and synthetic tests do not
constitute detector results or an accepted figure. Historical unknown outcomes
remain unchanged. Automatic scheduled continuation remains disabled.

## Direct user continuation — 2026-10-09T16:21:45.730229+00:00

**ACTIVE_DIRECT_USER_CONTINUATION.** Bootstrap and accepted Stage4a inputs independently validated; bounded resource admission is being prepared for one new atomic native inference attempt. No new biological job has started. Stage4 remains incomplete and Stages5–7 NOT_RUN. Historical tasks remain disabled and historical unknown exits remain preserved. See `reports/stage04/atomic_resume_20261009/REPORT.md` and `status/atomic_continuation_20261009.json`.

## Direct user halt — 2026-10-09T10:13:27.758472+00:00

**HALTED_BY_USER. Automatic continuation is disabled.** The external CLI was stopped, all18 LAB scheduled tasks disabled, and temporary leftovers cleaned. Recovery evidence publication had completed at `c49c9efeaa4566d8166e889150966e774b315d11` before the halt. Stage04 remains scientifically incomplete; Stages05–07 remain NOT_RUN. Resume requires a new direct user instruction. See `status/run_control.json` and `reports/storage/20261009_user_halt_cleanup.json`.

Reconciliation proposal prepared 2026-10-09T09:17:39.098978+00:00. Evidence as of 2026-10-09T09:00:54.2368705Z. Full approved196; no pilot.

INTERRUPTED_OUTCOME_UNKNOWN: V10 primary196; scientific Stage04 INCOMPLETE. Reconciliation evidence as of 2026-10-09T09:00:54.2368705Z. Original native26452/creation134359866154140144 and controller2968/creation134359865859802366 actual exits, old-job accounting and closure remain UNKNOWN. Power-off request, logoff and sleep/resume events are recorded; specific process cause and original SessionIDs are not established. Scheduler0x40010004 is not a native exit code. See reports/stage04/recovery_v11/negative_reconciliation_proposal_v1.json. No retry adopted or launched. Fresh held-lock inventory/resources, latest cache scope and hash-bound parent acceptance remain required. V6 exit1 and historical UNKNOWN closures remain preserved; Stage05-07 NOT_RUN and full Stage04 validation/verified Release pending.

Historical as-of observation preserved: V10_ACTUAL_NATIVE_RUNNING_INCOMPLETE: primary196. Observation as of 2026-10-09T06:54:42.782077+00:00; native PID26452, creation FILETIME134359866154140144. Actual Scheduler-bound controller and native JobObject measurements are in reports/stage04/recovery_v10/progress.json. V6 exit1 and UNKNOWN old controller/job closure remain preserved. Scientific acceptance and verified full Stage04 Release remain pending.

| stage | execution | validation | publication | observation_as_of_utc | native_pid | native_creation_filetime |
|---|---|---|---|---|---|---|
| 0_environment | COMPLETED | PASS_ACQUISITION_PREFLIGHT | UPLOAD_VERIFIED |  |  |  |
| 1_panel_freeze | COMPLETED | PASS_APPROVED_PANEL_FREEZE | UPLOAD_VERIFIED |  |  |  |
| 2_sequences | COMPLETED | PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS | UPLOAD_VERIFIED |  |  |  |
| 3_markers | COMPLETED | PASS_HOST_MARKER_INVENTORY | UPLOAD_VERIFIED |  |  |  |
| 4_phylogeny | INTERRUPTED_OUTCOME_UNKNOWN | PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE | STAGE04A_STAGE04B_STAGE04C_FAILURE_UPLOAD_VERIFIED_FULL_STAGE04_PENDING | 2026-10-09T09:00:54.2368705Z |  |  |
| 5_rm_inventory | NOT_RUN | NOT_RUN | NOT_RUN |  |  |  |
| 6_figure | NOT_RUN | NOT_RUN | NOT_RUN |  |  |  |
| 7_final_review | NOT_RUN | NOT_RUN | NOT_RUN |  |  |  |
