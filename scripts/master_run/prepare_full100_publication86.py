from pathlib import Path
import base64, datetime, hashlib, json, subprocess
W=Path(__file__).resolve().parent
G=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
R=G/'reports/stage01/local_full100_20261010/preparation'
P=W/'full100_publication86'
EXPECTED='2723aeef69b713dfcde10ec87cb2492c509deac7'
assert not P.exists() and not R.exists()
stage=json.loads((W/'full100_input_audit86/staging_receipt.json').read_text(encoding='utf-8-sig'))
assert stage['state']=='PASS_100_INPUTS_STAGED' and stage['markers']==100
P.mkdir(); R.mkdir(parents=True)
def new(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(data if isinstance(data,bytes) else data.encode())
for source in (W/'full100_input_audit86').iterdir():
    if source.is_file():new(R/source.name,source.read_bytes())
for name in ['stage_full100_inputs86.ps1','full100_runner86.sh','launch_full10086.ps1']:
    new(G/'scripts/master_run'/name,(W/name).read_bytes())
new(R/'AUTHORIZATION_AND_METHOD.md','''# Full 100-marker local run authorized

On 2026-10-10 the user explicitly authorized the full 100-marker run in the
background, with iTOL independent of inference and validate_pipeline.py untouched.
This supersedes the earlier pilot-only approval boundary. Scientific execution
remains local on WD Ubuntu WSL. No pipeline source flags or science methods change.

All 100 unaligned per-marker FASTAs are byte-identical to validated Stage 3 v2
sources: 19,359 sequences across exactly 196 approved accessions. There are 241
missing marker/taxon combinations, handled per locus. Duplicate accession headers
are absent; identical protein sequences across distinct taxa are retained.
Five staged inputs are preserved; 95 missing inputs were created without overwrites.

The approved run_pipeline.sh SHA256 remains
5bc5e1b2b3d0101177f052558428e9e30b1bb53dbf674309ed612f5c22bec09b.
Its full branch runs MAFFT --auto per locus, IQ-TREE -m MFP -bb 1000 -nt 2
-mem 3000M per alignment, then concatenates all 100 gene trees for ASTRAL -t 2.
Scientific outputs are pipeline_output/ and the final root species_tree.newick;
pilot outputs remain unchanged. Source filename ordering is the Bash glob order.

The hidden Windows owner holds the original exclusive workflow.lock while the
foreground WSL nohup Bash runner waits for its pipeline child. Launch and terminal
receipts retain boot identity, process start identity, hashes, commands and exits.
The wrapper refuses existing science outputs and logs. Failure stops the run;
there is no automatic rerun or replacement of checkpoints. iTOL is not invoked by
the scientific script. Full-run result acceptance remains pending real execution.

The copied iTOL bundle contains LABELS and TREE_COLORS for display labels and ten
operational taxonomic groups. It contains no defense-system calls or host traits.
These templates do not use DATASET_BINARY or DATASET_COLORSTRIP. A rendered pilot
checks display compatibility, not biological reliability of the final result.
''')
files=[]
def add(source,target):
    data=source.read_bytes()
    files.append({'local_absolute_path':str(source),'target':target,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
for source in sorted((G/'input_genes').glob('*.fasta')):add(source,source.relative_to(G).as_posix())
for source in sorted(R.iterdir()):
    if source.is_file():add(source,source.relative_to(G).as_posix())
for name in ['stage_full100_inputs86.ps1','full100_runner86.sh','launch_full10086.ps1']:
    source=G/'scripts/master_run'/name;add(source,source.relative_to(G).as_posix())
for source in sorted((G/'pipeline_output/itol_annotations').iterdir()):
    if source.is_file():add(source,source.relative_to(G).as_posix())
for source in sorted((W/'full100_labels_audit86').iterdir()):
    if source.is_file():add(source,'reports/stage01/local_full100_20261010/label_audit/'+source.name)
for name in ['generate_itol_bundle.py','manifest.json','color_legend.tsv']:
    add(W/'pilot_itol_labels01'/name,'reports/stage01/local_full100_20261010/label_bundle/'+name)
add(W/'local_itol_prepare85/remote_readback.json','reports/stage01/itol_pilot_20261010/remote_readback.json')
if (W/'full100_launch_review86').exists():
    for source in sorted((W/'full100_launch_review86').iterdir()):
        if source.is_file():add(source,'reports/stage01/local_full100_20261010/launcher_review/'+source.name)
old=json.loads(subprocess.run(['gh','api','repos/serg-alexv/lab-rm-phylogenomics-196/contents/STATUS.md?ref='+EXPECTED],capture_output=True,check=True).stdout)
history=base64.b64decode(old['content']).decode()
new(P/'STATUS.md','# Current request: full 100-marker run approved and prepared\n\nAll 100 audited FASTAs are staged: 19,359 records across196 approved taxa. Launch is authorized and pending. The unchanged local plain-Bash pipeline will run in the background independently of iTOL. Pilot science remains validated; copied annotation files provide labels and operational taxonomic colors, not defense or host traits. validate_pipeline.py remains untouched. See [preparation and method](reports/stage01/local_full100_20261010/preparation/AUTHORIZATION_AND_METHOD.md).\n\n'+history)
add(P/'STATUS.md','STATUS.md')
add(Path(__file__),'scripts/master_run/prepare_full100_publication86.py')
new(P/'git_plan.json',json.dumps({'expected_head':EXPECTED,'message':'Authorize and stage audited100-marker local run with guarded background launcher','files':files},indent=2)+'\n')
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
