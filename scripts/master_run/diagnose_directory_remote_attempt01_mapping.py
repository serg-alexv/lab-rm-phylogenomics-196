"""Reproduce one failed readback's publication diagnosis from frozen C evidence.

Default is no operation. No network, Git invocation, directory walk, G/old-C read,
payload execution, cleanup or acceptance is performed. Report bytes stay original.
"""
from pathlib import Path
import argparse
import hashlib
import json

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ATTEMPT = WORK / 'directory_prune_execution01_readback_20261009T221909Z_534f476f'
PREFIX = 'reports/master_run/20261009/cleanup/directory_prune_execution01/'
PINS = {
    ATTEMPT / 'command_io/000.stdout.txt': '227ded256a74446e209883f5ee359aa33dd2741e75e6c15e5a8cdedfe636b080',
    ATTEMPT / 'receipt.json': 'd9129edf5c9b085df12c76878ad6574d5e51aeb42be16bb3cc80d9ae93115ea8',
    WORK / 'directory_prune_execution_archive_completion.json': 'c14ab736f0dbe841919e1efca89b9d5405f8f79ff0daba0c78cbf868a5aaefe3',
    WORK / 'directory_prune_execution_remote_attempt01_diagnosis.json': '985df53a038c88222e552ba060a8acbb33e58b644bf0116b0981ed765e3e4a2a',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def checked(path, expected):
    require(path.is_relative_to(WORK) and not path.is_symlink(), 'C evidence scope/link')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'Evidence SHA: ' + str(path))
    return raw


def diagnose():
    require(Path(__file__).resolve().parent == WORK, 'Exact active C work only')
    raw = {p: checked(p, h) for p, h in PINS.items()}
    tree = json.loads(raw[ATTEMPT / 'command_io/000.stdout.txt'])
    receipt = json.loads(raw[ATTEMPT / 'receipt.json'])
    completion = json.loads(raw[WORK / 'directory_prune_execution_archive_completion.json'])
    report = json.loads(raw[WORK / 'directory_prune_execution_remote_attempt01_diagnosis.json'])
    require(tree['truncated'] is False and len(tree['tree']) == 1622, 'Frozen complete tree')
    remote = {r['path']: r for r in tree['tree'] if r['type'] == 'blob'}
    require(len(completion['public_control_mapping']) == 6
            and len(completion['public_source_and_review_mapping']) == 8, 'Original two mapping lists')
    for i, row in enumerate(completion['public_control_mapping']):
        path = row['suggested_repository_path']
        require(path in remote and remote[path]['size'] == row['bytes'], 'Declared control missing')
        fetched = ATTEMPT / 'published_controls' / (str(i).zfill(2) + '_' + Path(row['path']).name)
        data = checked(fetched, row['sha256'])
        require(len(data) == row['bytes'] and hashlib.sha1(
            b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == remote[path]['sha'],
            'Actual fetched control Git object')
    require(PREFIX + 'PUBLIC_COMPLETION.json' in remote, 'Public original completion missing')
    data = raw[WORK / 'directory_prune_execution_archive_completion.json']
    require(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            == remote[PREFIX + 'PUBLIC_COMPLETION.json']['sha'], 'Completion Git object differs')
    rows = []
    for row in completion['public_source_and_review_mapping']:
        original = Path(row['path'])
        data = checked(original, row['sha256'])
        require(len(data) == row['bytes'], 'Original source/control size')
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        item = dict(path=str(original), suggested_repository_path=row['suggested_repository_path'],
                    bytes=len(data), sha256=row['sha256'], git_blob=blob,
                    exact_blob_remote_paths=[r['path'] for r in tree['tree']
                                             if r['type'] == 'blob' and r['sha'] == blob],
                    declared_path_present=row['suggested_repository_path'] in remote)
        require(not item['declared_path_present'] and not item['exact_blob_remote_paths'],
                'Expected missing publication changed')
        rows.append(item)
    require(rows == report['missing_public_source_and_review_mapping'], 'Diagnosis mappings differ')
    require(receipt['state'] == 'FAILED_READBACK_NO_CLEANUP_AUTHORITY'
            and receipt['error']['message'] ==
            'Missing/oversized published control: scripts/master_run/build_directory_prune_execution_archive.py'
            and len(receipt['owned_commands']) == 10
            and all(r['closure_proven'] is True and r['exit_code'] == 0
                    for r in receipt['owned_commands']), 'Failure/owned command closure differs')
    require('release_before' not in receipt and report['asset_download_started'] is False,
            'Asset download evidence differs')
    return dict(state='PASS_FROZEN_ATTEMPT01_PUBLICATION_DIAGNOSIS_REPRODUCED',
                original_diagnosis_sha256=PINS[WORK / 'directory_prune_execution_remote_attempt01_diagnosis.json'],
                complete_tree_entries=1622, existing_declared_controls=6,
                missing_declared_source_review_files=8, closed_owned_commands=10,
                verifier_source_change_needed=False, remote_rerun=False,
                cleanup_authority=False, scientific_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-frozen-evidence', action='store_true')
    args = parser.parse_args()
    if args.check_frozen_evidence:
        print(json.dumps(diagnose(), indent=2, sort_keys=True))
    else:
        print(json.dumps(dict(state='NOT_RUN', network=False, mutation=False)))
