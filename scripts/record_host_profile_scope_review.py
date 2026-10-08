"""Record reviewed pinned family descriptors; source-hit review stays pending.

No profile, threshold or sequence is changed. Family predictions and unknown
functions remain separate from demonstrated activity in the approved strains.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
R=Path(__file__).resolve().parents[1]
PROFILE=R/'.tools/Firmicutes.hmm'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    # Explicit scope decisions after reading all119 pinned NAME/ACC/DESC fields.
    unknown={'DUF1934','DUF951','YbbR','YGGT'}
    clarified={'ATP_bind_2':'PF03668','DUF448':'PF04296','UPF0052':'PF01933','UPF0054':'PF02130','SPOUT_MTase':'PF02590'}
    rows=[]
    api=R/'.work/host_profile_annotations'
    references=[]
    for p in sorted(api.glob('*.json')):
        data=json.loads(p.read_text())
        references.append({'accession':p.stem,'url':'https://www.ebi.ac.uk/interpro/api/entry/pfam/'+p.stem+'/',
                           'raw_response_sha256':sha(p),'family_name':data['metadata']['name'],
                           'note':'Current annotation snapshot supplements, and does not replace, the pinned HMM.'})
    for block in PROFILE.read_text(encoding='ascii').split('//'):
        if not block.strip():continue
        fields={k:re.search(r'^'+k+r'\s+(.*)',block,re.M).group(1) for k in ('NAME','ACC','DESC')}
        name=fields['NAME'];refs=['Pinned GToTree1.8.10 Firmicutes model descriptor, SHA256='+sha(PROFILE)]
        if name in unknown:
            state='HOST_PROFILE_SCOPE_REVIEWED_FUNCTION_UNCHARACTERIZED'
            conclusion='Retained as a predicted conserved family in the curated host-marker set. Function remains uncharacterized; no enzymatic or R-M activity is inferred.'
        elif name in clarified:
            family=clarified[name];refs.append('https://www.ebi.ac.uk/interpro/entry/pfam/'+family+'/')
            state='HOST_PROFILE_SCOPE_REVIEWED'
            conclusion='Reviewed current family context supports host metabolism/RNA/ribosome scope. Every accepted source hit still requires independent annotation and exact-sequence review.'
            if name=='SPOUT_MTase':
                refs.append('https://pmc.ncbi.nlm.nih.gov/articles/PMC2553730/')
                conclusion='Pfam representative1ns5 is YbeA/RlmH; primary E.coli experiments establish rRNA methylation in that reference. This is family context, not demonstrated function for every approved-strain hit.'
        else:
            state='HOST_PROFILE_SCOPE_REVIEWED'
            conclusion='Pinned descriptor identifies a host translation, ribosome, metabolism, maintenance or cellular family. No descriptor explicitly identifies an R-M system role; individual hit annotations remain subject to review.'
        rows.append({'profile':name,'profile_accession':fields['ACC'],'profile_description':fields['DESC'],
                     'review_state':state,'conclusion':conclusion,'evidence_refs':refs})
    assert len(rows)==len({r['profile'] for r in rows})==119
    result={'status':'FAMILY_SCOPE_REVIEW_COMPLETE_SOURCE_HIT_REVIEW_PENDING','utc':datetime.now(timezone.utc).isoformat(),
            'profile_sha256':sha(PROFILE),'profile_count':119,'profiles':rows,'primary_annotation_snapshots':references,
            'unresolved_rm_candidates':None,'accepted_source_hit_review':{'status':'PENDING_ALL196_MARKER_INVENTORY'},
            'evidence_limit':'Predicted host orthology/function scope. Unknown function remains unknown; absence of explicit R-M words does not demonstrate function. Source-hit review must complete before Stage04 topology.'}
    out=R/'reports/stage03/host_profile_scope_review.json';out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('119_PROFILE_FAMILY_SCOPE_RECORDED; accepted source hit review pending')
if __name__=='__main__':main()
