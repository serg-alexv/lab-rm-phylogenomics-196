"""Read-only exact release-staging duplicate verification; never removes or downloads."""
from pathlib import Path, PurePosixPath
import collections, datetime, hashlib, json, os, re, stat, subprocess, zipfile

HERE=Path(__file__).resolve().parent/'yesterday_inventory/batch02'
ROOT=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
REPOSITORY='serg-alexv/lab-rm-phylogenomics-196'
TAGS={'stage02':'stage02-sequences196-v1','stage03':'stage03-hostmarkers196-v1',
      'stage04a':'stage04a-hostalignments196-v1','stage04b':'stage04b-inference-resource-failure196-v1'}
HERE.mkdir(exist_ok=True)

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,value): (HERE/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()
def api(endpoint):
    p=subprocess.run(['gh','api','repos/'+REPOSITORY+'/'+endpoint],capture_output=True,timeout=90,check=True)
    return json.loads(p.stdout)
def observe():
    result={}
    for group,tag in TAGS.items():
        r=api('releases/tags/'+tag)
        if r['draft'] or r['tag_name']!=tag: raise ValueError('Expected published exact release')
        result[group]={'tag':tag,'release_id':r['id'],'url':r['html_url'],'assets':{
            a['name']:{k:a.get(k) for k in ('id','name','size','digest','state','browser_download_url')}
            for a in r['assets']}}
    return result

started=utc(); before=observe(); save('remote_assets_before.json',{'utc':utc(),'releases':before})
receipt_pins={}; receipt_assets={}
for group,tag in TAGS.items():
    p=ROOT/'reports'/group/'publication_receipt.json'; content=p.read_bytes(); receipt=json.loads(content)
    if receipt.get('status')!='UPLOAD_VERIFIED' or receipt.get('release_tag')!=tag:
        raise ValueError('Retained publication receipt not validated for exact release')
    receipt_pins[group]={'path':str(p),'sha256':hashlib.sha256(content).hexdigest(),'tag':tag}
    receipt_assets[group]={a['asset_name']:a for a in receipt['assets']}

selected=[]
for group in TAGS:
    for p in sorted((ROOT/'release_staging'/group).rglob('*')):
        if not p.is_file() or not p.name.endswith(('.zip','.zip.sha256')): continue
        if p.is_symlink() or p.resolve()!=p.absolute() or not (ROOT/'release_staging'/group).resolve() in p.resolve().parents:
            raise ValueError('Nonliteral staging path or symlink')
        asset=before[group]['assets'].get(p.name)
        if not asset or asset['state']!='uploaded' or not re.fullmatch('sha256:[a-f0-9]{64}',asset.get('digest') or ''):
            raise ValueError('Current exact remote asset digest missing: '+str(p))
        selected.append((group,p,asset))
if len(selected)!=82: raise ValueError('Bounded expected batch changed; review selection')
records=[]; members_count=0; unpacked_bytes=0
with (HERE/'zip_member_validation.jsonl').open('w',encoding='utf-8',newline='\n') as details:
    for index,(group,p,asset) in enumerate(selected,1):
        s=p.stat(); digest=sha(p)
        if digest!=asset['digest'][7:] or s.st_size!=asset['size']:
            raise ValueError('Actual local bytes differ from current remote digest: '+str(p))
        row={'path':str(p),'relative_path':p.relative_to(ROOT).as_posix(),'bytes':s.st_size,
             'mtime_ns':s.st_mtime_ns,'sha256':digest,'release_tag':TAGS[group],
             'remote_asset_id':asset['id'],'remote_url':asset['browser_download_url'],
             'remote_digest':asset['digest'],'current_remote_sha256_equal':True,
             'retained_publication_receipt':receipt_pins[group]}
        if p.suffix=='.zip':
            retained=receipt_assets[group].get(p.name)
            if not retained or retained['sha256']!=digest or retained['bytes']!=s.st_size \
               or retained.get('download_readback_verified') is not True \
               or retained.get('all_zip_member_hashes_verified') is not True:
                raise ValueError('Retained exact-asset publication/readback evidence differs')
            with zipfile.ZipFile(p) as z:
                infos=z.infolist(); names=[item.filename for item in infos]
                if len(set(names))!=len(names) or 'SHA256SUMS.txt' not in names or 'README.txt' not in names:
                    raise ValueError('ZIP duplicate or missing checksum/README')
                for info in infos:
                    name=info.filename; pure=PurePosixPath(name)
                    if info.is_dir() or pure.is_absolute() or pure.as_posix()!=name or '..' in pure.parts \
                       or '\\' in name or ':' in name or stat.S_ISLNK(info.external_attr>>16):
                        raise ValueError('Nonportable ZIP member: '+name)
                sums=z.read('SHA256SUMS.txt'); checks={}
                for line in sums.decode('utf-8').splitlines():
                    match=re.fullmatch('([a-f0-9]{64})  (.+)',line)
                    if not match or match[2] in checks: raise ValueError('Malformed/duplicate internal SHA manifest')
                    checks[match[2]]=match[1]
                if set(checks)!=set(names)-{'SHA256SUMS.txt'}: raise ValueError('Internal SHA manifest does not cover exact member set')
                for info in infos:
                    h=hashlib.sha256(); count=0
                    with z.open(info) as stream:
                        # Exhaustion invokes ZipExtFile's CRC check, including the manifest.
                        for block in iter(lambda:stream.read(1024*1024),b''):
                            h.update(block); count+=len(block)
                    if count!=info.file_size or (info.filename!='SHA256SUMS.txt' and h.hexdigest()!=checks[info.filename]):
                        raise ValueError('Actual ZIP member SHA/size differs: '+info.filename)
                    details.write(json.dumps({'archive_relative_path':row['relative_path'],
                        'member':info.filename,'bytes':count,'sha256':h.hexdigest(),
                        'crc32':format(info.CRC,'08x'),'crc_verified':True,
                        'internal_sha256_verified':info.filename!='SHA256SUMS.txt'},sort_keys=True)+'\n')
                row.update(zip_validation='PASS_ALL_MEMBER_CRC_AND_INTERNAL_SHA256',
                    zip_members=len(infos),payload_members=len(checks),
                    zip_uncompressed_bytes=sum(i.file_size for i in infos),
                    internal_manifest_sha256=hashlib.sha256(sums).hexdigest())
                members_count+=len(infos); unpacked_bytes+=row['zip_uncompressed_bytes']
        else:
            match=re.fullmatch('([a-f0-9]{64})  ([^\r\n]+)\r?\n?',p.read_text(encoding='utf-8'))
            target=p.name[:-7]
            remote_zip=before[group]['assets'].get(target)
            if not match or match[2]!=target or not remote_zip or match[1]!=remote_zip['digest'][7:]:
                raise ValueError('Sidecar content does not bind exact published ZIP')
            row.update(sidecar_validation='PASS_REMOTE_DIGEST_AND_EXACT_ZIP_HASH_LINE',zip_name=target)
        after=p.stat()
        if (s.st_size,s.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise ValueError('File changed during read: '+str(p))
        records.append(row)
        print(json.dumps({'verified':index,'of':len(selected),'file':row['relative_path'],'bytes':row['bytes']}),flush=True)

after=observe(); save('remote_assets_after.json',{'utc':utc(),'releases':after})
if before!=after: raise ValueError('Remote asset identity/digest changed during verification')
save('file_allowlist.json',{'schema':'LAB_RM_EXACT_RELEASE_DUPLICATE_CLEANUP_CANDIDATE_V1',
    'state':'VERIFIED_CANDIDATE_NO_CLEANUP_EXECUTED','root':str(ROOT),'files':records,
    'protected':'No active toolchain/lock/controller/source/.work/input/private paths selected.',
    'delete_semantics':'Only individually listed exact files; never recursive-delete release_staging or stage directories.',
    'predelete_required':'Root commits this receipt remotely, confirms recoverable remote asset digests and exact local hashes/identity, excludes active handles, then records bounded cleanup.'})
summary={'schema':'LAB_RM_RELEASE_STAGING_DUPLICATE_VERIFICATION_V1',
    'status':'PASS_CURRENT_REMOTE_SHA256_AND_ALL_LOCAL_ZIP_MEMBERS',
    'started_utc':started,'completed_utc':utc(),'files':len(records),
    'bytes':sum(r['bytes'] for r in records),'zip_copies':sum(r['path'].endswith('.zip') for r in records),
    'distinct_zip_assets':len({r['remote_asset_id'] for r in records if r['path'].endswith('.zip')}),
    'sidecar_copies':sum(r['path'].endswith('.sha256') for r in records),
    'zip_members_streamed':members_count,'uncompressed_bytes_streamed':unpacked_bytes,
    'remote_asset_identity_unchanged_before_after':True,'asset_downloads':0,
    'large_ext4_image_read':False,'actual_cleanup':'NOT_RUN','actual_archive_rebuild':'NOT_RUN',
    'source_receipts':receipt_pins,'scientific_status_changes':False,
    'script_sha256':sha(Path(__file__))}
save('summary.json',summary)
save('evidence_sha256.json',{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}
    for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='evidence_sha256.json'})
print(json.dumps(summary,indent=2),flush=True)
