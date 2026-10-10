# UNC03 C config preparation after the memory profile repair

The old `prepare_stage5_unc_postboot02.py` is preserved byte-for-byte. It has no
argument interface/default NOOP and fixes obsolete runtime06/storage05 hashes,
so it cannot prepare the new route unchanged. This separate small preparer
preserves the original exact V2 template and both unchanged U0664 probe and
W7e06 storage helper sources. It implements no probe, mount or owner framework.

Default invocation reads no evidence and writes no config. After root publishes
the independently reviewed source and actual runtime08/storage06 candidates
exist, root explicitly supplies their exact actual SHA256 values:

```powershell
python -B work/prepare_stage5_unc_postprofile03.py --prepare `
  --runtime-sha256 <actual-runtime08-sha256> `
  --storage-sha256 <actual-storage06-sha256>
```

Only the fixed direct C paths `stage5_runtime_actual_postiq_08.json` and
`stage5_storage_actual_postiq_06.json` are accepted. The runtime candidate must
retain its discovery-only schema/scope, exact three template runtime roots and
complete relative file-role hash maps. The storage candidate must retain its
exact project target/backing/helper, current Linux boot
`f0ffcebc-4901-479d-9559-89d45e9cfa38`, positive integer directory identity,
nonzero canonical filesystem UUID and writable ext4 root-filesystem bind roles.
These are byte/content checks of completed evidence, not a new live observation.

Exactly four fields are filled in the unchanged template: runtime manifest
path/hash and work-storage proof path/hash. All five biological resource fields
remain null and the entire resource policy is unchanged. No scientific native
admission is authorized. The output name is exclusively fixed to
`stage5_unc_config_actual_postprofile_03.json`; any prior output is preserved.
Plain single-link evidence/ancestry, bounded16MiB reads and opened/end identity
checks are required, and every input byte is reread before fsynced exclusive
config creation. Original template/route/probe/storage SHA pins also recheck.

The unchanged U0664 owner still requires explicit source/config hashes and
performs its actual authority, original-lock, resource, current storage proof,
UNC I/O, exact sentinel cleanup and retained closure checks. This preparer does
not make the later probe successful or qualify candidate closure; root must
retain independent actual gate reviews before using these completed candidates.

Six pure tests use synthetic candidate bytes with the exact C template. They
cover deterministic four-field substitution/null budgets, same-byte pin checks,
runtime schema/role/hash-path tamper, old boot and invalid ext4-bind identities,
fixed routes/original source preservation, and default NOOP. A separate default
invocation is also NOOP. No future actual runtime08/storage06 candidate is read,
no config is created, and no UNC/WSL/process/lock/Git action runs in preparation.
