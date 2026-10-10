# Exact UNC03 read-only diagnostic preparation

This separate candidate preserves the proven UNC02 diagnostic and all failed UNC evidence. Source `stage5_unc03_readonly_diagnostic.py` SHA256 is `c0458522ca5483670f008049d1a4457ad27531b003b8397893ee5b0d05b31697`; pure tests `test_stage5_unc03_readonly_diagnostic.py` SHA256 is `8ac84b4e7cbf93c54ef40249ae1d965eff5988efe0a0c29e3b0e672b81b43c23`. The preserved UNC02 source remains `c0e5a8fdbb97b3b3d3251d417e530a858a65fdeff94ec24eaa2cd3dfe4acc45f`.

Changes are limited to UNC03 schema/output tags, `stage5_unc_bind_actual_postiq_03/request.json` SHA256 `7f28e209707483d1a50e25c7d35e5804f2b9ebb8ecf9bcc110714849228ce27d`, and exact sentinel nonce `8ae35884653047348cfa688d4bf00b36`. An explicit nonce guard rejects another well-formed nonce. Worker and owner lifecycle, Windows Job closure, original WorkflowLock, authority/resource checks, tiny-read implementation and independent read-only observations retain the proven diagnostic method.

The only UNC leaves inspected are `linux.bin` and `windows.bin` inside `.unc_visibility_8ae35884653047348cfa688d4bf00b36` at the exact canonical project UNC target and the exact Ubuntu `/var/tmp/lab_rm_stage05_atomic_v1` backing target from the pinned request. Their two containing directories receive metadata observation. No caller-selected UNC path, WSL process, Linux command, UNC write/delete, sentinel cleanup, mount action, service action, Git mutation or scientific acceptance is allowed.

Each leaf preserves the unchanged original `U.tiny_read` result or error. A separate regular, non-reparse bounded read observes at most 513 bytes and records only lengths, hashes and metadata; it never substitutes for original probe acceptance. Directory/leaf permission and nlink failures remain evidence. The diagnostic can establish what Windows actually sees; it cannot upgrade UNC03 into a successful interoperability gate.

Six pure/fake C-only tests and standalone default NOOP pass. Tests validate the exact pinned request/nonce/four leaves/two directories, preserve the original zero-link guard failure, retain permission and partial-payload evidence, prevent unexpected payload mutation, veto halted authority, and prove default NOOP does not import or invoke owner APIs. Synthetic fixtures are local C temp files, removed after tests. Actual UNC reads, Windows native handles/Job/WorkflowLock and WSL operations have not run in this preparation.

The root owner must join the independently audited closed failed UNC03 scope and current no-STOP/original-unlock evidence, publish and read back exact source bytes, and use a fresh C output spool. The later root-only invocation form is:

```text
python.exe -B work/stage5_unc03_readonly_diagnostic.py --run
  --source-sha256 c0458522ca5483670f008049d1a4457ad27531b003b8397893ee5b0d05b31697
  --output C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_unc03_diagnostic_actual01
```

The current owner holds the original byte WorkflowLock once and launches only the retained Windows read-only worker through unchanged `U.windows_job`. An unproved Windows Job closure preserves STOP. Actual diagnostic acceptance still needs its own retained worker terminal, empty Job, original unlock and final source-bound result. A later independent actual review must distinguish complete read-only observations from successful original UNC probe acceptance. No first-genome or image-capture admission follows from this source packet alone.
