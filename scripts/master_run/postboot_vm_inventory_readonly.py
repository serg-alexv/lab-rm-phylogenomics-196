"""Bounded metadata-only VM/recovery inventory. No WSL or image payload reads.

This writes one new public review receipt. It neither qualifies a backup nor
changes, detaches, renames, truncates, splits, or removes any registered disk.
"""
from pathlib import Path
import ctypes
import datetime as dt
import hashlib
import json
import math
import os
import stat
import urllib.request
import winreg

WORK = Path(__file__).resolve().parent
PYTHON_ROOT = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
IMAGES = {
    'stage05_installed_scientific_toolchain_ext4': PYTHON_ROOT / '.tools' / 'toolchain.ext4',
    'ubuntu_wsl2_root_vhdx': Path(r'C:\Users\wheel\AppData\Local\wsl\{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}\ext4.vhdx'),
}
SHARD_LIMIT = 448 * 1024**2
SOURCES = [
    'POST_RESTART_CONTINUATION.md',
    'stage5_runtime_recovery_contract.py',
    'stage5_runtime_logical_capture.py',
    'verify_stage5_runtime_logical_payload.py',
    'verify_stage5_runtime_cold_tree.py',
    'stage5_runtime_safe_extract.py',
    'stage5_runtime_recovery_IMPLEMENTATION_LIMITS.md',
    'stage5_runtime_recovery_preparation01/PLAN.json',
    'stage5_runtime_recovery_preparation01/CAPTURE_INPUTS_PENDING.json',
    'stage5_runtime_recovery_preparation01/PUBLIC_COMPLETION.json',
]


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def small_public_file(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_size > 2 * 1024**2:
        raise ValueError('Expected bounded plain public source/control')
    raw = path.read_bytes()
    after = path.lstat()
    if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('Public source changed during inventory')
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def allocated_bytes(path):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCompressedFileSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    kernel.GetCompressedFileSizeW.restype = ctypes.c_uint32
    high = ctypes.c_uint32()
    ctypes.set_last_error(0)
    low = kernel.GetCompressedFileSizeW(str(path), ctypes.byref(high))
    if low == 0xFFFFFFFF and ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())
    return (high.value << 32) | low


def image_metadata(role, path):
    checked = []
    for ancestor in reversed([path, *path.parents]):
        info = ancestor.lstat()
        if getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Reparse ancestor or image requires separate review')
        checked.append(str(ancestor))
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError('Expected plain image file')
    allocation = allocated_bytes(path)
    after = path.lstat()
    result = {
        'role': role, 'path': str(path), 'logical_bytes': before.st_size,
        'filesystem_allocated_bytes_metadata': allocation,
        'windows_file_attributes': getattr(before, 'st_file_attributes', None),
        'source_device': before.st_dev, 'source_inode': before.st_ino,
        'creation_utc': dt.datetime.fromtimestamp(before.st_birthtime, dt.timezone.utc).isoformat(),
        'last_write_before_utc': dt.datetime.fromtimestamp(before.st_mtime, dt.timezone.utc).isoformat(),
        'last_write_after_utc': dt.datetime.fromtimestamp(after.st_mtime, dt.timezone.utc).isoformat(),
        'metadata_stable_during_observation':
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
        'payload_sha256': None, 'payload_bytes_read': 0,
        'reparse_ancestry_checked_count': len(checked),
        'hypothetical_uncompressed_byte_shards_at_448MiB': math.ceil(before.st_size / SHARD_LIMIT),
        'last_uncompressed_byte_shard_bytes': before.st_size % SHARD_LIMIT or SHARD_LIMIT,
        'archive_created': False, 'public_payload_scope_accepted': False,
        'exact_remote_image_recovery': 'NOT_ESTABLISHED',
    }
    if before.st_dev != after.st_dev or before.st_ino != after.st_ino:
        raise ValueError('Image identity changed during metadata observation')
    return result


def distro_registry():
    rows = []
    keypath = r'Software\Microsoft\Windows\CurrentVersion\Lxss'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, keypath, 0, winreg.KEY_READ) as key:
        number = 0
        while True:
            try:
                subname = winreg.EnumKey(key, number)
            except OSError as error:
                if error.winerror == 259:
                    break
                raise
            number += 1
            if number > 32:
                raise ValueError('Unexpected distro registry count')
            with winreg.OpenKey(key, subname, 0, winreg.KEY_READ) as subkey:
                row = {'registry_key': subname}
                for name in ['DistributionName', 'Version', 'BasePath', 'VhdFileName', 'DefaultUid', 'Flags', 'State']:
                    try:
                        row[name] = winreg.QueryValueEx(subkey, name)[0]
                    except FileNotFoundError:
                        row[name] = None
                rows.append(row)
    return rows


def public_release_metadata():
    url = 'https://api.github.com/repos/serg-alexv/lab-rm-phylogenomics-196/releases/tags/master-run-storage-20261009-v1'
    request = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'lab-rm-readonly-vm-inventory'})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(2 * 1024**2 + 1)
    if len(raw) > 2 * 1024**2:
        raise ValueError('Release metadata exceeds bound')
    value = json.loads(raw)
    assets = [{'id': row['id'], 'name': row['name'], 'bytes': row['size'],
               'digest': row.get('digest'), 'state': row['state']} for row in value['assets']]
    return {
        'api_url': url, 'observed_utc': now(), 'api_json_sha256': hashlib.sha256(raw).hexdigest(),
        'release_id': value['id'], 'tag': value['tag_name'], 'url': value['html_url'],
        'target_commitish': value['target_commitish'], 'draft': value['draft'],
        'asset_count': len(assets), 'assets': assets,
        'verification_scope': 'FRESH_PUBLIC_METADATA_ONLY_NO_ASSET_PAYLOAD_READBACK',
        'installed_runtime_or_vm_shards_present_by_name': any(
            any(token in row['name'].lower() for token in ['installed-runtime', '.ext4', '.vhdx', 'ubuntu-root']) for row in assets),
    }


def main():
    if os.name != 'nt':
        raise ValueError('Windows metadata observation required')
    target = WORK / 'postboot_vm_recovery_review01.json'
    if target.exists():
        raise ValueError('Never overwrite an existing review receipt')
    receipt = {
        'schema': 'POSTBOOT_VM_METADATA_RECOVERY_REVIEW_V1', 'started_utc': now(),
        'state': 'PASS_BOUNDED_METADATA_INVENTORY_RECOVERY_DESIGN_ONLY',
        'images': [image_metadata(role, path) for role, path in IMAGES.items()],
        'distro_registry': distro_registry(),
        'wslconfig': small_public_file(Path(r'C:\Users\wheel\.wslconfig')),
        'existing_public_sources': [small_public_file(WORK / name) for name in SOURCES],
        'fresh_github_recovery_metadata': public_release_metadata(),
        'primary_strategy': 'REVIEWED_CONTENT_LOGICAL_ARCHIVES_PLUS_PINNED_OS_BOOTSTRAP_AND_ORIGINAL_SOURCES',
        'primary_scope': {
            'toolchain': 'Complete exact installed detector_env, defense_models and padloc_db logical bytes and POSIX metadata at original prefixes; one common manifest covers cross-role links.',
            'ubuntu': 'Separately inventory and preserve project-required Ubuntu loader/glibc/OS packages, configuration and bootstrap with full original source/notices; full distro and free-block contents are not presumed public.',
            'public_review': 'Screening emits reason codes only. Whole-file review must qualify required bytes and metadata before public archive capture. Private whole files remain excluded and required excluded dependency blocks complete public recovery.',
            'format': 'Existing gzip/PAX logical stream split at compressed byte boundaries, at most448MiB each; all shards plus the exact ordered index are required for restoration.',
            'content_label_proposal': 'stage05-runtime-detector-env-defense-models-padloc-db-20261010-v1.partNNNN',
            'label_limit': 'A compressed byte shard can span roles and is not independently extractable. The label describes the complete archive. Individual role capsules require a separate reviewed schema with cross-role dependency handling.',
            'coordinated_source_change_required': 'Producer21b33abc, independent reader9770354d and extractorbeec0d30 currently all require stage5-installed-runtime-01.partNNNN. Do not rename only producer output. Update and review all contracts together, or use an exact manifest-pinned remote transport alias adapter.',
        },
        'bounded_fallback': {
            'strategy': 'OFFLINE_BYTE_EXACT_SNAPSHOT_SHARDS_ONLY_IF_LOGICAL_RESTORATION_IS_INSUFFICIENT_AND_FULL_PUBLIC_SCOPE_IS_ACCEPTED',
            'conditions': ['All native work closed and original WorkflowLock held', 'Unmount loop aliases and stop Ubuntu through the root-owned lifecycle protocol', 'Retained offline source identity and stable full image SHA', 'Whole VM/free-block payload public audit or keep snapshot private outside public GitHub', 'Create new448MiB content-labelled shard files; never truncate or replace registered backing files', 'Independent zero-offset fresh GitHub full shard downloads, ordered whole-image SHA, disposable reassembly and actual cold mount/import test before deleting originals'],
            'toolchain_exact_snapshot_label': 'stage05-toolchain-detectors-models-db.ext4.partNNNN',
            'ubuntu_exact_snapshot_label': 'ubuntu-wsl2-os-bootstrap.ext4.vhdx.partNNNN',
            'run_now': False,
        },
        'proposed_remote_structure': {
            'git': ['scripts/master_run/recovery sources and tests', 'recovery/runtime/<snapshot>/INDEX.json, MANIFEST.jsonl, PUBLIC_SCOPE.json, NOTICES.json, RESTORE.md', 'reports/master_run/20261009/<snapshot>/capture, remote readback and cold restore receipts', 'status/master_run_20261009.json current evidence pointers'],
            'release': 'Immutable stage05-installed-runtime-<date>-v1 Release for448MiB payload assets and exact SHA256 sidecars; Git index pins source commit, tag commit, assetIDs, bytes, digests and ordered compressed stream SHA.',
            'local': 'Keep one working checkout and required original runtime prefixes until restore qualifies; use unique temporary capture/verification namespaces and delete only closed, remotely recovered nonrequired bytes after receipt.',
        },
        'next_bounded_steps': [
            'Root finishes new-boot/STOP reconciliation and fresh Stage5 runtime gates; source-byte/runtime manifests are prerequisites.',
            'Integrate inactive inventory with the existing Windows owner, finite Linux lease, resource callback and read-only frozen mount proof; no concurrent Stage5 detector or writer.',
            'Run full no-follow installed inventory and explicit OS/dependency fingerprint; keep raw candidates private until whole-file public and notices/source reviews.',
            'Publish reviewed operational sources and synthetic real Linux archive/extract fixtures, preserving all original source/notices.',
            'Capture448MiB logical shards to a new namespace with measured physical and commit reserves and one compression reader.',
            'Publish immutable index and assets; download every payload fresh and verify complete stream, every member and POSIX/link metadata independently.',
            'Cold restore from fresh remote bytes on new ext4, compare full logical tree, restore original prefixes and qualify actual pinned runtime plus benign fixtures.',
            'Only after all required recovery gates pass may root evict obsolete originals and compact/recreate the working VM using supported WSL lifecycle operations.',
        ],
        'external_primary_sources': [
            {'url': 'https://learn.microsoft.com/en-us/windows/wsl/basic-commands', 'used_for': 'Supported distro export/import, in-place import, shutdown and unregister semantics.'},
            {'url': 'https://learn.microsoft.com/en-us/windows/wsl/disk-space', 'used_for': 'Registered ext4.vhdx is a live distro backing file; Microsoft warns against modifying/moving AppData WSL files with Windows tools.'},
            {'url': 'https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases', 'used_for': 'Release assets as repository-associated recovery storage.'},
        ],
        'actual_limits': {
            'wsl_executions': 0, 'image_payload_bytes_read': 0, 'disk_mount_changes': 0,
            'image_changes_or_renames': 0, 'actual_split_shards_created': 0,
            'full_installed_inventory': 'NOT_RUN', 'public_payload_scope_review': 'NOT_RUN',
            'logical_runtime_capture': 'NOT_RUN', 'fresh_remote_runtime_payload_readback': 'NOT_RUN',
            'cold_restore': 'NOT_RUN', 'runtime_equivalence': 'NOT_ESTABLISHED',
            'exact_vm_recovery': 'NOT_ESTABLISHED', 'eviction_or_host_wipe_authority': False,
            'allocation_metric': 'Windows filesystem allocation metadata, not reclaimed bytes or guest-used filesystem bytes.',
        },
        'completed_utc': now(),
    }
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    result = small_public_file(target)
    print(json.dumps({'state': receipt['state'], 'receipt': result, 'images': receipt['images'],
                      'remote_asset_count': receipt['fresh_github_recovery_metadata']['asset_count']}, indent=2))


if __name__ == '__main__':
    main()
