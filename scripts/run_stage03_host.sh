#!/usr/bin/env bash
# The Windows controller holds the production lock. One actual full196 search.
set -euo pipefail
cd "$(dirname "$0")/.."
ulimit -v 2097152
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
exec taskset -c 0,1 /usr/bin/time -v -o .work/stage03_host_time.txt \
    python -u scripts/stage03_markers.py
