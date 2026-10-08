"""Summarize all accepted primary source annotations for explicit scope review.

This writes observations only, never a scientific PASS or functional claim.
"""
from collections import Counter,defaultdict
from pathlib import Path
import argparse,csv,json,re
import production_resume as w

def main(record=False):
    root=w.R;marker=root/'.work/stage03_markers_v1'
    rows=list(csv.DictReader((marker/'accepted_sequence_manifest.tsv').open(encoding='utf-8'),delimiter='\t'))
    inventory=json.loads((marker/'inventory_summary.json').read_text())
    if len(rows)!=inventory['accepted_marker_sequences']:raise ValueError('Accepted sequence count differs')
    profiles=json.loads((root/'reports/stage03/host_profile_scope_review.json').read_text())['profiles']
    by_profile=defaultdict(list);by_locus=defaultdict(list);candidates=[]
    pattern=re.compile(r'restriction|DNA.{0,30}methyl|\bhsd[MSR]\b|\b(?:mod|res)\b.{0,25}(?:subunit|restriction)',re.I)
    for row in rows:
        by_profile[row['profile']].append(row);by_locus[row['locus_key']].append(row['profile'])
        for header in json.loads(row['source_primary_headers']):
            if pattern.search(header):candidates.append({'locus_key':row['locus_key'],'profile':row['profile'],'header':header})
    observations=[]
    for profile in profiles:
        headers=Counter(header.split(' ',1)[1].rsplit(' [',1)[0] for row in by_profile[profile['profile']]
                        for header in json.loads(row['source_primary_headers']))
        observations.append({'profile':profile['profile'],'pinned_description':profile['profile_description'],
                             'accepted_loci':len(by_profile[profile['profile']]),'primary_source_product_counts':dict(headers)})
    output={'status':'OBSERVATIONS_FOR_REVIEW_ONLY','utc':w.now(),'approved_assemblies':196,
            'accepted_marker_sequences':len(rows),'profiles_accounted':len(observations),
            'inventory_summary_sha256':w.digest(marker/'inventory_summary.json'),
            'accepted_sequence_manifest_sha256':w.digest(marker/'accepted_sequence_manifest.tsv'),
            'profiles':observations,'source_header_rm_candidates':candidates,
            'same_locus_multiple_profiles':[{'locus_key':k,'profiles':v} for k,v in by_locus.items() if len(v)>1],
            'evidence_limit':'Source annotation and profile predictions; primary headers do not demonstrate activity. Independent GBFF/HMM source checker remains required.'}
    w.js(root/'.work/accepted_host_scope_observations.json',output)
    if record:
        if candidates:raise ValueError('Explicit R-M source candidates need individual evidence review')
        review_path=root/'reports/stage03/host_profile_scope_review.json'
        review=json.loads(review_path.read_text())
        for p in review['profiles']:
            observation=next(o for o in observations if o['profile']==p['profile'])
            p['accepted_source_observation']=observation
            p['conclusion']+=' Executed primary source annotation counts are preserved below; predicted host-family assignment does not establish activity.'
            if p['profile']=='UPF0052':
                p['conclusion']='Pinned UPF0052 family and all196 accepted YvcK/MgfK-related source annotations support a conserved host-family assignment. The current Pfam CofD description includes related sequences and is not proof these loci are CofD enzymes. Function in approved strains remains predicted.'
            if p['profile']=='DUF448':
                p['conclusion']='All196 accepted source loci are annotated RNase P modulator RnpM. Current Pfam YlxR context and pinned DUF448 identity are retained separately. Source annotations support host RNA scope; approved-strain activity is not demonstrated.'
        review.update(status='ACCEPTED_SOURCE_FAMILY_SCOPE_REVIEWED_ORIGINAL_DUPLICATE_SIGNAL_BLOCKED',utc=w.now(),
                      unresolved_rm_candidates=0,source_candidate_resolutions=[],
                      accepted_source_hit_review={'status':'REVIEWED_ALL196_ACCEPTED_SOURCE_HITS',
                        'inventory_summary_sha256':output['inventory_summary_sha256'],
                        'accepted_sequence_manifest_sha256':output['accepted_sequence_manifest_sha256'],
                        'accepted_marker_sequences':len(rows),'profiles_accounted':119,'assemblies_accounted':196,
                        'observations_sha256':w.digest(root/'.work/accepted_host_scope_observations.json'),
                        'review_basis':'All119 pinned descriptors and accepted source product-count classes explicitly inspected before topology. Unknown functions remain unknown. Independent GBFF/gene/HMM reader remains required and can reject additional conflicting annotations.'},
                      original_duplicate_signal_review={'status':'BLOCKED_PENDING_INDEPENDENT_CURATED_PROJECTION',
                        'duplicated_loci':len(output['same_locus_multiple_profiles']),
                        'profiles':['IPPT','IPT'],'basis':'Same complete source MiaA protein would be concatenated twice; no annotation-only waiver.'})
        w.js(review_path,review)
        print('EXECUTED_SOURCE_FAMILY_SCOPE_REVIEW_RECORDED; duplicated full-protein signal remains blocked')
    else:print(json.dumps(output,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--record-inspected-source-scope',action='store_true')
    main(parser.parse_args().record_inspected_source_scope)
