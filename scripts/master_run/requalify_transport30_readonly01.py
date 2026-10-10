"""Read exactly thirty frozen public transport leaves; no deletion or download."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / 'work/postcleanup_sidefolder_inventory01.json'
INVENTORY_SHA = 'f369d6f8f84576ea83f87414d7890ec76b6c7d56c1f674503d179036c7febf44'
REMOTE = ROOT / 'work/transport30_current_remote_metadata01.json'
REMOTE_SHA = '7ac947dc70dc64bcd301a72e702ff2e9ce1cef08d6e596e2fd5f7e042c2668e2'
OUTPUT = ROOT / 'work/transport30_current_requalification01.json'
CATEGORY = 'REDUNDANT_PUBLIC_RECOVERY_TRANSPORT_CONTAINER'
TAG = 'master-run-storage-20261009-v1'
TAG_SHA = '46c7089f906cce59afabaa4449b05df36ee124de'
EXPECTED_BYTES = 2048507163
DEADLINE_SECONDS = 120
CHUNK_BYTES = 4 * 1024 * 1024


def pinned(path, sha):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError('CONTROL_SHA_MISMATCH')
    return json.loads(raw)


def identity(s):
    return dict(device=s.st_dev, inode=s.st_ino, bytes=s.st_size,
                nlink=s.st_nlink, mode=s.st_mode, mtime_ns=s.st_mtime_ns,
                ctime_ns=s.st_ctime_ns,
                birthtime_ns=getattr(s, 'st_birthtime_ns', None),
                file_attributes=getattr(s, 'st_file_attributes', None))


def cross_binding(value):
    # Python 3.14 Windows lstat projects legacy ctime as creation time, while
    # fstat can project change time. Keep both, join on explicit birthtime.
    return {k: v for k, v in value.items() if k != 'ctime_ns'}


def ordinary(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
        raise ValueError('NOT_ORDINARY_REGULAR_FILE')
    parent = path.parent
    while parent != ROOT:
        if parent == parent.parent or getattr(parent.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('REPARENT_OR_REPARSE_SCOPE')
        parent = parent.parent
    return identity(s)


def main():
    started = time.monotonic()
    inv = pinned(INVENTORY, INVENTORY_SHA)
    remote = pinned(REMOTE, REMOTE_SHA)
    rows = [r for r in inv['candidate_metadata_and_exact_recovery_references']
            if r['category'] == CATEGORY]
    if len(rows) != 30 or len({r['path'] for r in rows}) != 30 or sum(r['bytes'] for r in rows) != EXPECTED_BYTES:
        raise ValueError('EXACT_THIRTY_LEAF_SCOPE_MISMATCH')
    if (remote['release']['tag_name'] != TAG or remote['release']['draft'] is not False
            or remote['ref']['ref'] != 'refs/tags/' + TAG
            or remote['ref']['object'] != dict(sha=TAG_SHA, type='commit',
                url='https://api.github.com/repos/serg-alexv/lab-rm-phylogenomics-196/git/commits/' + TAG_SHA)):
        raise ValueError('CURRENT_TAG_BINDING_MISMATCH')
    assets = {a['name']: a for a in remote['assets']}
    if len(assets) != 16 or len(remote['assets']) != 16:
        raise ValueError('REMOTE_ASSET_SCOPE_MISMATCH')
    result_rows = []
    for row in rows:
        if time.monotonic() - started > DEADLINE_SECONDS:
            raise TimeoutError('BOUNDED_OBSERVER_DEADLINE')
        path = Path(row['path'])
        if path.parent == ROOT or os.path.commonpath([str(ROOT / 'work'), str(path)]) != str(ROOT / 'work'):
            raise ValueError('OUTSIDE_FIXED_C_WORK_SCOPE')
        proof = row['expected_recovery']
        before = ordinary(path)
        if (before['bytes'] != row['bytes'] or before['mtime_ns'] != row['mtime_ns']
                or before['file_attributes'] != row['file_attributes']):
            raise ValueError('INVENTORY_METADATA_CHANGED')
        asset = assets[proof['asset_name']]
        expected = proof['expected_sha256']
        if (proof['release_tag'] != TAG or proof['tag_commit'] != TAG_SHA
                or asset['id'] != proof['remote_asset_id'] or asset['size'] != proof['bytes']
                or asset['state'] != 'uploaded'):
            raise ValueError('CURRENT_REMOTE_ASSET_ID_OR_SIZE_MISMATCH')
        digest = asset.get('digest')
        if digest is not None and digest != 'sha256:' + expected:
            raise ValueError('CURRENT_REMOTE_DIGEST_MISMATCH')
        h = hashlib.sha256()
        read_bytes = 0
        with path.open('rb') as handle:
            opened = identity(os.fstat(handle.fileno()))
            if cross_binding(opened) != cross_binding(before):
                raise ValueError('OPENED_FILE_IDENTITY_MISMATCH')
            while True:
                if time.monotonic() - started > DEADLINE_SECONDS:
                    raise TimeoutError('BOUNDED_OBSERVER_DEADLINE')
                block = handle.read(CHUNK_BYTES)
                if not block:
                    break
                read_bytes += len(block)
                if read_bytes > row['bytes']:
                    raise ValueError('FILE_GREW_DURING_HASH')
                h.update(block)
            after_handle = identity(os.fstat(handle.fileno()))
        after_path = ordinary(path)
        if (before != after_path or opened != after_handle
                or cross_binding(before) != cross_binding(opened)
                or cross_binding(after_handle) != cross_binding(after_path)):
            raise ValueError('READ_IDENTITY_CHANGED')
        actual = h.hexdigest()
        if read_bytes != row['bytes'] or actual != expected:
            raise ValueError('CURRENT_LOCAL_PAYLOAD_MISMATCH')
        result_rows.append(dict(path=str(path), bytes=read_bytes, current_local_sha256=actual,
            before=before, opened=opened, after_handle=after_handle, after_path=after_path,
            current_identity_stable=True, retained_read_handle_closed=True,
            exclusive_writer_guard=False, expected_recovery=proof,
            current_remote_asset=asset, remote_metadata_digest_matches_local=digest is not None,
            fresh_remote_asset_bytes_downloaded=False, deletion_authorized_now=False))
    pinned(INVENTORY, INVENTORY_SHA)
    pinned(REMOTE, REMOTE_SHA)
    result = dict(schema='lab-rm-thirty-transport-current-requalification-v1',
        state='PASS_30_CURRENT_LOCAL_HASH_IDENTITY_AND_REMOTE_TAG_ASSET_DIGEST_METADATA_NO_PURGE',
        utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started,
        observer_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        inventory_path=str(INVENTORY), inventory_sha256=INVENTORY_SHA,
        current_remote_metadata_path=str(REMOTE), current_remote_metadata_sha256=REMOTE_SHA,
        current_remote_queried_utc=remote['queried_utc'], files=len(result_rows),
        windows_stat_projection_note='Explicit device/inode/birthtime/size/mtime/mode/nlink/attributes bind lstat to fstat. Legacy ctime is retained and checked within each API, not equated across Python Windows lstat/fstat projections.',
        prior_observer_attempt='Initial no-output attempt rejected lstat/fstat legacy ctime projection mismatch before first candidate payload hash; corrected observer uses explicit birthtime and stable within-API ctime.',
        logical_bytes=sum(r['bytes'] for r in result_rows), rows=result_rows,
        limits=dict(deadline_seconds=DEADLINE_SECONDS, chunk_bytes=CHUNK_BYTES,
                    only_frozen_thirty_transport_leaves=True),
        effects=dict(local_candidate_payload_reads=True, local_deletions=False,
                     remote_asset_download=False, remote_mutations=False, wsl_launch=False,
                     native_process_or_workflow_lock_actions=False),
        boundary='Current API metadata SHA256 is not a fresh download/full archive reader. Original dated owned-download readers remain the recovery-byte evidence. Local read handles were shared, not exclusive purge guards; original-owner closure and exact final retained-handle recheck remain required before literal leaf deletion.',
        deletion_authorized_now=False)
    raw = (json.dumps(result, indent=2) + '\n').encode()
    with OUTPUT.open('xb') as handle:
        handle.write(raw)
    print(json.dumps(dict(state=result['state'], path=str(OUTPUT), files=result['files'],
        logical_bytes=result['logical_bytes'], elapsed_seconds=result['elapsed_seconds'],
        sha256=hashlib.sha256(raw).hexdigest(), output_bytes=len(raw))))


if __name__ == '__main__':
    main()
