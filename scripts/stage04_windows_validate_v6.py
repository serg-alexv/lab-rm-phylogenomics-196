"""Independent native Windows source, lifecycle and tree evidence checks.

Does not import the producer or launch biological computation. Reuses pinned
independent Newick/numeric parsers from the prior checker, with explicit new
Windows process evidence checks instead of pretending it is Linux RLIMIT_AS.
"""
from pathlib import Path
import csv, hashlib, json, math, re, sys
from Bio import Phylo, SeqIO
import stage04_inference_validate_v5 as V

ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
ALIGN=ROOT/'.work/stage04_phylogeny_v2'
INPUT=ROOT/'.work/stage04_inference_windows_v6'
NAMES=['primary196','sensitivity162','sensitivity187_markers','sensitivity_complete155']
def sha(p):return V.digest(p)
def read(p):return V.json_read(p)
def check(ok,msg):V.check(ok,msg)

def source_gate():
    check(sha(ROOT/'scripts/stage04_inference_validate_v5.py')=='433e5b97fa6b90fd2e33b373f06df82abd717cb1c875e121f346c42155665efe','Pinned independent parser changed')
    check(sha(ROOT/'reports/stage04/migration_v5_native_source_check.json')=='a77a27a096ec24132e7d7672d5a916dfa9ff719ff90160b5859a5dd7e26ebca0','Executed migration/source certificate changed')
    approval=read(ROOT/'config/approval.json');ids=(ROOT/'config/approved_accessions.txt').read_text().splitlines()
    check(approval['human_approval']=='APPROVED_FOR_SEQUENCE_ANALYSIS' and approval['approved_assembly_count']==196 and approval['pilot'] is False and approval['routine_stage_human_wait'] is False and len(set(ids))==len(ids)==196 and sha(ROOT/'config/approved_accessions.txt')==approval['panel_accessions_sha256'],'Approved full196 panel changed')
    validation=read(ROOT/'.work/stage04_alignment_validation/validation_summary.json')
    check(sha(ROOT/'.work/stage04_alignment_validation/validation_summary.json')=='2dcec67c0de7c8930046d82ac3c87d011e295844873805f17aae3a2453855b04' and validation['status'].startswith('PASS_'),'Existing independent alignment certificate changed')
    publication=read(ROOT/'reports/stage04a/publication_receipt.json')
    check(publication['status']=='UPLOAD_VERIFIED' and all(a['download_readback_verified'] and a['all_zip_member_hashes_verified'] for a in publication['assets']),'Existing alignment Release is not readback verified')
    summary=read(ALIGN/'alignment_summary.json');manifest=read(ALIGN/'analysis_alignment_manifest.json')
    analyses=read(ALIGN/'analysis_freeze.json')['analyses']
    check([a['name'] for a in analyses]==NAMES and [(len(a['accessions']),len(a['markers'])) for a in analyses]==[(196,100),(162,100),(196,88),(155,100)] and set(analyses[0]['accessions'])==set(ids),'Frozen scientific analysis scopes changed')
    hashes={}
    for a,s in zip(analyses,summary['analyses']):
        check(a['name']==s['name'],'Frozen alignment order differs')
        for name,expected in s['file_sha256'].items():
            p=ALIGN/'analyses'/a['name']/name
            check(sha(p)==expected,'Accepted alignment artifact changed: '+a['name']+'/'+name)
            hashes['data:'+p.relative_to(ROOT).as_posix()]=expected
    # Verify only existing certificates/accepted artifacts, not the completed
    # HMM/aligner jobs or a repeated broad biological audit.
    for rel in ['.work/stage04_phylogeny_v2/analysis_freeze.json','.work/stage04_phylogeny_v2/alignment_summary.json','.work/stage04_phylogeny_v2/analysis_alignment_manifest.json','.work/stage04_alignment_validation/validation_summary.json','reports/stage04a/publication_receipt.json']:
        check(sha(ROOT/rel)==sha(HISTORY/rel),'Explicit retained historical/data certificate copies differ')
        hashes['data:'+rel]=sha(ROOT/rel)
    prior=read(ROOT/'reports/stage04/inference_v4_adoption.json')
    for source in prior['sources']:
        check(sha(ROOT/source['path'])==sha(HISTORY/source['path'])==source['sha256'],'Historical adopted source changed: '+source['path'])
    previous=HISTORY/'.work/stage04_inference_v3/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json'
    fail=read(previous)
    check(fail['exit_code']==2 and fail['argv'][fail['argv'].index('-m')+1]=='MFP' and '-p' in fail['argv'] and '--mem' not in fail['argv'],'Retained real V3 failure differs')
    hashes['historical:'+previous.relative_to(HISTORY).as_posix()]=sha(previous)
    for rel in ['config/approval.json','config/approved_accessions.txt','reports/stage04/migration_v5_native_source_check.json','reports/stage04/inference_v4_adoption.json']:
        hashes['data:'+rel]=sha(ROOT/rel)
    return {'status':'PASS_REUSED_FROZEN_FULL196_SOURCE_CERTIFICATES_AND_FOUR_ACCEPTED_INPUTS','file_sha256':hashes,'analyses':analyses,'completed_biological_jobs_repeated':0}

def expected_argv(executable,name):
    source=ALIGN/'analyses'/name;out=INPUT/'analyses'/name/'iqtree'
    return [str(executable),'-s',str(source/'concatenated.faa'),'--seqtype','AA','-p',str(source/'partitions.nex'),'-m','MFP','-B','1000','--alrt','1000','--seed','1961008','-T','2','-keep-ident','--boot-trees','--prefix',str(out/'host')]

def audit_analysis(name):
    frozen=read(INPUT/'inference_freeze.json');analysis=[a for a in frozen['source_identity']['analyses'] if a['name']==name]
    check(len(analysis)==1,'Unknown frozen analysis');analysis=analysis[0]
    directory=INPUT/'analyses'/name/'iqtree';proof=read(directory/'tree_complete.json')
    attempt=directory/proof['attempt'];launch=read(attempt/'launch.json');exit=read(attempt/'exit.json')
    check(exit['exit_code']==0 and exit['job_active_processes']==0 and exit['process_exited'] and exit['actual_job_process_ids']==[],'Actual native job has not fully completed')
    expected=expected_argv(frozen['executable'],name)
    check(launch['argv']==exit['argv']==expected and launch['child_pid']==exit['child_pid']>0 and launch['child_creation_filetime']==exit['creation_filetime'] and exit['actual_launch_receipt_sha256']==sha(attempt/'launch.json'),'Actual pinned command/PID/creation proof differs')
    check(launch['job_bound_before_resume'] is True and launch['memory_kind']=='WINDOWS_COMMITTED_MEMORY_NOT_LINUX_RLIMIT_AS' and launch['process_committed_memory_cap_bytes']==launch['aggregate_job_committed_memory_cap_bytes']==3221225472 and launch['affinity_mask'].bit_count()==launch['allowed_logical_processors']==2 and launch['actual_executable_sha256']==frozen['tool_identity']['executable_sha256'],'Actual Windows resource/platform binding differs')
    check(proof['inference_freeze_sha256']==sha(INPUT/'inference_freeze.json'),'Tree proof freeze mismatch')
    for member,expected_hash in proof['file_sha256'].items():check(sha(directory/member)==expected_hash,'Native/portable tree evidence changed: '+member)
    ids=analysis['accessions'];alignment={r.id:str(r.seq) for r in SeqIO.parse(ALIGN/'analyses'/name/'concatenated.faa','fasta')}
    tree=None
    for member,fmt in [('host.treefile','newick'),('host.contree','newick'),('unrooted.nwk','newick'),('unrooted.nex','nexus')]:
        trees=list(V.finite_tree_parse(directory/member,fmt));check(len(trees)==1,'Expected one unrooted host tree')
        names=[n.name for n in trees[0].get_terminals()]
        check(len(names)==len(set(names))==len(ids) and set(names)==set(ids),'Missing/foreign/duplicate accepted tip')
        if member=='host.treefile':tree=trees[0]
        if member.startswith('unrooted'):check(V.split_sets(trees[0],ids)==V.split_sets(tree,ids),'Portable export alters topology')
    support,omitted=V.branch_support_states(tree,alignment)
    count=0
    for boot in V.finite_tree_parse(directory/'host.ufboot','newick'):
        names=[n.name for n in boot.get_terminals()];check(len(names)==len(set(names))==len(ids) and set(names)==set(ids),'Bootstrap tip corruption');count+=1
    check(count==1000,'Executed1000 UFBoot trees required')
    report=(directory/'host.iqtree').read_text();log=(directory/'host.log').read_text()
    check(re.search(r'1000.*(?:ultrafast|bootstrap)|(?:ultrafast|bootstrap).*1000',report,re.I) and re.search(r'SH-aLRT|SH-like|SH approximate',report,re.I),'Actual native support methods missing')
    check('1961008' in log and 'IQ-TREE' in log,'Native seed/version evidence missing')
    with (ALIGN/'analyses'/name/'partitions.tsv').open(newline='',encoding='utf-8') as f:parts=list(csv.DictReader(f,delimiter='\t'))
    scheme=(directory/'host.best_scheme.nex').read_text()
    check(re.findall(r'charset\s+(\S+)\s*=\s*(\d+)\s*-\s*(\d+)\s*;',scheme,re.I)==[(r['partition'],r['start_one_based'],r['end_one_based']) for r in parts],'ModelFinder merged/reordered/resized frozen partitions')
    model=re.findall(r'charpartition\s+\S+\s*=\s*([^;]+);',scheme,re.I)
    check(len(model)==1 and [s.rsplit(':',1)[1].strip() for s in model[0].split(',')]==[r['partition'] for r in parts],'Actual per-partition model allocation changed')
    return {'analysis':name,'tips':len(ids),'ufboot_trees_verified':count,'support_nodes':support,'omitted_support_identical_alignments':omitted,'native_exit_sha256':sha(attempt/'exit.json'),'actual_usage':exit,'file_sha256':proof['file_sha256']}

def main():
    results=[audit_analysis(n) for n in NAMES]
    value={'status':'PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY','analyses_verified':4,'primary_tip_ids':196,'checker_source_sha256':sha(__file__),'inference_freeze_sha256':sha(INPUT/'inference_freeze.json'),'analyses':results,'platform':'NATIVE_WINDOWS_IQTREE3_1_4'}
    # Separate checker output namespace; never changes immutable native outputs.
    import stage04_controller as C
    C.atomic(ROOT/'.work/stage04_final_validation_windows_v6/validation_summary.json',value)
    print(value['status'])

if __name__=='__main__':main()
