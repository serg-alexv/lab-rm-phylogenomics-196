The actual DriveFS02 scope remains FAILED with owned Windows worker closure
unproven and its original STOP preserved. Linux-native closure, retained WSL
exit0 and the independently written Windows byte readback are separate facts.
The original worker function discarded its Windows launch/root terminal/job
query and underlying finalizer exception. Its exact failure cause cannot be
reconstructed from those output files.

One authorized C-only benign fixture using unchanged A80 reproduced the faulty
timing assumption: retained root22928 exit0 was followed immediately by a
successful job query listing different descendant21836, then a successful empty
job query 25ms later. This proves root exit does not imply immediate full-job
emptiness on this host. It does not prove the old DriveFS02 failure had the same
cause or establish any old-scope terminal identity.

The future U worker creates a random named job, configures kill-on-close and
active-process limit1, creates one suspended child and retains its process/thread
handles. It saves launch identity before assignment/resume and requires exact
ResumeThread previous suspend count1. The actual root exit, including positive
FILETIME interval, is saved before job enumeration. A five-second bounded drain
requires the retained root signalled, accounting active count0 and an empty full
PID list. Query failures and nonempty snapshots are preserved, not accepted as
closure. On failure only the newly owned job or its unassigned suspended root can
be terminated, followed by one five-second cleanup drain. Failure-path root
terminal is saved before its first job query as well. Unknown closure remains
OwnedClosureFailure; primary and closure errors survive finalization. Filesystem
receipt failure cannot convert unknown closure to a plain successful return.

The root wait is20s, normal drain5s and exceptional cleanup drain5s, for at most
30s explicit wait/drain budget. Bounds are cooperative and do not hard-cancel
Windows syscalls or receipt fsync. Current setup conservatively preserves its
STOP on any worker exception; the child's closed-failure receipt can support a
separate reviewed reconciliation, never automatic historical reconstruction.

Persistent C evidence per new worker: progress.json, launch.json, root_exit.json
and result.json, including job name, argv, owner/source/API hashes, exact retained
birth/terminal, bounded drain samples and original/query/closure/close errors.
Neither native inference API80 nor Linux supervisor/runner/scientific methods,
accepted sources or resource reserves changed. Linux setup24aa has no U source
dependency and remains byte-identical. Only current direct U/S consumer pins are
refreshed; executed source snapshots and all historical receipts remain intact.
The one-off G helper is retained for source consistency only: its strict nested
mount veto means it must not be rerun after the canonical storage bind exists.

`verify_windows_owned_job_drain_fixture.py` is default-noop and requires the exact
root's retained Windows Python for explicit --run. It creates only a new C-only
Python `pass` job and never touches WSL/G/project lock/STOP/old scopes. Actual
corrected-worker fixture remains NOT_RUN in this source-preparation packet.

Microsoft primary references confirm the job PID list must be complete and job
accounting is queried separately; a signalled root handle is a different query:

- https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list
- https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject
