# Prepared directory-only old-C pruner

Status: **production old-C pruning NOT_RUN**. Root owns publication, fresh remote readback, the separate exact authorization, and any actual execution. The original 5,542-directory proposal is unchanged. This preparation removed only three newly created synthetic empty directories; every fixture file, replacement directory, referent, reparse point and failed-attempt namespace is retained.

`prune_old_scientific_directories.py` defaults to `PREPARED_NO_PRUNE`. Its production path requires the exact WD/current C deployment, explicit current source SHA, an independently SHA-pinned direct C-work root authorization, the original proposal SHA `be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5`, and the actual fresh remote proof SHA `e71b02889d5443017ef5ab8be206b1fc4e5f9f81c3de14c602eeaeef70c68063` from commit `25792aca769466123d7a5a3186e9c86bd97cd0f7`. The seven old-C roots, six holds, all preserved MacSyFinder-fragment ancestors, the causal postorder and exact 5,542 unique paths remain fixed. Unknown files/subtrees are never adopted.

For each directory, the helper retains every ancestor with `FILE_LIST_DIRECTORY | FILE_READ_ATTRIBUTES`, sharing read/write but excluding delete. It opens the target with `DELETE | FILE_READ_ATTRIBUTES | FILE_LIST_DIRECTORY`, sharing read only, and uses `FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT`. It verifies an actual non-reparse directory, volume serial, all 128 file-ID bits, full creation FILETIME, attributes and the literal final handle path. It closes its one-entry emptiness enumeration before marking the same checked handle through `SetFileInformationByHandle(FileDispositionInfo=4)` with a one-byte BOOLEAN. It never sets `FILE_FLAG_DELETE_ON_CLOSE`; no `Remove-Item`, `os.rmdir`, file disposition on regular files, path removal or recursive deletion is used. The kernel supplies a second nonempty-directory veto, verified in the actual fixture below.

Parent last-write/change timestamps may differ from the published snapshot only when that parent originally listed planned directory children and every listed child was already removed by this same run. Full identity/birth/type must still match, and the parent must actually be empty. This does not adopt unknown children or allow identity replacement.

The append-only C journal flushes and fsyncs `BEFORE_DISPOSITION`, the disposition mark, and `AFTER_REMOVED`, recording the exact original identity. A 900-second helper-only timer exits this Python process with 124; monotonic/source/owner checks also run before each disposition. Timeout, journal failure, failed metadata/hash/liveness checks, sharing errors, changed identities, or nonemptiness stop further pruning. A marked directory can disappear when the helper's handle closes even if a later journal write fails. Therefore a partial journal requires root reconciliation against its original identity/BEFORE evidence; it is not a completion or automatic resume certificate.

The helper retains query/synchronize handles for the exact native and controller PID/full-birth identities captured by the pinned protection receipt, checks their liveness before each disposition and after final protected hashes, and never signals them. All 12 protected source/config/input/executable hashes and the 1,025-byte excluded MacSyFinder fragment are checked before/after. It does not open/acquire/write the WorkflowLock, start WSL, launch native inference, write G, read the 8-GiB toolchain image, or alter scientific/controller sources. The production protection/owner checks have not been executed by this preparation.

## Actual fixtures and the corrected Windows finding

Attempt01 preserved `prune_old_scientific_directories_attempt01.py` (SHA `2f608bd1f11b3aac9223c7c751b9a9d8f5cb5c02568861bd6cfeadfff9304604`) and `test_directory_handle_prune_fixture_attempt01.py` (SHA `72e3a86e28f08e845cb37a9ef62f6ea056d220902e7074b4fdc63dbcb8e4d0c7`). Its receipt `directory_handle_fixture_20261009T211154Z_9cf77be3.json` records eight passing cases, then an actual ancestor rename unexpectedly succeeding under a READ_ATTRIBUTES-only handle. This is an observed Windows sharing failure, not source/data corruption. That source-only review is retained as attempt01 evidence and is not operational acceptance.

The correction adds `FILE_LIST_DIRECTORY` to all ancestor opens, including the identical fixture call. Final pruner SHA is `9b64d17bb2612ce35051b87d77863709d875c1f910865fd6a4db2f6ddd265381`; fixture SHA is `c0c62e1aa3bf7b6d7b011b6afbddf07c8827e6af54729961b955eda703a0031a`. A peer reviewed this exact delta before execution.

Actual attempt02 exited 0; receipt `directory_handle_fixture_20261009T211310Z_843dbf82.json` SHA `eebac12d62403b273713ee0f4aaad17955a4c6b7d33631e63ee1f86dc4e47ba1` records all nine passing cases:

1. An empty original directory disappears after marking/closing its exact handle.
2. An originally nonempty directory and its bytes are preserved.
3. A regular file is refused and preserved.
4. An actual newly created directory symlink/referent is refused and preserved.
5. A same-name replacement with a different full ID is refused; both originals remain.
6. Postorder child then parent removal succeeds with actual parent timestamp change and unchanged full ID/birth.
7. A new unknown child after the snapshot is preserved.
8. Direct native disposition of the checked nonempty directory returns actual `ERROR_DIR_NOT_EMPTY` 145.
9. The corrected retained ancestor handle rejects rename with actual `ERROR_SHARING_VIOLATION` 32.

The receipt reports three removed synthetic empty directories and zero old-C directory removals, files deleted, path-removal calls, recursive cleanup, G access, WSL starts, production execute calls or WorkflowLock access. Its journal SHA is `0109e6d8ae71bef6e465931a52510e8cd627e3ebda92a148caca42f8ab4cac4c`. These are bounded local Windows fixture results, not an old-C pruning certificate.

## Root-only later command

After final independent source/evidence review and remote publication/readback of these exact bytes, root may create a new direct C-work authority file from the separately retained FALSE template. Root must set both authorization booleans true only after those gates are fulfilled and pin the resulting actual authority bytes. The original template is intentionally rejected by `--run`.

```powershell
& 'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B `
  work/prune_old_scientific_directories.py --run `
  --source-sha256 9b64d17bb2612ce35051b87d77863709d875c1f910865fd6a4db2f6ddd265381 `
  --authorization 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\ROOT_CREATED_AUTHORITY.json' `
  --authorization-sha256 ROOT_VERIFIED_ACTUAL_AUTHORITY_SHA256 `
  --journal 'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\ROOT_NEW_DIRECTORY_PRUNE_JOURNAL.jsonl'
```

The command contains deliberate unresolved root-owned placeholders and has not been executed. Any source/control or protected-owner change requires a new bounded review; missing/changed/regular/reparse/nonempty paths stop rather than becoming implicit successful deletion. After any real run, a separate root-owned independent post-verification is required before declaring the 5,542 proposal completed or authorizing host wipe. This helper alone does not supply that post-verifier or expand cleanup scope.

Microsoft primary documentation: [SetFileInformationByHandle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfileinformationbyhandle), [FILE_DISPOSITION_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_disposition_info), [directory handles](https://learn.microsoft.com/en-us/windows/win32/fileio/obtaining-a-handle-to-a-directory), [CreateFile sharing/reparse flags](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew), and [CreateSymbolicLinkW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createsymboliclinkw). The actual platform fixture establishes the access/share behavior used here; documentation review alone was insufficient for attempt01.
