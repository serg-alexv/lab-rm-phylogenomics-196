"""Deterministic portable ZIP payloads and resumable verified GitHub publication.

The immutable payload manifest and commit are frozen before uploading. Mutable
publication plans/receipts live separately; retries reuse the frozen ZIP bytes.
"""
from pathlib import Path, PurePosixPath
import hashlib,json,os,re,subprocess,unicodedata,zipfile
import production_resume as w
from workflow_publication import commit

def hash_stream(stream):
    h=hashlib.sha256()
    for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def validate_member_names(names):
    """Reject aliases and invalid paths under normal Windows extraction rules."""
    normalized=set();directories=set();literal_paths={}
    reserved={'con','prn','aux','nul','clock$'}
    reserved.update('com'+n for n in '123456789¹²³')
    reserved.update('lpt'+n for n in '123456789¹²³')
    for name in names:
        p=PurePosixPath(name)
        if not name or p.is_absolute() or p.as_posix()!=name or name.endswith('/'):
            raise ValueError('Noncanonical/file ZIP member name: '+name)
        parts=p.parts
        for c in parts:
            if c in ('.','..') or c.endswith(('.', ' ')) or any(ord(x)<32 for x in c) or re.search(r'[<>:"\\|?*]',c):
                raise ValueError('Invalid Windows ZIP path component: '+name)
            if unicodedata.normalize('NFC',c)!=c or c.split('.')[0].casefold() in reserved:
                raise ValueError('Ambiguous/reserved Windows ZIP path: '+name)
        key='/'.join(c.casefold() for c in parts)
        for i in range(1,len(parts)+1):
            literal='/'.join(parts[:i]);alias=literal.casefold()
            if alias in literal_paths and literal_paths[alias]!=literal:
                raise ValueError('Windows ZIP directory/name spelling collision: '+name)
            literal_paths[alias]=literal
        if key in normalized or key in directories:
            raise ValueError('Windows ZIP extraction path collision: '+name)
        prefixes=['/'.join(c.casefold() for c in parts[:i]) for i in range(1,len(parts))]
        if any(k in normalized for k in prefixes):
            raise ValueError('ZIP file/directory path collision: '+name)
        normalized.add(key);directories.update(prefixes)

def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        validate_member_names(names)
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
    validate_member_names(names)
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

def validate_asset_manifest(assets):
    if not isinstance(assets,list) or not assets:raise ValueError('Expected a nonempty ZIP asset list')
    names=[]
    for a in assets:
        name=a.get('asset_name')
        if not isinstance(name,str) or len(PurePosixPath(name).parts)!=1 or not name.endswith('.zip'):
            raise ValueError('Expected one safe ZIP asset basename')
        names.append(name)
        if type(a.get('bytes')) is not int or not 0<a['bytes']<500*1024**2:
            raise ValueError('Invalid ZIP asset byte count')
        if type(a.get('payload_members')) is not int or a['payload_members']<=0:
            raise ValueError('Invalid ZIP payload member count')
        if not isinstance(a.get('sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',a['sha256']):
            raise ValueError('Invalid ZIP asset SHA256')
    validate_member_names(names)

def publish_frozen(stage,tag,staging,manifest_path,payload_paths,title,notes_path):
    """Run under the workflow lock. Existing plan means no payload regeneration."""
    staging=Path(staging);manifest_path=Path(manifest_path)
    plan_path=w.R/'status'/(stage+'_publication_plan.json')
    manifest_sha=w.digest(manifest_path)
    assets=json.loads(manifest_path.read_text())['assets']
    validate_asset_manifest(assets)
    # Check every declaration before a Git/Release mutation can freeze false data.
    for asset in assets:
        p=staging/asset['asset_name']
        if p.stat().st_size!=asset['bytes'] or w.digest(p)!=asset['sha256']:
            raise ValueError('Frozen local ZIP differs from declared bytes/hash')
        if verify_zip(p)!=asset['payload_members']:
            raise ValueError('Declared ZIP member count differs from payload')
    if plan_path.exists():
        plan=json.loads(plan_path.read_text())
        if plan['manifest_sha256']!=manifest_sha or plan['tag']!=tag or plan['assets']!=assets:
            raise ValueError('Existing immutable publication plan differs; preserve old payload')
        head=plan['payload_commit']
        # A prior push failure can leave a valid local plan untracked/unpublished.
        commit([plan_path.relative_to(w.R).as_posix()],'Verify '+stage+' immutable publication restart plan')
    else:
        head=commit(payload_paths,'Freeze '+stage+' validated portable payloads')
        plan={'stage':stage,'tag':tag,'payload_commit':head,'manifest_path':manifest_path.relative_to(w.R).as_posix(),
              'manifest_sha256':manifest_sha,'assets':assets,'frozen_utc':w.now()}
        w.js(plan_path,plan)
        commit([plan_path.relative_to(w.R).as_posix()],'Record '+stage+' immutable publication restart plan')
    frozen=w.run(['git','show',head+':'+plan['manifest_path']])
    if hashlib.sha256(frozen.encode('utf-8')).hexdigest()!=manifest_sha:
        raise ValueError('Frozen Git manifest bytes mismatch')
    for asset in assets:
        p=staging/asset['asset_name']
        if p.stat().st_size!=asset['bytes'] or w.digest(p)!=asset['sha256']:
            raise ValueError('Frozen local ZIP changed')
        side=p.with_suffix('.zip.sha256');expected=(asset['sha256']+'  '+p.name+'\n').encode()
        if not side.exists():w.atomic(side,expected)
        if side.read_bytes()!=expected:raise ValueError('Frozen sidecar mismatch')
    present=subprocess.run(['gh','release','view',tag,'--repo',w.REPO],capture_output=True).returncode==0
    if not present:
        w.run(['gh','release','create',tag,'--repo',w.REPO,'--target',head,'--title',title,'--notes-file',str(notes_path)],timeout=300)
    if w.run(['gh','api','repos/'+w.REPO+'/commits/'+tag,'--jq','.sha']).strip()!=head:
        raise ValueError('Release tag differs from immutable payload commit')
    readback=staging/'readback';readback.mkdir(exist_ok=True)
    progress_path=w.R/'reports'/stage/'publication_progress.json'
    historical_cache={};cache={}
    if progress_path.exists():
        previous=json.loads(progress_path.read_text())
        if previous.get('payload_commit')==head and previous.get('manifest_sha256')==manifest_sha:
            historical_cache=previous.get('verified_assets',{})
    # Progress counts only assets verified during this attempt; prior evidence is
    # a cache lookup, never current completion before the remote API is checked.
    w.js(progress_path,{'payload_commit':head,'manifest_sha256':manifest_sha,'verified_assets':{},
                        'required_files':2*len(assets),'verified_files':0,'complete':False})
    receipts=[]
    for asset in assets:
        p=staging/asset['asset_name'];side=p.with_suffix('.zip.sha256')
        for local in (p,side):
            h=w.digest(local)
            expected_hash=asset['sha256'] if local==p else hashlib.sha256((asset['sha256']+'  '+p.name+'\n').encode()).hexdigest()
            if h!=expected_hash:raise ValueError('Local frozen asset changed during publication')
            info=json.loads(w.run(['gh','api','repos/'+w.REPO+'/releases/tags/'+tag]))
            existing={a['name']:a for a in info['assets']}
            if local.name not in existing:
                w.run(['gh','release','upload',tag,str(local),'--repo',w.REPO],timeout=1800)
                info=json.loads(w.run(['gh','api','repos/'+w.REPO+'/releases/tags/'+tag]))
                existing={a['name']:a for a in info['assets']}
            a=existing[local.name]
            if a['size']!=local.stat().st_size or (a.get('digest') and a['digest']!='sha256:'+h):
                raise ValueError('Remote existing asset differs: '+local.name)
            prior=historical_cache.get(local.name,{})
            cached=readback/local.name
            reusable=(a.get('digest')=='sha256:'+h and prior.get('remote_asset_id')==a['id']
                      and prior.get('sha256')==h and prior.get('bytes')==a['size']
                      and prior.get('download_readback_verified') is True and cached.is_file()
                      and cached.stat().st_size==a['size'] and w.digest(cached)==h)
            if not reusable:
                w.run(['gh','release','download',tag,'--repo',w.REPO,'--pattern',local.name,'--dir',str(readback),'--clobber'],timeout=1800)
            if w.digest(readback/local.name)!=h:raise ValueError('Downloaded asset differs: '+local.name)
            if local==p and verify_zip(readback/local.name)!=asset['payload_members']:
                raise ValueError('Readback ZIP member count differs from manifest')
            cache[local.name]={'remote_asset_id':a['id'],'sha256':h,'bytes':a['size'],
                              'download_readback_verified':True,'all_zip_member_hashes_verified':local==p,
                              'utc':w.now()}
            w.js(progress_path,{'payload_commit':head,'manifest_sha256':manifest_sha,'verified_assets':cache,
                                'required_files':2*len(assets),'verified_files':len(cache),'complete':len(cache)==2*len(assets)})
        receipts.append({**asset,'download_readback_verified':True,'all_zip_member_hashes_verified':True,'sidecar_readback_verified':True})
        print('UPLOAD_READBACK_VERIFIED',p.name,flush=True)
    return {'status':'UPLOAD_VERIFIED','utc':w.now(),'release_tag':tag,'url':info['html_url'],
            'payload_commit':head,'remote_tag_commit_verified':True,'assets':receipts}
