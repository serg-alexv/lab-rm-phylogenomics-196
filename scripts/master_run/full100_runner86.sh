#!/usr/bin/env bash
set -euo pipefail
set -C
cd '/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
receipt='reports/stage01/local_full100_20261010/attempt01'
exec > full_run.log 2>&1
boot=$(cat /proc/sys/kernel/random/boot_id)
ticks=$(awk '{print $22}' "/proc/$$/stat")
printf '{"state":"RUNNING","boot_id":"%s","wrapper_pid":%s,"wrapper_start_ticks":%s,"started_utc":"%s","command":"PILOT_ONLY=0 bash run_pipeline.sh"}\n' "$boot" "$$" "$ticks" "$(date -u +%FT%TZ)" > "$receipt/linux_launch.json"
export PILOT_ONLY=0
/bin/bash run_pipeline.sh &
pipeline_pid=$!
printf '%s\n' "$pipeline_pid" > "$receipt/pipeline.pid"
pipeline_ticks=null
if [[ -r "/proc/$pipeline_pid/stat" ]]; then pipeline_ticks=$(awk '{print $22}' "/proc/$pipeline_pid/stat"); fi
printf '{"boot_id":"%s","pid":%s,"start_ticks":%s,"parent_pid":%s}\n' "$boot" "$pipeline_pid" "$pipeline_ticks" "$$" > "$receipt/pipeline_identity.json"
if wait "$pipeline_pid"; then result=0; else result=$?; fi
printf '{"state":"EXITED","exit_code":%s,"boot_id":"%s","pipeline_pid":%s,"pipeline_start_ticks":%s,"wrapper_pid":%s,"wrapper_start_ticks":%s,"finished_utc":"%s"}\n' "$result" "$boot" "$pipeline_pid" "$pipeline_ticks" "$$" "$ticks" "$(date -u +%FT%TZ)" > "$receipt/linux_terminal.json"
exit "$result"
