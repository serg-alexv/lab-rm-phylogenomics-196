"""Independent pure/default-noop check; no UNC or WSL access."""
from pathlib import Path,PureWindowsPath
import hashlib,importlib.util,json,subprocess,sys
W=Path(__file__).resolve().parent
q=W/'stage5_unc02_readonly_diagnostic.py';pin='c0e5a8fdbb97b3b3d3251d417e530a858a65fdeff94ec24eaa2cd3dfe4acc45f'
assert hashlib.sha256(q.read_bytes()).hexdigest()==pin
s=importlib.util.spec_from_file_location('unc_diag_review_only',q);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
request=json.loads((W/'stage5_unc_bind_actual_postiq_02/request.json').read_bytes())
rows=m.targets(request);dirs=m.directory_targets(request)
assert len(rows)==4 and len(dirs)==2
assert all(PureWindowsPath(r['path']).name in ('linux.bin','windows.bin') for r in rows)
assert all(PureWindowsPath(r['path']).parent.name==request['sentinel_name'] for r in rows)
assert all(r['expected_bytes'] in (116,122) for r in rows)
tamper=dict(request,sentinel_name='.unc_visibility_'+'0'*32)
try:m.targets(tamper)
except ValueError:pass
else:raise AssertionError('Tampered nonce accepted')
class Denied:
    def lstat(self):raise PermissionError(13,'synthetic exact UNC access denied')
def denied_read(_):raise PermissionError(13,'synthetic exact UNC access denied')
observed=m.inspect_leaf(rows[0],denied_read,lambda *_:None,lambda _:Denied())
assert observed['metadata_error']['kind']=='PermissionError'
assert observed['tiny_read_error']['kind']=='PermissionError'
assert observed['readonly_payload_error']['kind']=='PermissionError'
assert observed['metadata_after_error']['kind']=='PermissionError'
assert 'payload' not in observed and 'payload_sha256' not in observed
r=subprocess.run([sys.executable,'-B',str(q)],capture_output=True,text=True,timeout=10)
assert r.returncode==0 and json.loads(r.stdout)=={'state':'PREPARED_READONLY_DIAGNOSTIC_NOT_RUN','WSL_launches':0,'UNC_writes':0}
assert hashlib.sha256(q.read_bytes()).hexdigest()==pin
value={'schema':'ROOT_INDEPENDENT_UNC02_DIAGNOSTIC_SOURCE_REVIEW_V1','state':'PASS_PURE_GUARDS_AND_DEFAULT_NOOP',
       'source_sha256':pin,'checks':['fixed_four_leaf_and_two_directory_targets','tampered_nonce_rejected',
       'permission_errors_retained_without_payload_or_adoption','Windows_default_invocation_NOOP'],
       'source_read_review':'Reads exact request-bound public sentinel leaves only; C-only result/progress writes. Existing U0664 named Job retains worker birth/exit and proves empty. Original lock held by owner; exact authority/registry/source joins checked before and after. Actual path visibility and ownership remain unconfirmed.',
       'actual_UNC_access':'NOT_RUN','actual_WSL_launches':0}
out=W/'stage5_unc02_diagnostic_root_source_review01.json'
with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
print(json.dumps(value))
