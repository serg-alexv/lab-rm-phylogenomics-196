"""Archive only exact scoped public historical bytes; no deletion or execution."""
from pathlib import Path, PurePosixPath
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
ROOT = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT = WORK / 'master_old_checkout_changed_history01'
CHUNK = 256 * 1024
CONTROLS = {
    'inspect_old_checkout_changed_history.py': 'fd93629536b432b9eead9f1d1607da2540e37f562367b01d267651dddab66814',
    'finalize_old_checkout_changed_history.py': '1530f44c1d7cbf7d6d15909c806e0c56a75def13ab42809b12a47a5a7ab60239',
    'resolve_old_checkout_history_document.py': '0c88f95e233528c20518c48406099d49509801ab054706b39c1c3dffa39b98d5',
    'inspect_public_history02.py': '671b20fc3f8b89c214d9fc50a3b793275caafce72bac03bee4379468793dcfc0',
    'audit_old_checkout_git_metadata.py': '54aca001150a97f6219f08ce148434682e45d94dcb93dd25509494fc6370b5cc',
    'old_checkout_git_preservation_metadata.json': '2d7698c6a9b26a39c2e2bd511ff39b8816b9e142b93d8c16457573b507d8e8b0',
    'old_checkout_git_preservation_summary.json': '16036be7f777536b12d7f0d512062bfd7c2a00559f557b5828ccd5fb7c09438f',
    'old_checkout_changed_history_inspection01/inspection.json': 'f786c7b849bb98333aba18b4312706a2fbc2dd7447bbd0541ae4d0211c7181df',
    'old_checkout_changed_history_inspection01/selection.json': 'c73343901656721e52291e0b0f82b14efafbf7bd5358dd05b9e3dace288a79db',
    'old_checkout_changed_history_inspection01/decisions.jsonl': '2f5fadd494c6fc61affa77182674e260d7b2a9bb14e11798dfd0389a994e8d19',
    'old_checkout_changed_history_scope01/scope_review.json': 'f3689f2f7fe543eb47e282b3bf6b0abe14839811e52fccf2ab9e2395f83ef71d',
    'old_checkout_changed_history_scope01/public_files.json': '3738dd30ea17273164e30dc26d49a9be05031870fe00d1c38d6b4fb2fe598be7',
    'old_checkout_changed_history_scope01/excluded_files.json': 'ea5c3dd3b9b3c5ae7ad160c4f572e40da4af48f7dba171c0a2c2df80da3e1216',
    'old_checkout_changed_history_scope01/ATTRIBUTION_AND_LIMITS.txt': 'a2d88884134a9e97ef21d9ae527bbd6cb62b85f725e6706662ecb16a34b1c213',
    'old_checkout_changed_history_scope02/scope_review.json': '49599fe21edce64353aad6d37e63127104f3b1d43c7f9c945958677fb94d2983',
    'old_checkout_changed_history_scope02/public_files.json': 'fb80c41a18c9055a5c1c9748ad083e419b61a0919e7813a497f5ca8441aa1796',
    'old_checkout_changed_history_scope02/excluded_files.json': '5f551aadad4f627a9a319044e84ddb358e467efd3308544e7eb0230b90139645',
    'old_checkout_changed_history_scope02/ATTRIBUTION_AND_LIMITS.txt': 'a2d88884134a9e97ef21d9ae527bbd6cb62b85f725e6706662ecb16a34b1c213',
}
PRIVATE = {'status/attempt01_execution_receipt.json', 'status/continuation_execution_receipt.json',
           'status/execution_receipt.json', 'status/parent_execution_update.json',
           'docs/approved196_summaries/approved196_summary_readback.json'}


def require(value, message):
    if not value:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode('utf-8')


def identity(value):
    return (str(value.st_dev), str(value.st_ino), value.st_size, str(value.st_mtime_ns), value.st_nlink)


def digest(stream):
    value = hashlib.sha256()
    for block in iter(lambda: stream.read(CHUNK), b''):
        value.update(block)
    return value.hexdigest()


class Capture:
    def __init__(self, path, member, expected_sha=None, expected_identity=None):
        self.path, self.member = path, member
        require(path.resolve() == path and not any(p.is_symlink() for p in (path, *path.parents)), 'Aliased source held')
        require(WORK in path.parents or ROOT in path.parents, 'Source outside fixed C roots')
        for parent in (path, *path.parents):
            require(not parent.lstat().st_file_attributes & 0x400, 'Reparse source or ancestor held')
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size < 16 * 1024**2,
                'Nonregular/linked/oversize source held')
        self.expected_identity = identity(before)
        require(expected_identity is None or self.expected_identity == expected_identity, 'Scoped original identity drift')
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
        kernel.CreateFileW.restype = W.HANDLE
        kernel.CloseHandle.argtypes = [W.HANDLE]
        handle = kernel.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x00200000, None)
        require(handle != ctypes.c_void_p(-1).value, 'Retained source read open failed')
        try:
            descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException:
            kernel.CloseHandle(handle)
            raise
        self.stream = os.fdopen(descriptor, 'rb')
        try:
            self.check()
            actual = digest(self.stream)
            require(expected_sha is None or actual == expected_sha, 'Scoped original expected SHA drift')
            self.stream.seek(0)
            self.record = {'member': member, 'original_path': str(path), 'bytes': before.st_size, 'sha256': actual,
                           'device': str(before.st_dev), 'file_id': str(before.st_ino), 'mtime_ns': str(before.st_mtime_ns),
                           'birthtime_ns': str(getattr(before, 'st_birthtime_ns', 'UNAVAILABLE')),
                           'links': before.st_nlink, 'attributes': before.st_file_attributes,
                           'retained_access': 'READ_DENY_WRITE_DELETE'}
            self.check()
        except BaseException:
            self.stream.close()
            raise

    def check(self):
        current = self.path.lstat()
        require(identity(current) == self.expected_identity and identity(os.fstat(self.stream.fileno())) == self.expected_identity
                and stat.S_ISREG(current.st_mode) and not current.st_file_attributes & 0x400, 'Original source identity drift')


def info_for(name):
    value = zipfile.ZipInfo(name, (2026, 10, 9, 0, 0, 0))
    value.compress_type = zipfile.ZIP_DEFLATED
    value._compresslevel = 6
    value.create_system = 3
    value.external_attr = 0o100644 << 16
    return value


def build():
    require(os.name == 'nt' and Path(__file__).resolve().parent == WORK and not OUT.exists(), 'Exact new C build namespace required')
    priority_api = ctypes.WinDLL('kernel32', use_last_error=True)
    priority_api.GetCurrentProcess.restype = W.HANDLE
    priority_api.SetPriorityClass.argtypes = [W.HANDLE, W.DWORD]
    priority_api.GetPriorityClass.argtypes = [W.HANDLE]
    priority_api.GetPriorityClass.restype = W.DWORD
    own_handle = priority_api.GetCurrentProcess()
    require(priority_api.SetPriorityClass(own_handle, 0x4000)
            and priority_api.GetPriorityClass(own_handle) == 0x4000, 'Own BelowNormal reader priority required')
    captures = []
    try:
        for relative, pin in (*CONTROLS.items(), (Path(__file__).name, None)):
            captures.append(Capture(WORK / relative, 'control/' + relative, pin))
        scope = json.loads((WORK / 'old_checkout_changed_history_scope02/public_files.json').read_text())['files']
        excluded = json.loads((WORK / 'old_checkout_changed_history_scope02/excluded_files.json').read_text())['files']
        require(len(scope) == len({row['relative_path'].casefold() for row in scope}) == 194
                and sum(row['metadata']['bytes'] for row in scope) == 18622099
                and len(excluded) == 5 and {row['relative_path'] for row in excluded} == PRIVATE
                and sum(row['original_bytes'] for row in excluded) == 4795, 'Exact194public/5private selection differs')
        originals = []
        for row in sorted(scope, key=lambda item: item['relative_path']):
            relative = row['relative_path']
            pure = PurePosixPath(relative)
            require(pure.as_posix() == relative and not pure.is_absolute() and '..' not in pure.parts
                    and pure.parts[0] in {'docs', 'reports', 'scripts'}
                    and not {'.git', '.tools', '.work', '.private_run', '.codex', '__pycache__'}.intersection(part.casefold() for part in pure.parts)
                    and relative not in PRIVATE and row['archive_member'] == 'originals/' + relative
                    and row['decision'] == 'PUBLIC_SCIENTIFIC_HISTORY_ORIGINAL_BYTES_FOR_PRESERVATION_ONLY'
                    and row['expanded_privacy_scan'] == 'FULL_BYTES_NO_MATCH', 'Unsafe/nonpublic original selection')
            expected = row['metadata']
            path = ROOT.joinpath(*pure.parts)
            require(str(path) == row['absolute_path'], 'Exact original literal path differs')
            capture = Capture(path, row['archive_member'], row['sha256'],
                              (expected['device'], expected['file_id'], expected['bytes'], expected['mtime_ns'], expected['link_count']))
            captures.append(capture)
            originals.append(capture.record | {'scientific_kind': row['scientific_kind'],
                                              'historical_state': 'ORIGINAL_UNCHANGED_NO_ACCEPTANCE_OR_CLOSURE_INFERENCE'})
        require(sum(row.record['bytes'] for row in captures) < 128 * 1024**2, 'Bounded128MiB total input contract exceeded')
        generated = {
            'ORIGINAL_MAPPING.json': encoded({'schema': 'MASTER_OLD_CHECKOUT_CHANGED_HISTORY_ORIGINAL_MEMBER_MAPPING_V1',
                                             'files': originals, 'count': 194, 'bytes': 18622099,
                                             'whole_private_exclusions': excluded, 'pruning_authorized': False}),
            'README.txt': (b'Historical LAB R-M scientific preservation only. Exact194publicoriginals/18622099bytes; '
                           b'fivewholeprivatefiles/4795bytes excluded and preserved locally. No redaction. '
                           b'All original source/notices and historical failure, partial, pipeline and synthetic states remain unchanged. '
                           b'Initial privacy-pattern gap and conservative scientific-document filter correction are retained in control/ evidence. '
                           b'No native closure, scientific acceptance, tool readiness, remote durability or deletion authority is created. '
                           b'No .git, .tools, .work, private control payload, raw Codex events, prompts, usage or credentials are selected.\n')}
        members = {row.member: {'sha256': row.record['sha256'], 'bytes': row.record['bytes']} for row in captures}
        members.update({name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)} for name, data in generated.items()})
        sums = ''.join(row['sha256'] + '  ' + name + '\n' for name, row in sorted(members.items())).encode('ascii')
        generated['SHA256SUMS.txt'] = sums
        members['SHA256SUMS.txt'] = {'sha256': hashlib.sha256(sums).hexdigest(), 'bytes': len(sums)}
        OUT.mkdir()
        archive = OUT / 'master_old_checkout_changed_history01.zip'
        sources = {row.member: row for row in captures}
        require(len(sources) == len(captures), 'Duplicate source member')
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
                    for block in iter(lambda: capture.stream.read(CHUNK), b''):
                        copied.update(block)
                        destination.write(block)
                capture.check()
                require(copied.hexdigest() == capture.record['sha256'], 'Original bytes drifted during archive copy')
        require(archive.stat().st_size < 500 * 1024**2, '500MiB release asset contract exceeded')
        verified = []
        with zipfile.ZipFile(archive) as bundle:
            require(bundle.namelist() == sorted(members) and len(bundle.namelist()) == len(set(bundle.namelist()))
                    and not bundle.comment, 'Exact deterministic ZIP set/order/comment differs')
            for info in bundle.infolist():
                require(not info.extra and not info.comment and not info.flag_bits & 1, 'Unexpected ZIP member metadata')
                with bundle.open(info) as source:
                    actual = digest(source)
                require(actual == members[info.filename]['sha256'] and info.file_size == members[info.filename]['bytes'], 'Actual member CRC/SHA/size differs')
                verified.append({'member': info.filename, **members[info.filename], 'crc32': f'{info.CRC:08x}', 'crc_verified': True})
        for capture in captures:
            capture.check()
            capture.stream.seek(0)
            require(digest(capture.stream) == capture.record['sha256'], 'Final original retained SHA drift')
        with archive.open('rb') as source:
            archive_sha = digest(source)
        receipt = {'schema': 'MASTER_OLD_CHECKOUT_CHANGED_HISTORY_LOCAL_ARCHIVE_V1',
                   'state': 'PASS_LOCAL_EXACT194_PUBLIC_HISTORY_CRC_SHA_NO_PURGE',
                   'archive': archive.name, 'bytes': archive.stat().st_size, 'sha256': archive_sha,
                   'builder_sha256': next(row.record['sha256'] for row in captures if row.path == Path(__file__).resolve()),
                   'public_original_files': 194, 'public_original_bytes': 18622099,
                   'whole_private_excluded_files': 5, 'whole_private_excluded_bytes': 4795,
                   'control_source_files': len(CONTROLS) + 1, 'members': verified,
                   'original_mapping_member': 'ORIGINAL_MAPPING.json', 'stream_chunk_bytes': CHUNK, 'parallel_readers': 1,
                   'observed_own_priority_class': priority_api.GetPriorityClass(own_handle),
                   'historical_native_closure': 'NOT_INFERRED', 'scientific_acceptance_created': False,
                   'remote_publication': 'NOT_RUN', 'remote_readback': 'NOT_RUN', 'pruning': 'NOT_RUN',
                   'source_deletions': 0, 'g_writes': 0, 'wsl_starts': 0, 'native_jobs': 0, 'network_calls': 0}
        (OUT / 'build_receipt.json').write_bytes(encoded(receipt))
        (OUT / 'original_mapping.json').write_bytes(generated['ORIGINAL_MAPPING.json'])
        (OUT / 'SHA256SUMS.txt').write_bytes(sums)
        (OUT / (archive.name + '.sha256')).write_text(archive_sha + '  ' + archive.name + '\n', encoding='ascii')
        print(json.dumps({key: receipt[key] for key in ('state', 'archive', 'bytes', 'sha256', 'public_original_files', 'control_source_files')}))
    finally:
        for capture in reversed(captures):
            capture.stream.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    if args.build:
        build()
    else:
        print(json.dumps({'state': 'PREPARED_NO_BUILD_NO_PURGE', 'expected_public_original_files': 194}))
