#!/usr/bin/env python3
"""Resume IQ-TREE partition inference from validated immutable Stage04a inputs.

No alignment or biological search is repeated. Unsupported native --mem is
removed; the separate exec helper enforces3072MiB soft/hard address space.
Original failure/alignments/controller are never overwritten.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

NAMES=('primary196','sensitivity162','sensitivity187_markers','sensitivity_complete155')
COUNTS=(196,162,196,155)
LIMIT=3221225472
OUTER=3758096384
WINDOWS_MIN=4831838208
LINUX_MIN=4294967296


def require(ok,detail):
    if not ok:raise ValueError(detail)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.partial')
    temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');temporary.replace(path)


def within(root,name):
    path=(root/name).resolve();require(root.resolve() in path.parents,'Source path escapes project');return path


def hash_map(root,hashes):
    require(hashes,'Missing executed source hash map')
    for name,value in hashes.items():require(sha(within(root,name))==value,'Executed source bytes changed: '+name)


def protocol(config):
    require(config['status']=='FROZEN_RESUMED_INFERENCE_PROTOCOL_BEFORE_TOPOLOGY'
            and config['approved_assemblies']==196 and config['iqtree_address_space_limit_bytes']==LIMIT
            and config['outer_address_space_limit_bytes']==3758096384 and config['maximum_compute_threads']==2
            and config['windows_minimum_available_bytes']==WINDOWS_MIN and config['linux_minimum_available_bytes']==LINUX_MIN
            and config['windows_reserve_bytes']==1073741824
            and config['native_memory_option']=='OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS'
            and config['alignment_reexecution'] is False and config['partition_option']=='-p'
            and config['model_selection']=='MFP_WITHOUT_MERGING' and config['ultrafast_bootstrap_replicates']==1000
            and config['sh_alrt_replicates']==1000 and config['seed']==1961008
            and config['root_policy']=='EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP',
            'Frozen resumed inference policy differs; no model/panel/resource relaxation')


def previous_failure_gate(args):
    state=read(args.previous_control/'state.json');frozen=read(args.previous_input/'inference_freeze.json')
    require(args.previous_input!=args.output and args.previous_control!=args.source_control,
            'Separate preserved failed v3 namespaces required')
    require(state['scope']=='full196' and state['completed']=={} and state.get('current')
            and state['current']['phase']=='trees', 'Actual previous capped phase failure missing/different')
    hash_map(args.root,state['identity']['file_sha256'])
    current=state['current'];exit_path=within(args.root,current['receipt_directory'])/'linux_exit_receipt.json'
    exited=read(exit_path);launch=read(exit_path.parent/'linux_launch_receipt.json')
    require(exited['exit_code']!=0 and exited['identity']==launch['identity']==state['identity']
            and exited['invocation_id']==launch['invocation_id']==current['invocation_id']
            and exited['job_pid']==launch['job_pid']>0 and exited['launcher_pid']==launch['launcher_pid']>0
            and launch['address_space_limit_bytes']==2147483648, 'Previous actual failed phase/outer cap differs')
    attempt=args.previous_failed_attempt.parent;command=read(args.previous_failed_attempt)
    limited=read(attempt/'iqtree3.limit.json');observed=read(attempt/'iqtree3.actual_exe.json');native_launch=read(attempt/'iqtree3.launch.json')
    old=frozen['identity'];stderr=attempt/'iqtree3.stderr.txt'
    require(frozen['status']=='FROZEN_RESUMED_INFERENCE_BEFORE_TOPOLOGY' and frozen['alignment_reexecution'] is False
            and old==state['identity']['inference_identity']==command['identity']==limited['identity']==observed['identity']==native_launch['identity']
            and old['outer_address_space_limit_bytes']==2147483648 and old['iqtree_address_space_limit_bytes']==1610612736
            and old['alignment_validation_sha256']==sha(args.alignment_validation), 'Preserved previous frozen cap/source identity differs')
    require(command['execution']=='ACTUAL_NATIVE_CHILD_EXITED' and command['exit_code']==2
            and command['actual_native_executable_observed'] is True
            and command['limit_receipt_sha256']==sha(attempt/'iqtree3.limit.json')
            and command['child_pid']==native_launch['child_pid']==limited['pid']==observed['pid']>0
            and command['runner_pid']==native_launch['runner_pid']==limited['parent_pid']>0
            and limited['start_ticks']==observed['start_ticks']>0 and limited['boot_id']==observed['boot_id']
            and limited['binary_sha256']==observed['binary_sha256']==old['iqtree3_sha256']
            and limited['native_address_space_soft_hard_bytes']==[1610612736]*2
            and limited['outer_address_space_soft_hard_bytes']==[2147483648]*2
            and limited['limit_helper_source_sha256']==old['limit_helper_sha256']
            and command['argv']==limited['argv']==native_launch['argv']
            and command['wrapper_argv']==native_launch['wrapper_argv'], 'Previous applied native limit/binary/PID/argv proof differs')
    argv=command['argv'];fixed={'--seqtype':'AA','-m':'MFP','-B':'1000','--alrt':'1000','--seed':'1961008','-T':'2'}
    require('-p' in argv and '-keep-ident' in argv and '--boot-trees' in argv and '--mem' not in argv and '-mem' not in argv
            and all(argv.count(k)==1 and argv[argv.index(k)+1]==v for k,v in fixed.items()),
            'Preserved previous scientific argv differs from fixed method')
    require('allocation of 2084933760 bytes failed' in stderr.read_text()
            and not (attempt.parent/'tree_complete.json').exists(), 'Exact previous allocation failure missing or falsely completed')
    prior_sources={'resumed_producer_sha256':args.root/'scripts/stage04_inference_v3.py',
        'resumed_controller_sha256':args.root/'scripts/stage04_inference_controller_v3.py',
        'resumed_validator_sha256':args.root/'scripts/stage04_inference_validate_v3.py',
        'limit_helper_sha256':args.root/'scripts/stage04_iqtree_limit_v3.py',
        'observer_sha256':args.original_observer_source,'config_sha256':args.root/'config/host_inference_stage04_v3.json',
        'resource_receipt_sha256':args.root/'reports/stage04/resumed_inference_resource_preflight_v3.json'}
    require(all(old[k]==sha(p) for k,p in prior_sources.items()), 'Preserved actually executed previous code/config/resource bytes changed')
    receipt=read(args.previous_publication);evidence_path=args.root/'reports/stage04b/failure_evidence_validation.json'
    evidence=read(evidence_path)
    require(receipt['status']=='UPLOAD_VERIFIED' and receipt['scientific_validation']=='INCOMPLETE_ACTUAL_RESOURCE_FAILURE'
            and receipt['approved_assemblies']==196 and receipt['whole_stage04_phylogeny']=='NOT_COMPLETED'
            and receipt['remote_tag_commit_verified'] is True and receipt['assets']
            and all(a['download_readback_verified'] is True and a['all_zip_member_hashes_verified'] is True
                and a['sidecar_readback_verified'] is True and a['bytes']>0 for a in receipt['assets'])
            and receipt['failed_native_attempt_sha256']==sha(args.previous_failed_attempt)
            and receipt['failed_native_stderr_sha256']==sha(stderr)
            and receipt['previous_inference_freeze_sha256']==sha(args.previous_input/'inference_freeze.json')
            and receipt['failed_phase_exit_sha256']==sha(exit_path)
            and receipt['failure_evidence_validation_sha256']==sha(evidence_path), 'Previous failure portable publication bytes not verified/current')
    require(evidence['status']=='ACTUAL_FAILED_INFERENCE_EVIDENCE_VERIFIED_ONLY'
            and evidence['scientific_stage04']=='INCOMPLETE' and evidence['completed_native_trees']==0
            and evidence['native_command_receipt_sha256']==sha(args.previous_failed_attempt)
            and evidence['actual_phase_exit_receipt_sha256']==sha(exit_path)
            and evidence['native_limit_receipt_sha256']==sha(attempt/'iqtree3.limit.json'), 'Executed failure-only independent evidence differs')
    return {'previous_inference_identity':old,'previous_inference_freeze_sha256':sha(args.previous_input/'inference_freeze.json'),
        'previous_controller_state_sha256':sha(args.previous_control/'state.json'),
        'previous_failed_native_attempt_sha256':sha(args.previous_failed_attempt),'previous_failed_native_stderr_sha256':sha(stderr),
        'previous_failed_phase_exit_sha256':sha(exit_path),'previous_failure_evidence_validation_sha256':sha(evidence_path),
        'previous_inference_file_sha256':{p.relative_to(args.previous_input).as_posix():sha(p) for p in args.previous_input.rglob('*') if p.is_file()},
        'previous_source_sha256':{p.relative_to(args.root).as_posix():sha(p) for p in prior_sources.values()},
        'previous_input':args.previous_input.relative_to(args.root).as_posix(),
        'previous_control':args.previous_control.relative_to(args.root).as_posix(),
        'previous_failed_attempt':args.previous_failed_attempt.relative_to(args.root).as_posix(),
        'previous_failure_release_tag':receipt['release_tag'],'previous_failure_payload_commit':receipt['payload_commit'],
        'windows_minimum_available_bytes':WINDOWS_MIN,'linux_minimum_available_bytes':LINUX_MIN,'windows_reserve_bytes':1073741824}


def input_identity(args,native=False):
    config=read(args.config);protocol(config)
    old=read(args.alignment_input/'analysis_freeze.json');summary=read(args.alignment_input/'alignment_summary.json')
    manifest=read(args.alignment_input/'analysis_alignment_manifest.json');gate=read(args.alignment_validation)
    require(old['status']=='FROZEN_BEFORE_STAGE04_ALIGNMENT_AND_TOPOLOGY'
            and summary['execution']=='ALL_PRIMARY_ALIGNMENTS_AND_FOUR_CONCATENATIONS_CONSTRUCTED'
            and gate['status']=='PASS_ALIGNMENT_FORMATS_AND_PARTITIONS' and gate['analyses_verified']==4
            and gate['primary_tip_ids']==196 and gate['profiles_aligned']==100
            and gate['producer_identity']==old['identity']==summary['identity'], 'Original executed independent alignment gate missing')
    keys={'analysis_freeze_sha256':'analysis_freeze.json','alignment_summary_sha256':'alignment_summary.json','analysis_manifest_sha256':'analysis_alignment_manifest.json'}
    for key,name in keys.items():require(gate[key]==sha(args.alignment_input/name),'Original alignment proof hash drift')
    require(gate['validator_source_sha256']==sha(args.source_validator) and old['identity']['runner_sha256']==sha(args.source_producer),
            'Original actually executed producer/checker code changed')
    require([a['name'] for a in old['analyses']]==list(NAMES) and [len(a['accessions']) for a in old['analyses']]==list(COUNTS)
            and [a['name'] for a in manifest]==list(NAMES), 'Fixed four analysis scopes changed')
    panel=(args.root/'config/approved_accessions.txt').read_text().split()
    require(len(panel)==len(set(panel))==196 and old['analyses'][0]['accessions']==old['analyses'][2]['accessions']==panel,
            'Exact approved196 membership changed')
    approval=read(args.root/'config/approval.json')
    require(approval['human_approval']=='APPROVED_FOR_SEQUENCE_ANALYSIS' and approval['pilot'] is False
            and approval['approved_assembly_count']==196 and approval['panel_accessions_sha256']==sha(args.root/'config/approved_accessions.txt'),
            'Full196 authorization changed')
    for item,analysis in zip(manifest,old['analyses']):
        require(item['taxa']==len(analysis['accessions']) and item['markers']==len(analysis['markers']), 'Original concat counts differ')
        hash_map(args.alignment_input/'analyses'/item['name'],item['file_sha256'])
    published=read(args.alignment_publication)
    require(published['status']=='UPLOAD_VERIFIED' and published['remote_tag_commit_verified'] is True
            and published['scientific_validation']=='PASS_ALIGNMENT_FORMATS_AND_PARTITIONS' and published['approved_assemblies']==196
            and published['alignment_validation_sha256']==sha(args.alignment_validation)
            and published['whole_stage04_phylogeny']=='NOT_COMPLETED' and published['assets']
            and all(a['download_readback_verified'] is True and a['all_zip_member_hashes_verified'] is True
                    and a['sidecar_readback_verified'] is True for a in published['assets']),
            'Current independently validated Stage04a release bytes not verified')
    state=read(args.source_control/'state.json')
    require(set(state['completed'])=={'align','validate_alignment'}, 'Original two-phase execution proof differs')
    hash_map(args.root,state['identity']['file_sha256'])
    phase_sha={}
    for phase in ('align','validate_alignment'):
        receipt=state['completed'][phase];exit_path=within(args.root,receipt['actual_exit_receipt']);exited=read(exit_path)
        require(sha(exit_path)==receipt['actual_exit_receipt_sha256'] and exited['exit_code']==receipt['actual_exit_code']==0
                and exited['identity']==state['identity'] and exited['invocation_id']==receipt['invocation_id']
                and receipt['gate']['sha256']==sha(within(args.root,receipt['gate']['path'])), 'Original actual phase/gate proof changed')
        phase_sha[phase]=sha(exit_path)
    failed=read(args.failed_attempt);stderr=args.failed_attempt.parent/'iqtree3.stderr.txt'
    require(failed['exit_code']==2 and failed['child_pid']>0 and '--mem' in failed['argv'] and '-p' in failed['argv']
            and stderr.read_text().strip()=='-mem option does not work with partition models yet'
            and not (args.failed_attempt.parent.parent/'tree_complete.json').exists(), 'Preserved exact unsupported-option failure differs')
    current=state.get('current');require(current and current['phase']=='trees','Original failed tree phase identity missing')
    failure_exit=within(args.root,current['receipt_directory'])/'linux_exit_receipt.json';failure=read(failure_exit)
    require(failure['exit_code']!=0 and failure['identity']==state['identity'] and failure['invocation_id']==current['invocation_id'],
            'Original scientific runner has no actual failed exit; possible active job')
    receipt=read(args.resource_receipt)
    require(receipt['maximum_compute_threads']==2 and receipt['iqtree_memory_mib']==3072
            and receipt['process_address_space_limit_bytes']==3758096384
            and receipt['iqtree_address_space_limit_bytes']==LIMIT and receipt['native_memory_option']=='OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS'
            and receipt['windows_minimum_available_bytes']==WINDOWS_MIN and receipt['linux_minimum_available_bytes']==LINUX_MIN
            and receipt['windows_reserve_bytes']==1073741824
            and receipt['measured_windows_available_bytes']>=WINDOWS_MIN and receipt['measured_linux_available_bytes']>=LINUX_MIN,
            'Frozen measured external-cap resource receipt differs')
    paths={'resumed_producer_sha256':Path(__file__),'resumed_controller_sha256':args.controller_source,
           'resumed_validator_sha256':args.checker_source,'limit_helper_sha256':args.limit_helper,
           'source_producer_sha256':args.source_producer,'source_validator_sha256':args.source_validator,
           'source_controller_sha256':args.root/'scripts/stage04_controller.py',
           'observer_sha256':args.observer_source,'original_observer_sha256':args.original_observer_source,'wsl_wrapper_sha256':args.root/'scripts/wsl_project.sh',
           'config_sha256':args.config,'resource_receipt_sha256':args.resource_receipt}
    identity={key:sha(path) for key,path in paths.items()}
    identity.update(alignment_producer_identity=old['identity'],
        original_analysis_freeze_sha256=sha(args.alignment_input/'analysis_freeze.json'),
        original_alignment_summary_sha256=sha(args.alignment_input/'alignment_summary.json'),
        original_analysis_manifest_sha256=sha(args.alignment_input/'analysis_alignment_manifest.json'),
        alignment_validation_sha256=sha(args.alignment_validation),original_successful_phase_exit_sha256=phase_sha,
        original_failed_phase_exit_sha256=sha(failure_exit),failed_native_attempt_sha256=sha(args.failed_attempt),
        failed_native_stderr_sha256=sha(stderr),iqtree3_sha256=old['identity']['iqtree3_sha256'],
        maximum_compute_threads=2,outer_address_space_limit_bytes=3758096384,iqtree_address_space_limit_bytes=LIMIT,
        native_memory_option='OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS',
        source_alignment_input=args.alignment_input.relative_to(args.root).as_posix(),
        source_control=args.source_control.relative_to(args.root).as_posix(),
        failed_native_attempt=args.failed_attempt.relative_to(args.root).as_posix(),
        root_policy='EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP')
    identity.update(previous_failure_gate(args))
    if native:require(sha(args.host_env/'bin/iqtree3')==identity['iqtree3_sha256'],'Pinned actual native IQ-TREE binary changed')
    return identity,old['analyses']


def iqtree_argv(args,analysis):
    source=args.alignment_input/'analyses'/analysis['name'];output=args.output/'analyses'/analysis['name']/'iqtree'
    return [str(args.host_env/'bin/iqtree3'),'-s',str(source/'concatenated.faa'),'--seqtype','AA','-p',str(source/'partitions.nex'),
            '-m','MFP','-B','1000','--alrt','1000','--seed','1961008','-T','2','-keep-ident','--boot-trees','--prefix',str(output/'host')]


def native_success(attempt,argv,identity):
    command=read(attempt/'iqtree3.command.json');launch=read(attempt/'iqtree3.launch.json')
    limited=read(attempt/'iqtree3.limit.json');observed=read(attempt/'iqtree3.actual_exe.json')
    require(command['exit_code']==0 and command['argv']==launch['argv']==limited['argv']==argv
            and command['identity']==launch['identity']==limited['identity']==observed['identity']==identity
            and command['child_pid']==launch['child_pid']==limited['pid']==observed['pid']>0
            and limited['start_ticks']==observed['start_ticks']>0 and limited['boot_id']==observed['boot_id']
            and limited['binary_sha256']==observed['binary_sha256']==identity['iqtree3_sha256']
            and limited['native_address_space_soft_hard_bytes']==[LIMIT,LIMIT]
            and limited['outer_address_space_soft_hard_bytes']==[3758096384,3758096384]
            and limited['limit_helper_source_sha256']==identity['limit_helper_sha256']
            and observed['execution']=='ACTUAL_PINNED_NATIVE_EXECUTABLE_OBSERVED'
            and command['actual_native_executable_observed'] is True
            and command['limit_receipt_sha256']==sha(attempt/'iqtree3.limit.json'),
            'Actual completed native PID/start/boot/executable/strict-limit proof differs')
    return command


def frozen_tree_files(directory):
    return {p.relative_to(directory).as_posix():sha(p) for p in directory.rglob('*')
            if p.is_file() and p!=directory/'tree_complete.json'}


def cache_proof(args,analysis,directory,identity,record):
    require(record['identity']==identity and record['execution']=='COMPUTATION_OUTPUTS_CHECKED'
            and frozen_tree_files(directory)==record['file_sha256'], 'Cached completed inference identity/recursive coverage differs')
    if record['execution_source']=='ACTUAL_IQTREE3_EXTERNAL_RLIMIT_WITH_NATIVE_RESUMABLE_CHECKPOINTS':
        candidates=[p for p in directory.glob('attempt_*/iqtree3.command.json') if read(p)['exit_code']==0]
        require(candidates,'Completed inference lacks an actual native exit0 attempt')
        native_success(candidates[-1].parent,iqtree_argv(args,analysis),identity['stage04_identity'])
    else:
        require(record['execution_source']=='REUSED_EXACT_IDENTICAL_ALIGNMENT_PARTITION_INFERENCE'
                and record['source_analysis'] in NAMES and NAMES.index(record['source_analysis'])<NAMES.index(analysis['name']),
                'Unknown/cyclic cached inference reuse')
        source=args.output/'analyses'/record['source_analysis']/'iqtree';source_complete=source/'tree_complete.json'
        require(record['source_tree_complete_sha256']==sha(source_complete),'Reused completed source receipt changed')
        source_record=read(source_complete)
        require(source_record['identity']==identity,'Reused native source was not exact-byte/input identical')
        source_analysis={**analysis,'name':record['source_analysis']}
        cache_proof(args,source_analysis,source,identity,source_record)
        require(all(sha(directory/name)==sha(source/name) for name in record['file_sha256']
                    if name.startswith(('host.','unrooted'))),'Reused inference native/portable bytes differ')


def next_attempt(directory):
    attempts=sorted(directory.glob('attempt_*'))
    require(all(p.is_dir() and re.fullmatch(r'attempt_[0-9]{4}',p.name) for p in attempts),'Unrecognized native attempt namespace')
    index=max([int(p.name.split('_')[1]) for p in attempts]+[0])+1
    require(index<=9999,'Too many preserved native attempts; explicit review required')
    result=directory/('attempt_'+str(index).zfill(4));require(not result.exists(),'Fresh native attempt path collision');return result


def process(args,directory,argv,identity):
    import resource
    require(not directory.exists(),'Preserve existing native attempt; fresh directory required')
    directory.mkdir(parents=True);identity_path=directory/'identity.json';save(identity_path,identity)
    wrapper=[str(args.host_env/'bin/python'),'-u',str(args.limit_helper),'--receipt-file',str(directory/'iqtree3.limit.json'),
             '--identity-file',str(identity_path),'--',*argv]
    start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    with (directory/'iqtree3.stdout.txt').open('wb') as out,(directory/'iqtree3.stderr.txt').open('wb') as err:
        child=subprocess.Popen(wrapper,cwd=args.root,env=args.environment,stdout=out,stderr=err)
        save(directory/'iqtree3.launch.json',{'execution':'ACTUAL_EXTERNAL_LIMIT_HELPER_STARTED','utc':datetime.now(timezone.utc).isoformat(),
             'runner_pid':os.getpid(),'child_pid':child.pid,'argv':argv,'wrapper_argv':wrapper,'identity':identity})
        actual_exe=False
        while child.poll() is None:
            try:
                binary=Path('/proc')/str(child.pid)/'exe'
                if binary.resolve()==(args.host_env/'bin/iqtree3').resolve():
                    stat=(Path('/proc')/str(child.pid)/'stat').read_text();start_ticks=int(stat[stat.rfind(')')+2:].split()[19])
                    save(directory/'iqtree3.actual_exe.json',{'execution':'ACTUAL_PINNED_NATIVE_EXECUTABLE_OBSERVED','utc':datetime.now(timezone.utc).isoformat(),
                         'pid':child.pid,'start_ticks':start_ticks,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                         'binary_sha256':sha(args.host_env/'bin/iqtree3'),'identity':identity})
                    actual_exe=True;break
            except (OSError,ProcessLookupError):pass
            time.sleep(.01)
        code=child.wait()
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    limited=read(directory/'iqtree3.limit.json') if (directory/'iqtree3.limit.json').is_file() else None
    receipt={'execution':'ACTUAL_NATIVE_CHILD_EXITED','utc':datetime.now(timezone.utc).isoformat(),'argv':argv,'wrapper_argv':wrapper,
             'runner_pid':os.getpid(),'child_pid':child.pid,'exit_code':code,'elapsed_seconds':time.monotonic()-start,
             'child_cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
             'children_peak_rss_bytes_cumulative':after.ru_maxrss*1024,'identity':identity,
             'limit_receipt_sha256':sha(directory/'iqtree3.limit.json') if limited else None,'actual_native_executable_observed':actual_exe,
             'measurement_limit':'Child CPU delta and cumulative child maxRSS; outer observer retains sampled concurrent/phase RSS'}
    save(directory/'iqtree3.command.json',receipt)
    with (args.output/'commands.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(receipt)+'\n')
    require(code==0,'Bounded native IQ-TREE exit='+str(code)+'; no scientific PASS, preserve outputs')
    require(actual_exe and limited and limited['pid']==child.pid and limited['argv']==argv and limited['identity']==identity
            and limited['native_address_space_soft_hard_bytes']==[LIMIT,LIMIT], 'Actual external-limit/native-exec proof missing')
    return native_success(directory,argv,identity)


def tree_checks(directory,ids):
    from Bio import Phylo
    require(all((directory/name).is_file() and (directory/name).stat().st_size for name in
                ('host.treefile','host.contree','host.log','host.iqtree','host.ufboot','host.best_scheme.nex')), 'Actual native outputs incomplete')
    for name in ('host.treefile','host.contree'):
        trees=list(Phylo.parse(directory/name,'newick'));require(len(trees)==1,'Native tree count differs')
        tips=[n.name for n in trees[0].get_terminals()]
        require(len(tips)==len(set(tips))==len(ids) and set(tips)==set(ids),'Actual native exact-tip membership differs')
    count=0
    for tree in Phylo.parse(directory/'host.ufboot','newick'):
        tips=[n.name for n in tree.get_terminals()];require(len(tips)==len(set(tips))==len(ids) and set(tips)==set(ids),'Actual bootstrap membership differs');count+=1
    require(count==1000,'Actual1000 UFBoot trees missing')
    return {'tips':len(ids),'bootstrap_trees_verified':1000,'root_policy':'EXPLICITLY_UNROOTED','scientific_validation':'NOT_RUN_INDEPENDENT_FINAL_GATE_REQUIRED'}


def portable_exports(args,analysis,directory):
    import csv
    text=(directory/'host.treefile').read_text().strip()
    (directory/'unrooted.nwk').write_bytes((directory/'host.treefile').read_bytes())
    (directory/'unrooted.nex').write_text('#NEXUS\nBEGIN TREES;\n TREE host = [&U] '+text+'\nEND;\n')
    with (args.alignment_input/'analyses'/analysis['name']/'tip_label_map.tsv').open(newline='') as stream:
        labels={row['assembly_accession']:row['tree_label'] for row in csv.DictReader(stream,delimiter='\t')}
    seen=[]
    def replace(match):
        key=match.group();require(key in labels,'Unknown labeled native tip');seen.append(key);return "'"+labels[key]+"'"
    labeled=re.sub(r'(?<![A-Za-z0-9_.])GCF_[0-9]{9}\.[0-9]+(?![A-Za-z0-9_.])',replace,text)
    require(len(seen)==len(set(seen))==len(analysis['accessions']) and set(seen)==set(analysis['accessions']),'Labeled exact-tip replacement differs')
    (directory/'unrooted_labeled.nwk').write_text(labeled+'\n')
    (directory/'unrooted_labeled.nex').write_text('#NEXUS\nBEGIN TREES;\n TREE host = [&U] '+labeled+'\nEND;\n')


def run(args):
    import resource
    require(sys.platform=='linux' and Path.cwd().resolve()==args.root,'Dedicated WD Linux/WSL project required')
    require(resource.getrlimit(resource.RLIMIT_AS)==(3758096384,3758096384) and len(os.sched_getaffinity(0))<=2,
            'Outer3.5GiB and two-core bounds required')
    identity,analyses=input_identity(args,native=True);args.output.mkdir(parents=True,exist_ok=True)
    frozen={'status':'FROZEN_RESUMED_INFERENCE_BEFORE_TOPOLOGY','identity':identity,'analyses':analyses,
            'alignment_reexecution':False,'deviation':'Original --mem failure and v3 native1.5GiB allocation failure preserved. Same scientific argv; separately frozen native3GiB/outer3.5GiB budget with1GiB Windows reserve enforced externally',
            'root_policy':identity['root_policy'],'optional_concordance':'NOT_RUN'}
    path=args.output/'inference_freeze.json'
    if path.exists():require(read(path)==frozen,'Frozen resumed inference differs; no overwrite')
    else:
        require(not list(args.output.iterdir()),'Unowned resumed inference namespace');save(path,frozen)
    args.environment=dict(os.environ);args.environment.update(PATH=str(args.host_env/'bin')+':/usr/bin:/bin',LC_ALL='C',
        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
    save(args.output/'runner_launch_receipt.json',{'utc':datetime.now(timezone.utc).isoformat(),'runner_pid':os.getpid(),
         'parent_pid':os.getppid(),'argv':sys.argv,'identity':identity,'outer_AS':list(resource.getrlimit(resource.RLIMIT_AS)),
         'cpu_affinity':sorted(os.sched_getaffinity(0)),'scientific_validation':'NOT_RUN'})
    completed=[];reused={}
    for analysis in analyses:
        current_identity,current_analyses=input_identity(args,native=True)
        require(current_identity==identity and current_analyses==analyses,
                'Source/code/input correction during inference; no dependent analysis launch')
        directory=args.output/'analyses'/analysis['name']/'iqtree';source=args.alignment_input/'analyses'/analysis['name']
        tree_identity={'stage04_identity':identity,'concat_sha256':sha(source/'concatenated.faa'),
                       'partitions_sha256':sha(source/'partitions.nex'),'alignment_validation_sha256':sha(args.alignment_validation)}
        argv=iqtree_argv(args,analysis);key=(tree_identity['concat_sha256'],tree_identity['partitions_sha256'])
        complete=directory/'tree_complete.json'
        if complete.is_file():
            record=read(complete);cache_proof(args,analysis,directory,tree_identity,record)
            result=tree_checks(directory,analysis['accessions'])
        elif key in reused:
            old=reused[key];directory.mkdir(parents=True,exist_ok=True);require(not list(directory.iterdir()),'Unowned reuse namespace')
            source_record=read(old/'tree_complete.json')
            for name in source_record['file_sha256']:
                if name.startswith(('host.','unrooted')):(directory/name).write_bytes((old/name).read_bytes())
            result=tree_checks(directory,analysis['accessions'])
            save(complete,{'execution':'COMPUTATION_OUTPUTS_CHECKED','identity':tree_identity,**result,
                 'execution_source':'REUSED_EXACT_IDENTICAL_ALIGNMENT_PARTITION_INFERENCE','source_analysis':old.parent.name,
                 'source_tree_complete_sha256':sha(old/'tree_complete.json'),
                 'file_sha256':frozen_tree_files(directory)})
        else:
            directory.mkdir(parents=True,exist_ok=True);invocation=directory/'inference_identity.json'
            value={'identity':tree_identity,'argv':argv,'external_cap_bytes':LIMIT}
            if invocation.exists():require(read(invocation)==value,'Native checkpoint argv/source identity differs')
            else:
                require(not list(directory.iterdir()),'Unowned native inference namespace');save(invocation,value)
            attempts=sorted(directory.glob('attempt_*'));success=None
            for attempt in reversed(attempts):
                receipt=attempt/'iqtree3.command.json'
                if receipt.is_file():
                    native=read(receipt);require(native['identity']==identity and native['argv']==argv,'Prior native attempt identity differs')
                    if native['exit_code']==0:native_success(attempt,argv,identity);success=attempt;break
                elif (attempt/'iqtree3.launch.json').is_file():
                    raise ValueError('Unfinished native attempt needs actual observer/PID reconciliation; no duplicate native launch')
            if success is None:
                attempt=next_attempt(directory);process(args,attempt,argv,identity)
            result=tree_checks(directory,analysis['accessions']);portable_exports(args,analysis,directory)
            save(complete,{'execution':'COMPUTATION_OUTPUTS_CHECKED','identity':tree_identity,**result,
                 'execution_source':'ACTUAL_IQTREE3_EXTERNAL_RLIMIT_WITH_NATIVE_RESUMABLE_CHECKPOINTS',
                 'file_sha256':frozen_tree_files(directory)})
        reused[key]=directory;completed.append({'analysis':analysis['name'],**result,'tree_complete_sha256':sha(complete)})
        save(args.output/'execution_progress.json',{'execution':'RUNNING_RESUMED_INFERENCE','completed_analyses':completed,
             'required_analyses':4,'runner_pid':os.getpid(),'scientific_validation':'NOT_RUN'});print(analysis['name']+' BOUNDED_ACTUAL_TREE_OUTPUT_CHECKED',flush=True)
    current_identity,current_analyses=input_identity(args,native=True)
    require(current_identity==identity and current_analyses==analyses,'Source/code/input changed before final inference summary')
    save(args.output/'phylogeny_summary.json',{'execution':'ALL_PRIMARY_AND_SENSITIVITY_INFERENCES_COMPLETED','identity':identity,
         'alignment_validation_sha256':sha(args.alignment_validation),'inference_freeze_sha256':sha(path),'analyses':completed,
         'scientific_validation':'NOT_RUN_INDEPENDENT_FINAL_GATE_REQUIRED','github_publication':'NOT_RUN',
         'root_policy':identity['root_policy'],'optional_concordance':'NOT_RUN'})


def parse():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=['trees'],default='trees')
    defaults={'root':Path.cwd(),'alignment_input':'.work/stage04_phylogeny_v2','alignment_validation':'.work/stage04_alignment_validation/validation_summary.json',
      'alignment_publication':'reports/stage04a/publication_receipt.json','source_control':'.work/stage04_controller',
      'output':'.work/stage04_inference_v4','config':'config/host_inference_stage04_v4.json','resource_receipt':'reports/stage04/resumed_inference_resource_preflight_v4.json',
      'host_env':'.tools/linux/host_env','source_producer':'scripts/stage04_phylogeny.py','source_validator':'scripts/stage04_validate.py',
      'controller_source':'scripts/stage04_inference_controller_v4.py','checker_source':'scripts/stage04_inference_validate_v4.py',
      'limit_helper':'scripts/stage04_iqtree_limit_v4.py',
      'observer_source':'scripts/stage04_linux_launcher_v4.py','original_observer_source':'scripts/stage04_linux_launcher.py',
      'previous_input':'.work/stage04_inference_v3','previous_control':'.work/stage04_inference_controller_v3',
      'previous_failed_attempt':'.work/stage04_inference_v3/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json',
      'previous_publication':'reports/stage04b/publication_receipt.json'}
    for name,value in defaults.items():p.add_argument('--'+name.replace('_','-'),type=Path,default=Path(value))
    p.add_argument('--failed-attempt',type=Path,required=True);a=p.parse_args();a.root=a.root.resolve()
    for name,value in vars(a).copy().items():
        if isinstance(value,Path):
            resolved=value.resolve() if value.is_absolute() else (a.root/value).resolve();setattr(a,name,resolved)
            require(resolved==a.root or a.root in resolved.parents,'Dedicated project path required')
    require(a.output!=a.alignment_input and a.alignment_input not in a.output.parents,'New inference namespace required')
    return a


if __name__=='__main__':
    a=parse()
    try:run(a)
    except Exception as error:
        save(a.output/'execution_failure.json',{'execution':'FAILED','error':str(error),'outputs_preserved':True,'runner_pid':os.getpid(),'scientific_validation':'NOT_PASS'})
        raise
