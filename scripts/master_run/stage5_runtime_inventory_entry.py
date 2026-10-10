"""Opt-in read-only inventory worker for the EXISTING Windows/Linux owner.

No lock, controller, subprocess, mount, remount, detector or archive is created.
The original owner must already hold the lock, close runtime writers, freeze the
exact ext4 mount read-only, and supervise this worker under its existing lease.
Raw inventory/holds are PRIVATE pending whole-file public and notice review.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import stat
import sys
import time

sys.dont_write_bytecode = True
WORK = Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
PINS = {'stage5_atomic_process.py': 'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
        'stage5_runtime_logical_capture.py': '21b33abc389efe9bbfdcf8048737f2d7f10ce60b52d6e1c6f3678b24568b8220',
        'stage5_runtime_recovery_contract.py': 'daf48ea1c8cc96312519b1ab22f2d41216494773e5e345e3e5e0417139588bb6'}
RESERVE = 1536*1024**2
WORKER_RSS_LIMIT = 512*1024**2
METADATA_LIMIT = 64*1024**2
DEADLINE_SECONDS = 1800


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def source_module(name):
    path = WORK/name
    need(digest(path.read_bytes()) == PINS[name] and not path.is_symlink(), 'Exact published inventory dependency required')
    spec = importlib.util.spec_from_file_location('_inventory_'+name[:-3], path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    need(digest(path.read_bytes()) == PINS[name], 'Inventory dependency changed during import')
    return module


def control(path, expected):
    path = Path(path)
    need(path.is_relative_to(WORK) and path.resolve() == path and not path.is_symlink()
         and path.is_file() and path.stat().st_size <= METADATA_LIMIT
         and re.fullmatch('[a-f0-9]{64}', expected or ''), 'Bounded exact mounted-C control required')
    before = path.stat(); raw = path.read_bytes(); after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
         and digest(raw) == expected, 'Control changed or exact digest differs')
    return json.loads(raw)


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    for name in ['source-sha256', 'runtime', 'runtime-sha256', 'cold-proof', 'cold-proof-sha256', 'owner-lease', 'owner-nonce', 'output-private']:
        parser.add_argument('--'+name)
    args = parser.parse_args()
    if not args.run:
        print(json.dumps({'state': 'NO_OP_EXISTING_OWNER_AND_COLD_FREEZE_REQUIRED'})); return 0
    need(all(vars(args).values()), 'All explicit inventory inputs required')
    need(sys.platform == 'linux' and os.geteuid() == 0 and Path(__file__).resolve().parent == WORK,
         'Exact root-owned mounted-C Linux worker required')
    need(digest(Path(__file__).read_bytes()) == args.source_sha256, 'Explicit reviewed entry source required')
    for parent in [WORK, *WORK.parents]:
        need(not parent.is_symlink() and stat.S_ISDIR(parent.lstat().st_mode), 'Plain mounted-C source ancestry required')
    P = source_module('stage5_atomic_process.py'); R = source_module('stage5_runtime_logical_capture.py')
    runtime = control(args.runtime, args.runtime_sha256)
    proof = control(args.cold_proof, args.cold_proof_sha256)
    need(runtime.get('schema') == 'STAGE05_PINNED_RUNTIME_V1' and runtime.get('roots') == R.C.ROOTS,
         'Actual three-root scientific runtime candidate required')
    output = Path(args.output_private)
    need(output.parent == WORK and output.resolve() == output and not output.exists()
         and re.fullmatch('stage5_runtime_inventory_private_[A-Za-z0-9_]+', output.name), 'Fresh clearly private direct-C namespace required')
    lease = Path(args.owner_lease)
    need(lease.resolve() == lease and lease.is_relative_to(WORK) and not lease.is_symlink(), 'Exact current owner lease path required')
    policy = {'lease_max_age_seconds': 3}
    started = time.monotonic(); owner_identity = None; peak_rss = 0
    def admission():
        nonlocal owner_identity, peak_rss
        need(time.monotonic()-started <= DEADLINE_SECONDS, 'Finite inventory deadline expired')
        value = P.check_lease(lease, args.owner_nonce, policy)
        identity = (value['owner_pid'], value['owner_creation_filetime'])
        if owner_identity is None:
            owner_identity = identity
        need(identity == owner_identity and proof.get('owner_nonce') == args.owner_nonce
             and proof.get('workflow_lock') == value.get('workflow_lock'), 'Cold proof and exact current original owner binding differs')
        need(value['windows_available_bytes'] >= RESERVE+WORKER_RSS_LIMIT
             and value['windows_commit_headroom_bytes'] >= RESERVE+WORKER_RSS_LIMIT,
             'Current physical and commit reserve below finite inventory allocation')
        need(P.linux_available() >= 256*1024**2 and shutil.disk_usage(WORK).free >= 10*1024**3
             and all(free >= 10*1024**3 for free in value['disk_available_bytes'].values()), 'Current inventory Linux memory/disk reserve failed')
        rss = int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
        peak_rss = max(peak_rss, rss)
        need(rss <= WORKER_RSS_LIMIT, 'Finite inventory worker RSS allocation exceeded')
    admission()
    R.check_ro_mount(proof)
    output.mkdir(mode=0o700)
    public = {'schema': 'STAGE05_FULL_RUNTIME_INVENTORY_WORKER_V1', 'state': 'FAILED_PRIVATE_PARTIAL_PRESERVED',
              'entry_source_sha256': args.source_sha256, 'dependency_pins': PINS,
              'runtime_sha256': args.runtime_sha256, 'cold_proof_sha256': args.cold_proof_sha256,
              'public_scope_accepted': False, 'archive_created': False, 'cleanup_authority': False,
              'raw_candidates_publication_permitted': False,
              'capacity_basis': 'Finite512MiB worker RSS allocation plus1536MiB current Windows physical/commit reserve; not measured complete inventory requirement'}
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('Inventory wall deadline expired')))
    signal.alarm(DEADLINE_SECONDS)
    try:
        candidate = R.inventory_frozen_roots(runtime, proof, admission)
        manifest = output/'PRIVATE_MANIFEST_DO_NOT_PUBLISH.jsonl'; total = 0; hasher = hashlib.sha256()
        with manifest.open('xb') as stream:
            for row in candidate['entries']:
                admission(); raw = (json.dumps(row, sort_keys=True, separators=(',', ':'))+'\n').encode('utf-8')
                total += len(raw); need(total <= METADATA_LIMIT, '64MiB manifest admission bound exceeded')
                stream.write(raw); hasher.update(raw)
            stream.flush(); os.fsync(stream.fileno())
        write_new(output/'PRIVATE_HOLDS_DO_NOT_PUBLISH.json', candidate['hold_reason_codes'])
        roles = collections.defaultdict(lambda: collections.Counter())
        for row in candidate['entries']:
            roles[row['role']][row['kind']] += 1
            if row['kind'] == 'regular': roles[row['role']]['regular_bytes'] += row['bytes']
        reasons = collections.Counter(code for codes in candidate['hold_reason_codes'].values() for code in set(codes))
        admission(); R.check_ro_mount(proof)
        need(all(digest((WORK/name).read_bytes()) == pin for name, pin in PINS.items()), 'Final inventory dependency drift')
        public.update(state='PASS_PRIVATE_FULL_INVENTORY_CANDIDATE_PUBLIC_REVIEW_PENDING',
                      manifest_sha256=hasher.hexdigest(), manifest_bytes=total,
                      entry_count=len(candidate['entries']), role_totals=dict(roles),
                      held_nodes=len(candidate['hold_reason_codes']), hold_reason_counts=dict(reasons))
    except BaseException as error:
        public['error_kind'] = type(error).__name__  # Never disclose a private pathname/match.
    finally:
        signal.alarm(0)
        public.update(elapsed_seconds=time.monotonic()-started, sampled_self_peak_rss_bytes=peak_rss,
                      remaining_direct_children=[int(x) for x in Path(f'/proc/self/task/{os.getpid()}/children').read_text().split()])
        write_new(output/'PUBLIC_SUMMARY.json', public)
    print(json.dumps({'state': public['state'], 'public_summary': str(output/'PUBLIC_SUMMARY.json')}))
    return 0 if public['state'].startswith('PASS_') and not public['remaining_direct_children'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
