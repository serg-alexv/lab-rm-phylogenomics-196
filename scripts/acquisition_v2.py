"""Exact sequence-member audit with preserved version-history metadata, resuming cached cohort."""
import production_resume as w
from pathlib import Path, PurePosixPath
import json,zipfile,hashlib,time,os,sys,msvcrt
R=w.R;w.LOG=R/'reports/stage02/commands.jsonl'
from workflow_publication import commit as audited_commit
w.commit=audited_commit

def audit(zp,acc,target):
    with zipfile.ZipFile(zp) as z:
        assert z.testzip() is None,'ZIP CRC failure'
        names=z.namelist();report=next(n for n in names if n.endswith('/assembly_data_report.jsonl'))
        data=[json.loads(x) for x in z.read(report).splitlines() if x.strip()]
        exact=[x for x in data if x['accession']==acc];assert len(exact)==1,'Exact requested assembly report missing/duplicate'
        catname=next(n for n in names if n.endswith('dataset_catalog.json'))
        cat=json.loads(z.read(catname)); assemblies=[x for x in cat['assemblies'] if x.get('accession')]
        selected=[x for x in assemblies if x['accession']==acc]
        assert len(selected)==1,'Exact requested catalog assembly absent/duplicate'
        for extra in [x for x in assemblies if x['accession']!=acc]:
            assert extra['accession'].split('.')[0]==acc.split('.')[0],'Unrelated catalog assembly'
            assert not any('/'+extra['accession']+'/' in n for n in names),'Unapproved version has actual archive files'
        roles={x['fileType'] for x in selected[0]['files']}
        expected={'GENOMIC_NUCLEOTIDE_FASTA','PROTEIN_FASTA','CDS_NUCLEOTIDE_FASTA','GFF3','GENBANK_FLAT_FILE','SEQUENCE_REPORT'}
        assert expected<=roles,'Missing requested file role: '+str(expected-roles)
        directories={PurePosixPath(n).parts[2] for n in names if n.startswith('ncbi_dataset/data/GCF_')}
        assert directories=={acc},'Unexpected sequence directories '+str(directories)
        context=[x['accession'] for x in data if x['accession']!=acc]
        assert all(x.split('.')[0]==acc.split('.')[0] for x in context),'Unrelated assembly metadata returned'
        md5names=[n for n in names if PurePosixPath(n).name=='md5sum.txt']
        md5checked=0
        for name in md5names:
            for line in z.read(name).decode().splitlines():
                if not line.strip():continue
                hh,nn=line.split(None,1);nn=nn.lstrip('*').removeprefix('./')
                assert nn in names,'Provider MD5 member absent: '+nn
                assert hashlib.md5(z.read(nn)).hexdigest()==hh,'Provider MD5 mismatch: '+nn
                md5checked+=1
        extracted=target/'package';extracted.mkdir(exist_ok=True);w.safe_extract(z,extracted)
        members=[{'member':n,'bytes':z.getinfo(n).file_size,'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in names if not n.endswith('/')]
    w.js(target/'member_manifest.json',members)
    return context,md5checked,len(members)

def main():
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    inp=w.digest(R/'config/approved_accessions.txt');tool=w.digest(R/'.tools/datasets.exe');code=w.digest(Path(__file__))
    accessions=(R/'config/approved_accessions.txt').read_text().split();assert len(set(accessions))==len(accessions)==196
    rows=[];start=time.monotonic()
    w.status('2_sequences','RUNNING','NOT_RUN','PROGRESS_PUBLISHED','Resumed exact sequence retrieval after documented version-history metadata exception. Only requested sequence catalog/directory is accepted; raw historical report records retained. All196 remain required.')
    w.commit(['scripts/acquisition_v2.py','STATUS.md','status/stages.tsv'],'Resume exact196 retrieval; distinguish historical report context from sequence members')
    for i,acc in enumerate(accessions,1):
        target=R/'data/raw_ncbi'/acc;target.mkdir(parents=True,exist_ok=True)
        zp=target/(acc+'.ncbi.zip');tmp=target/(acc+'.partial.zip');cp=target/'retrieval_checkpoint.json';prior=json.loads(cp.read_text()) if cp.exists() else {}
        t=time.monotonic();errors=[];success=False
        if zp.exists() and prior.get('input_sha256')==inp and w.digest(zp)==prior.get('zip_sha256'):
            context,md5count,nmembers=audit(zp,acc,target);success=True
        elif tmp.exists():
            try:context,md5count,nmembers=audit(tmp,acc,target);tmp.replace(zp);success=True
            except Exception as e:errors.append({'cache_audit':str(e)})
        if not success:
            cmd=[str(R/'.tools/datasets.exe'),'download','genome','accession',acc,'--include','genome,protein,cds,gff3,gbff,seq-report','--no-progressbar','--filename',str(tmp)]
            for attempt,delay in enumerate([0,5,15],1):
                if delay:time.sleep(delay)
                try:
                    w.run(cmd,timeout=900);context,md5count,nmembers=audit(tmp,acc,target);tmp.replace(zp);success=True;break
                except Exception as e:errors.append({'attempt':attempt,'error':str(e)});print('RETRY',acc,str(e)[-350:],flush=True)
        record={'accession':acc,'index':i,'utc':w.now(),'status':'RETRIEVED_PACKAGE_AUDITED' if success else 'FAILED','scientific_validation':'NOT_RUN','zip_bytes':zp.stat().st_size if success else None,'zip_sha256':w.digest(zp) if success else None,'input_sha256':inp,'code_sha256':code,'datasets_sha256':tool,'elapsed_seconds':round(time.monotonic()-t,3),'original_retrieval_utc':prior.get('original_retrieval_utc',prior.get('utc')),'original_attempt_errors':prior.get('attempt_errors',[]),'attempt_errors':errors,'member_count':nmembers if success else None,'provider_md5_members_checked':md5count if success else None,'additional_version_metadata_preserved':context if success else None,'cpu_seconds':None,'peak_ram_bytes':None,'measurement_reason':'Command elapsed/snapshot RAM recorded; per-process peak unavailable'}
        w.js(cp,record);rows.append(record)
        w.js(R/'reports/stage02/retrieval_progress_resume.json',{'utc':w.now(),'approved':196,'retrieved':sum(x['status']=='RETRIEVED_PACKAGE_AUDITED' for x in rows),'failed':sum(x['status']=='FAILED' for x in rows),'remaining':196-i,'elapsed_seconds':round(time.monotonic()-start,3),'workflow_pid':os.getpid(),'input_sha256':inp,'scientific_validation':'NOT_RUN','assemblies':rows})
        print(f'{i}/196 {acc} {record["status"]} bytes={record["zip_bytes"]} md5={record["provider_md5_members_checked"]} history={record["additional_version_metadata_preserved"]}',flush=True)
        if i%10==0 or i==196 or not success:
            w.status('2_sequences','RUNNING' if success else 'FAILED','NOT_RUN','PROGRESS_PUBLISHED',f'Full196 retrieval: {sum(x["status"]=="RETRIEVED_PACKAGE_AUDITED" for x in rows)}/196 packages ZIP/catalog/provider-MD5 audited. {sum(x["status"]=="FAILED" for x in rows)} failed. Scientific QC pending. PID {os.getpid()}.')
            w.commit(['reports/stage02/retrieval_progress_resume.json','STATUS.md','status/stages.tsv'],'Publish measured exact196 retrieval progress '+str(i)+'/196')
        if not success:raise RuntimeError('Exact retrieval failed after bounded retries: '+acc)
    w.status('2_sequences','RETRIEVED','NOT_RUN','PROGRESS_PUBLISHED','All196 raw packages retrieved with exact sequence catalog membership and provider MD5 checks. Independent annotation/sequence validation and stage02 Release publication still pending.')
    w.commit(['reports/stage02/retrieval_progress_resume.json','reports/stage02/commands.jsonl','STATUS.md','status/stages.tsv'],'Record complete196 acquisition; independent scientific validation pending')

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0)
    try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:raise SystemExit('Workflow lock already held; no duplicate launch')
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),'scope':'resumed full196 retrieval'})
    try:main()
    except Exception as e:
        w.js(R/'status/workflow_failure_v2.json',{'utc':w.now(),'pid':os.getpid(),'error':str(e)})
        w.status('2_sequences','FAILED','NOT_PASS','INCOMPLETE',str(e)+'. Outputs preserved; no downstream completion claimed.')
        w.commit(['status/workflow_failure_v2.json','STATUS.md','status/stages.tsv'],'Record explicit resumed retrieval failure');raise
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
