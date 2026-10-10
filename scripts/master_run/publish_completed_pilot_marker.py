"""Freeze one independently validated, closed marker for a leased Git publication."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, subprocess, sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--marker', required=True)
p.add_argument('--receipt', type=Path, required=True)
p.add_argument('--name', required=True)
p.add_argument('--expected-head', required=True)
p.add_argument('--detail', required=True)
p.add_argument('--validated-count', type=int, required=True)
p.add_argument('--prior-readback', type=Path, required=True)
p.add_argument('--observation', type=Path)
a = p.parse_args()
W = Path(__file__).resolve().parent
G = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
P = W / a.name
assert a.marker in {'5-FTHF_cyc-lig', 'ADK', 'ATP-synt', 'ATP-synt_A', 'ATP-synt_B'}
assert Path(a.name).name == a.name and not P.exists()
receipt = json.loads(a.receipt.read_text())
assert receipt['status'] == 'PASS'
assert json.loads(a.prior_readback.read_text())['state'] == 'PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED'

def local_path(value):
    if value.startswith('/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/'):
        return G / PurePosixPath(value).relative_to('/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196')
    return Path(value)

for row in receipt['evidence'].values():
    if isinstance(row, dict) and 'path' in row and 'sha256' in row:
        assert hashlib.sha256(local_path(row['path']).read_bytes()).hexdigest().lower() == row['sha256'].lower()
subprocess.run([sys.executable, '-B', str(W / 'capture_pilot_progress.py'), '--name', a.name,
 '--expected-head', a.expected_head, '--detail', a.detail], check=True)
plan = json.loads((P / 'git_plan.json').read_text())

def add(source, target, freeze=False):
    data = source.read_bytes()
    if freeze:
        dest = P / 'frozen' / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as handle: handle.write(data)
        assert source.read_bytes() == data
        source = dest
    row = {'local_absolute_path': str(source), 'target': target, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if target.endswith('.gz'): row['transport_encoding'] = 'base64'
    plan['files'].append(row)

for source in sorted((G / 'pilot_output/trees').glob(a.marker + '.*')):
    add(source, source.relative_to(G).as_posix(), True)
alignment = G / 'pilot_output/alignments' / (a.marker + '_aligned.fasta')
add(alignment, alignment.relative_to(G).as_posix(), True)
for source in sorted(a.receipt.parent.iterdir()):
    if source.is_file():
        add(source, 'reports/stage01/local_pilot_20261010/marker' + f'{a.validated_count:02d}' + '/' + source.name)
add(a.prior_readback, 'reports/stage01/local_pilot_20261010/progress/' + a.prior_readback.parent.name + '/remote_readback.json')
if a.observation:
    add(a.observation, 'reports/stage01/local_pilot_20261010/progress/' + a.name + '/process_observation.json')
add(Path(__file__), 'scripts/master_run/publish_completed_pilot_marker.py')
plan['message'] = 'Publish validated ' + a.marker + ' pilot gene tree and native recovery evidence'
assert len({r['target'] for r in plan['files']}) == len(plan['files'])
with (P / 'git_plan_science.json').open('x') as f: json.dump(plan, f, indent=2)
print(json.dumps({'files': len(plan['files']), 'completed_validated_markers': a.validated_count, 'pilot_complete': False}))
