"""Preserve exact provider diagnosis and reviewed correction before one read-only retest."""
from pathlib import Path
import hashlib,json
work=Path(__file__).resolve().parent;files=[]
base='reports/master_run/20261009/'
def add(path,target,pin=None):
 path=Path(path)
 if not path.is_absolute():path=work/path
 raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
 assert 0<len(raw)<5*1024**2 and (pin is None or pin==digest),str(path)
 files.append({'local_absolute_path':str(path),'target':target,'bytes':len(raw),'sha256':digest})
prep=work/'directory_handle_postverify_preparation_02.json'
assert hashlib.sha256(prep.read_bytes()).hexdigest()=='747a792f0a37b425fb9af017dd8dfbec5e9fdee2dfeade432f0dd27dc29afe23'
for name,pin in json.loads(prep.read_bytes())['source_pins'].items():
 if name.endswith('.py'):target='scripts/master_run/'+name
 elif name.endswith('/receipt.json'):target=base+'cleanup/emptydirs_prune01/POSTVERIFY_ATTEMPT01_FAILED.json'
 elif name.endswith('/started.json'):target=base+'cleanup/emptydirs_prune01/POSTVERIFY_ATTEMPT01_STARTED.json'
 else:target=base+'cleanup/emptydirs_prune01/'+name
 add(name,target,pin)
add(prep,base+'cleanup/emptydirs_prune01/POSTVERIFY_PREPARATION_02.json')
add('observe_iqtree_controller_exit.py','scripts/master_run/observe_iqtree_controller_exit.py')
add(Path(__file__),'scripts/master_run/'+Path(__file__).name)
for name,target in {
 'master_source_recovery_result07_git_objects.json':'publication/SOURCE_RECOVERY_RESULT07_GIT_OBJECTS.json',
 'master_source_recovery_result07_remote_readback.json':'publication/SOURCE_RECOVERY_RESULT07_REMOTE_READBACK.json',
}.items():add(name,base+target)
with (work/'master_directory_provider_correction08_git_plan.json').open('x',encoding='utf-8') as stream:
 json.dump({'expected_head':'f5027656958d495bf810192b541e9554d1a98b66','message':'Pin observed DriveFS zero-link semantics for nine protected files; preserve strict identity and SHA checks','files':files},stream,indent=2);stream.write('\n')
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
