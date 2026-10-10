"""Bounded C-only metadata inventory and retained remote-proof joins; no effects.

No private file payload, VM/image/cache payload, native API, WSL, lock or network
operation is used. Candidates are observations, never deletion authorization.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import stat
import time

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
OLD = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
CHAT = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\referenced-chatgpt-conversation-this-is-an')
RECEIPTS = [
    'public_components01_readback_20261009T195312Z_16720f4a/receipt.json',
    'public_history02_readback_20261009T195508Z_1f99201e/receipt.json',
    'public_conda_packages01_readback_20261009T212013Z_9326e9e6/receipt.json',
    'batch03_mapping01_remote_readback_20261009T192220Z_3e6cf7d8/receipt.json',
    'batch03_execution01_readback_20261009T201344Z_f55cdf6b/receipt.json',
]
SKIP = {OLD/'.git': 'PROTECTED_HISTORICAL_GIT_STORE',
        OLD/'.private_run': 'PROTECTED_PRIVATE_CONTROL_HISTORY',
        OLD/'.tools/linux': 'PROTECTED_ACTIVE_WSL_RUNTIME_MOUNT',
        CHAT/'.private_run': 'PROTECTED_PRIVATE_CHAT_CONTROL_HISTORY'}
ASSET_SCOPES = ('public_components01_readback_', 'public_history02_readback_',
                'public_conda_packages01_readback_', 'batch03_mapping01_remote_readback_',
                'batch03_execution01_readback_', 'public_conda_packages01_continuation_')
ASSET_EXACT_SCOPES = {'master_public_components01', 'master_public_history02',
                      'master_batch03_mapping01', 'master_batch03_cleanup_execution01'}
PACKAGE_SCOPE = 'public_conda_packages01_continuation_20261009T204518Z_bd4c1b76'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    started = time.monotonic(); deadline = started + 45; limit = 120000
    evidence = []; asset_proofs = {}; package_proofs = {}; past_cleanup = []

    def read_public_json(relative):
        path = WORK/relative
        assert path.resolve() == path and path.stat().st_size <= 2*1024**2
        raw = path.read_bytes()
        evidence.append({'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)})
        return json.loads(raw), evidence[-1]

    for relative in RECEIPTS:
        value, ref = read_public_json(relative)
        assert value['state'].startswith('PASS_FRESH_REMOTE')
        assert value.get('release_tag_and_assets_unchanged_before_after') is True
        assert value.get('mode') in ('FRESH_REMOTE', 'FRESH_REMOTE_DOWNLOAD')
        common = {'receipt_path': str(WORK/relative), 'receipt_sha256': ref['sha256'],
                  'receipt_state': value['state'], 'verified_at_utc': value['finished_utc'],
                  'source_commit': value['source_commit'], 'tag_commit': value['expected_tag_commit'],
                  'release_tag': value['tag'], 'release_url': value['release_url']}
        for asset in value.get('downloaded_assets', value.get('assets', [])):
            assert asset['remote_digest'] == 'sha256:' + asset['sha256']
            asset_proofs[asset['name']] = {**common, 'asset_name': asset['name'],
                'remote_asset_id': asset['remote_asset_id'], 'bytes': asset['bytes'],
                'expected_sha256': asset['sha256']}
        if relative.startswith('public_conda_packages01_readback_'):
            for member in value['members']:
                if member['member'].startswith('packages/'):
                    assert member['crc_verified'] is True
                    package_proofs[member['member']] = {**common, 'archive_member': member['member'],
                        'bytes': member['bytes'], 'expected_sha256': member['sha256'],
                        'verified_archive_asset_names': [a['name'] for a in value['downloaded_assets']
                                                         if a['name'].endswith('.zip')]}
    for relative, count_key, bytes_key in [
        ('master_purge_01_02_receipt.json', 'deleted', 'deleted_bytes'),
        ('master_batch03_postverify_20261009T200023Z_f95312bd/receipt.json', 'removed_files', 'removed_bytes'),
        ('master_history02_postverify_20261009T201921Z_f90337c5/receipt.json', 'removed_files', 'removed_bytes'),
    ]:
        value, ref = read_public_json(relative)
        assert value['state'].startswith('PASS')
        count = len(value[count_key]) if isinstance(value[count_key], list) else value[count_key]
        past_cleanup.append({'receipt_path': str(WORK/relative), 'receipt_sha256': ref['sha256'],
                             'state': value['state'], 'files': count, 'logical_bytes': value[bytes_key]})

    totals = {}; groups = {}; skipped = []; errors = []; candidates = []; mismatched = []
    objects = 0; complete = True
    for label, root in [('old_project', OLD), ('old_pipeline_chat', CHAT), ('master_work', WORK)]:
        summary = {'path': str(root), 'files': 0, 'directories': 0, 'logical_bytes': 0,
                   'reparse_objects_not_traversed': 0, 'protected_scopes_not_traversed': 0}
        totals[label] = summary; stack = [root]
        while stack:
            if time.monotonic() >= deadline or objects >= limit:
                complete = False; errors.append({'scope': label, 'kind': 'FINITE_SCAN_BOUND_REACHED'}); break
            directory = stack.pop()
            try:
                with os.scandir(directory) as stream:
                    for entry in stream:
                        objects += 1
                        if time.monotonic() >= deadline or objects >= limit:
                            complete = False; errors.append({'scope': label, 'kind': 'FINITE_SCAN_BOUND_REACHED'}); break
                        path = Path(entry.path); info = entry.stat(follow_symlinks=False)
                        if path in SKIP:
                            summary['protected_scopes_not_traversed'] += 1
                            skipped.append({'path': str(path), 'reason': SKIP[path]}); continue
                        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                            summary['reparse_objects_not_traversed'] += 1; continue
                        rel = path.relative_to(root); parts = rel.parts
                        key = '/'.join(parts[:2]) if label == 'old_project' else parts[0]
                        group = groups.setdefault((label, key), {'files': 0, 'directories': 0, 'logical_bytes': 0})
                        if stat.S_ISDIR(info.st_mode):
                            summary['directories'] += 1; group['directories'] += 1; stack.append(path); continue
                        if not stat.S_ISREG(info.st_mode):
                            continue
                        summary['files'] += 1; group['files'] += 1
                        summary['logical_bytes'] += info.st_size; group['logical_bytes'] += info.st_size
                        if label != 'master_work' or len(parts) < 2:
                            continue
                        top = parts[0]; proof = None; category = None
                        if (top in ASSET_EXACT_SCOPES or top.startswith(ASSET_SCOPES)) and path.name in asset_proofs:
                            proof = asset_proofs[path.name]; category = 'REDUNDANT_PUBLIC_RECOVERY_TRANSPORT_CONTAINER'
                        elif top == PACKAGE_SCOPE:
                            member = '/'.join(parts[1:])
                            if member in package_proofs:
                                proof = package_proofs[member]; category = 'ACQUIRED_PUBLIC_PACKAGE_CACHE_ARCHIVE_MEMBER'
                        if proof is not None:
                            row = {'path': str(path), 'category': category, 'bytes': info.st_size,
                                   'mtime_ns': info.st_mtime_ns, 'inode': info.st_ino, 'nlink': info.st_nlink,
                                   'file_attributes': getattr(info, 'st_file_attributes', None),
                                   'expected_recovery': proof, 'current_payload_sha256': 'NOT_READ_METADATA_ONLY',
                                   'deletion_authorized_now': False}
                            (candidates if info.st_size == proof['bytes'] else mismatched).append(row)
            except OSError as error:
                errors.append({'scope': label, 'path': str(directory), 'kind': type(error).__name__})
                complete = False
        if not complete and (time.monotonic() >= deadline or objects >= limit):
            break
    categories = {}
    for row in candidates:
        group = categories.setdefault(row['category'], {'files': 0, 'logical_bytes': 0})
        group['files'] += 1; group['logical_bytes'] += row['bytes']
    report = {'schema': 'LAB_RM_POSTCLEANUP_C_ONLY_SIDEFOLDER_INVENTORY_V1',
        'state': 'PASS_BOUNDED_METADATA_INVENTORY_STORED_RECOVERY_PROOFS_NO_PURGE' if complete else 'PARTIAL_BOUNDED_METADATA_INVENTORY_NO_PURGE',
        'utc': datetime.now(timezone.utc).isoformat(), 'observer_source_sha256': sha(Path(__file__).read_bytes()),
        'elapsed_seconds': round(time.monotonic()-started, 3), 'object_limit': limit, 'deadline_seconds': 45,
        'objects_observed': objects, 'metadata_scan_complete_within_declared_exclusions': complete,
        'scope_totals': totals,
        'largest_remaining_groups': [{'scope': label, 'group': key, **value}
                                     for (label, key), value in sorted(groups.items(), key=lambda item: item[1]['logical_bytes'], reverse=True)[:40]],
        'protected_scopes_not_traversed': skipped, 'scan_errors': errors,
        'already_completed_cleanup': past_cleanup,
        'already_completed_cleanup_logical_bytes': sum(r['logical_bytes'] for r in past_cleanup),
        'candidate_categories': categories, 'candidate_files': len(candidates),
        'candidate_logical_bytes': sum(r['bytes'] for r in candidates),
        'candidate_metadata_and_exact_recovery_references': candidates,
        'size_mismatched_or_partial_payloads_held': mismatched,
        'proof_input_files': evidence,
        'protected_current_state': ['All current master sources, gates, launch/closure/owner/unlock receipts and active scientific namespace.',
            'Original workflow.lock, tool mount/native guards, both VM images and installed runtime/model/DB/source prefixes.',
            'Old Git metadata and private control/chat histories; no private payload contents read.',
            'All original source archives and expanded mamba/host/validation prefixes; no cache-to-prefix independence is inferred.'],
        'limits': ['Only logical file lengths were summed; hardlinks/sparse files can overstate physical reclaimable storage.',
            'Stored FRESH_REMOTE receipts prove their dated downloads/member SHA/CRC; no current network availability or current local payload rehash was performed.',
            'Candidate payload files match current metadata lengths only. Exact retained-handle hash/identity, no-active-owner and current remote asset/tag checks remain required before any literal leaf purge.',
            'Preserve all receipt/published_control files. Prefer duplicate downloaded/built ZIP transport first; acquired package blobs are a separate follow-on candidate.',
            'Disk cleanup is not evidence of resolving the current Linux memory admission shortfall.',
            'Ubuntu ext4.vhdx and Windows/profile/private caches outside the three fixed C scopes were not scanned.'],
        'effects': {'VM_runtime_cache_scientific_or_private_payload_reads': 0, 'WSL_UNC_native_lock_network': 0,
                    'source_mutations': 0, 'deletions': 0, 'Git_ref_mutations': 0,
                    'actual_VM_split_inventory_capture_restore_eviction': 'NOT_RUN'},
        'deletion_authorized_now': False}
    output = WORK/'postcleanup_sidefolder_inventory01.json'
    with output.open('xb') as stream:
        stream.write((json.dumps(report, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'state': report['state'], 'report': str(output), 'report_sha256': sha(output.read_bytes()),
                      'source_sha256': report['observer_source_sha256'], 'scope_totals': totals,
                      'candidate_categories': categories, 'candidate_files': len(candidates),
                      'candidate_logical_bytes': report['candidate_logical_bytes'], 'elapsed_seconds': report['elapsed_seconds']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
