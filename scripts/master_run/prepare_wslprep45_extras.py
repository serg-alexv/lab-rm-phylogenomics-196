"""Prepare reviewed WSL and VM source mappings only; no runtime or Git mutation."""
from pathlib import Path
import hashlib, json
W=Path(__file__).resolve().parent
p=W/'stage05_offline_image_source_preparation02/PUBLIC_MAPPING.json'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='51c15a85cda8607caaea0b8b1a7842832f3a94b91f1eadbdf2f6340e1163d7c2'
extras=[]
for r in json.loads(p.read_bytes())['files']:
    q=Path(r['local_path']).resolve()
    assert q.is_relative_to(W) and not q.is_symlink() and q.stat().st_size==r['bytes']
    assert hashlib.sha256(q.read_bytes()).hexdigest()==r['sha256']
    extras.append(q.relative_to(W).as_posix()+'='+r['repository_path'])
for name in ('stage5_wsl_config_owner.py','test_stage5_wsl_config_owner.py','prepare_wslprep45_extras.py'):
    extras.append(name+'=scripts/master_run/'+name)
for name in ('stage5_wsl_config_owner_METHODS.md','stage5_wsl_config_owner_preparation01.json',
             'stage5_wsl_config_owner_source_independent_review01.json','stage05_offline_image_corrections02_independent_review.json'):
    assert (W/name).is_file()
    extras.append(name+'=reports/master_run/20261009/wsl_and_vm_preparation45/'+name)
extras.append(p.relative_to(W).as_posix()+'=reports/master_run/20261009/wsl_and_vm_preparation45/PUBLIC_MAPPING.json')
extras.append('master_uncdiagnosis44_remote_readback.json=reports/master_run/20261009/publication/master_uncdiagnosis44_remote_readback.json')
assert len(extras)==len(set(extras))
with (W/'master_wslprep45_extras.json').open('x',encoding='utf-8') as f:
    json.dump(extras,f,indent=2);f.write('\n')
print(json.dumps({'files':len(extras),'state':'PREPARED_MAPPING_ONLY'}))
