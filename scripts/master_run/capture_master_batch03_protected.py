"""Capture immutable protected inputs before the approved cold C leaf purge."""
from pathlib import Path
import hashlib,json,datetime
work=Path(__file__).resolve().parent
rows=json.loads((work/'master_cleanup_protected_before.json').read_text())
extra=[Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.tools\iqtree_windows_3_1_4\extracted\iqtree-3.1.4-Windows\bin\iqtree3.exe'),
 Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage04_phylogeny_v2\analyses\primary196\concatenated.faa'),
 Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\.work\stage04_phylogeny_v2\analyses\primary196\partitions.nex'),
 Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\status\run_control.json')]
def inspect(p):
 s=p.stat()
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 t=p.stat();assert(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns)
 return {'path':str(p),'bytes':s.st_size,'sha256':h}
result=[]
for old in rows:
 new=inspect(Path(old['path']));assert new==old,'Protected source/dirty file drift'
 result.append(new)
result += [inspect(p) for p in extra]
assert result[8]['sha256']=='43c9bf3b0dc5e7d88c183a2582369d22c9d692b7585350038769334bb6fd9aed'
assert result[9]['sha256']=='442742d083628ab5382a10cafc422c57084cd9bde45a4f2950f15e2c199e3307'
assert result[10]['sha256']=='fa640e5e984b33e73a86b1ec7a7c18f7161a12252e68e9e3c6ceb2644eb7edc5'
out=work/'master_batch03_protected_before.json';assert not out.exists()
with out.open('x',encoding='utf-8') as f:json.dump({'state':'PASS_PROTECTED_BYTES_UNCHANGED',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':result},f,indent=2);f.write('\n')
print(json.dumps({'state':'PASS_PROTECTED_BYTES_UNCHANGED','files':len(result),'G_mutations':0}))
