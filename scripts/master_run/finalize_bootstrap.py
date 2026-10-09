from pathlib import Path
import datetime as dt
import hashlib
import json
import msvcrt
import subprocess
import publish_bootstrap as B

lock = (B.HISTORY / '.work/workflow.lock').open('r+b')
lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
try:
    assert B.git('rev-parse', 'HEAD') == B.EXPECTED
    allow = ['STATUS.md', 'WORK_ORDER.md', 'status/run_control.json', 'status/stages.tsv',
        'status/atomic_continuation_20261009.json', 'status/stage04_execution.json',
        'scripts/independent_stage04a_check_20261009.py']
    allow += [p.relative_to(B.ROOT).as_posix() for p in B.REPORT.iterdir() if p.is_file()]
    assert set(B.git('diff', '--cached', '--name-only').splitlines()) == set(allow)
    manifest = B.read_json(B.REPORT / 'sha256_manifest.json') if hasattr(B, 'read_json') else json.loads((B.REPORT / 'sha256_manifest.json').read_text())
    for name, expected in manifest.items():
        assert B.sha(B.ROOT / name) == expected, name
    # Repository * -text preserves exact imported bytes. CRLF and TSV empty
    # fields are legitimate bytes; retain other whitespace-error checks.
    subprocess.run(['git', '-C', str(B.ROOT), '-c', 'core.whitespace=cr-at-eol,-blank-at-eol', 'diff', '--cached', '--check'], check=True)
    subprocess.run(['git', '-C', str(B.ROOT), 'commit', '-m', 'Resume atomic full196 continuation and verify retained inputs'], check=True)
    commit = B.git('rev-parse', 'HEAD')
    subprocess.run(['git', '-C', str(B.ROOT), 'push', 'origin', 'main'], check=True)
    remote = B.git('ls-remote', 'origin', 'refs/heads/main').split()[0]
    assert remote == commit
    tree = json.loads(subprocess.check_output(['gh', 'api', f'repos/serg-alexv/lab-rm-phylogenomics-196/git/trees/{commit}?recursive=1'], text=True, encoding='utf-8'))
    assert not tree.get('truncated')
    blobs = {x['path']: x['sha'] for x in tree['tree'] if x['type'] == 'blob'}
    verified = []
    for name in allow:
        blob = B.git('hash-object', '--', name)
        assert blobs.get(name) == blob, name
        verified.append({'path': name, 'git_blob': blob, 'sha256': B.sha(B.ROOT / name)})
    B.save(B.CHAT / 'work/bootstrap/publication_receipt.json', {'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'state': 'UPLOAD_VERIFIED_GIT_BLOBS', 'commit': commit, 'remote_commit': remote,
        'files': verified, 'scientific_stage4': 'INCOMPLETE', 'scientific_stages5_to7': 'NOT_RUN'})
    print(json.dumps({'published': True, 'verified_files': len(verified), 'commit': commit}))
finally:
    lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1); lock.close()
