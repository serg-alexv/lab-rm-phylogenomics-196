"""Retain exact public IQ-TREE source and its two pinned submodules; execute nothing."""
from pathlib import Path, PurePosixPath
import ctypes, datetime, gzip, hashlib, json, subprocess, sys, tarfile, time, urllib.request, uuid

WORK=Path(__file__).resolve().parent
PIN='63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de'
REPOS=[('iqtree/iqtree3',PIN),('trongnhanuit/cmaple','3d45b1ab68e2d68a2825bf17a531e22200578cd6'),
       ('tothuhien/lsd2','c61110f3a4fa05325b45c97b2134792ff9d55d4c')]
RESERVE=1610612736
MAX_DOWNLOAD=128*1024*1024

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def require(ok,msg):
    if not ok:raise ValueError(msg)
def api(path):
    return subprocess.run(['gh','api','repos/'+path],capture_output=True,check=True,timeout=60).stdout
def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise RuntimeError('Unexpected redirect from exact official codeload endpoint')

def main():
    sys.dont_write_bytecode=True
    require(str(WORK)==r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work' and WORK.resolve()==WORK,
            'Source acquisition must use the exact WD C-work namespace')
    api_source=WORK/'atomic_iqtree_windows.py'
    require(digest(api_source)=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827','Windows resource-reader source differs')
    sys.path.insert(0,str(WORK));import atomic_iqtree_windows as A
    win=A.Win()
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    require(k.SetPriorityClass(k.GetCurrentProcess(),0x4000),'Cannot set below-normal priority')
    now=datetime.datetime.now(datetime.timezone.utc)
    out=WORK/('iqtree314_source01_'+now.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    receipt={'schema':'IQTREE314_PUBLIC_SOURCE_ACQUISITION_V1','started_utc':utc(),
        'source_sha256':digest(__file__),'state':'ACQUIRING_PUBLIC_SOURCE_ONLY','repositories':[],
        'resources':[],'payload_execution':0,'g_writes':0,'wsl_starts':0,'source_deletions':0,
        'installed_binary_equivalence':'NOT_PROVEN_BY_SOURCE_ARCHIVAL','standalone_intel_notice':'NOT_ASSERTED'}
    def save():
        (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    def gate(initial=False):
        r=win.resources([out]);receipt['resources'].append(r)
        minimum=2684354560 if initial else RESERVE
        require(r['physical_available_bytes']>=minimum and r['commit_headroom_bytes']>=minimum,
                'Physical/commit resource reserve not met; no retry')
        require(next(iter(r['disk_available_bytes'].values()))>=10*1024**3,'C disk reserve not met')
    try:
        gate(True)
        tag=json.loads(api('iqtree/iqtree3/commits/v3.1.4'))
        require(tag['sha']==PIN,'Official v3.1.4 source tag differs')
        (out/'tag_commit.json').write_bytes((json.dumps({'sha':tag['sha'],'html_url':tag['html_url']},indent=2)+'\n').encode())
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        for repo,commit in REPOS:
            gate()
            name=repo.split('/')[1]
            raw_commit=api(repo+'/git/commits/'+commit);commit_object=json.loads(raw_commit)
            require(commit_object['sha']==commit,'Exact pinned source commit differs')
            tree_sha=commit_object['tree']['sha']
            raw_tree=api(repo+'/git/trees/'+tree_sha+'?recursive=1');tree=json.loads(raw_tree)
            require(tree['sha']==tree_sha and tree['truncated'] is False,'Exact complete source tree differs')
            blobs={r['path']:r for r in tree['tree'] if r['type']=='blob'}
            links=[r for r in tree['tree'] if r['type']=='commit']
            require(sum(r['size'] for r in blobs.values())<=256*1024**2,'Source tree exceeds explicit bound')
            expected_links={'cmaple':REPOS[1][1],'lsd2':REPOS[2][1]} if repo==REPOS[0][0] else {}
            require({r['path']:r['sha'] for r in links}==expected_links,'Unexpected or missing nested submodule')
            for rel in blobs:
                p=PurePosixPath(rel)
                require(not p.is_absolute() and p.as_posix()==rel and '..' not in p.parts,'Noncanonical source blob path')
            (out/(name+'_git_tree.json')).write_bytes(raw_tree)
            (out/(name+'_git_commit.json')).write_bytes(raw_commit)
            url='https://codeload.github.com/'+repo+'/tar.gz/'+commit
            path=out/(name+'-'+commit+'.tar.gz.partial');count=0;started=time.monotonic()
            with opener.open(urllib.request.Request(url,headers={'User-Agent':'lab-rm-public-source-recovery/1'}),timeout=30) as response,path.open('xb') as dest:
                require(response.status==200 and response.geturl()==url,'Unexpected source response')
                while True:
                    require(time.monotonic()-started<300,'Bounded source download timed out')
                    gate();part=response.read(1024*1024)
                    if not part:break
                    count+=len(part);require(count<=MAX_DOWNLOAD,'Source download bound exceeded')
                    dest.write(part)
                dest.flush();__import__('os').fsync(dest.fileno())
            final=path.with_suffix('');path.rename(final)
            verify_started=time.monotonic();expanded=0
            with gzip.open(final,'rb') as compressed:
                while True:
                    gate()
                    require(time.monotonic()-verify_started<300,'Source gzip verification deadline exceeded')
                    part=compressed.read(256*1024)
                    if not part:break
                    expanded+=len(part);require(expanded<=320*1024**2,'Decompressed source archive bound exceeded')
            prefix=name+'-'+commit;seen={};notices=[]
            with tarfile.open(final,'r:gz') as archive:
                for item in archive:
                    gate()
                    require(time.monotonic()-verify_started<600,'Full source blob verification deadline exceeded')
                    p=PurePosixPath(item.name)
                    require(p.parts and p.parts[0]==prefix and '..' not in p.parts,'Unexpected archive source prefix/path')
                    if item.isdir():continue
                    rel=PurePosixPath(*p.parts[1:]).as_posix()
                    require(rel in blobs and rel not in seen,'Unexpected/duplicate source member')
                    expected=blobs[rel];h1=hashlib.sha1();h2=hashlib.sha256()
                    h1.update(b'blob '+str(expected['size']).encode()+b'\0')
                    if item.issym():
                        require(expected['mode']=='120000','Source symlink mode differs')
                        data=item.linkname.encode('utf-8');h1.update(data);h2.update(data);size=len(data)
                    else:
                        require(item.isfile() and expected['mode'] in ('100644','100755') and item.size==expected['size'],
                            'Source member type/size differs')
                        size=0
                        with archive.extractfile(item) as source:
                            while True:
                                gate()
                                require(time.monotonic()-verify_started<600,'Source blob verification deadline exceeded')
                                part=source.read(256*1024)
                                if not part:break
                                h1.update(part);h2.update(part);size+=len(part)
                    require(size==expected['size'] and h1.hexdigest()==expected['sha'],'Actual source blob differs: '+rel)
                    seen[rel]={'bytes':size,'sha256':h2.hexdigest(),'git_blob':expected['sha'],'mode':expected['mode']}
                    if any(word in p.name.casefold() for word in ('license','copying','copyright','notice','authors')):notices.append(rel)
            require(set(seen)==set(blobs),'Full source archive omits committed blobs')
            row={'repository':'https://github.com/'+repo,'commit':commit,'url':url,'archive':final.name,
                'bytes':final.stat().st_size,'sha256':digest(final),'tree_sha':tree_sha,'blob_count':len(seen),
                'uncompressed_blob_bytes':sum(r['bytes'] for r in seen.values()),'submodules':links,
                'original_notice_paths':notices,'all_git_blob_hashes_verified':True,'gzip_crc_verified':True}
            (out/(name+'_actual_blobs.json')).write_text(json.dumps(seen,indent=2)+'\n',encoding='utf-8')
            receipt['repositories'].append(row);save()
            print(json.dumps({'repo':repo,'state':'PASS_EXACT_GIT_SOURCE_BLOBS_RETAINED','blobs':len(seen),'bytes':row['bytes']}),flush=True)
        receipt.update(state='PASS_THREE_EXACT_PUBLIC_SOURCE_ARCHIVES_ALL_BLOBS_AND_SUBMODULE_PINS',finished_utc=utc())
        save();print(json.dumps({'state':receipt['state'],'receipt':str(out/'receipt.json')}),flush=True)
    except BaseException as e:
        receipt.update(state='FAILED_SOURCE_ACQUISITION_PARTIALS_PRESERVED_NO_RETRY',finished_utc=utc(),
                       error={'kind':type(e).__name__,'message':str(e)})
        save();print(json.dumps({'state':receipt['state'],'receipt':str(out/'receipt.json')}),flush=True);raise

if __name__=='__main__':main()
