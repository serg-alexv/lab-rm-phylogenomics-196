"""Build a bounded public recovery-mapping archive; no payload purge or upload."""
from pathlib import Path,PurePosixPath,PureWindowsPath
from collections import Counter
import datetime,hashlib,json,re,shutil,zipfile

WORK=Path(__file__).resolve().parent
OLD=PureWindowsPath(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=WORK/'master_batch03_mapping01'
NAME='master_batch03_scientific_cache_mapping01.zip'
PINS={
 'batch03/file_allowlist.jsonl':'df770f9e49e869c64f61db5720030aceff3b3282d53ee964aae02d228d7c3f64',
 'batch03/preserve_unmatched_or_excluded.jsonl':'bca12c16ff092b2e2fb612608186db728518d0ebf07fad80e1b401ed43ff0593',
 'batch03/source_proof.json':'67087f8bbed012fb8ec3741ea35fd22f1fbb4801f3d0b7d6661e7d22f279ff5d',
 'batch03/summary.json':'5e952c56472952f827f683d7bcebf030368ceb634ce75bbf54e2af3a3ec32288',
 'batch03/REVIEW.md':'9fae911d0f63f3b13784239be92b72672aec350f04b11575a3b0d19358e38e10',
 'batch02/evidence_sha256.json':'fa3737d7bd1799dc29e069c3862fbee5e3ec1c59eaeca99b68e79f05bcc3a74d'}
MAPPER_SHA='2b4c59634f4bf54cbd6f02e69cf980631f61611ccc36759314e9475f8d9564db'
SOURCE_SHA='a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84'
SCOPES={'data','.work/review2','.work/stage02_validated','.work/source_locus_inputs_v1',
        '.work/stage03_markers_v1','.work/stage04a_windows_alignments_v1','.work/stage04_phylogeny_v2'}
PRIVATE={'.git','.private_run','.codex'}

def must(ok,message):
    if not ok:raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    must(not OUT.exists(),'Use the unique new archive namespace; preserve prior builds')
    inputs={}
    for name,digest in PINS.items():
        path=WORK/'yesterday_inventory'/name
        must(path.is_file() and not path.is_symlink() and sha(path)==digest,'Frozen mapping input differs: '+name)
        inputs['mapping/'+name]=path
    b2=WORK/'yesterday_inventory/batch02'
    for name,row in read(b2/'evidence_sha256.json').items():
        path=b2/name;must(path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'Batch02 source witness drift')
        inputs['mapping/batch02/'+name]=path
    inputs['mapping/batch03/evidence_sha256.json']=WORK/'yesterday_inventory/batch03/evidence_sha256.json'
    mapper=WORK/'map_yesterday_scientific_batch03.py';must(sha(mapper)==MAPPER_SHA,'Original mapper source drift')
    inputs['code/map_yesterday_scientific_batch03.py']=mapper
    inputs['code/build_batch03_mapping_archive.py']=Path(__file__)
    pins_path=WORK/'stage5_accepted_source_pins.json';must(sha(pins_path)==SOURCE_SHA,'Accepted source pins differ')
    inputs['control/accepted_source_pins.json']=pins_path
    sourcepins=read(pins_path)
    sourceproof=read(WORK/'yesterday_inventory/batch03/source_proof.json')
    must(sourceproof['proof_sha256']=={name:sha(b2/name) for name in ('file_allowlist.json','summary.json','zip_member_validation.jsonl')}
         and sourceproof['actual_verified_member_rows']==45955,'Mapping proof is not bound to included actual member ledger')
    # Compact actual ZIP-member witness index, not another source-payload pass.
    archives={r['relative_path']:r for r in read(b2/'file_allowlist.json')['files'] if r['relative_path'].endswith('.zip')}
    witnesses={}
    with (b2/'zip_member_validation.jsonl').open(encoding='utf-8') as f:
        for line in f:
            r=json.loads(line);a=archives[r['archive_relative_path']]
            must(r['crc_verified'] is True and r['internal_sha256_verified'] is (r['member']!='SHA256SUMS.txt'),'Unverified member witness')
            key=(a['remote_asset_id'],r['member'],r['sha256'],r['bytes'],r['crc32'])
            witnesses[key]=(a['sha256'],a['bytes'],a['remote_url'],a['release_tag'])
    count=total=eligible_count=eligible_bytes=0;seen=set();holds=[];groups=Counter()
    with (WORK/'yesterday_inventory/batch03/file_allowlist.jsonl').open(encoding='utf-8') as f:
        for line in f:
            r=json.loads(line);rel=r['relative_path'];p=PurePosixPath(rel);recovery=r['recovery']
            must(p.as_posix()==rel and not p.is_absolute() and '..' not in p.parts and not PRIVATE.intersection(p.parts)
                 and r['scope'] in SCOPES and (rel==r['scope'] or rel.startswith(r['scope']+'/'))
                 and r['path']==str(OLD.joinpath(*p.parts)) and r['path'].casefold() not in seen,'Mapping path/scope duplicate or escape')
            seen.add(r['path'].casefold())
            must(type(r['bytes']) is int and r['bytes']>=0 and re.fullmatch('[a-f0-9]{64}',r['sha256'])
                 and recovery['member_sha256']==r['sha256'] and recovery['member_bytes']==r['bytes'],'Mapping byte binding differs')
            key=(recovery['remote_asset_id'],recovery['member'],r['sha256'],r['bytes'],recovery['member_crc32'])
            must(witnesses.get(key)==(recovery['remote_zip_sha256'],recovery['remote_zip_bytes'],recovery['remote_asset_url'],recovery['release_tag']),
                 'Mapping does not match included verified actual ZIP-member provenance')
            reason=None
            if r['scope']=='.work/review2':reason='PRESERVE_ALL_REVIEW2_PENDING_HISTORY_AND_CURRENT_POLICY_RECONCILIATION'
            elif rel in sourcepins['accepted_files']:reason='PRESERVE_CURRENT_ACCEPTED_SOURCE_CONTROL_PATH'
            elif r['scope']=='.work/source_locus_inputs_v1' and p.name=='build_receipt.json':
                accession=p.parent.name;must(accession in sourcepins['source_receipts'] and sourcepins['source_receipts'][accession]['sha256']==r['sha256'],
                    'Mapped old source receipt differs from current fixed accepted pin')
                reason='PRESERVE_OLD_C_SOURCE_RECEIPT_UNTIL_CANONICAL_G_AND_STANDALONE_GATE_RECONCILED'
            count+=1;total+=r['bytes'];groups[r['scope']]+=1
            if reason:holds.append({k:r[k] for k in ('path','relative_path','bytes','sha256')}|{'reason':reason})
            else:eligible_count+=1;eligible_bytes+=r['bytes']
    must((count,total)==(47648,6568632074),'Exact mapped proposal accounting differs')
    preserve_count=preserve_bytes=0
    with (WORK/'yesterday_inventory/batch03/preserve_unmatched_or_excluded.jsonl').open(encoding='utf-8') as f:
        for line in f:
            r=json.loads(line);preserve_count+=1;preserve_bytes+=r['bytes']
    must((preserve_count,preserve_bytes)==(619,981198193),'Exact preserved-unmatched accounting differs')
    OUT.mkdir()
    assessment={'schema':'MASTER_BATCH03_CONSERVATIVE_LEAF_ASSESSMENT_V1','state':'PROPOSAL_ONLY_NO_PURGE',
        'mapped_files':count,'mapped_bytes':total,'conservative_candidate_files':eligible_count,'conservative_candidate_bytes':eligible_bytes,
        'additionally_preserved_files':len(holds),'additionally_preserved_bytes':sum(r['bytes'] for r in holds),
        'unmatched_preserved_files':preserve_count,'unmatched_preserved_bytes':preserve_bytes,
        'accepted_source_pins_sha256':SOURCE_SHA,'files_preserved':holds,
        'actual_purge':'NOT_RUN','live_source_rehash':'NOT_RUN_REUSE_EXACT_COMPLETED_ONE_PASS_MAP',
        'requirements_before_any_purge':['Publish and independently verify this exact archive and controls remotely.',
            'Use literal mapped leaf paths only; never delete scope directories recursively.',
            'Recheck canonical old C roots, no reparse traversal, exact file ID/size/mtime and fresh SHA256.',
            'Verify current active dependency identities and no active handles; preserve on ambiguity or drift.',
            'Preserve all G source/input counterparts, toolchain, original lock/controller and private history.']}
    write(OUT/'conservative_leaf_assessment.json',assessment)
    inputs['control/conservative_leaf_assessment.json']=OUT/'conservative_leaf_assessment.json'
    text=('This archive contains public scientific cache path/hash/recovery metadata and source code only.\n'
          'It contains no old scientific payload copies, unmatched payloads, raw Codex events, private prompts, usage or credentials.\n'
          'The 47,648 mapped leaf paths are a historical byte-restoration proposal, not deletion authority or new scientific acceptance.\n'
          'Conservative selection excludes all review2 and all196 original C build receipts pending final active-dependency reconciliation.\n'
          'Source payload hashes are reused from the completed pinned one-pass mapper, not rerun here.\n'
          'The included batch02 member ledger was actually validated before old release-staging copies were purged.\n'
          'Root must publish, independently read back and check live exact identities before any later leaf-only purge.\n')
    (OUT/'README.txt').write_text(text,encoding='utf-8',newline='\n');inputs['README.txt']=OUT/'README.txt'
    captured={name:{'sha256':sha(path),'bytes':path.stat().st_size} for name,path in sorted(inputs.items())}
    binding={'schema':'MASTER_BATCH03_MAPPING_ARCHIVE_SOURCE_BINDING_V1','state':'LOCAL_BUILD_ONLY_NO_PURGE',
        'builder_sha256':sha(__file__),'mapper_sha256':MAPPER_SHA,'accepted_source_pins_sha256':SOURCE_SHA,
        'payload_inputs':captured,'mapped_files':count,'unmatched_payloads_archived':False,
        'old_payload_files_read':0,'network_calls':0,'g_writes':0,'wsl_starts':0,'source_deletions':0}
    write(OUT/'source_binding.json',binding);inputs['control/source_binding.json']=OUT/'source_binding.json'
    captured['control/source_binding.json']={'sha256':sha(OUT/'source_binding.json'),'bytes':(OUT/'source_binding.json').stat().st_size}
    sums=''.join(r['sha256']+'  '+name+'\n' for name,r in sorted(captured.items()))
    (OUT/'SHA256SUMS.txt').write_text(sums,encoding='utf-8',newline='\n');inputs['SHA256SUMS.txt']=OUT/'SHA256SUMS.txt'
    captured['SHA256SUMS.txt']={'sha256':sha(OUT/'SHA256SUMS.txt'),'bytes':(OUT/'SHA256SUMS.txt').stat().st_size}
    archive=OUT/NAME
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for name,path in sorted(inputs.items()):
            zi=zipfile.ZipInfo(name,(2026,10,9,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16
            with path.open('rb') as source,z.open(zi,'w',force_zip64=True) as target:shutil.copyfileobj(source,target,1024*1024)
    must(archive.stat().st_size<500*1024**2,'Stagewise asset bound exceeded')
    verified=[]
    with zipfile.ZipFile(archive) as z:
        must(len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(captured),'Archive member set differs')
        for name,expected in sorted(captured.items()):
            with z.open(name) as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            must(actual==expected['sha256'] and z.getinfo(name).file_size==expected['bytes'],'Actual ZIP bytes differ from captured expected source')
            must(sha(inputs[name])==expected['sha256'],'Input drift during archive construction')
            verified.append({'member':name,**expected,'crc32':f'{z.getinfo(name).CRC:08x}','crc_verified':True})
    receipt={'schema':'MASTER_BATCH03_MAPPING_ARCHIVE_LOCAL_BUILD_V1','state':'LOCAL_ZIP_ALL_MEMBERS_VERIFIED_NO_PURGE',
        'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,
        'builder_sha256':sha(__file__),'source_binding_sha256':sha(OUT/'source_binding.json'),
        'payload_members':len(captured)-1,'all_member_crc_sha256_and_captured_input_bytes_verified':True,
        'mapped_files':count,'unmatched_preserved_files':preserve_count,'conservative_candidate_files':eligible_count,
        'unmatched_payloads_archived':False,'source_deletions':0,'network_calls':0,'g_writes':0,'wsl_starts':0,
        'actual_remote_export':'NOT_RUN','scientific_acceptance_changes':False,'members':verified}
    write(OUT/'build_receipt.json',receipt)
    (OUT/(NAME+'.sha256')).write_text(receipt['sha256']+'  '+NAME+'\n',encoding='ascii',newline='\n')
    print(json.dumps({k:receipt[k] for k in ('state','archive','sha256','bytes','payload_members','mapped_files','conservative_candidate_files')},indent=2))

if __name__=='__main__':main()
