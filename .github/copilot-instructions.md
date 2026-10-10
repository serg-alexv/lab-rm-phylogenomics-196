# Local phylogenomics execution and validation

The latest user instruction is five-marker pilot first, then explicit user approval
before the full 100-marker run. Never start a second runner or replace its active
script. All scientific execution stays local in Ubuntu WSL. Do not overwrite,
move, or delete existing scientific artifacts without the user's approval.

## 10. Post-execution validation loop

Immediately after ASTRAL, run scripts/validate_pipeline.py with explicit
--mode pilot or --mode full and a fresh --report-dir. The prepared Bash integration
uses reports/stage01/validation_pilot and reports/stage01/validation_full.
The validator prints GLOBAL_PIPELINE_STATUS: PASS or FAIL, prints each failing
check, writes validation_summary.tsv, and exits nonzero on failure. set -euo
pipefail stops the Bash pipeline before decoration/upload if validation fails.

Compare every gene tree with its own FASTA taxa and the ASTRAL tree with the union
of selected marker taxa. Pilot mode selects the first five sorted FASTAs; full
mode requires exactly 100 markers and all 196 approved accessions. Never infer
mode from directory existence: both output directories are created in either mode.
Record unlabeled IQ-TREE branches explicitly without imputing support. Preserve
raw ASTRAL annotations and a separate validated numeric q1-frequency tree.
Use isolated fixture copies for corruption tests; never truncate master results.

The iTOL uploader requires the full validation receipt and matching source/derived
tree SHA256 values. Credentials remain in /mnt/c/itol.api-key.txt and must never
enter Git, archives, stdout, or logs. Publish completed results with checksums and
independently read back the remote bytes. Never force-push.
