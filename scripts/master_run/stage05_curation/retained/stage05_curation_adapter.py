#!/usr/bin/env python3
"""Reopen native/source evidence, prepare review queues and apply recorded review.

No biological search, invented functional role, or scientific PASS. A separately
executed full196 raw audit precedes preparation. Final cells still require a
separate independent curated-evidence audit before Stage05 publication/Stage06.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math,os,re,sys,time
from collections import Counter,defaultdict
from pathlib import Path
import stage05_evidence as E

TYPES=('I','II','III','IV')
POLICY_SHA='20fb827e8593424194a7defa3a1ac04fc4c1fcef71be26231d369e32146f68de'
POLICY_RECONCILIATION_SHA='74baa2ae85c90b08e583ab752f8cb97f76bf54969f661845135331c5d18753e3'
SCOPE_SHA='6284203055ada645b3f6a8023e71e57a5fe8156bc9d4dffcc72da7614f3b30be'
BOOL_FIELDS=('protein_target_present','source_pseudo_any','partial_or_fuzzy','origin_spanning','requires_coordinate_review')
RAW_GATE='PASS_FULL_NATIVE_SEARCH_AND_SOURCE_ACCOUNTING_ONLY'
RELATED=re.compile(r'methyl|mtase|rease|restriction|endonuclease|\bhsd[rm s]?\b|\bmcr[bc]?\b|\bgmr[sd]?\b|\bmrr\b|\bvsp|\bdcm\b|\bdam\b',re.I)

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):return E.sha(Path(path))
def load(path):return E.json_read(Path(path))
def packed(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def object_sha(value):return hashlib.sha256(packed(value).encode()).hexdigest()
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.partial');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');temp.replace(path)
def inside(root,path):
    path=Path(path).resolve();require(root.resolve() in path.parents,'Evidence path escapes dedicated repository');return path
def table(path):return E.table(Path(path))
def strict_bool(value):
    require(value in ('True','False'),'Source boolean is not literal True/False');return value=='True'
def finite(value):
    number=float(value);require(math.isfinite(number),'Nonfinite native numeric value');return number
def fasta(path):
    sequences={};name=None;parts=[]
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            if line.startswith('>'):
                if name is not None:sequences[name]=''.join(parts)
                name=line[1:].split()[0];require(name not in sequences,'Duplicate exact FASTA target');parts=[]
            else:
                require(name is not None,'Sequence before FASTA identifier');parts.append(line.strip())
    if name is not None:sequences[name]=''.join(parts)
    return sequences

def import_policy(path):
    require(sha(path)==POLICY_SHA,'Frozen architecture policy changed; explicit repaired policy/retests required')
    spec=importlib.util.spec_from_file_location('stage05_bound_architecture_policy',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class EvidenceReader:
    """Open actual files and resolve typed records, never just hash-shaped refs."""
    def __init__(self,root,allowed):
        self.root=root.resolve();self.allowed=[Path(p).resolve() for p in allowed];self.hashes={};self.tables={};self.jsons={};self.fastas={}
    def path(self,name):
        require(isinstance(name,str) and name and not Path(name).is_absolute(),'Portable project-relative evidence path required')
        path=inside(self.root,self.root/name)
        require(not any(p in ('.private_run','.git') for p in path.relative_to(self.root).parts),'Private/session evidence forbidden')
        require(any(path==p or p in path.parents for p in self.allowed),'Evidence outside scientific allowlist')
        require(path.is_file(),'Referenced actual evidence file missing');return path
    def hash(self,path):
        path=Path(path);stat=path.stat();key=(str(path),stat.st_size,stat.st_mtime_ns)
        if key not in self.hashes:self.hashes[key]=sha(path)
        return self.hashes[key]
    def make_ref(self,path,locator,record):
        path=inside(self.root,path)
        return {'path':path.relative_to(self.root).as_posix(),'sha256':self.hash(path),
                'record_locator':locator,'record_sha256':object_sha(record)}
    def resolve(self,ref):
        require(isinstance(ref,dict) and set(['path','sha256','record_locator','record_sha256'])<=set(ref),'Typed record reference incomplete')
        path=self.path(ref['path']);require(self.hash(path)==ref['sha256'],'Actual referenced evidence bytes changed')
        locator=ref['record_locator'];require(isinstance(locator,str) and ':' in locator,'Typed record locator required')
        kind,value=locator.split(':',1)
        if kind in ('tsv','csv','native_tsv'):
            index=int(value);require(index>=1,'TSV record numbers start at1')
            cache_key=(path,kind)
            if cache_key not in self.tables:
                if kind=='tsv':self.tables[cache_key]=table(path)
                elif kind=='csv':
                    with path.open(encoding='utf-8',newline='') as stream:self.tables[cache_key]=list(csv.DictReader(stream))
                else:self.tables[cache_key]=E.native_tsv(path,'# No Rejected candidates' if path.name=='rejected_candidates.tsv' else '# No Systems found')
            require(index<=len(self.tables[cache_key]),'TSV reference row missing');record=self.tables[cache_key][index-1]
        elif kind=='json':
            if path not in self.jsons:self.jsons[path]=load(path)
            record=self.jsons[path]
            if value:
                require(value.startswith('/'),'JSON pointer must begin slash')
                for part in value[1:].split('/'):
                    part=part.replace('~1','/').replace('~0','~')
                    record=record[int(part)] if isinstance(record,list) else record[part]
        elif kind=='text':
            match=re.fullmatch(r'(\d+)-(\d+)',value);require(match,'Text locator requires inclusive start-end lines')
            lo,hi=map(int,match.groups());lines=path.read_text(encoding='utf-8').splitlines(keepends=True)
            require(1<=lo<=hi<=len(lines),'Text evidence lines missing');record=''.join(lines[lo-1:hi])
        elif kind=='fasta':
            if path not in self.fastas:self.fastas[path]=fasta(path)
            sequences=self.fastas[path];require(value in sequences,'Exact AA evidence target missing');record={'target_id':value,'sequence':sequences[value]}
        else:raise ValueError('Unsupported record locator; references must resolve real TSV/JSON/text/FASTA records')
        require(object_sha(record)==ref['record_sha256'],'Referenced actual record differs')
        return record
    def refs(self,refs):
        require(isinstance(refs,list) and refs,'Actual evidence references required');return [self.resolve(ref) for ref in refs]

def global_gate(args):
    panel=(args.root/'config/approved_accessions.txt').read_text().split()
    require(len(panel)==len(set(panel))==196,'All exact196 required; no alternate cohort')
    approval=load(args.root/'config/approval.json')
    require(approval['human_approval']=='APPROVED_FOR_SEQUENCE_ANALYSIS' and approval['pilot'] is False
            and approval['approved_assembly_count']==196 and approval['panel_accessions_sha256']==sha(args.root/'config/approved_accessions.txt'),'Full196 approval differs')
    raw=load(args.raw_validation);freeze=load(args.execution/'execution_freeze.json');inventory=load(args.inventory/'inventory_manifest.json')
    require(raw['status']==RAW_GATE and raw['scientific_stage05_status']=='ARCHITECTURE_CURATION_REQUIRED'
            and raw['architecture_curation']=='NOT_RUN' and raw['all_exact196_accounted'] is True
            and raw['approved_assemblies']==196 and raw['protein_loci']==398537 and raw['replicons']==2120 and raw['empty_replicons']==271
            and all(raw[k] is True for k in ['full_model_scope_verified','native_query_domain_source_join_verified','native_table_inventory_equivalence_verified']),
            'Mandatory independent executed full196 raw audit missing/incomplete')
    bindings={'execution_freeze_sha256':args.execution/'execution_freeze.json','bundle_construction_sha256':args.bundle/'construction_summary.json',
              'bundle_validation_sha256':args.bundle_validation,'inventory_manifest_sha256':args.inventory/'inventory_manifest.json',
              'source_validation_sha256':args.source_validation,'validator_source_sha256':args.raw_validator}
    for field,path in bindings.items():require(raw[field]==sha(path),'Independent raw-audit binding changed: '+field)
    require(freeze['panel_sha256']==sha(args.root/'config/approved_accessions.txt'),'Native executed panel differs')
    require(inventory['status']=='NATIVE_EVIDENCE_INVENTORY_CURATION_PENDING' and inventory['scientific_stage05_status']=='NOT_VALIDATED'
            and inventory['execution_freeze_sha256']==sha(args.execution/'execution_freeze.json')
            and [r['assembly_accession'] for r in inventory['assemblies']]==panel,'Native inventory not exact/pending')
    files={r['path']:r for r in inventory['output_files']};require(len(files)==len(inventory['output_files']),'Duplicate inventory member')
    actual={p.relative_to(args.inventory).as_posix() for p in args.inventory.rglob('*') if p.is_file()}
    require(actual==set(files)|{'inventory_manifest.json'},'Inventory payload member set changed')
    for name,entry in files.items():
        path=inside(args.inventory,args.inventory/name)
        require(path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],'Raw inventory payload changed: '+name)
    scope_path=args.policy_dir/'models/pinned_model_candidate_scope.json'
    require(sha(scope_path)==SCOPE_SHA,'Frozen candidate scope changed; explicit scientific repair required')
    scope=load(scope_path);require(scope['status']=='PASS_PINNED_CANDIDATE_SCOPE_ACCOUNTING_ONLY' and len(scope['models'])==39,'Pinned full candidate model scope incomplete')
    require(sha(args.policy_reconciliation)==POLICY_RECONCILIATION_SHA,'Current policy repair lacks its exact independent reconciliation')
    reconciled=load(args.policy_reconciliation)
    require(reconciled['status']=='FROZEN_CURRENT_POLICY_RECONCILED_AND_SYNTHETICALLY_RETESTED_ONLY'
            and reconciled['current_policy_sha256']==POLICY_SHA and reconciled['original_fixture_passes']==55
            and reconciled['additional_independent_guard_passes']==10 and reconciled['failures']==0,'Current policy repair/check evidence differs')
    policy=import_policy(args.policy_module)
    identity={'adapter_source_sha256':sha(__file__),'policy_source_sha256':sha(args.policy_module),'evidence_parser_sha256':sha(E.__file__),
              'policy_contract_sha256':sha(args.policy_dir/'policy_contract.json'),'model_candidate_scope_sha256':sha(scope_path),
              'policy_reconciliation_sha256':sha(args.policy_reconciliation),
              'raw_validation_sha256':sha(args.raw_validation),'panel_sha256':sha(args.root/'config/approved_accessions.txt'),
              **{k:sha(p) for k,p in bindings.items()},'full196_required':True,'scientific_stage05_status':'INDEPENDENT_CURATED_VALIDATION_REQUIRED'}
    return panel,freeze,scope,policy,identity

def normalized_sources(rows,sequences,replicons):
    reps={r['replicon']:r for r in replicons};groups=defaultdict(list);out={}
    for row in rows:groups[row['replicon']].append(row['locus_key'])
    for row in rows:
        key=row['locus_key'];require(key==row['assembly_accession']+'|'+row['replicon']+'|'+row['locus_tag'] and key not in out,'Exact source key malformed/duplicate')
        flags={field:strict_bool(row[field]) for field in BOOL_FIELDS};length=int(row['protein_aa_length']) if flags['protein_target_present'] else 0
        aa_sha=row['primary_faa_sequence_sha256'];require(flags['protein_target_present']==(key in sequences),'Source protein/FAA presence differs')
        if flags['protein_target_present']:
            require(len(sequences[key])==length and hashlib.sha256(sequences[key].encode()).hexdigest()==aa_sha,'Reopened actual primary AA identity/length differs')
        else:require(not aa_sha and not row['protein_aa_length'],'Untranslated source has fabricated primary AA')
        rep=reps[row['replicon']];linear=rep['documented_circular'] is not True
        out[key]={**row,**flags,'protein_aa_length':length,'linear_edge':linear and key in (groups[row['replicon']][0],groups[row['replicon']][-1])}
    require(set(sequences)=={k for k,v in out.items() if v['protein_target_present']},'Primary proteins dropped/added');return out

def queue_item(kind,assembly,identity,refs,payload,types=TYPES):
    item={'kind':kind,'assembly_accession':assembly,'affected_types':list(types),'identity':identity,
          'actual_evidence_refs':refs,'evidence':payload,'review_state':'PENDING_EXECUTED_REVIEW'}
    item['queue_id']='RQ_'+object_sha({'kind':kind,'assembly_accession':assembly,'identity':identity})[:28]
    item['queue_item_sha256']=object_sha(item);return item

def verify_review_refs(reader,review):
    """Every policy ref is reopened; nested refs cannot pass by shape alone."""
    if isinstance(review,dict):
        if set(['path','sha256','record_locator'])<=set(review):reader.resolve(review)
        else:
            for value in review.values():verify_review_refs(reader,value)
    elif isinstance(review,list):
        for value in review:verify_review_refs(reader,value)

def threshold_facts(domain,row,profile,scope=None,metadata=None):
    """Recompute native per-domain numerical filters, keeping raw rejections."""
    lo,hi=int(domain['alignment_from']),int(domain['alignment_to']);hlo,hhi=int(domain['hmm_from']),int(domain['hmm_to'])
    target_length=int(domain['target_length']) if 'target_length' in domain else int(row['protein_aa_length'])
    profile_length=int(profile['length']);require(1<=lo<=hi<=target_length and 1<=hlo<=hhi<=profile_length,'Native/source domain bounds differ')
    ie=finite(domain['independent_evalue']);require(ie>=0,'Negative domain Evalue')
    if scope is not None:
        settings=scope['native_settings'];cov=(hhi-hlo+1)/profile_length;target_cov=(hi-lo+1)/target_length
        minimum=finite(settings['coverage_profile']);maximum_ie=finite(settings['i_evalue_sel'])
        require(profile['threshold']==(['--cut_ga'] if settings['cut_ga'] and profile['has_ga'] else ['-E',format(settings['e_value_search'],'f')]),'Native search threshold differs from frozen profile/config')
        passed=ie<=maximum_ie and cov>=minimum
        return {'native_role_threshold_passed':passed,'threshold_receipt_verified':True,'native_profile_coverage':cov,
                'native_target_coverage':target_cov,'maximum_independent_evalue':maximum_ie,'minimum_profile_coverage':minimum,
                'native_search_threshold':profile['threshold'],'native_filter_basis':'MacSyFinder2.1.4 report.py inclusive coordinates + exact frozen scope config'}
    require(metadata is not None,'Pinned PADLOC metadata required')
    # These are the actual pinned PADLOC2 R defaults for missing metadata cells.
    def numeric_meta(name,default):
        value=metadata[name];return default if value in ('NA','','NaN') else finite(value)
    maximum_ie=numeric_meta('e.value.threshold',1e-5);minimum=numeric_meta('hmm.coverage.threshold',0.3);minimum_target=numeric_meta('target.coverage.threshold',0.3)
    cov=round((hhi-hlo)/profile_length,3);target_cov=round((hi-lo)/target_length,3)
    passed=ie<=maximum_ie and cov>=minimum and target_cov>=minimum_target
    return {'native_role_threshold_passed':passed,'threshold_receipt_verified':True,'native_profile_coverage':cov,
            'native_target_coverage':target_cov,'maximum_independent_evalue':maximum_ie,'minimum_profile_coverage':minimum,
            'minimum_target_coverage':minimum_target,'native_search_threshold':['PADLOC_NATIVE_DEFAULT_REPORTING'],
            'native_filter_basis':'Pinned PADLOC2 padloc.R noninclusive coordinate differences rounded3 + exact metadata/defaults; full top-domain/model selection remains separately reviewed'}

def join_original_domain(domain,reported):
    """Bind a derived PADLOC row to the actual original HMMER query section."""
    matches=[r for r in reported if r['target_name']==domain['target_name'] and int(r['domain_number'])==int(domain['domain_number'])]
    require(len(matches)==1,'Derived PADLOC domain lacks one original reported query domain')
    original=matches[0]
    require(original['profile_name']==domain['profile_name'] and int(original['profile_length'])==int(domain['profile_length']),
            'Derived PADLOC query/profile identity differs')
    for field in original:
        if field in ('target_name','profile_name'):continue
        require(finite(original[field])==finite(domain[field]),'Derived PADLOC/original query domain differs: '+field)
    return original

def preparation_gate(manifest,identity):
    require(manifest['status']=='FULL196_ACTUAL_SOURCE_NATIVE_EVIDENCE_QUEUE_PREPARED_REVIEW_PENDING'
            and manifest['identity']==dict(identity,phase='prepare') and manifest['assemblies']==196,
            'Actual prepared full196 queue identity differs')

def rotate_parts(parts,length,offset):
    """Exact zero-based half-open source intervals, keeping biological order."""
    require(isinstance(parts,list) and parts,'Source geometry missing')
    result=[]
    for part in parts:
        require(isinstance(part,list) and len(part)==3,'Source interval/strand shape differs')
        start,end,strand=part
        require(all(isinstance(v,int) and not isinstance(v,bool) for v in part) and 0<=start<end<=length and strand in (-1,1),'Invalid original source interval')
        lo=(start-offset)%length;hi=lo+(end-start)
        segments=[[lo,min(hi,length),strand]]
        if hi>length:
            segments.append([0,hi-length,strand])
            if strand==-1:segments.reverse()
        result.extend(segments)
    return result

def validate_rotation_evidence(context,queue,rotation):
    """Open and recompute a cached-domain classification's source geometry.

    A separate executed geometry/domain-map audit is mandatory too. Its status
    does not replace the direct coordinate, AA, ID, cached-domain and argv joins.
    """
    reader=context.reader;verify_review_refs(reader,rotation)
    context.policy.validate_rotation_receipt(rotation,context.sources)
    original=queue['evidence']['original_locus_order'];rep=queue['evidence']['source_replicon']
    require(rotation['original_locus_order']==original and rep['documented_circular'] is True,'Rotation omitted source context or wrapped undocumented replicon')
    geometry=reader.resolve(rotation['geometry_ref']);mapping=reader.resolve(rotation['domain_target_map_ref'])
    require(geometry['execution']=='EXECUTED_SOURCE_COORDINATE_CIRCULAR_PERMUTATION' and geometry['replicon']==rep['replicon']
            and geometry['replicon_length']==rep['gbff_length'],'Executed exact source geometry missing')
    length=int(rep['gbff_length']);offset=geometry['rotation_nt_offset_zero_based']
    require(isinstance(offset,int) and not isinstance(offset,bool) and 0<=offset<length,'Invalid nucleotide rotation offset')
    rows=geometry['loci'];by_key={r['locus_key']:r for r in rows}
    require(len(rows)==len(by_key)==len(original) and set(by_key)==set(original),'Rotated geometry drops/adds source context')
    rotated=rotation['rotated_locus_order'];positions={key:i for i,key in enumerate(rotated,1)}
    expected={}
    for ordinal,key in enumerate(original,1):
        source=context.sources[key];parts=json.loads(source['gbff_parts_zero_based_biological_order']);row=by_key[key]
        transformed=rotate_parts(parts,length,offset);expected[key]=transformed
        require(row['source_parts']==parts and row['rotated_parts']==transformed
            and row['original_context_ordinal']==ordinal and row['rotated_context_ordinal']==positions[key]
            and row['source_aa_sha256']==source['primary_faa_sequence_sha256'],'Actual rotated source interval/order/AA differs')
    physical=sorted(original,key=lambda key:(min(p[0] for p in expected[key]),original.index(key)))
    require(rotated==physical,'Rotated rank order differs from actual transformed coordinates')
    cached=reader.resolve(rotation['cached_domain_ref']);require(isinstance(cached,str),'Cached native domain ref must resolve actual text')
    pad_hits={hid:hit for hid,hit in context.hits.items() if hit['detector']=='PADLOC' and hit['locus_key'] in original}
    known_dom={r['raw_file_sha256'] for r in context.domain_rows if r['detector']=='PADLOC'}
    native=load(context.execution/'padloc/native_call_inventory.json')
    original_dom=context.execution/'padloc'/native['classification_attempt']/'native/proteins.domtblout'
    known_dom.add(reader.hash(original_dom))
    require(rotation['input_cached_dom_sha256'] in known_dom and rotation['cached_domain_ref']['sha256']==rotation['input_cached_dom_sha256'],
            'Rotated classification did not use original byte-identical full cached PADLOC domains')
    require(mapping['execution']=='EXECUTED_EXACT_SOURCE_TARGET_AND_CACHED_DOMAIN_REMAPPING','Domain target mapping not executed')
    domain_rows=mapping['domains'];mapped={r['hit_id']:r for r in domain_rows}
    require(len(domain_rows)==len(mapped)==len(pad_hits) and set(mapped)==set(pad_hits),'Rotation omitted/added cached replicon domains')
    protein_order=[key for key in rotated if context.sources[key]['protein_target_present']]
    for hid,hit in pad_hits.items():
        key=hit['locus_key'];row=mapped[hid]
        require(row['locus_key']==row['target_id_before']==row['target_id_after']==key
                and row['native_domain_record_sha256']==object_sha(hit['domain'])
                and row['source_aa_sha256']==context.sources[key]['primary_faa_sequence_sha256']
                and row['original_protein_ordinal']==int(context.sources[key]['protein_ordinal_on_replicon'])
                and row['rotated_protein_ordinal']==protein_order.index(key)+1,'Actual cached domain/target/AA/rank remapping differs')
    faa_path=reader.path(rotation['rotated_faa_ref']['path']);reader.resolve(rotation['rotated_faa_ref'])
    sequences=fasta(faa_path)
    require(set(sequences)==set(context.sequences) and all(sequences[k]==context.sequences[k] for k in sequences),'Rotation altered/dropped/added original assembly primary proteins')
    gff_path=reader.path(rotation['rotated_gff_ref']['path']);reader.resolve(rotation['rotated_gff_ref'])
    gff={}
    for line in gff_path.read_text().splitlines():
        if not line or line.startswith('#'):continue
        fields=line.split('\t');require(len(fields)==9 and fields[2]=='CDS','Rotated detector GFF contains malformed/non-CDS row')
        attributes=dict(item.split('=',1) for item in fields[8].split(';') if '=' in item);key=attributes.get('ID','').removeprefix('cds-')
        require(key in context.sequences and key not in gff and fields[0]==context.sources[key]['replicon'],'Rotated GFF exact key/replicon differs')
        gff[key]=fields
    require(set(gff)==set(context.sequences),'Rotated GFF targets dropped/added')
    for key in context.sequences:
        parts=expected[key] if key in expected else json.loads(context.sources[key]['gbff_parts_zero_based_biological_order'])
        fields=gff[key];require(int(fields[3])==min(p[0] for p in parts)+1 and int(fields[4])==max(p[1] for p in parts)
            and fields[6]==('+' if int(context.sources[key]['gbff_strand'])==1 else '-'),'Rotated GFF bounds/strand differ from transformed source geometry')
    command=reader.resolve(rotation['native_command_ref']);launch=reader.resolve(rotation['native_launch_ref'])
    stdout=reader.resolve(rotation['native_stdout_ref'])
    require(command['execution']=='PROCESS_EXITED' and command['exit_code']==0 and command['child_pid']==launch['child_pid']>0
            and command['argv']==launch['argv'] and command['identity']==launch['identity']
            and command['identity']['freeze_sha256']==sha(context.args.execution/'execution_freeze.json')
            and command['stdout_sha256']==rotation['native_stdout_ref']['sha256'],'Actual cached-domain classifier command/exit/source proof differs')
    argv=command['argv']
    require(Path(argv[0]).resolve()==(context.args.environment_dir/'bin/padloc').resolve()
            and sha(argv[0])==context.freeze['tools']['padloc'],'Rotation classification did not use pinned actual PADLOC executable')
    for option,path in [('--faa',faa_path),('--gff',gff_path),('--data',context.args.padloc_db)]:
        require(argv.count(option)==1 and Path(argv[argv.index(option)+1]).resolve()==Path(path).resolve(),'Native rotation classifier argv differs: '+option)
    require(argv.count('--cpu')==1 and argv[argv.index('--cpu')+1]=='2' and 'domtblout already exists' in stdout,
            'Native rotation classifier did not confirm reuse of cached domains under two threads')
    require(argv.count('--outdir')==1,'Native rotated classifier output scope missing')
    output=Path(argv[argv.index('--outdir')+1]).resolve();cached_path=reader.path(rotation['cached_domain_ref']['path'])
    require(cached_path==output/(faa_path.stem+'.domtblout'),'Verified cached DOM was not at the actual native reused input path')
    validation=reader.resolve(rotation['independent_validation_ref'])
    require(validation['status']=='PASS_CACHED_DOMAIN_ROTATION_GEOMETRY_AND_SOURCE_ACCOUNTING'
            and validation['biological_HMM_searches_repeated']==0 and validation['assembly_accession']==context.accession
            and validation['replicon']==rep['replicon'],'Separate executed rotation geometry/domain audit missing')
    for field,ref in [('geometry_sha256','geometry_ref'),('domain_target_map_sha256','domain_target_map_ref'),
                      ('native_command_sha256','native_command_ref'),('rotated_faa_sha256','rotated_faa_ref'),('rotated_gff_sha256','rotated_gff_ref'),
                      ('cached_domain_sha256','cached_domain_ref'),('validator_source_sha256','independent_validator_source_ref')]:
        require(validation[field]==rotation[ref]['sha256'],'Independent rotation audit payload/source binding differs: '+field)
    reader.resolve(rotation['independent_validator_source_ref'])
    return True

def padloc_selection_facts(hits):
    """Recompute native per-model best-domain/top5/role ranking, preserving raw hits.

    This checks domain eligibility only. Clustering, minimum architecture and
    functional interpretation remain distinct native/curation evidence gates.
    Stable domain order is inherited from the verified original domtbl rows.
    """
    groups=defaultdict(list);priority={'core_genes':4,'secondary_genes':3,'neutral_genes':2,'prohibited_genes':1}
    for index,(hid,hit) in enumerate(hits.items()):
        if hit['detector']!='PADLOC':continue
        hit['native_numerical_domain_filter_passed']=hit['native_role_threshold_passed']
        hit['native_selected_model_ids']=[]
        roles=defaultdict(list)
        for assignment in hit['native_model_roles']:
            require(assignment['role_class'] in priority,'Unknown pinned PADLOC role class')
            roles[assignment['model']].append(priority[assignment['role_class']])
        for model,values in roles.items():groups[(model,hit['locus_key'])].append((hid,max(values),index))
    for (model,_),members in groups.items():
        minima={}
        for hid,_,_ in members:
            hit=hits[hid];name=hit['profile_name'];ie=finite(hit['domain']['independent_evalue'])
            minima[name]=min(minima.get(name,ie),ie)
        best=[item for item in members if finite(hits[item[0]]['domain']['independent_evalue'])==minima[hits[item[0]]['profile_name']]]
        cutoff=sorted(finite(hits[item[0]]['domain']['independent_evalue']) for item in best)[min(4,len(best)-1)]
        eligible=[item for item in best if finite(hits[item[0]]['domain']['independent_evalue'])<=cutoff and hits[item[0]]['native_numerical_domain_filter_passed']]
        def ranking(item):
            hid,role,index=item;h=hits[hid];d=h['domain']
            combined=(int(d['hmm_to'])-int(d['hmm_from']))/int(d['profile_length'])+(int(d['alignment_to'])-int(d['alignment_from']))/h['target_length']
            return -role,finite(d['independent_evalue']),-combined,index
        if eligible:hits[min(eligible,key=ranking)[0]]['native_selected_model_ids'].append(model)
    for hit in hits.values():
        if hit['detector']=='PADLOC':
            hit['native_selected_model_ids'].sort()
            hit['native_role_threshold_passed']=hit['native_numerical_domain_filter_passed'] and bool(hit['native_selected_model_ids'])
            hit['native_filter_basis']='Pinned PADLOC2 numeric thresholds + per-model minimum-iE domains, top5 with ties, core/secondary/neutral/prohibited rank, iE and combined coverage; no architecture completeness inferred'

class AssemblyEvidence:
    def __init__(self,args,accession,freeze,scope,policy):
        self.args=args;self.accession=accession;self.freeze=freeze;self.policy=policy
        self.directory=args.inventory/'assemblies'/accession;self.execution=args.execution/'assemblies'/accession
        self.source=args.source/'assemblies'/accession;self.bundle=args.bundle/'assemblies'/accession
        self.reader=EvidenceReader(args.root,[args.source,args.bundle,args.execution,args.inventory,args.policy_dir,
                                             args.models_dir,args.padloc_db,args.environment_dir,args.evidence_dir])
        self.scope={(r['detector'],r['model_id']):r for r in scope['models']};require(len(self.scope)==39,'Duplicate pinned model scope')
        source_receipt=load(self.source/'build_receipt.json');derived=load(self.bundle/'bundle_receipt.json')
        require(derived['source_receipt_sha256']==sha(self.source/'build_receipt.json'),'Current primary source receipt differs')
        entries={r['path']:r for r in source_receipt['output_files']}
        for name in ('locus_crosswalk.tsv','replicon_manifest.json',accession+'.faa'):
            path=self.source/name;entry=entries[name]
            require(path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],'Reopened source bytes differ: '+name)
        for entry in derived['output_files']:
            path=inside(self.bundle,self.bundle/entry['path']);require(path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],'Reopened bundle bytes differ')
        require(sha(self.bundle/'locus_crosswalk.tsv')==sha(self.directory/'source_locus_crosswalk.tsv')
                and sha(self.bundle/'replicon_topology.tsv')==sha(self.directory/'source_replicon_topology.tsv'),'Inventory source/replicon copy differs')
        self.rows=table(self.directory/'source_locus_crosswalk.tsv');original={r['locus_key']:r for r in table(self.source/'locus_crosswalk.tsv')}
        require(len(original)==len(self.rows) and all(all(row.get(k)==v for k,v in original[row['locus_key']].items()) for row in self.rows),'Source locus field join differs; aggregate order is not assumed')
        self.replicons=load(self.source/'replicon_manifest.json');self.sequences=fasta(self.source/(accession+'.faa'))
        self.sources=normalized_sources(self.rows,self.sequences,self.replicons)
        self.source_refs={row['locus_key']:self.reader.make_ref(self.directory/'source_locus_crosswalk.tsv','tsv:'+str(i),row) for i,row in enumerate(self.rows,1)}
        self.aa_refs={key:self.reader.make_ref(self.source/(accession+'.faa'),'fasta:'+key,{'target_id':key,'sequence':sequence}) for key,sequence in self.sequences.items()}
        self.protein_map={row['df_bundle_target_id']:row for row in self.rows if row['protein_target_present']=='True'}
        self.pad_profiles={p['query_name']:p for p in freeze['padloc_profiles']}
        self.pad_meta={r['hmm.name']:r for r in table(args.padloc_db/'hmm_meta.txt')}
        require(sha(args.padloc_db/'hmm_meta.txt')==freeze['padloc_metadata_system_files']['hmm_meta.txt'],'Pinned PADLOC metadata changed')
        self.domain_rows=table(self.directory/'all_native_profile_domains.tsv');self.query_rows=table(self.directory/'all_native_query_completion.tsv')
        self.call_rows=table(self.directory/'all_native_system_candidate_rows.tsv');self.filtered_rows=table(self.directory/'all_native_filtered_profile_hits.tsv')
        self.hits={};self.queue=[];self.scopes={};self.raw_domains={};self.native_completion_refs=defaultdict(list)
        self.bind_native_queries()
        self.bind_domains()
        self.bind_candidates()
        self.bind_contexts()

    def family_scope(self,row):
        # Derive the exact native task/family from the verified raw relative path.
        match=re.fullmatch(r'(defensefinder/(?:gembase|singletons/rep[0-9]{6}))/families/(DefenseFinder|RM|Cas)/.+',row['raw_file'])
        require(match and match.group(2)==row['family'],'Native raw task/family path differs')
        task,family=match.groups();key=(task,family)
        if key not in self.scopes:
            path=self.execution/task/'families'/family/'scope.json';scope=load(path)
            require(scope['family']==family and scope['target_count']==sum(r['df_bundle_task']==task for r in self.rows if r['protein_target_present']=='True'),'Native scope source task count differs')
            scope['_path']=path;self.scopes[key]=scope
        return self.scopes[key]

    def bind_native_queries(self):
        wanted=defaultdict(dict)
        for index,row in enumerate(self.query_rows,1):
            require(row['assembly_accession']==self.accession and row['evidence_state']=='COMPLETE_QUERY_NOT_CURATED_ABSENCE','Unverified native query inventory')
            path=inside(self.execution,self.execution/row['raw_file']);require(self.reader.hash(path)==row['raw_file_sha256'],'Reopened raw query file differs')
            name=row['query_name'];require(name not in wanted[path],'Duplicate authoritative raw query')
            if row['detector']=='PADLOC':profile=self.pad_profiles[name];targets={k:v['protein_aa_length'] for k,v in self.sources.items() if v['protein_target_present']}
            else:
                scope=self.family_scope(row);matches=[p for p in scope['profiles'] if p['query_name']==name];require(len(matches)==1,'Native profile lookup ambiguous');profile=matches[0]
                task=row['task'];targets={r['df_bundle_target_id']:self.sources[r['locus_key']] for r in self.rows if r['df_bundle_task']==task and r['protein_target_present']=='True'}
            require(profile['profile_sha256']==row['profile_sha256'] and int(row['target_sequences_searched'])==len(targets),'Native query profile/target identity differs')
            require(self.reader.hash(Path(profile['profile_path']))==profile['profile_sha256'],'Reopened native profile differs')
            wanted[path][name]=(row,profile,targets)
            ref=self.reader.make_ref(self.directory/'all_native_query_completion.tsv','tsv:'+str(index),row)
            self.native_completion_refs[row['detector']].append(ref)
        verified=set()
        for path,queries in wanted.items():
            for first,last,block in E.query_sections(path):
                name=block.splitlines()[0].split()[1]
                if name not in queries:continue
                row,profile,targets=queries[name];identity=(path,name);require(identity not in verified,'Duplicate original query section')
                proof=E.query_proof(block,name,profile['length'],len(targets),targets=targets,include_domains=True)
                require(proof['query_section_sha256']==row['query_section_sha256'] and proof['raw_reported_domains']==int(row['raw_reported_domains']),'Reopened raw completion/domain proof differs')
                self.raw_domains[(path,name)]=proof['native_domains'];verified.add(identity)
            require(all((path,name) in verified for name in queries),'Authoritative query section missing')
        require(sum(r['detector']=='PADLOC' for r in self.query_rows)==5027,'Incomplete PADLOC query scope')
        require({r['query_name'] for r in self.query_rows if r['detector']=='PADLOC'}==set(self.pad_profiles),'PADLOC authoritative profile identities incomplete')
        df_tasks={r['task'] for r in self.query_rows if r['detector']=='DefenseFinder'}
        require(df_tasks=={r['df_bundle_task'] for r in self.rows if r['protein_target_present']=='True'},'DF authoritative source task set incomplete')
        require(sum(r['detector']=='DefenseFinder' for r in self.query_rows)==1751*len(df_tasks),'Incomplete DF full3family query scope')
        for task in df_tasks:
            require(Counter(r['family'] for r in self.query_rows if r['detector']=='DefenseFinder' and r['task']==task)==Counter({'DefenseFinder':1092,'RM':134,'Cas':525}),'Native task family scope incomplete')
            for family in ('DefenseFinder','RM','Cas'):
                profiles=self.scopes[(task,family)]['profiles']
                require({r['query_name'] for r in self.query_rows if r['detector']=='DefenseFinder' and r['task']==task and r['family']==family}=={p['query_name'] for p in profiles},'DF authoritative family profile identities incomplete')
        # Query facts above are reopened for the full scope. Reference immutable
        # complete manifests rather than copying thousands of refs into4cells.
        self.native_completion_refs=defaultdict(list)
        for detector,paths in [('PADLOC',[self.execution/'padloc/complete.json']),
                               ('DefenseFinder',[self.execution/task/'complete.json' for task in sorted(df_tasks)])]:
            for path in paths:
                proof=load(path);require(proof['execution']=='NATIVE_OUTPUTS_CHECKED' and proof['scientific_curation']=='NOT_RUN'
                    and proof['identity']['freeze_sha256']==sha(self.args.execution/'execution_freeze.json'),'Native completion proof freeze/state differs')
                require(proof['files'],'Empty native completion manifest')
                for name,digest in proof['files'].items():
                    require(self.reader.hash(inside(path.parent,path.parent/name))==digest,'Reopened native task evidence changed: '+name)
                self.native_completion_refs[detector].append(self.reader.make_ref(path,'json:',proof))

    def bind_domains(self):
        pad_domains_cache={};df_query_lookup={(r['raw_file'],r['query_name']):r for r in self.query_rows if r['detector']=='DefenseFinder'}
        pad_query_lookup={r['query_name']:inside(self.execution,self.execution/r['raw_file']) for r in self.query_rows if r['detector']=='PADLOC'}
        for index,row in enumerate(self.domain_rows,1):
            key=row['locus_key'];source=self.sources[key]
            require(row['assembly_accession']==self.accession and all(row[field]==str(source[field]) for field in BOOL_FIELDS),'Native domain source flags differ')
            domain=json.loads(row['native_domain_json']);path=inside(self.execution,self.execution/row['raw_file'])
            require(self.reader.hash(path)==row['raw_file_sha256'] and int(row['protein_aa_length'])==source['protein_aa_length'],'Native domain actual bytes/source length differ')
            if row['detector']=='PADLOC':
                if path not in pad_domains_cache:
                    targets={k:v['protein_aa_length'] for k,v in self.sources.items() if v['protein_target_present']}
                    pad_domains_cache[path]=E.domtbl(path,targets,self.pad_profiles)
                native=[v for v in pad_domains_cache[path] if v['target_name']==key and v['profile_name']==row['profile_name'] and int(v['domain_number'])==int(domain['domain_number'])]
                require(len(native)==1 and {k:v for k,v in domain.items() if k!='profile_metadata'}==native[0],'Reopened actual PADLOC domain differs')
                join_original_domain(domain,self.raw_domains[(pad_query_lookup[row['profile_name']],row['profile_name'])])
                metadata=self.pad_meta[row['profile_name']];require(domain['profile_metadata']==metadata,'PADLOC domain native metadata differs')
                profile=self.pad_profiles[row['profile_name']];facts=threshold_facts(domain,row,profile,metadata=metadata)
            else:
                scope=self.family_scope(row);profiles=[p for p in scope['profiles'] if p['query_name']==row['profile_name']];require(len(profiles)==1,'Native domain profile ambiguous');profile=profiles[0]
                require((row['raw_file'],row['profile_name']) in df_query_lookup,'Raw DF domain lacks authoritative query proof')
                # DOMAIN_FIELDS stores source fields, not df_bundle_target_id.
                target=self.sources[key]['df_bundle_target_id']
                matches=[v for v in self.raw_domains[(path,row['profile_name'])] if v['target_name']==target and int(v['domain_number'])==int(domain['domain_number'])]
                require(len(matches)==1 and matches[0]==domain,'Reopened actual DF domain differs')
                facts=threshold_facts(domain,row,profile,scope=scope)
                # Every pass must also have its actual native filtered extract.
                filtered=[json.loads(r['native_row_json']) for r in self.filtered_rows if r['family']==row['family'] and r['locus_key']==key and r['gene_name']==profile['gene_name']]
                matched=[r for r in filtered if int(r['hit_begin_match'])==int(domain['alignment_from']) and int(r['hit_end_match'])==int(domain['alignment_to']) and finite(r['i_eval'])==finite(domain['independent_evalue']) and finite(r['hit_score'])==finite(domain['domain_score'])]
                require(bool(matched)==facts['native_role_threshold_passed'],'Native filtered extract/raw numerical filter differs')
            require(row['profile_sha256']==profile['profile_sha256'],'Raw domain profile SHA differs')
            ref=self.reader.make_ref(self.directory/'all_native_profile_domains.tsv','tsv:'+str(index),row)
            hit_id='DH_'+object_sha({'detector':row['detector'],'family':row['family'],'raw_file':row['raw_file'],'locus_key':key,'profile_sha256':row['profile_sha256'],'domain':domain})[:28]
            require(hit_id not in self.hits,'Repeated native domain identity')
            hit={'hit_id':hit_id,'locus_key':key,'source_aa_sha256':source['primary_faa_sequence_sha256'],'profile_sha256':profile['profile_sha256'],
                 'target_length':source['protein_aa_length'],'alignment_from':int(domain['alignment_from']),'alignment_to':int(domain['alignment_to']),
                 'raw_ref':ref,'profile_name':row['profile_name'],'detector':row['detector'],'family':row['family'],
                 'native_model_roles':json.loads(row['model_roles_json']),'domain':domain,**facts}
            self.hits[hit_id]=hit
        padloc_selection_facts(self.hits)
        for hit_id,hit in self.hits.items():
            key=hit['locus_key'];self.queue.append(queue_item('RAW_DOMAIN',self.accession,{'hit_id':hit_id},[hit['raw_ref'],self.source_refs[key],self.aa_refs[key]],hit))

    def model_ref(self,entry):
        if entry['detector']=='PADLOC':path=self.args.padloc_db/'sys'/entry['source_member'].split('/sys/',1)[1]
        else:path=self.args.models_dir/entry['model_id'].split('/',1)[0]/'definitions'/(entry['model_id'].split('/',1)[1]+'.xml')
        require(self.reader.hash(path)==entry['source_sha256'],'Pinned candidate definition changed')
        lines=path.read_text().splitlines(keepends=True);return self.reader.make_ref(path,'text:1-'+str(len(lines)),''.join(lines))

    def bind_candidates(self):
        groups={};native_cache={}
        for index,row in enumerate(self.call_rows,1):
            key=row['locus_key'];require(key in self.sources and row['assembly_accession']==self.accession,'Native call source locus missing')
            native=json.loads(row['native_row_json']);path=inside(self.execution,self.execution/row['raw_file'])
            require(self.reader.hash(path)==row['raw_file_sha256'],'Actual native call table changed')
            if path not in native_cache:
                if row['detector']=='PADLOC':
                    with path.open(encoding='utf-8',newline='') as stream:native_cache[path]=list(csv.DictReader(stream))
                else:native_cache[path]=E.native_tsv(path,'# No Rejected candidates' if path.name=='rejected_candidates.tsv' else '# No Systems found')
            base={k:v for k,v in native.items() if k not in ('assembly_accession','source_replicon','locus_key','protein_accession')}
            matches=[(i,r) for i,r in enumerate(native_cache[path],1) if r==base]
            require(len(matches)==1,'Actual native candidate row missing/ambiguous')
            raw_ref=self.reader.make_ref(path,('csv:' if row['detector']=='PADLOC' else 'native_tsv:')+str(matches[0][0]),base)
            if row['detector']=='PADLOC':
                require(native['target.name']==key and native['seqid']==self.sources[key]['replicon'],'Native PADLOC candidate source boundary differs')
                group_id=native['system.number'];call_class='PADLOC_NATIVE_SYSTEM'
            else:
                require(native['hit_id']==self.sources[key]['df_bundle_target_id'] and native['replicon']==self.sources[key]['df_bundle_replicon_name']
                        and int(native['hit_pos'])==int(self.sources[key]['df_bundle_sequence_rank']),'Native DF candidate source order/boundary differs')
                # Rejected candidates use native9-column schema, not sys_id/22.
                group_id=native['candidate_id'] if row['native_table']=='rejected_candidates.tsv' else native['sys_id']
                call_class='REJECTED_NATIVE_CANDIDATE' if row['native_table']=='rejected_candidates.tsv' else 'NATIVE_SYSTEM_CANDIDATE'
            identity=(row['detector'],str(path.parent),row['model_fqn'],group_id,call_class,self.sources[key]['replicon'])
            if identity not in groups:groups[identity]={'rows':[],'refs':[],'loci':set(),'model':self.scope.get((row['detector'],row['model_fqn']))}
            group=groups[identity];group['rows'].append(row);group['refs'].extend([raw_ref,self.reader.make_ref(self.directory/'all_native_system_candidate_rows.tsv','tsv:'+str(index),row)])
            group['loci'].add(key)
        candidates=[]
        for identity,group in groups.items():
            detector,_,model_id,group_id,call_class,replicon=identity;entry=group['model']
            facts={'detector':detector,'model_fqn':model_id,'native_group_id':group_id,'native_call_class':call_class,
                   'locus_keys':sorted(group['loci']),'raw_rows':group['rows'],'model_scope':entry,
                   'related_hit_ids':sorted(hid for hid,h in self.hits.items() if h['locus_key'] in group['loci'])}
            refs=group['refs']+[self.source_refs[key] for key in sorted(group['loci'])]
            if entry is None:
                self.queue.append(queue_item('NATIVE_MODEL_CONTEXT',self.accession,{'native_group':identity},refs,facts));continue
            refs.append(self.model_ref(entry))
            candidate={'assembly_accession':self.accession,'rm_type':entry['proposed_type'],'subtype':entry['subtype'],
                       'locus_keys':sorted(group['loci']),'detector':detector,'native_candidate_refs':refs}
            candidates.append(candidate)
        self.candidates=self.policy.deduplicate_exact(candidates)
        # Exact type+locus dedup merges table/detector duplicates only. Multiple
        # subtypes retain a conflict; interpretation cannot silently choose one.
        for candidate in self.candidates:
            candidate['subtype']=candidate['subtypes'][0] if len(candidate['subtypes'])==1 else None
            payload={**candidate,'related_hit_ids':sorted(hid for hid,h in self.hits.items() if h['locus_key'] in candidate['locus_keys']),
                     'source_loci':[self.sources[key] for key in candidate['locus_keys']]}
            refs=candidate['native_candidate_refs']+[self.source_refs[key] for key in candidate['locus_keys']]
            self.queue.append(queue_item('NATIVE_CANDIDATE',self.accession,{'candidate_id':candidate['candidate_id']},refs,payload))

    def bind_contexts(self):
        annotations={r['locus_key']:r for r in table(self.directory/'source_annotation_review.tsv')}
        for key,source in self.sources.items():
            issues=[flag for flag in ('source_pseudo_any','partial_or_fuzzy','origin_spanning','requires_coordinate_review','linear_edge') if source[flag]]
            if not source['protein_target_present']:issues.append('NO_PRIMARY_PROTEIN_TARGET')
            if key in annotations:issues.append('PUBLISHED_SOURCE_ANNOTATION_REVIEW')
            if issues:
                self.queue.append(queue_item('SOURCE_CONTEXT',self.accession,{'locus_key':key},[self.source_refs[key]],
                                             {'locus_key':key,'source':source,'issues':issues,'related_hit_ids':sorted(h for h,v in self.hits.items() if v['locus_key']==key)}))
        for index,rep in enumerate(self.replicons):
            ref=self.reader.make_ref(self.source/'replicon_manifest.json','json:/'+str(index),rep)
            if rep['primary_protein_targets']==0:
                self.queue.append(queue_item('EMPTY_REPLICON',self.accession,{'replicon':rep['replicon']},[ref],rep))
            if rep['documented_circular'] is True:
                keys=[r['locus_key'] for r in self.rows if r['replicon']==rep['replicon']]
                self.queue.append(queue_item('CIRCULAR_ORIGIN_CONTEXT',self.accession,{'replicon':rep['replicon']},[ref],
                                             {'replicon':rep['replicon'],'source_replicon':rep,'original_locus_order':keys,
                                              'source_geometry_independently_verified':False,
                                              'biological_HMM_searches_repeated':0,
                                              'review_requirement':'Assess real neighborhoods/origin; no role, intactness or absence inferred from circularity'}))
        ids=[q['queue_id'] for q in self.queue];require(len(ids)==len(set(ids)),'Duplicate required evidence queue item')

    def snapshot(self):
        files=[self.directory/name for name in ('all_native_profile_domains.tsv','all_native_filtered_profile_hits.tsv','all_native_system_candidate_rows.tsv',
            'all_native_query_completion.tsv','source_locus_crosswalk.tsv','source_replicon_topology.tsv','source_annotation_review.tsv','replicon_search_states.tsv')]
        files += [self.source/'build_receipt.json',self.source/'replicon_manifest.json',self.source/(self.accession+'.faa'),self.bundle/'bundle_receipt.json']
        return {str(p.relative_to(self.args.root).as_posix()):sha(p) for p in files}

    def prepared(self):
        return {'assembly_accession':self.accession,'status':'ACTUAL_NATIVE_SOURCE_EVIDENCE_QUEUE_PREPARED_REVIEW_PENDING',
                'native_search':'INDEPENDENT_FULL_SCOPE_RAW_AUDIT_PASSED','architecture_review':'NOT_RUN',
                'source_snapshot':self.snapshot(),'source_context_loci':len(self.sources),'protein_loci':len(self.sequences),
                'replicons':len(self.replicons),'empty_replicons':sum(r['primary_protein_targets']==0 for r in self.replicons),
                'raw_domains':len(self.hits),'native_candidates':len(self.candidates),'queue_counts':dict(Counter(q['kind'] for q in self.queue)),
                'native_completion_refs':dict(self.native_completion_refs),'queue':self.queue}

def review_record(queue,record,reader,snapshot_sha):
    require(record['queue_id']==queue['queue_id'] and record['queue_item_sha256']==queue['queue_item_sha256']
            and record['source_snapshot_sha256']==snapshot_sha,'Executed review queue/source snapshot differs')
    require(record['execution']=='EXECUTED_HASH_BOUND_EVIDENCE_REVIEW','Review not actually recorded as executed')
    require(isinstance(record.get('rationale'),str) and record['rationale'].strip(),'Concise scientific interpretation basis missing')
    verify_review_refs(reader,record);reader.refs(record.get('evidence_refs'))
    expected={object_sha(ref) for ref in queue['actual_evidence_refs']}
    used={object_sha(ref) for ref in record.get('reopened_queue_evidence_refs',[])}
    require(expected<=used,'Review omitted required actual queued source/native evidence')
    for ref in record['reopened_queue_evidence_refs']:reader.resolve(ref)
    decisions=record['affected_type_decisions']
    require(set(decisions)==set(queue['affected_types']) and all(v in ('RESOLVED_WITH_EXECUTED_BASIS','UNRESOLVED') for v in decisions.values()),
            'Every affected type needs an explicit honest review outcome')
    return decisions

def apply_candidate(context,candidate,record):
    """Only executed role/source/domain/context review produces typed results."""
    review=record['candidate_review'];candidate=dict(candidate)
    extra=record.get('additional_source_locus_keys',[])
    require(isinstance(extra,list) and len(extra)==len(set(extra)) and not set(extra)&set(candidate['locus_keys']),'Candidate expansion adds repeated/native existing locus')
    if extra:
        require(record.get('candidate_expansion_execution')=='EXECUTED_SOURCE_NEIGHBORHOOD_REVIEW'
                and isinstance(record.get('candidate_expansion_rationale'),str) and record['candidate_expansion_rationale'].strip(),'Candidate source extension not explicitly reviewed')
        context.reader.refs(record.get('candidate_expansion_basis_refs'))
        require(all(key in context.sources for key in extra),'Additional candidate locus absent from actual source')
        candidate['locus_keys']=sorted(candidate['locus_keys']+extra)
    mapped=review['rm_type']
    if mapped!=candidate['rm_type']:
        require(mapped in TYPES and record.get('type_mapping_execution')=='EXECUTED_SOURCE_DOMAIN_CONTEXT_TYPE_MAPPING',
                'Native proposed type changed without explicit executed mapping')
        context.reader.refs(record.get('type_mapping_basis_refs'));candidate['rm_type']=mapped
    # Frozen native subtype disagreement cannot be silently discarded.
    if candidate.get('subtype_conflict'):
        require(record.get('subtype_resolution_execution')=='EXECUTED_SOURCE_DOMAIN_CONTEXT_SUBTYPE_REVIEW','Native detector subtype disagreement unreviewed')
        context.reader.refs(record.get('subtype_resolution_basis_refs'));candidate['subtype']=record['reviewed_subtype']
    identity,cid=context.policy.canonical_candidate(candidate)
    require(review['candidate_id']==cid,'Review ID does not bind actual complete reviewed locus/type set')
    verify_review_refs(context.reader,review)
    # Source facts/AA and raw threshold flags were independently rebuilt by
    # AssemblyEvidence; they are never accepted from the review document.
    if review['decision']=='UNCERTAIN' and not review.get('roles'):
        require(review['execution']=='EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW' and review['rm_type']==candidate['rm_type']
                and review['functional_evidence_grade']=='PREDICTED_ARCHITECTURE_ONLY'
                and review.get('architecture_assignment')=='UNRESOLVED_AFTER_EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW',
                'Unassigned architecture cannot claim a role or completed prediction')
        context.reader.refs(review.get('source_context_refs'));context.reader.refs(review.get('architecture_basis_refs'))
        require(all(context.source_refs[key] in review['source_context_refs'] for key in candidate['locus_keys'])
                and all(ref in review['architecture_basis_refs'] for ref in candidate['native_candidate_refs']),
                'Unresolved interpretation omitted actual candidate/source evidence')
        result={'state':'UNCERTAIN','reason':'UNRESOLVED_AFTER_EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW','functional_evidence_grade':'NOT_ESTABLISHED'}
    elif candidate['rm_type'] is None and review['decision'] in ('REVIEWED_ORPHAN_MTASE','REVIEWED_GENERIC_NUCLEASE','REVIEWED_REPAIR_OR_NON_RM'):
        context.policy.validate_role_evidence(candidate,review,context.sources,context.hits)
        context.reader.refs(review.get('exclusion_basis_refs'))
        result={'state':'UNCERTAIN','excluded_from_type_cell':True,'locus_annotation_state':review['decision'],'functional_evidence_grade':'NOT_ESTABLISHED'}
    else:result=context.policy.classify_candidate(candidate,review,context.sources,context.hits)
    used_hits=set()
    for role in review.get('roles',[]):
        for hid in role['hit_ids']:
            hit=context.hits[hid];used_hits.add(hid)
            require(hit['raw_ref'] in role['functional_domain_basis_refs'] or hit['raw_ref'] in review['architecture_basis_refs'],
                    'Functional role basis omitted its reopened exact native domain')
            require(context.source_refs[role['locus_key']] in review['source_context_refs'],
                    'Functional role source basis omitted reopened exact source row')
            require(context.aa_refs[role['locus_key']] in role['functional_domain_basis_refs'],
                    'Functional role omitted reopened actual primary AA record')
    if result['state']=='COMPLETE_PREDICTED':
        require(all(hit in context.hits for hit in used_hits),'Complete architecture contains invented domain')
        require(record.get('overlap_review_execution')=='EXECUTED_EXACT_LOCUS_COUNTING_REVIEW' if candidate.get('overlapping_candidate_ids') else True,
                'Overlapping native candidates lack explicit biological counting review')
        if candidate.get('overlapping_candidate_ids'):context.reader.refs(record.get('overlap_review_basis_refs'))
    return {**identity,'candidate_id':cid,'native_candidate_id':candidate.get('candidate_id'),'native_candidate_refs':candidate['native_candidate_refs'],
            'review_record_sha256':object_sha(record),'result':result,'used_hit_ids':sorted(used_hits)}

def apply_assembly(context,prepared,document):
    require(document['assembly_accession']==context.accession and document['prepared_queue_sha256']==object_sha(prepared),'Review document targets different actual queue')
    require(document['execution']=='EXECUTED_FULL_REQUIRED_EVIDENCE_REVIEW','Assembly evidence review not executed')
    require(context.snapshot()==prepared['source_snapshot'],'Current actual source/native inventory differs from prepared queue')
    snapshots=object_sha(prepared['source_snapshot']);records=document['reviews'];by_id={r['queue_id']:r for r in records}
    require(len(by_id)==len(records) and set(by_id)=={q['queue_id'] for q in context.queue},'Every required candidate/domain/source/empty/origin item must have exactly one review')
    unresolved={t:Counter() for t in TYPES};candidate_results=[];used_hits=set();domain_dispositions={};decisions={}
    kind_field={'SOURCE_CONTEXT':'unresolved_source_contexts','EMPTY_REPLICON':'unresolved_empty_replicons',
                'CIRCULAR_ORIGIN_CONTEXT':'unresolved_origin_classifications','RAW_DOMAIN':'unresolved_model_mappings',
                'NATIVE_MODEL_CONTEXT':'unresolved_model_mappings'}
    for queue in context.queue:
        record=by_id[queue['queue_id']];outcomes=review_record(queue,record,context.reader,snapshots);decisions[queue['queue_id']]=outcomes
        if queue['kind']=='NATIVE_CANDIDATE':
            candidate=queue['evidence'];result=apply_candidate(context,candidate,record);candidate_results.append(result);used_hits.update(result['used_hit_ids'])
            if result['result']['state'] in ('COMPLETE_PREDICTED','CURATED_PARTIAL'):
                require(outcomes[result['rm_type']]=='RESOLVED_WITH_EXECUTED_BASIS','Typed resolved architecture marked unresolved by its review')
            elif result['result']['state'] in ('UNCERTAIN','PARTIAL_CANDIDATE') and not result['result'].get('excluded_from_type_cell'):
                require(all(v=='UNRESOLVED' for v in outcomes.values()) if result['rm_type'] is None else outcomes[result['rm_type']]=='UNRESOLVED',
                        'Unresolved candidate interpretation cannot clear its possible type')
            for rm_type,state in outcomes.items():
                if state=='UNRESOLVED':unresolved[rm_type]['unresolved_model_mappings']+=1
        else:
            if queue['kind']=='RAW_DOMAIN':
                allowed={'USED_IN_EXECUTED_CANDIDATE_REVIEW','REVIEWED_ORPHAN_MTASE','REVIEWED_GENERIC_NUCLEASE','REVIEWED_REPAIR_OR_NON_RM',
                         'REVIEWED_OTHER_FULL_SCOPE_DOMAIN_WITH_NO_I_IV_SUPPORT','UNRESOLVED'}
                require(record['disposition'] in allowed,'Unreviewed/unrecognized raw-domain disposition');domain_dispositions[queue['evidence']['hit_id']]=record['disposition']
                if record['disposition']=='UNRESOLVED':require(all(v=='UNRESOLVED' for v in outcomes.values()),'Unresolved raw domain cannot be cleared for a type')
            if queue['kind']=='SOURCE_CONTEXT' and not queue['evidence']['source']['protein_target_present']:
                annotation=queue['evidence']['source']['gbff_qualifiers_without_translation']+' '+queue['evidence']['source']['source_gene_qualifiers']
                if re.search(r'hypothetical|uncharacterized|unknown function',annotation,re.I):
                    require(all(v=='UNRESOLVED' for v in outcomes.values()) or record.get('primary_locus_specific_resolution')=='EXECUTED_LITERATURE_OR_PROVIDER_CONTRADICTION_REVIEW',
                            'Untranslated unknown context cannot become exclusion from annotation alone')
                    if any(v!='UNRESOLVED' for v in outcomes.values()):context.reader.refs(record.get('primary_locus_specific_basis_refs'))
            if queue['kind']=='CIRCULAR_ORIGIN_CONTEXT' and record.get('rotation_receipt'):
                validate_rotation_evidence(context,queue,record['rotation_receipt'])
            for rm_type,state in outcomes.items():
                if state=='UNRESOLVED':unresolved[rm_type][kind_field[queue['kind']]]+=1
    # Explicit manual candidates may use existing full-scope domains/source
    # neighborhoods, without changing native models or repeating searches.
    for item in document.get('manual_candidates',[]):
        require(item['execution']=='EXECUTED_SOURCE_NEIGHBORHOOD_REVIEW_OF_FULL_NATIVE_DOMAINS','Manual candidate lacks executed source/native review')
        verify_review_refs(context.reader,item);context.reader.refs(item['candidate']['native_candidate_refs'])
        result=apply_candidate(context,item['candidate'],item);candidate_results.append(result);used_hits.update(result['used_hit_ids'])
    require(set(domain_dispositions)==set(context.hits),'Full-scope raw domains not all accounted')
    require(all(h in used_hits for h,d in domain_dispositions.items() if d=='USED_IN_EXECUTED_CANDIDATE_REVIEW'),'Raw domain marked candidate evidence without an executed role join')
    # The same complete exact type+locus architecture is counted once after an
    # explicit reviewed expansion; incompatible reviews are an explicit blocker.
    unique={}
    for result in candidate_results:
        key=result['candidate_id']
        if key in unique:
            require(unique[key]['result']==result['result'],'Exact-locus candidate reviews disagree')
            unique[key]['native_candidate_refs']+=result['native_candidate_refs']
        else:unique[key]=result
    cells=[];coverage_reviews=document['cell_coverage_reviews'];require(set(coverage_reviews)==set(TYPES),'Four type-specific source coverage reviews required')
    for rm_type in TYPES:
        coverage_review=coverage_reviews[rm_type];require(coverage_review['execution']=='EXECUTED_HASH_BOUND_FULL_SCOPE_COVERAGE_REVIEW'
            and coverage_review['source_snapshot_sha256']==snapshots and isinstance(coverage_review.get('rationale'),str) and coverage_review['rationale'].strip(),
            'Type-specific whole-source/full-scope coverage review missing')
        verify_review_refs(context.reader,coverage_review);context.reader.refs(coverage_review.get('evidence_refs'))
        applicable={q['queue_id'] for q in context.queue if rm_type in q['affected_types']}
        require(set(coverage_review['reviewed_queue_ids'])==applicable and len(coverage_review['reviewed_queue_ids'])==len(applicable),'Coverage review silently omitted/duplicated evidence items')
        counts=unresolved[rm_type]
        coverage={field:counts[field] for field in ('unresolved_source_contexts','unresolved_empty_replicons','unresolved_model_mappings','unresolved_origin_classifications')}
        coverage.update(source_review_execution='EXECUTED_AND_HASH_BOUND',full_query_completion_verified=True,all_tasks_verified=True,
            all_candidates_accounted=True,all_full_scope_domains_accounted=True,native_completion_refs=dict(context.native_completion_refs))
        results=[result['result'] for result in unique.values() if result['rm_type'] in (rm_type,None)]
        cell=context.policy.cell_state({'PADLOC':'VALIDATED_FULL_NATIVE_SEARCH','DefenseFinder':'VALIDATED_FULL_NATIVE_SEARCH'},coverage,results)
        cells.append({'assembly_accession':context.accession,'rm_type':rm_type,**cell,'coverage_counts':dict(coverage),
                      'candidate_ids':sorted(result['candidate_id'] for result in unique.values() if result['rm_type'] in (rm_type,None)),
                      'demonstrated_function':'NOT_ESTABLISHED_BY_PROFILE_PREDICTION','review_execution':'COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW'})
    return {'assembly_accession':context.accession,'review_execution':'COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW','scientific_stage05_status':'INDEPENDENT_CURATED_VALIDATION_REQUIRED',
            'review_document_sha256':object_sha(document),'prepared_queue_sha256':object_sha(prepared),'source_snapshot':prepared['source_snapshot'],
            'required_review_items':len(context.queue),'raw_domains_accounted':len(context.hits),'candidates':list(unique.values()),'cells':cells}

def output_table(path,rows,columns):
    with Path(path).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,columns,delimiter='\t',lineterminator='\n');writer.writeheader()
        for row in rows:writer.writerow({k:packed(row[k]) if isinstance(row[k],(list,dict)) else row[k] for k in columns})

def run(args):
    import resource,fcntl
    require(sys.platform=='linux' and Path.cwd().resolve()==args.root,'Bounded WD Linux runtime/dedicated project required')
    require(resource.getrlimit(resource.RLIMIT_AS)==(2147483648,2147483648) and 0<len(os.sched_getaffinity(0))<=2,
            'Caller must apply strict2GiB soft/hard address space and maximum2core affinity')
    panel,freeze,scope,policy,identity=global_gate(args)
    if args.phase=='apply':
        require(args.prepared and args.reviews,'Actual prepared queue and executed review directory required')
        manifest=load(args.prepared/'preparation_manifest.json')
        preparation_gate(manifest,identity)
        identity={**identity,'prepared_manifest_sha256':sha(args.prepared/'preparation_manifest.json'),'phase':'apply'}
    else:identity={**identity,'phase':'prepare'}
    args.output.mkdir(parents=True,exist_ok=True)
    guard=(args.output/'.curation.guard').open('a+b');fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
    start=time.monotonic();completed=[];cells=[]
    try:
        namespace=args.output/'namespace_identity.json'
        if namespace.exists():require(load(namespace)==identity,'Curation source/code/gate namespace changed; preserve existing output')
        else:
            require(set(p.name for p in args.output.iterdir())=={'.curation.guard'},'Unowned curation namespace; preserve existing files')
            save(namespace,identity)
        save(args.output/'execution_receipt.json',{'utc_epoch':time.time(),'pid':os.getpid(),'parent_pid':os.getppid(),'argv':sys.argv,
            'outer_address_space_soft_hard_bytes':list(resource.getrlimit(resource.RLIMIT_AS)),'cpu_affinity':sorted(os.sched_getaffinity(0)),
            'phase':args.phase,'scientific_stage05_status':'INDEPENDENT_CURATED_VALIDATION_REQUIRED','biological_searches_repeated':0})
        for index,accession in enumerate(panel,1):
            context=AssemblyEvidence(args,accession,freeze,scope,policy);prepared=context.prepared()
            if args.phase=='prepare':record=prepared;filename='prepared_queue.json'
            else:
                require(load(args.prepared/'assemblies'/accession/'prepared_queue.json')==prepared,'Prepared queue facts no longer equal reopened actual evidence')
                review_path=args.reviews/(accession+'.json');document=load(review_path)
                record=apply_assembly(context,prepared,document);record['actual_review_file_sha256']=sha(review_path);filename='curated_evidence.json';cells.extend(record['cells'])
            path=args.output/'assemblies'/accession/filename
            if path.exists():require(load(path)==record,'Completed actual curation queue/review changed; preserve prior output')
            else:save(path,record)
            completed.append({'assembly_accession':accession,'path':path.relative_to(args.output).as_posix(),'sha256':sha(path),
                'source_context_loci':len(context.sources),'protein_loci':len(context.sequences),'replicons':len(context.replicons),
                'empty_replicons':sum(rep['primary_protein_targets']==0 for rep in context.replicons),'queue_items':len(context.queue),'raw_domains':len(context.hits)})
            save(args.output/'execution_progress.json',{'phase':args.phase,'assemblies_accounted':len(completed),'required_assemblies':196,
                'last_assembly':accession,'architecture_review':'NOT_RUN' if args.phase=='prepare' else 'EXECUTED_REVIEW_RECORDS_APPLIED_INDEPENDENT_VALIDATION_PENDING'})
            print(str(index)+'/196 '+accession+' '+('ACTUAL_EVIDENCE_QUEUE_PREPARED' if args.phase=='prepare' else 'ACTUAL_REVIEW_RECORDS_APPLIED_INDEPENDENT_GATE_PENDING'),flush=True)
        require(sum(r['source_context_loci'] for r in completed)==411523 and sum(r['protein_loci'] for r in completed)==398537
                and sum(r['replicons'] for r in completed)==2120 and sum(r['empty_replicons'] for r in completed)==271,'Full cohort source/annotation/protein/replicon accounting differs')
        # The upstream scientific bytes are checked again before output completion.
        _,_,_,_,current_identity=global_gate(args)
        require(all(identity[key]==value for key,value in current_identity.items()),'Source/model/code/gate changed during review phase')
        if args.phase=='prepare':
            status='FULL196_ACTUAL_SOURCE_NATIVE_EVIDENCE_QUEUE_PREPARED_REVIEW_PENDING';manifest_name='preparation_manifest.json'
        else:
            policy.validate_cells(panel,cells)
            output_table(args.output/'rm_cells.tsv',cells,['assembly_accession','rm_type','state','complete_predicted_count','curated_partial_count',
                'candidate_counts','coverage_unresolved','candidate_ids','demonstrated_function','review_execution'])
            status='COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW_APPLIED_PENDING_INDEPENDENT_CURATED_VALIDATION';manifest_name='curation_summary.json'
        summary={'status':status,'identity':identity,'assemblies':196,'cells':784 if args.phase=='apply' else None,
            'scientific_stage05_status':'INDEPENDENT_CURATED_VALIDATION_REQUIRED','architecture_review':'NOT_RUN' if args.phase=='prepare' else 'EXECUTED_RECORDS_APPLIED',
            'functional_evidence_grade':'PREDICTION_ONLY_ACTIVITY_NOT_ESTABLISHED','publication':'NOT_RUN','biological_searches_repeated':0,
            'outputs':completed,'cell_states':dict(Counter(c['state'] for c in cells)) if cells else {},
            'evidence_limit':'Real opened source/native records plus recorded scientific interpretation. A separate independent curated-evidence audit is required; no Stage05 PASS or Stage06 gate here.'}
        manifest_path=args.output/manifest_name
        if manifest_path.exists():require(load(manifest_path)==summary,'Immutable curation payload manifest changed')
        else:save(manifest_path,summary)
        save(args.output/'execution_completion_receipt.json',{'phase':args.phase,'pid':os.getpid(),'elapsed_seconds':time.monotonic()-start,
            'manifest_sha256':sha(manifest_path),'status':status,'scientific_stage05_status':'INDEPENDENT_CURATED_VALIDATION_REQUIRED'})
    except Exception as error:
        save(args.output/'execution_failure.json',{'phase':args.phase,'pid':os.getpid(),'error':type(error).__name__+': '+str(error),
            'outputs_preserved':True,'assemblies_accounted':len(completed),'scientific_stage05_status':'NOT_PASS'})
        raise
    finally:guard.close()

def parse():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=['prepare','apply'],required=True)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    defaults={'source':'.work/source_locus_inputs_v1','bundle':'.work/stage05_detector_inputs_v1',
        'bundle-validation':'.work/stage05_detector_input_validation_v1/validation_summary.json',
        'source-validation':'.work/stage03_source_validation/validation_summary.json','execution':'.work/stage05_native_detectors_v1',
        'inventory':'.work/stage05_evidence_inventory_v1','raw-validation':'.work/stage05_raw_validation_v1/validation_summary.json',
        'raw-validator':'scripts/validate_stage05_raw.py','policy-module':'scripts/stage05_architecture_policy.py',
        'policy-reconciliation':'reports/stage05/architecture_policy/policy_reconciliation_handoff.json',
        'policy-dir':'reports/stage05/architecture_policy','models-dir':'.tools/linux/defense_models','padloc-db':'.tools/linux/padloc_db',
        'environment-dir':'.tools/linux/detector_env','evidence-dir':'reports/stage05/evidence_reviews'}
    for name,value in defaults.items():parser.add_argument('--'+name,type=Path,default=Path(value))
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--prepared',type=Path);parser.add_argument('--reviews',type=Path)
    args=parser.parse_args();args.root=args.root.resolve()
    for name,value in vars(args).copy().items():
        if isinstance(value,Path):setattr(args,name,value.resolve() if value.is_absolute() else (args.root/value).resolve())
    require(args.root in args.output.parents and '.work' in args.output.relative_to(args.root).parts,'Dedicated .work curation namespace required')
    for source in [args.source,args.bundle,args.execution,args.inventory,args.policy_dir,args.prepared,args.reviews]:
        if source is not None:require(args.output!=source and args.output not in source.parents and source not in args.output.parents,'Curation namespace overlaps source/review evidence')
    return args

if __name__=='__main__':run(parse())
