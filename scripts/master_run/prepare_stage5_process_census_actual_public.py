"""Prepare exact closed C census controls; no live queries or native imports."""
from pathlib import Path
import hashlib
import json
import stat

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
SPOOL = WORK / 'stage5_process_census_62165165c82c4a5d9149d55894f426e8'
PREFIX = 'reports/master_run/20261009/stage5_process_census_actual01/'
REVIEW_SHA = '418ac6e16f69dbed00313340f8a582cb34c486ec4c7fe43a342a83a0fd5d5b8c'
CHECKER_SHA = '42b7b1502fcecec6add1ce829fa4b79d9092fa8d8011c0aabc6e5a9e6f5dfe20'
PEER_SHA = 'a0e4dcba09a78fdf7fc191d663da6e857f50234c4b6f3dcf74bf7a550897120b'
PUBLIC = ('started.json', 'receipt.json', 'before.spi_metadata.json',
          'after.spi_metadata.json', 'supplemental.json',
          'supplemental_worker_birth.json', 'supplemental_worker_terminal.json',
          'supplemental_worker_result.json')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read(path, expected=None):
    before = path.lstat()
    need(path.parent in (WORK, SPOOL) and stat.S_ISREG(before.st_mode)
         and before.st_nlink == 1 and not path.is_symlink()
         and not getattr(before, 'st_file_attributes', 0) & 0x400,
         'Exact plain one-link C control required')
    need(before.st_size <= 8 * 1024 ** 2, 'Control exceeds bound')
    with path.open('rb') as stream:
        raw = stream.read(8 * 1024 ** 2 + 1)
    after = path.lstat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'Control drift')
    digest = hashlib.sha256(raw).hexdigest()
    need(expected is None or digest == expected, 'Unexpected control bytes')
    return raw, dict(local_path=str(path), bytes=len(raw), sha256=digest)


def save(name, value):
    path = WORK / name
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + '\n')
    return read(path)[1]


def main():
    need(Path(__file__).resolve().parent == WORK, 'C-only deployment required')
    raw, review_pin = read(WORK / 'stage5_process_census_actual_independent_review.json', REVIEW_SHA)
    review = json.loads(raw)
    need(review['state'] == 'PASS_RETAINED_DIAGNOSTIC_EVIDENCE_NOT_OLD_SCOPE_CLOSURE'
         and review['closure_acceptance'] is False
         and review['STOP_removal_authorized'] is False, 'Diagnostic qualification missing')
    pins = {Path(item['path']).name: item for item in review['pins']}
    files = []
    for name in PUBLIC:
        _, pin = read(SPOOL / name, pins[name]['sha256'])
        need(pin['bytes'] == pins[name]['bytes'], 'Public control size changed')
        files.append(dict(pin, suggested_repository_path=PREFIX + 'actual/' + name))
    _, checker_pin = read(WORK / 'verify_stage5_process_census_actual.py', CHECKER_SHA)
    _, peer_pin = read(WORK / 'stage5_process_census_independent_review.json', PEER_SHA)
    files += [dict(checker_pin, suggested_repository_path='scripts/master_run/verify_stage5_process_census_actual.py'),
              dict(review_pin, suggested_repository_path=PREFIX + 'INDEPENDENT_ACTUAL_REVIEW.json'),
              dict(peer_pin, suggested_repository_path=PREFIX + 'DIAGNOSTIC_SOURCE_INDEPENDENT_REVIEW.json')]
    exclusions = []
    for item in review['raw_native_exclusions']:
        name = item['publicly_preserved_metadata']
        exclusions.append(dict(item, captured_metadata=next(row for row in files
                               if Path(row['local_path']).name == name),
                               raw_bytes_read_in_this_preparer=False,
                               local_original_must_be_preserved=True))
    need(len(exclusions) == 2 and {Path(row['path']).name for row in exclusions}
         == {'before.spi.bin', 'after.spi.bin'}, 'Exact raw exclusion set required')
    exclusion_pin = save('stage5_process_census_actual_raw_exclusions.json', dict(
        schema='STAGE05_CENSUS_RAW_NATIVE_EXCLUSIONS_V1', raw_file_count=2,
        raw_total_bytes=sum(row['bytes'] for row in exclusions), files=exclusions,
        raw_payload_publication_authorized=False, original_deletion_authorized=False,
        independent_actual_review_sha256=REVIEW_SHA))
    files.append(dict(exclusion_pin, suggested_repository_path=PREFIX + 'RAW_NATIVE_EXCLUSIONS.json'))
    completion_pin = save('stage5_process_census_ACTUAL_COMPLETION.json', dict(
        schema='STAGE05_PROCESS_CENSUS_ACTUAL_PUBLIC_COMPLETION_V1',
        state=review['state'], actual_projected_json_count=8, raw_native_excluded_count=2,
        actual_receipt_sha256=pins['receipt.json']['sha256'],
        independent_review=review_pin, independent_checker=checker_pin,
        source_only_peer_review=peer_pin, raw_native_exclusion_manifest=exclusion_pin,
        native_before_after_enum_pid_count=425, unknown_kernel_births_each_snapshot=168,
        accessible_birth_candidates_each_snapshot=0, new_query_worker_exit0_and_empty_job=True,
        original_owner_missing_is_exit_proof=False, historical_clock_continuity_proven=False,
        original_scope_closure_accepted=False, closure_acceptance=False,
        STOP_removal_authorized=False,
        next_step='ROOT_SEPARATELY_AUTHORIZED_VERIFIED_WINDOWS_BOOT_TRANSITION_FALLBACK',
        live_process_queries_by_independent_checker=0, WSL_launches=0, G_access=0,
        process_mutations=0, original_scientific_or_STOP_bytes_modified=False,
        already_published_source_references=[
            dict(pins['stage5_process_census.py'], repository_path='scripts/master_run/stage5_process_census.py'),
            dict(pins['stage5_process_census_cim_query.ps1'], repository_path='scripts/master_run/stage5_process_census_cim_query.ps1')]))
    files.append(dict(completion_pin, suggested_repository_path=PREFIX + 'ACTUAL_COMPLETION.json'))
    _, preparer_pin = read(Path(__file__))
    files.append(dict(preparer_pin, suggested_repository_path='scripts/master_run/prepare_stage5_process_census_actual_public.py'))
    need(len(files) == 14 and len({row['suggested_repository_path'] for row in files}) == 14,
         'Exact unique public mapping required')
    for row in files:
        read(Path(row['local_path']), row['sha256'])
    mapping_pin = save('stage5_process_census_actual_public_mapping.json', dict(
        schema='STAGE05_PROCESS_CENSUS_ACTUAL_PUBLIC_MAPPING_V1', files=files,
        file_count=len(files), total_bytes=sum(row['bytes'] for row in files),
        mapping_suggested_repository_path=PREFIX + 'PUBLIC_MAPPING.json',
        raw_native_binary_in_mapping=False, closure_acceptance=False,
        STOP_removal_authorized=False, original_deletion_authorized=False,
        scope='CLOSED_DIAGNOSTIC_EVIDENCE_ONLY_NOT_ORIGINAL_SCOPE_CLOSURE'))
    print(json.dumps(dict(mapping=mapping_pin, files=14,
                          exclusions=exclusion_pin, completion=completion_pin), sort_keys=True))


if __name__ == '__main__':
    main()
