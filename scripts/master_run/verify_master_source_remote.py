"""Independently read every published Git blob and verify actual decoded bytes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64,datetime,hashlib,json,subprocess,time

WORK=Path(__file__).resolve().parent
REPO='serg-alexv/lab-rm-phylogenomics-196'
EXPECTED='3ac8527fb70df6c4010a277d8f23609fcddb69f2'
OUTPUT=WORK/'master_source_remote_readback.json'

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def api(endpoint):
    p=subprocess.run(['gh','api','repos/'+REPO+'/'+endpoint],capture_output=True,timeout=60,check=True)
    return json.loads(p.stdout)

def save(value):
    OUTPUT.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')

declaration=json.loads((WORK/'master_source_git_objects.json').read_text())
assert declaration['commit']==EXPECTED
initial=api('commits/main')['sha']
assert initial==EXPECTED, 'Reconcile unexpected current main before verification'
tree=api('git/trees/'+EXPECTED+'?recursive=1')
assert tree['truncated'] is False
members={item['path']:item for item in tree['tree'] if item['type']=='blob'}
assert len(declaration['files'])==len({i['target'] for i in declaration['files']})==147
result={'schema':'MASTER_SOURCE_INDEPENDENT_REMOTE_BYTE_READBACK_V1','started_utc':utc(),
        'state':'READBACK_IN_PROGRESS','expected_commit':EXPECTED,'initial_remote_main':initial,
        'declaration_sha256':hashlib.sha256((WORK/'master_source_git_objects.json').read_bytes()).hexdigest(),
        'method':'GitHub REST Git blobs; actual base64-decoded bytes independently SHA256 hashed',
        'maximum_parallel_gh_requests':4,'required_files':len(declaration['files']),
        'verified_files':0,'files':[],'failures':[],'biological_acceptance':'NONE_SOURCE_AND_SYNTHETIC_PREPARATION_ONLY'}
save(result)
def verify(item):
    target=item['target'];obj=members[target]
    value=api('git/blobs/'+obj['sha'])
    assert value['encoding']=='base64' and value['sha']==obj['sha'],target
    data=base64.b64decode(value['content'],validate=False)
    digest=hashlib.sha256(data).hexdigest()
    assert len(data)==value['size']==obj['size']==item['bytes'],target+' bytes'
    assert digest==item['sha256'],target+' SHA256'
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==obj['sha'],target+' Git object'
    return {'path':target,'bytes':len(data),'sha256':digest,'remote_blob':obj['sha'],
            'actual_remote_bytes_read':True,'byte_count_verified':True,'sha256_verified':True}
start=time.monotonic()
with ThreadPoolExecutor(max_workers=4) as pool:
    futures={pool.submit(verify,item):item['target'] for item in declaration['files']}
    for future in as_completed(futures):
        try:result['files'].append(future.result())
        except Exception as error:result['failures'].append({'path':futures[future],'kind':type(error).__name__,'error':str(error)})
        result['verified_files']=len(result['files'])
        save(result)
        if (len(result['files'])+len(result['failures']))%25==0:
            print(json.dumps({'verified_files':result['verified_files'],'failures':len(result['failures'])}),flush=True)
result['files'].sort(key=lambda value:value['path'])
result['final_remote_main']=api('commits/main')['sha']
result.update(finished_utc=utc(),elapsed_seconds=time.monotonic()-start,
              verified_bytes=sum(i['bytes'] for i in result['files']))
if not result['failures'] and result['verified_files']==result['required_files'] and result['final_remote_main']==EXPECTED:
    result['state']='PASS_ALL147_REMOTE_BYTES_SHA256_VERIFIED'
elif not result['failures'] and result['verified_files']==result['required_files']:
    result['state']='ALL147_IMMUTABLE_COMMIT_BYTES_VERIFIED_CURRENT_HEAD_CHANGED_RECONCILE'
else:result['state']='FAILED_REMOTE_BYTE_READBACK'
save(result)
print(json.dumps({key:result[key] for key in ('state','expected_commit','final_remote_main','verified_files','verified_bytes','elapsed_seconds','failures')},indent=2))
if result['state']!='PASS_ALL147_REMOTE_BYTES_SHA256_VERIFIED':raise SystemExit(1)
