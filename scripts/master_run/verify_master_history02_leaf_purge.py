"""Independent read-only history02 post-purge check; run only after COMPLETE/STOP.

Imports only byte-pinned independent Windows read primitives, never a producer.
No cleanup, remote calls, G writes, WSL or native scientific execution.
"""
from pathlib import Path
import argparse
import ctypes
import datetime
import hashlib
import importlib.util
import json
import os
import stat
import sys
import uuid

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parent
HELPER_SHA = 'dbb0140fe2fac41940fa8d4838ffcbf1f6b72933d6d14a2011137ef4c401c56f'
helper = WORK / 'verify_master_batch03_leaf_purge.py'
if hashlib.sha256(helper.read_bytes()).hexdigest() != HELPER_SHA:
    raise ValueError('Independent Windows read-primitives source differs')
spec = importlib.util.spec_from_file_location('history02_independent_windows_reads', helper)
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
PINS = {
    'master_history02_leaf_purge_proposed.json': '6377f16835472951ccbe1bee5e15a25fb2d675d2a7edf24d656d34f008770b22',
    'master_batch03_protected_before.json': '22d307f5bba8a98dbd060e3d1d091e22c7f70dc85b40e77ada04c0eef36ce1a7',
    'public_history02_readback_20261009T195508Z_1f99201e/receipt.json':
        'd83aaff2695920d475742ace6c710255a326642222a5db771b95ec2d809b0ecb',
    'master_batch03_postverify_20261009T200023Z_f95312bd/receipt.json':
        '84cb29ebcc04b444ea90ca0e10d5f7e6832d09f14f8f8285f1241b4cf3e71868',
}
COMMIT = '9559e1cf32daf6a38bbbf74e87f8330bf800a925'
JOURNAL = WORK / 'master_history02_leaf_purge_20261009_receipt.jsonl'
EXCLUDED_SHA = '574547f9584dafce870492810ab02be990fe022939edd5a797292c473625027b'


def numeric_row(row):
    return dict(row, **{k: int(row[k]) for k in ('device', 'file_id', 'mtime_ns')})


def join_candidate(next_event, row, index, deleted, deleted_bytes):
    event = next_event()
    if event.get('event') == 'STOP':
        return None, event
    A.require(event.get('event') == 'VERIFIED_INTENT', 'Expected ordered verified intent')
    for key, value in {'index': index, 'path': row['path'], 'bytes': row['bytes'], 'sha256': row['sha256']}.items():
        A.require(event.get(key) == value, 'Journal intent binding differs: ' + key)
    for key in ('device', 'file_id', 'mtime_ns'):
        A.require(event.get(key) == str(row[key]), 'Journal inventory identity differs: ' + key)
    outcome = next_event()
    if outcome.get('event') == 'STOP':
        return event, outcome
    A.require(outcome.get('event') == 'REMOVED', 'Expected ordered removed outcome')
    for key in ('index', 'path', 'bytes', 'sha256'):
        A.require(outcome.get(key) == event[key], 'Journal intent/removal join differs: ' + key)
    A.require(outcome.get('deleted') == deleted + 1
              and outcome.get('deleted_bytes') == deleted_bytes + row['bytes'],
              'Journal cumulative deletion accounting differs')
    return event, outcome


def check_complete(event, files, size):
    A.require(event.get('event') == 'COMPLETE'
              and event.get('state') == 'PASS_EXACT837_RECOVERED_HISTORY_LEAVES_REMOVED'
              and event.get('deleted') == files == 837 and event.get('deleted_bytes') == size == 983926424
              and event.get('excluded_preserved') == 1 and event.get('excluded_bytes') == 1025
              and event.get('protected_hashes_unchanged') == 12 and event.get('recursive_deletes') == 0,
              'Terminal completion accounting differs')


def terminal_scan(path):
    first = path.lstat()
    A.require(stat.S_ISREG(first.st_mode) and first.st_nlink == 1 and first.st_size < 5 * 1024**2
              and not first.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,
              'Journal nonregular/reparse/hardlink')
    count = 0
    tail = None
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        A.require(A.signature(os.fstat(stream.fileno())) == A.signature(first), 'Opened journal identity differs')
        for line in stream:
            digest.update(line); tail = json.loads(line); count += 1
            A.require(count <= 1676, 'Unexpected excess history journal records')
        A.require(A.signature(os.fstat(stream.fileno())) == A.signature(first), 'Journal handle changed')
    A.require(tail and tail.get('event') in ('COMPLETE', 'STOP'),
              'Journal is still running; no post-purge verification')
    A.require(A.signature(path.lstat()) == A.signature(first), 'Journal changed during terminal precheck')
    return first, tail, digest.hexdigest(), count


def verify(result):
    # Require terminal evidence before any original/protected source payload read.
    first, tail, journal_sha, records = terminal_scan(JOURNAL)
    result.update(journal_sha256=journal_sha, journal_records=records, journal_terminal=tail)
    for name, pin in PINS.items():
        A.require(A.digest(WORK / name) == pin, 'Frozen post-purge control differs: ' + name)
    plan = json.loads((WORK / 'master_history02_leaf_purge_proposed.json').read_bytes())
    A.require(plan['schema'] == 'MASTER_HISTORY02_EXACT837_LEAF_PURGE_PROPOSAL_V1'
              and plan['state'] == 'BUILD_ONLY_NO_DELETE' and plan['candidate_files'] == len(plan['candidates']) == 837
              and plan['candidate_bytes'] == sum(r['bytes'] for r in plan['candidates']) == 983926424
              and len(plan['excluded_preserved']) == 1, 'Exact history proposal differs')
    rows = plan['candidates']
    excluded = plan['excluded_preserved'][0]
    A.require(excluded['bytes'] == 1025 and excluded['sha256'] == EXCLUDED_SHA, 'Exact excluded fragment differs')
    paths = [str(A.target(row)).casefold() for row in rows + [excluded]]
    A.require(len(paths) == len(set(paths)) == 838, 'Duplicate or excluded candidate path')
    owners = A.Owners()
    reads = A.Reads(owners)
    result['owners_before'] = owners.check()
    removed = removed_bytes = remaining = 0
    remainder = []
    missing = []
    stopped = None
    try:
        reads.plain_parents(JOURNAL)
        with JOURNAL.open('rb') as stream:
            count = 0
            current_hash = hashlib.sha256()
            def next_event():
                nonlocal count
                line = stream.readline()
                A.require(bool(line), 'Unexpected journal EOF')
                current_hash.update(line); count += 1
                return json.loads(line)
            begin = next_event()
            A.require(begin.get('event') == 'BEGIN' and begin.get('schema') == 'MASTER_HISTORY02_LEAF_APPEND_RECEIPT_V1'
                      and begin.get('proposal_commit') == COMMIT
                      and begin.get('plan_sha256') == PINS['master_history02_leaf_purge_proposed.json']
                      and begin.get('recovery_receipt_sha256') == plan['recovery_receipt']['sha256']
                      and begin.get('postverify_sha256') == plan['batch03_postverify']['sha256'],
                      'Journal BEGIN authority differs')
            for index, row in enumerate(rows, 1):
                reads.guard()
                if stopped is None:
                    intent, outcome = join_candidate(next_event, row, index, removed, removed_bytes)
                    if outcome['event'] != 'STOP':
                        reads.absent(A.target(row)); removed += 1; removed_bytes += row['bytes']
                        continue
                    stopped = outcome
                # An unreceipted absence after STOP stays explicit uncertainty.
                try:
                    remainder.append(reads.retained(numeric_row(row), full=False))
                except FileNotFoundError:
                    missing.append({'path': row['path'], 'state': 'UNRECEIPTED_ABSENCE_REQUIRES_RECONCILIATION'})
                remaining += 1
            terminal = stopped if stopped is not None else next_event()
            if terminal.get('event') == 'COMPLETE':
                check_complete(terminal, removed, removed_bytes)
            else:
                A.require(terminal.get('event') == 'STOP', 'Unexpected terminal event')
                stopped = terminal
            A.require(not stream.read(1) and current_hash.hexdigest() == journal_sha and count == records,
                      'Journal trailing rows/change or missing ordered join')
        retained = reads.retained(numeric_row(excluded))
        protected = json.loads((WORK / 'master_batch03_protected_before.json').read_bytes())['files']
        A.require(len(protected) == 12, 'Protected exact12 set differs')
        protected_results = []
        for row in protected:
            path = Path(row['path']); reads.guard(); reads.plain_parents(path); before = path.lstat()
            A.require(stat.S_ISREG(before.st_mode) and not before.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                      and before.st_size == row['bytes'], 'Protected file type/size differs')
            actual = A.digest(path)
            A.require(actual == row['sha256'] and A.signature(path.lstat()) == A.signature(before),
                      'Protected actual SHA/identity drift')
            protected_results.append(dict(path=str(path), bytes=row['bytes'], sha256=actual, unchanged=True))
        A.require(A.signature(JOURNAL.lstat()) == A.signature(first), 'Terminal journal changed during verification')
        for path, identity in reads.parents.items():
            now = path.lstat()
            A.require((now.st_dev, now.st_ino) == identity and stat.S_ISDIR(now.st_mode)
                      and not now.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                      and path.absolute() == path.resolve(), 'Observed ancestor changed during verification')
        reads.guard()
        result.update(state='PASS_EXACT837_REMOVED_EXCLUDED1025B_AND12_PROTECTED_UNCHANGED' if stopped is None else
                      'PARTIAL_STOP_REMOVALS_VERIFIED_REMAINDER_REQUIRES_RECONCILIATION',
                      removed_files=removed, removed_bytes=removed_bytes, remaining_after_stop=remaining,
                      unreceipted_absences=missing, remaining_metadata=remainder,
                      excluded_original=retained, protected_files=protected_results,
                      owners_after=owners.check(), retained_original_bytes_hashed=reads.bytes,
                      physical_disk_reclaimed_bytes='NOT_MEASURED', residual_leaf_race=plan['leaf_race'])
    finally:
        owners.close()


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    A.require(os.name == 'nt' and os.environ.get('COMPUTERNAME', '').casefold() == 'wd'
              and WORK == Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work').resolve(),
              'WD exact C-work verifier namespace required before creating output')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = A.W.HANDLE
    kernel.SetPriorityClass.argtypes = [A.W.HANDLE, A.W.DWORD]
    A.require(kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000), 'Own below-normal priority request failed')
    out = WORK / ('master_history02_postverify_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                  + '_' + uuid.uuid4().hex[:8])
    out.mkdir()
    result = dict(schema='MASTER_HISTORY02_INDEPENDENT_POST_PURGE_VERIFY_V1', state='IN_PROGRESS_READ_ONLY',
                  started_utc=A.utc(), verifier_sha256=A.digest(Path(__file__)), independent_helper_sha256=HELPER_SHA,
                  proposal_commit=COMMIT, control_pins=PINS, source_deletions=0, network_calls=0, g_writes=0,
                  wsl_starts=0, scientific_jobs=0, deadline_seconds=A.MAX_RUNTIME,
                  maximum_retained_hash_bytes=A.MAX_HASH_BYTES)
    try:
        verify(result)
    except BaseException as error:
        result.update(state='FAILED_POST_PURGE_VERIFY_NO_NEW_CLEANUP_AUTHORITY',
                      error=dict(kind=type(error).__name__, message=str(error)))
        raise
    finally:
        result['finished_utc'] = A.utc()
        with (out / 'receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
        print(json.dumps(dict(state=result['state'], receipt=str(out / 'receipt.json'))), flush=True)


if __name__ == '__main__':
    main()
