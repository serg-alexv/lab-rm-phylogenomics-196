from pathlib import Path
import base64,datetime,hashlib,json,subprocess
W=Path(__file__).resolve().parent
G=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
R=G/'reports/stage01/local_pilot_20261010'
P=W/'local_pilot75'
HEAD='cf2aa0ff4660e34d2405bb9a3bbbe2d9972b8b4a'
def sha(b): return hashlib.sha256(b).hexdigest()
def new(p,b):
    with p.open('xb') as f:f.write(b)
def api(e):return json.loads(subprocess.run(['gh','api','repos/serg-alexv/lab-rm-phylogenomics-196/'+e],capture_output=True,check=True).stdout)
assert api('git/ref/heads/main')['object']['sha']==HEAD
assert json.loads((W/'local_pilot74/remote_readback.json').read_text())['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED'
assert not P.exists()
P.mkdir()
B=R/'attempt01_preserved'
assert not B.exists()
B.mkdir()
for name in ['pilot_mafft.log','pilot_iqtree.log','pilot_console.log']:
    new(B/name,(G/'reports/stage01'/name).read_bytes())
new(B/'5-FTHF_cyc-lig_aligned.fasta',(G/'pilot_output/alignments/5-FTHF_cyc-lig_aligned.fasta').read_bytes())
active=G/'run_pipeline.sh'
assert sha(active.read_bytes())=='12f01df5050679c27d8acde1607d53753042e5946a3a958613d89e7479ad33c0'
candidate=(R/'run_pipeline.corrected_mem.sh').read_bytes()
assert sha(candidate)=='5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b'
active.write_bytes(candidate)
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'CORRECTION_APPLIED_PILOT_RERUN_AUTHORIZED_NOT_YET_LAUNCHED','authorization':'Direct user reply: Apply correction and rerun pilot','only_script_change':'Both IQ-TREE -mem 3000 flags changed to -mem 3000M','active_script_sha256':sha(active.read_bytes()),'original_script_preserved':'reports/stage01/local_pilot_20261010/run_pipeline.original.sh','failed_attempt_files_preserved':[p.name for p in sorted(B.iterdir())],'first_alignment_regeneration_authorized':True,'full_pipeline_authorized':False}
new(R/'correction_approval.json',(json.dumps(receipt,indent=2)+'\n').encode())
status=base64.b64decode(api('contents/STATUS.md?ref='+HEAD)['content']).decode().split('\n\n',2)
new(P/'STATUS.md',('# Current request: local five-marker pilot\n\nCORRECTION_APPLIED_PILOT_RERUN_AUTHORIZED. User approved replacing unitless -mem 3000 with -mem 3000M and regenerating the first alignment. Original script, first alignment and failure logs are preserved. Corrected pilot launch is next; full execution remains unapproved. See [approval](reports/stage01/local_pilot_20261010/correction_approval.json).\n\n'+status[2]).encode())
files=[]
def add(p,t):
    b=p.read_bytes();files.append({'local_absolute_path':str(p),'target':t,'bytes':len(b),'sha256':sha(b)})
add(active,'run_pipeline.sh')
add(P/'STATUS.md','STATUS.md')
for p in sorted(B.iterdir()):add(p,p.relative_to(G).as_posix())
add(R/'correction_approval.json','reports/stage01/local_pilot_20261010/correction_approval.json')
add(W/'local_pilot74/remote_readback.json','reports/stage01/local_pilot_20261010/failure_remote_readback.json')
for name in ['launch_corrected_pilot.ps1','prepare_pilot_correction75.py']:add(W/name,'scripts/master_run/'+name)
new(P/'git_plan.json',(json.dumps({'expected_head':HEAD,'message':'Apply user-approved IQ-TREE memory unit fix before local pilot retry','files':files},indent=2)+'\n').encode())
print(json.dumps(receipt))
