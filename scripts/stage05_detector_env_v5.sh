#!/usr/bin/env bash
# Enter only after the exact reviewed C bootstrap has mounted G and the image.
set -euo pipefail
historical=/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196
data='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
test "$#" -gt 0
test "$(readlink -f "$PWD")" = "$data"
test "$(findmnt -n -o SOURCE --mountpoint /mnt/g)" = 'G:'
test "$(findmnt -n -o FSTYPE --target "$historical/.tools/linux" | sort -u)" = ext4
prefix="$historical/.tools/linux/detector_env"
test -x "$prefix/bin/Rscript"
test -x "$prefix/bin/python"
export PATH="$prefix/bin:$PATH"
export MAMBA_ROOT_PREFIX="$historical/.tools/linux/mamba"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
exec "$@"
