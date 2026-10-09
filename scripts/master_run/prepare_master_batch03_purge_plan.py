"""Publish exact independently reviewed cold-leaf removal proposal before execution."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
rows=[]
def add(local,target):
 p=root/local;b=p.read_bytes();assert len(b)<5*1024*1024
 rows.append({'local_absolute_path':str(p),'target':target,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
for name in ['Invoke-MasterBatch03LeafPurge.ps1','prepare_master_batch03_leaf_purge.py',
 'test_master_batch03_leaf_purge.py','Test-MasterBatch03LeafPurge.ps1',
 'capture_master_batch03_protected.py','prepare_master_batch03_purge_plan.py']:
 add(name,'scripts/master_run/'+name)
prefix='reports/master_run/20261009/cleanup/batch03_purge01/'
add('master_batch03_leaf_purge_proposed.json',prefix+'proposed.json')
for name in ['master_batch03_leaf_purge_PREPARATION.md','master_batch03_leaf_purge_preparation_checks.json',
 'master_batch03_leaf_purge_source_review.json','master_batch03_stream_parser_check.json','master_batch03_protected_before.json']:
 add(name,prefix+name)
add('batch03_mapping01_remote_readback_20261009T192220Z_3e6cf7d8/receipt.json',
 'reports/master_run/20261009/cleanup/batch03_mapping01/REMOTE_READBACK.json')
add('master_batch03_verifier_git_objects.json','reports/master_run/20261009/publication/BATCH03_VERIFIER_GIT_OBJECTS.json')
add('master_batch03_verifier_remote_readback.json','reports/master_run/20261009/publication/BATCH03_VERIFIER_REMOTE_READBACK.json')
out=root/'master_batch03_purge_git_plan.json';assert not out.exists()
out.write_text(json.dumps({'expected_head':'5c078bdb19a034e95d6edbfd2e67542569f29a8c',
 'message':'Publish verified recovery and exact conservative cold-leaf purge proposal before execution',
 'files':rows},indent=2)+'\n')
print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows)}))
