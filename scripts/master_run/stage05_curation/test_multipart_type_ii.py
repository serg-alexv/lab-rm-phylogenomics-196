#!/usr/bin/env python3
"""Synthetic regression of family-specific RM+S; no genome or enzyme classified."""
from copy import deepcopy
import json,unittest
from types import SimpleNamespace
from pathlib import Path
import stage05_architecture_policy as P
import stage05_curation_atomic as A
import validate_atomic_curation as V
from test_independent_curation import architecture,MemoryEvidence,C

HERE=Path(__file__).resolve().parent

def fixture(subtype='IIG',reviewed='IIG'):
    c,r,s,h,e=architecture('II',['REASE','MTASE','SPECIFICITY'],subtype,locus_groups=[0,0,1])
    rm,specificity=c['locus_keys'];primary=e.add('json:primary-family-synthetic',{'dataset_kind':'SYNTHETIC','text':'Synthetic family architecture basis only.'})
    f={'schema':'RM_MULTIPART_TYPE_II_FAMILY_ARCHITECTURE_V1','architecture':'FUSED_RM_SEPARATE_SPECIFICITY',
       'family_id':'SYNTHETIC_FAMILY','reviewed_subtype':reviewed,'rm_locus_key':rm,'specificity_locus_key':specificity,
       'primary_family_basis_refs':[primary]}
    aa={role['locus_key']:next(ref for ref in role['functional_domain_basis_refs'] if ref['record_locator'].startswith('fasta:')) for role in r['roles']}
    w={'schema':'RM_MULTIPART_TYPE_II_FAMILY_REVIEW_V1','execution':'EXECUTED_INDEPENDENT_SOURCE_DOMAIN_FAMILY_REVIEW',
       'decision':'SUPPORTED_FUSED_RM_SEPARATE_SPECIFICITY','independent_of_curation_producer':True,'reviewer_id':'synthetic-family-independent',
       'assembly_accession':c['assembly_accession'],'candidate_id':r['candidate_id'],'family_id':f['family_id'],'reviewed_subtype':reviewed,
       'rm_locus_key':rm,'specificity_locus_key':specificity,'rm_source_aa_sha256':s[rm]['primary_faa_sequence_sha256'],
       'specificity_source_aa_sha256':s[specificity]['primary_faa_sequence_sha256'],'evidence_hit_ids':sorted(h),
       'native_model_ids':['EXACT_MODEL'],'native_candidate_ref_sha256':sorted(V.objsha(ref) for ref in c['native_candidate_refs']),
       'primary_family_basis_refs':[primary],'basis_refs':[hit['raw_ref'] for hit in h.values()]+list(aa.values())+[primary],
       'family_architecture_basis_statement':'Synthetic executed family/source/domain compatibility interpretation only.',
       'unresolved_competing_type_or_architecture_interpretations':0}
    f['independent_family_review_ref']=e.add('json:family-review',w)
    r.update(type_ii_family_architecture=f,fusion_architecture_review='REVIEWED_SUPPORTED_TYPE_II_FUSION',
             fusion_basis_refs=r['architecture_basis_refs'],recognition_architecture_review='REVIEWED_FAMILY_SPECIFIC_RECOGNITION_DOMAIN_BASIS',
             recognition_basis_refs=[primary])
    e.resolve=e.ref
    ctx=SimpleNamespace(hits=h,sources=s,reader=e,aa_refs=aa,queue=[])
    return (c,r,s,h,e),ctx

class MultipartFamily(unittest.TestCase):
    def both(self,args):
        self.assertEqual(P.classify_candidate(*args[:4])['state'],'COMPLETE_PREDICTED')
        self.assertEqual(V.additional_architecture(*args,C.architecture)[2]['state'],'COMPLETE_PREDICTED')
    def reject_both(self,args):
        with self.assertRaises((ValueError,KeyError)):P.classify_candidate(*args[:4])
        with self.assertRaises((ValueError,KeyError)):V.additional_architecture(*args,C.architecture)
    def test_obsolete_core_rejects_valid_two_gene_fixture_new_paths_accept(self):
        args,ctx=fixture()
        with self.assertRaises(ValueError):C.architecture(*args)
        self.both(args)
        A.review_addenda(ctx,{'manual_candidates':[{'candidate':args[0],'candidate_review':args[1]}]})
    def test_IIB_and_unresolved_subtype_remain_broad_II_without_guessing_IIG(self):
        for proposed,reviewed in [('IIB','IIB'),(None,'UNRESOLVED_TYPE_II_SUBTYPE'),('IIG','IIB')]:
            args,_=fixture(proposed,reviewed);self.both(args)
            self.assertEqual(args[0]['subtype'],proposed)
            self.assertEqual(args[1]['type_ii_family_architecture']['reviewed_subtype'],reviewed)
    def test_missing_S_or_unreviewed_extra_locus_rejected(self):
        for mode in ('S','extra'):
            args,_=fixture()
            if mode=='S':args[1]['roles']=[r for r in args[1]['roles'] if r['role']!='SPECIFICITY']
            else:args[0]['locus_keys'].append('GCF_999999999.1|NC_SYNTHETIC.1|UNREVIEWED')
            self.reject_both(args)
    def test_generic_fusion_plus_neighbor_S_not_automatic_complete(self):
        args,_=fixture(None,'UNRESOLVED_TYPE_II_SUBTYPE');del args[1]['type_ii_family_architecture'];self.reject_both(args)
    def test_primary_family_and_recognition_basis_required(self):
        for key in ('primary_family_basis_refs','independent_family_review_ref'):
            args,_=fixture();del args[1]['type_ii_family_architecture'][key];self.reject_both(args)
        args,_=fixture();args[1]['recognition_architecture_review']='UNRESOLVED';self.reject_both(args)
    def test_independent_family_witness_exact_native_source_and_attribution(self):
        for field,value in [('rm_source_aa_sha256','c'*64),('evidence_hit_ids',['H0']),('native_model_ids',['WRONG_MODEL']),
                            ('native_candidate_ref_sha256',[]),('reviewer_id','synthetic-producer'),
                            ('unresolved_competing_type_or_architecture_interpretations',1)]:
            args,ctx=fixture();w=args[4].ref(args[1]['type_ii_family_architecture']['independent_family_review_ref']);w[field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):V.additional_architecture(*args,C.architecture)
                with self.assertRaises(ValueError):A.review_addenda(ctx,{'manual_candidates':[{'candidate':args[0],'candidate_review':args[1]}]})
    def test_partial_pseudo_and_edge_S_still_reject_complete(self):
        for flag in ('partial_or_fuzzy','source_pseudo_any','linear_edge'):
            args,_=fixture();args[2][args[1]['type_ii_family_architecture']['specificity_locus_key']][flag]=True;self.reject_both(args)
    def test_domain_or_primaryAA_omitted_from_family_witness_rejected(self):
        for index in (0,3):
            args,ctx=fixture();args[4].ref(args[1]['type_ii_family_architecture']['independent_family_review_ref'])['basis_refs'].pop(index)
            with self.assertRaises(ValueError):V.additional_architecture(*args,C.architecture)
            with self.assertRaises(ValueError):A.review_addenda(ctx,{'manual_candidates':[{'candidate':args[0],'candidate_review':args[1]}]})
    def test_ordinary_single_chain_IIG_unchanged(self):
        args=architecture('II',['REASE','MTASE'],'IIG',True)
        args[1].update(fusion_architecture_review='REVIEWED_DUAL_FUNCTION_DOMAIN_ARCHITECTURE',fusion_basis_refs=args[1]['architecture_basis_refs'],
                       recognition_architecture_review='REVIEWED_FAMILY_SPECIFIC_RECOGNITION_DOMAIN_BASIS',recognition_basis_refs=args[1]['architecture_basis_refs'])
        self.both(args)
    def test_ignored_scalar_subtype_override_rejected(self):
        args,ctx=fixture()
        with self.assertRaises(ValueError):A.review_addenda(ctx,{'manual_candidates':[{'candidate':args[0],'reviewed_subtype':'IIB','candidate_review':args[1]}]})
    def test_actual_candidate_apply_and_independent_reconstruction_with_expansion(self):
        args,ctx=fixture();c,r,s,h,e=args;native=deepcopy(c)
        native['locus_keys']=[r['type_ii_family_architecture']['rm_locus_key']]
        native['candidate_id']=P.canonical_candidate(native)[1]
        item={'queue_id':'SYNTHETIC_QUEUE','candidate_review':r,
              'additional_source_locus_keys':[r['type_ii_family_architecture']['specificity_locus_key']],
              'candidate_expansion_execution':'EXECUTED_SOURCE_NEIGHBORHOOD_REVIEW',
              'candidate_expansion_rationale':'Synthetic exact source neighborhood extension only.',
              'candidate_expansion_basis_refs':r['type_ii_family_architecture']['primary_family_basis_refs']}
        ctx.queue=[{'queue_id':'SYNTHETIC_QUEUE','evidence':native}];ctx.policy=P;ctx.source_refs=e.source_refs
        A.review_addenda(ctx,{'reviews':[item]});adapter=A.load_retained()
        produced=adapter.apply_candidate(ctx,native,item)
        original=C.architecture;C.architecture=lambda *a:V.additional_architecture(*a,original)
        try:independent=C.reviewed_candidate(native,item,s,h,e)
        finally:C.architecture=original
        self.assertEqual(produced,independent)
        self.assertEqual(produced['result']['state'],'COMPLETE_PREDICTED')
        self.assertEqual(native['locus_keys'],[r['type_ii_family_architecture']['rm_locus_key']])
    def test_explicit_native_type_remapping_uses_same_final_family_type(self):
        args,ctx=fixture();c,r,s,h,e=args;native={**c,'rm_type':None}
        native['candidate_id']=P.canonical_candidate(native)[1]
        item={'queue_id':'SYNTHETIC_MAPPING','candidate_review':r,
              'type_mapping_execution':'EXECUTED_SOURCE_DOMAIN_CONTEXT_TYPE_MAPPING',
              'type_mapping_basis_refs':r['type_ii_family_architecture']['primary_family_basis_refs']}
        ctx.queue=[{'queue_id':'SYNTHETIC_MAPPING','evidence':native}];ctx.policy=P;ctx.source_refs=e.source_refs
        A.review_addenda(ctx,{'reviews':[item]});produced=A.load_retained().apply_candidate(ctx,native,item)
        original=C.architecture;C.architecture=lambda *a:V.additional_architecture(*a,original)
        try:independent=C.reviewed_candidate(native,item,s,h,e)
        finally:C.architecture=original
        self.assertEqual(produced,independent)
        self.assertEqual(independent['rm_type'],'II')

def main():
    suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'PASS_SYNTHETIC_MULTIPART_TYPE_II_REGRESSION_ONLY' if result.wasSuccessful() else 'FAIL',
            'dataset_kind':'SYNTHETIC','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'biological_jobs':0,'actual_architecture_curation':'NOT_RUN','production_curation_certificates_written':0,
            'sources':{p.name:V.sha(p) for p in (HERE/'stage05_architecture_policy.py',HERE/'stage05_curation_atomic.py',HERE/'validate_atomic_curation.py')}}
    (HERE/'multipart_synthetic_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':main()
