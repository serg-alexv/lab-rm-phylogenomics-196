# Exact execution-archive readback

`verify_directory_prune_execution_remote.py` defaults to no readback or network. Explicit `--local-inspect` reads only the fixed current-C archive and known public control/source files. Explicit `--verify-remote --source-commit <immutable 40-hex commit>` reads actual Git blobs at that exact source commit and freshly downloads the fixed ZIP and original LF sidecar from the pinned release/tag. The source commit is separate from the release tag target. Root alone authorizes and executes fresh remote readback after publication of the reviewed reader.

The checker imports only three exact-SHA-pinned independent readback helpers; it never imports the archive producer or native pruner. The existing owned-gh monitor retains each Popen process handle, preserves bounded stdout/stderr, checks resources/deadlines while waiting, and requests termination only through that exact retained child handle on failure. It requires observed child closure within five seconds; no PID adoption or process-name killing occurs. Physical and commit reserve are both 1536MiB, disk reserve10GiB, aggregate deadline1800s. Synchronous kernel-I/O cancellation and descendant-job containment are not claimed.

Whole ZIP size/SHA, exhaustive literal member names, Windows alias safety, sorted order, DEFLATED compression, regular-file attributes, timestamps, absent extras/comments/encryption, all54 member EOF CRC/SHA/size records and all53 internal SUMS records are checked. All50 original source names have independent literal expected SHA pins. Original path/byte/hash/file-identity/birth/link/capture metadata are joined to pinned build/index controls. This does not re-read original scientific payloads or establish current file identity from an archived record.

Distinct streaming journal logic parses all16628 records and joins all5542 ordered BEFORE/marked/AFTER triples to the original seven-scope proposal/full IDs/births. Parent timestamp changes require already removed planned children. The exact terminal, historical protected12/six dirtyG hashes, native/controller birth/liveness records at execution time, authority and recovery proof are cross-bound. The accepted independent postcheck must account for all5542 as documented/currently absent at its recorded check, preserve six holds/the MacSyFinder fragment, and bind the original lock metadata without lock content access/acquisition. No current old-C/G rescan, current owner query, lock query, cleanup, extraction, WSL or biological execution occurs.

Both actual historical failures and the original pending execution checkpoint must retain their failed/pending states. G-provider zero link counts remain explicitly qualified: single-link exclusion is not established. Remote mode checks release/tag and selected asset identities/digests before and after download. Local PASS does not prove remote preservation; fresh remote PASS grants no new deletion, host-wipe or scientific acceptance authority.

Prepared source36be18fcc4296b6d4e8a2e833678e64647aaac249e22e8ea50be1cb72d0ab434 and eight pure tests c973a3c0c7fca0dcb2d5d2ea87fbdf328b4a196f2d3a213b0df7d33cd574b548 are frozen. Independent source review66343876ba374064afa68deb93a4b0be0d7d850cd542469370895c89a4f0b5b3 is separate. The actual local checker exited0; its immutable receipt67d941a0cd2ea62ad2e4074478bc9ae5b2768c8064a15224008b9d49a4e1a9c6 records the local54/5542 joins. Fresh remote execution remains NOT_RUN in this preparation.

After root publication, the exact command is:

```powershell
& 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B work\verify_directory_prune_execution_remote.py --verify-remote --source-commit <new-published-reader-commit>
```

The default release is `master-run-storage-20261009-v1`, with expected tag commit46c7089f906cce59afabaa4449b05df36ee124de. All partial downloads, command logs and failed readback receipts are preserved; no automatic retry or cleanup is built in.
