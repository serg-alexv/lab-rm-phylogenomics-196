"""Explicit one-time continuation after the pinned resource stop; default is prepare-only.

No automatic admission wait/retry. Reopen and copy 95 completed originals into a
new namespace; redownload the original partial from zero without HTTP Range.
Uses only the SHA-pinned, peer-reviewed first-pass helpers, without invoking main.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,stat,time,uuid,zipfile,urllib.request

WORK=Path(__file__).resolve().parent
EXACT_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
BASE_SHA='e94e2d59e6d4b91353916db7bdf8485ecff0eba181f644e534a7e742e1e5bffc'
PLAN_SHA='ab4f2d6cb9a39815397e7281c636527139ce4fd1bc43c2adccd16835420b1862'
ADMISSION_PHYSICAL=5*1024**3//2
ADMISSION_COMMIT=7*1024**3//2

def sha(p):
    with Path(p).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def admission_passes(A,row):
    return A.resource_passes(row) and row['physical_available_bytes']>=ADMISSION_PHYSICAL and row['commit_headroom_bytes']>=ADMISSION_COMMIT
def guarded_sha(A,path,out,started):
    digest=hashlib.sha256()
    with Path(path).open('rb') as reader:
        while True:
            A.guard(A.resources,out,started);block=reader.read(A.BLOCK)
            if not block:break
            digest.update(block)
    return digest.hexdigest()
def load():
    require(WORK==EXACT_WORK and os.name=='nt' and os.environ.get('COMPUTERNAME','').casefold()=='wd','Exact WD C-work required')
    source=WORK/'acquire_public_conda_packages01.py';require(sha(source)==BASE_SHA,'Reviewed base helper changed')
    spec=importlib.util.spec_from_file_location('conda_base',source);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    path=WORK/'public_conda_packages01_recovery_plan.json';require(sha(path)==PLAN_SHA,'Explicit resource-stop recovery plan changed')
    plan=json.loads(path.read_text());require(plan['completed_count']==95 and plan['completed_bytes']==237225880
        and plan['no_automatic_resume'] is True and plan['http_range_requests']==0,'Exact resource-stop plan differs')
    originals,records,packages=A.selected_packages()
    for row,pin in zip(plan['completed'],packages):
        require(row['sha256']==pin['sha256'] and row['bytes']==pin['bytes'] and row['url']==pin['url']
            and Path(row['path'])==Path(plan['original_namespace'])/'packages'/pin['sha256']/pin['filename'],'Completed original source join differs')
    require(len(plan['completed'])==95,'Exact completed package count differs')
    return A,plan,originals,records,packages

def original_controls(A,plan,out,started):
    for row in plan['controls'].values():
        A.guard(A.resources,out,started);path=Path(row['path']);s=path.lstat()
        require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not s.st_file_attributes&1024
            and s.st_size==row['bytes'] and sha(path)==row['sha256'],'Frozen first-pass control differs')
    p=plan['original_partial'];path=Path(p['path']);s=path.lstat()
    require(A.signature(s)==tuple(p['identity']) and sha(path)==p['sha256'],'Preserved original partial changed')
    # It is deliberately never copied into a package target or used as a Range prefix.

def copy_completed(A,pin,old,out,started):
    source=Path(old['path']);s=source.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not s.st_file_attributes&1024
        and A.signature(s)==tuple(old['original_identity']),'Completed source identity changed')
    target=out/'packages'/pin['sha256']/pin['filename'];target.parent.mkdir(exist_ok=False)
    partial=target.with_name(target.name+'.unverified_copy');actual=hashlib.sha256();count=0
    with source.open('rb') as reader,partial.open('xb') as writer:
        require(A.signature(os.fstat(reader.fileno()))==A.signature(s),'Opened completed source identity differs')
        for block in iter(lambda:reader.read(A.BLOCK),b''):
            A.guard(A.resources,out,started)
            writer.write(block);actual.update(block);count+=len(block)
        require(A.signature(os.fstat(reader.fileno()))==A.signature(s),'Completed source handle changed')
        writer.flush();os.fsync(writer.fileno())
    require(A.signature(source.lstat())==A.signature(s) and count==pin['bytes'] and actual.hexdigest()==pin['sha256'],
        'Fresh full completed-source SHA/copy differs')
    A.guard(A.resources,out,started)
    require(guarded_sha(A,partial,out,started)==pin['sha256'],'New copy readback SHA differs');partial.rename(target)
    return dict(state='PASS_FRESH_ORIGINAL_SOURCE_AND_NEW_COPY_SHA',sha256=pin['sha256'],bytes=count,url=pin['url'],
        path=str(target),original_identity=A.signature(target.stat()),source_path=str(source),source_identity=A.signature(s),
        utc=A.utc(),automatic_retries=0)

def download_zero(A,pin,out,started):
    """One plain official HTTPS request, no Range/cached partial/retry; guard every1MiB."""
    target=out/'packages'/pin['sha256']/pin['filename'];target.parent.mkdir(exist_ok=False)
    partial=target.with_name(target.name+'.partial');began=time.monotonic();digest=hashlib.sha256();count=0
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),A.StrictRedirect())
    request=urllib.request.Request(A.public_url(pin['url']),headers={'Accept-Encoding':'identity','User-Agent':'LABRM-public-byte-recovery/1'})
    try:
        with partial.open('xb') as writer,opener.open(request,timeout=30) as response:
            require(response.status==200 and A.public_url(response.geturl()),'Unexpected HTTP status/final URL')
            length=response.headers.get('Content-Length');require(length is None or int(length)==pin['bytes'],'Server size differs from original pin')
            while True:
                A.guard(A.resources,out,started);require(time.monotonic()-began<A.MAX_PACKAGE_SECONDS,'Bounded individual package deadline reached')
                block=response.read(A.BLOCK)
                if not block:break
                count+=len(block);require(count<=pin['bytes'],'Package exceeds original size')
                writer.write(block);digest.update(block)
            writer.flush();os.fsync(writer.fileno())
        require(count==pin['bytes'] and digest.hexdigest()==pin['sha256'],'Actual downloaded size/SHA differs')
        require(guarded_sha(A,partial,out,started)==pin['sha256'],'Local downloaded readback SHA differs');partial.rename(target)
        return dict(state='PASS_EXACT_ORIGINAL_PACKAGE',sha256=pin['sha256'],bytes=count,url=pin['url'],path=str(target),
            original_identity=A.signature(target.stat()),utc=A.utc(),automatic_retries=0,http_range_requests=0)
    except BaseException as e:
        A.append(out/'download_errors.jsonl',dict(utc=A.utc(),sha256=pin['sha256'],url=pin['url'],partial=str(partial),
            observed_bytes=count,error_kind=type(e).__name__,error=str(e)[:1000],automatic_retries=0,http_range_requests=0));raise

def build(A,out,packages,downloads,started):
    """Same stored ZIP primitive as reviewed first pass; include continuation controls."""
    groups=[];group=[];size=0
    for p in packages:
        if group and size+p['bytes']>A.SHARD_PACKAGE_BYTES:groups.append(group);group=[];size=0
        group.append(p);size+=p['bytes']
    if group:groups.append(group)
    names=('detector_package_manifest.json','host_package_manifest.json','package_index.json','acquisition_receipt.json',
        'ATTRIBUTION_AND_RESTORE.txt','acquire_public_conda_packages01.py','continue_public_conda_packages01.py',
        'recovery_plan.json','original_resource_stop_receipt.json','original_download_errors.jsonl','downloaded_packages.jsonl')
    outputs=[]
    for number,group in enumerate(groups,1):
        A.guard(A.resources,out,started);sources={};pins={}
        for p in group:
            source=Path(downloads[p['sha256']]['path']);require(A.signature(source.stat())==tuple(downloads[p['sha256']]['original_identity']),
                'Completed new package identity changed before shard')
            n='packages/'+p['sha256']+'/'+p['filename'];sources[n]=source;pins[n]={'bytes':p['bytes'],'sha256':p['sha256']}
        for n in names:
            p=out/n;sources['control/'+n]=p;pins['control/'+n]={'bytes':p.stat().st_size,'sha256':sha(p)}
        sums=''.join(p['sha256']+'  '+n+'\n' for n,p in sorted(pins.items())).encode()
        pins['SHA256SUMS.txt']={'bytes':len(sums),'sha256':hashlib.sha256(sums).hexdigest()}
        name=f'master_public_conda_packages01-{number:03d}.zip';partial=out/(name+'.unverified');final=out/name
        with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
            for n,pin in sorted(pins.items()):
                A.guard(A.resources,out,started);info=zipfile.ZipInfo(n,(2026,10,9,0,0,0));info.compress_type=zipfile.ZIP_STORED;info.external_attr=0o100644<<16
                if n=='SHA256SUMS.txt':z.writestr(info,sums);continue
                p=sources[n];initial=A.signature(p.stat());digest=hashlib.sha256();count=0
                with p.open('rb') as reader,z.open(info,'w',force_zip64=True) as writer:
                    require(A.signature(os.fstat(reader.fileno()))==initial,'Opened shard source differs')
                    for block in iter(lambda:reader.read(A.BLOCK),b''):
                        A.guard(A.resources,out,started)
                        writer.write(block);digest.update(block);count+=len(block)
                    require(A.signature(os.fstat(reader.fileno()))==initial,'Shard source handle changed')
                require(A.signature(p.stat())==initial and count==pin['bytes'] and digest.hexdigest()==pin['sha256'],'Copied shard bytes differ')
        require(partial.stat().st_size<A.MAX_ASSET_BYTES,'Shard exceeds448MiB; unverified output preserved')
        members=[]
        with zipfile.ZipFile(partial) as z:
            require(len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(pins),'Exact shard membership differs')
            for n,pin in sorted(pins.items()):
                A.guard(A.resources,out,started);info=z.getinfo(n)
                digest=hashlib.sha256()
                with z.open(info) as reader:
                    for block in iter(lambda:reader.read(A.BLOCK),b''):
                        A.guard(A.resources,out,started);digest.update(block)
                require(info.file_size==pin['bytes'] and digest.hexdigest()==pin['sha256'],'Actual shard member CRC/SHA differs')
                members.append(dict(member=n,**pin,crc32=f'{info.CRC:08x}',crc_verified=True))
        partial.rename(final);digest=guarded_sha(A,final,out,started)
        sidecar=(digest+'  '+name+'\n').encode('ascii')
        with (out/(name+'.sha256')).open('xb') as f:f.write(sidecar)
        outputs.append(dict(name=name,bytes=final.stat().st_size,sha256=digest,package_files=len(group),package_bytes=sum(p['bytes'] for p in group),members=members,
            sidecar_name=name+'.sha256',sidecar_bytes=len(sidecar),sidecar_sha256=hashlib.sha256(sidecar).hexdigest(),sidecar_line_ending='LF'))
    require(sum(x['package_files'] for x in outputs)==339 and sum(x['package_bytes'] for x in outputs)==660114049,'Exact339 original-package accounting differs')
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--continue-from-resource-stop',action='store_true');args=parser.parse_args()
    A,plan,originals,records,packages=load()
    if not args.continue_from_resource_stop:
        print(json.dumps(dict(state='PREPARED_CONTINUATION_NOT_RUN',existing_complete=95,redownload_or_remaining=244,source_sha256=sha(__file__),plan_sha256=PLAN_SHA)));return
    A.resources=A.Resources();probe_started=time.monotonic();first=A.resources.read()
    print(json.dumps(dict(phase='FRESH_WINDOWS_RESOURCE_ADMISSION_1_OF_2',**first,passes=admission_passes(A,first))),flush=True)
    require(admission_passes(A,first),'First fresh2.5GiBphysical/3.5GiBcommit gate failed; no wait/retry/adoption/download/build')
    time.sleep(15)
    initial=A.resources.read();elapsed=time.monotonic()-probe_started
    print(json.dumps(dict(phase='FRESH_WINDOWS_RESOURCE_ADMISSION_2_OF_2',**initial,passes=admission_passes(A,initial),elapsed_seconds=elapsed)),flush=True)
    require(elapsed>=15 and admission_passes(A,initial),'Second fixed fresh resource gate failed; no wait/retry/adoption/download/build')
    out=WORK/('public_conda_packages01_continuation_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir();(out/'packages').mkdir()
    started=time.monotonic();summary=dict(schema='MASTER_PUBLIC_CONDA_RESOURCE_STOP_CONTINUATION_BUILD_V1',state='COPYING_VERIFIED_ORIGINALS_THEN_FRESH_DOWNLOADS',
        source_sha256=sha(__file__),base_source_sha256=BASE_SHA,recovery_plan_sha256=PLAN_SHA,original_failure_sha256=plan['failure_sha256'],
        started_utc=A.utc(),initial_resources=initial,admission_probes=[first,initial],admission_probe_separation_seconds=elapsed,
        admission_physical_bytes=ADMISSION_PHYSICAL,admission_commit_headroom_bytes=ADMISSION_COMMIT,
        streaming_readers=1,block_bytes=A.BLOCK,automatic_retries=0,automatic_admission_wait=False,per_buffer_resource_check=True,
        required_physical_and_commit_reserve_bytes=A.RESERVE,required_C_disk_free_bytes=A.MIN_DISK,
        original_partial='PRESERVED_UNCHANGED_NOT_ADOPTED;PINNED_PACKAGE_REDOWLOADED_FROM_ZERO',http_range_requests=0,
        original_records=397,expected_package_count=339,expected_package_bytes=660114049,source_deletions=0,wsl_starts=0,g_writes=0,
        package_extractions=0,package_executions=0,installations=0,scientific_jobs=0,remote_publication='NOT_RUN')
    try:
        original_controls(A,plan,out,started)
        for n,data in originals.items():
            with (out/n).open('xb') as f:f.write(data)
        A.write_new(out/'package_index.json',dict(schema='MASTER_EXACT_PUBLIC_CONDA_PACKAGE_INDEX_V1',original_records=records,packages=packages,
            manifest_pins=A.MANIFESTS,total_distinct_bytes=660114049,recovery_plan_sha256=PLAN_SHA))
        for n,source in [('acquire_public_conda_packages01.py',WORK/'acquire_public_conda_packages01.py'),('continue_public_conda_packages01.py',Path(__file__)),
            ('recovery_plan.json',WORK/'public_conda_packages01_recovery_plan.json'),('original_resource_stop_receipt.json',Path(plan['controls']['build_receipt.json']['path'])),
            ('original_download_errors.jsonl',Path(plan['controls']['download_errors.jsonl']['path'])),('ATTRIBUTION_AND_RESTORE.txt',Path(plan['controls']['ATTRIBUTION_AND_RESTORE.txt']['path']))]:
            with (out/n).open('xb') as f:f.write(source.read_bytes())
        require(sha(out/'acquire_public_conda_packages01.py')==BASE_SHA and sha(out/'continue_public_conda_packages01.py')==summary['source_sha256']
            and sha(out/'recovery_plan.json')==PLAN_SHA and sha(out/'original_resource_stop_receipt.json')==plan['failure_sha256']
            and sha(out/'original_download_errors.jsonl')==plan['controls']['download_errors.jsonl']['sha256']
            and sha(out/'ATTRIBUTION_AND_RESTORE.txt')==plan['controls']['ATTRIBUTION_AND_RESTORE.txt']['sha256'],
            'Captured continuation/source/recovery-control bytes differ')
        downloads={}
        for index,pin in enumerate(packages,1):
            A.guard(A.resources,out,started)
            row=copy_completed(A,pin,plan['completed'][index-1],out,started) if index<=95 else download_zero(A,pin,out,started)
            downloads[pin['sha256']]=row;A.append(out/'downloaded_packages.jsonl',row)
            summary.update(verified_packages=index,verified_package_bytes=sum(x['bytes'] for x in downloads.values()),reused_packages=min(index,95),fresh_downloaded_packages=max(index-95,0))
            A.checkpoint(out/'progress.json',summary);print(json.dumps(dict(phase='EXPLICIT_PUBLIC_CONDA_CONTINUATION',verified=index,total=339,namespace=str(out))),flush=True)
        require(sha(__file__)==summary['source_sha256'] and sha(WORK/'acquire_public_conda_packages01.py')==BASE_SHA,'Continuation/base source changed')
        A.write_new(out/'acquisition_receipt.json',{**summary,'state':'PASS_ALL339_ORIGINAL_SHA_SIZE_VERIFIED_95_REOPENED_244_FRESH_DOWNLOADS',
            'finished_utc':A.utc(),'downloaded_packages_sha256':sha(out/'downloaded_packages.jsonl')})
        summary['shards']=build(A,out,packages,downloads,started)
        original_controls(A,plan,out,started)
        require(sha(__file__)==summary['source_sha256'] and sha(WORK/'acquire_public_conda_packages01.py')==BASE_SHA,'Continuation/base source changed')
        summary.update(state='PASS_LOCAL_ALL339_ORIGINALS_AND_ALL_SHARD_MEMBERS_CRC_SHA_VERIFIED',finished_utc=A.utc(),installed_runtime_complete=False,
            full_corresponding_source_coverage_audited=False,resources_sha256=sha(out/'resources.jsonl'))
    except BaseException as e:summary.update(state='FAILED_PRESERVED_NEW_AND_ORIGINAL_PARTIALS_NO_AUTOMATIC_RETRY',finished_utc=A.utc(),error={'kind':type(e).__name__,'message':str(e)[:1500]});raise
    finally:
        if (out/'resources.jsonl').exists():summary['resources_sha256']=sha(out/'resources.jsonl')
        A.checkpoint(out/'build_receipt.json',summary)
        print(json.dumps(dict(state=summary['state'],receipt=str(out/'build_receipt.json'))),flush=True)
if __name__=='__main__':main()
