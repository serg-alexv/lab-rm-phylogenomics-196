# Copilot cleanup review

Executed GitHub Copilot CLI with supplied project facts and shell/write tools denied.
This is advisory operational review, not scientific validation.

Missing concrete checks:

1. **Lease atomicity**: "expected-head lease" needs a stated conflict policy — if remote main advances between inventory and final receipt commit, abort and re-verify rather than force-push.

2. **Active-process exclusion proof**: before purge, enumerate the live IQ-TREE PID's open file handles (checkpoint, .ckp.gz, log, lock) and diff against the deletion candidate list — not just path/name matching — to guarantee zero overlap.

3. **Hash algorithm + manifest format**: specify which hash (SHA-256 minimum) for both ZIP-member verification and the deletion receipt, and store expected hashes in the repo *before* purge, not alongside it.

4. **Verification independence**: "independently download and verify" must use a second execution context (different process/session than the archiver) to catch silent corruption or symlink/path tricks.

5. **Receipt-before-delete ordering**: deletion receipt must be committed and its remote commit SHA confirmed reachable *before* any local delete executes — not concurrently.

6. **Swap/cap interaction**: confirm WSL's 8GB swap file itself isn't among "yesterday obsolete artifacts" — exclude by explicit path, not just by being outside the project scope.

7. **UNKNOWN/raw-failure immutability check**: add a post-purge diff asserting those labels/records are byte-identical pre/post.


Disposition: apply explicit remote conflict, SHA-256 and recovery-before-delete gates.
Commit proposed removal receipts before deletion and actual receipts after it.
Open-handle exclusion has not been established; active pinned dependency trees
remain excluded from removal. No deletion was authorized solely by this review.
