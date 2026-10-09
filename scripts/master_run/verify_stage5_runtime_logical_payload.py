"""Inactive independent full-payload verifier for future runtime shards.

No capture-producer import, network, extraction, runtime launch or standalone
verification CLI. Fresh remote identity/owned-download binding must be supplied
by a separately reviewed wrapper after the actual immutable index exists.
"""
from pathlib import Path, PurePosixPath
from decimal import Decimal
import base64
import hashlib
import io
import json
import os
import posixpath
import re
import sqlite3
import tarfile
import unicodedata
import zlib

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PREFIX='/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux'
ROOTS={'environment_dir':PREFIX+'/detector_env','models_dir':PREFIX+'/defense_models','padloc_db':PREFIX+'/padloc_db'}
LIMIT=448*1024**2
BLOCK=256*1024
MAX_CONTROL=64*1024**2


def require(value,message):
    if not value: raise ValueError(message)


def sha(value): return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None


def safe_relative(value):
    require(isinstance(value,str) and value and '\\' not in value and unicodedata.normalize('NFC',value)==value
            and not any(ord(c)<32 or ord(c)==127 for c in value),'Unsafe metadata path')
    p=PurePosixPath(value)
    require(not p.is_absolute() and str(p)==value and '..' not in p.parts,'Noncanonical metadata path')


def member_for(row):
    require(row.get('role') in ROOTS,'Unexpected runtime role');safe_relative(row['path'])
    return 'payload/'+row['role']+('' if row['path']=='.' else '/'+row['path'])


class Parts(io.RawIOBase):
    def __init__(self,directory,index,guard):
        self.directory,self.index,self.guard=directory,index,guard
        self.number=0;self.current=None;self.hash=None;self.size=0;self.total=0;self.whole=hashlib.sha256()
    def readable(self): return True
    def readinto(self,buffer):
        self.guard()
        if self.current is None:
            if self.number==len(self.index['shards']): return 0
            row=self.index['shards'][self.number];path=self.directory/row['name']
            require(not path.is_symlink() and path.is_file() and path.stat().st_size==row['bytes'],'Exact fresh shard file required')
            self.current=path.open('rb');self.before=os.fstat(self.current.fileno());self.hash=hashlib.sha256();self.size=0
        data=self.current.read(min(len(buffer),BLOCK))
        if data:
            buffer[:len(data)]=data;self.hash.update(data);self.whole.update(data);self.size+=len(data);self.total+=len(data)
            return len(data)
        row=self.index['shards'][self.number];after=os.fstat(self.current.fileno())
        require((self.before.st_dev,self.before.st_ino,self.before.st_size,self.before.st_mtime_ns)==
                (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                and self.size==row['bytes'] and self.hash.hexdigest()==row['sha256'],'Shard bytes/identity changed')
        self.current.close();self.current=None;self.number+=1
        return self.readinto(buffer)
    def close(self):
        if self.current: self.current.close();self.current=None
        super().close()


class Inflate(io.RawIOBase):
    """Exactly one gzip member, CRC verified by zlib, bounded decoded reads."""
    def __init__(self,source,bound,guard):
        self.source,self.bound,self.guard=source,bound,guard
        self.decoder=zlib.decompressobj(31);self.tail=b'';self.total=0;self.finished=False
    def readable(self): return True
    def readinto(self,buffer):
        self.guard()
        if self.finished:return 0
        amount=min(len(buffer),BLOCK)
        while True:
            if not self.tail:
                self.tail=self.source.read(BLOCK)
                require(self.tail or self.decoder.eof,'Truncated gzip stream')
            data=self.decoder.decompress(self.tail,amount);self.tail=self.decoder.unconsumed_tail
            self.total+=len(data);require(self.total<=self.bound,'Declared uncompressed byte bound exceeded')
            if self.decoder.eof:
                require(not self.decoder.unused_data and not self.tail and self.source.read(1)==b'',
                        'Extra gzip member/trailing compressed bytes')
                self.finished=True;require(self.total==self.bound,'Exact uncompressed byte count differs')
            if data:
                buffer[:len(data)]=data;return len(data)
            if self.finished:return 0


def store_manifest(db,path):
    prior='';count=0;roots=set();regular_bytes=0
    with path.open('r',encoding='utf-8',newline='') as stream:
        for line in stream:
            require(len(line.encode('utf-8'))<=1024**2 and line.endswith('\n'),'Bounded canonical JSONL line')
            row=json.loads(line);name=member_for(row);require(name>prior,'Ordered unique manifest paths');prior=name
            require(row['kind'] in {'regular','directory','symlink','hardlink'}
                    and all(type(row[k]) is int and row[k]>=0 for k in ['mode','uid','gid','mtime_ns','bytes'])
                    and row['mode']<=0o7777,'Exact supported type/POSIX metadata')
            require(isinstance(row['xattrs'],dict),'Complete xattr map required')
            for key,value in row['xattrs'].items():
                require(isinstance(key,str) and key and '\0' not in key,'Invalid xattr name');base64.b64decode(value,validate=True)
            if row['path']=='.': require(row['kind']=='directory','Plain root required');roots.add(row['role'])
            else:
                parent=name.rsplit('/',1)[0];found=db.execute('SELECT kind FROM entries WHERE name=?',(parent,)).fetchone()
                require(found and found[0]=='directory','Manifest parent absent or symlink')
            if row['kind'] in {'regular','hardlink'}: require(sha(row['sha256']),'Content SHA required')
            else: require(row['bytes']==0 and row['sha256'] is None,'Nonregular data forbidden')
            if row['kind']=='symlink':
                target=row['link_target'];require(isinstance(target,str) and target and '\\' not in target
                    and not any(ord(c)<32 or ord(c)==127 for c in target),'Unsafe symlink target')
                original=ROOTS[row['role']]+('' if row['path']=='.' else '/'+row['path'])
                target=posixpath.normpath(target if target.startswith('/') else posixpath.dirname(original)+'/'+target)
                require(any(target==root or target.startswith(root+'/') for root in ROOTS.values()),'External link target forbidden')
            if row['kind']=='hardlink':
                target='payload/'+row['link_target'];found=db.execute('SELECT row_json FROM entries WHERE name=?',(target,)).fetchone()
                require(found,'Hardlink target must precede alias');other=json.loads(found[0])
                require(other['kind']=='regular' and all(row[k]==other[k] for k in
                        ['mode','uid','gid','mtime_ns','bytes','sha256','xattrs','source_dev','source_ino','source_nlink','source_ctime_ns']),
                        'Hardlink source/byte/metadata graph differs')
            db.execute('INSERT INTO entries VALUES(?,?,?,0)',(name,row['kind'],json.dumps(row,sort_keys=True)))
            if row['kind']=='regular':regular_bytes+=row['bytes']
            count+=1;require(count<=500000,'Entry admission limit exceeded')
    require(roots==set(ROOTS),'All three runtime roots required');db.commit();return count,regular_bytes


def node_for_original(db,path):
    for _ in range(41):
        changed=False
        for role,root in ROOTS.items():
            if path==root or path.startswith(root+'/'):
                relative=path[len(root):].lstrip('/');pieces=relative.split('/') if relative else []
                for i in range(len(pieces)+1):
                    name='payload/'+role+('/'+'/'.join(pieces[:i]) if i else '')
                    found=db.execute('SELECT row_json FROM entries WHERE name=?',(name,)).fetchone()
                    if found:
                        row=json.loads(found[0])
                        if row['kind']=='symlink':
                            original=root+('/'+'/'.join(pieces[:i]) if i else '')
                            target=row['link_target'];target=target if target.startswith('/') else posixpath.dirname(original)+'/'+target
                            path=posixpath.normpath(target+('/'+'/'.join(pieces[i:]) if i<len(pieces) else ''))
                            changed=True;break
                if not changed:
                    require(found,'Dangling/unselected link dependency');return json.loads(found[0])
                break
        else:raise ValueError('Link chain escaped exact roots')
        if not changed:raise ValueError('Missing captured dependency')
    raise ValueError('Symlink cycle/depth exceeds40')


def verify_payload(index_raw,expected_index_sha,shards_directory,output,admission):
    """Verify all local shard bytes; fresh remote authenticity is a separate gate."""
    require(Path(__file__).resolve().parent==WORK and callable(admission),'Exact C source/admission required')
    require(len(index_raw)<5*1024**2 and hashlib.sha256(index_raw).hexdigest()==expected_index_sha,'Independent index pin differs')
    index=json.loads(index_raw)
    require(index.get('schema')=='STAGE05_RUNTIME_LOGICAL_ARCHIVE_INDEX_V1' and index.get('roots')==ROOTS
            and index.get('maximum_asset_bytes')==LIMIT and index.get('installed_build_equivalence')=='NOT_ESTABLISHED',
            'Exact reviewed pending-equivalence index required')
    names=[]
    require(isinstance(index['shards'],list) and 1<=len(index['shards'])<=64,'Bounded shard count')
    for number,row in enumerate(index['shards'],1):
        require(row['name']=='stage5-installed-runtime-01.part'+str(number).zfill(4)
                and type(row['bytes']) is int and 0<row['bytes']<=LIMIT and sha(row['sha256']), 'Ordered bounded shard index')
        require(number==len(index['shards']) or row['bytes']==LIMIT,'Only last shard may be short')
        names.append(row['name'])
    require(names and index['compressed_bytes']==sum(r['bytes'] for r in index['shards'])
            and sha(index['compressed_stream_sha256']) and type(index['uncompressed_tar_bytes']) is int
            and 0<index['uncompressed_tar_bytes']<=32*1024**3,'Exact declared stream sizes/SHA')
    directory=Path(shards_directory);output=Path(output)
    require(directory.is_relative_to(WORK) and directory.resolve()==directory and directory.is_dir()
            and output.parent==WORK and re.fullmatch(r'stage5_runtime_payload_readback_[A-Za-z0-9_]+',output.name)
            and not output.exists() and not output.is_symlink(),'Exact fresh C readback paths')
    for row in index['shards']:
        side=directory/(row['name']+'.sha256')
        require(not side.is_symlink() and side.stat().st_size<1024
                and side.read_bytes()==(row['sha256']+'  '+row['name']+'\n').encode('ascii'),'Original LF sidecar differs')
    expected_controls={key:('controls/'+key+('.jsonl' if key=='manifest' else '.json')) for key in ['cold_proof','manifest','notices','public_review','runtime']}
    require(set(index['control_sha256'])==set(expected_controls)
            and all(sha(h) for h in index['control_sha256'].values()),'Exact control pins')
    admission();output.mkdir();db=sqlite3.connect(output/'manifest.sqlite3')
    db.execute('CREATE TABLE entries(name TEXT PRIMARY KEY,kind TEXT,row_json TEXT,seen INTEGER)')
    parts=Parts(directory,index,admission);compressed=io.BufferedReader(parts,buffer_size=BLOCK)
    inflater=Inflate(compressed,index['uncompressed_tar_bytes'],admission);plain=io.BufferedReader(inflater,buffer_size=BLOCK)
    controls_seen=[];payload_count=0;manifest_count=None;manifest_regular_bytes=None
    try:
        with tarfile.open(fileobj=plain,mode='r|') as archive:
            for item in archive:
                admission();safe_relative(item.name)
                require(set(item.pax_headers)<={'mtime','path','linkpath'},'Unexpected PAX metadata')
                if len(controls_seen)<len(expected_controls):
                    key=list(expected_controls)[len(controls_seen)]
                    require(item.name==expected_controls[key] and item.isreg() and item.size<=MAX_CONTROL
                            and (item.mode,item.uid,item.gid,item.mtime)==(0o644,0,0,0),'Ordered regular control differs')
                    target=output/(key+('.jsonl' if key=='manifest' else '.json'));h=hashlib.sha256();size=0
                    with archive.extractfile(item) as source,target.open('xb') as sink:
                        while data:=source.read(BLOCK): admission();sink.write(data);h.update(data);size+=len(data)
                    require(size==item.size and h.hexdigest()==index['control_sha256'][key],'Original control full SHA differs')
                    controls_seen.append(key)
                    if key=='manifest':manifest_count,manifest_regular_bytes=store_manifest(db,target)
                else:
                    found=db.execute('SELECT row_json,seen FROM entries WHERE name=?',(item.name,)).fetchone()
                    require(found and found[1]==0,'Unexpected/duplicate tar payload');row=json.loads(found[0])
                    require((item.mode,item.uid,item.gid)==(row['mode'],row['uid'],row['gid'])
                            and Decimal(item.pax_headers.get('mtime',str(item.mtime)))*10**9==row['mtime_ns'],
                            'Exact POSIX mode/ownership/nanosecond mtime differs')
                    if row['kind']=='regular':
                        require(item.isreg() and item.size==row['bytes'] and not item.linkname,'Regular logical bytes differ')
                        h=hashlib.sha256();size=0
                        with archive.extractfile(item) as source:
                            while data:=source.read(BLOCK):admission();h.update(data);size+=len(data)
                        require(size==row['bytes'] and h.hexdigest()==row['sha256'],'Full installed file SHA differs')
                    elif row['kind']=='directory':require(item.isdir() and item.size==0 and not item.linkname,'Plain directory differs')
                    elif row['kind']=='symlink':require(item.issym() and item.size==0 and item.linkname==row['link_target'],'Exact symlink target differs')
                    else:
                        require(item.islnk() and item.size==0 and item.linkname=='payload/'+row['link_target'],'Exact hardlink target differs')
                        require(db.execute('SELECT seen FROM entries WHERE name=?',(item.linkname,)).fetchone()==(1,), 'Hardlink target was not verified first')
                    db.execute('UPDATE entries SET seen=1 WHERE name=?',(item.name,));payload_count+=1
                archive.members.clear()
            while data:=archive.fileobj.read(BLOCK):
                admission();require(not any(data),'Unexpected buffered data after tar end')
        while data:=plain.read(BLOCK):admission();require(not any(data),'Unexpected data after tar end')
        require(inflater.finished and parts.number==len(index['shards']) and parts.total==index['compressed_bytes']
                and parts.whole.hexdigest()==index['compressed_stream_sha256'],'Full gzip/shard/ordered stream SHA differs')
        require(manifest_count==payload_count==index['entry_count']
                and manifest_regular_bytes==index['regular_bytes']
                and db.execute('SELECT COUNT(*) FROM entries WHERE seen=0').fetchone()==(0,), 'Exhaustive payload coverage differs')
        for (text,) in db.execute("SELECT row_json FROM entries WHERE kind='symlink'"):
            row=json.loads(text);node_for_original(db,ROOTS[row['role']]+'/'+row['path'])
        runtime=json.loads((output/'runtime.json').read_text())
        require(runtime.get('schema')=='STAGE05_PINNED_RUNTIME_V1' and runtime.get('roots')==ROOTS
                and set(runtime.get('files',{}))==set(ROOTS),'Exact actual scientific runtime subset')
        scientific_count=0
        for role,files in runtime['files'].items():
            for relative,expected in files.items():
                safe_relative(relative);require(sha(expected),'Scientific SHA required')
                row=node_for_original(db,ROOTS[role]+'/'+relative)
                require(row['kind'] in {'regular','hardlink'} and row['sha256']==expected,
                        'Scientific runtime dependency excluded/omitted/changed')
                scientific_count+=1
        result=dict(state='PASS_LOCAL_FULL_RUNTIME_PAYLOAD_AND_POSIX_MANIFEST_FRESH_REMOTE_NOT_PROVEN',
                    index_sha256=expected_index_sha,shards=len(names),entry_count=payload_count,
                    all_regular_file_sha_verified=True,all_control_sha_verified=True,all_gzip_crc_verified=True,
                    scientific_runtime_subset_files_verified=scientific_count,complete_internal_symlink_graph_verified=True,
                    compressed_stream_sha256=index['compressed_stream_sha256'],
                    extraction=False,installed_build_equivalence='NOT_ESTABLISHED',cold_restore='NOT_RUN',cleanup_authority=False)
        return result
    finally:
        db.close();plain.close();compressed.close();parts.close()


if __name__=='__main__':
    print(json.dumps(dict(state='PREPARATION_ONLY_NO_STANDALONE_READBACK_CLI',actual_payload_verification='NOT_RUN',
                         fresh_remote_wrapper='PENDING_IMMUTABLE_INDEX_AND_SOURCE_REVIEW')))
