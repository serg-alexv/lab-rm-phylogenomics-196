"""Independent raw ZIP/NEW-tree recovery predicates; no producer import/CLI.

Callers supply actual outer/complete pins and a fresh resource/deadline check.
No download, native process, eviction or scientific acceptance occurs here.
"""
from pathlib import Path, PurePosixPath
import base64, hashlib, json, os, re, stat, zipfile

MAX_ASSET=448*1024**2
MAX_FILES=100000
MAX_LOGICAL=16*1024**3
MAX_MANIFEST=128*1024**2
CHUNK=1024**2
SCOPE='ONE_CLOSED_GENOME_RAW_RECOVERY_ONLY'
SOURCE_PINS='a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84'
PANEL_SHA='85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None


def relative(value,root=False):
    require(isinstance(value,str) and value and '\\' not in value and ':' not in value
            and not any(ord(c)<32 or ord(c)==127 for c in value),'Unsafe raw recovery path')
    pure=PurePosixPath(value)
    require(not pure.is_absolute() and pure.as_posix()==value and '..' not in pure.parts
            and (root or value!='.'),'Noncanonical raw recovery path')
    return pure


def hash_stream(stream,check,limit):
    digest=hashlib.sha256();count=0
    while block:=stream.read(CHUNK):
        check();count+=len(block);require(count<=limit,'Raw recovery expanded byte bound exceeded');digest.update(block)
    return count,digest.hexdigest()


def member_bytes(archive,name,limit,check):
    info=archive.getinfo(name);require(info.file_size<=limit,'Recovery metadata cap exceeded')
    chunks=[];count=0
    with archive.open(info) as source:
        while block:=source.read(CHUNK):
            check();count+=len(block);require(count<=limit,'Expanded recovery metadata cap exceeded');chunks.append(block)
    return b''.join(chunks)


def decoded_metadata(value):
    require(type(value.get('bytes')) is int and 0<=value['bytes']<=8*1024**2 and sha(value.get('sha256')),
            'Original recovery metadata pin invalid')
    raw=base64.b64decode(value['base64_original_bytes'],validate=True)
    require(len(raw)==value['bytes'] and hashlib.sha256(raw).hexdigest()==value['sha256'],'Original metadata bytes/SHA differ')
    return raw


def verify_archive(path,expected_sha,complete_sha,accession,check=lambda:None):
    """Full actual outer SHA, every member CRC/SHA and externally bound complete.

    Limits bound bytes/counts, not a measured RSS guarantee. The caller must
    admit/monitor this process and owns any storage/lock/remote provenance proof.
    """
    path=Path(path);require(sha(expected_sha) and sha(complete_sha),'External immutable raw archive/complete SHA required')
    before=path.stat();require(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_size<=MAX_ASSET,
                               'Bounded regular raw archive required')
    with path.open('rb') as source:
        count,actual=hash_stream(source,check,MAX_ASSET)
    require(count==before.st_size and actual==expected_sha,'Actual raw archive outer SHA differs')
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist();require(len(names)==len(set(names)) and len(names)<=MAX_FILES+2,'Duplicate/oversized raw archive')
        manifest_bytes=member_bytes(archive,'_recovery/manifest.json',MAX_MANIFEST,check)
        manifest=json.loads(manifest_bytes)
        require(manifest['schema']=='STAGE05_CLOSED_GENOME_RAW_RECOVERY_MANIFEST_V1' and manifest['scope']==SCOPE
                and manifest['scientific_acceptance']=='NO_NEW_SCIENTIFIC_ACCEPTANCE' and manifest['eviction_authorized'] is False
                and manifest['complete_sha256']==complete_sha,'Raw archive manifest scope/complete differs')
        files=manifest['files'];dirs=manifest['directories_to_restore'];locks=manifest['omitted_empty_lock_files']
        require(isinstance(files,dict) and 0<len(files)<=MAX_FILES and isinstance(dirs,dict) and '.' in dirs
                and isinstance(locks,list) and len(locks)==len(set(locks)),'Raw path inventories invalid')
        require(set(names)=={'genome/'+n for n in files}|{'_recovery/manifest.json','SHA256SUMS.txt'},'Exact full raw member set differs')
        total=0
        for name,pin in files.items():
            pure=relative(name);require(pure.parent.as_posix() in dirs and name not in dirs and name not in locks,'Missing/overlapping raw parent')
            require(type(pin['bytes']) is int and pin['bytes']>=0 and sha(pin['sha256'])
                    and type(pin['mode']) is int and 0<=pin['mode']<=0o7777,'Raw byte/SHA/mode pin invalid')
            identity=pin['identity'];require(isinstance(identity,list) and len(identity)==4
                    and all(type(x) is int and x>=0 for x in identity) and identity[1]>0 and identity[2]==pin['bytes'],
                    'Raw original file identity invalid')
            total+=pin['bytes'];require(total<=MAX_LOGICAL,'Raw logical-byte cap exceeded')
        for name,value in dirs.items():
            pure=relative(name,True);require(name=='.' or pure.parent.as_posix() in dirs,'Missing raw directory parent')
            require(type(value['mode']) is int and 0<=value['mode']<=0o7777,'Raw directory mode invalid')
        for name in locks:
            pure=relative(name);require(pure.name in {'.guard','.runner.guard'} and pure.parent.as_posix() in dirs
                                       and name not in files and name not in dirs,'Omitted guard metadata invalid')
        require(manifest['raw_files']==len(files) and manifest['raw_logical_bytes']==total,'Raw count/byte summary differs')
        complete_bytes=member_bytes(archive,'genome/complete.json',8*1024**2,check)
        require(hashlib.sha256(complete_bytes).hexdigest()==complete_sha,'Externally pinned original complete differs')
        complete=json.loads(complete_bytes);identity=complete['scientific_identity']
        require(complete['schema']=='STAGE05_ATOMIC_GENOME_COMPLETE_V1' and complete['state']=='COMPLETE_VALIDATED'
                and identity['schema']=='STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2'
                and complete['accession']==identity['accession']==accession
                and hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()==complete['scientific_identity_sha256']
                and json.loads(member_bytes(archive,'genome/scientific_identity.json',8*1024**2,check))==identity,
                'Closed original V2 scientific identity differs')
        require(complete['files'] and all(n in files and files[n]['sha256']==h for n,h in complete['files'].items()),
                'Selected complete native payload omitted/changed')
        metadata=manifest['provenance']['actual_metadata_files']
        source=decoded_metadata(metadata['accepted_source_pins.json']);panel=decoded_metadata(metadata['approved_accessions.txt'])
        runtime=decoded_metadata(metadata['runtime_manifest.json'])
        require(hashlib.sha256(source).hexdigest()==SOURCE_PINS and hashlib.sha256(panel).hexdigest()==PANEL_SHA
                and accession in panel.decode().split() and identity['source_acceptance']['source_pins_sha256']==SOURCE_PINS
                and hashlib.sha256(runtime).hexdigest()==identity['runtime_manifest_sha256'],'Pinned panel/source/runtime recovery bytes differ')
        for value in metadata.values():decoded_metadata(value)
        provenance=manifest['provenance'];owner_raw=decoded_metadata(metadata['closed_owner_proof.json'])
        owner=json.loads(owner_raw);config_raw=decoded_metadata(metadata['config.json'])
        require(hashlib.sha256(owner_raw).hexdigest()==provenance['closed_owner_proof_sha256']
                and owner==provenance['closed_owner_proof'] and owner['schema']=='STAGE05_CLOSED_GENOME_ARCHIVE_OWNER_SOURCE_V1'
                and owner['accession']==accession and owner['complete_sha256']==complete_sha
                and owner['config_sha256']==hashlib.sha256(config_raw).hexdigest(),'Original closed-owner/config proof bytes differ')
        owner_files=owner['original_owner_files'];required_owner_files={'result.json','owner.json','progress.json',
            'lock_released.json','owner_lease.json',accession+'.launch.json',accession+'.exit.json',
            accession+'.stdout.txt',accession+'.stderr.txt'}
        require(set(owner_files)==required_owner_files and sum(v['bytes'] for v in owner_files.values())<=16*1024**2,
                'Exact previous owner receipt/log set differs')
        original_owner={n:decoded_metadata(v) for n,v in owner_files.items()}
        result=json.loads(original_owner['result.json']);launch=json.loads(original_owner[accession+'.launch.json'])
        exit_receipt=json.loads(original_owner[accession+'.exit.json'])
        status=json.loads(member_bytes(archive,'genome/status.json',8*1024**2,check))
        require(result['state']=='COMPLETE_VALIDATED' and result['scope']=='ONE_APPROVED_GENOME'
                and result['selected_accessions']==[accession] and result['genome_results']==[exit_receipt]
                and result['config_sha256']==owner['config_sha256'] and exit_receipt['status_sha256']==owner['status_sha256']
                and files['status.json']['sha256']==owner['status_sha256']
                and status['owner_nonce']==launch['owner_nonce']==owner['prior_owner_nonce']
                and status['state']=='COMPLETE_VALIDATED' and status['owned_closure_proven'] is True
                and status['accession']==accession and status['complete_receipt_sha256']==complete_sha
                and exit_receipt['actual_wsl_client_exit']['exited'] is True and exit_receipt['actual_wsl_client_exit']['exit_code']==0,
                'Actual original owner/status/complete joins differ')
        for suffix in ('stdout','stderr'):
            require(hashlib.sha256(original_owner[accession+'.'+suffix+'.txt']).hexdigest()==exit_receipt[suffix+'_sha256'],
                    'Original owner log SHA differs')
        require(json.loads(original_owner['lock_released.json'])['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED',
                'Original owner did not explicitly unlock')
        expected_sums={};verified=0
        for item in archive.infolist():
            relative(item.filename);require(not item.is_dir() and not item.flag_bits&1,'Unexpected directory/encrypted raw member')
            if item.filename.startswith('genome/'):
                pin=files[item.filename[7:]]
                require(item.file_size==pin['bytes'] and item.external_attr>>16==stat.S_IFREG|pin['mode'],
                        'Actual raw member size/mode differs')
            else:pin=None
            with archive.open(item) as stream:size,digest=hash_stream(stream,check,MAX_LOGICAL if pin else MAX_MANIFEST)
            if pin:require(size==pin['bytes'] and digest==pin['sha256'],'Actual raw member full CRC/SHA differs')
            if item.filename!='SHA256SUMS.txt':expected_sums[item.filename]=digest
            verified+=1
        sums=member_bytes(archive,'SHA256SUMS.txt',32*1024**2,check).decode('utf-8')
        require(sums==''.join(h+'  '+n+'\n' for n,h in sorted(expected_sums.items())),'Exhaustive original raw SUMS differs')
    after=path.stat();require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
                              (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'Archive changed during verification')
    return {'schema':'STAGE05_CLOSED_GENOME_INDEPENDENT_RAW_ARCHIVE_V1','state':'PASS_BOUND_RAW_RECOVERY_BYTES_ONLY',
            'archive_sha256':expected_sha,'complete_sha256':complete_sha,'accession':accession,
            'actual_members_crc_sha_verified':verified,'raw_files':len(files),'raw_logical_bytes':total,
            'new_scientific_acceptance':False,'eviction_authorized':False,'manifest':manifest}


def restore_fresh(path,output,expected_sha,complete_sha,accession,check=lambda:None):
    """Create only a NEW raw tree; never move/delete/overwrite the original.

    This proves bytes/modes/mtime of a new tree. Exact canonical-path adoption,
    runtime/native receipt/curation acceptance and remote recovery are separate.
    """
    proof=verify_archive(path,expected_sha,complete_sha,accession,check);manifest=proof['manifest'];output=Path(output)
    require(output.is_absolute() and output==output.resolve() and not output.exists() and not output.is_symlink(),
            'New absolute nonaliased restoration tree required')
    for parent in (output.parent,*output.parent.parents):
        info=parent.lstat();require(stat.S_ISDIR(info.st_mode) and not parent.is_symlink()
                                   and not getattr(info,'st_file_attributes',0)&0x400,'Restore ancestor alias/reparse forbidden')
    dirs=manifest['directories_to_restore'];files=manifest['files'];locks=manifest['omitted_empty_lock_files']
    require(all(p['mode']<=0o777 for p in [*files.values(),*dirs.values()]),
            'Unreviewed privilege bits forbid restoration; preserve archive and original')
    output.mkdir()
    for name in sorted(set(dirs)-{'.'},key=lambda n:(len(PurePosixPath(n).parts),n)):
        check();output.joinpath(*PurePosixPath(name).parts).mkdir()
    with zipfile.ZipFile(path) as archive:
        for name,pin in sorted(files.items()):
            check();target=output.joinpath(*PurePosixPath(name).parts);digest=hashlib.sha256();count=0
            with archive.open('genome/'+name) as source,target.open('xb') as destination:
                while block:=source.read(CHUNK):
                    check();count+=len(block);require(count<=pin['bytes'],'Restore member grew');digest.update(block);destination.write(block)
                destination.flush();os.fsync(destination.fileno())
            require(count==pin['bytes'] and digest.hexdigest()==pin['sha256'],'Restored original SHA/size differs')
            os.chmod(target,pin['mode']);os.utime(target,ns=(pin['identity'][3],pin['identity'][3]))
        for name in locks:
            check();target=output.joinpath(*PurePosixPath(name).parts)
            with target.open('xb') as stream:stream.flush();os.fsync(stream.fileno())
            os.chmod(target,0o600)
    for name in sorted(dirs,key=lambda n:(len(PurePosixPath(n).parts),n),reverse=True):
        target=output if name=='.' else output.joinpath(*PurePosixPath(name).parts);pin=dirs[name]
        os.chmod(target,pin['mode']);os.utime(target,ns=(pin['identity'][3],pin['identity'][3]))
    actual_files=set();actual_dirs={'.'}
    for directory,children,names in os.walk(output,followlinks=False):
        directory=Path(directory);directory_name=directory.relative_to(output).as_posix();directory_info=directory.lstat()
        require(directory_name in dirs and stat.S_IMODE(directory_info.st_mode)==dirs[directory_name]['mode']
                and directory_info.st_mtime_ns==dirs[directory_name]['identity'][3],'Restored directory mode/mtime differs')
        for name in children:
            target=Path(directory)/name;check();require(target.is_dir() and not target.is_symlink(),'Unexpected restored directory alias')
            actual_dirs.add(target.relative_to(output).as_posix())
        for name in names:
            target=Path(directory)/name;check();relative_name=target.relative_to(output).as_posix();actual_files.add(relative_name)
            info=target.lstat();require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and not target.is_symlink(),'Restored regular identity invalid')
            if relative_name in files:
                pin=files[relative_name]
                with target.open('rb') as stream:count,digest=hash_stream(stream,check,pin['bytes'])
                require(count==pin['bytes'] and digest==pin['sha256'] and stat.S_IMODE(info.st_mode)==pin['mode']
                        and info.st_mtime_ns==pin['identity'][3],'Restored full bytes/mode/mtime differ')
            else:require(relative_name in locks and info.st_size==0,'Unexpected restored raw file')
    require(actual_files==set(files)|set(locks) and actual_dirs==set(dirs),'Restored exact path inventory differs')
    with Path(path).open('rb') as stream:_,archive_sha=hash_stream(stream,check,MAX_ASSET)
    require(archive_sha==expected_sha,'Original archive changed during restoration')
    return {k:v for k,v in proof.items() if k!='manifest'}|{'state':'PASS_NEW_RAW_TREE_BYTES_MODES_MTIME_ONLY',
        'restored_path':str(output),'canonical_path_matches_manifest':str(output)==manifest['restore_genome_path'],
        'native_cache_adoption':'NOT_TESTED','curation_acceptance':'NOT_TESTED','remote_recovery':'NOT_ESTABLISHED'}
