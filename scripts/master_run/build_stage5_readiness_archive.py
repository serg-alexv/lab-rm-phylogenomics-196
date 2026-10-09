"""Freeze only this audit's fixed C controls/evidence; no G/runtime payloads."""
from pathlib import Path
import hashlib
import json
import os
import zipfile

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
FILES = [
    'stage5_deployment_readiness.md', 'stage5_deployment_readiness.json',
    'stage5_runtime_discovery.py', 'test_stage5_runtime_discovery.py',
    'stage5_source_readiness.py', 'stage5_source_readiness_attempt01.py',
    'test_stage5_source_readiness.py', 'stage5_preparation_checks.json',
    'stage5_support_code_readback_01.json', 'stage5_canonical_source_pins_readback.json',
    'stage5_accepted_source_pins.json', 'stage5_atomic_config.template.json',
    'build_stage5_readiness_archive.py',
]
for attempt in ['01', '02']:
    prefix = 'stage5_source_readiness_actual_' + attempt
    FILES.extend(prefix + '/' + name for name in
                 ['started.json', 'receipt.json', 'actual_file_hashes.jsonl', 'per_accession.jsonl'])
    FILES.extend([prefix + '.stdout.txt', prefix + '.stderr.txt'])


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def main():
    require(Path(__file__).resolve().parent == WORK, 'Exact C audit deployment required')
    final = json.loads((WORK / 'stage5_source_readiness_actual_02/receipt.json').read_text())
    require(final['status'] == 'PASS_CURRENT_CANONICAL_SOURCE_BYTES_ONLY'
            and final['passed'] == final['accessions_checked'] == 196 and final['failed'] == 0,
            'Actual196 source-readiness completion is required, not detector acceptance')
    for name, expected in final['files'].items():
        require(digest(WORK / 'stage5_source_readiness_actual_02' / name) == expected,
                'Final source proof drift')
    out = WORK / 'stage5_source_readiness01'
    require(not out.exists(), 'Preserve existing archive')
    originals = {}
    for name in FILES:
        path = WORK / name
        require(path.is_file() and not any(p.is_symlink() for p in [path, *path.parents])
                and WORK in path.resolve().parents, 'Missing/linked/out-of-scope C evidence')
        require(path.stat().st_size < 32 * 1024**2, 'Unexpected large audit evidence')
        originals[name] = {'sha256': digest(path), 'bytes': path.stat().st_size,
                           'identity': identity(path.stat())}
    require(sum(row['bytes'] for row in originals.values()) < 64 * 1024**2, 'Bounded evidence set required')
    out.mkdir()
    archive = out / 'master_stage5_source_readiness01.zip'
    members = {}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for name, expected in originals.items():
            path = WORK / name
            info = zipfile.ZipInfo(name, (2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            copied = hashlib.sha256()
            with path.open('rb') as source, bundle.open(info, 'w') as target:
                require(identity(os.fstat(source.fileno())) == expected['identity'], 'Source identity drift before copy')
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    copied.update(chunk); target.write(chunk)
                require(identity(os.fstat(source.fileno())) == expected['identity'], 'Source identity drift during copy')
            require(identity(path.stat()) == expected['identity'] and copied.hexdigest() == expected['sha256'],
                    'Original expected bytes drifted during capture')
            members[name] = {'sha256': expected['sha256'], 'bytes': expected['bytes']}
        sums = ''.join(row['sha256'] + '  ' + name + '\n' for name, row in sorted(members.items())).encode()
        info = zipfile.ZipInfo('SHA256SUMS.txt', (2026, 10, 9, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
        bundle.writestr(info, sums)
        members['SHA256SUMS.txt'] = {'sha256': hashlib.sha256(sums).hexdigest(), 'bytes': len(sums)}
    require(archive.stat().st_size < 500 * 1024**2, 'Release asset size contract violated')
    observed = []
    with zipfile.ZipFile(archive) as bundle:
        require(len(bundle.namelist()) == len(set(bundle.namelist())) == len(members)
                and set(bundle.namelist()) == set(members), 'Archive membership differs')
        for info in bundle.infolist():
            with bundle.open(info) as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            expected = members[info.filename]
            require(actual == expected['sha256'] and info.file_size == expected['bytes'], 'Expected original member SHA/size differs')
            observed.append({'member': info.filename, **expected, 'crc32': f'{info.CRC:08x}', 'crc_verified': True})
    for name, expected in originals.items():
        require(identity((WORK / name).stat()) == expected['identity'] and digest(WORK / name) == expected['sha256'],
                'Final original evidence drift')
    receipt = {'schema': 'STAGE05_SOURCE_READINESS_AUDIT_ARCHIVE_V1', 'state': 'PASS_LOCAL_ARCHIVE_CRC_SHA_ONLY',
               'archive': archive.name, 'bytes': archive.stat().st_size, 'sha256': digest(archive),
               'members': observed, 'original_controls': originals, 'native_execution': 'NOT_RUN',
               'remote_readback': 'NOT_RUN', 'scientific_acceptance_created': False,
               'scope': 'CURRENT196_SOURCE_BYTE_READINESS_PLUS_FAILED_CHECKER_ATTEMPT_AND_PREPARATION_ONLY'}
    (out / 'build_receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (out / (archive.name + '.sha256')).write_text(receipt['sha256'] + '  ' + archive.name + '\n', encoding='ascii')
    print(json.dumps({key: receipt[key] for key in ['state', 'archive', 'bytes', 'sha256']}))


if __name__ == '__main__':
    main()
