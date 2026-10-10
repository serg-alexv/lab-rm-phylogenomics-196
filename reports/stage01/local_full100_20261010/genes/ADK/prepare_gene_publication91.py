"""Hash-bound publication of completed ADK results; no active-locus artifacts."""
import csv
import gzip
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
OUT = WORK / 'full100_gene_publication91'
VALID = WORK / 'full100_gene_validation90/ADK_strict'
BASE = '1b4240e7b29a472fdc42be2666d97b1c5e8eea82'
TARGET = 'reports/stage01/local_full100_20261010/genes/ADK'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def fresh(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)

audit = json.loads((VALID / 'audit.json').read_text())
receipt = json.loads((VALID / 'execution_receipt.json').read_text())
assert audit['state'] == receipt['state'] == 'PASS' and receipt['native_exit_code'] == 0
assert not audit['errors'] and audit['marker'] == 'ADK'
assert audit['accepted_alignment_manifest_sha256'] == 'fed471c8d2ce1753c9e4e592873df300d3ba91a581d4a2d202a9860562a7b11a'
assert receipt['source_sha256'] == '3a0473c06478dbfa43589c7f8c7772d3488c90a277f074685dfa3bc12add98c3'
assert digest((WORK / 'full100_gene_validation90/audit_completed_locus.py').read_bytes()) == receipt['source_sha256']
for row in receipt['output_artifacts']:
    assert digest(Path(row['path']).read_bytes()) == row['sha256']
assert audit['input_records'] == 196 and audit['alignment_columns'] == 224
assert audit['marker_file_set_stable_before_after'] and audit['bootstrap']['bootstrap_trees_in_consensus_report'] == 1000
observation = json.loads((OUT / 'phase_observation.json').read_text())
assert observation['pipeline_sha256'] == '5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b'
assert observation['linux']['boot_id'] == '8cca020a-71b2-4163-92dc-6087df12dd45'
assert not observation['terminal_receipt_present'] and not observation['linux_terminal_receipt_present']
assert any(p['pid'] == 15624 and p['start_ticks'] == 2178131 and p['parent_pid'] == 4023 for p in observation['linux']['processes'])
with (VALID / 'file_manifest.tsv').open(newline='') as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))
assert len(rows) == 12 and all(r['stable'].lower() == 'true' for r in rows)
manifest = {r['filename']: r for r in rows}
native = sorted((ROOT / 'pipeline_output/trees').glob('ADK.*'))
assert len(native) == 10 and all(p.name in manifest for p in native)
previous = json.loads((WORK / 'full100_gene_publication90/remote_readback.json').read_text())
assert previous['state'] == 'PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and previous['expected_commit'] == BASE

now = datetime.now(timezone.utc).isoformat()
status = (WORK / 'full100_gene_publication90/STATUS_root.md').read_text()
status = re.sub(r'Updated .*?\. The user-approved', 'Updated ' + now + '. The user-approved', status, count=1)
status = re.sub(r'\| Full-run IQ-TREE \|.*?\|', '| Full-run IQ-TREE | 2/100 COMPLETE_VALIDATED: `5-FTHF_cyc-lig` and `ADK`; `ATP-synt_A` running, 97 pending at 10:51 UTC observation |', status, count=1)
begin = status.index('The same full run remains active')
end = status.index('\n\n\nPilot visualization:', begin)
status = status[:begin] + f'''ADK finished natively at 2026-10-10T10:49:04Z and passed the same independent local WSL audit: 196 exact input taxa in each tree, 224 alignment columns, and 1,000 consensus bootstrap trees reported natively. Both trees have 150 numeric support labels and 44 unlabeled internal nodes. WAG+I+G4 was selected by BIC. Native warnings concerning 305 parameters versus 224 sites and 24 near-zero internal branches are retained. See [ADK results]({TARGET}/RESULT.md) and [its validation receipt]({TARGET}/validation/execution_receipt.json).

The original full run was observed active at 10:51:26 UTC under Windows owner 31816, wrapper bash 4019 and pipeline bash 4023, all with their original creation identities. Child IQ-TREE PID 15624, start ticks 2178131, parent 4023, was computing ATP-synt_A with the approved two-thread command. The unchanged script SHA256 is `5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b`. Overall terminal receipts were absent. The protected validator remains untouched. Both prior milestones were independently verified from GitHub: 115 alignment-publication files and 33 first-locus files; their verification receipts are retained.
''' + status[end:]
begin = status.index('Completed first-locus outputs and checkpoint/model files')
status = status[:begin] + '''The two completed loci and their original model/checkpoint files are preserved. This update includes only completed ADK artifacts; active ATP-synt_A artifacts are excluded. The publisher checks this commit's remote bytes after advancing main. Earlier evidence remains in Git history. No new pipeline was started and no scientific output was overwritten.
'''
fresh(OUT / 'STATUS_root.md', status)

fresh(OUT / 'RESULT.md', '''# Full-run gene tree: ADK

State: COMPLETE_VALIDATED. Native completion was 2026-10-10T10:49:04Z. The same set-e pipeline advanced to ATP-synt_A, confirming this locus completed while the full run remains open.

Independent validation ran locally in Ubuntu WSL with the previously compiled and fixture-tested scripts/master_run/audit_completed_locus.py, unchanged at SHA256 3a0473c06478dbfa43589c7f8c7772d3488c90a277f074685dfa3bc12add98c3. See validation/execution_receipt.json for invocation, exit 0 and exact output hashes. The already accepted alignment manifest is pinned; the full alignment phase was not repeated.

| Check | Result |
|---|---|
| Input/alignment | 196 records, 224 columns, exact per-ID ungapped sequences |
| ML and consensus trees | Each has exactly all 196 input taxa; no duplicate, missing or extra tips |
| Selected model | WAG+I+G4, chosen by BIC |
| Bootstrap | Native reports state 1,000 requested and 1,000 consensus bootstrap trees |
| Numeric support | 150 labels each; ML 9-100, consensus 33-100 |
| Unlabeled internal nodes | 44 in each tree, including root; preserved without invented support |
| Native reduced data | 153 PHYLIP/split taxa, 806 splits; exact representative IDs and aligned sequences |
| Distinct exact aligned strings | 121; separate from the 153 native retained representatives |
| Total runtime | CPU 1161.243 seconds; wall 585.288 seconds |
| Stable artifacts | 12 audited: input, alignment and 10 native output files |

The approved IQ-TREE command does not save a separate .ufboot file, so the replicate count comes from the completed native report rather than independently counted replicate trees. All 196 taxa are restored in final tree outputs despite native identical-sequence reduction.

Native warnings are preserved verbatim: K=305 parameters versus n=224 sites, and 24 near-zero internal branches. These are computational integrity results; they do not establish strong biological resolution of this short locus.

The ten completed ADK artifacts include original model and checkpoint gzip files. No active ATP-synt_A scientific artifacts are published in this step. The process observation establishes the same original pipeline lineage; overall terminal/lock closure is still pending. ASTRAL awaits all 100 completed gene trees. The protected validator, pipeline source and scientific outputs were not modified.
''')

files = []
def add(path, target, expected=None):
    data = path.read_bytes()
    value = digest(data)
    if expected is not None:
        assert value == expected.lower(), target
    assert len(data) < 5 * 1024 * 1024, target
    binary = path.name.endswith('.gz')
    text = (gzip.decompress(data) if binary else data).decode('utf-8')
    assert not re.search(r'ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----', text), target
    row = dict(local_absolute_path=str(path), target=target, bytes=len(data), sha256=value)
    if binary:
        row['transport_encoding'] = 'base64'
    files.append(row)

for path in native:
    row = manifest[path.name]
    assert path.stat().st_size == int(row['bytes_after'])
    add(path, 'pipeline_output/trees/' + path.name, row['sha256_after'])
for path in (ROOT / 'input_genes/ADK.fasta', ROOT / 'pipeline_output/alignments/ADK_aligned.fasta'):
    assert digest(path.read_bytes()) == manifest[path.name]['sha256_after']
for name in ('audit.json', 'execution_receipt.json', 'file_manifest.tsv', 'native_warnings.txt'):
    add(VALID / name, TARGET + '/validation/' + name)
add(OUT / 'STATUS_root.md', 'STATUS.md')
add(OUT / 'RESULT.md', TARGET + '/RESULT.md')
add(Path(__file__), TARGET + '/prepare_gene_publication91.py')
for name in ('observe_phase91.ps1', 'phase_observation.json'):
    add(OUT / name, TARGET + '/' + name)
add(WORK / 'full100_gene_publication90/remote_readback.json', TARGET + '/previous_gene_remote_readback.json')
assert len({r['target'] for r in files}) == len(files)
fresh(OUT / 'git_plan.json', json.dumps(dict(expected_head=BASE, message='Validate and publish ADK gene tree; record 2 of 100 loci complete', files=files), indent=2) + '\n')
print(json.dumps(dict(state='PREPARED_HASH_VERIFIED', files=len(files), bytes=sum(r['bytes'] for r in files), expected_head=BASE)))
