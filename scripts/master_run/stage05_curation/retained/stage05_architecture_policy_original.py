#!/usr/bin/env python3
"""Strict Stage05 review-policy draft; pure reducers, no scientific runner.

This module validates explicit review records against separately joined source
and native-domain evidence. It never assigns functional roles from a string,
WP accession, detector minimum, directory, annotation or empty output. A future
production adapter must independently load/hash/join the inventory TSVs before
calling these functions. No CLI asserts a panel result.
"""
from collections import Counter
import hashlib, json, re

TYPES=('I','II','III','IV')
STATES={'NOT_RUN','FAILED','UNCERTAIN','PARTIAL_CANDIDATE','CURATED_PARTIAL','COMPLETE_PREDICTED','NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH'}
ROLE_REQUIREMENTS={'I':{'REASE','MTASE','SPECIFICITY'},'II':{'REASE','MTASE'},'III':{'MOD','RES'},'IV':{'MOD_DEPENDENT_RECOGNITION','CLEAVAGE'}}
SHA=re.compile(r'^[0-9a-f]{64}$')
def require(v,m):
    if not v:raise ValueError(m)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ref_valid(ref):return isinstance(ref,dict) and bool(ref.get('path')) and bool(SHA.fullmatch(ref.get('sha256',''))) and bool(ref.get('record_locator'))
def refs_valid(refs):return isinstance(refs,list) and bool(refs) and all(ref_valid(r) for r in refs)

def canonical_candidate(candidate):
    require(candidate['rm_type'] in TYPES or candidate['rm_type'] is None,'Unknown R-M type')
    loci=sorted(set(candidate['locus_keys']));require(loci and len(loci)==len(candidate['locus_keys']),'Empty/duplicate candidate locus')
    parts=[key.split('|') for key in loci]
    require(all(len(p)==3 and all(p) for p in parts),'Malformed exact locus key')
    require(all(p[0]==candidate['assembly_accession'] for p in parts),'Wrong assembly locus')
    require(len({p[1] for p in parts})==1,'Cross-replicon automatic architecture forbidden')
    identity={'assembly_accession':candidate['assembly_accession'],'replicon':parts[0][1],'rm_type':candidate['rm_type'],'locus_keys':loci}
    return identity, 'RMC_'+digest(identity)[:24]

def deduplicate_exact(candidates):
    """Only identical locus sets/type merge; overlapping sets remain separate."""
    groups={}
    for c in candidates:
        identity,cid=canonical_candidate(c)
        if cid not in groups:groups[cid]={**identity,'candidate_id':cid,'native_candidate_refs':[],'detectors':set(),'subtypes':set(),'architecture_review_required':True}
        group=groups[cid];group['detectors'].add(c['detector']);group['subtypes'].add(c.get('subtype'))
        require(refs_valid(c.get('native_candidate_refs')),'Native call references required')
        group['native_candidate_refs'].extend(c['native_candidate_refs'])
    result=[]
    for g in groups.values():
        g['detectors']=sorted(g['detectors']);g['subtypes']=sorted(g['subtypes'],key=lambda x:str(x));g['subtype_conflict']=len(g['subtypes'])>1
        result.append(g)
    # Sharing a source component among different systems can be real but must
    # not inflate counts via transitive locus-set unions.
    for g in result:
        g['overlapping_candidate_ids']=sorted(h['candidate_id'] for h in result if h['candidate_id']!=g['candidate_id'] and h['assembly_accession']==g['assembly_accession'] and set(g['locus_keys'])&set(h['locus_keys']))
    return sorted(result,key=lambda g:g['candidate_id'])

def validate_role_evidence(candidate,review,sources,hits):
    identity,cid=canonical_candidate(candidate);require(review['candidate_id']==cid,'Review candidate identity differs')
    require(review['rm_type']==candidate['rm_type'],'Review type differs')
    require(review['execution']=='EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW','Review not executed')
    require(refs_valid(review.get('source_context_refs')) and refs_valid(review.get('architecture_basis_refs')),'Source/architecture evidence required')
    require(review['functional_evidence_grade']=='PREDICTED_ARCHITECTURE_ONLY','Prediction cannot masquerade as activity')
    require(review.get('unresolved_competing_annotations',-1)==0,'Unresolved competing annotation')
    roles=set();role_to_locus={};issues=set();hit_roles={}
    for role in review['roles']:
        key=role['locus_key'];require(key in identity['locus_keys'] and key in sources,'Role source missing')
        source=sources[key];require(source['locus_key']==key,'Source identity differs')
        require(all(isinstance(source.get(flag),bool) for flag in ['protein_target_present','source_pseudo_any','partial_or_fuzzy','linear_edge','origin_spanning','requires_coordinate_review']),'Source flags must be normalized strict booleans')
        require(role['source_aa_sha256']==source['primary_faa_sequence_sha256'] and SHA.fullmatch(role['source_aa_sha256']),'Role AA identity differs')
        require(refs_valid(role.get('functional_domain_basis_refs')),'Functional-domain role basis required')
        require(role['role'] in {'REASE','MTASE','SPECIFICITY','MOD','RES','MOD_DEPENDENT_RECOGNITION','CLEAVAGE','MCRB','MCRC','GMR_S','GMR_D'},'Undefined architecture role')
        require(role.get('hit_ids') and len(role['hit_ids'])==len(set(role['hit_ids'])),'Role native hit references missing/repeated')
        role_domains=[]
        for hit_id in role['hit_ids']:
            require(hit_id in hits,'Role hit missing');h=hits[hit_id]
            require(h['locus_key']==key and h['source_aa_sha256']==role['source_aa_sha256'],'Role hit/source identity differs')
            require(SHA.fullmatch(h.get('profile_sha256','')) and ref_valid(h.get('raw_ref')),'Unbound native domain evidence')
            require(h['native_role_threshold_passed'] is True,'Rejected/raw-only domain cannot establish role')
            require(h['target_length']==source['protein_aa_length'],'Native target length differs')
            lo,hi=h['alignment_from'],h['alignment_to'];require(1<=lo<=hi<=h['target_length'],'Native target domain bounds invalid')
            require(h['threshold_receipt_verified'] is True,'Model threshold/domain criteria receipt missing')
            hit_roles.setdefault(hit_id,set()).add(role['role'])
            role_domains.append((lo,hi))
        roles.add(role['role']);role_to_locus.setdefault(role['role'],set()).add(key)
        for flag in ['source_pseudo_any','partial_or_fuzzy','linear_edge','origin_spanning','requires_coordinate_review']:
            if source.get(flag):issues.add(flag)
        require(source['protein_target_present'] is True,'Untranslated locus cannot acquire invented role protein')
        require(role['domain_completeness_review']=='REVIEWED_INTACT' or role['domain_completeness_review']=='REVIEWED_PARTIAL','Domain completeness review missing')
        if role['domain_completeness_review']=='REVIEWED_PARTIAL':issues.add('reviewed_partial_domain')
    # Context reviewed without protein can explain missing/partial architecture;
    # it remains separate, never turned into an HMM-supported role.
    for missing in review.get('untranslated_context_locus_keys',[]):
        require(missing in identity['locus_keys'] and missing in sources and sources[missing]['protein_target_present'] is False,'Untranslated context identity differs')
        issues.add('untranslated_context')
    covered={r['locus_key'] for r in review['roles']}|set(review.get('untranslated_context_locus_keys',[]))
    for context in review.get('other_candidate_locus_reviews',[]):
        require(context['locus_key'] in identity['locus_keys'] and context['locus_key'] in sources and refs_valid(context.get('evidence_refs')) and context['execution']=='EXECUTED_CANDIDATE_LOCUS_CONTEXT_REVIEW','Additional candidate locus unreviewed')
        covered.add(context['locus_key'])
    require(covered==set(identity['locus_keys']),'Not every native candidate locus accounted in review')
    require(set(role_to_locus) or review.get('untranslated_context_locus_keys'),'No actual role or source-context evidence')
    require(review.get('compatibility_state') in {'COMPATIBLE_REVIEWED','INCOMPATIBLE','UNRESOLVED'},'Compatibility review missing')
    if review['compatibility_state']!='COMPATIBLE_REVIEWED':issues.add('incompatible_or_unresolved_roles')
    require(refs_valid(review.get('compatibility_basis_refs')),'Role compatibility evidence required')
    if any(len(values)>1 for values in hit_roles.values()):
        if review.get('shared_profile_role_resolution')!='REVIEWED_MULTIFUNCTIONAL_PROFILE_WITH_DOMAIN_BASIS' or not refs_valid(review.get('shared_profile_role_basis_refs')):issues.add('one_profile_multiple_functional_roles_unresolved')
    fusion_by_type={'I':'REVIEWED_SUPPORTED_TYPE_I_FUSION','II':'REVIEWED_SUPPORTED_TYPE_II_FUSION','III':'REVIEWED_SUPPORTED_TYPE_III_FUSION'}
    if candidate['rm_type'] in fusion_by_type:
        relevant=ROLE_REQUIREMENTS[candidate['rm_type']];locus_roles={}
        for role,keys in role_to_locus.items():
            if role in relevant:
                for key in keys:locus_roles.setdefault(key,set()).add(role)
        if any(len(values)>1 for values in locus_roles.values()):
            allowed={fusion_by_type[candidate['rm_type']]}
            if candidate.get('subtype')=='IIG':allowed.add('REVIEWED_DUAL_FUNCTION_DOMAIN_ARCHITECTURE')
            if review.get('fusion_architecture_review') not in allowed or not refs_valid(review.get('fusion_basis_refs')):issues.add('fusion_architecture_unresolved')
    if candidate.get('subtype')=='IIG':
        # Family label alone is insufficient. Different reviewed domains may
        # share a locus; evidence must justify fusion and recognition basis.
        same=role_to_locus.get('REASE',set())&role_to_locus.get('MTASE',set())
        if len(identity['locus_keys'])!=1 or not same or review.get('fusion_architecture_review')!='REVIEWED_DUAL_FUNCTION_DOMAIN_ARCHITECTURE' or not refs_valid(review.get('fusion_basis_refs')):
            issues.add('unresolved_IIG_fusion')
    if candidate.get('subtype')=='McrBC' and not {'MCRB','MCRC'}<=roles:issues.add('McrBC_partner_missing')
    if candidate.get('subtype')=='GmrSD' and not {'GMR_S','GMR_D'}<=roles and review.get('fusion_architecture_review')!='REVIEWED_GmrSD_FUSION_ARCHITECTURE':issues.add('GmrSD_partner_or_fusion_unresolved')
    if candidate['rm_type']=='IV':
        if review.get('modification_dependence_basis')!='REVIEWED_FAMILY_SPECIFIC_PREDICTION' or not refs_valid(review.get('modification_dependence_refs')):issues.add('modification_dependence_unresolved')
        # LlaJI-like methylase contexts, general GTPase/nuclease or MTase labels
        # need a family-specific resolution before Type IV mapping is accepted.
        if review.get('TypeIV_vs_TypeII_competing_context')!='RESOLVED_WITH_EXPLICIT_BASIS':issues.add('TypeIV_TypeII_context_unresolved')
    resolutions=review.get('context_issue_resolutions',{})
    for issue in ['linear_edge','origin_spanning','requires_coordinate_review']:
        if issue in issues and isinstance(resolutions.get(issue),dict) and resolutions[issue].get('state')=='REVIEWED_SOURCE_ARCHITECTURE_UNAFFECTED' and refs_valid(resolutions[issue].get('evidence_refs')):issues.remove(issue)
    # A pseudogene/partial source claim cannot be erased by a generic resolution
    # enum. A documented provider contradiction is an explicit separate blocker.
    return roles,issues

def classify_candidate(candidate,review,sources,hits):
    canonical_candidate(candidate)
    if candidate['rm_type'] is None:
        return {'state':'UNCERTAIN','locus_annotation_state':'UNMAPPED_GENERIC_OR_REPAIR_CANDIDATE','functional_evidence_grade':'NOT_ESTABLISHED'}
    if review is None:return {'state':'PARTIAL_CANDIDATE','reason':'UNREVIEWED_RAW_CANDIDATE','functional_evidence_grade':'NOT_ESTABLISHED'}
    roles,issues=validate_role_evidence(candidate,review,sources,hits)
    missing=ROLE_REQUIREMENTS[candidate['rm_type']]-roles
    architecture_complete=not missing and not issues
    decision=review['decision']
    if decision=='COMPLETE_PREDICTED':require(architecture_complete,'Complete prediction lacks intact compatible required roles/context')
    elif decision=='CURATED_PARTIAL':
        require(not architecture_complete,'Intact complete architecture mislabeled partial')
        require(refs_valid(review.get('partial_basis_refs')) and review.get('partial_interpretation') in {'REVIEWED_MISSING_COMPONENT','REVIEWED_TRUNCATED_OR_PSEUDOGENIZED_ARCHITECTURE'},'Partial rationale missing')
        require(not {'incompatible_or_unresolved_roles','modification_dependence_unresolved','TypeIV_TypeII_context_unresolved'}&issues,'Unresolved type/compatibility cannot become reviewed partial')
    elif decision in {'UNCERTAIN','PARTIAL_CANDIDATE'}:pass
    elif decision in {'REVIEWED_ORPHAN_MTASE','REVIEWED_GENERIC_NUCLEASE','REVIEWED_REPAIR_OR_NON_RM'}:
        require(refs_valid(review.get('exclusion_basis_refs')),'Orphan/generic exclusion requires executed evidence')
        return {'state':'UNCERTAIN','locus_annotation_state':decision,'excluded_from_type_cell':True,'functional_evidence_grade':'NOT_ESTABLISHED'}
    else:raise ValueError('Unrecognized review decision')
    return {'state':decision,'missing_roles':sorted(missing),'context_issues':sorted(issues),'functional_evidence_grade':'PREDICTED_ARCHITECTURE_ONLY'}

def cell_state(search,coverage,candidate_results):
    """State plus preserved positive counts; failure priority cannot be white."""
    # This reducer accepts only outputs of an executed candidate review or
    # explicit unreviewed/uncertain candidates. Cell search states are invalid
    # candidate states; neither unknown nor failed candidate evidence is absence.
    require(isinstance(candidate_results,(list,tuple)),'Candidate outcomes must be an explicit sequence')
    allowed={'UNCERTAIN','PARTIAL_CANDIDATE','CURATED_PARTIAL','COMPLETE_PREDICTED'}
    excluded_reasons={'REVIEWED_ORPHAN_MTASE','REVIEWED_GENERIC_NUCLEASE','REVIEWED_REPAIR_OR_NON_RM'}
    for result in candidate_results:
        require(isinstance(result,dict) and result.get('state') in allowed,'Invalid candidate outcome state')
        excluded=result.get('excluded_from_type_cell',False)
        require(isinstance(excluded,bool),'Candidate exclusion flag must be a strict boolean')
        if excluded:
            require(result['state']=='UNCERTAIN' and result.get('locus_annotation_state') in excluded_reasons
                    and result.get('functional_evidence_grade')=='NOT_ESTABLISHED',
                    'Candidate exclusion lacks a typed reviewed non-RM reason')
    counts=Counter(r['state'] for r in candidate_results if not r.get('excluded_from_type_cell'))
    positives=counts['COMPLETE_PREDICTED'];partials=counts['CURATED_PARTIAL']
    required=['PADLOC','DefenseFinder'];states=[search.get(k,'NOT_RUN') for k in required]
    require(all(s in {'NOT_RUN','FAILED','VALIDATED_FULL_NATIVE_SEARCH'} for s in states),'Invalid search execution state')
    if states==['VALIDATED_FULL_NATIVE_SEARCH','VALIDATED_FULL_NATIVE_SEARCH']:
        require(coverage['full_query_completion_verified'] is True and coverage['all_tasks_verified'] is True,'Complete labels cannot substitute native query/task proof')
        require(set(coverage.get('native_completion_refs',{}))==set(required) and all(refs_valid(refs) for refs in coverage['native_completion_refs'].values()),'Both native completion receipts must be bound')
    if 'FAILED' in states:state='FAILED'
    elif 'NOT_RUN' in states:state='NOT_RUN'
    elif positives:state='COMPLETE_PREDICTED'
    elif counts['UNCERTAIN'] or coverage['unresolved_source_contexts'] or coverage['unresolved_empty_replicons'] or coverage['unresolved_model_mappings'] or coverage['unresolved_origin_classifications']:state='UNCERTAIN'
    elif counts['PARTIAL_CANDIDATE']:state='PARTIAL_CANDIDATE'
    elif partials:state='CURATED_PARTIAL'
    else:
        require(coverage['source_review_execution']=='EXECUTED_AND_HASH_BOUND','Source absence review not executed')
        require(coverage['full_query_completion_verified'] is True and coverage['all_tasks_verified'] is True,'Incomplete native searches cannot be non-detection')
        require(coverage['all_candidates_accounted'] is True and coverage['all_full_scope_domains_accounted'] is True,'Unreviewed evidence cannot be non-detection')
        state='NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH'
    return {'state':state,'candidate_counts':dict(counts),'complete_predicted_count':positives,'curated_partial_count':partials,'required_detector_completion':dict(zip(required,states)),'coverage_unresolved':any(coverage[k] for k in ['unresolved_source_contexts','unresolved_empty_replicons','unresolved_model_mappings','unresolved_origin_classifications']),'functional_evidence_grade':'NOT_ESTABLISHED'}

def validate_rotation_receipt(receipt,source_loci):
    require(receipt['execution']=='EXECUTED_NATIVE_CLASSIFICATION_FROM_CACHED_HMM','Rotation classification not executed')
    require(receipt['biological_HMM_searches_repeated']==0,'Rotation must not rerun HMM searches')
    require(receipt['source_topology']=='DOCUMENTED_CIRCULAR','Unknown/linear origin cannot wrap')
    require(receipt['input_cached_dom_sha256']==receipt['used_cached_dom_sha256'] and SHA.fullmatch(receipt['input_cached_dom_sha256']),'Cached domain identity changed')
    require(refs_valid(receipt.get('source_refs')) and refs_valid(receipt.get('native_classification_refs')),'Origin classification evidence missing')
    original=receipt['original_locus_order'];rotated=receipt['rotated_locus_order']
    require(len(original)==len(set(original))==len(rotated) and set(original)==set(rotated),'Rotation adds/drops/duplicates source locus')
    offset=receipt['rotation_offset'];require(isinstance(offset,int) and 0<=offset<len(original),'Invalid rotation offset')
    require(rotated==original[offset:]+original[:offset],'Input is not a circular permutation')
    require(set(receipt['unchanged_source_aa_sha256'])==set(original),'Rotation source hash set incomplete')
    for key in original:require(receipt['unchanged_source_aa_sha256'][key]==source_loci[key]['primary_faa_sequence_sha256'],'Rotation changed source AA')
    require(len({tuple(key.split('|')[:2]) for key in original})==1,'Rotation crossed replicons')
    require(receipt['source_geometry_independently_verified'] is True and receipt['domain_target_remapping_independently_verified'] is True,'Rotated geometry/domain mapping not verified')
    return True

def validate_cells(panel,cells):
    require(len(panel)==len(set(panel))==196,'Exact196 panel required')
    expected={(a,t) for a in panel for t in TYPES};observed=[(r['assembly_accession'],r['rm_type']) for r in cells]
    require(len(cells)==len(set(observed))==784 and set(observed)==expected,'Exact784 cell accounting differs')
    require(all(r['state'] in STATES for r in cells),'Unknown/null cell state')
    return True
