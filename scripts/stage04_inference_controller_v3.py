#!/usr/bin/env python3
"""WD Windows owner for resumed bounded IQ-TREE inference and independent check.

Original Stage04 alignments, failed attempt and controller remain immutable.
Uses the unchanged actual-PID observer/monitor, separate v3 lifecycle state.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import os
from pathlib import Path
import socket
import sys
import stage04_controller as C
import stage04_inference_v3 as R

PHASES=('trees','validate_final')
PASS='PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY'


def resource_preflight(args):
    windows=C.windows_snapshot(args.root)
    linux=json.loads(C.command(args.root,C.wsl(args,[C.linux_path(args.host_env/'bin/python'),'-u',
        C.linux_path(args.linux_launcher),'--mode','resources']),timeout=60))
    C.check(windows['available_bytes']>C.LIMIT and linux['linux_available_bytes']>C.LIMIT,
            'Measured current Windows/Linux headroom insufficient; no native launch')
    C.check(windows['disk_available_bytes']>5*1024**3 and len(linux['cpu_affinity_available'])>=2,'Measured disk/CPU scope insufficient')
    if not args.resource_receipt.exists():
        C.atomic(args.resource_receipt,{'utc':C.now(),'host':'WD','maximum_compute_threads':2,'iqtree_memory_mib':1536,
            'process_address_space_limit_bytes':C.LIMIT,'iqtree_address_space_limit_bytes':R.LIMIT,
            'native_memory_option':'OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS',
            'measured_windows_available_bytes':windows['available_bytes'],'measured_linux_available_bytes':linux['linux_available_bytes'],
            'measured_windows_disk_available_bytes':windows['disk_available_bytes'],'linux_cpu_affinity_available':linux['cpu_affinity_available'],
            'resource_scope':'New frozen external-cap inference preflight; old resource receipt unchanged'})
    value=C.load(args.resource_receipt)
    C.check(value['process_address_space_limit_bytes']==C.LIMIT and value['iqtree_address_space_limit_bytes']==R.LIMIT
            and value['maximum_compute_threads']==2 and value['iqtree_memory_mib']==1536
            and value['native_memory_option']=='OMITTED_UNSUPPORTED_WITH_PARTITION_MODELS'
            and value['measured_windows_available_bytes']>C.LIMIT and value['measured_linux_available_bytes']>C.LIMIT,
            'Frozen measured external-cap resource proof differs')
    return {'windows':windows,'linux':linux}


def input_identity(args):
    identity,analyses=R.input_identity(args,native=False)
    paths=[Path(__file__),args.producer,args.validator,args.limit_helper,args.linux_launcher,args.root/'scripts/stage04_controller.py',
           args.root/'scripts/wsl_project.sh',args.config,args.resource_receipt,args.source_producer,args.source_validator,
           args.alignment_validation,args.alignment_input/'analysis_freeze.json',args.alignment_input/'alignment_summary.json',
           args.alignment_input/'analysis_alignment_manifest.json',args.source_control/'state.json',args.failed_attempt,
           args.failed_attempt.parent/'iqtree3.stderr.txt']
    return {'scope':'Exact full196 resumed Stage4 inference; original validated alignments reused without recomputation',
            'file_sha256':{C.inside(args,p):C.digest(p) for p in paths},'inference_identity':identity,
            'maximum_compute_threads':2,'address_space_limit_bytes':C.LIMIT,'iqtree_address_space_limit_bytes':R.LIMIT,
            'iqtree_memory_mib':1536,'output':C.inside(args,args.output),'source_alignment_input':C.inside(args,args.alignment_input)}


def old_job_gate(args):
    state=C.load(args.source_control/'state.json');current=state.get('current')
    C.check(current and current['phase']=='trees','Preserved old failed phase required')
    directory=args.root/current['receipt_directory'];value=C.native_inspect(args,directory)
    C.check(value['status']=='ACTUAL_EXIT_RECEIPT_AVAILABLE' and value['exit_code']!=0
            and not value['job_alive'] and not value['launcher_alive'], 'Old exact job/observer may remain active; no duplicate allowed')
    return value


def phase_command(args,phase):
    path=C.linux_path;python=path(args.host_env/'bin/python')
    common=['--root',path(args.root),'--alignment-input',path(args.alignment_input),'--alignment-validation',path(args.alignment_validation),
            '--alignment-publication',path(args.alignment_publication),'--source-control',path(args.source_control),
            '--config',path(args.config),'--resource-receipt',path(args.resource_receipt),'--host-env',path(args.host_env),
            '--source-producer',path(args.source_producer),'--source-validator',path(args.source_validator),
            '--controller-source',path(Path(__file__)),'--checker-source',path(args.validator),'--limit-helper',path(args.limit_helper),
            '--failed-attempt',path(args.failed_attempt)]
    if phase=='trees':return [python,'-u',path(args.producer),'--phase','trees',*common,'--output',path(args.output)]
    return [python,'-u',path(args.validator),'--phase','final',*common,'--input',path(args.output),'--output',path(args.final_validation),
            '--producer-source',path(args.producer),'--host-config',path(args.host_config),'--markers',path(args.markers),
            '--marker-validation',path(args.marker_validation),'--orthology-config',path(args.orthology_config),
            '--original-markers',path(args.original_markers),'--original-marker-validation',path(args.original_marker_validation),
            '--original-resource-receipt',path(args.original_resource_receipt)]


def result_gate(args,phase):
    path=args.output/'phylogeny_summary.json' if phase=='trees' else args.final_validation/'validation_summary.json'
    value=C.load(path);frozen=C.load(args.output/'inference_freeze.json')
    C.check(value['inference_freeze_sha256']==C.digest(args.output/'inference_freeze.json'), 'Actual inference freeze hash missing/different')
    if phase=='trees':
        C.check(value['execution']=='ALL_PRIMARY_AND_SENSITIVITY_INFERENCES_COMPLETED' and len(value['analyses'])==4
                and value['identity']==frozen['identity'] and value['alignment_validation_sha256']==C.digest(args.alignment_validation),
                'Actual resumed four-tree construction incomplete')
    else:
        C.check(value['status']==PASS and value['analyses_verified']==4 and value['primary_tip_ids']==196
                and value['inference_identity']==frozen['identity'] and value['producer_identity']==frozen['identity']['alignment_producer_identity']
                and value['validator_source_sha256']==C.digest(args.validator)
                and value['phylogeny_summary_sha256']==C.digest(args.output/'phylogeny_summary.json')
                and value['original_analysis_freeze_sha256']==C.digest(args.alignment_input/'analysis_freeze.json')
                and value['original_alignment_summary_sha256']==C.digest(args.alignment_input/'alignment_summary.json')
                and value['original_analysis_manifest_sha256']==C.digest(args.alignment_input/'analysis_alignment_manifest.json')
                and value['alignment_validation_sha256']==C.digest(args.alignment_validation), 'Actual independent resumed final proof differs')
    return {'path':C.inside(args,path),'sha256':C.digest(path),'scientific_gate':value.get('status','CONSTRUCTION_ONLY_INDEPENDENT_GATE_REQUIRED')}


def progress(args,state,execution,failure=None):
    C.reconcile(args.root)
    if failure is None:C.check(input_identity(args)==state['identity'],'Current code/input correction differs; dependent continuation blocked')
    current=state.get('current') or {};directory=args.root/current['receipt_directory'] if current else None
    launch=C.load(directory/'linux_launch_receipt.json') if directory and (directory/'linux_launch_receipt.json').is_file() else None
    native=C.load(directory/'linux_progress.json') if directory and (directory/'linux_progress.json').is_file() else None
    complete=execution=='ALL_RESUMED_INFERENCE_AND_FINAL_PHASES_INDEPENDENTLY_VALIDATED'
    value={'utc':C.now(),'execution':execution,'phase':current.get('phase'),'controller_pid':os.getpid(),
            'windows_wsl_launcher_pid':current.get('windows_wsl_launcher_pid'),'windows_wsl_launcher_creation_utc':current.get('windows_wsl_launcher_creation_utc'),
            'linux_job_pid':launch['job_pid'] if launch else None,'linux_launcher_pid':launch['launcher_pid'] if launch else None,
            'actual_argv':launch['argv'] if launch else current.get('child_argv'),'actual_linux_process_measurements':native,
            'stdout_log':current.get('stdout_log'),'stderr_log':current.get('stderr_log'),'completed_resumed_phases':state['completed'],
            'scientific_input_identity':state['identity'],'scientific_validation':PASS if complete else 'INCOMPLETE',
            'alignment_substage':'ORIGINAL_TWO_PHASES_INDEPENDENTLY_VALIDATED_AND_STAGE04A_RELEASE_VERIFIED',
            'github_publication':'PROGRESS_COMMIT_ONLY_FULL_RELEASE_PENDING','failure':failure,'outputs_preserved':True}
    producer=args.output/'execution_progress.json'
    if producer.is_file():value['producer_progress']=C.load(producer)
    C.atomic(args.root/'reports/stage04/resumed_inference_progress_v3.json',value)
    C.atomic(args.root/'reports/stage04/progress.json',value);C.atomic(args.root/'status/stage04_execution.json',value)
    with (args.root/'status/stages.tsv').open(newline='',encoding='utf-8') as stream:rows=list(csv.DictReader(stream,delimiter='\t'))
    target=[row for row in rows if row['stage']=='4_phylogeny'];C.check(len(target)==1,'Stage4 status row lost')
    target[0].update(execution=execution,validation=value['scientific_validation'],publication='PROGRESS_PUBLISHED_RELEASE_PENDING')
    buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)
    C.atomic(args.root/'status/stages.tsv',buffer.getvalue())
    detail=('Original validated100-marker/full196 alignments plus four new bounded ML analyses and independent final validation completed; full portable Release/readback still required.' if complete else
            'Stage4 resumed inference '+execution+'. Original validated alignments/failure retained. Native unsupported --mem omitted; IQchild soft/hard1536MiB, outer2GiB, two threads. No full scientific or Release completion claimed.')
    if failure:detail+=' Blocker: '+failure
    status='# Current execution status\n\nUpdated '+C.now()+'. Full approved196 production cohort; no pilot.\n\n'+detail+'\n\n'
    status+='| Stage | Execution | Validation | Publication |\n|---|---|---|---|\n'+''.join('| '+' | '.join(row.values())+' |\n' for row in rows)
    status+='\nSeparate Stage04a alignment and final phylogeny/publication gates; private session traces excluded.\n'
    C.atomic(args.root/'STATUS.md',status);head=C.publish_progress(args.root)
    C.atomic(args.control/'last_progress_publication.json',{'utc':C.now(),'status':'REMOTE_ALLOWLIST_FILE_BYTES_VERIFIED','commit':head})


def needs_new_phase_preflight(args):
    path=args.control/'state.json'
    return not path.exists() or not C.load(path).get('current')


def run(args):
    C.check(sys.platform=='win32' and socket.gethostname().lower()=='wd' and Path.cwd().resolve()==args.root,'Dedicated WD Windows controller required')
    C.phase_command=phase_command;C.result_gate=result_gate;C.progress=progress;C.resource_preflight=resource_preflight
    C.PUBLIC=('STATUS.md','status/stages.tsv','status/stage04_execution.json','reports/stage04/progress.json',
              'reports/stage04/resumed_inference_progress_v3.json','reports/stage04/resumed_inference_resource_preflight_v3.json')
    with C.WorkflowLock(args.root/'.work/workflow.lock'):
        C.atomic(args.root/'.work/workflow_owner.json',{'pid':os.getpid(),'utc':C.now(),'script':C.inside(args,Path(__file__)),
                 'scope':'New bounded resumed inference/final validator; no repeated alignments or detector searches'})
        state=None
        try:
            C.reconcile(args.root);old_job_gate(args)
            if needs_new_phase_preflight(args):resource_preflight(args)
            identity=input_identity(args)
            path=args.control/'state.json'
            if path.exists():state=C.load(path);C.check(state['identity']==identity,'Frozen resumed controller identity changed; preserve state')
            else:
                state={'scope':'full196','started_utc':C.now(),'identity':identity,'completed':{},'current':None};C.state_update(args,state)
            for phase in PHASES:
                C.reconcile(args.root);old_job_gate(args);C.check(input_identity(args)==state['identity'],'Original/new immutable bytes changed')
                if phase in state['completed']:
                    item=state['completed'][phase];C.check(C.digest(args.root/item['actual_exit_receipt'])==item['actual_exit_receipt_sha256']
                        and C.load(args.root/item['actual_exit_receipt'])['exit_code']==0 and result_gate(args,phase)==item['gate'], 'Completed resumed actual proof changed')
                else:C.execute(args,state,phase)
                progress(args,state,'COMPLETED_RESUMED_'+phase.upper())
            progress(args,state,'ALL_RESUMED_INFERENCE_AND_FINAL_PHASES_INDEPENDENTLY_VALIDATED')
            C.atomic(args.control/'controller_complete.json',{'utc':C.now(),'execution':'ALL_RESUMED_INFERENCE_AND_FINAL_PHASES_INDEPENDENTLY_VALIDATED',
                'identity':identity,'completed':state['completed'],'source_alignment_phase_proofs':identity['inference_identity']['original_successful_phase_exit_sha256'],
                'publication':'FULL_STAGE04_RELEASE_AND_READBACK_REQUIRED'})
            print('ACTUAL_RESUMED_STAGE04_TREE_AND_FINAL_GATES_COMPLETE_RELEASE_REQUIRED',flush=True)
        except Exception as error:
            C.atomic(args.control/'controller_failure.json',{'utc':C.now(),'error':str(error),'outputs_preserved':True,'controller_pid':os.getpid(),
                      'dependent_stage_action':'BLOCKED; no resource/model/panel relaxation or duplicate native launch'})
            if state:
                try:progress(args,state,'STOPPED_WITH_EXPLICIT_BLOCKER',str(error))
                except Exception as publication_error:C.atomic(args.control/'failure_publication_failure.json',{'utc':C.now(),'error':str(publication_error)})
            raise


def parse():
    p=argparse.ArgumentParser(description=__doc__)
    defaults={'root':Path.cwd(),'alignment_input':'.work/stage04_phylogeny_v2','alignment_validation':'.work/stage04_alignment_validation/validation_summary.json',
      'alignment_publication':'reports/stage04a/publication_receipt.json','source_control':'.work/stage04_controller',
      'output':'.work/stage04_inference_v3','control':'.work/stage04_inference_controller_v3','final_validation':'.work/stage04_final_validation_v3',
      'config':'config/host_inference_stage04_v3.json','resource_receipt':'reports/stage04/resumed_inference_resource_preflight_v3.json',
      'host_env':'.tools/linux/host_env','source_producer':'scripts/stage04_phylogeny.py','source_validator':'scripts/stage04_validate.py',
      'producer':'scripts/stage04_inference_v3.py','validator':'scripts/stage04_inference_validate_v3.py',
      'limit_helper':'scripts/stage04_iqtree_limit_v3.py','linux_launcher':'scripts/stage04_linux_launcher.py',
      'host_config':'config/host_primary_stage03_v1.json','markers':'.work/stage03_orthology_v2',
      'marker_validation':'.work/stage03_curated_validation/validation_summary.json','orthology_config':'config/host_orthology_stage03_v2.json',
      'original_markers':'.work/stage03_markers_v1','original_marker_validation':'.work/stage03_marker_validation/validation_summary.json',
      'original_resource_receipt':'reports/stage04/resource_preflight.json'}
    for name,value in defaults.items():p.add_argument('--'+name.replace('_','-'),type=Path,default=Path(value))
    p.add_argument('--failed-attempt',type=Path,required=True);p.add_argument('--distribution',default='Ubuntu')
    p.add_argument('--publish-seconds',type=float,default=300);p.add_argument('--poll-seconds',type=float,default=5)
    a=p.parse_args();a.root=a.root.resolve();a.iqtree_memory_mib=1536
    for name,value in vars(a).copy().items():
        if isinstance(value,Path):setattr(a,name,value.resolve() if value.is_absolute() else (a.root/value).resolve());C.inside(a,getattr(a,name))
    a.controller_source=Path(__file__).resolve();a.checker_source=a.validator
    C.check(a.output!=a.alignment_input and a.control!=a.source_control and a.alignment_input not in a.output.parents,'Distinct resumed output/control namespaces required')
    C.check(a.publish_seconds>=60 and 1<=a.poll_seconds<=30,'Bounded progress cadence required');return a


if __name__=='__main__':run(parse())
