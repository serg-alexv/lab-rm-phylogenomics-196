#!/usr/bin/env python3
"""Bind actual full196 curation files/exceptions; never create a missing result."""
import argparse,hashlib,json
from pathlib import Path

PANEL_SHA='85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6'

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def build(settings):
    if settings.get('schema')!='RM_CURATION_AUDIT_SETTINGS_V1' or settings.get('dataset_kind')!='PRODUCTION':raise ValueError('Explicit production settings required')
    approved=Path(settings['approved']);panel=approved.read_text(encoding='ascii').split()
    if sha(approved)!=PANEL_SHA or len(panel)!=196 or len(set(panel))!=196:raise ValueError('Frozen approved196 differs')
    keys=('root','source','source_validation','approved','policy','models','padloc_db','environment','reviews','producer_source','matrix','state')
    contract={key:settings[key] for key in keys}
    contract.update(schema='RM_ATOMIC_INDEPENDENT_CURATION_CHECK_V1',dataset_kind='PRODUCTION',
                    producer_sha256=sha(settings['producer_source']),assemblies=[])
    for key in ('atomic_runner','supervisor'):
        contract[key+'_source']=settings[key+'_source'];contract[key+'_sha256']=sha(settings[key+'_source'])
    contract['runtime_manifest']=settings.get('runtime_manifest')
    contract['runtime_manifest_sha256']=sha(settings['runtime_manifest']) if settings.get('runtime_manifest') else None
    exceptions=settings.get('exception_records',{});positives=settings.get('retained_positive_entries',{})
    if not set(exceptions)<=set(panel) or not set(positives)<=set(exceptions):raise ValueError('Out-of-panel exception or unbound retained positive')
    for accession in panel:
        genome=Path(settings['genome_root'])/accession;entry={'accession':accession,'genome':str(genome)}
        if accession in exceptions:
            path=Path(exceptions[accession]);document=json.loads(path.read_text(encoding='utf-8'))
            if document.get('accession')!=accession or document.get('schema')!='RM_ATOMIC_CURATION_EXCEPTION_V1':raise ValueError('Wrong actual exception record')
            entry['exception_record']=str(path)
            if accession in positives:entry['retained_positive_entry']=positives[accession]
        else:
            directory=Path(settings['review_directory'])/accession
            members={'prepared':directory/'prepare/prepared.json','review':directory/'executed_review.json',
                     'result':directory/'apply/curated_candidate.json'}
            for name,path in members.items():
                if not path.is_file():raise ValueError('Actual full-panel review missing; provide an explicit genuine exception or finish this genome: '+str(path))
                entry[name]=str(path)
        contract['assemblies'].append(entry)
    return contract

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--settings',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists():raise ValueError('Preserve prior contract namespace')
    contract=build(json.loads(args.settings.read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8')
    print('FULL196_CURATION_CONTRACT_CANDIDATE_INDEPENDENT_AUDIT_REQUIRED')

if __name__=='__main__':main()
