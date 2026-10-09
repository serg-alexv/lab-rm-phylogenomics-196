#!/usr/bin/env python3
"""Focused synthetic guards for new atomic bridge/serialization, no biology."""
from __future__ import annotations
import csv,hashlib,json,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import stage05_architecture_policy as P
import stage05_curation_atomic as A
import rm_matrix as M
import validate_rm_join as J

HERE=Path(__file__).resolve().parent

def ref(name='fixture'):
    return {'path':name+'.tsv','sha256':'a'*64,'record_locator':'fixture:1'}

def fixture(kind='I',roles=None,subtype=None,fused=False):
    roles=roles or sorted(P.ROLE_REQUIREMENTS[kind]);keys=['GCF_999999999.1|NC_SYNTHETIC.1|L'+str(i) for i in range(len(roles))]
    if fused:keys=[keys[0]]*len(roles)
    c={'assembly_accession':'GCF_999999999.1','rm_type':kind,'subtype':subtype,'locus_keys':sorted(set(keys)),
       'detector':'PADLOC','native_candidate_refs':[ref()]}
    sources={k:{'locus_key':k,'primary_faa_sequence_sha256':hashlib.sha256(k.encode()).hexdigest(),'protein_aa_length':600,
                'protein_target_present':True,'source_pseudo_any':False,'partial_or_fuzzy':False,'linear_edge':False,
                'origin_spanning':False,'requires_coordinate_review':False,'protein_accession':'WP_REPEATED.1'} for k in keys}
    hits={};rr=[]
    for i,(role,key) in enumerate(zip(roles,keys)):
        h='H'+str(i);hits[h]={'locus_key':key,'source_aa_sha256':sources[key]['primary_faa_sequence_sha256'],
                            'profile_sha256':'b'*64,'raw_ref':ref(h),'native_role_threshold_passed':True,
                            'target_length':600,'alignment_from':1+i*80,'alignment_to':70+i*80,'threshold_receipt_verified':True}
        rr.append({'role':role,'locus_key':key,'source_aa_sha256':sources[key]['primary_faa_sequence_sha256'],
                   'functional_domain_basis_refs':[ref('role'+h)],'hit_ids':[h],'domain_completeness_review':'REVIEWED_INTACT'})
    review={'candidate_id':P.canonical_candidate(c)[1],'rm_type':kind,'execution':'EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW',
            'source_context_refs':[ref('source')],'architecture_basis_refs':[ref('architecture')],
            'functional_evidence_grade':'PREDICTED_ARCHITECTURE_ONLY','unresolved_competing_annotations':0,'roles':rr,
            'compatibility_state':'COMPATIBLE_REVIEWED','compatibility_basis_refs':[ref('compatibility')],'decision':'COMPLETE_PREDICTED',
            'modification_dependence_basis':'REVIEWED_FAMILY_SPECIFIC_PREDICTION','modification_dependence_refs':[ref('moddep')],
            'TypeIV_vs_TypeII_competing_context':'RESOLVED_WITH_EXPLICIT_BASIS'}
    return c,review,sources,hits

def cell(kind='II',state='COMPLETE_PREDICTED',complete=1,partial=0,uncertain=0,failed=False):
    counts={}
    for k,n in [('COMPLETE_PREDICTED',complete),('CURATED_PARTIAL',partial),('UNCERTAIN',uncertain)]:
        if n:counts[k]=n
    return {'assembly_accession':'GCF_999999999.1','rm_type':kind,'state':state,'candidate_counts':counts,
            'complete_predicted_count':complete,'curated_partial_count':partial,'candidate_ids':['CID'+str(i) for i in range(sum(counts.values()))],
            'required_detector_completion':{'PADLOC':M.SEARCH,'DefenseFinder':'FAILED' if failed else M.SEARCH},
            'coverage_unresolved':bool(uncertain),'review_execution':'COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW'}

class Architecture(unittest.TestCase):
    def test_retained_pins_and_exact_scope(self):
        A.load_retained();scope=A.load(HERE/'pinned_model_candidate_scope.json')
        self.assertEqual(len(scope['models']),39)
        mapping={(x['detector'],x['model_id']):x for x in scope['models']}
        self.assertEqual(mapping['PADLOC','RM_type_IIG']['proposed_type'],'II')
        self.assertIsNone(mapping['PADLOC','RM_type_HNH']['proposed_type'])
        self.assertNotIn(('PADLOC','unrecognized_type_IV_name'),mapping)
    def test_type_I_RM_without_S_rejects_complete(self):
        with self.assertRaises(ValueError):P.classify_candidate(*fixture('I',['REASE','MTASE']))
    def test_type_I_missingS_reviewed_partial(self):
        c,r,s,h=fixture('I',['REASE','MTASE']);r.update(decision='CURATED_PARTIAL',partial_basis_refs=[ref('missingS')],partial_interpretation='REVIEWED_MISSING_COMPONENT')
        self.assertEqual(P.classify_candidate(c,r,s,h)['state'],'CURATED_PARTIAL')
    def test_IIG_requires_fused_architecture_basis(self):
        c,r,s,h=fixture('II',['REASE','MTASE'],'IIG',True)
        with self.assertRaises(ValueError):P.classify_candidate(c,r,s,h)
        r.update(fusion_architecture_review='REVIEWED_DUAL_FUNCTION_DOMAIN_ARCHITECTURE',fusion_basis_refs=[ref('fusion')])
        self.assertEqual(P.classify_candidate(c,r,s,h)['state'],'COMPLETE_PREDICTED')
    def test_typeIII_needs_Mod_and_Res_compatibility(self):
        c,r,s,h=fixture('III');r['compatibility_state']='UNRESOLVED'
        with self.assertRaises(ValueError):P.classify_candidate(c,r,s,h)
    def test_typeIV_requires_partner_and_modification_basis(self):
        with self.assertRaises(ValueError):P.classify_candidate(*fixture('IV',['MOD_DEPENDENT_RECOGNITION','CLEAVAGE','MCRB'],'McrBC'))
        c,r,s,h=fixture('IV',['MOD_DEPENDENT_RECOGNITION','CLEAVAGE']);r['TypeIV_vs_TypeII_competing_context']='LlaJI_UNRESOLVED'
        with self.assertRaises(ValueError):P.classify_candidate(c,r,s,h)
    def test_typeIV_single_protein_no_cognate_MTase_requirement(self):
        self.assertEqual(P.classify_candidate(*fixture('IV',['MOD_DEPENDENT_RECOGNITION','CLEAVAGE'],fused=True))['state'],'COMPLETE_PREDICTED')
    def test_edge_partial_pseudogene_rejects_complete(self):
        for flag in ('linear_edge','partial_or_fuzzy','source_pseudo_any','origin_spanning'):
            with self.subTest(flag=flag):
                c,r,s,h=fixture();next(iter(s.values()))[flag]=True
                with self.assertRaises(ValueError):P.classify_candidate(c,r,s,h)
    def test_repeatedWP_exact_loci_and_nontransitive_dedup(self):
        c,r,s,h=fixture();self.assertEqual(len({v['protein_accession'] for v in s.values()}),1)
        self.assertEqual(P.classify_candidate(c,r,s,h)['state'],'COMPLETE_PREDICTED')
        other=deepcopy(c);other['detector']='DefenseFinder';self.assertEqual(len(P.deduplicate_exact([c,other])),1)
        other['locus_keys']=[c['locus_keys'][0],c['locus_keys'][1],'GCF_999999999.1|NC_SYNTHETIC.1|OTHER']
        self.assertEqual(len(P.deduplicate_exact([c,other])),2)
    def test_cross_scaffold_roles_reject(self):
        c=fixture()[0];c['locus_keys'][0]='GCF_999999999.1|NC_OTHER.1|L0'
        with self.assertRaises(ValueError):P.canonical_candidate(c)

class Bridge(unittest.TestCase):
    def setUp(self):
        self.key='GCF_999999999.1|NC_SYNTHETIC.1|L0'
        self.source={self.key:{'replicon':'NC_SYNTHETIC.1','derived_linear_order_start_one_based':'101','derived_linear_order_end_one_based':'900'}}
        self.hit={'detector':'PADLOC','locus_key':self.key,'profile_name':'EXACT_PROFILE',
                  'domain':{'independent_evalue':'1.23456e-20'},'native_profile_coverage':0.875,'native_target_coverage':0.725,
                  'native_role_threshold_passed':True}
        self.native={'target.name':self.key,'seqid':'NC_SYNTHETIC.1','hmm.name':'EXACT_PROFILE','system':'RM_type_I',
                     'domain.iE.value':'1.23e-20','hmm.coverage':'0.875','target.coverage':'0.725','start':'101','end':'900','protein.name':'MTase_I'}
    def calls(self,native=None):return [{'detector':'PADLOC','native_row_json':json.dumps(native or self.native)}]
    def test_actual_native_selected_rounded_domain(self):
        hits={'h':deepcopy(self.hit)};A.native_padloc_selection(hits,self.source,self.calls())
        self.assertTrue(hits['h']['native_role_threshold_passed']);self.assertEqual(hits['h']['native_selected_model_ids'],['RM_type_I'])
    def test_raw_unselected_domain_cannot_establish_role(self):
        hits={'h':deepcopy(self.hit)};A.native_padloc_selection(hits,self.source,[])
        self.assertFalse(hits['h']['native_role_threshold_passed'])
    def test_ambiguous_rounded_domain_blocks_role(self):
        hits={'h1':deepcopy(self.hit),'h2':deepcopy(self.hit)};A.native_padloc_selection(hits,self.source,self.calls())
        self.assertTrue(hits['h1']['native_domain_selector_ambiguous']);self.assertFalse(hits['h1']['native_role_threshold_passed'])
    def test_native_source_geometry_drift_rejected(self):
        n=deepcopy(self.native);n['start']='102'
        with self.assertRaises(ValueError):A.native_padloc_selection({'h':deepcopy(self.hit)},self.source,self.calls(n))
    def test_qualified_records_read_actual_C_and_G_roots(self):
        adapter=A.load_retained()
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            root=Path(d);roots=[]
            for name in A.qualified_reader_class(adapter).names:
                path=root/name;path.mkdir();roots.append(path)
            path=roots[5]/'model.txt';path.write_text('actual model\n',encoding='utf-8')
            reader=A.qualified_reader_class(adapter)(root,roots);r=reader.make_ref(path,'text:1-1','actual model\n')
            self.assertEqual(reader.resolve(r),'actual model\n');path.write_text('tampered\n',encoding='utf-8')
            with self.assertRaises(ValueError):reader.resolve(r)
    def test_manifest_escape_reject(self):
        with self.assertRaises(ValueError):A.member(HERE,'../escape')
        with self.assertRaises(ValueError):A.member(HERE,'a\\b')
    def test_explicit_role_profile_binding_and_IIG_recognition(self):
        raw=ref('raw');witness={'schema':'RM_FUNCTIONAL_DOMAIN_ROLE_REVIEW_V1','execution':'EXECUTED_INDEPENDENT_SOURCE_DOMAIN_ROLE_REVIEW',
            'decision':'SUPPORTED_PREDICTED_ROLE','independent_of_curation_producer':True,'reviewer_id':'synthetic-independent',
            'hit_id':'h','locus_key':'SYNTHETIC_LOCUS','source_aa_sha256':'b'*64,'profile_name':'EXACT_IIG_PROFILE','profile_sha256':'a'*64,
            'model_id':'RM_type_IIG','role':'REASE','alignment_from':1,'alignment_to':600,'target_length':600,
            'native_component_names':['REase_MTase_IIG'],'basis_refs':[raw],
            'functional_basis_statement':'Synthetic role interpretation only; no actual protein classified.',
            'unresolved_competing_role_interpretations':0,'functional_architecture_basis_refs':[ref('primary')]}
        reader=SimpleNamespace(refs=lambda refs: self.assertTrue(refs),resolve=lambda ref:witness)
        hit={'profile_name':'EXACT_IIG_PROFILE','profile_sha256':'a'*64,'native_model_roles':[{'model':'RM_type_IIG','role':'REase_MTase_IIG'}],
             'locus_key':'SYNTHETIC_LOCUS','source_aa_sha256':'b'*64,'alignment_from':1,'alignment_to':600,'target_length':600,'raw_ref':raw}
        context=SimpleNamespace(reader=reader,hits={'h':hit},queue=[])
        role={'role':'REASE','hit_ids':['h'],'native_profile_role_bindings':[{'hit_id':'h','profile_name':'EXACT_IIG_PROFILE',
              'profile_sha256':'a'*64,'model_id':'RM_type_IIG','role':'REASE','role_basis_refs':[ref('primary')],
              'independent_functional_role_ref':ref('independent')}]}
        review={'rm_type':'II','decision':'COMPLETE_PREDICTED','curation_reviewer_id':'synthetic-producer','roles':[role]}
        record={'candidate':{'subtype':'IIG'},'candidate_review':review}
        document={'manual_candidates':[record]}
        with self.assertRaises(ValueError):A.review_addenda(context,document)
        review.update(recognition_architecture_review='REVIEWED_FAMILY_SPECIFIC_RECOGNITION_DOMAIN_BASIS',recognition_basis_refs=[ref('recognition')])
        A.review_addenda(context,document)
        role['native_profile_role_bindings'][0]['profile_name']='ARBITRARY_NAME'
        with self.assertRaises(ValueError):A.review_addenda(context,document)

class Serialization(unittest.TestCase):
    def test_positive_persists_additional_uncertain_partial_failure(self):
        c=cell(state='FAILED',partial=1,uncertain=1,failed=True);r,v=M.normalize(c,c['assembly_accession'])
        self.assertEqual(v,'1');self.assertEqual(r['conflict'],'True');self.assertEqual(r['count_lower_bound'],'True')
    def test_invalidated_positive_is_NA(self):
        c=cell();c['positive_invalidated']=True;self.assertEqual(M.normalize(c,c['assembly_accession'])[1],'NA')
    def test_partial_failed_and_notrun_NA(self):
        for c in [cell(state='CURATED_PARTIAL',complete=0,partial=1),cell(state='FAILED',complete=0,failed=True),M.initial('GCF_999999999.1','II')]:
            self.assertEqual(M.normalize(c,c['assembly_accession'])[1],'NA')
    def test_zero_requires_two_detector_clean_executed_review(self):
        c=cell(state='NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH',complete=0)
        self.assertEqual(M.normalize(c,c['assembly_accession'])[1],'0')
        for k,v in [('coverage_unresolved',True),('review_execution','NOT_RUN')]:
            broken=deepcopy(c);broken[k]=v
            with self.assertRaises(ValueError):M.normalize(broken,c['assembly_accession'])
    def test_exact784_by_accession_not_row_position(self):
        panel=['GCF_'+str(900000000+i)+'.1' for i in range(196)]
        wide,long=M.build(panel,[])
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            root=Path(d);(root/'approved').write_text('\n'.join(panel)+'\n',encoding='ascii')
            (root/'tree').write_text('('+','.join(a+':0.1' for a in reversed(panel))+');\n',encoding='ascii')
            M.table(root/'matrix',list(reversed(wide)),['accession']+['Type_'+t for t in M.TYPES])
            M.table(root/'state',list(reversed(long)),M.STATE_FIELDS)
            report=J.check(root/'approved',root/'tree',root/'matrix',root/'state',True)
            self.assertEqual(report['status'],'PASS_SYNTHETIC_EXACT_JOIN');self.assertEqual(report['cell_values']['NA'],784)
            (root/'tree').write_text('('+','.join(a+':0.1' for a in panel[:-1]+[panel[0]])+');',encoding='ascii')
            with self.assertRaises(ValueError):J.check(root/'approved',root/'tree',root/'matrix',root/'state',True)
    def test_internal_support_not_tip_and_bad_newick(self):
        self.assertEqual(J.tips("(('GCF_1.1':.1,GCF_2.1:.2)99/100:.3,GCF_3.1:.4)[note];"),['GCF_1.1','GCF_2.1','GCF_3.1'])
        for value in ('(a:NaN,b:.1);','(a:-1,b:.1);','(a,b);(c,d);','(a,b','(a);'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):J.tips(value)

def main():
    suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'PASS_FOCUSED_SYNTHETIC_COMPONENT_TESTS_ONLY' if result.wasSuccessful() else 'FAIL',
            'dataset_kind':'SYNTHETIC','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'biological_jobs':0,'actual_architecture_curation':'NOT_RUN','full196_native_integration':'NOT_RUN',
            'sources':{p.name:M.sha(p) for p in HERE.glob('*.py')}}
    (HERE/'synthetic_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':main()
