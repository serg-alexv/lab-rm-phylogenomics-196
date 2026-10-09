"""Independent exact Conda-original Release readback; never extract or install.

Requires an immutable published source commit. Only fresh C receipt/download files
are written. Local inspection is explicitly weaker than fresh remote readback.
"""
from pathlib import Path
import collections
import ctypes
from ctypes import wintypes as W
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import sys
import time
from urllib.parse import urlsplit
import zipfile

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parent
EXACT_WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PREFIX = 'reports/master_run/20261009/cleanup/conda_packages01/'
LOCAL = WORK / 'public_conda_packages01_continuation_20261009T204518Z_bd4c1b76'
INDEX_SHA = 'f0b6f3a43909a43d5e409afb2f1edd5c04db6fc6f1eba00843534ac3ad9e503c'
BASE_SHA = 'e94e2d59e6d4b91353916db7bdf8485ecff0eba181f644e534a7e742e1e5bffc'
CONTINUE_SHA = 'a743347ee1d79afa438b9d95494db1736d7012536cca3ee4d1ff82c56ef11460'
REVIEW_SHA = '9def755b2d8917b8c135df9b8498a6ef6075625ca9e4b220b9532b8a145e9c57'
PLAN_SHA = 'ab4f2d6cb9a39815397e7281c636527139ce4fd1bc43c2adccd16835420b1862'
MANIFESTS = {
    'detector_package_manifest.json': '45fc8f2d49ea313afd7a18d489b6dfe8cf940591334a713ef584fca1ccb2e382',
    'host_package_manifest.json': 'e8c84f6c390cc0f03349c54f3992d7cc790a5388c15eec5c4ad5bab7453bfe48',
}
CONTROLS = {
    'ATTRIBUTION_AND_RESTORE.txt': 'e49032947e47ef5d95d357691a3836c51bf785e9d0f154c743094b0c99de248c',
    'acquisition_receipt.json': '6807810fad659bd47af053464af0dd899c22bbce8808288d15585aae6c6b14cf',
    'build_receipt.json': '66f250b24ce4978d7a9d34f8b40577bf1485f71779803a455e8551e090941931',
    **MANIFESTS,
    'downloaded_packages.jsonl': '07a819ee3d4871abd40cce03f969cf44ffc98884f696d7bac2f2cc80ecfc992b',
    'original_download_errors.jsonl': '64d2db6b72df0a73152df596b21b4b9548be1b0a62297ce0662012d574c760aa',
    'original_resource_stop_receipt.json': '001442792f652547bf79a85f8dee7ab0b5e3fddefdcbf5de47882b2b97b85c4b',
    'package_index.json': 'f016dc25c7c4fc7aa167ed22eeb4cd434f71d6d6b9cab50c0e47ff5bbb4a6233',
    'progress.json': 'e95de13e0366a4c948f03a6cb127b4b5f404a4cd14641b89098037d814827254',
    'recovery_plan.json': PLAN_SHA,
    'resources.jsonl': '3709922b6e145704fd33729be9ee58bb7e33b7a2ea5a1ab7506eea6951fa5e8d',
}
CODE = {
    'verify_master_public_components01_remote.py': '6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691',
    'verify_master_original_sidecars.py': '090e8068d9f2ee0a21631541681a835de5f97bd1cf695b06537aabeb4bf24841',
    'acquire_public_conda_packages01.py': BASE_SHA,
    'continue_public_conda_packages01.py': CONTINUE_SHA,
}
ASSETS = [
    dict(name='master_public_conda_packages01-001.zip', bytes=448642191,
         sha256='18e60eea6e797fa92047beebc78ff19171eb4298ab0d21f3c997e33147e4d3a6'),
    dict(name='master_public_conda_packages01-002.zip', bytes=214192437,
         sha256='0f65cc94c8ed0cf89a208d22465889eaf65e63153d231a3a776be3dfe20a4cbb'),
]
SIDECARS = [
    dict(name=ASSETS[0]['name'] + '.sha256', bytes=105, newline='\n',
         sha256='edcb298e5dc1e4e191bbba6924c68211044d699a1f7ee7567276a30e11aef1fe'),
    dict(name=ASSETS[1]['name'] + '.sha256', bytes=105, newline='\n',
         sha256='cc596d092b1105c33d055146bc2312ccb8bf57094657bc5debd2d87314a69c89'),
]
BLOCK = 1024**2
RESERVE = 3 * 1024**3 // 2
DEADLINE = float('inf')
RESOURCE = None
RESOURCE_MIN = {}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load_helper(name):
    path = WORK / name
    require(hashlib.sha256(path.read_bytes()).hexdigest() == CODE[name], 'Independent helper source differs')
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


A = load_helper('verify_master_public_components01_remote.py')
S = load_helper('verify_master_original_sidecars.py')


class ResourceReader:
    def __init__(self):
        require(os.name == 'nt' and ctypes.sizeof(ctypes.c_void_p) == 8, 'Windows64 reader required')
        class PERF(ctypes.Structure):
            _fields_ = [('cb', W.DWORD)] + [(n, ctypes.c_size_t) for n in
                ('CommitTotal', 'CommitLimit', 'CommitPeak', 'PhysicalTotal', 'PhysicalAvailable', 'SystemCache',
                 'KernelTotal', 'KernelPaged', 'KernelNonpaged', 'PageSize')] + [(n, W.DWORD) for n in
                ('HandleCount', 'ProcessCount', 'ThreadCount')]
        require(ctypes.sizeof(PERF) == 104, 'Unexpected PERFORMANCE_INFORMATION layout')
        self.PERF = PERF; self.psapi = ctypes.WinDLL('psapi', use_last_error=True)
        self.psapi.GetPerformanceInfo.argtypes = [ctypes.POINTER(PERF), W.DWORD]
        self.psapi.GetPerformanceInfo.restype = W.BOOL
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = W.HANDLE
        kernel.SetPriorityClass.argtypes = [W.HANDLE, W.DWORD]; kernel.SetPriorityClass.restype = W.BOOL
        kernel.GetPriorityClass.argtypes = [W.HANDLE]; kernel.GetPriorityClass.restype = W.DWORD
        handle = kernel.GetCurrentProcess()
        require(kernel.SetPriorityClass(handle, 0x4000) and kernel.GetPriorityClass(handle) == 0x4000,
                'Own below-normal priority not established')

    def read(self):
        value = self.PERF(); value.cb = ctypes.sizeof(value)
        require(self.psapi.GetPerformanceInfo(ctypes.byref(value), ctypes.sizeof(value)), 'GetPerformanceInfo failed')
        return dict(physical_available_bytes=value.PhysicalAvailable * value.PageSize,
                    commit_headroom_bytes=(value.CommitLimit - value.CommitTotal) * value.PageSize,
                    c_disk_free_bytes=shutil.disk_usage(WORK).free)


def guard():
    require(time.monotonic() < DEADLINE, 'Finite 1800-second readback budget exceeded')
    if RESOURCE is not None:
        values = RESOURCE.read()
        require(values['physical_available_bytes'] >= RESERVE and values['commit_headroom_bytes'] >= RESERVE
                and values['c_disk_free_bytes'] >= 10 * 1024**3, 'Current RAM/commit/C disk reserve failed; no automatic retry')
        for key, value in values.items():
            RESOURCE_MIN[key] = min(value, RESOURCE_MIN.get(key, value))


def streamed_sha(stream):
    digest = hashlib.sha256(); count = 0
    for block in iter(lambda: stream.read(BLOCK), b''):
        guard(); digest.update(block); count += len(block)
    guard()
    return count, digest.hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return streamed_sha(stream)[1]


def expected_packages(manifests, package_index, counts=(255, 142), unique=339, total=660114049):
    """Rebuild all role/row/license bindings directly from original manifest rows."""
    records = []; packages = {}
    for (name, data), expected_count in zip(manifests.items(), counts):
        rows = json.loads(data)['packages']; require(len(rows) == expected_count, 'Original manifest count differs')
        for number, row in enumerate(rows):
            url = urlsplit(row['url'])
            require(url.scheme == 'https' and url.hostname == 'conda.anaconda.org' and url.port in (None, 443)
                    and not url.username and not url.password and not url.query and not url.fragment
                    and len(url.path.split('/')) == 4 and url.path.split('/')[1] in ('conda-forge', 'bioconda')
                    and row['subdir'] in ('linux-64', 'noarch') and re.fullmatch('[A-Za-z0-9_.+-]+', row['fn'])
                    and row['url'] == 'https://conda.anaconda.org/' + url.path.split('/')[1] + '/' + row['subdir'] + '/' + row['fn']
                    and re.fullmatch('[a-f0-9]{64}', row['sha256']) and type(row['size']) is int
                    and 0 < row['size'] < 448 * 1024**2 and isinstance(row['license'], str) and bool(row['license']),
                    'Invalid original official URL/SHA/size/license/filename')
            records.append(dict(manifest=name, row_index=number, original_record=row))
            pin = dict(name=row['name'], version=row['version'], build=row.get('build', row.get('build_string')),
                       filename=row['fn'], subdir=row['subdir'], url=row['url'], bytes=row['size'],
                       sha256=row['sha256'], license=row['license'], source_records=[])
            key = row['sha256']
            if key in packages:
                require(all(packages[key][k] == value for k, value in pin.items() if k != 'source_records'),
                        'Conflicting original package SHA role metadata')
            else:
                packages[key] = pin
            packages[key]['source_records'].append(dict(manifest=name, row_index=number))
    ordered = [packages[key] for key in sorted(packages)]
    require(len(records) == sum(counts) and len(ordered) == unique and sum(p['bytes'] for p in ordered) == total,
            'Exact original record/package/byte accounting differs')
    require(package_index == dict(schema='MASTER_EXACT_PUBLIC_CONDA_PACKAGE_INDEX_V1', original_records=records,
            packages=ordered, manifest_pins=MANIFESTS, total_distinct_bytes=total, recovery_plan_sha256=PLAN_SHA),
            'Package index does not exactly preserve original role/license records')
    return {'packages/' + p['sha256'] + '/' + p['filename']: p for p in ordered}


def check_package_coverage(observed, expected):
    require(len(observed) == len(expected) and set(observed) == set(expected), 'Exact package coverage differs')
    for name, row in observed.items():
        require(row['bytes'] == expected[name]['bytes'] and row['sha256'] == expected[name]['sha256'],
                'Actual original package bytes differ: ' + name)


def verify_zip(path, asset, expected):
    require(path.stat().st_size == asset['bytes'] < 448 * 1024**2 and file_sha(path) == asset['sha256'], 'Outer original shard differs')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist(); A.safe_names(names)
        require(len(names) == len(expected) and set(names) == set(expected), 'Exact original shard members differ')
        require(sum(i.file_size for i in archive.infolist()) == sum(r['bytes'] for r in expected.values()), 'Uncompressed bound differs')
        checks = {}
        for line in archive.read('SHA256SUMS.txt').decode('ascii').splitlines():
            match = re.fullmatch(r'([a-f0-9]{64})  (.+)', line)
            require(match and match[2] not in checks, 'Invalid/duplicate SUMS row')
            checks[match[2]] = match[1]
        require(set(checks) == set(names) - {'SHA256SUMS.txt'}, 'Nonexhaustive internal SUMS')
        actual = {}
        for info in archive.infolist():
            require(info.compress_type == zipfile.ZIP_STORED and not info.is_dir() and not info.flag_bits & 1
                    and stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG)
                    and info.date_time == (2026, 10, 9, 0, 0, 0), 'Nonoriginal/nonregular shard member')
            with archive.open(info) as stream:
                size, digest = streamed_sha(stream)  # EOF also triggers independent ZIP CRC validation.
            pin = expected[info.filename]
            require(size == info.file_size == pin['bytes'] and digest == pin['sha256'] and pin['crc_verified'] is True
                    and f'{info.CRC:08x}' == pin['crc32'], 'Actual EOF CRC/SHA differs: ' + info.filename)
            require(info.filename == 'SHA256SUMS.txt' or checks[info.filename] == digest, 'Internal member SHA differs')
            actual[info.filename] = dict(member=info.filename, bytes=size, sha256=digest, crc32=f'{info.CRC:08x}', crc_verified=True)
        return actual


def verify(args, out, result):
    guard()
    extras = {PREFIX + 'final_index.json': (WORK / 'public_conda_packages01_final_index.json', INDEX_SHA),
              PREFIX + 'CONTINUATION_SOURCE_REVIEW.json': (WORK / 'public_conda_continuation01_source_review.json', REVIEW_SHA)}
    raw = A.get_controls(args, CONTROLS, {**CODE, Path(__file__).name: file_sha(__file__)}, PREFIX, LOCAL, out, result, extras)
    controls = {name: raw[PREFIX + name] for name in CONTROLS}
    index = json.loads(raw[PREFIX + 'final_index.json']); build = json.loads(controls['build_receipt.json'])
    acquisition = json.loads(controls['acquisition_receipt.json']); plan = json.loads(controls['recovery_plan.json'])
    failure = json.loads(controls['original_resource_stop_receipt.json'])
    require(index['schema'] == 'MASTER_PUBLIC_CONDA_ORIGINALS_LOCAL_ASSET_INDEX_V1'
            and index['state'] == build['state'] == 'PASS_LOCAL_ALL339_ORIGINALS_AND_ALL_SHARD_MEMBERS_CRC_SHA_VERIFIED'
            and index['actual_process_exit_code'] == 0 and index['source_sha256'] == CONTINUE_SHA
            and index['base_source_sha256'] == BASE_SHA and index['source_review_sha256'] == REVIEW_SHA
            and index['manifest_pins'] == MANIFESTS and set(index['controls']) == set(CONTROLS), 'Final exact index differs')
    for name, pin in index['controls'].items():
        require(pin['remote_path'] == PREFIX + name and pin['sha256'] == CONTROLS[name]
                and pin['bytes'] == len(controls[name]), 'Actual remote control/index size/hash/path join differs')
    require(index['installed_runtime_complete'] is False and index['full_corresponding_source_coverage_audited'] is False
            and index['original_partial'] == 'PRESERVED_UNCHANGED_AND_NOT_ADOPTED', 'Recovery limitation removed')
    require(build['schema'] == 'MASTER_PUBLIC_CONDA_RESOURCE_STOP_CONTINUATION_BUILD_V1'
            and build['source_sha256'] == CONTINUE_SHA and build['base_source_sha256'] == BASE_SHA
            and build['recovery_plan_sha256'] == PLAN_SHA and build['resources_sha256'] == CONTROLS['resources.jsonl']
            and build['original_failure_sha256'] == CONTROLS['original_resource_stop_receipt.json']
            and acquisition['state'] == 'PASS_ALL339_ORIGINAL_SHA_SIZE_VERIFIED_95_REOPENED_244_FRESH_DOWNLOADS'
            and acquisition['downloaded_packages_sha256'] == CONTROLS['downloaded_packages.jsonl'], 'Executed continuation bindings differ')
    for receipt in (build, acquisition):
        require(receipt['verified_packages'] == 339 and receipt['verified_package_bytes'] == 660114049
                and receipt['original_records'] == 397 and receipt['reused_packages'] == 95
                and receipt['fresh_downloaded_packages'] == 244 and receipt['streaming_readers'] == 1
                and receipt['per_buffer_resource_check'] is True and receipt['automatic_admission_wait'] is False
                and receipt['automatic_retries'] == receipt['http_range_requests'] == receipt['installations']
                == receipt['package_extractions'] == receipt['package_executions'] == receipt['scientific_jobs']
                == receipt['source_deletions'] == receipt['wsl_starts'] == receipt['g_writes'] == 0,
                'Executed pass scope/accounting differs')
        require(len(receipt['admission_probes']) == 2 and receipt['admission_probe_separation_seconds'] >= 15
                and all(p['physical_available_bytes'] >= 5 * 1024**3 // 2
                        and p['commit_headroom_bytes'] >= 7 * 1024**3 // 2
                        and p['c_disk_free_bytes'] >= 10 * 1024**3 for p in receipt['admission_probes']), 'Two-probe admission evidence differs')
    require(failure['state'] == 'FAILED_PRESERVED_PARTIALS_NO_AUTOMATIC_RETRY' and failure['verified_packages'] == 95
            and failure['verified_package_bytes'] == plan['completed_bytes'] == 237225880
            and plan['completed_count'] == len(plan['completed']) == 95 and plan['failure_sha256'] == CONTROLS['original_resource_stop_receipt.json']
            and plan['original_partial']['bytes'] == 1547473 and plan['http_range_requests'] == plan['automatic_retries'] == 0,
            'Preserved initial resource stop/partial evidence differs')
    expected = expected_packages({n: controls[n] for n in MANIFESTS}, json.loads(controls['package_index.json']))
    ledger = [json.loads(line) for line in controls['downloaded_packages.jsonl'].splitlines()]
    require(len(ledger) == 339 and len({r['sha256'] for r in ledger}) == 339
            and collections.Counter(r['state'] for r in ledger) == {
                'PASS_FRESH_ORIGINAL_SOURCE_AND_NEW_COPY_SHA': 95, 'PASS_EXACT_ORIGINAL_PACKAGE': 244}, 'Exact acquisition ledger differs')
    by_sha = {p['sha256']: p for p in expected.values()}
    for row in ledger:
        require(row['sha256'] in by_sha and row['bytes'] == by_sha[row['sha256']]['bytes']
                and row['url'] == by_sha[row['sha256']]['url'] and row['automatic_retries'] == 0, 'Actual ledger/original package join differs')
    original95 = {row['sha256']: row for row in plan['completed']}
    copied95 = {row['sha256']: row for row in ledger if row['state'] == 'PASS_FRESH_ORIGINAL_SOURCE_AND_NEW_COPY_SHA'}
    require(len(original95) == 95 and set(copied95) == set(original95), 'Exact original95 copied-source coverage differs')
    for key, row in copied95.items():
        require(row['source_identity'] == original95[key]['original_identity']
                and row['source_path'] == original95[key]['path'] and row['bytes'] == original95[key]['bytes'],
                'Original95 source birth/path/size evidence differs')
    minima = {}; resource_count = 0
    for line in controls['resources.jsonl'].splitlines():
        resource = json.loads(line); resource_count += 1
        require(resource['physical_available_bytes'] >= RESERVE and resource['commit_headroom_bytes'] >= RESERVE
                and resource['c_disk_free_bytes'] >= 10 * 1024**3
                and resource['own_priority_class'] == 'BELOW_NORMAL_PRIORITY_CLASS', 'Executed resource reserve evidence differs')
        for key in ('physical_available_bytes', 'commit_headroom_bytes', 'c_disk_free_bytes'):
            minima[key] = min(resource[key], minima.get(key, resource[key]))
    require(resource_count == index['resource_samples'] and resource_count > 0
            and minima['physical_available_bytes'] == index['minimum_physical_available_bytes']
            and minima['commit_headroom_bytes'] == index['minimum_commit_headroom_bytes']
            and minima['c_disk_free_bytes'] == index['minimum_C_disk_free_bytes'], 'Executed resource/index minima differ')
    release = selected = None
    if not args.local_inspect:
        release, selected = S.begin(A, args, ASSETS, SIDECARS, out, result)
    require(len(build['shards']) == len(index['archive_shards']) == 2, 'Exact two-shard accounting differs')
    packages = {}; all_members = []; sums = 0
    embedded = {name: controls[name] for name in ('ATTRIBUTION_AND_RESTORE.txt', 'acquisition_receipt.json',
        *MANIFESTS, 'downloaded_packages.jsonl', 'original_download_errors.jsonl', 'original_resource_stop_receipt.json',
        'package_index.json', 'recovery_plan.json')}
    embedded.update({name: raw['scripts/master_run/' + name] for name in ('acquire_public_conda_packages01.py', 'continue_public_conda_packages01.py')})
    for number, (asset, side, shard, final_shard) in enumerate(zip(ASSETS, SIDECARS, build['shards'], index['archive_shards'])):
        require(all(shard[k] == final_shard[k] == asset[k] for k in ('name', 'bytes', 'sha256'))
                and shard['sidecar_bytes'] == final_shard['sidecar_bytes'] == side['bytes']
                and shard['sidecar_sha256'] == final_shard['sidecar_sha256'] == side['sha256']
                and shard['sidecar_line_ending'] == final_shard['sidecar_line_ending'] == 'LF', 'Shard/sidecar/index join differs')
        if args.local_inspect:
            expected_side = (asset['sha256'] + '  ' + asset['name'] + '\n').encode('ascii')
            actual_side = (LOCAL / side['name']).read_bytes()
            require(actual_side == expected_side and len(actual_side) == side['bytes']
                    and A.sha(actual_side) == side['sha256'], 'Actual original local LF sidecar bytes differ')
        observed = verify_zip((LOCAL if args.local_inspect else out) / asset['name'], asset, A.member_table(shard['members']))
        expected_controls = {'control/' + n for n in embedded} | {'SHA256SUMS.txt'}
        package_rows = {n: r for n, r in observed.items() if n.startswith('packages/')}
        require(set(observed) == set(package_rows) | expected_controls
                and len(package_rows) == shard['package_files'] == (204, 135)[number]
                and len(observed) == final_shard['member_count'] == (216, 147)[number]
                and len(observed) - 1 == final_shard['SUMS_entries'], 'Exact package/control membership differs')
        for name, data in embedded.items():
            require(observed['control/' + name]['bytes'] == len(data)
                    and observed['control/' + name]['sha256'] == A.sha(data), 'Embedded original control differs: ' + name)
        require(not set(packages) & set(package_rows), 'Original package duplicated across shards')
        packages.update(package_rows); all_members.extend(observed.values()); sums += len(observed) - 1
        guard()
    check_package_coverage(packages, expected)
    require(len(all_members) == 363 and sums == 361 and sum(r['bytes'] for r in packages.values()) == 660114049,
            'Full339 package/all363 member/361 SUMS accounting differs')
    if not args.local_inspect:
        A.end_release(args, release, selected, result)
    result.update(state='PASS_LOCAL_CONDA339_ORIGINALS_REMOTE_NOT_RUN' if args.local_inspect else
                  'PASS_FRESH_REMOTE_CONDA339_ORIGINALS_397_ROLES_363_MEMBERS',
                  original_records=397, original_packages=339, original_package_bytes=660114049,
                  zip_members=363, internal_sum_entries=361, fresh_copied_originals=95, fresh_zero_offset_downloads=244,
                  preserved_initial_partial_bytes=1547473, members=all_members, resource_minimum_bytes=RESOURCE_MIN,
                  installed_runtime_complete=False, full_corresponding_source_coverage_audited=False,
                  package_extractions=0, package_installations=0, payload_executions=0,
                  live_original_package_rehash=False, original_partial_current_rehash=False)


def main():
    global DEADLINE, RESOURCE
    require(WORK == EXACT_WORK and os.name == 'nt', 'Exact current C Windows readback source required')
    args = A.cli(__doc__)
    DEADLINE = time.monotonic() + 1800
    RESOURCE = ResourceReader(); guard()
    original_run = A.run
    def bounded_run(argv, timeout=90):
        guard(); remaining = DEADLINE - time.monotonic()
        return original_run(argv, timeout=min(timeout, remaining))
    A.run = bounded_run; A.digest = file_sha
    A.execute_readback(args, 'public_conda_packages01', verify)


if __name__ == '__main__':
    main()
