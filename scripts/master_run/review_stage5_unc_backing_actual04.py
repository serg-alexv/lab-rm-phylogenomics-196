"""Dedicated C-only exact closed backing UNC04 reviewer; original generic unchanged."""
from pathlib import Path
import argparse, datetime, hashlib, json
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
SOURCE='779502c38c5db06b68e796abc6e1bd99db72d8f97b1129f9057a3f6b0c4221d5'
BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
ROOT='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196'
TARGET=ROOT+'/.work/stage05_atomic_v1'
UNC=r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1'
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827','stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e','stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--spool',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--publication-readback',type=Path,required=True);parser.add_argument('--publication-commit',required=True);args=parser.parse_args()
    d=args.spool;out=args.output;R.require(d==W/'stage5_unc_backing_actual_postiq_04' and out.parent==W and not out.exists(),'Exact closed backing04/fresh C review required')
    report={'schema':'STAGE05_BACKING_UNC04_ACTUAL_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_READBACK','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only decoded source/config/request/native phase/retained lifecycle bytes; no producer imports, UNC, WSL, registry, original lock, process effect, network or Git mutation','scientific_adoption':False,'old_canonical_UNC03':'PRESERVED_FAILED'}
    try:
        R.require(R.sha(W/'review_stage5_postboot_gate.py')=='d6f06b442c2a8be35bb4779355c99d61e9de72314215c02e3165c2dfd235a161','Original common reviewer changed')
        R.require(R.sha(W/'stage5_unc_backing_probe.py')==SOURCE,'New backing probe source differs')
        for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Exact unchanged source dependency differs')
        peer=R.pinned(W/'stage5_backing_transport_source_independent_review01.json','77a134cc2402eb6788a9072aa0a2b082d44e167a899051e7205653b27d6a4497');R.require(peer['state']=='PASS_TWO_FIXED_BACKING_TRANSPORT_SUBSTITUTIONS_SOURCE_ONLY','Source peer differs')
        pub=R.read(args.publication_readback);R.require(pub['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and pub['expected_commit']==args.publication_commit and pub['verified_files']==pub['required_files'],'Selected source publication incomplete/different')
        rows=[row for row in pub['files'] if row['path'].endswith('/stage5_unc_backing_probe.py')];R.require(len(rows)==1 and rows[0]['sha256']==SOURCE and rows[0]['actual_remote_bytes_read'] is True and rows[0]['sha256_verified'] is True,'Exact new probe source absent from verified publication')
        v=R.read(d/'result.json');unlock=R.read(d/'lock_released.json')
        R.require(v['schema']=='STAGE05_EXACT_BIND_UNC_VISIBILITY_V1' and v['state']=='PASS_NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY' and v['source_sha256']==SOURCE and v['source_pins']==PINS and v['scientific_adoption_authorized'] is False and v['exact_owned_cleanup'] is True,'Actual backing gate source/state/cleanup differs')
        R.lock(v['workflow_lock']);q=R.pinned(d/'request.json',v['request_sha256']);R.lock(q['workflow_lock'])
        R.require(q['script_sha256']==SOURCE and q['source_pins']==PINS and q['scope']==v['scope']=='NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY_ONLY' and q['root']==ROOT and q['target']==TARGET and q['unc']==UNC and q['sentinel_name']=='.unc_visibility_'+q['nonce'] and q['actual_windows_owner']==v['actual_windows_owner'],'Exact canonical/bind/backing request/source/owner differs')
        cfg=R.pinned(R.cpath(q['config_linux_path']),q['config_sha256']);R.require(q['config_sha256']==v['config_sha256'] and cfg['root']==ROOT and cfg['output_root']==TARGET,'Pinned actual config differs')
        for relative,pin in v['files'].items():R.require(Path(relative).name==relative and R.sha(d/relative)==pin,'Closed exact evidence leaf byte pin differs')
        p=R.read(d/'prepared.json');io=R.read(d/'windows_io.json');f=R.read(d/'final.json')
        R.require(p['state']=='PASS_LINUX_SENTINEL_PREPARED' and io['state']=='PASS_WINDOWS_UNC_WRITE_FSYNC_READ' and f['state']=='PASS_LINUX_UNC_READBACK_AND_EXACT_CLEANUP' and f['exact_owned_sentinel_cleanup'] is True,'Complete three-phase source states/cleanup differ')
        for value in (p,io,f):R.require(value['script_sha256']==SOURCE and value['request_sha256']==v['request_sha256'] and value['scope']==v['scope'],'Three-phase source/request/scope binding differs')
        R.require(p['nonce']==f['nonce']==q['nonce'] and p['child_processes_spawned']==f['child_processes_spawned']==0 and type(p['child_processes_spawned']) is int and type(f['child_processes_spawned']) is int,'Linux nonce/zero-child accounting differs')
        proof=f['storage_after'];R.require(p['storage_before']==p['storage_after']==f['storage_before']==proof and proof['boot_id']==BOOT and proof['canonical_root']==ROOT and proof['canonical_target']==TARGET and proof['backing']=='/var/tmp/lab_rm_stage05_atomic_v1' and proof['target_mount']['filesystem']=='ext4' and proof['target_mount']['mountpoint']==TARGET and proof['target_mount']['root']==proof['backing'],'Current canonical/backing ext4 same-object storage differs')
        storage=R.pinned(R.cpath(proof['proof_path']),proof['proof_sha256']);R.require(all(proof[k]==value for k,value in storage.items()) and cfg['work_storage']['proof_path']==proof['proof_path'] and cfg['work_storage']['proof_sha256']==proof['proof_sha256'],'Selected current storage proof bytes differ')
        R.require(proof['proof_path'].endswith('/stage5_storage_actual_postiq_06.json') and proof['proof_sha256']=='b69bd39fe4489cce639cc062633aafe749c4a26b8072d9fc28f7e0860cafb1f0','Fresh storage06 selection differs')
        R.require(p['directory_device']==proof['directory_device'] and p['linux_file']==f['files']['linux.bin'],'Original exact Linux sentinel inode/content changed')
        for leaf,key,win_key in (('linux.bin','linux_payload_hex','linux_file'),('windows.bin','windows_payload_hex','windows_file')):
            payload=bytes.fromhex(q[key]);expected=hashlib.sha256(payload).hexdigest();native=f['files'][leaf];windows=io[win_key]
            R.require(64<=len(payload)<=512 and native['bytes']==windows['bytes']==len(payload) and native['sha256']==windows['sha256']==expected and native['device']==proof['directory_device'] and native['inode']==windows['inode'],'Bidirectional exact payload/native device/inode join differs')
        R.require(v['windows_g_underlay_before']==v['windows_g_underlay_after'] and v['windows_g_underlay_before']['entries']==[],'Covered Windows G underlay changed')
        R.require([value['phase'] for value in v['steps']]==['linux-prepare','windows-io','linux-finalize'],'Actual phase order differs')
        boot=R.pinned(W/'master_newboot_reconciliation_actual01.json','07a6546d3100bd979884b5a1e4d0c44952a4fc3cdd5a020087d4bbbc5e6d8cf3');stamp=datetime.datetime.fromisoformat(boot['current_boot']['last_boot_utc']);ft=int((stamp-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10_000_000)
        first,job,last=v['steps'];R.windows_job(d/'windows_io_worker',{k:value for k,value in job.items() if k!='phase'},ft,SOURCE,PINS['atomic_iqtree_windows.py'])
        for step,mode in ((first,'linux-prepare'),(last,'linux-finalize')):
            R.terminal(step['birth'],step['exit'],ft)
            argv=step['argv'];R.require(argv[:8]==[R.WSL,'-d','Ubuntu','-u','root','--exec',q['expected_python'],'-B'] and argv[8].endswith('/stage5_unc_backing_probe.py') and argv[argv.index('--mode')+1]==mode and argv[argv.index('--request-sha256')+1]==v['request_sha256'],'Retained exact Linux phase command differs')
        R.require(job['owner']==v['actual_windows_owner'] and job['argv']==[R.PYTHON,'-B',str(W/'stage5_unc_backing_probe.py'),'--mode','windows-io','--request',str(d/'request.json'),'--request-sha256',v['request_sha256'],'--run'],'Retained exact Windows worker command/owner differs')
        R.require(first['exit']['exit_filetime']<job['birth']['creation_filetime']<job['exit']['exit_filetime']<last['birth']['creation_filetime'],'Actual serial retained phase ordering differs')
        R.require(unlock['state']=='EXPLICIT_ORIGINAL_OS_BYTE_UNLOCK' and unlock['released'] is True and unlock['scientific_adoption_authorized'] is False,'Original explicit unlock differs')
        R.require(v['resources']['physical_available_bytes']>=1879048192 and v['resources']['commit_headroom_bytes']>=1879048192 and all(n>=16*1024**2 for n in v['resources']['disk_available_bytes'].values()),'Unchanged bounded probe resource admission differs')
        stop=Path(v['workflow_lock']['path']).parent/'stage05_owned_closure_unproven.json';point=datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:stop.lstat()
        except FileNotFoundError:absent=True
        else:absent=False
        R.require(absent,'Current STOP present; root reconciliation required')
        for path in sorted(d.rglob('*')):
            if path.is_file():R.data(path)
        report.update(state='PASS_CURRENT_BOOT_BACKING_UNC04_THREE_PHASE_BYTES_CLOSURE_AND_EXACT_CLEANUP',source_sha256=SOURCE,source_publication_commit=args.publication_commit,actual_result_sha256=R.sha(d/'result.json'),original_unlock_sha256=R.sha(d/'lock_released.json'),request_sha256=v['request_sha256'],linux_boot_id=BOOT,current_storage_proof_sha256=proof['proof_sha256'],canonical_scientific_target=TARGET,fixed_windows_transport=UNC,actual_three_retained_phases_exit0=True,windows_named_job_empty=True,linux_steps_spawned_children=0,bidirectional_payload_hashes={name:row['sha256'] for name,row in f['files'].items()},exact_two_leaf_and_directory_cleanup=True,windows_G_underlay_unchanged=True,owned_scope_closed=True,original_lock_explicitly_released=True,current_STOP_observation={'utc':point,'exists':False,'scope':'POINT_IN_TIME_ONLY'},transport_qualification='Actual current ext4 canonical bind is qualified through its fixed native-backing Windows UNC alias; this does not make old canonical UNC03 pass or prove arbitrary UNC traversal.',scientific_admission_requirement='Separate actual first-request/config build, exact new owner/source binding, current resource/authority/native ownership admission and approved full method remain required.')
    except BaseException as error:report['error']={'kind':type(error).__name__,'message':str(error)}
    report['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':report['state'],'error':report.get('error'),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checked_files':len(R.CHECKED)}))
    return 0 if report['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
