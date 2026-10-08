"""Record executed migration source checks and unchanged pending resource gate."""
from pathlib import Path
import stage04_controller as C
import production_resume as w
from workflow_publication import commit
R=Path(__file__).resolve().parents[1]
H=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
w.LOG=R/'reports/stage04/migration_v5_progress_commands.jsonl'

def main():
    with C.WorkflowLock(H/'.work/workflow.lock'):
        C.reconcile(R)
        bridge=C.load(R/'reports/stage04/migration_v5_actual_interoperability.json')
        native=C.load(R/'reports/stage04/migration_v5_native_source_check.json')
        C.check(bridge['actual_native_exit']==0 and bridge['native_inference_started'] is False
                and native['approved_assemblies']==196 and native['markers_rechecked']==100
                and native['actual_windows_phase_argv_native_parse_checks']==['trees','validate_final']
                and native['producer_resource_binding']=='PENDING_HEADROOM; NO_PLACEHOLDER_RECEIPT'
                and bridge['native_report_sha256']==C.digest(R/'reports/stage04/migration_v5_native_source_check.json'),
                'Actual source/argv bridge evidence differs')
        snapshot=C.windows_snapshot(R)
        w.js(R/'reports/stage04/migration_v5_readiness_progress.json',
             {'utc':w.now(),'execution':'WAITING_MEASURED_HEADROOM_AFTER_ACTUAL_G_SOURCE_MAPPING_CHECKS',
              'actual_windows_snapshot':snapshot,'required_windows_available_bytes':4831838208,
              'required_linux_available_bytes':4294967296,'actual_source_audit_native_pid':native['actual_native_probe_pid'],
              'actual_source_audit_exit':0,'source_audit_wall_seconds':120.44,'source_audit_cpu_seconds':10.19,
              'source_audit_peak_rss_bytes':126512*1024,'resource_measurement':'Native /usr/bin/time -v; these are source-audit metrics, no IQ-TREE computation',
              'source_inputs_identical':len(native['migration_identity']['copied_input_sha256']),
              'actual_bootstrap_cwd':native['actual_cwd'],'pinned_tool_prefix':native['actual_host_tool_prefix'],
              'candidate_adoption':'NOT_ADOPTED','actual_producer_resource_binding':'PENDING_REAL_PASSED_ADMISSION',
              'native_inference_started':False,'stage05_stage06_stage07':'NOT_RUN','waiting_authority':'Latest user explicitly chose waiting for headroom',
              'no_automatic_usage_reset':True,'prior_sources_and_failures_preserved':True})
        w.atomic(R/'reports/stage04/MIGRATION_V5_PROGRESS.md',
            ('# Executed V5 migration preconditions and current resource wait\n\n'
             'The full52744-file directional copy gate and GitHub reconciliation were completed and published before these checks. All27 original adopted source rows and85 critical historical/data copies retain their recorded hashes. New V5 candidate bytes remain unchanged and unadopted. Independent parent tests passed116 isolated regression/integration fixtures plus21 path guards; actual G native interoperability is separate evidence.\n\n'
             'The Windows-emitted primary and independent-checker phase argv were parsed by their actual native Linux programs and retained the same qualified G data/C historical/tool roles. The actual C bootstrap mounted G, reused the existing C tool image/environment, entered G and performed a distinct full196/100-marker/four-concatenation source audit. Exit0, wall120.44s, CPU10.19s, peakRSS129548288bytes. It checked actual G fsync/atomic replace/readback, both historical failures and the current A8 old-source dependency. One Windows-to-WSL startup cwd translation warning was retained in the command log; the explicit bootstrap subsequently established and verified the exact G native cwd, so no alternate data root was used.\n\n'
             'Production requires Windows availability at least4831838208bytes before and after the WSL resource probe and Linux availability at least4294967296bytes. Two real attempts were rejected; original numerical snapshots remain preserved. The separate lightweight source audit did not waive the production admission requirement or invent a producer resource receipt. Its resource binding remains pending. New inference/ML/support outputs do not exist.\n\n'
             'Next: retain unchanged candidate/code/history, wait for measured headroom, complete actual measured producer boundary and reviewed V5 adoption/publication, then run four serial full-scope inferences and independent final checks. Both full196 detectors/evidence review,196-tip/784-cell figure and final handoff remain mandatory dependent work. No automatic account reset, unrelated termination, future reboot or source rewrite is authorized here.\n').encode())
        w.status('4_phylogeny','WAITING_HEADROOM_AFTER_V5_SOURCE_MAPPING_AUDIT','PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
                 'STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING',
                 'Actual G bootstrap/CLI/root mapping and full196/100-marker/four-alignment source audit passed; V5 candidate adoption and real producer resource binding remain pending. Waiting for unchanged4.5GiB Windows/4GiB Linux headroom. No new IQ-TREE result or downstream biological work has run.')
        paths=['scripts/check_stage04_migration_v5.py','scripts/publish_migration_v5_source_progress.py',
               'reports/stage04/migration_v5_actual_commands.jsonl','reports/stage04/migration_v5_actual_interoperability.json',
               'reports/stage04/migration_v5_windows_cli_check.json','reports/stage04/migration_v5_native_source_check.json',
               'reports/stage04/migration_v5_native_source.time.txt','reports/stage04/migration_v5_read_only_resource_snapshot.json',
               'reports/stage04/migration_v5_readiness_progress.json','reports/stage04/MIGRATION_V5_PROGRESS.md',
               'reports/stage04/migration_probe_revisions/initial_probe_848a971b.py.txt',
               'reports/stage04/migration_probe_revisions/initial_resource_rejection_184152.json',
               'reports/stage04/migration_probe_revisions/revised_probe_windows_phase_only.py.txt',
               'reports/stage04/migration_probe_revisions/second_resource_rejection.json','STATUS.md','status/stages.tsv']
        head=commit(paths,'Publish actual G native source interoperability and honest production headroom wait')
        C.command(R,['git','fetch','origin','main'])
        C.check(C.command(R,['git','rev-parse','origin/main'])==head,'Remote source-progress commit differs')
        import subprocess,hashlib
        for name in paths:
            data=subprocess.run(['git','show','origin/main:'+name],cwd=R,capture_output=True,check=True).stdout
            C.check(hashlib.sha256(data).hexdigest()==C.digest(R/name),'Remote source-progress bytes differ: '+name)
        print('REMOTE_SOURCE_INTEROPERABILITY_PROGRESS_BYTES_VERIFIED '+head,flush=True)

if __name__=='__main__':main()
