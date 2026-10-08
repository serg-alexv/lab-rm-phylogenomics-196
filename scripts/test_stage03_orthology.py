"""Synthetic independent projection checks; no production sequences or jobs."""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,datetime,importlib.util,json,shutil,tempfile

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent if HERE.name=='scripts' else HERE.parents[1]
SCRIPT=PROJECT/'scripts/validate_stage03_orthology.py' if HERE.name=='scripts' else HERE/'validate_stage03_orthology_projection.py'
spec=importlib.util.spec_from_file_location('independent_projection_tested',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OUT=PROJECT/'.work/review2/orthology_review';OUT.mkdir(parents=True,exist_ok=True)
def write(p,text):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
def fixture(root):
    old=root/'.work/original';new=root/'.work/curated';old.mkdir(parents=True);new.mkdir(parents=True)
    panel=['GCF_'+str(i).zfill(9)+'.1' for i in range(196)]
    profiles=sorted(['IPPT','IPT']+['M'+str(i).zfill(3) for i in range(99)]+['N'+str(i).zfill(3) for i in range(18)])
    order=sorted(['IPPT','IPT']+['M'+str(i).zfill(3) for i in range(99)])
    missing={(panel[k%196],'M'+str(k%99).zfill(3)) for k in range(241)}
    matrix=[];accepted=[];initial=Counter();post=Counter();occupancy=Counter()
    source={}
    for ai,a in enumerate(panel):
        for name in profiles:
            eligible=(a,name) not in missing and not (name=='IPT' and ai<4) and not (name.startswith('N') and ai>=176)
            key=a+'|SYNTHETIC_REP.1|'+('MIAA' if name in ('IPPT','IPT') else name)
            state='PRIMARY_ACCEPTED' if eligible and name in order else 'MARKER_LOW_OCCUPANCY' if eligible else 'NO_QUALIFYING_HIT_AFTER_SUCCESSFUL_SEARCH'
            matrix.append({'assembly_accession':a,'profile':name,'qualifying_distinct_loci':'1' if eligible else '0',
                           'state':state,'length_accepted':str(eligible),'locus_key':key if eligible else '',
                           'all_locus_keys':json.dumps([key] if eligible else [])})
            if eligible:initial[a]+=1;occupancy[name]+=1
            if eligible and name in order:
                sequence='MIAA' if name in ('IPPT','IPT') else 'MAAA';post[a]+=1;source[(a,name)]=sequence
                accepted.append({'assembly_accession':a,'profile':name,'profile_accession':'SYNTHETIC_'+name,
                                 'locus_key':key,'protein_accession':'WP_SYNTHETIC_MIAA' if name in ('IPPT','IPT') else 'WP_SYNTHETIC_'+name,
                                 'source_sequence_sha256':m.seqsha(sequence),'protein_aa_length':str(len(sequence))})
    accepted.sort(key=lambda r:(r['profile'],panel.index(r['assembly_accession'])))
    assert len(accepted)==19551
    m.put_table(old/'accepted_sequence_manifest.tsv',list(accepted[0]),accepted)
    m.put_table(old/'copy_occupancy_matrix.tsv',list(matrix[0]),matrix)
    qc=[{'profile':name,'median_single_copy_source_aa_length':'4.0','inclusive_minimum_aa_length':'3','inclusive_maximum_aa_length':'5',
         'accepted_genomes_fixed196':str(occupancy[name]),'occupancy_fixed196':str(occupancy[name]/196),'primary_retained':str(name in order)} for name in profiles]
    m.put_table(old/'marker_qc.tsv',list(qc[0]),qc)
    genomes=[{'assembly_accession':a,'length_accepted_markers':str(initial[a]),'recovery_fixed119':str(initial[a]/119),
              'primary_accepted_markers':str(post[a]),'primary_marker_denominator':'101','post_occupancy_recovery':str(post[a]/101),
              'post_minimum_markers':'81'} for a in panel]
    m.put_table(old/'genome_recovery.tsv',list(genomes[0]),genomes)
    write(old/'primary_marker_order.txt','\n'.join(order)+'\n')
    for name in order:
        rows=[r for r in accepted if r['profile']==name]
        write(old/'marker_sequences'/f'{name}.faa',''.join('>'+r['assembly_accession']+'\n'+source[(r['assembly_accession'],name)]+'\n' for r in rows))
    for a in panel:
        rows=[r for r in accepted if r['assembly_accession']==a]
        write(old/'accepted_by_genome'/f'{a}.faa',''.join('>'+r['locus_key']+' marker='+r['profile']+'\n'+source[(a,r['profile'])]+'\n' for r in rows))
    args=argparse.Namespace(root=root,original_markers=old,curated_markers=new,panel=root/'config/panel.txt',
         original_config=root/'config/original.json',config=root/'config/orthology.json',profile=root/'.tools/profiles.hmm',
         original_validation=root/'.work/original_validation/validation_summary.json',original_review=root/'reports/original_scope.json',
         host_profile_review=root/'reports/curated_scope.json',original_checker=root/'scripts/old_checker.py',source_reader=root/'scripts/source_reader.py',
         curator_source=root/'scripts/producer.py',profile_annotations=root/'.work/annotations',output=root/'.work/projection_validation')
    write(args.panel,'\n'.join(panel)+'\n');write(args.profile,'SYNTHETIC PROFILE FILE; NOT HMM\n')
    for p in [args.original_checker,args.source_reader,args.curator_source]:write(p,'# SYNTHETIC SOURCE HASH FIXTURE\n')
    m.save(args.original_config,{'genome_recovery_fixed_denominator':119,'genome_minimum_accepted_markers':96,
                               'marker_occupancy_fixed_denominator':196,'marker_minimum_accepted_genomes':177,'post_occupancy_genome_recovery_minimum':0.8})
    identity={'approved_accessions_sha256':m.sha(args.panel),'config_sha256':m.sha(args.original_config),'profile_sha256':m.sha(args.profile)}
    m.save(old/'input_identity.json',identity)
    inventory={'execution':'COMPLETED_ALL196_SEARCHES','identity':identity,'primary_markers':101,'accepted_marker_sequences':19551,
               'post_occupancy_denominator':101,'blocker_count':0,'blockers':[],'fixture_only':True}
    m.save(old/'inventory_summary.json',inventory)
    review={'profile_sha256':m.sha(args.profile),'profiles':[{'profile':name,'fixture_only':True} for name in profiles],
            'unresolved_rm_candidates':0,'source_candidate_resolutions':[],
            'accepted_source_hit_review':{'status':'REVIEWED_ALL196_ACCEPTED_SOURCE_HITS','profiles_accounted':119,'assemblies_accounted':196},
            'original_duplicate_signal_review':{'fixture_only':True}}
    m.save(args.original_review,review)
    report={'status':'PASS_MARKER_SOURCE_AND_FIXED_FILTERS','scientific_stage_status':'HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED',
            'approved_assemblies':196,'independently_verified_searches':196,'profiles_searched':119,'marker_cells':23324,
            'primary_markers':101,'accepted_marker_sequences':19551,'same_locus_multiple_profile_candidates':192,'scientific_blockers':[],
            'validator_source_sha256':m.sha(args.original_checker),'source_reader_sha256':m.sha(args.source_reader),
            'producer_identity':identity,'host_function_review':{'state':'REVIEWED_CONSERVED_HOST_PROFILE_SCOPE_WITH_DOCUMENTED_LIMITS',
            'profiles_accounted':119,'source_rm_candidates':0,'unresolved_rm_candidates':0,'review_sha256':m.sha(args.original_review)}}
    for key,path in [('inventory_summary_sha256',old/'inventory_summary.json'),('accepted_sequence_manifest_sha256',old/'accepted_sequence_manifest.tsv'),
                     ('primary_marker_order_sha256',old/'primary_marker_order.txt'),('config_sha256',args.original_config),('profile_sha256',args.profile)]:report[key]=m.sha(path)
    m.save(args.original_validation,report);m.save(args.original_validation.parent/'potential_rm_source_candidates.json',[])
    for name in ['profiles.tsv','hmm_hits.tsv','hmm_domains.tsv','runtime/runtime_receipt.json','length_method/native_bounds_receipts.json',
                 'input_guard_exclusions.tsv','rm_marker_source_review_candidates.tsv','scientific_blockers.tsv']:
        write(old/name,'SYNTHETIC ORIGINAL COPIED EVIDENCE; NOT BIOLOGICAL\n')
    config={'revision':'stage03-orthology-v2','frozen_before_alignment_and_topology':True,'no_biological_search_rerun':True,
            'excluded_primary_profiles':['IPT'],'retained_corresponding_profile':'IPPT','original_duplicate_loci':192,
            'selection_basis':'Synthetic explicit whole-profile same-source policy fixture','additional_strict_gate':'Unique original length-accepted >=96',
            'unchanged_thresholds':{'candidate_profiles':119,'initial_minimum':96,'assemblies':196,'occupancy_minimum':177,'post_recovery_fraction':0.8},
            'primary_source_evidence':[{'url':'https://pubmed.ncbi.nlm.nih.gov/19158097/','PMID':'19158097','scope':'SYNTHETIC API EVIDENCE FIXTURE'}]}
    for pfam in ['PF01715','PF01745']:
        m.save(args.profile_annotations/(pfam+'.json'),{'fixture_only':True})
        config['primary_source_evidence'].append({'url':'https://www.ebi.ac.uk/interpro/api/entry/pfam/'+pfam+'/',
                                                 'raw_response_sha256':m.sha(args.profile_annotations/(pfam+'.json'))})
    for key,path in [('original_config_sha256',args.original_config),('panel_sha256',args.panel),('profile_sha256',args.profile),
                     ('original_inventory_summary_sha256',old/'inventory_summary.json'),('original_validation_summary_sha256',args.original_validation),
                     ('original_accepted_sequence_manifest_sha256',old/'accepted_sequence_manifest.tsv')]:config[key]=m.sha(path)
    m.save(args.config,config)
    for path in old.rglob('*'):
        if path.is_file():dest=new/path.relative_to(old);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    (new/'marker_sequences/IPT.faa').unlink()
    kept=[r for r in accepted if r['profile']!='IPT'];m.put_table(new/'accepted_sequence_manifest.tsv',list(kept[0]),kept)
    write(new/'primary_marker_order.txt','\n'.join(n for n in order if n!='IPT')+'\n')
    for a in panel:
        records=[(h,s) for h,s in m.fasta(old/'accepted_by_genome'/f'{a}.faa') if not h.endswith(' marker=IPT')]
        write(new/'accepted_by_genome'/f'{a}.faa',''.join('>'+h+'\n'+s+'\n' for h,s in records))
    for row in matrix:
        if row['profile']=='IPT' and row['state']=='PRIMARY_ACCEPTED':row['state']='ORTHOLOGY_REDUNDANT_PROFILE_EXCLUDED'
    m.put_table(new/'copy_occupancy_matrix.tsv',list(matrix[0]),matrix)
    for row in qc:
        row['orthology_review_state']='REDUNDANT_COMPLETE_SOURCE_SIGNAL_EXCLUDED' if row['profile']=='IPT' else 'KEEP_ORIGINAL_FIXED_FILTER_RESULT'
        if row['profile']=='IPT':row['primary_retained']='False'
    m.put_table(new/'marker_qc.tsv',list(qc[0]),qc)
    kept_counts=Counter(r['assembly_accession'] for r in kept)
    for row in genomes:
        a=row['assembly_accession'];count=kept_counts[a]
        eligible=next(r for r in matrix if r['assembly_accession']==a and r['profile']=='IPT')['length_accepted']=='True'
        row.update(primary_accepted_markers=str(count),primary_marker_denominator='100',post_minimum_markers='80',post_occupancy_recovery=str(count/100),
                   orthology_unique_length_accepted_markers=str(initial[a]-int(eligible)))
    m.put_table(new/'genome_recovery.tsv',list(genomes[0]),genomes)
    ci={'config_sha256':m.sha(args.config),'builder_source_sha256':m.sha(args.curator_source),
        'original_validation_summary_sha256':m.sha(args.original_validation),'original_review_sha256':m.sha(args.original_review)}
    inventory.update(primary_markers=100,accepted_marker_sequences=19359,post_occupancy_denominator=100,original_primary_markers=101,
       original_accepted_marker_sequences=19551,original_inventory_summary_sha256=config['original_inventory_summary_sha256'],
       original_accepted_sequence_manifest_sha256=config['original_accepted_sequence_manifest_sha256'],orthology_curation_identity=ci,
       orthology_curation_status='CONSTRUCTED_INDEPENDENT_REVIEW_REQUIRED',scientific_validation='NOT_RUN_INDEPENDENT_CURATED_CHECK_REQUIRED')
    m.save(new/'inventory_summary.json',inventory)
    review['accepted_source_hit_review'].update(inventory_summary_sha256=m.sha(new/'inventory_summary.json'),
          accepted_sequence_manifest_sha256=m.sha(new/'accepted_sequence_manifest.tsv'),accepted_marker_sequences=19359)
    review['original_duplicate_signal_review'].update(excluded_profile='IPT',retained_profile='IPPT',orthology_config_sha256=m.sha(args.config))
    m.save(args.host_profile_review,review)
    m.save(new/'curation_receipt.json',{'status':'CURATED_VIEW_CONSTRUCTED_NOT_YET_INDEPENDENT_PASS','identity':ci,
       'no_hmm_or_alignment_job_run':True,'original_profiles':101,'curated_profiles':100,'excluded_profile':'IPT','duplicated_loci_resolved':192,'genomes':196,
       'minimum_unique_initial_recovery':min(int(r['orthology_unique_length_accepted_markers']) for r in genomes),
       'minimum_post_curation_recovery':min(kept_counts.values()),'host_profile_review_sha256':m.sha(args.host_profile_review),
       'output_sha256':{p.relative_to(new).as_posix():m.sha(p) for p in new.rglob('*') if p.is_file()}})
    return args

cases=[]
def test(name,fn):
    with tempfile.TemporaryDirectory(prefix='synthetic_',dir=OUT) as td:fn(fixture(Path(td)))
    cases.append({'name':name,'status':'PASS'})
def reject(args,edit,fn=None):
    edit(args)
    try:(fn or (lambda:m.check_projection(args.original_markers,args.curated_markers,args.panel.read_text().split())))()
    except (ValueError,KeyError,FileNotFoundError):return
    raise AssertionError('Expected independent scientific rejection')
def mutate_table(args,name,operation):
    fields,rows=m.table(args.curated_markers/name);operation(rows);m.put_table(args.curated_markers/name,fields,rows)
test('complete_synthetic196_projection_passes_all_prerequisite_receipt_and_scientific_gates',lambda a:m.production(a))
test('changed_manifest_source_hash_rejected',lambda a:reject(a,lambda a:mutate_table(a,'accepted_sequence_manifest.tsv',lambda r:r[0].update(source_sequence_sha256='0'*64))))
test('arbitrary_other_marker_exclusion_rejected',lambda a:reject(a,lambda a:mutate_table(a,'accepted_sequence_manifest.tsv',lambda r:r.pop())))
test('matrix_copynumber_change_rejected',lambda a:reject(a,lambda a:mutate_table(a,'copy_occupancy_matrix.tsv',lambda r:r[0].update(qualifying_distinct_loci='2'))))
test('matrix_length_evidence_change_rejected',lambda a:reject(a,lambda a:mutate_table(a,'copy_occupancy_matrix.tsv',lambda r:r[0].update(length_accepted='False'))))
test('matrix_omitted_genome_cell_rejected',lambda a:reject(a,lambda a:mutate_table(a,'copy_occupancy_matrix.tsv',lambda r:r.pop())))
test('marker_occupancy_fact_change_rejected',lambda a:reject(a,lambda a:mutate_table(a,'marker_qc.tsv',lambda r:r[0].update(accepted_genomes_fixed196='176'))))
test('original_initial_recovery_rewrite_rejected',lambda a:reject(a,lambda a:mutate_table(a,'genome_recovery.tsv',lambda r:r[0].update(length_accepted_markers='95'))))
test('unique_initial_recovery_gate_95_rejected',lambda a:reject(a,lambda a:mutate_table(a,'genome_recovery.tsv',lambda r:r[0].update(orthology_unique_length_accepted_markers='95'))))
test('post_recovery_denominator101_rejected',lambda a:reject(a,lambda a:mutate_table(a,'genome_recovery.tsv',lambda r:r[0].update(primary_marker_denominator='101'))))
test('post_recovery_minimum79_rejected',lambda a:reject(a,lambda a:mutate_table(a,'genome_recovery.tsv',lambda r:r[0].update(post_minimum_markers='79'))))
test('altered_retained_marker_sequence_rejected',lambda a:reject(a,lambda a:write(a.curated_markers/'marker_sequences/IPPT.faa',(a.curated_markers/'marker_sequences/IPPT.faa').read_text().replace('MIAA','MIVA',1))))
test('excluded_IPT_FASTA_retained_rejected',lambda a:reject(a,lambda a:shutil.copyfile(a.original_markers/'marker_sequences/IPT.faa',a.curated_markers/'marker_sequences/IPT.faa')))
test('reordered_marker_order_rejected',lambda a:reject(a,lambda a:write(a.curated_markers/'primary_marker_order.txt','\n'.join(reversed((a.curated_markers/'primary_marker_order.txt').read_text().split()))+'\n')))
test('omitted_accepted_genome_FASTA_rejected',lambda a:reject(a,lambda a:next((a.curated_markers/'accepted_by_genome').glob('*.faa')).unlink()))
test('changed_pergenome_exact_sequence_rejected',lambda a:reject(a,lambda a:write(next((a.curated_markers/'accepted_by_genome').glob('*.faa')),'>synthetic_wrong marker=IPPT\nMIAA\n')))
def prerequisite_reject(a,path,operation):
    v=m.load(path);operation(v);m.save(path,v)
    try:m.check_prerequisites(a,a.panel.read_text().split())
    except ValueError:return
    raise AssertionError('Expected prerequisite failure')
test('threshold_relaxation95_rejected',lambda a:prerequisite_reject(a,a.config,lambda v:v['unchanged_thresholds'].update(initial_minimum=95)))
test('original_scientific_numeric_blocker_rejected',lambda a:prerequisite_reject(a,a.original_validation,lambda v:v.update(scientific_blockers=[{'gate':'RECOVERY'}])))
test('original_executed_checker_hash_change_rejected',lambda a:reject(a,lambda a:write(a.original_checker,'# changed synthetic checker'),lambda:m.check_prerequisites(a,a.panel.read_text().split())))
test('curation_receipt_uncovered_file_rejected',lambda a:reject(a,lambda a:write(a.curated_markers/'extra_unowned.txt','SYNTHETIC EXTRA'),lambda:m.production(a)))
test('copied_runtime_altered_rejected',lambda a:reject(a,lambda a:write(a.curated_markers/'runtime/runtime_receipt.json','{}'),lambda:m.production(a)))
test('curated_function_review_stale_hash_rejected',lambda a:reject(a,lambda a:m.save(a.host_profile_review,{'profiles':[]}),lambda:m.production(a)))
report={'status':'PASS_ISOLATED_ORTHOLOGY_PROJECTION_CHECKS','tests':len(cases),'cases':cases,
        'validator_source_sha256':m.sha(SCRIPT),'test_source_sha256':m.sha(__file__),
        'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'biological_execution':'NOT_RUN',
        'command':'python .work/review2/test_stage03_orthology_projection.py',
        'evidence_limit':'Synthetic exact196/119 fixtures exercise parsers and scientific projection gates; actual full196 production validation remains separate.'}
m.save(OUT/'orthology_projection_synthetic_tests.json',report)
write(OUT/'ORTHOLOGY_PROJECTION_REVIEW.md',f'# Independent orthology projection checker\n\n{len(cases)} synthetic checks passed against SHA256 `{m.sha(SCRIPT)}`. '
      'The checker derives the exact IPT-only projection from source-bound original rows, validates unchanged source sequences and native evidence, '
      'all196 genome gates and119-profile facts, and verifies all curated output receipt hashes. No biological job or Git/network publication ran.\n\n'
      'Command: `python .work/review2/test_stage03_orthology_projection.py`. Actual source sequences require the original independent full196 marker audit and a separate production run of this checker.\n')
print(json.dumps({'status':report['status'],'tests':len(cases),'validator_source_sha256':report['validator_source_sha256']}))
