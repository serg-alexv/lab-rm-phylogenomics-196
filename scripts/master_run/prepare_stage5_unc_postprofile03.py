"""Default-NOOP C-only UNC03 config preparation; no runtime/UNC/WSL action.

Fill only exact runtime08/storage06 paths and explicitly supplied actual byte
pins in the preserved V2 template. All biological resource budgets stay null.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse, copy, hashlib, json, os, re, stat, uuid

WORK=Path(__file__).resolve().parent
EXACT_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
RUNTIME_NAME='stage5_runtime_actual_postiq_08.json'
STORAGE_NAME='stage5_storage_actual_postiq_06.json'
OUTPUT_NAME='stage5_unc_config_actual_postprofile_03.json'
BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
ROOT='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
TARGET=ROOT+'/.work/stage05_atomic_v1'
BACKING='/var/tmp/lab_rm_stage05_atomic_v1'
TEMPLATE='stage5_atomic_config.template.json'
FIELDS=('incremental_windows_requirement_bytes','commit_requirement_bytes','linux_job_requirement_bytes',
        'process_address_space_limit_bytes','sampled_rss_stop_bytes')
PINS={TEMPLATE:'94137787139276a70cd10e0c85e13597c860950c2fba04c5c05580601ddc11cf',
 'prepare_stage5_unc_postboot02.py':'bce2bdfb2d871299d56428da7839e7096f35dbca4b71337da0726b8e36d3f359',
 'stage5_unc_bind_probe.py':'0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d',
 'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f'}


def need(value,message):
    if not value:raise ValueError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def pin(value):
    need(isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None,'Explicit actual candidate SHA256 required')
    return value


def linux_path(name):
    need(name in (RUNTIME_NAME,STORAGE_NAME),'Fixed direct C candidate route required')
    path=PureWindowsPath(str(EXACT_WORK))/name
    need(path.drive.casefold()=='c:' and '..' not in path.parts,'Exact C mounted path required')
    return '/mnt/c/'+'/'.join(path.parts[1:])


def build_config(template_raw,runtime_raw,storage_raw,runtime_sha,storage_sha):
    """Pure bounded exact-byte constructor, without actual mount observation."""
    need(isinstance(template_raw,bytes) and digest(template_raw)==PINS[TEMPLATE],'Unchanged V2 template required')
    for raw,expected in [(runtime_raw,runtime_sha),(storage_raw,storage_sha)]:
        need(isinstance(raw,bytes) and 0<len(raw)<=16*1024**2 and digest(raw)==pin(expected),'Bounded actual candidate bytes/SHA differ')
    value=copy.deepcopy(json.loads(template_raw));runtime=json.loads(runtime_raw);storage=json.loads(storage_raw)
    need(value['schema']=='STAGE05_ATOMIC_CONFIG_V2' and value['root']==ROOT and value['output_root']==TARGET
         and value['source']==ROOT+'/.work/source_locus_inputs_v1'
         and value['source_validation']==ROOT+'/.work/stage03_source_validation/validation_summary.json'
         and all(value['resource_policy'][k] is None for k in FIELDS),'Exact V2 non-scientific probe roles/null budgets required')
    need(runtime['schema']=='STAGE05_PINNED_RUNTIME_V1'
         and runtime['scope']=='Hash/version discovery only; execution/interoperability NOT_RUN'
         and runtime['roots']=={k:value['runtime'][k] for k in ('environment_dir','models_dir','padloc_db')},
         'Actual runtime discovery scope/roots differ')
    need(set(runtime['files'])==set(runtime['roots']) and all(isinstance(files,dict) and files for files in runtime['files'].values()),
         'Complete runtime file-role maps required')
    for files in runtime['files'].values():
        for relative,sha in files.items():
            need(isinstance(relative,str) and relative and not PurePosixPath(relative).is_absolute()
                 and '..' not in PurePosixPath(relative).parts and '\\' not in relative,'Runtime relative file role differs')
            pin(sha)
    need(storage['schema']=='STAGE05_EXT4_BIND_STORAGE_PROOF_V1' and storage['canonical_root']==ROOT
         and storage['canonical_target']==TARGET and storage['backing']==BACKING and storage['boot_id']==BOOT
         and storage['helper_sha256']==PINS['stage5_work_storage.py'],'Actual storage role/current boot/helper differs')
    need(all(type(storage[k]) is int and storage[k]>0 for k in ('directory_device','directory_inode'))
         and str(uuid.UUID(storage['filesystem_uuid']))==storage['filesystem_uuid'] and uuid.UUID(storage['filesystem_uuid']).int>0,
         'Exact storage directory/UUID identity required')
    target,backing=storage['target_mount'],storage['backing_mount']
    for row in (target,backing):
        need(row['filesystem']=='ext4' and 'rw' in row['options'].split(',') and 'ro' not in row['options'].split(',')
             and type(row['mount_id']) is int and row['mount_id']>0 and type(row['parent_id']) is int and row['parent_id']>=0
             and re.fullmatch('[0-9]+:[0-9]+',row['major_minor']) is not None,'Writable ext4 mount evidence required')
    need(target['mountpoint']==TARGET and target['root']==BACKING and backing['mountpoint']==backing['root']=='/'
         and target['major_minor']==backing['major_minor'] and target['source']==backing['source']
         and isinstance(target['source'],str) and target['source'].startswith('/dev/'),'Exact root-filesystem ext4 bind roles differ')
    value['runtime'].update(manifest_path=linux_path(RUNTIME_NAME),manifest_sha256=runtime_sha)
    value['work_storage'].update(proof_path=linux_path(STORAGE_NAME),proof_sha256=storage_sha)
    need(all(value['resource_policy'][k] is None for k in FIELDS),'No biological admission budget may be filled')
    return value


def read_plain(name):
    path=WORK/name;need(path.parent==WORK and path==path.resolve(),'Exact direct C evidence file required')
    for node in (path,*path.parents):
        info=node.lstat();need(not node.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400,'Plain evidence ancestry required')
    before=path.lstat();need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=16*1024**2,'Bounded single-link C evidence required')
    with path.open('rb') as stream:
        opened=os.fstat(stream.fileno());raw=stream.read(16*1024**2+1);after=os.fstat(stream.fileno())
    identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_nlink)
    need(len(raw)==before.st_size and identity(before)==identity(opened)==identity(after)==identity(path.lstat()),'Evidence identity/bytes drift')
    return raw


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--runtime-sha256');parser.add_argument('--storage-sha256');args=parser.parse_args()
    if not args.prepare:
        print(json.dumps({'state':'PREPARED_NOT_RUN','configs_written':0,'WSL_launches':0,'UNC_actions':0,'scientific_admission':'NOT_AUTHORIZED'}));return 0
    need(os.name=='nt' and WORK==EXACT_WORK,'Exact WD Windows C preparation workspace required')
    runtime_sha,storage_sha=pin(args.runtime_sha256),pin(args.storage_sha256)
    output=WORK/OUTPUT_NAME;need(not output.exists() and not output.is_symlink() and output==output.resolve(),'Preserve prior UNC03 config')
    cache={n:read_plain(n) for n in PINS};need(all(digest(cache[n])==h for n,h in PINS.items()),'Preserved template/route/probe/storage source drift')
    cache[RUNTIME_NAME]=read_plain(RUNTIME_NAME);cache[STORAGE_NAME]=read_plain(STORAGE_NAME)
    value=build_config(cache[TEMPLATE],cache[RUNTIME_NAME],cache[STORAGE_NAME],runtime_sha,storage_sha)
    need(all(read_plain(n)==raw for n,raw in cache.items()),'Final candidate/source/template byte drift')
    with output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps({'config':str(output),'sha256':digest(output.read_bytes()),'scope':'NONSCIENTIFIC_UNC_ONLY_NATIVE_BUDGETS_REMAIN_NULL',
        'actual_probe':'NOT_RUN_REQUIRES_UNCHANGED_U0664_OWNER_CURRENT_STORAGE_AND_CLOSURE'}));return 0


if __name__=='__main__':raise SystemExit(main())
