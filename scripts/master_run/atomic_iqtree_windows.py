"""One explicitly authorized, hash-pinned native Windows IQ-TREE inference.

Win32 structures/lifecycle adapted from LAB R-M repository
scripts/stage04_windows_job_v6.py and stage04_windows_job_v10.py at
2a7552bc5556d5ff82cc44602bc366e51e25ff47. Their original authors/notices and
history remain in the canonical repository. This independent new file does not
alter or import frozen prior producers and does not perform tree validation.

No inference occurs without --run. A native exit0 is VALIDATION_REQUIRED, never
scientific PASS. The parent must invoke its distinct independent checker.
"""
from __future__ import annotations

import argparse
import ctypes as c
from ctypes import wintypes as w
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

GIB = 1024 ** 3
PREFERRED_CAP = 9 * GIB // 2
RESERVE = 3 * GIB // 2
EXPECTED_ALIGNMENT = '442742d083628ab5382a10cafc422c57084cd9bde45a4f2950f15e2c199e3307'
EXPECTED_PARTITIONS = 'fa640e5e984b33e73a86b1ec7a7c18f7161a12252e68e9e3c6ceb2644eb7edc5'
EXPECTED_PANEL = '85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'
EXPECTED_EXE = '43c9bf3b0dc5e7d88c183a2582369d22c9d692b7585350038769334bb6fd9aed'
ORIGINAL_LOCK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\workflow.lock')
LOCK_IDENTITY = (2430728143, 844424932784519, 134359335921635133)
CANONICAL = 'serg-alexv/lab-rm-phylogenomics-196'
SHA = re.compile(r'^[0-9a-f]{64}$')
COMMIT = re.compile(r'^[0-9a-f]{40}$')
SELECTED_SCRIPT = re.compile(
    r'(?:^|[\\/\s"\x27])(?:stage04_(?:controller|inference_controller_v\d+|'
    r'native_windows_v\d+|recovery_controller_v\d+(?:_admission_v\d+)?|'
    r'recovery_fixture_v\d+|linux_launcher)|stage05_(?:detectors_windows_v\d+|'
    r'inventory_windows_v\d+))\.py(?:\s|$|["\x27])', re.I)


def require(value, message):
    if not value:
        raise ValueError(message)


class OwnedClosureFailure(RuntimeError):
    """A new owned child/job did not produce required terminal proof; no fallback."""


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def pinned(item, expected=None):
    require(isinstance(item, dict) and SHA.fullmatch(item.get('sha256', '')), 'Malformed pinned input')
    path = Path(item['path'])
    require(path.is_absolute() and path.is_file(), 'Pinned input is not an existing absolute file: ' + str(path))
    actual = sha256(path)
    require(actual == item['sha256'], 'Pinned file changed: ' + str(path))
    if expected:
        require(actual == expected, 'Accepted input identity differs: ' + str(path))
    return path.resolve()


def validate_config(cfg):
    require(cfg.get('schema') == 'LAB_RM_ATOMIC_IQTREE_V1', 'Wrong configuration schema')
    require(cfg.get('mode') in ('partitioned', 'single_model'), 'Unknown scientific mode')
    require(COMMIT.fullmatch(cfg.get('canonical_commit', '')), 'Pin an exact remote main commit')
    require(cfg.get('run_control_state') == 'ACTIVE_DIRECT_USER_CONTINUATION', 'Explicit refreshed run-control authority required')
    require(cfg.get('threads') == 2 and cfg.get('seed') == 1961008, 'Frozen thread/seed contract differs')
    budget = cfg['budget']
    cap, reserve = budget['cap_bytes'], budget['reserve_bytes']
    require(type(cap) is int and type(reserve) is int and cap > 0 and reserve >= RESERVE, 'Invalid memory envelope/reserve')
    if cfg['mode'] == 'partitioned':
        require(cap == PREFERRED_CAP and 'iqtree_memory_mib' not in cfg, 'Preferred partition cap4.5GiB; omit incompatible --mem')
    else:
        require(cap == 7*GIB//2 and cfg.get('iqtree_memory_mib') == 2048 and 'resource_estimate_evidence' in cfg,
                'Reviewed fallback requires3.5GiB external cap, native --mem2G and pinned independent estimate')
    require(0 < cfg.get('runtime_seconds', 86400) <= 86400, 'Runtime must be bounded at24h or less')
    require(0 <= cfg.get('admission_seconds', 1800) <= 1800, 'Admission wait must be bounded at30min or less')
    tasks = cfg.get('expected_disabled_tasks', [])
    require(len(tasks) == len(set(tasks)) == 18 and all(t.startswith('LAB_RM_') for t in tasks), 'Pin all18disabled LAB tasks')
    output = Path(cfg['output_directory'])
    require(output.is_absolute() and output.drive.lower() == 'c:' and not output.exists(), 'Use new unique local C output namespace')
    require(output != ORIGINAL_LOCK.parent and ORIGINAL_LOCK.parent not in output.parents,
            'Use a separate new C spool, not original lock/history directory')
    require('argv' not in cfg and 'extra_args' not in cfg, 'Scientific arguments are constructed, not arbitrary')
    if 'iqtree_memory_mib' in cfg:
        mib = cfg['iqtree_memory_mib']
        require(type(mib) is int and 0 < mib * 1024 ** 2 <= cap - 256 * 1024 ** 2,
                'Native single-model --mem must leave external-cap headroom')
    if cfg['mode'] == 'single_model':
        require('partitions' not in cfg and 'cache_import' not in cfg, 'Do not import partition cache into single-model fallback')
    if 'cache_import' in cfg:
        require('cache_compatibility_evidence' in cfg, 'Partial cache import requires a pinned compatibility certificate')
    return cfg


def scientific_argv(cfg, exe, alignment, prefix, partitions=None):
    argv = [str(exe), '-s', str(alignment), '--seqtype', 'AA']
    if cfg['mode'] == 'partitioned':
        require(partitions is not None, 'Partition map required')
        argv += ['-p', str(partitions)]
    argv += ['-m', 'MFP', '-B', '1000', '--alrt', '1000', '--seed', '1961008',
             '-T', '2', '-keep-ident', '--boot-trees', '--prefix', str(prefix)]
    if cfg['mode'] == 'single_model' and 'iqtree_memory_mib' in cfg:
        argv += ['--mem', '2G', '--thread-site']
    return argv


class Win:
    """Only native declarations and one owned job; no legacy controller imports."""
    def __init__(self):
        require(os.name == 'nt' and c.sizeof(c.c_void_p) == 8, 'Windows64required')
        self.K = c.WinDLL('kernel32', use_last_error=True)
        self.P = c.WinDLL('psapi', use_last_error=True)
        SIZE = c.c_size_t
        class IO(c.Structure):
            _fields_ = [(n, c.c_uint64) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
        class BASIC(c.Structure):
            _fields_ = [('PerProcessUserTimeLimit',c.c_int64),('PerJobUserTimeLimit',c.c_int64),('LimitFlags',w.DWORD),('MinimumWorkingSetSize',SIZE),('MaximumWorkingSetSize',SIZE),('ActiveProcessLimit',w.DWORD),('Affinity',SIZE),('PriorityClass',w.DWORD),('SchedulingClass',w.DWORD)]
        class EXTENDED(c.Structure):
            _fields_ = [('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',SIZE),('JobMemoryLimit',SIZE),('PeakProcessMemoryUsed',SIZE),('PeakJobMemoryUsed',SIZE)]
        class STARTUP(c.Structure):
            _fields_ = [('cb',w.DWORD),('lpReserved',w.LPWSTR),('lpDesktop',w.LPWSTR),('lpTitle',w.LPWSTR),('dwX',w.DWORD),('dwY',w.DWORD),('dwXSize',w.DWORD),('dwYSize',w.DWORD),('dwXCountChars',w.DWORD),('dwYCountChars',w.DWORD),('dwFillAttribute',w.DWORD),('dwFlags',w.DWORD),('wShowWindow',w.WORD),('cbReserved2',w.WORD),('lpReserved2',c.POINTER(c.c_byte)),('hStdInput',w.HANDLE),('hStdOutput',w.HANDLE),('hStdError',w.HANDLE)]
        class PROCESS(c.Structure):
            _fields_ = [('hProcess',w.HANDLE),('hThread',w.HANDLE),('dwProcessId',w.DWORD),('dwThreadId',w.DWORD)]
        class ACCOUNTING(c.Structure):
            _fields_ = [(n,c.c_int64) for n in ('TotalUserTime','TotalKernelTime','ThisPeriodTotalUserTime','ThisPeriodTotalKernelTime')] + [(n,w.DWORD) for n in ('TotalPageFaultCount','TotalProcesses','ActiveProcesses','TotalTerminatedProcesses')]
        class PIDS(c.Structure):
            _fields_ = [('assigned',w.DWORD),('listed',w.DWORD),('ids',SIZE * 64)]
        class MEMORY(c.Structure):
            _fields_ = [('cb',w.DWORD),('PageFaultCount',w.DWORD)] + [(n,SIZE) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
        class PERF(c.Structure):
            _fields_ = [('cb',w.DWORD)] + [(n,SIZE) for n in ('CommitTotal','CommitLimit','CommitPeak','PhysicalTotal','PhysicalAvailable','SystemCache','KernelTotal','KernelPaged','KernelNonpaged','PageSize')] + [(n,w.DWORD) for n in ('HandleCount','ProcessCount','ThreadCount')]
        class FILEINFO(c.Structure):
            _fields_ = [('attributes',w.DWORD),('created',w.FILETIME),('accessed',w.FILETIME),('written',w.FILETIME),('volume',w.DWORD),('sizeHigh',w.DWORD),('sizeLow',w.DWORD),('links',w.DWORD),('indexHigh',w.DWORD),('indexLow',w.DWORD)]
        for name, value in locals().copy().items():
            if isinstance(value, type) and issubclass(value, c.Structure):
                setattr(self, name, value)
        def bind(lib, name, restype, args):
            fn = getattr(lib, name); fn.restype = restype; fn.argtypes = args
            return fn
        self.create_job = bind(self.K,'CreateJobObjectW',w.HANDLE,[c.c_void_p,w.LPCWSTR])
        self.set_job = bind(self.K,'SetInformationJobObject',w.BOOL,[w.HANDLE,c.c_int,c.c_void_p,w.DWORD])
        self.query_job = bind(self.K,'QueryInformationJobObject',w.BOOL,[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.c_void_p])
        self.create = bind(self.K,'CreateProcessW',w.BOOL,[w.LPCWSTR,w.LPWSTR,c.c_void_p,c.c_void_p,w.BOOL,w.DWORD,c.c_void_p,w.LPCWSTR,c.POINTER(STARTUP),c.POINTER(PROCESS)])
        self.assign = bind(self.K,'AssignProcessToJobObject',w.BOOL,[w.HANDLE,w.HANDLE])
        self.resume = bind(self.K,'ResumeThread',w.DWORD,[w.HANDLE])
        self.wait = bind(self.K,'WaitForSingleObject',w.DWORD,[w.HANDLE,w.DWORD])
        self.exit_code = bind(self.K,'GetExitCodeProcess',w.BOOL,[w.HANDLE,c.POINTER(w.DWORD)])
        self.times = bind(self.K,'GetProcessTimes',w.BOOL,[w.HANDLE] + [c.POINTER(w.FILETIME)] * 4)
        self.affinity = bind(self.K,'GetProcessAffinityMask',w.BOOL,[w.HANDLE,c.POINTER(SIZE),c.POINTER(SIZE)])
        self.current = bind(self.K,'GetCurrentProcess',w.HANDLE,[])
        self.close = bind(self.K,'CloseHandle',w.BOOL,[w.HANDLE])
        self.terminate_job = bind(self.K,'TerminateJobObject',w.BOOL,[w.HANDLE,w.UINT])
        self.terminate = bind(self.K,'TerminateProcess',w.BOOL,[w.HANDLE,w.UINT])
        self.mem = bind(self.P,'GetProcessMemoryInfo',w.BOOL,[w.HANDLE,c.POINTER(MEMORY),w.DWORD])
        self.performance = bind(self.P,'GetPerformanceInfo',w.BOOL,[c.POINTER(PERF),w.DWORD])
        self.image = bind(self.K,'QueryFullProcessImageNameW',w.BOOL,[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)])
        self.in_job = bind(self.K,'IsProcessInJob',w.BOOL,[w.HANDLE,w.HANDLE,c.POINTER(w.BOOL)])
        self.file_info = bind(self.K,'GetFileInformationByHandle',w.BOOL,[w.HANDLE,c.POINTER(FILEINFO)])
        self.session = bind(self.K,'ProcessIdToSessionId',w.BOOL,[w.DWORD,c.POINTER(w.DWORD)])
        self.execution_state = bind(self.K,'SetThreadExecutionState',w.DWORD,[w.DWORD])

    @staticmethod
    def ok(value, operation):
        if not value:
            raise c.WinError(c.get_last_error(), operation)

    @staticmethod
    def ft(value):
        return (value.dwHighDateTime << 32) | value.dwLowDateTime

    def identity(self, handle, pid, retained_image=None, retained_session=None):
        values = [w.FILETIME() for _ in range(4)]
        self.ok(self.times(handle, *(c.byref(x) for x in values)), 'GetProcessTimes')
        state = self.wait(handle, 0); require(state in (0,258), 'Process wait failed')
        text = c.create_unicode_buffer(32768); size = w.DWORD(len(text))
        if not self.image(handle,0,text,c.byref(size)):
            require(state == 0 and retained_image is not None, 'Actual live executable image query failed')
            text.value = retained_image
        code = w.DWORD(); self.ok(self.exit_code(handle,c.byref(code)), 'GetExitCodeProcess')
        session = w.DWORD()
        if state == 0:
            require(retained_session is not None, 'Retain live SessionID before process exit')
            session.value = retained_session
        else:
            self.ok(self.session(pid,c.byref(session)), 'Actual live process SessionID query')
        return {'pid':pid,'creation_filetime':self.ft(values[0]),'exit_filetime':self.ft(values[1]),
                'cpu_seconds':(self.ft(values[2])+self.ft(values[3]))/1e7,'executable':text.value,
                'session_id':session.value,'exited':state == 0,'exit_code':code.value if state == 0 else None}

    def outer_job(self, planned_cap):
        bound = w.BOOL(); self.ok(self.in_job(self.current(),None,c.byref(bound)), 'Controller outer-job membership')
        if not bound.value:
            return {'associated':False}
        actual = self.EXTENDED()
        self.ok(self.query_job(None,9,c.byref(actual),c.sizeof(actual),None), 'Controller inherited job controls')
        flags = actual.BasicLimitInformation.LimitFlags
        require(not (flags & 0x100) or actual.ProcessMemoryLimit >= planned_cap, 'Inherited process cap defeats new resource envelope')
        require(not (flags & 0x200) or actual.JobMemoryLimit >= planned_cap, 'Inherited aggregate cap defeats new resource envelope')
        return {'associated':True,'limit_flags':flags,'process_memory_cap_bytes':actual.ProcessMemoryLimit,
                'job_memory_cap_bytes':actual.JobMemoryLimit,'owner_or_lifetime':'NOT_PROVED_BY_MEMBERSHIP'}

    def job_state(self, job):
        peak = self.EXTENDED(); account = self.ACCOUNTING(); pids = self.PIDS()
        for kind, obj in ((9,peak),(1,account),(3,pids)):
            self.ok(self.query_job(job,kind,c.byref(obj),c.sizeof(obj),None), 'QueryInformationJobObject')
        require(pids.assigned == pids.listed <= 64, 'Incomplete owned-job PID list')
        return {'peak_process_committed_bytes':peak.PeakProcessMemoryUsed,'peak_job_committed_bytes':peak.PeakJobMemoryUsed,
                'job_cpu_seconds':(account.TotalUserTime+account.TotalKernelTime)/1e7,
                'job_active_processes':account.ActiveProcesses,'job_pids':list(pids.ids[:pids.listed])}

    def resources(self, paths):
        info = self.PERF(); info.cb = c.sizeof(info)
        self.ok(self.performance(c.byref(info),c.sizeof(info)), 'GetPerformanceInfo')
        disks = {}
        for path in paths:
            path = Path(path)
            while not path.exists():
                require(path != path.parent, 'No existing disk ancestor')
                path = path.parent
            disks[str(path)] = shutil.disk_usage(path).free
        return {'utc':utc(),'physical_available_bytes':info.PhysicalAvailable*info.PageSize,
                'commit_headroom_bytes':(info.CommitLimit-info.CommitTotal)*info.PageSize,
                'commit_total_bytes':info.CommitTotal*info.PageSize,'commit_limit_bytes':info.CommitLimit*info.PageSize,
                'disk_available_bytes':disks}


class WorkflowLock:
    def __init__(self, api):
        self.api = api; self.stream = None; self.released = False

    def __enter__(self):
        import msvcrt
        require(ORIGINAL_LOCK.is_file(), 'Original workflow lock missing; never recreate it')
        self.stream = ORIGINAL_LOCK.open('r+b')
        try:
            self.stream.seek(0); msvcrt.locking(self.stream.fileno(),msvcrt.LK_NBLCK,1)
            info = self.api.FILEINFO()
            self.api.ok(self.api.file_info(msvcrt.get_osfhandle(self.stream.fileno()),c.byref(info)), 'Workflow lock identity')
            identity = (info.volume,(info.indexHigh<<32)|info.indexLow,self.api.ft(info.created))
            require(identity == LOCK_IDENTITY, 'Stable original workflow lock identity differs')
            self.identity = {'path':str(ORIGINAL_LOCK),'volume_serial':identity[0],'file_index':identity[1],
                             'creation_filetime':identity[2],'locked_byte':0}
            return self
        except BaseException:
            self.stream.close(); self.stream = None; raise

    def __exit__(self, *unused):
        import msvcrt
        if self.stream:
            self.stream.seek(0); msvcrt.locking(self.stream.fileno(),msvcrt.LK_UNLCK,1)
            self.released = True; self.stream.close()


def command(argv, cwd=None, timeout=30):
    result = subprocess.run(argv,cwd=cwd,capture_output=True,timeout=timeout,check=False)
    require(result.returncode == 0, 'Bounded prerequisite command failed: ' + str(argv[0]))
    return result.stdout.decode('utf-8-sig').strip()


def authority(cfg):
    repo = Path(cfg['repository_path']).resolve()
    remote = command(['gh','api',f'repos/{CANONICAL}/commits/main','--jq','.sha'])
    require(remote == cfg['canonical_commit'], 'Canonical main changed; reconcile before launch')
    local = command(['git','rev-parse','HEAD'],cwd=repo)
    require(local == remote, 'Local HEAD differs from pinned canonical main')
    require(command(['git','remote','get-url','origin'],cwd=repo).rstrip('/').removesuffix('.git') in
            (f'https://github.com/{CANONICAL}',f'git@github.com:{CANONICAL}'), 'Wrong canonical origin')
    control = pinned(cfg['run_control'])
    require(control == (repo/'status/run_control.json').resolve(), 'Authority must be canonical run_control.json')
    data = read_json(control)
    require(data.get('state') == cfg['run_control_state'] and data.get('automatic_resume') is False,
            'Run control still halted or not explicitly authorized')
    tracked = command(['git','hash-object','status/run_control.json'],cwd=repo)
    committed = command(['git','rev-parse','HEAD:status/run_control.json'],cwd=repo)
    require(tracked == committed, 'Run control has unpublished changes')
    return {'canonical_commit':remote,'run_control_sha256':sha256(control)}


def inspect_owners(cfg):
    script = r'''$ErrorActionPreference='Stop'; $p=@(Get-CimInstance Win32_Process | ForEach-Object {
    [pscustomobject]@{pid=$_.ProcessId;name=$_.Name;image=$_.ExecutablePath;argv=$_.CommandLine;
    born=if($_.CreationDate){$_.CreationDate.ToUniversalTime().ToFileTimeUtc()}else{0}}});
    $t=@(Get-ScheduledTask | Where-Object {$_.TaskName -like 'LAB_RM_*'} | ForEach-Object {
    [pscustomobject]@{name=$_.TaskName;path=$_.TaskPath;state=[string]$_.State}});
    [pscustomobject]@{processes=$p;tasks=$t} | ConvertTo-Json -Depth 5 -Compress'''
    inventory = json.loads(command([cfg['powershell'],'-NoProfile','-NonInteractive','-Command',script]))
    tasks = inventory['tasks']
    require(len(tasks) == 18 and {r['name'] for r in tasks} == set(cfg['expected_disabled_tasks']) and
            all(r['state'] == 'Disabled' for r in tasks), 'All18pinned LAB tasks must remain disabled')
    selected = []
    native_names = {'iqtree.exe','iqtree2.exe','iqtree3.exe','raxml-ng.exe','hmmsearch.exe','hmmscan.exe','padloc.exe','defense-finder.exe'}
    for row in inventory['processes']:
        if row['pid'] == os.getpid():
            continue
        name = row['name'].lower(); argv = row.get('argv') or ''
        if name in native_names or SELECTED_SCRIPT.search(argv) or 'atomic_iqtree_windows.py' in argv:
            # The launcher PowerShell may contain the current script name. Its
            # identity is not automatically a scientific owner; only actual
            # Python runtimes or known native scientific processes qualify.
            if name in native_names or name in ('python.exe','pythonw.exe','wsl.exe','bash.exe'):
                selected.append(row)
        elif name in ('python.exe','pythonw.exe') and row.get('argv') is None:
            selected.append({**row,'classification':'UNRESOLVED_PYTHON_COMMAND_LINE'})
    require(not selected, 'Selected scientific owner or unresolved runtime exists: ' + json.dumps(selected))
    guests = subprocess.run([r'C:\Windows\System32\wsl.exe','--list','--running','--quiet'],
                            capture_output=True,timeout=30,check=False)
    require(guests.returncode == 0, 'Read-only running-WSL inventory failed')
    guest_text = guests.stdout.decode('utf-16-le' if b'\x00' in guests.stdout else 'utf-8-sig').strip('\ufeff\x00\r\n ')
    require(not guest_text, 'Running WSL guest may contain an unobserved scientific owner; reconcile before native launch')
    return {'utc':utc(),'selected_live_owners':selected,'disabled_tasks':tasks,'running_wsl_guests':[]}


def admission_passes(cfg, row):
    required = cfg['budget']['cap_bytes'] + cfg['budget']['reserve_bytes']
    return (row['physical_available_bytes'] >= required and row['commit_headroom_bytes'] >= required and
            min(row['disk_available_bytes'].values()) > 5*GIB)


def wait_admission(cfg, api, directory, paths):
    stop = time.monotonic() + cfg.get('admission_seconds',1800)
    while True:
        row = api.resources(paths); row['admitted'] = admission_passes(cfg,row)
        row['required_memory_bytes'] = cfg['budget']['cap_bytes'] + cfg['budget']['reserve_bytes']
        atomic(directory/'admission.json',row)
        with (directory/'admission_observations.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n'); stream.flush(); os.fsync(stream.fileno())
        if row['admitted']:
            return row
        if time.monotonic() >= stop:
            return None
        time.sleep(min(30,max(0,stop-time.monotonic())))


def run_native(cfg, api, directory, argv, authority_receipt, lock_receipt):
    import msvcrt
    allowed, system = c.c_size_t(), c.c_size_t()
    api.ok(api.affinity(api.current(),c.byref(allowed),c.byref(system)), 'Controller affinity')
    bits = [1<<i for i in range(64) if allowed.value & (1<<i)]
    require(len(bits) >= 2 and allowed.value & 5 == 5,
            'Previously verified distinct physical-core mask5 unavailable; new topology review required')
    mask = 5
    inherited_job = api.outer_job(cfg['budget']['cap_bytes'])
    job = api.create_job(None,None); api.ok(job,'CreateJobObjectW')
    process = api.PROCESS(); launched = None; final_receipt = None; resumed = False; created_identity = None
    power_request = None
    observational_errors = []; start = time.monotonic(); last_cpu = 0; last_files = None
    last_activity = start; diagnosed = False
    def observe(path, row):
        try:
            atomic(path,row)
        except (OSError,ValueError) as error:
            observational_errors.append({'utc':utc(),'operation':path.name,'kind':type(error).__name__})
    try:
        power_request = api.execution_state(0x80000001)
        api.ok(power_request,'SetThreadExecutionState transient ES_SYSTEM_REQUIRED')
        controls = api.EXTENDED(); controls.BasicLimitInformation.LimitFlags = 0x2310
        controls.BasicLimitInformation.Affinity = mask
        controls.ProcessMemoryLimit = controls.JobMemoryLimit = cfg['budget']['cap_bytes']
        api.ok(api.set_job(job,9,c.byref(controls),c.sizeof(controls)), 'SetInformationJobObject')
        actual = api.EXTENDED(); api.ok(api.query_job(job,9,c.byref(actual),c.sizeof(actual),None), 'Query controls')
        require(actual.BasicLimitInformation.LimitFlags == 0x2310 and actual.BasicLimitInformation.Affinity == mask and
                actual.ProcessMemoryLimit == actual.JobMemoryLimit == cfg['budget']['cap_bytes'], 'Queried owned-job controls differ')
        with open(os.devnull,'rb') as null, (directory/'stdout.txt').open('wb') as out, (directory/'stderr.txt').open('wb') as err:
            handles = [msvcrt.get_osfhandle(f.fileno()) for f in (null,out,err)]
            try:
                for handle in handles:
                    os.set_handle_inheritable(handle,True)
                si = api.STARTUP(); si.cb = c.sizeof(si); si.dwFlags = 0x100
                si.hStdInput, si.hStdOutput, si.hStdError = handles
                command_line = c.create_unicode_buffer(subprocess.list2cmdline(argv))
                api.ok(api.create(argv[0],command_line,None,None,True,0x4|0x08000000,None,str(directory),c.byref(si),c.byref(process)), 'Create suspended child')
            finally:
                for handle in handles:
                    os.set_handle_inheritable(handle,False)
            created_identity = api.identity(process.hProcess,process.dwProcessId)
            api.ok(api.assign(job,process.hProcess), 'Assign suspended child to owned job')
            identity = created_identity
            require(Path(identity['executable']).resolve() == Path(argv[0]).resolve() and not identity['exited'], 'Wrong suspended native identity')
            child_mask, sysmask = c.c_size_t(), c.c_size_t(); bound = w.BOOL()
            api.ok(api.affinity(process.hProcess,c.byref(child_mask),c.byref(sysmask)), 'Actual suspended affinity')
            api.ok(api.in_job(process.hProcess,job,c.byref(bound)), 'Actual child-job membership')
            require(child_mask.value == mask and bound.value, 'Suspended child controls differ')
            launched = {'utc':utc(),'argv':argv,'cwd':str(directory),'native':identity,
                        'controller':api.identity(api.current(),os.getpid()),'authority':authority_receipt,
                        'workflow_lock':lock_receipt,'config_sha256':cfg['_config_sha256'],
                        'runner_sha256':sha256(__file__),'executable_sha256':sha256(argv[0]),
                        'cap_bytes':cfg['budget']['cap_bytes'],'reserve_bytes':cfg['budget']['reserve_bytes'],
                        'affinity_mask':mask,'job_bound_before_resume':True,'job_limit_flags':0x2310,
                        'inherited_controller_job':inherited_job,
                        'transient_idle_sleep_prevention':{'requested_flags':0x80000001,'previous_thread_state':power_request,
                            'scope':'Only this controller thread; no permanent power preference change'},
                        'runtime_seconds':cfg.get('runtime_seconds',86400),'session_limit':'Account signed in; no power/logoff survival claim'}
            atomic(directory/'launch.json',launched)
            require(api.resume(process.hThread) == 1, 'Resume native exactly once')
            resumed = True; api.close(process.hThread); process.hThread = None
            next_progress = 0
            while True:
                state = api.wait(process.hProcess,1000); require(state in (0,258), 'Native wait failed')
                elapsed = time.monotonic()-start
                if state != 0 and elapsed >= cfg.get('runtime_seconds',86400):
                    raise TimeoutError('Owned native exceeded bounded wall runtime')
                if time.monotonic() >= next_progress or state == 0:
                    identity = api.identity(process.hProcess,process.dwProcessId,launched['native']['executable'],launched['native']['session_id'])
                    require(identity['creation_filetime'] == launched['native']['creation_filetime'], 'Held native birth changed')
                    row = {**identity,**api.job_state(job),'utc':utc(),'elapsed_seconds':elapsed}
                    memory = api.MEMORY(); memory.cb = c.sizeof(memory)
                    # Telemetry failures are observational, not lifecycle failure.
                    if api.mem(process.hProcess,c.byref(memory),c.sizeof(memory)):
                        row.update(working_set_bytes=memory.WorkingSetSize,peak_working_set_bytes=memory.PeakWorkingSetSize,
                                   private_committed_bytes=memory.PrivateUsage)
                    observe(directory/'progress.json',row)
                    try:
                        files = tuple((p.name,p.stat().st_size,p.stat().st_mtime_ns) for p in directory.glob('host.*'))
                    except OSError:
                        files = last_files
                    if identity['cpu_seconds'] > last_cpu or files != last_files:
                        last_activity = time.monotonic(); last_cpu = identity['cpu_seconds']; last_files = files
                    if not diagnosed and time.monotonic()-last_activity >= 1800:
                        diagnosed = True
                        try:
                            diagnosis = {'utc':utc(),'reason':'NO_NATIVE_CPU_OR_OUTPUT_ACTIVITY_FOR30MIN',
                                         'native':row,'resources':api.resources([directory,Path(cfg['alignment']['path'])]),
                                         'action':'Diagnostic only; no relaunch, no inferred failure cause'}
                            observe(directory/'no_progress_diagnostic.json',diagnosis)
                        except Exception as error:
                            observational_errors.append({'utc':utc(),'operation':'no_progress_diagnostic','kind':type(error).__name__})
                    next_progress = time.monotonic()+30
                if state == 0:
                    break
            identity = api.identity(process.hProcess,process.dwProcessId,launched['native']['executable'],launched['native']['session_id'])
            require(identity['exited'] and identity['exit_filetime'] > 0 and
                    identity['creation_filetime'] == launched['native']['creation_filetime'], 'Exact native terminal proof missing')
            empty = api.job_state(job); stop = time.monotonic()+10
            while (empty['job_active_processes'] or empty['job_pids']) and time.monotonic() < stop:
                time.sleep(.1); empty = api.job_state(job)
            require(empty['job_active_processes'] == 0 and empty['job_pids'] == [], 'New owned descendants remain after native exit')
            final_receipt = {'utc':utc(),'native':identity,**empty,'elapsed_seconds':time.monotonic()-start,
                             'launch_sha256':sha256(directory/'launch.json'),'observational_errors':observational_errors,
                             'execution':'NATIVE_EXITED','scientific_validation':'REQUIRED_DISTINCT_INDEPENDENT_CHECKER',
                             'transient_power_request_release':'ACTUAL_RELEASE_RECEIPT_WRITTEN_IN_FINALLY',
                             'state':'VALIDATION_REQUIRED' if identity['exit_code'] == 0 else 'FAILED_RETRYABLE'}
            atomic(directory/'exit.json',final_receipt)
            return final_receipt
    except BaseException as error:
        exception = {'utc':utc(),'kind':type(error).__name__,'message':str(error),'state':'FAILED_RETRYABLE',
                     'scientific_validation':'NOT_PERFORMED','ordinary_exit_receipt':False,'launch_present':launched is not None}
        if process.hProcess:
            # This exact newly created child/job only. A failed assignment can
            # leave our suspended child outside the job, hence exact-handle kill.
            exception['owned_job_termination_requested'] = bool(api.terminate_job(job,125))
            exception['exact_child_termination_requested'] = bool(api.terminate(process.hProcess,125))
            exception['exact_child_wait_result'] = api.wait(process.hProcess,10000)
            try:
                exception['native_observation'] = api.identity(process.hProcess,process.dwProcessId,
                    created_identity['executable'] if created_identity else argv[0],created_identity['session_id'] if created_identity else None)
                remaining = api.job_state(job); end = time.monotonic()+10
                while (remaining['job_active_processes'] or remaining['job_pids']) and time.monotonic() < end:
                    time.sleep(.1); remaining = api.job_state(job)
                exception['owned_job_observation'] = remaining
                exception['owned_job_empty_confirmed'] = remaining['job_active_processes'] == 0 and remaining['job_pids'] == []
                observed = exception['native_observation']
                exception['exact_child_exit_confirmed'] = (exception['exact_child_wait_result'] == 0 and
                    observed['exited'] and observed['exit_filetime'] > 0 and created_identity is not None and
                    observed['creation_filetime'] == created_identity['creation_filetime'])
                if not exception['owned_job_empty_confirmed'] or not exception['exact_child_exit_confirmed']:
                    exception['state'] = 'FAILED_FATAL'
                    exception['required_parent_action'] = 'Do not launch any fallback until new owned-job closure is reconciled'
            except Exception as query_error:
                exception['closure_query_error'] = type(query_error).__name__
                exception['state'] = 'FAILED_FATAL'
                exception['required_parent_action'] = 'Do not launch any fallback without exact child exit and empty-job proof'
        observe(directory/'exception.json',exception)
        if exception['state'] == 'FAILED_FATAL':
            raise OwnedClosureFailure('Actual new owned child/job closure proof missing; no fallback authorized') from error
        raise
    finally:
        if process.hThread:
            api.close(process.hThread)
        if process.hProcess:
            api.close(process.hProcess)
        api.close(job)  # KILL_ON_JOB_CLOSE applies exclusively to this owned job.
        if power_request:
            restored = api.execution_state(0x80000000)
            observe(directory/'execution_state_restored.json',{'utc':utc(),'requested_flags':0x80000000,
                'actual_api_success':bool(restored),'previous_thread_state_returned':restored,
                'winerror':None if restored else c.get_last_error()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--run',action='store_true',help='Explicit actual native launch; otherwise check only')
    args = parser.parse_args()
    cfg = validate_config(read_json(args.config)); cfg['_config_sha256'] = sha256(args.config)
    exe = pinned(cfg['executable'],EXPECTED_EXE); alignment = pinned(cfg['alignment'],EXPECTED_ALIGNMENT)
    panel = pinned(cfg['approved_accessions'],EXPECTED_PANEL)
    ids = panel.read_text().splitlines(); require(len(ids) == len(set(ids)) == 196, 'Approved panel membership changed')
    partitions = pinned(cfg['partitions'],EXPECTED_PARTITIONS) if cfg['mode'] == 'partitioned' else None
    if 'resource_estimate_evidence' in cfg:
        estimate = read_json(pinned(cfg['resource_estimate_evidence']))
        recommendation = estimate['recommendation']
        require(cfg['mode'] == 'single_model' and estimate['alignment_sha256'] == EXPECTED_ALIGNMENT and
                estimate['native_binary_sha256'] == EXPECTED_EXE and estimate['taxa'] == 196 and estimate['columns'] == 17456 and
                recommendation['native_mem_flag'] == '--mem 2G' and recommendation['candidate_thread_mode'] == '--thread-site' and
                recommendation['threads'] == 2 and recommendation['hard_process_and_aggregate_job_commit_bytes'] == cfg['budget']['cap_bytes'] and
                recommendation['host_physical_and_commit_admission_reserve_bytes'] == cfg['budget']['reserve_bytes'] and
                recommendation['minimum_physical_and_commit_headroom_bytes'] == cfg['budget']['cap_bytes']+cfg['budget']['reserve_bytes'],
                'Pinned fallback memory evidence does not support actual budget/command')
    if 'cache_import' in cfg:
        pinned(cfg['cache_import'])
        certificate = read_json(pinned(cfg['cache_compatibility_evidence']))
        require(certificate.get('status') == 'PASS_COMPATIBLE_MODEL_CACHE_INPUTS' and
                certificate.get('cache_sha256') == cfg['cache_import']['sha256'] and
                certificate.get('alignment_sha256') == EXPECTED_ALIGNMENT and
                certificate.get('partitions_sha256') == EXPECTED_PARTITIONS and
                certificate.get('executable_sha256') == EXPECTED_EXE and
                certificate.get('seed') == 1961008 and certificate.get('model_selection') == 'MFP_WITHOUT_MERGING' and
                certificate.get('partition_option') == '-p' and certificate.get('native_general_checkpoint_imported') is False,
                'Partial cache compatibility certificate differs')
    api = Win(); directory = Path(cfg['output_directory']).resolve()
    argv = scientific_argv(cfg,exe,alignment,directory/'host',partitions)
    if not args.run:
        authority_receipt = authority(cfg); owners = inspect_owners(cfg)
        print(json.dumps({'state':'CHECKED_NOT_LAUNCHED','argv':argv,'authority':authority_receipt,
                          'owners':owners,'resources':api.resources([directory,alignment])}))
        return 0
    directory.mkdir(parents=True,exist_ok=False)
    workflow_lock = WorkflowLock(api)
    try:
        with workflow_lock as lock:
            atomic(directory/'config.json',cfg)
            first_authority = authority(cfg); first_owners = inspect_owners(cfg)
            atomic(directory/'initial_authority.json',first_authority)
            atomic(directory/'initial_owner_check.json',first_owners)
            paths = [directory,alignment,Path(cfg['repository_path'])]
            admitted = wait_admission(cfg,api,directory,paths)
            if admitted is None:
                atomic(directory/'result.json',{'utc':utc(),'state':'DEFERRED_RESOURCE','scientific_validation':'NOT_RUN',
                                               'admission_sha256':sha256(directory/'admission.json')})
                return 3
            # Recheck exact sources, owners, authority and physical/commit/disk
            # immediately before launch, still retaining the original byte lock.
            pinned(cfg['executable'],EXPECTED_EXE); pinned(cfg['alignment'],EXPECTED_ALIGNMENT)
            if partitions:
                pinned(cfg['partitions'],EXPECTED_PARTITIONS)
            final_authority = authority(cfg); final_owners = inspect_owners(cfg)
            atomic(directory/'final_owner_check.json',final_owners)
            fresh = api.resources(paths)
            if not admission_passes(cfg,fresh):
                atomic(directory/'result.json',{'utc':utc(),'state':'DEFERRED_RESOURCE','scientific_validation':'NOT_RUN',
                                               'reason':'Resources changed immediately before launch','resources':fresh})
                return 3
            atomic(directory/'launch_admission.json',fresh)
            if 'cache_import' in cfg:
                source = pinned(cfg['cache_import'])
                shutil.copyfile(source,directory/'host.model.gz')
                require(sha256(directory/'host.model.gz') == cfg['cache_import']['sha256'], 'Model-cache copy mismatch')
                atomic(directory/'cache_import.json',{'utc':utc(),'source':str(source),'sha256':cfg['cache_import']['sha256'],
                    'claim':'COPIED_BYTES_ONLY_NATIVE_RESTORATION_AND_FINAL_MODEL_VALIDATION_REQUIRED'})
            for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
                os.environ[key] = '2'
            result = run_native(cfg,api,directory,argv,final_authority,lock.identity)
            atomic(directory/'result.json',result)
        return 0 if result['state'] == 'VALIDATION_REQUIRED' else 2
    except BaseException as error:
        atomic(directory/'failure.json',{'utc':utc(),'state':'FAILED_RETRYABLE' if isinstance(error,(OSError,TimeoutError)) else 'FAILED_FATAL',
                                       'kind':type(error).__name__,'message':str(error),'scientific_validation':'NOT_PERFORMED'})
        raise
    finally:
        if workflow_lock.released:
            atomic(directory/'lock_released.json',{'utc':utc(),'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'})


if __name__ == '__main__':
    sys.exit(main())
