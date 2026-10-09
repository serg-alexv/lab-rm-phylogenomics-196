"""Freeze independent batch03 verifier and externally pinned mapping controls."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
items=[('verify_batch03_mapping_archive_remote.py','scripts/master_run/verify_batch03_mapping_archive_remote.py'),
 ('prepare_master_batch03_verifier_plan.py','scripts/master_run/prepare_master_batch03_verifier_plan.py'),
 ('yesterday_inventory/batch03/evidence_sha256.json','reports/master_run/20261009/cleanup/batch03_mapping01/evidence_sha256.json'),
 ('yesterday_inventory/batch03/source_proof.json','reports/master_run/20261009/cleanup/batch03_mapping01/source_proof.json'),
 ('master_batch03_mapping_git_objects.json','reports/master_run/20261009/publication/BATCH03_MAPPING_GIT_OBJECTS.json'),
 ('master_batch03_mapping_remote_readback.json','reports/master_run/20261009/publication/BATCH03_MAPPING_REMOTE_READBACK.json')]
rows=[]
for local,target in items:
 p=root/local;b=p.read_bytes();assert len(b)<5*1024*1024
 rows.append({'local_absolute_path':str(p),'target':target,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
out=root/'master_batch03_verifier_git_plan.json';assert not out.exists()
out.write_text(json.dumps({'expected_head':'1f5c4e3432d1861b81cb0bd908f0c36e0d77545e',
 'message':'Pin independent batch03 recovery verifier and complete mapping source controls','files':rows},indent=2)+'\n')
print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows)}))
