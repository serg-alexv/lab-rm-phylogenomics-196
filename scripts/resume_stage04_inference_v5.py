#!/usr/bin/env python3
"""Resume the reviewed WD inference, checking published bytes inside its lock."""
from pathlib import Path
import hashlib
import subprocess
import stage04_controller as C
import stage04_inference_controller_v5 as V


def verify_adoption(root, remote=False, expected_receipt_sha256=None):
    receipt = root / 'reports/stage04/inference_v5_adoption.json'
    receipt_sha256 = C.digest(receipt)
    C.check(expected_receipt_sha256 is None or receipt_sha256 == expected_receipt_sha256,
            'Initial adoption receipt changed after process imports; preserve outputs and restart review')
    value = C.load(receipt)
    C.check(value['status'] == 'REVIEWED_RESUMED_INFERENCE_V5_ADOPTED_BEFORE_TOPOLOGY',
            'Reviewed v4 adoption receipt required')
    paths = set()
    for item in value['sources']:
        name = item['path']
        path = (root / name).resolve()
        C.check(root in path.parents and name not in paths,
                'Adoption source escapes project or repeats a path')
        paths.add(name)
        C.check(path.is_file() and C.digest(path) == item['sha256'],
                'Published adoption bytes changed: ' + name)
        if remote:
            result = subprocess.run(['git', 'show', 'origin/main:' + name],
                                    cwd=root, capture_output=True, check=True)
            C.check(hashlib.sha256(result.stdout).hexdigest() == item['sha256'],
                    'Canonical published source differs: ' + name)
    required = {'scripts/stage04_inference_v5.py',
                'scripts/stage04_inference_controller_v5.py',
                'scripts/stage04_inference_validate_v5.py',
                'scripts/stage04_iqtree_limit_v4.py',
                'scripts/stage04_linux_launcher_v4.py',
                'scripts/resume_stage04_inference_v5.py',
                'scripts/stage04_controller.py',
                'scripts/stage04_phylogeny.py',
                'scripts/stage04_validate.py',
                'scripts/wsl_project.sh',
                'config/host_inference_stage04_v5.json',
                'scripts/stage04_migration_support_v5.py',
                'scripts/stage04_migration_wsl_v5.sh'}
    C.check(required <= paths, 'Incomplete adopted production code identity')
    if remote:
        result = subprocess.run(['git', 'show', 'origin/main:reports/stage04/inference_v5_adoption.json'],
                                cwd=root, capture_output=True, check=True)
        C.check(hashlib.sha256(result.stdout).hexdigest() == receipt_sha256,
                'Canonical adoption receipt differs')
    return value


def main():
    args = V.parse()
    expected = C.digest(args.root / 'reports/stage04/inference_v5_adoption.json')
    verify_adoption(args.root, expected_receipt_sha256=expected)
    original_reconcile = C.reconcile

    def reconcile_with_adoption(root):
        head = original_reconcile(root)
        # V.run invokes this while holding the one actual Windows byte lock.
        # It is repeated before phases/progress; user changes block continuation.
        verify_adoption(root, remote=True, expected_receipt_sha256=expected)
        return head

    C.reconcile = reconcile_with_adoption
    V.run(args)


if __name__ == '__main__':
    main()
