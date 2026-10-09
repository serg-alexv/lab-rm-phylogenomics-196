#!/usr/bin/env python3
"""Independent exact196/784 tree-state-matrix accounting; no producer imports.

This validates serialization and accession identity, not domain interpretation,
tree inference quality, or Stage5 scientific acceptance.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re
from pathlib import Path

TYPES=('I','II','III','IV')
STATES={'NOT_RUN','FAILED','UNCERTAIN','PARTIAL_CANDIDATE','CURATED_PARTIAL','COMPLETE_PREDICTED','NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH'}

def must(ok,text):
    if not ok:raise ValueError(text)

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read_table(path,columns):
    with Path(path).open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream,delimiter='\t');rows=list(reader)
    must(reader.fieldnames==columns,'Unexpected/duplicate TSV header: '+str(path))
    must(all(None not in r and all(v is not None for v in r.values()) for r in rows),'Malformed TSV width')
    return rows

def integer(text):
    must(re.fullmatch(r'0|[1-9][0-9]*',text),'Noncanonical nonnegative count');return int(text)

def boolean(text):
    must(text in ('True','False'),'Literal True/False required');return text=='True'

def tips(text):
    # Grammar-aware Newick parser: internal labels/supports never become tips.
    i=0;result=[]
    def skip():
        nonlocal i
        while i<len(text):
            if text[i].isspace():i+=1
            elif text[i]=='[':
                i+=1;depth=1
                while i<len(text) and depth:
                    if text[i]=='[':depth+=1
                    elif text[i]==']':depth-=1
                    i+=1
                must(depth==0,'Unterminated Newick comment')
            else:break
    def label(required=False):
        nonlocal i
        skip();out=''
        if i<len(text) and text[i]=="'":
            i+=1
            while i<len(text):
                ch=text[i];i+=1
                if ch=="'":
                    if i<len(text) and text[i]=="'":out+="'";i+=1
                    else:return out
                else:out+=ch
            raise ValueError('Unterminated quoted Newick label')
        while i<len(text) and text[i] not in '():,;[]' and not text[i].isspace():out+=text[i];i+=1
        must(out or not required,'Missing Newick tip label');return out
    def branch():
        nonlocal i
        skip()
        if i<len(text) and text[i]==':':
            i+=1;value=label(True)
            try:n=float(value)
            except ValueError:raise ValueError('Invalid Newick branch length')
            must(math.isfinite(n) and n>=0,'Nonfinite/negative Newick length')
    def node():
        nonlocal i
        skip();must(i<len(text),'Unexpected end of tree')
        if text[i]=='(':
            i+=1;node();children=1
            while True:
                skip();must(i<len(text),'Unclosed Newick internal node')
                if text[i]==',':i+=1;node();children+=1
                elif text[i]==')':i+=1;break
                else:raise ValueError('Invalid Newick child separator')
            must(children>=2,'Unary Newick node');label()
        else:result.append(label(True))
        branch()
    node();skip();must(i<len(text) and text[i]==';','Newick terminator missing');i+=1;skip()
    must(i==len(text),'Extra Newick tree/trailing text');return result

def check(approved,tree,matrix,state,synthetic=False):
    panel=Path(approved).read_text(encoding='ascii').split()
    must(len(panel)==len(set(panel))==196 and all(re.fullmatch(r'GCF_[0-9]+\.[0-9]+',a) for a in panel),'Approved list is not exact196')
    tree_tips=tips(Path(tree).read_text(encoding='utf-8'))
    must(len(tree_tips)==len(set(tree_tips))==196 and set(tree_tips)==set(panel),'Tree tips differ from exact approved accessions')
    wide=read_table(matrix,['accession']+['Type_'+t for t in TYPES]);by={r['accession']:r for r in wide}
    must(len(wide)==len(by)==196 and set(by)==set(panel),'Matrix row set differs')
    columns=['accession','rm_type','state','complete_count','partial_count','candidate_count','search_complete','conflict','positive_invalidated','count_lower_bound','review_ids']
    long=read_table(state,columns);keys=[(r['accession'],r['rm_type']) for r in long]
    must(len(long)==len(set(keys))==784 and set(keys)=={(a,t) for a in panel for t in TYPES},'State table is not exact196 by4')
    counts={'1':0,'0':0,'NA':0}
    for row in long:
        a,t=row['accession'],row['rm_type'];value=by[a]['Type_'+t]
        must(value in counts,'Cell is not 1/0/NA');counts[value]+=1
        must(row['state'] in STATES,'Unknown state')
        complete,partial,candidate=[integer(row[k]) for k in ('complete_count','partial_count','candidate_count')]
        must(candidate>=complete+partial,'Candidate count below accepted counts')
        search,conflict,invalid,lower=[boolean(row[k]) for k in ('search_complete','conflict','positive_invalidated','count_lower_bound')]
        must(lower==conflict,'Count lower-bound flag differs from uncertainty flag')
        ids=json.loads(row['review_ids']);must(isinstance(ids,list) and len(ids)==len(set(ids)) and all(isinstance(i,str) and i for i in ids),'Invalid review/candidate IDs')
        if row['state']=='COMPLETE_PREDICTED':must(complete>0,'Positive state has zero complete count')
        if row['state']=='CURATED_PARTIAL':must(partial>0 and complete==0,'Partial state/count differs')
        if row['state']=='NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH':must(search and not conflict and not invalid and candidate==0,'Non-detection cell has incomplete/positive evidence')
        expected='1' if complete>0 and not invalid else ('0' if row['state']=='NOT_DETECTED_AFTER_SUCCESSFUL_SEARCH' else 'NA')
        must(value==expected,'Matrix value contradicts reviewed state/count for '+a+' '+t)
    return {'schema':'RM_EXACT_ACCESSION_JOIN_V1','status':'PASS_SYNTHETIC_EXACT_JOIN' if synthetic else 'PASS_EXACT_196_784_JOIN',
            'dataset_kind':'SYNTHETIC' if synthetic else 'PRODUCTION','tip_count':196,'accession_count':196,'cell_count':784,
            'exact_accession_join':True,'unique_tips':True,'tree_sha256':sha(tree),'matrix_sha256':sha(matrix),
            'state_sha256':sha(state),'approved_sha256':sha(approved),'checker_sha256':sha(__file__),
            'cell_values':counts,'scientific_acceptance':'NOT_ESTABLISHED_BY_ACCOUNTING_CHECK',
            'evidence_limit':'Exact accession and state serialization only; accepted native tree and independent domain/source curation required separately.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('approved','tree','matrix','state','output'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--synthetic',action='store_true');args=ap.parse_args()
    report=check(args.approved,args.tree,args.matrix,args.state,args.synthetic)
    must(not args.output.exists(),'Preserve existing join receipt');args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report['status'])

if __name__=='__main__':main()
