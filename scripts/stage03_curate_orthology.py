"""Create a strict pre-topology view without duplicate complete MiaA proteins.

All original119 searches and fixed filters remain immutable. No HMM is rerun.
"""
from collections import Counter,defaultdict
from pathlib import Path
import csv,io,json,math,msvcrt,os,shutil
import production_resume as w
from workflow_publication import commit

R=w.R;ORIGINAL=R/'.work/stage03_markers_v1';OUT=R/'.work/stage03_orthology_v2'
GATE=R/'.work/stage03_marker_validation/validation_summary.json'
CONFIG=R/'config/host_orthology_stage03_v2.json'
REVIEW=R/'reports/stage03/host_profile_scope_review.json'
NEW_REVIEW=R/'reports/stage03/host_profile_scope_review_orthology_v2.json'
w.LOG=R/'reports/stage03/commands.jsonl'

def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))

def table(path,data):
    text=io.StringIO();writer=csv.DictWriter(text,fieldnames=list(data[0]),delimiter='\t',lineterminator='\n')
    writer.writeheader();writer.writerows(data);w.atomic(path,text.getvalue().encode())

def fasta_records(path):
    records=[];header=None;parts=[]
    for line in path.read_text(encoding='ascii').splitlines():
        if line.startswith('>'):
            if header is not None:records.append((header,''.join(parts)))
            header=line[1:];parts=[]
        else:parts.append(line)
    if header is not None:records.append((header,''.join(parts)))
    return records

def make_config(validation,manifest):
    old=json.loads((R/'config/host_primary_stage03_v1.json').read_text())
    by_locus=defaultdict(list)
    for row in manifest:by_locus[row['locus_key']].append(row)
    duplicates=[v for v in by_locus.values() if len(v)>1]
    assert len(duplicates)==192
    for pair in duplicates:
        assert {r['profile'] for r in pair}=={'IPPT','IPT'}
        assert len({r['source_sequence_sha256'] for r in pair})==1
    counts=Counter(r['profile'] for r in manifest)
    assert counts['IPPT']==196 and counts['IPT']==192
    result={'revision':'stage03-orthology-v2','frozen_before_alignment_and_topology':True,
            'no_biological_search_rerun':True,'excluded_primary_profiles':['IPT'],
            'retained_corresponding_profile':'IPPT','original_duplicate_loci':192,
            'selection_basis':'All192 IPT accepted complete proteins are the same exact loci/sequences as IPPT. IPPT has196/196 accepted loci and the RNA-specific family context; retain this complete-source ortholog once. This choice precedes alignment/topology and preserves all original evidence.',
            'primary_source_evidence':[
              {'url':'https://www.ebi.ac.uk/interpro/api/entry/pfam/PF01715/','raw_response_sha256':w.digest(R/'.work/host_profile_annotations/PF01715.json')},
              {'url':'https://www.ebi.ac.uk/interpro/api/entry/pfam/PF01745/','raw_response_sha256':w.digest(R/'.work/host_profile_annotations/PF01745.json')},
              {'url':'https://pubmed.ncbi.nlm.nih.gov/19158097/','PMID':'19158097','scope':'Primary structural work establishes reference E.coli MiaA tRNA recognition; no approved-strain activity claim.'}],
            'unchanged_thresholds':{'candidate_profiles':119,'initial_minimum':96,'assemblies':196,'occupancy_minimum':177,'post_recovery_fraction':0.8},
            'additional_strict_gate':'After excluding redundant IPT contribution, unique initial length-accepted loci must still be>=96/119; all196 retained or blocker.',
            'original_config_sha256':w.digest(R/'config/host_primary_stage03_v1.json'),
            'panel_sha256':w.digest(R/'config/approved_accessions.txt'),'profile_sha256':old['profile_sha256'],
            'original_inventory_summary_sha256':w.digest(ORIGINAL/'inventory_summary.json'),
            'original_validation_summary_sha256':w.digest(GATE),
            'original_accepted_sequence_manifest_sha256':w.digest(ORIGINAL/'accepted_sequence_manifest.tsv')}
    stages=rows(R/'status/stages.tsv')
    assert next(r for r in stages if r['stage']=='4_phylogeny')['execution']=='NOT_RUN'
    assert not (R/'.work/stage04_phylogeny_v1/analysis_freeze.json').exists()
    if CONFIG.exists():assert json.loads(CONFIG.read_text())==result,'Existing curation freeze differs; preserve old view'
    else:w.js(CONFIG,result)
    return result

def main():
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    validation=json.loads(GATE.read_text());inventory=json.loads((ORIGINAL/'inventory_summary.json').read_text())
    assert validation['status']=='PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
    assert validation['approved_assemblies']==validation['independently_verified_searches']==196
    assert validation['scientific_stage_status']=='HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED'
    assert validation['same_locus_multiple_profile_candidates']==192 and validation['scientific_blockers']==[]
    assert validation['host_function_review']['state'].startswith('REVIEWED_')
    assert validation['host_function_review']['review_sha256']==w.digest(REVIEW)
    assert validation['inventory_summary_sha256']==w.digest(ORIGINAL/'inventory_summary.json')
    assert validation['accepted_sequence_manifest_sha256']==w.digest(ORIGINAL/'accepted_sequence_manifest.tsv')
    original=rows(ORIGINAL/'accepted_sequence_manifest.tsv');config=make_config(validation,original)
    identity={'config_sha256':w.digest(CONFIG),'builder_source_sha256':w.digest(Path(__file__)),
              'original_validation_summary_sha256':w.digest(GATE),'original_review_sha256':w.digest(REVIEW)}
    receipt_path=OUT/'curation_receipt.json'
    if receipt_path.exists():
        receipt=json.loads(receipt_path.read_text());assert receipt['identity']==identity
        for path,digest in receipt['output_sha256'].items():assert w.digest(OUT/path)==digest
        assert w.digest(NEW_REVIEW)==receipt['host_profile_review_sha256']
        print('HASH_VERIFIED_CURATED_VIEW_REUSED',flush=True);return
    if OUT.exists() and any(OUT.iterdir()):raise ValueError('Unowned/partial curation output; preserve and inspect')
    OUT.mkdir(parents=True,exist_ok=True)
    for path in ORIGINAL.rglob('*'):
        relative=path.relative_to(ORIGINAL)
        if not path.is_file() or relative.parts[0] in ('searches','evidence','shims','marker_sequences','accepted_by_genome'):continue
        dest=OUT/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    accepted=[r for r in original if r['profile']!='IPT'];assert len(accepted)==19359
    assert len({r['locus_key'] for r in accepted})==len(accepted)
    table(OUT/'accepted_sequence_manifest.tsv',accepted)
    order=(ORIGINAL/'primary_marker_order.txt').read_text().splitlines();assert len(order)==101
    order.remove('IPT');assert len(order)==100
    w.atomic(OUT/'primary_marker_order.txt',('\n'.join(order)+'\n').encode())
    (OUT/'marker_sequences').mkdir()
    for name in order:shutil.copyfile(ORIGINAL/'marker_sequences'/(name+'.faa'),OUT/'marker_sequences'/(name+'.faa'))
    (OUT/'accepted_by_genome').mkdir()
    for path in (ORIGINAL/'accepted_by_genome').glob('*.faa'):
        records=[(h,s) for h,s in fasta_records(path) if h.split(' marker=',1)[1]!='IPT']
        w.atomic(OUT/'accepted_by_genome'/path.name,''.join('>'+h+'\n'+s+'\n' for h,s in records).encode())
    matrix=rows(ORIGINAL/'copy_occupancy_matrix.tsv')
    eligible_ipt={r['assembly_accession'] for r in matrix if r['profile']=='IPT' and r['length_accepted']=='True'}
    excluded_ipt={r['assembly_accession'] for r in original if r['profile']=='IPT'}
    for row in matrix:
        if row['profile']=='IPT' and row['state']=='PRIMARY_ACCEPTED':row['state']='ORTHOLOGY_REDUNDANT_PROFILE_EXCLUDED'
    table(OUT/'copy_occupancy_matrix.tsv',matrix)
    qc=rows(ORIGINAL/'marker_qc.tsv')
    for row in qc:
        row['orthology_review_state']='REDUNDANT_COMPLETE_SOURCE_SIGNAL_EXCLUDED' if row['profile']=='IPT' else 'KEEP_ORIGINAL_FIXED_FILTER_RESULT'
        if row['profile']=='IPT':row['primary_retained']='False'
    table(OUT/'marker_qc.tsv',qc)
    recovery=rows(ORIGINAL/'genome_recovery.tsv')
    for row in recovery:
        key=row['assembly_accession'];count=int(row['primary_accepted_markers'])-(key in excluded_ipt)
        row.update(primary_accepted_markers=str(count),primary_marker_denominator='100',
                   post_occupancy_recovery=str(count/100),post_minimum_markers='80',
                   orthology_unique_length_accepted_markers=str(int(row['length_accepted_markers'])-(key in eligible_ipt)))
        assert count>=80 and int(row['orthology_unique_length_accepted_markers'])>=96
    table(OUT/'genome_recovery.tsv',recovery)
    inventory.update(primary_markers=100,accepted_marker_sequences=19359,post_occupancy_denominator=100,
                     original_primary_markers=101,original_accepted_marker_sequences=19551,
                     original_inventory_summary_sha256=config['original_inventory_summary_sha256'],
                     original_accepted_sequence_manifest_sha256=config['original_accepted_sequence_manifest_sha256'],
                     orthology_curation_identity=identity,orthology_curation_status='CONSTRUCTED_INDEPENDENT_REVIEW_REQUIRED',
                     scientific_validation='NOT_RUN_INDEPENDENT_CURATED_CHECK_REQUIRED')
    w.js(OUT/'inventory_summary.json',inventory)
    review=json.loads(REVIEW.read_text());review['status']='SOURCE_SCOPE_REVIEWED_CURATED_VIEW_PENDING_INDEPENDENT_CHECK'
    review['accepted_source_hit_review'].update(inventory_summary_sha256=w.digest(OUT/'inventory_summary.json'),
                         accepted_sequence_manifest_sha256=w.digest(OUT/'accepted_sequence_manifest.tsv'),accepted_marker_sequences=19359)
    review['original_duplicate_signal_review'].update(status='EXPLICIT_CURATED_PROJECTION_INDEPENDENT_REVIEW_PENDING',
                        excluded_profile='IPT',retained_profile='IPPT',orthology_config_sha256=w.digest(CONFIG))
    w.js(NEW_REVIEW,review)
    outputs={p.relative_to(OUT).as_posix():w.digest(p) for p in OUT.rglob('*') if p.is_file()}
    w.js(receipt_path,{'status':'CURATED_VIEW_CONSTRUCTED_NOT_YET_INDEPENDENT_PASS','utc':w.now(),'pid':os.getpid(),
                      'identity':identity,'host_profile_review_sha256':w.digest(NEW_REVIEW),'output_sha256':outputs,
                      'original_profiles':101,'curated_profiles':100,'excluded_profile':'IPT','duplicated_loci_resolved':192,
                      'genomes':196,'minimum_unique_initial_recovery':min(int(r['orthology_unique_length_accepted_markers']) for r in recovery),
                      'minimum_post_curation_recovery':min(int(r['primary_accepted_markers']) for r in recovery),
                      'no_hmm_or_alignment_job_run':True})
    w.js(R/'reports/stage03/orthology_curation_receipt.json',json.loads(receipt_path.read_text()))
    w.status('3_markers','CURATED_ORTHOLOGY_VIEW_CONSTRUCTED','PENDING_INDEPENDENT_CURATED_REVIEW','PROGRESS_PUBLISHED',
             'Original101 marker inventory passed source/fixed-filter integrity but would duplicate192 complete MiaA proteins. Pre-topology curation excludes only redundant IPT, retaining100 markers/19359 sequences/all196. Original119 search evidence and thresholds are preserved; independent curation validation is next.')
    commit(['scripts/stage03_curate_orthology.py','scripts/summarize_accepted_host_scope.py','config/host_orthology_stage03_v2.json',
            'reports/stage03/host_profile_scope_review.json','reports/stage03/host_profile_scope_review_orthology_v2.json',
            'reports/stage03/orthology_curation_receipt.json','STATUS.md','status/stages.tsv'],
           'Freeze strict pre-topology MiaA deduplication; retain all196 and immutable119-profile search evidence')
    print('ACTUAL_CURATED_VIEW_CONSTRUCTED; independent scientific review required',flush=True)

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),
                                     'scope':'Strict pre-topology orthology curation; no biological searches'})
    try:main()
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
