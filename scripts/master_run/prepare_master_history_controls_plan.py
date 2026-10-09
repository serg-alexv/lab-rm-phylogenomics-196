"""Publish exact history controls and the declared empty-directory proposal path."""
from pathlib import Path
import hashlib, json
root=Path(__file__).resolve().parent
rows=[]
def add(name,target):
 p=root/name;b=p.read_bytes()
 rows.append({'local_absolute_path':str(p),'target':target,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
add('master_emptydir_prune_proposed.json','reports/master_run/20261009/cleanup/EMPTY_DIRECTORIES_PROPOSED.json')
add('master_public_history_inventory01_metadata/sourcepins.json','reports/master_run/20261009/cleanup/HISTORY01_BUILD_SOURCE_PINS.json')
add('yesterday_inventory/batch02/evidence_sha256.json','reports/master_run/20261009/cleanup/HISTORY01_BATCH02_EVIDENCE_SHA256.json')
add('master_dependency_history_git_objects.json','reports/master_run/20261009/publication/DEPENDENCY_HISTORY_GIT_OBJECTS.json')
add('master_dependency_history_remote_readback.json','reports/master_run/20261009/publication/DEPENDENCY_HISTORY_REMOTE_READBACK.json')
add('prepare_master_history_controls_plan.py','scripts/master_run/prepare_master_history_controls_plan.py')
out=root/'master_history_controls_git_plan.json';assert not out.exists()
out.write_text(json.dumps({'expected_head':'f861056f31979a725e4f16b05398ab06eb6bcbe5',
 'message':'Pin public history build controls and exact empty-directory recovery proposal',
 'files':rows},indent=2)+'\n')
print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows)}))
