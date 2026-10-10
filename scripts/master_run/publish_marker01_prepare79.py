from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
G=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
P=W/'local_pilot79'
review=W/'pilot_marker01_validation79'
v=json.loads((review/'marker01_validation.json').read_text())
assert v['checks']['native_iqtree_log_completed'] and v['checks']['tree_tip_count']==189
for row in v['evidence'].values():
    if isinstance(row,dict) and 'path' in row and 'sha256' in row:
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']
subprocess.run([sys.executable,'-B',str(W/'capture_pilot_progress.py'),'--name','local_pilot79','--expected-head','b4b3bf764786bbd72c45dd7d4d7d18e0eecb414f','--detail','Pilot marker1 of5 completed and independently validated: 5-FTHF_cyc-lig,189 taxa,210 alignment columns,Q.PFAM+F+I+R5,1000 UFBoot replicates. All input sequences are preserved. 153 internal branches have numeric supports5-100;33 short internal branches have no support labels and remain explicitly unlabeled. Native completion was07:39:43 UTC. ADK is now running; ASTRAL and full pipeline have not run.'],check=True)
plan=json.loads((P/'git_plan.json').read_text())
def add(source,target,copy=False):
    data=source.read_bytes()
    if copy:
        path=P/'frozen'/target
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:f.write(data)
        assert source.read_bytes()==data
        source=path
    row={'local_absolute_path':str(source),'target':target,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    if target.endswith('.gz'):row['transport_encoding']='base64'
    plan['files'].append(row)
for source in sorted((G/'pilot_output/trees').glob('5-FTHF_cyc-lig.*')):
    add(source,source.relative_to(G).as_posix(),True)
aln=G/'pilot_output/alignments/5-FTHF_cyc-lig_aligned.fasta'
add(aln,aln.relative_to(G).as_posix(),True)
for source in sorted(review.iterdir()):
    if source.is_file():add(source,'reports/stage01/local_pilot_20261010/marker01/'+source.name)
add(W/'validate_five_marker_pilot.py','scripts/master_run/validate_five_marker_pilot.py')
add(W/'local_pilot78/remote_readback.json','reports/stage01/local_pilot_20261010/progress/local_pilot78/remote_readback.json')
add(W/'itol_hotfix77/remote_readback.json','reports/stage01/itol_hotfix_20261010/remote_readback.json')
add(Path(__file__),'scripts/master_run/publish_marker01_prepare79.py')
plan['message']='Publish independently validated first pilot gene tree and native recovery artifacts'
assert len({r['target'] for r in plan['files']})==len(plan['files'])
with (P/'git_plan_science.json').open('x',encoding='utf-8') as f:json.dump(plan,f,indent=2)
print(json.dumps({'files':len(plan['files']),'completed_validated_markers':1,'pilot_complete':False}))
