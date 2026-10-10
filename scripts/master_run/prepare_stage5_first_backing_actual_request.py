"""Default-NOOP first-genome request preparation from fixed post-restart gates.

Writes only an explicit fresh C request after --prepare. Does not execute gates,
build/admit a native config, invoke WSL, run science, acquire locks or alter refs.
"""
from pathlib import Path
import argparse,copy,hashlib,json,os,re,stat

WORK=Path(__file__).resolve().parent
EXACT_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ORIGINAL_SHA='d9addf686ceb29d35180ae65e55aa0d202be1c4228305d7d8fa2d885b3235a2c'
TEMPLATE_SHA='2db68c531594ccf6785ad2f6e9948008cc77b8cad88c982d044af115eb3cc136'
CANDIDATES={'runtime_manifest':'stage5_runtime_actual_postiq_08.json','storage_proof':'stage5_storage_actual_postiq_06.json'}
GATES={'toolchain':'stage5_setup_toolchain_actual_postiq_07','runtime':'stage5_setup_runtime_actual_postiq_08',
       'interop':'stage5_interop_actual_postiq_05','storage':'stage5_setup_storage_actual_postiq_06',
       'drivefs':'stage5_setup_drivefs_actual_postiq_04','unc':'stage5_unc_backing_actual_postiq_04'}
NATIVE_RESOURCE_BYTES={'incremental_windows_requirement_bytes':1610612736,'commit_requirement_bytes':3221225472,
    'linux_job_requirement_bytes':1610612736,'process_address_space_limit_bytes':4294967296,'sampled_rss_stop_bytes':1342177280}
RESOURCE_BASIS=(
    'Explicit conservative capacity allocation for the first complete approved genome GCF_000009425.1, '
    'using the unchanged full PADLOC5027 and complete DefenseFinder native method, two threads and one serial owner. '
    'These values are not measured detector requirements: allocate 1.5GiB incremental Windows and Linux job memory, '
    'retain the existing 1.5GiB Windows and 1GiB Linux reserves, require 3GiB Windows commit headroom, '
    'stop at sampled aggregate descendant RSS 1.25GiB and cap each process address space at 4GiB. '
    'Keep the WSL global 3GB memory setting. Fresh admission is required before native commands; insufficient capacity '
    'defers execution, and an exceeded limit is a preserved execution failure, never biological absence. '
    'Measure elapsed time, CPU and descendant RSS on this full genome before increasing concurrency or changing capacity. '
    'Accepted Stage4 and the approved196 panel are unchanged.')


def need(value,message):
    if not value:raise ValueError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def build_request(template_raw,reader,work=EXACT_WORK):
    """Pure deterministic constructor; reader supplies bounded exact bytes."""
    need(isinstance(template_raw,bytes) and digest(template_raw)==TEMPLATE_SHA and callable(reader),'Exact original template/source reader required')
    request=copy.deepcopy(json.loads(template_raw))
    need(request['schema']=='STAGE05_ACTUAL_CONFIG_REQUEST_V1' and request['purpose']=='FIRST_APPROVED_GENOME_RESOURCE_MEASUREMENT'
         and set(request['gates'])==set(GATES),'Original scientific request semantics differ')
    for key,name in CANDIDATES.items():
        raw=reader(name);need(isinstance(raw,bytes) and 0<len(raw)<=16*1024**2,'Bounded actual candidate required')
        value=json.loads(raw);schema='STAGE05_PINNED_RUNTIME_V1' if key=='runtime_manifest' else 'STAGE05_EXT4_BIND_STORAGE_PROOF_V1'
        need(value['schema']==schema,'Actual candidate role differs')
        request[key]={'path':str(work/name),'sha256':digest(raw)}
    for kind,name in GATES.items():
        relative=name+'/result.json';raw=reader(relative);unlock_raw=reader(name+'/lock_released.json')
        need(isinstance(raw,bytes) and isinstance(unlock_raw,bytes) and 0<len(raw)<=16*1024**2
             and 0<len(unlock_raw)<=16*1024**2,'Bounded complete actual gate/unlock bytes required')
        value=json.loads(raw);unlock=json.loads(unlock_raw)
        need(isinstance(value.get('state'),str) and value['state'].startswith('PASS_'),'Fresh gate has not passed: '+kind)
        need(unlock['state']==('EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK' if kind=='unc' else 'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED')
             and unlock.get('released',True) is True,'Fresh gate original unlock differs: '+kind)
        request['gates'][kind]={'path':str(work/relative),'sha256':digest(raw),'unlock_sha256':digest(unlock_raw)}
    request['native_resource_bytes']=copy.deepcopy(NATIVE_RESOURCE_BYTES);request['resource_basis']=RESOURCE_BASIS
    return request


def read_plain(relative):
    path=WORK/relative
    need(path.is_relative_to(WORK) and path.resolve()==path,'Exact C evidence path required')
    for node in (path,*path.parents):
        info=node.lstat();need(not node.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400,'Plain evidence ancestry required')
    before=path.lstat();need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=16*1024**2,'Bounded single-link actual evidence required')
    with path.open('rb') as stream:
        opened=os.fstat(stream.fileno());raw=stream.read(16*1024**2+1);after=os.fstat(stream.fileno())
    def identity(value):return value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns
    need(len(raw)==before.st_size and identity(before)==identity(opened)==identity(after)==identity(path.lstat()),'Evidence changed during read')
    return raw


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--output')
    args=parser.parse_args()
    if not args.prepare:
        print(json.dumps({'state':'PREPARED_NOT_RUN','gates_executed':0,'requests_written':0,'scientific_execution':'NOT_RUN'}));return 0
    need(os.name=='nt' and WORK==EXACT_WORK,'Exact WD Windows C request workspace required')
    need(re.fullmatch(r'stage5_actual_request_[A-Za-z0-9_]+[.]json',args.output or ''),'Fresh direct C request filename required')
    output=WORK/args.output;need(not output.exists() and output==output.resolve(),'Preserve any prior request')
    need(digest(read_plain('prepare_stage5_first_actual_request.py'))==ORIGINAL_SHA,'Preserved original helper source differs')
    cache={}
    def reader(name):
        raw=read_plain(name);cache[name]=raw;return raw
    request=build_request(reader('stage5_actual_config_request.template.json'),reader,WORK)
    need(all(read_plain(name)==raw for name,raw in cache.items())
         and digest(read_plain('prepare_stage5_first_actual_request.py'))==ORIGINAL_SHA,'Final actual evidence/template drift')
    with output.open('x',encoding='utf-8',newline='\n') as stream:json.dump(request,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps({'request':str(output),'sha256':digest(output.read_bytes()),'scientific_execution':'NOT_RUN','native_admission':'REQUIRES_EXISTING_CONFIG_BUILDER_AND_OWNER'}))
    return 0


if __name__=='__main__':raise SystemExit(main())
