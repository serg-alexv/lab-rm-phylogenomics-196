#!/usr/bin/env python3
"""Bounded WD Linux child lifecycle and measured process-tree receipts.

The Windows controller owns the workflow lock. This helper never performs Git,
installation, publication, detector search, or job termination. Inspect mode is
read-only and validates PID start tokens before reporting an existing job live.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import socket
import subprocess
import sys
import time


def check(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.partial')
    tmp.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    for attempt in range(8):
        try:
            tmp.replace(path)
            return
        except OSError:
            if attempt == 7:
                raise
            time.sleep(min(.025 * 2 ** attempt, 1))


def proc(pid):
    """Read numeric /proc fields only; never read another process's arguments/env."""
    try:
        text = (Path('/proc') / str(pid) / 'stat').read_text()
        fields = text[text.rfind(')') + 2:].split()
        status = (Path('/proc') / str(pid) / 'status').read_text()
        values = {}
        for line in status.splitlines():
            if line.startswith(('VmHWM:', 'VmPeak:')):
                name, amount, unit = line.split()
                values[name[:-1]] = int(amount) * 1024
        return {'pid': int(pid), 'ppid': int(fields[1]), 'state': fields[0],
                'user_ticks': int(fields[11]), 'system_ticks': int(fields[12]),
                'start_ticks': int(fields[19]), 'vsize_bytes': int(fields[20]),
                'rss_bytes': int(fields[21]) * os.sysconf('SC_PAGE_SIZE'),
                'peak_rss_bytes': values.get('VmHWM'), 'peak_vsize_bytes': values.get('VmPeak')}
    except (FileNotFoundError, ProcessLookupError):
        return None


def memory_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) * 1024
    raise ValueError('Linux MemAvailable measurement unavailable')


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def alive(pid, start, boot):
    current = proc(pid)
    return bool(boot == boot_id() and current and current['start_ticks'] == start and current['state'] != 'Z')


def descendants(pid, start):
    root = proc(pid)
    if not root or root['start_ticks'] != start:
        return []
    observed = {}
    for folder in Path('/proc').iterdir():
        if folder.name.isdigit():
            row = proc(int(folder.name))
            if row:
                observed[row['pid']] = row
    chosen = {pid}
    while True:
        expanded = chosen | {key for key, row in observed.items() if row['ppid'] in chosen}
        if expanded == chosen:
            break
        chosen = expanded
    current = proc(pid)
    check(current and current['start_ticks'] == start, 'Job ended during process-tree snapshot')
    return [observed[key] for key in sorted(chosen) if key in observed]


def inspection(directory):
    launch = load(directory / 'linux_launch_receipt.json')
    result = {'utc': now(), 'phase': launch['phase'], 'invocation_id': launch['invocation_id'],
              'identity': launch['identity'], 'launcher_pid': launch['launcher_pid'], 'job_pid': launch['job_pid'],
              'launcher_alive': alive(launch['launcher_pid'], launch['launcher_start_ticks'], launch['boot_id']),
              'job_alive': alive(launch['job_pid'], launch['job_start_ticks'], launch['boot_id']) if launch['job_start_ticks'] is not None else False}
    final = directory / 'linux_exit_receipt.json'
    if final.is_file():
        exit_record = load(final)
        check(exit_record['invocation_id'] == launch['invocation_id'] and exit_record['identity'] == launch['identity'], 'Exit receipt identity differs')
        result.update(status='ACTUAL_EXIT_RECEIPT_AVAILABLE', exit_code=exit_record['exit_code'])
    elif result['job_alive'] and result['launcher_alive']:
        result['status'] = 'VERIFIED_ACTIVE_EXACT_LINUX_JOB'
    elif result['job_alive']:
        result['status'] = 'ACTIVE_EXACT_JOB_BUT_LAUNCHER_LOST_NO_DUPLICATE_PERMITTED'
    elif result['launcher_alive']:
        result['status'] = 'LAUNCHER_ALIVE_JOB_EXIT_RECEIPT_PENDING'
    else:
        result['status'] = 'NO_ACTIVE_MATCHING_PID_AND_NO_EXIT_RECEIPT_BLOCKER'
    return result


def run(args):
    check(sys.platform == 'linux' and socket.gethostname().lower() == 'wd', 'WD Linux only')
    root = args.root.resolve()
    directory = args.receipt_dir.resolve()
    check(root == Path.cwd().resolve() and root in directory.parents and '.work' in directory.relative_to(root).parts, 'Dedicated project receipt directory required')
    check(not directory.exists() or not list(directory.iterdir()), 'Fresh actual invocation receipt directory required')
    command = args.command[1:] if args.command and args.command[0] == '--' else args.command
    check(command and Path(command[0]).is_absolute(), 'Absolute actual child interpreter required')
    check(args.threads == 2 and args.address_space_bytes == 3758096384, 'Frozen two-thread/3.5GiB process limits required')
    identity = load(args.identity_file)
    check(isinstance(identity, dict) and identity['maximum_compute_threads']==2
          and identity['address_space_limit_bytes']==3758096384 and identity['iqtree_address_space_limit_bytes']==3221225472
          and identity['inference_identity']['observer_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'Frozen actual new observer code/outer/native/thread identity differs')
    available = memory_available()
    check(available >= 4294967296, 'Insufficient measured Linux memory before phase launch')
    allowed = sorted(os.sched_getaffinity(0))
    check(len(allowed) >= 2, 'Fewer than two permitted compute cores')
    os.sched_setaffinity(0, set(allowed[:2]))
    resource.setrlimit(resource.RLIMIT_AS, (args.address_space_bytes, args.address_space_bytes))
    environment = dict(os.environ)
    environment.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2', LC_ALL='C')
    directory.mkdir(parents=True, exist_ok=True)
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    begin = time.monotonic()
    child = subprocess.Popen(command, cwd=root, env=environment, stdin=subprocess.DEVNULL)
    child_info, owner_info = proc(child.pid), proc(os.getpid())
    launch = {'execution': 'ACTUAL_LINUX_PHASE_CHILD_STARTED', 'utc': now(), 'phase': args.phase,
              'invocation_id': args.invocation_id, 'identity': identity, 'argv': command,
              'launcher_pid': os.getpid(), 'launcher_start_ticks': owner_info['start_ticks'],
              'job_pid': child.pid, 'job_start_ticks': child_info['start_ticks'] if child_info else None,
              'boot_id': boot_id(), 'cpu_affinity': allowed[:2],
              'address_space_limit_bytes': args.address_space_bytes, 'threads': 2,
              'measured_linux_available_bytes': available, 'scientific_validation': 'NOT_RUN'}
    write(directory / 'linux_launch_receipt.json', launch)
    print('ACTUAL_LINUX_PHASE_STARTED ' + args.phase + ' launcher_pid=' + str(os.getpid()) + ' job_pid=' + str(child.pid), flush=True)
    peak_sum = 0
    last = None
    while child.poll() is None:
        try:
            process_rows = descendants(child.pid, launch['job_start_ticks']) if launch['job_start_ticks'] is not None else []
            peak_sum = max(peak_sum, sum(row['rss_bytes'] for row in process_rows))
            last = {'execution': 'RUNNING', 'utc': now(), 'phase': args.phase, 'invocation_id': args.invocation_id,
                    'job_pid': child.pid, 'processes': process_rows, 'sampled_tree_peak_rss_bytes': peak_sum,
                    'linux_available_bytes': memory_available(), 'elapsed_seconds': time.monotonic() - begin,
                    'memory_measurement_limit': 'Sum of sampled per-process RSS; shared pages may be counted more than once; sampling may miss short peaks'}
            write(directory / 'linux_progress.json', last)
        except ValueError:
            if child.poll() is None:
                raise
        time.sleep(args.sample_seconds)
    code = child.wait()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    final = {'execution': 'ACTUAL_LINUX_PHASE_CHILD_EXITED', 'utc': now(), 'phase': args.phase,
             'invocation_id': args.invocation_id, 'identity': identity, 'argv': command, 'job_pid': child.pid,
             'launcher_pid': os.getpid(), 'exit_code': code, 'elapsed_seconds': time.monotonic() - begin,
             'child_cpu_seconds': after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
             'children_max_rss_bytes': after.ru_maxrss * 1024, 'sampled_tree_peak_rss_bytes': peak_sum,
             'peak_measurement_limit': 'rusage maximum child RSS plus sampled concurrent RSS sum; no total PSS/cgroup measurement',
             'last_process_snapshot': last, 'scientific_validation': 'NOT_RUN_CHECKER_GATE_REQUIRED'}
    write(directory / 'linux_exit_receipt.json', final)
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['run', 'inspect', 'resources'], default='run')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--receipt-dir', type=Path)
    parser.add_argument('--identity-file', type=Path)
    parser.add_argument('--phase')
    parser.add_argument('--invocation-id')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--address-space-bytes', type=int, default=3758096384)
    parser.add_argument('--sample-seconds', type=float, default=5)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.mode == 'resources':
        print(json.dumps({'utc': now(), 'host': socket.gethostname(), 'linux_available_bytes': memory_available(),
                          'cpu_affinity_available': sorted(os.sched_getaffinity(0)), 'boot_id': boot_id()}))
    elif args.mode == 'inspect':
        print(json.dumps(inspection(args.receipt_dir.resolve())))
    else:
        try:
            raise SystemExit(run(args))
        except Exception as error:
            if args.receipt_dir:
                write(args.receipt_dir / 'launcher_failure.json', {'execution': 'LAUNCHER_FAILED', 'utc': now(),
                      'phase': args.phase, 'invocation_id': args.invocation_id, 'error': str(error), 'outputs_preserved': True})
            raise
