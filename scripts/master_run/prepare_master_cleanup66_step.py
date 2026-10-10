"""Publish exact failed-probe cleanup including raw sentinel bytes and live wait observation."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    name='master_cleanup66';mapping=W/'stage5_unc03_cleanup_actual01_publication01/PUBLIC_MAPPING.json'
    assert sha(mapping)=='125f800f9b0cdc9d935fb3ecb8fca2f96a368ea1e3be41466669416d8c6d0587'
    extras=[Path(__file__).name+'=scripts/master_run/'+Path(__file__).name,'master_closedcapacity65_remote_readback.json=reports/master_run/20261009/publication/master_closedcapacity65_remote_readback.json']
    binary=[]
    for r in json.loads(mapping.read_bytes())['files']:
        p=Path(r.get('local_path',r.get('path'))).resolve();assert p.is_relative_to(W) and sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
        target=r.get('repository_path',r.get('suggested_repository_path'));assert target
        if r.get('requires_explicit_binary_plan_row'):binary.append({'local_absolute_path':str(p),'target':target,'bytes':r['bytes'],'sha256':r['sha256'],'transport_encoding':'base64'})
        else:extras.append(p.relative_to(W).as_posix()+'='+target)
    assert len(binary)==1 and binary[0]['bytes']==116
    extras.append(mapping.relative_to(W).as_posix()+'=reports/master_run/20261009/preparation/actual_cleanup_PUBLIC_MAPPING.json')
    native=Path(r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1\GCF_000009425.1')
    obs=W/'stage5_capacity02_presearch_observation01';obs.mkdir()
    rows=[]
    for p,label in [(native/'transactions/attempt_0002/latest_admission.json','initial_admission.json'),(native/'execution/assemblies/GCF_000009425.1/padloc/hmm_attempt_0001/latest_admission.json','presearch_admission.json'),(native/'scientific_identity.json','scientific_identity.json'),(native/'bundle/assemblies/GCF_000009425.1/detector_task_manifest.json','detector_task_manifest.json'),(Path(r'\\wsl.localhost\Ubuntu\proc\meminfo'),'linux_meminfo.txt'),(W/'stage5_owner_GCF_000009425_1_backing_capacity_02/GCF_000009425.1.launch.json','windows_launch.json')]:
        if not p.is_file():continue
        raw=p.read_bytes();q=obs/label
        with q.open('xb') as stream:stream.write(raw)
        rows.append({'source':str(p),'file':label,'sha256':sha(q),'bytes':len(raw)})
        extras.append(q.relative_to(W).as_posix()+'=reports/master_run/20261009/'+obs.name+'/'+label)
    assert json.loads((obs/'initial_admission.json').read_bytes())['admitted'] is True
    value={'state':'OBSERVED_INITIAL_ADMISSION_AND_PREPARATION_NO_ACCEPTED_NATIVE_RESULT','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_terminal_claim':False,'owned_closure_claim':False,'biological_result_claim':'NONE','source_sha256':sha(Path(__file__)),'files':rows}
    (obs/'observation.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');extras.append(obs.name+'/observation.json=reports/master_run/20261009/'+obs.name+'/observation.json')
    patch={'stage5_unc03_exact_cleanup':'PASS_ACTUAL_EXACT_TWO_OBJECT_CLEANUP_RETAINED_WORKER_EMPTY_JOB_ORIGINAL_UNLOCK_PUBLIC_RAW116B_BACKUP',
      'stage5_unc_failed03_history':'FAILED_CANONICAL_UNC03_PRESERVED; EXACT_SENTINEL_BACKUP_AND_CLEANUP_COMPLETE',
      'stage5_unc03_cleanup_source':'PASS_V2_SOURCE_AND_ACTUAL_CLEANUP_PEER',
      'stage5_first_full_method_genome':'CAPACITY02_INITIAL_ADMISSION_PASS_BUNDLE_PREPARED_FIRST_NATIVE_RESOURCE_WAIT_NO_ACCEPTED_RAW'}
    paragraph='Stage5 current execution: capacity02 passed initial Linux admission, validated inputs/runtime and prepared the first genome bundle. The first full PADLOC search is at repeated admission: prep filesystem cache increased host memory/commit pressure, and no accepted native result exists. WSL dropCache reclamation is being observed; no further booking reduction is planned. Failed03 exact116B sentinel backup and two-object cleanup are complete and independently checked: retained workerexit0, empty named Windows Job, original checked unlock and no WSL launch. Its raw backup and metadata are published together. The failed original probe remains failed. Waiting01 natural DEFERRED_RESOURCE and failed cancellation control remain preserved. Accepted Stage4 is unchanged; raw196, curation784, final figures and VM recovery remain incomplete.\n'
    for suffix,val in [('extras.json',extras),('patch.json',patch)]: (W/(name+'_'+suffix)).write_text(json.dumps(val,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,'--head','070908a09ff9cbf1a6b77302d044a7446a60408a','--previous','master_closedcapacity65','--phase','Verify exact failed-probe cleanup and record capacity02 prepared native admission wait','--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json'],check=True)
    p=W/(name+'_git_plan.json');plan=json.loads(p.read_bytes());plan['files']+=binary
    assert len(plan['files'])==len({r['target'] for r in plan['files']})
    p.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(plan['files']),'binary_backup':binary}))
if __name__=='__main__':main()
