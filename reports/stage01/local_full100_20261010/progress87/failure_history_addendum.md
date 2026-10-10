# Launch failure-history addendum

Root directly confirmed the separate PowerShell launch refusal for `G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\scripts\master_run\launch_full10086.ps1`:

> File G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\scripts\master_run\launch_full10086.ps1 cannot be loaded. The file is not digitally signed. You cannot run this script on the current system.

That native attempt exited 1 before execution. This is distinct from the earlier hidden/detached dispatch whose native exit remained unknown and which produced no science files. The later run used the guarded retained-session launch without an execution-policy bypass.
