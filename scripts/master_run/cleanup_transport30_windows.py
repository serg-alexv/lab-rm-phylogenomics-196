"""Default NOOP. Exact thirty recovered C transport leaves; no recursive cleanup.

Root-only explicit adoption after source publication and current owner closure.
No WSL, Git, remote download, directory deletion, package or runtime operation.
"""
from pathlib import Path
import argparse,ast,ctypes as c,hashlib,importlib.util,json,os,time,uuid
from ctypes import wintypes as w

WORK=Path(__file__).resolve().parent
EXACT_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PROOF='transport30_current_requalification01.json'
PROOF_SHA='f3d4b7eaafbf59ace779ab0ab187551e2013774793b441251dcc1894baa8d952'
METADATA='transport30_current_remote_metadata01.json'
METADATA_SHA='7ac947dc70dc64bcd301a72e702ff2e9ce1cef08d6e596e2fd5f7e042c2668e2'
CAPACITY_PEER_SHA='e7cb6737c50e35c3119fe443d820b77174b2e0b8f3560c5303837b95e42ac2e9'
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
      'stage5_wsl_host_profile_fallback_owner.py':'49596d3e9c0ef684978d0cbb05bc57d97b100f08ab77a7a4ece598abc2221299'}
EXPECTED_BYTES=2048507163
DEADLINE_SECONDS=180
CHUNK_BYTES=4*1024**2
# Fixed literal relative leaves, generated once from the frozen exact-thirty proof.
TARGETS=(
    'public_history02_readback_20261009T195508Z_1f99201e\\master_public_history02-001.zip',
    'public_history02_readback_20261009T195508Z_1f99201e\\master_public_history02-001.zip.sha256',
    'public_history02_readback_20261009T195508Z_1f99201e\\master_public_history02-002.zip',
    'public_history02_readback_20261009T195508Z_1f99201e\\master_public_history02-002.zip.sha256',
    'public_history02_readback_20261009T195508Z_1f99201e\\master_public_history02-003.zip',
    'public_history02_readback_20261009T195508Z_1f99201e\\master_public_history02-003.zip.sha256',
    'public_conda_packages01_readback_20261009T212013Z_9326e9e6\\master_public_conda_packages01-001.zip',
    'public_conda_packages01_readback_20261009T212013Z_9326e9e6\\master_public_conda_packages01-001.zip.sha256',
    'public_conda_packages01_readback_20261009T212013Z_9326e9e6\\master_public_conda_packages01-002.zip',
    'public_conda_packages01_readback_20261009T212013Z_9326e9e6\\master_public_conda_packages01-002.zip.sha256',
    'public_conda_packages01_continuation_20261009T204518Z_bd4c1b76\\master_public_conda_packages01-001.zip',
    'public_conda_packages01_continuation_20261009T204518Z_bd4c1b76\\master_public_conda_packages01-001.zip.sha256',
    'public_conda_packages01_continuation_20261009T204518Z_bd4c1b76\\master_public_conda_packages01-002.zip',
    'public_conda_packages01_continuation_20261009T204518Z_bd4c1b76\\master_public_conda_packages01-002.zip.sha256',
    'public_components01_readback_20261009T195312Z_16720f4a\\master_public_components01.zip',
    'public_components01_readback_20261009T195312Z_16720f4a\\master_public_components01.zip.sha256',
    'master_public_history02\\master_public_history02-001.zip',
    'master_public_history02\\master_public_history02-001.zip.sha256',
    'master_public_history02\\master_public_history02-002.zip',
    'master_public_history02\\master_public_history02-002.zip.sha256',
    'master_public_history02\\master_public_history02-003.zip',
    'master_public_history02\\master_public_history02-003.zip.sha256',
    'master_public_components01\\master_public_components01.zip',
    'master_public_components01\\master_public_components01.zip.sha256',
    'master_batch03_mapping01\\master_batch03_scientific_cache_mapping01.zip',
    'master_batch03_mapping01\\master_batch03_scientific_cache_mapping01.zip.sha256',
    'batch03_mapping01_remote_readback_20261009T192220Z_3e6cf7d8\\master_batch03_scientific_cache_mapping01.zip',
    'batch03_mapping01_remote_readback_20261009T192220Z_3e6cf7d8\\master_batch03_scientific_cache_mapping01.zip.sha256',
    'batch03_execution01_readback_20261009T201344Z_f55cdf6b\\master_batch03_cleanup_execution01.zip',
    'batch03_execution01_readback_20261009T201344Z_f55cdf6b\\master_batch03_cleanup_execution01.zip.sha256',
)

def need(ok,message):
    if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def exact_raw(path,pin,limit=2*1024**2):
    need(path.is_file() and path.stat().st_size<=limit,'Bounded ordinary control required')
    for p in (path,*path.parents):need(not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'Plain control ancestry required')
    raw=path.read_bytes();need(len(raw)<=limit and digest(raw)==pin,'Exact control bytes changed');return raw

def controls():
    proof=json.loads(exact_raw(WORK/PROOF,PROOF_SHA));meta=json.loads(exact_raw(WORK/METADATA,METADATA_SHA))
    rows=proof['rows']
    need(proof['state']=='PASS_30_CURRENT_LOCAL_HASH_IDENTITY_AND_REMOTE_TAG_ASSET_DIGEST_METADATA_NO_PURGE'
         and proof['files']==30 and proof['logical_bytes']==EXPECTED_BYTES and len(rows)==30
         and tuple(str(Path(r['path']).relative_to(WORK)) for r in rows)==TARGETS,'Exact fixed thirty transport scope differs')
    need(len(set(TARGETS))==30 and sum(r['bytes'] for r in rows)==EXPECTED_BYTES,'Exact30 accounting differs')
    assets={r['id']:r for r in meta['assets']}
    for row in rows:
        need(row['current_identity_stable'] is True and row['current_local_sha256']==row['expected_recovery']['expected_sha256']
             and row['current_remote_asset']['digest']=='sha256:'+row['current_local_sha256']
             and row['current_remote_asset']['id']==row['expected_recovery']['remote_asset_id']
             and row['current_remote_asset']['size']==row['bytes'] and row['current_remote_asset']['state']=='uploaded'
             and row['exclusive_writer_guard'] is False and row['fresh_remote_asset_bytes_downloaded'] is False,
             'Current local/current API/detailed dated full-reader proof joins differ')
        need(all(row['current_remote_asset'][key]==assets[row['current_remote_asset']['id']][key]
                 for key in ('id','name','size','digest','state')),'Exact saved API asset metadata differs')
        need(Path(row['path']).suffix in ('.zip','.sha256') and row['before']['nlink']==1,'Only single-link literal ZIP/sidecar leaves')
    need(proof['current_remote_metadata_sha256']==METADATA_SHA and meta['ref']['object']['sha']=='46c7089f906cce59afabaa4449b05df36ee124de',
         'Frozen current tag metadata differs')
    return proof,rows

def prepare_finalizer():
    """Prepare the pinned reviewed tail before acquiring any native handles/lock."""
    source=exact_raw(WORK/'stage5_wsl_host_profile_fallback_owner.py',PINS['stage5_wsl_host_profile_fallback_owner.py']).decode()
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='finish_after_unlock')
    helper=ast.get_source_segment(source,node).replace('HOST_PROFILE_VALIDATED_PENDING_EXPLICIT_UNLOCK','TRANSPORT30_VALIDATED_PENDING_EXPLICIT_UNLOCK').replace('PASS_NONSCIENTIFIC_WINDOWS_HOST_PROFILE_CHANGED_AND_ALL_DISTROS_STOPPED','PASS_EXACT30_RETAINED_TRANSPORT_LEAVES_REMOVED').replace('STAGE05_HOST_PROFILE_FINAL_PUBLICATION_FAILURE_V1','MASTER_EXACT30_FINAL_PUBLICATION_FAILURE_V1').replace('Profile-owned stop','Cleanup-owned stop').replace('Profile publication failure','Cleanup publication failure')
    ns={'need':need,'digest':digest};exec(compile(helper,'reviewed49596_finalizer','exec'),ns)
    return ns['finish_after_unlock']

class NativeLeaves:
    """Retained native file handles only; source default never constructs this."""
    def __init__(self,api):
        need(os.name=='nt' and c.sizeof(c.c_void_p)==8,'Windows64 required');self.api=api;self.handles={};self.close_errors=[];self.effects=[]
        def bind(name,result,args):
            fn=getattr(api.K,name);fn.restype=result;fn.argtypes=args;return fn
        self.create=bind('CreateFileW',w.HANDLE,[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE])
        self.info_ex=bind('GetFileInformationByHandleEx',w.BOOL,[w.HANDLE,c.c_int,c.c_void_p,w.DWORD])
        self.read=bind('ReadFile',w.BOOL,[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p])
        self.set_info=bind('SetFileInformationByHandle',w.BOOL,[w.HANDLE,c.c_int,c.c_void_p,w.DWORD])
        class ID(c.Structure):_fields_=[('volume',c.c_uint64),('file_id',c.c_ubyte*16)]
        class Disposition(c.Structure):_fields_=[('delete_file',c.c_ubyte)]
        self.ID=ID;self.Disposition=Disposition
    def open(self,path,directory=False):
        access=0x80 if directory else 0x80000000|0x00010000
        sharing=3 if directory else 0
        flags=0x02000000|0x00200000 if directory else 0x00200000|0x08000000
        handle=self.create(str(path),access,sharing,None,3,flags,None)
        need(handle not in (None,0,c.c_void_p(-1).value),'Retained exclusive native open failed')
        self.handles[int(handle)]={'path':str(path),'directory':directory,'close_attempted':False,
                                   'delete_disposition_attempted':False,'delete_disposition_returned':False};return int(handle)
    def info(self,handle):
        basic=self.api.FILEINFO();self.api.ok(self.api.file_info(handle,c.byref(basic)),'Retained leaf/ancestor information')
        wide=self.ID();self.api.ok(self.info_ex(handle,18,c.byref(wide),c.sizeof(wide)),'Retained128-bit file ID')
        ns=lambda ft:(self.api.ft(ft)-116444736000000000)*100
        return {'device':int(wide.volume),'inode':int.from_bytes(bytes(wide.file_id),'little'),
                'bytes':(basic.sizeHigh<<32)|basic.sizeLow,'nlink':int(basic.links),
                'birthtime_ns':ns(basic.created),'mtime_ns':ns(basic.written),'file_attributes':int(basic.attributes)}
    def hash(self,handle,expected_bytes,deadline):
        h=hashlib.sha256();buffer=c.create_string_buffer(CHUNK_BYTES);count=0
        while True:
            need(time.monotonic()<deadline,'Exact30 finite observer deadline exceeded')
            got=w.DWORD();self.api.ok(self.read(handle,buffer,CHUNK_BYTES,c.byref(got),None),'Retained exclusive read')
            need(got.value<=CHUNK_BYTES,'Native read count exceeded fixed buffer')
            if not got.value:break
            count+=got.value;need(count<=expected_bytes,'Retained leaf grew');h.update(buffer.raw[:got.value])
        need(count==expected_bytes,'Retained leaf length differs');return h.hexdigest()
    def mark_delete(self,handle):
        record=self.handles[handle];need(not record['directory'] and not record['delete_disposition_attempted'],'One literal leaf disposition only')
        effect={'path':record['path'],'delete_disposition_attempted':True,'delete_disposition_returned':False,
                'handle_close_proven':False,'absence_verified':False}
        self.effects.append(effect);record['delete_disposition_attempted']=True
        value=self.Disposition(1);self.api.ok(self.set_info(handle,4,c.byref(value),c.sizeof(value)),'Exact retained-handle delete disposition')
        record['delete_disposition_returned']=effect['delete_disposition_returned']=True
    def close(self,handle):
        record=self.handles[handle];need(not record['close_attempted'],'Never blindly retry uncertain native close')
        record['close_attempted']=True
        if not self.api.close(handle):
            self.close_errors.append(dict(record));raise OSError('Retained native CloseHandle failed; ownership remains unresolved')
        for effect in self.effects:
            if effect['path']==record['path']:effect['handle_close_proven']=True
        del self.handles[handle]
    def finalize(self):
        for handle,record in list(self.handles.items())[::-1]:
            if not record['close_attempted']:
                try:self.close(handle)
                except BaseException:pass
        return not self.handles and not self.close_errors

def match(actual,row):
    expected={k:row['before'][k] for k in actual}
    need(all(type(actual[k]) is type(v) and actual[k]==v for k,v in expected.items()),'Exact native retained file identity differs')
    need(actual['nlink']==1 and not actual['file_attributes']&(0x400|0x10),'Plain single-link ordinary leaf required')

def absent(path):
    try:path.lstat()
    except FileNotFoundError as error:need(getattr(error,'winerror',None)==2,'Exact Windows missing-file result required')
    else:raise ValueError('Deleted exact leaf still exists; do not recurse or retry')

def purge_exact(rows,native,progress,check,deadline):
    """Open and hash the entire fixed set before the first delete disposition."""
    ancestors=sorted({p for r in rows for p in Path(r['path']).parents},key=lambda p:len(p.parts))
    need(len(ancestors)<=64,'Bounded fixed ancestor set exceeded')
    for path in ancestors:
        check();handle=native.open(path,True);info=native.info(handle)
        need(info['file_attributes']&0x10 and not info['file_attributes']&0x400,'Ancestor must be ordinary directory')
    retained=[]
    for row in rows:
        check();handle=native.open(Path(row['path']));before=native.info(handle);match(before,row)
        actual=native.hash(handle,row['bytes'],deadline);need(actual==row['current_local_sha256'],'Exact exclusive retained SHA differs')
        need(native.info(handle)==before,'Retained leaf metadata changed during hash')
        retained.append((handle,row,before))
    progress('ALL30_EXCLUSIVE_IDENTITIES_AND_SHA256_VERIFIED',{'files':30,'logical_bytes':EXPECTED_BYTES})
    deleted=[]
    for index,(handle,row,before) in enumerate(retained,1):
        check();need(time.monotonic()<deadline,'Exact30 effect deadline exceeded');need(native.info(handle)==before,'Leaf changed before disposition')
        details={'index':index,'path':row['path'],'identity':before,'sha256':row['current_local_sha256'],
                 'remote_asset':row['current_remote_asset'],'dated_recovery':row['expected_recovery']}
        progress('BEFORE_EXACT_RETAINED_HANDLE_DELETE_DISPOSITION',details)
        native.mark_delete(handle)
        progress('DELETE_DISPOSITION_RETURNED_BEFORE_HANDLE_CLOSE',details)
        native.close(handle)
        absent(Path(row['path']))
        for effect in native.effects:
            if effect['path']==row['path']:effect['absence_verified']=True
        deleted.append(details);progress('EXACT_LEAF_DELETED_HANDLE_CLOSED_AND_ABSENCE_VERIFIED',details)
    return deleted

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--source-sha256')
    args=parser.parse_args()
    if not args.run:
        print(json.dumps({'state':'NO_OP_EXACT30_TRANSPORT_CLEANUP','candidate_files':30,'logical_bytes':EXPECTED_BYTES,'effects':0}));return 0
    need(os.name=='nt' and WORK==EXACT_WORK,'Exact current Windows C work required')
    source_sha=digest(Path(__file__).read_bytes());need(source_sha==args.source_sha256,'Explicit reviewed cleanup source SHA required')
    for name,pin in PINS.items():exact_raw(WORK/name,pin)
    finish_after_unlock=prepare_finalizer()
    A=module('_cleanup30_A80a2',WORK/'atomic_iqtree_windows.py')
    F=module('_cleanup30_F49596',WORK/'stage5_wsl_host_profile_fallback_owner.py');M=F.load_base();G=M.load_base()
    proof,rows=controls();peer,values,entries=F.capacity_read(G,CAPACITY_PEER_SHA)
    api=A.Win();native=NativeLeaves(api);owner=api.identity(api.current(),os.getpid());nonce=uuid.uuid4().hex
    out=WORK/('transport30_cleanup_'+nonce);out.mkdir();G.plain_chain(out)
    stop=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json');lock=A.WorkflowLock(api)
    record={'schema':'MASTER_EXACT30_RETAINED_TRANSPORT_CLEANUP_V1','state':'FAILED','source_sha256':source_sha,
            'owner_nonce':nonce,'owner':owner,'proof_sha256':PROOF_SHA,'capacity02_peer_sha256':CAPACITY_PEER_SHA,
            'candidate_files':30,'candidate_logical_bytes':EXPECTED_BYTES,'WSL_launches':0,'children_created':0,
            'deleted':[],'protected_receipts_packages_runtime_images_unchanged_by_source_scope':True,
            'fresh_remote_bytes_downloaded':False,'remote_metadata_query_utc':proof['current_remote_queried_utc']}
    start=time.monotonic();deadline=start+DEADLINE_SECONDS;stop_sha=None;sequence=0;held=False;closed=True
    def check():
        need(time.monotonic()<deadline,'Bounded exact30 cleanup deadline exceeded')
        need(digest(Path(__file__).read_bytes())==source_sha,'Cleanup source changed')
        controls();need(F.capacity_read(G,CAPACITY_PEER_SHA)[2]==entries,'Exact original closed capacity02 evidence changed')
        need(stop_sha is not None and digest(stop.read_bytes())==stop_sha and A.read_json(stop)['owner_nonce']==nonce,'Own cleanup STOP changed')
    def progress(phase,details):
        nonlocal sequence
        sequence+=1;event={'phase':phase,'sequence':sequence,'owner_nonce':nonce,'utc':A.utc(),**details}
        if phase=='EXACT_LEAF_DELETED_HANDLE_CLOSED_AND_ABSENCE_VERIFIED':record['deleted'].append(details)
        A.atomic(out/f'{sequence:03d}.json',event);need(A.read_json(out/f'{sequence:03d}.json')==event,'Durable intent/result readback differs')
    try:
        held_lock=lock.__enter__();held=True;need(not stop.exists(),'Existing unproven closure STOP vetoes cleanup')
        F.exact_lock(held_lock.identity);record['workflow_lock']=held_lock.identity
        A.atomic(stop,{'schema':'STAGE05_UNPROVEN_CLOSURE_STOP_V1','owner_nonce':nonce,'utc':A.utc(),'evidence':str(out),
                      'reason':'Exact30 retained native file/ancestor handles require checked closure and original unlock','automatic_resume':False})
        stop_sha=digest(stop.read_bytes());closed=False
        purge_exact(rows,native,progress,check,deadline)
        check();record['state']='TRANSPORT30_VALIDATED_PENDING_EXPLICIT_UNLOCK'
    except BaseException as error:record['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        try:closed=native.finalize()
        except BaseException as error:
            closed=False;record['retained_client_finalizer_error']={'kind':type(error).__name__,'message':str(error)}
        record.update(retained_file_handles_closed=closed,unclosed_handles=list(native.handles.values()),native_close_errors=native.close_errors,
            delete_disposition_effects=native.effects,unreconciled_delete_effects=[x for x in native.effects if not x['absence_verified']],
            deleted_files=len(record['deleted']),deleted_logical_bytes=sum(x['identity']['bytes'] for x in record['deleted']),elapsed_seconds=time.monotonic()-start)
        if held:finish_after_unlock(A,lock,out,record,stop,stop_sha,nonce,closed)
        else:A.atomic(out/'result.json',record)
    print(json.dumps({'state':record['state'],'result':str(out/'result.json'),'deleted_files':record['deleted_files']}))
    return 0 if record['state']=='PASS_EXACT30_RETAINED_TRANSPORT_LEAVES_REMOVED' and closed and record.get('original_unlock_receipt_proven') is True else 2

if __name__=='__main__':raise SystemExit(main())
