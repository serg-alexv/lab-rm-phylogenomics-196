# Pilot result: stopped on the first IQ-TREE error

The exact requested script ran locally on 2026-10-10 at 07:04:09 UTC and stopped at 07:04:36 UTC. MAFFT completed 5-FTHF_cyc-lig. The alignment has 189 unique approved taxa, equal sequence lengths, and preserves every input sequence after gap removal. IQ-TREE then exited 2 with:

    Invalid -mem option. Example: -mem 200M, -mem 10G

There are zero completed gene trees. ASTRAL did not run. `pilot_output/species_tree.newick` does not exist. The full pipeline was not started. The original workflow lock handle was released; no rerun has occurred.

The unchanged active run_pipeline.sh and a preserved original copy have SHA-256 12f01df5050679c27d8acde1607d53753042e5946a3a958613d89e7479ad33c0. A separate proposed script, run_pipeline.corrected_mem.sh, changes only `-mem 3000` to `-mem 3000M` in the pilot and full IQ-TREE commands; `bash -n` passes. This candidate has not replaced the active script and has not run.

The user's latest ask-before-overwrite instruction requires confirmation to replace the active script and rerun the pilot, which would regenerate the first alignment. Preserve all failed-run logs and original bytes. Confirmation of this correction would authorize only the pilot; full execution still requires a separate decision after pilot completion.

Inputs: five validated existing core markers from the 100-marker, 196-assembly master panel, not whole genomes. Four have 196 taxa; 5-FTHF_cyc-lig has 189. All 973 input protein sequences exactly match accepted manifest hashes and lengths. These pilot results do not change the accepted Stage4 tree or create R-M detector/curation results.
