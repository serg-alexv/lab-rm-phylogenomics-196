"""Pure peer of exact UNC03 diagnostic adaptation; no diagnostic execution."""
from pathlib import Path
import ast, datetime, hashlib, json, subprocess, sys
import review_stage5_postboot_gate as R
import stage5_unc03_readonly_diagnostic as D

W=Path(__file__).resolve().parent
SOURCE='c0458522ca5483670f008049d1a4457ad27531b003b8397893ee5b0d05b31697'
TESTS='8ac84b4e7cbf93c54ef40249ae1d965eff5988efe0a0c29e3b0e672b81b43c23'
OLD='c0e5a8fdbb97b3b3d3251d417e530a858a65fdeff94ec24eaa2cd3dfe4acc45f'

def main():
    out=W/'stage5_unc03_readonly_diagnostic_source_independent_review01.json';R.require(not out.exists(),'Fresh source peer required')
    report={'schema':'STAGE05_UNC03_READONLY_DIAGNOSTIC_SOURCE_INDEPENDENT_V1','state':'FAILED_SOURCE_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),'scope':'C-only source/failed public request and bounded pure fake tests/default NOOP. No UNC access, registry, WSL, original lock, retained handle, process effects or Git action.','actual_diagnostic':'NOT_RUN','original_UNC03_gate':'FAILED_PRESERVED','scientific_adoption':False}
    try:
        R.require(R.sha(W/'stage5_unc03_readonly_diagnostic.py')==SOURCE and R.sha(W/'test_stage5_unc03_readonly_diagnostic.py')==TESTS and R.sha(W/'stage5_unc02_readonly_diagnostic.py')==OLD,'Frozen source/test/history differs')
        for name,pin in D.PINS.items():R.require(R.sha(W/name)==pin,'Unchanged U/A dependency differs')
        original=R.data(W/'stage5_unc02_readonly_diagnostic.py').decode().replace('\r\n','\n')
        revised=R.data(W/'stage5_unc03_readonly_diagnostic.py').decode().replace('\r\n','\n')
        restored=revised.replace('UNC03','UNC02').replace('unc03','unc02').replace('postiq_03','postiq_02').replace(D.REQUEST_SHA,'b32fceaaf4757d2bd59c44004f4cd3c8ac502441692e621c9c05c80f61908e1c')
        restored=restored.replace("EXPECTED_NONCE = '8ae35884653047348cfa688d4bf00b36'\n",'')
        restored=restored.replace("value['nonce'] == EXPECTED_NONCE and re.fullmatch('[a-f0-9]{32}', value['nonce'])\n         and value['sentinel_name']", "re.fullmatch('[a-f0-9]{32}', value['nonce']) and value['sentinel_name']")
        R.require(restored==original,'Diagnostic changed beyond exact UNC03 tags/request/strict nonce guard')
        request=R.pinned(W/'stage5_unc_bind_actual_postiq_03/request.json',D.REQUEST_SHA)
        R.require(D.REQUEST_SHA=='7f28e209707483d1a50e25c7d35e5804f2b9ebb8ecf9bcc110714849228ce27d' and request['nonce']==D.EXPECTED_NONCE=='8ae35884653047348cfa688d4bf00b36','Failed03 request/nonce differs')
        targets=D.targets(request);dirs=D.directory_targets(request)
        R.require(len(targets)==4 and len(dirs)==2 and len({x['path'] for x in targets})==4 and all(x['expected_bytes']<=512 for x in targets),'Fixed bounded diagnostic targets differ')
        tree=ast.parse(revised);owner=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='owner')
        calls=[ast.unparse(n.func) for n in ast.walk(owner) if isinstance(n,ast.Call)]
        R.require(calls.count('A.WorkflowLock')==1 and calls.count('U.windows_job')==1 and 'subprocess.Popen' not in calls,'Original same-lock/retained named Job route changed')
        checks=[]
        for name in ('test_stage5_unc03_readonly_diagnostic.py','stage5_unc03_readonly_diagnostic.py'):
            p=subprocess.run([sys.executable,'-B',str(W/name)],cwd=W,capture_output=True,text=True,timeout=30)
            R.require(p.returncode==0,'Focused pure tests/default NOOP failed: '+p.stderr[-3000:])
            if name.startswith('test_'):R.require('Ran 6 tests' in p.stderr,'Six tests not completed')
            else:R.require(json.loads(p.stdout)=={'state':'PREPARED_READONLY_DIAGNOSTIC_NOT_RUN','WSL_launches':0,'UNC_writes':0},'Default NOOP differs')
            checks.append({'name':name,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        R.require(R.sha(W/'stage5_unc03_readonly_diagnostic.py')==SOURCE and R.sha(W/'test_stage5_unc03_readonly_diagnostic.py')==TESTS and R.sha(W/'stage5_unc02_readonly_diagnostic.py')==OLD,'Frozen source drift after pure tests')
        report.update(state='PASS_FROZEN_UNC03_READONLY_DIAGNOSTIC_SOURCE_SIX_PURE_TESTS_NOOP',source_sha256=SOURCE,tests_sha256=TESTS,preserved_proven_UNC02_source_sha256=OLD,only_source_changes=['UNC03 schema/spool/request tags','Exact failed03 request SHA','Additional strict exact failed03 nonce guard'],original_request_sha256=D.REQUEST_SHA,expected_nonce=D.EXPECTED_NONCE,targets=targets,directories=dirs,checks=checks,reviewed_contracts=['Exact WD/C ancestry and fresh spool/source/request binding','Original byte WorkflowLock and unchanged U.windows_job20second retained named Job','Fixed four leaves/two directories only; bounded readonly hashes without raw payload output','Unchanged U.tiny_read errors retained beside independent observation; no predicate relaxation/adoption','Current direct ACTIVE authority/raw hash/STOP/resource checks before reads and final acceptance','Exact Ubuntu UID/Flags registration observation and drift rechecks','No WSL/Linux/native/mount/UNC write/cleanup; only diagnostic C spool writes','Only OwnedClosureFailure creates unproven closure STOP; actual current gate remains failed'],actual_requirements='Root publishes exact source/test/peer bytes and verifies readback before explicit --run; retained child empty Job/exit, worker/source/control/registration joins and original unlock require actual review')
    except BaseException as error:report['error']={'kind':type(error).__name__,'message':str(error)}
    report['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':report['state'],'error':report.get('error'),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
    return 0 if report['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
