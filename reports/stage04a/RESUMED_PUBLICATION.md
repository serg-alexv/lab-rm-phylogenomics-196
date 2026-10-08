# Stage04a publication receipt recovery

The original publisher verified both ZIPs and sidecars, then its final receipt commit failed because it expected a stage-specific commands file that had not been configured. Actual command records had appended to the existing mutable Stage00 log, which is preserved locally unchanged. This report selects only Stage04a command records; no private session events are used.

This new resumed task configures a separate Stage04a command log and rechecks the unchanged immutable plan/tag/assets before committing the verified receipt. No ZIP, scientific payload, alignment, filter or historical commit is rewritten. Whole Stage4 phylogeny remains incomplete.
