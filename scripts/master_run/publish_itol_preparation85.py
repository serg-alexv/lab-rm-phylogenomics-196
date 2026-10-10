"""Publish reviewed iTOL source and observed preparation results, without ref changes."""
from pathlib import Path
import base64
import csv
import datetime
import hashlib
import json
import subprocess

W = Path(__file__).resolve().parent
G = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
P = W / 'local_itol_prepare85'
R = G / 'reports/stage01/itol_pilot_20261010'
EXPECTED = 'ea1f094cb4a976ce3d95a855b3dea26c3c577394'
assert not P.exists()
upload_terminal = json.loads((G / 'pilot_output/itol/terminal.json').read_text())
assert upload_terminal['tree_url'] is None and not upload_terminal['exports']
assert 'No valid subscription' in upload_terminal['error']
assert not (G / 'cell_mapping.tsv').exists()
assert hashlib.sha256((G / 'scripts/prep_itol_files.py').read_bytes()).hexdigest() == 'a54b7fac63541366156b86a9564f14b2478ad33a20487f662b94dea53fbcff10'
assert hashlib.sha256((G / 'scripts/upload_itol_pilot_account.py').read_bytes()).hexdigest() == 'bab451f2bd4b36c2bb6531b2fcd4a8cc440d8cda90ed3fc08de7c9498d909bcb'
assert hashlib.sha256((G / 'run_pipeline.sh').read_bytes()).hexdigest() == '5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b'
host_audit = json.loads((W / 'itol_raw_data_audit85/audit.json').read_text())
host_table = W / 'itol_raw_data_audit85/host_metadata_raw.tsv'
assert hashlib.sha256(host_table.read_bytes()).hexdigest() == host_audit['output']['sha256']
with host_table.open(encoding='utf-8', newline='') as handle:
    host_rows = list(csv.DictReader(handle, delimiter='\t'))
approved_ids = set((G / 'config/approved_accessions.txt').read_text().split())
assert len(host_rows) == len(approved_ids) == 196
assert {row['assembly_accession'] for row in host_rows} == approved_ids
for row in host_rows:
    native_bytes = (G / row['source_report_relative_path']).read_bytes()
    assert hashlib.sha256(native_bytes).hexdigest() == row['source_report_sha256']
    native = json.loads(native_bytes.decode().splitlines()[int(row['source_report_selected_record_line']) - 1])
    assert native['currentAccession'] == row['assembly_accession']
    sample = native.get('assemblyInfo', {}).get('biosample', {})
    for field, column in [('host', 'biosample_host_raw'), ('isolationSource', 'biosample_isolation_source_raw'), ('hostDisease', 'biosample_hostDisease_raw')]:
        assert (sample.get(field) or '') == row[column]
P.mkdir()

def new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode('utf-8'))

files = []

def add(source, target):
    data = source.read_bytes()
    frozen = P / 'frozen' / target
    new(frozen, data)
    row = {'local_absolute_path': str(frozen), 'target': target,
           'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if source.suffix.lower() in {'.zip', '.gz', '.pdf', '.png'}:
        row['transport_encoding'] = 'base64'
    files.append(row)

summary = {
    'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'pilot_state': 'COMPLETE_VALIDATED_AND_REMOTE_BYTES_VERIFIED',
    'pilot_commit': EXPECTED, 'marker_count': 5, 'astral_tip_count': 196,
    'upload_attempt01': {'exit_code': 1, 'http_started': False,
                         'error': 'Pilot iTOL preflight: Expected one nonempty iTOL token'},
    'credential_format_resolution': 'User confirmed username on line 1 and API key on line 2; structure verified without exposing values. New separate client accepts this format; original client and credential file unchanged.',
    'upload_attempt02': {'exit_code': 1, 'http_started': True,
                         'state': 'REJECTED_NO_VALID_SUBSCRIPTION',
                         'tree_url': None, 'exports': {}, 'error': upload_terminal['error']},
    'toolkit': 'itolapi==4.1.6 installed locally in phylogeny',
    'decoration_state': 'BLOCKED_DEFENSE_DETECTORS_NOT_RUN',
    'host_metadata_state': 'NCBI_REPORTS_AVAILABLE_RAW_HOST_AND_ISOLATION_SOURCE_EXTRACTED_SEPARATELY',
    'host_metadata_independent_readback': 'PASS_196_EXACT_APPROVED_IDS_ALL_SOURCE_HASHES_AND_RAW_FIELDS',
    'provided_prep_script': 'Saved byte-for-byte; syntax compile exit 0; isolated valid and malformed fixtures tested. Not executed on project data.',
    'provided_prep_script_limits': ['does not validate exact header or binary values', 'can return success after malformed/empty data', 'overwrites existing fixed-name outputs', 'host palette repeats after eight categories'],
    'scientific_outputs_changed': False, 'full_pipeline_started': False,
    'forbidden_validator_accessed': False,
}
new(R / 'preparation_status85.json', json.dumps(summary, indent=2) + '\n')
new(R / 'host_extraction_preparation_history.json', json.dumps({
    'initial_attempt': {'state': 'FAILED_BEFORE_RESULT_WRITES', 'exit_code': None,
                        'exit_code_evidence': 'not retained',
                        'exception': 'ValueError: GCF_000148815.2: expected one JSONL report record, found 2'},
    'resolution': 'Select the exact-accession record among records with matching currentAccession; retain all older alias record provenance.',
    'final_attempt': 'COMPLETED_196_ROWS_WITH_INDEPENDENT_SOURCE_READBACK',
    'scientific_input_or_output_changed': False,
}, indent=2) + '\n')
new(R / 'PREPARATION85.md', '''# iTOL pilot preparation and first preflight result

The five-marker pilot remains complete and independently validated: five gene
trees, 196 unique approved ASTRAL tips, and 193 informative splits. Its 81 published
files were independently read back and SHA-256 verified at ea1f094cb4a976ce3d95a855b3dea26c3c577394.
Raw scientific outputs, the original runner, and the original workflow lock remain unchanged.

The first upload client stopped before any HTTP request because it expected one
token in the local credential file. The user clarified the actual two-line format:
username, then API key. Only structure was reported; neither value is published.
The separate upload_itol_pilot_account.py client selects the second line. The original
client and credential file remain intact. The corrected client made one real request;
iTOL rejected it with ERR 0: No valid subscription detected for API key [REDACTED].
No tree URL or SVG/PDF export was created. Both attempts and the upload package
are preserved; further attempts require resolution of the account's batch API access.

The official endpoints are https://itol.embl.de/batch_uploader.cgi and
https://itol.embl.de/batch_downloader.cgi. The upload uses APIkey and zipFile;
SVG/PDF export uses the installed itolapi 4.1.6 writer with checked HTTP responses.
Documentation: https://itol.embl.de/help.cgi#batch and https://github.com/albertyw/itolapi.
The uploaded tree will be explicitly named as a five-marker pilot. Numeric internal
labels use q1 quartet frequencies; raw structured ASTRAL annotations remain preserved.

The user-provided scripts/prep_itol_files.py is preserved byte-for-byte. Its syntax
compiles and valid synthetic input generates the expected tab-separated templates.
It does not validate the schema, uniqueness, binary values or tree membership, and
its error and overwrite behavior require independent input checks before real use.
No canonical cell_mapping.tsv exists. Real NCBI source metadata was located for
the approved panel and is preserved separately without invented host categories.
Stage 5 production defense detection is NOT_RUN; no defensible six-system matrix
can be merged. Missing or unfinished detection is not biological absence.
The historical mapping under a synthetic
Stage 6 render directory is drawing geometry for test accessions, not biological
defense or host evidence. No decoration data has been fabricated or generated.

Full 100-marker execution remains unapproved. scripts/validate_pipeline.py was
not accessed or changed. The completed-pilot follow-up remains paused.
''')

for name in ['upload_itol_pilot.py', 'upload_itol_pilot_account.py', 'prep_itol_files.py']:
    add(G / 'scripts' / name, 'scripts/' + name)
for source in sorted(R.rglob('*')):
    if source.is_file():
        add(source, source.relative_to(G).as_posix())
for source in sorted((G / 'pilot_output/itol').iterdir()):
    if source.is_file():
        add(source, source.relative_to(G).as_posix())
for folder, target in [
    ('itol_pilot_upload_tests84', 'uploader_offline_tests'),
    ('itol_prep_attachment_tests85', 'provided_prep_script_tests'),
    ('itol_account_tests85', 'account_format_tests'),
    ('itol_raw_data_audit85', 'raw_data_audit'),
]:
    directory = W / folder
    assert directory.is_dir(), folder
    for source in sorted(directory.iterdir()):
        if source.is_file() and source.suffix in {'.json', '.py', '.md', '.txt', '.tsv'}:
            add(source, 'reports/stage01/itol_pilot_20261010/' + target + '/' + source.name)
add(W / 'local_pilot_complete84/remote_readback.json', 'reports/stage01/local_pilot_20261010/completed/remote_readback.json')
base = json.loads(subprocess.run(['gh', 'api', 'repos/serg-alexv/lab-rm-phylogenomics-196/contents/STATUS.md?ref=' + EXPECTED], capture_output=True, check=True).stdout)
previous = base64.b64decode(base['content']).decode()
status = '''# Current request: validated pilot and iTOL preparation

PILOT_COMPLETE_VALIDATED: five gene trees, 196 ASTRAL tips, 193 informative splits;
published bytes independently verified. First iTOL upload stopped before HTTP due
to a credential-format mismatch. The corrected two-line account reader made one real
request, rejected by iTOL for no valid subscription. No tree URL or exports exist.
Real NCBI host metadata was recovered, but Stage 5 defense detection is NOT_RUN.
No complete host/defense matrix can be generated from the available evidence.
The user-supplied prep_itol_files.py is preserved and syntax-tested; no project data
was processed. Full 100-marker execution remains unapproved. See
[iTOL preparation](reports/stage01/itol_pilot_20261010/PREPARATION85.md) and
[completed pilot](reports/stage01/local_pilot_20261010/completed/RESULT.md).

''' + previous
new(P / 'STATUS.md', status)
add(P / 'STATUS.md', 'STATUS.md')
add(Path(__file__), 'scripts/master_run/publish_itol_preparation85.py')
assert len(files) == len({row['target'] for row in files})
credential_lines = Path(r'C:\itol.api-key.txt').read_text(encoding='utf-8-sig').splitlines()
assert len(credential_lines) == 2 and all(value.strip() for value in credential_lines)
for row in files:
    candidate = Path(row['local_absolute_path']).read_bytes()
    assert all(value.strip().encode() not in candidate for value in credential_lines), 'Credential scan failed: ' + row['target']
new(P / 'git_plan.json', json.dumps({'expected_head': EXPECTED,
    'message': 'Preserve iTOL pilot preflight, tested clients and exact supplied decoration script',
    'files': files}, indent=2) + '\n')
print(json.dumps({'files': len(files), 'bytes': sum(row['bytes'] for row in files)}))
