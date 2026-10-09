# IQ-TREE 3.1.4 source recovery readback

The checker independently reopens the immutable published controls and nine source
blobs, downloads the original 41,054,085-byte Release ZIP and its exact 105-byte LF
sidecar into a fresh C work directory, verifies every outer member through EOF CRC
and SHA256, and checks the exhaustive 30-entry checksum table. It imports only the
SHA-pinned independent 6825690d common reader, 090e8068 original-sidecar reader and
cadeda01 Conda reader's resource, owned-command, hashing and ZIP primitives. It
does not import the acquisition, archive builder or active IQ-TREE producer.

The three nested raw gzip/tar exports are read without filesystem extraction.
All 1,938 captured Git blob SHA1/SHA256/size/mode records are joined to the exact
recursive Git-tree metadata and pinned upstream commit/tree identities for
iqtree3, cmaple and lsd2. The expected original Git payload is 112,557,970 bytes.
Regular, executable and symlink payloads remain distinct. Paths, membership,
submodule Gitlinks and original notice paths are checked. Each actual expanded
tar stream, including headers, padding and tail, is bounded at 320MiB; all gzip
streams reach trailer CRC/length validation. Unknown or nonzero trailing payloads
are rejected.

The only admitted export mismatch is iqtree3 `terraphast/appveyor.yml`: the exact
unchanged 264-byte CRLF export and the exact 249-byte original Git supplement are
verified separately. General line-ending normalization is never allowed. Raw
exports are preserved unchanged. Captured Git API commit/tree identifiers are
checked; this checker does not reconstruct serialized signed Git commit objects.
Source preservation does not prove equivalence to the installed Windows binary,
provide a missing standalone Intel notice, or confer biological acceptance,
cleanup authority or host-wipe authority.

The owner runs below normal Windows priority and samples actual physical RAM,
commit availability and C free space. Minimum admission and ongoing reserves are
1.5GiB physical RAM, 1.5GiB commit and 10GiB C space. Each owned `gh` process has
finite timeout and at most one-second nominal waits between resource checks; on
failure only that retained child is terminated and waited for up to five seconds.
Partial files and failure receipts stay preserved; there are no automatic retries.
The aggregate budget is 1,800 seconds. These observations do not reserve memory
or guarantee hard kernel-I/O cancellation. Release tag and selected asset IDs,
sizes, digests and states must match before and after the readback.

Canonical controls are under
`reports/master_run/20261009/cleanup/iqtree314_source01/`; exact paths and hashes
are listed in `verify_iqtree314_source_recovery01_remote_preparation.json`.
Source blobs are under `scripts/master_run/`. After publication and explicit
authorization, run once from this chat's C workspace:

```powershell
python -B work/verify_iqtree314_source_recovery01_remote.py --source-commit <immutable-40-hex-commit>
```

The existing master storage tag and its original target commit are default-pinned
by the common CLI. `--local-inspect` reopens only the existing C recovery artifact
and controls and produces a separately qualified local receipt. Remote readback
remains NOT_RUN until the fresh run produces its own terminal receipt.

Ten in-memory synthetic contracts pass, covering regular/executable/symlink Git
payloads, regenerated-CRC tampering, missing/extra/duplicate/traversal members,
type substitution, actual gzip trailer corruption, hidden trailing payload,
finite expansion, the exact-only supplement and LF-versus-CRLF sidecar identity.
Preparation tests read no upstream archive, invoke no resource API or network,
and start no WSL or scientific computation.
