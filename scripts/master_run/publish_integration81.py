from pathlib import Path
import hashlib, json, subprocess, sys, zipfile
W = Path(__file__).resolve().parent
G = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
R = G / 'reports/stage01/itol_api_20261010'
P = W / 'local_integration81'
tests = W / 'pipeline_validation_tests01/run03'
api_tests = W / 'itol_api_tests02/fixtures_run01'
validation = json.loads((tests / 'results.json').read_text())
api = json.loads((api_tests / 'results.json').read_text())
assert validation['all_passed'] and api['all_passed']
assert hashlib.sha256((G / 'scripts/validate_pipeline.py').read_bytes()).hexdigest() == validation['validator_source_sha256_after']['validate_pipeline.py']
assert hashlib.sha256((G / 'scripts/upload_itol.py').read_bytes()).hexdigest() == api['source_sha256']
assert json.loads((W / 'local_pilot80/remote_readback.json').read_text())['state'] == 'PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED'
subprocess.run([sys.executable, '-B', str(W / 'capture_pilot_progress.py'), '--name', P.name,
 '--expected-head', '4845082d01085f51fa71cf2d3bc76ba67bf45dc7', '--detail',
 'Two of five pilot markers validated; ATP-synt is running. Explicit pilot/full validation passed8 isolated WSL fixture cases including truncation detection and missing-locus taxon unions. Direct iTOL integration passed12 offline mocked API cases and is staged for installation after pilot closure. No real upload, production tree, or defense dataset yet. Active Bash source is unchanged.'], check=True)
plan = json.loads((P / 'git_plan.json').read_text())
def add(source, target):
    data = source.read_bytes()
    row = {'local_absolute_path': str(source), 'target': target, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if source.suffix == '.zip': row['transport_encoding'] = 'base64'
    plan['files'].append(row)
for rel in ['scripts/validate_pipeline.py', 'scripts/upload_itol.py', 'scripts/requirements-itol.txt',
 '.github/copilot-instructions.md', 'reports/stage01/local_pilot_20261010/REVIEW_CRITERIA.md']:
    add(G / rel, rel)
for source in sorted(R.iterdir()):
    if source.is_file(): add(source, source.relative_to(G).as_posix())
base = 'reports/stage01/itol_api_20261010/'
add(tests / 'results.json', base + 'validation_tests/results.json')
add(W / 'pipeline_validation_tests01/run_validation_tests.py', 'scripts/tests/test_pipeline_validation.py')
for source in sorted((tests / 'reports').rglob('*')):
    if source.is_file(): add(source, base + 'validation_tests/reports/' + source.relative_to(tests / 'reports').as_posix())
add(api_tests / 'results.json', base + 'api_tests/results.json')
add(W / 'itol_api_tests02/test_upload.py', 'scripts/tests/test_itol_upload.py')
for folder, filename in [(W / 'pipeline_validation_tests01', 'synthetic_validation_fixtures.zip'),
                         (W / 'itol_api_tests02', 'synthetic_api_fixtures.zip')]:
    dest = P / filename
    with zipfile.ZipFile(dest, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(folder.rglob('*')):
            if source.is_file() and '__pycache__' not in source.parts:
                archive.write(source, source.relative_to(folder).as_posix())
    add(dest, base + 'tests/' + filename)
receipt = {'active_pipeline_script_unchanged_sha256': hashlib.sha256((G / 'run_pipeline.sh').read_bytes()).hexdigest(),
 'candidate_sha256': hashlib.sha256((R / 'run_pipeline.with_validation_itol.sh').read_bytes()).hexdigest(),
 'bash_syntax_check': 'PASS via local WSL bash -n',
 'python_compile_check': 'PASS via local phylogeny Python, no bytecode files written',
 'validation_cases': len(validation['cases']), 'api_cases': len(api['cases']),
 'candidate_activated': False, 'real_itol_upload': False, 'full_pipeline_started': False}
with (P / 'integration_receipt.json').open('x') as f: json.dump(receipt, f, indent=2)
add(P / 'integration_receipt.json', base + 'integration_receipt.json')
add(W / 'local_pilot80/remote_readback.json', 'reports/stage01/local_pilot_20261010/progress/local_pilot80/remote_readback.json')
add(W / 'prepare_integration80.py', 'scripts/master_run/prepare_integration80.py')
add(Path(__file__), 'scripts/master_run/publish_integration81.py')
plan['message'] = 'Add tested explicit-scope validation and staged authenticated iTOL upload integration'
assert len({r['target'] for r in plan['files']}) == len(plan['files'])
with (P / 'git_plan_integration.json').open('x') as f: json.dump(plan, f, indent=2)
print(json.dumps({'files': len(plan['files']), 'bytes': sum(r['bytes'] for r in plan['files']), **receipt}))
