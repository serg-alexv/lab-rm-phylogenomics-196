"""Independent C-only source/pure fixture peer; no kernel/WSL/image operations."""
from pathlib import Path
import ast,contextlib,datetime,hashlib,io,json,runpy,sys,unittest

WORK=Path(__file__).resolve().parent
PINS={
 'stage5_setup_cold_fixture_linux.py':'853fc5e0f354a61dc7332c5c8141423d845616f3cb3a71d60a2efaaa8e80f3ca',
 'stage5_setup_cold_fixture_windows.py':'f03c72327fd6ea0daf6b61cad49d4f59caa3342550fede9e25e2213df9c8002a',
 'test_stage5_setup_cold_fixture.py':'7bf3b3bbe1c8217b0d8ca1f769dc7a3b183961c064ef284238bb263448ae00c4',
 'STAGE05_DISPOSABLE_COLD_FIXTURE_PREPARATION01.md':'3e8d60c1fa168eb66f9dca6bbc9c3737753b045b48bb7ce5aef0ebdd67ddce1c',
 'stage5_setup_cold_linux_v2.py':'d734bac3b5604c645c9b099f9a220aae118e547dbcdf7178bb62b43b0c6dc77c',
 'stage5_setup_cold_windows_v2.py':'a7991c3bb0408f2b7bf7a60e2e1aee13d69e49d1324b670e9321aa20bb3e554c',
 'stage5_offline_image_read_parts_v2.py':'f0bf9fe02597cdce26e337d1c40fda45763b5225ea9f240e1962be18acacc151',
 'stage5_atomic_process.py':'e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e',
 'stage5_work_storage.py':'7e06eb842db147e6e26bfcd99e6ccffd2ab9fbcac106b122461b8df7f37edb6f'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    for name,pin in PINS.items():assert sha(WORK/name)==pin,name
    sys.path.insert(0,str(WORK))
    import test_stage5_setup_cold_fixture as T
    import stage5_setup_cold_fixture_linux as C
    import stage5_setup_cold_fixture_windows as O
    for name,pin in {**O.PINS,**C.COLD_PINS,**C.PINS}.items():assert sha(WORK/name)==pin,name
    ast_counts={}
    for suffix in ('linux','windows'):
        old=ast.parse((WORK/('stage5_setup_cold_'+suffix+'_v2.py')).read_bytes())
        new=ast.parse((WORK/('stage5_setup_cold_fixture_'+suffix+'.py')).read_bytes())
        funcs=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
        oldfunc,newfunc=funcs(old),funcs(new)
        assert all(body==newfunc[name] for name,body in oldfunc.items())
        ast_counts[suffix]=len(oldfunc)
    output=io.StringIO()
    tests=unittest.TextTestRunner(stream=output,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(T))
    assert tests.wasSuccessful(),output.getvalue()
    defaults=[]
    for name in ('stage5_setup_cold_fixture_linux.py','stage5_setup_cold_fixture_windows.py'):
        argv=sys.argv;sys.argv=[str(WORK/name)]
        try:
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                try:runpy.run_path(str(WORK/name),run_name='__main__')
                except SystemExit as error:assert error.code==0
            value=json.loads(captured.getvalue());assert value['state']=='NO_OP_DISPOSABLE_COLD_FIXTURE'
            defaults.append({'source':name,'result':value})
        finally:sys.argv=argv
    for name,pin in PINS.items():assert sha(WORK/name)==pin,name
    report={'schema':'STAGE05_DISPOSABLE_COLD_FIXTURE_SOURCE_PEER_V1',
      'state':'PASS_SOURCE_ONLY_ACTUAL_DISPOSABLE_KERNEL_DRVFS_FIXTURE_NOT_RUN',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':sha(__file__),
      'frozen_sources':PINS,'original_function_AST_counts':ast_counts,'pure_tests':tests.testsRun,
      'test_failures':len(tests.failures),'test_errors':len(tests.errors),'test_output':output.getvalue(),
      'actual_main_default_NOOPs':defaults,'operational_adoption_blockers':[],
      'scope_review':[
        'Only a fresh directly contained C disposable.ext4 of64MiB and fixed nonce mount are writable; original image and mount argv absent from fixture commands.',
        'Existing original byte WorkflowLock/lease/mount/native guards and one-command reader preserved; no second controller hierarchy.',
        'Original coldv2 functions, including checked unlock/receipt/STOP and bounded final publication fault handling, are AST-identical.',
        'Windows retained GENERIC_READ/FILE_SHARE_READ guard inherits reviewed owner-binding/check/checked-close/failed-close retention; exact fresh path/file identity/type/size guarded.',
        'Real future O_RDWR before/during/after sharing controls, kernel RO loop+noload+EROFS, complete public payload/metadata/hardlink/symlink/xattrs and detach/process exclusion are required by source.',
        'Finite25-phase/source/nonce/boot/hash/argv/count ledger with unchanged native closure readback, current original proof equality and exactf64 runtime rediscovery required.'
      ],
      'nonblocking_findings':[
        {'kind':'FAIL_CLOSED_PARTIAL_PHASE_PUBLICATION_WINDOW','detail':'Linux uses the unchanged direct final-path write_new; Windows can observe08/16 existence before JSON write/fsync completes and reject. This cannot grant PASS and preserves STOP, but could require root reconciliation after an otherwise healthy fixture.'}
      ],
      'required_before_actual':['Publish exact reviewed bytes and verify remote readback.','Obtain actual first scientific owner/client/native closure and original checked unlock; no active science.','Fresh original authority/STOP/boot/toolchain/runtime/resources must pass; this source review supplies none of those actual facts.'],
      'actual_disposable_fixture_WSL_UNC_lock_handles_mounts_signals_images':'NOT_RUN',
      'actual_production_inventory_capture_rawsplit_upload_restore_cleanup':'NOT_RUN',
      'biological_result_or_absence':'NOT_CREATED','safe_original_image_cold_adoption':'REQUIRES_ACTUAL_DISPOSABLE_FIXTURE_PEER_AND_SEPARATE_PRODUCTION_GATES'}
    path=WORK/'stage5_disposable_cold_fixture_source_independent_review01.json'
    assert not path.exists(),'Preserve existing peer receipt'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'state':report['state'],'review':str(path),'sha256':sha(path),'tests':tests.testsRun}))

if __name__=='__main__':main()
