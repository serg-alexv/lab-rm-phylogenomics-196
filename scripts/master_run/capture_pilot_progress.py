from pathlib import Path
import argparse,base64,datetime,hashlib,json,subprocess
p=argparse.ArgumentParser()
p.add_argument('--name',required=True)
p.add_argument('--expected-head',required=True)
p.add_argument('--state',default='RUNNING')
p.add_argument('--detail',required=True)
a=p.parse_args()
W=Path(__file__).resolve().parent
G=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
P=W/a.name
assert not P.exists()
def api(e):return json.loads(subprocess.run(['gh','api','repos/serg-alexv/lab-rm-phylogenomics-196/'+e],capture_output=True,check=True).stdout)
assert api('git/ref/heads/main')['object']['sha']==a.expected_head
P.mkdir()
def new(p,b):
    with p.open('xb') as f:f.write(b)
files=[]
def add(p,t):
    b=p.read_bytes();files.append({'local_absolute_path':str(p),'target':t,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
snapshot={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':a.state,'detail':a.detail,'command':'PILOT_ONLY=1 bash run_pipeline.sh','script_sha256':hashlib.sha256((G/'run_pipeline.sh').read_bytes()).hexdigest(),'full_pipeline_started':False,'treefile_names_observed':[p.name for p in sorted((G/'pilot_output/trees').glob('*.treefile'))],'observation_is_final_validation':False}
new(P/'progress.json',(json.dumps(snapshot,indent=2)+'\n').encode())
base='reports/stage01/local_pilot_20261010/progress/'+a.name+'/'
add(P/'progress.json',base+'progress.json')
log=G/'reports/stage01/pilot_iqtree.log'
new(P/'iqtree_tail.txt',('\n'.join(log.read_text().splitlines()[-40:])+'\n').encode())
add(P/'iqtree_tail.txt',base+'iqtree_tail.txt')
launch=G/'reports/stage01/local_pilot_20261010/attempt02/launch.json'
add(launch,'reports/stage01/local_pilot_20261010/attempt02/launch.json')
prior=base64.b64decode(api('contents/STATUS.md?ref='+a.expected_head)['content']).decode().split('\n\n',2)
new(P/'STATUS.md',('# Current request: local five-marker pilot\n\n'+a.state+'. '+a.detail+' Full execution remains unapproved. See [progress receipt]('+base+'progress.json).\n\n'+prior[2]).encode())
add(P/'STATUS.md','STATUS.md')
add(Path(__file__),'scripts/master_run/capture_pilot_progress.py')
readback=W/'local_pilot75/remote_readback.json'
add(readback,'reports/stage01/local_pilot_20261010/correction_remote_readback.json')
new(P/'git_plan.json',(json.dumps({'expected_head':a.expected_head,'message':'Record local five-marker pilot progress: '+a.name,'files':files},indent=2)+'\n').encode())
print(json.dumps(snapshot))
