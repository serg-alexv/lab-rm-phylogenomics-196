"""Freeze fixed public C metadata only, serial 256-KiB I/O; never prune."""
from pathlib import Path
from ctypes import wintypes as W
import argparse
import ctypes
import hashlib
import json
import msvcrt
import os
import stat
import zipfile

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
OUT = WORK / 'master_old_scientific_emptydirs01'
CHUNK = 256 * 1024
FIXED = (
    ('master_old_scientific_emptydirs_proposed_02.json', 'be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5'),
    ('prepare_old_scientific_emptydirs.py', '7287809f47f912eddb21ba9f05d927872ef710d45ac6857837ae6689c320b21f'),
    ('prepare_old_scientific_emptydirs_attempt01.py', '5e5f88302b175e68cdcfbd1cb3913200296667b56448f8c0726b3b5e89398b69'),
    ('test_old_scientific_emptydirs.py', '9318add3dc29fa316c1d5a507c01bcef6f88881fc124d344e2e85009f2cf96af'),
    ('master_old_scientific_emptydirs_tests.json', '6eadaf218f571264cfa8acaa6bcfebcb36b46d3cdfabe05b98df1d5f1d4b7ce1'),
    ('master_old_scientific_emptydirs_attempt01_failure.json', '11c408830bcf2c2d5db54e9a2769c811629fb3f8c16ef9d8f106d4f56bbe2a37'),
    ('master_old_scientific_emptydirs_attempt01_diagnostic.json', 'a0a872ca6d293f87610ef5922afd1b2843dd480bc0bf845ae5cdf94c2fa8684e'),
    ('master_old_scientific_emptydirs_attempt01_traceback.txt', '93a2479c662eda44ca638c119e639fc88b3be8213af6811050cb59cb3272f5e9'),
    ('master_old_scientific_emptydirs_REVIEW.md', '20d8f47a5693b1ecaa36b7e4e24775b4407b303e4d3fd4e56eb496702f9ce5b1'),
    ('master_old_scientific_emptydirs_independent_review.json', '3891047eb81f8cf2d61d6d9c4cefec4492af94ecaeddec3779b053cc34809c82'),
    ('master_batch03_postverify_20261009T200023Z_f95312bd/receipt.json', '84cb29ebcc04b444ea90ca0e10d5f7e6832d09f14f8f8285f1241b4cf3e71868'),
    ('master_history02_postverify_20261009T201921Z_f90337c5/receipt.json', 'a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082'),
    ('audit_old_checkout_git_metadata.py', '54aca001150a97f6219f08ce148434682e45d94dcb93dd25509494fc6370b5cc'),
    ('old_checkout_git_preservation_metadata.json', '2d7698c6a9b26a39c2e2bd511ff39b8816b9e142b93d8c16457573b507d8e8b0'),
    ('old_checkout_git_preservation_summary.json', '16036be7f777536b12d7f0d512062bfd7c2a00559f557b5828ccd5fb7c09438f'),
)
COUNTS_HOLDS = {
    'schema': 'MASTER_OLD_SCIENTIFIC_EMPTY_DIRECTORY_COMPACT_V1',
    'state': 'PREPARED_REVIEWED_NO_DELETE',
    'plan_sha256': FIXED[0][1], 'plan_bytes': 8937244,
    'directory_count': 5542, 'empty_now_count': 3736, 'planned_children_only_count': 1806,
    'derived_ancestor_count': 5548, 'held_count': 6,
    'scope_counts': {'data': 982, '.work/review2': 244, '.work/stage02_validated': 198,
                     '.work/source_locus_inputs_v1': 2514, '.work/stage03_markers_v1': 988,
                     '.work/stage04a_windows_alignments_v1': 308, '.work/stage04_phylogeny_v2': 308},
    'held_relative_paths': ['.work/review2/io_streaming_interrupted/assemblies',
                            '.work/review2/io_streaming_interrupted', '.work/review2/publication_review',
                            '.work/review2/stage05_raw_review', '.work/review2', '.work/stage04_phylogeny_v2'],
    'unknown_subtrees_preserved_without_traversal': [
        '.work/review2/io_streaming_interrupted/assemblies/GCF_000011045.1',
        '.work/review2/publication_review/__pycache__', '.work/review2/__pycache__',
        '.work/stage04_phylogeny_v2/temporary'],
    'fragment_and_all_ancestors_preserved': '.work/review2/stage05_raw_review/installed_rejected_serializer.txt',
    'git_modified_tracked_count': 4, 'git_untracked_status_entries': 191,
    'git_untracked_files': 189, 'git_untracked_collapsed_directories': 2, 'git_indexed_paths': 356,
    'git_durable_remote_coverage': 'UNKNOWN_UNPROVEN_PRESERVE_CHECKOUT_AND_GIT',
    'execution_authorized': False, 'files_deleted': 0, 'directories_deleted': 0,
    'recursive_deletes': 0, 'g_writes': 0, 'wsl_starts': 0, 'scientific_jobs': 0,
    'future_executor': 'NOT_BUILT_NOT_TESTED_REQUIRES_SEPARATE_ROOT_AUTHORITY_AND_EXACT_HANDLE_DIRECTORY_ONLY_FIXTURE',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(stream):
    value = hashlib.sha256()
    for chunk in iter(lambda: stream.read(CHUNK), b''):
        value.update(chunk)
    return value.hexdigest()


def identity(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_nlink)


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


class Capture:
    """Keep source bytes deny-write/delete locked until archive verification ends."""
    def __init__(self, name, pin):
        self.path = WORK / name
        self.name = name
        require(self.path.resolve() == self.path and WORK in self.path.parents
                and not any(p.is_symlink() for p in (self.path, *self.path.parents)), 'Linked/aliased/outside fixed C source')
        initial = self.path.lstat()
        require(stat.S_ISREG(initial.st_mode) and initial.st_nlink == 1
                and not initial.st_file_attributes & 0x400 and initial.st_size < 16 * 1024**2, 'Unexpected source kind/size')
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
        self.kernel.CreateFileW.restype = W.HANDLE
        self.kernel.CloseHandle.argtypes = [W.HANDLE]
        handle = self.kernel.CreateFileW(str(self.path), 0x80000000, 1, None, 3, 0x00200000, None)
        require(handle != ctypes.c_void_p(-1).value, 'Source native read/deny-write-delete open failed')
        try:
            descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException:
            self.kernel.CloseHandle(handle)
            raise
        self.stream = os.fdopen(descriptor, 'rb')
        try:
            self.original_identity = identity(initial)
            require(identity(os.fstat(self.stream.fileno())) == self.original_identity, 'Source identity changed before retained open')
            actual = digest(self.stream)
            require(pin is None or actual == pin, 'Fixed expected source SHA differs')
            self.stream.seek(0)
            self.record = {'original_path': str(self.path), 'bytes': initial.st_size, 'sha256': actual,
                           'device': str(initial.st_dev), 'file_id': str(initial.st_ino),
                           'mtime_ns': str(initial.st_mtime_ns),
                           'birthtime_ns': str(getattr(initial, 'st_birthtime_ns', 'UNAVAILABLE')),
                           'links': initial.st_nlink, 'attributes': initial.st_file_attributes,
                           'retained_access': 'READ_DENY_WRITE_DELETE', 'member': name}
            self.check()
        except BaseException:
            self.stream.close()
            raise

    def check(self):
        current = self.path.lstat()
        require(identity(current) == self.original_identity
                and identity(os.fstat(self.stream.fileno())) == self.original_identity
                and stat.S_ISREG(current.st_mode) and not current.st_file_attributes & 0x400, 'Retained source identity drift')

    def close(self):
        self.stream.close()


def info_for(name):
    info = zipfile.ZipInfo(name, (2026, 10, 9, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info._compresslevel = 6
    return info


def build():
    require(os.name == 'nt' and Path(__file__).resolve().parent == WORK, 'Exact Windows C deployment required')
    require(not OUT.exists(), 'Preserve existing archive directory')
    captures = []
    try:
        for name, pin in (*FIXED, (Path(__file__).name, None)):
            captures.append(Capture(name, pin))
        require(sum(row.record['bytes'] for row in captures) < 32 * 1024**2, 'Bounded metadata set required')
        originals = {row.name: row.record for row in captures}
        index = {'schema': 'MASTER_OLD_SCIENTIFIC_EMPTY_DIRECTORY_METADATA_ARCHIVE_INDEX_V1',
                 'scope': 'FIXED_PUBLIC_C_METADATA_AND_SOURCES_ONLY_NO_PROJECT_PAYLOADS',
                 'originals': originals, 'counts_holds': COUNTS_HOLDS,
                 'retained_snapshot_limit': 'Directory handles closed after scan; future current checks and exact-handle removal fixture mandatory',
                 'scientific_acceptance_created': False, 'execution_authorized': False}
        generated = {'INDEX.json': encoded(index), 'COUNTS_HOLDS.json': encoded(COUNTS_HOLDS)}
        members = {row.name: {'sha256': row.record['sha256'], 'bytes': row.record['bytes']} for row in captures}
        members.update({name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)} for name, data in generated.items()})
        sums = ''.join(row['sha256'] + '  ' + name + '\n' for name, row in sorted(members.items())).encode('ascii')
        generated['SHA256SUMS.txt'] = sums
        members['SHA256SUMS.txt'] = {'sha256': hashlib.sha256(sums).hexdigest(), 'bytes': len(sums)}
        OUT.mkdir()
        archive = OUT / 'master_old_scientific_emptydirs01.zip'
        sources = {row.name: row for row in captures}
        with zipfile.ZipFile(archive, 'x') as bundle:
            for name in sorted(members):
                if name in generated:
                    bundle.writestr(info_for(name), generated[name])
                    continue
                capture = sources[name]
                capture.check()
                capture.stream.seek(0)
                copied = hashlib.sha256()
                with bundle.open(info_for(name), 'w') as destination:
                    for chunk in iter(lambda: capture.stream.read(CHUNK), b''):
                        copied.update(chunk)
                        destination.write(chunk)
                capture.check()
                require(copied.hexdigest() == capture.record['sha256'], 'Original bytes changed during ZIP capture')
        require(archive.stat().st_size < 500 * 1024**2, 'Release asset exceeds 500 MiB')
        verified = []
        with zipfile.ZipFile(archive) as bundle:
            require(bundle.namelist() == sorted(members) and len(bundle.namelist()) == len(set(bundle.namelist()))
                    and not bundle.comment, 'Archive exact member order/set/comment differs')
            for info in bundle.infolist():
                require(not info.extra and not info.comment and not info.flag_bits & 1, 'Unexpected member metadata')
                with bundle.open(info) as stream:
                    actual = digest(stream)
                expected = members[info.filename]
                require(actual == expected['sha256'] and info.file_size == expected['bytes'], 'Readback CRC/SHA/size mismatch')
                verified.append({'member': info.filename, **expected, 'crc32': f'{info.CRC:08x}', 'crc_verified': True})
        for capture in captures:
            capture.check()
            capture.stream.seek(0)
            require(digest(capture.stream) == capture.record['sha256'], 'Final retained original SHA changed')
        with archive.open('rb') as stream:
            archive_sha = digest(stream)
        receipt = {'schema': 'MASTER_OLD_SCIENTIFIC_EMPTY_DIRECTORY_METADATA_ARCHIVE_BUILD_V1',
                   'state': 'PASS_LOCAL_EXACT_METADATA_ARCHIVE_CRC_SHA_NO_DELETE',
                   'archive': archive.name, 'bytes': archive.stat().st_size, 'sha256': archive_sha,
                   'builder_sha256': originals[Path(__file__).name]['sha256'],
                   'original_count': len(captures), 'member_count': len(members),
                   'members': verified, 'originals': originals, 'counts_holds': COUNTS_HOLDS,
                   'stream_chunk_bytes': CHUNK, 'parallel_readers': 1,
                   'remote_publication': 'NOT_RUN', 'remote_readback': 'NOT_RUN', 'pruning': 'NOT_RUN',
                   'scientific_acceptance_created': False, 'execution_authorized': False}
        require(len(encoded(receipt)) < 1024**2, 'Compact control exceeded 1 MiB')
        (OUT / 'build_receipt.json').write_bytes(encoded(receipt))
        (OUT / 'counts_holds.json').write_bytes(encoded(COUNTS_HOLDS))
        (OUT / 'index.json').write_bytes(generated['INDEX.json'])
        (OUT / 'SHA256SUMS.txt').write_bytes(sums)
        (OUT / (archive.name + '.sha256')).write_text(archive_sha + '  ' + archive.name + '\n', encoding='ascii')
        print(json.dumps({key: receipt[key] for key in ('state', 'archive', 'bytes', 'sha256', 'original_count', 'member_count')}))
    finally:
        for capture in reversed(captures):
            capture.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    if args.build:
        build()
    else:
        print(json.dumps({'state': 'PREPARED_NO_BUILD_NO_DELETE', 'fixed_source_count': len(FIXED) + 1}))
