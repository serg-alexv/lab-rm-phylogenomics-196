# Targeted runtime hash cache advice: prepared method

The only operative change is `sha()` in `stage5_atomic.py`, four constants and the `stat` import. An AST comparison against the retained exact original proves every other runner node unchanged. Exact SHA256 results and runtime manifest structures remain unchanged. Both discovery (`pin_runtime`) and subsequent per-genome manifest validation use this function.

On POSIX, only canonical plain regular files at least 16 MiB under the three exact retained `detector_env`, `defense_models`, and `padloc_db` roots qualify. The function opens the exact file read-only with `O_NOFOLLOW`, binds the opened descriptor to pre-read path metadata, streams 1 MiB blocks, and rejects size or device/inode/mtime/ctime/mode/link metadata changes. Other files use the original `hashlib.file_digest` path.

Completed whole page intervals receive `POSIX_FADV_DONTNEED` advice at intervals of at most 8 MiB. The final file page is excluded, even when EOF is aligned. Unsupported advice, errors and unexpected return values fail closed. There are no source writes, dirty-page flushes, global cache operations, changes to scientific source data, or biological launches.

Nine synthetic tests pass independently. They read actual own C-work bytes through read-only descriptors and mock POSIX advice and consistent Linux inode metadata. Production Linux metadata guards remain strict. The tests cover exact large/small SHA, other-scope behavior, partial and aligned EOF retention, readonly/no-follow flags, descriptor closure, opened identity replacement, post-read metadata drift and unsupported/error advice. Forty-two retained atomic/source contracts also passed in the author's bounded check.

The kernel hint is advisory. Outer loop-image cache may remain, and no reduction of Windows physical/commit use or resource admission is guaranteed. Actual Linux runtime hashing/advice and interoperability remain NOT_RUN by this preparation. Root publication of the reviewed source and the combined consumer pin cascade precedes any actual use. Existing lifecycle, lock, resource, runtime, source and scientific gates remain in force.
