"""The actual long-lived Scheduler action; C-owned lifetime, serial full scopes.

Fixture mode exercises this controller and the same suspended-child job helper.
Production mode rejects missing/changed hash-bound parent review before a native
scientific launch. It never repairs V6 receipts or calls the old B2 gate as PASS.
"""
import argparse, csv, hashlib, json, os, re, shutil, sys, time
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v9 as S
import stage04_windows_job_v9 as J
import stage04_recovery_outbox_v9 as Q

PROPOSAL=S.ROOT/'config/host_inference_stage04_recovery_v9_freeze.json'
ACCEPTANCE=S.ROOT/'.work/host_review/PARENT_RECOVERY_V9_REVIEW.json'

def verify_artifacts(items):
    C.check(isinstance(items,dict) and items,'Empty adoption artifact map')
    for name,sha in items.items():
        role,rel=name.split(':',1);C.check(role in ('data','historical') and rel and not Path(rel).is_absolute() and '..' not in Path(rel).parts,'Invalid adoption path role')
        base=S.ROOT if role=='data' else S.HISTORY
        path=base/rel;C.check(path.resolve().is_relative_to(base.resolve()) and C.digest(path)==sha,'Adoption hash changed: '+name)

def acceptance():
    value=C.load(ACCEPTANCE);proposal=C.load(PROPOSAL)
    C.check(value.get('schema')=='PARENT_RECOVERY_V9_HASH_BOUND_ACCEPTANCE' and value.get('decision')=='ACCEPTED_FOR_SINGLE_PRODUCTION_START' and
      value.get('reviewer')=='INDEPENDENT_PARENT' and value.get('production_task_name')==proposal['production_task']['task_name'],
      'No structurally valid parent acceptance; production blocked')
    required={**proposal['required_review_artifacts'],'data:config/host_inference_stage04_recovery_v9_freeze.json':C.digest(PROPOSAL)}
    C.check(value.get('artifact_sha256')==required,'Parent acceptance must name exactly every adopted source/freeze/fixture artifact with actual hash')
    expected_outer={'decision':'ACCEPT_OBSERVED_SCHEDULER_BOUND_OUTER_JOB_LIFETIME','fixture_sha256':proposal['scheduler_fixture_sha256'],
      'production_task_definition_sha256':proposal['production_task']['definition_sha256'],
      'native_controls':'NESTED_OWNED_JOB_3GIB_MASK5_NO_BREAKAWAY','old_missing_closure':'REMAINS_UNKNOWN_NEGATIVE_HISTORY_ONLY'}
    C.check(value.get('outer_job_lifetime_review')==expected_outer,'Explicit hash-bound outer-job lifetime review missing/different')
    verify_artifacts(required);S.pins()
    negative=C.load(S.REPORT/'failed_attempt_reconciliation_v1.json')
    C.check(negative['ordinary_success_receipt'] is False and negative['original_job_closure']=='UNKNOWN' and
      negative['original_controller_outcome']=='UNKNOWN' and negative['actual_native_exit']['exit_code_dword']==1,
      'Negative history cannot become an ordinary successful receipt')
    return proposal,value

def exports(name):
    d=S.OUT/'analyses'/name/'iqtree';text=(d/'host.treefile').read_text().strip()
    (d/'unrooted.nwk').write_bytes((d/'host.treefile').read_bytes())
    (d/'unrooted.nex').write_text('#NEXUS\nBEGIN TREES;\n TREE host = [&U] '+text+'\nEND;\n',encoding='utf-8')
    with (S.ROOT/'.work/stage04_phylogeny_v2/analyses'/name/'tip_label_map.tsv').open(encoding='utf-8',newline='') as f:
        labels={r['assembly_accession']:r['tree_label'] for r in csv.DictReader(f,delimiter='\t')}
    seen=[]
    def replace(m):
        key=m.group();C.check(key in labels,'Foreign export tip');seen.append(key);return "'"+labels[key].replace("'","''")+"'"
    labeled=re.sub(r'(?<![A-Za-z0-9_.])GCF_[0-9]{9}\.[0-9]+(?![A-Za-z0-9_.])',replace,text)
    C.check(len(seen)==len(set(seen))==len(labels) and set(seen)==set(labels),'Export label join changed tips')
    (d/'unrooted_labeled.nwk').write_text(labeled+'\n',encoding='utf-8')
    (d/'unrooted_labeled.nex').write_text('#NEXUS\nBEGIN TREES;\n TREE host = [&U] '+labeled+'\nEND;\n',encoding='utf-8')

def admission(runtime):
    # Direct Win32 physical-memory measurement; no WSL boot or uncontained report subprocess.
    import ctypes as c
    from ctypes import wintypes as t
    class MEMORY(c.Structure):
        _fields_=[('length',t.DWORD),('load',t.DWORD)]+[(n,c.c_uint64) for n in ('total_phys','available_phys','total_page','available_page','total_virtual','available_virtual','extended')]
    f=S.J.bind(S.K,'GlobalMemoryStatusEx',t.BOOL,[c.POINTER(MEMORY)])
    samples=[]
    for _ in range(2):
        mem=MEMORY();mem.length=c.sizeof(mem);S.J.ok(f(c.byref(mem)),'Fresh Windows memory admission')
        samples.append({'utc':C.now(),'available_physical_bytes':mem.available_phys,'available_pagefile_bytes':mem.available_page})
        time.sleep(.15)
    disks={str(p):shutil.disk_usage(p).free for p in (S.ROOT,S.HISTORY)}
    receipt={'utc':C.now(),'samples':samples,'disk_free_bytes':disks,'minimum_windows_available_bytes':4831838208,
      'reserve_bytes':1073741824,'reserve_kind':'ADMISSION_ARITHMETIC_NOT_CONTINUOUS_ENFORCEMENT',
      'process_and_aggregate_job_committed_cap_bytes':3221225472,'linux_measurement':'NOT_APPLICABLE_NATIVE_WINDOWS',
      'passed':min(r['available_physical_bytes'] for r in samples)>=4831838208 and min(disks.values())>5*1024**3}
    C.atomic(runtime/'admission.json',receipt);C.check(receipt['passed'],'Fresh numeric Windows resource gate failed; no native launch')

def production(config,runtime,lock,isolation,topology):
    proposal,review=acceptance()
    C.check(config['mode']=='production' and config['analysis_names']==S.NAMES and config['threads']==2 and config['seed']==1961008,
      'Production configuration differs')
    C.check(not (runtime/'production_started.json').exists() and not S.OUT.exists(),'Unique V9 production attempt collision; no silent retry')
    # Reconcile/source checks run inside a bounded control job, with no biological duplication.
    control=J.run_job([str(S.VALIDATOR),str(S.ROOT/'scripts/stage04_recovery_validate_v9.py'),'--source-gate'],S.ROOT,
      runtime/'source_gate_process',cap_bytes=768*1024**2,deadline_seconds=180,role='INDEPENDENT_SOURCE_GATE')
    C.check(control['exit_code']==0,'Frozen source/canonical-main gate failed')
    C.atomic(runtime/'production_started.json',{'utc':C.now(),'parent_acceptance_sha256':C.digest(ACCEPTANCE),
      'proposal_sha256':C.digest(PROPOSAL),'controller':isolation['controller'],'shared_lock_identity':S.lock_identity(lock)})
    S.OUT.mkdir(parents=True,exist_ok=False)
    freeze={**C.load(S.OLD/'inference_freeze.json'),'recovery_protocol':'V9_NEGATIVE_HISTORY_PLUS_NEW_REAL_ORDINARY_CLOSURE',
      'old_freeze_sha256':S.FREEZE_SHA,'recovery_proposal_sha256':C.digest(PROPOSAL),'parent_acceptance_sha256':C.digest(ACCEPTANCE),
      'negative_history_certificate_sha256':C.digest(S.REPORT/'failed_attempt_reconciliation_v1.json'),
      'scheduler_isolation_sha256':C.digest(runtime/'isolation.json'),'stable_runtime':str(runtime)}
    C.atomic(S.OUT/'inference_freeze.json',freeze)
    for name in S.NAMES:
        verify_artifacts(proposal['required_review_artifacts']);S.pins()
        d=S.OUT/'analyses'/name/'iqtree';d.mkdir(parents=True,exist_ok=False)
        scope=runtime/'analyses'/name;scope.mkdir(parents=True,exist_ok=False)
        if name=='primary196':
            source=S.OLD/'analyses/primary196/iqtree/host.model.gz';shutil.copy2(source,d/'host.model.gz')
            C.check(C.digest(d/'host.model.gz')==S.CACHE_SHA,'Byte-identical cache copy failed')
            C.atomic(scope/'cache_import.json',{'utc':C.now(),'source_sha256':S.CACHE_SHA,'destination_sha256':C.digest(d/'host.model.gz'),
              'original_general_checkpoint':'ABSENT','redo':False,'reuse_observed':'PENDING_ACTUAL_NATIVE_OUTPUT','new_prefix':str(d/'host')})
        admission(scope)
        source=S.ROOT/'.work/stage04_phylogeny_v2/analyses'/name
        argv=[freeze['executable'],'-s',str(source/'concatenated.faa'),'--seqtype','AA','-p',str(source/'partitions.nex'),
          '-m','MFP','-B','1000','--alrt','1000','--seed','1961008','-T','2','-keep-ident','--boot-trees','--prefix',str(d/'host')]
        C.atomic(scope/'invocation.json',{'argv':argv,'freeze_sha256':C.digest(S.OUT/'inference_freeze.json')})
        shutil.copy2(scope/'invocation.json',d/'invocation.json')
        with Q.Outbox(runtime,name,fixture=False) as outbox:
            receipt=J.run_job(argv,S.ROOT,scope/'attempt_0001',offer=outbox.offer)
        C.check(receipt['exit_code']==0,'Actual native exit'+str(receipt['exit_code'])+'; preserve outputs, no scientific PASS')
        # Copy C ordinary receipts byte-for-byte only after actual exit/empty job. G errors now cannot close native science.
        attempt=d/'attempt_0001';shutil.copytree(scope/'attempt_0001',attempt)
        exports(name)
        files={p.relative_to(d).as_posix():C.digest(p) for p in d.rglob('*') if p.is_file() and p.name!='tree_complete.json'}
        C.atomic(d/'tree_complete.json',{'execution':'OUTPUT_CONSTRUCTION_ONLY_INDEPENDENT_VALIDATION_REQUIRED','attempt':'attempt_0001',
          'inference_freeze_sha256':C.digest(S.OUT/'inference_freeze.json'),'file_sha256':files,'actual_native_exit_sha256':C.digest(attempt/'exit.json')})
        checked=J.run_job([str(S.VALIDATOR),str(S.ROOT/'scripts/stage04_recovery_validate_v9.py'),'--analysis',name],S.ROOT,
          scope/'independent_checker_process',cap_bytes=768*1024**2,deadline_seconds=300,role='INDEPENDENT_SCIENTIFIC_CHECKER')
        C.check(checked['exit_code']==0,'Independent actual output validation failed')
    C.atomic(runtime/'all_scope_checks_complete.json',{'utc':C.now(),'status':'FOUR_ACTUAL_SCOPES_INDEPENDENTLY_VALIDATED_RELEASE_PENDING',
      'scientific_certificates':{n:C.digest(S.REPORT/(n+'_independent_check.json')) for n in S.NAMES}})

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args()
    config=C.load(a.config);runtime=Path(config['runtime']);mode=config['mode']
    C.check(runtime.is_relative_to(S.RUNTIME) and mode in ('fixture','production'),'Invalid controller role/runtime')
    C.check(not (runtime/'controller_closure.json').exists(),'Controller attempt already closed')
    runtime.mkdir(parents=True,exist_ok=True);code=1;scientific_jobs=0
    try:
        with C.WorkflowLock(S.LOCK) as lock:
            S.pins();iso=S.isolation(runtime);cpu=S.topology()
            C.atomic(runtime/'isolation.json',iso);C.atomic(runtime/'topology.json',cpu)
            if iso['is_process_in_job_null']:
                if mode=='fixture':
                    C.check(config.get('allow_fixture_scheduler_outer_job_observation') is True,
                      'Fixture observation of true outer job not explicitly enabled; no child')
                else:acceptance()
            # Bind the actual Scheduler instance, not merely a script-supplied task name.
            request=C.load(runtime/'task_request.json');started=C.load(runtime/'task_start.json')
            C.check(started['engine_pid']==iso['controller']['pid'] and started['task_name']==config['task_name'] and
              started['definition_sha256']==request['definition_sha256'],'Actual Scheduler engine/definition binding differs')
            C.atomic(runtime/'controller_binding.json',{'utc':C.now(),'controller':iso['controller'],'lock_identity':S.lock_identity(lock),
              'config_sha256':C.digest(a.config),'source_sha256':C.digest(__file__),'mode':mode,'runtime':str(runtime),
              'scheduler_task_name':config['task_name'],'scheduler_instance_guid':started['instance_guid'],
              'scheduler_definition_sha256':request['definition_sha256'],'controller_action_is_long_lived':True,
              'outer_job_acceptance':'FIXTURE_OBSERVATION_ONLY_PARENT_PRODUCTION_REVIEW_REQUIRED' if mode=='fixture' else 'HASH_BOUND_PARENT_RECORD_REQUIRED'})
            if mode=='fixture':
                with Q.Outbox(runtime,'SYNTHETIC',fixture=True) as outbox:
                    result=J.run_job([str(S.PYTHON),str(S.ROOT/'scripts/stage04_recovery_fixture_v9.py'),'--runtime',str(runtime)],
                      S.ROOT,runtime/'native_attempt',cap_bytes=128*1024**2,offer=outbox.offer,deadline_seconds=55,role='SYNTHETIC_FIXTURE')
                C.check(result['exit_code']==0,'Fixture native exit failed')
            else:
                production(config,runtime,lock,iso,cpu);scientific_jobs=4
            C.atomic(runtime/'controller_closure.json',{'utc':C.now(),'status':'ORDINARY_CONTROLLER_SCOPE_CLOSURE',
              'mode':mode,'controller':iso['controller'],'lock_identity':S.lock_identity(lock),'native_jobs_actual_empty':True,
              'scientific_jobs_completed':scientific_jobs,'publication':'SEPARATE_VERIFIED_RELEASE_REQUIRED'})
            code=0
    except BaseException as error:
        J.best_effort(runtime/'controller_exception.json',{'utc':C.now(),'kind':type(error).__name__,'message':str(error),
          'controller_pid':os.getpid(),'ordinary_controller_closure':'NOT_EMITTED','mode':mode})
    sys.exit(code)

if __name__=='__main__':main()
