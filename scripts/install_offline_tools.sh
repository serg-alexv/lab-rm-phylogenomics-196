#!/usr/bin/env bash
# Project-contained Linux filesystem; source packages remain unchanged on WD.
set -euo pipefail
cd "$(dirname "$0")/.."
root=$(pwd -P)
kind=${1:?host or detector required}
case "$kind" in host|detector) ;; *) exit 2 ;; esac
mkdir -p .tools/linux
if ! test -e .tools/toolchain.ext4; then
    truncate -s 8G .tools/toolchain.ext4
    /usr/sbin/mkfs.ext4 -q -F .tools/toolchain.ext4
fi
if ! mountpoint -q .tools/linux; then
    mount -o loop .tools/toolchain.ext4 .tools/linux
fi
test "$(findmnt -n -o FSTYPE --target "$root/.tools/linux")" = ext4
python3 - "$kind" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
kind=sys.argv[1];root=Path.cwd()
j=json.loads((root/('.work/'+kind+'_solve.json')).read_text(encoding='utf-8-sig'))
assert j['success']
cache=root/'.tools/linux/mamba/pkgs';cache.mkdir(parents=True,exist_ok=True)
for p in j['actions']['LINK']:
    source=root/'.tools/mamba/pkgs'/p['fn']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==p['sha256'],p['fn']
    dest=cache/p['fn']
    if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest()!=p['sha256']:
        shutil.copyfile(source,dest)
print('Pinned archive SHA256 audit and native cache staging PASS',kind,len(j['actions']['LINK']))
PY
export MAMBA_ROOT_PREFIX="$root/.tools/linux/mamba"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
# Affinity also bounds extraction/post-link CPU use; no unrelated process changes.
taskset -c 0,1 .tools/micromamba create -y --offline \
    -p "$root/.tools/linux/${kind}_env" -f ".work/${kind}_explicit.txt"
.tools/micromamba list -p "$root/.tools/linux/${kind}_env" --explicit > ".work/${kind}_installed_explicit.txt"
