from pathlib import Path
import base64, datetime, hashlib, json, subprocess

W=Path(__file__).resolve().parent
G=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
P=W/'local_pilot73'
HEAD='1e51327a36cc6c1fff655ea3c533797288c9726e'
REPO='serg-alexv/lab-rm-phylogenomics-196'
def sha(b): return hashlib.sha256(b).hexdigest()
def api(endpoint):
    return json.loads(subprocess.run(['gh','api','repos/'+REPO+'/'+endpoint],capture_output=True,check=True).stdout)
def new(path,data):
    with path.open('xb') as f: f.write(data)
assert api('git/ref/heads/main')['object']['sha']==HEAD
script=G/'run_pipeline.sh'
assert sha(script.read_bytes())=='12f01df5050679c27d8acde1607d53753042e5946a3a958613d89e7479ad33c0'
assert not P.exists() and not (G/'input_genes').exists()
assert not (G/'pilot_output').exists() and not (G/'pipeline_output').exists()
P.mkdir()
markers=['5-FTHF_cyc-lig','ADK','ATP-synt','ATP-synt_A','ATP-synt_B']
expected=['b6a7dca05abecb2640065e29c592dde672cb71952431e577e128c11168d690be','1bf708f18ecea80df0177f98d20c9aff90a10bd77f06c61c064c88601a48a0df','7fd9d32ca5c4d0723af15ab71445ce60779b105097a3f4628e834435ebff098c','5908056ab17f4c4e80f899efd54c030a4861c5bcc8d1ef08d66d0f95126598da','861cdf3764f4669bacb308e01eb62697cfe3fb34d90b7b4bcac943ae40bc2f2a']
approved=set((G/'config/approved_accessions.txt').read_text().splitlines())
order=(G/'.work/stage04_phylogeny_v2/analyses/primary196/marker_order.txt').read_text().splitlines()
assert len(approved)==196 and len(order)==100 and sorted(order)[:5]==markers
rows=[]
captured=[]
for name,digest in zip(markers,expected):
    src=G/'.work/stage03_orthology_v2/marker_sequences'/(name+'.faa')
    data=src.read_bytes()
    assert sha(data)==digest
    ids=[s[1:].split()[0] for s in data.decode().splitlines() if s.startswith('>')]
    assert len(ids)==len(set(ids)) and set(ids)<=approved
    target='input_genes/'+name+'.fasta'
    rows.append({'marker':name,'source':src.relative_to(G).as_posix(),'target':target,'bytes':len(data),'sha256':digest,'taxa':len(ids),'unique_approved_taxa':True,'sequence_bytes_unchanged':True})
    captured.append((G/target,data))
(G/'input_genes').mkdir()
for target,data in captured: new(target,data)
manifest={'schema':'LOCAL_FIVE_MARKER_PILOT_INPUTS_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'PREPARED_NOT_RUN','authorization':'Latest direct user request: exact Bash pilot first; use five existing validated core-marker FASTAs. Full pipeline requires separate confirmation after pilot.','approved_panel_taxa':196,'existing_core_loci':100,'selected_loci':5,'input_kind':'Unaligned amino-acid marker sequences; not whole genomes','script_sha256':sha(script.read_bytes()),'source_manifest':'accepted_sequence_manifest.tsv','source_manifest_sha256':sha((G/'.work/stage03_orthology_v2/accepted_sequence_manifest.tsv').read_bytes()),'approved_accessions_sha256':sha((G/'config/approved_accessions.txt').read_bytes()),'marker_order_sha256':sha((G/'.work/stage04_phylogeny_v2/analyses/primary196/marker_order.txt').read_bytes()),'files':rows,'full_pipeline_authorized':False,'deletions_moves_overwrites_performed':False}
new(P/'input_manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
doc='''# Local five-marker pilot, 2026-10-10

Latest direct user instructions authorize the exact attached `run_pipeline.sh`, local Bash loops in Ubuntu WSL, and five existing validated marker FASTAs. This request supersedes historical no-pilot/no-pause directions for this pilot only. The full pipeline needs a new confirmation after pilot completion. No full pipeline has been launched.

The existing master dataset has 100 core markers across 196 approved assemblies, not 196 loci. The first five marker names in lexical order are selected. Four contain 196 taxa; 5-FTHF_cyc-lig contains 189. Inputs are unchanged unaligned amino-acid sequences copied from the accepted stage03 marker collection. Input hashes and source paths are in input_manifest.json. Existing accepted Stage4 results are preserved.

The requested script is byte-identical to the attachment and passes `bash -n`. It uses MAFFT --auto, IQ-TREE -m MFP -bb 1000 -nt 2 -mem 3000, then ASTRAL -t 2. It activates /root/miniconda3/envs/phylogeny. Live conda metadata reports MAFFT 7.526, IQ-TREE 3.1.4, astral-tree 5.7.8, and SeqKit 2.14.0. Tool exit logs and result validation follow execution.

Working directory: canonical lab-rm-phylogenomics-196 checkout. Command: `PILOT_ONLY=1 bash run_pipeline.sh`. Outputs: pilot_output/ and reports/stage01/pilot_*.log. The script also creates empty pipeline_output directories. No existing output is overwritten. Stop on the first error. No rm/mv/overwrite without the user's permission.

Scientific status: pilot prepared, not run. This pilot is a five-gene ASTRAL methods check; it does not replace the accepted 100-marker Stage4 tree and does not complete R-M detector Stage5 or curated Stage6 results. No biological absence is inferred from incomplete work. Full run would require staging the remaining approved markers; a five-file input directory must never be called the full 100-marker dataset.

Previously completed current-boot G-drive diagnosis/mount closure evidence and reviewed recovery/cleanup sources are archived in this commit. Recovery and cleanup sources remain NOT RUN; the latest ask-before-delete instruction is in force. No VM image is split or removed.
'''
new(P/'README.md',doc.encode())
remote_status=base64.b64decode(api('contents/STATUS.md?ref='+HEAD)['content']).decode()
new(P/'STATUS.md',('# Current request: local five-marker pilot\n\nPREPARED_NOT_RUN. Latest direct user instruction selects five existing validated core-marker FASTAs, runs the exact attached Bash script with PILOT_ONLY=1, and requires confirmation before full execution. See [pilot report](reports/stage01/local_pilot_20261010/README.md). Prior accepted Stage4 results are preserved. Stage5 native detectors remain not run.\n\n'+remote_status).encode())
files=[]
def add(path,target):
    b=path.read_bytes()
    assert len(b)<5*1024*1024
    row={'local_absolute_path':str(path),'target':target,'bytes':len(b),'sha256':sha(b)}
    if target.endswith(('.gz','.pdf','.png')): row['transport_encoding']='base64'
    files.append(row)
add(script,'run_pipeline.sh')
for row in rows: add(G/row['target'],row['target'])
for name in ['input_manifest.json','README.md']: add(P/name,'reports/stage01/local_pilot_20261010/'+name)
add(P/'STATUS.md','STATUS.md')
add(W/'master_interopg72_remote_readback.json','reports/master_run/20261009/publication/master_interopg72_remote_readback.json')
for name in ['stage05_gdrive_postfallback_actual_pair01','stage05_storage_prepared_recovery_source_preparation01','stage5_storage_recovery_builder_source01','stage05_transport30_exact_cleanup_source01']:
    mapping=W/name/'PUBLIC_MAPPING.json'
    for row in json.loads(mapping.read_text())['files']:
        source=Path(row['local_path'])
        assert len(source.read_bytes())==row['bytes'] and sha(source.read_bytes())==row['sha256']
        add(source,row.get('repository_path') or row.get('suggested_remote_path') or row.get('target'))
    add(mapping,'reports/master_run/20261009/'+name+'/PUBLIC_MAPPING.json')
add(Path(__file__),'scripts/master_run/prepare_local_pilot73.py')
publisher=(W/'prepare_master_git_update.py').read_text()
assert "{'STATUS.md', 'README.md'}" in publisher
publisher=publisher.replace("{'STATUS.md', 'README.md'}","{'STATUS.md', 'README.md', 'run_pipeline.sh'}")
new(P/'publish_pilot_git_objects.py',publisher.encode())
add(P/'publish_pilot_git_objects.py','scripts/master_run/publish_pilot_git_objects.py')
assert len({r['target'] for r in files})==len(files)
plan={'expected_head':HEAD,'message':'Prepare exact local five-marker Bash pilot and archive closed G-drive evidence','files':files}
new(P/'git_plan.json',(json.dumps(plan,indent=2)+'\n').encode())
print(json.dumps({'state':'PREPARED_NOT_RUN','files':len(files),'input_files':rows,'plan':str(P/'git_plan.json')}))
