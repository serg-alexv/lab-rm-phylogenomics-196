"""Publish only the completed first locus and its independent integrity evidence."""
import csv
import gzip
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
OUT = WORK / 'full100_gene_publication90'
VALID = WORK / 'full100_gene_validation90'
STRICT = VALID / '5-FTHF_cyc-lig_strict'
BASE = '09ef14733d0acf71a6842cf208732c1a52700f4f'
TARGET = 'reports/stage01/local_full100_20261010/genes/5-FTHF_cyc-lig'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def fresh(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)

audit = json.loads((STRICT / 'audit.json').read_text())
receipt = json.loads((STRICT / 'execution_receipt.json').read_text())
assert audit['state'] == receipt['state'] == 'PASS'
assert not audit['errors'] and not receipt['errors']
assert receipt['native_exit_code'] == receipt['strict_compile_native_exit_code'] == receipt['parser_fixture_native_exit_code'] == 0
assert receipt['source_sha256'] == '3a0473c06478dbfa43589c7f8c7772d3488c90a277f074685dfa3bc12add98c3'
assert digest((VALID / 'audit_completed_locus.py').read_bytes()) == receipt['source_sha256']
assert audit['accepted_alignment_manifest_sha256'] == 'fed471c8d2ce1753c9e4e592873df300d3ba91a581d4a2d202a9860562a7b11a'
assert audit['input_records'] == 189 and audit['marker_file_set_stable_before_after']
assert audit['bootstrap']['bootstrap_trees_in_consensus_report'] == 1000
observation = json.loads((OUT / 'phase_observation.json').read_text())
assert observation['pipeline_sha256'] == '5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b'
assert not observation['terminal_receipt_present'] and not observation['linux_terminal_receipt_present']
assert any(p['pid'] == 15548 and p['start_ticks'] == 2119388 and p['parent_pid'] == 4023 for p in observation['linux']['processes'])
with (STRICT / 'file_manifest.tsv').open(newline='') as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))
assert len(rows) == 12 and all(r['stable'].lower() == 'true' for r in rows)
manifest = {r['filename']: r for r in rows}
native = sorted((ROOT / 'pipeline_output/trees').glob('5-FTHF_cyc-lig.*'))
assert len(native) == 10 and all(p.name in manifest for p in native)

now = datetime.now(timezone.utc).isoformat()
status = (WORK / 'full100_alignment_publication89/STATUS_root.md').read_text()
status = re.sub(r'Updated .*?\. The user-approved', 'Updated ' + now + '. The user-approved', status, count=1)
old = '| Full-run IQ-TREE | RUNNING: first marker `5-FTHF_cyc-lig`, ModelFinder; no completed gene tree at observation |'
assert old in status
status = status.replace(old, '| Full-run IQ-TREE | 1/100 COMPLETE_VALIDATED: `5-FTHF_cyc-lig`; `ADK` running, 98 pending at 10:45 UTC observation |')
old_start = status.index('The full run began at ')
old_end = status.index('\n\nPilot visualization:', old_start)
status = status[:old_start] + f'''The first locus finished natively at 2026-10-10T10:39:17Z and passed independent local WSL validation. Its final tree and consensus each contain exactly the 189 taxa in that locus's input, with 1,000 bootstrap trees reported by IQ-TREE. Each has 153 numeric support labels in range 0-100 and 34 unlabeled internal nodes, which remain unlabeled. Native warnings about 338 parameters versus 210 sites and 17 near-zero internal branches are preserved. See [first-locus results]({TARGET}/RESULT.md) and [validation receipt]({TARGET}/validation/execution_receipt.json).

The same full run remains active under its original workflow lock. At 10:45:05 UTC, Windows owner 31816, wrapper bash 4019 and pipeline bash 4023 retained their original creation identities; IQ-TREE PID 15548 (start ticks 2119388, parent 4023) was computing ADK. The unchanged script SHA256 is `5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b`; the active command uses `-m MFP -bb 1000 -nt 2 -mem 3000M`. Full-run terminal receipts remain absent. The protected validator is untouched. All 115 files from the completed alignment publication were independently read back with matching hashes; its receipt is included in this update.
''' + status[old_end:]
last = status.index('This update replaces stale top-level')
status = status[:last] + '''Completed first-locus outputs and checkpoint/model files are preserved unchanged. No active ADK outputs are included. Scientific completion and remote byte verification are separate: the publisher verifies this commit after advancing main. Earlier status and evidence remain in Git history. No new pipeline was started and no scientific output was overwritten.
'''
fresh(OUT / 'STATUS_root.md', status)

result = '''# First full-run gene tree: 5-FTHF_cyc-lig

State: COMPLETE_VALIDATED. IQ-TREE finished at 2026-10-10T10:39:17Z; the original set-e pipeline advanced to ADK. This establishes per-locus completion, not overall process or lock closure.

The independent Python audit ran locally in Ubuntu WSL and exited 0. It checked the exact locus input, alignment, final tree, consensus, reduced PHYLIP sequences, split file, native report/log and stable hashes. Its source hash and invocation are in validation/execution_receipt.json. The alignment manifest is pinned to the already accepted all-100-locus audit; that phase was not repeated.

| Check | Result |
|---|---|
| Input and alignment | 189 records; 210 aligned columns; exact IDs and ungapped sequences |
| ML tree and consensus tips | 189 each; zero missing, extra or duplicate taxa |
| Selected model | Q.PFAM+F+R6 (BIC) |
| Bootstrap | 1,000 requested and 1,000 used in consensus, according to native report |
| Numeric support labels | 153 in each tree; ML 5-100, consensus 6-100 |
| Unlabeled internal nodes | 34 in each tree, including root; left unchanged |
| Reduced native data | 156 PHYLIP/split taxa and 897 splits; exact representative IDs and sequences |
| Literal distinct aligned strings | 129; this differs from the 156 native retained representatives |
| Native total runtime | CPU 3918.038 seconds; wall 1968.485 seconds |
| Stable files audited | 12: input, alignment and 10 native artifacts |

The default approved command did not retain a separate .ufboot file. The replicate count is established by the native completion report, not an independent count of stored replicate trees. The reduced PHYLIP/splits use fewer representatives; the final tree and consensus restore all 189 input taxa. Seven of the approved 196 genomes lack this locus in the staged data, as already recorded by the input audit.

Native warnings are retained verbatim in validation/native_warnings.txt and the original report: parameter count K=338 exceeds site count n=210, and 17 near-zero internal branches require caution. Passing integrity checks does not establish that this individual short locus strongly resolves species relationships.

The separate audit parser was compiled and exercised with valid and malformed fixtures (missing semicolon, unterminated quote, nonfinite and negative branch lengths). The initial audit and source are retained under preliminary/; validation/ contains the final strict receipt. The main pipeline, scientific results and protected validator were not modified.

Publication includes only this completed prefix, its validation evidence, the observed transition to ADK and the previous alignment publication's verified remote hashes. Active ADK artifacts are excluded. ASTRAL remains pending all 100 completed gene trees.
'''
fresh(OUT / 'RESULT.md', result)

files = []
def add(local, target, expected=None):
    data = local.read_bytes()
    value = digest(data)
    if expected is not None:
        assert value == expected.lower(), target
    assert len(data) < 5 * 1024 * 1024, target
    binary = local.name.endswith('.gz')
    text = (gzip.decompress(data) if binary else data).decode('utf-8')
    assert not re.search(r'ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----', text), target
    row = dict(local_absolute_path=str(local), target=target, bytes=len(data), sha256=value)
    if binary:
        row['transport_encoding'] = 'base64'
    files.append(row)

for path in native:
    row = manifest[path.name]
    assert path.stat().st_size == int(row['bytes_after'])
    add(path, 'pipeline_output/trees/' + path.name, row['sha256_after'])
for path in (ROOT / 'input_genes/5-FTHF_cyc-lig.fasta', ROOT / 'pipeline_output/alignments/5-FTHF_cyc-lig_aligned.fasta'):
    assert digest(path.read_bytes()) == manifest[path.name]['sha256_after']
add(OUT / 'STATUS_root.md', 'STATUS.md')
add(OUT / 'RESULT.md', TARGET + '/RESULT.md')
add(Path(__file__), TARGET + '/prepare_gene_publication90.py')
add(VALID / 'audit_completed_locus.py', 'scripts/master_run/audit_completed_locus.py', receipt['source_sha256'])
for name in ('audit.json', 'execution_receipt.json', 'file_manifest.tsv', 'native_warnings.txt'):
    add(STRICT / name, TARGET + '/validation/' + name)
    add(VALID / '5-FTHF_cyc-lig' / name, TARGET + '/preliminary/' + name)
for path in sorted((VALID / 'parser_fixtures').iterdir()):
    if path.is_file():
        add(path, TARGET + '/parser_fixtures/' + path.name)
add(VALID / 'before_reviewcopy/audit_completed_locus.py', TARGET + '/preliminary/audit_completed_locus.py')
for name in ('observe_phase90.ps1', 'phase_observation.json'):
    add(OUT / name, TARGET + '/' + name)
add(WORK / 'full100_alignment_publication89/remote_readback.json', TARGET + '/previous_alignment_remote_readback.json')
assert len({r['target'] for r in files}) == len(files)
plan = dict(expected_head=BASE, message='Validate and preserve first full-run gene tree; record ADK inference in progress', files=files)
fresh(OUT / 'git_plan.json', json.dumps(plan, indent=2) + '\n')
print(json.dumps(dict(state='PREPARED_HASH_VERIFIED', expected_head=BASE, files=len(files), bytes=sum(r['bytes'] for r in files))))
