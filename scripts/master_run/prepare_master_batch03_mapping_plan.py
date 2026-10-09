"""Publish recovery controls before exporting the exact old-cache proposal."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
items=[('build_batch03_mapping_archive.py','scripts/master_run/build_batch03_mapping_archive.py'),
 ('prepare_master_batch03_mapping_plan.py','scripts/master_run/prepare_master_batch03_mapping_plan.py'),
 ('master_source_split_git_objects.json','reports/master_run/20261009/publication/SOURCE_SPLIT_GIT_OBJECTS.json'),
 ('master_source_split_remote_readback.json','reports/master_run/20261009/publication/SOURCE_SPLIT_REMOTE_READBACK.json')]
for name in ['build_receipt.json','source_binding.json','conservative_leaf_assessment.json','README.txt','SHA256SUMS.txt']:
 items.append(('master_batch03_mapping01/'+name,'reports/master_run/20261009/cleanup/batch03_mapping01/'+name))
rows=[]
for local,target in items:
 path=root/local;data=path.read_bytes();assert len(data)<5*1024*1024
 rows.append({'local_absolute_path':str(path),'target':target,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
out=root/'master_batch03_mapping_git_plan.json';assert not out.exists()
out.write_text(json.dumps({'expected_head':'addf594d69990b4d4bc95d1e0fa38c76f59efdd6',
 'message':'Preserve exact released-member mapping and conservative old-cache removal proposal',
 'files':rows},indent=2)+'\n')
print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows)}))
