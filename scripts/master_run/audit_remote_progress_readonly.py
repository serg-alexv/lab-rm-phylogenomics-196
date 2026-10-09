"""Read-only canonical GitHub/G checkout audit; all outputs stay in chat C work."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

OUT = Path(__file__).resolve().parent/'remote_progress_audit'
OUT.mkdir(exist_ok=True)
REPO = 'serg-alexv/lab-rm-phylogenomics-196'
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')

def run(argv):
    p = subprocess.run(argv,capture_output=True,timeout=60,check=True)
    return p.stdout

def api(endpoint):
    return json.loads(run(['gh','api','repos/'+REPO+('/'+endpoint if endpoint else '')]))

def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')

head = api('commits/main')
tree = api('git/trees/'+head['sha']+'?recursive=1')
releases = api('releases?per_page=100')
repo = api('')
branch = api('branches/main')
save('remote_main.json',head)
save('remote_tree.json',tree)
save('remote_releases.json',releases)
save('remote_access.json',{'permissions':repo.get('permissions'),'visibility':repo.get('visibility'),
                         'default_branch':repo.get('default_branch'),'main_protected':branch.get('protected')})
local = {'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
         'head':run(['git','--no-optional-locks','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),
         'status_porcelain':run(['git','--no-optional-locks','-C',str(ROOT),'status','--porcelain=v1']).decode(),
         'files':{}}
for name in ('AGENTS.md','WORK_ORDER.md','README.md','STATUS.md','status/stages.tsv',
             'status/stage04_execution.json','status/run_control.json'):
    data = (ROOT/name).read_bytes()
    target = OUT/'local_canonical'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    local['files'][name] = {'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
save('local_snapshot.json',local)
print(json.dumps({'remote_main':head['sha'],'local_main':local['head'],
 'remote_date':head['commit']['committer']['date'],'remote_message':head['commit']['message'],
 'tree_blobs':sum(x['type']=='blob' for x in tree['tree']),'tree_truncated':tree.get('truncated'),
 'release_count':len(releases),'release_assets':sum(len(r['assets']) for r in releases),
 'release_bytes':sum(a['size'] for r in releases for a in r['assets']),
 'permissions':repo.get('permissions'),'main_protected':branch.get('protected'),
 'local_status':local['status_porcelain'],'output':str(OUT)},indent=2))
