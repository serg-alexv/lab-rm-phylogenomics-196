"""Inactive, Linux-only, NEW-tree extraction of independently recovered shards.

No download/CLI extraction, original runtime read, native process or deletion.
An external reviewed owner must enforce admission, lease and finite closure.
Absolute original-prefix link TEXT is preserved and never followed here. A
role-layout restore is not an original-prefix runtime/ABI equivalence proof.
"""
from pathlib import Path, PurePosixPath
from decimal import Decimal
import base64, ctypes, datetime as dt, hashlib, importlib.util, io, json
import os, platform, re, sqlite3, stat, sys, tarfile, time, unicodedata

C_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
L_WORK=Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
W=Path(__file__).resolve().parent
REPO='serg-alexv/lab-rm-phylogenomics-196'
PINS={'stage5_runtime_recovery_contract.py':'daf48ea1c8cc96312519b1ab22f2d41216494773e5e345e3e5e0417139588bb6',
      'verify_stage5_runtime_logical_payload.py':'9770354da6e9f8cbbab3735f78daadf458b18a86bfae7c90ce2492430c1a74ac',
      'verify_stage5_runtime_cold_tree.py':'cd64e0d4da3ab2509f93d4295af891e0173ed9bef9d81007620bf1f4d872fcfe'}
CAPTURE_SHA='21b33abc389efe9bbfdcf8048737f2d7f10ce60b52d6e1c6f3678b24568b8220'
BLOCK=256*1024
MAX_CONTROL=64*1024**2
CONTROL_ORDER=('cold_proof','manifest','notices','public_review','runtime')


def need(ok,message):
    if not ok:raise ValueError(message)


def digest(data):return hashlib.sha256(data).hexdigest()


def sha(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None


def strict_json(raw):
    def pairs(values):
        result={}
        for key,value in values:
            need(key not in result,'Duplicate JSON object key');result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs)


def relative(value,root=False):
    need(isinstance(value,str) and value and '\\' not in value and ':' not in value
         and unicodedata.normalize('NFC',value)==value
         and not any(ord(c)<32 or ord(c)==127 for c in value),'Unsafe relative path/drive/ADS')
    p=PurePosixPath(value)
    need(not p.is_absolute() and p.as_posix()==value and '..' not in p.parts
         and (value!='.' or root) and all(len(x.encode('utf-8'))<=255 for x in p.parts)
         and len(value.encode('utf-8'))<=4095,'Noncanonical/oversized relative path')
    return value


def helpers():
    need(W in (C_WORK,L_WORK),'Exact reviewed source deployment required')
    values=[]
    for number,(name,expected) in enumerate(PINS.items()):
        path=W/name;raw=path.read_bytes();need(digest(raw)==expected,'Pinned independent helper differs')
        spec=importlib.util.spec_from_file_location('runtime_extract_helper_'+str(number),path)
        value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
        need(digest(path.read_bytes())==expected,'Helper changed during import');values.append(value)
    return tuple(values)


def index_contract(raw):
    need(isinstance(raw,bytes) and len(raw)<5*1024**2,'Bounded immutable index bytes required')
    C,_,_=helpers();v=strict_json(raw)
    need(v.get('schema')=='STAGE05_RUNTIME_LOGICAL_ARCHIVE_INDEX_V1' and v.get('roots')==C.ROOTS
         and v.get('maximum_asset_bytes')==C.SHARD_LIMIT and v.get('source_sha256')==CAPTURE_SHA
         and v.get('installed_build_equivalence')=='NOT_ESTABLISHED' and v.get('cleanup_authority') is False,
         'Exact pinned logical archive index required')
    rows=v['shards'];need(isinstance(rows,list) and 1<=len(rows)<=64,'Bounded ordered shard count')
    for number,row in enumerate(rows,1):
        need(set(row)=={'name','bytes','sha256'} and row['name']=='stage5-installed-runtime-01.part'+str(number).zfill(4)
             and type(row['bytes']) is int and 0<row['bytes']<=C.SHARD_LIMIT and sha(row['sha256'])
             and (number==len(rows) or row['bytes']==C.SHARD_LIMIT),'Invalid shard order/size/hash')
    need(v['compressed_bytes']==sum(r['bytes'] for r in rows) and sha(v['compressed_stream_sha256'])
         and type(v['uncompressed_tar_bytes']) is int and 0<v['uncompressed_tar_bytes']<=32*1024**3
         and type(v['entry_count']) is int and 3<=v['entry_count']<=500000
         and type(v['regular_bytes']) is int and 0<=v['regular_bytes']<=32*1024**3
         and set(v['control_sha256'])==set(CONTROL_ORDER) and all(sha(x) for x in v['control_sha256'].values()),
         'Index totals/control pins invalid')
    return v


def remote_plan(index_raw,source_commit,release_tag,tag_commit):
    """Pure plan only. A separate owned downloader must establish its evidence."""
    index=index_contract(index_raw)
    need(re.fullmatch('[a-f0-9]{40}',source_commit or '') and re.fullmatch('[a-f0-9]{40}',tag_commit or '')
         and re.fullmatch('[A-Za-z0-9._-]{1,128}',release_tag or ''),'Immutable remote commit/tag required')
    assets=[]
    for row in index['shards']:
        assets.append(dict(name=row['name'],bytes=row['bytes'],sha256=row['sha256']))
        line=(row['sha256']+'  '+row['name']+'\n').encode('ascii')
        assets.append(dict(name=row['name']+'.sha256',bytes=len(line),sha256=digest(line)))
    return dict(schema='STAGE05_INSTALLED_RUNTIME_REMOTE_PLAN_V1',state='PENDING_ACTUAL_FRESH_REMOTE_VERIFICATION',
                repository=REPO,source_commit=source_commit,release_tag=release_tag,tag_target_commit=tag_commit,
                index_sha256=digest(index_raw),assets=assets,accepted_remote=False,
                capture_control_sha256=index['control_sha256'],helper_source_sha256=PINS,
                actual_download='NOT_RUN',cleanup_authority=False,installed_build_equivalence='NOT_ESTABLISHED')


def remote_gate(index_raw,remote_raw,expected_remote_sha,payload_raw,expected_payload_sha,
                source_commit,release_tag,tag_commit,remote_verifier_sha,now=None,synthetic=False):
    """Bind independently supplied, externally SHA-pinned evidence; never mint it.

    Pure synthetic mode is only for contract tests; extract() never enables it.
    The future remote wrapper itself is not implemented or accepted by this API.
    """
    need(sha(expected_remote_sha) and sha(expected_payload_sha) and sha(remote_verifier_sha)
         and digest(remote_raw)==expected_remote_sha and digest(payload_raw)==expected_payload_sha,
         'External remote/payload/source receipt pins differ')
    plan=remote_plan(index_raw,source_commit,release_tag,tag_commit);index=index_contract(index_raw)
    remote=strict_json(remote_raw);payload=strict_json(payload_raw)
    need(remote.get('schema')=='STAGE05_INSTALLED_RUNTIME_FRESH_REMOTE_RECOVERY_V1'
         and remote.get('dataset_kind')==('SYNTHETIC' if synthetic else 'PRODUCTION')
         and remote.get('state')==('PASS_SYNTHETIC_REMOTE_GATE_CONTRACT' if synthetic else 'PASS_FRESH_REMOTE_FULL_INSTALLED_RUNTIME_BYTES')
         and remote.get('accepted_remote') is (not synthetic),'Actual independent fresh remote gate required')
    for key in ('repository','source_commit','release_tag','tag_target_commit','index_sha256','capture_control_sha256','helper_source_sha256'):
        need(remote.get(key)==plan[key],'Remote identity/source/control binding differs: '+key)
    need(remote.get('remote_verifier_source_sha256')==remote_verifier_sha
         and remote.get('independent_payload_receipt_sha256')==expected_payload_sha
         and all(remote.get(key) is True for key in ('all_git_control_bytes_verified','all_asset_bytes_verified',
             'all_sidecars_exact','asset_metadata_stable_before_after','owned_download_clients_closed','fresh_unique_download_namespace')),
         'Incomplete actual remote payload/download closure proof')
    before=remote['assets_before'];after=remote['assets_after']
    need(before==after and len(before)==len(plan['assets']),'Current selected asset metadata drift/missing')
    ids=set()
    for actual,expected in zip(before,plan['assets']):
        need(set(actual)=={'id','name','bytes','sha256'} and type(actual['id']) is int and actual['id']>0
             and actual['id'] not in ids and all(actual[k]==expected[k] for k in expected),'Exact asset ID/digest/size differs')
        ids.add(actual['id'])
    observed=dt.datetime.fromisoformat(remote['verified_at_utc'])
    now=now or dt.datetime.now(dt.timezone.utc)
    need(observed.tzinfo is not None and now.tzinfo is not None and -5<=(now-observed).total_seconds()<=900,
         'Fresh actual remote receipt required (15-minute maximum age)')
    need(payload.get('state')=='PASS_LOCAL_FULL_RUNTIME_PAYLOAD_AND_POSIX_MANIFEST_FRESH_REMOTE_NOT_PROVEN'
         and payload.get('index_sha256')==plan['index_sha256']
         and payload.get('compressed_stream_sha256')==index['compressed_stream_sha256']
         and payload.get('shards')==len(index['shards']) and payload.get('entry_count')==index['entry_count']
         and all(payload.get(k) is True for k in ('all_regular_file_sha_verified','all_control_sha_verified',
             'all_gzip_crc_verified','complete_internal_symlink_graph_verified'))
         and payload.get('extraction') is False and payload.get('installed_build_equivalence')=='NOT_ESTABLISHED',
         'Independent exhaustive local payload receipt required')
    C,_,_=helpers();inputs=remote['capture_inputs'];C.capture_gate(inputs)
    expected={'manifest':inputs['complete_inventory_sha256'],'runtime':inputs['actual_runtime_manifest_sha256'],
              'public_review':inputs['whole_file_public_review_sha256'],'cold_proof':inputs['cold_exclusive_capture_receipt_sha256'],
              'notices':inputs['license_source_notice_review_sha256']}
    need(expected==index['control_sha256'] and inputs['published_capture_source_sha256']==CAPTURE_SHA,
         'Remote source scope and capture authority differ')
    return index,remote


def exact_control(path,expected,guard,capture=False):
    path=Path(path);need(path.resolve()==path and not path.is_symlink(),'Plain verified control path required')
    h=hashlib.sha256();size=0;captured=bytearray() if capture else None
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size<=MAX_CONTROL,'Control size/type bound')
        while data:=stream.read(BLOCK):
            guard();h.update(data);size+=len(data)
            need(size<=MAX_CONTROL,'Control grew beyond bounded size')
            if capture:captured.extend(data)
        after=os.fstat(stream.fileno())
    final=path.lstat()
    key=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_nlink)
    need(key(before)==key(after)==key(final) and size==before.st_size and h.hexdigest()==expected,'Verified control bytes/identity drift')
    guard();return bytes(captured) if capture else size


def load_ledger(manifest,db,C,R,guard,verified_raw=None):
    """Bounded disk index; strict extra path/inode checks precede any extraction."""
    prior='';count=0
    db.execute('CREATE TABLE originals(dev INTEGER,ino INTEGER,key TEXT,PRIMARY KEY(dev,ino))')
    if verified_raw is not None:
        need(isinstance(verified_raw,bytes) and len(verified_raw)<=MAX_CONTROL,'Bounded captured manifest bytes required')
    with (io.BytesIO(verified_raw) if verified_raw is not None else Path(manifest).open('rb')) as stream:
        while line:=stream.readline(1024**2+1):
            guard();need(len(line)<=1024**2 and line.endswith(b'\n'),'Bounded complete ledger line required')
            row=strict_json(line);C.entry(row);relative(row['path'],True)
            if row['kind']=='symlink':
                need(':' not in row['link_target'] and unicodedata.normalize('NFC',row['link_target'])==row['link_target'],
                     'Unsafe symlink drive/ADS/noncanonical text')
                need(row['mode']==0o777,'Linux symlink mode cannot be restored exactly')
            if row['kind']=='hardlink':relative(row['link_target'])
            key=row['role']+'/'+row['path'];need(key>prior,'Duplicate/noncanonical ledger order');prior=key
            found=db.execute('SELECT key FROM originals WHERE dev=? AND ino=?',(row['source_dev'],row['source_ino'])).fetchone()
            need((found==(row['link_target'],)) if row['kind']=='hardlink' else found is None,
                 'Original inode alias graph invalid')
            if row['kind']!='hardlink':db.execute('INSERT INTO originals VALUES(?,?,?)',(row['source_dev'],row['source_ino'],key))
            count+=1;need(count<=500000,'Ledger count limit')
    db.execute('CREATE TABLE entries(name TEXT PRIMARY KEY,kind TEXT,row_json TEXT,seen INTEGER)')
    class CapturedManifest:
        def open(self,*args,**kwargs):return io.TextIOWrapper(io.BytesIO(verified_raw),encoding='utf-8',newline='')
    result=R.store_manifest(db,CapturedManifest() if verified_raw is not None else Path(manifest))
    need(result[0]==count,'Ledger count drift')
    db.execute('CREATE INDEX ordered_unseen ON entries(seen,name)')
    for (text,) in db.execute("SELECT row_json FROM entries WHERE kind='symlink'"):
        guard();row=strict_json(text);R.node_for_original(db,C.absolute(row))
    db.execute('CREATE TABLE restored(name TEXT PRIMARY KEY,dev INTEGER,ino INTEGER)');db.commit()
    return result


def tar_member(item,row,R):
    relative(item.name);need(set(item.pax_headers)<={'mtime','path','linkpath'} and not item.sparse,
                             'Unreviewed/sparse PAX metadata forbidden')
    need(item.name==R.member_for(row) and (item.mode,item.uid,item.gid)==(row['mode'],row['uid'],row['gid'])
         and Decimal(item.pax_headers.get('mtime',str(item.mtime)))*10**9==row['mtime_ns'], 'Exact payload metadata differs')
    kinds={'regular':item.isreg,'directory':item.isdir,'symlink':item.issym,'hardlink':item.islnk}
    need(kinds[row['kind']]() and item.size==(row['bytes'] if row['kind']=='regular' else 0),'Payload type/size differs')
    link=row['link_target'] if row['kind']=='symlink' else 'payload/'+row['link_target'] if row['kind']=='hardlink' else ''
    need(item.linkname==link,'Payload link text differs')


class SafeLinux:
    """Linux x86_64 ABI, no fallback: no mount/symlink traversal in opens.

    Linux6.18 UAPI open_how/flags and x86 syscall437; linkat AT_EMPTY_PATH
    binds the exact retained source inode. No tarfile extraction method is used.
    """
    class How(ctypes.Structure):
        _fields_=[('flags',ctypes.c_uint64),('mode',ctypes.c_uint64),('resolve',ctypes.c_uint64)]
    def __init__(self):
        need(sys.platform=='linux' and platform.machine()=='x86_64' and ctypes.sizeof(self.How)==24,'Exact Linux x86_64 openat2 ABI required')
        self.libc=ctypes.CDLL(None,use_errno=True);self.libc.syscall.restype=ctypes.c_long
        self.libc.linkat.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_int]
        self.libc.linkat.restype=ctypes.c_int
    def opened(self,parent,name,flags,mode=0):
        relative(name,True);how=self.How(flags|os.O_NOFOLLOW|os.O_CLOEXEC,mode,0x01|0x02|0x04|0x08)
        fd=self.libc.syscall(ctypes.c_long(437),ctypes.c_int(parent),ctypes.c_char_p(name.encode()),ctypes.byref(how),ctypes.c_size_t(24))
        if fd<0:raise OSError(ctypes.get_errno(),'Required no-mount/no-link openat2 rejected')
        return int(fd)
    def linked(self,source,parent,leaf):
        relative(leaf);need('/' not in leaf,'One literal hardlink leaf required')
        if self.libc.linkat(source,b'',parent,leaf.encode(),0x1000)!=0:
            raise OSError(ctypes.get_errno(),'Required exact-inode AT_EMPTY_PATH hardlink failed')


def extract(index_raw,remote_raw,expected_remote_sha,payload_raw,expected_payload_sha,
            source_commit,release_tag,tag_commit,remote_verifier_sha,shards_directory,
            verified_controls,staging,evidence,admission):
    """Inactive owner-callable API. Preserve failed partial trees; never adopt them."""
    need(os.name=='posix' and sys.platform=='linux' and W==L_WORK and os.geteuid()==0 and callable(admission),
         'Reviewed Linux root owner/exact deployment/admission required')
    index,remote=remote_gate(index_raw,remote_raw,expected_remote_sha,payload_raw,expected_payload_sha,
                            source_commit,release_tag,tag_commit,remote_verifier_sha)
    C,R,T=helpers();start=time.monotonic()
    def guard():
        need(time.monotonic()-start<=1800,'Finite extraction deadline exceeded');admission()
    staging,evidence,directory=map(Path,(staging,evidence,shards_directory))
    need(staging.parent==Path('/var/tmp') and re.fullmatch('lab_rm_runtime_restore_[A-Za-z0-9_]+',staging.name)
         and not staging.exists() and not staging.is_symlink() and staging.parent.resolve()==staging.parent,
         'NEW direct disposable ext4 staging path required')
    need(evidence.parent==L_WORK and re.fullmatch('stage5_runtime_extract_evidence_[A-Za-z0-9_]+',evidence.name)
         and not evidence.exists() and not evidence.is_symlink(),'NEW direct C extraction evidence required')
    need(directory.parent==L_WORK and re.fullmatch('stage5_runtime_remote_[A-Za-z0-9_]+',directory.name)
         and directory.resolve()==directory and directory.is_dir() and not directory.is_symlink(), 'Fresh C remote namespace required')
    need(set(verified_controls)==set(CONTROL_ORDER),'Exact five previously verified control files required')
    for key,path in verified_controls.items():
        path=Path(path);need(path.parent.parent==L_WORK and path.parent.name.startswith('stage5_runtime_payload_readback_')
                             and path.name==key+('.jsonl' if key=='manifest' else '.json'),'Independent readback control role required')
        exact_control(path,index['control_sha256'][key],guard)
    guard();evidence.mkdir();db=sqlite3.connect(evidence/'manifest.sqlite3');rootfd=parentfd=None
    parts=compressed=plain=None;record={'schema':'STAGE05_NEW_RUNTIME_LOGICAL_EXTRACTION_V1','state':'FAILED_PARTIAL_PRESERVED',
        'index_sha256':digest(index_raw),'remote_receipt_sha256':expected_remote_sha,'payload_receipt_sha256':expected_payload_sha,
        'staging':str(staging),'original_runtime_payload_reads':0,'native_launches':0,'cleanup_authority':False,
        'installed_build_equivalence':'NOT_ESTABLISHED','original_prefix_runtime_execution':'NOT_RUN'}
    try:
        manifest_raw=exact_control(verified_controls['manifest'],index['control_sha256']['manifest'],guard,True)
        counts=load_ledger(verified_controls['manifest'],db,C,R,guard,manifest_raw);del manifest_raw
        need(counts==(index['entry_count'],index['regular_bytes']),'Exact index/manifest totals differ')
        runtime=strict_json(exact_control(verified_controls['runtime'],index['control_sha256']['runtime'],guard,True))
        review=strict_json(exact_control(verified_controls['public_review'],index['control_sha256']['public_review'],guard,True))
        notices=strict_json(exact_control(verified_controls['notices'],index['control_sha256']['notices'],guard,True))
        cold=strict_json(exact_control(verified_controls['cold_proof'],index['control_sha256']['cold_proof'],guard,True))
        need(review.get('schema')=='STAGE05_RUNTIME_PUBLIC_SCOPE_REVIEW_V1' and review.get('whole_file_review_executed') is True
             and review.get('inventory_sha256')==index['control_sha256']['manifest']
             and notices.get('scope_reviewed') is True and notices.get('inventory_sha256')==index['control_sha256']['manifest']
             and cold.get('schema')=='STAGE05_RUNTIME_COLD_CAPTURE_PROOF_V1'
             and all(cold.get(k) is True for k in ('original_workflow_lock_held','all_relevant_native_jobs_closed','backing_image_writer_exclusion_proven')),
             'Actual public/notice/exclusive capture controls required')
        decisions=review['entries'];need(len(decisions)==counts[0],'Exhaustive public decisions required')
        for (text,) in db.execute('SELECT row_json FROM entries'):
            guard();row=strict_json(text);need(decisions.get(row['role']+'/'+row['path'],{}).get('decision')=='PUBLIC_ORIGINAL_BYTES',
                                               'Every restored node must be public original bytes')
        need(runtime.get('schema')=='STAGE05_PINNED_RUNTIME_V1' and runtime.get('roots')==C.ROOTS
             and set(runtime.get('files',{}))==set(C.ROOTS),'Actual scientific subset roots required')
        for role,files in runtime['files'].items():
            for name,expected in files.items():
                guard();relative(name);row=R.node_for_original(db,C.ROOTS[role]+'/'+name)
                need(sha(expected) and row['kind'] in ('regular','hardlink') and row['sha256']==expected,'Scientific subset is not fully restored')
        topology=T.current_topology(staging);parent=staging.parent.lstat();device=parent.st_dev
        source_devices={v[0] for v in db.execute('SELECT DISTINCT dev FROM originals')}
        need(stat.S_ISDIR(parent.st_mode) and not staging.parent.is_symlink() and device not in source_devices
             and f'{os.major(device)}:{os.minor(device)}'==topology['major_minor'],'Staging must use distinct admitted ext4 device')
        for ancestor in staging.parent.parents:
            need(stat.S_ISDIR(ancestor.lstat().st_mode) and not ancestor.is_symlink(),'Plain staging ancestors required')
        api=SafeLinux();parentfd=os.open(staging.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        need((os.fstat(parentfd).st_dev,os.fstat(parentfd).st_ino)==(parent.st_dev,parent.st_ino),'Staging parent changed')
        probe=api.opened(parentfd,'.',os.O_RDONLY|os.O_DIRECTORY);os.close(probe)
        guard();os.mkdir(staging.name,0o700,dir_fd=parentfd)
        rootfd=api.opened(parentfd,staging.name,os.O_RDONLY|os.O_DIRECTORY);root_identity=os.fstat(rootfd)
        need(root_identity.st_dev==device and root_identity.st_uid==0 and stat.S_IMODE(root_identity.st_mode)==0o700
             and not os.listdir(rootfd),'Owned NEW empty staging inode required')
        def opened_parent(name):
            guard();relative(name);parent,leaf=name.rsplit('/',1) if '/' in name else ('.',name)
            fd=api.opened(rootfd,parent,os.O_RDONLY|os.O_DIRECTORY)
            need(os.fstat(fd).st_dev==device,'Opened staging ancestor device differs');return fd,leaf
        def remember(name,info):
            need(info.st_dev==device,'Restored device escape');db.execute('INSERT INTO restored VALUES(?,?,?)',(name,info.st_dev,info.st_ino))
        def same(name,info):
            need(db.execute('SELECT dev,ino FROM restored WHERE name=?',(name,)).fetchone()==(info.st_dev,info.st_ino),
                 'Restored inode changed');need(info.st_dev==device,'Restored mount escape')
        for row in index['shards']:
            side=directory/(row['name']+'.sha256');need(side.resolve()==side and side.is_file() and not side.is_symlink()
                and side.stat().st_size<1024 and side.read_bytes()==(row['sha256']+'  '+row['name']+'\n').encode(),'Exact original LF sidecar required')
        parts=R.Parts(directory,index,guard);compressed=io.BufferedReader(parts,buffer_size=BLOCK)
        inflater=R.Inflate(compressed,index['uncompressed_tar_bytes'],guard);plain=io.BufferedReader(inflater,buffer_size=BLOCK)
        control_count=payload_count=0
        with tarfile.open(fileobj=plain,mode='r|') as archive:
            for item in archive:
                guard();relative(item.name);need(set(item.pax_headers)<={'mtime','path','linkpath'} and not item.sparse,'Unexpected PAX/sparse metadata')
                if control_count<5:
                    key=CONTROL_ORDER[control_count];name='controls/'+key+('.jsonl' if key=='manifest' else '.json')
                    need(item.name==name and item.isreg() and item.size<=MAX_CONTROL and not item.linkname
                         and (item.mode,item.uid,item.gid,item.mtime)==(0o644,0,0,0),'Ordered exact control member required')
                    h=hashlib.sha256();count=0
                    with archive.extractfile(item) as stream:
                        while data:=stream.read(BLOCK):guard();h.update(data);count+=len(data)
                    need(count==item.size and h.hexdigest()==index['control_sha256'][key],'Tar control SHA differs')
                    control_count+=1
                else:
                    next_row=db.execute('SELECT name,row_json FROM entries WHERE seen=0 ORDER BY name LIMIT 1').fetchone()
                    need(next_row and item.name==next_row[0],'Duplicate/conflicting/out-of-order/unexpected member')
                    row=strict_json(next_row[1]);tar_member(item,row,R);name=item.name[len('payload/'):]
                    fd,leaf=opened_parent(name)
                    try:
                        if row['kind']=='directory':
                            os.mkdir(leaf,0o700,dir_fd=fd);child=api.opened(fd,leaf,os.O_RDONLY|os.O_DIRECTORY)
                            try:remember(name,os.fstat(child))
                            finally:os.close(child)
                        elif row['kind']=='regular':
                            child=api.opened(fd,leaf,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600)
                            try:
                                h=hashlib.sha256();count=0
                                with archive.extractfile(item) as stream:
                                    while data:=stream.read(BLOCK):
                                        guard();h.update(data);count+=len(data);need(count<=row['bytes'],'Regular length grew')
                                        view=memoryview(data)
                                        while view:guard();written=os.write(child,view);need(written>0,'Short filesystem write');view=view[written:]
                                os.fsync(child);need(count==row['bytes'] and h.hexdigest()==row['sha256']
                                                     and os.fstat(child).st_size==count,'Copied complete regular SHA/size differs')
                                remember(name,os.fstat(child))
                            finally:os.close(child)
                        elif row['kind']=='symlink':
                            os.symlink(row['link_target'],leaf,dir_fd=fd);info=os.stat(leaf,dir_fd=fd,follow_symlinks=False)
                            need(stat.S_ISLNK(info.st_mode) and os.readlink(leaf,dir_fd=fd)==row['link_target'],'Exact new symlink required');remember(name,info)
                        else:
                            target=relative(row['link_target']);source=api.opened(rootfd,target,os.O_RDONLY)
                            try:
                                info=os.fstat(source);same(target,info);need(stat.S_ISREG(info.st_mode),'Only captured prior regular inode can be linked')
                                api.linked(source,fd,leaf);new=os.stat(leaf,dir_fd=fd,follow_symlinks=False)
                                need((new.st_dev,new.st_ino)==(info.st_dev,info.st_ino),'Exact new hardlink inode differs');remember(name,new)
                            finally:os.close(source)
                    finally:os.close(fd)
                    db.execute('UPDATE entries SET seen=1 WHERE name=?',(item.name,));payload_count+=1
                archive.members.clear()
            while data:=archive.fileobj.read(BLOCK):guard();need(not any(data),'Nonzero hidden tar tail')
        while data:=plain.read(BLOCK):guard();need(not any(data),'Nonzero trailing tar data')
        need(control_count==5 and payload_count==index['entry_count'] and inflater.finished
             and parts.number==len(index['shards']) and parts.total==index['compressed_bytes']
             and parts.whole.hexdigest()==index['compressed_stream_sha256'],'Exhaustive full gzip/shard/member proof required')
        # Metadata is applied after creating children/aliases. This prevents a
        # restored default ACL or restrictive directory mode affecting creation.
        for (text,) in db.execute('SELECT row_json FROM entries ORDER BY length(name) DESC,name DESC'):
            guard();row=strict_json(text);name=row['role']+('' if row['path']=='.' else '/'+row['path']);fd,leaf=opened_parent(name)
            try:
                info=os.stat(leaf,dir_fd=fd,follow_symlinks=False);same(name,info)
                if row['kind']=='symlink':
                    os.chown(leaf,row['uid'],row['gid'],dir_fd=fd,follow_symlinks=False)
                    alias='/proc/self/fd/'+str(fd)+'/'+leaf
                    existing=set(os.listxattr(alias,follow_symlinks=False));need(existing<=set(row['xattrs']),'Unexpected inherited symlink xattrs')
                    for key,value in row['xattrs'].items():guard();os.setxattr(alias,key,base64.b64decode(value,validate=True),follow_symlinks=False)
                    os.utime(leaf,ns=(row['mtime_ns'],row['mtime_ns']),dir_fd=fd,follow_symlinks=False)
                    need(os.readlink(leaf,dir_fd=fd)==row['link_target'],'Symlink target changed')
                elif row['kind']!='hardlink':
                    child=api.opened(fd,leaf,os.O_RDONLY|(os.O_DIRECTORY if row['kind']=='directory' else 0))
                    try:
                        same(name,os.fstat(child));os.fchown(child,row['uid'],row['gid']);os.fchmod(child,row['mode'])
                        need(set(os.listxattr(child))<=set(row['xattrs']),'Unexpected inherited xattrs')
                        for key,value in row['xattrs'].items():guard();os.setxattr(child,key,base64.b64decode(value,validate=True))
                        os.utime(child,ns=(row['mtime_ns'],row['mtime_ns']));os.fsync(child)
                    finally:os.close(child)
            finally:os.close(fd)
        # Each inode group shares one exact metadata record. The independent
        # cold checker performs separate full byte/metadata/link verification.
        need((staging.lstat().st_dev,staging.lstat().st_ino)==(root_identity.st_dev,root_identity.st_ino)
             and (os.fstat(rootfd).st_dev,os.fstat(rootfd).st_ino)==(root_identity.st_dev,root_identity.st_ino)
             and T.current_topology(staging)==topology,'Disposable root/mount topology changed')
        for key,path in verified_controls.items():exact_control(path,index['control_sha256'][key],guard)
        for name,expected in PINS.items():need(digest((W/name).read_bytes())==expected,'Helper source changed')
        record.update(state='NEW_LOGICAL_TREE_EXTRACTED_PENDING_INDEPENDENT_COLD_CHECK',entry_count=payload_count,
                      all_input_stream_and_control_hashes_verified=True,mount_topology=topology,
                      absolute_link_text_preserved_never_followed=True,cold_tree_validation='NOT_RUN',host_wipe_authority=False)
        return record
    except BaseException as error:
        record.update(error_kind=type(error).__name__,error_message=str(error));raise
    finally:
        final_errors=[]
        for stream in (plain,compressed,parts):
            if stream is not None:
                try:stream.close()
                except BaseException as error:final_errors.append(type(error).__name__+': stream close')
        for fd in (rootfd,parentfd):
            if fd is not None:
                try:os.close(fd)
                except BaseException as error:final_errors.append(type(error).__name__+': descriptor close')
        try:db.close()
        except BaseException as error:final_errors.append(type(error).__name__+': metadata DB close')
        if final_errors:record.update(state='FAILED_PARTIAL_PRESERVED',finalizer_errors=final_errors)
        with (evidence/'receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(record,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        if final_errors:raise RuntimeError('Extraction finalizer failed; partial tree remains unaccepted')


if __name__=='__main__':
    print(json.dumps(dict(state='PREPARATION_ONLY_NO_EXTRACTION_OR_DOWNLOAD_CLI',actual_fresh_remote_gate='PENDING',
                         actual_restore='NOT_RUN',original_prefix_runtime_execution='NOT_RUN',host_wipe_authority=False)))
