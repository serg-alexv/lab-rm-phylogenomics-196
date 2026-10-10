from pathlib import Path
import base64,datetime,hashlib,json,subprocess
W=Path(__file__).resolve().parent
G=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
P=W/'itol_hotfix77'
HEAD='4b58e93f81a66ad0189d6e6ef54e0453e50b7617'
def new(p,b):
    with p.open('xb') as f:f.write(b)
def api(e):return json.loads(subprocess.run(['gh','api','repos/serg-alexv/lab-rm-phylogenomics-196/'+e],capture_output=True,check=True).stdout)
assert api('git/ref/heads/main')['object']['sha']==HEAD
assert not P.exists()
P.mkdir()
source=G/'scripts/make_itol_decorations.py'
doc='''# iTOL decoration hotfix

The user approved DATASET_BINARY with six colored square columns after the official iTOL heatmap template was checked: heatmaps use a shared gradient and cannot assign each binary column its own presence hue using FIELD_COLORS.

`scripts/make_itol_decorations.py` is a standalone, standard-library Python program. Its default input is project-root cell_mapping.tsv, with required columns GenomeID, Host, RM, Cas, Abi2, CBASS, BREX, Septu. The user's final exact template fixes output field order to RM, Cas, Abi2, CBASS, BREX, Septu regardless of input header order. Colors, configuration order, comments, blank lines and six-entry legend match that template. Missing, unknown, or nonbinary defense states cause failure, never conversion to absence. Duplicate genome IDs, malformed TSV rows, control characters and blank hosts are rejected.

The program writes exactly two files: pipeline_output/defense_systems_heatmap.txt (filename retained as requested; header DATASET_BINARY) and pipeline_output/host_colorstrip.txt (DATASET_COLORSTRIP). All configuration/data fields are tab-delimited. Presence uses each system's FIELD_COLORS hue; zero is an empty square, white on a white canvas. This binary format does not independently force the background color. Host colors are deterministic unique hexadecimal colors, with matching legends. Both output paths are checked before writing, and exclusive creation refuses overwrite.

No real decoration datasets have been produced: the canonical project-root cell_mapping.tsv does not exist, and historical R-M render-geometry grids do not implement this new eight-column input contract. Synthetic test results establish program behavior only, not defense-system or host evidence. No new host classifications or defense calls are fabricated. No GUI directions or automatic upload are included.

Official format references:
- https://itol.embl.de/help/dataset_binary_template.txt
- https://itol.embl.de/help/dataset_color_strip_template.txt
- https://itol.embl.de/help/dataset_heatmap_template.txt

The corrected local five-marker pilot remains running separately under the original workflow lock; the full pipeline remains unapproved. Its first marker was still in ModelFinder at 07:17 UTC. This hotfix does not interrupt or alter its inference command.
'''
new(P/'README.md',doc.encode())
files=[]
def add(p,t):
    b=p.read_bytes();files.append({'local_absolute_path':str(p),'target':t,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
add(source,'scripts/make_itol_decorations.py')
add(P/'README.md','reports/stage01/itol_hotfix_20261010/README.md')
testdir=W/'itol_hotfix_exact_tests02'
assert testdir.is_dir()
for p in sorted(testdir.rglob('*')):
    if p.is_file():add(p,'reports/stage01/itol_hotfix_20261010/tests/'+p.relative_to(testdir).as_posix())
add(W/'local_pilot76/remote_readback.json','reports/stage01/local_pilot_20261010/progress/local_pilot76/remote_readback.json')
add(Path(__file__),'scripts/master_run/prepare_itol_hotfix77.py')
new(P/'git_plan.json',(json.dumps({'expected_head':HEAD,'message':'Add validated TSV-to-iTOL binary defense and host decoration exporter','files':files},indent=2)+'\n').encode())
print(json.dumps({'files':len(files),'script_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'actual_defense_datasets_generated':False}))
