"""Bind the exact source-readiness evidence ZIP and sidecar to published controls."""
from pathlib import Path
import argparse, hashlib, json, re

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-controls-commit', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert re.fullmatch('[0-9a-f]{40}', a.source_controls_commit)
    work = Path(__file__).resolve().parent
    directory = work / 'stage5_source_readiness01'
    build = json.loads((directory / 'build_receipt.json').read_bytes())
    assert build['sha256'] == 'b06723bf684d76084072d710a0573b34137bc097b5a21f1069077ec69dc6a447'
    assert build['bytes'] == 853741 and build['scientific_acceptance_created'] is False
    path = directory / build['archive']; raw = path.read_bytes()
    assert len(raw) == build['bytes'] and hashlib.sha256(raw).hexdigest() == build['sha256']
    side = path.with_name(path.name + '.sha256'); side_raw = side.read_bytes()
    assert side_raw.decode().strip() == build['sha256'] + '  ' + path.name
    rows = [{'name': q.name, 'local_absolute_path': str(q), 'bytes': len(b),
             'sha256': hashlib.sha256(b).hexdigest()} for q, b in [(path, raw), (side, side_raw)]]
    with a.output.open('x', encoding='utf-8') as stream:
        json.dump({'repository': 'serg-alexv/lab-rm-phylogenomics-196',
                   'tag': 'master-run-storage-20261009-v1',
                   'source_controls_commit': a.source_controls_commit, 'assets': rows}, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'assets': len(rows), 'bytes': sum(r['bytes'] for r in rows)}))

if __name__ == '__main__': main()
