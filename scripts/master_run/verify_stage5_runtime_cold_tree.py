"""Inactive independent read-only comparison of a future disposable Linux restore.

Does not create/extract/install/mount/execute anything or touch original runtime.
Source inode/birth/ctime are provenance; exact internal hardlink equivalence is
checked against fresh restored inode groups. Invocation requires reviewed owner.
"""
from pathlib import Path
import base64
import hashlib
import json
import os
import re
import stat

WORK=Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
ROLES={'environment_dir','models_dir','padloc_db'}
BLOCK=256*1024


def require(ok,message):
    if not ok:raise ValueError(message)


def metadata(info,row):
    kind='directory' if stat.S_ISDIR(info.st_mode) else 'symlink' if stat.S_ISLNK(info.st_mode) else 'regular' if stat.S_ISREG(info.st_mode) else 'special'
    return kind==('regular' if row['kind']=='hardlink' else row['kind']) and (
        stat.S_IMODE(info.st_mode),info.st_uid,info.st_gid,info.st_mtime_ns)==(
        row['mode'],row['uid'],row['gid'],row['mtime_ns']) and (
        row['kind'] not in {'regular','hardlink'} or info.st_size==row['bytes'])


def mount_topology(raw,staging):
    """Pure metadata predicate: disposable ext4 only, no nested mount adoption."""
    require(isinstance(raw,bytes) and len(raw)<=1024**2,'Bounded mount topology required')
    staging=str(staging);mounts=[]
    for line in raw.decode('utf-8',errors='strict').splitlines():
        left,right=line.split(' - ',1);parts=left.split();after=right.split()
        point=re.sub(r'\\([0-7]{3})',lambda m:chr(int(m[1],8)),parts[4])
        require(not point.startswith(staging+'/'),'Nested mount under disposable restore is forbidden')
        if staging==point or staging.startswith(point.rstrip('/')+'/'):
            mounts.append((len(point),parts[0],parts[2],after[0]))
    require(mounts,'Disposable target mount not proven')
    deepest=max(item[0] for item in mounts);selected=[item for item in mounts if item[0]==deepest]
    require(len(selected)==1 and selected[0][3]=='ext4','Actual disposable target must be unambiguous ext4')
    return {'mount_id':selected[0][1],'major_minor':selected[0][2],
            'filesystem_type':'ext4','topology_sha256':hashlib.sha256(raw).hexdigest()}


def current_topology(staging):
    with Path('/proc/self/mountinfo').open('rb') as stream:
        return mount_topology(stream.read(1024**2+1),staging)


def validate_restored_tree(manifest_path,manifest_sha256,staging,admission):
    require(os.name=='posix' and Path(__file__).resolve().parent==WORK and callable(admission),
            'Reviewed Linux owner/callback/exact source required')
    manifest_path=Path(manifest_path);staging=Path(staging)
    require(manifest_path.parent.parent==WORK and manifest_path.name=='manifest.jsonl'
            and manifest_path.parent.name.startswith('stage5_runtime_payload_readback_')
            and manifest_path.resolve()==manifest_path and not manifest_path.is_symlink(),
            'Previously verified C manifest role required')
    require(staging.parent==Path('/var/tmp') and re.fullmatch(r'lab_rm_runtime_restore_[A-Za-z0-9_]+',staging.name)
            and staging.resolve()==staging and staging.is_dir() and not staging.is_symlink(),
            'Exact disposable restore target only')
    admission();topology=current_topology(staging)
    rows={};digest=hashlib.sha256();total=0
    with manifest_path.open('rb') as stream:
        before=os.fstat(stream.fileno())
        for line in stream:
            admission();total+=len(line);require(len(line)<=1024**2 and total<=64*1024**2,'Bounded full metadata ledger')
            digest.update(line);row=json.loads(line);require(row['role'] in ROLES,'Exact three restore roles')
            path=row['path'];require(isinstance(path,str) and path and '\\' not in path and not path.startswith('/')
                and '..' not in path.split('/') and not any(ord(c)<32 for c in path),'Safe manifest path')
            key=row['role']+('' if path=='.' else '/'+path);require(key not in rows,'Duplicate manifest path');rows[key]=row
        after=os.fstat(stream.fileno())
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
            (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) and digest.hexdigest()==manifest_sha256,
            'Verified manifest source/hash drift')
    require(all(role in rows for role in ROLES),'All three plain root directories required')
    staging_info=staging.lstat();device=staging_info.st_dev
    require(f'{os.major(device)}:{os.minor(device)}'==topology['major_minor']
            and device not in {row['source_dev'] for row in rows.values()},
            'Disposable restore must be distinct from all retained source devices')
    group_counts={}
    for row in rows.values():
        if row['kind'] in {'regular','hardlink'}:
            original=(row['source_dev'],row['source_ino']);group_counts[original]=group_counts.get(original,0)+1
    seen=set();original_to_new={};new_to_original={};regular_hashes=0;handles=[]
    rootfd=os.open(staging,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);handles.append(rootfd)
    def attrs(fd):return {name:base64.b64encode(os.getxattr(fd,name)).decode('ascii') for name in sorted(os.listxattr(fd))}
    def identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_nlink)
    def walk(parentfd,prefix):
        nonlocal regular_hashes
        with os.scandir(parentfd) as entries:
            for listing in entries:
                admission();name=listing.name;key=prefix+'/'+name if prefix else name
                require(key in rows and key not in seen,'Unexpected/unselected restored node: '+key)
                row=rows[key];initial=os.stat(name,dir_fd=parentfd,follow_symlinks=False)
                require(initial.st_dev==device and metadata(initial,row),'Restored node device/type/POSIX metadata differs: '+key)
                seen.add(key)
                if row['kind']=='symlink':
                    require(initial.st_nlink==1,'External/restored symlink hardlink alias not excluded')
                    require(os.readlink(name,dir_fd=parentfd)==row['link_target'],'Exact symlink text differs')
                    alias='/proc/self/fd/'+str(parentfd)+'/'+name
                    actual={n:base64.b64encode(os.getxattr(alias,n,follow_symlinks=False)).decode('ascii') for n in sorted(os.listxattr(alias,follow_symlinks=False))}
                    require(actual==row['xattrs'],'Symlink xattr/ACL differs')
                else:
                    fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|(os.O_DIRECTORY if row['kind']=='directory' else 0),dir_fd=parentfd)
                    try:
                        require(os.fstat(fd).st_dev==device and identity(os.fstat(fd))==identity(initial)
                                and attrs(fd)==row['xattrs'],'Opened restored identity/xattrs differ')
                        if row['kind']=='directory':walk(fd,key)
                        else:
                            h=hashlib.sha256();count=0
                            while data:=os.read(fd,BLOCK):admission();h.update(data);count+=len(data)
                            require(count==row['bytes'] and h.hexdigest()==row['sha256'],'Full restored regular bytes/SHA differ')
                            regular_hashes+=1
                            old=(row['source_dev'],row['source_ino']);new=(initial.st_dev,initial.st_ino)
                            require(initial.st_nlink==group_counts[old],'Unexpected restored hardlink outside scoped tree')
                            require(old not in original_to_new or original_to_new[old]==new,'Required internal hardlink lost')
                            require(new not in new_to_original or new_to_original[new]==old,'Unintended inode coalescence')
                            original_to_new[old]=new;new_to_original[new]=old
                        require(identity(os.fstat(fd))==identity(initial),'Restored descriptor metadata drift')
                    finally:os.close(fd)
                require(identity(os.stat(name,dir_fd=parentfd,follow_symlinks=False))==identity(initial),'Restored leaf changed during comparison')
    try:
        require(identity(os.fstat(rootfd))==identity(staging_info),'Opened disposable root identity differs')
        walk(rootfd,'');require(seen==set(rows),'Missing restored logical nodes')
        require(identity(os.fstat(rootfd))==identity(staging_info)
                and identity(staging.lstat())==identity(staging_info),'Disposable root changed during comparison')
        require(current_topology(staging)==topology,
                'Disposable mount topology changed during comparison')
    finally:
        for fd in handles:os.close(fd)
    final=manifest_path.stat();require((final.st_dev,final.st_ino,final.st_size,final.st_mtime_ns)==
                                      (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns),'Final manifest path drift')
    h=hashlib.sha256()
    with manifest_path.open('rb') as stream:
        while block:=stream.read(BLOCK):admission();h.update(block)
    require(h.hexdigest()==manifest_sha256,'Final manifest full SHA drift')
    return dict(state='PASS_EXACT_SCOPED_LOGICAL_TREE_BYTES_METADATA_LINKS_ONLY',entries=len(seen),
                full_regular_hashes=regular_hashes,manifest_sha256=manifest_sha256,
                source_inode_birth_ctime_recreation=False,original_block_image_equivalence=False,
                filesystem_type='ext4',external_restored_hardlink_aliases_excluded=True,
                nested_mounts_excluded=True,retained_source_device_distinct=True,mount_topology=topology,
                original_prefix_runtime_execution='NOT_RUN',installed_build_equivalence='NOT_ESTABLISHED',
                biological_acceptance=False,host_wipe_authority=False)


if __name__=='__main__':
    print(json.dumps(dict(state='PREPARATION_ONLY_NO_STANDALONE_RESTORE_CHECK_CLI',actual_cold_restore='NOT_RUN')))
