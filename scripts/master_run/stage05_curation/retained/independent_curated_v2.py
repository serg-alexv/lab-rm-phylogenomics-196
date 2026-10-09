#!/usr/bin/env python3
"""Independent Stage05 curated-schema candidate. No producer imports or searches.

Versioned ahead checker; NOT ADOPTED. Production is deliberately blocked until
its contract names the exact independently reviewed, repaired producer bytes.
Synthetic tests establish checker behavior only, never scientific completion.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = 'PARENT_STAGE05_CURATED_CHECK_INPUT_V2_CBAF00AE'
SNAPSHOT = 'cbaf00aee2d9961eaaa0be76b589315014a88183e3f7f8ed1f2ff234e6418177'
RECONCILIATION = '74baa2ae85c90b08e583ab752f8cb97f76bf54969f661845135331c5d18753e3'
POLICY = '20fb827e8593424194a7defa3a1ac04fc4c1fcef71be26231d369e32146f68de'
TYPES = ('I','II','III','IV')
STATES = {'NOT_RUN','FAILED','UNCERTAIN','PARTIAL_CANDIDATE','CURATED_PARTIAL','COMPLETE_PREDICTED','NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH'}
SEARCH = {'NOT_RUN','FAILED','VALIDATED_FULL_NATIVE_SEARCH'}
EXCLUSIONS = {'REVIEWED_ORPHAN_MTASE','REVIEWED_GENERIC_NUCLEASE','REVIEWED_REPAIR_OR_NON_RM'}
NEEDED = {'I':{'REASE','MTASE','SPECIFICITY'},'II':{'REASE','MTASE'},'III':{'MOD','RES'},'IV':{'MOD_DEPENDENT_RECOGNITION','CLEAVAGE'}}
ROLES = set.union(*NEEDED.values()) | {'MCRB','MCRC','GMR_S','GMR_D'}
UNRESOLVED = ('unresolved_source_contexts','unresolved_empty_replicons','unresolved_model_mappings','unresolved_origin_classifications')
FLAGS = ('protein_target_present','source_pseudo_any','partial_or_fuzzy','origin_spanning','requires_coordinate_review')
SHA = re.compile(r'^[a-f0-9]{64}$')
CELL_COLUMNS = ['assembly_accession','rm_type','state','complete_predicted_count','curated_partial_count','candidate_counts','coverage_unresolved','candidate_ids','demonstrated_function','review_execution']

def must(condition, text):
    if not condition: raise ValueError(text)

def packed(value): return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def objsha(value): return hashlib.sha256(packed(value).encode('utf-8')).hexdigest()
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
def pairs(items):
    out={}
    for key,value in items:
        must(key not in out,'Duplicate JSON field: '+key);out[key]=value
    return out
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=pairs)
def number(value):
    value=float(value);must(math.isfinite(value),'Nonfinite numerical evidence');return value
def integer(value):
    must(not isinstance(value,bool),'Boolean is not an integer evidence value')
    result=int(value);must(str(result)==str(value),'Noncanonical integer evidence');return result
def truth(value):
    must(value in ('True','False'),'Source flag must be literal True/False');return value=='True'
def records(path,delimiter='\t',native=False):
    text=Path(path).read_text(encoding='utf-8')
    must(not re.search(r'has been SKIPPED|cannot be solved|before timeout',text,re.I),'Native skipped/timeout evidence')
    if native: text='\n'.join(line for line in text.splitlines() if line and not line.startswith('#'))
    reader=csv.DictReader(io.StringIO(text),delimiter=delimiter);rows=list(reader)
    must(reader.fieldnames is not None and len(set(reader.fieldnames))==len(reader.fieldnames),'Missing/duplicate table header')
    must(all(None not in row and all(v is not None for v in row.values()) for row in rows),'Malformed table row')
    return rows
def proteins(path):
    out={};key=None;parts=[]
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if line.startswith('>'):
            if key is not None: out[key]=''.join(parts)
            key=line[1:].split()[0];must(key and key not in out,'Duplicate/empty primary AA key');parts=[]
        elif line.strip(): must(key is not None,'AA before identifier');parts.append(line.strip())
    if key is not None: out[key]=''.join(parts)
    must(all(out.values()),'Empty primary AA');return out

class Reader:
    """Independent portable file/typed-record resolver with exact byte hashes."""
    def __init__(self,root,allowed,linux_root=None):
        self.root=Path(root).resolve();self.allowed=[Path(p).resolve() for p in allowed]
        self.linux_root=linux_root;self.hashes={};self.tables={};self.jsons={};self.fastas={}
    def path(self,name):
        must(isinstance(name,str) and name,'Missing evidence path')
        if self.linux_root and name.startswith(self.linux_root.rstrip('/')+'/'):
            name=name[len(self.linux_root.rstrip('/'))+1:]
        p=Path(name)
        if not p.is_absolute(): p=self.root/p
        p=p.resolve();must(p!=self.root and self.root in p.parents,'Evidence path outside project')
        must(not any(v in ('.git','.private_run') for v in p.relative_to(self.root).parts),'Private evidence forbidden')
        must(any(p==a or a in p.parents for a in self.allowed),'Evidence outside reviewed scientific roots')
        must(p.is_file(),'Missing actual evidence: '+str(p));return p
    def directory(self,name):
        if self.linux_root and str(name).startswith(self.linux_root.rstrip('/')+'/'):name=str(name)[len(self.linux_root.rstrip('/'))+1:]
        p=Path(name)
        if not p.is_absolute():p=self.root/p
        p=p.resolve();must(self.root in p.parents and p.is_dir() and any(p==a or a in p.parents for a in self.allowed),'Native directory outside reviewed project roots');return p
    def release_assembly(self,model_roots):
        # Keep shared immutable model digests; discard assembly-sized tables,
        # JSON/AA records and native-file digest keys before the next assembly.
        self.tables.clear();self.jsons.clear();self.fastas.clear()
        self.hashes={k:v for k,v in self.hashes.items() if any(root==k[0] or root in k[0].parents for root in model_roots)}
    def digest(self,path):
        path=Path(path);st=path.stat();key=(path,st.st_size,st.st_mtime_ns)
        if key not in self.hashes:self.hashes[key]=sha(path)
        return self.hashes[key]
    def ref(self,ref):
        must(isinstance(ref,dict) and {'path','sha256','record_locator','record_sha256'}<=ref.keys(),'Incomplete typed record ref')
        p=self.path(ref['path']);must(self.digest(p)==ref['sha256'],'Referenced file hash mismatch')
        locator=ref['record_locator'];must(isinstance(locator,str) and ':' in locator,'Missing typed locator')
        kind,key=locator.split(':',1)
        if kind in ('tsv','csv','native_tsv'):
            cache=(p,kind)
            if cache not in self.tables:self.tables[cache]=records(p,',' if kind=='csv' else '\t',kind=='native_tsv')
            rows=self.tables[cache];i=integer(key);must(1<=i<=len(rows),'Referenced table row missing');value=rows[i-1]
        elif kind=='json':
            if p not in self.jsons:self.jsons[p]=read(p)
            value=self.jsons[p]
            if key:
                must(key.startswith('/'),'Bad JSON pointer')
                for item in key[1:].split('/'):
                    item=item.replace('~1','/').replace('~0','~');value=value[int(item)] if isinstance(value,list) else value[item]
        elif kind=='fasta':
            if p not in self.fastas:self.fastas[p]=proteins(p)
            must(key in self.fastas[p],'Exact primary AA target missing');value={'target_id':key,'sequence':self.fastas[p][key]}
        elif kind=='text':
            match=re.fullmatch(r'(\d+)-(\d+)',key);must(match,'Bad text locator');lo,hi=map(int,match.groups())
            lines=p.read_text(encoding='utf-8').splitlines(keepends=True);must(1<=lo<=hi<=len(lines),'Text range missing');value=''.join(lines[lo-1:hi])
        else: raise ValueError('Unknown typed-record schema')
        must(objsha(value)==ref['record_sha256'],'Referenced record hash mismatch');return value
    def refs(self,refs):
        must(isinstance(refs,list) and refs,'Empty required evidence list');return [self.ref(r) for r in refs]
    def nested(self,value):
        if isinstance(value,dict):
            if {'path','sha256','record_locator'}<=value.keys():self.ref(value)
            else:
                for child in value.values():self.nested(child)
        elif isinstance(value,list):
            for child in value:self.nested(child)

def canonical(assembly,rm_type,loci):
    must(rm_type in TYPES or rm_type is None,'Invalid candidate type')
    must(isinstance(loci,list) and loci and len(set(loci))==len(loci),'Candidate loci empty/duplicated')
    parts=[key.split('|') for key in loci]
    must(all(len(p)==3 and all(p) and p[0]==assembly for p in parts),'Candidate source accession mismatch')
    must(len({p[1] for p in parts})==1,'Cross-sequence architecture forbidden')
    identity={'assembly_accession':assembly,'replicon':parts[0][1],'rm_type':rm_type,'locus_keys':sorted(loci)}
    # Policy canonical IDs use ASCII JSON; reviewed accessions/loci are ASCII.
    encoded=json.dumps(identity,sort_keys=True,separators=(',',':')).encode()
    return identity,'RMC_'+hashlib.sha256(encoded).hexdigest()[:24]

def matrix(panel,cells):
    must(len(panel)==len(set(panel))==196 and all(re.fullmatch(r'GCF_\d{9}\.\d+',a) for a in panel),'Exact196 versioned assembly panel required')
    keys=[(c['assembly_accession'],c['rm_type']) for c in cells]
    must(len(keys)==len(set(keys))==784 and set(keys)=={(a,t) for a in panel for t in TYPES},'Wrong784 accession/type keys')
    must(all(c['state'] in STATES for c in cells),'Unknown cell state')

def derive_cell(search,coverage,results):
    """Independent reducer; positive counts survive explicit detector failures."""
    must(set(search)=={'PADLOC','DefenseFinder'} and all(s in SEARCH for s in search.values()),'Unknown detector execution state')
    for result in results:
        must(result.get('state') in {'UNCERTAIN','PARTIAL_CANDIDATE','CURATED_PARTIAL','COMPLETE_PREDICTED'},'Invalid candidate state')
        excluded=result.get('excluded_from_type_cell',False);must(type(excluded) is bool,'Invalid exclusion flag')
        if excluded:must(result['state']=='UNCERTAIN' and result.get('locus_annotation_state') in EXCLUSIONS and result.get('functional_evidence_grade')=='NOT_ESTABLISHED','Untyped exclusion')
    counts=Counter(r['state'] for r in results if not r.get('excluded_from_type_cell',False))
    positive=counts['COMPLETE_PREDICTED'];partial=counts['CURATED_PARTIAL']
    unresolved=any(coverage[k]>0 for k in UNRESOLVED)
    if all(s=='VALIDATED_FULL_NATIVE_SEARCH' for s in search.values()):
        must(coverage.get('full_query_completion_verified') is True and coverage.get('all_tasks_verified') is True,'Successful labels lack query/task proof')
        must(set(coverage.get('native_completion_refs',{}))==set(search) and all(coverage['native_completion_refs'].values()),'Missing native task receipt')
    if 'FAILED' in search.values():state='FAILED'
    elif 'NOT_RUN' in search.values():state='NOT_RUN'
    elif positive:state='COMPLETE_PREDICTED'
    elif counts['UNCERTAIN'] or unresolved:state='UNCERTAIN'
    elif counts['PARTIAL_CANDIDATE']:state='PARTIAL_CANDIDATE'
    elif partial:state='CURATED_PARTIAL'
    else:
        must(coverage.get('source_review_execution')=='EXECUTED_AND_HASH_BOUND' and coverage.get('all_candidates_accounted') is True and coverage.get('all_full_scope_domains_accounted') is True,'Non-detection lacks executed whole-source coverage')
        state='NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH'
    return dict(state=state,candidate_counts=dict(counts),complete_predicted_count=positive,curated_partial_count=partial,required_detector_completion=search,coverage_unresolved=unresolved,functional_evidence_grade='NOT_ESTABLISHED')

def architecture(candidate,review,sources,hits,reader):
    """Reconstruct documented role/partner/completeness policy; no policy import."""
    identity,cid=canonical(candidate['assembly_accession'],candidate['rm_type'],candidate['locus_keys'])
    must(review['candidate_id']==cid and review['rm_type']==candidate['rm_type'],'Review canonical identity mismatch')
    if review['decision']=='UNCERTAIN' and not review.get('roles'):
        must(review['execution']=='EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW'
             and review['functional_evidence_grade']=='PREDICTED_ARCHITECTURE_ONLY'
             and review.get('architecture_assignment')=='UNRESOLVED_AFTER_EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW',
             'Role-free uncertainty lacks explicit executed unresolved architecture review')
        reader.nested(review);reader.refs(review['source_context_refs']);reader.refs(review['architecture_basis_refs'])
        must(hasattr(reader,'source_refs') and all(key in sources and key in reader.source_refs
             and reader.source_refs[key] in review['source_context_refs'] for key in identity['locus_keys']),
             'Unresolved architecture omitted exact original source row')
        must(all(ref in review['architecture_basis_refs'] for ref in candidate['native_candidate_refs']),
             'Unresolved architecture omitted actual native candidate basis')
        return identity,cid,{'state':'UNCERTAIN','reason':'UNRESOLVED_AFTER_EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW',
                            'functional_evidence_grade':'NOT_ESTABLISHED'},[]
    if candidate['rm_type'] is None and review['decision'] not in EXCLUSIONS:
        # Five pinned ambiguous/orphan scope entries legitimately stay unmapped.
        # Such a record cannot become a complete or pale typed architecture.
        reader.nested(review);used=set()
        for role in review.get('roles',[]):
            key=role['locus_key'];must(key in sources and key in identity['locus_keys'],'Unmapped review role source absent')
            for hid in role['hit_ids']:
                must(hid in hits and hits[hid]['locus_key']==key and hits[hid]['source_aa_sha256']==role['source_aa_sha256'],'Unmapped review contains invented source/domain');used.add(hid)
        return identity,cid,{'state':'UNCERTAIN','locus_annotation_state':'UNMAPPED_GENERIC_OR_REPAIR_CANDIDATE','functional_evidence_grade':'NOT_ESTABLISHED'},sorted(used)
    must(review['execution']=='EXECUTED_SOURCE_DOMAIN_CONTEXT_REVIEW' and review['functional_evidence_grade']=='PREDICTED_ARCHITECTURE_ONLY','Architecture review/activity grade invalid')
    must(review.get('unresolved_competing_annotations',-1)==0,'Competing annotation unresolved')
    reader.nested(review);reader.refs(review['source_context_refs']);reader.refs(review['architecture_basis_refs'])
    roles=set();issues=set();role_loci=defaultdict(set);hit_roles=defaultdict(set);used=set();covered=set()
    for role in review['roles']:
        name=role['role'];key=role['locus_key'];must(name in ROLES and key in identity['locus_keys'] and key in sources,'Unknown role/source')
        source=sources[key];must(source['protein_target_present'] is True and role['source_aa_sha256']==source['primary_faa_sequence_sha256'] and SHA.fullmatch(role['source_aa_sha256']),'Role lacks exact original translated AA')
        must(all(type(source.get(flag)) is bool for flag in (*FLAGS,'linear_edge')),'Nonboolean source flags')
        basis=role['functional_domain_basis_refs'];reader.refs(basis)
        must(role.get('hit_ids') and len(set(role['hit_ids']))==len(role['hit_ids']),'Empty/duplicate role hit IDs')
        for hid in role['hit_ids']:
            must(hid in hits,'Invented native domain');h=hits[hid]
            must(h['locus_key']==key and h['source_aa_sha256']==role['source_aa_sha256'] and h['target_length']==source['protein_aa_length'],'Role domain/source mismatch')
            must(h['native_role_threshold_passed'] is True and h['threshold_receipt_verified'] is True,'Rejected domain cannot establish role')
            must(1<=h['alignment_from']<=h['alignment_to']<=h['target_length'] and SHA.fullmatch(h['profile_sha256']),'Invalid role domain/profile')
            reader.ref(h['raw_ref']);must(h['raw_ref'] in basis or h['raw_ref'] in review['architecture_basis_refs'],'Role omitted exact raw domain ref')
            must(any(r['record_locator']=='fasta:'+key and reader.ref(r)=={'target_id':key,'sequence':source['_sequence']} for r in basis),'Role omitted primary AA record')
            must(any(r['record_locator'].startswith('tsv:') and reader.ref(r).get('locus_key')==key for r in review['source_context_refs']),'Role omitted exact source row')
            used.add(hid);hit_roles[hid].add(name)
        roles.add(name);role_loci[name].add(key);covered.add(key)
        issues.update(flag for flag in ('source_pseudo_any','partial_or_fuzzy','linear_edge','origin_spanning','requires_coordinate_review') if source[flag])
        must(role['domain_completeness_review'] in ('REVIEWED_INTACT','REVIEWED_PARTIAL'),'Missing domain integrity review')
        if role['domain_completeness_review']=='REVIEWED_PARTIAL':issues.add('reviewed_partial_domain')
    untranslated=review.get('untranslated_context_locus_keys',[])
    for key in untranslated:must(key in identity['locus_keys'] and key in sources and sources[key]['protein_target_present'] is False,'Invalid untranslated context');issues.add('untranslated_context');covered.add(key)
    for row in review.get('other_candidate_locus_reviews',[]):
        must(row['execution']=='EXECUTED_CANDIDATE_LOCUS_CONTEXT_REVIEW' and row['locus_key'] in identity['locus_keys'] and row['locus_key'] in sources,'Unreviewed additional locus');reader.refs(row['evidence_refs']);covered.add(row['locus_key'])
    must(covered==set(identity['locus_keys']) and (roles or untranslated),'Candidate loci not fully reviewed')
    must(review['compatibility_state'] in ('COMPATIBLE_REVIEWED','INCOMPATIBLE','UNRESOLVED'),'Unknown role compatibility');reader.refs(review['compatibility_basis_refs'])
    if review['compatibility_state']!='COMPATIBLE_REVIEWED':issues.add('incompatible_or_unresolved_roles')
    if any(len(rs)>1 for rs in hit_roles.values()):
        if review.get('shared_profile_role_resolution')!='REVIEWED_MULTIFUNCTIONAL_PROFILE_WITH_DOMAIN_BASIS' or not review.get('shared_profile_role_basis_refs'):issues.add('one_profile_multiple_functional_roles_unresolved')
    rm_type=candidate['rm_type'];subtype=candidate.get('subtype')
    fusion={'I':'REVIEWED_SUPPORTED_TYPE_I_FUSION','II':'REVIEWED_SUPPORTED_TYPE_II_FUSION','III':'REVIEWED_SUPPORTED_TYPE_III_FUSION'}
    if rm_type in fusion:
        by_locus=defaultdict(set)
        for role in NEEDED[rm_type]:
            for key in role_loci[role]:by_locus[key].add(role)
        if any(len(rs)>1 for rs in by_locus.values()):
            allowed={fusion[rm_type]}|({'REVIEWED_DUAL_FUNCTION_DOMAIN_ARCHITECTURE'} if subtype=='IIG' else set())
            if review.get('fusion_architecture_review') not in allowed or not review.get('fusion_basis_refs'):issues.add('fusion_architecture_unresolved')
    if subtype=='IIG' and (len(identity['locus_keys'])!=1 or not role_loci['REASE']&role_loci['MTASE'] or review.get('fusion_architecture_review')!='REVIEWED_DUAL_FUNCTION_DOMAIN_ARCHITECTURE' or not review.get('fusion_basis_refs')):issues.add('unresolved_IIG_fusion')
    if subtype=='McrBC' and not {'MCRB','MCRC'}<=roles:issues.add('McrBC_partner_missing')
    if subtype=='GmrSD' and not {'GMR_S','GMR_D'}<=roles and review.get('fusion_architecture_review')!='REVIEWED_GmrSD_FUSION_ARCHITECTURE':issues.add('GmrSD_partner_or_fusion_unresolved')
    if rm_type=='IV':
        if review.get('modification_dependence_basis')!='REVIEWED_FAMILY_SPECIFIC_PREDICTION' or not review.get('modification_dependence_refs'):issues.add('modification_dependence_unresolved')
        if review.get('TypeIV_vs_TypeII_competing_context')!='RESOLVED_WITH_EXPLICIT_BASIS':issues.add('TypeIV_TypeII_context_unresolved')
    for issue in ('linear_edge','origin_spanning','requires_coordinate_review'):
        resolution=review.get('context_issue_resolutions',{}).get(issue,{})
        if issue in issues and resolution.get('state')=='REVIEWED_SOURCE_ARCHITECTURE_UNAFFECTED' and resolution.get('evidence_refs'):reader.refs(resolution['evidence_refs']);issues.remove(issue)
    missing=(NEEDED[rm_type]-roles) if rm_type in TYPES else set()
    decision=review['decision'];complete=not missing and not issues
    if decision in EXCLUSIONS:
        reader.refs(review['exclusion_basis_refs']);result={'state':'UNCERTAIN','locus_annotation_state':decision,'excluded_from_type_cell':True,'functional_evidence_grade':'NOT_ESTABLISHED'}
    elif rm_type is None:result={'state':'UNCERTAIN','locus_annotation_state':'UNMAPPED_GENERIC_OR_REPAIR_CANDIDATE','functional_evidence_grade':'NOT_ESTABLISHED'}
    else:
        must(decision in ('COMPLETE_PREDICTED','CURATED_PARTIAL','UNCERTAIN','PARTIAL_CANDIDATE'),'Unknown architecture decision')
        if decision=='COMPLETE_PREDICTED':must(complete,'Complete prediction lacks intact compatible full architecture')
        if decision=='CURATED_PARTIAL':
            must(not complete and review.get('partial_interpretation') in ('REVIEWED_MISSING_COMPONENT','REVIEWED_TRUNCATED_OR_PSEUDOGENIZED_ARCHITECTURE'),'Unjustified partial architecture');reader.refs(review['partial_basis_refs'])
            must(not issues&{'incompatible_or_unresolved_roles','modification_dependence_unresolved','TypeIV_TypeII_context_unresolved'},'Uncertain type cannot become reviewed partial')
        result={'state':decision,'missing_roles':sorted(missing),'context_issues':sorted(issues),'functional_evidence_grade':'PREDICTED_ARCHITECTURE_ONLY'}
    return identity,cid,result,sorted(used)

def query_blocks(path):
    current=[]
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            if line.startswith('Query:'):current=[line]
            elif current:
                current.append(line)
                if line.strip()=='//':yield ''.join(current);current=[]

def query_domains(block,name,length,targets):
    lines=block.splitlines();must(re.fullmatch(r'Query:\s+'+re.escape(name)+r'\s+\[M='+str(length)+r'\]',lines[0].strip()),'Native query name/length mismatch')
    must(lines[-1]=='//' and re.findall(r'^Query model\(s\):\s+(\d+)\b',block,re.M)==['1'] and re.findall(r'^Target sequences:\s+(\d+)\b',block,re.M)==[str(len(targets))],'Native query incomplete/wrong target count')
    scores={};domains=[];score_mode=False;target=None
    for line in lines:
        if line.startswith('Scores for complete sequences'):score_mode=True
        if line.startswith('Domain annotation'):score_mode=False
        fields=line.split()
        if score_mode and len(fields)>=9 and re.fullmatch(r'[0-9.eE+-]+',fields[0]) and fields[7].isdigit():
            target_id=fields[8];must(target_id in targets and target_id not in scores,'Raw score target unknown/duplicated');scores[target_id]=fields[:3]+[int(fields[7])]
        if line.startswith('>>'):target=fields[1];must(target in scores,'Raw domain target absent from scored list')
        if len(fields)==16 and fields[0].isdigit() and fields[1] in ('!','?'):
            must(target is not None,'Domain without source target')
            row=dict(target_name=target,domain_number=fields[0],domain_score=fields[2],domain_bias=fields[3],conditional_evalue=fields[4],independent_evalue=fields[5],hmm_from=fields[6],hmm_to=fields[7],alignment_from=fields[9],alignment_to=fields[10],envelope_from=fields[12],envelope_to=fields[13],accuracy=fields[15],profile_name=name,profile_length=length)
            row.update(full_evalue=scores[target][0],full_score=scores[target][1],full_bias=scores[target][2],total_domains=scores[target][3]);domains.append(row)
    for key,score in scores.items():must(sorted(int(d['domain_number']) for d in domains if d['target_name']==key)==list(range(1,score[3]+1)),'Native target domain inventory incomplete')
    for d in domains:
        must(1<=int(d['hmm_from'])<=int(d['hmm_to'])<=length and 1<=int(d['alignment_from'])<=int(d['alignment_to'])<=targets[d['target_name']],'Raw domain bounds invalid')
        must(0<=number(d['accuracy'])<=1 and number(d['independent_evalue'])>=0,'Invalid native accuracy/E-value')
    return domains

def dom_records(path):
    fields=['target_name','target_accession','target_length','profile_name','profile_accession','profile_length','full_evalue','full_score','full_bias','domain_number','total_domains','conditional_evalue','independent_evalue','domain_score','domain_bias','hmm_from','hmm_to','alignment_from','alignment_to','envelope_from','envelope_to','accuracy','description']
    result=[]
    for i,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
        if not line.strip() or line.startswith('#'):continue
        parts=line.split(maxsplit=22);must(len(parts)==23,'Malformed original domtbl row')
        result.append({**dict(zip(fields,parts)),'source_line':i,'native_line':line})
    return result

def numeric_threshold(domain,profile,metadata=None,settings=None):
    lo,hi=int(domain['alignment_from']),int(domain['alignment_to']);hlo,hhi=int(domain['hmm_from']),int(domain['hmm_to']);length=int(profile['length']);target=int(domain['target_length'])
    must(1<=lo<=hi<=target and 1<=hlo<=hhi<=length,'Invalid domain threshold coordinates')
    ie=number(domain['independent_evalue']);must(ie>=0,'Negative domain E-value')
    if settings is not None:
        must(profile['threshold']==(['--cut_ga'] if settings['cut_ga'] and profile['has_ga'] else ['-E',format(settings['e_value_search'],'f')]),'Native GA/search threshold drift')
        return ie<=number(settings['i_evalue_sel']) and (hhi-hlo+1)/length>=number(settings['coverage_profile'])
    def meta(key,default):return default if metadata[key] in ('NA','','NaN') else number(metadata[key])
    return ie<=meta('e.value.threshold',1e-5) and round((hhi-hlo)/length,3)>=meta('hmm.coverage.threshold',0.3) and round((hi-lo)/target,3)>=meta('target.coverage.threshold',0.3)

def selected_padloc(hits):
    priority={'core_genes':4,'secondary_genes':3,'neutral_genes':2,'prohibited_genes':1};groups=defaultdict(list);chosen=defaultdict(list)
    for ordinal,(hid,h) in enumerate(hits.items()):
        if h['detector']!='PADLOC':continue
        model_priority=defaultdict(list)
        for role in h['native_model_roles']:must(role['role_class'] in priority,'Unknown pinned role class');model_priority[role['model']].append(priority[role['role_class']])
        for model,roles in model_priority.items():groups[(model,h['locus_key'])].append((hid,max(roles),ordinal))
    for (model,_),members in groups.items():
        best_ie={}
        for hid,_,_ in members:
            h=hits[hid];name=h['profile_name'];best_ie[name]=min(best_ie.get(name,float('inf')),number(h['domain']['independent_evalue']))
        winners=[item for item in members if number(hits[item[0]]['domain']['independent_evalue'])==best_ie[hits[item[0]]['profile_name']]]
        limit=sorted(number(hits[i[0]]['domain']['independent_evalue']) for i in winners)[min(4,len(winners)-1)]
        eligible=[i for i in winners if number(hits[i[0]]['domain']['independent_evalue'])<=limit and hits[i[0]]['_numeric_pass']]
        def rank(item):
            hid,role,ordinal=item;h=hits[hid];d=h['domain'];coverage=(int(d['hmm_to'])-int(d['hmm_from']))/int(d['profile_length'])+(int(d['alignment_to'])-int(d['alignment_from']))/h['target_length']
            return -role,number(d['independent_evalue']),-coverage,ordinal
        if eligible:chosen[min(eligible,key=rank)[0]].append(model)
    for hid,h in hits.items():
        if h['detector']=='PADLOC':h['native_role_threshold_passed']=h['_numeric_pass'] and bool(chosen[hid]);h['native_selected_model_ids']=sorted(chosen[hid])

def sources_from_rows(rows,seqs,reps,assembly):
    by_rep={r['replicon']:r for r in reps};order=defaultdict(list);out={}
    for row in rows:order[row['replicon']].append(row['locus_key'])
    for row in rows:
        key=row['locus_key'];must(key==assembly+'|'+row['replicon']+'|'+row['locus_tag'] and key not in out,'Source locus identity duplicate/mismatch')
        flags={flag:truth(row[flag]) for flag in FLAGS};present=flags['protein_target_present'];must(present==(key in seqs),'Primary AA/source presence disagreement')
        length=int(row['protein_aa_length']) if present else 0
        if present:must(len(seqs[key])==length and hashlib.sha256(seqs[key].encode()).hexdigest()==row['primary_faa_sequence_sha256'],'Exact original AA length/hash disagreement')
        else:must(not row['primary_faa_sequence_sha256'] and not row['protein_aa_length'],'Untranslated source fabricates AA')
        out[key]={**row,**flags,'protein_aa_length':length,'linear_edge':by_rep[row['replicon']]['documented_circular'] is not True and key in (order[row['replicon']][0],order[row['replicon']][-1]),'_sequence':seqs.get(key)}
    must(set(seqs)=={k for k,s in out.items() if s['protein_target_present']},'Dropped/added primary target');return out

def check_task_receipts(reader,prepared,freeze_path,sources,execution):
    derived={};freeze_sha=reader.digest(freeze_path)
    must(set(prepared['native_completion_refs'])=={'PADLOC','DefenseFinder'},'Both native detectors required')
    for detector,refs in prepared['native_completion_refs'].items():
        must(refs,'Missing detector task receipts')
        expected={execution/'padloc/complete.json'} if detector=='PADLOC' else {execution/s['df_bundle_task']/'complete.json' for s in sources.values() if s['protein_target_present']}
        actual=[reader.path(r['path']) for r in refs];must(len(actual)==len(set(actual)) and set(actual)=={p.resolve() for p in expected},'Native task receipt set incomplete/wrong detector')
        for ref in refs:
            doc=reader.ref(ref);must(doc['execution']=='NATIVE_OUTPUTS_CHECKED' and doc['scientific_curation']=='NOT_RUN' and doc['identity']['freeze_sha256']==freeze_sha,'Failed/notrun native task cannot pass')
            must(doc['files'],'Empty native completion files')
            parent=reader.path(ref['path']).parent
            for name,digest in doc['files'].items():must(reader.digest(reader.path(str(parent/name)))==digest,'Native task member hash mismatch')
        derived[detector]='VALIDATED_FULL_NATIVE_SEARCH'
    return derived

def check_queries(reader,inventory,execution,freeze,sources):
    rows=records(inventory/'all_native_query_completion.tsv');by_file=defaultdict(dict);profiles={p['query_name']:p for p in freeze['padloc_profiles']};scopes={};df_tasks={s['df_bundle_task'] for s in sources.values() if s['protein_target_present']}
    observed=set()
    target_maps={'padloc':{k:s['protein_aa_length'] for k,s in sources.items() if s['protein_target_present']}}
    for task in df_tasks:target_maps[task]={s['df_bundle_target_id']:s['protein_aa_length'] for s in sources.values() if s['protein_target_present'] and s['df_bundle_task']==task}
    for row in rows:
        must(row['evidence_state']=='COMPLETE_QUERY_NOT_CURATED_ABSENCE','Unvalidated native query row');path=reader.path(str(execution/row['raw_file']));must(reader.digest(path)==row['raw_file_sha256'],'Raw query bytes drift')
        if row['detector']=='PADLOC':profile=profiles[row['query_name']];targets=target_maps['padloc']
        else:
            must(row['detector']=='DefenseFinder' and row['task'] in df_tasks and row['family'] in ('DefenseFinder','RM','Cas'),'Unknown native detector/task/family')
            key=(row['task'],row['family'])
            if key not in scopes:scopes[key]=read(execution/row['task']/'families'/row['family']/'scope.json')
            scope=scopes[key];must(scope['family']==row['family'],'Native family scope changed');matches=[p for p in scope['profiles'] if p['query_name']==row['query_name']];must(len(matches)==1,'Profile query ambiguous');profile=matches[0]
            targets=target_maps[row['task']]
            must(scope['target_count']==len(targets),'Native task source count drift')
        must(reader.digest(reader.path(profile['profile_path']))==profile['profile_sha256']==row['profile_sha256'] and int(row['target_sequences_searched'])==len(targets),'Native query profile/AA membership mismatch')
        identity=(row['detector'],row['task'],row['family'],row['query_name']);must(identity not in observed,'Duplicate native query identity');observed.add(identity)
        must(row['query_name'] not in by_file[path],'Repeated native query in file');by_file[path][row['query_name']]=(row,profile,targets)
    must({r['query_name'] for r in rows if r['detector']=='PADLOC'}==set(profiles) and len(profiles)==5027,'Incomplete full PADLOC scope')
    must({r['task'] for r in rows if r['detector']=='DefenseFinder'}==df_tasks,'Incomplete DF task set')
    for task in df_tasks:
        for family,count in [('DefenseFinder',1092),('RM',134),('Cas',525)]:
            scope=scopes[(task,family)];names={p['query_name'] for p in scope['profiles']};must(len(names)==count and {r['query_name'] for r in rows if r['detector']=='DefenseFinder' and r['task']==task and r['family']==family}==names,'Incomplete full DF family/profile scope')
    domain_lookup={}
    for path,wanted in by_file.items():
        found=set()
        for block in query_blocks(path):
            name=block.splitlines()[0].split()[1]
            if name not in wanted:continue
            must(name not in found,'Duplicated original native query');found.add(name);row,profile,targets=wanted[name]
            ds=query_domains(block,name,profile['length'],targets)
            must(hashlib.sha256(block.encode()).hexdigest()==row['query_section_sha256'] and len(ds)==int(row['raw_reported_domains']),'Native original section/domain count drift')
            domain_lookup[(str(path),name)]={ (d['target_name'],int(d['domain_number'])):d for d in ds }
        must(found==set(wanted),'Incomplete original native queries')
    return rows,profiles,scopes,domain_lookup

def check_domains(reader,inventory,execution,freeze,sources,prepared,query_rows,profiles,scopes,lookup,padloc_db):
    metadata={r['hmm.name']:r for r in records(padloc_db/'hmm_meta.txt')};must(reader.digest(padloc_db/'hmm_meta.txt')==freeze['padloc_metadata_system_files']['hmm_meta.txt'],'PADLOC metadata changed')
    role_path=padloc_db/'model_role_manifest.tsv';must(reader.digest(role_path)==freeze['padloc_metadata_system_files']['model_role_manifest.tsv'],'Pinned model-role manifest changed');pad_roles=defaultdict(list)
    for r in records(role_path):
        for name in r['active_hmm_names'].split('|'):
            if name and name!='NA':pad_roles[name].append({k:r[k] for k in ('model','role_class','role')})
    pad_paths={r['query_name']:str(reader.path(str(execution/r['raw_file']))) for r in query_rows if r['detector']=='PADLOC'}
    by_id={};rows=records(inventory/'all_native_profile_domains.tsv');raw_queues=[q for q in prepared['queue'] if q['kind']=='RAW_DOMAIN'];queues={q['evidence']['hit_id']:q for q in raw_queues};must(len(queues)==len(raw_queues),'Duplicate raw-domain queue');dom_cache={}
    for index,row in enumerate(rows,1):
        key=row['locus_key'];must(key in sources and all(row[flag]==str(sources[key][flag]) for flag in FLAGS),'Native domain/source flags mismatch')
        source=sources[key];domain=json.loads(row['native_domain_json']);raw=reader.path(str(execution/row['raw_file']));must(reader.digest(raw)==row['raw_file_sha256'],'Native domain original hash mismatch')
        detector=row['detector'];name=row['profile_name']
        if detector=='PADLOC':
            profile=profiles[name];target=key;original=lookup[(pad_paths[name],name)][(target,int(domain['domain_number']))]
            must(domain['profile_metadata']==metadata[name],'Native metadata projection mismatch')
            if raw not in dom_cache:dom_cache[raw]=dom_records(raw)
            matches=[d for d in dom_cache[raw] if d['target_name']==key and d['profile_name']==name and int(d['domain_number'])==int(domain['domain_number'])]
            must(len(matches)==1 and matches[0]=={k:v for k,v in domain.items() if k!='profile_metadata'},'Actual PADLOC domtbl row differs')
            settings=None;meta=metadata[name];native_roles=pad_roles[name]
        else:
            must(detector=='DefenseFinder','Unknown domain detector');scope=next(v for (task,family),v in scopes.items() if family==row['family'] and str(raw).startswith(str(execution/task/'families'/family)))
            profile=next(p for p in scope['profiles'] if p['query_name']==name);target=source['df_bundle_target_id'];original=lookup[(str(raw),name)][(target,int(domain['domain_number']))];settings=scope['native_settings'];meta=None;native_roles=[r for r in scope['roles'] if r['gene_name']==profile['gene_name']]
        for field,value in original.items():
            must(field in domain and (domain[field]==value if field in ('target_name','profile_name') else number(domain[field])==number(value)),'Original HMM section/domain numeric mismatch: '+field)
        must(row['profile_sha256']==profile['profile_sha256'],'Native domain profile hash mismatch')
        hid='DH_'+objsha({'detector':detector,'family':row['family'],'raw_file':row['raw_file'],'locus_key':key,'profile_sha256':row['profile_sha256'],'domain':domain})[:28]
        must(hid not in by_id and hid in queues,'Native domain queue missing/duplicated')
        hit=queues[hid]['evidence'];must(hit['domain']==domain and hit['locus_key']==key and hit['source_aa_sha256']==source['primary_faa_sequence_sha256'] and hit['profile_sha256']==profile['profile_sha256'],'Queued domain/source identity mismatch')
        reader.ref(hit['raw_ref']);must(hit['raw_ref']['record_locator']=='tsv:'+str(index) and reader.ref(hit['raw_ref'])==row,'Domain raw reference mismatch')
        normalized=dict(domain,target_length=source['protein_aa_length']);numeric=numeric_threshold(normalized,profile,meta,settings)
        by_id[hid]={**hit,'_numeric_pass':numeric,'native_role_threshold_passed':numeric,'threshold_receipt_verified':True,'target_length':source['protein_aa_length'],'alignment_from':int(domain['alignment_from']),'alignment_to':int(domain['alignment_to'])}
        must(by_id[hid]['native_model_roles']==json.loads(row['model_roles_json'])==native_roles,'Pinned native role assignment inventory drift')
    must(set(by_id)==set(queues),'Missing/extra raw domain queue')
    selected_padloc(by_id)
    for hid,h in by_id.items():
        given=queues[hid]['evidence'];must(given['native_role_threshold_passed']==h['native_role_threshold_passed'] and given['threshold_receipt_verified'] is True,'Native domain threshold/ranking projection mismatch')
        if h['detector']=='PADLOC':must(given['native_selected_model_ids']==h['native_selected_model_ids'],'PADLOC best/top5/model ranking mismatch')
    return by_id

def check_native_candidates(reader,inventory,execution,sources,prepared,scope,model_roots):
    """Rebuild exact native table groups so omitting a queue cannot create white."""
    candidate_scope={(s['detector'],s['model_id']):s for s in scope['models']};must(len(candidate_scope)==39,'Candidate model scope drift')
    groups={};rows=records(inventory/'all_native_system_candidate_rows.tsv');must(len({objsha(r) for r in rows})==len(rows),'Repeated native candidate inventory row');cache={}
    for row in rows:
        key=row['locus_key'];must(key in sources and row['assembly_accession']==prepared['assembly_accession'],'Native candidate source absent')
        p=reader.path(str(execution/row['raw_file']));must(reader.digest(p)==row['raw_file_sha256'],'Original native candidate table changed')
        if p not in cache:cache[p]=records(p,',' if row['detector']=='PADLOC' else '\t',row['detector']!='PADLOC')
        native=json.loads(row['native_row_json']);base={k:v for k,v in native.items() if k not in ('assembly_accession','source_replicon','locus_key','protein_accession')}
        must(sum(r==base for r in cache[p])==1,'Original native candidate row missing/ambiguous')
        source=sources[key]
        if row['detector']=='PADLOC':
            must(native['target.name']==key and native['seqid']==source['replicon'] and native.get('system','')==row['model_fqn'],'PADLOC native source/model sequence mismatch');group_id=native['system.number'];call_class='PADLOC_NATIVE_SYSTEM'
        else:
            must(row['detector']=='DefenseFinder' and native['hit_id']==source['df_bundle_target_id'] and native['replicon']==source['df_bundle_replicon_name'] and int(native['hit_pos'])==int(source['df_bundle_sequence_rank']) and native['model_fqn']==row['model_fqn'],'DF native source/model sequence/order mismatch')
            rejected=row['native_table']=='rejected_candidates.tsv';group_id=native['candidate_id'] if rejected else native['sys_id'];call_class='REJECTED_NATIVE_CANDIDATE' if rejected else 'NATIVE_SYSTEM_CANDIDATE'
        identity=(row['detector'],row['raw_file'].rsplit('/',1)[0],row['model_fqn'],group_id,call_class,source['replicon'])
        if identity not in groups:groups[identity]={'rows':[],'loci':set(),'scope':candidate_scope.get((row['detector'],row['model_fqn']))}
        groups[identity]['rows'].append(row);groups[identity]['loci'].add(key)
    known={};unknown=[]
    for identity,group in groups.items():
        detector,_,model,group_id,call_class,rep=identity;entry=group['scope']
        if entry is None:unknown.append((detector,model,group_id,call_class,rep,group));continue
        if detector=='PADLOC':definition=model_roots['padloc_db']/'sys'/entry['source_member'].split('/sys/',1)[1]
        else:definition=model_roots['models']/entry['model_id'].split('/',1)[0]/'definitions'/(entry['model_id'].split('/',1)[1]+'.xml')
        must(reader.digest(reader.path(str(definition)))==entry['source_sha256'],'Pinned candidate definition changed')
        identity,cid=canonical(prepared['assembly_accession'],entry['proposed_type'],sorted(group['loci']))
        if cid not in known:known[cid]={'identity':identity,'detectors':set(),'subtypes':set(),'rows':[]}
        known[cid]['detectors'].add(detector);known[cid]['subtypes'].add(entry['subtype']);known[cid]['rows']+=group['rows']
    qknown=[q for q in prepared['queue'] if q['kind']=='NATIVE_CANDIDATE'];qmap={q['evidence']['candidate_id']:q for q in qknown}
    must(len(qknown)==len(qmap) and set(qmap)==set(known),'Native architecture queue omitted/added/duplicated')
    for cid,expected in known.items():
        q=qmap[cid];actual=q['evidence'];reader.refs(q['actual_evidence_refs']);resolved=[reader.ref(ref) for ref in q['actual_evidence_refs']]
        must(all(actual[k]==v for k,v in expected['identity'].items()) and actual['detectors']==sorted(expected['detectors']) and actual['subtypes']==sorted(expected['subtypes'],key=str),'Native type/locus-set/detector/subtype dedup drift')
        must(actual['subtype_conflict']==(len(expected['subtypes'])>1) and actual['subtype']==(next(iter(expected['subtypes'])) if len(expected['subtypes'])==1 else None),'Native subtype conflict erased')
        must(all(row in resolved for row in expected['rows']),'Candidate queue omitted actual native inventory row')
        overlaps=sorted(other for other,g in known.items() if other!=cid and set(g['identity']['locus_keys'])&set(expected['identity']['locus_keys']))
        must(actual['overlapping_candidate_ids']==overlaps,'Native candidate overlap context omitted')
    qunknown=[q for q in prepared['queue'] if q['kind']=='NATIVE_MODEL_CONTEXT'];must(len(qunknown)==len(unknown),'Unknown native model context omitted')
    for detector,model,group_id,call_class,rep,group in unknown:
        matches=[q for q in qunknown if q['evidence']['detector']==detector and q['evidence']['model_fqn']==model and q['evidence']['native_group_id']==group_id and q['evidence']['native_call_class']==call_class and q['evidence']['locus_keys']==sorted(group['loci']) and q['evidence']['raw_rows']==group['rows']]
        must(len(matches)==1,'Unknown native model group/source context absent');reader.refs(matches[0]['actual_evidence_refs'])

def rotate_intervals(parts,length,offset):
    out=[]
    for start,end,strand in parts:
        must(type(start) is int and type(end) is int and type(strand) is int and 0<=start<end<=length and strand in (-1,1),'Invalid source interval')
        lo=(start-offset)%length;hi=lo+end-start;new=[[lo,min(hi,length),strand]]
        if hi>length:
            new.append([0,hi-length,strand])
            if strand<0:new.reverse()
        out.extend(new)
    return out

def check_reviewed_code(contract,opened):
    """An arbitrary caller hash never authorizes a new producer revision."""
    must(sha(opened['policy_source'])==POLICY and sha(opened['producer_snapshot'])==SNAPSHOT,
         'Reviewed policy/schema snapshot drift')
    must(contract['reviewed_producer_sha256']==SNAPSHOT and sha(opened['producer_source'])==SNAPSHOT,
         'Unreviewed producer revision; version the checker contract before use')
    text=opened['producer_source'].read_text(encoding='utf-8')
    must(("POLICY_SHA='"+POLICY+"'") in text and ("POLICY_RECONCILIATION_SHA='"+RECONCILIATION+"'") in text,
         'Producer exact current policy/reconciliation pins changed')

def check_policy_reconciliation(opened,reader):
    """Reopen exact current repair record and its eight small code/test artifacts."""
    path=opened['policy_reconciliation'];must(reader.digest(path)==RECONCILIATION,'Policy reconciliation bytes drift')
    report=read(path)
    must(report['status']=='FROZEN_CURRENT_POLICY_RECONCILED_AND_SYNTHETICALLY_RETESTED_ONLY'
         and report['current_policy_sha256']==POLICY and report['original_fixture_passes']==55
         and report['additional_independent_guard_passes']==10 and report['failures']==0
         and report['biological_searches']=='NOT_RUN' and report['actual_architecture_curation']=='NOT_RUN',
         'Policy repair report is not the independently reviewed synthetic reconciliation')
    rows=report['files'];must(len(rows)==8 and len({r['path'] for r in rows})==8,'Policy repair artifact set drift')
    for row in rows:
        member=reader.path(row['path']);must(member.stat().st_size==row['bytes'] and reader.digest(member)==row['sha256'],
                                            'Policy reconciliation cited artifact changed: '+row['path'])
    must(any(r['sha256']==POLICY for r in rows),'Current architecture policy absent from reconciliation')

def require_candidate_outcomes(candidate,outcomes):
    """Unresolved candidate evidence cannot turn its possible types white."""
    state=candidate['result']['state'];rm_type=candidate['rm_type']
    if state in ('COMPLETE_PREDICTED','CURATED_PARTIAL'):
        must(rm_type in TYPES and outcomes[rm_type]=='RESOLVED_WITH_EXECUTED_BASIS','Typed architecture flagged unresolved')
    elif state in ('UNCERTAIN','PARTIAL_CANDIDATE') and not candidate['result'].get('excluded_from_type_cell'):
        must(all(v=='UNRESOLVED' for v in outcomes.values()) if rm_type is None else outcomes[rm_type]=='UNRESOLVED',
             'Unresolved candidate interpretation cannot clear its possible type')

def original_padloc_dom_hash(reader,assembly):
    """Resolve a zero-row original DOM through the completed native task receipt."""
    must(hasattr(reader,'native_runtime'),'Explicit original PADLOC runtime contract missing')
    runtime=reader.native_runtime;task=runtime['execution']/'assemblies'/assembly/'padloc'
    complete=read(reader.path(str(task/'complete.json')))
    must(complete['execution']=='NATIVE_OUTPUTS_CHECKED' and complete['scientific_curation']=='NOT_RUN'
         and complete['identity']['freeze_sha256']==runtime['freeze_sha256'],
         'Original PADLOC task was not successfully completed with current freeze')
    inventory_path=reader.path(str(task/'native_call_inventory.json'));native=read(inventory_path)
    must(complete['files']['native_call_inventory.json']==reader.digest(inventory_path)
         and native['search_complete'] is True and native['curation_state']=='NOT_RUN',
         'Original PADLOC inventory is unbound or search incomplete')
    attempt=native['classification_attempt']
    must(isinstance(attempt,str) and re.fullmatch(r'classification_attempt_\d+',attempt)
         and complete['summary']['classification_attempt']==attempt,'Original classification attempt drift')
    relative=attempt+'/native/proteins.domtblout';path=reader.path(str(task/relative));digest=reader.digest(path)
    must(complete['files'][relative]==digest,'Original PADLOC full DOM file lacks exact native completion binding')
    return digest

def check_rotation(rotation,queue,sources,hits,reader):
    reader.nested(rotation);must(rotation['execution']=='EXECUTED_NATIVE_CLASSIFICATION_FROM_CACHED_HMM' and rotation['biological_HMM_searches_repeated']==0 and rotation['source_topology']=='DOCUMENTED_CIRCULAR','Invalid cached-domain rotation execution')
    original=queue['evidence']['original_locus_order'];rotated=rotation['rotated_locus_order'];offset=rotation['rotation_offset']
    must(rotation['original_locus_order']==original and type(offset) is int and 0<=offset<len(original) and rotated==original[offset:]+original[:offset],'Invalid circular permutation')
    must(rotation['input_cached_dom_sha256']==rotation['used_cached_dom_sha256']==rotation['cached_domain_ref']['sha256'],'Rotation changed cached domain bytes')
    must(set(rotation['unchanged_source_aa_sha256'])==set(original) and all(rotation['unchanged_source_aa_sha256'][k]==sources[k]['primary_faa_sequence_sha256'] for k in original),'Rotation source AA identity map changed')
    geometry=reader.ref(rotation['geometry_ref']);rep=queue['evidence']['source_replicon'];length=rep['gbff_length'];nt=geometry['rotation_nt_offset_zero_based']
    must(rep['documented_circular'] is True and geometry['execution']=='EXECUTED_SOURCE_COORDINATE_CIRCULAR_PERMUTATION' and geometry['replicon']==rep['replicon'] and geometry['replicon_length']==length and type(nt) is int and 0<=nt<length,'Rotation source geometry invalid')
    rows={r['locus_key']:r for r in geometry['loci']};must(len(rows)==len(geometry['loci'])==len(original) and set(rows)==set(original),'Rotation source context lost')
    transformed={}
    for i,key in enumerate(original,1):
        parts=json.loads(sources[key]['gbff_parts_zero_based_biological_order']);expected=rotate_intervals(parts,length,nt);transformed[key]=expected;r=rows[key]
        must(r['source_parts']==parts and r['rotated_parts']==expected and r['original_context_ordinal']==i and r['rotated_context_ordinal']==rotated.index(key)+1 and r['source_aa_sha256']==sources[key]['primary_faa_sequence_sha256'],'Rotation actual coordinates/order/AA mismatch')
    must(rotated==sorted(original,key=lambda key:(min(p[0] for p in transformed[key]),original.index(key))),'Rotated physical ranks mismatch')
    mapping=reader.ref(rotation['domain_target_map_ref']);items=mapping['domains'];expected={hid:h for hid,h in hits.items() if h['detector']=='PADLOC' and h['locus_key'] in original};mapped={i['hit_id']:i for i in items}
    must(mapping['execution']=='EXECUTED_EXACT_SOURCE_TARGET_AND_CACHED_DOMAIN_REMAPPING' and len(items)==len(mapped)==len(expected) and set(mapped)==set(expected),'Rotation cached-domain set mismatch')
    protein_order=[k for k in rotated if sources[k]['protein_target_present']]
    for hid,h in expected.items():
        r=mapped[hid];key=h['locus_key'];must(r['locus_key']==r['target_id_before']==r['target_id_after']==key and r['native_domain_record_sha256']==objsha(h['domain']) and r['source_aa_sha256']==sources[key]['primary_faa_sequence_sha256'] and r['original_protein_ordinal']==int(sources[key]['protein_ordinal_on_replicon']) and r['rotated_protein_ordinal']==protein_order.index(key)+1,'Rotated target/domain/source ordinal mismatch')
    original_domain_hashes={reader.ref(h['raw_ref'])['raw_file_sha256'] for h in hits.values() if h['detector']=='PADLOC'}
    original_domain_hashes.add(original_padloc_dom_hash(reader,queue['assembly_accession']))
    must(rotation['input_cached_dom_sha256'] in original_domain_hashes,'Rotation cache differs from original full native domains')
    actual=proteins(reader.path(rotation['rotated_faa_ref']['path']));must(actual=={k:s['_sequence'] for k,s in sources.items() if s['protein_target_present']},'Rotation changed/dropped/added primary proteins')
    gff={}
    for line in reader.path(rotation['rotated_gff_ref']['path']).read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        fields=line.split('\t');must(len(fields)==9 and fields[2]=='CDS','Malformed rotated GFF')
        attrs=dict(v.split('=',1) for v in fields[8].split(';') if '=' in v);key=attrs.get('ID','').removeprefix('cds-');must(key in actual and key not in gff,'Rotated GFF source target missing/duplicated');gff[key]=fields
    must(set(gff)==set(actual),'Rotated GFF target set differs')
    for key,fields in gff.items():
        parts=transformed[key] if key in transformed else json.loads(sources[key]['gbff_parts_zero_based_biological_order'])
        must(fields[0]==sources[key]['replicon'] and int(fields[3])==min(p[0] for p in parts)+1 and int(fields[4])==max(p[1] for p in parts) and fields[6]==('+' if int(sources[key]['gbff_strand'])==1 else '-'),'Rotated GFF source geometry mismatch')
    native=reader.ref(rotation['native_command_ref']);launch=reader.ref(rotation['native_launch_ref']);stdout=reader.ref(rotation['native_stdout_ref'])
    must(native['execution']=='PROCESS_EXITED' and native['exit_code']==0 and native['child_pid']==launch['child_pid']>0 and native['argv']==launch['argv'] and native['identity']==launch['identity'] and native['stdout_sha256']==rotation['native_stdout_ref']['sha256'] and 'domtblout already exists' in stdout,'Rotation native exit/cache evidence invalid')
    must(hasattr(reader,'native_runtime'),'Explicit pinned rotation runtime contract missing');runtime=reader.native_runtime;argv=native['argv']
    executable=reader.path(argv[0]);must(executable==(runtime['environment']/'bin/padloc').resolve() and reader.digest(executable)==runtime['freeze']['tools']['padloc'] and native['identity']['freeze_sha256']==runtime['freeze_sha256'],'Rotation executable/freeze changed')
    for option,path in [('--faa',reader.path(rotation['rotated_faa_ref']['path'])),('--gff',reader.path(rotation['rotated_gff_ref']['path'])),('--data',runtime['padloc_db'])]:
        must(argv.count(option)==1,'Rotation native option missing/duplicated');value=argv[argv.index(option)+1];resolved=reader.path(value) if option!='--data' else reader.directory(value);must(resolved==path.resolve(),'Rotation actual native argv differs')
    must(argv.count('--cpu')==1 and argv[argv.index('--cpu')+1]=='2' and argv.count('--outdir')==1,'Rotation native CPU/output options differ')
    output=reader.directory(argv[argv.index('--outdir')+1]);cached=reader.path(rotation['cached_domain_ref']['path']);must(cached==(output/(Path(argv[argv.index('--faa')+1]).stem+'.domtblout')).resolve(),'Rotation did not reuse actual original cached DOM input')
    audit=reader.ref(rotation['independent_validation_ref']);must(audit['status']=='PASS_CACHED_DOMAIN_ROTATION_GEOMETRY_AND_SOURCE_ACCOUNTING' and audit['biological_HMM_searches_repeated']==0 and audit['assembly_accession']==queue['assembly_accession'] and audit['replicon']==rep['replicon'],'Rotation independent audit absent')
    for field,key in [('geometry_sha256','geometry_ref'),('domain_target_map_sha256','domain_target_map_ref'),('native_command_sha256','native_command_ref'),('rotated_faa_sha256','rotated_faa_ref'),('rotated_gff_sha256','rotated_gff_ref'),('cached_domain_sha256','cached_domain_ref'),('validator_source_sha256','independent_validator_source_ref')]:must(audit[field]==rotation[key]['sha256'],'Rotation independent audit stale binding')

def reviewed_candidate(native,record,sources,hits,reader):
    candidate=dict(native);loci=list(candidate['locus_keys']);extra=record.get('additional_source_locus_keys',[])
    must(isinstance(extra,list) and len(set(extra))==len(extra) and not set(extra)&set(loci),'Duplicate source neighborhood expansion')
    if extra:
        must(record.get('candidate_expansion_execution')=='EXECUTED_SOURCE_NEIGHBORHOOD_REVIEW' and record.get('candidate_expansion_rationale') and all(k in sources for k in extra),'Unreviewed/invented neighborhood extension');reader.refs(record['candidate_expansion_basis_refs']);candidate['locus_keys']=sorted(loci+extra)
    review=record['candidate_review']
    if review['rm_type']!=candidate['rm_type']:
        must(review['rm_type'] in TYPES and record.get('type_mapping_execution')=='EXECUTED_SOURCE_DOMAIN_CONTEXT_TYPE_MAPPING','Unreviewed type remapping');reader.refs(record['type_mapping_basis_refs']);candidate['rm_type']=review['rm_type']
    if candidate.get('subtype_conflict'):
        must(record.get('subtype_resolution_execution')=='EXECUTED_SOURCE_DOMAIN_CONTEXT_SUBTYPE_REVIEW','Unreviewed native subtype conflict');reader.refs(record['subtype_resolution_basis_refs']);candidate['subtype']=record['reviewed_subtype']
    identity,cid,result,used=architecture(candidate,review,sources,hits,reader)
    if result['state']=='COMPLETE_PREDICTED' and native.get('overlapping_candidate_ids'):
        must(record.get('overlap_review_execution')=='EXECUTED_EXACT_LOCUS_COUNTING_REVIEW','Overlapping complete count not reviewed');reader.refs(record['overlap_review_basis_refs'])
    return {**identity,'candidate_id':cid,'native_candidate_id':native.get('candidate_id'),'native_candidate_refs':candidate['native_candidate_refs'],'review_record_sha256':objsha(record),'result':result,'used_hit_ids':used}

def reconstruct(prepared,document,record,sources,hits,search,reader):
    assembly=prepared['assembly_accession'];must(document['assembly_accession']==record['assembly_accession']==assembly,'Wrong reviewed assembly')
    must(document['execution']=='EXECUTED_FULL_REQUIRED_EVIDENCE_REVIEW' and document['prepared_queue_sha256']==objsha(prepared),'Unexecuted/stale assembly review')
    must(record['prepared_queue_sha256']==objsha(prepared) and record['review_document_sha256']==objsha(document) and record['source_snapshot']==prepared['source_snapshot'],'Curated source/review provenance drift')
    queue=prepared['queue'];ids=[q['queue_id'] for q in queue];must(len(ids)==len(set(ids)),'Duplicate required queue')
    reviews={r['queue_id']:r for r in document['reviews']};must(len(reviews)==len(document['reviews']) and set(reviews)==set(ids),'Queue review dropped/duplicated/added')
    snapshot_sha=objsha(prepared['source_snapshot']);unresolved={t:Counter() for t in TYPES};candidates=[];dispositions={};used=set()
    kinds={'SOURCE_CONTEXT':'unresolved_source_contexts','EMPTY_REPLICON':'unresolved_empty_replicons','CIRCULAR_ORIGIN_CONTEXT':'unresolved_origin_classifications','RAW_DOMAIN':'unresolved_model_mappings','NATIVE_MODEL_CONTEXT':'unresolved_model_mappings','NATIVE_CANDIDATE':'unresolved_model_mappings'}
    for q in queue:
        must(q['kind'] in kinds and q['assembly_accession']==assembly and q['affected_types']==list(TYPES),'Unknown queue schema')
        body={k:v for k,v in q.items() if k not in ('queue_id','queue_item_sha256')};identity={k:q[k] for k in ('kind','assembly_accession','identity')}
        must(q['queue_id']=='RQ_'+objsha(identity)[:28] and q['queue_item_sha256']==objsha({**body,'queue_id':q['queue_id']}),'Queue ID/item integrity mismatch')
        review=reviews[q['queue_id']];must(review['execution']=='EXECUTED_HASH_BOUND_EVIDENCE_REVIEW' and review['queue_item_sha256']==q['queue_item_sha256'] and review['source_snapshot_sha256']==snapshot_sha and isinstance(review.get('rationale'),str) and review['rationale'].strip(),'Unexecuted/stale queue review')
        reader.nested(review);reader.refs(review['evidence_refs']);reader.refs(q['actual_evidence_refs'])
        must({objsha(ref) for ref in q['actual_evidence_refs']}<={objsha(ref) for ref in review['reopened_queue_evidence_refs']},'Required native/source queue evidence omitted')
        outcomes=review['affected_type_decisions'];must(set(outcomes)==set(TYPES) and all(v in ('RESOLVED_WITH_EXECUTED_BASIS','UNRESOLVED') for v in outcomes.values()),'Unreviewed affected type')
        if q['kind']=='NATIVE_CANDIDATE':
            result=reviewed_candidate(q['evidence'],review,sources,hits,reader);candidates.append(result);used.update(result['used_hit_ids'])
            require_candidate_outcomes(result,outcomes)
        elif q['kind']=='RAW_DOMAIN':
            must(review['disposition'] in EXCLUSIONS|{'USED_IN_EXECUTED_CANDIDATE_REVIEW','REVIEWED_OTHER_FULL_SCOPE_DOMAIN_WITH_NO_I_IV_SUPPORT','UNRESOLVED'},'Unknown raw domain disposition')
            dispositions[q['evidence']['hit_id']]=review['disposition']
            if review['disposition']=='UNRESOLVED':must(set(outcomes.values())=={'UNRESOLVED'},'Unresolved domain cleared')
        elif q['kind']=='SOURCE_CONTEXT':
            source=sources[q['evidence']['locus_key']]
            if not source['protein_target_present'] and re.search(r'hypothetical|uncharacterized|unknown function',source['gbff_qualifiers_without_translation']+' '+source['source_gene_qualifiers'],re.I) and any(v!='UNRESOLVED' for v in outcomes.values()):
                must(review.get('primary_locus_specific_resolution')=='EXECUTED_LITERATURE_OR_PROVIDER_CONTRADICTION_REVIEW','Unknown untranslated source cleared by annotation');reader.refs(review['primary_locus_specific_basis_refs'])
        elif q['kind']=='CIRCULAR_ORIGIN_CONTEXT' and review.get('rotation_receipt'):check_rotation(review['rotation_receipt'],q,sources,hits,reader)
        for t,outcome in outcomes.items():
            if outcome=='UNRESOLVED':unresolved[t][kinds[q['kind']]]+=1
    for item in document.get('manual_candidates',[]):
        must(item['execution']=='EXECUTED_SOURCE_NEIGHBORHOOD_REVIEW_OF_FULL_NATIVE_DOMAINS','Unexecuted manual architecture');reader.nested(item);reader.refs(item['candidate']['native_candidate_refs']);result=reviewed_candidate(item['candidate'],item,sources,hits,reader);candidates.append(result);used.update(result['used_hit_ids'])
    must(set(dispositions)==set(hits) and all(h in used for h,d in dispositions.items() if d=='USED_IN_EXECUTED_CANDIDATE_REVIEW'),'Full domains/role joins not accounted')
    unique={}
    for candidate in candidates:
        cid=candidate['candidate_id']
        if cid in unique:must(unique[cid]['result']==candidate['result'],'Exact-locus review conflict');unique[cid]['native_candidate_refs']+=candidate['native_candidate_refs']
        else:unique[cid]=candidate
    must(record['candidates']==list(unique.values()),'Curated candidate provenance/result/dedup mismatch')
    must(record['required_review_items']==len(queue) and record['raw_domains_accounted']==len(hits),'Curated required-item/domain counts mismatch')
    cells=[];coverage_reviews=document['cell_coverage_reviews'];must(set(coverage_reviews)==set(TYPES),'Four full-scope coverage reviews required')
    for t in TYPES:
        reviewed=coverage_reviews[t];must(reviewed['execution']=='EXECUTED_HASH_BOUND_FULL_SCOPE_COVERAGE_REVIEW' and reviewed['source_snapshot_sha256']==snapshot_sha and isinstance(reviewed.get('rationale'),str) and reviewed['rationale'].strip(),'Unexecuted coverage review')
        reader.nested(reviewed);reader.refs(reviewed['evidence_refs']);applicable={q['queue_id'] for q in queue if t in q['affected_types']}
        must(set(reviewed['reviewed_queue_ids'])==applicable and len(reviewed['reviewed_queue_ids'])==len(applicable),'Coverage queue omission/duplicate')
        coverage={k:unresolved[t][k] for k in UNRESOLVED};coverage.update(source_review_execution='EXECUTED_AND_HASH_BOUND',full_query_completion_verified=True,all_tasks_verified=True,all_candidates_accounted=True,all_full_scope_domains_accounted=True,native_completion_refs=prepared['native_completion_refs'])
        results=[c['result'] for c in unique.values() if c['rm_type'] in (t,None)]
        cell={'assembly_accession':assembly,'rm_type':t,**derive_cell(search,coverage,results),'coverage_counts':coverage,'candidate_ids':sorted(c['candidate_id'] for c in unique.values() if c['rm_type'] in (t,None)),'demonstrated_function':'NOT_ESTABLISHED_BY_PROFILE_PREDICTION','review_execution':'COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW'};cells.append(cell)
    must(record['cells']==cells,'Curated cell states/counts/coverage/provenance differ from independent reconstruction')
    return cells

def gate(contract,reader):
    must(contract['schema']==SCHEMA and contract['mode']=='PRODUCTION','Only explicit production contract can validate production')
    artifacts=contract['artifacts'];required={'panel','approval','producer_source','policy_source','producer_snapshot','source_validation','bundle_construction','bundle_validation','raw_validation','raw_validator','stage04_validation','stage04_publication','execution_freeze','inventory_manifest','curation_summary','prepared_manifest','candidate_scope','policy_contract','evidence_parser','policy_reconciliation'}
    must(set(artifacts)==required,'Input artifact schema drift/missing mandatory gates')
    opened={}
    for role,ref in artifacts.items():
        p=reader.path(ref['path']);must(reader.digest(p)==ref['sha256'],'Contract artifact changed: '+role);opened[role]=p
    check_reviewed_code(contract,opened)
    check_policy_reconciliation(opened,reader)
    panel=opened['panel'].read_text().split();matrix(panel,[{'assembly_accession':a,'rm_type':t,'state':'NOT_RUN'} for a in panel for t in TYPES])
    approval=read(opened['approval']);must(approval['human_approval']=='APPROVED_FOR_SEQUENCE_ANALYSIS' and approval['pilot'] is False and approval['approved_assembly_count']==196 and approval['panel_accessions_sha256']==sha(opened['panel']),'Full196 approval invalid')
    validation=read(opened['stage04_validation']);publication=read(opened['stage04_publication'])
    must(validation['status']=='PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY' and validation['primary_tip_ids']==196 and validation['analyses_verified']==4,'Incomplete upstream scientific tree gate')
    must(publication['status']=='UPLOAD_VERIFIED' and publication['remote_tag_commit_verified'] is True and publication['approved_assemblies']==196 and publication['scientific_validation']==validation['status'] and publication['final_validation_summary_sha256']==sha(opened['stage04_validation']),'Upstream publication/current report binding invalid')
    must(publication['assets'] and all(a['download_readback_verified'] is True and a['all_zip_member_hashes_verified'] is True and a['bytes']>0 and SHA.fullmatch(a['sha256']) for a in publication['assets']),'Upstream remote byte verification absent')
    for field in ('analysis_freeze_sha256','phylogeny_summary_sha256'):must(publication[field]==validation[field] and SHA.fullmatch(validation[field]),'Upstream scientific payload binding drift')
    raw=read(opened['raw_validation']);must(raw['status']=='PASS_FULL_NATIVE_SEARCH_AND_SOURCE_ACCOUNTING_ONLY' and raw['scientific_stage05_status']=='ARCHITECTURE_CURATION_REQUIRED' and raw['architecture_curation']=='NOT_RUN' and raw['all_exact196_accounted'] is True and raw['approved_assemblies']==196 and raw['protein_loci']==398537 and raw['replicons']==2120 and raw['empty_replicons']==271,'Raw only/full196 native gate incomplete')
    must(all(raw[k] is True for k in ('full_model_scope_verified','native_query_domain_source_join_verified','native_table_inventory_equivalence_verified')),'Raw independent evidence joins incomplete')
    for field,role in [('execution_freeze_sha256','execution_freeze'),('bundle_construction_sha256','bundle_construction'),('bundle_validation_sha256','bundle_validation'),('inventory_manifest_sha256','inventory_manifest'),('source_validation_sha256','source_validation'),('validator_source_sha256','raw_validator'),('stage04_validation_sha256','stage04_validation')]:must(raw[field]==sha(opened[role]),'Raw report source binding drift: '+field)
    source_gate=read(opened['source_validation']);must(source_gate['status']=='PASS_SOURCE_LOCUS_INPUT_TRACEABILITY' and source_gate['complete_exact196_accounting'] is True and source_gate['assemblies_passed']==196 and source_gate['panel_sha256']==sha(opened['panel']),'Independent source-locus gate incomplete')
    bundle_gate=read(opened['bundle_validation']);must(bundle_gate['status']=='PASS_FULL196_DETECTOR_BUNDLE_PARSER_AUDIT' and bundle_gate['assemblies_passed']==bundle_gate['assemblies_audited']==196 and bundle_gate['failures']==[] and bundle_gate['protein_targets_per_tool']==398537 and bundle_gate['replicons']==2120,'Independent detector bundle gate incomplete')
    freeze=read(opened['execution_freeze']);must(freeze['panel_sha256']==sha(opened['panel']) and freeze['stage04_validation_sha256']==sha(opened['stage04_validation']),'Native panel/upstream science changed')
    binding=freeze['stage04_verified_scientific_publication_binding'];must(all(publication.get(k)==v for k,v in binding.items()) and binding['final_validation_summary_sha256']==sha(opened['stage04_validation']),'Executed native upstream publication binding drift')
    must(sha(opened['candidate_scope'])=='6284203055ada645b3f6a8023e71e57a5fe8156bc9d4dffcc72da7614f3b30be','Reviewed39-model candidate scope changed')
    summary=read(opened['curation_summary']);must(summary['status']=='COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW_APPLIED_PENDING_INDEPENDENT_CURATED_VALIDATION' and summary['scientific_stage05_status']=='INDEPENDENT_CURATED_VALIDATION_REQUIRED' and summary['architecture_review']=='EXECUTED_RECORDS_APPLIED' and summary['publication']=='NOT_RUN' and summary['assemblies']==196 and summary['cells']==784 and summary['biological_searches_repeated']==0,'Curated producer status/schema invalid')
    identity=summary['identity'];must(identity['phase']=='apply' and identity['adapter_source_sha256']==sha(opened['producer_source']) and identity['policy_source_sha256']==POLICY and identity['raw_validation_sha256']==sha(opened['raw_validation']) and identity['prepared_manifest_sha256']==sha(opened['prepared_manifest']),'Curated exact code/raw/prepared identity drift')
    for field,role in [('evidence_parser_sha256','evidence_parser'),('policy_contract_sha256','policy_contract'),('model_candidate_scope_sha256','candidate_scope'),('execution_freeze_sha256','execution_freeze'),('bundle_construction_sha256','bundle_construction'),('bundle_validation_sha256','bundle_validation'),('inventory_manifest_sha256','inventory_manifest'),('source_validation_sha256','source_validation'),('validator_source_sha256','raw_validator'),('panel_sha256','panel'),('policy_reconciliation_sha256','policy_reconciliation')]:must(identity[field]==sha(opened[role]),'Curated source/code/policy contract identity drift: '+field)
    prepared=read(opened['prepared_manifest']);must(prepared['status']=='FULL196_ACTUAL_SOURCE_NATIVE_EVIDENCE_QUEUE_PREPARED_REVIEW_PENDING' and prepared['assemblies']==196 and prepared['identity']=={k:('prepare' if k=='phase' else v) for k,v in identity.items() if k!='prepared_manifest_sha256'},'Prepared/apply exact identity drift')
    return opened,panel,freeze,summary

def check_source_queue(prepared,sources,reps,inventory):
    qs=prepared['queue'];context={q['evidence']['locus_key']:q for q in qs if q['kind']=='SOURCE_CONTEXT'};annot={r['locus_key'] for r in records(inventory/'source_annotation_review.tsv')}
    required={k for k,s in sources.items() if any(s[f] for f in FLAGS if f!='protein_target_present') or s['linear_edge'] or not s['protein_target_present'] or k in annot}
    must(set(context)==required,'Source annotation/partial/edge/unknown queue incomplete')
    for key,q in context.items():must(q['evidence']['source']=={k:v for k,v in sources[key].items() if k!='_sequence'},'Prepared source facts drift')
    empty=[q['identity']['replicon'] for q in qs if q['kind']=='EMPTY_REPLICON'];circular=[q['identity']['replicon'] for q in qs if q['kind']=='CIRCULAR_ORIGIN_CONTEXT']
    must(len(empty)==len(set(empty)) and set(empty)=={r['replicon'] for r in reps if r['primary_protein_targets']==0},'Empty sequence record omitted')
    must(len(circular)==len(set(circular)) and set(circular)=={r['replicon'] for r in reps if r['documented_circular'] is True},'Documented circular origin omitted')
    by_rep={r['replicon']:r for r in reps}
    for q in qs:
        if q['kind']=='EMPTY_REPLICON':must(q['evidence']==by_rep[q['identity']['replicon']],'Empty sequence context payload differs')
        if q['kind']=='CIRCULAR_ORIGIN_CONTEXT':
            name=q['identity']['replicon'];must(q['evidence']['source_replicon']==by_rep[name] and q['evidence']['original_locus_order']==[k for k,s in sources.items() if s['replicon']==name],'Circular source context/order payload differs')

def run(contract):
    start=time.perf_counter();root=Path(contract['root']).resolve();roots={k:(root/v).resolve() for k,v in contract['roots'].items()}
    must(set(roots)=={'source','bundle','execution','inventory','prepared','reviews','curated','padloc_db','models','evidence','environment','config','reports','scripts','checker','producer','policy'},'Reviewed root-role schema drift')
    reader=Reader(root,list(roots.values()),contract.get('linux_root'));opened,panel,freeze,summary=gate(contract,reader)
    reader.native_runtime={'execution':roots['execution'],'environment':roots['environment'],'padloc_db':roots['padloc_db'],'freeze':freeze,'freeze_sha256':sha(opened['execution_freeze'])}
    entries=summary['outputs'];must([e['assembly_accession'] for e in entries]==panel and len(entries)==196,'Curated full196 output accounting differs')
    inventory_manifest=read(opened['inventory_manifest']);must(inventory_manifest['status']=='NATIVE_EVIDENCE_INVENTORY_CURATION_PENDING' and inventory_manifest['scientific_stage05_status']=='NOT_VALIDATED' and inventory_manifest['execution_freeze_sha256']==sha(opened['execution_freeze']) and [e['assembly_accession'] for e in inventory_manifest['assemblies']]==panel,'Inventory exact source identity drift')
    listed={r['path']:r for r in inventory_manifest['output_files']};must(len(listed)==len(inventory_manifest['output_files']),'Duplicate native inventory manifest member')
    actual={p.relative_to(roots['inventory']).as_posix() for p in roots['inventory'].rglob('*') if p.is_file()};must(actual==set(listed)|{'inventory_manifest.json'},'Native inventory missing/extra member')
    for name,entry in listed.items():
        p=reader.path(str(roots['inventory']/name));must(p.stat().st_size==entry['bytes'] and reader.digest(p)==entry['sha256'],'Native inventory member bytes changed')
    prep_manifest=read(opened['prepared_manifest']);preps=prep_manifest['outputs'];must([e['assembly_accession'] for e in preps]==panel,'Prepared full196 accession membership differs');prep_by={e['assembly_accession']:e for e in preps};scope=read(opened['candidate_scope'])
    all_cells=[];totals=Counter()
    for entry in entries:
        assembly=entry['assembly_accession'];p=reader.path(str(roots['curated']/entry['path']));must(reader.digest(p)==entry['sha256'],'Curated assembly file changed')
        record=read(p);prepath=roots['prepared']/'assemblies'/assembly/'prepared_queue.json';must(reader.digest(prepath)==prep_by[assembly]['sha256'],'Prepared queue manifest bytes differ');prepared=read(prepath);docpath=roots['reviews']/(assembly+'.json');document=read(docpath)
        must(record['actual_review_file_sha256']==sha(docpath),'Actual review file changed')
        must(record['review_execution']=='COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW' and record['scientific_stage05_status']=='INDEPENDENT_CURATED_VALIDATION_REQUIRED','Unexecuted curated assembly')
        for name,digest in prepared['source_snapshot'].items():must(reader.digest(reader.path(name))==digest,'Source/native prepared snapshot changed')
        source=roots['source']/'assemblies'/assembly;inventory=roots['inventory']/'assemblies'/assembly;execution=roots['execution']/'assemblies'/assembly
        rows=records(inventory/'source_locus_crosswalk.tsv');reps=read(source/'replicon_manifest.json');seqs=proteins(source/(assembly+'.faa'));sources=sources_from_rows(rows,seqs,reps,assembly)
        crosswalk=inventory/'source_locus_crosswalk.tsv';crosswalk_sha=reader.digest(crosswalk)
        reader.source_refs={row['locus_key']:{'path':crosswalk.relative_to(root).as_posix(),'sha256':crosswalk_sha,
            'record_locator':'tsv:'+str(i),'record_sha256':objsha(row)} for i,row in enumerate(rows,1)}
        source_receipt=read(source/'build_receipt.json');bundle=roots['bundle']/'assemblies'/assembly;bundle_receipt=read(bundle/'bundle_receipt.json');must(bundle_receipt['source_receipt_sha256']==sha(source/'build_receipt.json'),'Bundle source receipt drift')
        for name in ('locus_crosswalk.tsv','replicon_manifest.json',assembly+'.faa'):
            ref=next(e for e in source_receipt['output_files'] if e['path']==name);must((source/name).stat().st_size==ref['bytes'] and sha(source/name)==ref['sha256'],'Source build-receipt member changed')
        original={r['locus_key']:r for r in records(source/'locus_crosswalk.tsv')};must(len(original)==len(rows) and all(r['locus_key'] in original and all(r.get(k)==v for k,v in original[r['locus_key']].items()) for r in rows),'Inventory source row differs from original source')
        for ref in bundle_receipt['output_files']:
            member=reader.path(str(bundle/ref['path']));must(member.stat().st_size==ref['bytes'] and reader.digest(member)==ref['sha256'],'Detector bundle actual member changed')
        must(sha(bundle/'locus_crosswalk.tsv')==sha(inventory/'source_locus_crosswalk.tsv') and sha(bundle/'replicon_topology.tsv')==sha(inventory/'source_replicon_topology.tsv'),'Inventory source topology/crosswalk copy differs')
        check_source_queue(prepared,sources,reps,inventory);search=check_task_receipts(reader,prepared,opened['execution_freeze'],sources,execution)
        query_rows,profiles,scopes,lookup=check_queries(reader,inventory,execution,freeze,sources)
        hits=check_domains(reader,inventory,execution,freeze,sources,prepared,query_rows,profiles,scopes,lookup,roots['padloc_db'])
        check_native_candidates(reader,inventory,execution,sources,prepared,scope,roots)
        cells=reconstruct(prepared,document,record,sources,hits,search,reader);all_cells.extend(cells)
        for key,value in [('source_context_loci',len(sources)),('protein_loci',len(seqs)),('replicons',len(reps)),('empty_replicons',sum(r['primary_protein_targets']==0 for r in reps))]:must(entry[key]==value,'Assembly source accounting drift');totals[key]+=value
        reader.release_assembly([roots['padloc_db'],roots['models'],roots['environment']])
    matrix(panel,all_cells);must(dict(totals)=={'source_context_loci':411523,'protein_loci':398537,'replicons':2120,'empty_replicons':271},'Full source cohort accounting changed')
    observed=records(roots['curated']/'rm_cells.tsv');must(len(observed)==784 and list(observed[0])==CELL_COLUMNS,'Cell TSV schema drift')
    expected=[]
    for row in all_cells:expected.append({k:packed(row[k]) if isinstance(row[k],(dict,list)) else str(row[k]) for k in CELL_COLUMNS})
    must(observed==expected,'Published cell TSV differs from actual independently reconstructed cells')
    must(summary['cell_states']==dict(Counter(c['state'] for c in all_cells)),'Curated cell state summary differs')
    # Contract is frozen across validation; no reads of mutable checkpoints.
    for ref in contract['artifacts'].values():must(sha(reader.path(ref['path']))==ref['sha256'],'Input changed during independent validation')
    return {'status':'PASS_REVIEWED_STAGE05_ARCHITECTURE_AND_784_CELLS','schema':SCHEMA,'adopted':False,'approved_assemblies':196,'cells':784,'source_counts':dict(totals),'states':dict(Counter(c['state'] for c in all_cells)),'validator_source_sha256':sha(__file__),'contract_sha256':objsha(contract),'producer_source_sha256':sha(opened['producer_source']),'policy_source_sha256':POLICY,'policy_reconciliation_sha256':RECONCILIATION,'raw_validation_sha256':sha(opened['raw_validation']),'curation_summary_sha256':sha(opened['curation_summary']),'publication':'NOT_RUN','functional_evidence':'PROFILE_PREDICTIONS_AND_EXECUTED_ARCHITECTURE_REVIEW_ONLY_NOT_ACTIVITY','elapsed_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time(),'peak_ram_bytes':None,'peak_ram_reason':'Not measured by this standalone candidate; caller must record resource receipt','biological_searches_repeated':0}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--contract',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    try:result=run(read(args.contract));code=0
    except Exception as error:result={'status':'FAIL_CLOSED_CURATED_EVIDENCE_CHECK','error':type(error).__name__+': '+str(error),'adopted':False,'biological_searches_repeated':0};code=1
    args.output.parent.mkdir(parents=True,exist_ok=True);must(not args.output.exists(),'Preserve existing checker output');args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status']);return code

if __name__=='__main__':sys.exit(main())
