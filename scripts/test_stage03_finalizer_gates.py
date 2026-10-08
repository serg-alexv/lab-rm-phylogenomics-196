"""Isolated Stage03 publication gate fixtures; no Git, network, or biology jobs."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,shutil,sys,tempfile,types

PROJECT=Path(__file__).resolve().parents[1]
SCRIPT=PROJECT/'scripts/finalize_stage03.py'
OUT=PROJECT/'.work/stage03_finalizer_adopted_tests'
OUT.mkdir(parents=True,exist_ok=True)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(data if isinstance(data,bytes) else data.encode())
def js(p,v):write(p,json.dumps(v,indent=2)+'\n')
def read(p):return json.loads(Path(p).read_text())
def forbidden(*a,**k):raise AssertionError('Git/network/production operation forbidden in fixtures')

cases=[]
archives=[]
def mock_zip(path,files,guide):
    rows=[(Path(p),name) for p,name in files]
    assert all(p.is_file() for p,name in rows)
    assert len({name for p,name in rows})==len(rows)
    archives.append({'asset_name':path.name,'members':[name for p,name in rows]})
    write(path,b'SYNTHETIC MOCK ZIP; NOT BIOLOGICAL OUTPUT\n')
    return {'asset_name':path.name,'bytes':path.stat().st_size,'sha256':digest(path),'payload_members':len(rows)+1}

def load(root):
    w=types.ModuleType('production_resume');w.R=root;w.WORK=root/'.work';w.digest=digest;w.js=js;w.atomic=write
    for n in ('run','status','now'):setattr(w,n,forbidden)
    publication=types.ModuleType('workflow_publication');publication.commit=forbidden
    publication.check=lambda paths:all((root/p).is_file() for p in paths) or forbidden()
    portable=types.ModuleType('portable_release');portable.make_zip=mock_zip;portable.publish_frozen=forbidden
    for name,m in [('production_resume',w),('workflow_publication',publication),('portable_release',portable)]:sys.modules[name]=m
    spec=importlib.util.spec_from_file_location('isolated_stage03_finalizer',SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def fixture(root,blocked=False):
    m=load(root);panel=[f'GCF_{i:09d}.1' for i in range(1,197)]
    write(root/'config/approved_accessions.txt','\n'.join(panel)+'\n')
    js(root/'config/approval.json',{'human_approval':'APPROVED_FOR_SEQUENCE_ANALYSIS','approved_assembly_count':196,
                                 'pilot':False,'panel_accessions_sha256':digest(root/'config/approved_accessions.txt')})
    js(root/'config/host_primary_stage03_v1.json',{'fixture_only':True})
    write(root/'.tools/Firmicutes.hmm','SYNTHETIC PROFILE FIXTURE; NO SEARCH\n')
    for n in ['validate_stage03_markers.py','validate_locus_inputs.py','build_locus_inputs.py','stage03_markers.py','gtotree_evidence.py']:
        write(root/'scripts'/n,'# synthetic provenance fixture: '+n+'\n')
    js(m.STAGE02_VALIDATION/'validation_summary.json',{'fixture_only':True})
    builder={'panel_sha256':digest(root/'config/approved_accessions.txt'),'builder_source_sha256':digest(root/'scripts/build_locus_inputs.py'),
             'stage02_validation_summary_sha256':digest(m.STAGE02_VALIDATION/'validation_summary.json')}
    js(m.SOURCE/'construction_summary.json',{'status':'SOURCE_LOCUS_INPUTS_CONSTRUCTED','constructed_assemblies':196,'identity':builder})
    audit=[{'assembly_accession':acc,'status':'PASS_SOURCE_LOCUS_INPUT_TRACEABILITY','source_gbff_cds_loci':119,
            'source_context_loci':119,'protein_bearing_loci':119,'gene_only_pseudogenes':0,'gbff_replicons':1} for acc in panel]
    js(m.SOURCE_VALIDATION/'assembly_audit.json',audit)
    source={'status':'PASS_SOURCE_LOCUS_INPUT_TRACEABILITY','required_assemblies':196,'assemblies_audited':196,'assemblies_passed':196,
            'complete_exact196_accounting':True,'failed_assemblies':[],'global_errors':[],'panel_sha256':builder['panel_sha256'],
            'validator_source_sha256':digest(root/'scripts/validate_locus_inputs.py'),'builder_identity':builder}
    for f in ['source_gbff_cds_loci','source_context_loci','protein_bearing_loci','gene_only_pseudogenes','gbff_replicons']:
        source[f]=sum(row[f] for row in audit)
    js(m.SOURCE_VALIDATION/'validation_summary.json',source)
    write(m.MARKERS/'primary_marker_order.txt','synthetic_marker\n')
    write(m.MARKERS/'accepted_sequence_manifest.tsv','fixture_only\n')
    js(m.PUBLIC/'host_profile_scope_review.json',{'fixture_only':True})
    identity={'approved_accessions_sha256':builder['panel_sha256'],'config_sha256':digest(root/'config/host_primary_stage03_v1.json'),
              'profile_sha256':digest(root/'.tools/Firmicutes.hmm'),'runner_sha256':digest(root/'scripts/stage03_markers.py'),
              'wrapper_sha256':digest(root/'scripts/gtotree_evidence.py'),'source_construction_summary_sha256':digest(m.SOURCE/'construction_summary.json'),
              'stage02_validation_summary_sha256':builder['stage02_validation_summary_sha256'],
              'independent_source_locus_validation_summary_sha256':digest(m.SOURCE_VALIDATION/'validation_summary.json')}
    js(m.MARKERS/'input_identity.json',identity)
    js(m.MARKERS/'inventory_summary.json',{'execution':'COMPLETED_ALL196_SEARCHES','approved_assemblies':196,'successful_searches':196,
       'profiles_searched':119,'marker_cells':196*119,'identity':identity,'inventory':'SCIENTIFIC_BLOCKER' if blocked else 'MARKER_INVENTORY_CONSTRUCTED',
       'blocker_count':1 if blocked else 0})
    v={'status':'PASS_MARKER_SOURCE_AND_FIXED_FILTERS','scientific_stage_status':'SCIENTIFIC_BLOCKER' if blocked else 'PASS_HOST_MARKER_INVENTORY',
       'approved_assemblies':196,'independently_verified_searches':196,'profiles_searched':119,'marker_cells':196*119,
       'producer_identity':identity,'validator_source_sha256':digest(root/'scripts/validate_stage03_markers.py'),
       'source_reader_sha256':digest(root/'scripts/validate_locus_inputs.py'),'primary_markers':119,'accepted_marker_sequences':196*119,
       'scientific_blockers':[{'gate':'POST_OCCUPANCY_GENOME_RECOVERY','assembly_accession':panel[0]}] if blocked else [],
       'same_locus_multiple_profile_candidates':0,'host_function_review':{'review_sha256':digest(m.PUBLIC/'host_profile_scope_review.json'),
       'profiles_accounted':119,'state':'PENDING_ACCEPTED_SOURCE_REVIEW' if blocked else 'REVIEWED_CONSERVED_HOST_PROFILE_SCOPE_WITH_DOCUMENTED_LIMITS',
       'unresolved_rm_candidates':None if blocked else 0}}
    for k,p in [('inventory_summary_sha256',m.MARKERS/'inventory_summary.json'),('accepted_sequence_manifest_sha256',m.MARKERS/'accepted_sequence_manifest.tsv'),
                ('primary_marker_order_sha256',m.MARKERS/'primary_marker_order.txt'),('config_sha256',root/'config/host_primary_stage03_v1.json'),('profile_sha256',root/'.tools/Firmicutes.hmm')]:v[k]=digest(p)
    js(m.VALIDATION/'validation_summary.json',v)
    return m,v,panel

def case(name,operation):
    with tempfile.TemporaryDirectory(prefix='isolated_',dir=OUT) as td:operation(Path(td))
    cases.append({'name':name,'status':'PASS'})
def expect_failure(fn,text=None):
    try:fn()
    except (ValueError,RuntimeError,KeyError) as e:
        if text:assert text in str(e),(text,str(e))
    else:raise AssertionError('Expected explicit rejection')
def pass_fixture(r):
    m,v,p=fixture(r);assert m.scientific_state(False)==(v,True)
def blocker_fixture(r):
    m,v,p=fixture(r,True);assert m.scientific_state(True)==(v,False)
    expect_failure(lambda:m.scientific_state(False),'SCIENTIFIC_BLOCKER')
case('coherent_exact196_resolved_fixture_passes',pass_fixture)
case('numeric_blocker_pending_function_review_only_explicit_evidence_passed_false',blocker_fixture)

def mutate_provenance(r,key):
    m,v,p=fixture(r);path=m.provenance_paths()[key];write(path,path.read_bytes()+b'\n')
    expect_failure(lambda:m.scientific_state(False))
for key in ['panel_sha256','approval_sha256','config_sha256','profile_sha256','marker_validator_source_sha256',
            'source_validator_source_sha256','builder_source_sha256','runner_source_sha256','wrapper_source_sha256',
            'source_construction_summary_sha256','source_validation_summary_sha256','stage02_validation_summary_sha256',
            'accepted_sequence_manifest_sha256','primary_marker_order_sha256','host_profile_scope_review_sha256']:
    if key=='approval_sha256':
        def approval(r):
            m,v,p=fixture(r);a=read(r/'config/approval.json');a['pilot']=True;js(r/'config/approval.json',a)
            expect_failure(lambda:m.scientific_state(False),'Approved full196')
        case('changed_approval_to_pilot_rejected',approval)
    else:case('stale_'+key+'_rejected',lambda r,key=key:mutate_provenance(r,key))

def conflicting(r,field,value):
    m,v,p=fixture(r);v[field]=value;js(m.VALIDATION/'validation_summary.json',v)
    expect_failure(lambda:m.scientific_state(False),'PASS label conflicts')
case('pass_with_numeric_blocker_rejected',lambda r:conflicting(r,'scientific_blockers',[{'gate':'RECOVERY'}]))
case('pass_with_duplicate_full_protein_signal_rejected',lambda r:conflicting(r,'same_locus_multiple_profile_candidates',1))
def pending(r):
    m,v,p=fixture(r);v['host_function_review']['state']='PENDING';js(m.VALIDATION/'validation_summary.json',v)
    expect_failure(lambda:m.scientific_state(False),'PASS label conflicts')
case('pass_with_pending_function_review_rejected',pending)
def audit_change(r,mode):
    m,v,p=fixture(r);a=read(m.SOURCE_VALIDATION/'assembly_audit.json')
    if mode=='missing':a.pop()
    elif mode=='duplicate':a[-1]=a[0]
    elif mode=='reordered':a.reverse()
    else:a[0]['protein_bearing_loci']+=1
    js(m.SOURCE_VALIDATION/'assembly_audit.json',a);expect_failure(lambda:m.scientific_state(False),'Flat source')
for mode in ['missing','duplicate','reordered','wrong_count']:case('source_audit_'+mode+'_rejected',lambda r,mode=mode:audit_change(r,mode))

def freeze(m,v):
    p=m.scientific_provenance(v);js(m.PUBLIC/'asset_manifest.json',{'scientific_validation':v['scientific_stage_status'],'scientific_provenance':p})
    shutil.copyfile(m.VALIDATION/'validation_summary.json',m.PUBLIC/'marker_validation_summary.json');js(m.PUBLIC/'scientific_provenance.json',p)
def unchanged(r):
    m,v,p=fixture(r,True);freeze(m,v);m.require_frozen_scientific_provenance(v)
case('unchanged_frozen_blocked_release_retry_accepted',unchanged)
def changed_status(r):
    m,v,p=fixture(r,True);freeze(m,v);v['scientific_stage_status']='PASS_HOST_MARKER_INVENTORY'
    js(m.VALIDATION/'validation_summary.json',v);expect_failure(lambda:m.require_frozen_scientific_provenance(v),'distinct reviewed publication')
case('blocked_frozen_payload_cannot_be_relabelled_pass',changed_status)
def changed_report(r):
    m,v,p=fixture(r);freeze(m,v);v['completed_at_utc']='new fixture report time';js(m.VALIDATION/'validation_summary.json',v)
    expect_failure(lambda:m.require_frozen_scientific_provenance(v),'Frozen Stage03 scientific outcome/bytes changed')
case('changed_executed_report_bytes_reject_plan_reuse',changed_report)
def changed_public(r):
    m,v,p=fixture(r);freeze(m,v);write(m.PUBLIC/'marker_validation_summary.json','{}\n')
    expect_failure(lambda:m.require_frozen_scientific_provenance(v),'Frozen public scientific evidence')
case('changed_public_report_bytes_reject_plan_reuse',changed_public)

def coverage(r):
    m,v,panel=fixture(r,True);archives.clear()
    for n in m.COMPACT:
        if not (m.MARKERS/n).exists():write(m.MARKERS/n,'SYNTHETIC ISOLATED FIXTURE ONLY\n')
    scripts=['build_locus_inputs.py','validate_locus_inputs.py','stage03_source_inputs.py','stage03_validate_source.py','stage03_markers.py',
             'gtotree_evidence.py','stage03_run_markers.py','run_stage03_host.sh','validate_stage03_markers.py','record_host_profile_scope_review.py',
             'finalize_stage03.py','portable_release.py','test_portable_release.py','test_portable_publication.py','stage03_validate_markers.py',
             'workflow_publication.py','production_resume.py','wsl_project.sh']
    for n in scripts:
        if not (r/'scripts'/n).exists():write(r/'scripts'/n,'# SYNTHETIC ISOLATED FIXTURE ONLY\n')
    reports=['source_construction_summary.json','marker_start_resources.json','start_resources.json','source_process_resource_snapshot.json',
             'source_locus_synthetic_tests.json','source_locus_validator_synthetic_tests.json','marker_filter_synthetic_tests.json',
             'marker_validator_synthetic_tests.json','hmm_evidence_wrapper_synthetic_tests.txt','portable_archive_synthetic_tests.json',
             'portable_publication_independent_tests.json','PORTABLE_PUBLICATION_REVIEW.md']
    for n in reports:write(m.PUBLIC/n,'SYNTHETIC ISOLATED FIXTURE ONLY\n')
    for acc in panel:
        write(m.SOURCE/'assemblies'/acc/'primary_ncbi_protein.faa','>synthetic_fixture\nM\n')
        write(m.MARKERS/'searches'/acc/'attempt_0001/temporary/uniq_hmm_names.tmp','SYNTHETIC TEMP EVIDENCE\n')
        write(m.MARKERS/'searches'/acc/'attempt_0001/cache.ssi','SYNTHETIC CACHE\n')
    paths=m.prepare(v,False);assert len(archives)==12
    inventory=next(a for a in archives if a['asset_name']=='stage03-full196-marker-inventory.zip')['members']
    assert 'independent_source_validation/assembly_audit.json' in inventory
    assert 'independent_source_validation/validation_summary.json' in inventory
    assert 'independent_marker_validation/validation_summary.json' in inventory
    all_names=[n for a in archives for n in a['members']]
    assert sum(n.endswith('uniq_hmm_names.tmp') for n in all_names)==196
    assert not any(n.endswith(('.tmp.txt','.ssi')) for n in all_names)
    methods=next(a for a in archives if a['asset_name']=='stage03-methods-and-reports.zip')['members']
    for n in ['config/approved_accessions.txt','config/approval.json','scripts/stage03_validate_markers.py','scripts/test_portable_publication.py',
              'reports/stage03/portable_publication_independent_tests.json','reports/stage03/PORTABLE_PUBLICATION_REVIEW.md',
              'reports/stage03/source_locus_assembly_audit.json','reports/stage03/scientific_provenance.json']:
        assert n in methods,n
    assert read(m.PUBLIC/'asset_manifest.json')['scientific_validation']=='SCIENTIFIC_BLOCKER'
    assert digest(m.PUBLIC/'marker_validation_summary.json')==digest(m.VALIDATION/'validation_summary.json')
    assert digest(m.PUBLIC/'source_locus_assembly_audit.json')==digest(m.SOURCE_VALIDATION/'assembly_audit.json')
    assert 'reports/stage03/SHA256SUMS.txt' in paths
case('twelve_mock_batches_complete_flat_audit_methods_and_original_tmp_names',coverage)

report={'status':'PASS_ISOLATED_STAGE03_FINALIZER_GATES','completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'finalizer_source_sha256':digest(SCRIPT),'test_source_sha256':digest(__file__),'tests':len(cases),'cases':cases,
        'biological_execution':'NOT_RUN','git_operations':'NOT_RUN','network_publication':'NOT_RUN',
        'fixtures':'Exact196 synthetic hash-bound records; ZIP writer mocked. Actual portable ZIP validation is separately tested.',
        'command':'python .work/review2/test_stage03_finalizer_gates.py'}
js(OUT/'stage03_finalizer_review.json',report)
write(OUT/'STAGE03_FINALIZER_REVIEW.md',f'# Stage03 finalizer independent isolated checks\n\n{len(cases)} checks passed against finalizer SHA256 `{digest(SCRIPT)}`.\n\n'
      'Tests cover exact196 source accounting, current code/input/profile/review hash bindings, unresolved scientific gate rejection, '
      'numeric blocker evidence with pending function review, immutable retry provenance, complete flat audit inclusion and original `.tmp` names. '
      'Twelve archive batches were inspected through a mocked ZIP writer; biological jobs, Git and network publication did not run.\n\n'
      'Command: `python .work/review2/test_stage03_finalizer_gates.py`. Full biological validation and real Release readback remain separate production prerequisites.\n')
print(json.dumps({'status':report['status'],'tests':len(cases),'finalizer_source_sha256':report['finalizer_source_sha256']}))
