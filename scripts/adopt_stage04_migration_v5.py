"""Adopt exact reviewed V5 sources only after actual resource-bound integration.

Missing/failed scientific or resource evidence raises before adoption writes.
This task publishes code; it never launches inference or repeats alignments.
"""
from pathlib import Path
from unittest.mock import patch
import hashlib, json, os, subprocess, sys
import stage04_controller as C
import stage04_inference_v5 as R
import production_resume as w
from workflow_publication import commit
ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
CANDIDATES=HISTORY/'.work/migration_review'
PARENT=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\referenced-chatgpt-conversation-this-is-an\outputs')
NEW_SOURCES=('stage04_inference_v5.py','stage04_inference_controller_v5.py',
             'stage04_inference_validate_v5.py','resume_stage04_inference_v5.py',
             'stage04_migration_support_v5.py','stage04_migration_wsl_v5.sh','host_inference_stage04_v5.json')

def actual_ready(root):
    ready=C.load(root/'reports/stage04/migration_v5_ready_for_adoption.json')
    C.check(ready['status']=='PASS_ACTUAL_G_SOURCE_BOOTSTRAP_ARGV_PRODUCER_RESOURCE_BOUNDARY_READY_FOR_CODE_ADOPTION'
            and ready['actual_native_exit']==0 and ready['native_inference']=='NOT_RUN' and ready['full_stage04']=='INCOMPLETE',
            'Actual measured integration required; no synthetic/sentinel adoption')
    refs={'source_report_sha256':'reports/stage04/migration_v5_native_source_check.json',
          'producer_boundary_report_sha256':'reports/stage04/migration_v5_actual_producer_boundary.json',
          'resource_receipt_sha256':'reports/stage04/resumed_inference_resource_preflight_v5.json'}
    for field,name in refs.items():C.check(ready[field]==C.digest(root/name),'Actual ready binding changed: '+field)
    measured=ready['actual_fresh_resources']
    C.check(measured['windows']['available_bytes']>=R.WINDOWS_MIN
            and measured['windows_after_wsl']['available_bytes']>=R.WINDOWS_MIN
            and measured['linux']['linux_available_bytes']>=R.LINUX_MIN,'Actual full memory admission was not passed')
    return ready

def main():
    C.check(sys.platform=='win32' and Path.cwd().resolve()==ROOT,'Dedicated G Windows adoption owner required')
    w.LOG=ROOT/'reports/stage04/migration_v5_adoption_commands.jsonl'
    with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
        C.reconcile(ROOT)
        receipt_path=ROOT/'reports/stage04/inference_v5_adoption.json'
        C.check(not receipt_path.exists(),'Initial adoption already exists; verify it and use the published resume wrapper')
        ready=actual_ready(ROOT)
        manifest=C.load(CANDIDATES/'candidate_manifest.json')
        C.check(C.digest(CANDIDATES/'candidate_manifest.json')=='771836af40f20c4aaff94ba8f8f44d941f2923748531b408ae49be986570506a', 'Reviewed candidate manifest changed')
        current=[]
        for name in NEW_SOURCES:
            rel=('config/' if name.endswith('.json') else 'scripts/')+name
            expected=manifest['files'][name]
            C.check(C.digest(ROOT/rel)==C.digest(CANDIDATES/name)==expected['sha256']
                    and (ROOT/rel).stat().st_size==expected['bytes'],'Reviewed candidate differs: '+name)
            current.append(rel)
        with patch.object(sys,'argv',['adoption','--failed-attempt','.work/stage04_phylogeny_v2/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json']):args=R.parse()
        identity,analyses=R.input_identity(args,native=False)
        native=C.load(ROOT/'reports/stage04/migration_v5_actual_producer_boundary.json')
        source=C.load(ROOT/'reports/stage04/migration_v5_native_source_check.json')
        C.check(native['identity']==identity,
                'Actual native producer identity differs from current Windows identity')
        C.check(identity['migration']==source['migration_identity'] and len(analyses)==4
                and native['resource_receipt_sha256']==C.digest(args.resource_receipt)
                and native['script_sha256']==C.digest(ROOT/'scripts/complete_migration_v5_resource_binding.py')
                and native['native_inference']=='NOT_RUN','Actual source/native producer/resource boundary changed')
        prior=C.load(ROOT/'reports/stage04/inference_v4_adoption.json')
        for item in prior['sources']:
            C.check(C.digest(ROOT/item['path'])==C.digest(HISTORY/item['path'])==item['sha256'],'Historical adopted source changed: '+item['path'])
        parent=C.load(ROOT/'reports/storage/20261008_v5_isolated_tests.json')
        C.check(parent['status']=='PASS_ISOLATED_V5_REGRESSIONS_AND_CLI_ROLE_INTEGRATION'
                and parent['source_files_unchanged'] is True and len(parent['tests'])==4
                and all(t['exit_code']==0 for t in parent['tests']) and parent['biological_jobs_run']==0,
                'Independent exact-candidate regression/integration review missing')
        for name in NEW_SOURCES:
            key=str(CANDIDATES/name)
            C.check(parent['production_sources_sha256'][key]==manifest['files'][name]['sha256'],'Independent reviewer did not test exact candidate: '+name)
        pub=ROOT/'reports/stage04/migration_v5_adoption_review';pub.mkdir(parents=True,exist_ok=True)
        (pub/'candidate_manifest.json').write_bytes((CANDIDATES/'candidate_manifest.json').read_bytes())
        (pub/'parent_path_review.json').write_bytes((PARENT/'PARENT_V5_INDEPENDENT_PATH_REVIEW.json').read_bytes())
        path_review=C.load(pub/'parent_path_review.json')
        C.check(path_review['path_fixtures_passed']==21 and path_review['actual_prior_adoption_sources']==27
                and path_review['actual_historical_copy_manifest_files']==85,'Independent path/historical review incomplete')
        copied=[]
        for test in parent['tests']:
            name=test['test'];path=PARENT/'PARENT_V5_SYNTHETIC_055zd9r7/DATA/scripts'/name
            C.check(C.digest(path)==test['test_sha256'],'Actual executed test source differs: '+name)
            destination=pub/name;(destination).write_bytes(path.read_bytes());copied.append(destination.relative_to(ROOT).as_posix())
            for stream in ['stdout','stderr']:
                source_path=Path(test[stream+'_path']);destination=pub/(name+'.'+stream+'.txt')
                destination.write_bytes(source_path.read_bytes());copied.append(destination.relative_to(ROOT).as_posix())
        method=ROOT/'reports/stage04/INFERENCE_V5.md'
        method.write_text('# Adopted explicit G data/C history inference revision\n\n'
            'The exact V5 producer, controller, independent checker and role/bootstrap support retain the independently reviewed bytes. All27 historical adopted source hashes,85 critical C/G input hashes,21 path fixtures and116 isolated regression/integration fixtures are preserved. Actual Windows-to-WSL bootstrap cwd, both native phase argv, full196/100-marker/four-concatenation source gate and actual measured producer resource binding passed separately before this adoption.\n\n'
            'Primary196 and fixed162, high-occupancy88-marker196 and high-contiguity155 sensitivities reuse the validated alignments. IQ-TREE3 ModelFinder with -p partitions, no merging,1000 UFBoot,1000 SH-aLRT, seed1961008, two threads, keep-ident and bootstrap trees. Native unsupported --mem remains omitted. Native3GiB and outer3.5GiB per-process address-space bounds; before/after-WSL Windows4.5GiB and Linux4GiB admission at each fresh phase. These are not an aggregate cgroup or a guarantee of continuing headroom; later native sufficiency remains unproven.\n\n'
            'Data/output/code on G; original source/control/failure receipts and tool image/environment at physical C. Stable C writer byte lock and exact qualified data:/historical: identities. No junction, old argv rewrite, source relaxation, alignment reexecution, scope reduction or automatic usage reset. Native phase exits and distinct full output checks plus portable Release/readback remain required; adoption is not scientific completion.\n',encoding='utf-8')
        source_paths=list(dict.fromkeys([item['path'] for item in prior['sources']]+current+
             ['scripts/adopt_stage04_migration_v5.py','scripts/complete_migration_v5_resource_binding.py','reports/stage04/INFERENCE_V5.md']))
        sources=[{'path':name,'sha256':C.digest(ROOT/name),'bytes':(ROOT/name).stat().st_size} for name in source_paths]
        value={'status':'REVIEWED_RESUMED_INFERENCE_V5_ADOPTED_BEFORE_TOPOLOGY','utc':C.now(),'actual_adoption_pid':os.getpid(),
               'sources':sources,'candidate_manifest_sha256':C.digest(CANDIDATES/'candidate_manifest.json'),
               'prior_v4_adoption_sha256':C.digest(ROOT/'reports/stage04/inference_v4_adoption.json'),
               'actual_ready_report_sha256':C.digest(ROOT/'reports/stage04/migration_v5_ready_for_adoption.json'),
               'actual_producer_identity':identity,'approved_assemblies':196,'analyses':4,
               'synthetic_producer_checks':36,'synthetic_independent_checker_checks':63,'synthetic_adoption_guards':7,'synthetic_cli_role_checks':10,'path_checks':21,
               'scientific_inference':'NOT_RUN_AT_ADOPTION','alignment_reexecution':False,'full_stage04':'INCOMPLETE',
               'resume_command':[str(HISTORY/'.tools/validation_env/Scripts/python.exe'),'-u','scripts/resume_stage04_inference_v5.py','--failed-attempt','.work/stage04_phylogeny_v2/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json'],
               'resume_cwd':str(ROOT),'fresh_inference_memory_gate':'UNCHANGED_AND_REQUIRED_AGAIN',
               'publication_protocol':'Exact adopted code and initial receipt compared to origin/main under stable C byte lock before actual phases'}
        C.atomic(receipt_path,value)
        from resume_stage04_inference_v5 import verify_adoption
        verify_adoption(ROOT)
        w.status('4_phylogeny','V5_ADOPTED_ACTUAL_INFERENCE_NOT_YET_STARTED','PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
                 'STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING','Exact reviewed V5 sources adopted after actual G bootstrap/source/argv/producer/resource integration. This publication precedes native inference; fresh memory admission and all four native output/independent validation gates remain required.')
        paths=source_paths+copied+['reports/stage04/migration_v5_adoption_review/candidate_manifest.json',
            'reports/stage04/migration_v5_adoption_review/parent_path_review.json','reports/stage04/inference_v5_adoption.json',
            'reports/stage04/migration_v5_ready_for_adoption.json','reports/stage04/migration_v5_actual_producer_boundary.json',
            'reports/stage04/migration_v5_actual_producer_boundary.time.txt','reports/stage04/resumed_inference_resource_preflight_v5.json',
            'reports/stage04/migration_v5_resource_binding_commands.jsonl','STATUS.md','status/stages.tsv']
        head=commit(paths,'Adopt reviewed explicit G/C inference revision after actual measured integration')
        C.command(ROOT,['git','fetch','origin','main']);verify_adoption(ROOT,remote=True,expected_receipt_sha256=C.digest(receipt_path))
        for name in paths:
            remote=subprocess.run(['git','show','origin/main:'+name],cwd=ROOT,capture_output=True,check=True).stdout
            C.check(hashlib.sha256(remote).hexdigest()==C.digest(ROOT/name),'Remote adoption evidence bytes differ: '+name)
        C.atomic(ROOT/'status/migration_v5_adoption_publication.json',{'status':'REMOTE_ALL_ADOPTION_SOURCE_AND_EVIDENCE_BYTES_VERIFIED',
            'utc':C.now(),'commit':head,'adoption_receipt_sha256':C.digest(receipt_path),'native_inference':'NOT_RUN'})
        print('ACTUAL_V5_ADOPTION_ALL_REMOTE_BYTES_VERIFIED '+head,flush=True)

if __name__=='__main__':main()
