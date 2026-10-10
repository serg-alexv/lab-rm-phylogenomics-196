from pathlib import Path
import base64, datetime, hashlib, json, subprocess
W=Path(__file__).resolve().parent
G=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
P=W/'local_pilot74'
R=G/'reports/stage01/local_pilot_20261010'
HEAD='e23fae00a4b8463d4d24272e5c2610ec32509e80'
REPO='serg-alexv/lab-rm-phylogenomics-196'
def sha(b): return hashlib.sha256(b).hexdigest()
def new(p,b):
    with p.open('xb') as f: f.write(b)
def api(e): return json.loads(subprocess.run(['gh','api','repos/'+REPO+'/'+e],capture_output=True,check=True).stdout)
def fasta(p):
    out={}; current=None
    for s in p.read_text().splitlines():
        if s.startswith('>'):
            current=s[1:].split()[0]
            assert current not in out
            out[current]=''
        elif s.strip():
            assert current is not None
            out[current]+=s.strip()
    return out
assert api('git/ref/heads/main')['object']['sha']==HEAD
assert not P.exists()
P.mkdir()
terminal=json.loads((R/'terminal.json').read_text(encoding='utf-8-sig'))
assert terminal['exit_code']==2 and terminal['original_lock_handle_disposed']
assert not list((G/'pilot_output/trees').iterdir())
assert not (G/'pilot_output/species_tree.newick').exists()
original=(G/'run_pipeline.sh').read_bytes()
assert sha(original)=='12f01df5050679c27d8acde1607d53753042e5946a3a958613d89e7479ad33c0'
assert original.count(b'-mem 3000 ')==2
candidate=original.replace(b'-mem 3000 ',b'-mem 3000M ')
new(R/'run_pipeline.corrected_mem.sh',candidate)
new(R/'run_pipeline.original.sh',original)
src=fasta(G/'input_genes/5-FTHF_cyc-lig.fasta')
aln=fasta(G/'pilot_output/alignments/5-FTHF_cyc-lig_aligned.fasta')
assert set(src)==set(aln) and len(src)==189
assert len(set(map(len,aln.values())))==1
assert all(aln[k].replace('-','')==v for k,v in src.items())
log=(G/'reports/stage01/pilot_iqtree.log').read_text()
assert 'Invalid -mem option' in log
packages=subprocess.run(['wsl.exe','-d','Ubuntu','-u','root','--exec','/bin/bash','-lc','source ~/miniconda3/etc/profile.d/conda.sh && conda activate phylogeny && conda list --explicit'],capture_output=True,check=True).stdout
new(R/'conda-explicit.txt',packages)
check=subprocess.run(['wsl.exe','-d','Ubuntu','-u','root','--exec','/bin/bash','-n','/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/reports/stage01/local_pilot_20261010/run_pipeline.corrected_mem.sh'],capture_output=True,check=True)
receipt={'schema':'LOCAL_PILOT_FIRST_ERROR_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'STOPPED_ON_FIRST_IQTREE_ERROR','native_wsl_exit_code':2,'outer_exec_session_exit_code':1,'first_alignment':{'taxa':189,'columns':len(next(iter(aln.values()))),'source_sequences_preserved':True,'sha256':sha((G/'pilot_output/alignments/5-FTHF_cyc-lig_aligned.fasta').read_bytes())},'completed_gene_trees':0,'astral_run':False,'pilot_species_tree_exists':False,'full_pipeline_started':False,'exact_error':log.strip(),'original_script_sha256':sha(original),'proposed_script_sha256':sha(candidate),'proposal':'Replace -mem 3000 with -mem 3000M in the two IQ-TREE commands; no other changes. Candidate bash -n passed.','correction_applied_to_active_script':False,'rerun_requires_confirmation':True,'reason':'Latest user instruction explicitly requires asking before overwrite and requests an exact script. Rerun would replace run_pipeline.sh and regenerate the first alignment; original bytes and all failed-run logs are retained.'}
new(R/'failure_validation.json',(json.dumps(receipt,indent=2)+'\n').encode())
doc='''# Pilot result: stopped on the first IQ-TREE error

The exact requested script ran locally on 2026-10-10 at 07:04:09 UTC and stopped at 07:04:36 UTC. MAFFT completed 5-FTHF_cyc-lig. The alignment has 189 unique approved taxa, equal sequence lengths, and preserves every input sequence after gap removal. IQ-TREE then exited 2 with:

    Invalid -mem option. Example: -mem 200M, -mem 10G

There are zero completed gene trees. ASTRAL did not run. `pilot_output/species_tree.newick` does not exist. The full pipeline was not started. The original workflow lock handle was released; no rerun has occurred.

The unchanged active run_pipeline.sh and a preserved original copy have SHA-256 12f01df5050679c27d8acde1607d53753042e5946a3a958613d89e7479ad33c0. A separate proposed script, run_pipeline.corrected_mem.sh, changes only `-mem 3000` to `-mem 3000M` in the pilot and full IQ-TREE commands; `bash -n` passes. This candidate has not replaced the active script and has not run.

The user's latest ask-before-overwrite instruction requires confirmation to replace the active script and rerun the pilot, which would regenerate the first alignment. Preserve all failed-run logs and original bytes. Confirmation of this correction would authorize only the pilot; full execution still requires a separate decision after pilot completion.

Inputs: five validated existing core markers from the 100-marker, 196-assembly master panel, not whole genomes. Four have 196 taxa; 5-FTHF_cyc-lig has 189. All 973 input protein sequences exactly match accepted manifest hashes and lengths. These pilot results do not change the accepted Stage4 tree or create R-M detector/curation results.
'''
new(R/'RESULT.md',doc.encode())
status=base64.b64decode(api('contents/STATUS.md?ref='+HEAD)['content']).decode()
old=status.split('\n\n',2)
assert old[0]=='# Current request: local five-marker pilot'
updated='# Current request: local five-marker pilot\n\nSTOPPED_ON_FIRST_IQTREE_ERROR. MAFFT completed the first 189-taxon alignment; IQ-TREE rejects unitless -mem 3000. Zero gene trees; ASTRAL and full pipeline not run. A separate correction candidate uses -mem 3000M and awaits the user\'s required overwrite approval. See [actual pilot result](reports/stage01/local_pilot_20261010/RESULT.md).\n\n'+old[2]
new(P/'STATUS.md',updated.encode())
files=[]
def add(path,target):
    b=path.read_bytes()
    files.append({'local_absolute_path':str(path),'target':target,'bytes':len(b),'sha256':sha(b)})
for p in sorted(R.iterdir()):
    if p.is_file(): add(p,p.relative_to(G).as_posix())
for p in sorted((G/'reports/stage01').glob('pilot_*.log')): add(p,p.relative_to(G).as_posix())
for p in sorted((G/'pilot_output').rglob('*')):
    if p.is_file(): add(p,p.relative_to(G).as_posix())
add(P/'STATUS.md','STATUS.md')
add(W/'local_pilot73/remote_readback.json','reports/stage01/local_pilot_20261010/preparation_remote_readback.json')
add(W/'launch_exact_pilot.ps1','scripts/master_run/launch_exact_pilot.ps1')
add(Path(__file__),'scripts/master_run/prepare_pilot_failure74.py')
seq=W/'pilot_sequence_verification73.json'
assert seq.exists(), 'Wait for independent input sequence receipt'
add(seq,'reports/stage01/local_pilot_20261010/sequence_verification.json')
assert len({r['target'] for r in files})==len(files)
new(P/'git_plan.json',(json.dumps({'expected_head':HEAD,'message':'Record exact local pilot failure and review unit-qualified memory correction','files':files},indent=2)+'\n').encode())
print(json.dumps(receipt,indent=2))
