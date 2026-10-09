"""Prepare exact public recovery controls; create no remote refs or uploads."""
from pathlib import Path
import argparse, hashlib, json

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-head', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    work = Path(__file__).resolve().parent
    rows = []
    def add(local, target):
        path = work / local
        raw = path.read_bytes()
        assert 0 < len(raw) < 5 * 1024 * 1024
        rows.append({'local_absolute_path': str(path), 'target': target,
                     'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    for source in ['build_master_public_components01.py', 'build_public_history02.py',
                   'inspect_public_history02.py', 'finalize_public_history02_scope.py',
                   'test_public_history02_screen.py', Path(__file__).name,
                   'upload_master_recovery_assets.py',
                   'prepare_master_recovery_progress.py',
                   'prepare_master_recovery_assets_plan.py',
                   'verify_master_public_components01_remote.py',
                   'verify_master_public_history02_remote.py']:
        add(source, 'scripts/master_run/' + source)
    prefix = 'reports/master_run/20261009/cleanup/'
    for name in ['build_receipt.json', 'source_binding.json', 'original_source_manifest.json',
                 'component_source_map.json', 'README.txt', 'SHA256SUMS.txt']:
        add('master_public_components01/' + name, prefix + 'components01/' + name)
    for name in ['asset_index.json', 'build_receipt.json', 'source_binding.json',
                 'original_member_mapping.json', 'PUBLICATION_CONTROL_SHA256.json',
                 'REVIEW.md', 'ATTRIBUTION_AND_SCOPE.txt']:
        add('master_public_history02/' + name, prefix + 'history02/' + name)
    for name in ['inspection.json', 'manual_scope_review.json', 'excluded_files.json', 'public_scope.json']:
        add('master_public_history02_inspection/' + name, prefix + 'history02/inspection/' + name)
    add('master_public_history02_source_review.json', prefix + 'history02/source_review.json')
    add('master_batch03_purge_remote_readback.json', prefix + 'batch03_purge01/SOURCE_REMOTE_READBACK.json')
    add('master_recovery_progress01/native_progress.json', 'reports/master_run/20261009/snapshots/recovery_progress01/native_progress.json')
    add('master_recovery_progress01/status.json', 'status/master_run_20261009.json')
    add('master_recovery_progress01/STATUS.md', 'STATUS.md')
    plan = {'expected_head': a.expected_head,
            'message': 'Preserve exact public component and historical source recovery controls before archival',
            'files': rows}
    with a.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(plan, indent=2) + '\n')
    print(json.dumps({'files': len(rows), 'bytes': sum(r['bytes'] for r in rows), 'plan': str(a.output)}))

if __name__ == '__main__':
    main()
