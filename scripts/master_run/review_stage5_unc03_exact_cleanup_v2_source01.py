"""C-only source peer for the separate exact failed03 cleanup revision."""
from pathlib import Path
import ast, datetime, hashlib, json, subprocess, sys
import review_stage5_postboot_gate as R
import stage5_unc03_exact_sentinel_cleanup_v2 as C

W=Path(__file__).resolve().parent
PINS={'stage5_unc03_exact_sentinel_cleanup.py':'7a485a908c6d200588d781bf7b26e65d9a51c5f3c5b41b4dea0e9761d1ea8f92',
      'test_stage5_unc03_exact_sentinel_cleanup.py':'117f453e6a7f226021ba0bc4d5ef5a8da8fe26d563b5740da6f8341b82932af4',
      'stage5_unc03_exact_sentinel_cleanup_v2.py':'0984781820c8dd2b85a909b182902990e5c335c6e19187733dadbe3039ef77d4',
      'test_stage5_unc03_exact_sentinel_cleanup_v2.py':'c96601fc1334706ed73124bc00de9e62281306f057d71383c279e42912396b33',
      'STAGE05_UNC03_EXACT_SENTINEL_CLEANUP_PREPARATION02.md':'3e133559e3d93e0c804459716710c34248bea8360df770d0e356879c92af5573'}

def main():
    out=W/'stage5_unc03_exact_cleanup_v2_source_independent_review01.json'
    blocked=W/'stage5_unc03_exact_cleanup_original_blocked_source_review01.json'
    R.require(not out.exists() and not blocked.exists(),'Preserve cleanup source peers')
    value={'schema':'STAGE05_UNC03_EXACT_CLEANUP_SOURCE_INDEPENDENT_V2','state':'FAILED_SOURCE_REVIEW',
           'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
           'method':'C-only frozen source bytes/AST/dependency and prior control joins, 19 focused fake/pure tests including tiny C fsync/readback fixture, separate default NOOP. No UNC/G/WSL/registry/lock/native process effects/network/Git.',
           'actual_cleanup':'NOT_RUN','scientific_adoption':False,'original_failed_UNC03':'PRESERVED_FAILED'}
    try:
        for name,pin in {**PINS,**C.PINS,**C.RECEIPTS}.items():R.require(R.sha(W/name)==pin,'Frozen cleanup member/control differs: '+name)
        old=R.data(W/'stage5_unc03_exact_sentinel_cleanup.py');new=R.data(W/'stage5_unc03_exact_sentinel_cleanup_v2.py')
        guard=b"if __name__ == '__main__':\n    raise SystemExit(main())\n"
        R.require(old.count(guard)==new.count(guard)==1 and new==old.replace(guard,b'').rstrip()+b'\n\n\n'+guard,'Revision differs beyond exact guard relocation')
        original=ast.parse(old);revised=ast.parse(new)
        def functions(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
        R.require(functions(original)==functions(revised),'Cleanup function AST changed')
        original_guard=next(i for i,n in enumerate(original.body) if isinstance(n,ast.If))
        original_resources=next(i for i,n in enumerate(original.body) if isinstance(n,ast.FunctionDef) and n.name=='resources')
        R.require(original_guard<original_resources and isinstance(revised.body[-1],ast.If),'Original CLI defect or final corrected ordering differs')
        reject={'schema':'STAGE05_UNC03_EXACT_CLEANUP_REJECTED_SOURCE_V1','state':'BLOCKED_SOURCE_ACTUAL_CLI_RESOURCES_UNDEFINED',
                'utc':value['utc'],'source_sha256':PINS['stage5_unc03_exact_sentinel_cleanup.py'],'test_sha256':PINS['test_stage5_unc03_exact_sentinel_cleanup.py'],
                'reviewer_source_sha256':value['reviewer_source_sha256'],'evidence':'The top-level __main__ guard raises SystemExit(main()) before resources is defined. Actual --run owner reaches resources before definition; import-based tests and default NOOP do not detect this. No actual cleanup ran.',
                'required_correction':'Separate revision moving only the main guard to the final top-level statement and adding CLI definition-order regression. Original source remains rejected and unchanged.','actual_operations':'NOT_RUN'}
        with blocked.open('x',encoding='utf-8',newline='\n') as stream:json.dump(reject,stream,indent=2);stream.write('\n')
        controls=C.controls();request=R.pinned(C.FAILED/'request.json',C.REQUEST_SHA)
        R.require(request['nonce']==C.EXPECTED_NONCE and C.EXPECTED_LEAF['inode']==33554461 and C.EXPECTED_DIRECTORY['inode']==33554454,'Known failed scope target differs')
        diagnostic=R.read(W/'stage5_unc03_readonly_diagnostic.py') if False else ast.parse(R.data(W/'stage5_unc03_readonly_diagnostic.py'))
        for name in ('need','sha','error_record','plain_c','original_request','authority','resources','metadata'):
            R.require(functions(diagnostic)[name]==functions(revised)[name],'Original diagnostic guard AST changed: '+name)
        checks=[]
        for name,count in [('test_stage5_unc03_exact_sentinel_cleanup_v2.py',19),('stage5_unc03_exact_sentinel_cleanup_v2.py',0)]:
            run=subprocess.run([sys.executable,'-B',str(W/name)],cwd=W,capture_output=True,text=True,timeout=30)
            R.require(run.returncode==0,'Pure cleanup check failed: '+run.stderr[-3000:])
            if count:R.require('Ran 19 tests' in run.stderr,'Focused cleanup test count differs')
            else:R.require(json.loads(run.stdout)=={'state':'PREPARED_EXACT_FAILED03_CLEANUP_NOT_RUN','WSL_launches':0,'UNC_effects':0,'probe_success_claimed':False},'Default cleanup NOOP differs')
            checks.append({'name':name,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
        for name,pin in {**PINS,**C.PINS,**C.RECEIPTS}.items():R.require(R.sha(W/name)==pin,'Frozen cleanup bytes changed during pure review')
        value.update(state='PASS_MINIMAL_EXACT_FAILED03_CLEANUP_V2_SOURCE_ONLY',frozen_sources=PINS,checks=checks,original_rejected_source_report=str(blocked),original_rejected_source_report_sha256=R.sha(blocked),move_only_delta=True,all_original_function_ASTs_identical=True,prior_failed_and_diagnostic_scopes_closed=True,contracts=['Only exact nonce directory projected inode33554454/nlink2 and known116B inode33554461/nlink1 Linux leaf; absent windows.bin error2 and bounded exact entry listing mandatory','Unchanged U0664.tiny_read and typed full metadata/payload/hash rechecks before fixed leaf unlink and exact empty directory rmdir','Exclusive C binary backup with flush/fsync and metadata readback plus durable effect intents before either deletion; truthful partial-progress failure evidence','Same original WorkflowLock, direct authority/STOP/resource gates and unchanged retained U.windows_job root20s plus bounded full-Job drain; no WSL or science','Original unlock and closed lock stream plus durable unlock receipt precede successful owner result; unknown scope/unlock leaves STOP, no STOP removal','Single-master exclusive workflow required; fixed path rechecks do not claim kernel atomic compare-and-delete against arbitrary concurrent writers'],actual_requirements=['Root publishes source/peer and verifies remote exact bytes before actual cleanup','Fresh original workflow ownership and direct authority; previous scope closure/STOP absent; no concurrent science owner','Root explicitly maps actual linux.bin.backup116B despite suffix filtering and verifies remote SHA plus backup_metadata.json after actual operation','Independent actual source/target/backup/effect/retained closure/original unlock review; old UNC03 stays failed and separate accepted backing04 remains separate qualification'])
    except BaseException as error:value['error']={'kind':type(error).__name__,'message':str(error)}
    value['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'error':value.get('error'),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
    return 0 if value['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
