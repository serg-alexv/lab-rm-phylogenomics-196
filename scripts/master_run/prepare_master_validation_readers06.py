"""Freeze independently reviewed recovery/post-verification readers before actual use."""
from pathlib import Path
import hashlib,json

work=Path(__file__).resolve().parent;files=[]
def add(local,target,pin=None):
    path=work/local
    raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    assert 0<len(raw)<5*1024**2 and (pin is None or pin==digest),local
    files.append({'local_absolute_path':str(path),'target':target,'bytes':len(raw),'sha256':digest})
sources={
 'verify_iqtree314_source_recovery01_remote.py':'c13047a8cec8ccfa5eb9878afb53f16b2fae47f3a80f128b2e204b189c1189f1',
 'test_verify_iqtree314_source_recovery01_remote.py':'85856e2d7d739c01e6b1343e658cde8023e4671bffff743540184cb8670876b8',
 'verify_directory_handle_prune.py':'130e7eca3a784d069b4033858c04faebbe2b4765c7942cdd0b9bb35a624cda0c',
 'test_verify_directory_handle_prune.py':'46c059fb90a76c17d11d810b128cd8e06c56b006741dd4a94f29fdae54376d42',
 'accept_stage4_after_native_closure.py':'45c7f39832e898be84473a31802f678cd4035d99c82a8de4fb5bf53eeaac483c',
 Path(__file__).name:None,
}
for name,pin in sources.items():add(name,'scripts/master_run/'+name,pin)
base='reports/master_run/20261009/'
pairs={
 'verify_iqtree314_source_recovery01_remote.md':('cleanup/iqtree314_source01/REMOTE_READBACK_METHODS.md','093cd121d75d70070a08034ffe1139ee396613aa600926f57bb838fceade05ee'),
 'verify_iqtree314_source_recovery01_remote_preparation.json':('cleanup/iqtree314_source01/REMOTE_READBACK_PREPARATION.json','ee36b962d5af19090d2392f7a1d90d73fc90c03b824ac919e6f8565aa76d537d'),
 'iqtree314_source_remote_verifier_independent_review.json':('cleanup/iqtree314_source01/REMOTE_READER_INDEPENDENT_REVIEW.json','36d72f132630040d1799ff87d8b85b0c41673043d0c5ffa7931feaff799f313c'),
 'directory_handle_postverifier_independent_source_review.json':('cleanup/emptydirs_prune01/POSTVERIFIER_INDEPENDENT_REVIEW.json','5a537805072cd07d1f23e7d681309ba4b70a2607dbe65cc4747e0d51929437c6'),
 'stage04_acceptance_wrapper_independent_source_review.json':('preparation/stage04_acceptance_wrapper_independent_source_review.json','51fd2f26a116e7baf7d8f42a0585b3fdf903667dc9e6790effbea12de4fba179'),
 'stage04_acceptance_wrapper_source_review_attempt01.json':('preparation/stage04_acceptance_wrapper_source_review_attempt01.json',None),
 'master_recovery_receipts05_git_objects.json':('publication/RECOVERY_RECEIPTS05_GIT_OBJECTS.json',None),
 'master_recovery_receipts05_remote_readback.json':('publication/RECOVERY_RECEIPTS05_REMOTE_READBACK.json',None),
}
for name,(target,pin) in pairs.items():add(name,base+target,pin)
assert len({r['target'] for r in files})==len(files)
with (work/'master_validation_readers06_git_plan.json').open('x',encoding='utf-8') as stream:
 json.dump({'expected_head':'c9e133ae2aecb34733ca9138ca91a7f3409a51f5','message':'Freeze independent IQ-TREE full-source and exact-directory post-verification readers before actual use','files':files},stream,indent=2);stream.write('\n')
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
