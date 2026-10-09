"""Opt-in raw recovery ZIP for one closed genome; never deletes or runs tools."""
from pathlib import Path, PurePosixPath
import argparse, base64, hashlib, json, os, signal, stat, sys, time, zipfile
import stage5_atomic as S
import stage5_atomic_process as P
import stage5_work_storage as W

WORK=Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work')
ROOT=Path('/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196')
SCOPE='ONE_CLOSED_GENOME_RAW_RECOVERY_ONLY'
PINS={'stage5_atomic.py':'2d7414fd33fe6216b95cfd549cee743d8b7057db698aced509f9a7ffefa77fc0',
      'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
      'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f'}
MAX_FILES=100000
MAX_LOGICAL=16*1024**3
MAX_ASSET=448*1024**2
CHUNK=1024**2
MAX_METADATA_FILE=8*1024**2
DIRECTORIES={'bundle','execution','bundle_audit','inventory','raw_validation','transactions'}
ROOT_FILES={'complete.json','scientific_identity.json','status.json','.guard'}


def require(ok,message):
    if not ok: raise ValueError(message)


def identity(info):
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns)


def json_bytes(value):
    return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode('utf-8')


def closure_proven(children,scope_entered,scope_complete,observed_unproven):
    return not children and not observed_unproven and (not scope_entered or scope_complete)


def captured_metadata(path,expected_sha,check):
    path=W.canonical(path);require(path.is_file() and path.stat().st_size<=MAX_METADATA_FILE,'Bounded regular recovery metadata required')
    digest=hashlib.sha256();chunks=[];count=0
    with path.open('rb') as source:
        before=identity(os.fstat(source.fileno()))
        while block:=source.read(CHUNK):
            check();count+=len(block);require(count<=MAX_METADATA_FILE,'Recovery metadata byte cap exceeded')
            digest.update(block);chunks.append(block)
        require(identity(os.fstat(source.fileno()))==before==identity(path.lstat()),'Recovery metadata identity changed')
    require(digest.hexdigest()==expected_sha,'Recovery metadata SHA differs')
    return {'path':str(path),'bytes':count,'sha256':expected_sha,'base64_original_bytes':base64.b64encode(b''.join(chunks)).decode('ascii')}


def inventory(root,max_files=MAX_FILES,max_logical=MAX_LOGICAL,check=lambda:None):
    """No-follow bounded traversal; unknown or aliased payload is preserved."""
    rows={};directories={};omitted=[];total=0;visited=0;stack=[root];device=root.stat().st_dev
    while stack:
        directory=stack.pop();info=directory.lstat()
        require(stat.S_ISDIR(info.st_mode) and not directory.is_symlink() and info.st_dev==device,'Raw source directory alias/type/device changed')
        directories[directory.relative_to(root).as_posix()]={'identity':identity(info),'mode':stat.S_IMODE(info.st_mode)}
        with os.scandir(directory) as entries:
            for entry in entries:
                check();visited+=1;require(visited<=max_files*2+1000,'Raw traversal entry cap exceeded; preserve')
                path=Path(entry.path);relative=path.relative_to(root).as_posix();parts=PurePosixPath(relative).parts
                require(not any(ord(c)<32 for c in relative) and '\\' not in relative,'Unsafe raw filename')
                info=path.lstat()  # Fresh no-follow identity, not cached DirEntry metadata.
                require(not stat.S_ISLNK(info.st_mode) and not path.is_symlink(),'Raw source symlink forbidden; preserve')
                if stat.S_ISDIR(info.st_mode):
                    require(parts[0] in DIRECTORIES,'Unknown raw source directory; preserve')
                    stack.append(path)
                else:
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_dev==device,'Raw source must be regular with one link on the bound device')
                    require(parts[0] in DIRECTORIES or relative in ROOT_FILES,'Unknown raw root file; preserve')
                    if path.name in {'.guard','.runner.guard'}:
                        require(info.st_size==0,'Nonempty raw guard is unknown evidence; preserve')
                        omitted.append(relative);continue
                    rows[relative]={'bytes':info.st_size,'identity':identity(info),'mode':stat.S_IMODE(info.st_mode)};total+=info.st_size
                    require(len(rows)<=max_files and total<=max_logical,'Raw recovery file/logical-byte cap exceeded; preserve')
    require(rows,'No raw recovery payload')
    return rows,sorted(omitted),total,directories


class LimitedWriter:
    def __init__(self,stream,limit):self.stream,self.limit=stream,limit
    def write(self,data):
        require(self.stream.tell()+len(data)<=self.limit,'Compressed asset cap exceeded; preserve partial')
        return self.stream.write(data)
    def seek(self,offset,whence=0):
        value=self.stream.seek(offset,whence)
        require(0<=value<=self.limit,'Compressed asset seek exceeds cap')
        return value
    def tell(self):return self.stream.tell()
    def flush(self):return self.stream.flush()
    def seekable(self):return True


def zip_info(name,mode=0o644):
    value=zipfile.ZipInfo(name,(2026,10,9,0,0,0));value.create_system=3
    value.external_attr=(stat.S_IFREG|mode)<<16;value.compress_type=zipfile.ZIP_DEFLATED
    return value


def zip_reopen(path,expected,check):
    with zipfile.ZipFile(path,'r') as archive:
        names=archive.namelist();require(len(names)==len(set(names)) and set(names)==set(expected),'ZIP exact member set differs')
        for item in archive.infolist():
            check();pin=expected[item.filename]
            require(not item.is_dir() and item.file_size==pin['bytes'],'ZIP member type/size differs')
            if 'mode' in pin:
                require(item.external_attr>>16==stat.S_IFREG|pin['mode'],'ZIP original regular-file mode differs')
            digest=hashlib.sha256();count=0
            with archive.open(item,'r') as source:
                while block:=source.read(CHUNK):check();digest.update(block);count+=len(block)
            require(count==pin['bytes'] and digest.hexdigest()==pin['sha256'],'ZIP actual CRC/size/SHA readback differs')
    return len(names)


def build_zip(genome,output,complete_sha,metadata,check,max_files=MAX_FILES,max_logical=MAX_LOGICAL,max_asset=MAX_ASSET):
    """Pure file builder also used by synthetic tests; output must be fresh."""
    require(not output.exists() and not output.with_suffix(output.suffix+'.partial').exists()
            and not output.with_name(output.name+'.sha256').exists(),'Archive, partial or sidecar already exists; preserve')
    require((genome/'complete.json').stat().st_size<=MAX_METADATA_FILE
            and (genome/'scientific_identity.json').stat().st_size<=MAX_METADATA_FILE,'Bounded raw checkpoint metadata required')
    require(S.sha(genome/'complete.json')==complete_sha,'Closed raw complete receipt changed')
    complete=S.read_json(genome/'complete.json')
    require(complete['schema']=='STAGE05_ATOMIC_GENOME_COMPLETE_V1' and complete['state']=='COMPLETE_VALIDATED'
            and complete['scientific_identity']['schema']=='STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2'
            and complete['accession']==complete['scientific_identity']['accession']==genome.name
            and S.fingerprint(complete['scientific_identity'])==complete['scientific_identity_sha256'],
            'Closed raw native V2 checkpoint required')
    require(S.read_json(genome/'scientific_identity.json')==complete['scientific_identity'],'Raw identity file differs from complete')
    rows,omitted,total,directories=inventory(genome,max_files,max_logical,check)
    require(set(complete['files'])<=set(rows),'Selected complete payload is missing/omitted')
    partial=output.with_suffix(output.suffix+'.partial');expected={}
    with partial.open('xb') as raw:
        with zipfile.ZipFile(LimitedWriter(raw,max_asset),'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
            for relative,pin in sorted(rows.items()):
                check();path=S.safe_member(genome,relative);digest=hashlib.sha256();count=0
                descriptor=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
                with os.fdopen(descriptor,'rb') as source:
                    before=os.fstat(source.fileno())
                    require(identity(before)==pin['identity'] and stat.S_IMODE(before.st_mode)==pin['mode']
                            and stat.S_ISREG(before.st_mode) and before.st_nlink==1,'Raw file identity changed before copy')
                    with archive.open(zip_info('genome/'+relative,pin['mode']),'w',force_zip64=True) as destination:
                        while block:=source.read(CHUNK):check();digest.update(block);count+=len(block);destination.write(block)
                    after=os.fstat(source.fileno());current=path.lstat()
                    require(identity(after)==pin['identity']==identity(current)
                            and stat.S_IMODE(after.st_mode)==pin['mode']==stat.S_IMODE(current.st_mode),
                            'Raw file identity changed during copy')
                require(count==pin['bytes'],'Raw file length changed during copy')
                value={'bytes':count,'sha256':digest.hexdigest(),'mode':pin['mode']}
                if relative in complete['files']:require(value['sha256']==complete['files'][relative],'Selected complete member SHA differs')
                if relative=='complete.json':require(value['sha256']==complete_sha,'Raw complete changed during copy')
                expected['genome/'+relative]=value;pin['sha256']=value['sha256']
            manifest={'schema':'STAGE05_CLOSED_GENOME_RAW_RECOVERY_MANIFEST_V1','scope':SCOPE,
                      'scientific_acceptance':'NO_NEW_SCIENTIFIC_ACCEPTANCE','eviction_authorized':False,
                      'restore_genome_path':str(genome),'complete_sha256':complete_sha,'files':rows,
                      'directories_to_restore':directories,'omitted_empty_lock_files':omitted,
                      'raw_files':len(rows),'raw_logical_bytes':total,'provenance':metadata}
            data=json_bytes(manifest);archive.writestr(zip_info('_recovery/manifest.json'),data)
            expected['_recovery/manifest.json']={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
            sums=''.join(pin['sha256']+'  '+name+'\n' for name,pin in sorted(expected.items())).encode('utf-8')
            archive.writestr(zip_info('SHA256SUMS.txt'),sums)
            expected['SHA256SUMS.txt']={'bytes':len(sums),'sha256':hashlib.sha256(sums).hexdigest()}
        raw.flush();os.fsync(raw.fileno())
    members=zip_reopen(partial,expected,check)
    current,current_omitted,current_total,current_directories=inventory(genome,max_files,max_logical,check)
    require(set(current)==set(rows) and current_omitted==omitted and current_total==total
            and current_directories==directories
            and all(current[n]['identity']==rows[n]['identity'] and current[n]['mode']==rows[n]['mode'] for n in rows),
            'Raw tree membership/identity drift after readback')
    check();digest=hashlib.sha256()
    with partial.open('rb') as source:
        while block:=source.read(CHUNK):check();digest.update(block)
    require(partial.stat().st_size<=max_asset,'Actual archive cap exceeded')
    partial.rename(output)
    with output.with_name(output.name+'.sha256').open('xb') as stream:
        stream.write((digest.hexdigest()+'  '+output.name+'\n').encode('ascii'));stream.flush();os.fsync(stream.fileno())
    return {'schema':'STAGE05_CLOSED_GENOME_RAW_RECOVERY_BUILD_V1','state':'PASS_RAW_RECOVERY_ZIP_BYTES_ONLY',
            'scope':SCOPE,'asset_path':str(output),'asset_bytes':output.stat().st_size,'asset_sha256':digest.hexdigest(),
            'sidecar_path':str(output)+'.sha256','sidecar_sha256':S.sha(str(output)+'.sha256'),
            'actual_members_crc_sha_verified':members,'raw_files':len(rows),'raw_logical_bytes':total,
            'complete_sha256':complete_sha,'restore_genome_path':str(genome),'eviction_authorized':False,
            'remote_recovery':'NOT_RUN','new_scientific_acceptance':False}


def main():
    import fcntl
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('config','config-sha256','accession','complete-sha256','output','owner-lease','owner-nonce','source-sha256','asset-relative','prior-owner-proof','prior-owner-proof-sha256'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    require(sys.platform=='linux' and os.geteuid()==0 and Path(__file__).resolve().parent==WORK,'Exact root Linux archive helper required')
    require(S.sha(__file__)==args.source_sha256 and all(S.sha(WORK/n)==pin for n,pin in PINS.items()),'Archive/helper code differs')
    config_path=W.canonical(args.config);out=W.canonical(args.output)
    require(config_path.parent==WORK and S.sha(config_path)==args.config_sha256 and out.parent==WORK and out.is_dir(),'Actual C config/spool pins differ')
    terminal={'schema':'STAGE05_CLOSED_GENOME_ARCHIVE_LINUX_TERMINAL_V1','state':'FAILED','scope':SCOPE,
              'source_sha256':S.sha(__file__),'owner_nonce':args.owner_nonce,'native_launch_count':0,
              'prior_scope_check_entered':False,'prior_scope_check_complete':False,
              'observed_prior_closure_unproven':False,
              'bootstrap':{'argv':list(sys.argv),'executable':sys.executable,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                           'identity':P.proc_record(os.getpid())},'owned_closure_proven':False}
    deadline=time.monotonic()+1800;supervisor=None
    def check():
        require(time.monotonic()<deadline,'Finite raw recovery archive deadline expired')
        supervisor.check_owner()
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(ValueError('Raw recovery archive wall deadline expired')))
    signal.alarm(1800)
    try:
        config=S.load_config(config_path);require(config['root']==str(ROOT),'Canonical scientific root differs')
        S.validate_storage(config);S.approved_accession(ROOT,args.accession)
        genome=Path(config['output_root'])/args.accession
        require(genome.parent==ROOT/'.work/stage05_atomic_v1' and W.canonical(genome)==genome,'Exact nonaliased bind genome root required')
        relative=PurePosixPath(args.asset_relative)
        require(relative.as_posix()==args.asset_relative and relative.parts[:2]==('release_staging','stage05_atomic_archives_v1')
                and len(relative.parts)==3 and relative.name==args.accession+'_'+args.complete_sha256[:12]+'_'+args.owner_nonce[:8]+'.zip'
                and '..' not in relative.parts and '\\' not in args.asset_relative,'Scoped new G archive asset required')
        paths=[W.canonical(genome.parent/'.native_runner.guard'),W.canonical(genome/'.guard')]
        with os.fdopen(os.open(paths[0],os.O_RDWR|os.O_NOFOLLOW),'r+b') as global_guard,os.fdopen(os.open(paths[1],os.O_RDWR|os.O_NOFOLLOW),'r+b') as guard:
            for stream in (global_guard,guard):
                info=os.fstat(stream.fileno())
                require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size==0,'Existing empty regular raw runner guard required')
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            supervisor=P.Supervisor(Path(args.owner_lease),args.owner_nonce,config['resource_policy'],out,S.sha)
            supervisor.admission(out)
            os.nice(10);terminal['linux_nice']=os.getpriority(os.PRIO_PROCESS,0)
            terminal['prior_scope_check_entered']=True
            for path in (genome/'execution').rglob('*.launch_intent.json'):check();supervisor.assert_intent_closed(path)
            for path in (genome/'execution').rglob('*.launch.json'):check();supervisor.assert_closed(S.read_json(path))
            terminal['prior_scope_check_complete']=True
            require(S.sha(genome/'complete.json')==args.complete_sha256,'Owner-bound completed raw checkpoint differs')
            proof_path=W.canonical(args.prior_owner_proof)
            require(proof_path.parent==out and S.sha(proof_path)==args.prior_owner_proof_sha256,'Pinned actual closed owner proof differs')
            proof=S.read_json(proof_path);status=S.read_json(genome/'status.json')
            complete=S.read_json(genome/'complete.json')
            require(proof['schema']=='STAGE05_CLOSED_GENOME_ARCHIVE_OWNER_SOURCE_V1'
                    and proof['accession']==args.accession and proof['config_sha256']==args.config_sha256
                    and proof['complete_sha256']==args.complete_sha256 and S.sha(genome/'status.json')==proof['status_sha256']
                    and status['accession']==args.accession and status['owner_nonce']==proof['prior_owner_nonce']
                    and status['state']=='COMPLETE_VALIDATED' and status['owned_closure_proven'] is True
                    and status['complete_receipt_sha256']==args.complete_sha256,'Actual closed genome/owner/status binding differs')
            require(complete['scientific_identity']['runtime_manifest_sha256']==config['runtime']['manifest_sha256']
                    and complete['scientific_identity']['source_acceptance']['source_pins_sha256']==S.PINNED_SOURCE_ACCEPTANCE,
                    'Closed genome/source/runtime identity differs from archival config')
            S.validate_storage(config)
            asset=W.canonical(ROOT.joinpath(*relative.parts));asset.parent.mkdir(parents=True,exist_ok=True)
            metadata={'config_sha256':args.config_sha256,'source_sha256':args.source_sha256,'source_pins':PINS,
                      'storage_proof_sha256':config['work_storage']['proof_sha256'],'accession':args.accession,
                      'closed_owner_proof':proof,'closed_owner_proof_sha256':args.prior_owner_proof_sha256,
                      'actual_metadata_files':{
                          'config.json':captured_metadata(config_path,args.config_sha256,check),
                          'closed_owner_proof.json':captured_metadata(proof_path,args.prior_owner_proof_sha256,check),
                          'runtime_manifest.json':captured_metadata(config['runtime']['manifest_path'],config['runtime']['manifest_sha256'],check),
                          'storage_proof.json':captured_metadata(config['work_storage']['proof_path'],config['work_storage']['proof_sha256'],check),
                          'accepted_source_pins.json':captured_metadata(WORK/'stage5_accepted_source_pins.json',S.PINNED_SOURCE_ACCEPTANCE,check),
                          'approved_accessions.txt':captured_metadata(ROOT/'config/approved_accessions.txt',S.PINNED_PANEL,check)}}
            report=build_zip(genome,asset,args.complete_sha256,metadata,check)
            S.validate_storage(config);require(S.sha(config_path)==args.config_sha256
                    and S.sha(proof_path)==args.prior_owner_proof_sha256,'Archive config/owner proof drift')
            check();P.atomic_json(out/'build_receipt.json',report);terminal['build_receipt_sha256']=S.sha(out/'build_receipt.json')
            terminal['state']='PASS_RAW_RECOVERY_ZIP_BYTES_ONLY'
    except BaseException as error:terminal['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        signal.alarm(0)
        try:
            terminal['remaining_direct_children']=[int(x) for x in Path(f'/proc/self/task/{os.getpid()}/children').read_text().split()]
            terminal['observed_prior_closure_unproven']=bool(supervisor and supervisor.closure_unproven)
            terminal['owned_closure_proven']=closure_proven(terminal['remaining_direct_children'],
                terminal['prior_scope_check_entered'],terminal['prior_scope_check_complete'],
                terminal['observed_prior_closure_unproven'])
        except BaseException as error:terminal['closure_error']=str(error)
        P.atomic_json(out/'archive_linux_terminal.json',terminal)
    return 0 if terminal['state']=='PASS_RAW_RECOVERY_ZIP_BYTES_ONLY' and terminal['owned_closure_proven'] else 2


if __name__=='__main__':raise SystemExit(main())
