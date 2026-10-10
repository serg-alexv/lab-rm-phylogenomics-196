<# Default no-op. A reviewed future RunOnce entry may pass -Run after reboot.
Never registers/reboots, clears STOP, starts WSL or executes a scientific command.
Private handoff/session ID and raw CLI output must never be published. #>
param([switch]$Run)
$ErrorActionPreference = 'Stop'
if (-not $Run) { Write-Output 'PREPARED_DEFAULT_NOOP'; exit 0 }
$expected = 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\Resume-MasterAfterBootOnce.ps1'
if ($PSCommandPath -cne $expected) { throw 'Exact reviewed C launcher path required' }
$python = 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$helper = 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\resume_master_after_boot_once.py'
& $python -B $helper --resume-once
exit $LASTEXITCODE
