# Read-only retained Stage5 runtime assessment

2026-10-09. Static source/config review only: no WSL boot, mount, installation, model scan, filesystem remount, runtime experiment or biology. Eleven retained upstream source copies were rehashed against `.work/detector_review/vendor_stage05_sources/index.json`; all matched. These are installed-source evidence from2026-10-08, not current live mount verification.

## Recommendation

Keep full hash reopens for the first actual production genome. Measure hashing wall/CPU time, actual process/block I/O and memory pressure before changing them. Repeated logical reads of984MB can be page-cache reads; the source review does not establish physical disk traffic or a material performance cost. No optimization is required for scientific acceptance without measurement.

Sealing the retained `toolchain.ext4` read-only looks compatible with the selected native commands, subject to the concrete startup/config prerequisites below. It can provide a sound basis for once-per-owner-batch runtime/model verification later. Mounting read-only alone will not remove current repeated hashes: `validate_runtime`, unchanged native PADLOC helpers and independent raw model audit each perform their own reads. A later optimization must explicitly use one verified immutable manifest while preserving actual per-genome inputs/cache/raw-query verification.

## Observed writes

| Component | Source evidence | Required writable destination |
|---|---|---|
| PADLOC2 wrapper startup | `00_bin_padloc:234` unconditionally `mkdir -p ${SRC_DIR}/../data` before parsing `--data` | Default env/data must already exist and resolve correctly before sealing. Existing-directory mkdir can succeed without creating anything; verify this live. |
| PADLOC DB install/update/compile | wrapper189–225 and268–270 write DATA, concatenate profiles and move compiledDB | These options are absent from actual detector argv. Finish any such preparation before sealing; do not invoke them during a sealed batch. |
| PADLOC native HMMER/classification | wrapper392–436 uses selected outdir/domtbl and readonlyDB; `01_bin_padloc.R:874,877` writes CSV/GFF to OUTPUT_DIR | Per-genome G native attempt/outdir. No model/library write found in reviewed native R. |
| MacSyFinder2.1.4 | `15_scripts_macsyfinder.py:526,1150,1167,1275–1350` writes working-dir config/log/results; `13_macsypy_profile.py:174–194` writes HMM reports/errors there | Explicit G `--out-dir`. Native profile objects/results cache in memory or job-output previous-run files; no model compilation/hmmpress path found in reviewed code. |
| MacSy sequence index | `Indexes_installed_source.txt:91–136` builds `<index-dir>/<faa>.idx`, requiring writable directory | Explicit G `--index-dir` already supplied by retained native commands. Default input-directory writes are avoided by this option. |
| DefenseFinder3 post-treatment | `06_defense_finder_posttreat___init__.py::run`, df_genes/systems/hmmer copies | Passed G output directory. df_genes can rewrite/remove its intermediate tables inside that outdir; raw families remain separate. |
| Python imports | Native child environment already has `PYTHONDONTWRITEBYTECODE=1` | Start the top-level retained interpreter with `-B` or the same environment too; a sealed mount must not depend on creating pyc files. |
| Temporary runtime files | R/Python/system runtime behavior was not executed here | Explicit writable job TMPDIR outside the sealed runtime. Keep outputs, logs, caches and owner leases outside it. |

The actual selected commands invoke original PADLOC, HMMER, MacSyFinder and unmodified DefenseFinder post-treatment. They do not run package/model installation, model updates, PADLOC DB compilation, nucleotide gene prediction, or a generic DefenseFinder CLI updater. No detector classification code is replaced for this assessment.

## Read dependencies and proof required for future reuse

MacSy `Config` reads system/env configuration, optional environment override, `~/.macsyfinder/macsyfinder.conf`, jobcwd config, previous-run config and selected model configuration (`12_macsypy_config.py:175–239`). These reads do not require a writable runtime, but are scientific dependencies even without read-only optimization. The new draft now pins their actual presence/bytes/resolved paths and HOME/VIRTUAL_ENV/MACSY_CONF/PYTHONPATH/PYTHONHOME values in its runtime candidate, rechecks task cwd config against the independent bundle receipt, and binds the same environment to parent scope and native children. Discovery on actual Linux remains NOT_RUN. The native task/seed/effective configs and selected model files are retained; the independent raw checker compares all effective config values except output/index/previous-run locations. Actual MacSy2.1.4 rejects combining `--cfg-file` with `--previous-run`, so the adapter preserves native previous-run behavior. R startup and shared-library/temp behavior also remain a live integration question.

The existing `scripts/wsl_project.sh` mounts `toolchain.ext4` with `mount -o loop` when absent and only verifies ext4 type. It does not establish read-only mode, backing-device/UUID identity or absence of a writable alias. A prospective sealed mode must not silently accept this existing weaker mount assertion.

For one batch, independently establish actual backing-image identity, loop/block source and major/minor, filesystem UUID, mount identity/options `ro`, all resolved runtime/model paths within that sealed mount, and no alternative writable mount/backing writer. Verify the complete pinned scientific runtime/model manifest after sealing and bind that manifest and mount identity to the actual Windows owner batch. UUID, size, pathname and mtimes alone do not prove content immutability. Any unmount/remount, unseal, source substitution or writer invalidates reuse and requires new full verification.

Keep current full reopens if these facts cannot be established cheaply and reliably. Preserve per-genome source/FAA/GFF/config/cache/raw evidence hashes even in a future sealed mode. An optimization must not weaken query-completion evidence, boundary routing, upstream native classification, failed/not-run states, or actual process closure.
