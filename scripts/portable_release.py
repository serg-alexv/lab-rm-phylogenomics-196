"""Deterministic portable ZIP payloads and resumable verified GitHub publication.

The immutable payload manifest and commit are frozen before uploading. Mutable
publication plans/receipts live separately; retries reuse the frozen ZIP bytes.
"""
from pathlib import Path, PurePosixPath
import hashlib,json,os,subprocess,zipfile
import production_resume as w
from workflow_publication import commit

def hash_stream(stream):
    h=hashlib.sha256()
    for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:
            raise ValueError('Duplicate ZIP names or failed CRC')
        for name in names:
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe ZIP name: '+name)
            if (z.getinfo(name).external_attr>>16)&0o170000==0o120000:
                raise ValueError('ZIP symlink forbidden')
        checks={}
        for line in z.read('SHA256SUMS.txt').decode('utf-8').splitlines():
            h,name=line.split('  ',1)
            if name in checks or len(h)!=64: raise ValueError('Invalid checksum entry')
            checks[name]=h
        if set(checks)!=set(names)-{'SHA256SUMS.txt'}:
            raise ValueError('Checksum manifest does not cover every payload member')
        for name,h in checks.items():
            with z.open(name) as stream:
                if hash_stream(stream)!=h: raise ValueError('ZIP member SHA256 mismatch: '+name)
    return len(checks)

def make_zip(destination,files,guide):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    sources=sorted([(Path(p),n) for p,n in files],key=lambda x:x[1])
    names=[n for _,n in sources]+['README.txt','SHA256SUMS.txt']
    if len(names)!=len(set(names)): raise ValueError('Duplicate/reserved ZIP member')
    tmp=destination.with_suffix('.zip.partial')
    hashes=[]
    def info(name):
        i=zipfile.ZipInfo(name,date_time=(2026,10,8,0,0,0))
        i.create_system=0;i.external_attr=0x20;i.compress_type=zipfile.ZIP_DEFLATED
        return i
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p,n in sources:
            if not p.is_file() or p.is_symlink(): raise ValueError('Missing/nonportable ZIP source')
            h=hashlib.sha256()
            with p.open('rb') as src,z.open(info(n),'w',force_zip64=True) as dst:
                for block in iter(lambda:src.read(1024*1024),b''):
                    h.update(block);dst.write(block)
            hashes.append((h.hexdigest(),n))
        b=guide.encode('utf-8');z.writestr(info('README.txt'),b)
        hashes.append((hashlib.sha256(b).hexdigest(),'README.txt'))
        z.writestr(info('SHA256SUMS.txt'),''.join(h+'  '+n+'\n' for h,n in hashes).encode('utf-8'))
    if tmp.stat().st_size>=500*1024**2: raise ValueError('Split ZIP into batches below500MiB')
    count=verify_zip(tmp);os.replace(tmp,destination)
    h=w.digest(destination)
    w.atomic(destination.with_suffix('.zip.sha256'),(h+'  '+destination.name+'\n').encode())
    return {'asset_name':destination.name,'bytes':destination.stat().st_size,'sha256':h,'payload_members':count}

def publish_frozen(stage,tag,staging,manifest_path,payload_paths,title,notes_path):
    """Run under the workflow lock. Existing plan means no payload regeneration."""
    staging=Path(staging);manifest_path=Path(manifest_path)
    plan_path=w.R/'status'/(stage+'_publication_plan.json')
    manifest_sha=w.digest(manifest_path)
    assets=json.loads(manifest_path.read_text())['assets']
    if plan_path.exists():
        plan=json.loads(plan_path.read_text())
        if plan['manifest_sha256']!=manifest_sha or plan['tag']!=tag or plan['assets']!=assets:
            raise ValueError('Existing immutable publication plan differs; preserve old payload')
        head=plan['payload_commit']
    else:
        head=commit(payload_paths,'Freeze '+stage+' validated portable payloads')
        plan={'stage':stage,'tag':tag,'payload_commit':head,'manifest_path':manifest_path.relative_to(w.R).as_posix(),
              'manifest_sha256':manifest_sha,'assets':assets,'frozen_utc':w.now()}
        w.js(plan_path,plan)
        commit([plan_path.relative_to(w.R).as_posix()],'Record '+stage+' immutable publication restart plan')
    frozen=w.run(['git','show',head+':'+plan['manifest_path']])
    if json.loads(frozen)!=json.loads(manifest_path.read_text()): raise ValueError('Frozen Git manifest mismatch')
    for asset in assets:
        p=staging/asset['asset_name']
        if p.stat().st_size!=asset['bytes'] or w.digest(p)!=asset['sha256']:
            raise ValueError('Frozen local ZIP changed')
        verify_zip(p)
        side=p.with_suffix('.zip.sha256');expected=(asset['sha256']+'  '+p.name+'\n').encode()
        if not side.exists():w.atomic(side,expected)
        if side.read_bytes()!=expected:raise ValueError('Frozen sidecar mismatch')
    present=subprocess.run(['gh','release','view',tag,'--repo',w.REPO],capture_output=True).returncode==0
    if not present:
        w.run(['gh','release','create',tag,'--repo',w.REPO,'--target',head,'--title',title,'--notes-file',str(notes_path)],timeout=300)
    if w.run(['gh','api','repos/'+w.REPO+'/commits/'+tag,'--jq','.sha']).strip()!=head:
        raise ValueError('Release tag differs from immutable payload commit')
    readback=staging/'readback';readback.mkdir(exist_ok=True)
    receipts=[]
    for asset in assets:
        p=staging/asset['asset_name'];side=p.with_suffix('.zip.sha256')
        for local in (p,side):
            info=json.loads(w.run(['gh','api','repos/'+w.REPO+'/releases/tags/'+tag]))
            existing={a['name']:a for a in info['assets']}
            if local.name not in existing:
                w.run(['gh','release','upload',tag,str(local),'--repo',w.REPO],timeout=1800)
                info=json.loads(w.run(['gh','api','repos/'+w.REPO+'/releases/tags/'+tag]))
                existing={a['name']:a for a in info['assets']}
            a=existing[local.name];h=w.digest(local)
            if a['size']!=local.stat().st_size or (a.get('digest') and a['digest']!='sha256:'+h):
                raise ValueError('Remote existing asset differs: '+local.name)
            w.run(['gh','release','download',tag,'--repo',w.REPO,'--pattern',local.name,'--dir',str(readback),'--clobber'],timeout=1800)
            if w.digest(readback/local.name)!=h:raise ValueError('Downloaded asset differs: '+local.name)
        verify_zip(readback/p.name)
        receipts.append({**asset,'download_readback_verified':True,'all_zip_member_hashes_verified':True,'sidecar_readback_verified':True})
        print('UPLOAD_READBACK_VERIFIED',p.name,flush=True)
    return {'status':'UPLOAD_VERIFIED','utc':w.now(),'release_tag':tag,'url':info['html_url'],
            'payload_commit':head,'remote_tag_commit_verified':True,'assets':receipts}
