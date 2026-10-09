"""Derive exact source pins from previously verified released ZIP-member evidence.

Only small existing C receipts and pinned C evidence are read. No network,
source rebuild, scientific search, WSL, G write or acceptance decision.
"""
from pathlib import Path
import hashlib, json, re

WORK = Path(__file__).resolve().parent
OLD = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
PROOF = WORK/'yesterday_inventory/batch02'
EXPECTED = {
    'config/approved_accessions.txt':'85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6',
    'config/approval.json':'9e231457d39cd959942f38930a1f2b72cc391cabc86d0839a8adf8f5b6c94bdc',
    'reports/stage02/validation_summary.json':'5ea6555ae18780c407d2cfe69489dac1027571035abcc279f0f26d958ec891a0',
    'reports/stage02/publication_receipt.json':'23e8a6f2bb6ebea58b74b07f74f4011658e4387253544b1937d1e8803b227438',
    'reports/stage03/publication_receipt.json':'1f7c7b7739a61508ace397c28f9d2022b0dd5b67543dd1cb12ceda64506514d1',
    '.work/stage03_source_validation/validation_summary.json':'260420038849dc8509a2e5e99c48a6c9eba7c2e06953f4a4fc865a408d5481eb',
}
PROOF_PINS = {
    'summary.json':'5af4a85ef721cb5ca3f7f3c4517a2cc05c0a90bd6954ae28c01f4546a2b753be',
    'file_allowlist.json':'b0b5ed7da87c9c781dba2719ec6474e864ca9b1b241e4c490b35e5da07a0c351',
    'zip_member_validation.jsonl':'3cad66818067e0387ef955ba4dddcd73a85510debd48a8f9ee31126c93f4f524',
}

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def require(ok,text):
    if not ok:raise ValueError(text)

def main():
    for relative,digest in EXPECTED.items():require(sha(OLD/relative)==digest,'Accepted source receipt drift: '+relative)
    for relative,digest in PROOF_PINS.items():require(sha(PROOF/relative)==digest,'Released-byte proof drift: '+relative)
    summary=json.loads((PROOF/'summary.json').read_text())
    require(summary['status']=='PASS_CURRENT_REMOTE_SHA256_AND_ALL_LOCAL_ZIP_MEMBERS'
            and summary['remote_asset_identity_unchanged_before_after'] is True,'Actual released-byte proof incomplete')
    panel=(OLD/'config/approved_accessions.txt').read_text().split()
    require(len(panel)==len(set(panel))==196,'Approved panel differs')
    assets={r['relative_path']:r for r in json.loads((PROOF/'file_allowlist.json').read_text())['files'] if r['path'].endswith('.zip')}
    published={r['asset_name']:r for r in json.loads((OLD/'reports/stage03/publication_receipt.json').read_text())['assets']}
    receipts={};validation=None
    with (PROOF/'zip_member_validation.jsonl').open() as stream:
        for line in stream:
            row=json.loads(line);match=re.fullmatch(r'source_locus_inputs/assemblies/(GCF_[0-9]+\.[0-9]+)/build_receipt.json',row['member'])
            if not match and row['sha256']!=EXPECTED['.work/stage03_source_validation/validation_summary.json']:continue
            require(row['crc_verified'] is True and row['internal_sha256_verified'] is True,'Actual selected member verification absent')
            asset=assets[row['archive_relative_path']];name=Path(asset['path']).name
            require(asset['release_tag']=='stage03-hostmarkers196-v1' and name in published
                    and published[name]['sha256']==asset['sha256'] and published[name]['bytes']==asset['bytes']
                    and published[name]['download_readback_verified'] is True
                    and published[name]['all_zip_member_hashes_verified'] is True,'Published source asset identity differs')
            witness={'sha256':row['sha256'],'bytes':row['bytes'],'member':row['member'],
                     'asset_name':name,'asset_sha256':asset['sha256'],'remote_asset_id':asset['remote_asset_id'],
                     'release_tag':asset['release_tag'],'remote_asset_url':asset['remote_url']}
            if match:
                accession=match[1];require(accession in panel and accession not in receipts,'Unknown/duplicate released genome source')
                require(accession in published[name]['assemblies'],'Genome absent from original published asset accounting')
                path=OLD/'.work/source_locus_inputs_v1/assemblies'/accession/'build_receipt.json'
                require(not path.is_symlink() and path.resolve(strict=True)==path.absolute()
                        and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'Actual genome receipt differs from released member')
                receipts[accession]=witness
            else:
                require(validation is None and row['member']=='independent_source_validation/validation_summary.json',
                        'Missing/duplicate authoritative source-validation member')
                validation=witness
    require(set(receipts)==set(panel) and validation is not None,'Exact196 released source acceptance coverage required')
    result={'schema':'STAGE05_ACCEPTED_SOURCE_PINS_V1','approved_accessions_sha256':EXPECTED['config/approved_accessions.txt'],
            'accepted_files':EXPECTED,'source_validation_release_member':validation,
            'source_receipts':{accession:receipts[accession] for accession in panel},
            'derivation':{'builder_sha256':sha(__file__),'actual_released_byte_proof_sha256':PROOF_PINS,
                          'acceptance_created':False,'network_access':False,'source_rebuild':False}}
    output=WORK/'stage5_accepted_source_pins.json'
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'path':str(output),'sha256':sha(output),'bytes':output.stat().st_size,'genomes':len(receipts),
                      'actual_source_receipt_bytes_read':sum(row['bytes'] for row in receipts.values()),'state':'DERIVED_EXISTING_ACCEPTANCE_ONLY'}))

if __name__=='__main__':main()
