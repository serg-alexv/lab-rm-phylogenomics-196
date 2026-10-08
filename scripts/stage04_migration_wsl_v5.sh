#!/usr/bin/env bash
# New explicit migration entry. Historical wrapper and tool prefix stay intact.
set -euo pipefail
historical=/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196
data='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
self="$historical/.private_run/migration_runtime_v5/stage04_migration_wsl_v5.sh"
test "$(readlink -f "$0")" = "$self"
if test "${1:-}" != --enter-data; then
    test "$#" -gt 0
    # This is a mount-setup lock, distinct from the Windows production lock.
    exec 8>"$historical/.work/migration_mount_v5.lock"
    flock -x 8
    if ! mountpoint -q /mnt/g; then
        mkdir -p /mnt/g
        mount -t drvfs 'G:' /mnt/g
    fi
    test "$(findmnt -n -o SOURCE --mountpoint /mnt/g)" = 'G:'
    test "$(findmnt -n -o FSTYPE --mountpoint /mnt/g)" = '9p'
    options=$(findmnt -n -o OPTIONS --mountpoint /mnt/g)
    case "$options" in *'aname=drvfs;path=G:;'*) ;; *) echo 'Wrong G mount identity' >&2; exit 2 ;; esac
    test "$(readlink -f "$data")" = "$data"
    cmp -s "$self" "$data/scripts/stage04_migration_wsl_v5.sh"
    test "$(sha256sum "$historical/scripts/wsl_project.sh" | cut -d' ' -f1)" = 459c33d5edd186836ba8079ee6204221b79cfe70160f3f5ec7f9503286f28d12
    flock -u 8
    exec 8>&-
    exec bash "$historical/scripts/wsl_project.sh" host bash "$self" --enter-data "$@"
fi
shift
test "$#" -gt 0
test "$(findmnt -n -o SOURCE --mountpoint /mnt/g)" = 'G:'
test "$(readlink -f "$data")" = "$data"
cmp -s "$self" "$data/scripts/stage04_migration_wsl_v5.sh"
test -x "$historical/.tools/linux/host_env/bin/python"
test "$(findmnt -n -o FSTYPE --target "$historical/.tools/linux" | sort -u)" = ext4
cd "$data"
exec "$@"
