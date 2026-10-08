#!/usr/bin/env python3
"""Private synthetic argv/resource/native-proof/cache/resume fixtures; no biology."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import stage04_inference_v3 as R
import stage04_inference_controller_v3 as C3


def run():
    results=[]
    def reject(name,operation):
        try:operation()
        except (ValueError,KeyError,FileNotFoundError):results.append(name);return
        raise AssertionError('Bad synthetic fixture accepted: '+name)
    policy_path=(Path.cwd()/'config/host_inference_stage04_v3.json' if Path(__file__).parent.name=='scripts'
                 else Path(__file__).with_name('host_inference_stage04_v3.json'))
    policy=R.read(policy_path)
    R.protocol(policy);results.append('frozen_full196_unchanged_partition_model_support_and_stricter_cap')
    for key,value in [('approved_assemblies',162),('iqtree_address_space_limit_bytes',2147483648),
                      ('maximum_compute_threads',16),('partition_option','-q'),('ultrafast_bootstrap_replicates',100),
                      ('alignment_reexecution',True),('native_memory_option','--mem1536M')]:
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
                 'native_address_space_soft_hard_bytes':[R.LIMIT,R.LIMIT],'outer_address_space_soft_hard_bytes':[2147483648,2147483648],
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
        for field,value in [('native_address_space_soft_hard_bytes',[2147483648,2147483648]),('pid',999),
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
    output={'status':'PASS_SYNTHETIC_STAGE04_RESUMED_INFERENCE_POLICY_AND_NATIVE_PROOF','fixtures':results,'count':len(results),
            'biological_jobs_run':0,'git_commands_run':0,'production_lock_touched':False}
    out=Path.cwd()/'reports/stage04/inference_v3_synthetic_tests.json' if Path(__file__).parent.name=='scripts' else Path(__file__).with_name('stage04_inference_v3_synthetic_results.json')
    R.save(out,output);print(json.dumps(output,indent=2))


if __name__=='__main__':run()
