"""Read-only canonical G receipt comparison against released source byte pins."""
from pathlib import Path
import datetime, hashlib, json

work=Path(__file__).resolve().parent
root=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
pinfile=work/'stage5_accepted_source_pins.json'
def sha(data): return hashlib.sha256(data).hexdigest()
assert sha(pinfile.read_bytes()) == 'a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84'
pins=json.loads(pinfile.read_text())
assert pins['schema']=='STAGE05_ACCEPTED_SOURCE_PINS_V1'
rows=[]
for rel, expected in pins['accepted_files'].items():
    p=root.joinpath(*rel.split('/')); data=p.read_bytes()
    rows.append({'relative_path':rel,'bytes':len(data),'sha256':sha(data),'matches':sha(data)==expected})
panel=(root/'config/approved_accessions.txt').read_text().split()
assert len(panel)==len(set(panel))==196 and set(panel)==set(pins['source_receipts'])
for accession in panel:
    expected=pins['source_receipts'][accession]
    rel='.work/source_locus_inputs_v1/assemblies/'+accession+'/build_receipt.json'
    data=(root.joinpath(*rel.split('/'))).read_bytes()
    value=json.loads(data)
    rows.append({'relative_path':rel,'bytes':len(data),'sha256':sha(data),
                 'matches':sha(data)==expected['sha256'] and len(data)==expected['bytes']
                 and value['assembly_accession']==accession})
result={'schema':'STAGE05_CANONICAL_SOURCE_RECEIPT_READBACK_V1',
    'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'state':'PASS' if all(r['matches'] for r in rows) else 'FAIL',
    'canonical_root':str(root),'pins_sha256':sha(pinfile.read_bytes()),
    'checked_files':len(rows),'actual_bytes_read':sum(r['bytes'] for r in rows),
    'scope':'Acceptance and196 released build receipts only; per-job source outputs still require exact reopening',
    'canonical_mutations':0,'wsl_starts':0,'files':rows}
out=work/'stage5_canonical_source_pins_readback.json';assert not out.exists()
with out.open('x',encoding='utf-8') as f: f.write(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['state','checked_files','actual_bytes_read','canonical_mutations','wsl_starts']}))
assert result['state']=='PASS'
