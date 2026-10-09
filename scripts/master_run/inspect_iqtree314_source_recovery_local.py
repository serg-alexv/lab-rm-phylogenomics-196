"""Independent streaming LOCAL source recovery inspection; no producer import.

Only ZIP/tar/gzip streams are opened. Nothing is extracted or executed. A local
PASS is not remote durability, compiled-binary equivalence or scientific acceptance.
"""
from pathlib import Path, PurePosixPath
from ctypes import wintypes as W
import argparse, ctypes, datetime, gzip, hashlib, importlib.util, json, os, shutil, stat, tarfile, time, uuid, zipfile

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
FOLDER=WORK/'master_iqtree314_source_recovery01'
ZIP=FOLDER/'master_iqtree314_source_recovery01.zip'
ZIP_SHA='4b4d123a2d901e03806136eb27a38bdc3a4d8da2dc5c0438afc4eb303d96a564'
BUILD_SHA='32efdc9d2da0ec2b96ea85f5b1d4900810033020df8c238c2cbc3c4f829b48d9'
HELPER_SHA='6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691'
REPOS=[('iqtree3','63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de','4605e2cff872f408e5174efecb4715122f9582d9',1077,81595459),
 ('cmaple','3d45b1ab68e2d68a2825bf17a531e22200578cd6','58f3347daf5803388375277896e3e08b2fa87b9c',820,25117159),
 ('lsd2','c61110f3a4fa05325b45c97b2134792ff9d55d4c','39662489fd879fca80e166f26c797a8a1024d7e6',41,5845352)]
GIT='4b5d6aa580496004b342d8d49cbe8f6629e835f8'; ORIGINAL='6a22862d34ecc3e5a11e59c29726711016ad6a66f3b9283603e46cae77358797'
EXPORTED='65991b0d98a7003ec9b0ae5ee821287b4c7e0c7294c0ed47b502e97f3b6085e4'
CHUNK=256*1024; DEADLINE=float('inf'); RESOURCES=None; MINIMA={}

def require(ok,message):
 if not ok:raise ValueError(message)

def guard():
 require(time.monotonic()<DEADLINE,'600-second local source inspection deadline')
 if RESOURCES:
  row=RESOURCES()
  require(row['physical_available_bytes']>=3*1024**3//2 and row['commit_headroom_bytes']>=3*1024**3//2 and row['c_disk_free_bytes']>=10*1024**3,'Current reserve failed')
  for k,v in row.items():MINIMA[k]=min(v,MINIMA.get(k,v))

def hash_stream(stream):
 h=hashlib.sha256(); n=0
 for block in iter(lambda:stream.read(CHUNK),b''):
  guard();h.update(block);n+=len(block)
 guard();return n,h.hexdigest()

def resource_reader():
 class Perf(ctypes.Structure):
  _fields_=[('cb',W.DWORD)]+[(n,ctypes.c_size_t) for n in ('CommitTotal','CommitLimit','CommitPeak','PhysicalTotal','PhysicalAvailable','SystemCache','KernelTotal','KernelPaged','KernelNonpaged','PageSize')]+[(n,W.DWORD) for n in ('HandleCount','ProcessCount','ThreadCount')]
 require(ctypes.sizeof(Perf)==104,'Windows64 PERFORMANCE_INFORMATION layout')
 api=ctypes.WinDLL('psapi',use_last_error=True);api.GetPerformanceInfo.argtypes=[ctypes.POINTER(Perf),W.DWORD];api.GetPerformanceInfo.restype=W.BOOL
 kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=W.HANDLE
 kernel.SetPriorityClass.argtypes=[W.HANDLE,W.DWORD];kernel.SetPriorityClass.restype=W.BOOL
 kernel.GetPriorityClass.argtypes=[W.HANDLE];kernel.GetPriorityClass.restype=W.DWORD
 own=kernel.GetCurrentProcess();require(kernel.SetPriorityClass(own,0x4000) and kernel.GetPriorityClass(own)==0x4000,'Own BelowNormal priority')
 def read():
  p=Perf();p.cb=ctypes.sizeof(p);require(api.GetPerformanceInfo(ctypes.byref(p),ctypes.sizeof(p)),'GetPerformanceInfo failed')
  return dict(physical_available_bytes=p.PhysicalAvailable*p.PageSize,commit_headroom_bytes=(p.CommitLimit-p.CommitTotal)*p.PageSize,c_disk_free_bytes=shutil.disk_usage(WORK).free)
 return read

class Expanded:
 def __init__(self,stream):self.stream=stream;self.count=0
 def read(self,n=CHUNK):
  require(0<n<=CHUNK,'Bounded expanded-source read required');guard();data=self.stream.read(n);self.count+=len(data)
  require(self.count<=320*1024**2,'Expanded320MiB source bound');return data

def source_archive(bundle,name,commit,tree_sha,count,source_bytes,supplement):
 read=lambda suffix:json.loads(bundle.read('success/'+name+suffix))
 commit_obj=read('_git_commit.json');tree=read('_git_tree.json');actual=read('_actual_blobs.json')
 require(commit_obj['sha']==commit and commit_obj['tree']['sha']==tree['sha']==tree_sha and tree['truncated'] is False,'Exact commit/tree differs')
 expected={x['path']:x for x in tree['tree'] if x['type']=='blob'}
 directories={x['path'] for x in tree['tree'] if x['type'] in ('tree','commit')}|{'.'}
 require(len(expected)==len(actual)==count and set(expected)==set(actual) and sum(x['size'] for x in expected.values())==source_bytes,'Full source membership/count differs')
 seen={};seen_dirs=set();exceptions=0;prefix=name+'-'+commit
 with bundle.open('success/'+prefix+'.tar.gz') as compressed:
  with gzip.GzipFile(fileobj=compressed) as gz:
   expanded=Expanded(gz)
   with tarfile.open(fileobj=expanded,mode='r|',bufsize=CHUNK) as archive:
    for item in archive:
     guard();pure=PurePosixPath(item.name)
     require(pure.as_posix()==item.name.rstrip('/') and pure.parts and pure.parts[0]==prefix and '..' not in pure.parts and not pure.is_absolute(),'Unsafe/noncanonical source tar member')
     relative=PurePosixPath(*pure.parts[1:]).as_posix()
     if item.isdir():
      require(relative in directories and relative not in seen_dirs,'Unexpected/duplicate source directory');seen_dirs.add(relative);continue
     require(relative in expected and relative not in seen,'Unexpected/duplicate source blob')
     pin=expected[relative];record=actual[relative];size=0;h1=hashlib.sha1(b'blob '+str(pin['size']).encode()+b'\0');h2=hashlib.sha256()
     if name=='iqtree3' and relative=='terraphast/appveyor.yml':
      require(item.isfile() and item.size==264 and pin['size']==249 and pin['sha']==GIT and pin['mode']=='100644','Fixed original export metadata differs')
      with archive.extractfile(item) as stream:export=stream.read(512)
      require(len(export)==264 and hashlib.sha256(export).hexdigest()==EXPORTED and export.count(b'\r\n')==15 and export.replace(b'\r\n',b'\n')==supplement,'Exact CRLF export qualification differs')
      data=supplement;h1.update(data);h2.update(data);size=len(data);exceptions+=1
      require(record['original_recovery_supplement']=='original_git_blobs/'+GIT+'.blob' and record['archive_bytes']==264 and record['archive_sha256']==EXPORTED,'Original supplement map differs')
     elif item.issym():
      require(pin['mode']=='120000','Unexpected symbolic-link mode');data=item.linkname.encode('utf-8');h1.update(data);h2.update(data);size=len(data)
     else:
      require(item.isfile() and pin['mode'] in ('100644','100755') and item.size==pin['size'],'Source type/size differs')
      with archive.extractfile(item) as stream:
       for block in iter(lambda:stream.read(CHUNK),b''):
        guard();size+=len(block);h1.update(block);h2.update(block)
     require(size==pin['size']==record['bytes'] and h1.hexdigest()==pin['sha']==record['git_blob'] and h2.hexdigest()==record['sha256'] and pin['mode']==record['mode'],'Actual original GitSHA1/SHA256 blob differs: '+relative)
     seen[relative]=dict(bytes=size,sha256=h2.hexdigest(),git_blob=h1.hexdigest(),mode=pin['mode'])
   while expanded.read(CHUNK):pass # Full gzip EOF independently validates trailer CRC and expanded bound.
 require(set(seen)==set(expected) and exceptions==(1 if name=='iqtree3' else 0),'Complete original blob/supplement set differs')
 if name=='iqtree3':
  require([(x['path'],x['sha']) for x in tree['tree'] if x['type']=='commit']==[(n,c) for n,c,*_ in REPOS[1:]],'Exact two submodule gitlinks differ')
 else:require(not any(x['type']=='commit' for x in tree['tree']),'Unexpected nested submodule')
 return dict(repository=name,commit=commit,tree_sha=tree_sha,original_git_blobs=len(seen),original_blob_bytes=sum(x['bytes'] for x in seen.values()),expanded_tar_bytes=expanded.count,gzip_crc_verified=True,qualified_export_supplements=exceptions,actual_git_blob_sha1_sha256_verified=True)

def inspect():
 global DEADLINE,RESOURCES
 require(os.name=='nt' and Path(__file__).resolve().parent==WORK,'Exact current Windows C-work deployment')
 DEADLINE=time.monotonic()+600;RESOURCES=resource_reader();guard()
 target=WORK/('iqtree314_source_recovery_local_inspection_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json')
 result=dict(schema='MASTER_IQTREE314_SOURCE_RECOVERY_INDEPENDENT_LOCAL_INSPECTION_V1',state='STARTED',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),remote_readback='NOT_RUN',payload_extraction=0,payload_execution=0,g_writes=0,wsl_starts=0,source_deletions=0,network_calls=0)
 try:
  raw=(FOLDER/'build_receipt.json').read_bytes();require(hashlib.sha256(raw).hexdigest()==BUILD_SHA,'Exact buildreceipt differs');build=json.loads(raw)
  require(ZIP.stat().st_size==41054085 and build['sha256']==ZIP_SHA and len(build['members'])==31,'Exact known local archive differs')
  with ZIP.open('rb') as stream:require(hash_stream(stream)==(41054085,ZIP_SHA),'Whole original recovery ZIP differs')
  helper=WORK/'verify_master_public_components01_remote.py';require(hashlib.sha256(helper.read_bytes()).hexdigest()==HELPER_SHA,'Independent safe-path helper differs')
  spec=importlib.util.spec_from_file_location('independent_safe_zip_names',helper);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
  with zipfile.ZipFile(ZIP) as bundle:
   names=bundle.namelist();A.safe_names(names);expected={r['member']:r for r in build['members']}
   require(len(names)==len(expected)==31 and set(names)==set(expected),'Exact31 member table differs')
   checks={}
   for line in bundle.read('SHA256SUMS.txt').decode('ascii').splitlines():
    digest,name=line.split('  ',1);require(name not in checks,'Duplicate SUMS row');checks[name]=digest
   require(set(checks)==set(names)-{'SHA256SUMS.txt'},'Exact30 SUMS membership differs')
   for item in bundle.infolist():
    require(not item.is_dir() and item.compress_type==zipfile.ZIP_STORED and stat.S_IFMT(item.external_attr>>16)==stat.S_IFREG,'Unexpected ZIP original type')
    with bundle.open(item) as stream:size,digest=hash_stream(stream)
    pin=expected[item.filename];require(size==item.file_size==pin['bytes'] and digest==pin['sha256'] and f'{item.CRC:08x}'==pin['crc32'] and pin['crc_verified'] is True,'Actual ZIP EOF CRC/SHA differs')
    require(item.filename=='SHA256SUMS.txt' or checks[item.filename]==digest,'Actual innerSUMS mismatch')
   supplement=bundle.read('success/original_git_blobs/'+GIT+'.blob')
   require(len(supplement)==249 and supplement.count(b'\r\n')==0 and hashlib.sha256(supplement).hexdigest()==ORIGINAL and hashlib.sha1(b'blob 249\0'+supplement).hexdigest()==GIT,'Exact original249B supplement differs')
   sources=[source_archive(bundle,*repo,supplement) for repo in REPOS]
  side=(ZIP_SHA+'  '+ZIP.name+'\n').encode('ascii');actual=(FOLDER/(ZIP.name+'.sha256')).read_bytes();require(actual==side and len(side)==105 and hashlib.sha256(side).hexdigest()=='ea3baff1e98b6ef358a611ba47dca303422d5f37478b484b2980ec50fd585635','Original LF sidecar differs')
  result.update(state='PASS_LOCAL31_MEMBERS_ALL1938_ORIGINAL_GIT_BLOBS_AND_ONE_EXACT_SUPPLEMENT',zip_sha256=ZIP_SHA,zip_bytes=41054085,zip_members=31,SUMS_entries=30,repositories=sources,original_git_blobs=1938,qualified_original_supplemental_blobs=1,resource_minimum_bytes=MINIMA,installed_binary_equivalence='NOT_PROVEN_BY_SOURCE_ARCHIVAL',all_archive_files_equal_git_bytes=False,standalone_intel_notice='NOT_ASSERTED')
 except BaseException as error:result.update(state='FAILED_LOCAL_INSPECTION',error=dict(kind=type(error).__name__,message=str(error)));raise
 finally:
  with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
  print(json.dumps(dict(state=result['state'],receipt=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest())))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inspect',action='store_true');args=p.parse_args()
 if args.inspect:inspect()
 else:print(json.dumps(dict(state='PREPARED_NO_LOCAL_INSPECTION',remote_readback='NOT_RUN')))
