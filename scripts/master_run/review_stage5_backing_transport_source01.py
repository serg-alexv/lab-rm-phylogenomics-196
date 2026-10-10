"""C-only source peer for two fixed backing UNC transport substitutions."""
from pathlib import Path
import ast, copy, datetime, hashlib, json, subprocess, sys
import review_stage5_postboot_gate as R

W=Path(__file__).resolve().parent
PINS={'stage5_unc_bind_probe.py':'0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d','stage5_unc_backing_probe.py':'779502c38c5db06b68e796abc6e1bd99db72d8f97b1129f9057a3f6b0c4221d5','stage5_windows_owner.py':'8851bc4fc48ad3069d4ffabe410e159004ef4fc8d6d0755213fc14c22fe0603d','stage5_windows_backing_owner.py':'296492aa4205f64058846b9901a7bb3a3458f99eda1c7ff388a6e33cdc38b834','stage5_atomic.py':'500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04','stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e','test_stage5_backing_transport.py':'47f8f7fc49a58948bd4eb5734f938a36fd2ead4061ffae2b2ec31fd79a97701a'}

def main():
    out=W/'stage5_backing_transport_source_independent_review01.json';R.require(not out.exists(),'Fresh source peer required')
    report={'schema':'STAGE05_BACKING_TRANSPORT_SOURCE_INDEPENDENT_V1','state':'FAILED_SOURCE_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only exact source byte/AST readback, bounded pure synthetic tests, probe default NOOP and owner --help. No G or UNC observation, WSL, registry, lock, native process effect or Git mutation.','actual_backing_bidirectional_gate':'NOT_RUN','scientific_adoption':False,'original_UNC02_UNC03_failed_scopes':'PRESERVED_FAILED'}
    try:
        for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Frozen old/new/scientific/test source drift: '+name)
        uold=R.data(W/'stage5_unc_bind_probe.py');unew=R.data(W/'stage5_unc_backing_probe.py')
        before=b"UNC = PureWindowsPath(r'\\\\wsl.localhost\\Ubuntu').joinpath(*PurePosixPath(TARGET).parts[1:])"
        after=b"UNC = PureWindowsPath(r'\\\\wsl.localhost\\Ubuntu\\var\\tmp\\lab_rm_stage05_atomic_v1')"
        R.require(uold.count(before)==unew.count(after)==1 and uold.replace(before,after)==unew,'Probe differs beyond one fixed UNC constant')
        oold=R.data(W/'stage5_windows_owner.py');onew=R.data(W/'stage5_windows_backing_owner.py')
        before=b"    return Path(r'\\\\wsl.localhost\\Ubuntu').joinpath(*PurePosixPath(target).parts[1:])"
        after=b"    return Path(r'\\\\wsl.localhost\\Ubuntu').joinpath(*PurePosixPath(frozen['backing']).parts[1:])"
        R.require(oold.count(before)==onew.count(after)==1 and oold.replace(before,after)==onew,'Owner differs beyond final frozen-backing evidence return')
        funcs=lambda raw:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
        R.require(funcs(uold)==funcs(unew),'Probe function AST drift')
        oldtree=ast.parse(oold);newtree=ast.parse(onew);ov=next(n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name=='evidence_view');nv=next(n for n in newtree.body if isinstance(n,ast.FunctionDef) and n.name=='evidence_view');nv.body[-1]=copy.deepcopy(ov.body[-1]);R.require(ast.dump(oldtree,include_attributes=False)==ast.dump(newtree,include_attributes=False),'Owner AST changed beyond reviewed return')
        checks=[]
        for name,args in (('test_stage5_backing_transport.py',[]),('stage5_unc_backing_probe.py',[]),('stage5_windows_backing_owner.py',['--help'])):
            p=subprocess.run([sys.executable,'-B',str(W/name),*args],cwd=W,capture_output=True,text=True,timeout=30)
            R.require(p.returncode==0,'Pure verification failed: '+name+' '+p.stderr[-2500:])
            if name.startswith('test_'):R.require('Ran 17 tests' in p.stderr,'Seventeen tests not completed')
            if name=='stage5_unc_backing_probe.py':
                value=json.loads(p.stdout);R.require(value['state']=='PREPARED_NOT_RUN' and value['exact_unc']==r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1' and value['scientific_adoption_authorized'] is False and value['source_sha256']==PINS[name],'Probe NOOP/alias differs')
            checks.append({'name':name,'args':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Frozen source drift after pure tests')
        report.update(state='PASS_TWO_FIXED_BACKING_TRANSPORT_SUBSTITUTIONS_SOURCE_ONLY',frozen_sources=PINS,probe_all_function_asts_unchanged=len(funcs(uold)),owner_whole_ast_unchanged_after_single_return_restore=True,checks=checks,canonical_scientific_target='/mnt/g/My Drive/LAB_RM/lab-rm-phylogenomics-196/.work/stage05_atomic_v1',fixed_windows_transport=r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1',reviewed_contracts=['Only fixed Windows UNC view changes; canonical Linux root/target and exact ext4 backing/helper/proof requirements remain','All U request, tiny_read single-link/opened identity/hash, three-phase bidirectional fsync/readback, exact two-leaf cleanup, resources, original lock and retained named Job/WSL closure functions identical','Windows evidence_view validates proof byte pin and exact original canonical root/target/backing/helper before returning fixed proven backing UNC','Every Windows owner function other than evidence_view unchanged, including ACTIVE/STOP, nonce, lease, resource deadlines, retained client/native closure, exact completed checkpoint, original lock and power restoration','Scientific Linux runner500dc and native Supervisore5be bytes unchanged','Original sources/failed histories preserved; no reboot, namespace mutation, mount repair or relaxed predicate introduced'],owner_noop_boundary='Only --help and pure mocked function checks ran. Preserved owner main needs explicit config/script/output and reads project authority/panel before --run; it was not called.',required_actual_order=['Root publish exact new source/test/peer bytes and verify remote readback','Run new backing probe with exact config/source pins; independently review all three phases, current ext4 canonical-to-backing storage identity, both payload directions, retained native/Windows closure and exact cleanup','Update first-genome source binding to exact new Windows owner entrypoint while preserving original Linux runner/resources; retain all current fresh gates','Only then root may admit one approved scientific genome through original lock and current measured resources'],actual_alias_adoption='NOT_YET_AUTHORIZED_BY_SOURCE_ONLY_PEER',actual_cleanup_or_science_run='NOT_RUN')
    except BaseException as error:report['error']={'kind':type(error).__name__,'message':str(error)}
    report['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':report['state'],'error':report.get('error'),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
    return 0 if report['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
