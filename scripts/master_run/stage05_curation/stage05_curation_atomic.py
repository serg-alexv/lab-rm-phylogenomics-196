#!/usr/bin/env python3
"""Bridge retained source/domain review logic to one atomic genome receipt.

No searches, installs, WSL startup, control/runner mutation, or automatic role
assignment. prepare writes a real pending review queue; apply consumes actual
executed typed review records and leaves independent scientific audit pending.
Native PADLOC selected CSV rows are evidence; the unfinished Python top5 alias
reconstruction and old full-panel/four-tree gate are never called.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re,sys
from collections import defaultdict
from pathlib import Path,PurePosixPath
from types import SimpleNamespace
import stage05_architecture_policy as P

HERE=Path(__file__).resolve().parent
PINNED_PANEL='85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'
SOURCE_PINS_SHA='a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84'
PINS={'stage05_architecture_policy.py':'942edc6312d1490afc681c42ab1e32d67c92373024acca7360918ed3eeaef3e4',
      'retained/stage05_curation_adapter.py':'cbaf00aee2d9961eaaa0be76b589315014a88183e3f7f8ed1f2ff234e6418177',
      'retained/stage05_evidence.py':'7582d1a37980d89669159e3926f5b459e8d68abfde530ea0b8fc13b991d4363e',
      'pinned_model_candidate_scope.json':'6284203055ada645b3f6a8023e71e57a5fe8156bc9d4dffcc72da7614f3b30be'}
INVENTORY_FILES=('all_native_profile_domains.tsv','all_native_filtered_profile_hits.tsv',
                 'all_native_system_candidate_rows.tsv','all_native_query_completion.tsv',
                 'source_locus_crosswalk.tsv','source_replicon_topology.tsv',
                 'source_annotation_review.tsv','replicon_search_states.tsv')

def require(ok,text):
    if not ok:raise ValueError(text)

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def duplicate_free(items):
    out={}
    for key,value in items:
        require(key not in out,'Duplicate JSON field: '+key);out[key]=value
    return out

def load(path):return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=duplicate_free)

def object_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def member(root,name):
    pp=PurePosixPath(name)
    require(name and pp.as_posix()==name and not pp.is_absolute() and '..' not in pp.parts and '\\' not in name,'Unsafe manifest/reference path')
    path=Path(root).joinpath(*pp.parts).resolve();require(Path(root).resolve() in path.parents,'Manifest/reference escaped root')
    return path

def load_retained():
    for name,digest in PINS.items():require(sha(HERE/name)==digest,'Retained dependency bytes changed: '+name)
    sys.path.insert(0,str(HERE/'retained'))
    spec=importlib.util.spec_from_file_location('retained_stage05_adapter',HERE/'retained/stage05_curation_adapter.py')
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    return adapter

def accepted_source_gate(root,identity,accession,source_receipt):
    """Bind native V2 inputs to previously released source bytes, without a tree."""
    pins_path=HERE/'accepted_source_pins.json'
    require(sha(pins_path)==SOURCE_PINS_SHA,'Standalone accepted source pins changed')
    pins=load(pins_path)
    require(pins.get('schema')=='STAGE05_ACCEPTED_SOURCE_PINS_V1'
            and pins.get('approved_accessions_sha256')==PINNED_PANEL
            and len(pins['source_receipts'])==196 and accession in pins['source_receipts'],
            'Exact released full196 source selection differs')
    selected=pins['source_receipts'][accession]
    expected={'source_pins_sha256':SOURCE_PINS_SHA,'accepted_files':pins['accepted_files'],
              'released_source_member':selected}
    require(identity.get('schema')=='STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2'
            and identity.get('source_acceptance')==expected,
            'Native V2 released source acceptance differs')
    for name,digest in pins['accepted_files'].items():
        require(sha(member(root,name))==digest,'Accepted canonical source control changed: '+name)
    require(identity.get('source_receipt_sha256')==selected['sha256']
            and Path(source_receipt).stat().st_size==selected['bytes']
            and sha(source_receipt)==selected['sha256'],'Source receipt differs from exact released member')

def atomic_gate(root,genome,accession,approved,source_root):
    panel=Path(approved).read_text(encoding='ascii').split()
    require(sha(approved)==PINNED_PANEL and len(panel)==len(set(panel))==196 and accession in panel,'Exact approved196 panel changed')
    complete=load(genome/'complete.json')
    require(complete.get('dataset_kind','PRODUCTION')=='PRODUCTION','Synthetic native checkpoint cannot satisfy production curation')
    require(complete.get('schema')=='STAGE05_ATOMIC_GENOME_COMPLETE_V1' and complete.get('state')=='COMPLETE_VALIDATED' and complete.get('accession')==accession
            and complete.get('validation_scope')=='NATIVE_SEARCH_SOURCE_AND_RAW_INTEGRITY_ONLY'
            and complete.get('curation')=='NOT_RUN' and complete.get('biological_absence_claim')=='NONE','Atomic native/source completion missing')
    identity=complete['scientific_identity']
    require(complete.get('scientific_identity_sha256')==object_sha(identity),'Atomic scientific identity digest differs')
    require(identity.get('schema')=='STAGE05_SINGLE_GENOME_SCIENTIFIC_IDENTITY_V2'
            and identity.get('accession')==accession and identity.get('panel_sha256')==PINNED_PANEL
            and identity.get('methods')=='FULL_PADLOC5027_DF3_THREE_NATIVE_FAMILIES_RAW_INTEGRITY_ONLY','Atomic scientific identity differs')
    accepted_source_gate(root,identity,accession,source_root/'assemblies'/accession/'build_receipt.json')
    files=complete['files'];require(isinstance(files,dict) and files,'Empty atomic native payload manifest')
    for name,digest in files.items():
        require(re.fullmatch('[a-f0-9]{64}',digest),'Unfilled atomic payload pin')
        path=member(genome,name);require(path.is_file() and sha(path)==digest,'Atomic payload changed: '+name)
    inv=[n for n in files if n.endswith('/assemblies/'+accession+'/all_native_profile_domains.tsv') and n.startswith('inventory/')]
    audits=[n for n in files if re.fullmatch(r'raw_validation/attempt_[0-9]+/validation.json',n)]
    require(len(inv)==len(audits)==1,'Atomic receipt must name exactly one selected inventory and independent raw audit')
    inventory=member(genome,inv[0]).parents[2]
    require(all((inventory/'assemblies'/accession/name).relative_to(genome).as_posix() in files for name in INVENTORY_FILES),'Atomic inventory payload incomplete')
    raw_path=member(genome,audits[0]);raw=load(raw_path);freeze=genome/'execution/execution_freeze.json'
    require(member(genome,complete['inventory_directory'])==inventory/'assemblies'/accession
            and member(genome,complete['raw_validation_file'])==raw_path,'Explicit selected inventory/raw receipt differs from manifest')
    require(raw['status']=='PASS_FULL_NATIVE_SEARCH_AND_SOURCE_ACCOUNTING_ONLY' and raw['architecture_curation']=='NOT_RUN'
            and raw['assembly_accession']==accession and raw['execution_freeze_sha256']==sha(freeze),'Independent per-genome raw audit differs')
    frozen=load(freeze);require(frozen['scientific_identity']==identity and frozen['panel_sha256']==PINNED_PANEL,'Native freeze differs')
    binding={'schema':'ATOMIC_STAGE05_CURATION_BINDING_V1','assembly_accession':accession,
             'complete_receipt_sha256':sha(genome/'complete.json'),'raw_validation_sha256':sha(raw_path),
             'execution_freeze_sha256':sha(freeze),'source_receipt_sha256':identity['source_receipt_sha256'],
             'retained_dependency_sha256':PINS,'bridge_sha256':sha(__file__),'native_payload_sha256':object_sha(files)}
    return inventory,raw_path,frozen,binding

def multipart_family_evidence(context,candidate,review):
    if not P.multipart_type_ii(candidate,review):return False
    family=review['type_ii_family_architecture'];witness=context.reader.resolve(family['independent_family_review_ref'])
    rm=family['rm_locus_key'];specificity=family['specificity_locus_key']
    roles=[r for r in review['roles'] if r['role'] in ('REASE','MTASE','SPECIFICITY')]
    ids=sorted({h for r in roles for h in r['hit_ids']})
    require(witness.get('schema')=='RM_MULTIPART_TYPE_II_FAMILY_REVIEW_V1'
            and witness.get('execution')=='EXECUTED_INDEPENDENT_SOURCE_DOMAIN_FAMILY_REVIEW'
            and witness.get('decision')=='SUPPORTED_FUSED_RM_SEPARATE_SPECIFICITY'
            and witness.get('independent_of_curation_producer') is True,'Multipart family interpretation was not independently executed')
    expected={'assembly_accession':candidate['assembly_accession'],'candidate_id':review['candidate_id'],
              'family_id':family['family_id'],'reviewed_subtype':family['reviewed_subtype'],
              'rm_locus_key':rm,'specificity_locus_key':specificity,
              'rm_source_aa_sha256':context.sources[rm]['primary_faa_sequence_sha256'],
              'specificity_source_aa_sha256':context.sources[specificity]['primary_faa_sequence_sha256'],
              'evidence_hit_ids':ids,'native_model_ids':sorted({b['model_id'] for r in roles for b in r['native_profile_role_bindings']}),
              'native_candidate_ref_sha256':sorted(object_sha(ref) for ref in candidate['native_candidate_refs']),
              'primary_family_basis_refs':family['primary_family_basis_refs']}
    require(all(witness.get(k)==v for k,v in expected.items()),'Multipart family interpretation differs from exact native/source evidence')
    require(isinstance(witness.get('reviewer_id'),str) and witness['reviewer_id'].strip()
            and witness['reviewer_id']!=review['curation_reviewer_id'],'Independent family review attribution missing')
    statement=witness.get('family_architecture_basis_statement')
    require(isinstance(statement,str) and 0<len(statement.strip())<=8000
            and witness.get('unresolved_competing_type_or_architecture_interpretations')==0,'Unexplained or competing multipart family architecture')
    context.reader.refs(witness.get('basis_refs'));context.reader.refs(family['primary_family_basis_refs'])
    required=[context.hits[h]['raw_ref'] for h in ids]+[context.aa_refs[rm],context.aa_refs[specificity]]
    require(all(ref in witness['basis_refs'] for ref in required),'Multipart family review omitted exact role domains or primary RM/S amino acids')
    return True

def review_addenda(context,document):
    """Require exact native profile/role bindings and explicit IIG recognition.

    The binding establishes what was reviewed; a scientific role still requires
    the opened functional-domain/primary basis and independent curation audit.
    It is never derived from an annotation or profile-name substring.
    """
    for record in list(document.get('reviews',[]))+list(document.get('manual_candidates',[])):
        review=record.get('candidate_review')
        if review is None:continue
        for role in review.get('roles',[]):
            bindings=role.get('native_profile_role_bindings',[])
            require(len(bindings)==len(role['hit_ids']) and {b['hit_id'] for b in bindings}==set(role['hit_ids']),
                    'Every role hit needs exact native profile/model binding')
            for binding in bindings:
                hit=context.hits[binding['hit_id']]
                models={r.get('model_fqn',r.get('model')) for r in hit['native_model_roles']}
                require(binding['profile_name']==hit['profile_name'] and binding['profile_sha256']==hit['profile_sha256']
                        and binding['model_id'] in models and binding['role']==role['role'],
                        'Role assignment is not bound to actual frozen native profile/model')
                context.reader.refs(binding.get('role_basis_refs'))
                # Model membership (including native exchangeability) does not
                # establish the biochemical role. Reopen a separate executed
                # source/domain interpretation, never a serializer assertion.
                witness=context.reader.resolve(binding['independent_functional_role_ref'])
                require(witness.get('schema')=='RM_FUNCTIONAL_DOMAIN_ROLE_REVIEW_V1'
                        and witness.get('execution')=='EXECUTED_INDEPENDENT_SOURCE_DOMAIN_ROLE_REVIEW'
                        and witness.get('decision')=='SUPPORTED_PREDICTED_ROLE'
                        and witness.get('independent_of_curation_producer') is True,
                        'Missing separately executed functional domain role review')
                require(isinstance(review.get('curation_reviewer_id'),str) and review['curation_reviewer_id'].strip()
                        and isinstance(witness.get('reviewer_id'),str) and witness['reviewer_id'].strip()
                        and witness['reviewer_id']!=review['curation_reviewer_id'],'Role interpretation is not independently attributed')
                expected={'hit_id':binding['hit_id'],'locus_key':hit['locus_key'],'source_aa_sha256':hit['source_aa_sha256'],
                          'profile_name':hit['profile_name'],'profile_sha256':hit['profile_sha256'],
                          'model_id':binding['model_id'],'role':role['role'],'alignment_from':hit['alignment_from'],
                          'alignment_to':hit['alignment_to'],'target_length':hit['target_length']}
                require(all(witness.get(k)==v for k,v in expected.items()),'Independent role review differs from exact source/native domain')
                components=sorted({row.get('role',row.get('gene_name')) for row in hit['native_model_roles']
                                   if row.get('model_fqn',row.get('model'))==binding['model_id']})
                require(components and None not in components and witness.get('native_component_names')==components,
                        'Independent functional basis omitted exact native component names')
                context.reader.refs(witness.get('basis_refs'))
                require(hit['raw_ref'] in witness['basis_refs'],'Independent functional interpretation omitted exact native domain')
                require(isinstance(witness.get('functional_basis_statement'),str) and 0<len(witness['functional_basis_statement'].strip())<=8000
                        and witness.get('unresolved_competing_role_interpretations')==0,'Independent functional interpretation is unresolved or unexplained')
                context.reader.refs(witness.get('functional_architecture_basis_refs'))
        if review.get('decision')=='COMPLETE_PREDICTED':
            # Candidate expansion/type/subtype resolution remains in the retained
            # executed review logic; inspect the final reviewed subtype here.
            reviewed_subtype=record.get('reviewed_subtype')
            native_id=record.get('queue_id')
            q=next((q for q in context.queue if q['queue_id']==native_id),None)
            candidate=record.get('candidate') or (q.get('evidence',{}) if q else {})
            if 'reviewed_subtype' in record and not candidate.get('subtype_conflict'):
                require(reviewed_subtype==candidate.get('subtype'),'Retained adapter would ignore an unsupported scalar subtype override; use explicit family review')
            subtype=reviewed_subtype if candidate.get('subtype_conflict') else candidate.get('subtype')
            if record.get('additional_source_locus_keys'):
                candidate={**candidate,'locus_keys':sorted(candidate['locus_keys']+record['additional_source_locus_keys'])}
            # The retained apply path separately requires executed type-mapping
            # evidence. Family binding must inspect that same final reviewed type.
            candidate={**candidate,'rm_type':review['rm_type']}
            if review.get('type_ii_family_architecture') is not None:
                multipart_family_evidence(context,candidate,review)
            if subtype=='IIG':
                require(review.get('recognition_architecture_review')=='REVIEWED_FAMILY_SPECIFIC_RECOGNITION_DOMAIN_BASIS',
                        'Complete IIG lacks explicit recognition architecture review')
                context.reader.refs(review.get('recognition_basis_refs'))

def native_padloc_selection(hits,sources,call_rows):
    """Bind accepted native CSV selection to actual original domains.

    PADLOC2 CSV rounds E-values to 3 significant figures and coverage to3
    decimals; use that exact representation and retain all raw unselected hits.
    A rounded selector matching several distinct domains is ambiguous and cannot
    establish a functional role without a separate reviewed selector repair.
    """
    rows=[json.loads(r['native_row_json']) for r in call_rows if r['detector']=='PADLOC']
    supported=defaultdict(list)
    for row in rows:
        required={'target.name','seqid','hmm.name','system','domain.iE.value','hmm.coverage','target.coverage','start','end'}
        require(required<=set(row),'Native PADLOC2 CSV selector fields missing')
        key=row['target.name'];require(key in sources and row['seqid']==sources[key]['replicon'],'PADLOC exact source boundary differs')
        source=sources[key]
        require(int(row['start'])==int(source['derived_linear_order_start_one_based']) and int(row['end'])==int(source['derived_linear_order_end_one_based']),'PADLOC native source geometry differs')
        matches=[]
        for hid,hit in hits.items():
            if hit['detector']!='PADLOC' or hit['locus_key']!=key or hit['profile_name']!=row['hmm.name']:continue
            d=hit['domain'];ie=float(d['independent_evalue'])
            if (float(format(ie,'.3g'))==float(row['domain.iE.value'])
                and abs(hit['native_profile_coverage']-float(row['hmm.coverage']))<=1e-12
                and abs(hit['native_target_coverage']-float(row['target.coverage']))<=1e-12):matches.append(hid)
        require(matches,'Accepted PADLOC CSV row lacks original native domain selector')
        for hid in matches:supported[hid].append((row['system'],len(matches),row.get('protein.name','')))
    for hid,hit in hits.items():
        if hit['detector']!='PADLOC':continue
        numerical=hit['native_role_threshold_passed'];matches=supported.get(hid,[])
        hit['native_numerical_domain_filter_passed']=numerical
        hit['native_selected_model_ids']=sorted({m for m,n,label in matches if n==1})
        hit['native_selected_protein_labels']=sorted({label for m,n,label in matches if n==1})
        hit['native_domain_selector_ambiguous']=any(n>1 for m,n,label in matches)
        hit['native_role_threshold_passed']=numerical and bool(hit['native_selected_model_ids'])
        hit['native_filter_basis']='Actual pinned PADLOC2 native CSV selection + exact source/AA/profile/domain selector; rounded3 native Evalue/coverage accounted. No Python top5/alias emulation or architecture inference.'
    return hits

def qualified_reader_class(adapter):
    class QualifiedReader(adapter.EvidenceReader):
        """Exact read-only roots permit retained C tools with G scientific data."""
        names=('source','bundle','execution','inventory','policy','models','padloc_db','environment','reviews')
        def __init__(self,root,allowed):
            super().__init__(root,allowed);require(len(allowed)==len(self.names),'Qualified root inventory differs')
            self.roots=dict(zip(self.names,map(lambda p:Path(p).resolve(),allowed)))
        def path(self,name):
            require(isinstance(name,str) and name.count('::')==1,'Qualified portable record reference required')
            alias,relative=name.split('::');require(alias in self.roots,'Unknown qualified evidence root')
            path=member(self.roots[alias],relative)
            require(path.is_file() and not any(p in ('.git','.private_run') for p in Path(relative).parts),'Missing/private qualified evidence')
            return path
        def make_ref(self,path,locator,record):
            path=Path(path).resolve();choices=[(name,root) for name,root in self.roots.items() if root in path.parents]
            require(choices,'Referenced evidence outside exact scientific/tool roots')
            name,root=max(choices,key=lambda item:len(item[1].parts))
            return {'path':name+'::'+path.relative_to(root).as_posix(),'sha256':self.hash(path),
                    'record_locator':locator,'record_sha256':adapter.object_sha(record)}
    return QualifiedReader

def evidence_class(adapter):
    class AtomicEvidence(adapter.AssemblyEvidence):
        def bind_domains(self):
            # Retained adapter is loaded privately in this sequential one-genome
            # CLI. Only its provisional selection callback is temporarily replaced.
            original=adapter.padloc_selection_facts
            adapter.padloc_selection_facts=lambda hits:native_padloc_selection(hits,self.sources,self.call_rows)
            try:super().bind_domains()
            finally:adapter.padloc_selection_facts=original
        def bind_candidates(self):
            # Native duplicate rows are retained in the manifest/raw audit and
            # queue refs, but cannot increase exact locus/type system counts.
            groups={}
            for index,row in enumerate(self.call_rows,1):
                key=row['locus_key'];require(key in self.sources and row['assembly_accession']==self.accession,'Native candidate source missing')
                native=json.loads(row['native_row_json']);raw=member(self.execution,row['raw_file'])
                require(sha(raw)==row['raw_file_sha256'],'Native candidate table hash differs')
                if row['detector']=='PADLOC':
                    require(native['target.name']==key and native['seqid']==self.sources[key]['replicon'],'PADLOC candidate boundary differs')
                    groupid=native['system.number'];callclass='PADLOC_NATIVE_SYSTEM'
                else:
                    require(native['hit_id']==self.sources[key]['df_bundle_target_id'] and native['replicon']==self.sources[key]['df_bundle_replicon_name']
                            and int(native['hit_pos'])==int(self.sources[key]['df_bundle_sequence_rank']),'DF candidate source order differs')
                    rejected=row['native_table']=='rejected_candidates.tsv'
                    groupid=native['candidate_id'] if rejected else native['sys_id'];callclass='REJECTED_NATIVE_CANDIDATE' if rejected else 'NATIVE_SYSTEM_CANDIDATE'
                identity=(row['detector'],str(raw.parent),row['model_fqn'],groupid,callclass,self.sources[key]['replicon'])
                group=groups.setdefault(identity,{'loci':set(),'refs':[],'rows':[]})
                group['loci'].add(key);group['rows'].append(row)
                group['refs'].append(self.reader.make_ref(self.directory/'all_native_system_candidate_rows.tsv','tsv:'+str(index),row))
            candidates=[]
            for identity,group in groups.items():
                detector,_,modelid,groupid,callclass,replicon=identity;entry=self.scope.get((detector,modelid))
                refs=group['refs']+[self.source_refs[k] for k in sorted(group['loci'])]
                if entry is None:
                    self.queue.append(adapter.queue_item('NATIVE_MODEL_CONTEXT',self.accession,{'native_group':identity},refs,
                        {'detector':detector,'model_fqn':modelid,'native_group_id':groupid,'native_call_class':callclass,
                         'locus_keys':sorted(group['loci']),'raw_rows':group['rows'],'model_scope':None}));continue
                refs.append(self.model_ref(entry))
                candidates.append({'assembly_accession':self.accession,'rm_type':entry['proposed_type'],'subtype':entry['subtype'],
                                   'locus_keys':sorted(group['loci']),'detector':detector,'native_candidate_refs':refs})
            self.candidates=P.deduplicate_exact(candidates)
            for c in self.candidates:
                c['subtype']=c['subtypes'][0] if len(c['subtypes'])==1 else None
                payload={**c,'related_hit_ids':sorted(h for h,v in self.hits.items() if v['locus_key'] in c['locus_keys']),
                         'source_loci':[self.sources[k] for k in c['locus_keys']]}
                self.queue.append(adapter.queue_item('NATIVE_CANDIDATE',self.accession,{'candidate_id':c['candidate_id']},
                                  c['native_candidate_refs']+[self.source_refs[k] for k in c['locus_keys']],payload))
    return AtomicEvidence

def run(args):
    adapter=load_retained();adapter.EvidenceReader=qualified_reader_class(adapter)
    root=args.root.resolve();genome=args.genome.resolve();require(root in genome.parents,'Genome evidence must reside in canonical repository')
    accession=args.accession;source=args.source.resolve()
    inventory,raw_path,frozen,binding=atomic_gate(root,genome,accession,args.approved,source)
    require(not args.output.exists(),'Use fresh curation output namespace')
    options=SimpleNamespace(root=root,source=source,bundle=genome/'bundle',execution=genome/'execution',inventory=inventory,
                            policy_dir=args.policy_dir.resolve(),models_dir=args.models.resolve(),padloc_db=args.padloc_db.resolve(),
                            environment_dir=args.environment.resolve(),evidence_dir=args.reviews.resolve())
    scope=load(HERE/'pinned_model_candidate_scope.json')
    context=evidence_class(adapter)(options,accession,frozen,scope,P);prepared=context.prepared()
    prepared.update(schema='ATOMIC_STAGE05_REVIEW_QUEUE_V1',dataset_kind='PRODUCTION',atomic_binding=binding,
                    evidence_roots={name:str(path) for name,path in context.reader.roots.items()})
    if args.phase=='prepare':result=prepared
    else:
        require(args.prepared and args.review,'apply requires exact prepared queue and actual executed review document')
        prior=load(args.prepared);require(prior==prepared,'Actual source/native/model/code queue changed since preparation')
        document=load(args.review);review_addenda(context,document)
        result=adapter.apply_assembly(context,prepared,document)
        result.update(schema='ATOMIC_STAGE05_REVIEW_RESULT_V1',dataset_kind='PRODUCTION',atomic_binding=binding,
                      producer_sha256=sha(__file__),prepared_sha256=sha(args.prepared),review_sha256=sha(args.review),
                      biological_searches_repeated=0)
    args.output.mkdir(parents=True)
    target=args.output/('prepared.json' if args.phase=='prepare' else 'curated_candidate.json')
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('REVIEW_PENDING' if args.phase=='prepare' else 'INDEPENDENT_CURATED_VALIDATION_REQUIRED')
    return target

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('phase',choices=('prepare','apply'))
    for name in ('root','genome','approved','source','policy-dir','models','padloc-db','environment','reviews','output'):
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--accession',required=True);ap.add_argument('--prepared',type=Path);ap.add_argument('--review',type=Path)
    run(ap.parse_args())

if __name__=='__main__':main()
