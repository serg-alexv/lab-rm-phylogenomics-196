"""Build a C-only first-genome config from actual gates and an explicit budget.

Default is preparation only. Never boots WSL, mounts, installs or runs biology.
The existing owner/runner still perform fresh actual native admission.
"""
from pathlib import Path, PurePosixPath
import argparse, copy, hashlib, importlib, json, math, os, re

WORK=Path(__file__).resolve().parent
EXACT_WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
LINUX_ROOT='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
FIELDS=('incremental_windows_requirement_bytes','commit_requirement_bytes','linux_job_requirement_bytes',
        'process_address_space_limit_bytes','sampled_rss_stop_bytes')
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
      'stage5_atomic.py':'500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04',
      'stage5_windows_owner.py':'8851bc4fc48ad3069d4ffabe410e159004ef4fc8d6d0755213fc14c22fe0603d',
      'stage5_owner_lease.py':'add2cbf12ee6d51bb10168b629a8befd2136f58e5194a6e7195fea25002620b8',
      'stage5_atomic_config.template.json':'94137787139276a70cd10e0c85e13597c860950c2fba04c5c05580601ddc11cf',
      'stage5_setup_windows.py':'b5826e46af71ad2353fef4a2c1ab28fe009f02411f9ab0b22032d46026755b33',
      'stage5_setup_linux.py':'24aab72b74dd0aab6c58cac4951c30e6b1bfc9462460486748b546e50ec92e27',
      'stage5_interop_smoke_windows.py':'35ad3326488679770a74fe5b0df37e9b0518e317230f611b53c1aca1a3b4d898',
      'stage5_unc_bind_probe.py':'17eb6df098b01089e5919df1982fb047539385e07c69f9eba64060e61db24ed7'}


def require(ok,message):
    if not ok: raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    path=Path(path)
    require(path.stat().st_size<=16*1024**2,'Bounded explicit config/gate JSON required')
    return json.loads(path.read_bytes())


def pinned(spec,direct=False):
    path=Path(spec.get('path',''))
    require(path.is_absolute() and path==path.resolve() and WORK in path.parents
            and not any(p.is_symlink() for p in (path,*path.parents))
            and (not direct or path.parent==WORK),'Pinned C-work input required')
    require(re.fullmatch('[0-9a-f]{64}',spec.get('sha256','')) and sha(path)==spec['sha256'],
            'Explicit actual input SHA differs')
    return path,read(path)


def linux_path(path):
    require(path.drive.lower()=='c:' and WORK in path.parents,'C-mounted config evidence required')
    return '/mnt/c/'+'/'.join(path.parts[1:])


def explicit_policy(template,request):
    require(request.get('schema')=='STAGE05_ACTUAL_CONFIG_REQUEST_V1'
            and request.get('purpose')=='FIRST_APPROVED_GENOME_RESOURCE_MEASUREMENT','Explicit first-genome request required')
    policy=request.get('native_resource_bytes',{})
    require(set(policy)==set(FIELDS) and all(type(policy[k]) is int and policy[k]>0 for k in FIELDS),
            'All five explicit positive integer byte budgets required; no guessed defaults')
    basis=request.get('resource_basis')
    require(isinstance(basis,str) and 20<=len(basis.strip())<=8000,'Actual policy basis/uncertainty statement required')
    result=copy.deepcopy(template)
    result['resource_policy'].update(policy)
    result['resource_policy']['resource_wait_seconds']=0
    fixed=result['resource_policy']
    require(fixed['windows_reserve_bytes']==1610612736 and fixed['linux_reserve_bytes']==1073741824
            and fixed['threads']==2,'Keep reviewed native reserves and thread count')
    require(policy['incremental_windows_requirement_bytes']>=policy['linux_job_requirement_bytes']
            and policy['commit_requirement_bytes']>=fixed['windows_reserve_bytes']+policy['incremental_windows_requirement_bytes']
            and policy['sampled_rss_stop_bytes']<=policy['linux_job_requirement_bytes']
            and policy['process_address_space_limit_bytes']>=policy['sampled_rss_stop_bytes'],
            'Explicit admission/commit/RSS/address-space budgets are inconsistent')
    return result


def checked_gate(name,spec):
    path,value=pinned(spec)
    unlock=path.parent/'lock_released.json'
    require(re.fullmatch('[0-9a-f]{64}',spec.get('unlock_sha256','')) and sha(unlock)==spec['unlock_sha256'],
            'Actual explicit unlock pin differs')
    unlocked=read(unlock)
    require(unlocked['state']==('EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK' if name=='unc' else 'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED')
            and unlocked.get('released',True) is True,'Gate did not explicitly release its original lock')
    if name in ('toolchain','runtime','storage','drivefs'):
        require(value['state']=='PASS_NONSCIENTIFIC_SETUP_AND_WINDOWS_READBACK' and value['step']==name
                and value['source_sha256']==PINS['stage5_setup_windows.py']
                and value['linux_source_sha256']==PINS['stage5_setup_linux.py']
                and value['owned_closure_proven'] is True and value['unknown_closure_stop_preserved'] is False
                and value['actual_wsl_exit']['exited'] is True and value['actual_wsl_exit']['exit_code']==0,
                'Actual setup gate/source/closure differs: '+name)
        terminal=path.parent/'linux_terminal.json'
        require(sha(terminal)==value['linux_terminal_sha256'],'Actual setup Linux terminal SHA differs')
        native=read(terminal)
        require(native['owner_nonce']==value['owner_nonce'] and native['step']==name
                and native['source_sha256']==PINS['stage5_setup_linux.py'] and native['owned_closure_proven'] is True
                and native['state']=='PASS_NONSCIENTIFIC_SETUP_STEP','Actual setup terminal binding differs')
        if name in ('runtime','drivefs'): require(native['owned_command_count']==1,'Actual helper execution required')
    elif name=='interop':
        require(value['state']=='PASS_NONSCIENTIFIC_INTEROP_ONLY'
                and value['worker_sha256']=='38da0eb4e0bd4f1fdf11f90c3573fb693e833465bd7fd974aa7d46fdf456d28c'
                and value['supervisor_sha256']=='e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e'
                and [r['fixture'] for r in value['results']]==['exit0','lease_expiry','escaped_descendant']
                and all(r['state']=='PASS_NONSCIENTIFIC_INTEROP_FIXTURE' and r['owned_closure_proven'] is True
                        for r in value['results']),'Actual three-fixture interop gate differs')
    else:
        require(name=='unc' and value['state']=='PASS_NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY'
                and value['source_sha256']==PINS['stage5_unc_bind_probe.py'] and value['exact_owned_cleanup'] is True
                and [r['phase'] for r in value['steps']]==['linux-prepare','windows-io','linux-finalize'],
                'Actual exact bind UNC gate differs')
    return path,value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path); parser.add_argument('--request-sha256')
    parser.add_argument('--output',type=Path); parser.add_argument('--build',action='store_true')
    args=parser.parse_args()
    if not args.build:
        print(json.dumps({'state':'PREPARED_NOT_RUN','native_execution':'NOT_RUN','required_gates':[
            'toolchain','runtime','interop','storage','drivefs','unc'],'explicit_resource_fields':FIELDS})); return 0
    require(os.name=='nt' and WORK==EXACT_WORK,'Exact Windows C-work builder required')
    require(all(sha(WORK/name)==pin for name,pin in PINS.items()),'Reviewed config/source template differs')
    request_path,request=pinned({'path':str(args.request),'sha256':args.request_sha256},True)
    template=read(WORK/'stage5_atomic_config.template.json'); config=explicit_policy(template,request)
    require(set(request.get('gates',{}))=={'toolchain','runtime','interop','storage','drivefs','unc'},'Exact six actual gates required')
    gates={name:checked_gate(name,spec) for name,spec in request['gates'].items()}
    runtime_path,runtime=pinned(request['runtime_manifest'],True); storage_path,storage=pinned(request['storage_proof'],True)
    require(runtime['schema']=='STAGE05_PINNED_RUNTIME_V1' and runtime['scope']=='Hash/version discovery only; execution/interoperability NOT_RUN'
            and runtime['roots']=={k:config['runtime'][k] for k in ('environment_dir','models_dir','padloc_db')},'Actual runtime manifest roles differ')
    require(storage['schema']=='STAGE05_EXT4_BIND_STORAGE_PROOF_V1' and storage['canonical_root']==LINUX_ROOT
            and storage['canonical_target']==config['output_root'] and storage['backing']=='/var/tmp/lab_rm_stage05_atomic_v1'
            and storage['helper_sha256']=='7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f',
            'Actual storage proof roles/helper differ')
    for name,path in [('runtime',runtime_path),('storage',storage_path)]:
        terminal=read(gates[name][0].parent/'linux_terminal.json')
        require(terminal['candidate_path']==linux_path(path) and terminal['candidate_sha256']==sha(path),'Setup did not produce selected candidate')
    final=read(gates['unc'][0].parent/'final.json')
    require(sha(gates['unc'][0].parent/'final.json')==gates['unc'][1]['files']['final.json'],
            'UNC selected final receipt SHA differs')
    require(final['storage_after']['proof_path']==linux_path(storage_path)
            and final['storage_after']['proof_sha256']==sha(storage_path),'UNC tested a different bind proof')
    config['runtime'].update(manifest_path=linux_path(runtime_path),manifest_sha256=sha(runtime_path))
    config['work_storage'].update(proof_path=linux_path(storage_path),proof_sha256=sha(storage_path))
    output=args.output
    require(output is not None and output.is_absolute() and output.parent==WORK and output==output.resolve()
            and not output.exists() and output.suffix=='.json','Fresh direct C config output required')
    receipt=output.with_name(output.stem+'_build_receipt.json');require(not receipt.exists(),'Preserve config-build receipt')
    A=importlib.import_module('atomic_iqtree_windows'); S=importlib.import_module('stage5_atomic')
    require(Path(A.__file__).resolve()==WORK/'atomic_iqtree_windows.py' and Path(S.__file__).resolve()==WORK/'stage5_atomic.py','Config imports shadowed')
    api=A.Win()
    with A.WorkflowLock(api) as lock:
        require(not A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json').exists(),'Unreconciled closure stop exists')
        control=read(ROOT/'status/run_control.json')
        require(control['state']=='ACTIVE_DIRECT_USER_CONTINUATION' and control['automatic_resume'] is False,'Fresh direct authority absent')
        resources=api.resources([ROOT,WORK]); policy=config['resource_policy']
        require(resources['physical_available_bytes']>=policy['windows_reserve_bytes']+policy['incremental_windows_requirement_bytes']
                and resources['commit_headroom_bytes']>=policy['commit_requirement_bytes']
                and all(v>=policy['minimum_disk_free_bytes'] for v in resources['disk_available_bytes'].values()),
                'Actual first-genome Windows admission insufficient; config not created')
        require(sha(request_path)==args.request_sha256 and all(sha(WORK/n)==p for n,p in PINS.items())
                and all(sha(gates[n][0])==s['sha256'] and sha(gates[n][0].parent/'lock_released.json')==s['unlock_sha256']
                        for n,s in request['gates'].items())
                and sha(runtime_path)==request['runtime_manifest']['sha256']
                and sha(storage_path)==request['storage_proof']['sha256'],'Build controls drifted')
        with output.open('x',encoding='utf-8',newline='\n') as stream: json.dump(config,stream,indent=2);stream.write('\n')
        S.load_config(output)
        value={'schema':'STAGE05_FIRST_GENOME_CONFIG_BUILD_V1','state':'PASS_CONFIG_AND_WINDOWS_ADMISSION_ONLY',
               'config_path':str(output),'config_sha256':sha(output),'request_sha256':sha(request_path),
               'resource_basis':request['resource_basis'],'actual_windows_resources':resources,'workflow_lock':lock.identity,
               'gate_pins':request['gates'],'runtime_manifest':request['runtime_manifest'],'storage_proof':request['storage_proof'],
               'source_sha256':sha(__file__),'source_pins':PINS,'linux_fresh_admission':'REQUIRED_AT_NATIVE_RUN',
               'actual_detector_peak':'UNMEASURED_FIRST_APPROVED_GENOME_REQUIRED','scientific_execution':'NOT_RUN'}
    value['explicit_original_byte_unlock']=lock.released
    with receipt.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'config':str(output),'config_sha256':value['config_sha256'],'receipt':str(receipt)}))
    return 0


if __name__=='__main__': raise SystemExit(main())
