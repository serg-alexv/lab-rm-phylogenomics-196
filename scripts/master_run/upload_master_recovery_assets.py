"""Upload exact public recovery assets without overwriting; fresh-byte readback is separate."""
from pathlib import Path
import argparse, datetime, hashlib, json, subprocess

REPO = 'serg-alexv/lab-rm-phylogenomics-196'
TAG = 'master-run-storage-20261009-v1'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()

def release():
    r = subprocess.run(['gh', 'api', f'repos/{REPO}/releases/tags/{TAG}'],
                       capture_output=True, check=True, timeout=60)
    return json.loads(r.stdout)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    a = p.parse_args()
    assert not a.receipt.exists(), 'Preserve prior receipts'
    plan = json.loads(a.plan.read_text())
    assert plan['repository'] == REPO and plan['tag'] == TAG
    rows = plan['assets']
    assert len(rows) == len({r['name'] for r in rows}) and rows
    for r in rows:
        path = Path(r['local_absolute_path'])
        assert path.name == r['name'] and path.is_file()
        assert path.stat().st_size == r['bytes'] and digest(path) == r['sha256']
    report = {'schema': 'MASTER_RECOVERY_ASSET_UPLOAD_V1', 'repository': REPO, 'tag': TAG,
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_controls_commit': plan['source_controls_commit'], 'assets': [],
              'state': 'UPLOAD_IN_PROGRESS_FRESH_READBACK_NOT_RUN', 'source_deletions': 0}
    with a.receipt.open('x', encoding='utf-8') as out:
        out.write(json.dumps(report, indent=2) + '\n')
    for row in rows:
        found = [x for x in release()['assets'] if x['name'] == row['name']]
        assert len(found) <= 1, 'Ambiguous asset names'
        uploaded = False
        if not found:
            subprocess.run(['gh', 'release', 'upload', TAG, row['local_absolute_path'],
                            '--repo', REPO], check=True, timeout=1800)
            uploaded = True
            found = [x for x in release()['assets'] if x['name'] == row['name']]
        assert len(found) == 1
        remote = found[0]
        assert remote['size'] == row['bytes'] and remote['digest'] == 'sha256:' + row['sha256']
        assert remote['state'] == 'uploaded'
        report['assets'].append({'name': row['name'], 'bytes': row['bytes'], 'sha256': row['sha256'],
                                 'asset_id': remote['id'], 'url': remote['browser_download_url'],
                                 'uploaded_in_this_call': uploaded})
        a.receipt.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'asset': row['name'], 'state': 'REGISTERED_DIGEST_MATCH_FRESH_READBACK_NOT_RUN'}), flush=True)
    report['state'] = 'ALL_REGISTERED_DIGESTS_MATCH_FRESH_READBACK_NOT_RUN'
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    a.receipt.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
