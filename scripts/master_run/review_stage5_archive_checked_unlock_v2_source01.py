"""Independent source-only checked-unlock/owned-STOP archive owner review."""
from pathlib import Path
import ast, datetime, hashlib, json, subprocess, sys
import review_stage5_postboot_gate as R
import stage5_closed_genome_archive_windows_checked_unlock_v2 as V

W=Path(__file__).resolve().parent
PINS={'stage5_closed_genome_archive_windows_checked_unlock_v2.py':'f0d3456dbfd02fa46e127f9dc93f8da7083cd777380561031de8c565cde738e4',
      'test_stage5_closed_genome_archive_checked_unlock_v2.py':'1168dec604043aac0465c80c6420f9a81b2a388d6fb02f7528404ee2864d65d3',
      'stage5_closed_genome_archive_checked_unlock_v2_METHODS.md':'ffbdd37877d1397a8aa6eb669e73161063733bb0ba97aeda75e67a8c8f6144e5',
      'stage5_closed_genome_archive_checked_unlock_v2_preparation01.json':'20c4ea58fa39828ce468f1d0c5771cd090d3d5b1771e293ac50c024cb23e55b7',
      'stage5_closed_genome_archive_windows_checked_unlock.py':'52f19e3367625f75ccdbf3232e1e1dcd204e1f329be8d61bd161dc629cfbe68f',
      'stage5_closed_genome_archive_windows.py':'249b9de14219d8c0a5f1e7e88e48f6c80694bd04699c7c3e506b50a0980fab45'}

def main():
    out=W/'stage5_archive_checked_unlock_v2_source_independent_review01.json'
    R.require(not out.exists(),'Preserve archive source peer')
    value={'schema':'STAGE05_ARCHIVE_CHECKED_UNLOCK_V2_INDEPENDENT_SOURCE_V1','state':'FAILED_SOURCE_REVIEW',
           'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
           'method':'C-only complete Windows source/AST/delta and pinned dependency reads; 17 pure fake-lock/control/C-temp fault tests and separate default NOOP. No actual G/UNC/WSL/API/OS lock/native/archive/upload/restore/delete action.',
           'actual_archive':'NOT_RUN','scientific_adoption':False,'local_eviction_authorized':False}
    try:
        for name,pin in {**PINS,**V.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen archive source/dependency differs: '+name)
        prep=R.read(W/'stage5_closed_genome_archive_checked_unlock_v2_preparation01.json')
        for name,row in prep['files'].items():R.require(R.sha(W/name)==row['sha256'] and len(R.data(W/name))==row['bytes'],'Prepared archive member differs')
        original=ast.parse(R.data(W/'stage5_closed_genome_archive_windows.py'));new=ast.parse(R.data(W/'stage5_closed_genome_archive_windows_checked_unlock_v2.py'))
        funcs=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
        before=funcs(original);after=funcs(new)
        R.require(all(after[name]==row for name,row in before.items() if name!='main'),'Original non-main archive function changed')
        assignments=lambda tree:[ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.Assign,ast.Import,ast.ImportFrom))]
        R.require(assignments(original)==assignments(new),'Original archive imports/constants/PINS changed')
        source=R.data(W/'stage5_closed_genome_archive_windows_checked_unlock_v2.py').decode();helper=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='archive_authority')
        lines=source.splitlines(keepends=True);restored=''.join(lines[:helper.lineno-1]+lines[helper.end_lineno+2:])
        restored=restored.replace('archive_authority(A,O,stop,stop_sha,nonce);last=api.resources([ROOT,output])','O.fresh_authority();last=api.resources([ROOT,output])')
        R.require(restored==R.data(W/'stage5_closed_genome_archive_windows_checked_unlock.py').decode(),'V2 changes beyond exact owned STOP authority helper/one call')
        owner_uses={n.attr for n in ast.walk(new) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='O'}
        R.require(owner_uses=={'LOCAL_CLOSURE_STOP','fresh_authority'},'Archive adds unrelated original-owner transport dependency')
        main_node=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        R.require(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='unlink' for n in ast.walk(main_node)), 'Owned STOP deletion must stay after checked unlock finalizer')
        checks=[]
        for name,count in [('test_stage5_closed_genome_archive_checked_unlock_v2.py',17),('stage5_closed_genome_archive_windows_checked_unlock_v2.py',0)]:
            p=subprocess.run([sys.executable,'-B',str(W/name)],cwd=W,capture_output=True,text=True,timeout=30)
            R.require(p.returncode==0,'Pure archive source check failed: '+p.stderr[-3000:])
            if count:R.require('Ran 17 tests' in p.stderr,'Focused archive check count differs')
            else:R.require(json.loads(p.stdout)['state']=='PREPARED_NOT_RUN' and json.loads(p.stdout)['eviction_authorized'] is False,'Default archive NOOP differs')
            checks.append({'name':name,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        for name,pin in {**PINS,**V.PINS}.items():R.require(R.sha(W/name)==pin,'Frozen archive source drift during review')
        value.update(state='PASS_CHECKED_UNLOCK_AND_EXACT_OWNED_STOP_ARCHIVE_V2_SOURCE_ONLY',frozen_sources=PINS,checks=checks,all_original_non_main_function_ASTs_and_constants_preserved=True,v2_exact_minimal_delta_from52f=True,unchanged_Linux_source_sha256=V.PINS['stage5_closed_genome_archive_linux.py'],original_owner_transport_alias_change_required=False,rejected_checked_unlock52f={'source_sha256':PINS['stage5_closed_genome_archive_windows_checked_unlock.py'],'state':'PRESERVED_BLOCKED_SOURCE_NOT_ACTUAL_FAILURE','blocker':'Inherited lease renewal calls original STOP-absent authority after writing its own active STOP; source-only v2 corrects this exact self-rejection.'},reviewed_contracts=['Same original WorkflowLock object entered once and checked __exit__ called in outer finally before exact owned STOP removal','Actual retained WSL/Linux no-child/prior-scope closure, inactive lease and restored power state required; unchanged finite client1830s and Linux1800s limits','Durable/readback original unlock receipt SHA plus true closure and successful finalizers precede owned STOP SHA+nonce check and removal; pending success becomes PASS only afterward','Initial original fresh_authority still rejects existing STOP; active renewal accepts only exact current owned STOP SHA+nonce and freshly requires direct ACTIVE control with literal automatic_resume false','Foreign/changed/missing STOP, halt or automatic-resume control rejects renewal; no global original owner change','Unlock/receipt/hash/finalizer/unknown-closure/foreign STOP failures cannot yield PASS or clear owned STOP','Final result persistence failure becomes FAILED and one bounded publication_failure receipt attempt; proved closure/unlock stay truthful and no fabricated unclosed-process STOP is created','Same prior actual complete/config/owner/launch/exit/source/progress/lease/panel checks, canonical Linux storage path and448MiB raw ZIP cap; no UNC use or eviction'],actual_acceptance_requirements=['Root publishes exact source/peer packet and verifies remote bytes','Previous full-method single-genome owner genuinely complete, retained native/client scope closed and original unlock independently accepted','Archive actual helper exit0, final PASS after explicit unlock, no publication_failure receipt or owner finalizer error, independent actual Linux/archive payload/metadata/hash readback','Remote byte recovery and restoration verification remain separate prerequisites before any local purge'],scope_limit='This peer adopts only the reviewed Windows unlock/owned STOP source correction and unchanged pinned helper composition; source tests do not prove an actual Linux archive, remote durability, restoration, biological curation or cleanup eligibility.')
    except BaseException as error:value['error']={'kind':type(error).__name__,'message':str(error)}
    value['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':value['state'],'error':value.get('error'),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checker_sha256':R.sha(Path(__file__))}))
    return 0 if value['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
