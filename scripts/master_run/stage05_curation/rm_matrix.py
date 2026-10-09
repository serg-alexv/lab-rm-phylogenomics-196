#!/usr/bin/env python3
"""Serialize reviewed atomic Stage5 cells; no detector or biological computation.

Missing genomes initialize NOT_RUN. Positive counts are accepted lower bounds;
1 means at least one accepted intact architecture, regardless of other unknowns.
An output is a curation candidate, never independent scientific acceptance.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from pathlib import Path

TYPES = ('I', 'II', 'III', 'IV')
STATES = {'NOT_RUN', 'FAILED', 'UNCERTAIN', 'PARTIAL_CANDIDATE', 'CURATED_PARTIAL',
          'COMPLETE_PREDICTED', 'NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH'}
SEARCH = 'VALIDATED_FULL_NATIVE_SEARCH'
STATE_FIELDS = ['accession','rm_type','state','complete_count','partial_count','candidate_count',
                'search_complete','conflict','positive_invalidated','count_lower_bound','review_ids']

def require(ok, message):
    if not ok: raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()

def pairs(items):
    result = {}
    for key,value in items:
        require(key not in result, 'Duplicate JSON field: '+key); result[key] = value
    return result

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=pairs)

def approved(path):
    panel = Path(path).read_text(encoding='ascii').split()
    require(len(panel)==len(set(panel))==196,'Exact196 unique approved accessions required')
    require(all(re.fullmatch(r'GCF_[0-9]+\.[0-9]+',a) for a in panel),'Versioned GCF accession required')
    return panel

def number(value):
    require(type(value) is int and value>=0,'Nonnegative integer count required'); return value

def normalize(cell, accession):
    require(cell['assembly_accession']==accession and cell['rm_type'] in TYPES,'Wrong cell identity')
    state=cell['state'];require(state in STATES,'Unknown/null state')
    counts=cell.get('candidate_counts',{})
    require(set(counts)<={'COMPLETE_PREDICTED','CURATED_PARTIAL','PARTIAL_CANDIDATE','UNCERTAIN'},'Unknown candidate state')
    for value in counts.values():number(value)
    complete=number(cell.get('complete_predicted_count',0));partial=number(cell.get('curated_partial_count',0))
    require(complete==counts.get('COMPLETE_PREDICTED',0) and partial==counts.get('CURATED_PARTIAL',0),'Counts disagree')
    candidate=sum(counts.values());search=cell.get('required_detector_completion',{})
    require(set(search)=={'PADLOC','DefenseFinder'} and all(v in {'NOT_RUN','FAILED',SEARCH} for v in search.values()),'Two explicit detector search states required')
    search_complete=all(v==SEARCH for v in search.values())
    coverage=cell.get('coverage_unresolved',True);invalid=cell.get('positive_invalidated',False)
    require(type(coverage) is bool and type(invalid) is bool,'Strict coverage/positive invalidation booleans required')
    unresolved=counts.get('UNCERTAIN',0)+counts.get('PARTIAL_CANDIDATE',0)
    conflict=bool(coverage or unresolved or not search_complete or invalid)
    if state=='COMPLETE_PREDICTED':require(complete>0,'Positive state lacks accepted complete architecture')
    if state=='CURATED_PARTIAL':require(partial>0 and complete==0,'Partial state/count differs')
    if state=='NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH':
        require(search_complete and not coverage and candidate==0 and not invalid,'Non-detection has incomplete/unresolved/positive evidence')
        require(cell.get('review_execution')=='COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW','Non-detection lacks executed source/fullscope review')
    value='1' if complete and not invalid else ('0' if state=='NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH' else 'NA')
    ids=cell.get('candidate_ids',[])
    require(isinstance(ids,list) and len(ids)==len(set(ids)) and all(isinstance(i,str) and i for i in ids),'Candidate IDs invalid')
    # review_ids contains candidate IDs plus explicit review-record digests in a
    # separate JSON artifact. It never encodes an executed review from a blank.
    row={'accession':accession,'rm_type':cell['rm_type'],'state':state,'complete_count':complete,
         'partial_count':partial,'candidate_count':candidate,'search_complete':str(search_complete),
         'conflict':str(conflict),'positive_invalidated':str(invalid),
         'count_lower_bound':str(conflict),'review_ids':json.dumps(ids,separators=(',',':'))}
    return row,value

def initial(accession, rm_type):
    return {'assembly_accession':accession,'rm_type':rm_type,'state':'NOT_RUN',
            'candidate_counts':{},'complete_predicted_count':0,'curated_partial_count':0,
            'required_detector_completion':{'PADLOC':'NOT_RUN','DefenseFinder':'NOT_RUN'},
            'coverage_unresolved':True,'candidate_ids':[]}

def documented_exception(document):
    """Candidate serialization only: independent checker reopens every proof."""
    require(document.get('schema')=='RM_ATOMIC_CURATION_EXCEPTION_V1' and document.get('execution_state') in
            {'FAILED_FATAL','FAILED_RETRYABLE','DEFERRED_RESOURCE','NOT_RUN'},'Explicit execution exception required')
    require(isinstance(document.get('reason'),str) and 0<len(document['reason'].strip())<=4000,'Bounded exception reason required')
    accession=document['accession'];proof=document.get('retained_positive_result');prior={}
    if proof is not None:
        require(sha(proof['path'])==proof['sha256'],'Retained positive result changed')
        actual=load(proof['path']);require(actual['assembly_accession']==accession and actual['scientific_stage05_status']==
                'INDEPENDENT_CURATED_VALIDATION_REQUIRED','Retained positive source identity/status differs')
        rows=actual['cells'];require(len(rows)==4 and {r['rm_type'] for r in rows}==set(TYPES),'Retained positive cell product differs')
        prior={r['rm_type']:r for r in rows}
    failed=document['execution_state']!='NOT_RUN';cells=[]
    for kind in TYPES:
        old=prior.get(kind,{});cell=initial(accession,kind)
        cell.update(state='FAILED' if failed else 'NOT_RUN',candidate_counts=old.get('candidate_counts',{}),
                    complete_predicted_count=old.get('complete_predicted_count',0),curated_partial_count=old.get('curated_partial_count',0),
                    candidate_ids=old.get('candidate_ids',[]),positive_invalidated=old.get('positive_invalidated',False),
                    required_detector_completion={'PADLOC':'FAILED' if failed else 'NOT_RUN','DefenseFinder':'FAILED' if failed else 'NOT_RUN'},
                    review_execution='DOCUMENTED_EXECUTION_EXCEPTION_INDEPENDENT_AUDIT_REQUIRED')
        normalize(cell,accession);cells.append(cell)
    return cells

def build(panel, documents, exceptions=()):
    cells={(a,t):initial(a,t) for a in panel for t in TYPES};seen=set()
    for doc in documents:
        a=doc['assembly_accession'];require(a in panel and a not in seen,'Duplicate/out-of-panel assembly result');seen.add(a)
        require(doc['scientific_stage05_status']=='INDEPENDENT_CURATED_VALIDATION_REQUIRED','Result incorrectly claims acceptance')
        require(doc['review_execution']=='COMPLETE_ALL_REQUIRED_EVIDENCE_REVIEW','Assembly review incomplete')
        rows=doc['cells'];require(len(rows)==4 and {r['rm_type'] for r in rows}==set(TYPES),'Exactly four cells per reviewed assembly required')
        for r in rows:normalize(r,a);cells[(a,r['rm_type'])]=r
    for document in exceptions:
        a=document['accession'];require(a in panel and a not in seen,'Duplicate/out-of-panel reviewed result or exception');seen.add(a)
        for r in documented_exception(document):cells[(a,r['rm_type'])]=r
    long=[];wide=[]
    for a in panel:
        row={'accession':a}
        for t in TYPES:
            state,value=normalize(cells[(a,t)],a);long.append(state);row['Type_'+t]=value
        wide.append(row)
    require(len(long)==784 and len(wide)==196,'Cartesian product count differs')
    return wide,long

def table(path,rows,fields):
    with Path(path).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fields,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--approved',type=Path,required=True)
    ap.add_argument('--result',type=Path,action='append',default=[]);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--exception',type=Path,action='append',default=[])
    ap.add_argument('--contract',type=Path,help='Full196 audit contract; actual result/exception files only')
    ap.add_argument('--synthetic',action='store_true');args=ap.parse_args()
    panel=approved(args.approved)
    if args.contract:
        require(not args.result and not args.exception,'Contract and explicit result lists are mutually exclusive')
        contract=load(args.contract);require(contract.get('schema')=='RM_ATOMIC_INDEPENDENT_CURATION_CHECK_V1'
                and [e['accession'] for e in contract['assemblies']]==panel,'Full196 candidate contract required')
        require(sha(contract['approved'])==sha(args.approved),'Contract approved panel differs')
        args.result=[Path(e['result']) for e in contract['assemblies'] if not e.get('exception_record')]
        args.exception=[Path(e['exception_record']) for e in contract['assemblies'] if e.get('exception_record')]
    docs=[load(p) for p in args.result];exceptions=[load(p) for p in args.exception]
    require(all(d.get('dataset_kind','PRODUCTION')==('SYNTHETIC' if args.synthetic else 'PRODUCTION') for d in docs+exceptions),'Synthetic/production evidence mixed')
    wide,long=build(panel,docs,exceptions);require(not args.output.exists(),'Use fresh output namespace');args.output.mkdir(parents=True)
    table(args.output/'rm_type_presence_absence.tsv',wide,['accession']+['Type_'+t for t in TYPES])
    table(args.output/'rm_type_state.tsv',long,STATE_FIELDS)
    record={'status':'MATRIX_CANDIDATE_INDEPENDENT_CURATION_AUDIT_REQUIRED',
            'dataset_kind':'SYNTHETIC' if args.synthetic else 'PRODUCTION','accession_count':196,'cell_count':784,
            'reviewed_assemblies':len(docs),'approved_sha256':sha(args.approved),'producer_sha256':sha(__file__),
            'input_results':{str(p):sha(p) for p in args.result},
            'documented_exception_candidates':{str(p):sha(p) for p in args.exception},
            'matrix_sha256':sha(args.output/'rm_type_presence_absence.tsv'),'state_sha256':sha(args.output/'rm_type_state.tsv'),
            'semantics':'1 at least one accepted complete predicted architecture; 0 successful fullscope two-detector source-reviewed non-detection; else NA. Counts lower bounds when conflict=True. Prediction does not establish activity.'}
    (args.output/'matrix_manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(record['status'])

if __name__=='__main__':main()
