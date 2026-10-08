#!/usr/bin/env python3
"""Synthetic-only independent resumed-inference checker negatives. No jobs/Git."""
from pathlib import Path
from types import SimpleNamespace
import copy, hashlib, importlib.util, json, tempfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_stage04_v4', HERE/'stage04_inference_validate_v4.py')
V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
results=[]

def test(name, operation, negative=False):
    try: operation()
    except (ValueError,KeyError,FileNotFoundError,TypeError,IndexError) as error:
        if not negative: raise
        results.append({'name':name,'status':'PASS','kind':'REJECT_MALFORMED','error':str(error)})
        return
    if negative:raise AssertionError('Malformed synthetic fixture accepted: '+name)
    results.append({'name':name,'status':'PASS','kind':'VALID_SYNTHETIC_GUARD'})

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n' if isinstance(value,(dict,list)) else value)

def mutate(path,key,value):
    row=V.json_read(path);row[key]=value;write(path,row)

with tempfile.TemporaryDirectory(prefix='stage04-v4-checker-fixture-',dir=HERE) as temp:
    root=Path(temp);ids=['SYNTHETIC_1.1','SYNTHETIC_2.1','SYNTHETIC_3.1','SYNTHETIC_4.1']
    args=SimpleNamespace(root=root,alignment_input=root/'original',input=root/'resumed',host_env=root/'env',limit_helper=root/'limit.py',alignment_validation=root/'gate.json')
    a={'name':'toy','accessions':ids,'markers':['marker1']}
    source=args.alignment_input/'analyses/toy';directory=args.input/'analyses/toy/iqtree';attempt=directory/'attempt_0001'
    write(args.limit_helper,'# SYNTHETIC helper bytes, never executed\n');write(args.host_env/'bin/iqtree3','SYNTHETIC native bytes, never executed\n')
    write(args.alignment_validation,{'status':'SYNTHETIC_ONLY_NOT_PRODUCTION_PASS'})
    write(source/'concatenated.faa',''.join('>'+i+'\n'+s+'\n' for i,s in zip(ids,['MKR','MKN','AKR','AKN'])))
    write(source/'partitions.nex','#NEXUS\nBEGIN SETS; CHARSET m001 = 1-3; END;\n')
    write(source/'partitions.tsv','partition\tstart_one_based\tend_one_based\n'+'m001\t1\t3\n')
    write(source/'tip_label_map.tsv','tree_label\tassembly_accession\n'+''.join('label_'+str(i)+'\t'+key+'\n' for i,key in enumerate(ids)))
    native='((SYNTHETIC_1.1:1,SYNTHETIC_2.1:1)90/95:1,SYNTHETIC_3.1:1,SYNTHETIC_4.1:1);\n'
    labeled=native
    for i,key in enumerate(ids):labeled=labeled.replace(key,'label_'+str(i))
    for name in ('host.treefile','host.contree','unrooted.nwk'):write(directory/name,native)
    write(directory/'unrooted.nex','#NEXUS\nBEGIN TREES; TREE host = [&U] '+native+'END;\n')
    write(directory/'unrooted_labeled.nwk',labeled)
    write(directory/'unrooted_labeled.nex','#NEXUS\nBEGIN TREES; TREE host = [&U] '+labeled+'END;\n')
    write(directory/'host.ufboot',native*1000)
    write(directory/'host.iqtree','SYNTHETIC report never computed: 1000 ultrafast bootstrap replicates\nSH-aLRT test with 1000 replicates\n')
    write(directory/'host.log','SYNTHETIC_ONLY_NO_NATIVE_EXECUTION\n')
    write(directory/'host.best_scheme.nex','#NEXUS\nBEGIN SETS; charset m001 = 1-3; charpartition models = LG+G4: m001; END;\n')
    identity={'limit_helper_sha256':V.digest(args.limit_helper),'iqtree3_sha256':V.digest(args.host_env/'bin/iqtree3')}
    tree_identity={'stage04_identity':identity,'concat_sha256':V.digest(source/'concatenated.faa'),'partitions_sha256':V.digest(source/'partitions.nex'),'alignment_validation_sha256':V.digest(args.alignment_validation)}
    argv=V.exact_argv(args,a);wrapper=[str(args.host_env/'bin/python'),'-u',str(args.limit_helper),'--receipt-file',str(attempt/'iqtree3.limit.json'),'--identity-file',str(attempt/'identity.json'),'--',*argv]
    launch={'execution':'ACTUAL_EXTERNAL_LIMIT_HELPER_STARTED','runner_pid':123,'child_pid':321,'argv':argv,'wrapper_argv':wrapper,'identity':identity}
    limit={'execution':'ACTUAL_LIMIT_SET_IMMEDIATELY_BEFORE_NATIVE_EXEC','pid':321,'parent_pid':123,'start_ticks':789,'boot_id':'11111111-1111-4111-8111-111111111111','argv':argv,'binary_sha256':identity['iqtree3_sha256'],'identity':identity,'cpu_affinity':[0,1],'outer_address_space_soft_hard_bytes':[V.OUTER,V.OUTER],'native_address_space_soft_hard_bytes':[V.LIMIT,V.LIMIT],'limit_helper_source_sha256':identity['limit_helper_sha256']}
    observed={'execution':'ACTUAL_PINNED_NATIVE_EXECUTABLE_OBSERVED','pid':321,'start_ticks':789,'boot_id':limit['boot_id'],'binary_sha256':identity['iqtree3_sha256'],'identity':identity}
    command={'execution':'ACTUAL_NATIVE_CHILD_EXITED','argv':argv,'wrapper_argv':wrapper,'runner_pid':123,'child_pid':321,'exit_code':0,'elapsed_seconds':1.0,'child_cpu_seconds':.5,'children_peak_rss_bytes_cumulative':10000,'identity':identity,'actual_native_executable_observed':True}
    def restore_attempt():
        write(attempt/'identity.json',identity);write(attempt/'iqtree3.launch.json',launch);write(attempt/'iqtree3.limit.json',limit);write(attempt/'iqtree3.actual_exe.json',observed)
        c=copy.deepcopy(command);c['limit_receipt_sha256']=V.digest(attempt/'iqtree3.limit.json');write(attempt/'iqtree3.command.json',c)
        write(attempt/'iqtree3.stdout.txt','SYNTHETIC_ONLY\n');write(attempt/'iqtree3.stderr.txt','')
    def refresh():
        write(directory/'inference_identity.json',{'identity':tree_identity,'argv':argv,'external_cap_bytes':V.LIMIT})
        payload={p.relative_to(directory).as_posix():V.digest(p) for p in directory.rglob('*') if p.is_file() and p.name!='tree_complete.json'}
        write(directory/'tree_complete.json',{'execution':'COMPUTATION_OUTPUTS_CHECKED','identity':tree_identity,'execution_source':'ACTUAL_IQTREE3_EXTERNAL_RLIMIT_WITH_NATIVE_RESUMABLE_CHECKPOINTS','file_sha256':payload})
    restore_attempt();refresh()
    audit=lambda:V.attempt_audit(attempt,argv,identity,args.host_env,args.limit_helper)
    tree_audit=lambda:V.resumed_tree_audit(args,a,identity,set())
    test('synthetic_exact_argv_omits_mem_preserves_all_science_options',lambda:V.check('--mem' not in argv and '-mem' not in argv and argv[argv.index('-T')+1]=='2','argv'))
    test('synthetic_limit_pid_start_boot_guard_accepts_consistency',audit)
    test('synthetic_1000_tree_model_coordinate_export_guard',tree_audit)
    for name,file,key,value in [
        ('zero_exit_without_native_executable_proof','iqtree3.command.json','actual_native_executable_observed',False),
        ('native_nonzero_exit','iqtree3.command.json','exit_code',2),
        ('native_pid_reused_different_start','iqtree3.actual_exe.json','start_ticks',790),
        ('native_boot_identity_changed','iqtree3.actual_exe.json','boot_id','22222222-2222-4222-8222-222222222222'),
        ('native_soft_hard_cap_relaxed','iqtree3.limit.json','native_address_space_soft_hard_bytes',[V.OUTER,V.OUTER]),
        ('native_outer_cap_unbounded','iqtree3.limit.json','outer_address_space_soft_hard_bytes',[-1,-1]),
        ('native_affinity_unbounded','iqtree3.limit.json','cpu_affinity',[0,1,2]),
        ('native_helper_source_changed','iqtree3.limit.json','limit_helper_source_sha256','0'*64),
        ('native_binary_changed','iqtree3.actual_exe.json','binary_sha256','0'*64),
        ('native_elapsed_nonfinite','iqtree3.command.json','elapsed_seconds',float('nan')),
        ('native_wrapper_identity_file_changed','iqtree3.launch.json','wrapper_argv',['wrong']),
        ('unsupported_mem_option_reintroduced','iqtree3.command.json','argv',argv+['--mem','1536M']),
        ('different_seed','iqtree3.command.json','argv',[x if x!='1961008' else '7' for x in argv])]:
        restore_attempt();mutate(attempt/file,key,value)
        if file=='iqtree3.limit.json':mutate(attempt/'iqtree3.command.json','limit_receipt_sha256',V.digest(attempt/file))
        test(name,audit,True)
    restore_attempt();refresh()
    missing=V.json_read(directory/'tree_complete.json');del missing['file_sha256']['attempt_0001/iqtree3.limit.json'];write(directory/'tree_complete.json',missing)
    test('actual_limit_evidence_omitted_from_manifest',tree_audit,True);refresh()
    write(directory/'host.ufboot',native*999);refresh();test('999_ufboot_trees_reject_even_zeroexit',tree_audit,True)
    write(directory/'host.ufboot',native*1000);refresh()
    write(directory/'host.best_scheme.nex','#NEXUS\nBEGIN SETS; charset m001 = 1-2; charpartition models = LG+G4: m001; END;\n');refresh();test('model_partition_coordinate_drift',tree_audit,True)
    write(directory/'host.best_scheme.nex','#NEXUS\nBEGIN SETS; charset m001 = 1-3; charpartition models = LG+G4: omitted; END;\n');refresh();test('model_partition_profile_omission',tree_audit,True)
    write(directory/'host.best_scheme.nex','#NEXUS\nBEGIN SETS; charset m001 = 1-3; charpartition models = LG+G4: m001; END;\n');refresh()
    write(directory/'unrooted.nwk','((SYNTHETIC_1.1:1,SYNTHETIC_3.1:1)90/95:1,SYNTHETIC_2.1:1,SYNTHETIC_4.1:1);\n');refresh();test('portable_export_topology_drift',tree_audit,True)
    write(directory/'unrooted.nwk',native);refresh()
    write(directory/'host.treefile',native.replace('90/95','101/95'));refresh();test('native_support_outside_0_100',tree_audit,True)
    write(directory/'host.treefile',native);refresh()
    write(directory/'host.contree',native.replace('SYNTHETIC_4.1','SYNTHETIC_3.1'));refresh();test('native_contree_duplicate_tip',tree_audit,True)
    write(directory/'host.contree',native);refresh()
    write(directory/'host.treefile',native.replace(':1',':-1',1));refresh();test('negative_native_branch_length',tree_audit,True)
    write(directory/'host.treefile',native);refresh()
    path=attempt/'iqtree3.command.json';original=path.read_bytes();path.write_bytes(original+b' ')
    test('native_attempt_bytes_changed_after_freeze',tree_audit,True);path.write_bytes(original)
    refresh()
    # Synthetic exact inference reuse retains independently audited prior-source
    # receipt and actual identical input bytes; no tree computation is repeated.
    second={'name':'toycopy','accessions':ids,'markers':['marker1']}
    second_source=args.alignment_input/'analyses/toycopy';second_tree=args.input/'analyses/toycopy/iqtree'
    for path in source.iterdir():
        if path.is_file():write(second_source/path.name,path.read_text())
    for path in directory.iterdir():
        if path.is_file() and path.name.startswith(('host.','unrooted')):write(second_tree/path.name,path.read_text())
    reused={'execution':'COMPUTATION_OUTPUTS_CHECKED','identity':tree_identity,
        'execution_source':'REUSED_EXACT_IDENTICAL_ALIGNMENT_PARTITION_INFERENCE','source_analysis':'toy',
        'source_tree_complete_sha256':V.digest(directory/'tree_complete.json'),
        'file_sha256':{p.relative_to(second_tree).as_posix():V.digest(p) for p in second_tree.rglob('*') if p.is_file()}}
    write(second_tree/'tree_complete.json',reused)
    reuse_audit=lambda:V.resumed_tree_audit(args,second,identity,{'toy'})
    test('identical_input_reuse_binds_prior_independent_completed_receipt',reuse_audit)
    test('reuse_source_not_independently_completed',lambda:V.resumed_tree_audit(args,second,identity,set()),True)
    altered=copy.deepcopy(reused);altered['source_tree_complete_sha256']='0'*64;write(second_tree/'tree_complete.json',altered)
    test('reused_source_receipt_hash_drift',reuse_audit,True)
    write(second_tree/'tree_complete.json',reused)
    write(second_source/'concatenated.faa',(second_source/'concatenated.faa').read_text().replace('MKR','MKA'))
    altered=copy.deepcopy(reused);altered['identity']['concat_sha256']=V.digest(second_source/'concatenated.faa');write(second_tree/'tree_complete.json',altered)
    test('nonidentical_source_alignment_cannot_reuse_native_inference',reuse_audit,True)
    p={'status':'FROZEN_RESUMED_INFERENCE_PROTOCOL_BEFORE_TOPOLOGY','approved_assemblies':196,'iqtree_address_space_limit_bytes':V.LIMIT,'outer_address_space_limit_bytes':V.OUTER,'maximum_compute_threads':2,'windows_minimum_available_bytes':V.WINDOWS_MIN,'linux_minimum_available_bytes':V.LINUX_MIN,'windows_reserve_bytes':1073741824,'native_memory_option':'OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS','alignment_reexecution':False,'partition_option':'-p','model_selection':'MFP_WITHOUT_MERGING','ultrafast_bootstrap_replicates':1000,'sh_alrt_replicates':1000,'seed':1961008,'root_policy':'EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP'}
    test('exact_frozen_partition_support_resource_policy',lambda:V.policy_gate(p))
    resources={'maximum_compute_threads':2,'iqtree_memory_mib':3072,'process_address_space_limit_bytes':V.OUTER,
        'iqtree_address_space_limit_bytes':V.LIMIT,'native_memory_option':'OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS',
        'windows_minimum_available_bytes':V.WINDOWS_MIN,'linux_minimum_available_bytes':V.LINUX_MIN,
        'windows_reserve_bytes':1073741824,'measured_windows_available_bytes':V.WINDOWS_MIN,'measured_linux_available_bytes':V.LINUX_MIN,
        'windows_before_wsl_resources':{'available_bytes':V.WINDOWS_MIN},'windows_after_wsl_resources':{'available_bytes':V.WINDOWS_MIN}}
    test('measured_v4_resources_exact_headroom_boundary',lambda:V.resource_gate(resources,resources))
    for name,key,val in [('measured_windows_one_byte_below_required','measured_windows_available_bytes',V.WINDOWS_MIN-1),
        ('measured_linux_one_byte_below_required','measured_linux_available_bytes',V.LINUX_MIN-1),
        ('v3_resource_cap_cannot_certify_v4','iqtree_memory_mib',1536),
        ('resource_receipt_reserve_silently_changed','windows_reserve_bytes',0)]:
        changed=dict(resources);changed[key]=val;test(name,lambda x=changed:V.resource_gate(x,resources),True)
    for field in ['windows_before_wsl_resources','windows_after_wsl_resources']:
        changed=copy.deepcopy(resources);changed[field]['available_bytes']=V.WINDOWS_MIN-1
        test('actual_'+field+'_fails_despite_falsely_high_minimum',lambda x=changed:V.resource_gate(x,resources),True)
    for name,key,val in [('panel_reduction','approved_assemblies',195),('model_merge_enabled','model_selection','MFP+MERGE'),('bootstrap_reduction','ultrafast_bootstrap_replicates',999),('native_cap_relaxed','iqtree_address_space_limit_bytes',V.OUTER),('thread_raise','maximum_compute_threads',3),('alignment_reexecution_allowed','alignment_reexecution',True),('windows_fresh_headroom_lowered','windows_minimum_available_bytes',V.WINDOWS_MIN-1),('linux_fresh_headroom_lowered','linux_minimum_available_bytes',V.LINUX_MIN-1),('windows_reserve_omitted','windows_reserve_bytes',0)]:
        changed=dict(p);changed[key]=val;test(name,lambda x=changed:V.policy_gate(x),True)
    pub={'status':'UPLOAD_VERIFIED','remote_tag_commit_verified':True,'scientific_validation':'PASS_ALIGNMENT_FORMATS_AND_PARTITIONS','whole_stage04_phylogeny':'NOT_COMPLETED','approved_assemblies':196,'alignment_validation_sha256':'a'*64,'payload_commit':'b'*40,'assets':[{'asset_name':name,'bytes':100,'payload_members':1,'sha256':'c'*64,'download_readback_verified':True,'all_zip_member_hashes_verified':True,'sidecar_readback_verified':True} for name in ('stage04a-full196-validated-alignments.zip','stage04a-methods-and-independent-evidence.zip')]}
    test('stage04a_current_exact_release_gate',lambda:V.publication_gate(pub,'a'*64))
    wrong=copy.deepcopy(pub);wrong['alignment_validation_sha256']='d'*64;test('stale_alignment_publication_hash',lambda:V.publication_gate(wrong,'a'*64),True)
    wrong=copy.deepcopy(pub);wrong['assets'][0]['download_readback_verified']=False;test('upload_started_without_remote_byte_proof',lambda:V.publication_gate(wrong,'a'*64),True)
    wrong=copy.deepcopy(pub);wrong['whole_stage04_phylogeny']='COMPLETED';test('alignment_only_receipt_counterfeits_whole_stage4',lambda:V.publication_gate(wrong,'a'*64),True)
    test('unsafe_manifest_parent_escape',lambda:V.safe_member(root,'../unrelated'),True)

    # Independent full prior-failure gate fixtures. All files here are synthetic;
    # no actual failed record or production dependency is edited or inferred.
    prevargs=SimpleNamespace(root=root,input=root/'new-v4',previous_input=root/'failed-v3',
        previous_control=root/'failed-v3-control',source_control=root/'old-v2-control',
        original_observer_source=root/'scripts/stage04_linux_launcher.py',
        alignment_input=args.alignment_input,alignment_validation=args.alignment_validation,
        host_env=args.host_env,previous_publication=root/'reports/stage04b/publication_receipt.json')
    prevdir=prevargs.previous_input/'analyses/toy/iqtree/attempt_0001'
    prevargs.previous_failed_attempt=prevdir/'iqtree3.command.json'
    previous_sources={'resumed_producer_sha256':root/'scripts/stage04_inference_v3.py',
        'resumed_controller_sha256':root/'scripts/stage04_inference_controller_v3.py',
        'resumed_validator_sha256':root/'scripts/stage04_inference_validate_v3.py',
        'limit_helper_sha256':root/'scripts/stage04_iqtree_limit_v3.py',
        'observer_sha256':prevargs.original_observer_source,
        'config_sha256':root/'config/host_inference_stage04_v3.json',
        'resource_receipt_sha256':root/'reports/stage04/resumed_inference_resource_preflight_v3.json'}
    for field,path in previous_sources.items():write(path,'SYNTHETIC never executed '+field+'\n')
    previous_identity={k:V.digest(p) for k,p in previous_sources.items()}
    previous_identity.update(alignment_producer_identity={'fixture':'SYNTHETIC_ORIGINAL'},
        alignment_validation_sha256=V.digest(args.alignment_validation),
        iqtree_address_space_limit_bytes=1610612736,outer_address_space_limit_bytes=2147483648,
        iqtree3_sha256=V.digest(args.host_env/'bin/iqtree3'))
    original={'identity':previous_identity['alignment_producer_identity'],'analyses':[a]}
    previous_argv=V.exact_argv(SimpleNamespace(alignment_input=args.alignment_input,input=prevargs.previous_input,host_env=args.host_env),a)
    previous_wrapper=[str(args.host_env/'bin/python'),'-u',str(previous_sources['limit_helper_sha256']),
        '--receipt-file',str(prevdir/'iqtree3.limit.json'),'--identity-file',str(prevdir/'identity.json'),'--',*previous_argv]
    previous_state_identity={'inference_identity':previous_identity,
        'file_sha256':{p.relative_to(root).as_posix():V.digest(p) for p in previous_sources.values()}}
    phase_dir=prevargs.previous_control/'trees_attempt_0001'
    frozen_path=prevargs.previous_input/'inference_freeze.json'
    state_path=prevargs.previous_control/'state.json'
    evidence_path=root/'reports/stage04b/failure_evidence_validation.json'
    def restore_previous():
        write(frozen_path,{'status':'FROZEN_RESUMED_INFERENCE_BEFORE_TOPOLOGY','alignment_reexecution':False,'analyses':[a],'identity':previous_identity})
        write(state_path,{'scope':'full196','completed':{},'current':{'phase':'trees','invocation_id':'synthetic-failure',
            'receipt_directory':phase_dir.relative_to(root).as_posix()},'identity':previous_state_identity})
        phase={'identity':previous_state_identity,'invocation_id':'synthetic-failure','job_pid':123,'launcher_pid':789}
        write(phase_dir/'linux_launch_receipt.json',dict(phase,address_space_limit_bytes=2147483648))
        write(phase_dir/'linux_exit_receipt.json',dict(phase,execution='ACTUAL_LINUX_PHASE_CHILD_EXITED',exit_code=1))
        write(prevdir/'identity.json',previous_identity)
        write(prevdir/'iqtree3.launch.json',dict(launch,argv=previous_argv,wrapper_argv=previous_wrapper,identity=previous_identity))
        write(prevdir/'iqtree3.limit.json',dict(limit,argv=previous_argv,identity=previous_identity,
            binary_sha256=previous_identity['iqtree3_sha256'],limit_helper_source_sha256=previous_identity['limit_helper_sha256'],
            outer_address_space_soft_hard_bytes=[2147483648]*2,native_address_space_soft_hard_bytes=[1610612736]*2))
        write(prevdir/'iqtree3.actual_exe.json',dict(observed,identity=previous_identity))
        write(prevargs.previous_failed_attempt,dict(command,argv=previous_argv,wrapper_argv=previous_wrapper,identity=previous_identity,
            exit_code=2,limit_receipt_sha256=V.digest(prevdir/'iqtree3.limit.json')))
        write(prevdir/'iqtree3.stdout.txt','SYNTHETIC_ONLY_NO_BIOLOGY\n')
        write(prevdir/'iqtree3.stderr.txt','SYNTHETIC allocation of 2084933760 bytes failed (bad_alloc)\n')
        write(evidence_path,{'status':'ACTUAL_FAILED_INFERENCE_EVIDENCE_VERIFIED_ONLY','scientific_stage04':'INCOMPLETE',
            'completed_native_trees':0,'native_exit':2,'native_pid':321,'native_address_space_cap_bytes':1610612736,
            'failed_single_allocation_bytes':2084933760,'native_command_receipt_sha256':V.digest(prevargs.previous_failed_attempt),
            'actual_phase_exit_receipt_sha256':V.digest(phase_dir/'linux_exit_receipt.json'),
            'native_limit_receipt_sha256':V.digest(prevdir/'iqtree3.limit.json'),'exact_failed_job_and_observer_absent':True})
        write(prevargs.previous_publication,{'status':'UPLOAD_VERIFIED','scientific_validation':'INCOMPLETE_ACTUAL_RESOURCE_FAILURE',
            'approved_assemblies':196,'whole_stage04_phylogeny':'NOT_COMPLETED','remote_tag_commit_verified':True,
            'payload_commit':'b'*40,'release_tag':'stage04b-inference-resource-failure196-v1',
            'failed_native_attempt_sha256':V.digest(prevargs.previous_failed_attempt),
            'failed_native_stderr_sha256':V.digest(prevdir/'iqtree3.stderr.txt'),
            'previous_inference_freeze_sha256':V.digest(frozen_path),
            'failed_phase_exit_sha256':V.digest(phase_dir/'linux_exit_receipt.json'),
            'failure_evidence_validation_sha256':V.digest(evidence_path),
            'assets':[{'bytes':1,'payload_members':1,'sha256':'c'*64,'download_readback_verified':True,
                'all_zip_member_hashes_verified':True,'sidecar_readback_verified':True}]})
    previous_audit=lambda:V.previous_failure_gate(prevargs,original)
    restore_previous();test('prior_actual_failure_complete_binding_synthetic_guard',previous_audit)
    for name,path,key,value in [
        ('previous_failed_phase_counterfeits_completion',state_path,'completed',{'trees':{}}),
        ('previous_freeze_counterfeits_alignment_rerun',frozen_path,'alignment_reexecution',True),
        ('previous_phase_exit_zero',phase_dir/'linux_exit_receipt.json','exit_code',0),
        ('previous_failure_evidence_claims_finished_tree',evidence_path,'completed_native_trees',1),
        ('previous_failure_absent_job_check_missing',evidence_path,'exact_failed_job_and_observer_absent',False),
        ('previous_failure_publication_claims_scientific_pass',prevargs.previous_publication,'scientific_validation','PASS'),
        ('previous_failure_publication_stale_native_hash',prevargs.previous_publication,'failed_native_attempt_sha256','0'*64),
        ('previous_failure_publication_unverified_tag',prevargs.previous_publication,'remote_tag_commit_verified',False)]:
        restore_previous();mutate(path,key,value);test(name,previous_audit,True)
    restore_previous();prior=previous_sources['resumed_validator_sha256'];saved=prior.read_bytes();prior.write_bytes(saved+b'CHANGED\n')
    test('previous_recorded_checker_source_bytes_differ',previous_audit,True);prior.write_bytes(saved)
    restore_previous();mutate(prevdir/'iqtree3.limit.json','native_address_space_soft_hard_bytes',[V.LIMIT]*2)
    mutate(prevargs.previous_failed_attempt,'limit_receipt_sha256',V.digest(prevdir/'iqtree3.limit.json'))
    test('previous_native_cap_relabelled_as_new_v4_cap',previous_audit,True)
    restore_previous();write(prevargs.previous_input/'phylogeny_summary.json',{'status':'SYNTHETIC_FALSE_COMPLETION'})
    test('previous_failed_namespace_has_false_completion_summary',previous_audit,True)

report={'status':'PASS_SYNTHETIC_RESUMED_INFERENCE_CHECKER_FIXTURES','validator_source_sha256':V.digest(HERE/'stage04_inference_validate_v4.py'),'test_source_sha256':V.digest(__file__),'passed':len(results),'failed':0,'fixtures':results,'biological_inference':'NOT_RUN','full196_final_validation':'NOT_RUN'}
out=HERE/'stage04_inference_v4_review';out.mkdir(exist_ok=True)
V.atomic_json(out/'synthetic_checker_tests.json',report)
print(json.dumps({'status':report['status'],'passed':len(results),'failed':0,'biological_inference':'NOT_RUN'}))
