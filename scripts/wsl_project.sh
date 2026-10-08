#!/usr/bin/env bash
# Restore the project-local tool mount for each normal WSL invocation.
set -euo pipefail
cd "$(dirname "$0")/.."
root=$(pwd -P)
kind=${1:?host or detector required}
shift
case "$kind" in host|detector) ;; *) exit 2 ;; esac
test -f .tools/toolchain.ext4
mkdir -p .tools/linux
if ! mountpoint -q .tools/linux; then
    mount -o loop .tools/toolchain.ext4 .tools/linux
fi
test "$(findmnt -n -o FSTYPE --target "$root/.tools/linux")" = ext4
prefix="$root/.tools/linux/${kind}_env"
test -d "$prefix/bin"
export PATH="$prefix/bin:$PATH"
export MAMBA_ROOT_PREFIX="$root/.tools/linux/mamba"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
exec "$@"
