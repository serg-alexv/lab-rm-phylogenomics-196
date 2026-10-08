#!/usr/bin/env python3
"""Independent topology-blind IPT/IPPT projection audit; no producer imports/search.

The executed original independent marker report remains a prerequisite. This
reader verifies exactly one whole redundant profile is removed, all source
sequences and native fixed-filter evidence remain unchanged, and no full source
protein contributes multiple retained marker blocks.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath
import tempfile

LIMIT='Orthology projection/source identity check only; no new HMM search, topology, R-M prediction or demonstrated protein function.'
MODIFIED={'accepted_sequence_manifest.tsv','primary_marker_order.txt','copy_occupancy_matrix.tsv',
          'marker_qc.tsv','genome_recovery.tsv','inventory_summary.json'}
NOT_COPIED={'searches','evidence','shims','marker_sequences','accepted_by_genome'}

def require(value,detail):
    if not value:raise ValueError(detail)
def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()
def seqsha(sequence):return hashlib.sha256(sequence.encode('ascii')).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');temp.replace(path)
def table(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream,delimiter='\t');fields=reader.fieldnames
        require(fields and len(fields)==len(set(fields)),'Missing/duplicate TSV columns: '+str(path))
        rows=list(reader)
    require(all(None not in r and all(v is not None for v in r.values()) for r in rows),'TSV row width differs: '+str(path))
    return fields,rows
def put_table(path,fields,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)
def true(value):
    require(value in ('True','False'),'Noncanonical Boolean in biological matrix');return value=='True'
def fasta(path):
    rows=[];header=None;parts=[]
    for line in Path(path).read_text(encoding='ascii').splitlines():
        if line.startswith('>'):
            if header is not None:rows.append((header,''.join(parts)))
            header=line[1:];require(header,'Empty FAA header');parts=[]
        elif line:
            require(header is not None and line==line.strip() and line.isalpha() and line.upper()==line,'Malformed/altered FAA sequence')
            parts.append(line)
    if header is not None:rows.append((header,''.join(parts)))
    require(rows and all(sequence for header,sequence in rows) and len(rows)==len({header for header,sequence in rows}),'Empty/duplicate FAA records')
    return rows
def compare_numeric(left,right,label):
    require(math.isfinite(float(right)) and math.isclose(float(left),float(right),rel_tol=0,abs_tol=1e-14),'Incorrect derived numeric value: '+label)

def check_projection(original,curated,panel):
    """Recompute projection from original rows without calling a producer."""
    original=Path(original);curated=Path(curated)
    of,old=table(original/'accepted_sequence_manifest.tsv');nf,new=table(curated/'accepted_sequence_manifest.tsv')
    require(of==nf and len(old)==19551,'Original accepted manifest schema/count differs from executed approved projection')
    require(all(r['assembly_accession'] in panel for r in old),'Unknown assembly in original manifest')
    old_index={(r['assembly_accession'],r['profile']):r for r in old}
    require(len(old_index)==len(old),'Duplicate original accepted genome/profile')
    old_order=(original/'primary_marker_order.txt').read_text(encoding='ascii').split()
    require(len(old_order)==101 and len(set(old_order))==101 and old_order==sorted(old_order) and 'IPT' in old_order and 'IPPT' in old_order,
            'Original primary marker order must be exact sorted101 including IPT/IPPT')
    order=[name for name in old_order if name!='IPT'];new_order=(curated/'primary_marker_order.txt').read_text(encoding='ascii').split()
    require(new_order==order and len(order)==100,'Curated order is not the sole whole-profile IPT exclusion')
    require(set(r['profile'] for r in old)==set(old_order),'Original accepted rows/profile order differs')
    old_counts=Counter(r['profile'] for r in old)
    require(old_counts['IPPT']==196 and old_counts['IPT']==192,'Documented IPPT100-percent and IPT192 accepted occupancy differs')
    removed=[r for r in old if r['profile']=='IPT'];expected=[r for r in old if r['profile']!='IPT']
    require(len(removed)==192 and new==expected and len(new)==19359,'Curated manifest is not exact original rows minus192 IPT rows')
    duplicates=defaultdict(list)
    for r in old:duplicates[r['locus_key']].append(r['profile'])
    old_overlap={key:values for key,values in duplicates.items() if len(values)>1}
    require(len(old_overlap)==192 and all(sorted(v)==['IPPT','IPT'] for v in old_overlap.values()),'Original duplicate signals differ from sole documented MiaA pair')
    require({r['locus_key'] for r in removed}==set(old_overlap),'Excluded IPT loci do not exactly resolve documented duplicate signals')
    for r in removed:
        match=old_index.get((r['assembly_accession'],'IPPT'))
        require(match and all(match[k]==r[k] for k in ('locus_key','source_sequence_sha256','protein_aa_length','protein_accession')),
                'IPPT/IPT exclusion lacks exact same-source protein evidence')
    require(len(new)==len({r['locus_key'] for r in new}),'Remaining repeated full source protein marker signal')

    mf,matrix=table(original/'copy_occupancy_matrix.tsv');cf,current=table(curated/'copy_occupancy_matrix.tsv')
    require(mf==cf and len(matrix)==len(current)==196*119,'Full196x119 matrix was pruned or schema changed')
    index={(r['assembly_accession'],r['profile']):r for r in matrix}
    require(len(index)==len(matrix) and {a for a,name in index}==set(panel) and len({name for a,name in index})==119,'Original full matrix membership differs')
    changes=0
    for before,after in zip(matrix,current):
        expected_row=before.copy()
        if before['profile']=='IPT' and before['state']=='PRIMARY_ACCEPTED':expected_row['state']='ORTHOLOGY_REDUNDANT_PROFILE_EXCLUDED';changes+=1
        require(after==expected_row,'Curated matrix changed source/copy/length/missingness or another marker cell')
    require(changes==192,'Expected exactly192 changed IPT PRIMARY_ACCEPTED cells')
    retained_cells={(r['assembly_accession'],r['profile']) for r in current if r['state']=='PRIMARY_ACCEPTED'}
    require(retained_cells=={(r['assembly_accession'],r['profile']) for r in new},'Curated PRIMARY_ACCEPTED cells/manifest join differs')
    for r in new:
        cell=index[(r['assembly_accession'],r['profile'])]
        require(cell['locus_key']==r['locus_key'] and true(cell['length_accepted']) and int(cell['qualifying_distinct_loci'])==1,
                'Accepted manifest lacks original unique length-accepted locus')

    qf,qc=table(original/'marker_qc.tsv');vf,view_qc=table(curated/'marker_qc.tsv')
    require(vf==qf+['orthology_review_state'] and len(qc)==len(view_qc)==119,'Curated marker QC schema/count differs')
    require(len({r['profile'] for r in qc})==119,'Duplicate marker QC profile')
    for before,after in zip(qc,view_qc):
        expected_row=before.copy()
        if before['profile']=='IPT':expected_row['primary_retained']='False'
        expected_state='REDUNDANT_COMPLETE_SOURCE_SIGNAL_EXCLUDED' if before['profile']=='IPT' else 'KEEP_ORIGINAL_FIXED_FILTER_RESULT'
        require({k:after[k] for k in qf}==expected_row and after['orthology_review_state']==expected_state, 'Curated QC modified fixed length/occupancy facts')
        require(true(after['primary_retained'])==(after['profile'] in order),'Curated marker QC/order retained flag differs')
    occupancy=Counter(r['profile'] for r in new)
    for row in view_qc:
        if row['profile'] in order:require(int(row['accepted_genomes_fixed196'])==occupancy[row['profile']]>=177,'Retained marker fails original177/196 occupancy')

    gf,genomes=table(original/'genome_recovery.tsv');rf,recovery=table(curated/'genome_recovery.tsv')
    require(rf==gf+['orthology_unique_length_accepted_markers'] and [r['assembly_accession'] for r in genomes]==panel
            and [r['assembly_accession'] for r in recovery]==panel,'Exact196 genome recovery schema/order differs')
    counts=Counter(r['assembly_accession'] for r in new);initial_unique=[]
    initial_counts=Counter(r['assembly_accession'] for r in matrix if true(r['length_accepted']))
    original_primary_counts=Counter(r['assembly_accession'] for r in old)
    for before,after in zip(genomes,recovery):
        accession=before['assembly_accession'];initial=int(before['length_accepted_markers'])
        require(initial==initial_counts[accession]>=96 and int(before['primary_accepted_markers'])==original_primary_counts[accession]
                and after['length_accepted_markers']==before['length_accepted_markers'] and after['recovery_fixed119']==before['recovery_fixed119'],
                'Original96/119 genome gate altered or failed')
        compare_numeric(initial/119,before['recovery_fixed119'],'original initial119 recovery')
        unique=initial-int(true(index[(accession,'IPT')]['length_accepted']))
        require(unique>=96 and int(after['orthology_unique_length_accepted_markers'])==unique,'Independent unique initial96/119 orthology gate failed')
        require(int(after['primary_accepted_markers'])==counts[accession]>=80 and int(after['primary_marker_denominator'])==100
                and int(after['post_minimum_markers'])==80,'Post-occupancy80/100 genome gate differs or failed')
        compare_numeric(counts[accession]/100,after['post_occupancy_recovery'],'curated post100 recovery')
        initial_unique.append(unique)

    require({p.stem for p in (original/'marker_sequences').glob('*.faa')}==set(old_order),'Original marker FAA set differs')
    require({p.stem for p in (curated/'marker_sequences').glob('*.faa')}==set(order),'Curated marker FAA set contains missing/extra/excluded profile')
    manifest_by_profile=defaultdict(list)
    for r in old:manifest_by_profile[r['profile']].append(r)
    checked_sequences=0
    for name in old_order:
        file=original/'marker_sequences'/f'{name}.faa';records=fasta(file);rows=manifest_by_profile[name]
        require([header for header,seq in records]==[r['assembly_accession'] for r in rows],'Original marker FAA/manifest order differs')
        for (header,sequence),row in zip(records,rows):
            require(seqsha(sequence)==row['source_sequence_sha256'] and len(sequence)==int(row['protein_aa_length']), 'Original accepted sequence/hash join differs')
        if name!='IPT':
            require(sha(file)==sha(curated/'marker_sequences'/file.name),'Retained marker FAA bytes changed')
            checked_sequences+=len(records)
    require(checked_sequences==19359,'Retained marker FAA sequence total differs')
    require({p.stem for p in (original/'accepted_by_genome').glob('*.faa')}==set(panel)
            and {p.stem for p in (curated/'accepted_by_genome').glob('*.faa')}==set(panel),'Per-genome accepted FAA omits/adds an assembly')
    manifest_by_genome=defaultdict(list)
    for r in old:manifest_by_genome[r['assembly_accession']].append(r)
    for a in panel:
        rows=manifest_by_genome[a];records=fasta(original/'accepted_by_genome'/f'{a}.faa')
        lookup={r['locus_key']+' marker='+r['profile']:r for r in rows}
        require(len(lookup)==len(rows)==len(records) and set(lookup)=={header for header,seq in records},'Original per-genome FAA source/header join differs')
        for header,sequence in records:
            row=lookup[header];require(seqsha(sequence)==row['source_sequence_sha256'] and len(sequence)==int(row['protein_aa_length']),'Original genome FAA/source hash differs')
        expected_records=[(h,s) for h,s in records if not h.endswith(' marker=IPT')]
        require(fasta(curated/'accepted_by_genome'/f'{a}.faa')==expected_records,'Curated per-genome FAA differs from exact source projection')
    return {'original_primary_markers':101,'original_accepted_marker_sequences':19551,'excluded_profile':'IPT',
            'retained_corresponding_profile':'IPPT','excluded_accepted_sequences':192,'primary_markers':100,
            'accepted_marker_sequences':19359,'original_same_locus_multiple_profile_candidates':192,
            'same_locus_multiple_profile_candidates':0,'marker_cells':23324,'minimum_unique_initial_length_markers':min(initial_unique)}

def check_prerequisites(args,panel):
    old=load(args.original_validation);inventory=load(args.original_markers/'inventory_summary.json')
    identity=load(args.original_markers/'input_identity.json');config=load(args.config)
    require(old.get('status')=='PASS_MARKER_SOURCE_AND_FIXED_FILTERS'
            and old.get('scientific_stage_status')=='HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED'
            and old.get('approved_assemblies')==old.get('independently_verified_searches')==196
            and old.get('profiles_searched')==119 and old.get('marker_cells')==23324
            and old.get('primary_markers')==101 and old.get('accepted_marker_sequences')==19551
            and old.get('same_locus_multiple_profile_candidates')==192 and old.get('scientific_blockers')==[],
            'Original full196 independently executed marker/source/fixed-filter prerequisite differs')
    require(old.get('validator_source_sha256')==sha(args.original_checker)
            and old.get('source_reader_sha256')==sha(args.source_reader),'Original independent checker/source-reader code changed')
    for key,path in [('inventory_summary_sha256',args.original_markers/'inventory_summary.json'),
                     ('accepted_sequence_manifest_sha256',args.original_markers/'accepted_sequence_manifest.tsv'),
                     ('primary_marker_order_sha256',args.original_markers/'primary_marker_order.txt'),
                     ('config_sha256',args.original_config),('profile_sha256',args.profile)]:
        require(old.get(key)==sha(path),'Original executed evidence hash differs: '+key)
    require(identity==inventory.get('identity')==old.get('producer_identity')
            and identity.get('approved_accessions_sha256')==sha(args.panel),'Original producer/panel identity differs')
    function=old.get('host_function_review',{})
    require(function.get('state')=='REVIEWED_CONSERVED_HOST_PROFILE_SCOPE_WITH_DOCUMENTED_LIMITS'
            and function.get('profiles_accounted')==119 and function.get('source_rm_candidates')==function.get('unresolved_rm_candidates')==0
            and function.get('review_sha256')==sha(args.original_review),'Original accepted-source function review incomplete or changed')
    require(load(args.original_validation.parent/'potential_rm_source_candidates.json')==[], 'Original executed source RM candidate audit not empty')
    require(config.get('revision')=='stage03-orthology-v2' and config.get('frozen_before_alignment_and_topology') is True
            and config.get('no_biological_search_rerun') is True and config.get('excluded_primary_profiles')==['IPT']
            and config.get('retained_corresponding_profile')=='IPPT' and config.get('original_duplicate_loci')==192
            and bool(config.get('selection_basis')) and bool(config.get('additional_strict_gate')),
            'Curation policy is not explicit whole-profile topology-blind MiaA deduplication')
    require(config.get('unchanged_thresholds')=={'candidate_profiles':119,'initial_minimum':96,'assemblies':196,
                                               'occupancy_minimum':177,'post_recovery_fraction':0.8},'Curation changes frozen scientific thresholds')
    for key,path in [('original_config_sha256',args.original_config),('panel_sha256',args.panel),('profile_sha256',args.profile),
                     ('original_inventory_summary_sha256',args.original_markers/'inventory_summary.json'),
                     ('original_validation_summary_sha256',args.original_validation),
                     ('original_accepted_sequence_manifest_sha256',args.original_markers/'accepted_sequence_manifest.tsv')]:
        require(config.get(key)==sha(path),'Frozen curation prerequisite bytes changed: '+key)
    original_config=load(args.original_config)
    require(original_config.get('genome_recovery_fixed_denominator')==119 and original_config.get('genome_minimum_accepted_markers')==96
            and original_config.get('marker_occupancy_fixed_denominator')==196 and original_config.get('marker_minimum_accepted_genomes')==177
            and original_config.get('post_occupancy_genome_recovery_minimum')==0.8,'Original frozen threshold prerequisite differs')
    evidence=config.get('primary_source_evidence',[]);pfam={}
    for item in evidence:
        url=item.get('url','')
        for accession in ('PF01715','PF01745'):
            if url=='https://www.ebi.ac.uk/interpro/api/entry/pfam/'+accession+'/':
                require(accession not in pfam and item.get('raw_response_sha256')==sha(args.profile_annotations/(accession+'.json')),
                        'Missing/different primary Pfam curation evidence');pfam[accession]=item
    require(set(pfam)=={'PF01715','PF01745'} and any(r.get('PMID')=='19158097' and r.get('scope') for r in evidence),
            'Primary MiaA profile/structural evidence is incomplete')
    return old,inventory,identity,config

def check_receipt_and_copies(args,old_inventory,old_identity,config,counts):
    receipt=load(args.curated_markers/'curation_receipt.json');curated_inventory=load(args.curated_markers/'inventory_summary.json')
    expected_identity={'config_sha256':sha(args.config),'builder_source_sha256':sha(args.curator_source),
                       'original_validation_summary_sha256':sha(args.original_validation),'original_review_sha256':sha(args.original_review)}
    require(receipt.get('status')=='CURATED_VIEW_CONSTRUCTED_NOT_YET_INDEPENDENT_PASS'
            and receipt.get('identity')==expected_identity and receipt.get('no_hmm_or_alignment_job_run') is True
            and receipt.get('original_profiles')==101 and receipt.get('curated_profiles')==100
            and receipt.get('excluded_profile')=='IPT' and receipt.get('duplicated_loci_resolved')==192 and receipt.get('genomes')==196,
            'Curation receipt provenance/execution/counts differs')
    actual={p.relative_to(args.curated_markers).as_posix():p for p in args.curated_markers.rglob('*')
            if p.is_file() and p!=args.curated_markers/'curation_receipt.json'}
    hashes=receipt.get('output_sha256',{})
    require(set(hashes)==set(actual),'Curation receipt does not exactly cover all view payload files')
    for name,digest in hashes.items():
        parts=PurePosixPath(name)
        require(not parts.is_absolute() and '..' not in parts.parts and '\\' not in name
                and args.curated_markers in actual[name].resolve().parents,'Unsafe curation receipt file path')
        require(sha(actual[name])==digest,'Curation payload receipt hash differs: '+name)
    expected_original={p.relative_to(args.original_markers).as_posix():p for p in args.original_markers.rglob('*')
                       if p.is_file() and p.relative_to(args.original_markers).parts[0] not in NOT_COPIED}
    copied={name:p for name,p in expected_original.items() if name not in MODIFIED}
    for name,path in copied.items():require(name in actual and sha(path)==sha(actual[name]),'Original raw/filter/runtime evidence was changed or omitted: '+name)
    permitted=set(expected_original)|{'marker_sequences/'+n+'.faa' for n in (args.curated_markers/'primary_marker_order.txt').read_text().split()}|{'accepted_by_genome/'+a+'.faa' for a in args.panel.read_text().split()}
    require(set(actual)==permitted,'Curated view contains missing or unexpected files')
    expected=old_inventory.copy();expected.update(primary_markers=100,accepted_marker_sequences=19359,post_occupancy_denominator=100,
        original_primary_markers=101,original_accepted_marker_sequences=19551,
        original_inventory_summary_sha256=sha(args.original_markers/'inventory_summary.json'),
        original_accepted_sequence_manifest_sha256=sha(args.original_markers/'accepted_sequence_manifest.tsv'),
        orthology_curation_identity=expected_identity,orthology_curation_status='CONSTRUCTED_INDEPENDENT_REVIEW_REQUIRED',
        scientific_validation='NOT_RUN_INDEPENDENT_CURATED_CHECK_REQUIRED')
    require(curated_inventory==expected and curated_inventory.get('identity')==old_identity
            and curated_inventory.get('blocker_count')==0 and curated_inventory.get('blockers')==[],
            'Curated inventory changes original execution/threshold/input provenance or has a scientific blocker')
    _,genomes=table(args.curated_markers/'genome_recovery.tsv')
    require(receipt.get('minimum_unique_initial_recovery')==counts['minimum_unique_initial_length_markers']
            and receipt.get('minimum_post_curation_recovery')==min(int(r['primary_accepted_markers']) for r in genomes),
            'Curation receipt measured recovery minima differ')
    require(receipt.get('host_profile_review_sha256')==sha(args.host_profile_review),'Curated accepted-source review bytes changed')
    return receipt

def check_function_review(args,old):
    review=load(args.host_profile_review);original=load(args.original_review)
    require(review.get('profile_sha256')==sha(args.profile) and review.get('profiles')==original.get('profiles')
            and len(review.get('profiles',[]))==119 and review.get('unresolved_rm_candidates')==0,
            'Curated function-scope family decision set changed or unresolved')
    require(review.get('source_candidate_resolutions')==original.get('source_candidate_resolutions'), 'Curated source candidate resolutions differ')
    executed=review.get('accepted_source_hit_review',{})
    require(executed.get('status')=='REVIEWED_ALL196_ACCEPTED_SOURCE_HITS'
            and executed.get('inventory_summary_sha256')==sha(args.curated_markers/'inventory_summary.json')
            and executed.get('accepted_sequence_manifest_sha256')==sha(args.curated_markers/'accepted_sequence_manifest.tsv')
            and executed.get('accepted_marker_sequences')==19359 and executed.get('profiles_accounted')==119
            and executed.get('assemblies_accounted')==196,'Curated accepted-source function review missing/stale')
    duplicate_review=review.get('original_duplicate_signal_review',{})
    require(duplicate_review.get('excluded_profile')=='IPT' and duplicate_review.get('retained_profile')=='IPPT'
            and duplicate_review.get('orthology_config_sha256')==sha(args.config), 'Curated review does not bind explicit duplicate-signal policy')
    function=old['host_function_review'].copy();function.update(review_sha256=sha(args.host_profile_review))
    return function

def production(args):
    started=time.monotonic()
    for name in ('root','original_markers','original_validation','curated_markers','config','panel','host_profile_review',
                 'original_review','original_config','original_checker','source_reader','curator_source','profile','profile_annotations','output'):
        setattr(args,name,getattr(args,name).resolve())
    require(args.root in args.output.parents and args.original_markers not in args.output.parents and args.curated_markers not in args.output.parents
            and args.output not in (args.original_markers,args.curated_markers)
            and args.output.relative_to(args.root).parts[0]=='.work','Separate project-local .work independent report directory required')
    panel=args.panel.read_text(encoding='ascii').split();require(len(panel)==len(set(panel))==196,'Approved full196 panel required')
    old,old_inventory,identity,config=check_prerequisites(args,panel)
    counts=check_projection(args.original_markers,args.curated_markers,panel)
    receipt=check_receipt_and_copies(args,old_inventory,identity,config,counts)
    function=check_function_review(args,old)
    report={**old,'status':'PASS_MARKER_SOURCE_AND_FIXED_FILTERS','scientific_stage_status':'PASS_HOST_MARKER_INVENTORY',
            'curation_status':'PASS_TOPOLOGY_BLIND_ORTHOLOGY_DEDUPLICATION','completed_at_utc':datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds':time.monotonic()-started,'original_validation_elapsed_seconds':old.get('elapsed_seconds'),
            **counts,'scientific_blockers':[],'host_function_review':function,
            'fixed_denominators':{'genomes':196,'candidate_markers':119,'post_occupancy_markers':100},
            'producer_identity':identity,'validator_source_sha256':sha(__file__),'original_validator_source_sha256':old['validator_source_sha256'],
            'original_validation_summary_sha256':sha(args.original_validation),'orthology_curation_config_sha256':sha(args.config),
            'orthology_curation_receipt_sha256':sha(args.curated_markers/'curation_receipt.json'),
            'orthology_curator_source_sha256':sha(args.curator_source),
            'inventory_summary_sha256':sha(args.curated_markers/'inventory_summary.json'),
            'accepted_sequence_manifest_sha256':sha(args.curated_markers/'accepted_sequence_manifest.tsv'),
            'primary_marker_order_sha256':sha(args.curated_markers/'primary_marker_order.txt'),
            'config_sha256':sha(args.original_config),'profile_sha256':sha(args.profile),'evidence_limit':LIMIT,
            'biological_search_reexecuted':False,'original_scientific_stage_status_preserved':old['scientific_stage_status']}
    save(args.output/'validation_summary.json',report)
    save(args.output/'projection_counts.json',counts)
    print(json.dumps({'status':report['scientific_stage_status'],'curation_status':report['curation_status'],**counts}),flush=True)
    return report

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-markers',type=Path);p.add_argument('--original-validation',type=Path)
    p.add_argument('--curated-markers',type=Path);p.add_argument('--config',type=Path);p.add_argument('--panel',type=Path)
    p.add_argument('--host-profile-review',type=Path);p.add_argument('--original-checker',type=Path)
    p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--original-review',type=Path)
    p.add_argument('--original-config',type=Path);p.add_argument('--source-reader',type=Path)
    p.add_argument('--curator-source',type=Path);p.add_argument('--profile',type=Path);p.add_argument('--profile-annotations',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--self-test',action='store_true')
    return p

if __name__=='__main__':
    args=parser().parse_args()
    if args.self_test:raise SystemExit('Run .work/review2/test_stage03_orthology_projection.py isolated fixtures')
    defaults={'original_markers':'.work/stage03_markers_v1','original_validation':'.work/stage03_marker_validation/validation_summary.json',
              'curated_markers':'.work/stage03_orthology_v2','config':'config/host_orthology_stage03_v2.json','panel':'config/approved_accessions.txt',
              'host_profile_review':'reports/stage03/host_profile_scope_review_orthology_v2.json',
              'original_review':'reports/stage03/host_profile_scope_review.json','original_config':'config/host_primary_stage03_v1.json',
              'original_checker':'scripts/validate_stage03_markers.py','source_reader':'scripts/validate_locus_inputs.py',
              'curator_source':'scripts/stage03_curate_orthology.py','profile':'.tools/Firmicutes.hmm',
              'profile_annotations':'.work/host_profile_annotations','output':'.work/stage03_curated_validation'}
    for key,relative in defaults.items():
        if getattr(args,key) is None:setattr(args,key,args.root/relative)
    try:production(args)
    except Exception as error:
        safe=args.output.resolve();root=args.root.resolve()
        if (root in safe.parents and safe.relative_to(root).parts[0]=='.work'
                and all(p.resolve()!=safe and p.resolve() not in safe.parents for p in (args.original_markers,args.curated_markers))):
            save(safe/'execution_failure.json',{'utc':datetime.now(timezone.utc).isoformat(),'status':'FAIL_ORTHOLOGY_PROJECTION',
                 'error':str(error),'outputs_preserved':True,'no_dependent_topology_permitted':True})
        raise
