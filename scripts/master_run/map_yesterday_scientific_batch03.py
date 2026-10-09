"""One-pass read-only old scientific cache to verified Release-member recovery mapping."""
from pathlib import Path
import collections, datetime, hashlib, json, os, re, stat

HERE=Path(__file__).resolve().parent/'yesterday_inventory/batch03'
PROOF=HERE.parent/'batch02'
ROOT=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
SCOPES=('data','.work/review2','.work/stage02_validated','.work/source_locus_inputs_v1',
        '.work/stage03_markers_v1','.work/stage04a_windows_alignments_v1','.work/stage04_phylogeny_v2')
EXPECTED={'summary.json':'5af4a85ef721cb5ca3f7f3c4517a2cc05c0a90bd6954ae28c01f4546a2b753be',
          'file_allowlist.json':'b0b5ed7da87c9c781dba2719ec6474e864ca9b1b241e4c490b35e5da07a0c351',
          'zip_member_validation.jsonl':'3cad66818067e0387ef955ba4dddcd73a85510debd48a8f9ee31126c93f4f524'}
MAX_SOURCE_BYTES=8*1024**3
MAX_SOURCE_FILES=60000
HERE.mkdir(exist_ok=True)

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()
def save(name,obj): (HERE/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def private(rel):
    parts=Path(rel).parts; name=Path(rel).name.lower()
    return '.private_run' in parts or any(x in name for x in ('codex_events','codex_stderr',
        'continuation_events','continuation_stderr','usage_reset','session_prompt','continuation_prompt'))
def same(a,b): return (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns)
def metadata(path,s):
    return {'path':str(path),'relative_path':path.relative_to(ROOT).as_posix(),'bytes':s.st_size,
            'mtime_ns':s.st_mtime_ns,'device':s.st_dev,'file_id':s.st_ino,'link_count':s.st_nlink}

started=utc()
for name in ('summary.json','file_allowlist.json'):
    if sha(PROOF/name)!=EXPECTED[name]: raise ValueError('Verified recovery proof changed: '+name)
accepted=json.loads((PROOF/'summary.json').read_text())
if accepted['status']!='PASS_CURRENT_REMOTE_SHA256_AND_ALL_LOCAL_ZIP_MEMBERS' \
    or accepted['remote_asset_identity_unchanged_before_after'] is not True:
    raise ValueError('Full actual current-remote/member proof required')
assets=json.loads((PROOF/'file_allowlist.json').read_text())['files']
asset_map={r['relative_path']:r for r in assets if r['path'].endswith('.zip')}

# Store one deterministic restoration witness per SHA+size, plus basename/accession
# alternatives. Equal bytes establish restoration, not biological equivalence.
by_content={}; by_name={}; by_accession={}; multiplicity=collections.Counter(); member_lines=0
mh=hashlib.sha256()
with (PROOF/'zip_member_validation.jsonl').open('rb') as f:
    for line in f:
        mh.update(line); r=json.loads(line); member_lines+=1
        if r['crc_verified'] is not True or not re.fullmatch('[a-f0-9]{64}',r['sha256']):
            raise ValueError('Invalid actual member proof')
        asset=asset_map[r['archive_relative_path']]
        key=(r['sha256'],r['bytes'])
        witness={'release_tag':asset['release_tag'],'remote_asset_id':asset['remote_asset_id'],
            'remote_asset_url':asset['remote_url'],'remote_zip_sha256':asset['sha256'],
            'remote_zip_bytes':asset['bytes'],'member':r['member'],'member_sha256':r['sha256'],
            'member_bytes':r['bytes'],'member_crc32':r['crc32']}
        by_content.setdefault(key,witness)
        by_name.setdefault((key,Path(r['member']).name),witness)
        accession=re.search(r'GC[FA]_\d+\.\d+',r['member'])
        if accession: by_accession.setdefault((key,Path(r['member']).name,accession[0]),witness)
        multiplicity[key]+=1
if mh.hexdigest()!=EXPECTED['zip_member_validation.jsonl'] or member_lines!=45955:
    raise ValueError('Member mapping exact hash/count changed')
save('source_proof.json',{'schema':'LAB_RM_VERIFIED_REMOTE_MEMBER_SOURCE_V1','utc':utc(),
    'proof_directory':str(PROOF),'proof_sha256':EXPECTED,'actual_verified_member_rows':member_lines,
    'current_remote_asset_identity_verified_by':'batch02/remote_assets_before.json + remote_assets_after.json',
    'assets_downloaded_or_rebuilt':False,'byte_restoration_only_not_new_scientific_acceptance':True})

groups=collections.defaultdict(lambda:collections.Counter())
counts=collections.Counter(); total_bytes=0; read_bytes=0
with (HERE/'file_allowlist.jsonl').open('w',encoding='utf-8',newline='\n') as good, \
     (HERE/'preserve_unmatched_or_excluded.jsonl').open('w',encoding='utf-8',newline='\n') as keep:
    for scope in SCOPES:
        scope_root=ROOT.joinpath(*Path(scope).parts)
        if scope_root.is_symlink() or scope_root.resolve()!=scope_root.absolute() or ROOT.resolve() not in scope_root.resolve().parents:
            raise ValueError('Exact source scope escaped old C root')
        for directory,dirs,names in os.walk(scope_root,followlinks=False):
            safe_dirs=[]
            for name in sorted(dirs):
                p=Path(directory)/name; s=p.lstat()
                if s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    row={'path':str(p),'scope':scope,'preserve_reason':'REPARSE_DIRECTORY_NOT_FOLLOWED'}
                    keep.write(json.dumps(row,sort_keys=True)+'\n'); counts['excluded_reparse_directories']+=1
                else: safe_dirs.append(name)
            dirs[:]=safe_dirs
            for name in sorted(names):
                p=Path(directory)/name; rel=p.relative_to(ROOT).as_posix(); s=p.lstat()
                row=metadata(p,s); row['scope']=scope
                counts['candidate_files']+=1; total_bytes+=s.st_size; groups[scope]['files']+=1; groups[scope]['bytes']+=s.st_size
                if counts['candidate_files']>MAX_SOURCE_FILES or total_bytes>MAX_SOURCE_BYTES:
                    raise ValueError('Bounded source count/byte scope exceeded; no cleanup authorized')
                reason=None
                if private(rel): reason='PRIVATE_CONTROL_OR_EVENT_METADATA_EXCLUDED'
                elif s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT: reason='REPARSE_FILE_NOT_READ'
                elif not stat.S_ISREG(s.st_mode): reason='NONREGULAR_FILE_NOT_READ'
                elif p.name.endswith(('.lock','.guard')): reason='LOCK_OR_GUARD_NOT_READ'
                if reason:
                    row['preserve_reason']=reason; keep.write(json.dumps(row,sort_keys=True)+'\n'); counts['excluded_files']+=1; groups[scope]['excluded_files']+=1; continue
                # One payload read; no earlier broad inventory hash is trusted in place of it.
                try:
                    h=hashlib.sha256(); actual_size=0
                    with p.open('rb') as f:
                        opened=os.fstat(f.fileno())
                        if not same(s,opened): raise ValueError('Identity changed before source read')
                        for block in iter(lambda:f.read(1024*1024),b''):
                            h.update(block); actual_size+=len(block)
                        closed=os.fstat(f.fileno())
                    after=p.stat()
                    if not same(s,closed) or not same(s,after) or actual_size!=s.st_size:
                        raise ValueError('Identity/content metadata changed during source read')
                    digest=h.hexdigest(); read_bytes+=actual_size; counts['hashed_files']+=1
                    row['sha256']=digest; key=(digest,actual_size)
                    accession=re.search(r'GC[FA]_\d+\.\d+',rel)
                    witness=(by_accession.get((key,p.name,accession[0])) if accession else None)
                    witness=witness or by_name.get((key,p.name)) or by_content.get(key)
                    if witness is None:
                        row['preserve_reason']='NO_EXACT_VERIFIED_REMOTE_MEMBER_SHA256_SIZE_MATCH'
                        keep.write(json.dumps(row,sort_keys=True)+'\n'); counts['unmatched_files']+=1; counts['unmatched_bytes']+=s.st_size; groups[scope]['unmatched_files']+=1; groups[scope]['unmatched_bytes']+=s.st_size
                    else:
                        row['recovery']=witness; row['matching_member_witness_count']=multiplicity[key]
                        row['validation_scope']='EXACT_BYTE_RESTORATION_ONLY_NOT_BIOLOGICAL_IDENTITY_OR_NEW_ACCEPTANCE'
                        good.write(json.dumps(row,sort_keys=True)+'\n'); counts['matched_files']+=1; counts['matched_bytes']+=s.st_size; groups[scope]['matched_files']+=1; groups[scope]['matched_bytes']+=s.st_size
                except (OSError,ValueError) as e:
                    row['preserve_reason']='READ_OR_CONCURRENT_CHANGE_UNPROVEN'; row['detail']=str(e)
                    keep.write(json.dumps(row,sort_keys=True)+'\n'); counts['changed_or_unreadable_files']+=1; groups[scope]['changed_or_unreadable_files']+=1
                if counts['candidate_files']%1000==0:
                    print(json.dumps({'files':counts['candidate_files'],'hashed_bytes':read_bytes,
                        'matched_files':counts['matched_files'],'scope':scope}),flush=True)
        print(json.dumps({'scope_complete':scope,'counts':dict(groups[scope])}),flush=True)

summary={'schema':'LAB_RM_OLD_SCIENTIFIC_CACHE_RELEASE_MEMBER_MAPPING_V1',
    'status':'PASS_EXACT_MATCHES_ONLY_UNMATCHED_PRESERVED','started_utc':started,'completed_utc':utc(),
    'root':str(ROOT),'scopes':list(SCOPES),'counts':dict(counts),'source_logical_bytes':total_bytes,
    'payload_bytes_read_one_pass':read_bytes,'maximum_scope_bytes':MAX_SOURCE_BYTES,
    'stream_chunk_bytes':1024*1024,'source_file_payload_passes':1,
    'groups':{k:dict(v) for k,v in groups.items()},'source_proof_sha256':sha(HERE/'source_proof.json'),
    'allowlist_sha256':sha(HERE/'file_allowlist.jsonl'),
    'preserve_manifest_sha256':sha(HERE/'preserve_unmatched_or_excluded.jsonl'),
    'actual_cleanup':'NOT_RUN','archive_or_download':'NOT_RUN','wsl_or_g_writes':'NOT_RUN',
    'ext4_image_read':False,'scientific_status_changes':False,
    'protected':'G counterpart source/accepted inputs; old C toolchain, original controllers/source guards/lock/private history.',
    'delete_semantics':'Only exact literal allowlisted leaf paths after root publishes pinned evidence and confirms unchanged bytes and no active handles; never recursive-delete scope directories.',
    'script_sha256':sha(Path(__file__))}
save('summary.json',summary)
save('evidence_sha256.json',{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}
    for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='evidence_sha256.json'})
print(json.dumps(summary,indent=2),flush=True)
