"""Freeze exact public C cleanup execution history; default no build/no deletion.

Retained-native-read capture pattern adapted from this project's independently
reviewed build_old_scientific_emptydirs_archive.py SHA00d144480ad83967b3f6dba270fbbfca5d5cad48fea33c6b17974d91f1ab97fe.
No old-C/G payload traversal, scientific execution, network or cleanup API.
"""
from pathlib import Path, PurePosixPath
from ctypes import wintypes as W
import argparse
import ctypes
import datetime
import hashlib
import json
import msvcrt
import os
import re
import stat
import threading
import time
import zipfile

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
OUT = WORK / 'master_directory_prune_execution01'
CHUNK = 256 * 1024
MIN_HEADROOM = 1536 * 1024**2
JOURNAL = 'master_directory_prune01_execution.jsonl'
JOURNAL_SHA = '5ff92323b29af9a6620a251825ea6531e95bbf14ef2ff6c3d36279beb891f4a5'
POST_NAME = 'directory_prune_postverify_20261009T213844Z_e301284e/receipt.json'
POST_SHA = '7820c5048722f517c291f7eab74ea7199197c1ed354b90f3bdfe4df5a35889dd'
REVIEW_NAME = 'directory_prune_execution_archive_builder_independent_review.json'
DECLARATIONS = {
    'directory_handle_pruner_preparation_completion_02.json': 'ee0a5516641e21d2c16e60c4acdd11f60c2569a0e42308c8086a00a9cccd211a',
    'directory_handle_postverify_preparation_02.json': '747a792f0a37b425fb9af017dd8dfbec5e9fdee2dfeade432f0dd27dc29afe23',
}
FIXED = {
    'master_old_scientific_emptydirs_proposed_02.json': 'be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5',
    JOURNAL: JOURNAL_SHA,
    'master_directory_prune_root_authority01.json': '0afeb4c2a06b4920765466474f354ed0638a228c450eb17a1c1acc9ee7bfbe63',
    'master_directory_prune_root_review01.json': '9203c29e478620a430e75f121508eb87dc2eeb90f55f670bb9312b9ba070f50a',
    'master_directory_authority01_remote_readback.json': '1e58f75d5c4183f7fafdce237be3c07775d023c5cc092c8b09de9dc471f6b7e3',
    'master_recovery_verified04_remote_readback.json': '393abb637ce96ced1155c66001184004dfcc09dd578ed083d19769366b6279f6',
    'master_recovery_receipts05/directory_execution_checkpoint.json': 'b287cd8a1d18e206c212fe65709b569d10027eacfefc9000871631b99a9a5232',
    'directory_handle_postverify_preparation.json': '9aee97a33bc9aaecf6dc53846105d6b7044e87d5d3d0079dc31510d17534dbc4',
    'directory_handle_postverify_METHODS.md': '3a03f5449f38c28b964987f5321b9785656a3da8dbc37be8aad093971440c648',
    'directory_handle_postverifier_independent_source_review.json': '5a537805072cd07d1f23e7d681309ba4b70a2607dbe65cc4747e0d51929437c6',
    'master_directory_provider_correction08_remote_readback.json': '6e25f14055234f4f7fceb72b2139b5ac84d9980bad71e2d4cceceb2dee819f0f',
    'test_build_directory_prune_execution_archive.py': 'de061b5201f061abd8b55a689199eb365dd54a7cee723867c043b64d40402973',
    'directory_prune_execution_archive_METHODS.md': '633afb31bd6a36c8aaddab32d98cd0a068a4648a940305bac2c5027bd3f7a56c',
    'build_directory_prune_execution_archive_draft150e.py': '150e6c4f46f2f13325cb28f163bfbfa82291c4fb65cd0e12eabf9495bc74f421',
    'test_build_directory_prune_execution_archive_draft2fe5.py': '2fe5ec14bc870a1b8b163a94a387802fc2536d68e157976f32ae441d4b65a124',
    'directory_prune_execution_archive_METHODS_draft_e5e6.md': 'e5e6f927997a16d58ae100ad97b7e7623f76925a8939e25d59bf8b2d65e5555a',
    'directory_prune_postverify_20261009T213844Z_e301284e/started.json': '42d79f6eef296cf14bc2a9d7586cff459578301bf37035fa9d0fd98206112565',
}
CORRECTION_NAMES = {
    'verify_directory_handle_prune.py', 'test_verify_directory_handle_prune.py',
    'directory_handle_postverify_METHODS_02.md', 'directory_handle_postverifier_provider_corrected_independent_review.json',
    'diagnose_directory_postverify_provider.py', 'directory_postverify_provider_diagnostic01.json',
    'verify_directory_handle_prune_attempt01.py', 'test_verify_directory_handle_prune_attempt01.py',
    'directory_prune_postverify_20261009T212934Z_35de2767/receipt.json',
    'directory_prune_postverify_20261009T212934Z_35de2767/started.json',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


def signature(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_nlink)


def canonical(name):
    path = PurePosixPath(name)
    require(path.as_posix() == name and not path.is_absolute() and '\\' not in name and ':' not in name
            and all(part not in ('', '.', '..') and not part.endswith((' ', '.')) for part in name.split('/')),
            'Noncanonical explicit member source')
    return name


class MemoryStatus(ctypes.Structure):
    _fields_ = [('length', W.DWORD), ('load', W.DWORD)] + [(name, ctypes.c_ulonglong) for name in
        ('physical_total', 'physical_available', 'pagefile_total', 'pagefile_available', 'virtual_total', 'virtual_available', 'extended')]


class Budget:
    def __init__(self):
        self.start = time.monotonic()
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        self.k.GetCurrentProcess.restype = W.HANDLE
        self.k.SetPriorityClass.argtypes = [W.HANDLE, W.DWORD]
        self.k.GetPriorityClass.argtypes = [W.HANDLE]
        self.k.GetPriorityClass.restype = W.DWORD
        self.k.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MemoryStatus)]
        require(self.k.SetPriorityClass(self.k.GetCurrentProcess(), 0x4000)
                and self.k.GetPriorityClass(self.k.GetCurrentProcess()) == 0x4000, 'Own BelowNormal priority required')
        self.initial = self.check()

    def check(self):
        value = MemoryStatus()
        value.length = ctypes.sizeof(value)
        require(time.monotonic() - self.start < 900 and self.k.GlobalMemoryStatusEx(ctypes.byref(value)), 'Build deadline/resource query failed')
        require(value.physical_available >= MIN_HEADROOM and value.pagefile_available >= MIN_HEADROOM,
                'Archive build deferred below1536MiB physical/commit headroom')
        return {'physical_available_bytes': value.physical_available, 'commit_available_bytes': value.pagefile_available,
                'own_priority_class': self.k.GetPriorityClass(self.k.GetCurrentProcess())}


def stream_sha(stream, budget):
    result = hashlib.sha256()
    for chunk in iter(lambda: stream.read(CHUNK), b''):
        budget.check()
        result.update(chunk)
    return result.hexdigest()


class Capture:
    def __init__(self, name, expected, budget):
        self.name, self.path = canonical(name), WORK / name
        self.budget = budget
        require(self.path.resolve() == self.path and WORK in self.path.parents
                and not any(parent.is_symlink() for parent in (self.path, *self.path.parents)), 'Outside/linked explicit C-work source')
        first = self.path.lstat()
        limit = 32 * 1024**2 if name == JOURNAL else 16 * 1024**2
        require(stat.S_ISREG(first.st_mode) and first.st_nlink == 1 and not first.st_file_attributes & 0x400
                and first.st_size < limit, 'Unexpected source type/link/size')
        k = ctypes.WinDLL('kernel32', use_last_error=True)
        k.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
        k.CreateFileW.restype = W.HANDLE
        k.CloseHandle.argtypes = [W.HANDLE]
        handle = k.CreateFileW(str(self.path), 0x80000000, 1, None, 3, 0x00200000, None)
        require(handle != ctypes.c_void_p(-1).value, 'Native retained C source read/deny-write-delete failed')
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException:
            k.CloseHandle(handle)
            raise
        self.stream = os.fdopen(fd, 'rb')
        try:
            self.original = signature(first)
            self.check()
            actual = stream_sha(self.stream, budget)
            require(actual == expected, 'Explicit source SHA changed: ' + name)
            self.stream.seek(0)
            self.record = {'original_path': str(self.path), 'source_relative_path': name,
                           'member': 'evidence/' + name, 'bytes': first.st_size, 'sha256': actual,
                           'device': str(first.st_dev), 'file_id': str(first.st_ino),
                           'mtime_ns': str(first.st_mtime_ns), 'birthtime_ns': str(first.st_birthtime_ns),
                           'links': first.st_nlink, 'attributes': first.st_file_attributes,
                           'retained_access': 'READ_DENY_WRITE_DELETE'}
        except BaseException:
            self.stream.close()
            raise

    def check(self):
        self.budget.check()
        current = self.path.lstat()
        require(signature(current) == self.original == signature(os.fstat(self.stream.fileno()))
                and stat.S_ISREG(current.st_mode) and not current.st_file_attributes & 0x400, 'Retained C source identity drift')

    def json(self):
        require(self.path.stat().st_size < 16 * 1024**2, 'Bounded explicit JSON control required')
        self.stream.seek(0)
        value = json.load(self.stream)
        self.stream.seek(0)
        self.check()
        return value

    def close(self):
        self.stream.close()


def zip_info(name):
    info = zipfile.ZipInfo(name, (2026, 10, 9, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info._compresslevel = 6
    return info


def build(args):
    require(os.name == 'nt' and Path(__file__).resolve().parent == WORK and not OUT.exists(), 'Exact fresh C build namespace required')
    require(args.postverify and args.postverify.parent.parent == WORK and args.postverify.name == 'receipt.json'
            and re.fullmatch(r'directory_prune_postverify_\d{8}T\d{6}Z_[0-9a-f]{8}', args.postverify.parent.name)
            and args.postverify_exit_code == 0, 'Root actual exit0 post-verification receipt required')
    require(args.postverify == WORK / POST_NAME and args.postverify_sha256 == POST_SHA, 'Exact accepted root postcheck required')
    require(all(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value)
                for value in (args.source_sha256, args.postverify_sha256, args.review_sha256)), 'Explicit source/postcheck/review SHA required')
    budget, captures = Budget(), {}
    timer = threading.Timer(900, lambda: os._exit(124))
    timer.daemon = True
    timer.start()
    def add(name, pin):
        if name in captures:
            require(captures[name].record['sha256'] == pin, 'Conflicting duplicate source pin')
        else:
            captures[name] = Capture(name, pin, budget)
        return captures[name]
    try:
        add(Path(__file__).name, args.source_sha256)
        review = add(REVIEW_NAME, args.review_sha256).json()
        require(review['state'] == 'PASS_SOURCE_ONLY' and review['builder_sha256'] == args.source_sha256,
                'Separate actual source-only peer review does not bind this builder')
        declaration = add(next(iter(DECLARATIONS)), next(iter(DECLARATIONS.values()))).json()
        require(len(declaration['public_control_mapping']) == 18 and declaration['production_execution'] == 'NOT_RUN', 'Original prep control shape differs')
        for row in declaration['public_control_mapping']:
            name = canonical(row['relative_control_name'])
            require(str(WORK / name) == row['local_path'], 'Original prep exact source root differs')
            captured = add(name, row['sha256'])
            require(captured.record['bytes'] == row['bytes'], 'Original prep size differs')
        correction_name = 'directory_handle_postverify_preparation_02.json'
        correction = add(correction_name, DECLARATIONS[correction_name]).json()
        require(set(correction['source_pins']) == CORRECTION_NAMES and correction['focused_tests']['tests'] == 25
                and correction['focused_tests']['exit_code'] == 0 and correction['production_prune_rerun'] == 'NOT_AUTHORIZED_NOT_RUN',
                'Exact corrected prep source set differs')
        for name, pin in correction['source_pins'].items():
            add(name, pin)
        for name, pin in FIXED.items():
            add(name, pin)
        post_name = args.postverify.relative_to(WORK).as_posix()
        post = add(post_name, args.postverify_sha256).json()
        require(post['schema'] == 'MASTER_DIRECTORY_HANDLE_PRUNE_INDEPENDENT_POST_VERIFY_V1'
                and post['state'] == 'PASS_EXACT5542_REMOVED_AND_PROTECTED_IDENTITIES_UNCHANGED'
                and post['complete_prune_verified'] is True and post['all5542_accounted'] is True
                and post['documented_removed_directories'] == 5542 and post['retained_planned_directories'] == 0
                and post['unproven_absences'] == [] and post['held_directories_preserved'] == 6
                and post['journal_sha256'] == JOURNAL_SHA and post['journal_records'] == 16628
                and post['verifier_sha256'] == correction['source_pins']['verify_directory_handle_prune.py']
                and len(post['protected_files']) == 12 and len(post['six_dirty_g_files_unchanged']) == 6
                and post['workflow_lock_metadata_only'] is True and post['lock_contents_read'] is False
                and post['lock_acquired'] is False and post['g_provider_metadata_diagnostic_sha256'] == correction['source_pins']['directory_postverify_provider_diagnostic01.json'],
                'Actual independent production acceptance missing or mismatched')
        plan = captures['master_old_scientific_emptydirs_proposed_02.json'].json()
        expected_paths = {row['path'] for row in plan['directories']}
        require(len(expected_paths) == len(post['directory_states']) == 5542
                and {row['path'] for row in post['directory_states']} == expected_paths
                and all(row['state'] == 'DOCUMENTED_REMOVED_AND_CURRENTLY_ABSENT' and row['presence_evidence']['present'] is False
                        for row in post['directory_states']), 'Exact5542 actual source-to-postcheck join differs')
        checkpoint = captures['master_recovery_receipts05/directory_execution_checkpoint.json'].json()
        require(checkpoint['actual_tool_reported_exit_code'] == 0 and checkpoint['journal']['sha256'] == JOURNAL_SHA
                and checkpoint['journal']['record_counts'] == {'BEGIN': 1, 'BEFORE_DISPOSITION': 5542,
                    'DISPOSITION_MARKED_ON_EXACT_DIRECTORY_HANDLE': 5542, 'AFTER_REMOVED': 5542, 'COMPLETE': 1},
                'Retained original root execution exit/journal evidence differs')
        require(sum(item.record['bytes'] for item in captures.values()) < 64 * 1024**2, 'Total explicit capture set exceeds64MiB')
        summary = {'schema': 'MASTER_DIRECTORY_PRUNE_EXECUTION_RECOVERY_SUMMARY_V1',
                   'scope': 'EXACT_PUBLISHED_SEVEN_OLD_C_CACHE_SCOPES_ONLY',
                   'pruner_exit_code': 0, 'independent_postverify_exit_code': args.postverify_exit_code,
                   'journal_sha256': JOURNAL_SHA, 'journal_records': 16628, 'directories_removed_verified': 5542,
                   'held_directories': 6, 'protected_files': 12, 'dirty_g_files': 6,
                   'first_pruner_fixture_failure_preserved': True, 'first_postverify_provider_failure_preserved': True,
                   'g_single_link_exclusion': post['g_provider_single_link_exclusion'],
                   'original_execution_checkpoint_state_preserved': checkpoint['state'],
                   'postverify_receipt': post_name, 'postverify_sha256': args.postverify_sha256,
                   'new_deletion_or_host_wipe_authority': False, 'scientific_acceptance_created': False,
                   'files_deleted_by_builder': 0, 'directories_deleted_by_builder': 0,
                   'remote_publication': 'NOT_RUN', 'remote_readback': 'NOT_RUN'}
        originals = {item.record['member']: item.record for item in captures.values()}
        index = {'schema': 'MASTER_DIRECTORY_PRUNE_EXECUTION_ARCHIVE_INDEX_V1', 'originals': originals, 'summary': summary,
                 'scope': 'EXACT_PUBLIC_C_WORK_EXECUTION_METADATA_AND_PROJECT_SOURCES_ONLY',
                 'raw_project_payloads_or_private_controls': 'NOT_INCLUDED', 'source_byte_redaction': False}
        notice = ('Project-specific cleanup sources and immutable public evidence are copied unchanged.\n'
                  'The retained-native-read capture pattern comes from this project\'s independently reviewed\n'
                  'build_old_scientific_emptydirs_archive.py; its source/history remain in the canonical repository.\n'
                  'No third-party executable/library, MacSyFinder serializer fragment, license-less vendor source,\n'
                  'private run control contents, raw prompts/events/usage/credentials or scientific source payload is included.\n'
                  'All original notices in selected project source bytes remain unchanged; no new license is asserted.\n'
                  'Historical failed/pending states stay original. Actual post-verification binds the later accepted state.\n'
                  'G provider single-link exclusion remains NOT_ESTABLISHED; exact protected hashes/identities were verified.\n'
                  'This archive is local recovery preparation, with no new cleanup, publication or host-wipe authority.\n').encode('utf-8')
        generated = {'INDEX.json': encoded(index), 'EXECUTION_SUMMARY.json': encoded(summary), 'ATTRIBUTION_AND_LIMITS.md': notice}
        members = {name: {'bytes': row['bytes'], 'sha256': row['sha256']} for name, row in originals.items()}
        members.update({name: {'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()} for name, value in generated.items()})
        sums = ''.join(row['sha256'] + '  ' + name + '\n' for name, row in sorted(members.items())).encode('ascii')
        generated['SHA256SUMS.txt'] = sums
        members['SHA256SUMS.txt'] = {'bytes': len(sums), 'sha256': hashlib.sha256(sums).hexdigest()}
        OUT.mkdir()
        (OUT / 'started.json').write_bytes(encoded({'state': 'IN_PROGRESS_C_ONLY_ARCHIVE_BUILD_NO_DELETE', 'builder_sha256': args.source_sha256}))
        archive = OUT / 'master_directory_prune_execution01.zip'
        by_member = {item.record['member']: item for item in captures.values()}
        with zipfile.ZipFile(archive, 'x') as bundle:
            for name in sorted(members):
                budget.check()
                if name in generated:
                    bundle.writestr(zip_info(name), generated[name])
                    continue
                item = by_member[name]
                item.check()
                item.stream.seek(0)
                copied = hashlib.sha256()
                with bundle.open(zip_info(name), 'w') as destination:
                    for chunk in iter(lambda: item.stream.read(CHUNK), b''):
                        budget.check()
                        copied.update(chunk)
                        destination.write(chunk)
                item.check()
                require(copied.hexdigest() == item.record['sha256'], 'Captured source bytes changed during ZIP copy')
        require(archive.stat().st_size < 500 * 1024**2, 'Release asset exceeds500MiB')
        verified = []
        with zipfile.ZipFile(archive) as bundle:
            require(bundle.namelist() == sorted(members) and len(set(bundle.namelist())) == len(members) and not bundle.comment,
                    'Exact archive order/set/comment mismatch')
            for info in bundle.infolist():
                require(not info.extra and not info.comment and not info.flag_bits & 1, 'Unexpected archive entry metadata')
                with bundle.open(info) as stream:
                    actual = stream_sha(stream, budget)
                require(actual == members[info.filename]['sha256'] and info.file_size == members[info.filename]['bytes'], 'Actual EOF CRC/SHA/size mismatch')
                verified.append({'member': info.filename, **members[info.filename], 'crc32': f'{info.CRC:08x}', 'crc_verified': True})
        for item in captures.values():
            item.check()
            item.stream.seek(0)
            require(stream_sha(item.stream, budget) == item.record['sha256'], 'Final retained original SHA changed')
        with archive.open('rb') as stream:
            archive_sha = stream_sha(stream, budget)
        receipt = {'schema': 'MASTER_DIRECTORY_PRUNE_EXECUTION_ARCHIVE_BUILD_V1',
                   'state': 'PASS_LOCAL_EXECUTION_RECOVERY_ARCHIVE_ALL_CRC_SHA_NO_NEW_DELETE',
                   'archive': archive.name, 'bytes': archive.stat().st_size, 'sha256': archive_sha,
                   'builder_sha256': args.source_sha256, 'original_count': len(captures), 'member_count': len(members),
                   'originals': originals, 'members': verified, 'summary': summary,
                   'stream_chunk_bytes': CHUNK, 'parallel_readers': 1, 'deadline_seconds': 900,
                   'resource_before': budget.initial, 'resource_after': budget.check(),
                   'minimum_physical_and_commit_headroom_bytes': MIN_HEADROOM,
                   'new_source_deletions': 0, 'g_writes': 0, 'wsl_starts': 0, 'native_scientific_launches': 0}
        require(len(encoded(receipt)) < 1024**2, 'Compact build receipt exceeds1MiB')
        controls = {'build_receipt.json': encoded(receipt), 'index.json': generated['INDEX.json'],
                    'execution_summary.json': generated['EXECUTION_SUMMARY.json'], 'SHA256SUMS.txt': sums,
                    archive.name + '.sha256': (archive_sha + '  ' + archive.name + '\n').encode('ascii')}
        for name, value in controls.items():
            (OUT / name).write_bytes(value)
        completion = {'schema': 'MASTER_DIRECTORY_PRUNE_EXECUTION_ARCHIVE_COMPLETION_V1',
                      'state': receipt['state'], 'archive': {'path': str(archive), 'bytes': archive.stat().st_size, 'sha256': archive_sha},
                      'source': {'path': str(Path(__file__)), 'sha256': args.source_sha256},
                      'original_count': len(captures), 'member_count': len(members), 'summary': summary,
                      'compact_public_controls': [{'local_path': str(OUT / name), 'suggested_public_name': name,
                                                  'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()} for name, value in controls.items()]}
        (OUT / 'completion.json').write_bytes(encoded(completion))
        print(json.dumps({'state': receipt['state'], 'archive': str(archive), 'bytes': archive.stat().st_size,
                          'sha256': archive_sha, 'original_count': len(captures), 'member_count': len(members)}))
    finally:
        timer.cancel()
        for item in reversed(list(captures.values())):
            item.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--source-sha256')
    parser.add_argument('--postverify', type=Path)
    parser.add_argument('--postverify-sha256')
    parser.add_argument('--postverify-exit-code', type=int)
    parser.add_argument('--review-sha256')
    args = parser.parse_args()
    if not args.build:
        print(json.dumps({'state': 'PREPARED_NO_BUILD_NO_DELETE', 'root_actual_postverify_exit0_required': True}))
        return 0
    return build(args)


if __name__ == '__main__':
    main()
