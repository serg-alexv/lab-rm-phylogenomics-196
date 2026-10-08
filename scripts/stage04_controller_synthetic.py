#!/usr/bin/env python3
"""Controller failure/resume tests; fake scientific files, no Git or biology."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import stage04_controller as c


def run():
    results = []
    def rejected(name, operation):
        try:
            operation()
        except (ValueError, KeyError):
            results.append(name)
            return
        raise AssertionError('Malformed fixture accepted: ' + name)
    with tempfile.TemporaryDirectory(prefix='controller-synthetic-', dir=Path(__file__).parent) as temporary:
        root = Path(temporary)
        identity = {'SYNTHETIC_ONLY': True}
        invocation = 'SYNTHETIC_INVOCATION'
        def exit_record(code=0):
            return {'execution':'ACTUAL_LINUX_PHASE_CHILD_EXITED','identity':identity,'invocation_id':invocation,
                    'exit_code':code,'elapsed_seconds':.1,'child_cpu_seconds':0,'children_max_rss_bytes':0}
        def monitor_fixture(name, status='VERIFIED_ACTIVE_EXACT_LINUX_JOB', publication_error=False, code=0):
            directory = root / name
            directory.mkdir()
            c.atomic(directory/'linux_launch_receipt.json', {'synthetic':True})
            calls = []
            def inspection():
                calls.append('inspect')
                return {'identity':identity,'invocation_id':invocation,'status':status}
            def publish():
                calls.append('publish')
                if publication_error:
                    raise ValueError('SYNTHETIC_PUBLICATION_DENIAL')
            def sleeper(seconds):
                calls.append('wait_existing_job')
                c.atomic(directory/'linux_exit_receipt.json', exit_record(code))
            with patch.object(c.time,'sleep',sleeper):
                result = c.monitor(directory, identity, invocation, None, inspection, publish, 300, 5)
            return directory,calls,result
        directory,calls,result = monitor_fixture('active_then_exit')
        assert calls == ['publish','inspect','wait_existing_job'] and result['exit_code']==0
        results.append('verified_existing_job_monitored_to_actual_exit')
        directory,calls,result = monitor_fixture('observer_pending',status='LAUNCHER_ALIVE_JOB_EXIT_RECEIPT_PENDING')
        assert result['exit_code']==0
        results.append('observer_pending_exit_write_waits_without_duplicate')
        directory=root/'bad_exit';directory.mkdir();c.atomic(directory/'linux_exit_receipt.json',exit_record(9))
        rejected('nonzero_actual_exit_is_not_scientific_pass',lambda:c.monitor(directory,identity,invocation,None,lambda:{},lambda:None))
        bad=exit_record();bad['identity']={'WRONG':True};c.atomic(directory/'linux_exit_receipt.json',bad)
        rejected('exit_identity_mismatch_rejected',lambda:c.exit_gate(directory,identity,invocation))
        bad=exit_record();bad['invocation_id']='OTHER';c.atomic(directory/'linux_exit_receipt.json',bad)
        rejected('exit_invocation_mismatch_rejected',lambda:c.exit_gate(directory,identity,invocation))
        rejected('lost_observer_live_job_blocks_no_duplicate',lambda:monitor_fixture('lost_observer',status='ACTIVE_EXACT_JOB_BUT_LAUNCHER_LOST_NO_DUPLICATE_PERMITTED'))
        rejected('stale_pid_without_exit_receipt_blocks',lambda:monitor_fixture('stale_pid',status='NO_ACTIVE_MATCHING_PID_AND_NO_EXIT_RECEIPT_BLOCKER'))
        rejected('publication_failure_waits_existing_job_then_blocks',lambda:monitor_fixture('publication_denied',publication_error=True))
        assert (root/'publication_denied/linux_exit_receipt.json').is_file()
        assert c.load(root/'publication_denied/progress_publication_failure.json')['action'].startswith('Continue monitoring')
        results.append('publication_failure_preserves_actual_child_exit_evidence')
        assert c.PHASES == ('align','validate_alignment','trees','validate_final')
        results.append('independent_alignment_gate_precedes_topology')
        args=SimpleNamespace(root=root,output=root/'output',alignment_validation=root/'alignment',final_validation=root/'final',validator=Path(c.__file__))
        for path in (args.output,args.alignment_validation,args.final_validation):path.mkdir()
        for name in ('analysis_freeze.json','analysis_alignment_manifest.json'):c.atomic(args.output/name,{'synthetic':name})
        alignment={'execution':'ALL_PRIMARY_ALIGNMENTS_AND_FOUR_CONCATENATIONS_CONSTRUCTED','analyses':[1,2,3,4],
                   'analysis_freeze_sha256':c.digest(args.output/'analysis_freeze.json'),
                   'analysis_manifest_sha256':c.digest(args.output/'analysis_alignment_manifest.json')}
        c.atomic(args.output/'alignment_summary.json',alignment)
        assert c.result_gate(args,'align')['scientific_gate']=='CONSTRUCTION_ONLY_INDEPENDENT_GATE_REQUIRED'
        results.append('exit0_alignment_construction_distinguished_from_pass')
        check={'status':'PASS_ALIGNMENT_FORMATS_AND_PARTITIONS','analyses_verified':4,'primary_tip_ids':196,
               'analysis_freeze_sha256':c.digest(args.output/'analysis_freeze.json'),
               'analysis_manifest_sha256':c.digest(args.output/'analysis_alignment_manifest.json'),
               'alignment_summary_sha256':c.digest(args.output/'alignment_summary.json'),
               'validator_source_sha256':c.digest(args.validator)}
        c.atomic(args.alignment_validation/'validation_summary.json',check)
        assert c.result_gate(args,'validate_alignment')['scientific_gate']==check['status']
        results.append('independent_196_tip_four_analysis_gate')
        check['primary_tip_ids']=195;c.atomic(args.alignment_validation/'validation_summary.json',check)
        rejected('195_tip_silent_pruning_rejected',lambda:c.result_gate(args,'validate_alignment'))
        check['primary_tip_ids']=196;check['alignment_summary_sha256']='0'*64;c.atomic(args.alignment_validation/'validation_summary.json',check)
        rejected('stale_independent_summary_hash_rejected',lambda:c.result_gate(args,'validate_alignment'))
        script=root/'flags.py';script.write_text("p.add_argument('--orthology-config')\np.add_argument('--original-marker-validation')\n")
        assert c.supported_flags(script)=={'--orthology-config','--original-marker-validation'}
        results.append('actual_parser_flags_checked_before_v2_launch')
        phase_args=SimpleNamespace(root=root,host_env=root/'native',markers=root/'curated',producer=root/'producer.py',
                   validator=root/'validator.py',marker_validation=root/'current_validation.json',marker_publication=root/'publication.json',
                   config=root/'original_config.json',output=root/'output',resource_receipt=root/'resources.json',
                   alignment_validation=root/'alignment',final_validation=root/'final',iqtree_memory_mib=1536,
                   orthology_config=root/'orthology_config.json',original_marker_validation=root/'original_validation.json',original_markers=root/'original')
        for phase in c.PHASES:
            argv=c.phase_command(phase_args,phase)
            assert all(flag in argv for flag in ('--orthology-config','--original-markers','--original-marker-validation'))
            assert argv[argv.index('--markers')+1]==c.linux_path(phase_args.markers)
            assert '--redo' not in argv and '--redo-tree' not in argv
            if phase.startswith('validate_'):
                assert argv[argv.index('--marker-validation')+1]==c.linux_path(phase_args.marker_validation)
                assert argv[argv.index('--producer-source')+1]==c.linux_path(phase_args.producer)
        results.append('all_four_phases_receive_current_view_and_original_integrity_paths')
        results.append('validators_bind_actual_current_producer_source')
        c.atomic(root/'atomic.json',identity);assert c.load(root/'atomic.json')==identity
        assert not list(root.glob('*.tmp'))
        results.append('atomic_checkpoint_written_without_sentinel_assumption')
        assert c.SECRET.search(b'ghp_' + b'X'*40)
        assert c.SECRET.search(b'Authorization: Bearer '+b'X'*30)
        assert not c.SECRET.search(b'command=MAFFT --auto --thread 2')
        results.append('public_progress_credential_patterns_blocked')
        if sys.platform=='win32':
            lockpath=root/'synthetic_workflow.lock'
            with c.WorkflowLock(lockpath):
                rejected('held_kernel_byte_lock_blocks_second_owner',lambda:c.WorkflowLock(lockpath).__enter__())
            with c.WorkflowLock(lockpath):pass
            results.append('released_byte_lock_reusable_without_file_deletion')
        c.atomic(Path(__file__).parent/'stage04_controller_synthetic_results.json',
                 {'status':'PASS_SYNTHETIC_CONTROLLER_FIXTURES','fixtures':results,'count':len(results),
                  'biological_jobs_run':0,'git_commands_run':0,'production_lock_touched':False})
        print(json.dumps({'status':'PASS_SYNTHETIC_CONTROLLER_FIXTURES','count':len(results),'fixtures':results},indent=2))


if __name__=='__main__':run()
