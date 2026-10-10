"""Pure source peer of fixed backing first-request/config builder packet."""
from pathlib import Path
import copy, datetime, hashlib, json, subprocess, sys, tempfile
import review_stage5_postboot_gate as R
import stage5_build_backing_actual_config as B
import prepare_stage5_first_backing_actual_request as M
import stage5_atomic as S

W=Path(__file__).resolve().parent
PINS={'stage5_build_backing_actual_config.py':'e1b7b4782be7cb4faa84cf546884075e860d2d010a1774ba7d61846bfff7905c','prepare_stage5_first_backing_actual_request.py':'aed494a55de00bf719ce0827f4e45c66b2079203dd046bb49243e805b066c44a','test_stage5_build_backing_actual_config.py':'b6d2ad80523a32cb259870c6615b2660c3bb30257a4c4d26e4e9148d269f3878','test_prepare_stage5_first_backing_actual_request.py':'30d065ad2cc864c09ff50c127d49567e823eae7a70cebbd1285c6fa75e543816','stage5_first_backing_actual_config_METHODS.md':'28a00eb22178d171278c5b56e92b09c9a898e8f7e917a2fb628fca172d94bd4d','stage5_first_backing_actual_config_preparation01.json':'3f8474067a919e1b19a75712764c29dda5953fd0cfafc324d7d12489c25cd192','stage5_build_actual_config.py':'15dd2d4de4646d154ebfe503ae91f765d15f9f3cbd9e75099fbbfe703ffa2daa','prepare_stage5_first_actual_request_v3.py':'cf49f22430a0bfa435491c25ac73494b253acae53aac2ff3b8b910d4a65eaa09'}

def main():
    out=W/'stage5_first_backing_actual_config_source_independent_review01.json';R.require(not out.exists(),'Fresh builder/request peer required')
    result={'schema':'STAGE05_FIRST_BACKING_CONFIG_SOURCE_INDEPENDENT_V1','state':'FAILED_SOURCE_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only source byte/diff checks, bounded pure synthetic tests/default NOOPs and synthetic temporary-C config parse. No actual gate/candidate/request/config creation, G/UNC, WSL, WorkflowLock, registry, process effects or Git action.','scientific_adoption':False,'actual_backing_UNC04':'NOT_RUN'}
    try:
        for name,pin in {**PINS,**B.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen source/helper/history differs: '+name)
        prep=R.read(W/'stage5_first_backing_actual_config_preparation01.json')
        for name,row in prep['source_pins'].items():R.require(R.sha(W/name)==row['sha256'] and len(R.data(W/name))==row['bytes'],'Preparation member differs: '+name)
        old=R.data(W/'stage5_build_actual_config.py');new=R.data(W/'stage5_build_backing_actual_config.py')
        rules=[(b"'stage5_windows_owner.py'",b"'stage5_windows_backing_owner.py'"),(b'8851bc4fc48ad3069d4ffabe410e159004ef4fc8d6d0755213fc14c22fe0603d',b'296492aa4205f64058846b9901a7bb3a3458f99eda1c7ff388a6e33cdc38b834'),(b"'stage5_unc_bind_probe.py'",b"'stage5_unc_backing_probe.py'"),(b'0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d',b'779502c38c5db06b68e796abc6e1bd99db72d8f97b1129f9057a3f6b0c4221d5'),(b"result['resource_policy']['resource_wait_seconds']=0",b"result['resource_policy']['resource_wait_seconds']=1800")]
        restored=new
        for before,after in rules:R.require(after in restored,'Expected minimal rule absent');restored=restored.replace(after,before)
        R.require(restored==old,'Builder differs beyond five fixed replacement rules')
        old_request=R.data(W/'prepare_stage5_first_actual_request_v3.py');new_request=R.data(W/'prepare_stage5_first_backing_actual_request.py')
        R.require(new_request.count(b'stage5_unc_backing_actual_postiq_04')==1 and new_request.replace(b'stage5_unc_backing_actual_postiq_04',b'stage5_unc_bind_actual_postiq_03')==old_request,'Request differs beyond one UNC04 route')
        checks=[]
        for name,count in (('test_stage5_build_backing_actual_config.py',8),('test_prepare_stage5_first_backing_actual_request.py',7),('stage5_build_backing_actual_config.py',0),('prepare_stage5_first_backing_actual_request.py',0)):
            p=subprocess.run([sys.executable,'-B',str(W/name)],cwd=W,capture_output=True,text=True,timeout=30)
            R.require(p.returncode==0,'Pure test/default NOOP failed: '+name+' '+p.stderr[-3000:])
            if count:R.require('Ran '+str(count)+' tests' in p.stderr,'Focused test count differs')
            else:R.require(json.loads(p.stdout)['state']=='PREPARED_NOT_RUN','CLI default NOOP differs')
            checks.append({'name':name,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        template=R.read(W/'stage5_atomic_config.template.json');before=copy.deepcopy(template)
        request={'schema':'STAGE05_ACTUAL_CONFIG_REQUEST_V1','purpose':'FIRST_APPROVED_GENOME_RESOURCE_MEASUREMENT','native_resource_bytes':copy.deepcopy(M.NATIVE_RESOURCE_BYTES),'resource_basis':M.RESOURCE_BASIS}
        policy=B.explicit_policy(template,request);R.require(template==before and policy['support_source_sha256']==before['support_source_sha256'] and policy['resource_policy']['resource_wait_seconds']==1800,'Synthetic native policy mutated template/method or finite wait differs')
        with tempfile.TemporaryDirectory(prefix='peer_backing_config_pure_',dir=W) as temp:
            path=Path(temp)/'synthetic_config.json';path.write_text(json.dumps(policy),encoding='utf-8');R.require(S.load_config(path)==policy,'Unchanged scientific parser rejected synthetic explicit finite policy')
        R.require(M.NATIVE_RESOURCE_BYTES==prep['native_resource_bytes_unchanged'] and M.GATES['unc']=='stage5_unc_backing_actual_postiq_04' and B.PINS['stage5_unc_backing_probe.py']=='779502c38c5db06b68e796abc6e1bd99db72d8f97b1129f9057a3f6b0c4221d5','New route/budget/source binding differs')
        for name,pin in {**PINS,**B.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen source drift after checks')
        result.update(state='PASS_MINIMAL_BACKING_FIRST_REQUEST_CONFIG_BUILDER_SOURCE_ONLY',frozen_sources=PINS,checks=checks,builder_exact_preimage_restored_by_five_rules=True,request_exact_v3_restored_by_one_route=True,native_resource_bytes_unchanged=M.NATIVE_RESOURCE_BYTES,finite_native_resource_wait_seconds=1800,unchanged_native_parser_accepts_synthetic_policy=True,builder_immediate_Windows_capacity_gate_unchanged=True,full_method_support_template_runner_supervisor_unchanged=True,reviewed_contracts=['Six actual gates plus exact explicit unlock hashes remain required','Backing probe exact new source, expected success schema, all three phases and exact owned cleanup required; failed canonical UNC03 cannot qualify','Runtime08/storage06 candidate paths/pins and actual producer terminal joins preserved','UNC final receipt hash and selected storage proof path/SHA joins preserved','Original WorkflowLock/current direct authority/STOP/fresh Windows physical+commit+disk checks preserved','Unchanged Linux native reserves, two threads, serial owner, sampled RSS and per-process address limits remain mandatory','New1800second retry window retains fresh admission before native commands and finite defer on expiration; original builder forced0'],actual_requirements=['Root publishes exact source/peer packet and verifies remote bytes','Close and independently accept actual backing UNC04 three-phase bidirectional sentinel plus exact cleanup through current ext4 proof','Create fresh actual request via --prepare, then fresh actual config via --build under original lock/current resources; independently review actual build and explicit unlock','Bind exact new Windows backing owner to original scientific Linux runner and only then admit one approved full-method genome'],actual_operations='NOT_RUN; synthetic temporary config is test-only and removed',old_sources_and_failed_scopes_preserved=True)
    except BaseException as error:result['error']={'kind':type(error).__name__,'message':str(error)}
    result['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':result['state'],'error':result.get('error'),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
    return 0 if result['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
