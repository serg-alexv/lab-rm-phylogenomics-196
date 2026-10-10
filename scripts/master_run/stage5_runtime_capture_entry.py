"""Opt-in logical-capture worker for the EXISTING cold Windows/Linux owner.

No lock, controller, subprocess, mount, installer, upload or eviction is created.
The original owner must already retain the real Windows image read guard and
RO loop/mount freeze, and supervise this worker with its existing fresh lease.
Default is a no-op. Actual freeze/integration/capture/restore are NOT_RUN.
"""
from pathlib import Path
import argparse
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
INVENTORY_NAME = 'stage5_runtime_inventory_entry_v2.py'
INVENTORY_SHA = 'dd3a68f0e1dc86399ca07f95a329f93b955e4e1b4082405a2cd72e8ee10f5363'
DEADLINE = 1800
ALLOCATION = 512*1024**2
RESERVE = 1536*1024**2


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_inventory(path=None):
    path = WORK/INVENTORY_NAME if path is None else Path(path)
    need(not path.is_symlink() and digest(path.read_bytes()) == INVENTORY_SHA, 'Exact reviewed v2 owner binding required')
    spec = importlib.util.spec_from_file_location('_capture_v2_owner_binding', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    need(digest(path.read_bytes()) == INVENTORY_SHA, 'V2 owner-binding source drift')
    return module


def capture_owner_binding(I, proof, lease, nonce, boot_id, source_sha, previous=None):
    need(isinstance(source_sha, str) and re.fullmatch('[a-f0-9]{64}', source_sha)
         and proof.get('capture_entry_source_sha256') == source_sha,
         'Current cold proof must pin this reviewed capture entry')
    return I.owner_binding(proof, lease, nonce, boot_id, INVENTORY_SHA, previous)


def output_capacity(manifest_raw, controls_bytes):
    """Finite worst-case logical data plus generous tar/control overhead reserve."""
    need(isinstance(manifest_raw, bytes) and len(manifest_raw) <= 64*1024**2
         and type(controls_bytes) is int and 0 <= controls_bytes <= 5*64*1024**2,
         'Bounded complete manifest/control bytes required')
    rows = [json.loads(line) for line in manifest_raw.decode('utf-8').splitlines()]
    need(rows and len(rows) <= 500000, 'Finite nonempty manifest required')
    total = 0
    for row in rows:
        need(isinstance(row, dict) and row.get('kind') in {'regular','hardlink','directory','symlink'}
             and type(row.get('bytes')) is int and row['bytes'] >= 0, 'Exact manifest sizes/types required')
        if row['kind'] == 'regular': total += row['bytes']
    need(total <= 128*1024**3, 'Finite installed logical payload bound exceeded')
    return total+controls_bytes+(len(rows)+8)*4096+64*1024**2


def remaining_disk_requirement(capacity, already_written):
    need(type(capacity) is int and capacity > 0 and type(already_written) is int and already_written >= 0,
         'Exact positive capacity and observed output bytes required')
    return 10*1024**3+max(0,capacity-already_written)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    for name in ['source-sha256','inputs','inputs-sha256','runtime','runtime-sha256','manifest','manifest-sha256',
                 'public-review','public-review-sha256','notices','notices-sha256','cold-proof','cold-proof-sha256',
                 'owner-lease','owner-nonce','output','terminal']:
        parser.add_argument('--'+name)
    args = parser.parse_args()
    if not args.run:
        print(json.dumps({'state':'NO_OP_EXISTING_OWNER_COLD_FREEZE_AND_FULL_PUBLIC_REVIEW_REQUIRED'})); return 0
    need(all(vars(args).values()), 'Every actual pinned capture input required')
    need(sys.platform == 'linux' and os.geteuid() == 0 and Path(__file__).resolve().parent == WORK,
         'Exact root-owned mounted-C Linux capture worker required')
    need(digest(Path(__file__).read_bytes()) == args.source_sha256, 'Explicit reviewed capture-entry source required')
    for parent in [WORK, *WORK.parents]:
        need(not parent.is_symlink() and stat.S_ISDIR(parent.lstat().st_mode), 'Plain mounted-C capture source ancestry required')
    I = load_inventory(); P = I.source_module('stage5_atomic_process.py'); R = I.source_module('stage5_runtime_logical_capture.py')
    inputs = I.control(args.inputs, args.inputs_sha256)
    paths = {key:Path(getattr(args,key.replace('-','_'))) for key in ['runtime','manifest','public-review','notices','cold-proof']}
    paths = {'public_review' if key=='public-review' else 'cold_proof' if key=='cold-proof' else key:value for key,value in paths.items()}
    pins = {'runtime':args.runtime_sha256,'manifest':args.manifest_sha256,'public_review':args.public_review_sha256,
            'notices':args.notices_sha256,'cold_proof':args.cold_proof_sha256}
    # Full exact controls are rechecked by capture() before/after every archive.
    runtime = I.control(paths['runtime'],pins['runtime']); proof = I.control(paths['cold_proof'],pins['cold_proof'])
    raw = {key:R.exact_bytes(path,pins[key]) for key,path in paths.items()}
    need(runtime.get('schema') == 'STAGE05_PINNED_RUNTIME_V1' and runtime.get('roots') == R.C.ROOTS,
         'Actual pinned three-role scientific runtime required')
    expected = {'actual_runtime_manifest_sha256':pins['runtime'],'complete_inventory_sha256':pins['manifest'],
                'whole_file_public_review_sha256':pins['public_review'],'cold_exclusive_capture_receipt_sha256':pins['cold_proof'],
                'license_source_notice_review_sha256':pins['notices'],
                'published_capture_source_sha256':I.PINS['stage5_runtime_logical_capture.py']}
    need(all(inputs.get(key) == value for key,value in expected.items()), 'Capture request and every actual control pin differ')
    R.C.capture_gate(inputs)
    required_disk = output_capacity(raw['manifest'],sum(len(value) for value in raw.values()))
    output = Path(args.output); terminal = Path(args.terminal); lease = Path(args.owner_lease)
    need(output.parent == WORK and output.resolve() == output and not output.exists()
         and re.fullmatch('stage5_runtime_capture_[A-Za-z0-9_]+',output.name), 'Fresh direct-C capture namespace required')
    need(terminal.parent == WORK and terminal.resolve() == terminal and not terminal.exists()
         and re.fullmatch('stage5_runtime_capture_terminal_[A-Za-z0-9_]+[.]json',terminal.name), 'Fresh direct-C capture terminal required')
    need(lease.resolve() == lease and lease.is_relative_to(WORK) and not lease.is_symlink(), 'Exact current owner lease path required')
    boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    started = time.monotonic(); identity = None; peak = 0
    def admission():
        nonlocal identity, peak
        need(time.monotonic()-started <= DEADLINE, 'Finite capture worker deadline expired')
        current = P.check_lease(lease,args.owner_nonce,{'lease_max_age_seconds':3})
        identity = capture_owner_binding(I,proof,current,args.owner_nonce,boot_id,args.source_sha256,identity)
        need(current['windows_available_bytes'] >= RESERVE+ALLOCATION
             and current['windows_commit_headroom_bytes'] >= RESERVE+ALLOCATION,
             'Current physical/commit reserve below finite capture allocation')
        written = 0
        if output.exists():
            need(output.is_dir() and not output.is_symlink(), 'Owned capture output alias appeared')
            for member in output.iterdir():
                info=member.lstat()
                need(stat.S_ISREG(info.st_mode) and not member.is_symlink() and info.st_nlink == 1,
                     'Unknown nonregular/aliased local capture output')
                written += info.st_size
        need(P.linux_available() >= 256*1024**2
             and shutil.disk_usage(WORK).free >= remaining_disk_requirement(required_disk,written)
             and all(value >= 10*1024**3 for value in current['disk_available_bytes'].values()),
             'Current capture Linux memory or worst-case output disk admission failed')
        rss = int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
        peak = max(peak,rss); need(rss <= ALLOCATION, 'Finite capture sampled-self RSS allocation exceeded')
    admission(); R.check_ro_mount(proof)
    result = {'schema':'STAGE05_RUNTIME_CAPTURE_WORKER_V1','state':'FAILED_PARTIAL_PRESERVED',
              'source_sha256':args.source_sha256,'inventory_binding_source_sha256':INVENTORY_SHA,
              'inputs_sha256':args.inputs_sha256,'cold_proof_sha256':args.cold_proof_sha256,
              'capacity_bytes':required_disk,'actual_capture':False,'remote_recovery':'NOT_RUN',
              'cold_restore':'NOT_RUN','cleanup_authority':False,
              'rss_limit_scope':'Sampled self RSS only; original owner supplies actual lifecycle/resource enforcement'}
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Capture worker wall deadline expired')))
    signal.alarm(DEADLINE)
    try:
        index = R.capture(inputs,paths,output,admission)
        admission(); R.check_ro_mount(proof)
        need(digest(Path(__file__).read_bytes()) == args.source_sha256 and digest((WORK/INVENTORY_NAME).read_bytes()) == INVENTORY_SHA
             and all(digest((WORK/name).read_bytes()) == pin for name,pin in I.PINS.items()), 'Final capture/source dependency drift')
        need(I.control(args.inputs,args.inputs_sha256) == inputs
             and I.control(paths['runtime'],pins['runtime']) == runtime
             and I.control(paths['cold_proof'],pins['cold_proof']) == proof
             and Path('/proc/sys/kernel/random/boot_id').read_text().strip() == boot_id, 'Final capture control/current boot drift')
        result.update(state='PASS_LOCAL_LOGICAL_PARTS_PENDING_INDEPENDENT_FULL_READBACK', actual_capture=True,
                      index_sha256=digest((output/'index.json').read_bytes()),shard_count=len(index['shards']),
                      compressed_bytes=index['compressed_bytes'])
    except BaseException as error:
        result['error_kind'] = type(error).__name__  # Never disclose private scope bytes or paths.
    finally:
        signal.alarm(0)
        result.update(elapsed_seconds=time.monotonic()-started,sampled_self_peak_rss_bytes=peak,
                      remaining_direct_children=[int(value) for value in Path(f'/proc/self/task/{os.getpid()}/children').read_text().split()])
        I.write_new(terminal,result)
    print(json.dumps({'state':result['state'],'terminal':str(terminal)}))
    return 0 if result['state'].startswith('PASS_') and not result['remaining_direct_children'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
