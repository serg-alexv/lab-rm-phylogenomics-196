#!/usr/bin/env python3
"""Resume IQ-TREE partition inference from validated immutable Stage04a inputs.

No alignment or biological search is repeated. Unsupported native --mem is
removed; the separate exec helper enforces1536MiB soft/hard address space.
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
LIMIT=1610612736


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
            and config['outer_address_space_limit_bytes']==2147483648 and config['maximum_compute_threads']==2
            and config['native_memory_option']=='OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS'
            and config['alignment_reexecution'] is False and config['partition_option']=='-p'
            and config['model_selection']=='MFP_WITHOUT_MERGING' and config['ultrafast_bootstrap_replicates']==1000
            and config['sh_alrt_replicates']==1000 and config['seed']==1961008
            and config['root_policy']=='EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP',
            'Frozen resumed inference policy differs; no model/panel/resource relaxation')


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
    require(receipt['maximum_compute_threads']==2 and receipt['iqtree_memory_mib']==1536
            and receipt['process_address_space_limit_bytes']==2147483648
            and receipt['iqtree_address_space_limit_bytes']==LIMIT and receipt['native_memory_option']=='OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS'
            and receipt['measured_windows_available_bytes']>2147483648 and receipt['measured_linux_available_bytes']>2147483648,
            'Frozen measured external-cap resource receipt differs')
    paths={'resumed_producer_sha256':Path(__file__),'resumed_controller_sha256':args.controller_source,
           'resumed_validator_sha256':args.checker_source,'limit_helper_sha256':args.limit_helper,
           'source_producer_sha256':args.source_producer,'source_validator_sha256':args.source_validator,
           'source_controller_sha256':args.root/'scripts/stage04_controller.py',
           'observer_sha256':args.root/'scripts/stage04_linux_launcher.py','wsl_wrapper_sha256':args.root/'scripts/wsl_project.sh',
           'config_sha256':args.config,'resource_receipt_sha256':args.resource_receipt}
    identity={key:sha(path) for key,path in paths.items()}
    identity.update(alignment_producer_identity=old['identity'],
        original_analysis_freeze_sha256=sha(args.alignment_input/'analysis_freeze.json'),
        original_alignment_summary_sha256=sha(args.alignment_input/'alignment_summary.json'),
        original_analysis_manifest_sha256=sha(args.alignment_input/'analysis_alignment_manifest.json'),
        alignment_validation_sha256=sha(args.alignment_validation),original_successful_phase_exit_sha256=phase_sha,
        original_failed_phase_exit_sha256=sha(failure_exit),failed_native_attempt_sha256=sha(args.failed_attempt),
        failed_native_stderr_sha256=sha(stderr),iqtree3_sha256=old['identity']['iqtree3_sha256'],
        maximum_compute_threads=2,outer_address_space_limit_bytes=2147483648,iqtree_address_space_limit_bytes=LIMIT,
        native_memory_option='OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS',
        source_alignment_input=args.alignment_input.relative_to(args.root).as_posix(),
        source_control=args.source_control.relative_to(args.root).as_posix(),
        failed_native_attempt=args.failed_attempt.relative_to(args.root).as_posix(),
        root_policy='EXPLICITLY_UNROOTED_NO_VALIDATED_OUTGROUP')
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
            and limited['outer_address_space_soft_hard_bytes']==[2147483648,2147483648]
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
    require(resource.getrlimit(resource.RLIMIT_AS)==(2147483648,2147483648) and len(os.sched_getaffinity(0))<=2,
            'Outer2GiB and two-core bounds required')
    identity,analyses=input_identity(args,native=True);args.output.mkdir(parents=True,exist_ok=True)
    frozen={'status':'FROZEN_RESUMED_INFERENCE_BEFORE_TOPOLOGY','identity':identity,'analyses':analyses,
            'alignment_reexecution':False,'deviation':'Remove unsupported --mem with -p; stricter native soft/hard1536MiB enforced by exec helper',
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
      'output':'.work/stage04_inference_v3','config':'config/host_inference_stage04_v3.json','resource_receipt':'reports/stage04/resumed_inference_resource_preflight_v3.json',
      'host_env':'.tools/linux/host_env','source_producer':'scripts/stage04_phylogeny.py','source_validator':'scripts/stage04_validate.py',
      'controller_source':'scripts/stage04_inference_controller_v3.py','checker_source':'scripts/stage04_inference_validate_v3.py',
      'limit_helper':'scripts/stage04_iqtree_limit_v3.py'}
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
