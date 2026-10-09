"""Prepare public recovery controls from exact retained C evidence only.

No image/runtime payload read, WSL, mount, subprocess, archive build, network,
scientific execution or deletion. Default no operation. Actual capture is pending.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PREFIX = '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux'
ROOTS = {'environment_dir': PREFIX + '/detector_env',
         'models_dir': PREFIX + '/defense_models', 'padloc_db': PREFIX + '/padloc_db'}
EVIDENCE = {
    'master_toolchain_preservation_plan.json': '8ece8ee1afea53392c6dd6b14872595f02b91f77fd639f3c81ff836830d818d5',
    'master_public_components01/frozen/manifests/detector_package_manifest.json': '45fc8f2d49ea313afd7a18d489b6dfe8cf940591334a713ef584fca1ccb2e382',
    'master_public_components01/frozen/manifests/host_package_manifest.json': 'e8c84f6c390cc0f03349c54f3992d7cc790a5388c15eec5c4ad5bab7453bfe48',
    'public_conda_packages01_final_index.json': 'f0b6f3a43909a43d5e409afb2f1edd5c04db6fc6f1eba00843534ac3ad9e503c',
    'public_conda_packages01_readback_20261009T212013Z_9326e9e6/receipt.json': '02d56dc933db94af3b93a737e55ffd4463cdc88e9e96cb885c02bc6311b6ea6a',
    'public_components01_readback_20261009T195312Z_16720f4a/receipt.json': '8c075ca1a75e0c4af4242e3caa0e17be0797e219fbd0cc69bc0202834cc1d07f',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(output):
    require(Path(__file__).resolve().parent == WORK, 'Exact active C source required')
    require(output.parent == WORK and re.fullmatch('stage5_runtime_recovery_preparation[0-9]{2}', output.name)
            and not output.exists() and not output.is_symlink(), 'New exact C preparation namespace only')
    values, pins = {}, []
    source = Path(__file__).read_bytes()
    for name, expected in EVIDENCE.items():
        p = WORK / name
        require(p.is_file() and not p.is_symlink() and p.stat().st_size < 2 * 1024**2, 'Bounded exact C evidence')
        raw = p.read_bytes()
        require(sha(raw) == expected, 'Retained evidence changed: ' + name)
        values[name] = json.loads(raw)
        pins.append(dict(path=str(p), bytes=len(raw), sha256=expected))
    old = values['master_toolchain_preservation_plan.json']
    conda = values['public_conda_packages01_readback_20261009T212013Z_9326e9e6/receipt.json']
    components = values['public_components01_readback_20261009T195312Z_16720f4a/receipt.json']
    require(conda['state'] == 'PASS_FRESH_REMOTE_CONDA339_ORIGINALS_397_ROLES_363_MEMBERS'
            and conda['original_packages'] == 339 and conda['original_package_bytes'] == 660114049
            and conda['installed_runtime_complete'] is False, 'Exact original Conda recovery evidence')
    require(components['state'] == 'PASS_FRESH_REMOTE_COMPONENTS29_MEMBERS_17_ORIGINALS_EXPLICIT_NOTICE_GAPS'
            and components['installed_toolchain_image_included'] is False, 'Exact source/model recovery evidence')
    manifests = [values['master_public_components01/frozen/manifests/' + name]['packages']
                 for name in ['detector_package_manifest.json', 'host_package_manifest.json']]
    require([len(x) for x in manifests] == [255, 142]
            and len({r['sha256'] for rows in manifests for r in rows}) == 339, 'Recorded resolution roles')
    plan = dict(
        schema='STAGE05_INSTALLED_RUNTIME_RECOVERY_PREPARATION_V1',
        state='PENDING_ACTUAL_FULL_INVENTORY_PUBLIC_REVIEW_COLD_CAPTURE_AND_RESTORE',
        evidence=pins, source_sha256=sha(source), actual_runtime_manifest=None,
        exact_roots=ROOTS, original_prefix_required=True,
        recorded_image_metadata={**old['image'], 'fresh_metadata_check': 'NOT_RUN',
                                 'image_payload_bytes_read_by_preparation': 0},
        independently_verified_original_packages=dict(count=339, bytes=660114049,
            resolution_roles=397, installed_build_equivalence=False,
            remote_readback_receipt_sha256=EVIDENCE['public_conda_packages01_readback_20261009T212013Z_9326e9e6/receipt.json'],
            release=conda['release_url'], assets=conda['downloaded_assets']),
        independently_verified_sources_models_notices=dict(
            remote_readback_receipt_sha256=EVIDENCE['public_components01_readback_20261009T195312Z_16720f4a/receipt.json'],
            assets=components['downloaded_assets'], full_corresponding_source_coverage='NOT_ESTABLISHED'),
        primary_strategy='FULL_REVIEWED_LOGICAL_THREE_ROOT_COPY_PLUS_ORIGINAL_PACKAGES_AND_SOURCES',
        minimum_actual_capture_inputs=[
            'Fresh successful STAGE05_PINNED_RUNTIME_V1 candidate from the retained mounted interpreter; roots must equal these exact three prefixes. Its env file map is a scientific subset, not full installed inventory.',
            'Complete no-follow three-root inventory: every directory/regular/symlink/internal-hardlink, full regular-file SHA, original device/inode/linkcount/ctime, exact UTF8 path, mode/uid/gid/mtime_ns and all xattr/ACL/capability values. Hold special files, unknown names/metadata, dangling/external links and unresolved privilege bits.',
            'Whole-file public review tied to the full inventory SHA: scan all payload/xattr/target bytes and reviewed package metadata; preserve entire excluded files privately without redaction. Screening alone never establishes public scope. Any excluded scientific-manifest dependency blocks complete public recovery.',
            'Installed Conda conda-meta records and info/paths.json original package mapping; complete pip .dist-info METADATA/RECORD/direct_url.json/licenses; complete R library DESCRIPTION/COPYING/compiled libraries; all installed binaries/shared libraries/data and local changes. Missing wheel/source or notice mapping stays an explicit gap, not an equivalence claim.',
            'Independent notice/source attribution review including original copyright/licenses/COPYRIGHT/COPYING and local modification attribution. Existing Conda/model source assets are referenced by exact digest/member; no package reinstall is claimed identical.',
            'Root-owned cold/exclusive capture proof under the original WorkflowLock, all relevant native descendants closed, no runtime writer/writable mount alias, exact loop-image/mount/UUID/device identity and read-only runtime freeze. No new controller or lock is introduced.',
            'Measured host physical AND commit reserve >=1536MiB, one below-normal compression reader, <=256KiB buffers, finite deadline and owned process closure through existing supervisor. Existing owner integration must be reviewed before invoking the capture function; no unmonitored standalone build is supplied.'
        ],
        logical_archive=dict(format='SINGLE_PAX_TAR_GZIP_STREAM_SPLIT_AT_COMPRESSED_BYTE_BOUNDARIES',
            gzip_level=1, gzip_mtime=0, maximum_asset_bytes=448 * 1024**2,
            stream_chunk_bytes=256 * 1024, parallel_compression_workers=1,
            output='New direct C-mounted chat work namespace; no G exports and no raw block-image publication',
            metadata='Exact mode/uid/gid/mtime_ns/target/internal hardlink graph; xattrs/ACL/capabilities losslessly represented in reviewed manifest. No chown/chmod or link dereference during capture.',
            first_control='Exhaustive reviewed manifest (bounded streamed JSONL) plus original runtime candidate/public-review/attribution/cold-proof bytes',
            index='Small Git index pins ordered shard names/size/SHA, whole compressed-stream SHA, manifest SHA/count/byte bound, every control source pin and explicit exclusions/limits',
            sidecars='Exact ASCII SHA256  two spaces  assetname LF; per-shard and ordered whole-stream digests',
            failures='Preserve partial output and failed receipt. No retry, source deletion, mutation, package installer or acceptance promotion.'),
        fresh_remote_verification=[
            'Publish exact source/tests/review/index and small controls first; root alone uploads immutable shards and original sidecars.',
            'Use existing retained owned-gh monitor with source commit separate from Release tag commit, host reserve and deadline; fresh zero-offset downloads of EVERY shard and sidecar into a new C namespace.',
            'Verify Git blob objects and independently pinned index, exact unique ordered asset IDs/digests/sizes before and after download, every shard SHA and ordered compressed-stream SHA.',
            'Stream decompress/parse every tar payload to EOF: exhaustive manifest membership, all full file SHAs and logical lengths, exact POSIX metadata/link graph, no duplicate/path traversal/special members, complete control/notices and gzip CRC. No extraction/execution at readback.',
            'Independent reader must not import the capture producer. Actual reader pins cannot be frozen until actual manifest/index/shard bytes exist; preparation has no remote payload acceptance.'
        ],
        cold_restoration_verification=[
            'Use a new disposable ext4 restore target, never overwrite the retained runtime. Restore only freshly verified reviewed members with directory-relative no-follow creation, no tar.extractall, no link traversal, directories first and symlinks last.',
            'Recreate internal hardlinks only to previously verified regular files, restore exact modes/mtime/uid/gid plus all reviewed xattrs/ACL/capabilities; required privileges or unsupported metadata cause an explicit stop.',
            'Independent no-follow rescan compares exhaustive path/type/bytes/SHA/mode/uid/gid/mtime_ns/xattrs/targets/internal hardlink equivalence. Source inode/birth/ctime and original block-image SHA are provenance, not recreated identity.',
            'Absolute symlinks, shebangs and Conda prefix substitutions require the ORIGINAL three installation prefixes. A staging-prefix scan does not prove those binaries will run. Under a separate cold lock, mount a clean derived runtime at the exact original prefix before runtime discovery/version/dependency checks.',
            'Re-run actual scientific runtime discovery and compare every selected binary/source/model/library SHA and effective ambient configuration, then the bounded operational fixtures. No biological inference/search is needed for logical restoration acceptance.',
            'Only then PASS_EXACT_SCOPED_LOGICAL_RUNTIME_RESTORATION; distinguish this from bit-identical8GiB image recovery, complete corresponding-source audit and biological acceptance. Until then retain the original image and required private/excluded files; host-wipe authority remains NONE.'
        ],
        explicit_limits=dict(actual_inventory='NOT_RUN', public_payload_review='NOT_RUN',
            installed_pip_R_localmods_enumeration='NOT_RUN', cold_capture='NOT_RUN',
            archives_created=0, image_payload_bytes_read=0, wsl_starts=0, mounts=0,
            fresh_remote_runtime_payload_readback='NOT_RUN', cold_restore='NOT_RUN',
            installed_build_equivalence='NOT_ESTABLISHED', biological_acceptance=False,
            host_wipe_authority=False))
    template = dict(schema='STAGE05_INSTALLED_RUNTIME_CAPTURE_INPUTS_V1', state='PENDING_NOT_AUTHORITY',
        roots=ROOTS, original_prefix_required=True,
        actual_runtime_manifest_sha256=None, complete_inventory_sha256=None,
        whole_file_public_review_sha256=None, cold_exclusive_capture_receipt_sha256=None,
        license_source_notice_review_sha256=None, published_capture_source_sha256=None,
        all_required_runtime_files_public_and_covered=False, all_special_metadata_resolved=False,
        installed_build_equivalence='NOT_ESTABLISHED', actual_capture='NOT_RUN')
    require(Path(__file__).read_bytes() == source, 'Preparation source changed')
    output.mkdir()
    for name, value in [('PLAN.json', plan), ('CAPTURE_INPUTS_PENDING.json', template)]:
        with (output / name).open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
    return {name: dict(bytes=(output / name).stat().st_size, sha256=sha((output / name).read_bytes()))
            for name in ['PLAN.json', 'CAPTURE_INPUTS_PENDING.json']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.prepare:
        require(args.output, 'New C work output is required')
        print(json.dumps(prepare(Path(args.output)), indent=2, sort_keys=True))
    else:
        print(json.dumps(dict(state='NOT_RUN', image_payload_bytes_read=0, archives_created=0)))
