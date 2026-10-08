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
mkdir -p .work
# Serialize project-local mount inspection/creation across independent tool probes.
exec 9>.work/tool_mount.lock
flock -x 9
if ! mountpoint -q .tools/linux; then
    mount -o loop .tools/toolchain.ext4 .tools/linux
fi
# Retain any existing project mounts. Stacked ext4 entries can follow overlapping
# preflight probes; verify every returned type rather than rejecting two lines.
test "$(findmnt -n -o FSTYPE --target "$root/.tools/linux" | sort -u)" = ext4
flock -u 9
exec 9>&-
prefix="$root/.tools/linux/${kind}_env"
test -d "$prefix/bin"
export PATH="$prefix/bin:$PATH"
export MAMBA_ROOT_PREFIX="$root/.tools/linux/mamba"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
exec "$@"
