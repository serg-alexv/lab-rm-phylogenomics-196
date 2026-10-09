#!/usr/bin/env python3
"""One read-only exact-sequence QA on already accepted primary196 alignment."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
ROOT=Path('G:/My Drive/LAB_RM/lab-rm-phylogenomics-196')
TARGET=ROOT/'.work/stage04_phylogeny_v2/analyses/primary196/concatenated.faa'
EXPECTED='442742d083628ab5382a10cafc422c57084cd9bde45a4f2950f15e2c199e3307'
payload=TARGET.read_bytes();assert hashlib.sha256(payload).hexdigest()==EXPECTED
seqs={};current=None
for line in payload.decode('ascii').splitlines():
    if line.startswith('>'):
        current=line[1:];assert current and current not in seqs;seqs[current]=''
    elif line.strip():assert current is not None;seqs[current]+=line.strip()
assert len(seqs)==196 and {len(s) for s in seqs.values()}=={17456}
approved=(ROOT/'config/approved_accessions.txt').read_text().split();assert set(seqs)==set(approved) and len(approved)==196
groups=defaultdict(list)
for accession,sequence in seqs.items():groups[sequence].append(accession)
duplicates=[{'size':len(accessions),'accessions':sorted(accessions),'aligned_sequence_sha256':hashlib.sha256(sequence.encode()).hexdigest()}
            for sequence,accessions in groups.items() if len(accessions)>1]
duplicates.sort(key=lambda r:(-r['size'],r['accessions']))
report={'status':'PASS_EXACT_ACCEPTED_ALIGNMENT_DUPLICATE_QA','alignment_sha256':EXPECTED,'taxa':196,'columns':17456,
        'unique_full_aligned_sequences':len(groups),'duplicate_group_count':len(duplicates),
        'taxa_in_duplicate_groups':sum(r['size'] for r in duplicates),'groups':duplicates,
        'comparison':'Exact full concatenated aligned AA strings including all gap/ambiguous characters; no case/gap normalization or site exclusion.',
        'biological_computation':False,'panel_preserved':True,'tree_checker_changed':False,
        'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
Path(__file__).with_name('exact_alignment_duplicates.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
