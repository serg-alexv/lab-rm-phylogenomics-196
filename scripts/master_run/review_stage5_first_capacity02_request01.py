"""C-only independent peer of the explicit unmeasured Linux booking revision."""
from pathlib import Path
import copy, datetime, hashlib, json, subprocess, sys, tempfile
from unittest import mock
import review_stage5_postboot_gate as R
import stage5_build_backing_actual_config as B
import stage5_atomic as S
import prepare_stage5_first_capacity02_request as M

W=Path(__file__).resolve().parent
PINS={'prepare_stage5_first_capacity02_request.py':'4d5271f18de482104760e491281973b083232665b5caea8536c0822eebbdae76',
      'stage5_actual_request_backing_capacity_02.json':'13cdeba557bf0042a4fe2e95bf0905734cdd4735b0c333f255838b3fdb7e9ccb',
      'stage5_actual_request_backing_01.json':'96fc9e6a9893fb56122f701378aa49eb3f50773b797d6cdf4c9130548be3cb44',
      'stage5_build_backing_actual_config.py':'e1b7b4782be7cb4faa84cf546884075e860d2d010a1774ba7d61846bfff7905c'}

def main():
    out=W/'stage5_first_capacity02_request_independent_review01.json';R.require(not out.exists(),'Preserve capacity peer')
    value={'schema':'STAGE05_CAPACITY02_REQUEST_INDEPENDENT_V1','state':'FAILED_CAPACITY_REQUEST_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only decoded source/request deltas, default NOOP, deterministic temporary-C constructor and unchanged scientific config parser. No WSL/G/UNC/API/lock/native process effects, actual native config build or resource measurement.',
           'actual_config_build':'NOT_RUN','actual_native_execution':'NOT_RUN','scientific_adoption':False}
    try:
        for name,pin in {**PINS,**B.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen capacity/source bytes differ')
        before=R.read(W/'stage5_actual_request_backing_01.json');actual=R.read(W/'stage5_actual_request_backing_capacity_02.json')
        expected=copy.deepcopy(before);expected['native_resource_bytes']['linux_job_requirement_bytes']=1476395008
        expected['resource_basis']=actual['resource_basis']
        R.require(actual==expected and actual['resource_basis']!=before['resource_basis'],'Request differs beyond one Linux booking and documented basis')
        R.require(actual['native_resource_bytes']['sampled_rss_stop_bytes']==1342177280<1476395008
                  and all(actual['native_resource_bytes'][k]==v for k,v in before['native_resource_bytes'].items() if k!='linux_job_requirement_bytes'),'Unchanged RSS/other four budgets differ')
        p=subprocess.run([sys.executable,'-B',str(W/'prepare_stage5_first_capacity02_request.py')],cwd=W,capture_output=True,text=True,timeout=20)
        R.require(p.returncode==0 and json.loads(p.stdout)=={'state':'PREPARED_NOT_RUN','Linux_booking_bytes':1476395008,'native_actions':0},'Default NOOP differs')
        with tempfile.TemporaryDirectory(prefix='peer_capacity02_pure_',dir=W) as temp:
            folder=Path(temp);base=folder/M.BASE;base.write_bytes(R.data(W/M.BASE))
            with mock.patch.object(M,'W',folder),mock.patch('sys.argv',[str(M.__file__),'--prepare']):M.main()
            generated=folder/M.OUTPUT;R.require(generated.read_bytes()==R.data(W/M.OUTPUT),'Deterministic constructor actual bytes differ')
            generated.unlink()
            with mock.patch.object(M,'W',folder),mock.patch('sys.argv',[str(M.__file__),'--prepare']),mock.patch.object(M,'BASE_SHA','0'*64):
                try:M.main()
                except AssertionError:pass
                else:raise ValueError('Changed base SHA did not veto temporary constructor')
            R.require(not generated.exists(),'Rejected base wrote output')
            synthetic=B.explicit_policy(R.read(W/'stage5_atomic_config.template.json'),actual)
            config=folder/'synthetic_config.json';config.write_text(json.dumps(synthetic),encoding='utf-8')
            R.require(S.load_config(config)==synthetic and synthetic['resource_policy']['resource_wait_seconds']==1800
                      and synthetic['resource_policy']['linux_reserve_bytes']==1073741824,'Unchanged builder/parser/reserve/wait contract differs')
        for name,pin in {**PINS,**B.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen capacity bytes drifted')
        value.update(state='PASS_EXPLICIT_LINUX_BOOKING02_REQUEST_SOURCE_AND_EXACT_DELTA_ONLY',frozen_sources=PINS,unchanged_request_fields=['schema','purpose','runtime_manifest','storage_proof','all six exact gate/result/unlock pins','four other native byte budgets'],old_linux_job_requirement_bytes=1610612736,new_linux_job_requirement_bytes=1476395008,unchanged_sampled_aggregate_RSS_stop_bytes=1342177280,unchanged_Linux_reserve_bytes=1073741824,new_repeated_Linux_admission_requirement_bytes=2550136832,unchanged_windows_reserve_incremental_commit_and_full_native_method=True,resource_basis=actual['resource_basis'],checks={'default_NOOP':'PASS','temporary_C_deterministic_constructor_bytes':'PASS','changed_base_SHA_veto_no_output':'PASS','unchanged_builder_explicit_policy_and_S_load_config':'PASS'},capacity_interpretation='Explicit unmeasured capacity booking above unchanged execution RSS stop. It is not a measured detector requirement or guarantee of admission; runtime preparation can consume available margin. All native repeated admission, finite defer, closure and result semantics remain mandatory.',required_next=['Retain and genuinely close waiting01 exact owned runner/client/lock without any detector launch claim','Publish exact request/source/peer and verify remote bytes','Use unchanged actual builder only after prior original lock release; independently verify new actual config/build/admission/unlock','Native owner repeats current authority/storage/runtime/ownership/resources before first full-method genome; no further booking reduction if preparation/execution does not fit'],WSL_capacity_fallback='A higher configured maximum requires clean closure/restart and all fresh gates; an added512MiB maximum is not evidence of512MiB additional resident host use.')
    except BaseException as error:value['error']={'kind':type(error).__name__,'message':str(error)}
    value['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'error':value.get('error'),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
    return 0 if value['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
