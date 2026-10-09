"""Inactive Linux capture function for reviewed Stage5 runtime logical recovery.

No executable build CLI is supplied. A reviewed existing owner must supply a
continuous admission callback and exact actual frozen inputs. No controller,
installer, mount command, extraction or remote publication is introduced.
Actual integration and capture are NOT_RUN.
"""
from pathlib import Path
from contextlib import ExitStack
import base64
import gzip
import hashlib
import io
import importlib.util
import json
import os
import re
import stat
import sys
import tarfile
import time

sys.dont_write_bytecode=True
CONTRACT = Path(__file__).resolve().with_name('stage5_runtime_recovery_contract.py')
CONTRACT_SHA = 'daf48ea1c8cc96312519b1ab22f2d41216494773e5e345e3e5e0417139588bb6'
if CONTRACT.is_symlink() or hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=CONTRACT_SHA:
    raise ValueError('Exact reviewed recovery contract required before import')
_spec=importlib.util.spec_from_file_location('_reviewed_runtime_recovery_contract',CONTRACT)
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
if hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=CONTRACT_SHA:
    raise ValueError('Recovery contract changed during import')

LINUX_WORK = Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
MAX_METADATA_BYTES = 64 * 1024**2


def exact_bytes(path, expected, limit=MAX_METADATA_BYTES):
    path = Path(path)
    C.require(path.is_relative_to(LINUX_WORK) and path.resolve()==path
              and not path.is_symlink() and path.is_file() and path.stat().st_size <= limit,
              'Bounded regular original control required')
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    C.require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
              == (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
              and len(raw) <= limit and C.digest(raw) == expected, 'Original control drift/SHA')
    return raw


def observed_matches(info, row):
    kind = 'directory' if stat.S_ISDIR(info.st_mode) else 'symlink' if stat.S_ISLNK(info.st_mode) else 'regular' if stat.S_ISREG(info.st_mode) else 'special'
    return kind == ('regular' if row['kind'] == 'hardlink' else row['kind']) and all([
        info.st_dev == row['source_dev'], info.st_ino == row['source_ino'],
        info.st_nlink == row['source_nlink'], info.st_ctime_ns == row['source_ctime_ns'],
        info.st_mtime_ns == row['mtime_ns'], stat.S_IMODE(info.st_mode) == row['mode'],
        info.st_uid == row['uid'], info.st_gid == row['gid'],
        row['kind'] not in {'regular','hardlink'} or info.st_size == row['bytes']])


def fd_xattrs(fd):
    return {name:base64.b64encode(os.getxattr(fd,name)).decode('ascii') for name in sorted(os.listxattr(fd))}


def check_ro_mount(proof):
    """Current Linux mount metadata check; backing-writer closure is owner's proof."""
    matches, aliases = [], []
    def unescape(value):
        return re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1],8)),value)
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left,right=line.split(' - ',1); parts=left.split(); after=right.split()
        mountpoint=unescape(parts[4]); device=parts[2]
        if device == proof['major_minor']:
            aliases.append(dict(mountpoint=mountpoint,options=parts[5].split(','),super_options=after[2].split(',')))
        if any(mountpoint==root or mountpoint.startswith(root+'/') for root in C.ROOTS.values()):
            C.require(device==proof['major_minor'] and 'ro' in parts[5].split(',')
                      and 'rw' not in after[2].split(','),'Nested runtime mount escapes frozen backing')
        if mountpoint == C.PREFIX:
            matches.append((parts,after))
    C.require(len(matches)==1 and matches[0][0][0]==str(proof['mount_id'])
              and matches[0][0][2]==proof['major_minor'] and matches[0][1][0]=='ext4'
              and 'ro' in matches[0][0][5].split(',')
              and all('rw' not in a['options'] and 'rw' not in a['super_options'] for a in aliases),
              'Exact frozen ext4 mount/current aliases differ')


class Shards:
    def __init__(self, output, guard):
        self.output,self.guard=output,guard
        self.stream=None;self.current=None;self.records=[];self.total=0;self.whole=hashlib.sha256()
    def writable(self): return True
    def tell(self): return self.total
    def flush(self):
        if self.stream: self.stream.flush()
    def _close(self):
        if self.stream:
            self.stream.flush();os.fsync(self.stream.fileno());self.stream.close()
            self.current['sha256']=self.current.pop('hash').hexdigest()
            self.records.append(self.current);self.stream=None
    def write(self, data):
        view=memoryview(data)
        while view:
            self.guard()
            if self.stream is None:
                name='stage5-installed-runtime-01.part'+str(len(self.records)+1).zfill(4)
                self.stream=(self.output/name).open('xb')
                self.current=dict(name=name,bytes=0,hash=hashlib.sha256())
            count=min(len(view),C.SHARD_LIMIT-self.current['bytes'],C.CHUNK_BYTES)
            block=view[:count];self.stream.write(block);self.current['hash'].update(block)
            self.whole.update(block);self.total+=count;self.current['bytes']+=count;view=view[count:]
            if self.current['bytes']==C.SHARD_LIMIT: self._close()
        return len(data)
    def close(self): self._close()


class ContentReader:
    def __init__(self, fd, row, guard, public_codes):
        self.stream=os.fdopen(fd,'rb',closefd=False);self.row=row;self.guard=guard
        self.hash=hashlib.sha256();self.count=0;self.tail=b'';self.public_codes=set(public_codes)
    def read(self, amount):
        self.guard();data=self.stream.read(min(amount,C.CHUNK_BYTES));self.count+=len(data);self.hash.update(data)
        codes=C.scan_secret_blocks([self.tail+data] if len(self.tail)+len(data)<=C.CHUNK_BYTES else [self.tail,data])
        C.require(set(codes)<=self.public_codes,'New private/ambiguous byte-pattern reason; preserve partial')
        self.tail=(self.tail+data)[-8192:]
        return data
    def finish(self, fd):
        C.require(self.count==self.row['bytes'] and self.hash.hexdigest()==self.row['sha256']
                  and observed_matches(os.fstat(fd),self.row),'Original regular content/metadata drift')


class PlainCounter:
    def __init__(self, target): self.target=target;self.bytes=0
    def write(self,data): self.bytes+=len(data);return self.target.write(data)


def metadata_reason_codes(row):
    """Screen exact pathname/link/xattr metadata bytes; return codes, never matches."""
    values=[row['role']+'/'+row['path']]
    if row['kind']=='symlink': values.append(row['link_target'])
    values.extend(row['xattrs'])
    blocks=[]
    for value in values:
        raw=value.encode('utf-8',errors='strict')
        blocks.extend(raw[i:i+C.CHUNK_BYTES] for i in range(0,len(raw),C.CHUNK_BYTES))
    codes=set(C.scan_secret_blocks(blocks))
    for value in row['xattrs'].values():
        raw=base64.b64decode(value,validate=True)
        codes.update(C.scan_secret_blocks(raw[i:i+C.CHUNK_BYTES] for i in range(0,len(raw),C.CHUNK_BYTES)))
    return sorted(codes)


def canonicalize_hardlinks(rows,holds):
    """Choose the first final canonical path per inode, independent of DFS order."""
    rows.sort(key=lambda r:r['role']+'/'+r['path']);groups={}
    for row in rows:
        if row['kind'] in {'regular','hardlink'}:
            groups.setdefault((row['source_dev'],row['source_ino']),[]).append(row)
    for group in groups.values():
        first=group[0];target=first['role']+'/'+first['path'];codes=set()
        for row in group:
            C.require(all(row[k]==first[k] for k in ['mode','uid','gid','mtime_ns','bytes','sha256',
                         'xattrs','source_dev','source_ino','source_nlink','source_ctime_ns']),
                      'Same original inode has inconsistent bytes/metadata')
            codes.update(holds.get(row['role']+'/'+row['path'],[]))
        for index,row in enumerate(group):
            row['kind']='regular' if index==0 else 'hardlink'
            row['link_target']=None if index==0 else target
            if codes:holds[row['role']+'/'+row['path']]=sorted(codes)
    return rows


def inventory_frozen_roots(runtime, proof, admission):
    """Future full no-follow inventory; returned raw candidate is PRIVATE pending review.

    No output file or archive is written. All regular content and all xattrs are
    read only during a separately admitted future call. This function has not run.
    """
    C.require(os.name=='posix' and Path(__file__).resolve().parent==LINUX_WORK and callable(admission),
              'Reviewed Linux owner admission required for full inventory')
    C.require(proof.get('schema')=='STAGE05_RUNTIME_COLD_CAPTURE_PROOF_V1'
              and proof.get('original_workflow_lock_held') is True
              and proof.get('all_relevant_native_jobs_closed') is True
              and proof.get('backing_image_writer_exclusion_proven') is True,'Actual exclusive frozen inventory proof required')
    admission();check_ro_mount(proof);rows=[];holds={};inodes={};start=time.monotonic()
    def guard():
        C.require(time.monotonic()-start<=1800,'Finite full inventory deadline exceeded');admission()
    def visit(parent,name,role,relative):
        guard();info=os.stat(name,dir_fd=parent,follow_symlinks=False)
        path=Path(C.ROOTS[role]) if relative=='.' else Path(C.ROOTS[role])/relative
        kind='directory' if stat.S_ISDIR(info.st_mode) else 'symlink' if stat.S_ISLNK(info.st_mode) else 'regular' if stat.S_ISREG(info.st_mode) else 'special'
        C.require(kind!='special','Unsupported special runtime node must remain held')
        row=dict(role=role,path=relative,kind=kind,mode=stat.S_IMODE(info.st_mode),uid=info.st_uid,gid=info.st_gid,
                 mtime_ns=info.st_mtime_ns,bytes=0,sha256=None,link_target=None,xattrs={},source_dev=info.st_dev,
                 source_ino=info.st_ino,source_nlink=info.st_nlink,source_ctime_ns=info.st_ctime_ns)
        key=role+'/'+relative;reason=C.private_path_reason(relative)
        if reason:holds.setdefault(key,[]).append(reason)
        if row['mode']&0o7000:holds.setdefault(key,[]).append('PRIVILEGE_OR_SPECIAL_MODE_REQUIRES_REVIEW')
        if kind=='symlink':
            row['link_target']=os.readlink(name,dir_fd=parent)
            alias='/proc/self/fd/'+str(parent)+'/'+name
            row['xattrs']={n:base64.b64encode(os.getxattr(alias,n,follow_symlinks=False)).decode('ascii') for n in sorted(os.listxattr(alias,follow_symlinks=False))}
        else:
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|(os.O_DIRECTORY if kind=='directory' else 0),dir_fd=parent)
            try:
                C.require(observed_matches(os.fstat(fd),{**row,'bytes':info.st_size if kind=='regular' else 0}),'Inventory opened identity differs')
                row['xattrs']=fd_xattrs(fd)
                if kind=='directory':
                    rows.append(row)
                    with os.scandir(fd) as entries:names=sorted(e.name for e in entries)
                    for child in names:visit(fd,child,role,child if relative=='.' else relative+'/'+child)
                else:
                    row['bytes']=info.st_size;inode=(info.st_dev,info.st_ino)
                    if inode in inodes:
                        prior=inodes[inode];row.update(kind='hardlink',link_target=prior['role']+'/'+prior['path'],sha256=prior['sha256'])
                    else:
                        h=hashlib.sha256();tail=b'';codes=set();count=0
                        while block:=os.read(fd,C.CHUNK_BYTES):
                            guard();h.update(block);count+=len(block);codes.update(C.scan_secret_blocks([tail,block]));tail=(tail+block)[-8192:]
                        C.require(count==info.st_size,'Inventory regular length drift')
                        row['sha256']=h.hexdigest();inodes[inode]=row
                        if codes:holds.setdefault(key,[]).extend(sorted(codes))
                    rows.append(row)
                C.require(observed_matches(os.fstat(fd),row),'Inventory source changed during read')
            finally:os.close(fd)
        if kind=='symlink':rows.append(row)
        codes=metadata_reason_codes(row)
        if codes:holds.setdefault(key,[]).extend(codes)
        C.require(observed_matches(os.stat(name,dir_fd=parent,follow_symlinks=False),row),'Final inventory leaf drift')
        C.require(len(rows)<=500000,'Inventory entry admission limit exceeded')
    for role,root in sorted(C.ROOTS.items()):
        fd=os.open(str(Path(root).parent),os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:visit(fd,Path(root).name,role,'.')
        finally:os.close(fd)
    canonicalize_hardlinks(rows,holds);C.validate_manifest(rows,runtime);check_ro_mount(proof)
    return dict(state='PRIVATE_FULL_INVENTORY_CANDIDATE_REQUIRES_WHOLE_FILE_PUBLIC_REVIEW',entries=rows,
                hold_reason_codes=holds,public_scope_accepted=False,actual_archive='NOT_RUN')


def capture(inputs, control_paths, output, admission):
    """Serial full logical capture, callable only by a separately reviewed owner.

    control_paths maps manifest/runtime/public_review/cold_proof/notices to paths.
    admission MUST enforce current host physical+commit1536MiB reserve, finite
    owner deadline and owned lifecycle. This function neither invents nor bypasses
    that Windows owner proof. It cannot be invoked by this file as a standalone CLI.
    """
    C.require(os.name=='posix' and Path('/proc/self/mountinfo').is_file() and callable(admission),
              'Existing admitted Linux owner callback required')
    C.capture_gate(inputs)
    C.require(Path(__file__).resolve().parent==LINUX_WORK,'Exact reviewed C-mounted source required')
    output=Path(output)
    C.require(output.parent==LINUX_WORK and re.fullmatch(r'stage5_runtime_capture_[A-Za-z0-9_]+',output.name)
              and not output.exists() and not output.is_symlink(),'Fresh direct C export namespace required')
    expected={'manifest':inputs['complete_inventory_sha256'],'runtime':inputs['actual_runtime_manifest_sha256'],
              'public_review':inputs['whole_file_public_review_sha256'],
              'cold_proof':inputs['cold_exclusive_capture_receipt_sha256'],
              'notices':inputs['license_source_notice_review_sha256']}
    C.require(set(control_paths)==set(expected),'Exact capture control roles')
    raw={key:exact_bytes(control_paths[key],value) for key,value in expected.items()}
    rows=[json.loads(line) for line in raw['manifest'].decode('utf-8').splitlines()]
    runtime,review,proof,notices=(json.loads(raw[k]) for k in ['runtime','public_review','cold_proof','notices'])
    C.validate_manifest(rows,runtime)
    C.require(review.get('schema')=='STAGE05_RUNTIME_PUBLIC_SCOPE_REVIEW_V1'
              and review.get('inventory_sha256')==expected['manifest'] and review.get('whole_file_review_executed') is True,
              'Actual full-byte public scope review required')
    decisions=review.get('entries',{})
    keys={r['role']+'/'+r['path'] for r in rows}
    C.require(set(decisions)==keys and all(v.get('decision')=='PUBLIC_ORIGINAL_BYTES' for v in decisions.values()),
              'Every captured node needs exact public review; no secret/private adoption')
    for row in rows:
        C.require(set(metadata_reason_codes(row)) <= set(decisions[row['role']+'/'+row['path']].get(
                      'reviewed_false_positive_reason_codes',[])),
                  'Unresolved private/ambiguous metadata byte-pattern reason')
    C.require(not any(C.private_path_reason(r['path']) for r in rows),
              'Private/ambiguous path remains whole-file held, not public payload')
    C.require(notices.get('scope_reviewed') is True and notices.get('inventory_sha256')==expected['manifest'],
              'Actual original notice/source scope review required')
    C.require(proof.get('schema')=='STAGE05_RUNTIME_COLD_CAPTURE_PROOF_V1'
              and proof.get('original_workflow_lock_held') is True
              and proof.get('all_relevant_native_jobs_closed') is True
              and proof.get('backing_image_writer_exclusion_proven') is True,
              'Actual root-owned cold/exclusive capture proof required')
    start=time.monotonic()
    def guard():
        C.require(time.monotonic()-start<=1800,'Finite capture deadline exceeded')
        admission()
    guard();check_ro_mount(proof);output.mkdir()
    source_sha=C.digest(Path(__file__).read_bytes())
    C.require(source_sha==inputs['published_capture_source_sha256'],'Published capture source changed')
    table={C.absolute(r):r for r in rows};root_handles={};sink=None
    try:
        with ExitStack() as stack:
            for role,path in C.ROOTS.items():
                fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);stack.callback(os.close,fd)
                C.require(observed_matches(os.fstat(fd),table[path]),'Root original identity changed')
                root_handles[role]=fd
            def exact_coverage():
                seen=set()
                def visit(parent,role,relative):
                    key=C.ROOTS[role]+('/'+relative if relative else '')
                    C.require(key in table and observed_matches(os.fstat(parent),table[key]),'Current source directory identity differs')
                    seen.add(key)
                    with os.scandir(parent) as entries:
                        for item in entries:
                            guard();child=relative+'/'+item.name if relative else item.name
                            name=C.ROOTS[role]+'/'+child
                            C.require(name in table,'Unknown source node outside reviewed complete inventory')
                            row=table[name];info=os.stat(item.name,dir_fd=parent,follow_symlinks=False)
                            C.require(observed_matches(info,row),'Current source node metadata differs')
                            seen.add(name)
                            if row['kind']=='directory':
                                fd=os.open(item.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
                                try:visit(fd,role,child)
                                finally:os.close(fd)
                for role,fd in root_handles.items():visit(fd,role,'')
                C.require(seen==set(table),'Complete source membership differs')
            exact_coverage()
            def opened(row, flags):
                current=os.dup(root_handles[row['role']]);parents=[]
                try:
                    parts=[] if row['path']=='.' else row['path'].split('/')
                    for i,part in enumerate(parts[:-1]):
                        fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=current)
                        parents.append(current);current=fd
                        C.require(observed_matches(os.fstat(fd),table[C.ROOTS[row['role']]+'/'+ '/'.join(parts[:i+1])]),'Ancestor identity changed')
                    if not parts: return current
                    fd=os.open(parts[-1],flags|os.O_NOFOLLOW,dir_fd=current)
                    os.close(current);current=None
                    return fd
                finally:
                    if current is not None and row['path']!='.': os.close(current)
                    for fd in parents: os.close(fd)
            sink=Shards(output,guard)
            with gzip.GzipFile(filename='',mode='wb',compresslevel=1,fileobj=sink,mtime=0) as gz:
                plain=PlainCounter(gz)
                with tarfile.open(fileobj=plain,mode='w|',format=tarfile.PAX_FORMAT) as archive:
                    for name,data in sorted(raw.items()):
                        item=tarfile.TarInfo('controls/'+name+('.jsonl' if name=='manifest' else '.json'))
                        item.size=len(data);item.mode=0o644;item.mtime=0
                        archive.addfile(item,io.BytesIO(data))
                    for row in rows:
                        guard();path=Path(C.absolute(row));info=path.lstat()
                        C.require(observed_matches(info,row),'Current source identity/type changed')
                        item=tarfile.TarInfo('payload/'+row['role']+('' if row['path']=='.' else '/'+row['path']))
                        item.mode=row['mode'];item.uid=row['uid'];item.gid=row['gid'];item.mtime=row['mtime_ns']//10**9
                        item.pax_headers={'mtime':str(row['mtime_ns']//10**9)+'.'+str(row['mtime_ns']%10**9).zfill(9)}
                        if row['kind']=='symlink':
                            C.require(os.readlink(path)==row['link_target'],'Symlink target drift')
                            attrs={n:base64.b64encode(os.getxattr(path,n,follow_symlinks=False)).decode('ascii') for n in sorted(os.listxattr(path,follow_symlinks=False))}
                            C.require(attrs==row['xattrs'],'Symlink xattr drift')
                            item.type=tarfile.SYMTYPE;item.linkname=row['link_target'];archive.addfile(item)
                        else:
                            fd=opened(row,os.O_RDONLY|(os.O_DIRECTORY if row['kind']=='directory' else 0))
                            try:
                                C.require(observed_matches(os.fstat(fd),row) and fd_xattrs(fd)==row['xattrs'],'Opened source/xattr drift')
                                if row['kind']=='directory': item.type=tarfile.DIRTYPE;archive.addfile(item)
                                elif row['kind']=='hardlink':
                                    item.type=tarfile.LNKTYPE;item.linkname='payload/'+row['link_target'];archive.addfile(item)
                                else:
                                    item.size=row['bytes'];reader=ContentReader(fd,row,guard,decisions[row['role']+'/'+row['path']].get('reviewed_false_positive_reason_codes',[]))
                                    archive.addfile(item,reader);reader.finish(fd)
                            finally: os.close(fd)
                        C.require(observed_matches(path.lstat(),row),'Source final identity changed')
            sink.close();guard();check_ro_mount(proof)
            for row in rows: C.require(observed_matches(Path(C.absolute(row)).lstat(),row),'Final complete source metadata drift')
            exact_coverage()
        for key,value in expected.items(): exact_bytes(control_paths[key],value)
        C.require(C.digest(Path(__file__).read_bytes())==source_sha,'Capture source changed')
        index=dict(schema='STAGE05_RUNTIME_LOGICAL_ARCHIVE_INDEX_V1',state='LOCAL_CAPTURE_PENDING_INDEPENDENT_FULL_PAYLOAD_READBACK',
                   source_sha256=source_sha,roots=C.ROOTS,shards=sink.records,compressed_bytes=sink.total,
                   compressed_stream_sha256=sink.whole.hexdigest(),maximum_asset_bytes=C.SHARD_LIMIT,
                   uncompressed_tar_bytes=plain.bytes,
                   control_sha256=expected,entry_count=len(rows),regular_bytes=sum(r['bytes'] for r in rows if r['kind']=='regular'),
                   installed_build_equivalence='NOT_ESTABLISHED',cold_restore='NOT_RUN',cleanup_authority=False)
        with (output/'index.json').open('x',encoding='utf-8',newline='\n') as stream: json.dump(index,stream,indent=2,sort_keys=True);stream.write('\n')
        for row in sink.records:
            with (output/(row['name']+'.sha256')).open('x',encoding='ascii',newline='\n') as stream: stream.write(row['sha256']+'  '+row['name']+'\n')
        return index
    except BaseException:
        if sink: sink.close()
        raise


if __name__=='__main__':
    print(json.dumps(dict(state='PREPARATION_ONLY_NO_STANDALONE_CAPTURE_CLI',actual_capture='NOT_RUN',
                         integration='REQUIRES_REVIEWED_EXISTING_OWNER_ADMISSION_CALLBACK')))
