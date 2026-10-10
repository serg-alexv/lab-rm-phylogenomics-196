from pathlib import Path
import base64, csv, datetime, hashlib, json, subprocess
W=Path(__file__).resolve().parent
G=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
P=W/'local_pilot_complete84'
V=W/'pilot_final_validation84'
R=G/'reports/stage01/local_pilot_20261010/completed'
expected='cc5106a620f14cb142fb17bc60c18a76bd3ecbe7'
assert not P.exists() and not R.exists()
report=json.loads((V/'validation_report.json').read_text())
closure=json.loads((W/'pilot_closure84.json').read_text())
assert report['status']=='PASS' and report['astral_result']['tip_count']==196
assert closure['terminal']['exit_code']==0 and not closure['windows_launcher_present']
assert not closure['linux']['owned_processes_remaining'] and closure['original_lock_exclusive_read_opened_and_released']
for path,digest in report['input_sha256'].items():
    assert hashlib.sha256((G/path).read_bytes()).hexdigest()==digest,path
for name,digest in report['artifact_sha256'].items():
    assert hashlib.sha256((V/name).read_bytes()).hexdigest()==digest,name
P.mkdir();R.mkdir()
def new(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(data if isinstance(data,bytes) else data.encode())
for source in V.iterdir():
    if source.is_file():new(R/source.name,source.read_bytes())
flat=G/'pilot_output/species_tree.itol_quartet_frequency.newick'
new(flat,(V/flat.name).read_bytes())
support=list(csv.DictReader((V/'astral_quartet_support_by_split.tsv').open(),delimiter='\t'))
q=[float(r['q1_quartet_frequency']) for r in support]
en=[float(r['EN_effective_number_of_genes']) for r in support]
summary={'state':'PILOT_COMPLETE_VALIDATED','markers':5,'taxa':196,'finished_utc':closure['terminal']['finished_utc'],
 'raw_tree_sha256':report['artifact_sha256']['species_tree.newick'],
 'flat_q1_tree_sha256':report['artifact_sha256'][flat.name],
 'informative_splits':len(support),'q1_min':min(q),'q1_max':max(q),'effective_gene_count_min':min(en),'effective_gene_count_max':max(en),
 'full_pipeline_started':False,'inference_restarted':False,'forbidden_validator_accessed':False,
 'itol_state':'PENDING_PILOT_TREE_UPLOAD','host_defense_mapping_available':False}
new(R/'completion_summary.json',json.dumps(summary,indent=2)+'\n')
new(R/'RESULT.md','''# Five-marker pilot completed and validated

The original approved Bash attempt02 exited0 on2026-10-10 at08:36:34 UTC
(11:36:34 Europe/Moscow). All five IQ-TREE markers and ASTRAL completed locally.
No inference was restarted. The original lock was opened exclusively after exit
and released without changing its bytes; the owned runner processes are gone.

Species tree: pilot_output/species_tree.newick,196 unique approved accessions.
All973 input records retain their exact ungapped sequences through alignment.
Each gene tree matches its own FASTA taxa, and all_gene_trees.tre is their exact
byte concatenation. All five native reports confirm1000 UFBoot replicates.

The independent pre-existing v2 validator passed all193 informative ASTRAL splits.
Raw structured ASTRAL output is preserved. A separate iTOL Newick uses numeric q1
quartet frequencies and preserves topology and branch lengths; q1 is not pp1.
ASTRAL warns about limited effective gene counts (4-5), so this five-locus pilot
establishes workflow integrity, not production phylogenetic reliability.
Native terminal branch lengths are absent where ASTRAL did not estimate them.
Unlabeled IQ-TREE supports remain explicitly unlabeled in the validation report.

scripts/validate_pipeline.py was not accessed, changed, or executed. The existing
run_pipeline.sh was not replaced. Full100-marker execution remains unapproved;
only five input FASTAs are staged. Missing cell_mapping.tsv means host and defense
decorations cannot yet be generated. Pilot-tree iTOL upload is the next requested
step and will use a separate pilot name, preserving the production boundary.
''')
files=[]
def add(source,target,freeze=False):
    data=source.read_bytes()
    if freeze:
        dest=P/'frozen'/target;new(dest,data);assert source.read_bytes()==data;source=dest
    row={'local_absolute_path':str(source),'target':target,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    if target.endswith('.gz'):row['transport_encoding']='base64'
    files.append(row)
for source in sorted((G/'pilot_output').rglob('*')):
    if source.is_file():add(source,source.relative_to(G).as_posix(),True)
for source in sorted(R.iterdir()):
    if source.is_file():add(source,source.relative_to(G).as_posix())
for suffix in ['mafft','iqtree','astral']:
    source=G/f'reports/stage01/pilot_{suffix}.log';add(source,source.relative_to(G).as_posix(),True)
for name in ['launch.json','terminal.json','console.log']:
    source=G/'reports/stage01/local_pilot_20261010/attempt02'/name;add(source,source.relative_to(G).as_posix(),True)
for folder,num in [('pilot_marker04_validation83',4),('pilot_marker05_validation84',5)]:
    for source in sorted((W/folder).iterdir()):
        if source.is_file():add(source,f'reports/stage01/local_pilot_20261010/marker{num:02d}/'+source.name)
add(W/'pilot_closure84.json','reports/stage01/local_pilot_20261010/completed/closure.json')
add(W/'local_pilot82/remote_readback.json','reports/stage01/local_pilot_20261010/progress/local_pilot82/remote_readback.json')
base=json.loads(subprocess.run(['gh','api','repos/serg-alexv/lab-rm-phylogenomics-196/contents/STATUS.md?ref='+expected],capture_output=True,check=True).stdout)
history=base64.b64decode(base['content']).decode().split('\n\n',2)[2]
status='# Current request: completed local five-marker pilot\n\nPILOT_COMPLETE_VALIDATED. Five gene trees and ASTRAL completed locally;196 approved tips and193 informative splits validated. Raw and flat-q1 trees are preserved. Native exit0, process closure and original lock release are verified. Pilot iTOL upload pending; host/defense mapping absent. Full100-marker execution remains unapproved. See [completion report](reports/stage01/local_pilot_20261010/completed/RESULT.md).\n\n'+history
new(P/'STATUS.md',status);add(P/'STATUS.md','STATUS.md')
add(Path(__file__),'scripts/master_run/publish_completed_pilot84.py')
assert len({r['target'] for r in files})==len(files)
new(P/'git_plan.json',json.dumps({'expected_head':expected,'message':'Publish completed five-marker pilot,196-tip ASTRAL tree and independent validation','files':files},indent=2)+'\n')
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files),**summary}))
