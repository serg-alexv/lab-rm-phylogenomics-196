"""Independent post-restart cache audit. Input ZIPs and extracted sources remain unchanged."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import json,hashlib,zipfile,socket,os,msvcrt,subprocess
import production_resume as w
from workflow_publication import commit
R=w.R;w.LOG=R/'reports/stage02/commands.jsonl'
def sha(p):return w.digest(p)
def main():
    assert socket.gethostname().lower()=='wd'
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    inp=sha(R/'config/approved_accessions.txt');tool=sha(R/'.tools/datasets.exe')
    approved=json.loads((R/'config/approval.json').read_text());assert inp==approved['panel_accessions_sha256'] and approved['pilot'] is False
    accessions=(R/'config/approved_accessions.txt').read_text().split();rows=[];errors=[];pending=[]
    for acc in accessions:
        folder=R/'data/raw_ncbi'/acc;zp=folder/(acc+'.ncbi.zip');cp=folder/'retrieval_checkpoint.json'
        if not zp.exists():pending.append(acc);continue
        try:
            record=json.loads(cp.read_text());assert record['input_sha256']==inp and record['datasets_sha256']==tool
            assert sha(zp)==record['zip_sha256']
            manifest=json.loads((folder/'member_manifest.json').read_text());hashes={x['member']:x for x in manifest}
            with zipfile.ZipFile(zp) as z:
                assert z.testzip() is None
                names=z.namelist();assert len(set(names))==len(names)
                for n in names:
                    p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts and '\\' not in n and ':' not in n
                dirs={PurePosixPath(n).parts[2] for n in names if n.startswith('ncbi_dataset/data/GCF_')};assert dirs=={acc}
                data=[json.loads(x) for x in z.read(next(n for n in names if n.endswith('assembly_data_report.jsonl'))).splitlines()];assert len([x for x in data if x['accession']==acc])==1
                md5=0
                for line in z.read('md5sum.txt').decode().splitlines():
                    h,n=line.split(None,1);n=n.lstrip('*').removeprefix('./');assert hashlib.md5(z.read(n)).hexdigest()==h;md5+=1
                for n in names:
                    if n.endswith('/'):continue
                    b=z.read(n);assert hashlib.sha256(b).hexdigest()==hashes[n]['sha256'] and len(b)==hashes[n]['bytes']
                    assert sha(folder/'package'/n)==hashes[n]['sha256'],'Extracted file mismatch '+n
            rows.append({'accession':acc,'status':'PASS_CACHE_ARCHIVE_AND_EXTRACTED_MEMBERS','zip_sha256':record['zip_sha256'],'zip_bytes':zp.stat().st_size,'members':len(manifest),'provider_md5_checks':md5,'code_sha256_from_checkpoint':record['code_sha256']})
        except Exception as e:errors.append({'accession':acc,'error':str(e)})
    ps="$o=Get-CimInstance Win32_OperatingSystem; [pscustomobject]@{boot_utc=$o.LastBootUpTime.ToUniversalTime().ToString('o');total_ram_bytes=([int64]$o.TotalVisibleMemorySize*1024);free_ram_bytes=([int64]$o.FreePhysicalMemory*1024);free_disk_bytes=(Get-PSDrive C).Free} | ConvertTo-Json -Compress"
    resource=json.loads(w.run(['powershell','-NoProfile','-Command',ps]))
    result={'utc':w.now(),'host':'wd','interruption':'User/parent identified Windows restart at 15:02MSK, 2026-10-08; old workflow PID39828 absent and advisory lock acquired','old_workflow_pid':39828,'recovery_pid':os.getpid(),'approved':196,'cached_reaudited':len(rows),'failed_cache_checks':len(errors),'missing':len(pending),'errors':errors,'cached':rows,'missing_accessions':pending,'resources':resource,'source_zip_and_extracted_evidence_preserved':True,'scientific_validation':'NOT_RUN_THIS_AUDIT','input_sha256':inp,'checker_sha256':sha(__file__)}
    w.js(R/'reports/stage02/restart_cache_audit.json',result)
    detail=f'Post-restart independent cache audit: {len(rows)}/196 exact packages retained; {len(errors)} cache failures; {len(pending)} missing. Retrieval currently INTERRUPTED, no scientific runner active; resuming only missing packages after this receipt. Scientific sequence QC pending.'
    w.status('2_sequences','INTERRUPTED','NOT_RUN','PROGRESS_PUBLISHED',detail)
    commit(['scripts/recover_restart.py','scripts/workflow_publication.py','reports/stage02/restart_cache_audit.json','STATUS.md','status/stages.tsv','status/continuation_execution_receipt.json'],'Audit and retain cached full196 packages after Windows restart')
    print(json.dumps({'retained':len(rows),'errors':errors,'missing':len(pending),'receipt_published':True}),flush=True)
    if errors:raise RuntimeError('Cache audit failures require review; no resumed download launched')
if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),'scope':'independent post-restart audit'})
    try:main()
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
