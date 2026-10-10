"""Independent source-only review of corrected paired owner v2; no cold action."""
from pathlib import Path
import ast, datetime, hashlib, json, struct, subprocess, sys
import review_stage5_postboot_gate as R
import stage5_setup_cold_linux_v2 as C
import stage5_setup_cold_windows_v2 as W

HERE=Path(__file__).resolve().parent
PINS={'stage5_setup_cold_linux_v2.py':'d734bac3b5604c645c9b099f9a220aae118e547dbcdf7178bb62b43b0c6dc77c','stage5_setup_cold_windows_v2.py':'a7991c3bb0408f2b7bf7a60e2e1aee13d69e49d1324b670e9321aa20bb3e554c','test_stage5_setup_cold_owner_v2.py':'5dc2005094f50d0dd04feb712504a5c4e58139875381604f0c07c8fa76ed54c7','STAGE05_COLD_EXISTING_OWNER_PREPARATION02.md':'71e8c52ba1b5dec9d5c53049d90778a62fa1e8c5ed211539f3d448e8fbe8a720','stage5_setup_cold_linux.py':'d10faf17d42db44243f10fa1908fede549f3dd20ff58013fcaa37f36f3eeb9d5','stage5_setup_cold_windows.py':'e81ca9b5f2b3402b1fa983270bf32fe60b16cdf2b1c4d1c9f043bf7164c4a2d1','stage05_cold_owner_source_independent_review01.json':'53390992b3787fe39cae4415e00804ad40532adaf910c5a57fb369dfc735aef0','stage05_cold_owner_unlock_order_addendum01.json':'6f3d7989f08f957a8465d9b995777d853618a6ad078f46c2cc2af1ec8c0c741f'}

def funcs(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}

def main():
    out=HERE/'stage05_cold_owner_v2_source_independent_review01.json';R.require(not out.exists(),'Fresh corrected source peer required')
    report={'schema':'STAGE05_COLD_OWNER_V2_SOURCE_INDEPENDENT_V1','state':'FAILED_SOURCE_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),'scope':'C-only source/AST/byte pins plus bounded pure synthetic fixtures/default NOOPs. No actual WSL, image, UNC, mount, handle, workflow lock, process effects or Git ref action.','actual_integration':'NOT_RUN','scientific_adoption':False,'cleanup_authority':False}
    try:
        for name,pin in {**PINS,**C.COLD_PINS,**W.PINS}.items():R.require(R.sha(HERE/name)==pin,'Frozen source/history/helper drift: '+name)
        ordinary={}
        for kind in ('linux','windows'):
            old=funcs(R.data(HERE/f'stage5_setup_{kind}.py'));new=funcs(R.data(HERE/f'stage5_setup_cold_{kind}_v2.py'))
            R.require(all(new.get(k)==v for k,v in old.items()),'Original ordinary setup function AST changed: '+kind)
            ordinary[kind]=list(old)
        p=subprocess.run([sys.executable,'-B',str(HERE/'test_stage5_setup_cold_owner_v2.py')],cwd=HERE,capture_output=True,text=True,timeout=40)
        R.require(p.returncode==0 and 'Ran 30 tests' in p.stderr,'Thirty focused pure/synthetic tests failed: '+p.stderr[-3000:])
        noops=[]
        for kind in ('linux','windows'):
            n=subprocess.run([sys.executable,'-B',str(HERE/f'stage5_setup_cold_{kind}_v2.py')],cwd=HERE,capture_output=True,text=True,timeout=20)
            R.require(n.returncode==0 and json.loads(n.stdout)['state'].startswith('NO_OP'),'Separate paired CLI default NOOP failed')
            noops.append({'kind':kind,'exit_code':n.returncode,'stdout':n.stdout,'stderr':n.stderr})
        rejected=[]
        for state in (0,3,5,9,0xffff):
            raw=bytearray(1024);raw[56:58]=b'\x53\xef';struct.pack_into('<H',raw,0x3a,state);raw[104:120]=bytes.fromhex('0123456789abcdef0123456789abcdef')
            try:C.cold_clean_superblock(bytes(raw))
            except C.P.Fatal:rejected.append(state)
            else:raise ValueError('Dirty/orphan/unknown superblock state accepted')
        policy=C.cold_resource_policy()
        R.require(C.COLD_ALLOCATION==512*1024**2 and C.COLD_TOTAL_ALLOCATION==1024*1024**2 and C.COLD_WINDOWS_REQUIREMENT==2560*1024**2 and policy['incremental_windows_requirement_bytes']==policy['linux_job_requirement_bytes']==1024*1024**2 and policy['commit_requirement_bytes']==2560*1024**2,'Conservative parent+worker capacity booking differs')
        for value in (True,False,8.0,'8',None,9):
            try:W.cold_terminal_count(value,8)
            except (ValueError,W.A.Fatal if hasattr(W.A,'Fatal') else ValueError):pass
            except Exception:pass
            else:raise ValueError('Non-exact terminal count accepted')
        R.require(W.cold_terminal_count(8,8)==8,'Exact integer terminal count rejected')
        wt=ast.parse(R.data(HERE/'stage5_setup_cold_windows_v2.py'));mainnode=next(n for n in wt.body if isinstance(n,ast.FunctionDef) and n.name=='cold_main');final=next(n for n in wt.body if isinstance(n,ast.FunctionDef) and n.name=='cold_finish_after_unlock')
        R.require(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='unlink' for n in ast.walk(mainnode)),'Cold main clears STOP before explicit unlock finalizer')
        calls=sorted((n.lineno,ast.unparse(n.func),[ast.unparse(a) for a in n.args]) for n in ast.walk(final) if isinstance(n,ast.Call))
        unlock=min(n for n,func,args in calls if func=='lock.__exit__');clear=min(n for n,func,args in calls if func=='STOP.unlink')
        receipt=min(n for n,func,args in calls if func=='A.atomic' and args[0]=='path')
        R.require(unlock<receipt<clear,'Original checked unlock/receipt do not precede STOP clear')
        R.require(any(func=='A.read_json' and args==['path'] and unlock<n<clear for n,func,args in calls),'Explicit unlock receipt lacks before-clear readback')
        sources={n:R.sha(HERE/n) for n in ('stage5_setup_cold_linux_v2.py','stage5_setup_cold_windows_v2.py','test_stage5_setup_cold_owner_v2.py')}
        for name,pin in {**PINS,**C.COLD_PINS,**W.PINS}.items():R.require(R.sha(HERE/name)==pin,'Post-test frozen source/history drift')
        report.update(state='PASS_CORRECTED_PAIRED_COLD_OWNER_V2_SOURCE_ONLY_ACTUAL_NOT_RUN',frozen_sources=sources,ordinary_function_asts_unchanged=ordinary,authored_tests={'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},separate_default_noops=noops,independent_rejected_superblock_states=rejected,conservative_capacity={'parent_bytes':512*1024**2,'worker_bytes':512*1024**2,'windows_reserve_bytes':1536*1024**2,'physical_and_commit_requirement_bytes':2560*1024**2,'aggregate_kernel_memory_cap_claimed':False},corrected_findings=['Exact clean ext4 integer state1 on Linux and both Windows detached joins','Honest conservative512+512MiB capacity in both owners','Strict integer terminal command accounting','Checked original unlock plus durable read-back receipt before exact owned STOP clear'],final_publication_boundary={'failure_receipt':'publication_failure.json','bounded_failure_receipt_attempts':1,'bounded_FAILED_result_retries':1,'caller_failure_propagated':True,'actual_closure_and_restoration_facts_preserved':True,'unclosed_process_STOP_fabricated':False,'master_reconciliation_required_on_failure':True},remaining_actual_gates=['First scientific genome and independent curation/archive closed before cold scheduling','Publish exact reviewed sources and current authority; fresh original24aa RW toolchain and controller closure receipts','Disposable Linux integration: real DrvFS sharing refusal, alias/writer exclusion, clean detach, RO noload loops and all closure/guard/STOP/restoration failure paths','Actual read-only inventory followed by original-byte/public-path/metadata/notices review before capture','Actual canonical logical capture, full payload/remote assets/fresh owned download/cold-tree restore before eviction'],runtime_join='Only SHA f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1; fresh byte-identical successor may join through its current closed receipt. Stale boot evidence cannot be adopted.',raw_both_image_splitting='NOT_RUN; logical runtime roles do not establish raw .ext4 or Ubuntu .vhdx split/recovery',actual_adoption_requirements='Successful externally retained caller exit0, final expected PASS, no publication_failure file, complete actual phase/native/WSL/guard/RW/runtime evidence, original explicit unlock and current authority',old_blocked_reports_preserved=True)
    except BaseException as error:report['error']={'kind':type(error).__name__,'message':str(error)}
    report['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':report['state'],'error':report.get('error'),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checked_files':len(R.CHECKED)}))
    return 0 if report['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
