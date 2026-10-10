# Stage 5 exact backing-UNC transport preparation

This packet changes only the Windows view used to read the already qualified
Linux ext4 bind. It prepares a new full bidirectional sentinel qualification;
source tests and the earlier diagnostic do not establish that qualification.

The scientific Linux root remains
`/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196` and the scientific output remains
that root plus `/.work/stage05_atomic_v1`. The frozen storage proof must still
bind those exact canonical paths to ext4 backing
`/var/tmp/lab_rm_stage05_atomic_v1`, its helper, boot and filesystem identity.
Windows uses the exact alias
`\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1` after those unchanged
proof checks. The alias is a transport view of the same Linux objects; it does
not move scientific output, adopt the covered Windows G directory, or replace
the canonical root/storage proof.

The root-owned read-only UNC03 diagnostic reports the original `U.tiny_read`
successfully read the known 116-byte Linux sentinel at the backing alias with
inode 33554461 and the prepared SHA. The corresponding canonical UNC queries
returned Windows error 5; the backing Windows sentinel was absent with error 2.
That observation supports testing the exact alias and establishes neither a
general Windows permission diagnosis nor successful two-way I/O.

## Exact source deltas

- `stage5_unc_backing_probe.py`, SHA
  `779502c38c5db06b68e796abc6e1bd99db72d8f97b1129f9057a3f6b0c4221d5`,
  changes only the `UNC` constant from original `stage5_unc_bind_probe.py`
  SHA `0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d`.
  Root, target, runtime, helper pins, schema, request fields, all functions,
  Windows Job ownership, original WorkflowLock, deadlines, two-way sentinel
  write/fsync/readback, exact Linux cleanup and terminal receipts are unchanged.
- `stage5_windows_backing_owner.py`, SHA
  `296492aa4205f64058846b9901a7bb3a3458f99eda1c7ff388a6e33cdc38b834`,
  changes only the final `evidence_view` return expression from original
  `stage5_windows_owner.py` SHA
  `8851bc4fc48ad3069d4ffabe410e159004ef4fc8d6d0755213fc14c22fe0603d`.
  It constructs the UNC path from `frozen['backing']` after the existing exact
  backing, canonical root/target, proof path/hash, helper, ext4, boot and UUID
  checks. All scientific source, resources, admission and ownership stay intact.
- Linux `stage5_atomic.py` remains
  `500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04`;
  `stage5_atomic_process.py` remains
  `e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e`.

## Verification and integration gate

`python -B work/test_stage5_backing_transport.py` passed 17 pure tests. They
check exact source pins; original-byte reversibility; identical probe function
ASTs; the owner AST after restoring its sole changed return; accepted exact
canonical target/backing alias; rejected arbitrary UNC/backing/target, changed
proof and unsafe C proof paths; and a default probe NOOP. Storage observations
are mocked and even G resolution is avoided. A separate probe default NOOP
passed; Windows owner `--help` passed. The owner main was not invoked because
its preserved preparation path reads the project authority/panel before the
`--run` branch.

Root must publish and read back these exact files and the coordinated separate
builder/request variant, then run the unchanged three-step probe in a new
UNC04 owned spool. Adoption requires actual `linux-prepare`, `windows-io`,
`linux-finalize`, both public payloads read back, exact owned-sentinel cleanup,
matching current frozen storage proof, empty owned Windows Job, positive
retained client exits, explicit original unlock and no unresolved STOP. The
existing builder checked-gate schema/state/step contract is preserved. Prior
failed UNC03 scope and its sentinel require their own honest reconciliation;
they are not relabelled as a successful probe.

Only after that qualification and fresh scientific gates may root construct
the first approved genome configuration and use the new Windows owner. The
separate builder revision may introduce the explicitly reviewed finite wait of
1800 seconds while retaining every resource reserve and budget; this producer
packet does not modify the builder or implement a resource/cache effect. The
original actual builder explicitly used zero resource wait; see the preserved
memory assessment correction JSON.

No actual WSL, UNC, lock, native handle, sentinel, detector, image, remote
publication or cleanup operation was performed while preparing this packet.
The whole-image split/cold restore and three-role archive actual gates remain
pending independently.
