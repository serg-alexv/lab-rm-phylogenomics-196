"""Bind verified local recovery ZIPs and sidecars to their public controls commit."""
from pathlib import Path
import argparse, hashlib, json, re

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-controls-commit', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert re.fullmatch('[0-9a-f]{40}', a.source_controls_commit)
    work = Path(__file__).resolve().parent
    component = json.loads((work / 'master_public_components01/build_receipt.json').read_text())
    history = json.loads((work / 'master_public_history02/asset_index.json').read_text())
    rows = []
    for directory, declared in [('master_public_components01', [
            {'name': component['asset_name'], 'bytes': component['bytes'], 'sha256': component['sha256']}]),
            ('master_public_history02', history['assets'])]:
        for original in declared:
            path = work / directory / original['name']
            assert path.stat().st_size == original['bytes']
            rows.append({**original, 'local_absolute_path': str(path)})
            sidecar = path.with_name(path.name + '.sha256')
            raw = sidecar.read_bytes()
            assert raw.decode().strip() == original['sha256'] + '  ' + path.name
            rows.append({'name': sidecar.name, 'bytes': len(raw),
                         'sha256': hashlib.sha256(raw).hexdigest(), 'local_absolute_path': str(sidecar)})
    report = {'repository': 'serg-alexv/lab-rm-phylogenomics-196',
              'tag': 'master-run-storage-20261009-v1',
              'source_controls_commit': a.source_controls_commit, 'assets': rows}
    with a.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'assets': len(rows), 'bytes': sum(r['bytes'] for r in rows)}))

if __name__ == '__main__':
    main()
