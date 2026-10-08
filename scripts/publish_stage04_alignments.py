"""Publish independently validated alignments; never claim a completed phylogeny."""
import json,os,sys
from pathlib import Path
from types import SimpleNamespace
import stage04_controller as C
import production_resume as w
from portable_release import make_zip,publish_frozen
from workflow_publication import check,commit
R=Path(__file__).resolve().parents[1]
OUTPUT=R/'.work/stage04_phylogeny_v2'
GATE=R/'.work/stage04_alignment_validation'
CONTROL=R/'.work/stage04_controller'
PUBLIC=R/'reports/stage04a'
STAGING=R/'release_staging/stage04a'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def collect(folder,prefix):
    return [(p,prefix+'/'+p.relative_to(folder).as_posix()) for p in sorted(folder.rglob('*')) if p.is_file()]
def scientific_gate():
    state=read(CONTROL/'state.json');v=read(GATE/'validation_summary.json')
    C.check(state['current'] is None and set(state['completed'])=={'align','validate_alignment'},'Alignment-only actual state required')
    required={'scripts/stage04_controller.py','scripts/stage04_phylogeny.py','scripts/stage04_validate.py','scripts/stage04_linux_launcher.py'}
    C.check(required<=set(state['identity']['file_sha256']),'Executed mandatory source identity incomplete')
    for name,digest in state['identity']['file_sha256'].items():C.check(C.digest(R/name)==digest,'Executed source/input changed: '+name)
    args=SimpleNamespace(root=R,output=OUTPUT,alignment_validation=GATE,validator=R/'scripts/stage04_validate.py')
    for phase,row in state['completed'].items():
        path=R/row['actual_exit_receipt']
        C.check(C.digest(path)==row['actual_exit_receipt_sha256'],'Actual native exit receipt changed')
        C.exit_gate(path.parent,state['identity'],row['invocation_id'])
        C.check(C.result_gate(args,phase)==row['gate'],'Actual alignment gate bytes changed')
    C.check(v['status']=='PASS_ALIGNMENT_FORMATS_AND_PARTITIONS' and v['analyses_verified']==4 and
            v['primary_tip_ids']==196 and v['profiles_aligned']==100,'Independent exact full196 alignment gate failed')
    summary=read(OUTPUT/'alignment_summary.json')
    for analysis in summary['analyses']:
        folder=OUTPUT/'analyses'/analysis['name']
        C.check(not (folder/'iqtree').exists(),'Inference namespace already exists; use full Stage4 finalizer')
        for name,digest in analysis['file_sha256'].items():C.check(C.digest(folder/name)==digest,'Validated concatenation bytes changed')
    order=(R/'.work/stage03_orthology_v2/primary_marker_order.txt').read_text().split()
    C.check(len(order)==100 and set(p.name for p in (OUTPUT/'markers').iterdir() if p.is_dir())==set(order),'Exact marker namespace differs')
    for marker in order:
        folder=OUTPUT/'markers'/marker;receipt=read(folder/'alignment_complete.json')
        C.check(receipt['identity']['stage04_identity']==summary['identity'],'Marker execution identity differs')
        for name,digest in receipt['file_sha256'].items():C.check(C.digest(folder/name)==digest,'Validated marker bytes changed')
    return state,v,summary

def prepare(state,v,summary):
    PUBLIC.mkdir(parents=True,exist_ok=True);STAGING.mkdir(parents=True,exist_ok=True)
    copies={GATE/'validation_summary.json':'validation_summary.json',OUTPUT/'alignment_summary.json':'alignment_summary.json',
            OUTPUT/'analysis_freeze.json':'analysis_freeze.json',OUTPUT/'analysis_alignment_manifest.json':'analysis_alignment_manifest.json',
            CONTROL/'controller_failure.json':'initial_resource_failure.json'}
    for source,name in copies.items():w.atomic(PUBLIC/name,source.read_bytes())
    w.js(PUBLIC/'executed_alignment_phases.json',state['completed'])
    guide=('Stage04a: independently validated full196 host alignments, not a completed phylogeny.\n'
           'Extract this standalone ZIP with Windows Explorer or PowerShell. Every payload member is in SHA256SUMS.txt.\n'
           'host_alignments/analyses contains primary196 and three sensitivity concatenations in FASTA/CLUSTAL/PHYLIP/NEXUS, partitions and exact source-block maps.\n'
           'host_alignments/markers preserves raw and trimmed native alignments, column maps, four portable formats and scientific command/exit evidence.\n'
           'Use exact versioned assembly IDs; missing marker blocks are gaps. Primary196 has100 markers/17456 amino-acid columns.\n'
           'No IQ-TREE result, R-M inventory or figure is supplied or claimed by this substage. Those mandatory stages remain pending.\n'
           'The actual executed Stage3 source/marker release is a separate dependency: stage03-hostmarkers196-v1.\n')
    report=('# Validated host alignment substage\n\n'
            'All100 source-validated host markers were aligned once with pinned MAFFT and trimAl. The separate BioPython checker independently verified every retained trim column, all four file formats, all source-locus blocks and exhaustive partitions for all four frozen analyses.\n\n'
            'Primary196:196 tips,100 markers,17456 amino-acid columns. Sensitivity162:162 tips/100 markers/17456 columns. High-occupancy sensitivity:196 tips/88 markers/15174 columns. Complete Genome/Chromosome sensitivity:155 tips/100 markers/17456 columns. No primary genome was pruned.\n\n'
            'Actual alignment elapsed954.60s, child CPU1343.42s, maximum child RSS102830080bytes, sampled concurrent RSS peak113598464bytes. Independent alignment audit elapsed25.11s, child CPU6.20s, maximum child RSS125972480bytes. These describe the recorded process scopes; sampling and shared-page limits remain in the native receipts.\n\n'
            'At15:18:21UTC the controller stopped before IQ-TREE launch because the combined Windows/Linux headroom preflight failed. The original frozen threshold is greater than2147483648bytes available on both systems. The existing controller did not retain the failed-instant numeric snapshot; follow-up at15:19:05UTC showed Windows2132267008bytes and Linux7208030208bytes, identifying Windows below the threshold in that follow-up. At15:20:41UTC Windows free RAM measured4974198784bytes. No process was killed, no limit changed and no inference was launched on the failed preflight. The original failure and completed native exit receipts are preserved.\n\n'
            'Scientific validation:PASS_ALIGNMENT_FORMATS_AND_PARTITIONS. Whole Stage4 phylogeny remains incomplete: no topology, UFBoot, SH-aLRT or sensitivity tree is claimed here. The unchanged controller can resume past completed align/check checkpoints only when its current resource gate passes.\n\n'
            'No registered Geneious application or Geneious executable on PATH was found by the WD checks. Geneious import:NOT_RUN; formats were independently parser-tested.\n\n'+guide)
    w.atomic(PUBLIC/'REPORT.md',report.encode());w.atomic(PUBLIC/'RELEASE_NOTES.md',report.encode())
    assets=[make_zip(STAGING/'stage04a-full196-validated-alignments.zip',collect(OUTPUT,'host_alignments'),guide)]
    members=collect(GATE,'independent_alignment_validation')
    for phase,row in state['completed'].items():
        folder=(R/row['actual_exit_receipt']).parent
        members+=collect(folder,'native_phase_receipts/'+phase)
        for log in ('stdout_log','stderr_log'):members.append((R/row[log],'native_phase_logs/'+phase+'.'+log+'.txt'))
    scripts=['stage04_controller.py','stage04_linux_launcher.py','stage04_phylogeny.py','stage04_validate.py',
             'stage04_controller_synthetic.py','stage04_orthology_gate_synthetic.py','stage04_synthetic.py',
             'publish_stage04_alignments.py','validate_windows_zip.ps1','portable_release.py','workflow_publication.py',
             'production_resume.py','wsl_project.sh']
    paths=['scripts/'+n for n in scripts]+['config/'+n for n in ['approved_accessions.txt','approved_panel.tsv','approval.json',
             'host_primary_stage03_v1.json','host_orthology_stage03_v2.json']]
    paths+=['reports/stage04/'+n for n in ['CONTROLLER.md','METHOD.md','resource_preflight.json','tooling_handoff_manifest.json',
             'controller_synthetic_tests.json','orthology_gate_synthetic_tests.json','producer_synthetic_tests.json',
             'independent_synthetic_tests.json','controller_independent_source_review.json','CONTROLLER_INDEPENDENT_SOURCE_REVIEW.md']]
    paths+=['reports/stage04a/'+n for n in ['validation_summary.json','alignment_summary.json','analysis_freeze.json',
             'analysis_alignment_manifest.json','initial_resource_failure.json','executed_alignment_phases.json','REPORT.md','RELEASE_NOTES.md']]
    check(paths);members+=[(R/p,p) for p in paths]
    for source,_ in members:C.check(not C.SECRET.search(source.read_bytes()),'Credential-like publication content withheld')
    assets.append(make_zip(STAGING/'stage04a-methods-and-independent-evidence.zip',members,guide))
    w.js(PUBLIC/'asset_manifest.json',{'stage':'stage04a','approved_assemblies':196,'scientific_validation':v['status'],
         'whole_stage04_phylogeny':'NOT_COMPLETED','alignment_validation_sha256':C.digest(GATE/'validation_summary.json'),
         'analysis_freeze_sha256':C.digest(OUTPUT/'analysis_freeze.json'),'assets':assets,'publication_receipts_separate':True})
    paths.append('reports/stage04a/asset_manifest.json')
    w.atomic(PUBLIC/'SHA256SUMS.txt',''.join(C.digest(R/p)+'  '+p+'\n' for p in sorted(paths)).encode())
    paths.append('reports/stage04a/SHA256SUMS.txt');w.js(STAGING/'payload_paths.json',paths)
    return paths

def main():
    with C.WorkflowLock(R/'.work/workflow.lock'):
        C.reconcile(R);state,v,summary=scientific_gate()
        plan=R/'status/stage04a_publication_plan.json'
        if plan.exists():
            manifest=read(PUBLIC/'asset_manifest.json')
            C.check(manifest['alignment_validation_sha256']==C.digest(GATE/'validation_summary.json') and
                    manifest['analysis_freeze_sha256']==C.digest(OUTPUT/'analysis_freeze.json'),'Frozen substage science changed')
            paths=read(STAGING/'payload_paths.json')
        else:paths=prepare(state,v,summary)
        receipt=publish_frozen('stage04a','stage04a-hostalignments196-v1',STAGING,PUBLIC/'asset_manifest.json',paths,
                 'Stage04a: independently validated full196 alignments; phylogeny pending',PUBLIC/'RELEASE_NOTES.md')
        receipt.update(approved_assemblies=196,scientific_validation=v['status'],whole_stage04_phylogeny='NOT_COMPLETED',
                       alignment_validation_sha256=C.digest(GATE/'validation_summary.json'))
        w.js(PUBLIC/'publication_receipt.json',receipt)
        commit(['reports/stage04a/publication_receipt.json','reports/stage04a/publication_progress.json',
                'reports/stage04a/publication_commands.jsonl'],'Verify portable full196 alignment substage without claiming completed phylogeny')
        print('STAGE04A_VALIDATED_ALIGNMENT_PORTABLE_RELEASE_VERIFIED; FULL_PHYLOGENY_STILL_PENDING',flush=True)
if __name__=='__main__':main()
