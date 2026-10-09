# WD resource configuration

Applied and verified on 9 October 2026. WD has 15.75 GiB usable physical RAM and 16 logical processors. Windows pagefile management remains automatic.

## Changes applied

| Setting | Before | Applied |
|---|---:|---:|
| WSL memory limit | 12 GB | 6 GB |
| WSL virtual CPUs | 16 | 4 |
| WSL swap | 4 GB | 8 GB |

Mirrored networking, DNS tunnelling, proxy/firewall integration, nested virtualization, graphics, gradual memory reclamation and sparse-VHD settings were retained. The applied configuration was boot-tested in Ubuntu; the live guest reported the requested memory/CPU/swap limits. Ubuntu was then stopped for native host-tree inference.

Twenty confirmed idle optional tool-service processes were stopped using retained process handles and fresh identity checks. Scientific jobs, Codex, Google Drive and unrelated user applications were preserved. No scientific inputs or checkpoint files were deleted.

The retained toolchain was mounted and probed successfully: PADLOC 2.0.0, DefenseFinder 3.0.0, MacSyFinder 2.1.4, HMMER 3.4, Python 3.11.17 and R 4.3.1. No tool or database upgrade was required.

## Operating recommendation

Keep the existing installation. Run the current IQ-TREE job natively, with WSL stopped, then run the Linux detector jobs with bounded concurrency. Admit each heavy job using fresh available RAM, actual Windows system commit headroom and working-volume disk space. Swap is overflow capacity and does not count as physical RAM for admission.

Use local temporary storage for live inference and freeze/hash-verify accepted results into the canonical project afterward. A WSL rebuild, distro deletion or virtual-disk compaction is unnecessary for the measured RAM constraint. Reconsider the limits only after measuring the real detector peak.

## Recovery files

`wslconfig.before.txt` is the exact previous configuration; SHA-256 `cd4ece709346e258d2506f47057d3de22189598651cc863dab27014905640b73`.

`wslconfig.applied.txt` is the exact applied configuration; SHA-256 `fa7e395a9e14e9ed7233032a92a4eeb6b5d2f2a02f3717745c5072b475fb89a8`.

To restore the previous limits, copy the previous file to `C:\Users\wheel\.wslconfig`, then restart WSL after its active work has exited. No restoration has been requested or performed.

Configuration reference: [Microsoft WSL configuration documentation](https://learn.microsoft.com/windows/wsl/wsl-config).

This resource change is operational preparation. It does not establish scientific completion of the host tree, detector screens or figure.
