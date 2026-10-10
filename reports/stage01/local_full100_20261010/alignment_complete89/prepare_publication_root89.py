"""Prepare a bounded, hash-bound publication of the completed MAFFT phase."""
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
OUT = WORK / 'full100_alignment_publication89'
VALID = WORK / 'full100_alignment_validation89'
BASE = '06918f30a83fb620908b0d29c34e688d8f69a890'
TARGET = 'reports/stage01/local_full100_20261010/alignment_complete89'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def fresh(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)

audit = json.loads((VALID / 'bound_validation/audit.json').read_text())
receipt = json.loads((VALID / 'bound_validation/receipt.json').read_text())
assert audit['state'] == receipt['state'] == 'PASS'
assert receipt['native_exit_code'] == 0
assert audit['observed_alignment_markers'] == 100
assert audit['observed_records'] == 19359 and audit['observed_accession_union'] == 196
assert audit['accepted_input_audit_sha256'] == 'c4aeb2afea658d5b0c7a1e4fb4e4e8b9a88c41070f9525657b992c8749e09c9c'
assert digest((VALID / 'audit_full100_alignments.py').read_bytes()) == receipt['source_sha256'].lower()
assert digest((VALID / 'bound_validation/audit.json').read_bytes()) == receipt['audit_json_sha256'].lower()
assert digest((VALID / 'bound_validation/per_marker.tsv').read_bytes()) == receipt['per_marker_tsv_sha256'].lower()
with (VALID / 'bound_validation/per_marker.tsv').open(newline='') as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))
assert len(rows) == len({r['marker'] for r in rows}) == 100
assert {p.name for p in (ROOT / 'pipeline_output/alignments').glob('*_aligned.fasta')} == {r['marker'] + '_aligned.fasta' for r in rows}

now = datetime.now(timezone.utc).isoformat()
status = f'''# Current master run status

Updated {now}. The user-approved full 100-marker gene-tree/ASTRAL run is active locally in Ubuntu WSL.

| Component | Verified state |
|---|---|
| Full-run MAFFT alignments | COMPLETE_VALIDATED: 100 loci, 19,359 sequences, exact approved union of 196 genomes; 20,957 columns across loci |
| Full-run IQ-TREE | RUNNING: first marker `5-FTHF_cyc-lig`, ModelFinder; no completed gene tree at observation |
| Full-run ASTRAL | NOT_RUN; waits for all 100 gene trees |
| Five-marker pilot | COMPLETE_VALIDATED: five trees, 196 ASTRAL tips; raw and flat-q1 outputs preserved |
| Historical concatenated primary Stage 4 | Previously COMPLETE_VALIDATED and Release UPLOAD_VERIFIED; accepted outputs preserved |
| Stage 5 defense detection and curation | NOT_RUN |
| Final defense figure and biological review | NOT_RUN; host is not ready to wipe |

All input hashes match the approved manifest. Each alignment preserves its input IDs and exact amino-acid sequence after documented case/whitespace normalization and removal of alignment gaps. All sequences within each locus have equal aligned length; input and output hashes remained stable during the independent WSL audit. See [alignment results]({TARGET}/ALIGNMENT_RESULT.md) and [native audit receipt]({TARGET}/validation/receipt.json).

The full run began at 2026-10-10T09:31:05.9280558Z under the original workflow lock. The unchanged plain Bash script SHA256 is `5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b`. At the phase observation, the same owner and pipeline process identities were present, and IQ-TREE PID 15472 was running with `-m MFP -bb 1000 -nt 2 -mem 3000M`. The IQ-TREE process began at 10:06:25 UTC; native CPU usage subsequently advanced at approximately two cores. Full-run terminal receipts are absent because the pipeline is still running. `scripts/validate_pipeline.py` remains untouched.

Pilot visualization: [PDF](pilot_output/itol_visual_check_20261010/pilot_196_taxa.pdf), [SVG](pilot_output/itol_visual_check_20261010/pilot_196_taxa.svg), and [account tree](https://itol.embl.de/tree/15124432167298281791625397). Both exports contain all 196 labels. The ring represents operational taxonomic groups, not Host or defense calls. iTOL subscription restrictions prevent server-side annotation saving and batch API upload; the account tree is bare after reopening, while local exports preserve the styled draft. The legend overlaps some labels, so the layout remains a draft.

This update replaces stale top-level launch-pending and unapproved-run wording. Earlier evidence is preserved in Git history and [the previous status](https://github.com/serg-alexv/lab-rm-phylogenomics-196/blob/{BASE}/STATUS.md). Scientific completion and GitHub byte verification are separate; the publisher records remote verification after this commit is created. No scientific output was overwritten, no active checkpoint was copied or modified, and no new pipeline was started.
'''
fresh(OUT / 'STATUS_root.md', status)
method = f'''# Full 100-marker alignment acceptance

Independent local WSL validation passed at {audit['finished_utc']} with native exit 0. It checked all 100 selected loci and 19,359 input records, yielding the exact approved union of 196 accessions. Aligned lengths range from 39 to 557 columns, totaling 20,957 columns across loci; this sum is not a claim that a new concatenated inference was run.

The finalized audit source is `audit_full100_alignments.py`; execution arguments, source hash and receipt hashes are recorded in `validation/receipt.json`. `validation/per_marker.tsv` contains all input and alignment hashes before and after validation. Each input SHA256 matches the pinned preparation manifest. Sequence comparison concatenates FASTA lines after whitespace removal, uppercases both sides, and removes only `-` alignment gaps before exact comparison. Headers are checked by accession identifier (the first FASTA header token).

Native phase completion is established by the unchanged script's `set -euo pipefail`, completion of its sequential 100-input MAFFT loop, and the observed same-owner transition to IQ-TREE. The first IQ-TREE process is PID 15472, parent 4023, start ticks 1922262, on boot `8cca020a-71b2-4163-92dc-6087df12dd45`. This proves alignment-phase completion, not full-run terminal closure. The final MAFFT log is stable. IQ-TREE log snapshots are explicitly in-progress evidence and do not establish marker completion.

Published files are allowlisted: the 100 validated alignments, stable MAFFT log, phase/progress snapshots, audit source and final receipts, and the previous publication's independent remote-byte verification. Active IQ-TREE model/checkpoint files are excluded. The initial unbound integrity receipt is retained separately as preliminary evidence; the final manifest-bound receipt is authoritative. No scientific inputs or outputs were changed by validation.

This is computational integrity evidence, not independent proof of orthology, biological function, or final species-tree reliability. The full 100-marker tree inference and ASTRAL consolidation remain in progress/not yet run, respectively.
'''
fresh(OUT / 'ALIGNMENT_RESULT.md', method)
files = []
def add(local, target, expected=None):
    data = local.read_bytes()
    value = digest(data)
    if expected is not None:
        assert value == expected.lower(), target
    assert len(data) < 5 * 1024 * 1024, target
    text = data.decode('utf-8')
    assert not re.search(r'ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----', text), target
    files.append(dict(local_absolute_path=str(local), target=target, bytes=len(data), sha256=value))

for row in rows:
    name = row['marker'] + '_aligned.fasta'
    assert row['input_stable'] == row['alignment_stable'] == 'true'
    add(ROOT / 'pipeline_output/alignments' / name, 'pipeline_output/alignments/' + name, row['alignment_sha256_after'])
add(OUT / 'STATUS_root.md', 'STATUS.md')
add(OUT / 'ALIGNMENT_RESULT.md', TARGET + '/ALIGNMENT_RESULT.md')
add(Path(__file__), TARGET + '/prepare_publication_root89.py')
add(VALID / 'audit_full100_alignments.py', TARGET + '/audit_full100_alignments.py', receipt['source_sha256'])
for name in ('audit.json', 'per_marker.tsv', 'receipt.json'):
    add(VALID / 'bound_validation' / name, TARGET + '/validation/' + name)
for name in ('audit.json', 'per_marker.tsv'):
    add(VALID / 'attempt01_pre_manifest_binding' / name, TARGET + '/preliminary_unbound_integrity/' + name)
add(OUT / 'progress_receipt.json', TARGET + '/process_observation.json')
add(OUT / 'progress_snapshot_receipt89.json', TARGET + '/snapshot_receipt.json')
snapshots = OUT / 'reports/stage01/progress89'
add(snapshots / 'mafft_align.log.capture2', 'reports/stage01/mafft_align.log', '816f35700ce6adfb57bc5f45e356aaa780062fc6ef54679ec7df937279de0aad')
add(snapshots / 'full_run.log.capture2', TARGET + '/full_run.log.snapshot')
add(snapshots / 'iqtree_progress.log.capture2', TARGET + '/iqtree_progress.log.snapshot')
add(WORK / 'full100_visual_publication88/remote_readback.json', TARGET + '/previous_remote_readback.json')
assert len({r['target'] for r in files}) == len(files)
plan = dict(expected_head=BASE, message='Validate and publish all 100 completed MAFFT alignments; record active IQ-TREE phase', files=files)
fresh(OUT / 'git_plan_root89.json', json.dumps(plan, indent=2) + '\n')
print(json.dumps(dict(files=len(files), bytes=sum(r['bytes'] for r in files), max_file_bytes=max(r['bytes'] for r in files), state='PREPARED_HASH_VERIFIED', expected_head=BASE)))
