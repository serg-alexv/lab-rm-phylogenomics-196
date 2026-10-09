#!/usr/bin/env python3
"""Independently reopen native/source/domain/review evidence for atomic Stage5.

Imports only a separately authored, hash-pinned retained independent checker.
Never imports the curation producer, serializer, architecture reducer or runner.
All196 entries must have actual reviewed results or independently bound explicit
execution exceptions. An exception never becomes detector success or absence.
No classifier/search, installed-R execution, WSL startup or DB download occurs.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,re,time
from collections import Counter,defaultdict
from pathlib import Path,PurePosixPath

HERE=Path(__file__).resolve().parent
CORE_SHA='2183d3459254c3acf9bc1f8fab14a240e9fc47c05b68592773438eb2ed086612'
SCOPE_SHA='6284203055ada645b3f6a8023e71e57a5fe8156bc9d4dffcc72da7614f3b30be'
PADLOC_R_SHA='d21ba942e80720d80027aa1740d756322560feaeb168bfa2890640d88950d4c0'
PADLOC_HMM_SHA='a03df990d47ef40d2573a04d9a0f513e70999c3b9104216e3f6656a9bef8d5da'
PANEL_SHA='85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'
SOURCE_VALIDATION_SHA='260420038849dc8509a2e5e99c48a6c9eba7c2e06953f4a4fc865a408d5481eb'
SOURCE_PINS_SHA='a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84'
ALIASES=('source','bundle','execution','inventory','policy','models','padloc_db','environment','reviews')
TYPES=('I','II','III','IV')
EXCEPTION_STATES={'FAILED_FATAL','FAILED_RETRYABLE','DEFERRED_RESOURCE','NOT_RUN'}
DEPENDENCY_PINS={'stage05_architecture_policy.py':'942edc6312d1490afc681c42ab1e32d67c92373024acca7360918ed3eeaef3e4',
                 'retained/stage05_curation_adapter.py':'cbaf00aee2d9961eaaa0be76b589315014a88183e3f7f8ed1f2ff234e6418177',
                 'retained/stage05_evidence.py':'7582d1a37980d89669159e3926f5b459e8d68abfde530ea0b8fc13b991d4363e',
                 'pinned_model_candidate_scope.json':SCOPE_SHA}

def must(ok,text):
    if not ok:raise ValueError(text)

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def pairs(items):
    result={}
    for key,value in items:must(key not in result,'Duplicate JSON field: '+key);result[key]=value
    return result

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=pairs)

def packed(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def objsha(value):return hashlib.sha256(packed(value).encode()).hexdigest()

def safe(root,name):
    pp=PurePosixPath(name);must(name and pp.as_posix()==name and not pp.is_absolute() and '..' not in pp.parts and '\\' not in name,'Unsafe native/manifest member')
    p=Path(root).joinpath(*pp.parts).resolve();must(Path(root).resolve() in p.parents,'Member escaped root');return p

def verify_released_source(accession,root,source_receipt):
    """Independently reopen fixed published source pins; no producer import."""
    pinfile=HERE/'accepted_source_pins.json'
    must(sha(pinfile)==SOURCE_PINS_SHA,'Independent accepted-source pin bytes differ')
    published=read(pinfile)
    must(published.get('schema')=='STAGE05_ACCEPTED_SOURCE_PINS_V1'
         and published.get('approved_accessions_sha256')==PANEL_SHA
         and len(published['source_receipts'])==196 and accession in published['source_receipts'],
         'Independent released full196 source selection differs')
    witness=published['source_receipts'][accession]
    for relative,expected in published['accepted_files'].items():
        must(sha(safe(root,relative))==expected,'Independent canonical accepted source control mismatch: '+relative)
    must(Path(source_receipt).stat().st_size==witness['bytes']
         and sha(source_receipt)==witness['sha256'],'Independent source receipt differs from released member')
    return published,witness

def verify_source_acceptance(identity,accession,root,source_receipt):
    published,witness=verify_released_source(accession,root,source_receipt)
    must(identity.get('schema')=='STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2'
         and identity.get('source_receipt_sha256')==witness['sha256']
         and identity.get('source_acceptance')=={'source_pins_sha256':SOURCE_PINS_SHA,
             'accepted_files':published['accepted_files'],'released_source_member':witness},
         'Independent V2 released-source acceptance mismatch')

def core():
    path=HERE/'retained/independent_curated_v2.py';must(sha(path)==CORE_SHA,'Retained independent checker changed')
    spec=importlib.util.spec_from_file_location('separate_independent_curated_core',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def native_provenance(contract):
    """Rehash the actual retained scientific runtime once per full-panel audit."""
    for key in ('atomic_runner','supervisor'):
        must(sha(contract[key+'_source'])==contract[key+'_sha256'],'Actual native orchestration provenance changed: '+key)
    path=contract['runtime_manifest'];must(path and sha(path)==contract['runtime_manifest_sha256'],'Actual native runtime pin missing/changed')
    manifest=read(path)
    must(manifest.get('schema')=='STAGE05_PINNED_RUNTIME_V1' and manifest.get('versions')==
         {'mdmparis-defense-finder':'3.0.0','MacSyFinder':'2.1.4','pyhmmer':'0.12.3','pyrodigal':'3.7.1'},'Actual retained scientific runtime schema/versions differ')
    must(manifest['files']['environment_dir'].get('bin/padloc.R')==PADLOC_R_SHA
         and manifest['files']['padloc_db'].get('hmm/padlocdb.hmm')==PADLOC_HMM_SHA,
         'Actual PADLOC implementation/compiled5027 database pin differs')
    for native,alias in [('environment_dir','environment'),('models_dir','models'),('padloc_db','padloc_db')]:
        must(Path(manifest['roots'][native]).resolve()==Path(contract[alias]).resolve(),'Actual runtime manifest read root differs')
        files=manifest['files'][native];must(isinstance(files,dict) and files,'Empty native runtime file manifest')
        for name,digest in files.items():must(sha(safe(contract[alias],name))==digest,'Installed runtime/model bytes differ: '+name)
    return sha(path)

def reader_type(C):
    class AtomicReader(C.Reader):
        def __init__(self,root,roots):
            must(tuple(roots)==ALIASES,'Exact qualified read roots required')
            super().__init__(root,list(roots.values()));self.roots={k:Path(v).resolve() for k,v in roots.items()}
        def path(self,name):
            must(isinstance(name,str) and name,'Missing evidence path')
            if '::' in name:
                must(name.count('::')==1,'Malformed qualified reference');alias,relative=name.split('::')
                must(alias in self.roots,'Unknown qualified root');p=safe(self.roots[alias],relative)
            else:
                # Retained checker constructs absolute internal source/native paths.
                p=Path(name).resolve();must(any(r in p.parents for r in self.roots.values()),'Internal read escaped exact evidence roots')
            must(p.is_file() and not any(x in ('.git','.private_run') for x in p.parts),'Missing/private scientific evidence');return p
        def directory(self,name):
            p=Path(name).resolve();must(p.is_dir() and any(r==p or r in p.parents for r in self.roots.values()),'Native directory escaped roots');return p
        def make_ref(self,path,locator,record):
            p=Path(path).resolve();choices=[(a,r) for a,r in self.roots.items() if r in p.parents];must(choices,'Reference outside roots')
            alias,root=max(choices,key=lambda item:len(item[1].parts))
            return {'path':alias+'::'+p.relative_to(root).as_posix(),'sha256':self.digest(p),'record_locator':locator,'record_sha256':objsha(record)}
    return AtomicReader

def native_padloc(hits,inventory,sources,C):
    """Independent selected-native-row witness, not a producer helper import."""
    observed=defaultdict(list)
    for r in C.records(inventory/'all_native_system_candidate_rows.tsv'):
        if r['detector']!='PADLOC':continue
        call=json.loads(r['native_row_json']);key=call['target.name'];s=sources[key]
        must(call['seqid']==s['replicon'] and int(call['start'])==int(s['derived_linear_order_start_one_based'])
             and int(call['end'])==int(s['derived_linear_order_end_one_based']),'Native PADLOC source coordinate selector differs')
        found=[]
        for hid,h in hits.items():
            if h['detector']!='PADLOC' or h['locus_key']!=key or h['profile_name']!=call['hmm.name']:continue
            d=h['domain'];hcov=round((int(d['hmm_to'])-int(d['hmm_from']))/int(d['profile_length']),3)
            tcov=round((int(d['alignment_to'])-int(d['alignment_from']))/h['target_length'],3)
            native_ie=float('%.3g'%float(d['independent_evalue']))
            if native_ie==float(call['domain.iE.value']) and abs(hcov-float(call['hmm.coverage']))<=1e-12 and abs(tcov-float(call['target.coverage']))<=1e-12:found.append(hid)
        must(found,'Actual PADLOC selected CSV row lacks original native domain witness')
        for hid in found:observed[hid].append((call['system'],len(found),call.get('protein.name','')))
    for hid,h in hits.items():
        if h['detector']!='PADLOC':continue
        selected=observed[hid];h['native_selected_model_ids']=sorted({model for model,n,label in selected if n==1})
        labels=sorted({label for model,n,label in selected if n==1})
        must(h.get('native_selected_protein_labels')==labels and h.get('native_numerical_domain_filter_passed')==h['_numeric_pass'],
             'PADLOC selected native labels/numerical projection differ')
        h['native_selected_protein_labels']=labels
        ambiguous=any(n>1 for model,n,label in selected)
        must(h.get('native_domain_selector_ambiguous')==ambiguous,'PADLOC selector ambiguity was erased')
        h['native_role_threshold_passed']=h['_numeric_pass'] and bool(h['native_selected_model_ids'])

def candidates(reader,inventory,execution,sources,prepared,scope,roots,C):
    """Independent exact native-row multiplicity and candidate grouping audit."""
    lookup={(e['detector'],e['model_id']):e for e in scope['models']};must(len(lookup)==39,'Exact frozen model scope differs')
    rows=C.records(inventory/'all_native_system_candidate_rows.tsv');byfile=defaultdict(list);groups={}
    for index,row in enumerate(rows,1):
        key=row['locus_key'];must(key in sources and row['assembly_accession']==prepared['assembly_accession'],'Candidate source absent')
        native=json.loads(row['native_row_json']);path=safe(execution,row['raw_file']);must(sha(path)==row['raw_file_sha256'],'Actual candidate table changed')
        original={k:v for k,v in native.items() if k not in ('assembly_accession','source_replicon','locus_key','protein_accession')}
        byfile[path].append((row['detector'],original));source=sources[key]
        if row['detector']=='PADLOC':
            must(native['target.name']==key and native['seqid']==source['replicon'] and native['system']==row['model_fqn'],'PADLOC actual source/model mismatch')
            gid=native['system.number'];kind='PADLOC_NATIVE_SYSTEM'
        else:
            must(row['detector']=='DefenseFinder' and native['hit_id']==source['df_bundle_target_id']
                 and native['replicon']==source['df_bundle_replicon_name'] and int(native['hit_pos'])==int(source['df_bundle_sequence_rank'])
                 and native['model_fqn']==row['model_fqn'],'DF actual source/model/order mismatch')
            rejected=row['native_table']=='rejected_candidates.tsv';gid=native['candidate_id'] if rejected else native['sys_id'];kind='REJECTED_NATIVE_CANDIDATE' if rejected else 'NATIVE_SYSTEM_CANDIDATE'
        identity=(row['detector'],str(path.parent),row['model_fqn'],gid,kind,source['replicon'])
        g=groups.setdefault(identity,{'loci':set(),'rows':[]});g['loci'].add(key);g['rows'].append(row)
    for path,entries in byfile.items():
        detector=entries[0][0];native=C.records(path,',' if detector=='PADLOC' else '\t',detector!='PADLOC')
        must(Counter(objsha(r) for r in native)==Counter(objsha(r) for detector,r in entries),'Native row multiplicity differs from inventory')
    known={};unknown=[]
    for identity,g in groups.items():
        detector,_,model,gid,kind,rep=identity;entry=lookup.get((detector,model))
        if entry is None:unknown.append((identity,g));continue
        definition=(roots['padloc_db']/'sys'/entry['source_member'].split('/sys/',1)[1] if detector=='PADLOC' else
                    roots['models']/model.split('/',1)[0]/'definitions'/(model.split('/',1)[1]+'.xml'))
        must(sha(definition)==entry['source_sha256'],'Frozen exact native model definition differs')
        ident,cid=C.canonical(prepared['assembly_accession'],entry['proposed_type'],sorted(g['loci']))
        x=known.setdefault(cid,{'identity':ident,'detectors':set(),'subtypes':set(),'rows':[]})
        x['detectors'].add(detector);x['subtypes'].add(entry['subtype']);x['rows']+=g['rows']
    qs=[q for q in prepared['queue'] if q['kind']=='NATIVE_CANDIDATE'];qmap={q['evidence']['candidate_id']:q for q in qs}
    must(len(qmap)==len(qs) and set(qmap)==set(known),'Native architecture queue omission/duplicate')
    for cid,x in known.items():
        q=qmap[cid];a=q['evidence'];resolved=reader.refs(q['actual_evidence_refs'])
        must(all(a[k]==v for k,v in x['identity'].items()) and a['detectors']==sorted(x['detectors'])
             and a['subtypes']==sorted(x['subtypes'],key=str),'Exact type/locus/model dedup differs')
        must(a['subtype_conflict']==(len(x['subtypes'])>1) and a['subtype']==(next(iter(x['subtypes'])) if len(x['subtypes'])==1 else None),'Subtype conflict erased')
        available=Counter(objsha(r) for r in resolved);wanted=Counter(objsha(r) for r in x['rows'])
        must(all(available[k]>=n for k,n in wanted.items()),'Actual native candidate rows omitted from review basis')
        overlaps=sorted(other for other,y in known.items() if other!=cid and set(y['identity']['locus_keys'])&set(x['identity']['locus_keys']))
        must(a['overlapping_candidate_ids']==overlaps,'Candidate overlap context omitted')
    uq=[q for q in prepared['queue'] if q['kind']=='NATIVE_MODEL_CONTEXT'];must(len(uq)==len(unknown),'Unmapped native groups omitted')
    for identity,g in unknown:
        detector,_,model,gid,kind,rep=identity
        matches=[q for q in uq if q['evidence']['detector']==detector and q['evidence']['model_fqn']==model
                 and q['evidence']['native_group_id']==gid and q['evidence']['native_call_class']==kind
                 and q['evidence']['locus_keys']==sorted(g['loci']) and q['evidence']['raw_rows']==g['rows']]
        must(len(matches)==1,'Unmapped candidate group differs');reader.refs(matches[0]['actual_evidence_refs'])

def multipart_family(candidate,review,sources,hits,reader):
    """Separately rederive the exceptional family architecture from opened facts."""
    f=review.get('type_ii_family_architecture')
    if f is None:return False
    must(candidate['rm_type']=='II' and f.get('schema')=='RM_MULTIPART_TYPE_II_FAMILY_ARCHITECTURE_V1'
         and f.get('architecture')=='FUSED_RM_SEPARATE_SPECIFICITY','Unknown multipart TypeII review')
    must(isinstance(f.get('family_id'),str) and 0<len(f['family_id'].strip())<=200
         and f.get('reviewed_subtype') in ('IIB','IIG','UNRESOLVED_TYPE_II_SUBTYPE'),'Family/subtype review missing')
    rm=f.get('rm_locus_key');s=f.get('specificity_locus_key')
    must(rm!=s and set(candidate['locus_keys'])=={rm,s},'Exceptional family exact two-gene context differs')
    relevant=[r for r in review['roles'] if r['role'] in ('REASE','MTASE','SPECIFICITY')]
    assigned={role:{r['locus_key'] for r in relevant if r['role']==role} for role in ('REASE','MTASE','SPECIFICITY')}
    must(assigned=={'REASE':{rm},'MTASE':{rm},'SPECIFICITY':{s}},'Exceptional family fused RM/separate S roles missing')
    must(review.get('fusion_architecture_review')=='REVIEWED_SUPPORTED_TYPE_II_FUSION','Unsupported multipart fusion')
    reader.refs(review.get('fusion_basis_refs'))
    must(review.get('recognition_architecture_review')=='REVIEWED_FAMILY_SPECIFIC_RECOGNITION_DOMAIN_BASIS','Multipart recognition basis missing')
    reader.refs(review.get('recognition_basis_refs'));reader.refs(f.get('primary_family_basis_refs'))
    w=reader.ref(f['independent_family_review_ref'])
    must(w.get('schema')=='RM_MULTIPART_TYPE_II_FAMILY_REVIEW_V1'
         and w.get('execution')=='EXECUTED_INDEPENDENT_SOURCE_DOMAIN_FAMILY_REVIEW'
         and w.get('decision')=='SUPPORTED_FUSED_RM_SEPARATE_SPECIFICITY'
         and w.get('independent_of_curation_producer') is True,'Family architecture lacks separately executed review')
    ids=sorted({hid for r in relevant for hid in r['hit_ids']})
    facts={'assembly_accession':candidate['assembly_accession'],'candidate_id':review['candidate_id'],
           'family_id':f['family_id'],'reviewed_subtype':f['reviewed_subtype'],'rm_locus_key':rm,'specificity_locus_key':s,
           'rm_source_aa_sha256':sources[rm]['primary_faa_sequence_sha256'],'specificity_source_aa_sha256':sources[s]['primary_faa_sequence_sha256'],
           'evidence_hit_ids':ids,'native_model_ids':sorted({b['model_id'] for r in relevant for b in r['native_profile_role_bindings']}),
           'native_candidate_ref_sha256':sorted(objsha(ref) for ref in candidate['native_candidate_refs']),
           'primary_family_basis_refs':f['primary_family_basis_refs']}
    must(all(w.get(k)==v for k,v in facts.items()),'Family interpretation source/native context binding differs')
    must(isinstance(w.get('reviewer_id'),str) and w['reviewer_id'].strip() and w['reviewer_id']!=review['curation_reviewer_id'],'Independent family attribution missing')
    must(isinstance(w.get('family_architecture_basis_statement'),str) and 0<len(w['family_architecture_basis_statement'].strip())<=8000
         and w.get('unresolved_competing_type_or_architecture_interpretations')==0,'Unexplained/competing TypeII family architecture')
    opened=reader.refs(w.get('basis_refs'))
    must(all(hits[hid]['raw_ref'] in w['basis_refs'] for hid in ids),'Family review omitted exact role-domain evidence')
    for key in (rm,s):
        must(any(ref['record_locator']=='fasta:'+key and value=={'target_id':key,'sequence':sources[key]['_sequence']}
                 for ref,value in zip(w['basis_refs'],opened)),'Family review omitted exact RM/S primary amino acids')
    return True

def additional_architecture(candidate,review,sources,hits,reader,original):
    for role in review.get('roles',[]):
        bindings=role.get('native_profile_role_bindings',[])
        must(len(bindings)==len(role['hit_ids']) and {b['hit_id'] for b in bindings}==set(role['hit_ids']),'Exact role/profile evidence missing')
        for b in bindings:
            h=hits[b['hit_id']];modelids={m.get('model_fqn',m.get('model')) for m in h['native_model_roles']}
            must(b['profile_name']==h['profile_name'] and b['profile_sha256']==h['profile_sha256'] and b['model_id'] in modelids and b['role']==role['role'],'Role assigned from wrong profile/model')
            reader.refs(b['role_basis_refs'])
            witness=reader.ref(b['independent_functional_role_ref'])
            must(witness.get('schema')=='RM_FUNCTIONAL_DOMAIN_ROLE_REVIEW_V1'
                 and witness.get('execution')=='EXECUTED_INDEPENDENT_SOURCE_DOMAIN_ROLE_REVIEW'
                 and witness.get('decision')=='SUPPORTED_PREDICTED_ROLE' and witness.get('independent_of_curation_producer') is True,
                 'Native model membership alone cannot establish a functional role')
            must(isinstance(review.get('curation_reviewer_id'),str) and review['curation_reviewer_id'].strip()
                 and isinstance(witness.get('reviewer_id'),str) and witness['reviewer_id'].strip()
                 and witness['reviewer_id']!=review['curation_reviewer_id'],'Independent functional role attribution missing')
            facts={'hit_id':b['hit_id'],'locus_key':h['locus_key'],'source_aa_sha256':h['source_aa_sha256'],
                   'profile_name':h['profile_name'],'profile_sha256':h['profile_sha256'],'model_id':b['model_id'],'role':role['role'],
                   'alignment_from':h['alignment_from'],'alignment_to':h['alignment_to'],'target_length':h['target_length']}
            must(all(witness.get(k)==v for k,v in facts.items()),'Independent functional role source/domain binding differs')
            actual=sorted({m.get('role',m.get('gene_name')) for m in h['native_model_roles']
                           if m.get('model_fqn',m.get('model'))==b['model_id']})
            must(actual and None not in actual and witness.get('native_component_names')==actual,
                 'Functional role interpretation omitted exact upstream component labels')
            reader.refs(witness.get('basis_refs'));must(h['raw_ref'] in witness['basis_refs'],'Independent role review lacks exact raw domain basis')
            statement=witness.get('functional_basis_statement')
            must(isinstance(statement,str) and 0<len(statement.strip())<=8000 and witness.get('unresolved_competing_role_interpretations')==0,
                 'Independent biochemical role interpretation is unexplained/unresolved')
            reader.refs(witness.get('functional_architecture_basis_refs'))
    if candidate.get('subtype')=='IIG' and review.get('decision')=='COMPLETE_PREDICTED':
        must(review.get('recognition_architecture_review')=='REVIEWED_FAMILY_SPECIFIC_RECOGNITION_DOMAIN_BASIS','IIG recognition architecture not reviewed')
        reader.refs(review.get('recognition_basis_refs'))
    if review.get('decision')=='COMPLETE_PREDICTED':
        exceptional=multipart_family(candidate,review,sources,hits,reader)
        fused={r['locus_key'] for r in review.get('roles',[]) if r['role']=='REASE'}&{r['locus_key'] for r in review.get('roles',[]) if r['role']=='MTASE'}
        separate={r['locus_key'] for r in review.get('roles',[]) if r['role']=='SPECIFICITY'}-fused
        must(not (candidate['rm_type']=='II' and fused and separate) or exceptional,'Multipart TypeII lacks explicit family architecture review')
        if exceptional:
            # Original independently authored core still checks every source,
            # role/domain/flag/compatibility. Only its obsolete one-gene IIG
            # cardinality condition is bypassed after this stricter family audit.
            return original({**candidate,'subtype':None},review,sources,hits,reader)
    return original(candidate,review,sources,hits,reader)

def atomic_one(entry,contract,C):
    accession=entry['accession'];root=Path(contract['root']).resolve();genome=Path(entry['genome']).resolve()
    must(root in genome.parents,'Atomic genome outside canonical repository')
    complete_path=genome/'complete.json';complete=read(complete_path)
    must(complete.get('schema')=='STAGE05_ATOMIC_GENOME_COMPLETE_V1' and complete.get('state')=='COMPLETE_VALIDATED'
         and complete.get('accession')==accession and complete.get('curation')=='NOT_RUN'
         and complete.get('validation_scope')=='NATIVE_SEARCH_SOURCE_AND_RAW_INTEGRITY_ONLY'
         and complete.get('biological_absence_claim')=='NONE' and complete.get('dataset_kind','PRODUCTION')=='PRODUCTION','Missing actual raw-only atomic checkpoint')
    files=complete['files'];must(files and isinstance(files,dict),'Empty native payload manifest')
    for name,digest in files.items():must(re.fullmatch('[a-f0-9]{64}',digest) and sha(safe(genome,name))==digest,'Native payload hash drift')
    launches=[name for name in files if name.startswith('execution/') and name.endswith('.launch.json')]
    must(launches,'Accepted native checkpoint lacks retained actual launches')
    for name in launches:
        launch=read(safe(genome,name));closure_name=name[:-len('.launch.json')]+'.closure.json'
        must(closure_name in files,'Accepted native launch lacks manifest-pinned closure')
        closure=read(safe(genome,closure_name))
        must(launch.get('execution')=='ACTUAL_PROCESS_STARTED' and launch.get('signalling')=='VERIFIED_KERNEL_PIDFDS_ONLY'
             and closure.get('command_nonce')==launch.get('command_nonce') and closure.get('boot_id')==launch.get('boot_id')
             and type(closure.get('root_exit_code')) is int and closure.get('group_empty') is True
             and closure.get('tracked_descendants_empty') is True and not closure.get('survivors')
             and not closure.get('unexplained_pgid_members'),'Accepted scientific native checkpoint has unproven owned closure')
    identity=complete['scientific_identity'];must(complete['scientific_identity_sha256']==objsha(identity)
         and identity.get('schema')=='STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2'
         and identity['accession']==accession and identity['panel_sha256']==PANEL_SHA
         and identity.get('source_validation_sha256')==SOURCE_VALIDATION_SHA
         and identity.get('runtime_manifest_sha256')==contract['runtime_manifest_sha256']
         and identity.get('runner_sha256')==contract['atomic_runner_sha256']
         and identity.get('supervisor_sha256')==contract['supervisor_sha256']
         and identity.get('methods')=='FULL_PADLOC5027_DF3_THREE_NATIVE_FAMILIES_RAW_INTEGRITY_ONLY','Atomic scientific identity differs')
    verify_source_acceptance(identity,accession,root,Path(contract['source'])/'assemblies'/accession/'build_receipt.json')
    inv=safe(genome,complete['inventory_directory']);raw_path=safe(genome,complete['raw_validation_file'])
    must(raw_path.relative_to(genome).as_posix() in files and all((inv/name).relative_to(genome).as_posix() in files for name in
        ('all_native_profile_domains.tsv','all_native_filtered_profile_hits.tsv','all_native_system_candidate_rows.tsv','all_native_query_completion.tsv',
         'source_locus_crosswalk.tsv','source_replicon_topology.tsv','source_annotation_review.tsv','replicon_search_states.tsv')),'Selected raw/inventory members absent from complete manifest')
    raw=read(raw_path);freeze_path=genome/'execution/execution_freeze.json';freeze=read(freeze_path)
    must(raw['status']=='PASS_FULL_NATIVE_SEARCH_AND_SOURCE_ACCOUNTING_ONLY' and raw['architecture_curation']=='NOT_RUN'
         and raw['assembly_accession']==accession and raw['execution_freeze_sha256']==sha(freeze_path)
         and freeze['scientific_identity']==identity and freeze['panel_sha256']==PANEL_SHA,'Raw/native scientific freeze mismatch')
    roots={'source':Path(contract['source']).resolve(),'bundle':genome/'bundle','execution':genome/'execution',
           'inventory':inv.parents[1],'policy':Path(contract['policy']).resolve(),'models':Path(contract['models']).resolve(),
           'padloc_db':Path(contract['padloc_db']).resolve(),'environment':Path(contract['environment']).resolve(),
           'reviews':Path(contract['reviews']).resolve()}
    reader=reader_type(C)(root,roots)
    prepared=read(entry['prepared']);document=read(entry['review']);result=read(entry['result'])
    must(prepared.get('dataset_kind')==result.get('dataset_kind')=='PRODUCTION' and prepared['schema']=='ATOMIC_STAGE05_REVIEW_QUEUE_V1'
         and result['schema']=='ATOMIC_STAGE05_REVIEW_RESULT_V1','Synthetic/wrong producer artifact schema')
    must(prepared['evidence_roots']=={k:str(v) for k,v in roots.items()},'Qualified producer read roots changed')
    must(prepared['atomic_binding']==result['atomic_binding'],'Prepared/result scientific binding differs')
    binding=prepared['atomic_binding']
    for field,path in [('complete_receipt_sha256',complete_path),('raw_validation_sha256',raw_path),('execution_freeze_sha256',freeze_path)]:must(binding[field]==sha(path),'Producer raw/native binding differs')
    must(binding['bridge_sha256']==contract['producer_sha256']==result['producer_sha256'],'Unreviewed producer bytes')
    must(binding['retained_dependency_sha256']==DEPENDENCY_PINS and binding['native_payload_sha256']==objsha(files),
         'Producer dependency/native manifest binding differs')
    must(result['prepared_sha256']==sha(entry['prepared']) and result['review_sha256']==sha(entry['review']),'Actual prepared/review file changed')
    for name,digest in prepared['source_snapshot'].items():
        p=safe(root,name);must(sha(p)==digest,'Actual source/native snapshot changed')
    source=roots['source']/'assemblies'/accession;bundle=roots['bundle']/'assemblies'/accession;execution=roots['execution']/'assemblies'/accession
    source_receipt=read(source/'build_receipt.json');must(sha(source/'build_receipt.json')==identity['source_receipt_sha256']==binding['source_receipt_sha256'],'Original source receipt mismatch')
    must(source_receipt.get('assembly_accession')==accession and source_receipt.get('identity')==read(contract['source_validation'])['builder_identity'],
         'Original source differs from accepted full-panel source builder identity')
    rows=C.records(inv/'source_locus_crosswalk.tsv');reps=read(source/'replicon_manifest.json');seqs=C.proteins(source/(accession+'.faa'))
    sources=C.sources_from_rows(rows,seqs,reps,accession)
    reader.source_refs={r['locus_key']:reader.make_ref(inv/'source_locus_crosswalk.tsv','tsv:'+str(i),r) for i,r in enumerate(rows,1)}
    for item in source_receipt['output_files']:
        p=safe(source,item['path']);must(p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],'Original source receipt member changed')
    derived=read(bundle/'bundle_receipt.json');must(derived['source_receipt_sha256']==sha(source/'build_receipt.json'),'Derived source binding differs')
    for item in derived['output_files']:
        p=safe(bundle,item['path']);must(p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],'Derived bundle changed')
    original={r['locus_key']:r for r in C.records(source/'locus_crosswalk.tsv')}
    must(len(original)==len(rows) and all(r['locus_key'] in original and all(r.get(k)==v for k,v in original[r['locus_key']].items()) for r in rows),'Inventory original source join differs')
    must(sha(bundle/'locus_crosswalk.tsv')==sha(inv/'source_locus_crosswalk.tsv') and sha(bundle/'replicon_topology.tsv')==sha(inv/'source_replicon_topology.tsv'),'Source copy changed')
    C.check_source_queue(prepared,sources,reps,inv);search=C.check_task_receipts(reader,prepared,freeze_path,sources,execution)
    query_rows,profiles,scopes,lookup=C.check_queries(reader,inv,execution,freeze,sources)
    old_selection=C.selected_padloc;C.selected_padloc=lambda hits:native_padloc(hits,inv,sources,C)
    try:hits=C.check_domains(reader,inv,execution,freeze,sources,prepared,query_rows,profiles,scopes,lookup,roots['padloc_db'])
    finally:C.selected_padloc=old_selection
    scope=read(HERE/'pinned_model_candidate_scope.json');candidates(reader,inv,execution,sources,prepared,scope,roots,C)
    reader.native_runtime={'execution':roots['execution'],'environment':roots['environment'],'padloc_db':roots['padloc_db'],'freeze':freeze,'freeze_sha256':sha(freeze_path)}
    queue_by_id={q['queue_id']:q for q in prepared['queue']}
    for item in list(document.get('reviews',[]))+list(document.get('manual_candidates',[])):
        if 'reviewed_subtype' not in item:continue
        proposed=item.get('candidate') or queue_by_id.get(item.get('queue_id'),{}).get('evidence',{})
        must(proposed.get('subtype_conflict') or item['reviewed_subtype']==proposed.get('subtype'),
             'Ignored scalar subtype override must not replace explicit family evidence')
    original_architecture=C.architecture;C.architecture=lambda *args:additional_architecture(*args,original_architecture)
    try:cells=C.reconstruct(prepared,document,result,sources,hits,search,reader)
    finally:C.architecture=original_architecture
    must(result['scientific_stage05_status']=='INDEPENDENT_CURATED_VALIDATION_REQUIRED' and result['biological_searches_repeated']==0,'Producer scientific status changed')
    return cells,{'accession':accession,'complete_sha256':sha(complete_path),'prepared_sha256':sha(entry['prepared']),
                 'review_sha256':sha(entry['review']),'result_sha256':sha(entry['result']),
                 'source_context_loci':len(sources),'raw_domains':len(hits),'replicons':len(reps),
                 'states':dict(Counter(c['state'] for c in cells))}

def source_exception_binding(accession,document,contract):
    """Reopen exact source inputs even when there is no detector checkpoint."""
    source=Path(contract['source']).resolve()/'assemblies'/accession
    receipt_path=source/'build_receipt.json';receipt=read(receipt_path)
    verify_released_source(accession,Path(contract['root']).resolve(),receipt_path)
    must(receipt.get('assembly_accession')==accession and receipt.get('identity',{}).get('panel_sha256')==PANEL_SHA,
         'Exception original source accession/panel differs')
    if 'source_validation' in contract:
        must(receipt.get('identity')==read(contract['source_validation'])['builder_identity'],'Exception source differs from accepted source traceability receipt')
    must(document['source_receipt_sha256']==sha(receipt_path),'Exception source receipt changed')
    outputs=receipt['output_files'];pins={item['path']:item['sha256'] for item in outputs}
    must(len(pins)==len(outputs) and document.get('source_input_files')==pins,'Exception must pin every exact original source output')
    must({accession+'.faa','locus_crosswalk.tsv','replicon_manifest.json'}<=set(pins),'Exception source context incomplete')
    for item in outputs:
        path=safe(source,item['path']);must(path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],'Exception source input drift')
    return source,receipt

def terminal_exception_binding(genome,document):
    """Check a terminal snapshot, recording rather than concealing closure gaps.

    This is scientific panel accounting. UNPROVEN closure never authorizes a
    retry/relaunch; it is retained as an explicit operational exception.
    """
    terminal=document.get('current_terminal_receipt');state=document['execution_state']
    if terminal is None:
        must(state=='NOT_RUN' and not (genome/'status.json').exists() and not (genome/'complete.json').exists(),
             'NOT_RUN without terminal receipt contradicts existing current checkpoint')
        must(not list(genome.rglob('*.launch.json')),'Unattempted exception contains native launches')
        must(document.get('process_closure_state')=='NO_ATTEMPT','Unattempted exception closure state differs')
        return None,{'process_closure_state':'NO_ATTEMPT','native_launch_count':0}
    must(isinstance(terminal,dict) and terminal.get('path')=='status.json','Exception must bind the actual current status.json')
    path=safe(genome,terminal['path']);current=read(path)
    must(terminal['sha256']==sha(path) and current.get('accession')==document['accession'] and current.get('state')==state,
         'Exception current terminal receipt differs')
    must(current.get('curation')=='NOT_RUN' and current.get('biological_absence_claim')=='NONE'
         and current.get('outputs_preserved') is True and current.get('error')==document.get('terminal_error'),
         'Exception conceals actual terminal error/scope')
    must(isinstance(current.get('owner_nonce'),str) and current['owner_nonce'] and isinstance(current.get('transaction'),str),
         'Attempted exception lacks actual transaction identity')
    transaction=safe(genome,current['transaction']);transaction_status=transaction/'status.json'
    must(transaction.is_dir() and re.fullmatch(r'transactions/attempt_[0-9]+',current['transaction'])
         and sha(transaction_status)==sha(path),'Current terminal does not match its immutable transaction receipt')
    pinned=document.get('launch_receipts');must(isinstance(pinned,list),'Exception must inventory actual retained launches')
    actual={p.resolve() for p in genome.rglob('*.launch.json')}
    declared={safe(genome,item['path']) for item in pinned}
    must(len(declared)==len(pinned) and actual==declared,'Exception launch receipts omitted/duplicated')
    gaps=[];launches=[]
    for item in pinned:
        launch_path=safe(genome,item['path']);launch=read(launch_path)
        must(item['sha256']==sha(launch_path) and launch.get('execution')=='ACTUAL_PROCESS_STARTED'
             and launch.get('new_process_session') is True and launch.get('signalling')=='VERIFIED_KERNEL_PIDFDS_ONLY'
             and isinstance(launch.get('child_pid'),int) and isinstance(launch.get('child_start_ticks'),int)
             and launch.get('command_nonce') and launch.get('boot_id'),'Exception launch identity is unproven')
        closure_path=launch_path.with_name(launch_path.name[:-len('.launch.json')]+'.closure.json')
        # Stored Linux paths may be mounted under a host mapping. The immutable
        # sibling path and nonce/boot identity are checked, never a numeric PID.
        closure_pin=item.get('closure_sha256');proven=False
        if closure_path.is_file():
            must(closure_pin==sha(closure_path),'Exception closure hash differs')
            closure=read(closure_path)
            proven=(closure.get('command_nonce')==launch['command_nonce'] and closure.get('boot_id')==launch['boot_id']
                    and type(closure.get('root_exit_code')) is int and closure.get('group_empty') is True
                    and closure.get('tracked_descendants_empty') is True and not closure.get('survivors')
                    and not closure.get('unexplained_pgid_members') and closure.get('signalling')=='VERIFIED_KERNEL_PIDFDS_ONLY')
        else:must(closure_pin is None,'Exception pins a nonexistent closure')
        if not proven:gaps.append(item['path'])
        launches.append({'path':item['path'],'launch_sha256':item['sha256'],'closure_sha256':closure_pin,'closure_proven':proven})
    claimed=current.get('owned_closure_proven');must(type(claimed) is bool,'Terminal closure flag is missing')
    closure_state='PROVEN_CLOSED' if claimed and not gaps else 'UNPROVEN_RECONCILIATION_REQUIRED'
    must(document.get('process_closure_state')==closure_state,'Exception process-closure uncertainty was erased')
    if closure_state=='UNPROVEN_RECONCILIATION_REQUIRED':
        must(isinstance(document.get('closure_unresolved_reason'),str) and document['closure_unresolved_reason'].strip(),
             'Unproven closure needs a bounded explicit reason; this audit does not authorize a relaunch')
    must(not claimed or not gaps,'Terminal claims closure but actual retained launch/closure contradict it')
    return sha(path),{'process_closure_state':closure_state,'native_launch_count':len(launches),'launches':launches,
                      'owner_nonce':current['owner_nonce'],'transaction':current['transaction']}

def exception_cells(accession,state,positive_cells=None):
    """Retain independently accepted positives while all unproved cells stay NA."""
    result=[];positive={c['rm_type']:c for c in (positive_cells or [])}
    for kind in TYPES:
        prior=positive.get(kind,{})
        # Carry all prior scientifically reviewed candidates/IDs to preserve a
        # lower bound; the new exception never establishes non-detection.
        counts=dict(prior.get('candidate_counts',{}));complete=prior.get('complete_predicted_count',0)
        result.append({'assembly_accession':accession,'rm_type':kind,'state':'NOT_RUN' if state=='NOT_RUN' else 'FAILED',
                       'candidate_counts':counts,'complete_predicted_count':complete,'curated_partial_count':prior.get('curated_partial_count',0),
                       'candidate_ids':list(prior.get('candidate_ids',[])),
                       'required_detector_completion':{'PADLOC':'NOT_RUN' if state=='NOT_RUN' else 'FAILED',
                                                       'DefenseFinder':'NOT_RUN' if state=='NOT_RUN' else 'FAILED'},
                       'coverage_unresolved':True,'positive_invalidated':False,
                       'review_execution':'DOCUMENTED_EXECUTION_EXCEPTION_INDEPENDENT_AUDIT_REQUIRED'})
    return result

def exception_one(entry,contract,C):
    accession=entry['accession'];genome=Path(entry['genome']).resolve();root=Path(contract['root']).resolve()
    must(root in genome.parents,'Exception genome outside canonical repository')
    path=Path(entry['exception_record']);document=read(path)
    must(document.get('schema')=='RM_ATOMIC_CURATION_EXCEPTION_V1' and document.get('dataset_kind')=='PRODUCTION'
         and document.get('accession')==accession and document.get('approved_sha256')==PANEL_SHA
         and document.get('execution_state') in EXCEPTION_STATES,'Exception schema/accession/state differs')
    reason=document.get('reason');must(isinstance(reason,str) and 0<len(reason.strip())<=4000,'Bounded exception reason required')
    source,receipt=source_exception_binding(accession,document,contract)
    terminal_sha,closure=terminal_exception_binding(genome,document)
    positive=None;positive_audit=None;proof=entry.get('retained_positive_entry')
    if proof is not None:
        must(isinstance(proof,dict) and proof.get('accession')==accession and not proof.get('exception_record'),
             'Retained positive must be an actual independently reopenable same-accession curated checkpoint')
        positive,positive_audit=atomic_one(proof,contract,C)
        actual=read(proof['prepared'])['atomic_binding']['source_receipt_sha256']
        must(actual==document['source_receipt_sha256'],'Retained positive uses different exact source data')
        must(document.get('retained_positive_result')=={'path':str(proof['result']),'sha256':sha(proof['result'])},
             'Exception retained-positive source pin differs')
    else:must(document.get('retained_positive_result') is None,'Exception positive claim lacks actual independent evidence')
    cells=exception_cells(accession,document['execution_state'],positive)
    summary={'accession':accession,'execution_state':document['execution_state'],'reason':reason,
             'source_receipt_sha256':document['source_receipt_sha256'],'exception_record_sha256':sha(path),
             'current_terminal_receipt_sha256':terminal_sha,
             'accepted_complete_positive_count':sum(c['complete_predicted_count'] for c in cells)}
    audit={**summary,'source_input_files':document['source_input_files'],'closure':closure,'retained_positive_audit':positive_audit}
    return cells,audit,summary

def compare_serialized(panel,cells,matrix_path,state_path,C):
    wide=C.records(matrix_path);must(wide and list(wide[0])==['accession']+['Type_'+t for t in TYPES],'Binary matrix schema differs')
    by={r['accession']:r for r in wide};must(len(wide)==len(by)==196 and set(by)==set(panel),'Binary matrix accessions differ')
    columns=['accession','rm_type','state','complete_count','partial_count','candidate_count','search_complete','conflict','positive_invalidated','count_lower_bound','review_ids']
    long=C.records(state_path);must(long and list(long[0])==columns,'State matrix schema differs')
    states={(r['accession'],r['rm_type']):r for r in long};must(len(long)==len(states)==784 and set(states)=={(a,t) for a in panel for t in TYPES},'State matrix Cartesian product differs')
    for c in cells:
        key=(c['assembly_accession'],c['rm_type']);r=states[key];counts=c['candidate_counts']
        complete=c['complete_predicted_count'];partial=c['curated_partial_count'];candidate=sum(counts.values())
        search=all(v=='VALIDATED_FULL_NATIVE_SEARCH' for v in c['required_detector_completion'].values())
        conflict=bool(c['coverage_unresolved'] or counts.get('UNCERTAIN',0) or counts.get('PARTIAL_CANDIDATE',0) or not search)
        expected={'accession':key[0],'rm_type':key[1],'state':c['state'],'complete_count':str(complete),'partial_count':str(partial),
                  'candidate_count':str(candidate),'search_complete':str(search),'conflict':str(conflict),'positive_invalidated':'False',
                  'count_lower_bound':str(conflict),'review_ids':json.dumps(c['candidate_ids'],separators=(',',':'))}
        must(r==expected,'Serialized cell differs from independently reconstructed scientific evidence: '+str(key))
        value='1' if complete>0 else ('0' if c['state']=='NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH' else 'NA')
        must(by[key[0]]['Type_'+key[1]]==value,'Binary value contradicts independent source/domain architecture: '+str(key))

def run(contract):
    began=time.perf_counter();C=core();must(sha(HERE/'pinned_model_candidate_scope.json')==SCOPE_SHA,'Exact model lookup changed')
    must(contract.get('schema')=='RM_ATOMIC_INDEPENDENT_CURATION_CHECK_V1' and contract.get('dataset_kind')=='PRODUCTION','Production scientific audit contract required')
    approved=Path(contract['approved']);panel=approved.read_text(encoding='ascii').split()
    must(sha(approved)==PANEL_SHA and len(panel)==len(set(panel))==196,'Exact approved196 panel differs')
    source_validation=read(contract['source_validation'])
    must(sha(contract['source_validation'])==SOURCE_VALIDATION_SHA and source_validation.get('status')=='PASS_SOURCE_LOCUS_INPUT_TRACEABILITY'
         and source_validation.get('complete_exact196_accounting') is True and source_validation.get('panel_sha256')==PANEL_SHA
         and source_validation.get('assemblies_passed')==196,'Accepted source traceability receipt changed')
    must(re.fullmatch('[a-f0-9]{64}',contract.get('producer_sha256','')),'Missing independently reviewed producer source pin')
    must(sha(contract['producer_source'])==contract['producer_sha256'],'Actual reviewed producer source changed')
    for name,digest in DEPENDENCY_PINS.items():must(sha(HERE/name)==digest,'Actual retained producer dependency changed')
    entries=contract['assemblies'];must(len(entries)==196 and [e['accession'] for e in entries]==panel,'All approved genomes in frozen order required; no pilot or omitted result')
    actual_native=any(not e.get('exception_record') or e.get('retained_positive_entry') for e in entries)
    native_manifest_sha=native_provenance(contract) if actual_native else None
    all_cells=[];audits=[];exceptions=[];closure_unproven=[]
    for entry in entries:
        if entry.get('exception_record'):
            cells,audit,summary=exception_one(entry,contract,C);exceptions.append(summary)
            if audit['closure']['process_closure_state']=='UNPROVEN_RECONCILIATION_REQUIRED':closure_unproven.append(entry['accession'])
        else:cells,audit=atomic_one(entry,contract,C)
        all_cells.extend(cells);audits.append(audit)
    C.matrix(panel,all_cells);compare_serialized(panel,all_cells,contract['matrix'],contract['state'],C)
    manifest={'schema':'RM_INDEPENDENT_CURATION_SOURCE_MANIFEST_V1','dataset_kind':'PRODUCTION','contract_sha256':objsha(contract),
              'producer_sha256':contract['producer_sha256'],'checker_sha256':sha(__file__),'independent_core_sha256':CORE_SHA,
              'candidate_scope_sha256':SCOPE_SHA,'assemblies':audits,'source_read_roots':{k:contract[k] for k in ('root','source','policy','models','padloc_db','environment','reviews')},
              'source_validation_sha256':SOURCE_VALIDATION_SHA,
              'runtime_manifest_sha256':native_manifest_sha,
              'functional_activity_claim':'NONE','biological_searches_repeated':0,
              'exception_evidence_scope':'Terminal/launch/closure snapshots are accounting evidence only, never accepted mutable scientific output inputs.',
              'operational_closure_unproven_accessions':closure_unproven}
    status=('ACCOUNTED_RM_CURATION_WITH_UNPROVEN_OPERATIONAL_CLOSURE' if closure_unproven else
            'PASS_INDEPENDENT_RM_CURATION_WITH_DOCUMENTED_EXCEPTIONS' if exceptions else 'PASS_INDEPENDENT_RM_CURATION')
    receipt={'schema':'RM_INDEPENDENT_CURATION_ACCEPTANCE_V1','status':status,'dataset_kind':'PRODUCTION',
             'accepted_curation':not closure_unproven,'accession_count':196,'cell_count':784,'matrix_sha256':sha(contract['matrix']),
             'state_sha256':sha(contract['state']),'approved_sha256':sha(approved),'all_actual_review_records_checked':True,
             'source_native_bindings_verified':True,'complete_and_partial_architectures_checked':True,
             'functional_activity_claim':'NONE','scientific_uncertainties':dict(Counter(c['state'] for c in all_cells)),
             'checker_sha256':sha(__file__),'independent_core_sha256':CORE_SHA,'biological_searches_repeated':0,
             'documented_exception_count':len(exceptions),'operational_closure_verified':not closure_unproven,
             'operational_closure_unproven_accessions':closure_unproven,
             'elapsed_seconds':time.perf_counter()-began,
             'evidence_limit':'All196 accounted through actual source/native/domain/review audit or explicit source-bound terminal exceptions. Unresolved stays NA; accepted intact positives survive other exceptions. Unproven owned closure vetoes publication/figure acceptance and every new launch.'}
    exception_manifest=({'schema':'RM_DOCUMENTED_CURATION_EXCEPTIONS_V1','dataset_kind':'PRODUCTION','approved_sha256':PANEL_SHA,
                         'entries':exceptions,'operational_closure_unproven_accessions':closure_unproven} if exceptions else None)
    return receipt,manifest,exception_manifest,all_cells

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--contract',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();must(not args.output.exists(),'Preserve prior audit namespace')
    try:
        receipt,manifest,exceptions,cells=run(read(args.contract));code=0 if receipt['accepted_curation'] else 2
    except Exception as error:
        receipt={'schema':'RM_INDEPENDENT_CURATION_ACCEPTANCE_V1','status':'FAIL_INDEPENDENT_RM_CURATION','accepted_curation':False,
                 'error':type(error).__name__+': '+str(error),'biological_searches_repeated':0};manifest=None;exceptions=None;cells=None;code=1
    args.output.mkdir(parents=True)
    if manifest is not None:
        p=args.output/'curation_source_manifest.json';p.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        receipt['curation_source_manifest_sha256']=sha(p)
    if exceptions is not None:
        p=args.output/'exception_manifest.json';p.write_text(json.dumps(exceptions,indent=2)+'\n',encoding='utf-8')
        receipt['exception_manifest_sha256']=sha(p)
    if cells is not None:
        (args.output/'independently_reconstructed_cells.json').write_text(json.dumps(cells,indent=2)+'\n',encoding='utf-8')
    (args.output/'curation_validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(receipt['status']);return code

if __name__=='__main__':raise SystemExit(main())
