"""Strict native HMMER/PADLOC/MacSyFinder evidence parsers; no searches.

Partial HMMER output can establish only a query ending // with target statistics
and matching complete domain rows. It never establishes completion of all models.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import csv,hashlib,io,json,math,re

DOM_FIELDS=['target_name','target_accession','target_length','profile_name','profile_accession','profile_length',
 'full_evalue','full_score','full_bias','domain_number','total_domains','conditional_evalue','independent_evalue',
 'domain_score','domain_bias','hmm_from','hmm_to','alignment_from','alignment_to','envelope_from','envelope_to','accuracy','description']
EXTRACT_FIELDS=['hit_id','replicon','hit_pos','hit_sequence_length','gene_name','i_eval','hit_score',
                'hit_profile_cov','hit_seq_cov','hit_begin_match','hit_end_match']

def require(value,message):
    if not value:raise ValueError(message)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def table(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def json_read(path):return json.loads(Path(path).read_text())
def stage04_publication_binding(validation_path,publication):
    """Bind verified publication to the actual current scientific report."""
    validation=json_read(validation_path)
    require(validation['status']=='PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY'
            and validation['primary_tip_ids']==196 and validation['analyses_verified']==4,'Stage4 scientific report incomplete')
    require(publication['status']=='UPLOAD_VERIFIED' and publication['remote_tag_commit_verified'] is True
            and publication['approved_assemblies']==196 and publication['assets']
            and all(a['download_readback_verified'] is True and a['all_zip_member_hashes_verified'] is True
                    and a['bytes']>0 and re.fullmatch('[a-f0-9]{64}',a['sha256']) for a in publication['assets']),
            'Stage4 publication/readback incomplete')
    require(publication['final_validation_summary_sha256']==sha(validation_path)
            and publication['scientific_validation']==validation['status'],'Stage4 publication/current final scientific report binding differs')
    for field in ['analysis_freeze_sha256','phylogeny_summary_sha256']:
        require(re.fullmatch('[a-f0-9]{64}',validation[field])
                and publication[field]==validation[field],'Stage4 publication scientific payload binding differs: '+field)
    require(re.fullmatch('[a-f0-9]{64}',publication['alignment_validation_summary_sha256']),
            'Stage4 publication alignment validation identity absent')
    return {field:publication[field] for field in ['scientific_validation','final_validation_summary_sha256',
                'analysis_freeze_sha256','alignment_validation_summary_sha256','phylogeny_summary_sha256']}
def numeric(value):
    result=float(value);require(math.isfinite(result),'Nonfinite native numeric field');return result

def domtbl(path,targets=None,profiles=None):
    rows=[]
    for number,line in enumerate(Path(path).read_text().splitlines(),1):
        if not line.strip() or line.startswith('#'):continue
        fields=line.split(maxsplit=22);require(len(fields)==23,'Malformed native domtbl row '+str(number))
        row=dict(zip(DOM_FIELDS,fields));row['source_line']=number;row['native_line']=line
        if targets is not None:
            require(row['target_name'] in targets and int(row['target_length'])==targets[row['target_name']],
                    'Native domtbl target/locus length differs')
        if profiles is not None:
            require(row['profile_name'] in profiles,'Unknown native profile name')
            if isinstance(profiles,dict):
                profile=profiles[row['profile_name']]
                if isinstance(profile,dict):require(int(row['profile_length'])==profile['length'],'Native domtbl pinned profile length differs')
        for field in ['full_evalue','full_score','full_bias','conditional_evalue','independent_evalue','domain_score','domain_bias','accuracy']:
            numeric(row[field])
        for field in ['full_evalue','conditional_evalue','independent_evalue']:
            require(numeric(row[field])>=0,'Native domain Evalue is negative')
        require(0<=numeric(row['accuracy'])<=1,'Native domain accuracy outside[0,1]')
        require(1<=int(row['domain_number'])<=int(row['total_domains']),'Invalid native domain ordinal')
        require(1<=int(row['hmm_from'])<=int(row['hmm_to'])<=int(row['profile_length']), 'Native HMM coordinates invalid')
        require(1<=int(row['alignment_from'])<=int(row['alignment_to'])<=int(row['target_length']), 'Native alignment coordinates invalid')
        require(1<=int(row['envelope_from'])<=int(row['envelope_to'])<=int(row['target_length']), 'Native envelope coordinates invalid')
        rows.append(row)
    return rows

def query_sections(path):
    """Read complete native query blocks even when a later query was interrupted."""
    section=[];first=None
    with Path(path).open(encoding='utf-8') as stream:
        for line_number,line in enumerate(stream,1):
            if line.startswith('Query:'):
                section=[line];first=line_number
            elif section:
                section.append(line)
                if line.strip()=='//':
                    yield first,line_number,''.join(section)
                    section=[];first=None

def query_proof(text,expected_name,expected_length,target_count,domain_rows=None,targets=None,include_domains=False):
    lines=text.splitlines();query=re.fullmatch(r'Query:\s+(\S+)\s+\[M=(\d+)\]',lines[0].strip())
    require(query is not None and query.group(1)==expected_name and int(query.group(2))==expected_length,'Native query identity/length differs')
    require(lines[-1].strip()=='//','Native query missing end delimiter')
    query_stats=re.findall(r'^Query model\(s\):\s+(\d+)\b',text,re.M)
    target_stats=re.findall(r'^Target sequences:\s+(\d+)\b',text,re.M)
    require(query_stats==['1'] and target_stats==[str(target_count)],'Native complete query/target statistics differ')
    raw_domains=[];target=None;scores={};in_scores=False
    for line in lines:
        if line.startswith('Scores for complete sequences'):in_scores=True;continue
        if line.startswith('Domain annotation'):in_scores=False
        if in_scores:
            fields=line.split()
            if len(fields)>=9 and re.fullmatch(r'[0-9.eE+-]+',fields[0]) and re.fullmatch(r'\d+',fields[7]):
                require(fields[8] not in scores,'Duplicate native scored target')
                if targets is not None:require(fields[8] in targets,'Native scored target absent from exact source crosswalk')
                require(numeric(fields[0])>=0,'Native raw sequence Evalue is negative')
                scores[fields[8]]=(fields[0],fields[1],fields[2],int(fields[7]))
        if line.startswith('>>'):
            target=line.split()[1];require(target in scores,'Native domain target absent from score table')
        fields=line.split()
        if len(fields)==16 and fields[0].isdigit() and fields[1] in ('!','?'):
            require(target is not None,'Native domain without target')
            raw_domains.append({'target_name':target,'domain_number':fields[0],'domain_score':fields[2],
                'domain_bias':fields[3],'conditional_evalue':fields[4],'independent_evalue':fields[5],
                'hmm_from':fields[6],'hmm_to':fields[7],'alignment_from':fields[9],'alignment_to':fields[10],
                'envelope_from':fields[12],'envelope_to':fields[13],'accuracy':fields[15]})
    for target_name,score in scores.items():
        ordinals=[int(r['domain_number']) for r in raw_domains if r['target_name']==target_name]
        require(sorted(ordinals)==list(range(1,score[3]+1)),
                'Native scored target domain annotations incomplete/duplicate')
    for raw in raw_domains:
        require(1<=int(raw['hmm_from'])<=int(raw['hmm_to'])<=expected_length,'Native raw HMM coordinates invalid')
        require(0<=numeric(raw['accuracy'])<=1,'Native raw domain accuracy outside[0,1]')
        for field in ['conditional_evalue','independent_evalue']:require(numeric(raw[field])>=0,'Native raw domain Evalue is negative')
        if targets is not None:
            value=targets[raw['target_name']];length=int(value['protein_aa_length']) if isinstance(value,dict) else value
            require(1<=int(raw['alignment_from'])<=int(raw['alignment_to'])<=length,'Native raw alignment coordinates invalid')
            require(1<=int(raw['envelope_from'])<=int(raw['envelope_to'])<=length,'Native raw envelope coordinates invalid')
    if domain_rows is not None:
        observed={(r['target_name'],r['domain_number']):r for r in domain_rows}
        require(len(observed)==len(domain_rows)==len(raw_domains),'Native query domain rows incomplete/duplicate')
        for raw in raw_domains:
            key=raw['target_name'],raw['domain_number'];require(key in observed,'Native query domain missing from domtbl')
            row=observed[key]
            for field in raw:
                if field in ('target_name','domain_number'):continue
                require(numeric(raw[field])==numeric(row[field]),'Native query/domtbl domain disagreement: '+field)
            full_evalue,full_score,full_bias,total_domains=scores[raw['target_name']]
            require(numeric(row['full_evalue'])==numeric(full_evalue) and numeric(row['full_score'])==numeric(full_score)
                    and numeric(row['full_bias'])==numeric(full_bias) and int(row['total_domains'])==total_domains,
                    'Native query/domtbl full-score disagreement')
    result={'query_name':expected_name,'profile_length':expected_length,'target_sequences_searched':target_count,
            'raw_reported_domains':len(raw_domains),'query_section_sha256':hashlib.sha256(text.encode()).hexdigest()}
    if include_domains:
        result['native_domains']=[dict(row,profile_name=expected_name,profile_length=expected_length,
            full_evalue=scores[row['target_name']][0],full_score=scores[row['target_name']][1],
            full_bias=scores[row['target_name']][2],total_domains=scores[row['target_name']][3]) for row in raw_domains]
    return result

def complete_hmm_output(path,profile,target_count,targets=None,include_domains=False):
    sections=list(query_sections(path))
    require(len(sections)==1,'Native single-profile output query count differs')
    proof=query_proof(sections[0][2],profile['query_name'],profile['length'],target_count,targets=targets,include_domains=include_domains)
    require(Path(path).read_text().rstrip().endswith('[ok]'),'Native HMM output incomplete')
    return proof

def native_tsv(path,empty_message):
    text=Path(path).read_text();lines=[line for line in text.splitlines() if line.strip() and not line.startswith('#')]
    require(not re.search(r'has been SKIPPED|cannot be solved|before timeout',text,re.I),'Native replicon skipped/timeout')
    if not lines:
        require(empty_message in text,'Native empty output lacks explicit no-candidate message')
        return []
    reader=csv.DictReader(io.StringIO('\n'.join(lines)),delimiter='\t');rows=list(reader)
    require(reader.fieldnames and len(set(reader.fieldnames))==len(reader.fieldnames),'Native TSV header invalid')
    require(all(None not in row and all(v is not None for v in row.values()) for row in rows),'Native TSV field count differs')
    require(rows or empty_message in text,'Native header-only output lacks explicit no-candidate message')
    return rows

def extracts(path,mapping,expected_gene):
    lines=Path(path).read_text().splitlines();require(len(lines)>=5 and lines[0].startswith('# gene:'),'Native extract header missing')
    require(lines[0].split()[2]==expected_gene,'Native extract profile identity differs')
    result=[]
    for line_number,line in enumerate(lines,1):
        if not line or line.startswith('#'):continue
        fields=line.split('\t');require(len(fields)==11,'Native CoreHit extract must have actual11 columns')
        row=dict(zip(EXTRACT_FIELDS,fields));key=row['hit_id'];require(key in mapping,'Native extract target absent from exact locus crosswalk')
        source=mapping[key]
        require(row['gene_name']==expected_gene and row['replicon']==source['df_bundle_replicon_name']
                and int(row['hit_pos'])==int(source['df_bundle_sequence_rank'])
                and int(row['hit_sequence_length'])==int(source['protein_aa_length']),'Native extract source rank/replicon/length differs')
        require(1<=int(row['hit_begin_match'])<=int(row['hit_end_match'])<=int(row['hit_sequence_length']), 'Native extract coordinates invalid')
        for field in ['i_eval','hit_score','hit_profile_cov','hit_seq_cov']:numeric(row[field])
        require(numeric(row['i_eval'])>=0,'Native extract Evalue is negative')
        require(all(0<=numeric(row[f])<=1 for f in ['hit_profile_cov','hit_seq_cov']),'Native extract coverage outside[0,1]')
        row.update(assembly_accession=source['assembly_accession'],replicon_accession=source['replicon'],locus_key=source['locus_key'],
                   source_line=line_number,protein_accession=source['protein_accession'])
        result.append(row)
    return result

def audit_native_family(raw,scope,mapping):
    import configparser
    config=configparser.ConfigParser();config.read(raw/'macsyfinder.conf')
    frozen_config=configparser.ConfigParser();frozen_config.read_string(scope['config_text'])
    require(set(config.sections())==set(frozen_config.sections()),'Native configuration sections differ')
    for section in frozen_config.sections():
        observed=dict(config.items(section));expected=dict(frozen_config.items(section))
        # Output/index directory locations affect storage only; exact input,
        # topology, model/profile scope, all score weights and filters must match.
        if section=='directories':
            for field in ['out_dir','index_dir']:observed.pop(field,None);expected.pop(field,None)
        if section=='general':observed.pop('previous_run',None);expected.pop('previous_run',None)
        require(observed==expected,'Native complete configuration differs: '+section)
    settings=scope['native_settings'];require(config.get('base','db_type')==settings['db_type'],'Native db type differs')
    require(config.getint('general','worker')==2 and config.getboolean('hmmer','cut_ga')==settings['cut_ga'],'Native threads/GA differ')
    require(config.getfloat('hmmer','coverage_profile')==settings['coverage_profile']
            and config.getfloat('hmmer','i_evalue_sel')==settings['i_evalue_sel']
            and config.getfloat('hmmer','e_value_search')==settings['e_value_search'],'Native scoring/filter configuration differs')
    require(config.get('models','models')==scope['model_family']+' all','Native family scope differs')
    require(config.get('base','replicon_topology')==settings['replicon_topology']
            and config.get('base','topology_file',fallback=None)==settings['topology_file'],'Native topology configuration differs')
    require(Path(config.get('base','sequence_db')).resolve()==Path(settings['sequence_db']).resolve(),'Native input path differs')
    log=(raw/'macsyfinder.log').read_text();require(re.search(r'^INFO\s*:\s*END\s*$',log,re.M),'Native family log lacks END')
    require(not re.search(r'SKIP IT|cannot be solved|has been SKIPPED|Run Aborted|CRITICAL',log,re.I),'Native family has failure/skipped condition')
    hits=[];proofs=[]
    expected={p['gene_name'] for p in scope['profiles']}
    hmmer=raw/settings['hmmer_dir']
    actual={p.name[:-len(settings['res_search_suffix'])] for p in hmmer.glob('*'+settings['res_search_suffix'])}
    require(actual==expected,'Native family searched profile set differs')
    for profile in scope['profiles']:
        path=hmmer/(profile['gene_name']+settings['res_search_suffix'])
        proofs.append(complete_hmm_output(path,profile,len(mapping),targets=mapping))
        hits.extend(extracts(hmmer/(profile['gene_name']+settings['res_extract_suffix']),mapping,profile['gene_name']))
    calls=native_tsv(raw/'best_solution.tsv','# No Systems found')
    candidates=native_tsv(raw/'all_systems.tsv','# No Systems found')
    rejected=native_tsv(raw/'rejected_candidates.tsv','# No Rejected candidates')
    model_names=set(scope['model_definitions'])
    for row in calls+candidates+rejected:
        require('hit_id' in row and row['hit_id'] in mapping and row.get('model_fqn') in model_names,
                'Native system/candidate exact source/model join differs')
        source=mapping[row['hit_id']]
        require(row['replicon']==source['df_bundle_replicon_name'] and int(row['hit_pos'])==int(source['df_bundle_sequence_rank']),
                'Native candidate replicon/order differs')
        row.update(assembly_accession=source['assembly_accession'],source_replicon=source['replicon'],
                   locus_key=source['locus_key'],protein_accession=source['protein_accession'])
    return {'execution_integrity':'ALL_NATIVE_PROFILE_QUERIES_AND_REPLICON_CONFIG_CHECKED','scientific_curation':'NOT_RUN',
            'profiles':len(proofs),'target_loci':len(mapping),'skipped_replicons':[],
            'filtered_profile_hits':hits,'native_calls':calls,'native_all_candidates':candidates,'native_rejected_candidates':rejected}
