"""One bounded public-source Copilot review, raw session output kept PRIVATE.

No model override, no tools, no automatic update or remote session export.
The native CLI is suspended until assigned to a kill-on-close owned Windows Job.
No WorkflowLock, WSL, scientific input, archive or image is touched.
"""
from pathlib import Path
import ctypes
import hashlib
import json
import msvcrt
import os
import subprocess
import time
import atomic_iqtree_windows as A
import stage5_unc_bind_probe as U

WORK = Path(__file__).resolve().parent
CLI = Path(r'C:\Users\wheel\AppData\Local\GitHubCopilotCLI\copilot.exe')
PRIVATE = WORK/'private_copilot_vm_alias_review01'


def main():
    A.require(os.name == 'nt' and not PRIVATE.exists(), 'One fresh private review namespace required')
    A.require(A.sha256(WORK/'atomic_iqtree_windows.py') == '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
              and A.sha256(WORK/'stage5_unc_bind_probe.py') == '0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d', 'Current exact retained lifecycle dependencies required')
    source = WORK/'stage5_runtime_transport_alias.py'
    raw = source.read_bytes()
    prompt = ('Review this public project source ONLY as supplied below. Do not use any tools or read any files. '
              'Find concrete correctness/security defects in immutable remote alias names, exact canonical restoration names, original LF sidecar bytes, asset identity/digest/size bindings and bounded verification. '
              'Do not suggest a new controller. Reply under300 words with blockers first and mark assumptions. Source:\n'+raw.decode('utf-8'))
    PRIVATE.mkdir()
    argv = [str(CLI), '--available-tools=', '--deny-tool=shell', '--deny-tool=write', '--deny-tool=url',
            '--disable-builtin-mcps', '--no-custom-instructions', '--no-remote-export', '--no-ask-user',
            '--no-auto-update', '--no-color', '--log-level=none', '--silent', '--prompt', prompt]
    api = A.Win(); job = None; process = api.PROCESS(); birth = None
    record = {'schema': 'COPILOT_PUBLIC_ALIAS_REVIEW_OWNED_LIFECYCLE_V1', 'state': 'FAILED',
              'reviewed_source_sha256': hashlib.sha256(raw).hexdigest(), 'tools_available_argument': '',
              'model_override': None, 'raw_output_publication_permitted': False,
              'owned_closure_proven': False, 'drain_samples': [], 'created': False, 'assigned': False}
    def persist(value): A.atomic(PRIVATE/'PRIVATE_LIFECYCLE_DO_NOT_PUBLISH.json', value)
    try:
        job = api.create_job(None, None); api.ok(job, 'Create owned Copilot review job')
        limits = api.EXTENDED(); limits.BasicLimitInformation.LimitFlags = 0x2000
        api.ok(api.set_job(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)), 'Set Copilot review kill-on-close')
        with open(os.devnull, 'rb') as stdin, (PRIVATE/'PRIVATE_STDOUT_DO_NOT_PUBLISH.txt').open('xb') as stdout, (PRIVATE/'PRIVATE_STDERR_DO_NOT_PUBLISH.txt').open('xb') as stderr:
            handles = [msvcrt.get_osfhandle(stream.fileno()) for stream in [stdin, stdout, stderr]]
            try:
                for handle in handles: os.set_handle_inheritable(handle, True)
                startup = api.STARTUP(); startup.cb = ctypes.sizeof(startup); startup.dwFlags = 0x100
                startup.hStdInput, startup.hStdOutput, startup.hStdError = handles
                command = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
                api.ok(api.create(str(CLI), command, None, None, True, 0x4|0x08000000, None, str(WORK), ctypes.byref(startup), ctypes.byref(process)), 'Create suspended Copilot review client')
            finally:
                for handle in handles: os.set_handle_inheritable(handle, False)
            record['created'] = True
            birth = api.identity(process.hProcess, process.dwProcessId); record['birth'] = birth; persist(record)
            A.require(Path(birth['executable']).resolve() == CLI.resolve(), 'Exact installed Copilot executable required')
            api.ok(api.assign(job, process.hProcess), 'Assign suspended Copilot review'); record['assigned'] = True
            A.require(api.resume(process.hThread) == 1, 'Exact Copilot suspended count differs')
            started = time.monotonic()
            while api.wait(process.hProcess, 500) != 0:
                A.require(time.monotonic()-started < 60, 'Bounded Copilot model/auth review deadline expired')
            record['exit'] = api.identity(process.hProcess, process.dwProcessId, birth['executable'], birth['session_id'])
            persist(record)
            record['job'] = U.drain_windows_job(api, job, process.hProcess, record, persist)
            record['owned_closure_proven'] = True
            record['state'] = 'CLOSED_ROOT_EXIT0_REVIEW_OUTPUT_PENDING_SANITIZED_READ' if record['exit']['exit_code'] == 0 else 'CLOSED_REVIEW_EXIT_NONZERO'
    except BaseException as error:
        record['error_kind'] = type(error).__name__
    finally:
        if record['created'] and not record['owned_closure_proven']:
            try:
                if record['assigned']: api.ok(api.terminate_job(job, 2), 'Terminate exact owned failed Copilot review job')
                else: api.ok(api.terminate(process.hProcess, 2), 'Terminate exact suspended Copilot review root')
                def terminal():
                    record['exit'] = api.identity(process.hProcess, process.dwProcessId, birth['executable'], birth['session_id'])
                    persist(record)
                record['job'] = U.drain_windows_job(api, job, process.hProcess, record, persist, root_terminal=terminal)
                record['owned_closure_proven'] = True
            except BaseException as error: record['closure_error_kind'] = type(error).__name__
        for handle in [process.hThread, process.hProcess, job]:
            if handle: api.ok(api.close(handle), 'Close exact Copilot review handle')
        persist(record)
    print(json.dumps({'state': record['state'], 'owned_closure_proven': record['owned_closure_proven'],
                      'exit_code': record.get('exit', {}).get('exit_code'), 'reviewed_source_sha256': record['reviewed_source_sha256']}))
    return 0 if record['owned_closure_proven'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
