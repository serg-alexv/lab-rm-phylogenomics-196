import builtins, contextlib, hashlib, importlib.util, io, json, os, pathlib, sys, tempfile, types, time
BASE=pathlib.Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/itol_account_tests85')
SOURCE=pathlib.Path('/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/scripts/upload_itol_pilot_account.py')
if (BASE/'account_reader_test_receipt.json').exists(): raise RuntimeError('refusing existing receipt')
BASE.mkdir(parents=True,exist_ok=True)
source_bytes=SOURCE.read_bytes(); compile(source_bytes,str(SOURCE),'exec')
DUMMY_USER='fixture_username_only_not_token'
DUMMY_KEY='DUMMY_API_TOKEN_2LINE_85_NEVER_REAL'
real_open=builtins.open
real_sleep=time.sleep
responses=[]
calls=[]
class RequestException(Exception): pass
class Response:
    def __init__(self,status_code=200,text='',content=b''):
        self.status_code=status_code; self.text=text; self.content=content
fake_requests=types.ModuleType('requests'); fake_requests.RequestException=RequestException

def post(url,data=None,files=None,timeout=None,allow_redirects=None):
    calls.append({'url':url,'timeout':list(timeout) if isinstance(timeout,tuple) else timeout,'allow_redirects':allow_redirects,
                  'key_is_line2':bool(data and data.get('APIkey')==DUMMY_KEY),'username_not_sent':bool(data and DUMMY_USER not in data.values()),
                  'format':data.get('format') if data else None})
    if url.endswith('batch_uploader.cgi'):
        return Response(200,'server echoed '+DUMMY_KEY+'\nSUCCESS: 85731\n')
    if data.get('format')=='svg': return Response(200,'',b'<svg xmlns="http://www.w3.org/2000/svg"><text>fixture</text></svg>')
    return Response(200,'',b'%PDF-1.4\nfixture\n%%EOF\n')
fake_requests.post=post
sys.modules['requests']=fake_requests
state={'credential_text':''}
def patched_open(file,*args,**kwargs):
    try: keypath=os.fspath(file)
    except TypeError: keypath=None
    if keypath=='/mnt/c/itol.api-key.txt': return io.StringIO(state['credential_text'])
    return real_open(file,*args,**kwargs)
builtins.open=patched_open
time.sleep=lambda *_a,**_k: None
spec=importlib.util.spec_from_file_location('upload_pilot_account_under_test',SOURCE)
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

def fixture(name,credential):
    project=BASE/name; (project/'pilot_output').mkdir(parents=True)
    reportdir=project/'reports/stage01/local_pilot_20261010/completed'; reportdir.mkdir(parents=True)
    raw=b'(A:0.1,B:0.2);\n'; flat=b'(A:0.1,B:0.2);\n'
    (project/'pilot_output/species_tree.newick').write_bytes(raw)
    (project/'pilot_output/species_tree.itol_quartet_frequency.newick').write_bytes(flat)
    report={'status':'PASS','marker_results':[{} for _ in range(5)],'astral_result':{'tip_count':196},
            'artifact_sha256':{'species_tree.newick':hashlib.sha256(raw).hexdigest(),
             'species_tree.itol_quartet_frequency.newick':hashlib.sha256(flat).hexdigest()}}
    (reportdir/'validation_report.json').write_text(json.dumps(report),encoding='utf-8')
    state['credential_text']=credential; calls.clear()
    old_argv=sys.argv; old_cwd=pathlib.Path.cwd(); out=io.StringIO(); err=io.StringIO()
    try:
        os.chdir(project); sys.argv=[str(SOURCE),'--project',str(project)]
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            try: rc=module.main(); exc=None
            except Exception as e: rc=None; exc=f'{type(e).__name__}: {e}'
    finally:
        sys.argv=old_argv; os.chdir(old_cwd)
    artifacts={}
    outdir=project/'pilot_output/itol'
    if outdir.exists():
        for p in outdir.rglob('*'):
            if p.is_file(): artifacts[str(p.relative_to(outdir))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size,'token_absent':DUMMY_KEY.encode() not in p.read_bytes(),'username_absent':DUMMY_USER.encode() not in p.read_bytes()}
    return {'returncode':rc,'exception':exc,'stdout':out.getvalue(),'stderr':err.getvalue(),'calls':list(calls),'artifacts':artifacts,'output_exists':outdir.exists()}

results={}
results['two_line_success']=fixture('two_line_success',DUMMY_USER+'\n'+DUMMY_KEY+'\n')
assert results['two_line_success']['returncode']==0,results['two_line_success']
assert len(results['two_line_success']['calls'])==3,results['two_line_success']['calls']
assert results['two_line_success']['calls'][0]['key_is_line2'] and results['two_line_success']['calls'][0]['username_not_sent']
assert all(x['token_absent'] and x['username_absent'] for x in results['two_line_success']['artifacts'].values())
assert 'DUMMY_API_TOKEN' not in results['two_line_success']['stdout']+results['two_line_success']['stderr']
for name,cred in [('three_lines_rejected',DUMMY_USER+'\n'+DUMMY_KEY+'\nEXTRA\n'),('blank_token_rejected',DUMMY_USER+'\n\n')]:
    results[name]=fixture(name,cred)
    assert results[name]['exception'] and 'Expected one token line' in results[name]['exception'],results[name]
    assert not results[name]['calls'],results[name]['calls']
    assert not results[name]['output_exists']
receipt={'tested_source':str(SOURCE),'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'compile_exit':0,
         'python':sys.version,'toolkit':getattr(module.ItolExport,'__module__','unknown'),
         'network':'All requests.post calls intercepted in-process; no real network call possible.',
         'credential':'Only mocked exact key path /mnt/c/itol.api-key.txt; fixture username and dummy token only.',
         'results':results,'all_passed':True}
path=BASE/'account_reader_test_receipt.json'; path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
receipt['receipt_file_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps(receipt,indent=2,sort_keys=True))

