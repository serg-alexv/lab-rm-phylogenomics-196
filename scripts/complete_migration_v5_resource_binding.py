"""Complete the actual producer boundary only after unchanged measured admission."""
from pathlib import Path
from unittest.mock import patch
import json, os, sys
ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
sys.path.insert(0,str(ROOT/'scripts'))

def producer_args():
    import stage04_inference_v5 as R
    with patch.object(sys,'argv',['resource_boundary','--failed-attempt',
        '.work/stage04_phylogeny_v2/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json']):return R.parse()

def native():
    import stage04_inference_v5 as R
    import stage04_inference_validate_v5 as V
    args=producer_args();identity,analyses=R.input_identity(args,native=True)
    migration=V.independent_migration_identity(args)
    R.require(identity['migration']==migration and Path.cwd().resolve()==ROOT,'Actual resource-bound producer migration differs')
    R.save(ROOT/'reports/stage04/migration_v5_actual_producer_boundary.json',
           {'status':'PASS_ACTUAL_NATIVE_PRODUCER_INPUT_IDENTITY_AND_MEASURED_RESOURCE_BINDING_NO_INFERENCE',
            'actual_pid':os.getpid(),'actual_python':sys.executable,'actual_cwd':str(Path.cwd()),
            'identity':identity,'analyses':analyses,'script_sha256':R.sha(__file__),
            'resource_receipt_sha256':R.sha(args.resource_receipt),'native_inference':'NOT_RUN'})
    print(json.dumps({'status':'PASS_ACTUAL_NATIVE_PRODUCER_BOUNDARY_NO_INFERENCE','pid':os.getpid(),'analyses':4}))

def windows():
    import stage04_controller as C
    import stage04_inference_controller_v5 as K
    import stage04_inference_v5 as R
    import production_resume as w
    w.LOG=ROOT/'reports/stage04/migration_v5_resource_binding_commands.jsonl'
    with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
        C.reconcile(ROOT)
        with patch.object(sys,'argv',['resource_boundary','--failed-attempt',
            '.work/stage04_phylogeny_v2/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json']):args=K.parse()
        C.atomic(HISTORY/'.work/workflow_owner.json',{'utc':C.now(),'pid':os.getpid(),'script':'G:scripts/complete_migration_v5_resource_binding.py',
            'scope':'Actual source/resource boundary, no native inference','data_root':str(ROOT)})
        C.LIMIT=R.OUTER;C.wsl=K.bounded_wsl
        measured=K.resource_preflight(args)
        identity,analyses=R.input_identity(producer_args(),native=False)
        command=['wsl','-d','Ubuntu','--','bash',C.linux_path(args.bootstrap),
                 '/usr/bin/time','-v','-o',C.linux_path(ROOT/'reports/stage04/migration_v5_actual_producer_boundary.time.txt'),
                 C.linux_path(args.host_env/'bin/python'),'-u',C.linux_path(Path(__file__)),'--native-resource-boundary']
        w.run(command,timeout=180)
        actual=C.load(ROOT/'reports/stage04/migration_v5_actual_producer_boundary.json')
        C.check(actual['identity']==identity and actual['script_sha256']==C.digest(__file__)
                and len(actual['analyses'])==4 and actual['native_inference']=='NOT_RUN','Actual Windows/Linux producer identity differs')
        source=C.load(ROOT/'reports/stage04/migration_v5_native_source_check.json')
        C.check(source['migration_identity']==identity['migration'] and source['actual_windows_phase_argv_native_parse_checks']==['trees','validate_final'],
                'Previously executed independent source/argv gates no longer bind actual data')
        w.js(ROOT/'reports/stage04/migration_v5_ready_for_adoption.json',
             {'utc':w.now(),'status':'PASS_ACTUAL_G_SOURCE_BOOTSTRAP_ARGV_PRODUCER_RESOURCE_BOUNDARY_READY_FOR_CODE_ADOPTION',
              'source_report_sha256':C.digest(ROOT/'reports/stage04/migration_v5_native_source_check.json'),
              'producer_boundary_report_sha256':C.digest(ROOT/'reports/stage04/migration_v5_actual_producer_boundary.json'),
              'resource_receipt_sha256':C.digest(args.resource_receipt),'actual_fresh_resources':measured,
              'actual_native_argv':command,'actual_native_exit':0,'native_inference':'NOT_RUN',
              'full_stage04':'INCOMPLETE','later_memory_sufficiency':'UNPROVEN'})
        print('ACTUAL_V5_PRODUCER_RESOURCE_BOUNDARY_PASSED; ADOPTION_PUBLICATION_REQUIRED',flush=True)

if __name__=='__main__':
    if '--native-resource-boundary' in sys.argv:native()
    else:windows()
