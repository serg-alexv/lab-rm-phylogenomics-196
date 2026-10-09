"""Publish exact completed cleanup evidence and the next separately reviewed proposal."""
from pathlib import Path
import argparse, hashlib, json

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-head', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    work = Path(__file__).resolve().parent
    files = []
    def add(local, target):
        path = work / local
        raw = path.read_bytes()
        assert 0 < len(raw) < 5 * 1024 * 1024
        files.append({'local_absolute_path': str(path), 'target': target,
                      'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    sources = ['prepare_master_cleanup_completed_progress.py', Path(__file__).name,
        'verify_master_batch03_leaf_purge.py', 'test_master_batch03_postverify.py',
        'build_master_batch03_execution_archive.py', 'test_master_batch03_execution_archive.py',
        'verify_master_batch03_execution_remote.py', 'verify_master_batch03_execution_remote_attempt01.py',
        'test_master_batch03_execution_remote.py',
        'Invoke-MasterHistory02LeafPurge.ps1', 'prepare_master_history02_leaf_purge.py',
        'test_master_history02_leaf_purge.py', 'test_public_archive_readback.py',
        'stage5_runtime_discovery.py', 'test_stage5_runtime_discovery.py',
        'stage5_source_readiness.py', 'stage5_source_readiness_attempt01.py', 'test_stage5_source_readiness.py']
    for name in sources:
        add(name, 'scripts/master_run/' + name)
    base = 'reports/master_run/20261009/'
    for name in ['manifest.json', 'source_bindings.json', 'build_receipt.json']:
        add('master_batch03_cleanup_execution01_metadata/' + name, base + 'cleanup/batch03_execution01/' + name)
    pairs = {
        'master_batch03_postverify_20261009T200023Z_f95312bd/receipt.json': 'cleanup/batch03_purge01/INDEPENDENT_POSTVERIFY.json',
        'master_batch03_postverify_PREPARATION.md': 'cleanup/batch03_execution01/POSTVERIFY_PREPARATION.md',
        'master_batch03_postverify_preparation_checks.json': 'cleanup/batch03_execution01/POSTVERIFY_PREPARATION_CHECKS.json',
        'master_batch03_execution_archive_PREPARATION.md': 'cleanup/batch03_execution01/ARCHIVE_PREPARATION.md',
        'master_batch03_execution_archive_preparation_checks.json': 'cleanup/batch03_execution01/ARCHIVE_PREPARATION_CHECKS.json',
        'batch03_execution01_readback_20261009T200359Z_a06a0974/receipt.json': 'cleanup/batch03_execution01/LOCAL_READBACK.json',
        'batch03_execution01_readback_20261009T200346Z_b4643a06/receipt.json': 'cleanup/batch03_execution01/LOCAL_DRAFT_FAILURE.json',
        'master_batch03_execution_remote_source_review.json': 'cleanup/batch03_execution01/REMOTE_VERIFIER_SOURCE_REVIEW.json',
        'public_history02_readback_20261009T195508Z_1f99201e/receipt.json': 'cleanup/history02/REMOTE_READBACK.json',
        'public_components01_readback_20261009T195312Z_16720f4a/receipt.json': 'cleanup/components01/REMOTE_READBACK.json',
        'public_archive_readback_preparation_checks.json': 'cleanup/PUBLIC_ARCHIVE_READBACK_PREPARATION_CHECKS.json',
        'master_history02_leaf_purge_proposed.json': 'cleanup/history02_purge01/proposed.json',
        'master_history02_leaf_purge_PREPARATION.md': 'cleanup/history02_purge01/PREPARATION.md',
        'master_history02_leaf_purge_preparation_checks.json': 'cleanup/history02_purge01/PREPARATION_CHECKS.json',
        'master_recovery_assets_upload_plan.json': 'publication/RECOVERY_ASSET_UPLOAD_PLAN.json',
        'master_recovery_assets_upload_receipt.json': 'publication/RECOVERY_ASSET_UPLOAD_RECEIPT.json',
        'master_recovery_controls_git_objects.json': 'publication/RECOVERY_CONTROLS_GIT_OBJECTS.json',
        'master_recovery_controls_remote_readback.json': 'publication/RECOVERY_CONTROLS_REMOTE_READBACK.json',
        'stage5_deployment_readiness.md': 'preparation/stage5_deployment_readiness.md',
        'stage5_deployment_readiness.json': 'preparation/stage5_deployment_readiness.json',
        'stage5_preparation_checks.json': 'preparation/stage5_preparation_checks.json',
        'stage5_support_code_readback_01.json': 'preparation/stage5_support_code_readback_01.json',
        'master_cleanup_completed_progress01/native_progress.json': 'snapshots/cleanup_completed_progress01/native_progress.json',
    }
    for local, target in pairs.items():
        add(local, base + target)
    add('master_cleanup_completed_progress01/status.json', 'status/master_run_20261009.json')
    add('master_cleanup_completed_progress01/STATUS.md', 'STATUS.md')
    add('master_cleanup_completed_progress01/STORAGE_LEDGER.md', 'docs/master_run/STORAGE_LEDGER.md')
    assert len({row['target'] for row in files}) == len(files)
    with a.output.open('x', encoding='utf-8') as stream:
        json.dump({'expected_head': a.expected_head,
                   'message': 'Record independently verified cold cleanup and recovery; prepare accession queue and next exact purge',
                   'files': files}, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'files': len(files), 'bytes': sum(row['bytes'] for row in files)}))

if __name__ == '__main__':
    main()
