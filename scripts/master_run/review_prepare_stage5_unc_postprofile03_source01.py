"""Pure source/tests peer review; no actual candidates, config, UNC or WSL use."""
from pathlib import Path
import ast, copy, datetime, hashlib, json, subprocess, sys
import review_stage5_postboot_gate as R
import prepare_stage5_unc_postprofile03 as M

W=Path(__file__).resolve().parent
PINS={'prepare_stage5_unc_postprofile03.py':'651c2bf5f54ea221f2493f1b31f9e840d057961c025f76aed9fd0820786e297a','test_prepare_stage5_unc_postprofile03.py':'929285e6c80545cad9bd3fa27d8556020954dfe74d4ad7c1f1f17990277f8363','prepare_stage5_unc_postprofile03_METHODS.md':'2673a5799616807f25b4dd83c5bb6b06c6a2051c7c4947358f0dc60300be12fe','prepare_stage5_unc_postprofile03_preparation01.json':'beb4fb605573bee25d8a699a104fe57cb1551e1d452983f5910865802f06ccef'}

def main():
    out=W/'prepare_stage5_unc_postprofile03_independent_review01.json';R.require(not out.exists(),'Fresh peer required')
    result={'schema':'STAGE05_UNC03_CONFIG_SOURCE_INDEPENDENT_V1','state':'FAILED_SOURCE_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only source/byte readback and bounded pure synthetic tests/default NOOP; no actual runtime08/storage06 candidate reads, config creation, UNC, WSL, registry, lock, Git or native action','scientific_adoption':False}
    try:
        for n,pin in {**PINS,**M.PINS}.items():R.require(R.sha(W/n)==pin,'Frozen source/template dependency differs: '+n)
        tree=ast.parse(R.data(W/'prepare_stage5_unc_postprofile03.py'))
        imports={n.names[0].name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import)}
        R.require(not imports.intersection({'subprocess','ctypes','socket','winreg','requests'}),'Unexpected effect API import')
        R.require(M.RUNTIME_NAME=='stage5_runtime_actual_postiq_08.json' and M.STORAGE_NAME=='stage5_storage_actual_postiq_06.json' and M.OUTPUT_NAME=='stage5_unc_config_actual_postprofile_03.json' and M.BOOT=='f0ffcebc-4901-479d-9559-89d45e9cfa38','Fixed current route differs')
        checks=[]
        for name in ('test_prepare_stage5_unc_postprofile03.py','prepare_stage5_unc_postprofile03.py'):
            p=subprocess.run([sys.executable,'-B',str(W/name)],cwd=W,capture_output=True,text=True,timeout=30)
            R.require(p.returncode==0,'Pure test/default NOOP failed: '+name+' '+p.stderr[-2000:])
            checks.append({'name':name,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        noop=json.loads(checks[1]['stdout']);R.require(noop['configs_written']==noop['WSL_launches']==noop['UNC_actions']==0,'Default invocation had actions')
        from test_prepare_stage5_unc_postprofile03 import Tests
        fixture=Tests();raw,runtime,storage=fixture.fixture()
        r=json.dumps(runtime).encode();s=json.dumps(storage).encode()
        config=M.build_config(raw,r,s,M.digest(r),M.digest(s));template=json.loads(raw);restored=copy.deepcopy(config)
        for key,prefix in (('runtime','manifest'),('work_storage','proof')):
            for suffix in ('path','sha256'):restored[key][prefix+'_'+suffix]=template[key][prefix+'_'+suffix]
        R.require(restored==template and config['resource_policy']==template['resource_policy'] and all(config['resource_policy'][k] is None for k in M.FIELDS),'Constructor changed fields beyond four pins')
        extra=[]
        for label in ('target_mount_bool','backing_mount_float','noncanonical_uuid','runtime_backslash','storage_wrong_source'):
            badr=copy.deepcopy(runtime);bads=copy.deepcopy(storage)
            if label=='target_mount_bool':bads['target_mount']['mount_id']=True
            if label=='backing_mount_float':bads['backing_mount']['parent_id']=0.0
            if label=='noncanonical_uuid':bads['filesystem_uuid']=bads['filesystem_uuid'].upper()
            if label=='runtime_backslash':badr['files']['models_dir']={'a\\b':'a'*64}
            if label=='storage_wrong_source':bads['target_mount']['source']='/dev/other'
            rb=json.dumps(badr).encode();sb=json.dumps(bads).encode()
            try:M.build_config(raw,rb,sb,M.digest(rb),M.digest(sb))
            except (ValueError,KeyError,TypeError):extra.append({'case':label,'rejected':True})
            else:raise ValueError('Independent tamper accepted: '+label)
        for n,pin in {**PINS,**M.PINS}.items():R.require(R.sha(W/n)==pin,'Frozen source drift after pure checks')
        result.update(state='PASS_FROZEN_UNC03_PREPARER_SIX_PURE_TESTS_DEFAULT_NOOP',source_sha256=PINS['prepare_stage5_unc_postprofile03.py'],checks=checks,independent_tamper_checks=extra,only_changes=['runtime.manifest_path','runtime.manifest_sha256','work_storage.proof_path','work_storage.proof_sha256'],entire_resource_policy_unchanged=True,five_biological_budgets_remain_null=True,preserved_old_source_unchanged=True,actual_candidate_closure_adoption='REQUIRES_ROOT_COMPLETED_CURRENT_GATE_REVIEWS_AND_PUBLISHED_ACTUAL_BYTES',actual_probe='NOT_RUN_REQUIRES_UNCHANGED_U0664_OWNER_CURRENT_STORAGE_ORIGINAL_LOCK_AND_CLOSURE')
    except BaseException as e:result['error']={'kind':type(e).__name__,'message':str(e)}
    result['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'state':result['state'],'error':result.get('error'),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
    return 0 if result['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
