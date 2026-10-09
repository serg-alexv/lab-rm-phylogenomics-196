"""Preserve successful batch03 execution evidence in one bounded C-only ZIP.

Requires actual independent post-purge PASS. Does not clean, infer science,
contact GitHub, boot WSL, execute archived code or copy scientific payloads.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,stat,zipfile

WORK=Path(__file__).resolve().parent
VERIFIER_SHA='dbb0140fe2fac41940fa8d4838ffcbf1f6b72933d6d14a2011137ef4c401c56f'
OWNERS=((4768,'134360369876207076'),(27048,'134360369803845506'))
FIXED={
 'code/Invoke-MasterBatch03LeafPurge.ps1':('Invoke-MasterBatch03LeafPurge.ps1','94b5d9fb98c211b1c4915ff84de8d006ded9d01ec3d3bb11650657781f9d285c'),
 'code/prepare_master_batch03_leaf_purge.py':('prepare_master_batch03_leaf_purge.py','b26e130c3f5e857ccd1491a5489577ef78f10abbf589ec000b2652a86555e1f2'),
 'code/test_master_batch03_leaf_purge.py':('test_master_batch03_leaf_purge.py','5ca75eb48204d89576fb42125140cbc4fd3e561e32b3b7ab93091641917ca57f'),
 'code/Test-MasterBatch03LeafPurge.ps1':('Test-MasterBatch03LeafPurge.ps1','69c3971a3220e3d72297756fc149a6cb2d831d813a225e895ba60758ca864915'),
 'code/verify_master_batch03_leaf_purge.py':('verify_master_batch03_leaf_purge.py',VERIFIER_SHA),
 'code/test_master_batch03_postverify.py':('test_master_batch03_postverify.py','167a768a5ce607880e540e96d107b5f90c1bf430f3d42f50727cfa4616f6b557'),
 'control/proposed.json':('master_batch03_leaf_purge_proposed.json','3f291dc20bb7051a9586aaefc75b7c57c463fba03e87d5ea8c9cdd2dc2ffd952'),
 'control/protected_before.json':('master_batch03_protected_before.json','22d307f5bba8a98dbd060e3d1d091e22c7f70dc85b40e77ada04c0eef36ce1a7'),
 'reviews/leaf_purge_preparation_checks.json':('master_batch03_leaf_purge_preparation_checks.json','ca06101bee75f0f99a533b1116dd2091d517a405a5116e9602b9dfd2f3c88f6e'),
 'reviews/leaf_purge_PREPARATION.md':('master_batch03_leaf_purge_PREPARATION.md','2d9bd848bdabdd7748faaad7cf5e8f3ca2cdd57d69dd7da3923250164bd13b55'),
 'reviews/postverify_preparation_checks.json':('master_batch03_postverify_preparation_checks.json','03bdc0758900f49ca0509f5ea6c8685b74ef3e0d46c3c1ccaece6751abfa3eb6'),
 'reviews/postverify_PREPARATION.md':('master_batch03_postverify_PREPARATION.md','8ee96c5ad094f089b580377c75a7d6e0c8ce651cec825e2af9a281604dda48c8'),
 'reviews/actual_stream_parser_check.json':('master_batch03_stream_parser_check.json','7dc02ca7f57069713ffb045f9f7da86d313c027461847b37250cf3823b8c297c'),
 'recovery/purge_source_remote_readback.json':('master_batch03_purge_remote_readback.json','b4cca6490a1261bf5d9badfbc4bec96ff46473fb436394e7f3be1e36e735b412'),
 'recovery/purge_git_objects.json':('master_batch03_purge_git_objects.json','0d8932ecc38b2049c6f3ab4031c7b586a0b0caf98d09a7ffb2ad5cb617f01398'),
 'recovery/mapping_archive_remote_readback.json':('batch03_mapping01_remote_readback_20261009T192220Z_3e6cf7d8/receipt.json','edb749c997c3d68b061af0441807cd7eb9a8b3df453474d69c740c6640e182d1'),
 'recovery/master_batch03_scientific_cache_mapping01.zip':('master_batch03_mapping01/master_batch03_scientific_cache_mapping01.zip','f6d7e0558953d2542ca085552a6cd8219a4ec1acde4072ce6f03d12dd953178e'),
}
JOURNAL_FIELDS={
 'BEGIN':{'proposal_commit','plan_sha256','recovery_receipt_sha256','schema','mapping_sha256','event','utc'},
 'VERIFIED_INTENT':{'event','utc','line','path','bytes','sha256','device','file_id','mtime_ns'},
 'REMOVED':{'event','utc','line','path','bytes','sha256','deleted','deleted_bytes'},
 'COMPLETE':{'event','utc','state','deleted','deleted_bytes','held_files','unmatched_preserved','recursive_deletes'},
}
LIMIT=500*1024**2

def require(ok,message):
    if not ok:raise ValueError(message)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def signature(s):return(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
def plain(path):
    require(path.absolute()==path.resolve(),'Input/output path alias')
    for p in [path,*path.parents]:
        s=p.lstat();require(not s.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT,'Reparse archive input/parent')
    require(stat.S_ISREG(path.lstat().st_mode),'Nonregular archive input')
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')

def validate_post(p):
    require(p.get('schema')=='MASTER_BATCH03_INDEPENDENT_POST_PURGE_VERIFY_V1'
            and p.get('state')=='PASS_EXACT47429_REMOVED_838_ORIGINALS_AND12_PROTECTED_UNCHANGED'
            and p.get('verifier_sha256')==VERIFIER_SHA,'Actual independent successful post-purge receipt required')
    require((p.get('removed_files'),p.get('removed_bytes'),p.get('held_files'),p.get('held_bytes'),
             p.get('unmatched_files'),p.get('unmatched_bytes'))==(47429,6565902818,219,2729256,619,981198193),
            'Post-purge exact source/removed accounting differs')
    require(p.get('remaining_after_stop')==0 and p.get('unreceipted_absences')==[]
            and p.get('retained_original_bytes_hashed')==983927449,'Partial/unproven cleanup cannot be archived as successful')
    require(all(p.get(k)==0 for k in ('source_deletions','network_calls','g_writes','wsl_starts','scientific_jobs')),
            'Post-verifier scope differs')
    originals=p.get('retained_originals',[])
    require(len(originals)==len({r['path'].casefold() for r in originals})==838
            and sum(r['bytes'] for r in originals)==983927449
            and all(r.get('identity_equal') is True and re.fullmatch('[a-f0-9]{64}',r['sha256']) for r in originals),
            'Exact838 full-hash preserved original proof required')
    require(len(p.get('protected_files',[]))==12 and all(r.get('unchanged') is True for r in p['protected_files']),
            'All12 protected byte proofs required')
    for key in ('owners_before','owners_after'):
        rows=p.get(key,[])
        require(len(rows)==2 and tuple((r['pid'],r['creation_filetime']) for r in rows)==OWNERS
                and all(r.get('alive') is True and r.get('retained_handle') is True for r in rows),
                'Retained exact live native/controller proof required')
    t=p.get('journal_terminal',{})
    require(t.get('event')=='COMPLETE' and t.get('state')=='PASS_EXACT_47429_COLD_LEAVES_REMOVED'
            and t.get('deleted')==47429 and t.get('deleted_bytes')==6565902818
            and t.get('held_files')==219 and t.get('unmatched_preserved')==619 and t.get('recursive_deletes')==0,
            'Exact successful terminal journal required')

def journal_scope(path,post):
    count=0;last=None;digest=hashlib.sha256()
    with path.open('rb') as f:
        for line in f:
            digest.update(line);r=json.loads(line);event=r.get('event')
            require(event in JOURNAL_FIELDS and set(r)==JOURNAL_FIELDS[event],
                    'Public journal has unexpected/raw/private record fields')
            require(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z',r['utc']),
                    'Unexpected journal timestamp payload')
            count+=1;last=r
    require(digest.hexdigest()==post['journal_sha256'] and count==post['journal_records']
            and last==post['journal_terminal'],'Actual full journal differs from independent post-purge readback')

def build(post_path,post_sha):
    require(os.name=='nt' and os.environ.get('COMPUTERNAME','').casefold()=='wd'
            and WORK==Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work').resolve(),
            'Exact WD C-work build namespace required')
    post_path=Path(post_path).absolute();plain(post_path)
    require(post_path.parent.parent==WORK and re.fullmatch(r'master_batch03_postverify_\d{8}T\d{6}Z_[a-f0-9]{8}',post_path.parent.name)
            and post_path.name=='receipt.json' and sha(post_path)==post_sha,'Exact new postverify receipt namespace/SHA required')
    post=json.loads(post_path.read_bytes());validate_post(post)
    own_sha=sha(__file__);journal=WORK/'master_batch03_leaf_purge_20261009_receipt.jsonl';plain(journal);journal_scope(journal,post)
    inputs={};initial_pins={member:pin for member,(_,pin) in FIXED.items()}
    for member,(name,pin) in FIXED.items():
        path=WORK/name;plain(path);require(sha(path)==pin,'Frozen executed source/control differs: '+name);inputs[member]=path
    inputs.update({'execution/full_public_cleanup_journal.jsonl':journal,'execution/independent_postverify.json':post_path,
                   'code/build_master_batch03_execution_archive.py':Path(__file__),
                   'code/test_master_batch03_execution_archive.py':WORK/'test_master_batch03_execution_archive.py'})
    initial_pins.update({'execution/full_public_cleanup_journal.jsonl':post['journal_sha256'],
                        'execution/independent_postverify.json':post_sha,
                        'code/build_master_batch03_execution_archive.py':own_sha,
                        'code/test_master_batch03_execution_archive.py':sha(inputs['code/test_master_batch03_execution_archive.py'])})
    # Reopen the exact original838 path/SHA proof from the actual immutable mapping archive.
    with zipfile.ZipFile(inputs['recovery/master_batch03_scientific_cache_mapping01.zip']) as z:
        holds={r['path'].casefold() for r in json.loads(z.read('control/conservative_leaf_assessment.json'))['files_preserved']}
        expected={}
        with z.open('mapping/batch03/file_allowlist.jsonl') as f:
            for line in f:
                r=json.loads(line)
                if r['path'].casefold() in holds:expected[r['path']]=(r['bytes'],r['sha256'])
        with z.open('mapping/batch03/preserve_unmatched_or_excluded.jsonl') as f:
            for line in f:
                r=json.loads(line);require(r['path'] not in expected,'Original838 duplicate');expected[r['path']]=(r['bytes'],r['sha256'])
    require({r['path']:(r['bytes'],r['sha256']) for r in post['retained_originals']}==expected and len(expected)==838,
            'Postverify originals do not match original published mapping')
    protected=json.loads(inputs['control/protected_before.json'].read_bytes())['files']
    require({r['path']:(r['bytes'],r['sha256']) for r in protected}==
            {r['path']:(r['bytes'],r['sha256']) for r in post['protected_files']},'Postverify protected pins differ from original baseline')
    out=WORK/'master_batch03_cleanup_execution01_metadata';asset=WORK/'master_batch03_cleanup_execution01.zip';partial=WORK/(asset.name+'.unverified')
    require(not out.exists() and not asset.exists() and not partial.exists(),'Preserve existing archive/build namespace');out.mkdir()
    captured={}
    for member,path in inputs.items():
        plain(path);s=path.lstat();captured[member]={'path':str(path),'bytes':s.st_size,'sha256':sha(path),'original_file_identity':signature(s)}
        require(captured[member]['sha256']==initial_pins[member] and signature(path.lstat())==signature(s),
                'Pinned source changed while capturing input manifest')
    binding={'schema':'MASTER_BATCH03_EXECUTION_ARCHIVE_SOURCE_BINDING_V1','state':'BUILD_ONLY_FROM_ACTUAL_SUCCESSFUL_POSTVERIFY',
             'builder_sha256':own_sha,'postverify_sha256':post_sha,'inputs':captured,
             'logical_removed_bytes':6565902818,'physical_disk_reclaimed_bytes':'NOT_MEASURED',
             'residual_leaf_race':'Exclusive hash handle closes before literal PowerShell Remove-Item. Short leaf replacement interval explicitly retained; no atomic-delete claim.',
             'raw_codex_events_prompts_usage_archived':False,'scientific_acceptance':'NONE_EXECUTION_HISTORY_ONLY',
             'source_deletions':0,'network_calls':0,'g_writes':0,'wsl_starts':0,'native_launches':0}
    write(out/'source_bindings.json',binding);inputs['control/source_bindings.json']=out/'source_bindings.json'
    expected={m:{'bytes':r['bytes'],'sha256':r['sha256']} for m,r in captured.items()}
    expected['control/source_bindings.json']={'bytes':(out/'source_bindings.json').stat().st_size,'sha256':sha(out/'source_bindings.json')}
    sums=''.join(pin['sha256']+'  '+m+'\n' for m,pin in sorted(expected.items())).encode()
    expected['SHA256SUMS.txt']={'bytes':len(sums),'sha256':hashlib.sha256(sums).hexdigest()}
    with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for member in sorted(expected):
            zi=zipfile.ZipInfo(member,(2026,10,9,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16
            if member=='SHA256SUMS.txt':z.writestr(zi,sums);continue
            path=inputs[member];plain(path);before=path.lstat();h=hashlib.sha256();size=0
            if member in captured:require(signature(before)==tuple(captured[member]['original_file_identity']),'Captured source file identity changed before ZIP copy')
            with path.open('rb') as source,z.open(zi,'w',force_zip64=True) as target:
                require(signature(os.fstat(source.fileno()))==signature(before),'Source identity changed before copy')
                for block in iter(lambda:source.read(1024**2),b''):target.write(block);h.update(block);size+=len(block)
                require(signature(os.fstat(source.fileno()))==signature(before),'Source handle changed during copy')
            require(signature(path.lstat())==signature(before) and h.hexdigest()==expected[member]['sha256']
                    and size==expected[member]['bytes'],'Actual archive source drift')
    require(partial.stat().st_size<LIMIT,'Actual ZIP exceeds500MiB');verified=[]
    with zipfile.ZipFile(partial) as z:
        require(len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(expected),'Exact ZIP member set differs')
        for member,pin in sorted(expected.items()):
            info=z.getinfo(member);require(stat.S_IFMT(info.external_attr>>16)==stat.S_IFREG and not info.flag_bits&1,'Nonregular/encrypted member')
            with z.open(member) as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            require(actual==pin['sha256'] and info.file_size==pin['bytes'],'Actual ZIP member CRC/SHA/source mismatch')
            verified.append({'member':member,**pin,'crc32':f'{info.CRC:08x}','crc_verified':True})
    for member,path in inputs.items():
        require(sha(path)==expected[member]['sha256'],'Source changed after ZIP verification')
        if member in captured:require(signature(path.lstat())==tuple(captured[member]['original_file_identity']),'Captured source identity changed after ZIP verification')
    require(sha(__file__)==own_sha,'Builder source changed');partial.rename(asset)
    asset_sha=sha(asset);(WORK/(asset.name+'.sha256')).write_text(asset_sha+'  '+asset.name+'\n',encoding='ascii',newline='\n')
    manifest={'schema':'MASTER_BATCH03_EXECUTION_ARCHIVE_MANIFEST_V1','asset':str(asset),'bytes':asset.stat().st_size,'sha256':asset_sha,
              'members':verified,'source_binding_sha256':sha(out/'source_bindings.json'),'original_notice_policy':'Executed original source bytes/headers preserved; no third-party tools/models or scientific payloads copied.'}
    write(out/'manifest.json',manifest)
    result={**{k:v for k,v in binding.items() if k!='inputs'},'schema':'MASTER_BATCH03_EXECUTION_ARCHIVE_BUILD_V1',
            'state':'LOCAL_ZIP_ALL_EXECUTION_MEMBERS_CRC_SHA_VERIFIED_NO_UPLOAD_OR_PURGE','finished_utc':utc(),
            'asset':str(asset),'sha256':asset_sha,'bytes':asset.stat().st_size,'members':len(verified),
            'manifest_sha256':sha(out/'manifest.json'),'actual_remote_export':'NOT_RUN','logical_removed_files':47429,
            'all_actual_zip_members_crc_sha_and_captured_source_verified':True}
    write(out/'build_receipt.json',result);print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--postverify',required=True);parser.add_argument('--postverify-sha256',required=True)
    args=parser.parse_args();build(args.postverify,args.postverify_sha256)
