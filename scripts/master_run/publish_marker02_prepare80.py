from pathlib import Path
import hashlib, json, subprocess, sys
W = Path(__file__).resolve().parent
G = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
P = W / 'local_pilot80'
review = W / 'pilot_marker02_validation81'
receipt = json.loads((review / 'marker02_v2_validation.json').read_text())
assert receipt['status'] == 'PASS'
for row in receipt['evidence'].values():
    if isinstance(row, dict) and 'path' in row and 'sha256' in row:
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest().lower() == row['sha256'].lower()
subprocess.run([sys.executable, '-B', str(W / 'capture_pilot_progress.py'), '--name', P.name,
 '--expected-head', 'e4487917a8e59135c24d267bfc12c9f5c4e5fe38', '--detail',
 'Pilot markers1 and2 completed and independently validated. ADK has196 exact unique tips,224 alignment columns,WAG+I+G4,1000 UFBoot replicates,150 numeric supports6-100 and43 explicitly unlabeled internal branches. Its native completion was07:53:10 UTC. ATP-synt is now running; ASTRAL and full pipeline have not run. The v2 validator records native unlabeled supports without imputation.'], check=True)
plan = json.loads((P / 'git_plan.json').read_text())
def add(source, target, freeze=False):
    data = source.read_bytes()
    if freeze:
        dest = P / 'frozen' / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as f: f.write(data)
        assert source.read_bytes() == data
        source = dest
    row = {'local_absolute_path': str(source), 'target': target, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if target.endswith('.gz'): row['transport_encoding'] = 'base64'
    plan['files'].append(row)
for source in sorted((G / 'pilot_output/trees').glob('ADK.*')):
    add(source, source.relative_to(G).as_posix(), True)
aln = G / 'pilot_output/alignments/ADK_aligned.fasta'
add(aln, aln.relative_to(G).as_posix(), True)
for folder, name in ((review, 'marker02'), (W / 'pilot_marker01_validation_v2', 'marker01_v2')):
    for source in sorted(folder.iterdir()):
        if source.is_file(): add(source, 'reports/stage01/local_pilot_20261010/' + name + '/' + source.name)
add(W / 'validate_five_marker_pilot_v2.py', 'scripts/master_run/validate_five_marker_pilot_v2.py')
add(W / 'local_pilot79/remote_readback.json', 'reports/stage01/local_pilot_20261010/progress/local_pilot79/remote_readback.json')
add(Path(__file__), 'scripts/master_run/publish_marker02_prepare80.py')
plan['message'] = 'Publish validated ADK pilot tree and preserve unlabeled native support evidence'
assert len({r['target'] for r in plan['files']}) == len(plan['files'])
with (P / 'git_plan_science.json').open('x') as f: json.dump(plan, f, indent=2)
print(json.dumps({'files': len(plan['files']), 'completed_validated_markers': 2, 'pilot_complete': False}))
