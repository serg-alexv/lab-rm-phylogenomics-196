"""Publish an immutable portable stage01 snapshot, preserving exact bytes."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, io, json, subprocess, zipfile
R=Path(__file__).resolve().parents[1]
def run(args):
    p=subprocess.run(args,cwd=R,capture_output=True,check=True)
    return p.stdout

def sha(b): return hashlib.sha256(b).hexdigest()
# Disable Git line-ending transformation: checksums are over actual delivered bytes.
(R/'.gitattributes').write_bytes(b'* -text\n')
# Mutable status/publication receipts are deliberately not included in stage payload hashes.
files=[p for d in ['config','evidence','reports/stage01'] for p in (R/d).rglob('*') if p.is_file() and p.name not in ['SHA256SUMS.txt','publication_receipt.json']]
manifest=''.join(sha(p.read_bytes())+'  '+p.relative_to(R).as_posix()+'\n' for p in sorted(files))
(R/'reports/stage01/SHA256SUMS.txt').write_bytes(manifest.encode())
run(['git','add','--renormalize','.'])
run(['git','add','--','AGENTS.md','scripts/publish_panel_freeze.py','.gitattributes','reports/stage01/SHA256SUMS.txt'])
run(['git','commit','-m','Preserve exact artifact bytes; stabilize stage01 checksum scope and execution rules'])
run(['git','push','origin','main'])
commit=run(['git','rev-parse','HEAD']).decode().strip()
remote=run(['git','ls-remote','origin','refs/heads/main']).decode().split()[0]
assert commit==remote,'Remote commit verification failed'
# Re-read the committed payload independently through git archive, not working-tree existence.
committed=run(['git','archive','--format=zip',commit])
with zipfile.ZipFile(io.BytesIO(committed)) as z:
    for line in manifest.splitlines():
        digest,name=line.split('  ',1)
        assert sha(z.read(name))==digest, 'Committed checksum mismatch: '+name
stage=R/'release_staging';stage.mkdir(exist_ok=True)
p=stage/'stage01-approved196.zip'
with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for item in sorted(files+[R/'reports/stage01/SHA256SUMS.txt',R/'README.md',R/'WORK_ORDER.md',R/'AGENTS.md']):
        z.write(item,item.relative_to(R).as_posix())
with zipfile.ZipFile(p) as z: assert z.testzip() is None
asset_hash=sha(p.read_bytes())
sidecar=stage/'stage01-approved196.zip.sha256';sidecar.write_bytes((asset_hash+'  '+p.name+'\n').encode())
tag='stage01-approved196-v1'
run(['gh','release','create',tag,str(p),str(sidecar),'--repo','serg-alexv/lab-rm-phylogenomics-196','--target',commit,'--title','Stage 01: approved196 panel freeze','--notes','Executed on WD. Approved196 metadata freeze; no biological pilot and no sequence results yet. ZIP includes exact panel, G0 source evidence, executed validation and hashes. Historical G0 pending labels are retained; config/approval.json records subsequent human approval.'])
info=json.loads(run(['gh','api','repos/serg-alexv/lab-rm-phylogenomics-196/releases/tags/'+tag]))
a=next(x for x in info['assets'] if x['name']==p.name)
assert a['size']==p.stat().st_size
# Actual independent receiving-side download, not only the upload command exit code.
down=stage/'stage01-readback';down.mkdir(exist_ok=True)
run(['gh','release','download',tag,'--repo','serg-alexv/lab-rm-phylogenomics-196','--pattern',p.name,'--dir',str(down)])
assert sha((down/p.name).read_bytes())==asset_hash
receipt={'status':'UPLOAD_VERIFIED','utc':datetime.now(timezone.utc).isoformat(),'commit':commit,'release_tag':tag,'url':info['html_url'],'asset_name':p.name,'bytes':p.stat().st_size,'sha256':asset_hash,'committed_payload_hashes_tested':len(files),'github_download_readback_sha256_match':True}
(R/'reports/stage01/publication_receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
rows=[]
with (R/'status/stages.tsv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f,delimiter='\t'))
for row in rows:
    if row['stage']=='1_panel_freeze': row['publication']='UPLOAD_VERIFIED'
with (R/'status/stages.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n'); w.writeheader(); w.writerows(rows)
(R/'STATUS.md').write_bytes(('# Current execution status\n\nStage1: PASS_APPROVED_PANEL_FREEZE, UPLOAD_VERIFIED. 196 exact-version accessions; no pilot. Environment setup STARTING; stages2-7 NOT_RUN.\n\nStage1 release: '+info['html_url']+'\n\nSee reports/stage01/publication_receipt.json, reports/stage01/REPORT.md and status/stages.tsv.\n').encode())
run(['git','add','--','reports/stage01/publication_receipt.json','status/stages.tsv','STATUS.md'])
run(['git','commit','-m','Verify stage01 GitHub download/hash receipt and mark publication complete'])
run(['git','push','origin','main'])
print(json.dumps(receipt))
