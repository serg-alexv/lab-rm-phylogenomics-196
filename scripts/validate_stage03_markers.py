#!/usr/bin/env python3
"""Independent full196 marker evidence/source/filter audit; no HMM jobs.

The source-input validator is an independent reader library, not a producer.
Marker producer/wrapper helpers are never imported. Native HMM tables, original
NCBI proteins, GBFF locus annotations, native extraction outputs and final
accepted FASTAs are reread. Function-scope review is a separate explicit gate.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
from decimal import Decimal,ROUND_HALF_EVEN
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path,PurePosixPath
import re
import statistics
import tempfile
import time
from Bio import SeqIO
from Bio.SeqFeature import ExactPosition

LIMIT='Executed HMM evidence, source identities and frozen host marker filters; profile predictions are not demonstrated protein function.'
RM_PATTERN=re.compile(r'restriction|DNA.{0,30}methyl|(?:adenine|cytosine).{0,30}DNA.{0,30}methyl|\bhsd[MSR]\b|\b(?:mod|res)\b.{0,25}(?:subunit|restriction)',re.I)
AMBIGUOUS={'ATP_bind_2','CTP_transf_1','Cytidylate_kin2','DHOase','Ham1p_like','IPPT','IPT','NifU_N','UPF0052','UPF0054','YbbR','YGGT','YbaB_DNA_bd'}


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def seqsha(sequence):return hashlib.sha256(sequence.encode('ascii')).hexdigest()


def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(path)


def reader_module(path):
    spec=importlib.util.spec_from_file_location('independent_source_reader',path)
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    return reader


def profile_metadata(path):
    result=[]
    for block in Path(path).read_text(encoding='ascii').split('//'):
        if not block.strip():continue
        fields={}
        for line in block.splitlines():
            match=re.match(r'^(NAME|ACC|DESC|LENG|GA)\s+(.+)$',line)
            if match:
                name,value=match.groups();require(name not in fields,'Duplicate HMM profile metadata');fields[name]=value
        require(set(fields)=={'NAME','ACC','DESC','LENG','GA'},'Incomplete profile metadata')
        cutoffs=fields['GA'].replace(';','').split();require(len(cutoffs)==2,'Invalid GA cutoff count')
        sequence_ga,domain_ga=map(float,cutoffs)
        require(all(math.isfinite(v) for v in (sequence_ga,domain_ga)) and int(fields['LENG'])>0,'Invalid HMM length/cutoffs')
        description=fields['DESC'];generic=(fields['NAME'] in AMBIGUOUS or bool(re.search('unknown|uncharacter|predicted spout',description,re.I)))
        state=('EXPLICIT_RM_OR_DNA_METHYLASE_DESCRIPTION_REVIEW_REQUIRED' if re.search(r'restriction|dna.*methyl|methyl.*dna',description,re.I)
               else 'GENERIC_OR_UNCHARACTERIZED_FAMILY_REVIEW_REQUIRED' if generic
               else 'PROFILE_DESCRIPTION_HAS_HOST_FUNCTION_NO_EXPLICIT_RM_DESCRIPTION')
        result.append({'profile':fields['NAME'],'profile_accession':fields['ACC'],'profile_description':description,
                       'profile_length':int(fields['LENG']),'ga_sequence':sequence_ga,'ga_domain':domain_ga,
                       'source_ga_text':fields['GA'],'annotation_review_state':state})
    require(len(result)==len({p['profile'] for p in result})==119,'Pinned HMM must contain exact119 unique profiles')
    return result


def finite(value,label,nonnegative=False):
    parsed=float(value)
    require(math.isfinite(parsed) and (not nonnegative or parsed>=0),'Nonfinite/invalid HMM '+label)
    return parsed


def native_rows(path,fixed):
    lines=Path(path).read_text(encoding='utf-8').splitlines()
    require(lines and lines[0].startswith('#') and lines[-1].strip()=='# [ok]','Native HMM evidence lacks completed header/trailer: '+Path(path).name)
    parsed=[]
    for number,line in enumerate(lines,1):
        if not line.strip() or line.startswith('#'):continue
        values=line.split(maxsplit=fixed)
        require(len(values)>=fixed,'Truncated native HMM table row')
        parsed.append((number,values[:fixed]))
    return parsed


def inspect_native(accession,evidence,profile_rows,target_map,source,identity):
    rename,search=load(evidence/'rename_receipt.json'),load(evidence/'hmm_receipt.json')
    require(rename.get('status')=='RENAMING_IDENTITY_VERIFIED' and rename.get('assembly')==accession
            and rename.get('wrapper_sha256')==identity['wrapper_sha256']
            and rename.get('real_binary_sha256')==identity['rename_sha256'],'Invalid rename receipt/provenance')
    require(search.get('status')=='HMM_OUTPUTS_PRESERVED' and search.get('exit_code')==0
            and search.get('assembly')==accession and search.get('identity',{}).get('profile_sha256')==identity['profile_sha256']
            and search['identity'].get('binary_sha256')==identity['hmmsearch_sha256']
            and search['identity'].get('wrapper_sha256')==identity['wrapper_sha256'],'Failed/not-run/different HMM search receipt')
    require(set(search['output_sha256'])=={'hmm.tblout','hmm.domtblout','hmm.stdout.txt','hmm.stderr.txt'},'Native HMM mandatory evidence omitted')
    for name,digest in search['output_sha256'].items():require(sha(evidence/name)==digest,'Native HMM evidence hash differs')
    options=search['identity']['options']
    require(options.count('--cut_ga')==1 and options.count('--cpu')==1
            and options[options.index('--cpu')+1]=='2' and options.count('--tblout')==1
            and options[options.index('--tblout')+1]=='<GToTree-temporary-tblout>', 'Actual HMM cutoff/CPU options differ')
    stdout=(evidence/'hmm.stdout.txt').read_text(encoding='utf-8')
    queries=re.findall(r'^Query:\s+(\S+)\s+\[M=(\d+)\]',stdout,re.M)
    require(queries==[(p['profile'],str(p['profile_length'])) for p in profile_rows], 'Native HMM profile query order/length incomplete')
    profile={p['profile']:p for p in profile_rows};hits=[];hit_index={};reported={};domains=[];domain_index=defaultdict(list)
    for line,x in native_rows(evidence/'hmm.tblout',18):
        target,name=x[0],x[2];pair=(target,name)
        require(target in target_map and name in profile and pair not in hit_index,'Unknown/duplicate HMM target-profile pair')
        require(x[3]==profile[name]['profile_accession'],'HMM query accession differs')
        key=target_map[target];entry=source[key]
        nums=[finite(x[i],'tblout value',i in (4,6,7,9,10)) for i in range(4,11)]
        require(nums[1]+0.051>=profile[name]['ga_sequence'],'HMM full score below recorded GA threshold')
        counts=list(map(int,x[11:18]));require(all(n>=0 for n in counts),'Negative HMM domain counts')
        reported[pair]={'domains':counts[4],'reported':counts[5],'included':counts[6]}
        row={'assembly_accession':accession,'profile':name,'profile_accession':x[3],'target_id':target,
             'locus_key':key,'protein_accession':entry['protein_accession'], 'source_sequence_sha256':seqsha(entry['sequence']),
             'protein_aa_length':len(entry['sequence']),'full_evalue':nums[0],'full_score':nums[1],'full_bias':nums[2],
             'best_domain_evalue':nums[3],'best_domain_score':nums[4],'source_tblout_line':line,
             'source_partial_or_fuzzy':entry['partial_or_fuzzy'],'source_pseudo':entry['pseudo'],
             'source_exceptions':entry['source_exceptions'],'source_primary_headers':entry['source_primary_headers'],
             'gbff_location':entry['gbff_location'],'gbff_parts_zero_based':entry['gbff_parts_zero_based'],
             '_sequence':entry['sequence'],'_product':entry['product'],'_qualifiers':entry['qualifiers']}
        hits.append(row);hit_index[pair]=row
    for line,x in native_rows(evidence/'hmm.domtblout',22):
        pair=(x[0],x[3]);require(pair in hit_index,'HMM domain lacks qualifying tblout hit')
        hit,p=hit_index[pair],profile[x[3]];length=hit['protein_aa_length']
        require(x[4]==p['profile_accession'] and int(x[2])==length and int(x[5])==p['profile_length'],'Native domain accession/length differs')
        full_e=finite(x[6],'domain full E-value',True);full_score=finite(x[7],'domain full score');full_bias=finite(x[8],'domain full bias')
        require((full_e,full_score,full_bias)==(hit['full_evalue'],hit['full_score'],hit['full_bias']),'Tblout/domtblout full values disagree')
        number,total=int(x[9]),int(x[10]);require(1<=number<=total and total==reported[pair]['reported'],'Domain numbering/count differs from tblout')
        ce,ie,score,bias=[finite(x[i],'domain value',i in (11,12,14)) for i in range(11,15)]
        require(score+0.051>=p['ga_domain'],'Reported domain score below stored GA domain threshold')
        hf,ht,af,at,ef,et=map(int,x[15:21]);accuracy=finite(x[21],'domain accuracy')
        require(1<=hf<=ht<=p['profile_length'] and 1<=ef<=af<=at<=et<=length and 0<=accuracy<=1,'Domain coordinates/accuracy invalid')
        require(number not in [d['domain_number'] for d in domain_index[pair]],'Duplicate native domain number')
        domain={'assembly_accession':accession,'profile':x[3],'profile_accession':x[4],'target_id':x[0],
                'locus_key':hit['locus_key'],'protein_accession':hit['protein_accession'],'source_domtblout_line':line,
                'domain_number':number,'domains_on_target':total,'conditional_evalue':ce,'independent_evalue':ie,'domain_score':score,
                'hmm_from':hf,'hmm_to':ht,'ali_from':af,'ali_to':at,'env_from':ef,'env_to':et,
                'hmm_coverage':(ht-hf+1)/p['profile_length'],'source_sequence_coverage':(at-af+1)/length,'domain_accuracy':accuracy}
        domains.append(domain);domain_index[pair].append(domain)
    for pair,count in reported.items():
        require(len(domain_index[pair])==count['reported'] and count['included']<=count['reported']<=count['domains'],
                'Reported/included domain counts disagree with native domtblout')
    return hits,domains


def source_records(accession,zip_path,validated,host_path,reader):
    require(sha(zip_path)==validated['raw_zip_sha256'],'Raw NCBI source changed after Stage2')
    payload,_=reader.raw_sources(zip_path,accession)
    primary=defaultdict(list)
    for protein in reader.parse_faa(payload['protein']):primary[protein['id']].append(protein)
    require(all(len({r['sequence'] for r in repeated})==1 for repeated in primary.values()),'Conflicting repeated raw protein accession')
    features={}
    for record in SeqIO.parse(io.StringIO(payload['gbff'].decode('utf-8')),'genbank'):
        for feature in record.features:
            if feature.type!='CDS' or not feature.qualifiers.get('protein_id'):continue
            locus=feature.qualifiers.get('locus_tag',[])
            require(len(locus)==1,'Source marker CDS locus missing/ambiguous')
            key='|'.join((accession,record.id,locus[0]));require(key not in features,'Duplicate raw source marker locus')
            features[key]=feature
    source={}
    for row in validated['loci']:
        pid=row.get('protein_accession')
        if not pid:continue
        key=row['locus_key'];require(key not in source and key in features and pid in primary,'Validated locus/raw primary join differs')
        feature=features[key];sequence=primary[pid][0]['sequence'];q=feature.qualifiers
        require(q.get('protein_id')==[pid] and q.get('translation')==[sequence]
                and seqsha(sequence)==row['protein_sequence_sha256']==row['source_translation_sha256'], 'Exact raw protein/GBFF/Stage2 source sequence differs')
        parts=list(feature.location.parts)
        raw_metadata={
            'partial_or_fuzzy':any(not isinstance(p.start,ExactPosition) or not isinstance(p.end,ExactPosition) for p in parts),
            'pseudo':'pseudo' in q or 'pseudogene' in q,
            'source_exceptions':{k:q[k] for k in ('exception','transl_except','ribosomal_slippage','pseudo','pseudogene') if k in q},
            'gbff_location':str(feature.location),
            'gbff_parts_zero_based':[[int(p.start),int(p.end),p.strand] for p in parts],
        }
        for field,value in raw_metadata.items():
            require(field in row and row[field]==value, 'Stage2 metadata differs from raw GBFF: '+key+' '+field)
        source[key]={**row,'sequence':sequence,'source_primary_headers':[r['header'] for r in primary[pid]],
                     'product':q.get('product',[]),'qualifiers':{k:v for k,v in q.items() if k!='translation'}}
    require(set(source)==set(features),'Raw GBFF/validated protein loci differ')
    host=reader.parse_faa(host_path.read_bytes());require(len(host)==len(source) and {r['id'] for r in host}==set(source),'Host input source membership differs')
    for row in host:require(row['header']==row['id'] and row['sequence']==source[row['id']]['sequence'],'Host source sequence changed')
    return source,host


def compare_table(reader,path,expected,fields=None):
    actual=reader.tsv_rows(path,fields)
    require(len(actual)==len(expected),'Derived table row count differs: '+path.name)
    for index,(row,source) in enumerate(zip(actual,expected),1):
        for key,value in source.items():
            if key.startswith('_'):continue
            require(key in row and row[key]==reader.csv_value(value), f'Derived table/source differs: {path.name} row={index} field={key}')


def verify_search(accession,args,profiles,identity,reader):
    validated=load(args.stage02_dir/'assemblies'/accession/'validation.json')
    require(validated.get('assembly_accession')==accession and validated.get('error_count')==0,'Failed/not-run Stage2 assembly')
    host_path=args.inputs/'assemblies'/accession/(accession+'.faa')
    receipt=load(host_path.parent/'build_receipt.json')
    require(receipt['raw_zip_sha256']==validated['raw_zip_sha256'],'Source builder raw hash differs')
    reader.checkpoint_files(host_path.parent,receipt)
    source,host=source_records(accession,args.root/'data/raw_ncbi'/accession/(accession+'.ncbi.zip'),validated,host_path,reader)
    per=args.markers/'searches'/accession;complete=load(per/'search_complete.json')
    require(complete.get('exit_code')==0 and complete.get('assembly_accession')==accession
            and complete.get('identity')==identity and complete.get('input_sha256')==sha(host_path), 'Native search checkpoint incomplete/different')
    attempt_name=complete['attempt'];require(re.fullmatch(r'attempt_[0-9]{4}',attempt_name),'Unsafe native attempt path')
    attempt=per/attempt_name
    recorded=set()
    for name,digest in complete['file_sha256'].items():
        pp=PurePosixPath(name);path=per/name
        require(not pp.is_absolute() and '..' not in pp.parts and '\\' not in name and ':' not in name
                and pp.parts[0]==attempt_name and path.is_file() and not path.is_symlink()
                and sha(path)==digest,'Search checkpoint file hash/path differs')
        recorded.add(name)
    require(recorded=={p.relative_to(per).as_posix() for p in attempt.rglob('*') if p.is_file()},'Native attempt checkpoint file coverage differs')
    command=load(attempt/'command_receipt.json')
    require(command.get('exit_code')==0 and command.get('identity')==identity and command.get('input_sha256')==sha(host_path), 'Actual GToTree command receipt differs')
    argv=command['argv']
    require(len(argv)==13 and argv[0]=='bash' and argv[5:8]==['196','2','119']
            and argv[-4:]==['false','false','false','none'], 'Actual GToTree arbitrary best-hit/filter/CPU options changed')
    evidence=args.markers/'evidence'/accession
    rename=load(evidence/'rename_receipt.json');search=load(evidence/'hmm_receipt.json')
    original=reader.parse_faa((evidence/'unaltered_locus_input.faa').read_bytes())
    wanted=[row for row in host if len(row['sequence'])<=99999]
    require([(r['header'],r['sequence']) for r in original]==[(r['header'],r['sequence']) for r in wanted], 'Actual HMM input guard changed eligible source proteins')
    renamed=reader.parse_faa((evidence/'gtotree_search_input.faa').read_bytes())
    mapping=reader.tsv_rows(evidence/'target_locus_map.tsv',['assembly','gtotree_target_id','exact_locus_key','filtered_input_ordinal','aa_length','unaltered_sequence_sha256','input_header'])
    require(len(mapping)==len(original)==len(renamed)==rename['records'],'Actual renamed counts differ')
    require(sha(evidence/'unaltered_locus_input.faa')==rename['input_sha256']
            and sha(evidence/'gtotree_search_input.faa')==rename['renamed_input_sha256']==search['identity']['input_sha256'], 'Actual renamed input hashes differ')
    target_map={}
    for index,(row,old,new) in enumerate(zip(mapping,original,renamed),1):
        target=accession+'_'+str(index)
        require(row['assembly']==accession and row['gtotree_target_id']==new['id']==new['header']==target
                and row['exact_locus_key']==old['id'] and row['filtered_input_ordinal']==str(index)
                and row['aa_length']==str(len(old['sequence'])) and row['input_header']==old['header']
                and new['sequence']==old['sequence']==source[old['id']]['sequence']
                and row['unaltered_sequence_sha256']==seqsha(new['sequence']), 'Actual renamed target/locus/source join differs')
        target_map[target]=old['id']
    hits,domains=inspect_native(accession,evidence,profiles,target_map,source,identity)
    copies=Counter(r['profile'] for r in hits)
    require((attempt/'temporary/uniq_hmm_names.tmp').read_text().splitlines()==[p['profile'] for p in profiles],'Native count profile order differs')
    count_lines=(attempt/'helper_output/SCG_hit_counts.tsv').read_text().splitlines()
    require(len(count_lines)==1 and count_lines[0].split('\t')==[accession]+[str(copies[p['profile']]) for p in profiles], 'GToTree native copy counts differ')
    for p in profiles:
        rows=[r for r in hits if r['profile']==p['profile']]
        path=attempt/'temporary'/(p['profile']+'_hits.faa')
        if len(rows)==1:
            extracted=reader.parse_faa(path.read_bytes())
            require(len(extracted)==1 and extracted[0]['id']==accession and extracted[0]['sequence']==rows[0]['_sequence'], 'Native singleton extraction changed source protein')
        else:require(not path.exists() or path.stat().st_size==0,'Native extraction arbitrarily retained missing/multicopy marker')
    exclusions=[{'assembly_accession':accession,'locus_key':r['id'],'protein_accession':source[r['id']]['protein_accession'],
                 'protein_aa_length':len(r['sequence']),'source_sequence_sha256':seqsha(r['sequence']),
                 'reason':'ACTUAL_GTOTREE_INPUT_GUARD_GT99999_AA'} for r in host if len(r['sequence'])>99999]
    return hits,domains,exclusions


def fixed_filters(panel,names,hits,native=None):
    groups=defaultdict(list)
    for hit in hits:groups[(hit['assembly_accession'],hit['profile'])].append(hit)
    lengths={name:[groups[(a,name)][0]['protein_aa_length'] for a in panel if len(groups[(a,name)])==1] for name in names}
    bounds={}
    for name,values in lengths.items():
        if not values:continue
        middle=Decimal(str(statistics.median(values)))
        lo=int((middle*Decimal('.8')).quantize(Decimal('1'),rounding=ROUND_HALF_EVEN))
        hi=int((middle*Decimal('1.2')).quantize(Decimal('1'),rounding=ROUND_HALF_EVEN))
        if native is not None:
            receipt=native[name]
            require(Decimal(receipt['native_median_text'])==middle
                    and Decimal(receipt['bc_minimum_text'])==middle*Decimal('.8')
                    and Decimal(receipt['bc_maximum_text'])==middle*Decimal('1.2')
                    and receipt['printf_inclusive_minimum']==lo and receipt['printf_inclusive_maximum']==hi,
                    'Native median/bc/printf differs from independent integer-length arithmetic: '+name)
        bounds[name]=(float(middle),lo,hi)
    if native is not None:require(set(native)==set(bounds),'Native length receipt profile set differs')
    accepted_cells={};occupancy=Counter();pre=Counter()
    for a in panel:
        for name in names:
            rows=groups[(a,name)]
            eligible=len(rows)==1 and bounds[name][1]<=rows[0]['protein_aa_length']<=bounds[name][2] if rows else False
            accepted_cells[(a,name)]=eligible
            if eligible:occupancy[name]+=1;pre[a]+=1
    retained=sorted(name for name in names if occupancy[name]>=177)
    cells=[];post=Counter();accepted=[]
    for a in panel:
        for name in names:
            rows=groups[(a,name)];eligible=accepted_cells[(a,name)]
            state='MULTICOPY_MISSING' if len(rows)>1 else 'NO_QUALIFYING_HIT_AFTER_SUCCESSFUL_SEARCH' if not rows else 'LENGTH_EXCLUDED'
            if eligible:
                state='PRIMARY_ACCEPTED' if name in retained else 'MARKER_LOW_OCCUPANCY'
                if name in retained:post[a]+=1;accepted.append(rows[0])
            cells.append({'assembly_accession':a,'profile':name,'qualifying_distinct_loci':len(rows),'state':state,
                          'length_accepted':eligible,'locus_key':rows[0]['locus_key'] if len(rows)==1 else None,
                          'all_locus_keys':[r['locus_key'] for r in rows]})
    required=math.ceil(Decimal('.8')*len(retained));blockers=[]
    if not retained:blockers.append({'scope':'marker_set','reason':'NO_MARKER_PASSES_FIXED196_OCCUPANCY','observed':0,'required':1})
    genomes=[]
    for a in panel:
        if pre[a]<96:blockers.append({'scope':a,'reason':'RECOVERY_BELOW_FIXED119_MINIMUM','observed':pre[a],'required':96})
        if post[a]<required:blockers.append({'scope':a,'reason':'RECOVERY_BELOW_POST_OCCUPANCY_MINIMUM','observed':post[a],'required':required})
        genomes.append({'assembly_accession':a,'length_accepted_markers':pre[a],'recovery_fixed119':pre[a]/119,
                        'primary_accepted_markers':post[a],'primary_marker_denominator':len(retained),
                        'post_occupancy_recovery':post[a]/len(retained) if retained else None,'post_minimum_markers':required})
    markers=[{'profile':name,'median_single_copy_source_aa_length':bounds.get(name,(None,None,None))[0],
              'inclusive_minimum_aa_length':bounds.get(name,(None,None,None))[1],
              'inclusive_maximum_aa_length':bounds.get(name,(None,None,None))[2],
              'accepted_genomes_fixed196':occupancy[name],'occupancy_fixed196':occupancy[name]/196,'primary_retained':name in retained} for name in sorted(names)]
    return cells,markers,genomes,retained,accepted,blockers,lengths


def check_function_review(args,profiles,accepted):
    observations=[];candidates=[]
    for p in profiles:
        rows=[r for r in accepted if r['profile']==p['profile']]
        products=Counter(product for r in rows for product in r['_product'])
        headers=Counter(header.split(' ',1)[1] if ' ' in header else header for r in rows for header in r['source_primary_headers'])
        observations.append({**p,'accepted_loci':len(rows),'source_product_annotations':dict(products),
                             'primary_header_annotation_counts':dict(headers),
                             'review_limit':'Family/annotation evidence supports profile scope; exact-strain function is not demonstrated.'})
        for row in rows:
            evidence_texts=[*row['_product'],*row['source_primary_headers'],*row['_qualifiers'].get('gene',[])]
            matches=[text for text in evidence_texts if RM_PATTERN.search(text)]
            if matches:candidates.append({'assembly_accession':row['assembly_accession'],'profile':row['profile'],
                                          'locus_key':row['locus_key'],'source_annotations':matches})
    write_json(args.output_dir/'host_profile_source_review.json',observations)
    write_json(args.output_dir/'potential_rm_source_candidates.json',candidates)
    if args.host_profile_review is None:
        return {'state':'REVIEW_REQUIRED','profiles_accounted':119,'source_rm_candidates':len(candidates),
                'unresolved_rm_candidates':len(candidates),'review_sha256':None,'limit':LIMIT}
    review=load(args.host_profile_review)
    require(review.get('profile_sha256')==sha(args.profile),'Host family review profile digest differs')
    decisions=review.get('profiles',[])
    require(len(decisions)==119 and len({r['profile'] for r in decisions})==119,'Host function-scope review must account exact119 profiles')
    by_name={r['profile']:r for r in decisions}
    valid_states={'HOST_PROFILE_SCOPE_REVIEWED','HOST_PROFILE_SCOPE_REVIEWED_FUNCTION_UNCHARACTERIZED'}
    for p in profiles:
        decision=by_name.get(p['profile'])
        require(decision is not None and decision.get('profile_accession')==p['profile_accession']
                and decision.get('review_state') in valid_states and bool(decision.get('conclusion'))
                and bool(decision.get('evidence_refs')), 'Host profile decision missing/incomplete: '+p['profile'])
    executed=review.get('accepted_source_hit_review',{})
    current_reviewed=(executed.get('status')=='REVIEWED_ALL196_ACCEPTED_SOURCE_HITS'
                      and executed.get('inventory_summary_sha256')==sha(args.markers/'inventory_summary.json')
                      and executed.get('accepted_sequence_manifest_sha256')==sha(args.markers/'accepted_sequence_manifest.tsv')
                      and executed.get('accepted_marker_sequences')==len(accepted)
                      and executed.get('profiles_accounted')==119 and executed.get('assemblies_accounted')==196
                      and review.get('unresolved_rm_candidates')==0)
    if not current_reviewed:
        return {'state':'REVIEW_REQUIRED','profiles_accounted':119,'source_rm_candidates':len(candidates),
                'unresolved_rm_candidates':None,'review_sha256':sha(args.host_profile_review),
                'reason':'Pre-search family review or stale/incomplete accepted-source review does not complete full196 scientific gate.',
                'limit':LIMIT}
    resolutions=review.get('source_candidate_resolutions',[])
    require(len(resolutions)==len({r['locus_key'] for r in resolutions}),'Duplicate host source review resolution')
    resolved={r['locus_key']:r for r in resolutions}
    unresolved=[]
    for candidate in candidates:
        resolution=resolved.get(candidate['locus_key'])
        if (resolution is None or resolution.get('state')!='REVIEWED_HOST_FUNCTION_SUPPORTED'
                or not resolution.get('basis') or not resolution.get('evidence_refs')):
            unresolved.append(candidate)
    require(set(resolved)<={r['locus_key'] for r in candidates},'Host source resolution lacks current source candidate')
    require(not unresolved,'Potential R-M marker source candidates require actual evidence review')
    return {'state':'REVIEWED_CONSERVED_HOST_PROFILE_SCOPE_WITH_DOCUMENTED_LIMITS','profiles_accounted':119,
            'source_rm_candidates':len(candidates),'unresolved_rm_candidates':0,'review_sha256':sha(args.host_profile_review),
            'function_uncharacterized_profiles':sum(r['review_state']=='HOST_PROFILE_SCOPE_REVIEWED_FUNCTION_UNCHARACTERIZED' for r in decisions),
            'limit':LIMIT}


def production(args):
    started=time.monotonic();reader=reader_module(args.source_validator)
    for name in ('root','markers','inputs','stage02_dir','output_dir','profile','config'):
        setattr(args,name,getattr(args,name).resolve())
    require(args.root in args.output_dir.parents and not any(p in ('data','config','scripts') for p in args.output_dir.relative_to(args.root).parts)
            and args.markers not in args.output_dir.parents and args.output_dir!=args.markers,'Independent report directory required')
    panel_path=args.root/'config/approved_accessions.txt';panel=panel_path.read_text().split()
    require(len(panel)==len(set(panel))==196,'Exact196 marker audit required')
    config=load(args.config);profile_rows=profile_metadata(args.profile);names=[p['profile'] for p in profile_rows]
    require(config.get('approved_accessions_sha256')==sha(panel_path) and config.get('profile_sha256')==sha(args.profile)
            and config.get('frozen_before_marker_search_and_topology') is True
            and config.get('profile_count_independently_measured')==config.get('genome_recovery_fixed_denominator')==119
            and config.get('genome_minimum_accepted_markers')==96 and config.get('marker_occupancy_fixed_denominator')==196
            and config.get('marker_minimum_accepted_genomes')==177 and config.get('genome_recovery_minimum')==0.8
            and config.get('marker_occupancy_minimum')==0.9 and config.get('post_occupancy_genome_recovery_minimum')==0.8,
            'Frozen exact119/exact196 filters differ')
    independent=load(args.locus_validation);construct=load(args.inputs/'construction_summary.json')
    require(independent.get('status')=='PASS_SOURCE_LOCUS_INPUT_TRACEABILITY'
            and independent.get('required_assemblies')==independent.get('assemblies_audited')==independent.get('assemblies_passed')==196
            and independent.get('failed_assemblies')==[] and independent.get('global_errors')==[]
            and independent.get('complete_exact196_accounting') is True
            and independent.get('panel_sha256')==sha(panel_path) and independent.get('builder_identity')==construct['identity']
            and independent.get('validator_source_sha256')==sha(args.source_validator), 'Independent full196 source gate/hash differs')
    identity=load(args.markers/'input_identity.json');inventory=load(args.markers/'inventory_summary.json')
    binding={'approved_accessions_sha256':sha(panel_path),'config_sha256':sha(args.config),'profile_sha256':sha(args.profile),
             'runner_sha256':sha(args.runner_script),'wrapper_sha256':sha(args.wrapper_script),
             'source_construction_summary_sha256':sha(args.inputs/'construction_summary.json'),
             'stage02_validation_summary_sha256':sha(args.stage02_dir/'validation_summary.json'),
             'independent_source_locus_validation_summary_sha256':sha(args.locus_validation)}
    require(all(identity.get(k)==v for k,v in binding.items()) and inventory.get('identity')==identity,'Marker input/code hash bindings differ')
    require(inventory.get('execution')=='COMPLETED_ALL196_SEARCHES'
            and inventory.get('approved_assemblies')==inventory.get('successful_searches')==196
            and inventory.get('profiles_searched')==119 and inventory.get('marker_cells')==196*119,'Complete196*119 actual search accounting required')
    runtime=load(args.markers/'runtime/runtime_receipt.json')
    require(runtime.get('status')=='ACTUAL_INSTALLED_RUNTIME_HELP_AND_BYTES_CAPTURED'
            and runtime['source_sha256']['gtt-amino-acid-serial.sh']==identity['helper_sha256']
            and runtime['programs']['hmmsearch']['sha256']==identity['hmmsearch_sha256']
            and runtime['source_sha256']['gtt-rename-fasta-headers']==identity['rename_sha256'], 'Runtime evidence hashes differ')
    for name,digest in runtime['source_sha256'].items():require(sha(args.markers/'runtime'/('source_'+name+'.txt'))==digest,'Preserved runtime source bytes changed')
    labels=['gtotree_version','gtotree_help','hmmer_help_version','sfetch_help_version','rename_help','filter_help',
            'mafft_version','mafft_help','trimal_version','trimal_help','iqtree3_version','iqtree3_help']
    require(len(runtime['commands'])==len(labels),'Actual installed runtime command accounting differs')
    for label,record in zip(labels,runtime['commands']):
        require(record['binary_sha256'] and record['resolved_binary_sha256'] and record['exit_code'] in (0,1),'Runtime tool receipt invalid')
        for suffix in ('stdout','stderr'):
            require(sha(args.markers/'runtime'/(label+'.'+suffix+'.txt'))==record[suffix+'_sha256'], 'Runtime help/version evidence digest differs')
    require(sha(args.markers/'runtime/installed_packages.json')==runtime['packages_sha256'],'Runtime installed package evidence changed')
    compare_table(reader,args.markers/'profiles.tsv',profile_rows)
    hits=[];domains=[];exclusions=[];failures=[]
    actual={p.name for p in (args.markers/'searches').iterdir() if p.is_dir()}
    require(actual==set(panel),'Unexpected/missing executed search directory')
    for index,accession in enumerate(panel,1):
        try:
            current,current_domains,current_exclusions=verify_search(accession,args,profile_rows,identity,reader)
            hits.extend(current);domains.extend(current_domains);exclusions.extend(current_exclusions)
        except Exception as error:failures.append({'assembly_accession':accession,'error':str(error)})
        print(f'{index}/196 {accession} '+('FAIL' if failures and failures[-1]['assembly_accession']==accession else 'NATIVE_EVIDENCE_SOURCE_JOIN_VERIFIED'),flush=True)
    write_json(args.output_dir/'native_search_failures.json',failures)
    require(not failures,'Native marker/source search audit failed; preserved all assembly failures')
    compare_table(reader,args.markers/'hmm_hits.tsv',hits)
    compare_table(reader,args.markers/'hmm_domains.tsv',domains)
    compare_table(reader,args.markers/'input_guard_exclusions.tsv',exclusions)
    receipts=load(args.markers/'length_method/native_bounds_receipts.json');native={r['profile']:r for r in receipts}
    require(len(native)==len(receipts),'Duplicate native length method receipt')
    cells,markers,genomes,retained,accepted,blockers,lengths=fixed_filters(panel,names,hits,native)
    for name,values in lengths.items():
        if not values:continue
        path=args.markers/'length_method'/(name+'.singleton_lengths.txt')
        receipt=native[name]
        require(list(map(int,path.read_text().splitlines()))==values and sha(path)==receipt['lengths_sha256']
                and receipt['source_singleton_count']==len(values) and receipt['exit_code']==0,'Native source singleton lengths differ')
    compare_table(reader,args.markers/'copy_occupancy_matrix.tsv',cells)
    compare_table(reader,args.markers/'marker_qc.tsv',markers)
    compare_table(reader,args.markers/'genome_recovery.tsv',genomes)
    compare_table(reader,args.markers/'scientific_blockers.tsv',blockers)
    require((args.markers/'primary_marker_order.txt').read_text().splitlines()==retained,'Primary frozen marker order differs')
    accepted.sort(key=lambda r:(r['profile'],panel.index(r['assembly_accession'])))
    compare_table(reader,args.markers/'accepted_sequence_manifest.tsv',accepted)
    require({p.name for p in (args.markers/'marker_sequences').glob('*.faa')}=={name+'.faa' for name in retained},'Accepted marker FASTA membership differs')
    for name in retained:
        expected=[r for r in accepted if r['profile']==name];records=reader.parse_faa((args.markers/'marker_sequences'/(name+'.faa')).read_bytes())
        require([(r['id'],r['header'],r['sequence']) for r in records]==[(r['assembly_accession'],r['assembly_accession'],r['_sequence']) for r in expected], 'Accepted per-marker exact source sequence/order differs')
    for accession in panel:
        expected=[r for r in accepted if r['assembly_accession']==accession]
        path=args.markers/'accepted_by_genome'/(accession+'.faa')
        if expected:
            records=reader.parse_faa(path.read_bytes())
            require([(r['id'],r['header'],r['sequence']) for r in records]==[(r['locus_key'],r['locus_key']+' marker='+r['profile'],r['_sequence']) for r in expected], 'Accepted per-genome exact source sequence/marker differs')
        else:require(not path.exists(),'Genome with no accepted markers has spurious FASTA')
    require(inventory['primary_markers']==len(retained) and inventory['accepted_marker_sequences']==len(accepted)
            and inventory['blocker_count']==len(blockers) and inventory['blockers']==blockers
            and inventory['inventory']==('SCIENTIFIC_BLOCKER' if blockers else 'MARKER_INVENTORY_CONSTRUCTED'), 'Inventory summary scientific totals differ')
    same_locus=defaultdict(list)
    for row in accepted:same_locus[row['locus_key']].append(row['profile'])
    overlaps=[{'locus_key':key,'accepted_profiles':values,'state':'MULTIPLE_PROFILES_SAME_FULL_SOURCE_PROTEIN_DUPLICATE_SIGNAL_REVIEW_REQUIRED',
               'basis':'Both marker blocks would reuse the same complete primary protein; distinct HMM domains alone do not establish independent loci.'}
              for key,values in same_locus.items() if len(values)>1]
    write_json(args.output_dir/'same_locus_multiple_profiles_review.json',overlaps)
    function_review=check_function_review(args,profile_rows,accepted)
    producer_review=load(args.markers/'host_marker_annotation_review.json')
    require(producer_review['profiles_audited']==119,'Producer host annotation review incomplete')
    report={'status':'PASS_MARKER_SOURCE_AND_FIXED_FILTERS','scientific_stage_status':
            'SCIENTIFIC_BLOCKER' if blockers else 'HOST_ORTHOLOGY_DUPLICATE_SIGNAL_REVIEW_REQUIRED' if overlaps
            else 'PASS_HOST_MARKER_INVENTORY' if function_review['state'].startswith('REVIEWED_') else 'HOST_FUNCTION_SCOPE_REVIEW_REQUIRED',
            'completed_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-started,
            'approved_assemblies':196,'independently_verified_searches':196,'profiles_searched':119,'marker_cells':len(cells),
            'native_tblout_hits':len(hits),'native_domtblout_rows':len(domains),'primary_markers':len(retained),
            'accepted_marker_sequences':len(accepted),'input_guard_exclusions':len(exclusions),'scientific_blockers':blockers,
            'host_function_review':function_review,'fixed_denominators':{'genomes':196,'candidate_markers':119,'post_occupancy_markers':len(retained)},
            'same_locus_multiple_profile_candidates':len(overlaps),
            'producer_identity':identity,'source_reader_sha256':sha(args.source_validator),'validator_source_sha256':sha(__file__),
            'inventory_summary_sha256':sha(args.markers/'inventory_summary.json'),
            'accepted_sequence_manifest_sha256':sha(args.markers/'accepted_sequence_manifest.tsv'),
            'primary_marker_order_sha256':sha(args.markers/'primary_marker_order.txt'),
            'profile_sha256':sha(args.profile),'config_sha256':sha(args.config),'evidence_limit':LIMIT}
    write_json(args.output_dir/'validation_summary.json',report)
    print(json.dumps(report,indent=2),flush=True)
    require(report['scientific_stage_status']=='PASS_HOST_MARKER_INVENTORY','Integrity checked; frozen filters/function-scope review has unresolved scientific gate')


def self_test(args):
    panel=['S'+str(n) for n in range(196)];names=['M'+str(n) for n in range(119)]
    rows=[{'assembly_accession':a,'profile':name,'locus_key':a+'|rep|'+name,'protein_aa_length':100} for a in panel for name in names]
    cases=[]
    result=fixed_filters(panel,names,rows);require(len(result[0])==23324 and len(result[3])==119 and not result[5],'Complete synthetic fixed196/fixed119 matrix rejected');cases.append('complete196x119')
    values=fixed_filters(panel,names,[*rows,{**rows[0],'locus_key':'S0|rep|M0_copy2'}]);require(values[0][0]['state']=='MULTICOPY_MISSING','Multicopy selected arbitrarily');cases.append('multicopy_missing')
    short=[r for r in rows if not(r['assembly_accession']=='S0' and int(r['profile'][1:])>=95)]
    require(any(b['reason']=='RECOVERY_BELOW_FIXED119_MINIMUM' and b['observed']==95 for b in fixed_filters(panel,names,short)[5]),'95/119 genome accepted');cases.append('95_of119_blocked')
    low=[r for r in rows if not(r['profile']=='M0' and int(r['assembly_accession'][1:])>=176)]
    require('M0' not in fixed_filters(panel,names,low)[3],'176/196 accepted');cases.append('176_of196_marker_excluded')
    edge=[{**r,'protein_aa_length':80} if r is rows[0] else r for r in rows]
    require(fixed_filters(panel,names,edge)[0][0]['state']=='PRIMARY_ACCEPTED','Inclusive80% boundary rejected');cases.append('inclusive_length_boundary')
    outlier=[{**r,'protein_aa_length':79} if r is rows[0] else r for r in rows]
    require(fixed_filters(panel,names,outlier)[0][0]['state']=='LENGTH_EXCLUDED','Length outside bound accepted');cases.append('outside_length_boundary')
    for median,low,high in [('101.5',81,122),('102.5',82,123),('99998.5',79999,119998),('3.5',3,4)]:
        value=Decimal(median)
        require(int((value*Decimal('.8')).quantize(Decimal('1'),rounding=ROUND_HALF_EVEN))==low
                and int((value*Decimal('1.2')).quantize(Decimal('1'),rounding=ROUND_HALF_EVEN))==high,
                'Independent numeric bounds disagree with observed installed synthetic native bounds')
    cases.append('native_half_median_probes_match_independent_math')
    for value in ('nan','inf','-inf'):
        try:finite(value,'synthetic')
        except ValueError:cases.append('nonfinite_'+value+'_rejected')
        else:raise AssertionError('Nonfinite HMM score accepted')
    # Handwritten native HMM fixtures exercise readers independently of producer.
    args.output_dir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='native_hmm_synthetic_',dir=args.output_dir) as folder:
        evidence=Path(folder);accession='GCF_000000001.1';target=accession+'_1';name='SYNTHETIC_MARKER'
        key=accession+'|SYNTH.1|LOCUS';identity={'wrapper_sha256':'1'*64,'rename_sha256':'2'*64,'profile_sha256':'3'*64,'hmmsearch_sha256':'4'*64}
        p={'profile':name,'profile_accession':'PF00000.1','profile_length':100,'ga_sequence':50.,'ga_domain':50.}
        source={key:{'protein_accession':'WP_SYNTHETIC.1','sequence':'M'*100,'partial_or_fuzzy':False,'pseudo':False,
                     'source_exceptions':{},'source_primary_headers':['WP_SYNTHETIC.1 host enzyme'],
                     'gbff_location':'[0:303](+)','gbff_parts_zero_based':[[0,303,1]],'product':['host enzyme'],'qualifiers':{'product':['host enzyme']}}}
        tbl=[target,'-',name,p['profile_accession'],'1e-30','100.0','0.0','1e-30','100.0','0.0','1.0','1','0','0','1','1','1','1']
        dom=[target,'-','100',name,p['profile_accession'],'100','1e-30','100.0','0.0','1','1','1e-30','1e-30','100.0','0.0','1','100','1','100','1','100','0.99']
        rename={'status':'RENAMING_IDENTITY_VERIFIED','assembly':accession,'wrapper_sha256':identity['wrapper_sha256'],'real_binary_sha256':identity['rename_sha256']}
        write_json(evidence/'rename_receipt.json',rename)
        def fixture(t=tbl,d=dom,extra_tbl='',extra_dom='',tail='# [ok]\n',query=True):
            (evidence/'hmm.tblout').write_text('# synthetic native table\n'+' '.join(t)+' synthetic source\n'+extra_tbl+tail,encoding='utf-8')
            (evidence/'hmm.domtblout').write_text('# synthetic native domain table\n'+(' '.join(d)+' synthetic source\n' if d else '')+extra_dom+tail,encoding='utf-8')
            (evidence/'hmm.stdout.txt').write_text('Query: '+name+' [M=100]\n[ok]\n' if query else '[ok]\n',encoding='utf-8')
            (evidence/'hmm.stderr.txt').write_text('',encoding='utf-8')
            write_json(evidence/'hmm_receipt.json',{'status':'HMM_OUTPUTS_PRESERVED','exit_code':0,'assembly':accession,
              'identity':{'profile_sha256':identity['profile_sha256'],'binary_sha256':identity['hmmsearch_sha256'],
                          'wrapper_sha256':identity['wrapper_sha256'],'options':['--cut_ga','--cpu','2','--tblout','<GToTree-temporary-tblout>']},
              'output_sha256':{n:sha(evidence/n) for n in ('hmm.tblout','hmm.domtblout','hmm.stdout.txt','hmm.stderr.txt')}})
        fixture();found,found_domains=inspect_native(accession,evidence,[p],{target:key},source,identity)
        require(len(found)==len(found_domains)==1,'Valid handwritten native HMM fixture rejected');cases.append('native_HMM_handwritten_positive')
        def altered(values,index,new):
            result=list(values);result[index]=new;return result
        malformed=[('missing_reported_domain',{'d':[]}),
                   ('domain_outside_source',{'d':altered(dom,20,'101')}),
                   ('domain_GA_below_threshold',{'d':altered(dom,13,'49.0')}),
                   ('domain_wrong_profile_accession',{'d':altered(dom,4,'PF99999.1')}),
                   ('domain_full_score_disagrees',{'d':altered(dom,7,'101.0')}),
                   ('domain_wrong_total',{'d':altered(dom,10,'2')}),
                   ('duplicate_domain_number',{'extra_dom':' '.join(dom)+' duplicate\n'}),
                   ('tbl_unknown_target',{'t':altered(tbl,0,'UNMAPPED_TARGET')}),
                   ('tbl_nonfinite_score',{'t':altered(tbl,5,'nan')}),
                   ('tbl_reported_count_disagrees',{'t':altered(tbl,16,'0')}),
                   ('duplicate_tblout_pair',{'extra_tbl':' '.join(tbl)+' duplicate\n'}),
                   ('missing_native_trailer',{'tail':''}),('missing_profile_query',{'query':False})]
        for case,mutation in malformed:
            fixture(**mutation)
            try:inspect_native(accession,evidence,[p],{target:key},source,identity)
            except ValueError:cases.append(case+'_rejected')
            else:raise AssertionError('Malformed native HMM fixture accepted: '+case)
        if args.profile.is_file():
            profiles=profile_metadata(args.profile)
            scope={'profile_sha256':sha(args.profile),'profiles':[
                {'profile':p['profile'],'profile_accession':p['profile_accession'],
                 'review_state':'HOST_PROFILE_SCOPE_REVIEWED_FUNCTION_UNCHARACTERIZED','conclusion':'Synthetic function gate test only',
                 'evidence_refs':['synthetic unit test fixture']} for p in profiles],
                'unresolved_rm_candidates':None,'accepted_source_hit_review':{'status':'PENDING_ALL196_MARKER_INVENTORY'}}
            review_path=evidence/'synthetic_scope_review.json';write_json(review_path,scope)
            (evidence/'inventory_summary.json').write_text('{"synthetic_fixture":true}\n',encoding='utf-8')
            (evidence/'accepted_sequence_manifest.tsv').write_text('synthetic_fixture\n',encoding='utf-8')
            gate_args=argparse.Namespace(output_dir=args.output_dir/'function_gate_tests',host_profile_review=review_path,profile=args.profile,markers=evidence)
            require(check_function_review(gate_args,profiles,[])['state']=='REVIEW_REQUIRED','Pre-search function review counted as scientific completion');cases.append('presearch_family_review_cannot_PASS')
            scope['unresolved_rm_candidates']=0
            scope['accepted_source_hit_review']={'status':'REVIEWED_ALL196_ACCEPTED_SOURCE_HITS',
                'inventory_summary_sha256':sha(evidence/'inventory_summary.json'),
                'accepted_sequence_manifest_sha256':sha(evidence/'accepted_sequence_manifest.tsv'),
                'accepted_marker_sequences':0,'profiles_accounted':119,'assemblies_accounted':196}
            write_json(review_path,scope)
            require(check_function_review(gate_args,profiles,[])['state'].startswith('REVIEWED_'),'Valid synthetic executed review binding rejected');cases.append('executed_review_hash_gate_positive_synthetic_only')
            scope['accepted_source_hit_review']['accepted_sequence_manifest_sha256']='0'*64;write_json(review_path,scope)
            require(check_function_review(gate_args,profiles,[])['state']=='REVIEW_REQUIRED','Stale accepted source review counted as scientific completion');cases.append('stale_accepted_source_review_cannot_PASS')
    report={'status':'PASS_SYNTHETIC_INDEPENDENT_MARKER_CHECKS','cases':cases,'tests':len(cases),'biological_execution':'NOT_RUN','validator_source_sha256':sha(__file__)}
    write_json(args.output_dir/'synthetic_tests.json',report);print(json.dumps(report,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--markers',type=Path,default=Path('.work/stage03_markers_v1'))
    p.add_argument('--inputs',type=Path,default=Path('.work/source_locus_inputs_v1'));p.add_argument('--stage02-dir',type=Path,default=Path('.work/stage02_validated'))
    p.add_argument('--locus-validation',type=Path,default=Path('.work/stage03_source_validation/validation_summary.json'))
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--profile',type=Path,default=Path('.tools/Firmicutes.hmm'))
    p.add_argument('--config',type=Path,default=Path('config/host_primary_stage03_v1.json'))
    p.add_argument('--source-validator',type=Path,default=Path('scripts/validate_locus_inputs.py'))
    p.add_argument('--runner-script',type=Path,default=Path('scripts/stage03_markers.py'));p.add_argument('--wrapper-script',type=Path,default=Path('scripts/gtotree_evidence.py'))
    p.add_argument('--host-profile-review',type=Path);p.add_argument('--self-test-only',action='store_true');a=p.parse_args()
    if a.self_test_only:self_test(a)
    else:
        try:production(a)
        except Exception as error:
            write_json(a.output_dir/'execution_failure.json',{'status':'FAILED','error':str(error),'outputs_preserved':True,'evidence_limit':LIMIT})
            raise


if __name__=='__main__':main()
