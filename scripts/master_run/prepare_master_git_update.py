"""Create public Git objects from an exact hash-pinned plan; never update refs."""
from pathlib import Path, PurePosixPath
import argparse, base64, datetime, hashlib, json, subprocess

REPO = 'serg-alexv/lab-rm-phylogenomics-196'
def api(route, body=None):
    command = ['gh', 'api', 'repos/' + REPO + '/' + route]
    if body is not None:
        command += ['--method', 'POST', '--input', '-']
    result = subprocess.run(command, input=json.dumps(body).encode() if body is not None else None,
                            capture_output=True, check=True)
    return json.loads(result.stdout)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    args = p.parse_args()
    assert not args.receipt.exists(), 'Preserve prior publication receipts'
    plan = json.loads(args.plan.read_text())
    expected = plan['expected_head']
    assert api('git/ref/heads/main')['object']['sha'] == expected, 'Remote advanced; inspect before publication'
    base = api('git/commits/' + expected)['tree']['sha']
    captured = []
    for row in plan['files']:
        path = PurePosixPath(row['target'])
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in str(path)
        assert str(path) == row['target'] and (len(path.parts) > 1 or str(path) in {'STATUS.md', 'README.md'})
        data = Path(row['local_absolute_path']).read_bytes()
        assert len(data) < 5*1024*1024 and len(data) == row['bytes']
        assert hashlib.sha256(data).hexdigest() == row['sha256'], row['target']
        captured.append((row, data))
    assert captured and len({row['target'] for row, _ in captured}) == len(captured)
    entries = []
    for row, data in captured:
        entry = {'path': row['target'], 'mode': '100644', 'type': 'blob'}
        if row.get('transport_encoding', 'utf-8') == 'base64':
            entry['sha'] = api('git/blobs', {'encoding': 'base64', 'content': base64.b64encode(data).decode()})['sha']
        else:
            entry['content'] = data.decode('utf-8')
        entries.append(entry)
    tree = api('git/trees', {'base_tree': base, 'tree': entries})['sha']
    commit = api('git/commits', {'message': plan['message'], 'tree': tree, 'parents': [expected]})['sha']
    receipt = {'schema': 'MASTER_UPDATE_GIT_OBJECTS_V1',
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'state': 'OBJECTS_ONLY_REF_NOT_UPDATED',
        'expected_head': expected, 'tree': tree, 'commit': commit,
        'files': [{k: row[k] for k in ('target','bytes','sha256')} for row, _ in captured]}
    with args.receipt.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'expected_head':expected, 'commit':commit, 'files':len(captured)}))

if __name__ == '__main__':
    main()
