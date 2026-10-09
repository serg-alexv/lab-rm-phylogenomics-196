"""Acquire exact public Conda originals; never install, extract, run, or delete them.

One streaming reader, 1MiB buffers, no automatic retries. A failed pass retains
partials and reports errors; a separate explicitly reviewed recovery is required.
GetPerformanceInfo declaration follows the reviewed atomic Windows resource reader.
"""
from pathlib import Path
import argparse, collections, ctypes, datetime, hashlib, json, os, re, shutil, stat
import time, urllib.request, urllib.parse, uuid, zipfile
from ctypes import wintypes as W

WORK=Path(__file__).resolve().parent
EXACT_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
GIB=1024**3; BLOCK=1024**2; RESERVE=3*GIB//2; MIN_DISK=10*GIB
MAX_SECONDS=7200; MAX_PACKAGE_SECONDS=180; SHARD_PACKAGE_BYTES=440*1024**2; MAX_ASSET_BYTES=448*1024**2
MANIFESTS={'detector_package_manifest.json':'45fc8f2d49ea313afd7a18d489b6dfe8cf940591334a713ef584fca1ccb2e382',
 'host_package_manifest.json':'e8c84f6c390cc0f03349c54f3992d7cc790a5388c15eec5c4ad5bab7453bfe48'}
PUBLIC_CHANNELS=('conda-forge','bioconda')

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):
    with Path(path).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def signature(s):return(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as s:json.dump(value,s,indent=2,sort_keys=True);s.write('\n');s.flush();os.fsync(s.fileno())
def checkpoint(path,value):
    # Only our new namespace's own receipt is replaceable; previous observations stay in JSONL.
    next_path=path.with_name(path.name+'.next')
    write_new(next_path,value);os.replace(next_path,path)
def append(path,row):
    with path.open('a',encoding='utf-8',newline='\n') as s:s.write(json.dumps(row,sort_keys=True)+'\n');s.flush();os.fsync(s.fileno())

def public_url(url):
    u=urllib.parse.urlsplit(url)
    require(u.scheme=='https' and u.hostname=='conda.anaconda.org' and u.port in (None,443)
        and not u.username and not u.password and not u.query and not u.fragment
        and len(u.path.split('/'))==4 and u.path.split('/')[1] in PUBLIC_CHANNELS
        and '..' not in u.path.split('/'), 'Nonpublic/redirected/nonofficial Conda URL')
    return url

class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        public_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class Resources:
    def __init__(self):
        require(os.name=='nt' and ctypes.sizeof(ctypes.c_void_p)==8,'Windows64 resource reader required')
        class PERF(ctypes.Structure):
            _fields_=[('cb',W.DWORD)]+[(n,ctypes.c_size_t) for n in ('CommitTotal','CommitLimit','CommitPeak','PhysicalTotal',
                'PhysicalAvailable','SystemCache','KernelTotal','KernelPaged','KernelNonpaged','PageSize')]+[(n,W.DWORD) for n in ('HandleCount','ProcessCount','ThreadCount')]
        require(ctypes.sizeof(PERF)==104,'Unexpected Windows PERFORMANCE_INFORMATION size')
        self.PERF=PERF;self.psapi=ctypes.WinDLL('psapi',use_last_error=True)
        self.psapi.GetPerformanceInfo.argtypes=[ctypes.POINTER(PERF),W.DWORD];self.psapi.GetPerformanceInfo.restype=W.BOOL
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.GetCurrentProcess.restype=W.HANDLE
        self.kernel.SetPriorityClass.argtypes=[W.HANDLE,W.DWORD];self.kernel.SetPriorityClass.restype=W.BOOL
        self.kernel.GetPriorityClass.argtypes=[W.HANDLE];self.kernel.GetPriorityClass.restype=W.DWORD
        handle=self.kernel.GetCurrentProcess()
        require(self.kernel.SetPriorityClass(handle,0x4000) and self.kernel.GetPriorityClass(handle)==0x4000,'Own below-normal priority not established')
    def read(self):
        p=self.PERF();p.cb=ctypes.sizeof(p)
        require(self.psapi.GetPerformanceInfo(ctypes.byref(p),ctypes.sizeof(p)),'GetPerformanceInfo failed')
        return dict(utc=utc(),physical_available_bytes=p.PhysicalAvailable*p.PageSize,
            commit_headroom_bytes=(p.CommitLimit-p.CommitTotal)*p.PageSize,commit_total_bytes=p.CommitTotal*p.PageSize,
            commit_limit_bytes=p.CommitLimit*p.PageSize,c_disk_free_bytes=shutil.disk_usage(WORK).free,
            own_priority_class='BELOW_NORMAL_PRIORITY_CLASS')

def resource_passes(row):
    return row['physical_available_bytes']>=RESERVE and row['commit_headroom_bytes']>=RESERVE and row['c_disk_free_bytes']>=MIN_DISK

def selected_packages():
    records=[];originals={};packages={}
    for manifest,expected in MANIFESTS.items():
        path=WORK/'master_public_components01/frozen/manifests'/manifest
        data=path.read_bytes();require(hashlib.sha256(data).hexdigest()==expected,'Public manifest drift')
        originals[manifest]=data
        for index,r in enumerate(json.loads(data)['packages']):
            public_url(r['url'])
            require(re.fullmatch('[a-f0-9]{64}',r['sha256']) and type(r['size']) is int and 0<r['size']<MAX_ASSET_BYTES
                and isinstance(r['license'],str) and r['license'] and r['subdir'] in ('linux-64','noarch')
                and re.fullmatch('[A-Za-z0-9_.+-]+',r['fn']) and r['url']=='https://conda.anaconda.org/'+urllib.parse.urlsplit(r['url']).path.split('/')[1]+'/'+r['subdir']+'/'+r['fn'], 'Invalid original package record')
            record={'manifest':manifest,'row_index':index,'original_record':r};records.append(record)
            item={'name':r['name'],'version':r['version'],'build':r.get('build',r.get('build_string')),'filename':r['fn'],
                'subdir':r['subdir'],'url':r['url'],'bytes':r['size'],'sha256':r['sha256'],'license':r['license'],'source_records':[]}
            key=r['sha256']
            if key in packages:
                require(all(packages[key][k]==item[k] for k in item if k!='source_records'),'Conflicting original SHA/URL/size/license')
            else:packages[key]=item
            packages[key]['source_records'].append({'manifest':manifest,'row_index':index})
    rows=[packages[k] for k in sorted(packages)]
    require(len(records)==397 and len(rows)==339 and sum(r['bytes'] for r in rows)==660114049,'Exact public397/339/bytes accounting differs')
    return originals,records,rows

def guard(resources,out,started):
    require(time.monotonic()-started<MAX_SECONDS,'Bounded acquisition/build deadline reached')
    row=resources.read();append(out/'resources.jsonl',row)
    require(resource_passes(row),'Resource reserve or C disk gate failed; preserved partials, no automatic resume')
    return row

def download(row,out,resources,started):
    target=out/'packages'/row['sha256']/row['filename'];target.parent.mkdir(exist_ok=False)
    partial=target.with_name(target.name+'.partial')
    public_url(row['url']);began=time.monotonic();digest=hashlib.sha256();count=0;last_guard=began
    # Direct official HTTPS only; ambient proxy credentials/auth are not adopted.
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),StrictRedirect())
    request=urllib.request.Request(row['url'],headers={'Accept-Encoding':'identity','User-Agent':'LABRM-public-byte-recovery/1'})
    try:
        with partial.open('xb') as sink:
            with opener.open(request,timeout=30) as response:
                require(response.status==200 and public_url(response.geturl()),'Unexpected HTTP status/final URL')
                length=response.headers.get('Content-Length')
                require(length is None or int(length)==row['bytes'],'Server Content-Length differs from original pin')
                while True:
                    require(time.monotonic()-began<MAX_PACKAGE_SECONDS,'Bounded individual package deadline reached')
                    block=response.read(BLOCK)
                    if not block:break
                    count+=len(block);require(count<=row['bytes'],'Package exceeds pinned original size')
                    sink.write(block);digest.update(block)
                    if count%(8*BLOCK)<BLOCK or time.monotonic()-last_guard>=5:
                        guard(resources,out,started);last_guard=time.monotonic()
            sink.flush();os.fsync(sink.fileno())
        require(count==row['bytes'] and digest.hexdigest()==row['sha256'],'Actual downloaded SHA/size differs')
        guard(resources,out,started)
        require(partial.stat().st_size==row['bytes'] and sha(partial)==row['sha256'],'Downloaded local readback differs')
        partial.rename(target)
        return dict(state='PASS_EXACT_ORIGINAL_PACKAGE',sha256=row['sha256'],bytes=count,url=row['url'],
            path=str(target),original_identity=signature(target.stat()),utc=utc(),automatic_retries=0)
    except BaseException as error:
        append(out/'download_errors.jsonl',dict(utc=utc(),sha256=row['sha256'],url=row['url'],partial=str(partial),
            observed_bytes=count,error_kind=type(error).__name__,error=str(error)[:1000],automatic_retries=0))
        raise

def build_shards(out,rows,downloads,resources,started):
    groups=[];group=[];size=0
    for row in rows:
        if group and size+row['bytes']>SHARD_PACKAGE_BYTES:groups.append(group);group=[];size=0
        group.append(row);size+=row['bytes']
    if group:groups.append(group)
    common={n:out/n for n in ('detector_package_manifest.json','host_package_manifest.json','package_index.json',
        'acquisition_receipt.json','ATTRIBUTION_AND_RESTORE.txt','acquire_public_conda_packages01.py')}
    common['downloaded_packages.jsonl']=out/'downloaded_packages.jsonl'
    outputs=[]
    for number,group in enumerate(groups,1):
        guard(resources,out,started)
        name=f'master_public_conda_packages01-{number:03d}.zip';partial=out/(name+'.unverified');final=out/name
        pins={};sources={};members=[]
        for row in group:
            path=Path(downloads[row['sha256']]['path']);member='packages/'+row['sha256']+'/'+row['filename']
            require(signature(path.stat())==tuple(downloads[row['sha256']]['original_identity']) and sha(path)==row['sha256'],'Captured downloaded package changed before archive')
            pins[member]={'bytes':row['bytes'],'sha256':row['sha256']};sources[member]=path
        for n,path in common.items():pins['control/'+n]={'bytes':path.stat().st_size,'sha256':sha(path)};sources['control/'+n]=path
        sums=''.join(r['sha256']+'  '+n+'\n' for n,r in sorted(pins.items())).encode()
        pins['SHA256SUMS.txt']={'bytes':len(sums),'sha256':hashlib.sha256(sums).hexdigest()}
        with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
            for member,pin in sorted(pins.items()):
                guard(resources,out,started)
                info=zipfile.ZipInfo(member,(2026,10,9,0,0,0));info.compress_type=zipfile.ZIP_STORED;info.external_attr=0o100644<<16
                if member=='SHA256SUMS.txt':z.writestr(info,sums);continue
                path=sources[member];before=signature(path.stat());actual=hashlib.sha256();count=0
                with path.open('rb') as source,z.open(info,'w',force_zip64=True) as sink:
                    require(signature(os.fstat(source.fileno()))==before,'Opened archive input changed')
                    for block in iter(lambda:source.read(BLOCK),b''):
                        actual.update(block);sink.write(block);count+=len(block)
                        if count%(8*BLOCK)<BLOCK:guard(resources,out,started)
                    require(signature(os.fstat(source.fileno()))==before,'Archive input handle changed')
                require(signature(path.stat())==before and count==pin['bytes'] and actual.hexdigest()==pin['sha256'],'Actual source copy differs')
        require(partial.stat().st_size<MAX_ASSET_BYTES,'Archive exceeds448MiB; preserve unverified output')
        with zipfile.ZipFile(partial) as z:
            require(len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(pins),'Exact package shard membership differs')
            for member,pin in sorted(pins.items()):
                guard(resources,out,started);info=z.getinfo(member)
                with z.open(info) as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
                require(actual==pin['sha256'] and info.file_size==pin['bytes'],'Actual ZIP member CRC/SHA/source pin differs')
                members.append(dict(member=member,**pin,crc32=f'{info.CRC:08x}',crc_verified=True))
        partial.rename(final);actual=sha(final)
        with (out/(name+'.sha256')).open('x',encoding='ascii',newline='\n') as s:s.write(actual+'  '+name+'\n')
        outputs.append(dict(name=name,bytes=final.stat().st_size,sha256=actual,package_files=len(group),
            package_bytes=sum(r['bytes'] for r in group),members=members))
    require(sum(r['package_files'] for r in outputs)==339 and sum(r['package_bytes'] for r in outputs)==660114049,'Final exact package shard accounting differs')
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--acquire',action='store_true');args=parser.parse_args()
    require(WORK==EXACT_WORK.resolve() and os.name=='nt' and os.environ.get('COMPUTERNAME','').casefold()=='wd','Exact WD C-work namespace required')
    originals,records,rows=selected_packages()
    if not args.acquire:
        print(json.dumps(dict(state='PREPARED_NOT_DOWNLOADED',records=397,distinct_packages=339,bytes=660114049,source_sha256=sha(__file__))));return
    resources=Resources();initial=resources.read()
    print(json.dumps(dict(phase='FRESH_WINDOWS_RESOURCE_ADMISSION',**initial,passes=resource_passes(initial))),flush=True)
    require(resource_passes(initial),'Fresh initial RAM/commit/Cfree gate failed before creating acquisition namespace')
    out=WORK/('public_conda_packages01_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir();(out/'packages').mkdir()
    started=time.monotonic();summary=dict(schema='MASTER_PUBLIC_CONDA_ACQUISITION_BUILD_V1',state='ACQUIRING_NO_INSTALL_OR_EXECUTION',started_utc=utc(),
        source_sha256=sha(__file__),manifest_pins=MANIFESTS,original_records=397,distinct_packages=339,expected_package_bytes=660114049,
        streaming_readers=1,block_bytes=BLOCK,automatic_retries=0,minimum_physical_and_commit_reserve_bytes=RESERVE,
        minimum_C_disk_free_bytes=MIN_DISK,initial_resources=initial,source_deletions=0,wsl_starts=0,g_writes=0,
        package_extraction=0,package_execution=0,installations=0,scientific_jobs=0,remote_publication='NOT_RUN')
    try:
        for name,data in originals.items():
            with (out/name).open('xb') as s:s.write(data)
        write_new(out/'package_index.json',dict(schema='MASTER_EXACT_PUBLIC_CONDA_PACKAGE_INDEX_V1',original_records=records,
            packages=rows,manifest_pins=MANIFESTS,total_distinct_bytes=660114049))
        with (out/'acquire_public_conda_packages01.py').open('xb') as s:s.write(Path(__file__).read_bytes())
        notice='Exact retained Conda package restoration cache:397 original records/339 distinct SHA256 objects.\nOfficial source URLs, original package licenses, names, versions and builds are in package_index.json and the unchanged two original manifests.\nAll upstream package bytes, including original embedded author/copyright/license notices, remain unchanged; payloads are never extracted or executed here.\nOnly linux-64/noarch Conda package archives are included. Pip/R local changes, the installed ext4 image, OS/host base runtime and unknown components are excluded.\nThis does not claim complete installed-environment recovery or newly audited complete corresponding-source/license coverage. Restore by independently checking SHA256SUMS and original package pins, then use a separately authorized compatible package manager; this builder never installs.\n'
        with (out/'ATTRIBUTION_AND_RESTORE.txt').open('x',encoding='utf-8',newline='\n') as s:s.write(notice)
        downloads={}
        for index,row in enumerate(rows,1):
            guard(resources,out,started);record=download(row,out,resources,started);downloads[row['sha256']]=record
            append(out/'downloaded_packages.jsonl',record)
            summary.update(verified_packages=index,verified_package_bytes=sum(x['bytes'] for x in downloads.values()))
            checkpoint(out/'progress.json',summary)
            print(json.dumps(dict(phase='PUBLIC_PACKAGE_DOWNLOAD',verified=index,total=339,bytes=summary['verified_package_bytes'],namespace=str(out))),flush=True)
        require(sha(__file__)==summary['source_sha256'],'Acquisition source changed during pass')
        acquisition={**summary,'state':'PASS_ALL339_ORIGINAL_DOWNLOAD_SHA_SIZE_VERIFIED','finished_utc':utc(),
            'downloads_sha256':sha(out/'downloaded_packages.jsonl'),'original_notices':'PRESERVED_INSIDE_UNCHANGED_ORIGINAL_PACKAGE_BYTES_NOT_EXTRACTED'}
        write_new(out/'acquisition_receipt.json',acquisition)
        summary.update(state='BUILDING_LOCAL_ORIGINAL_PACKAGE_SHARDS',acquisition_receipt_sha256=sha(out/'acquisition_receipt.json'))
        summary['shards']=build_shards(out,rows,downloads,resources,started)
        require(sha(__file__)==summary['source_sha256'],'Builder source changed')
        summary.update(state='PASS_LOCAL_ALL339_ORIGINALS_AND_ALL_SHARD_MEMBERS_CRC_SHA_VERIFIED',finished_utc=utc(),
            installed_runtime_complete=False,full_corresponding_source_coverage_audited=False)
    except BaseException as error:
        summary.update(state='FAILED_PRESERVED_PARTIALS_NO_AUTOMATIC_RETRY',finished_utc=utc(),
            error=dict(kind=type(error).__name__,message=str(error)[:1500]));raise
    finally:
        checkpoint(out/'build_receipt.json',summary)
        print(json.dumps(dict(state=summary['state'],namespace=str(out),receipt=str(out/'build_receipt.json'))),flush=True)

if __name__=='__main__':main()
