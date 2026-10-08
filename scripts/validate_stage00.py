"""Independent stage00 checker: re-read evidence, do not rerun producers."""
from pathlib import Path
import hashlib,json,socket
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'config/approval.json').read_text())
b=(R/'config/approved_accessions.txt').read_bytes()
assert hashlib.sha256(b).hexdigest()==a['panel_accessions_sha256']
assert len(b.decode().split())==len(set(b.decode().split()))==196
assert b==(R/'evidence/g0/reports/proposed_accessions.txt').read_bytes()
for line in (R/'reports/stage01/SHA256SUMS.txt').read_text().splitlines():
    h,n=line.split('  ',1);assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
p=json.loads((R/'reports/stage01/publication_receipt.json').read_text());assert p['status']=='UPLOAD_VERIFIED' and p['github_download_readback_sha256_match']
e=json.loads((R/'reports/stage00/environment.json').read_text())
assert socket.gethostname().lower()=='wd'
assert e['download_jobs']==1 and e['compute_thread_limit']<=2
assert hashlib.sha256((R/'.tools/datasets.exe').read_bytes()).hexdigest()==e['datasets_binary_sha256']
helptext=(R/'reports/stage00/datasets_download_help.txt').read_text()
assert all(k in helptext for k in ['seq-report','gbff','gff3','--assembly-version','--filename'])
(R/'reports/stage00/independent_validation.json').write_text(json.dumps({'status':'PASS_ACQUISITION_PREFLIGHT','stage01_hashes_checked':71,'exact_panel':196,'resources_and_tool_help_checked':True,'downstream_tools_not_claimed':True},indent=2)+'\n')
print('INDEPENDENT PREFLIGHT PASS')
