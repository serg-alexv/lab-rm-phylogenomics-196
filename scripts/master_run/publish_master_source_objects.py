"""Publish an exact reviewed public source allowlist as unreferenced Git objects.

The root subsequently advances main with the GitHub connector expected-head
lease. This script does not edit the checkout, update refs or remove files.
"""
from pathlib import Path, PurePosixPath
import base64, datetime, hashlib, json, subprocess

W = Path(__file__).resolve().parent
REPO = 'serg-alexv/lab-rm-phylogenomics-196'
plan = json.loads((W / 'master_source_publication_plan.json').read_text())
def api(route, body=None):
    argv = ['gh', 'api', 'repos/' + REPO + '/' + route]
    if body is not None:
        argv += ['--method', 'POST', '--input', '-']
    result = subprocess.run(argv, input=json.dumps(body).encode() if body is not None else None,
                            capture_output=True, check=True)
    return json.loads(result.stdout)
expected = plan['expected_remote_head']
assert api('git/ref/heads/main')['object']['sha'] == expected, 'Remote advanced; inspect before publishing'
base = api('git/commits/' + expected)['tree']['sha']
rows = plan['files'][:]
for path, target in [
    (W/'cleanup_inventory_plan.json', 'reports/master_run/20261009/cleanup/INITIAL_INVENTORY.json'),
    (W/'master_remote_update_readback.json', 'reports/master_run/20261009/verification/initial_progress_readback.json'),
    (W/'master_source_publication_plan.json', 'reports/master_run/20261009/preparation/SOURCE_PUBLICATION_PLAN.json'),
    (Path(__file__), 'scripts/master_run/publish_master_source_objects.py')]:
    data = path.read_bytes()
    rows.append({'local_absolute_path': str(path), 'target': target, 'bytes': len(data),
                 'sha256': hashlib.sha256(data).hexdigest(), 'transport_encoding': 'utf-8'})
captured = []
for row in rows:
    pure = PurePosixPath(row['target'])
    assert not pure.is_absolute() and '..' not in pure.parts and '\\' not in str(pure)
    assert str(pure) == row['target'] and len(pure.parts) > 1
    data = Path(row['local_absolute_path']).read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['target']
    assert len(data) < 5*1024*1024
    captured.append((row, data))
assert len({row['target'] for row, _ in captured}) == len(captured), 'Duplicate publication target'
entries = []
for row, data in captured:
    entry = {'path': row['target'], 'mode': '100644', 'type': 'blob'}
    if row['transport_encoding'] == 'base64':
        entry['sha'] = api('git/blobs', {'encoding': 'base64', 'content': base64.b64encode(data).decode()})['sha']
    else:
        entry['content'] = data.decode('utf-8')
    entries.append(entry)
tree = api('git/trees', {'base_tree': base, 'tree': entries})['sha']
commit = api('git/commits', {'message': 'Preserve master-run preparation source, checks and cleanup inventory',
                            'tree': tree, 'parents': [expected]})['sha']
receipt = {'schema': 'MASTER_SOURCE_GIT_OBJECT_PREPARATION_V1',
    'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'state': 'OBJECTS_ONLY_REF_NOT_UPDATED',
    'expected_head': expected, 'tree': tree, 'commit': commit,
    'files': [{k: row[k] for k in ('target','bytes','sha256')} for row, _ in captured]}
with (W/'master_source_git_objects.json').open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({'expected_head':expected,'commit':commit,'files':len(captured),
                  'bytes':sum(len(data) for _,data in captured),'state':receipt['state']}))
