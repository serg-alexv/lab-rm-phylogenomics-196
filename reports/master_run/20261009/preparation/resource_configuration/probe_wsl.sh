#!/usr/bin/env bash
set -euo pipefail
historical=/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196
printf 'UTC '; date -u +%FT%TZ
uname -a
printf '\nROOT FILESYSTEM\n'; df -B1 -T /
printf '\nMEMORY\n'; free -b
printf '\nCPUS\n'; nproc
printf '\nPREEXISTING SCIENTIFIC PROCESSES\n'
ps -eo pid,ppid,lstart,comm | awk 'NR==1 || /iqtree|padloc|defense|hmmscan|hmmsearch|Rscript/'
mkdir -p "$historical/.tools/linux"
exec 9>"$historical/.work/tool_mount.lock"
flock -x 9
if ! mountpoint -q "$historical/.tools/linux"; then
  mount -o loop "$historical/.tools/toolchain.ext4" "$historical/.tools/linux"
fi
findmnt --target "$historical/.tools/linux"
flock -u 9
exec 9>&-
printf '\nTOOLCHAIN FILESYSTEM\n'; df -B1 -T "$historical/.tools/linux"
prefix="$historical/.tools/linux/detector_env"
export PATH="$prefix/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
printf '\nEXECUTABLE PATHS\n'
for exe in python Rscript hmmsearch hmmscan padloc defense-finder macsyfinder; do command -v "$exe" || true; done
printf '\nPYTHON PACKAGE VERSIONS\n'
timeout 30 "$prefix/bin/python" -c "import sys,importlib.metadata as m,json;print(sys.version);print(json.dumps({d.metadata['Name']:d.version for d in m.distributions() if any(x in d.metadata['Name'].lower() for x in ['defense','macsy','pyhmmer','pyrodigal'])}))"
printf '\nR VERSION\n'; timeout 30 "$prefix/bin/Rscript" --version
printf '\nHMMER VERSION\n'; timeout 30 "$prefix/bin/hmmsearch" -h | sed -n '1,8p'
printf '\nPADLOC VERSION\n'; timeout 45 "$prefix/bin/padloc" --version
printf '\nDEFENSEFINDER CLI (version established by installed distribution metadata above)\n'; timeout 30 "$prefix/bin/defense-finder" --help | sed -n '1,16p'
printf '\nMODEL/DB PATHS\n'
find "$historical/.tools/linux" -maxdepth 3 -type d \( -iname '*padloc*' -o -iname '*defense*' -o -iname '*models*' \) -print
printf '\nFINAL MEMORY\n'; free -b
printf '\nDONE '; date -u +%FT%TZ
