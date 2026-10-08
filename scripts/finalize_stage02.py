"""Publish executed full196 validation and standalone Windows ZIP batches."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,io,json,msvcrt,os,shutil,sys,time,zipfile
import production_resume as w
from workflow_publication import commit,check

R=w.R; REPO=w.REPO
w.LOG=R/'reports/stage02/publication_commands.jsonl'
QC=R/'.work/stage02_validated'; PUBLIC=R/'reports/stage02'
STAGE=R/'release_staging/stage02'; STAGE.mkdir(parents=True,exist_ok=True)
COMPACT=['assembly_qc.tsv','replicon_qc.tsv','review_exceptions.tsv','errors.tsv','member_sha256.tsv','validation_summary.json','negative_parser_tests.json']

def stream_hash(stream):
    h=hashlib.sha256()
    for b in iter(lambda:stream.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def make_zip(name,files,guide):
    dest=STAGE/name
    members=[]
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p,n in sorted(files,key=lambda x:x[1]):
            if p.is_symlink():raise ValueError('Symlink forbidden in portable archive: '+str(p))
            z.write(p,n);members.append((w.digest(p),n))
        z.writestr('README.txt',guide.encode())
        members.append((hashlib.sha256(guide.encode()).hexdigest(),'README.txt'))
        manifest=''.join(h+'  '+n+'\n' for h,n in members)
        z.writestr('SHA256SUMS.txt',manifest.encode())
    if dest.stat().st_size>=500*1024**2:raise ValueError('ZIP batch exceeds practical500MiB bound: '+name)
    verify_zip(dest)
    h=w.digest(dest)
    w.atomic(dest.with_suffix('.zip.sha256'),(h+'  '+name+'\n').encode())
    return {'asset_name':name,'bytes':dest.stat().st_size,'sha256':h,'payload_members':len(members)}

def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None,'ZIP CRC failure'
        names=z.namelist();assert len(names)==len(set(names))
        for n in names:
            p=Path(n);assert not p.is_absolute() and '..' not in p.parts and '\\' not in n and ':' not in n
            assert (z.getinfo(n).external_attr>>16)&0o170000!=0o120000
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            h,n=line.split('  ',1)
            with z.open(n) as stream:assert stream_hash(stream)==h,n

def main():
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    accessions=(R/'config/approved_accessions.txt').read_text().split()
    assert len(accessions)==len(set(accessions))==196
    summary=json.loads((QC/'validation_summary.json').read_text())
    assert summary['complete_exact196_accounting'] and summary['raw_packages_present']==196
    assert summary['validator_source_sha256']==w.digest(R/'scripts/validate_sequences.py')
    for n in COMPACT:shutil.copyfile(QC/n,PUBLIC/n)
    paths=['reports/stage02/'+n for n in COMPACT]
    if summary['error_count']:
        w.status('2_sequences','BLOCKED_SCIENTIFIC_VALIDATION','FAIL_SEQUENCE_VALIDATION','EVIDENCE_PUBLISHED',f'All196 raw packages acquired; independent validation found {summary["error_count"]} errors in {summary["assemblies_with_errors"]} assemblies. No dependent marker job permitted. See reports/stage02/errors.tsv.')
        commit(paths+['STATUS.md','status/stages.tsv'],'Publish explicit full196 sequence-validation errors; retain all genomes')
        raise RuntimeError('Sequence validation errors require source-evidence review')
    assert summary['status']=='PASS_SEQUENCE_INTEGRITY_WITH_DOCUMENTED_EXCEPTIONS'
    w.status('2_sequences','VALIDATED',summary['status'],'PREPARING_PORTABLE_RELEASE',f'All196 raw packages passed independent validation: zero errors, {summary["locus_map_rows_written"]} locus rows and {summary["review_exception_count"]} explicit source exceptions. Portable ZIP Release batches are being prepared; marker jobs wait for verified publication.')
    commit(paths+['scripts/finalize_stage02.py','STATUS.md','status/stages.tsv'],'Publish executed full196 sequence integrity results; prepare portable Release batches')
    for acc in accessions:
        result=json.loads((QC/'assemblies'/acc/'validation.json').read_text())
        assert result['error_count']==0 and result['assembly_accession']==acc
        assert w.digest(R/'data/raw_ncbi'/acc/(acc+'.ncbi.zip'))==result['raw_zip_sha256']
    with (PUBLIC/'assembly_qc.tsv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f,delimiter='\t'))
    assert [x['assembly_accession'] for x in rows]==accessions
    with (PUBLIC/'assembly_qc.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    paths.append('reports/stage02/assembly_qc.csv')
    guide=('Stage02 full196 sequence handoff. UTF-8 text and normal ZIP files; no WSL is required to open the biological files.\n'
           'Each batch is independently extractable on Windows. raw_ncbi/<assembly>/package/ncbi_dataset/data/<assembly>/ contains genomic FNA, primary protein FAA, CDS FNA, GFF, GBFF and sequence report.\n'
           'The original .ncbi.zip is preserved separately. Member hashes, provider MD5, catalog and assembly report remain evidence. Failed/interrupted earlier attempts are preserved under attempts/ and are NOT primary biological inputs.\n'
           'validation/<assembly>/validation.json records executed source/feature/protein checks and explicit pseudogene, partial, translation and historical metadata exceptions.\n'
           'SHA256SUMS.txt covers every payload member except the checksum manifest itself. Genome integrity and source taxonomy compatibility do not demonstrate ANI identity or R-M activity.\n'
           'The 196 exact assembly IDs and all biological sequence bytes remain unchanged.\n')
    report=('# Stage02: complete approved196 sequences and independent integrity validation\n\n'
            f'All196 exact-version assemblies were downloaded on WD with NCBI Datasets18.38.0. Independent validation reports zero errors and {summary["review_exception_count"]} explicit source annotation/metadata review exceptions. Full196 accounting passed; no assembly was dropped, replaced or used as a pilot.\n\n'
            f'Validation elapsed: {summary["elapsed_seconds"]:.3f}s. Python {summary["python_version"]}; BioPython {summary["biopython_version"]}; {summary["parser_test_count"]} parser self-tests, plus separately executed synthetic package tests in validator_review_evidence.json. This stage verifies file/feature/translation integrity and preserved taxonomy compatibility, not independent ANI or enzymatic function.\n\n'
            'The checker rereads raw provider ZIPs, catalog roles, provider MD5/member SHA256, genomic FASTA and sequence-report IDs/lengths, GBFF genomic sequences, protein/CDS/GFF/GBFF exact-locus joins, CDS frames/segment phases and source translations. It retains assembly+replicon+locus keys; repeated WP accessions do not collapse biological loci. GC, ambiguity, record count and replicon topology are in replicon_qc.tsv.\n\n'
            'Pseudogenes and documented translation exceptions remain explicit. Annotated codon_start offsets are applied only during CDS comparison. For documented 3-prime partial codons, virtual N ambiguity padding is used only as a validation operation; source sequence files are never altered. Omission is accepted only for an unresolved terminal X with an exactly matching complete-codon prefix. Internal mismatches fail.\n\n'
            'NCBI --assembly-version all was experimentally rejected when it returned unapproved historical biological files. Its failed raw attempt is retained. Subsequent retrieval used tested default exact-accession commands. The few earlier accepted packages retain historical metadata-only catalog/report entries, explicitly reviewed and excluded from biological membership. Archived metadata are not an alternative cohort.\n\n'
            'The Windows restart interrupted retrieval at79 packages; the independent restart audit preserved all79. Mutable progress replacement later encountered Windows file-sharing denial, so timestamped atomic progress receipts were used. No unrelated processes were stopped and no restart was requested by the workflow.\n\n'
            'Publication is checked separately from scientific validation. Standalone ZIP batches contain original provider ZIPs, extracted portable files, individual hashes and per-assembly validation. Full locus tables are Release assets to avoid giant Git blobs. Source/derived namespaces remain separate.\n\n'
            '[NCBI Datasets documentation](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/command-line-tools/download-and-install/) supplies the acquisition method; exact executed commands and tool/code/input hashes are retained in this repository and asset manifests.\n\n'
            'Stages3-7 remain not run at this payload freeze. Host filters are predeclared in config/host_primary.json before marker searches/topology.\n')
    w.atomic(PUBLIC/'REPORT.md',report.encode());paths.append('reports/stage02/REPORT.md')
    assets=[]
    for start in range(0,196,20):
        cohort=accessions[start:start+20];files=[]
        for acc in cohort:
            folder=R/'data/raw_ncbi'/acc
            for p in folder.rglob('*'):
                if not p.is_file() or p.name.endswith('.tmp'):continue
                rel=p.relative_to(folder).as_posix()
                if p.name.endswith('.partial.zip'):continue
                namespace='attempts/'+acc if 'attempt-' in p.name or 'interrupted-' in p.name else 'raw_ncbi/'+acc
                files.append((p,namespace+'/'+rel))
            files.append((QC/'assemblies'/acc/'validation.json','validation/'+acc+'/validation.json'))
        item=make_zip(f'stage02-raw-{start+1:03}-{start+len(cohort):03}.zip',files,guide)
        item['assemblies']=cohort;assets.append(item)
        print('ZIP_VALIDATED',item['asset_name'],item['bytes'],flush=True)
    files=[(QC/n,'derived_validation/'+n) for n in COMPACT+['locus_protein_map.tsv']]
    assets.append(make_zip('stage02-full196-derived-tables.zip',files,guide))
    script_names=['validate_sequences.py','validate_stage02_locked.py','finalize_stage02.py','acquisition_v2.py','recover_restart.py','workflow_publication.py','production_resume.py','stage_tool_packages.py','install_offline_tools.sh','wsl_project.sh']
    files=[(R/'scripts'/n,'scripts/'+n) for n in script_names]
    files += [(R/n,n) for n in ['WORK_ORDER.md','AGENTS.md','config/approval.json','config/approved_accessions.txt','config/approved_panel.tsv','config/host_primary.json']]
    files += [(PUBLIC/n,'reports/stage02/'+n) for n in COMPACT+['REPORT.md','assembly_qc.csv','VALIDATOR_REVIEW.md','validator_review_evidence.json','restart_cache_audit.json']]
    assets.append(make_zip('stage02-methods-and-reports.zip',files,guide))
    w.js(PUBLIC/'asset_manifest.json',{'stage':'stage02','scientific_validation':summary['status'],'approved_assembly_count':196,'approved_accessions_sha256':summary['approved_accessions_sha256'],'assets':assets,'portable_zip_member_checks':'SHA256 and ZIP CRC executed before upload','publication_receipt_separate':True})
    paths+=['reports/stage02/asset_manifest.json']+['scripts/'+n for n in script_names]+['config/host_primary.json']
    check(paths)
    stable=[R/p for p in paths]+[PUBLIC/'VALIDATOR_REVIEW.md',PUBLIC/'validator_review_evidence.json',PUBLIC/'restart_cache_audit.json']
    stable=sorted(set(stable))
    w.atomic(PUBLIC/'SHA256SUMS.txt',''.join(w.digest(p)+'  '+p.relative_to(R).as_posix()+'\n' for p in stable).encode())
    paths.append('reports/stage02/SHA256SUMS.txt')
    w.status('2_sequences','VALIDATED',summary['status'],'UPLOADING','All196 packages independently validated with zero errors and documented exceptions. Portable ZIP payloads locally CRC/member-hash checked. GitHub release upload/readback is pending; no marker job started.')
    head=commit(paths+['STATUS.md','status/stages.tsv'],'Validate all196 source genomes and freeze portable sequence ZIP manifests')
    tag='stage02-sequences196-v1'
    notes=PUBLIC/'RELEASE_NOTES.md';w.atomic(notes,(report+'\n'+guide).encode())
    exists=os.system('gh release view '+tag+' --repo '+REPO+' >NUL 2>NUL')==0
    if not exists:w.run(['gh','release','create',tag,'--repo',REPO,'--target',head,'--title','Stage02: validated full196 source sequences','--notes-file',str(notes)],timeout=300)
    readback=STAGE/'readback';readback.mkdir(exist_ok=True)
    receipts=[]
    info=json.loads(w.run(['gh','api','repos/'+REPO+'/releases/tags/'+tag]))
    for asset in assets:
        local=STAGE/asset['asset_name'];existing={a['name']:a for a in info['assets']}
        if asset['asset_name'] not in existing:
            w.run(['gh','release','upload',tag,str(local),str(local.with_suffix('.zip.sha256')),'--repo',REPO],timeout=1800)
        info=json.loads(w.run(['gh','api','repos/'+REPO+'/releases/tags/'+tag]))
        remote=next(a for a in info['assets'] if a['name']==asset['asset_name'])
        assert remote['size']==asset['bytes']
        if remote.get('digest'):assert remote['digest']=='sha256:'+asset['sha256']
        w.run(['gh','release','download',tag,'--repo',REPO,'--pattern',asset['asset_name'],'--dir',str(readback),'--clobber'],timeout=1800)
        assert w.digest(readback/asset['asset_name'])==asset['sha256']
        verify_zip(readback/asset['asset_name'])
        receipts.append({'asset_name':asset['asset_name'],'remote_asset_id':remote['id'],'bytes':remote['size'],'sha256':asset['sha256'],'download_readback_verified':True,'all_zip_member_hashes_verified':True})
        print('UPLOAD_READBACK_VERIFIED',asset['asset_name'],flush=True)
    remote_tag=w.run(['gh','api','repos/'+REPO+'/commits/'+tag,'--jq','.sha']).strip()
    assert remote_tag==head
    w.js(PUBLIC/'publication_receipt.json',{'status':'UPLOAD_VERIFIED','utc':w.now(),'scientific_validation':summary['status'],'release_tag':tag,'url':info['html_url'],'payload_commit':head,'remote_tag_commit_verified':True,'approved_assemblies':196,'assets':receipts})
    w.status('2_sequences','COMPLETED',summary['status'],'UPLOAD_VERIFIED','All196 source sequence packages passed independent integrity checks. Every standalone ZIP Release asset was downloaded back and CRC/member SHA256 verified; remote tag matched the payload commit. Stages3-7 have not run; continuing automatically to conserved host markers.')
    commit(['reports/stage02/publication_receipt.json','reports/stage02/RELEASE_NOTES.md','STATUS.md','status/stages.tsv'],'Verify all stage02 Release bytes and complete full196 sequence stage')
    print('STAGE02_SCIENTIFIC_VALIDATION_AND_UPLOAD_VERIFIED',flush=True)

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),'scope':'stage02 validation evidence and verified release publication'})
    try:main()
    except Exception as e:
        w.js(R/'status/stage02_finalize_failure.json',{'utc':w.now(),'error':str(e),'scientific_validation_preserved':True,'outputs_preserved':True})
        print('STAGE02_FINALIZATION_FAILED',e,flush=True)
        try:
            summary=json.loads((QC/'validation_summary.json').read_text())
            validation=summary['status']
            state='BLOCKED_SCIENTIFIC_VALIDATION' if summary['error_count'] else 'VALIDATED'
            publication='EVIDENCE_PUBLISHED' if summary['error_count'] else 'FAILED_OR_INCOMPLETE'
            w.status('2_sequences',state,validation,publication,'Stage02 finalization stopped: '+str(e)+'. Scientific result and source outputs are preserved; no dependent marker job allowed before verified publication.')
            commit(['status/stage02_finalize_failure.json','STATUS.md','status/stages.tsv'],'Record explicit stage02 publication/finalization blockage')
        except Exception as report_error:
            print('Failure receipt push also failed:',report_error,flush=True)
        raise
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
