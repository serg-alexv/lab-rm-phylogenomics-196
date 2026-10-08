"""Resumed production on WD. No historical bootstrap and no biological pilot."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import csv, hashlib, json, os, platform, shutil, socket, subprocess, sys, time, zipfile
import msvcrt
R=Path(__file__).resolve().parents[1]
os.chdir(R)
REPO='serg-alexv/lab-rm-phylogenomics-196'
WORK=R/'.work'; WORK.mkdir(exist_ok=True)
LOG=R/'reports/stage00/commands.jsonl'

def now(): return datetime.now(timezone.utc).isoformat()
def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def atomic(p,b):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+'.tmp');q.write_bytes(b);q.replace(p)
def js(p,x): atomic(p,(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def run(a,timeout=180,check=True):
    t=time.monotonic(); started=now()
    p=subprocess.run(a,cwd=R,capture_output=True,timeout=timeout)
    out=p.stdout.decode('utf-8',errors='replace').replace('\x00','');err=p.stderr.decode('utf-8',errors='replace').replace('\x00','')
    LOG.parent.mkdir(parents=True,exist_ok=True)
    with LOG.open('a',encoding='utf-8') as f:
        f.write(json.dumps({'utc':started,'argv':[str(s) for s in a],'exit_code':p.returncode,'elapsed_seconds':round(time.monotonic()-t,3),'stdout':out,'stderr':err},ensure_ascii=False)+'\n')
    if check and p.returncode: raise RuntimeError(f'Command exit {p.returncode}: {a}; {err[-1600:]}')
    return out

def status(stage,execution,validation,publication,detail):
    p=R/'status/stages.tsv'
    with p.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f,delimiter='\t'))
    for row in rows:
        if row['stage']==stage: row.update(execution=execution,validation=validation,publication=publication)
    import io
    b=io.StringIO();w=csv.DictWriter(b,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
    atomic(p,b.getvalue().encode())
    s='# Current execution status\n\nUpdated '+now()+'. Full approved196 production cohort; no pilot.\n\n'+detail+'\n\n'
    s+='| Stage | Execution | Validation | Publication |\n|---|---|---|---|\n'
    s+=''.join('| '+' | '.join(row.values())+' |\n' for row in rows)
    s+='\nSee stage reports and separate publication receipts. Raw private session logs are excluded.\n'
    atomic(R/'STATUS.md',s.encode())

def commit(paths,message):
    for item in paths:
        if not (R/item).exists(): raise RuntimeError('Allowlist path absent: '+item)
    run(['git','add','--']+paths)
    staged=run(['git','diff','--cached','--name-only']).splitlines()
    if any(x.startswith(('.private_run/','.tools/','.work/','data/raw_ncbi/','release_staging/')) for x in staged): raise RuntimeError('Forbidden staged file')
    if staged: run(['git','commit','-m',message])
    run(['git','push','origin','main'])
    head=run(['git','rev-parse','HEAD']).strip()
    assert run(['git','ls-remote','origin','refs/heads/main']).split()[0]==head
    return head

def publish_stage0():
    global LOG
    run(['git','fetch','origin','main']);run(['git','pull','--ff-only','origin','main'])
    assert socket.gethostname().lower()=='wd'
    assert run(['gh','api','user','--jq','.login']).strip()=='serg-alexv'
    approved=json.loads((R/'config/approval.json').read_text())
    assert approved['human_approval']=='APPROVED_FOR_SEQUENCE_ANALYSIS' and approved['pilot'] is False
    assert digest(R/'config/approved_accessions.txt')==approved['panel_accessions_sha256']
    assert len(set((R/'config/approved_accessions.txt').read_text().split()))==196
    assert json.loads((R/'reports/stage01/publication_receipt.json').read_text())['status']=='UPLOAD_VERIFIED'
    ps="$o=Get-CimInstance Win32_OperatingSystem; [pscustomobject]@{host=(hostname);os=$o.Caption;total_ram_bytes=([int64]$o.TotalVisibleMemorySize*1024);free_ram_bytes=([int64]$o.FreePhysicalMemory*1024);free_disk_bytes=(Get-PSDrive C).Free;process_count=(Get-Process).Count} | ConvertTo-Json -Compress"
    env=json.loads(run(['powershell','-NoProfile','-Command',ps]))
    wsl=run(['wsl','-d','Ubuntu','--','bash','-lc','hostname; uname -a; free -m; df -h /; command -v python3; command -v curl; for t in micromamba conda hmmsearch GToTree mafft trimal iqtree iqtree2 padloc defense-finder; do command -v "$t" || true; done'],timeout=90)
    version=run([str(R/'.tools/datasets.exe'),'version']).strip()
    helptext=run([str(R/'.tools/datasets.exe'),'download','genome','accession','--help'])
    atomic(R/'reports/stage00/datasets_download_help.txt',helptext.encode())
    env.update(utc=now(),python_version=platform.python_version(),datasets_version=version,datasets_binary_sha256=digest(R/'.tools/datasets.exe'),wsl_probe=wsl,download_jobs=1,compute_thread_limit=2,toolchain_status='ACQUISITION_READY; downstream tools absent from WSL PATH and require isolated installation',cpu_seconds=None,peak_ram_bytes=None,resource_measurement_limit='Snapshot RAM/disk; command elapsed recorded. No peak monitor yet.',environment_scope='Stage00 validates acquisition readiness, not successful installation or execution of downstream scientific tools',workflow_pid=os.getpid(),model_cli_record='See sanitized outer execution receipt; actual API usage unavailable',source_urls=['https://www.ncbi.nlm.nih.gov/datasets/docs/v2/command-line-tools/download-and-install/'])
    assert env['free_disk_bytes']>10*1024**3
    js(R/'reports/stage00/environment.json',env)
    atomic(R/'reports/stage00/REPORT.md',('# Stage00: measured acquisition preflight\n\nExecuted on WD at '+now()+'. Stage01 immutable payload and receipt were independently checked (71 files, 196 exact accessions); no bootstrap repeated. GitHub identity serg-alexv and main reconciled.\n\nWindows free RAM '+str(env['free_ram_bytes'])+' bytes; C free disk '+str(env['free_disk_bytes'])+' bytes. One sequential NCBI download; at most two compute threads. No unrelated processes stopped. Ubuntu inspected: Python/curl available; downstream scientific tools absent from PATH. Their installation and database pinning remain pending, explicitly recorded.\n\nOfficial NCBI Datasets '+version+' is acquisition-ready; exact binary SHA256 and actual --help retained. The six requested file roles are genome, protein, CDS, GFF3, GBFF and sequence report. Exact version accessions only; --assembly-version all permits archived explicit versions, with returned membership checked.\n\nValidation: input SHA256/196 uniqueness, stage01 verified receipt, WD identity, authenticated user, remote commit, >10GiB disk and actual CLI help passed. Independent checker report is included. No sequence QC, phylogeny or R-M results are claimed.\n\nMethods source: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/command-line-tools/download-and-install/\n').encode())
    js(R/'reports/stage00/validation_results.json',{'utc':now(),'status':'PASS_ACQUISITION_PREFLIGHT','panel_count':196,'remote_identity':'serg-alexv','host':'wd','no_pilot':True,'downstream_tools':'PENDING_INSTALLATION'})
    run([sys.executable,str(R/'scripts/validate_stage00.py')])
    status('0_environment','COMPLETED','PASS_ACQUISITION_PREFLIGHT','PENDING','Stage00 acquisition preflight passed. Stage01 remains verified. Stage02 starts after stage00 release bytes are verified. Downstream tool environments are pending installation.')
    files=[p for p in (R/'reports/stage00').iterdir() if p.is_file() and p.name not in ('SHA256SUMS.txt','publication_receipt.json','commands.jsonl')]
    files += [R/'scripts/production_resume.py',R/'scripts/validate_stage00.py']
    manifest=''.join(digest(p)+'  '+p.relative_to(R).as_posix()+'\n' for p in sorted(files))
    atomic(R/'reports/stage00/SHA256SUMS.txt',manifest.encode())
    head=commit(['scripts/production_resume.py','scripts/validate_stage00.py','reports/stage00','STATUS.md','status/stages.tsv'],'Record measured WD acquisition preflight; resume full196 production')
    stage=R/'release_staging';stage.mkdir(exist_ok=True);asset=stage/'stage00-acquisition-preflight.zip'
    with zipfile.ZipFile(asset,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[R/'reports/stage00/SHA256SUMS.txt',R/'WORK_ORDER.md',R/'AGENTS.md']: z.write(p,p.relative_to(R).as_posix())
    with zipfile.ZipFile(asset) as z: assert z.testzip() is None
    h=digest(asset); side=asset.with_suffix('.zip.sha256');atomic(side,(h+'  '+asset.name+'\n').encode())
    tag='stage00-acquisition-preflight-v1'
    exists=subprocess.run(['gh','release','view',tag,'--repo',REPO],capture_output=True).returncode==0
    if not exists: run(['gh','release','create',tag,str(asset),str(side),'--repo',REPO,'--target',head,'--title','Stage00: WD acquisition preflight','--notes','Measured acquisition readiness for the approved full196 production cohort. Downstream tools require installation. No biological pilot or sequence results.'],timeout=300)
    info=json.loads(run(['gh','api','repos/'+REPO+'/releases/tags/'+tag]))
    a=next(a for a in info['assets'] if a['name']==asset.name);assert a['size']==asset.stat().st_size
    down=stage/'stage00-readback';down.mkdir(exist_ok=True)
    run(['gh','release','download',tag,'--repo',REPO,'--pattern',asset.name,'--dir',str(down),'--clobber'],timeout=300)
    assert digest(down/asset.name)==h
    with zipfile.ZipFile(down/asset.name) as z:
        assert z.testzip() is None
        for line in manifest.splitlines():
            hh,nn=line.split('  ',1);assert hashlib.sha256(z.read(nn)).hexdigest()==hh
    js(R/'reports/stage00/publication_receipt.json',{'status':'UPLOAD_VERIFIED','utc':now(),'commit':head,'release_tag':tag,'url':info['html_url'],'bytes':asset.stat().st_size,'sha256':h,'download_readback_sha256_match':True,'zip_crc_and_member_manifest_match':True})
    status('0_environment','COMPLETED','PASS_ACQUISITION_PREFLIGHT','UPLOAD_VERIFIED','Stage00 release downloaded and hashes/ZIP CRC verified. Stage01 remains verified. Full196 retrieval is starting; downstream installation remains pending.')
    commit(['reports/stage00/publication_receipt.json','STATUS.md','status/stages.tsv'],'Verify stage00 portable ZIP publication')
    print('STAGE00 UPLOAD_VERIFIED',flush=True)

def safe_extract(z,target):
    for item in z.infolist():
        p=PurePosixPath(item.filename)
        if p.is_absolute() or '..' in p.parts or '\\' in item.filename or ':' in item.filename or (item.external_attr>>16)&0o170000==0o120000: raise RuntimeError('Unsafe ZIP member '+item.filename)
        dest=(target/item.filename).resolve()
        if not dest.is_relative_to(target.resolve()): raise RuntimeError('ZIP escapes workspace')
    z.extractall(target)

def acquire():
    global LOG
    LOG=R/'reports/stage02/commands.jsonl';LOG.parent.mkdir(parents=True,exist_ok=True)
    run(['git','fetch','origin','main']);run(['git','pull','--ff-only','origin','main'])
    accessions=(R/'config/approved_accessions.txt').read_text().split(); assert len(accessions)==len(set(accessions))==196
    code=digest(Path(__file__));tool=digest(R/'.tools/datasets.exe'); inp=digest(R/'config/approved_accessions.txt')
    raw=R/'data/raw_ncbi';raw.mkdir(parents=True,exist_ok=True)
    rows=[]
    status('2_sequences','RUNNING','NOT_RUN','PROGRESS_PUBLISHED','Full196 exact-accession production retrieval is running, sequentially. Package audit is recorded separately from scientific sequence QC. No genomes omitted; stages3-7 have not run.')
    commit(['STATUS.md','status/stages.tsv'],'Start actual full196 NCBI sequence acquisition')
    started=time.monotonic()
    for index,acc in enumerate(accessions,1):
        target=raw/acc; target.mkdir(exist_ok=True); zp=target/(acc+'.ncbi.zip'); checkpoint=target/'retrieval_checkpoint.json'
        if checkpoint.exists():
            record=json.loads(checkpoint.read_text())
            if record.get('input_sha256')==inp and record.get('datasets_sha256')==tool and zp.exists() and digest(zp)==record['zip_sha256']:
                rows.append(record); print(f'REUSE {index}/196 {acc}',flush=True); continue
        tmp=target/(acc+'.partial.zip'); cmd=[str(R/'.tools/datasets.exe'),'download','genome','accession',acc,'--assembly-version','all','--include','genome,protein,cds,gff3,gbff,seq-report','--no-progressbar','--filename',str(tmp)]
        t=time.monotonic();success=False;errs=[]
        for attempt,delay in enumerate([0,5,15],1):
            if delay: time.sleep(delay)
            try:
                run(cmd,timeout=900)
                with zipfile.ZipFile(tmp) as z:
                    assert z.testzip() is None,'ZIP CRC failure'
                    names=z.namelist(); reports=[n for n in names if n.endswith('/assembly_data_report.jsonl')]
                    assert len(reports)==1,'Assembly report missing/ambiguous'
                    data=[json.loads(x) for x in z.read(reports[0]).decode().splitlines() if x.strip()]
                    assert [x['accession'] for x in data]==[acc],'Requested/returned exact accession mismatch'
                    assert any(n.endswith('dataset_catalog.json') for n in names),'Catalog absent'
                    extracted=target/'package';extracted.mkdir(exist_ok=True);safe_extract(z,extracted)
                    members=[{'member':n,'bytes':z.getinfo(n).file_size,'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in names if not n.endswith('/')]
                tmp.replace(zp);success=True;break
            except Exception as e:
                errs.append({'attempt':attempt,'error':str(e)});print('RETRY',acc,str(e)[-400:],flush=True)
        record={'accession':acc,'index':index,'utc':now(),'status':'RETRIEVED_PACKAGE_AUDITED' if success else 'FAILED','scientific_validation':'NOT_RUN','zip_bytes':zp.stat().st_size if success else None,'zip_sha256':digest(zp) if success else None,'input_sha256':inp,'code_sha256':code,'datasets_sha256':tool,'elapsed_seconds':round(time.monotonic()-t,3),'attempt_errors':errs,'member_count':len(members) if success else None}
        js(checkpoint,record)
        if success: js(target/'member_manifest.json',members)
        rows.append(record)
        js(R/'reports/stage02/retrieval_progress.json',{'utc':now(),'approved':196,'retrieved':sum(x['status']=='RETRIEVED_PACKAGE_AUDITED' for x in rows),'failed':sum(x['status']=='FAILED' for x in rows),'remaining':196-index,'elapsed_seconds':round(time.monotonic()-started,3),'workflow_pid':os.getpid(),'input_sha256':inp,'scientific_validation':'NOT_RUN','assemblies':rows})
        print(f'{index}/196 {acc} {record["status"]} bytes={record["zip_bytes"]}',flush=True)
        if index%10==0 or not success or index==196:
            status('2_sequences','RUNNING','NOT_RUN','PROGRESS_PUBLISHED',f'Full196 retrieval: {sum(x["status"]=="RETRIEVED_PACKAGE_AUDITED" for x in rows)}/196 packages retrieved and ZIP-audited; {sum(x["status"]=="FAILED" for x in rows)} failed; independent sequence validation not yet run. PID {os.getpid()}.')
            commit(['reports/stage02/retrieval_progress.json','STATUS.md','status/stages.tsv'],'Record measured full196 retrieval progress '+str(index)+'/196')
        if not success: raise RuntimeError('Exact accession retrieval failed after bounded retries: '+acc)
    status('2_sequences','RETRIEVED','NOT_RUN','PROGRESS_PUBLISHED','All196 packages retrieved and ZIP-audited. Independent biological file/annotation validation is still required before stage02 completion or downstream work.')
    commit(['reports/stage02/retrieval_progress.json','reports/stage02/commands.jsonl','STATUS.md','status/stages.tsv'],'Record all196 raw packages retrieved; scientific QC pending')

if __name__=='__main__':
    lock=(WORK/'workflow.lock').open('a+b');lock.seek(0)
    if lock.read(1)==b'': lock.write(b'0');lock.flush()
    lock.seek(0)
    try: msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError: raise SystemExit('Competing workflow lock held; inspect owner, no duplicate launch')
    js(WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':now(),'script':str(Path(__file__)),'scope':'stage00 then full196 retrieval','outer_session_lock_is_distinct':True})
    try:
        receipt=R/'reports/stage00/publication_receipt.json'
        if not receipt.exists() or json.loads(receipt.read_text()).get('status')!='UPLOAD_VERIFIED': publish_stage0()
        acquire()
    except Exception as e:
        js(R/'status/workflow_failure.json',{'utc':now(),'pid':os.getpid(),'error':str(e),'no_downstream_completion_claimed':True})
        print('FAILED',str(e),flush=True)
        try:
            stage='2_sequences' if LOG.parent.name=='stage02' else '0_environment'
            status(stage,'FAILED','NOT_PASS','FAILED_OR_INCOMPLETE','Concrete execution failure: '+str(e)+'. Outputs preserved; inspect status/workflow_failure.json. No downstream completion claimed.')
            commit(['status/workflow_failure.json','STATUS.md','status/stages.tsv'],'Record explicit production execution failure')
        except Exception as pe: print('Failure receipt publication also failed:',pe,flush=True)
        raise
    finally:
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
