#!/usr/bin/env python3
"""Synthetic full-sized cardinality fixtures; no biological tool invocation."""
import copy,csv,json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import stage04_phylogeny as p
import stage04_validate as v


def run():
    results=[]
    def rejects(name,operation):
        try:operation()
        except (ValueError,KeyError):results.append(name);return
        raise AssertionError('Malformed fixture accepted: '+name)
    with tempfile.TemporaryDirectory(prefix='orthology-gate-synthetic-',dir=Path(__file__).parent) as temporary:
        root=Path(temporary);old=root/'original';view=root/'curated';old.mkdir();view.mkdir()
        names=sorted(['IPPT','IPT']+['SYN_M'+str(i).zfill(3) for i in range(99)])
        ids=['SYN_ASSEMBLY_'+str(i).zfill(3)+'.1' for i in range(196)]
        rows=[];omissions=241
        for name in names:
            missing=4 if name=='IPT' else 0
            if name.startswith('SYN_M'):
                missing=min(19,omissions);omissions-=missing
            for accession in ids[missing:]:
                rows.append({'assembly_accession':accession,'profile':name,
                             'locus_key':accession+'|SYN_REP|'+('SYN_MIAA' if name in ('IPPT','IPT') else name)})
        assert len(rows)==19551 and omissions==0
        def table(path,records):
            with path.open('w',encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(records[0]),delimiter='\t',lineterminator='\n')
                writer.writeheader();writer.writerows(records)
        table(old/'accepted_sequence_manifest.tsv',rows)
        table(view/'accepted_sequence_manifest.tsv',[r for r in rows if r['profile']!='IPT'])
        (old/'primary_marker_order.txt').write_text('\n'.join(names)+'\n')
        (view/'primary_marker_order.txt').write_text('\n'.join(n for n in names if n!='IPT')+'\n')
        producer={'SYNTHETIC_ONLY':True}
        p.save(old/'inventory_summary.json',{'identity':producer})
        inventory={'identity':producer,'primary_markers':100,'accepted_marker_sequences':19359}
        p.save(view/'inventory_summary.json',inventory)
        config={'profile_sha256':'0'*64,'genome_recovery_fixed_denominator':119,'genome_minimum_accepted_markers':96,
                'marker_occupancy_fixed_denominator':196,'marker_minimum_accepted_genomes':177,'post_occupancy_genome_recovery_minimum':.8}
        p.save(root/'original_config.json',config)
        original={'status':'PASS_MARKER_SOURCE_AND_FIXED_FILTERS','scientific_stage_status':'HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED',
                  'approved_assemblies':196,'independently_verified_searches':196,'profiles_searched':119,'marker_cells':23324,
                  'primary_markers':101,'accepted_marker_sequences':19551,'same_locus_multiple_profile_candidates':192,
                  'scientific_blockers':[],'producer_identity':producer,'config_sha256':p.sha(root/'original_config.json'),
                  'profile_sha256':config['profile_sha256'],
                  'inventory_summary_sha256':p.sha(old/'inventory_summary.json'),
                  'accepted_sequence_manifest_sha256':p.sha(old/'accepted_sequence_manifest.tsv'),
                  'primary_marker_order_sha256':p.sha(old/'primary_marker_order.txt')}
        p.save(root/'original_validation.json',original)
        policy={'revision':'stage03-orthology-v2','frozen_before_alignment_and_topology':True,'no_biological_search_rerun':True,
                'excluded_primary_profiles':['IPT'],'retained_corresponding_profile':'IPPT','original_duplicate_loci':192,
                'unchanged_thresholds':{'candidate_profiles':119,'initial_minimum':96,'assemblies':196,'occupancy_minimum':177,'post_recovery_fraction':.8},
                'original_config_sha256':p.sha(root/'original_config.json'),'original_validation_summary_sha256':p.sha(root/'original_validation.json'),
                'original_inventory_summary_sha256':p.sha(old/'inventory_summary.json'),
                'original_accepted_sequence_manifest_sha256':p.sha(old/'accepted_sequence_manifest.tsv')}
        p.save(root/'orthology_config.json',policy)
        receipt={'no_hmm_or_alignment_job_run':True,'output_sha256':{f.name:p.sha(f) for f in view.iterdir()}}
        p.save(view/'curation_receipt.json',receipt)
        validation={**original,'scientific_stage_status':'PASS_HOST_MARKER_INVENTORY','curation_status':'PASS_TOPOLOGY_BLIND_ORTHOLOGY_DEDUPLICATION',
                    'primary_markers':100,'accepted_marker_sequences':19359,'same_locus_multiple_profile_candidates':0,
                    'minimum_unique_initial_length_markers':96,'biological_search_reexecuted':False,
                    'original_scientific_stage_status_preserved':original['scientific_stage_status'],
                    'original_validation_summary_sha256':p.sha(root/'original_validation.json'),
                    'orthology_curation_config_sha256':p.sha(root/'orthology_config.json'),
                    'orthology_curation_receipt_sha256':p.sha(view/'curation_receipt.json'),
                    'inventory_summary_sha256':p.sha(view/'inventory_summary.json'),
                    'accepted_sequence_manifest_sha256':p.sha(view/'accepted_sequence_manifest.tsv'),
                    'primary_marker_order_sha256':p.sha(view/'primary_marker_order.txt'),
                    'host_function_review':{'state':'REVIEWED_CONSERVED_HOST_PROFILE_SCOPE_WITH_DOCUMENTED_LIMITS',
                                            'profiles_accounted':119,'unresolved_rm_candidates':0}}
        p.save(root/'curated_validation.json',validation)
        args=SimpleNamespace(root=root,markers=view,config=root/'original_config.json',orthology_config=root/'orthology_config.json',
                             original_markers=old,original_marker_validation=root/'original_validation.json',
                             marker_validation=root/'curated_validation.json',producer_source=Path(p.__file__))
        gate=p.orthology_gate(args,validation,inventory,config)
        assert gate['primary_marker_count']==100
        results.append('strict_119_196_to_100_19359_projection_accepted')
        identity={**gate,'runner_sha256':p.sha(p.__file__),'marker_validation_sha256':p.sha(args.marker_validation),
                  'config_sha256':p.sha(args.config),'inventory_summary_sha256':p.sha(view/'inventory_summary.json')}
        assert v.upstream_marker_gate(args,identity,view)['retained_profiles']==100
        results.append('independent_gate_reads_curated_and_blocked_original_separately')
        for key,value in [('primary_markers',99),('accepted_marker_sequences',19358),('minimum_unique_initial_length_markers',95),
                          ('biological_search_reexecuted',True),('orthology_curation_receipt_sha256','1'*64),
                          ('original_validation_summary_sha256','1'*64),('original_scientific_stage_status_preserved','PASS_HOST_MARKER_INVENTORY')]:
            bad=copy.deepcopy(validation);bad[key]=value
            rejects('producer_rejects_'+key,lambda bad=bad:p.orthology_gate(args,bad,inventory,config))
        previous=copy.deepcopy(original);previous['scientific_stage_status']='PASS_HOST_MARKER_INVENTORY'
        p.save(args.original_marker_validation,previous)
        rejects('blocked_original_cannot_be_rewritten_pass',lambda:p.orthology_gate(args,validation,inventory,config))
        rejects('independent_reader_rejects_rewritten_original',lambda:v.upstream_marker_gate(args,identity,view))
        p.save(args.original_marker_validation,original)
        changed=copy.deepcopy(policy);changed['unchanged_thresholds']['initial_minimum']=95
        p.save(args.orthology_config,changed)
        rejects('original96_119_gate_cannot_be_relaxed',lambda:p.orthology_gate(args,validation,inventory,config))
        p.save(args.orthology_config,policy)
        order=(view/'primary_marker_order.txt').read_text();(view/'primary_marker_order.txt').write_text(order.replace('IPPT\n',''))
        rejects('additional_whole_family_removal_rejected',lambda:p.orthology_gate(args,validation,inventory,config))
        (view/'primary_marker_order.txt').write_text(order)
        before=(view/'accepted_sequence_manifest.tsv').read_bytes();(view/'accepted_sequence_manifest.tsv').write_bytes(before.replace(b'SYN_M000',b'SYN_CHANGED',1))
        rejects('source_locus_row_change_rejected',lambda:p.orthology_gate(args,validation,inventory,config))
        (view/'accepted_sequence_manifest.tsv').write_bytes(before)
        identity_bad={**identity,'orthology_curation_config_sha256':'f'*64}
        rejects('independent_frozen_curation_hash_mismatch_rejected',lambda:v.upstream_marker_gate(args,identity_bad,view))
        args.orthology_config=None;args.original_marker_validation=None;args.original_markers=None
        rejects('curated_view_cannot_use_uncurated_gate_route',lambda:p.orthology_gate(args,validation,inventory,config))
        rejects('independent_curated_view_requires_explicit_policy',lambda:v.upstream_marker_gate(args,identity,view))
    p.save(Path(__file__).parent/'stage04_orthology_gate_synthetic_results.json',
           {'status':'PASS_SYNTHETIC_STRICT_ORTHOLOGY_STAGE04_GATES','count':len(results),'fixtures':results,'biological_jobs_run':0})
    print(json.dumps({'status':'PASS_SYNTHETIC_STRICT_ORTHOLOGY_STAGE04_GATES','count':len(results),'fixtures':results},indent=2))


if __name__=='__main__':run()
