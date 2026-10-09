#!/usr/bin/env python3
"""Synthetic component tests of independent reviewer; no production certificate."""
from __future__ import annotations
import csv,json,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import validate_atomic_curation as V
import rm_matrix as M

HERE=Path(__file__).resolve().parent
C=V.core()

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

class MemoryEvidence:
    """Explicit synthetic typed records used only for local predicate checks."""
    def __init__(self):self.values={};self.source_refs={}
    def add(self,locator,value):
        ref={'path':'SYNTHETIC','sha256':'a'*64,'record_locator':locator,'record_sha256':V.objsha(value)}
        self.values[V.objsha(ref)]=value;return ref
    def ref(self,ref):return self.values[V.objsha(ref)]
    def refs(self,refs):
        if not refs:raise ValueError('Missing synthetic evidence')
        return [self.ref(r) for r in refs]
    def nested(self,document):pass

def architecture(kind='I',roles=None,subtype=None,fused=False,locus_groups=None):
    roles=roles or sorted(C.NEEDED[kind]);reader=MemoryEvidence();sources={};hits={};review_roles=[]
    keys=['GCF_999999999.1|NC_SYNTHETIC.1|L'+str(locus_groups[i] if locus_groups is not None else 0 if fused else i) for i in range(len(roles))]
    basis=[];source_refs=[]
    for i,(role,key) in enumerate(zip(roles,keys)):
        source={'locus_key':key,'protein_target_present':True,'primary_faa_sequence_sha256':'a'*64,'protein_aa_length':600,
                '_sequence':'A'*600,**{flag:False for flag in C.FLAGS},'linear_edge':False}
        source['protein_target_present']=True;sources[key]=source
        sr=reader.add('tsv:'+str(i+1),{'locus_key':key});source_refs.append(sr);reader.source_refs[key]=sr
        aa=reader.add('fasta:'+key,{'target_id':key,'sequence':'A'*600})
        raw=reader.add('tsv:domain'+str(i),{'synthetic_domain':i});basis.append(raw)
        hid='H'+str(i);hits[hid]={'locus_key':key,'source_aa_sha256':'a'*64,'target_length':600,'native_role_threshold_passed':True,
            'threshold_receipt_verified':True,'alignment_from':1+100*i,'alignment_to':90+100*i,'profile_sha256':'b'*64,
            'profile_name':'EXACT_PROFILE_'+role,'native_model_roles':[{'model':'EXACT_MODEL','role':'EXACT_COMPONENT_'+role}],'raw_ref':raw}
        witness={'schema':'RM_FUNCTIONAL_DOMAIN_ROLE_REVIEW_V1','execution':'EXECUTED_INDEPENDENT_SOURCE_DOMAIN_ROLE_REVIEW',
                 'decision':'SUPPORTED_PREDICTED_ROLE','independent_of_curation_producer':True,'reviewer_id':'synthetic-independent',
                 'hit_id':hid,'locus_key':key,'source_aa_sha256':'a'*64,'profile_name':hits[hid]['profile_name'],'profile_sha256':'b'*64,
                 'model_id':'EXACT_MODEL','role':role,'alignment_from':hits[hid]['alignment_from'],'alignment_to':hits[hid]['alignment_to'],
                 'target_length':600,'native_component_names':['EXACT_COMPONENT_'+role],'basis_refs':[raw,aa],
                 'functional_basis_statement':'Explicit synthetic functional domain interpretation; no actual protein classified.',
                 'unresolved_competing_role_interpretations':0,'functional_architecture_basis_refs':[aa]}
        independent=reader.add('json:independent-role-'+str(i),witness)
        review_roles.append({'role':role,'locus_key':key,'source_aa_sha256':'a'*64,'functional_domain_basis_refs':[raw,aa],
                            'hit_ids':[hid],'domain_completeness_review':'REVIEWED_INTACT',
                            'native_profile_role_bindings':[{'hit_id':hid,'profile_name':hits[hid]['profile_name'],'profile_sha256':'b'*64,
                            'model_id':'EXACT_MODEL','role':role,'role_basis_refs':[raw],'independent_functional_role_ref':independent}]})
    candidate={'assembly_accession':'GCF_999999999.1','rm_type':kind,'locus_keys':sorted(set(keys)),'subtype':subtype,'native_candidate_refs':[basis[0]]}
    review={'candidate_id':C.canonical(candidate['assembly_accession'],kind,candidate['locus_keys'])[1],'rm_type':kind,
        'decision':'COMPLETE_PREDICTED','execution':'EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW','functional_evidence_grade':'PREDICTED_ARCHITECTURE_ONLY',
        'unresolved_competing_annotations':0,'curation_reviewer_id':'synthetic-producer','roles':review_roles,'source_context_refs':source_refs,'architecture_basis_refs':basis,
        'compatibility_state':'COMPATIBLE_REVIEWED','compatibility_basis_refs':[basis[0]],
        'modification_dependence_basis':'REVIEWED_FAMILY_SPECIFIC_PREDICTION','modification_dependence_refs':[basis[0]],
        'TypeIV_vs_TypeII_competing_context':'RESOLVED_WITH_EXPLICIT_BASIS'}
    return candidate,review,sources,hits,reader

class IndependentArchitecture(unittest.TestCase):
    def check(self,args):return V.additional_architecture(*args,C.architecture)[2]
    def test_type_I_full_source_domains_accept_missingS_reject(self):
        self.assertEqual(self.check(architecture())['state'],'COMPLETE_PREDICTED')
        with self.assertRaises(ValueError):self.check(architecture(roles=['REASE','MTASE']))
    def test_domain_raw_or_primary_AA_omission_rejects(self):
        for remove in (0,1):
            args=architecture();args[1]['roles'][0]['functional_domain_basis_refs'].pop(remove)
            if remove==0:args[1]['architecture_basis_refs'].remove(args[3]['H0']['raw_ref'])
            with self.assertRaises((ValueError,KeyError)):self.check(args)
    def test_rejected_native_domain_cannot_supply_role(self):
        args=architecture();args[3]['H0']['native_role_threshold_passed']=False
        with self.assertRaises(ValueError):self.check(args)
    def test_pseudo_partial_edge_and_origin_need_actual_resolution(self):
        for flag in ('source_pseudo_any','partial_or_fuzzy','linear_edge','origin_spanning'):
            args=architecture();next(iter(args[2].values()))[flag]=True
            with self.subTest(flag=flag),self.assertRaises(ValueError):self.check(args)
    def test_IIG_fusion_and_recognition_required(self):
        args=architecture('II',['REASE','MTASE'],'IIG',True)
        args[1].update(fusion_architecture_review='REVIEWED_DUAL_FUNCTION_DOMAIN_ARCHITECTURE',fusion_basis_refs=args[1]['architecture_basis_refs'])
        with self.assertRaises(ValueError):self.check(args)
        args[1].update(recognition_architecture_review='REVIEWED_FAMILY_SPECIFIC_RECOGNITION_DOMAIN_BASIS',recognition_basis_refs=args[1]['architecture_basis_refs'])
        self.assertEqual(self.check(args)['state'],'COMPLETE_PREDICTED')
    def test_typeIII_compatibility_typeIV_modification_dependence(self):
        args=architecture('III');args[1]['compatibility_state']='UNRESOLVED'
        with self.assertRaises(ValueError):self.check(args)
        args=architecture('IV');args[1]['modification_dependence_basis']='MTASE_ANNOTATION_ONLY'
        with self.assertRaises(ValueError):self.check(args)
    def test_McrBC_partner_and_LlaJI_context_reject(self):
        with self.assertRaises(ValueError):self.check(architecture('IV',['MOD_DEPENDENT_RECOGNITION','CLEAVAGE','MCRB'],'McrBC'))
        args=architecture('IV');args[1]['TypeIV_vs_TypeII_competing_context']='LlaJI_UNRESOLVED'
        with self.assertRaises(ValueError):self.check(args)
    def test_wrong_exact_model_profile_assignment_rejects(self):
        args=architecture();args[1]['roles'][0]['native_profile_role_bindings'][0]['model_id']='LOOKALIKE_MODEL'
        with self.assertRaises(ValueError):self.check(args)
    def test_native_membership_without_independent_role_review_rejects(self):
        args=architecture();binding=args[1]['roles'][0]['native_profile_role_bindings'][0]
        witness=args[4].ref(binding['independent_functional_role_ref']);witness['native_component_names']=['UNRELATED_COMPONENT']
        with self.assertRaises(ValueError):self.check(args)
        witness['native_component_names']=['EXACT_COMPONENT_MTASE'];witness['reviewer_id']='synthetic-producer'
        with self.assertRaises(ValueError):self.check(args)

class NativeSelection(unittest.TestCase):
    def fixture(self):
        key='GCF_999999999.1|NC_SYNTHETIC.1|L1'
        source={key:{'replicon':'NC_SYNTHETIC.1','derived_linear_order_start_one_based':'101','derived_linear_order_end_one_based':'900'}}
        call={'target.name':key,'seqid':'NC_SYNTHETIC.1','hmm.name':'EXACT_PROFILE','system':'RM_type_I',
              'domain.iE.value':'1.23e-20','hmm.coverage':'0.875','target.coverage':'0.725','start':'101','end':'900','protein.name':'MTase_I'}
        hit={'detector':'PADLOC','locus_key':key,'profile_name':'EXACT_PROFILE','target_length':400,'_numeric_pass':True,
             'domain':{'independent_evalue':'1.23456e-20','hmm_from':'1','hmm_to':'351','profile_length':'400','alignment_from':'1','alignment_to':'291'},
             'native_selected_protein_labels':['MTase_I'],'native_numerical_domain_filter_passed':True,'native_domain_selector_ambiguous':False}
        return source,call,hit
    def invoke(self,hits,source,calls):
        V.native_padloc(hits,HERE,source,SimpleNamespace(records=lambda path:calls))
    def test_independent_rounded_selection_unselected_and_ambiguity(self):
        source,call,hit=self.fixture();hits={'h':deepcopy(hit)}
        self.invoke(hits,source,[{'detector':'PADLOC','native_row_json':json.dumps(call)}]);self.assertTrue(hits['h']['native_role_threshold_passed'])
        hit['native_selected_protein_labels']=[];hits={'h':deepcopy(hit)};self.invoke(hits,source,[]);self.assertFalse(hits['h']['native_role_threshold_passed'])
        hit['native_domain_selector_ambiguous']=True;hits={'h1':deepcopy(hit),'h2':deepcopy(hit)}
        self.invoke(hits,source,[{'detector':'PADLOC','native_row_json':json.dumps(call)}]);self.assertFalse(hits['h1']['native_role_threshold_passed'])
    def test_native_selected_no_original_domain_and_geometry_drift(self):
        for field,value in [('domain.iE.value','1e-2'),('start','102')]:
            source,call,hit=self.fixture();call[field]=value
            with self.assertRaises(ValueError):self.invoke({'h':hit},source,[{'detector':'PADLOC','native_row_json':json.dumps(call)}])

class ExceptionAccounting(unittest.TestCase):
    def test_exception_without_positive_is_NA_not_zero(self):
        for state in V.EXCEPTION_STATES:
            for cell in V.exception_cells('GCF_999999999.1',state):self.assertEqual(M.normalize(cell,cell['assembly_accession'])[1],'NA')
    def test_independent_retained_positive_survives_failed_search(self):
        prior={'rm_type':'II','candidate_counts':{'COMPLETE_PREDICTED':1,'CURATED_PARTIAL':1},'complete_predicted_count':1,
               'curated_partial_count':1,'candidate_ids':['complete','partial']}
        cells=V.exception_cells('GCF_999999999.1','FAILED_RETRYABLE',[prior]);row,value=M.normalize(cells[1],cells[1]['assembly_accession'])
        self.assertEqual(value,'1');self.assertEqual(row['count_lower_bound'],'True');self.assertEqual(row['state'],'FAILED')
    def test_exception_source_full_pin_and_mutation(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            root=Path(d);accession='GCF_999999999.1';source=root/'assemblies'/accession;source.mkdir(parents=True)
            outputs=[]
            for name in (accession+'.faa','locus_crosswalk.tsv','replicon_manifest.json'):
                path=source/name;path.write_text('SYNTHETIC_ONLY\n',encoding='utf-8');outputs.append({'path':name,'bytes':path.stat().st_size,'sha256':V.sha(path)})
            write(source/'build_receipt.json',{'assembly_accession':accession,'identity':{'panel_sha256':V.PANEL_SHA},'output_files':outputs})
            doc={'source_receipt_sha256':V.sha(source/'build_receipt.json'),'source_input_files':{i['path']:i['sha256'] for i in outputs}}
            V.source_exception_binding(accession,doc,{'source':str(root)})
            (source/'locus_crosswalk.tsv').write_text('MUTATED\n',encoding='utf-8')
            with self.assertRaises(ValueError):V.source_exception_binding(accession,doc,{'source':str(root)})
    def test_NOT_RUN_does_not_hide_current_terminal_or_launch(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            root=Path(d);doc={'execution_state':'NOT_RUN','process_closure_state':'NO_ATTEMPT','current_terminal_receipt':None}
            self.assertEqual(V.terminal_exception_binding(root,doc)[1]['native_launch_count'],0)
            write(root/'hidden.launch.json',{})
            with self.assertRaises(ValueError):V.terminal_exception_binding(root,doc)
    def terminal(self,root,closed):
        current={'accession':'GCF_999999999.1','state':'FAILED_RETRYABLE','curation':'NOT_RUN','biological_absence_claim':'NONE',
                 'outputs_preserved':True,'error':'Synthetic failure','owner_nonce':'synthetic-owner','transaction':'transactions/attempt_0001',
                 'owned_closure_proven':closed,'no_native_launch_in_this_invocation':False}
        write(root/'status.json',current);write(root/'transactions/attempt_0001/status.json',current)
        launch={'execution':'ACTUAL_PROCESS_STARTED','new_process_session':True,'signalling':'VERIFIED_KERNEL_PIDFDS_ONLY',
                'child_pid':99999999,'child_start_ticks':123,'command_nonce':'synthetic-command','boot_id':'synthetic-boot'}
        write(root/'execution/test.launch.json',launch)
        pin={'path':'execution/test.launch.json','sha256':V.sha(root/'execution/test.launch.json'),'closure_sha256':None}
        if closed:
            write(root/'execution/test.closure.json',{'command_nonce':'synthetic-command','boot_id':'synthetic-boot','root_exit_code':1,
                  'group_empty':True,'tracked_descendants_empty':True,'survivors':[],'unexplained_pgid_members':[],
                  'signalling':'VERIFIED_KERNEL_PIDFDS_ONLY'})
            pin['closure_sha256']=V.sha(root/'execution/test.closure.json')
        return {'accession':current['accession'],'execution_state':current['state'],'terminal_error':current['error'],
                'current_terminal_receipt':{'path':'status.json','sha256':V.sha(root/'status.json')},'launch_receipts':[pin],
                'process_closure_state':'PROVEN_CLOSED' if closed else 'UNPROVEN_RECONCILIATION_REQUIRED',
                'closure_unresolved_reason':'Synthetic missing closure, no relaunch authorized'}
    def test_failed_terminal_hash_transaction_and_closed_launch(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            root=Path(d);doc=self.terminal(root,True);self.assertEqual(V.terminal_exception_binding(root,doc)[1]['process_closure_state'],'PROVEN_CLOSED')
            write(root/'transactions/attempt_0001/status.json',{'MUTATED':True})
            with self.assertRaises(ValueError):V.terminal_exception_binding(root,doc)
    def test_missing_closure_explicitly_accounted_never_proven(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            root=Path(d);doc=self.terminal(root,False);self.assertEqual(V.terminal_exception_binding(root,doc)[1]['process_closure_state'],'UNPROVEN_RECONCILIATION_REQUIRED')
            doc['process_closure_state']='PROVEN_CLOSED'
            with self.assertRaises(ValueError):V.terminal_exception_binding(root,doc)
    def test_missing_native_launch_inventory_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            root=Path(d);doc=self.terminal(root,True);doc['launch_receipts']=[]
            with self.assertRaises(ValueError):V.terminal_exception_binding(root,doc)
    def test_duplicate_exception_or_success_plus_exception_rejected(self):
        panel=['GCF_'+str(900000000+i)+'.1' for i in range(196)]
        doc={'schema':'RM_ATOMIC_CURATION_EXCEPTION_V1','accession':panel[0],'execution_state':'NOT_RUN','reason':'Synthetic explicit missing runtime'}
        wide,long=M.build(panel,[],[doc]);self.assertEqual(wide[0]['Type_I'],'NA')
        with self.assertRaises(ValueError):M.build(panel,[],[doc,doc])

class IndependentOutputAndGuards(unittest.TestCase):
    def test_actual_qualified_JSON_role_record_and_tamper(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            root=Path(d);roots={alias:root/alias for alias in V.ALIASES}
            for directory in roots.values():directory.mkdir()
            path=roots['reviews']/'independent_role.json';value={'dataset_kind':'SYNTHETIC','role':'REASE','decision':'SYNTHETIC_COMPONENT_ONLY'}
            write(path,value);reader=V.reader_type(C)(root,roots);ref=reader.make_ref(path,'json:',value)
            self.assertEqual(reader.ref(ref),value)
            write(path,{'MUTATED':'ROLE'})
            with self.assertRaises(ValueError):reader.ref(ref)
    def test_independent_serializer_exact_cells_then_zero_tamper(self):
        panel=['GCF_'+str(900000000+i)+'.1' for i in range(196)];cells=[]
        for a in panel:cells.extend(V.exception_cells(a,'NOT_RUN'))
        wide,long=M.build(panel,[])
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            root=Path(d);M.table(root/'matrix',wide,['accession']+['Type_'+t for t in V.TYPES]);M.table(root/'state',long,M.STATE_FIELDS)
            V.compare_serialized(panel,cells,root/'matrix',root/'state',C)
            wide[0]['Type_I']='0';M.table(root/'matrix',wide,['accession']+['Type_'+t for t in V.TYPES])
            with self.assertRaises(ValueError):V.compare_serialized(panel,cells,root/'matrix',root/'state',C)
    def test_production_gate_rejects_synthetic_contract(self):
        with self.assertRaises(ValueError):V.run({'schema':'RM_ATOMIC_INDEPENDENT_CURATION_CHECK_V1','dataset_kind':'SYNTHETIC'})
    def test_duplicate_JSON_path_escapes_rejected(self):
        with self.assertRaises(ValueError):V.pairs([('state','FAILED'),('state','COMPLETE')])
        for member in ('../escape','a\\b','/absolute'):
            with self.assertRaises(ValueError):V.safe(HERE,member)

def main():
    suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'PASS_INDEPENDENT_SYNTHETIC_COMPONENT_TESTS_ONLY' if result.wasSuccessful() else 'FAIL',
            'dataset_kind':'SYNTHETIC','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'biological_jobs':0,'production_curation_certificates_written':0,'actual_architecture_curation':'NOT_RUN',
            'full196_native_integration':'NOT_RUN','checker_sha256':V.sha(HERE/'validate_atomic_curation.py'),
            'independent_core_sha256':V.CORE_SHA,'test_sha256':V.sha(__file__)}
    write(HERE/'independent_synthetic_validation.json',report)
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':main()
