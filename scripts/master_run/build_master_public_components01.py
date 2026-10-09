"""Archive only the explicit retained public components; no network or execution.

One bounded C-only build. Read-only native source handles deny concurrent writes
and deletes during each capture. Original tools, live executable and image are
never modified. Existing third-party archives and notices remain byte-identical.
"""
from pathlib import Path, PurePosixPath
import ctypes, datetime, hashlib, json, msvcrt, os, re, shutil, stat, sys, tarfile
import urllib.parse, zipfile

WORK=Path(__file__).resolve().parent
OLD=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=WORK/'master_public_components01'
NAME='master_public_components01.zip'
EXE_SHA='43c9bf3b0dc5e7d88c183a2582369d22c9d692b7585350038769334bb6fd9aed'
NATIVE=OLD/'.tools/iqtree_windows_3_1_4/extracted/iqtree-3.1.4-Windows'
NATIVE_NAMES={'bin/iqtree3-click.exe':12332544,'bin/iqtree3.exe':12332544,'bin/libiomp5md.dll':1114552,
    'example.cf':2256166,'example.nex':183,'example.phy':34196,'models.nex':122624}
ARCHIVES={
 'CasFinder-3.1.0.tar.gz':(14908642,'CasFinder-ad7096548a814788ca04538602d71f85115b4c71','https://github.com/macsy-models/CasFinder','3.1.0','CC-BY-NC-SA-4.0',586),
 'defense-finder-models-3.0.0.tar.gz':(55000078,'defense-finder-models-9b0d07b759f5f73d8c2b9aa3e696f4cdd04c11d2','https://github.com/mdmparis/defense-finder-models','3.0.0','GPL-3.0',2524),
 'padloc-db-2.0.0.tar.gz':(146280058,'padloc-db-7f99b47b75e232b111c18626badb9ac32e8e0b5a','https://github.com/padlocbio/padloc-db','2.0.0','MIT',5485)}
FIXED={
 'manifests/detector_package_manifest.json':(OLD/'.work/detector_package_manifest.json','45fc8f2d49ea313afd7a18d489b6dfe8cf940591334a713ef584fca1ccb2e382'),
 'manifests/host_package_manifest.json':(OLD/'.work/host_package_manifest.json','e8c84f6c390cc0f03349c54f3992d7cc790a5388c15eec5c4ad5bab7453bfe48'),
 'manifests/iqtree_source_pin.json':(WORK/'iqtree_3_1_4_source_review/source_pin.json',None),
 'notices/IQTREE-3.1.4-LICENSE.txt':(WORK/'master_cleanup_batch01_metadata/IQTREE-3.1.4-LICENSE.txt','c03cea027b4b40e4402fabd08557736727ec3d5bc54ad64ab6472de432198cad'),
 'manifests/accepted_source_pins.json':(WORK/'stage5_accepted_source_pins.json','a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84'),
 'manifests/recorded_wsl_toolchain_probe.txt':(WORK/'bootstrap/wsl_toolchain_probe_final.txt','3b774b536057121c1498233dee5b84cb029d5b1dcc678d8f107f0ddb8665a60d')}
K=ctypes.WinDLL('kernel32',use_last_error=True)
K.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
K.CreateFileW.restype=ctypes.c_void_p
K.GetFinalPathNameByHandleW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32]
K.GetFinalPathNameByHandleW.restype=ctypes.c_uint32
K.CloseHandle.argtypes=[ctypes.c_void_p];K.CloseHandle.restype=ctypes.c_int

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def json_bytes(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def write_new(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
def plain(path):
    path=Path(path).absolute()
    require(path.drive.casefold()=='c:' and path.resolve()==path,'Only canonical C paths allowed')
    for p in [path,*path.parents]:
        s=p.lstat();require(not(s.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT),'Source reparse/alias forbidden')
    require(path.is_file(),'Exact regular source file required')
    return path

def capture(source,member,kind,pinned=None,expected_size=None):
    source=plain(source);before=source.stat()
    require(expected_size is None or before.st_size==expected_size,'Known source size changed: '+str(source))
    # FILE_SHARE_READ only: existing writers/deleters or new ones cannot overlap capture.
    h=K.CreateFileW(str(source),0x80000000,1,None,3,0x00200000,None)
    if h in (None,ctypes.c_void_p(-1).value):raise ctypes.WinError(ctypes.get_last_error())
    try:
        final=ctypes.create_unicode_buffer(32768);n=K.GetFinalPathNameByHandleW(h,final,32768,0)
        require(0<n<32768 and final.value.removeprefix('\\\\?\\').casefold()==str(source).casefold(),'Retained source handle path differs')
        fd=msvcrt.open_osfhandle(h,os.O_RDONLY|os.O_BINARY);h=None
        dest=OUT/'frozen'/member;dest.parent.mkdir(parents=True,exist_ok=True);digest=hashlib.sha256();count=0
        with os.fdopen(fd,'rb') as src,dest.open('xb') as dst:
            opened=os.fstat(src.fileno());require(stat.S_ISREG(opened.st_mode) and identity(opened)==identity(before),'Source handle identity differs')
            for block in iter(lambda:src.read(1024*1024),b''):dst.write(block);digest.update(block);count+=len(block)
            require(identity(os.fstat(src.fileno()))==identity(opened),'Source changed during capture')
            dst.flush();os.fsync(dst.fileno())
        after=plain(source).stat();actual=digest.hexdigest()
        require(identity(before)==identity(after) and count==before.st_size and sha(dest)==actual,'Captured source stability/readback failed')
        require(pinned is None or actual==pinned,'Original fixed SHA mismatch: '+str(source))
        return dest,dict(member=member,source_absolute_path=str(source),kind=kind,bytes=count,sha256=actual,
            source_identity=dict(device=str(before.st_dev),file_id=str(before.st_ino),mtime_ns=str(before.st_mtime_ns),bytes=before.st_size),
            source_handle_share='READ_ONLY_DENY_WRITES_AND_DELETE_DURING_CAPTURE',known_sha256_pin=pinned)
    finally:
        if h is not None:K.CloseHandle(h)

def main():
    require(sys.platform=='win32','Exact Windows C-only capture required')
    require(not OUT.exists(),'New component namespace required; preserve previous build')
    OUT.mkdir();inputs={};originals=[];components=[];notices=[]
    receipt_path=OUT/'build_receipt.json'
    receipt=dict(schema='MASTER_PUBLIC_COMPONENTS_LOCAL_BUILD_V1',state='IN_PROGRESS_NO_PURGE',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        network_calls=0,wsl_starts=0,mounts=0,source_deletions=0,g_writes=0,scientific_jobs=0,image_payload_bytes_read=0,remote_readback='NOT_RUN')
    try:
        selected=[(OLD/'.tools/source_archives'/n,'sources/'+n,'UNCHANGED_RETAINED_OFFICIAL_SOURCE_ARCHIVE',None,v[0]) for n,v in ARCHIVES.items()]
        selected += [(NATIVE/n,'native/iqtree-3.1.4-Windows/'+n,'UNCHANGED_NATIVE_IQTREE_DISTRIBUTION',EXE_SHA if n=='bin/iqtree3.exe' else None,size) for n,size in NATIVE_NAMES.items()]
        selected += [(p,n,'FIXED_PUBLIC_MANIFEST_OR_NOTICE',pin,None) for n,(p,pin) in FIXED.items()]
        selected += [(Path(__file__),'code/build_master_public_components01.py','BUILD_SOURCE',None,None)]
        for source,member,kind,pin,size in selected:
            captured,row=capture(source,member,kind,pin,size);inputs[member]=captured;originals.append(row)
        sourcepin=json.loads(inputs['manifests/iqtree_source_pin.json'].read_text())
        require(sourcepin['repository']=='https://github.com/iqtree/iqtree3' and sourcepin['tag']=='v3.1.4'
            and sourcepin['commit']=='63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de','Retained IQTREE source identity differs')
        for filename,v in ARCHIVES.items():
            size,root,repo,version,license_name,expected_count=v;source=inputs['sources/'+filename];count=0;found={}
            with tarfile.open(source,'r|gz') as t:
                for i in t:
                    count+=1;p=PurePosixPath(i.name)
                    require(not p.is_absolute() and '..' not in p.parts and '\\' not in i.name and p.parts[0]==root,'Source tar root/traversal differs')
                    if i.isfile() and len(p.parts)==2 and p.name in ('LICENSE','README.md'):
                        require(i.size<=128*1024,'Notice bounded size exceeded');data=t.extractfile(i).read()
                        member='notices/'+filename.removesuffix('.tar.gz')+'/'+p.name;path=OUT/'frozen'/member;write_new(path,data);inputs[member]=path
                        found[p.name]=dict(member=member,original_tar_member=i.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            require(count==expected_count and set(found)=={'LICENSE','README.md'},'Known source entry/notice selection differs')
            components.append(dict(name=filename,recorded_version=version,source_archive_member='sources/'+filename,source_archive_sha256=sha(source),
                embedded_source_root=root,embedded_commit=root.rsplit('-',1)[1],official_repository=repo,license_from_original_notice=license_name,
                original_notices=found,upstream_byte_equivalence='NOT_NEWLY_NETWORK_VERIFIED_RETAINED_BYTES_PINNED',archive_entries=count))
        package_rows={}
        for name in ('detector','host'):
            obj=json.loads(inputs['manifests/'+name+'_package_manifest.json'].read_text())
            require(len(obj['packages'])==({'detector':255,'host':142}[name]),'Original package selection differs')
            for r in obj['packages']:
                u=urllib.parse.urlsplit(r['url']);require(u.scheme=='https' and u.hostname=='conda.anaconda.org' and not u.username and not u.query
                    and re.fullmatch('[a-f0-9]{64}',r['sha256']) and r.get('license'),'Unreviewed/private package manifest URL or missing pin/license')
                package_rows[r['sha256']]=r
        require(len(package_rows)==339 and sum(r['size'] for r in package_rows.values())==660114049,'Original339 package identity accounting differs')
        attribution=('Public retained components for LAB R-M phylogenomics. Original notices are accessible under notices/; original source archives remain unchanged.\n\n'
            'CasFinder3.1.0: macsy-models/CasFinder; embedded sourcecommit ad7096548a814788ca04538602d71f85115b4c71; original CC-BY-NC-SA4.0 LICENSE and README/citations preserved.\n'
            'DefenseFinder models3.0.0: MDM Labs/maintainers, mdmparis/defense-finder-models; embedded sourcecommit9b0d07b759f5f73d8c2b9aa3e696f4cdd04c11d2; original GPL3 license and README/citations preserved.\n'
            'PADLOC-DB2.0.0: Leighton Payne and PADLOC contributors, padlocbio/padloc-db; embedded sourcecommit7f99b47b75e232b111c18626badb9ac32e8e0b5a; original MIT copyright/license and README/citations preserved. Model-level authors/references remain in the unmodified archive.\n'
            'IQ-TREE3.1.4: IQ-TREE developers/contributors, https://github.com/iqtree/iqtree3/tree/63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de; exact retained Windows distribution and original GPL license preserved, plus source-pin map. Full corresponding upstream source was not downloaded or added in this constrained build.\n'
            'Bundled libiomp5md.dll: Intel Corporation; embedded PE notice Copyright(C)1997-2014, Intel Corporation. All rights reserved.; FileVersion20140611/ProductVersion5.0. The retained upstream seven-file distribution has no standalone Intel runtime license. That separate license provenance remains unresolved; no substitute license is invented here.\n'
            'Two original public conda package manifests preserve339 distinct SHA-pinned official package identities and recorded license fields. Package artifacts are NOT in this archive. Those fields are provenance, not substitutes for original license texts in future package archives.\n\n'
            'This is a local preservation build, not a new model scientific acceptance or a complete installed-runtime/image recovery certificate. No source deletion, WSL, image access or network operation is performed.\n')
        p=OUT/'frozen/notices/ATTRIBUTION_AND_SOURCE_MAP.md';write_new(p,attribution.encode());inputs['notices/ATTRIBUTION_AND_SOURCE_MAP.md']=p
        component_map=dict(schema='MASTER_PUBLIC_COMPONENT_ATTRIBUTION_MAP_V1',state='RETAINED_PUBLIC_BYTES_ONLY',components=components,
            iqtree=dict(recorded_version='3.1.4',exe_sha256=EXE_SHA,official_repository=sourcepin['repository'],source_commit=sourcepin['commit'],source_pin_member='manifests/iqtree_source_pin.json',original_license_member='notices/IQTREE-3.1.4-LICENSE.txt',
                full_corresponding_source_archive_included=False,standalone_intel_runtime_license_in_retained_distribution=False),
            original_package_records=397,distinct_original_package_sha256=339,package_artifacts_included=False,
            notices_preserved_unchanged=True,source_archive_authenticity='RETAINED_OFFICIAL_INPUT_SCOPE_AND_INTERNAL_COMMIT_DECLARATION_NO_NEW_UPSTREAM_DOWNLOAD',
            installed_toolchain_image_included=False,scientific_acceptance_changes=False)
        p=OUT/'component_source_map.json';write_new(p,json_bytes(component_map));inputs['control/component_source_map.json']=p
        original_map=dict(schema='MASTER_PUBLIC_COMPONENT_ORIGINAL_SOURCE_MANIFEST_V1',state='NO_PURGE',files=originals,source_files=len(originals),source_bytes=sum(r['bytes'] for r in originals),
            image_excluded=True,private_or_unrelated_inputs_selected=False,original_tools_modified=False)
        p=OUT/'original_source_manifest.json';write_new(p,json_bytes(original_map));inputs['control/original_source_manifest.json']=p
        guide=('Public component preservation01. Only three known retained source/model tar.gz archives, the exact seven-file IQ-TREE3.1.4 Windows distribution, fixed public manifests/notices and this builder are selected.\n'
            'No ext4 image, installed environment, Python home, arbitrary cache, raw Codex session, credential or unrelated data is selected.\n'
            'All original source archives/distribution bytes and source notices are unchanged. Read notices/ATTRIBUTION_AND_SOURCE_MAP.md for source identities and explicit Intel-runtime/full-IQTREE-source coverage gaps.\n'
            'This archive does not authorize deletion or prove complete environment recovery, detector execution, scientific acceptance, or remote durability.\n')
        p=OUT/'README.txt';write_new(p,guide.encode());inputs['README.txt']=p
        captured={n:dict(sha256=sha(p),bytes=p.stat().st_size) for n,p in sorted(inputs.items())}
        binding=dict(schema='MASTER_PUBLIC_COMPONENT_SOURCE_BINDING_V1',state='LOCAL_BUILD_ONLY_NO_PURGE',builder_sha256=sha(__file__),payload_inputs=captured,
            original_sources=len(originals),source_original_identity_hash_stability_verified=True,original_live_exe_pin=EXE_SHA,all_original_notices_in_selected_source_archives_preserved=True,
            standalone_intel_runtime_notice_gap=True,full_iqtree_corresponding_source_not_in_selected_inputs=True,
            image_payload_bytes_read=0,network_calls=0,wsl_starts=0,source_deletions=0,g_writes=0)
        p=OUT/'source_binding.json';write_new(p,json_bytes(binding));inputs['control/source_binding.json']=p
        captured['control/source_binding.json']=dict(sha256=sha(p),bytes=p.stat().st_size)
        p=OUT/'SHA256SUMS.txt';write_new(p,''.join(r['sha256']+'  '+n+'\n' for n,r in sorted(captured.items())).encode());inputs['SHA256SUMS.txt']=p
        captured['SHA256SUMS.txt']=dict(sha256=sha(p),bytes=p.stat().st_size)
        archive=OUT/NAME
        with zipfile.ZipFile(archive,'x',allowZip64=True) as z:
            for n,p in sorted(inputs.items()):
                i=zipfile.ZipInfo(n,(2026,10,9,0,0,0));i.external_attr=0o100644<<16;i.compress_type=zipfile.ZIP_STORED if n.endswith('.tar.gz') else zipfile.ZIP_DEFLATED;i._compresslevel=1
                with p.open('rb') as src,z.open(i,'w',force_zip64=True) as dest:shutil.copyfileobj(src,dest,1024*1024)
        require(archive.stat().st_size<500*1024**2,'Public component ZIP exceeds strict500MiB bound')
        verified=[]
        with zipfile.ZipFile(archive) as z:
            require(len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(captured),'ZIP membership differs')
            for n,pin in sorted(captured.items()):
                with z.open(n) as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
                require(actual==pin['sha256'] and z.getinfo(n).file_size==pin['bytes'] and sha(inputs[n])==pin['sha256'],'Actual ZIP/captured input SHA/size differs')
                verified.append(dict(member=n,**pin,crc32=f'{z.getinfo(n).CRC:08x}',crc_verified=True))
        # Final stable-source verification is still read-only and deny-write scoped.
        for row in originals:
            source=plain(row['source_absolute_path']);s=source.stat();pin=row['source_identity']
            require(str(s.st_dev)==pin['device'] and str(s.st_ino)==pin['file_id'] and str(s.st_mtime_ns)==pin['mtime_ns'] and s.st_size==pin['bytes']
                and sha(source)==row['sha256'],'Original component changed after capture; do not publish')
        receipt.update(state='LOCAL_ZIP_ALL_BYTES_VERIFIED_NOTICE_COVERAGE_GAPS_EXPLICIT_NO_PURGE',archive=str(archive),asset_name=NAME,bytes=archive.stat().st_size,sha256=sha(archive),
            zip_members=len(captured),payload_members=len(captured)-1,source_files=len(originals),source_bytes=sum(r['bytes'] for r in originals),
            builder_sha256=sha(__file__),source_binding_sha256=sha(OUT/'source_binding.json'),source_manifest_sha256=sha(OUT/'original_source_manifest.json'),component_source_map_sha256=sha(OUT/'component_source_map.json'),
            all_member_crc_sha_and_expected_source_bytes_verified=True,live_native_exe_unchanged_sha256=EXE_SHA,original_sources_unchanged=True,
            standalone_intel_runtime_notice_gap=True,full_iqtree_corresponding_source_not_in_selected_inputs=True,original_source_notices_preserved_unchanged=True,members=verified)
        write_new(OUT/(NAME+'.sha256'),(receipt['sha256']+'  '+NAME+'\n').encode())
    except Exception as error:
        receipt.update(state='FAILED_COMPONENT_LOCAL_BUILD_NO_PURGE',error=dict(kind=type(error).__name__,message=str(error)));raise
    finally:
        receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();write_new(receipt_path,json_bytes(receipt))
    print(json.dumps({k:receipt[k] for k in ('state','archive','bytes','sha256','zip_members','source_files')},indent=2))

if __name__=='__main__':main()
