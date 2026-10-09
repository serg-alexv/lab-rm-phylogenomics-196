# Old-C scientific cache directory proposal

Actual metadata-only scan completed with exit 0. It proposes 5,542 directories: 3,736 empty at observation and 1,806 containing only proposed child directories. Every child precedes its parent in the proposal. The original 8,937,244-byte JSON remains unchanged at `master_old_scientific_emptydirs_proposed_02.json`, SHA256 `be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5`.

The fixed old checkout is `C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196`. Exact proposed counts by allowed scope:

| Scope | Proposed directories |
| --- | ---: |
| data | 982 |
| .work/review2 | 244 |
| .work/stage02_validated | 198 |
| .work/source_locus_inputs_v1 | 2514 |
| .work/stage03_markers_v1 | 988 |
| .work/stage04a_windows_alignments_v1 | 308 |
| .work/stage04_phylogeny_v2 | 308 |

The scan derives exactly 5,548 causal directory ancestors from two SHA-bound, independently verified leaf-purge journals. Those prove the earlier 47,429 and 837 file removals; they do not authorize any directory removal. Root confirmed the second independent postproof `a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082` before this proposal.

Six observed directories are held: `review2/io_streaming_interrupted/assemblies`, its `io_streaming_interrupted` parent, `review2/publication_review`, `review2/stage05_raw_review`, `review2` itself, and `stage04_phylogeny_v2`. The whole 1,025-byte MacSyFinder serializer fragment and every ancestor remain protected. Four unknown subtrees remain untraversed: the interrupted-review `GCF_000011045.1` directory, both encountered `__pycache__` directories, and the Stage4 `temporary` directory. No unknown files or subtrees are adopted into this proposal.

Each proposed directory has full retained-handle NTFS 128-bit file identity, volume serial, full creation/last-write/change/access FILETIME metadata, attributes, and literal final handle path. The scanner uses no-follow reads and denies ancestor rename/delete during observation. Full-directory identity and relevant metadata remain stable during their observation. This is a snapshot, not a deletion certificate.

The first scanner stopped before producing a proposal because Windows cached `DirEntry.stat` supplied inode zero. Its exact reviewed source, failure receipt, traceback, and seven-root diagnosis are preserved. Fresh no-follow `Path.lstat` supplied IDs matching the retained handle IDs; the corrected scanner keeps that exact comparison. Four pure guard tests passed. A separate agent independently reviewed the corrected source and exact completed plan; its receipt is included.

No executor was built or run. No G writes, WSL starts, native jobs, file deletion, or directory deletion occurred. Future pruning requires published controls, explicit root authority, current exact identity/type/emptiness checks, and a separately tested directory-only exact-handle deletion primitive. Plain check-then-`Remove-Item` has a leaf replacement race and cannot establish the required no-file-loss guarantee. New files, reparse points, changed identity, or nonempty directories must veto removal. Windows `SetFileInformationByHandle(FileDispositionInfo)` on an opened directory DELETE handle is only a future candidate requiring an actual benign fixture and independent review.

The separate read-only old-checkout Git audit found four modified tracked paths and 191 untracked status entries (189 files and two collapsed directories), with 356 indexed paths. It did not establish durable remote coverage. Preserve the checkout and `.git`; do not infer that these histories are recoverable merely from their names or Git status. Exact metadata paths and the audit source are included. Git can internally read tracked bytes for status; no source contents or private Git bundle were dumped.

The metadata ZIP preserves the original proposal and fixed public preparation evidence with exact original path/identity/size/mtime/SHA bindings, a deterministic member order/timestamp, and streamed CRC/SHA readback. Actual future deletion, remote publication, fresh remote readback, Stage5 biology, and operational native closure remain outside this package's claims.
