This helper targets only the eight originally observed Chrome processes and the
single observed Microsoft.Media.Player process at the two exact executable paths
embedded in the source. It does not discover or adopt new processes or children.
The default invocation performs no query or action. `--capture-plan` performs
read-only retained-handle birth/image/memory queries and hashes the exact retained
executable file handles. An explicit `--run` requires that captured source-bound
manifest, its SHA256, and a fresh direct-child C-work receipt filename.

Run mode retains all nine exact process handles and both executable READ handles,
proves every birth/image/session and executable file ID/bytes before the first
action, then calls TerminateProcess only on those retained handles. Each action
has a durable preceding receipt; each target closure is read from the same
retained handle. The Chrome parent is processed last. There are no HWND messages,
RestartManager calls, numeric PID signals, taskkill, service actions or descendant
adoption. This is forced termination, with the corresponding possibility of lost
unsaved app state. Codex, tool servers, Google Drive, WSL and services are outside
the exact executable allowlist.

There is a cooperative 25-second action deadline and at most one five-second wait
after the final admitted target, hence at most 30 seconds of explicit action/wait
budget, excluding filesystem/API latency. The deadline does not cancel blocked
Windows calls or receipt fsync. On preflight drift no target is terminated. On
later failure no remaining target is acted on; already completed actions remain
explicitly receipted. Host resource deltas are concurrent observations and are
not exclusively attributable to these apps. Executable file identity describes
the retained filesystem file, without claiming a separate mapped-image audit.

Current preparation observed a real state change: all original targets vanished
before the first read-only capture completed. OpenProcess for original PID14764
returned WinError87. A fresh CIM query then found neither allowlisted app name.
No captured plan was written and this helper sent no termination calls. Original
CIM metadata, the failed capture and the later resource snapshot are preserved in
the preparation receipt. The fixed-nine helper is now a historical prepared
implementation; it must not be used to adopt replacement processes. Any future
scope requires a separately reviewed source/manifest refresh.
