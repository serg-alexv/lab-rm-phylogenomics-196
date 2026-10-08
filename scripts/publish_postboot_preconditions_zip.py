"""Portable executed postboot preconditions; no biological completion claim."""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, zipfile
import stage04_controller as C
import production_resume as w
from portable_release import make_zip, publish_frozen, verify_zip
from workflow_publication import check, commit
ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
PUBLIC=ROOT/'reports/stage00r'
STAGING=ROOT/'release_staging/stage00r'
TAG='stage00r-postboot-preconditions196-v1'

def main():
    w.LOG=PUBLIC/'publication_commands.jsonl'
    with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
        C.reconcile(ROOT)
        C.check(not (ROOT/'reports/stage04/inference_v5_adoption.json').exists(), 'V5 adoption already changed this preconditions scope; preserve outputs and review a new release')
        PUBLIC.mkdir(parents=True,exist_ok=True);STAGING.mkdir(parents=True,exist_ok=True)
        plan=ROOT/'status/stage00r_publication_plan.json'
        if not plan.exists() and not (PUBLIC/'asset_manifest.json').exists():
            source=C.load(ROOT/'reports/stage04/migration_v5_native_source_check.json')
            selection=C.load(ROOT/'reports/stage05/preparation_selection_v4/review.json')
            C.check(source['approved_assemblies']==196 and source['markers_rechecked']==100
                    and source['actual_windows_phase_argv_native_parse_checks']==['trees','validate_final']
                    and source['producer_resource_binding']=='PENDING_HEADROOM; NO_PLACEHOLDER_RECEIPT','Actual source-only preparation differs')
            C.check(selection['installed_native_R_cases']==17 and selection['python_negative_and_regression_tests']==24,
                    'Actual installed-native synthetic review differs')
            snapshot=C.windows_snapshot(ROOT)
            C.atomic(PUBLIC/'execution_scope.json',{'status':'EXECUTED_POSTBOOT_PRECONDITIONS_AND_DOCUMENTED_RESOURCE_WAIT_ONLY',
                'observed_utc':C.now(),'approved_assemblies':196,'marker_alignments_rechecked':100,'concatenations_rechecked':4,
                'copied_critical_input_hashes_verified':85,'historical_adopted_source_hashes_verified':27,
                'native_source_wall_seconds':120.44,'native_source_cpu_seconds':10.19,'native_source_peak_rss_bytes':129548288,
                'installed_native_selection_synthetic_cases':17,'selection_python_regressions':24,
                'synthetic_selection_wall_seconds':2.32,'synthetic_selection_cpu_seconds':1.48,'synthetic_selection_peak_rss_bytes':112668672,
                'windows_observation_at_packaging':snapshot,'required_production_windows_before_and_after_wsl_bytes':4831838208,
                'required_production_linux_bytes':4294967296,'v5_adoption':'NOT_ADOPTED_AT_PACKAGING',
                'producer_resource_boundary':'PENDING','inference':'NOT_RUN_V5','full_stage04':'INCOMPLETE',
                'stage05_stage06_stage07':'NOT_RUN','scientific_completion_from_synthetic_fixtures':False,
                'drive_cloud_sync_durability':'NOT_VERIFIED; local directional copy/hash gate only'})
            notes=('# Executed WD postboot preconditions, full196 retained\n\n'
                'This release preserves the actual storage-copy/source/CLI/bootstrap checks and synthetic native-detector selection review performed after reboot. It is a preparation/resource-wait artifact, not a completed phylogeny or biological R-M inventory. Stage02 all196 sequence integrity, Stage03 all196/100 markers and Stage04a all100 alignments/four concatenations were already independently validated and published; none were redownloaded or recomputed.\n\n'
                'The directional C-to-G gate independently checked52744 included files and9852158003bytes. G is streamed DriveFS using C cache, not an independent physical disk or proven cloud upload. Old history/tool prefixes and byte locks stay physical C. Exact new G native cwd and atomic readback,27 old sources,85 critical copied inputs, both actual phase argv and a full196 source/alignment recheck passed. New V5 sources are exact reviewed candidates and remain NOT_ADOPTED pending actual measured producer-resource integration. Historical receipts/argv were preserved.\n\n'
                'Production admission remains4.5GiB Windows before and after WSL and4GiB Linux; actual rejections are evidence, not successful inference. Two-thread/native3GiB/outer3.5GiB per-process limits are unchanged. Both PADLOC and DefenseFinder production, architecture/partial/source evidence review,196-tip/784-cell figure and final independent handoff remain NOT_RUN.\n\n'
                'The coordinate grouping repair passed24 Python regressions and17 evaluations of expressions parsed from the exact installed PADLOC2 R source. These synthetic cases searched no biological sequences and do not prove systems or absence. Actual first-attempt mount failure and observer lock-contention stop are preserved with tested successors. Live execution status and publication receipts are separate from this immutable snapshot.\n\n'
                'Download the standalone ZIP and its SHA256 sidecar. Open/extract with normal Windows Explorer or PowerShell; no WSL is needed to read MD/JSON/TSV/source files. Biological FASTA/alignments are in the previous Stage02/Stage03/Stage04a release ZIPs. Every ZIP member has a SHA256 entry. No tool image, raw private session logs, authentication material or unrelated files are included.\n')
            (PUBLIC/'REPORT.md').write_text(notes,encoding='utf-8');(PUBLIC/'RELEASE_NOTES.md').write_text(notes,encoding='utf-8')
            paths=['scripts/publish_postboot_preconditions_zip.py','reports/stage00r/execution_scope.json','reports/stage00r/REPORT.md','reports/stage00r/RELEASE_NOTES.md',
                'config/approved_accessions.txt','config/approval.json','config/host_inference_stage04_v5.json',
                'scripts/stage04_inference_v5.py','scripts/stage04_inference_controller_v5.py','scripts/stage04_inference_validate_v5.py',
                'scripts/resume_stage04_inference_v5.py','scripts/stage04_migration_support_v5.py','scripts/stage04_migration_wsl_v5.sh',
                'scripts/check_stage04_migration_v5.py','scripts/complete_migration_v5_resource_binding.py',
                'scripts/adopt_stage04_migration_v5.py','scripts/wait_migration_v5_headroom_v2.py','scripts/test_waiter_writer_serialization_v2.py',
                'scripts/stage05_padloc_selection_v3.py','scripts/test_stage05_padloc_selection_v3.py','scripts/check_stage05_padloc_selection_native_v3.R',
                'scripts/review_stage05_selection_v3.py','scripts/review_stage05_selection_v4.py','scripts/stage05_detector_env_v5.sh',
                'reports/storage/20261008_completed_copy_gate.json','reports/stage04/migration_v5_actual_interoperability.json',
                'reports/stage04/migration_v5_windows_cli_check.json','reports/stage04/migration_v5_native_source_check.json',
                'reports/stage04/migration_v5_native_source.time.txt','reports/stage04/migration_v5_read_only_resource_snapshot.json',
                'reports/storage/20261008_v5_isolated_tests.json','reports/stage05/preparation_coordinate_audit/summary.json',
                'reports/stage04/resource_wait_v5_v2/serialization_test.json','reports/stage04/resource_wait_v5_v2/actual_contention_child.json',
                'reports/stage04/resource_wait_v5_v2/prior_observer_stop.json',
                'scripts/portable_release.py','scripts/validate_windows_zip.ps1','scripts/workflow_publication.py','scripts/production_resume.py']
            # Explicit reviewed report subtrees, no ignored caches or raw data.
            for folder in ['reports/stage05/preparation_selection_v3','reports/stage05/preparation_selection_v4']:
                paths.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*') if p.is_file())
            C.check(len(paths)==len(set(paths)),'Repeated payload paths')
            check(paths)
            asset=make_zip(STAGING/'stage00r-full196-postboot-preconditions.zip',[(ROOT/name,name) for name in paths],
                'WD full196 postboot preconditions only. No completed V5 phylogeny/R-M inventory.\nExtract using Windows Explorer or PowerShell; all member hashes are in SHA256SUMS.txt.\nRead reports/stage00r/REPORT.md and use GitHub STATUS.md for current execution.\n')
            C.atomic(PUBLIC/'asset_manifest.json',{'stage':'stage00r','approved_assemblies':196,'assets':[asset],
                'scientific_scope':'EXECUTED_STORAGE_SOURCE_MAPPING_AND_SYNTHETIC_PREPARATION_ONLY',
                'full_stage04':'INCOMPLETE','v5_sources':'REVIEWED_CANDIDATES_NOT_ADOPTED',
                'payload_file_sha256':{name:C.digest(ROOT/name) for name in paths},'mutable_receipts_and_live_status_excluded':True})
            paths.append('reports/stage00r/asset_manifest.json')
            (PUBLIC/'SHA256SUMS.txt').write_text(''.join(C.digest(ROOT/name)+'  '+name+'\n' for name in sorted(paths)),encoding='utf-8')
            paths.append('reports/stage00r/SHA256SUMS.txt')
            C.atomic(STAGING/'payload_paths.json',paths)
        else:paths=C.load(STAGING/'payload_paths.json')
        manifest=C.load(PUBLIC/'asset_manifest.json')
        for name,value in manifest['payload_file_sha256'].items():C.check(C.digest(ROOT/name)==value,'Frozen preconditions payload changed: '+name)
        asset=manifest['assets'][0];archive=STAGING/asset['asset_name']
        C.check(C.digest(archive)==asset['sha256'] and verify_zip(archive)==asset['payload_members'],'Frozen preconditions ZIP differs')
        extraction=ROOT/'.work/postboot_windows_zip'/asset['sha256'][:12]
        helper=ROOT/'scripts/validate_windows_zip.ps1'
        shell=Path(shutil.which('pwsh')).resolve()
        native_command=[str(shell),'-NoProfile','-File',str(helper),
                        '-ZipPath',str(archive),'-ExpectedSha256',asset['sha256'],'-Destination',str(extraction)]
        if extraction.exists():
            result=C.load(PUBLIC/'windows_extraction_receipt.json')
            C.check(result['native_helper_sha256']==C.digest(helper) and result['native_shell_sha256']==C.digest(shell),
                    'Original Windows extraction tool bytes changed')
            with zipfile.ZipFile(archive) as zipped:
                C.check({p.relative_to(extraction).as_posix() for p in extraction.rglob('*') if p.is_file()}==set(zipped.namelist()),
                        'Original Windows extracted member set changed')
                for name in zipped.namelist():
                    with zipped.open(name) as stream:
                        C.check(C.digest(extraction/name)==hashlib.file_digest(stream,'sha256').hexdigest(),
                                'Original Windows extracted member differs: '+name)
        else:
            result=json.loads(w.run(native_command,timeout=120))
            result.update(native_helper_sha256=C.digest(helper),native_shell_sha256=C.digest(shell),actual_native_argv=native_command)
        C.check(result['status']=='PASS_NATIVE_WINDOWS_EXTRACTION_AND_ALL_MEMBER_HASHES' and result['sha256']==asset['sha256']
                and result['payload_members_hash_verified']==asset['payload_members'],'Actual Windows extraction proof differs')
        C.atomic(PUBLIC/'windows_extraction_receipt.json',result)
        receipt=publish_frozen('stage00r',TAG,STAGING,PUBLIC/'asset_manifest.json',paths,
            'WD postboot full196 preconditions; inference resource admission still pending',PUBLIC/'RELEASE_NOTES.md')
        C.check(receipt['status']=='UPLOAD_VERIFIED','Actual release readback incomplete')
        receipt.update(scientific_scope=manifest['scientific_scope'],full_stage04='INCOMPLETE',v5_adoption='NOT_ADOPTED_AT_PAYLOAD_FREEZE',
            native_windows_extraction_validation=result['status'],native_windows_extraction_receipt_sha256=C.digest(PUBLIC/'windows_extraction_receipt.json'))
        C.atomic(PUBLIC/'publication_receipt.json',receipt)
        head=commit(['reports/stage00r/publication_receipt.json','reports/stage00r/windows_extraction_receipt.json',
                     'reports/stage00r/publication_progress.json','reports/stage00r/publication_commands.jsonl'],
                    'Verify native Windows extraction and remote postboot preconditions ZIP bytes')
        C.command(ROOT,['git','fetch','origin','main'])
        for name in ['reports/stage00r/publication_receipt.json','reports/stage00r/windows_extraction_receipt.json']:
            data=subprocess.run(['git','show','origin/main:'+name],cwd=ROOT,capture_output=True,check=True).stdout
            C.check(hashlib.sha256(data).hexdigest()==C.digest(ROOT/name),'Remote receipt bytes differ')
        print('POSTBOOT_PRECONDITIONS_WINDOWS_ZIP_AND_ACTUAL_REMOTE_BYTES_VERIFIED '+head,flush=True)

if __name__=='__main__':main()
