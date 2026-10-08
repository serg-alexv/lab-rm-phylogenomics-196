"""One WD owner for four unchanged frozen analyses using official Windows IQ-TREE.

Resumable IQ-TREE checkpoints; native processes always inside the queried job.
Original Linux sources/receipts and already completed alignments are read-only.
"""
from pathlib import Path
import argparse, csv, hashlib, json, os, re, socket, subprocess, time
import stage04_controller as C
import stage04_windows_job_v6 as J
import stage04_windows_validate_v6 as V
import production_resume as w
from workflow_publication import commit

ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=ROOT/'.work/stage04_inference_windows_v6'
TOOL=HISTORY/'.tools/iqtree_windows_3_1_4'
EXE=TOOL/'extracted/iqtree-3.1.4-Windows/bin/iqtree3.exe'
REPORT=ROOT/'reports/stage04/native_windows_v6'
CONFIG=ROOT/'config/host_inference_stage04_windows_v6.json'
SOURCES=['scripts/stage04_native_windows_v6.py','scripts/stage04_windows_job_v6.py','scripts/stage04_windows_validate_v6.py','config/host_inference_stage04_windows_v6.json']
PUBLIC=['STATUS.md','status/stages.tsv','status/stage04_execution.json','reports/stage04/native_windows_v6/progress.json']

def publish(paths,message):
    head=commit(paths,message);C.command(ROOT,['git','fetch','origin','main'])
    for name in paths:
        p=ROOT/name
        for f in ([p] if p.is_file() else [f for f in p.rglob('*') if f.is_file()]):
            rel=f.relative_to(ROOT).as_posix()
            b=subprocess.run(['git','show','origin/main:'+rel],cwd=ROOT,capture_output=True,check=True).stdout
            C.check(hashlib.sha256(b).hexdigest()==C.digest(f),'Remote byte verification failed: '+rel)
    print('REMOTE_BYTES_VERIFIED '+head,flush=True);return head

def tool_identity():
    config=C.load(CONFIG);archive=TOOL/config['official_archive_name']
    C.check(archive.stat().st_size==config['official_archive_bytes'] and C.digest(archive)==config['official_archive_sha256'] and C.digest(EXE)==config['official_executable_sha256'],'Official native archive/executable hash differs')
    import zipfile
    with zipfile.ZipFile(archive) as z:
        dll=EXE.parent/'libiomp5md.dll'
        C.check(hashlib.sha256(z.read('iqtree-3.1.4-Windows/bin/libiomp5md.dll')).hexdigest()==C.digest(dll),'Official native OpenMP DLL differs')
    return {'official_release_url':'https://github.com/iqtree/iqtree3/releases/tag/v3.1.4','official_archive_sha256':C.digest(archive),'official_archive_bytes':archive.stat().st_size,'executable_sha256':C.digest(EXE),'openmp_dll_sha256':C.digest(dll),'version':'3.1.4','platform':'Windows64'}

def policy():
    cfg=C.load(CONFIG)
    fixed={'approved_assemblies':196,'analysis_names':V.NAMES,'partition_option':'-p','model_selection':'MFP_WITHOUT_MERGING','ultrafast_bootstrap_replicates':1000,'sh_alrt_replicates':1000,'seed':1961008,'threads':2,'root_policy':'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP','alignment_reexecution':False,'windows_available_minimum_bytes':4831838208,'windows_reserve_bytes':1073741824,'process_committed_memory_cap_bytes':3221225472,'aggregate_job_committed_memory_cap_bytes':3221225472,'memory_kind':'WINDOWS_COMMITTED_MEMORY_NOT_LINUX_RLIMIT_AS','native_memory_option':'OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS'}
    C.check(all(cfg[k]==v for k,v in fixed.items()),'Fixed scientific/platform contract changed')
    return cfg

def adoption():
    path=REPORT/'adoption.json';review=C.load(ROOT/'reports/stage04/native_windows_v6_review/review.json')
    C.check(review['status']=='PASS_ACTUAL_WINDOWS_JOB_ASSIGN_BEFORE_RESUME_QUERYBACK_MEMORY_DENIAL_AND_AFFINITY' and review['biological_jobs_run']==0 and review['helper_sha256']==C.digest(ROOT/'scripts/stage04_windows_job_v6.py') and review['test_source_sha256']==C.digest(ROOT/'scripts/test_stage04_windows_job_v6.py'),'Actual Windows control validation missing/changed')
    source=V.source_gate();cfg=policy();tool=tool_identity()
    identity={'source_identity':source,'tool_identity':tool,'config_sha256':C.digest(CONFIG),'code_sha256':{p:C.digest(ROOT/p) for p in SOURCES},'actual_windows_control_review_sha256':C.digest(ROOT/'reports/stage04/native_windows_v6_review/review.json')}
    if path.exists():
        existing=C.load(path);C.check(existing['identity']==identity,'Adopted platform/source identity changed');return existing
    value={'utc':C.now(),'status':'REVIEWED_NATIVE_WINDOWS_V6_ADOPTED_BEFORE_TOPOLOGY','actual_pid':os.getpid(),'identity':identity,'scientific_inference':'NOT_RUN_AT_ADOPTION','original_v1_v4_sources_preserved':True,'v5_candidate':'PRESERVED_NOT_ADOPTED','alignment_reexecution':False,'shared_workflow_lock':'historical:.work/workflow.lock','data_root':str(ROOT),'historical_tools_root':str(HISTORY),'resume_command':[str(HISTORY/'.tools/validation_env/Scripts/python.exe'),'-u','scripts/stage04_native_windows_v6.py','--run'],'resume_cwd':str(ROOT)}
    C.atomic(path,value)
    method=ROOT/'reports/stage04/INFERENCE_WINDOWS_V6.md'
    method.write_text('# Native Windows inference revision V6\n\nActual WSL resource probes and a bounded60-second settling diagnostic never passed the Windows admission gate. All raw measurements and historical Linux allocation failures remain retained. The direct human repair authorization permits this explicit platform adapter. The official IQ-TREE3.1.4 Windows archive and executable were downloaded and hash verified; actual installed help/version and two executed Windows control fixtures are preserved. The first fixture attempt exposed asynchronous job accounting after process exit; the adapter now queries actual job active-process counts for at most5seconds and rejects any remaining descendants. No biological computation was used for these tests.\n\nThe four accepted primary196, sensitivity162, high-occupancy88-marker196 and high-contiguity155 matrices/partitions are reused byte for byte. ModelFinder MFP with -p partitions without merging;1000 UFBoot,1000 SH-aLRT, seed1961008, -T2, -keep-ident, --boot-trees, explicitly unrooted. Unsupported --mem is omitted. Source certificates, copied input hashes and all27 historical adopted source hashes are checked without rerunning HMM/MAFFT/trimAl work.\n\nWindows fresh physical available-memory admission remains4.5GiB before each native launch;1GiB stated reserve, not a continuous guarantee. The child starts suspended, receives an actual queried-back Windows JobObject before resumption, with3GiB per-process and aggregate job committed-memory caps and affinity restricted to two logical processors. These are Windows committed-memory caps, not Linux RLIMIT_AS. No WSL/Linux gate applies to native inference. Record actual process/job PID and creation tokens, wall/CPU, working-set peaks and committed-memory peaks. Existing Linux environments, sources, argv and failures remain unchanged; new native output identities bind actual G paths and C tools/runtime lock.\n\nIndependent native output validation and portable Release/hash readback remain separate from exit codes and adoption. Prediction/figure stages remain NOT_RUN until actual evidence.\n',encoding='utf-8')
    w.status('4_phylogeny','NATIVE_WINDOWS_V6_ADOPTED_INFERENCE_NOT_STARTED','PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE','STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING','Official Windows IQ-TREE3.1.4 and actual Windows job memory/affinity controls validated. Four accepted inputs reused; new Windows platform contract frozen. Linux failures and unadopted V5 evidence retained. Fresh4.5GiB Windows gate required before actual native launch.')
    publish(SOURCES+['scripts/test_stage04_windows_job_v6.py','reports/stage04/native_windows_v6_review','reports/stage04/native_windows_v6/adoption.json','reports/stage04/INFERENCE_WINDOWS_V6.md','STATUS.md','status/stages.tsv'],'Adopt tested native Windows IQ-TREE adapter with unchanged full196 scientific protocol')
    return value

def verify_remote(adopted):
    C.reconcile(ROOT)
    for rel in [*SOURCES,'reports/stage04/native_windows_v6/adoption.json']:
        remote=subprocess.run(['git','show','origin/main:'+rel],cwd=ROOT,capture_output=True,check=True).stdout
        C.check(hashlib.sha256(remote).hexdigest()==C.digest(ROOT/rel),'Canonical native source/adoption differs: '+rel)
    C.check({p:C.digest(ROOT/p) for p in SOURCES}==adopted['identity']['code_sha256'],'Pinned adopted source bytes changed')

def progress(name,state,row=None,failure=None):
    value={'utc':C.now(),'execution':state,'analysis':name,'actual_controller_pid':os.getpid(),'actual_native_process_measurements':row,'platform':'NATIVE_WINDOWS_IQTREE3_1_4','full_stage04':'INCOMPLETE','scientific_validation':'INCOMPLETE','github_publication':'PROGRESS_ONLY_FULL_RELEASE_PENDING','failure':failure,'outputs_preserved':True}
    C.atomic(REPORT/'progress.json',value);C.atomic(ROOT/'status/stage04_execution.json',value)
    w.status('4_phylogeny',state,'PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE','STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING','Native Windows IQ-TREE3.1.4 analysis '+str(name)+': '+state+'. Same four frozen matrices/partitions, MFP,1000 UFBoot/SH-aLRT, seed1961008, two threads. Actual process/job measurements attached; independent final validation and verified portable publication pending.'+(' Blocker: '+failure if failure else ''))
    publish(PUBLIC,'Record actual native Windows full196 inference progress')

def admission(directory):
    cfg=policy();first=C.windows_snapshot(ROOT,pid=os.getpid());second=C.windows_snapshot(ROOT,pid=os.getpid());disk=C.windows_snapshot(HISTORY)
    receipt={'utc':C.now(),'windows_before_launch_first':first,'windows_before_launch_second':second,'tool_disk':disk,'required_windows_available_bytes':cfg['windows_available_minimum_bytes'],'process_committed_memory_cap_bytes':cfg['process_committed_memory_cap_bytes'],'aggregate_job_committed_memory_cap_bytes':cfg['aggregate_job_committed_memory_cap_bytes'],'reserve_bytes':cfg['windows_reserve_bytes'],'linux_measurement':'NOT_APPLICABLE_NATIVE_WINDOWS','admission_passed':min(first['available_bytes'],second['available_bytes'])>=cfg['windows_available_minimum_bytes'] and min(first['disk_available_bytes'],second['disk_available_bytes'],disk['disk_available_bytes'])>5*1024**3}
    C.atomic(directory,receipt);C.check(receipt['admission_passed'],'Fresh native Windows headroom/disk admission failed; no scientific launch')
    return receipt

def exports(name):
    directory=OUT/'analyses'/name/'iqtree';text=(directory/'host.treefile').read_text().strip()
    (directory/'unrooted.nwk').write_bytes((directory/'host.treefile').read_bytes())
    (directory/'unrooted.nex').write_text('#NEXUS\nBEGIN TREES;\n TREE host = [&U] '+text+'\nEND;\n',encoding='utf-8')
    with (V.ALIGN/'analyses'/name/'tip_label_map.tsv').open(newline='',encoding='utf-8') as f:labels={r['assembly_accession']:r['tree_label'] for r in csv.DictReader(f,delimiter='\t')}
    seen=[]
    def replace(m):
        key=m.group();C.check(key in labels,'Foreign native tip');seen.append(key);return "'"+labels[key].replace("'","''")+"'"
    labeled=re.sub(r'(?<![A-Za-z0-9_.])GCF_[0-9]{9}\.[0-9]+(?![A-Za-z0-9_.])',replace,text)
    C.check(len(seen)==len(set(seen))==len(labels) and set(seen)==set(labels),'Labeled native tip join differs')
    (directory/'unrooted_labeled.nwk').write_text(labeled+'\n',encoding='utf-8')
    (directory/'unrooted_labeled.nex').write_text('#NEXUS\nBEGIN TREES;\n TREE host = [&U] '+labeled+'\nEND;\n',encoding='utf-8')

def run(adopted):
    verify_remote(adopted);OUT.mkdir(parents=True,exist_ok=True)
    frozen=OUT/'inference_freeze.json'
    value={**adopted['identity'],'executable':str(EXE),'adoption_sha256':C.digest(REPORT/'adoption.json'),'scientific_method':'Same frozen4scopes/MFP-p/UF1000/SH1000/seed1961008/T2; Windows platform change only','optional_concordance':'NOT_RUN','root_policy':'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP'}
    if frozen.exists():C.check(C.load(frozen)==value,'Native freeze identity changed')
    else:C.atomic(frozen,value)
    for name in V.NAMES:
        verify_remote(adopted);C.check(V.source_gate()==adopted['identity']['source_identity'] and tool_identity()==adopted['identity']['tool_identity'],'Current frozen scientific source/tool differs')
        directory=OUT/'analyses'/name/'iqtree';directory.mkdir(parents=True,exist_ok=True)
        if (directory/'tree_complete.json').exists():
            V.audit_analysis(name);print('EXISTING_VERIFIED_NATIVE_TREE '+name,flush=True);continue
        previous=sorted(directory.glob('attempt_*/launch.json'))
        for launch_path in previous:
            launch=C.load(launch_path);exit=launch_path.parent/'exit.json'
            C.check(exit.exists(),'Unfinished actual native attempt requires PID/creation reconciliation; duplicate launch blocked')
            C.check(C.load(exit)['exit_code']!=0,'Native exit0 without complete independent artifact proof requires recovery; duplicate computation blocked')
        index=len(previous)+1;attempt=directory/('attempt_'+str(index).zfill(4))
        C.check(not attempt.exists(),'Preserved native attempt path collision')
        admission(directory/('admission_'+str(index).zfill(4)+'.json'))
        argv=V.expected_argv(EXE,name)
        C.atomic(directory/'invocation.json',{'argv':argv,'inference_freeze_sha256':C.digest(frozen),'resumable_checkpoint':'host.ckp.gz','native_memory_option':'OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS'})
        next_publish=[0]
        def report(row):
            if time.monotonic()>=next_publish[0]:
                progress(name,'ACTUAL_NATIVE_WINDOWS_INFERENCE_RUNNING',row);next_publish[0]=time.monotonic()+300
            print('ACTUAL_NATIVE '+name+' PID='+str(row['child_pid'])+' WALL='+str(round(row['wall_seconds'],1))+' JOB_PEAK='+str(row['peak_job_committed_bytes']),flush=True)
        receipt=J.run_job(argv,ROOT,attempt,3221225472,on_progress=report)
        C.check(receipt['exit_code']==0,'Actual native IQ-TREE exit='+str(receipt['exit_code'])+'; preserve checkpoints, no scientific PASS')
        exports(name)
        files={p.relative_to(directory).as_posix():C.digest(p) for p in directory.rglob('*') if p.is_file() and p.name!='tree_complete.json'}
        proof={'execution':'NATIVE_OUTPUT_CONSTRUCTION_ONLY_INDEPENDENT_VALIDATION_REQUIRED','inference_freeze_sha256':C.digest(frozen),'attempt':attempt.name,'file_sha256':files,'actual_native_exit_sha256':C.digest(attempt/'exit.json')}
        C.atomic(directory/'tree_complete.json',proof)
        result=V.audit_analysis(name);C.atomic(REPORT/(name+'_independent_check.json'),result)
        progress(name,'NATIVE_ANALYSIS_COMPLETED_INDEPENDENT_OUTPUT_CHECK_PASSED',receipt)
    V.main()
    summary={'execution':'ALL_PRIMARY_AND_SENSITIVITY_INFERENCES_COMPLETED','inference_freeze_sha256':C.digest(frozen),'analyses':[C.load(REPORT/(n+'_independent_check.json')) for n in V.NAMES],'independent_final_validation_sha256':C.digest(ROOT/'.work/stage04_final_validation_windows_v6/validation_summary.json'),'publication':'FULL_PORTABLE_RELEASE_PENDING'}
    C.atomic(OUT/'phylogeny_summary.json',summary)
    progress('ALL4','ALL_NATIVE_WINDOWS_INFERENCES_INDEPENDENTLY_VALIDATED_RELEASE_PENDING')
    print('ALL4_NATIVE_WINDOWS_TREES_VALIDATED_PORTABLE_RELEASE_REQUIRED',flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    C.check(os.name=='nt' and socket.gethostname().lower()=='wd' and Path.cwd().resolve()==ROOT,'Dedicated WD G Windows owner required')
    with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
        C.reconcile(ROOT);C.atomic(HISTORY/'.work/workflow_owner.json',{'utc':C.now(),'pid':os.getpid(),'scope':'Native Windows V6 actual four ML trees; no aligner/detector duplicates','script':'data:scripts/stage04_native_windows_v6.py'})
        try:
            adopted=adoption()
            if args.run:run(adopted)
            else:print('NATIVE_PLATFORM_ADOPTED_REMOTE_BYTES_VERIFIED_NO_INFERENCE',flush=True)
        except Exception as error:
            C.atomic(REPORT/'failure.json',{'utc':C.now(),'actual_pid':os.getpid(),'error':str(error),'outputs_preserved':True,'scientific_validation':'INCOMPLETE'})
            try:progress(None,'STOPPED_NATIVE_WINDOWS_EXPLICIT_BLOCKER',failure=str(error))
            except Exception as publication_error:C.atomic(REPORT/'failure_publication_error.json',{'utc':C.now(),'error':str(publication_error)})
            raise

if __name__=='__main__':main()
