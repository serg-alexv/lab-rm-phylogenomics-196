"""Malformed published-source guards; synthetic files only, no native jobs."""
from pathlib import Path
import copy
import json
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import resume_stage04_inference_v4 as L


def run():
    passed = []
    with tempfile.TemporaryDirectory(prefix='stage04_adoption_guard_') as temp:
        root = Path(temp)
        names = ['scripts/stage04_inference_v4.py', 'scripts/stage04_inference_controller_v4.py',
                 'scripts/stage04_inference_validate_v4.py', 'scripts/stage04_iqtree_limit_v4.py',
                 'scripts/stage04_linux_launcher_v4.py', 'scripts/resume_stage04_inference_v4.py',
                 'scripts/stage04_controller.py', 'scripts/stage04_phylogeny.py',
                 'scripts/stage04_validate.py', 'scripts/wsl_project.sh',
                 'config/host_inference_stage04_v4.json']
        for name in names:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('SYNTHETIC_SOURCE\n', encoding='utf-8')
        good = {'status': 'REVIEWED_RESUMED_INFERENCE_V4_ADOPTED_BEFORE_TOPOLOGY',
                'sources': [{'path': name, 'sha256': L.C.digest(root / name)} for name in names]}
        receipt = root / 'reports/stage04/inference_v4_adoption.json'
        L.C.atomic(receipt, good)
        L.verify_adoption(root)
        passed.append('valid_exact_adoption')

        def reject(name, value):
            L.C.atomic(receipt, value)
            try:
                L.verify_adoption(root)
            except ValueError:
                passed.append(name)
            else:
                raise AssertionError(name)

        bad = copy.deepcopy(good); bad['sources'][0]['sha256'] = '0' * 64
        reject('changed_source_bytes', bad)
        bad = copy.deepcopy(good); bad['sources'].pop()
        reject('required_config_missing', bad)
        bad = copy.deepcopy(good); bad['sources'][0]['path'] = '../outside'
        reject('path_escape', bad)
        bad = copy.deepcopy(good); bad['sources'].append(bad['sources'][0])
        reject('duplicate_source', bad)
        L.C.atomic(receipt, good)
        initial = L.C.digest(receipt)
        changed = copy.deepcopy(good); changed['new_field'] = 'SYNTHETIC_CHANGE_AFTER_IMPORT'
        L.C.atomic(receipt, changed)
        try:
            L.verify_adoption(root, expected_receipt_sha256=initial)
        except ValueError:
            passed.append('initial_adoption_receipt_changed_after_import')
        else:
            raise AssertionError('Changed adoption receipt accepted')
        L.C.atomic(receipt, good)
        with patch.object(L.subprocess, 'run', return_value=SimpleNamespace(stdout=b'CHANGED_REMOTE')):
            try:
                L.verify_adoption(root, remote=True)
            except ValueError:
                passed.append('canonical_remote_source_changed')
            else:
                raise AssertionError('Changed remote source accepted')
    report = {'status': 'PASS_SYNTHETIC_PUBLISHED_SOURCE_GUARDS', 'passed': len(passed),
              'fixtures': passed, 'biological_jobs_run': 0,
              'launcher_source_sha256': L.C.digest(Path(L.__file__)),
              'test_source_sha256': L.C.digest(Path(__file__))}
    L.C.atomic(Path.cwd() / 'reports/stage04/inference_v4_published_source_tests.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    run()
