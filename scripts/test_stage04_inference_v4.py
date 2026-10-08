#!/usr/bin/env python3
"""Private synthetic argv/resource/native-proof/cache/resume fixtures; no biology."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import stage04_inference_v4 as R
import stage04_inference_controller_v4 as C3
from unittest.mock import patch


def run():
    results=[]
    def reject(name,operation):
        try:operation()
        except (ValueError,KeyError,FileNotFoundError):results.append(name);return
        raise AssertionError('Bad synthetic fixture accepted: '+name)
    policy_path=(Path.cwd()/'config/host_inference_stage04_v4.json' if Path(__file__).parent.name=='scripts'
                 else Path(__file__).with_name('host_inference_stage04_v4.json'))
    policy=R.read(policy_path)
    R.protocol(policy);results.append('frozen_full196_unchanged_partition_model_support_and_explicit_budget')
    for key,value in [('approved_assemblies',162),('iqtree_address_space_limit_bytes',3758096384),
                      ('maximum_compute_threads',16),('partition_option','-q'),('ultrafast_bootstrap_replicates',100),
                      ('alignment_reexecution',True),('native_memory_option','--mem1536M'),
                      ('windows_minimum_available_bytes',R.OUTER),('linux_minimum_available_bytes',R.OUTER),
                      ('windows_reserve_bytes',0),('outer_address_space_limit_bytes',2147483648)]:
        bad=copy.deepcopy(policy);bad[key]=value;reject('frozen_policy_change_'+key,lambda bad=bad:R.protocol(bad))
    with tempfile.TemporaryDirectory(prefix='SYNTHETIC_STAGE04_V3_',dir=Path(__file__).parent) as temporary:
        root=Path(temporary);args=SimpleNamespace(root=root,alignment_input=root/'SYNTHETIC_ALIGNMENT',output=root/'SYNTHETIC_INFERENCE',host_env=root/'SYNTHETIC_TOOLS',control=root/'SYNTHETIC_CONTROL')
        analysis={'name':'primary196','accessions':['SYNTHETIC_TIP'],'markers':['SYNTHETIC_MARKER']}
        argv=R.iqtree_argv(args,analysis)
        assert '--mem' not in argv and '-mem' not in argv and '-p' in argv and '-keep-ident' in argv and '--boot-trees' in argv
        assert all(argv[argv.index(flag)+1]==value for flag,value in {'--seqtype':'AA','-m':'MFP','-B':'1000','--alrt':'1000','--seed':'1961008','-T':'2'}.items())
        assert str(args.alignment_input) in argv[argv.index('-s')+1] and str(args.output) in argv[argv.index('--prefix')+1]
        results.append('exact_native_argv_omits_only_unsupported_memory_flag_and_uses_distinct_output')
        identity={'SYNTHETIC_ONLY':True,'iqtree3_sha256':'a'*64,'limit_helper_sha256':'b'*64}
        tree_identity={'stage04_identity':identity,'concat_sha256':'c'*64,'partitions_sha256':'d'*64,'alignment_validation_sha256':'e'*64}
        directory=args.output/'analyses/primary196/iqtree';attempt=directory/'attempt_0001';attempt.mkdir(parents=True)
        limited={'identity':identity,'pid':123,'start_ticks':456,'boot_id':'SYNTHETIC_BOOT','argv':argv,'binary_sha256':'a'*64,
                 'native_address_space_soft_hard_bytes':[R.LIMIT,R.LIMIT],'outer_address_space_soft_hard_bytes':[3758096384,3758096384],
                 'limit_helper_source_sha256':'b'*64}
        R.save(attempt/'iqtree3.limit.json',limited)
        launch={'identity':identity,'child_pid':123,'argv':argv}
        R.save(attempt/'iqtree3.launch.json',launch)
        observed={'identity':identity,'pid':123,'start_ticks':456,'boot_id':'SYNTHETIC_BOOT','binary_sha256':'a'*64,'execution':'ACTUAL_PINNED_NATIVE_EXECUTABLE_OBSERVED'}
        R.save(attempt/'iqtree3.actual_exe.json',observed)
        command={'identity':identity,'child_pid':123,'argv':argv,'exit_code':0,'actual_native_executable_observed':True,
                 'limit_receipt_sha256':R.sha(attempt/'iqtree3.limit.json')}
        R.save(attempt/'iqtree3.command.json',command)
        R.native_success(attempt,argv,identity);results.append('complete_native_start_boot_pid_binary_strict_limit_proof_required')
        for field,value in [('native_address_space_soft_hard_bytes',[3758096384,3758096384]),('pid',999),
                            ('start_ticks',999),('boot_id','WRONG_BOOT'),('limit_helper_source_sha256','x'*64)]:
            bad=copy.deepcopy(limited);bad[field]=value;R.save(attempt/'iqtree3.limit.json',bad)
            changed=copy.deepcopy(command);changed['limit_receipt_sha256']=R.sha(attempt/'iqtree3.limit.json');R.save(attempt/'iqtree3.command.json',changed)
            reject('native_proof_drift_'+field,lambda:R.native_success(attempt,argv,identity))
        R.save(attempt/'iqtree3.limit.json',limited);command['limit_receipt_sha256']=R.sha(attempt/'iqtree3.limit.json');R.save(attempt/'iqtree3.command.json',command)
        observed_bad=copy.deepcopy(observed);observed_bad['execution']='SYNTHETIC_SENTINEL';R.save(attempt/'iqtree3.actual_exe.json',observed_bad)
        reject('native_exe_sentinel_rejected',lambda:R.native_success(attempt,argv,identity));R.save(attempt/'iqtree3.actual_exe.json',observed)
        (directory/'host.log').write_text('SYNTHETIC_ONLY\n')
        receipt={'execution':'COMPUTATION_OUTPUTS_CHECKED','identity':tree_identity,
                 'execution_source':'ACTUAL_IQTREE3_EXTERNAL_RLIMIT_WITH_NATIVE_RESUMABLE_CHECKPOINTS','file_sha256':R.frozen_tree_files(directory)}
        R.save(directory/'tree_complete.json',receipt);R.cache_proof(args,analysis,directory,tree_identity,receipt)
        results.append('exact_recursive_completed_native_cache_proof')
        changed=copy.deepcopy(receipt);del changed['file_sha256']['attempt_0001/iqtree3.limit.json']
        reject('incomplete_cached_native_manifest_rejected',lambda:R.cache_proof(args,analysis,directory,tree_identity,changed))
        (directory/'untracked_native_note.txt').write_text('SYNTHETIC_ONLY\n')
        reject('extra_native_cache_member_rejected',lambda:R.cache_proof(args,analysis,directory,tree_identity,receipt))
        (directory/'untracked_native_note.txt').unlink()
        assert R.next_attempt(directory).name=='attempt_0002'
        (directory/'attempt_0005').mkdir();assert R.next_attempt(directory).name=='attempt_0006'
        results.append('gapped_native_attempt_numbering_preserves_prior_directories')
        (directory/'attempt_unowned').mkdir();reject('unrecognized_attempt_namespace_rejected',lambda:R.next_attempt(directory))
        args.control.mkdir();assert C3.needs_new_phase_preflight(args)
        R.save(args.control/'state.json',{'SYNTHETIC_ONLY':True,'current':{'phase':'trees','actual_pid':'SYNTHETIC_EXISTING'}})
        assert C3.needs_new_phase_preflight(args) is False
        results.append('existing_current_phase_pid_adoption_precedes_ram_preflight')
        R.save(args.control/'state.json',{'SYNTHETIC_ONLY':True,'current':None})
        assert C3.needs_new_phase_preflight(args);results.append('fresh_launch_requires_new_resource_preflight')
        args.linux_launcher=root/'scripts/stage04_linux_launcher_v4.py';args.distribution='Ubuntu'
        run_child=['SYNTHETIC_PYTHON','-u',C3.C.linux_path(args.linux_launcher),'--phase','trees','--','SYNTHETIC_JOB']
        wrapped=C3.bounded_wsl(args,run_child)
        assert wrapped[wrapped.index('--address-space-bytes')+1]==str(R.OUTER)
        assert wrapped[wrapped.index('--threads')+1]=='2'
        assert wrapped.index('--address-space-bytes')<wrapped.index('SYNTHETIC_JOB')
        results.append('new_observer_explicit_outer3point5GiB_and_two_threads_in_actual_launcher_argv')
        for mode in ('inspect','resources'):
            child=['SYNTHETIC_PYTHON','-u',C3.C.linux_path(args.linux_launcher),'--mode',mode]
            assert C3.bounded_wsl(args,child)==C3._BASE_WSL(args,child)
            results.append('observer_'+mode+'_arguments_preserved_without_launch_mutation')
        duplicate=run_child[:-2]+['--address-space-bytes',str(R.OUTER),*run_child[-2:]]
        reject('duplicate_outer_cap_argument_rejected',lambda:C3.bounded_wsl(args,duplicate))
        args.resource_receipt=root/'reports/stage04/SYNTHETIC_RESOURCE.json'
        linux={'linux_available_bytes':R.LINUX_MIN,'cpu_affinity_available':[0,1]}
        adequate={'available_bytes':R.WINDOWS_MIN,'disk_available_bytes':6*1024**3}
        inadequate={**adequate,'available_bytes':R.WINDOWS_MIN-1}
        recorded=[]
        with patch.object(C3.C,'LIMIT',R.OUTER),patch.object(C3.C,'windows_snapshot',side_effect=[adequate,inadequate]),\
             patch.object(C3.C,'command',return_value=json.dumps(linux)),\
             patch.object(C3.C,'atomic',side_effect=lambda path,value:recorded.append((str(path),copy.deepcopy(value)))):
            reject('cold_wsl_windows_memory_drop_blocks_before_any_native_launch',lambda:C3.resource_preflight(args))
        assert len(recorded)==2 and recorded[0][1]['windows_before_wsl']==adequate and recorded[0][1]['windows_after_wsl']==inadequate
        results.append('failed_resource_instant_persists_both_numeric_windows_and_linux_snapshots')
        with patch.object(C3.C,'LIMIT',R.OUTER),patch.object(C3.C,'windows_snapshot',side_effect=[adequate,adequate]),\
             patch.object(C3.C,'command',return_value=json.dumps(linux)):
            C3.resource_preflight(args)
        measured=R.read(args.resource_receipt)
        assert measured['windows_minimum_available_bytes']==R.WINDOWS_MIN and measured['windows_reserve_bytes']==2**30
        assert measured['process_address_space_limit_bytes']==R.OUTER and measured['iqtree_address_space_limit_bytes']==R.LIMIT
        results.append('fresh_exact_thresholds_pass_only_with_frozen3GiB3point5GiB_and_oneGiB_reserve')
        args.previous_control=root/'.work/SYNTHETIC_PREVIOUS';args.source_control=root/'.work/SYNTHETIC_ORIGINAL'
        args.original_observer_source=root/'scripts/stage04_linux_launcher.py'
        for directory in (args.previous_control,args.source_control):
            directory.mkdir(parents=True);R.save(directory/'state.json',{'current':{'phase':'trees','receipt_directory':directory.relative_to(root).as_posix()}})
        responses=iter([{'status':'ACTUAL_EXIT_RECEIPT_AVAILABLE','exit_code':1,'job_alive':False,'launcher_alive':False}]*2)
        calls=[]
        with patch.object(C3.C,'command',side_effect=lambda *a,**kw:(calls.append(a[1]),json.dumps(next(responses)))[1]):
            assert set(C3.old_job_gate(args))=={'original','v3'}
        assert len(calls)==2 and all(C3.C.linux_path(args.original_observer_source) in argv for argv in calls)
        results.append('both_prior_failed_actual_jobs_inspected_with_preserved_original_observer')
        responses=iter([{'status':'ACTUAL_EXIT_RECEIPT_AVAILABLE','exit_code':1,'job_alive':False,'launcher_alive':False},
                        {'status':'ACTUAL_EXIT_RECEIPT_AVAILABLE','exit_code':1,'job_alive':True,'launcher_alive':False}])
        with patch.object(C3.C,'command',side_effect=lambda *a,**kw:json.dumps(next(responses))):
            reject('surviving_previous_v3_actual_job_blocks_new_launch',lambda:C3.old_job_gate(args))
    output={'status':'PASS_SYNTHETIC_STAGE04_RESUMED_INFERENCE_POLICY_AND_NATIVE_PROOF','fixtures':results,'count':len(results),
            'biological_jobs_run':0,'git_commands_run':0,'production_lock_touched':False,
            'source_sha256':{name:R.sha(Path(__file__).with_name(name)) for name in
                ('stage04_inference_v4.py','stage04_inference_controller_v4.py','stage04_iqtree_limit_v4.py',
                 'stage04_linux_launcher_v4.py','test_stage04_inference_v4.py')},
            'config_sha256':R.sha(policy_path)}
    out=Path.cwd()/'reports/stage04/inference_v4_synthetic_tests.json' if Path(__file__).parent.name=='scripts' else Path(__file__).with_name('stage04_inference_v4_synthetic_results.json')
    R.save(out,output);print(json.dumps(output,indent=2))


if __name__=='__main__':run()
