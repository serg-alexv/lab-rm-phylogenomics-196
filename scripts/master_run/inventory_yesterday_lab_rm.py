"""Bounded read-only C inventory. Writes only beside this script; never deletes/publishes."""
from pathlib import Path
import collections, csv, datetime, hashlib, json, os, stat, subprocess

HERE = Path(__file__).resolve().parent / 'yesterday_inventory'
BASE = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08')
REPO = BASE / 'lab-rm-phylogenomics-196'
CHAT = BASE / 'referenced-chatgpt-conversation-this-is-an'
CURRENT = Path(__file__).resolve().parent
HASH_LIMIT = 256 * 1024 * 1024
SMALL_LIMIT = 2 * 1024 * 1024
TEXT = {'.py','.ps1','.md','.json','.jsonl','.tsv','.csv','.txt','.log','.yaml','.yml','.toml','.sh','.xml','.r','.nex','.nwk'}
FIXTURES = ('waiter_serialization_fixture_', 'windows_zip_open_')
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
HERE.mkdir(exist_ok=True)

def dump(name, value):
    (HERE/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def run(argv, timeout=90):
    p = subprocess.run(argv,capture_output=True,timeout=timeout)
    if p.returncode:
        raise RuntimeError('command failed: '+str(argv[:5])+'; '+p.stderr.decode('utf-8','replace')[:500])
    return p.stdout

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def file_digests(path, size, git_blob=False):
    h=hashlib.sha256()
    b=hashlib.sha1(b'blob '+str(size).encode()+b'\0') if git_blob else None
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
            if b is not None: b.update(block)
    return h.hexdigest(),b.hexdigest() if b is not None else None

def git(*args):
    return run(['git','--no-optional-locks','-C',str(REPO),*args])

head=git('rev-parse','HEAD').decode().strip()
tracked={}
for part in git('ls-tree','-rz','HEAD').split(b'\0'):
    if not part: continue
    info, name=part.split(b'\t',1)
    mode, kind, blob=info.decode().split()
    if kind=='blob': tracked[name.decode('utf-8','surrogateescape')]=blob
status_raw=git('status','--porcelain=v1','-z','--untracked-files=all')
status=[]
parts=status_raw.split(b'\0'); i=0
while i<len(parts):
    part=parts[i]; i+=1
    if not part: continue
    code=part[:2].decode('ascii'); path=part[3:].decode('utf-8','surrogateescape')
    row={'code':code,'path':path}
    if 'R' in code or 'C' in code:
        row['source_path']=parts[i].decode('utf-8','surrogateescape'); i+=1
    status.append(row)
dump('historical_git_status.json',{'utc':NOW,'head':head,'remote':git('remote','-v').decode(),'entries':status})

remote={'utc':NOW,'repository':'serg-alexv/lab-rm-phylogenomics-196','writes':False}
try:
    info=json.loads(run(['gh','api','repos/'+remote['repository']+'/commits/main','--jq','{commit:.sha,tree:.commit.tree.sha}']))
    remote.update(info)
    tree=json.loads(run(['gh','api','repos/'+remote['repository']+'/git/trees/'+info['tree']+'?recursive=1']))
    if tree.get('truncated'): raise RuntimeError('Remote tree truncated')
    dump('remote_main_tree.json',tree)
    compare=json.loads(run(['gh','api','repos/'+remote['repository']+'/compare/'+head+'...'+info['commit'],'--jq','{status:.status,ahead_by:.ahead_by,behind_by:.behind_by,merge_base_sha:.merge_base_commit.sha}']))
    remote['historical_head_ancestry']=compare
    releases=json.loads(run(['gh','api','--paginate','--slurp','repos/'+remote['repository']+'/releases?per_page=100']))
    releases=[item for page in releases for item in page]
    # Retain only public provenance fields; no auth/header state is captured.
    dump('remote_releases.json',[{'id':r['id'],'tag_name':r['tag_name'],'html_url':r['html_url'],
         'draft':r['draft'],'published_at':r['published_at'],'assets':[{
         k:a.get(k) for k in ('id','name','size','digest','state','browser_download_url','updated_at')}
         for a in r['assets']]} for r in releases])
    remote['status']='PASS_CURRENT_API_TREE_AND_RELEASE_METADATA_ONLY'
    remote['release_count']=len(releases)
except Exception as e:
    remote['status']='REMOTE_CHECK_UNPROVEN'; remote['error']=str(e)
    tree={'tree':[]}; releases=[]
dump('remote_observation.json',remote)
remote_blobs={x['path']:x['sha'] for x in tree['tree'] if x['type']=='blob'}
ancestor=remote.get('historical_head_ancestry',{}).get('status') in ('ahead','identical')

def classification(rel, scope):
    parts=rel.split('/')
    if scope=='historical_chat':
        return 'HISTORICAL_CHAT_ARCHIVE_BEFORE_PURGE'
    if parts[0]=='.tools': return 'PROTECTED_TOOLCHAIN_AND_RUNTIME'
    if parts[0]=='.git': return 'PROTECTED_HISTORICAL_GIT_STORE'
    if parts[0]=='.private_run': return 'PROTECTED_ORIGINAL_PRIVATE_CONTROL_HISTORY'
    if rel=='.work/workflow.lock': return 'PROTECTED_ORIGINAL_ACTIVE_LOCK'
    if parts[0] in ('scripts','config','status'):
        return 'PROTECTED_ORIGINAL_SOURCE_GUARDS_AND_CONTROL'
    if parts[0]=='.work' and len(parts)>1:
        group=parts[1]
        if group.startswith(FIXTURES): return 'SYNTHETIC_FIXTURE_ARCHIVE_BEFORE_PURGE'
        if any(x in group for x in ('controller','observer','recovery','durable')):
            return 'PROTECTED_ORIGINAL_CONTROLLER_AND_UNKNOWN_HISTORY'
        if group.startswith('stage04_inference_') or group.startswith('stage04_phylogeny_'):
            return 'SCIENTIFIC_CHECKPOINT_OR_FAILURE_HISTORY_PRESERVE'
        if group in ('source_locus_inputs_v1','stage02_validated') or group.startswith(('stage03','stage04a')):
            return 'SCIENTIFIC_INPUT_OR_ACCEPTED_DERIVATIVE_REMOTE_MEMBER_PROOF_REQUIRED'
        return 'HISTORICAL_WORK_ARCHIVE_BEFORE_PURGE'
    if parts[0] in ('data','release_staging'):
        return 'SCIENTIFIC_INPUT_OR_RELEASE_BYTES_REMOTE_MEMBER_PROOF_REQUIRED'
    return 'HISTORICAL_PROJECT_RECORD_REMOTE_PROOF_REQUIRED'

files=[]; skipped=[]; groups=collections.defaultdict(lambda:{'files':0,'bytes':0,'hashed_files':0,'hashed_bytes':0})
for scope,root in [('historical_repo',REPO),('historical_chat',CHAT)]:
    for directory, dirs, names in os.walk(root,followlinks=False):
        keep=[]
        for name in dirs:
            p=Path(directory)/name
            try:
                s=p.lstat()
                if s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    skipped.append({'path':str(p),'reason':'REPARSE_DIRECTORY_NOT_FOLLOWED'}); continue
            except OSError as e:
                skipped.append({'path':str(p),'reason':str(e)}); continue
            keep.append(name)
        dirs[:]=sorted(keep)
        for name in sorted(names):
            p=Path(directory)/name
            try:
                s=p.lstat(); rel=p.relative_to(root).as_posix()
                row={'scope':scope,'path':str(p),'relative_path':rel,'bytes':s.st_size,
                     'mtime_ns':s.st_mtime_ns,'classification':classification(rel,scope),'sha256':None}
                if s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    row['hash_state']='REPARSE_FILE_NOT_READ'
                else: row['hash_state']='PENDING_SELECTION'
                files.append(row)
            except OSError as e: skipped.append({'path':str(p),'reason':str(e)})

def important(row):
    rel=row['relative_path']; p=Path(rel)
    if rel in ('.work/workflow.lock','.private_run/session.lock') or p.name.endswith(('.guard','.lock')): return False
    if rel.startswith(('.git/', '.tools/')):
        return rel.startswith('.tools/iqtree_windows_3_1_4/') and p.name=='iqtree3.exe'
    if p.name in ('host.model.gz','host.ckp.gz'): return True
    return p.suffix.lower() in TEXT or p.name in ('SHA256SUMS','.gitattributes','.gitignore')

hash_bytes=0
for row in sorted(files,key=lambda x:(not x['relative_path'].startswith(('scripts/','reports/','status/','config/')),x['scope'],x['relative_path'])):
    if row['hash_state']!='PENDING_SELECTION': continue
    if row['relative_path'] in ('.work/workflow.lock','.private_run/session.lock') or Path(row['relative_path']).name.endswith(('.guard','.lock')):
        row['hash_state']='ACTIVE_OR_RETAINED_LOCK_NOT_OPENED'; continue
    pinned_exe=row['relative_path'].startswith('.tools/iqtree_windows_3_1_4/') and Path(row['relative_path']).name=='iqtree3.exe'
    if row['bytes']>SMALL_LIMIT and not pinned_exe:
        row['hash_state']='LARGE_FILE_METADATA_ONLY_LOW_IO'; continue
    if not important(row):
        row['hash_state']='RUNTIME_OR_DATA_PAYLOAD_METADATA_ONLY'; continue
    if hash_bytes+row['bytes']>HASH_LIMIT:
        row['hash_state']='BOUNDED_HASH_BUDGET_EXHAUSTED'; continue
    try:
        p=Path(row['path']); before=p.stat()
        check_blob=row['scope']=='historical_repo' and row['relative_path'] in tracked
        sha,blob=file_digests(p,before.st_size,check_blob); after=p.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            row['hash_state']='CHANGED_DURING_READ_UNPROVEN'; continue
        row['sha256']=sha; row['hash_state']='SHA256_CAPTURED'; hash_bytes+=row['bytes']
        if check_blob:
            # Git blob hash is checked from actual bytes, never inferred from clean status.
            row['actual_git_blob_sha1']=blob
            if remote_blobs.get(row['relative_path'])==blob:
                row['remote_recovery']='ACTUAL_BYTES_MATCH_CURRENT_REMOTE_MAIN_BLOB'
                row['remote_commit']=remote.get('commit')
            elif ancestor and tracked[row['relative_path']]==blob:
                row['remote_recovery']='ACTUAL_BYTES_MATCH_HISTORICAL_COMMIT_PROVEN_ANCESTOR_OF_REMOTE_MAIN'
                row['remote_commit']=head
            else: row['remote_recovery']='NO_VERIFIED_REMOTE_BLOB_MATCH'
    except OSError as e: row['hash_state']='READ_ERROR'; row['error']=str(e)

for row in files:
    parts=row['relative_path'].split('/')
    group='/'.join(parts[:2]) if parts[0] in ('.work','.tools','.private_run','release_staging','outputs','work') and len(parts)>1 else parts[0]
    key=row['scope']+'/'+group; g=groups[key]; g['files']+=1; g['bytes']+=row['bytes']
    if row['sha256']: g['hashed_files']+=1; g['hashed_bytes']+=row['bytes']
with (HERE/'files.jsonl').open('w',encoding='utf-8',newline='\n') as f:
    for row in sorted(files,key=lambda x:(x['scope'],x['relative_path'])): f.write(json.dumps(row,sort_keys=True)+'\n')
dump('groups.json',dict(sorted(groups.items())))
dump('skipped_paths.json',skipped)

receipts=[]
for p in sorted((REPO/'reports').rglob('publication_receipt.json')):
    try:
        value=json.loads(p.read_text(encoding='utf-8-sig'))
        receipts.append({'path':str(p),'sha256':digest(p),'status':value.get('status'),
             'release_tag':value.get('release_tag'),'url':value.get('url'),
             'payload_commit':value.get('payload_commit'),'assets':value.get('assets')})
    except Exception as e: receipts.append({'path':str(p),'error':str(e)})
dump('retained_publication_receipts.json',receipts)

pins=[]
for p in [CURRENT/'atomic_iqtree_windows.py',CURRENT/'stage5_atomic_config.template.json',
          CURRENT/'stage05_curation/audit_settings.template.json',CURRENT/'bootstrap/wsl_toolchain_probe_final.txt',
          CURRENT/'iqtree_attempts/partitioned_20261009T162904Z/config.json']:
    if p.is_file(): pins.append({'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)})
dump('current_dependency_evidence.json',pins)
sha_groups=collections.defaultdict(list)
for row in files:
    if row['sha256']: sha_groups[row['sha256']].append(row['path'])
dump('local_small_file_duplicate_groups.json',[{'sha256':k,'paths':v} for k,v in sorted(sha_groups.items()) if len(v)>1])
summary={'schema':'LAB_RM_BOUNDED_C_HISTORY_INVENTORY_V1','utc':NOW,
    'scope_roots':[str(REPO),str(CHAT)],'excluded_other_yesterday_chats':'12 look-through-my-chats-library-files folders: no bounded LABRM textual hits; task/task-3 empty; task-2 firmware unrelated',
    'files':len(files),'bytes':sum(r['bytes'] for r in files),'hashed_files':sum(bool(r['sha256']) for r in files),
    'hashed_unique_pass_bytes':hash_bytes,'hash_limit':HASH_LIMIT,'small_file_limit':SMALL_LIMIT,
    'remote_blob_matches':dict(collections.Counter(r.get('remote_recovery','NOT_CHECKED') for r in files)),
    'hash_states':dict(collections.Counter(r['hash_state'] for r in files)),
    'classifications':dict(collections.Counter(r['classification'] for r in files)),
    'remote':remote,'historical_head':head,'dirty_entries':len(status),'skipped_paths':len(skipped),
    'execution':'READ_ONLY_SOURCE_AND_METADATA_ONLY','actual_archive_export':'NOT_RUN',
    'actual_cleanup':'NOT_RUN','move_delete_push_or_biology':False,
    'limitations':['Large runtime/data/ZIP/ext4 bytes not hashed or streamed; sizes are metadata only.',
      'GitHub releases observation is metadata/digest only, not a new asset download/member verification.',
      'Local duplicate SHA groups do not prove remote recovery; no path is deletion-authorized by this report.',
      'Toolchain backing prefix, original source/control guards and active lock remain explicitly protected.']}
dump('summary.json',summary)
print(json.dumps(summary,indent=2))
