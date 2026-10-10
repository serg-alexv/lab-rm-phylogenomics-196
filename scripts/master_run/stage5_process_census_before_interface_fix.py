"""Opt-in Windows metadata census. Never clears STOP or accepts closure.

Default is a no-op. --run uses the original WorkflowLock while preserving the
exact DriveFS02 STOP. --with-cim adds one bounded, owned read-only PowerShell
query. Reserved native fields remain opaque; no undocumented birth offsets.
"""
from pathlib import Path
import argparse
import ctypes as c
import datetime as dt
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import uuid

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
API_SHA = '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
CIM_SHA = '7bdc78b789d330e52c56d27f685b84940cc1e3824a5fa1c4aa98d93e32f96853'
STOP_SHA = '3de7057780d280d5f204b535207a174e616ca425b5638fe9848a48cfca20838a'
RESULT_SHA = '6c7595ddbcd5847e1ad311ae922bb9f95d483764f9faec5625659723e1f42b68'
SOURCE_SHA = 'b5826e46af71ad2353fef4a2c1ab28fe009f02411f9ab0b22032d46026755b33'
OLD_PID = 21672
OLD_BIRTH = 134360636630302864
MAX_BUFFER = 8 * 1024**2
MAX_PROCESSES = 4096
OLD_RESULT = WORK / 'stage5_setup_drivefs_actual_postiq_02/result.json'
OLD_SOURCE = WORK / 'stage5_setup_windows_before_windows_job_drain.py'
POWERSHELL = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
U32, I32, U64, PTR = c.c_uint32, c.c_int32, c.c_uint64, c.c_void_p


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n'); f.flush(); os.fsync(f.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def error_info(error):
    return dict(kind=type(error).__name__, message=str(error), winerror=getattr(error, 'winerror', None))


def bounded_json(path, limit=2 * 1024**2):
    with Path(path).open('rb') as f:
        raw = f.read(limit + 1)
    need(len(raw) <= limit, 'Bounded JSON exceeded')
    return json.loads(raw)


def filetime_from_iso(value):
    stamp = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(stamp.utcoffset() == dt.timedelta(0), 'UTC timestamp required')
    delta = stamp - dt.datetime(1601, 1, 1, tzinfo=dt.timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 10_000_000 + delta.microseconds * 10


def birth_window(old_result):
    need(old_result['actual_windows_owner']['pid'] == OLD_PID
         and old_result['actual_windows_owner']['creation_filetime'] == OLD_BIRTH,
         'Exact original owner identity differs')
    upper = filetime_from_iso(old_result['utc'])
    need(upper >= OLD_BIRTH, 'Original result timestamp precedes owner birth')
    return dict(inclusive_lower_filetime=OLD_BIRTH - 600_000_000,
                inclusive_upper_filetime=upper + 600_000_000,
                margin_seconds_each_side=60,
                interpretation='DIAGNOSTIC_CANDIDATE_WINDOW_NOT_PROVEN_CLOCK_CONTINUITY_OR_OWNER_EXIT')


class UNICODE(c.Structure):
    _fields_ = [('Length', c.c_uint16), ('MaximumLength', c.c_uint16), ('Buffer', PTR)]


class SPI(c.Structure):
    # Microsoft winternl.h public layout: all Reserved members stay opaque.
    _fields_ = [('NextEntryOffset', U32), ('NumberOfThreads', U32), ('Reserved1', c.c_ubyte * 48),
                ('ImageName', UNICODE), ('BasePriority', I32), ('UniqueProcessId', PTR),
                ('Reserved2', PTR), ('HandleCount', U32), ('SessionId', U32), ('Reserved3', PTR),
                ('PeakVirtualSize', c.c_size_t), ('VirtualSize', c.c_size_t), ('Reserved4', U32),
                ('PeakWorkingSetSize', c.c_size_t), ('WorkingSetSize', c.c_size_t), ('Reserved5', PTR),
                ('QuotaPagedPoolUsage', c.c_size_t), ('Reserved6', PTR), ('QuotaNonPagedPoolUsage', c.c_size_t),
                ('PagefileUsage', c.c_size_t), ('PeakPagefileUsage', c.c_size_t),
                ('PrivatePageCount', c.c_size_t), ('Reserved7', c.c_int64 * 6)]


class CLIENT_ID(c.Structure):
    _fields_ = [('UniqueProcess', PTR), ('UniqueThread', PTR)]


class STI(c.Structure):
    _fields_ = [('Reserved1', c.c_int64 * 3), ('Reserved2', U32), ('StartAddress', PTR),
                ('ClientId', CLIENT_ID), ('Priority', I32), ('BasePriority', I32),
                ('Reserved3', U32), ('ThreadState', U32), ('WaitReason', U32)]


def validate_abi():
    need(c.sizeof(PTR) == 8 and c.sizeof(SPI) == 256 and c.sizeof(STI) == 80
         and SPI.ImageName.offset == 56 and SPI.UniqueProcessId.offset == 80
         and SPI.SessionId.offset == 100 and STI.ClientId.offset == 40,
         'Unsupported public Windows x64 SPI/STI ABI; no guessed offsets')


def parse_native(raw, base_address):
    validate_abi()
    need(0 < len(raw) <= MAX_BUFFER and base_address > 0, 'Native returned length/base invalid')
    rows = []; seen = set(); offset = 0
    while True:
        need(len(rows) < MAX_PROCESSES and offset + c.sizeof(SPI) <= len(raw), 'Native record count/header bound')
        row = SPI.from_buffer_copy(raw, offset)
        step = int(row.NextEntryOffset)
        end = offset + step if step else len(raw)
        need(not step or (step % 8 == 0 and step >= c.sizeof(SPI)), 'Native next offset alignment/size')
        need(end <= len(raw) and end > offset and row.NumberOfThreads <= 65536, 'Native record extent/thread bound')
        thread_end = offset + c.sizeof(SPI) + row.NumberOfThreads * c.sizeof(STI)
        need(thread_end <= end, 'Native thread array exceeds returned record')
        pid = int(row.UniqueProcessId or 0)
        need(0 <= pid <= 0xffffffff and pid not in seen, 'Native duplicate/invalid PID')
        seen.add(pid)
        for index in range(row.NumberOfThreads):
            thread = STI.from_buffer_copy(raw, offset + c.sizeof(SPI) + index * c.sizeof(STI))
            need(int(thread.ClientId.UniqueProcess or 0) == pid, 'Native thread owner differs from record')
        length, maximum, address = row.ImageName.Length, row.ImageName.MaximumLength, int(row.ImageName.Buffer or 0)
        need(length % 2 == 0 and maximum % 2 == 0 and length <= maximum <= 65534, 'Native Unicode length invalid')
        name = None
        if maximum:
            name_offset = address - base_address
            need(address > 0 and thread_end <= name_offset and name_offset + maximum <= end,
                 'Native Unicode pointer outside its admitted returned record')
            name = raw[name_offset:name_offset + length].decode('utf-16-le', errors='strict')
        else:
            need(length == 0, 'Native absent name has nonzero length')
        rows.append(dict(pid=pid, image_name=name, session_id=int(row.SessionId),
                         threads=int(row.NumberOfThreads), handles=int(row.HandleCount),
                         record_offset=offset, record_bytes=end - offset,
                         creation_filetime=None, native_birth_status='UNSUPPORTED_OPAQUE_RESERVED_FIELDS'))
        if not step:
            break
        offset = end
    need(rows, 'Empty native process universe')
    return rows


def native_snapshot(ntquery, check, output, label):
    size = 65536; attempts = []
    for _ in range(10):
        check(); need(size <= MAX_BUFFER, 'Native buffer maximum exceeded')
        buffer = c.create_string_buffer(size); needed = U32()
        status = int(ntquery(5, buffer, size, c.byref(needed))) & 0xffffffff
        attempts.append(dict(buffer_bytes=size, return_bytes=int(needed.value), ntstatus=f'0x{status:08x}'))
        if status == 0xc0000004:
            size = max(size * 2, int(needed.value) + 65536)
            continue
        need(status == 0 and 0 < needed.value <= size, 'Native query status/returned length unsupported')
        raw = buffer.raw[:needed.value]; base = c.addressof(buffer)
        rows = parse_native(raw, base)
        path = output / (label + '.spi.bin')
        with path.open('xb') as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        return dict(state='RETURNED_RECORDS_VALIDATED', api_class='SystemProcessInformation(5)',
                    raw_file=str(path), raw_sha256=sha(path), raw_bytes=len(raw), captured_base_address=base,
                    attempts=attempts, records=rows, native_birth_supported=False)
    raise ValueError('Native query growth attempts exhausted')


def enum_pids(enum, check):
    count = 1024
    while count <= MAX_PROCESSES:
        check(); values = (U32 * count)(); used = U32()
        if not enum(values, c.sizeof(values), c.byref(used)):
            raise c.WinError(c.get_last_error())
        need(used.value % c.sizeof(U32) == 0 and used.value <= c.sizeof(values), 'EnumProcesses invalid length')
        if used.value == c.sizeof(values):
            count *= 2
            continue
        pids = [int(x) for x in values[:used.value // c.sizeof(U32)]]
        need(len(set(pids)) == len(pids), 'EnumProcesses duplicate PID')
        return sorted(pids)
    raise ValueError('EnumProcesses full buffer/truncation at maximum')


def retained_births(api, pids, check):
    opened = []; rows = []
    open_process = api.K.OpenProcess
    open_process.restype = PTR; open_process.argtypes = [U32, c.c_int, U32]
    try:
        for pid in sorted(pids):
            check()
            if pid == 0:
                rows.append(dict(pid=0, state='IDLE_SPECIAL_NO_USER_WORKER_BIRTH', creation_filetime=None))
                continue
            handle = open_process(0x1000, False, pid)
            if not handle:
                rows.append(dict(pid=pid, state='UNKNOWN_OPEN_FAILED', winerror=c.get_last_error()))
                continue
            opened.append((pid, handle))
            try:
                values = [api.FILETIME() for _ in range(4)]
                api.ok(api.times(handle, *(c.byref(x) for x in values)), 'Retained GetProcessTimes')
                rows.append(dict(pid=pid, state='RETAINED_KERNEL_TIMES', creation_filetime=api.ft(values[0]),
                                 exit_filetime_raw_undefined_if_active=api.ft(values[1]),
                                 access_mask='PROCESS_QUERY_LIMITED_INFORMATION_ONLY',
                                 kernel_exit_or_liveness_proven=False))
            except BaseException as error:
                rows.append(dict(pid=pid, state='UNKNOWN_RETAINED_QUERY_FAILED', error=error_info(error)))
        return rows, opened
    except BaseException:
        for _, handle in opened:
            api.close(handle)
        raise


def candidates(rows, window):
    return [row for row in rows if row.get('creation_filetime') is not None
            and window['inclusive_lower_filetime'] <= int(row['creation_filetime']) <= window['inclusive_upper_filetime']]


def crossvalidate_cim(rows, supplemental):
    native = {row['pid']: row for row in rows}; result = []
    need(supplemental.get('schema') == 'STAGE05_PROCESS_CENSUS_CIM_CLOCK_SUPPLEMENT_V1', 'CIM supplement schema differs')
    seen = set()
    for row in supplemental.get('process_census', {}).get('rows', []):
        need(row.get('pid') is not None, 'CIM null PID is an explicit incomplete row')
        pid = int(row['pid']); need(pid not in seen and 0 <= pid <= 0xffffffff, 'CIM duplicate/invalid PID')
        seen.add(pid); kernel = native.get(pid); birth = row.get('birth_filetime')
        state = 'NO_RETAINED_KERNEL_BIRTH_FOR_CROSSCHECK'
        if birth is not None and kernel and kernel.get('creation_filetime') is not None:
            state = 'MATCH_WITHIN_CIM_MICROSECOND_PRECISION' if abs(int(birth) - kernel['creation_filetime']) <= 10 else 'MISMATCH_OR_PID_REUSE'
        result.append(dict(pid=pid, state=state, cim_creation_filetime=birth,
                           kernel_creation_filetime=kernel.get('creation_filetime') if kernel else None))
    return result


def powershell_query(api, output, check):
    """Only the newly created read-only query worker may be terminated on timeout."""
    script = WORK / 'stage5_process_census_cim_query.ps1'
    need(sha(script) == CIM_SHA, 'Pinned CIM source differs')
    argv = [POWERSHELL, '-NoLogo', '-NoProfile', '-NonInteractive', '-File', str(script),
            '-OutputJSON', str(output / 'supplemental.json')]
    job = api.create_job(None, None); need(job, 'Create exact diagnostic job failed')
    process = api.PROCESS(); assigned = False; created = False; closed = False
    result = dict(argv=argv, scope='OWN_NEW_READ_ONLY_POWERSHELL_QUERY_ONLY', source_sha256=CIM_SHA)
    try:
        limits = api.EXTENDED(); limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x8
        limits.BasicLimitInformation.ActiveProcessLimit = 1
        api.ok(api.set_job(job, 9, c.byref(limits), c.sizeof(limits)), 'Set exact diagnostic job policy')
        startup = api.STARTUP(); startup.cb = c.sizeof(startup)
        command = c.create_unicode_buffer(subprocess.list2cmdline(argv))
        api.ok(api.create(POWERSHELL, command, None, None, False, 0x4 | 0x08000000,
                          None, str(WORK), c.byref(startup), c.byref(process)), 'Create suspended diagnostic query')
        created = True
        birth = api.identity(process.hProcess, process.dwProcessId)
        result['birth'] = birth; write(output / 'supplemental_worker_birth.json', result)
        need(Path(birth['executable']).resolve() == Path(POWERSHELL).resolve(), 'Diagnostic worker image differs')
        api.ok(api.assign(job, process.hProcess), 'Assign exact diagnostic worker'); assigned = True
        need(api.resume(process.hThread) != 0xffffffff, 'Resume exact diagnostic worker failed')
        deadline = time.monotonic() + 20
        while api.wait(process.hProcess, 100) == 258:
            check(); need(time.monotonic() < deadline, 'Optional CIM/clock query exceeded20seconds')
        final = api.identity(process.hProcess, process.dwProcessId, birth['executable'], birth['session_id'])
        result['terminal'] = final
        write(output / 'supplemental_worker_terminal.json', result)
        need(final['exited'] and final['creation_filetime'] == birth['creation_filetime'], 'Diagnostic retained terminal differs')
    except BaseException as error:
        result['error'] = error_info(error)
    finally:
        try:
            if created:
                if api.wait(process.hProcess, 0) != 0:
                    api.ok(api.terminate_job(job, 2) if assigned else api.terminate(process.hProcess, 2),
                           'Stop only owned diagnostic query')
                deadline = time.monotonic() + 10
                while True:
                    signaled = api.wait(process.hProcess, 50) == 0
                    account = api.ACCOUNTING()
                    api.ok(api.query_job(job, 1, c.byref(account), c.sizeof(account), None), 'Query diagnostic job accounting')
                    if signaled and account.ActiveProcesses == 0:
                        closed = True; break
                    need(time.monotonic() < deadline, 'Diagnostic query closure unproven')
                result['final_kernel_terminal'] = api.identity(process.hProcess, process.dwProcessId,
                                                               str(POWERSHELL), birth['session_id'])
                result['job_active_processes'] = int(account.ActiveProcesses)
            else:
                closed = True
        except BaseException as error:
            closed = False
            result['closure_error'] = error_info(error)
        finally:
            if created:
                api.close(process.hThread); api.close(process.hProcess)
            api.close(job)
        result['owned_query_closure_proven'] = closed
        write(output / 'supplemental_worker_result.json', result)
    need(closed, 'New diagnostic query closure unknown; original STOP preserved')
    if result.get('error') or result.get('terminal', {}).get('exit_code') != 0:
        return dict(state='OPTIONAL_QUERY_FAILED', lifecycle=result)
    need(sha(script) == CIM_SHA, 'CIM source changed during diagnostic')
    return dict(state='OPTIONAL_QUERY_RETURNED', lifecycle=result,
                data=bounded_json(output / 'supplemental.json', 4 * 1024**2))


def clock_sample(kernel):
    value = c.c_uint64(); kernel.GetSystemTimePreciseAsFileTime(c.byref(value))
    counter, frequency = c.c_int64(), c.c_int64()
    need(kernel.QueryPerformanceCounter(c.byref(counter)) and kernel.QueryPerformanceFrequency(c.byref(frequency)), 'QPC query failed')
    need(frequency.value > 0, 'QPC frequency invalid')
    return dict(utc=utc(), utc_filetime=value.value, qpc=counter.value, qpc_frequency=frequency.value,
                python_monotonic_ns=time.monotonic_ns())


def collect(with_cim=False):
    need(os.name == 'nt' and Path(__file__).resolve().parent == WORK and c.sizeof(PTR) == 8,
         'Exact current C Windows x64 diagnostic required')
    module_path = WORK / 'atomic_iqtree_windows.py'; need(sha(module_path) == API_SHA, 'A80 source differs')
    spec = importlib.util.spec_from_file_location('census_pinned_a80', module_path)
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    need(Path(A.__file__).resolve() == module_path and sha(module_path) == API_SHA, 'A80 import/source differs')
    need(sha(OLD_RESULT) == RESULT_SHA and sha(OLD_SOURCE) == SOURCE_SHA, 'Exact original DriveFS result/source differs')
    old = bounded_json(OLD_RESULT); window = birth_window(old)
    stop = A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
    need(sha(stop) == STOP_SHA, 'Exact original STOP differs; no diagnostic adoption')
    source_sha = sha(__file__); api = A.API(); validate_abi()
    nt = c.WinDLL('ntdll', use_last_error=True).NtQuerySystemInformation
    nt.restype = I32; nt.argtypes = [U32, PTR, U32, c.POINTER(U32)]
    enum = c.WinDLL('psapi', use_last_error=True).EnumProcesses
    enum.restype = c.c_int; enum.argtypes = [c.POINTER(U32), U32, c.POINTER(U32)]
    api.K.GetSystemTimePreciseAsFileTime.restype = None
    api.K.GetSystemTimePreciseAsFileTime.argtypes = [c.POINTER(U64)]
    for name in ('QueryPerformanceCounter', 'QueryPerformanceFrequency'):
        fun = getattr(api.K, name); fun.restype = c.c_int; fun.argtypes = [c.POINTER(c.c_int64)]
    output = WORK / ('stage5_process_census_' + uuid.uuid4().hex)
    output.mkdir()
    result = dict(schema='STAGE05_WINDOWS_PROCESS_CENSUS_DIAGNOSTIC_V1', state='FAILED_OR_PARTIAL_DIAGNOSTIC',
                  output=str(output), source_sha256=source_sha, original_result_sha256=RESULT_SHA,
                  original_stop_sha256=STOP_SHA, owner_nonce=old['owner_nonce'], candidate_window=window,
                  closure_acceptance=False, STOP_removal_authorized=False, historical_terminal_reconstructed=False,
                  native_birth_supported=False, birth_reserved_bytes_interpreted=False,
                  historical_clock_continuity_proven=False, original_owner_exit_proven=False,
                  process_signals_to_observed_population=0, WSL_launches=0, scientific_payload_bytes_read=0)
    deadline = time.monotonic() + 75
    def check():
        need(time.monotonic() < deadline, '75second application diagnostic bound')
        need(sha(stop) == STOP_SHA, 'Original STOP changed during observation')
    lock = A.WorkflowLock(api); handles = []
    write(output / 'started.json', result)
    try:
        with lock:
            result['workflow_lock'] = lock.identity
            result['clock_before'] = clock_sample(api.K)
            result['enum_before'] = enum_pids(enum, check)
            result['native_before'] = native_snapshot(nt, check, output, 'before')
            pids = set(result['enum_before']) | {row['pid'] for row in result['native_before']['records']}
            rows, handles = retained_births(api, pids, check); result['retained_processes'] = rows
            if with_cim:
                result['supplemental'] = powershell_query(api, output, check)
                if result['supplemental']['state'] == 'OPTIONAL_QUERY_RETURNED':
                    result['cim_crossvalidation'] = crossvalidate_cim(rows, result['supplemental']['data'])
            else:
                result['supplemental'] = dict(state='NOT_REQUESTED_UNAVAILABLE_FOR_THIS_DIAGNOSTIC')
            result['native_after'] = native_snapshot(nt, check, output, 'after')
            result['enum_after'] = enum_pids(enum, check)
            after_pids = set(result['enum_after']) | {r['pid'] for r in result['native_after']['records']}
            after_rows, after_handles = retained_births(api, after_pids, check)
            handles.extend(after_handles); result['retained_after'] = after_rows
            result['clock_after'] = clock_sample(api.K)
            before_clock, after_clock = result['clock_before'], result['clock_after']
            need(before_clock['qpc_frequency'] == after_clock['qpc_frequency'], 'QPC frequency changed')
            result['observed_clock_delta'] = dict(
                utc_elapsed_seconds=(after_clock['utc_filetime']-before_clock['utc_filetime'])/10_000_000,
                qpc_elapsed_seconds=(after_clock['qpc']-before_clock['qpc'])/before_clock['qpc_frequency'],
                historical_continuity_inference_allowed=False)
            native_before = {r['pid'] for r in result['native_before']['records']}
            native_after = {r['pid'] for r in result['native_after']['records']}
            result['pid_sets'] = dict(before_native_only=sorted(native_before-set(result['enum_before'])),
                                      before_enum_only=sorted(set(result['enum_before'])-native_before),
                                      after_native_only=sorted(native_after-set(result['enum_after'])),
                                      after_enum_only=sorted(set(result['enum_after'])-native_after),
                                      native_appeared=sorted(native_after-native_before),
                                      native_disappeared=sorted(native_before-native_after))
            result['kernel_birth_candidates'] = dict(before=candidates(rows, window), after=candidates(after_rows, window))
            result['original_owner_observations'] = dict(before=[r for r in rows if r['pid'] == OLD_PID],
                                                       after=[r for r in after_rows if r['pid'] == OLD_PID])
            result['original_owner_exact_birth_seen'] = any(r.get('creation_filetime') == OLD_BIRTH
                                                            for group in result['original_owner_observations'].values() for r in group)
            result['owner_absence_is_exit_proof'] = False
            result['unknown_births'] = dict(before=[r for r in rows if r['pid'] != 0 and r.get('creation_filetime') is None],
                                            after=[r for r in after_rows if r['pid'] != 0 and r.get('creation_filetime') is None])
            result['vetoes'] = ['NO_CLOSURE_AUTHORITY_DIAGNOSTIC_ONLY', 'NATIVE_CREATE_TIME_IS_NOT_A_PUBLIC_SPI_FIELD',
                                'HISTORICAL_CLOCK_CONTINUITY_NOT_ESTABLISHED', 'ORIGINAL_OWNER_KERNEL_TERMINAL_NOT_BOUND']
            if any(result['unknown_births'].values()): result['vetoes'].append('INACCESSIBLE_OR_UNKNOWN_KERNEL_BIRTHS')
            if any(result['kernel_birth_candidates'].values()): result['vetoes'].append('PROCESS_BIRTH_INTERSECTS_CONSERVATIVE_WINDOW')
            if any(result['pid_sets'].values()): result['vetoes'].append('PROCESS_SNAPSHOT_OR_PID_SET_RACES')
            earlier = {r['pid']: r.get('creation_filetime') for r in rows}
            result['pid_birth_changes'] = [r['pid'] for r in after_rows if r['pid'] in earlier
                                           and r.get('creation_filetime') != earlier[r['pid']]]
            if result['pid_birth_changes']: result['vetoes'].append('PID_REUSE_OR_BIRTH_QUERY_CHANGED')
            if result['supplemental']['state'] == 'OPTIONAL_QUERY_RETURNED':
                data = result['supplemental']['data']; census = data.get('process_census', {})
                if census.get('state') != 'PROVIDER_QUERY_COMPLETED_SUPPLEMENTAL_ONLY' or census.get('truncated') is not False:
                    result['vetoes'].append('CIM_QUERY_INCOMPLETE_OR_UNKNOWN')
                if any(r['state'] != 'MATCH_WITHIN_CIM_MICROSECOND_PRECISION' and r['pid'] != 0
                       for r in result.get('cim_crossvalidation', [])):
                    result['vetoes'].append('CIM_KERNEL_BIRTH_UNKNOWN_MISMATCH_OR_RACE')
                cim_pids = {r['pid'] for r in census.get('rows', [])}
                result['cim_pid_differences'] = dict(native_before_missing=sorted(native_before-cim_pids),
                                                     native_after_missing=sorted(native_after-cim_pids),
                                                     cim_only=sorted(cim_pids-(native_before|native_after)))
                if any(result['cim_pid_differences'].values()): result['vetoes'].append('CIM_NATIVE_PID_COVERAGE_RACE')
                result['cim_birth_candidates'] = [r for r in census.get('rows', [])
                    if r.get('birth_filetime') is not None and window['inclusive_lower_filetime'] <= int(r['birth_filetime']) <= window['inclusive_upper_filetime']]
                if result['cim_birth_candidates']: result['vetoes'].append('CIM_BIRTH_INTERSECTS_WINDOW_SUPPLEMENTAL_ONLY')
            else:
                result['vetoes'].append('CIM_UNAVAILABLE_OR_FAILED')
            if abs(result['observed_clock_delta']['utc_elapsed_seconds']-result['observed_clock_delta']['qpc_elapsed_seconds']) > 0.1:
                result['vetoes'].append('OBSERVED_UTC_QPC_DISCONTINUITY_OR_SAMPLE_LATENCY')
            need(sha(__file__) == source_sha and sha(module_path) == API_SHA and sha(OLD_RESULT) == RESULT_SHA
                 and sha(OLD_SOURCE) == SOURCE_SHA and sha(stop) == STOP_SHA, 'Source/original controls changed')
            result['state'] = 'READ_ONLY_DIAGNOSTIC_COMPLETED_NO_CLOSURE_ACCEPTANCE'
    except BaseException as error:
        result['error'] = error_info(error)
    finally:
        for _, handle in handles:
            api.close(handle)
        result['original_lock_released'] = lock.released
        result['original_STOP_unchanged'] = sha(stop) == STOP_SHA
        result['utc'] = utc(); write(output / 'receipt.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--with-cim', action='store_true')
    args = parser.parse_args()
    if not args.run:
        print(json.dumps(dict(state='PREPARED_NOT_RUN', Windows_queries=0, STOP_mutations=0, WSL_launches=0)))
        return 0
    result = collect(args.with_cim)
    print(json.dumps(dict(state=result['state'], receipt=result['output'] + '/receipt.json')))
    return 0 if result['state'] == 'READ_ONLY_DIAGNOSTIC_COMPLETED_NO_CLOSURE_ACCEPTANCE' else 2


if __name__ == '__main__':
    raise SystemExit(main())
