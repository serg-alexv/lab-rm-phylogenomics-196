"""Independent retained-public-component readback; never extract or execute payloads.

Common readback primitives are also used by the separately pinned history02 verifier.
Local mode certifies local archive bytes only. No source deletion authority is given.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse, base64, collections, datetime, hashlib, json, re, stat, subprocess
import sys, tarfile, unicodedata, uuid
from urllib.parse import urlsplit
import zipfile

WORK = Path(__file__).resolve().parent
REPO = 'serg-alexv/lab-rm-phylogenomics-196'
PREFIX = 'reports/master_run/20261009/cleanup/components01/'
EXE_SHA = '43c9bf3b0dc5e7d88c183a2582369d22c9d692b7585350038769334bb6fd9aed'
ASSETS = [{'name':'master_public_components01.zip','bytes':228162511,
    'sha256':'4663ddfb3e204bff5d0ba6f218717eae28ddd56bf4c51d325bb2b0db240dca35'}]
# These independent expected pins must not be inferred from downloaded bytes.
CONTROL_HASHES = {
    'build_receipt.json':'cbc1797cf692c88a8366244731575cd994352568d4a9e4bf610ac9c8d0734fe7',
    'source_binding.json':'89a1035594d340bbb52513ee852e5fe547d3803921ba8e00192b2ecf728f1038',
    'original_source_manifest.json':'ebb682c7e5e95ba8bb2b8b5ed1f090a0b4aa4e23297c083bfbbc1935b40f540a',
    'component_source_map.json':'776e5d432a6b76855036c23cfed52c5e8d1c2152930e3c5f49bccc28402937b6',
    'README.txt':'04bfac5bcd27be70dc6ceb36ef06a39a6662386784694596e72f1dcd6431bfdd',
    'SHA256SUMS.txt':'aa0f7ac6c8cef21895a504ca9f6e3e87d1f22f1f2a36120d18a08104f69b8bf1'}
CODE_HASHES = {'build_master_public_components01.py':'352f8fd6e7b1419a923d89b162b7bdad11b8e161f45f0ec83c0a7b285a5fc4a6'}

def require(value, message):
    if not value: raise ValueError(message)

def sha(data): return hashlib.sha256(data).hexdigest()
def digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def is_sha(value): return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None
def run(argv, timeout=90):
    return subprocess.run(argv, capture_output=True, check=True, timeout=timeout).stdout
def api(endpoint): return json.loads(run(['gh','api','repos/'+REPO+'/'+endpoint]))

def safe_names(names):
    require(len(names)==len(set(names)), 'Duplicate literal ZIP names')
    files, dirs, spelling = set(), set(), {}
    reserved = {'con','prn','aux','nul','clock$'} | {p+n for p in ('com','lpt') for n in '123456789¹²³'}
    for name in names:
        p = PurePosixPath(name)
        require(name and not p.is_absolute() and p.as_posix()==name and not name.endswith('/'), 'Noncanonical ZIP name')
        for part in p.parts:
            require(part not in ('.','..') and not part.endswith(('.', ' '))
                and not any(ord(c)<32 or ord(c)==127 for c in part)
                and re.search(r'[<>:"\\|?*]',part) is None
                and unicodedata.normalize('NFC',part)==part
                and part.split('.')[0].casefold() not in reserved, 'Unsafe Windows ZIP component')
        key=name.casefold(); prefixes=['/'.join(p.parts[:i]).casefold() for i in range(1,len(p.parts))]
        require(key not in files and key not in dirs and not any(x in files for x in prefixes), 'ZIP alias/file-directory collision')
        for i in range(1,len(p.parts)+1):
            literal='/'.join(p.parts[:i]); folded=literal.casefold()
            require(folded not in spelling or spelling[folded]==literal, 'ZIP spelling alias')
            spelling[folded]=literal
        files.add(key); dirs.update(prefixes)

def verify_zip(path, asset, expected_members):
    require(path.stat().st_size==asset['bytes'] and digest(path)==asset['sha256'], 'Outer archive size/SHA differs')
    z=zipfile.ZipFile(path)
    try:
        names=z.namelist(); safe_names(names)
        require(len(names)==len(expected_members) and set(names)==set(expected_members), 'Exact archive membership differs')
        require(sum(i.file_size for i in z.infolist())==sum(r['bytes'] for r in expected_members.values()), 'Uncompressed byte bound differs')
        checks={}
        for line in z.read('SHA256SUMS.txt').decode('utf-8').splitlines():
            m=re.fullmatch(r'([a-f0-9]{64})  (.+)',line)
            require(m is not None and m[2] not in checks, 'Invalid/duplicate SHA256SUMS row')
            checks[m[2]]=m[1]
        require(set(checks)==set(names)-{'SHA256SUMS.txt'}, 'SHA256SUMS is not exhaustive')
        observed={}
        for i in z.infolist():
            require(not i.is_dir() and stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG)
                and not(i.flag_bits&1) and i.date_time==(2026,10,9,0,0,0), 'Nonregular/encrypted/nondeterministic entry')
            with z.open(i) as stream: actual=hashlib.file_digest(stream,'sha256').hexdigest()
            expected=expected_members[i.filename]
            require(actual==expected['sha256'] and i.file_size==expected['bytes'] and f'{i.CRC:08x}'==expected['crc32']
                and expected['crc_verified'] is True, 'Build receipt/member bytes differ: '+i.filename)
            require(i.filename=='SHA256SUMS.txt' or actual==checks[i.filename], 'Internal SUMS differs: '+i.filename)
            observed[i.filename]=dict(member=i.filename,bytes=i.file_size,sha256=actual,crc32=f'{i.CRC:08x}',
                crc_verified=True,internal_sha256_manifest_covered=i.filename in checks)
        return z,observed
    except BaseException:
        z.close(); raise

def member_table(rows):
    require(isinstance(rows,list) and all(set(r)=={'member','bytes','sha256','crc32','crc_verified'}
        and type(r['bytes']) is int and r['bytes']>=0 and is_sha(r['sha256'])
        and re.fullmatch('[a-f0-9]{8}',r['crc32']) for r in rows), 'Invalid expected member table')
    table={r['member']:r for r in rows}; require(len(table)==len(rows), 'Duplicate expected member')
    return table

def bind_inputs(table, observed):
    for name,row in table.items():
        require(set(row)=={'bytes','sha256'} and type(row['bytes']) is int and row['bytes']>=0 and is_sha(row['sha256'])
            and name in observed and observed[name]['bytes']==row['bytes'] and observed[name]['sha256']==row['sha256'],
            'Captured source input differs: '+name)

def get_controls(args, hashes, code_hashes, prefix, local_dir, out, result, extras=None):
    paths={prefix+n:(local_dir/n,h) for n,h in hashes.items()}
    paths.update({'scripts/master_run/'+n:(WORK/n,h) for n,h in code_hashes.items()})
    if extras: paths.update(extras)
    remote={}; values={}
    if not args.local_inspect:
        tree=api('git/trees/'+args.source_commit+'?recursive=1')
        require(tree['truncated'] is False, 'Published source tree truncated')
        remote={r['path']:r for r in tree['tree'] if r['type']=='blob'}
    records=[]; control_dir=out/'published_controls'; control_dir.mkdir()
    for index,(path,(local,expected)) in enumerate(paths.items()):
        if args.local_inspect: data=local.read_bytes(); object_sha=None
        else:
            require(path in remote and remote[path].get('size',0)<5*1024**2, 'Missing/oversized published control: '+path)
            object_sha=remote[path]['sha']; blob=api('git/blobs/'+object_sha)
            require(blob['encoding']=='base64', 'Unexpected Git blob encoding')
            data=base64.b64decode(blob['content'],validate=False)
            require(len(data)==remote[path]['size']==blob['size']
                and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==object_sha, 'Actual Git blob/size differs')
        require(len(data)<5*1024**2 and sha(data)==expected, 'Published/captured control SHA differs: '+path)
        with (control_dir/(str(index).zfill(2)+'_'+PurePosixPath(path).name)).open('xb') as stream: stream.write(data)
        values[path]=data
        records.append(dict(path=path,commit=args.source_commit,remote_blob=object_sha,bytes=len(data),sha256=sha(data),
            actual_remote_bytes_read=not args.local_inspect))
    result['authoritative_control_readback']=records
    return values

def begin_release(args, assets, out, result):
    require(api('commits/'+args.tag)['sha']==args.expected_tag_commit, 'Release tag target differs')
    release=api('releases/tags/'+args.tag)
    require(release['tag_name']==args.tag and release['draft'] is False, 'Release identity/draft differs')
    expected=[]
    for row in assets:
        side=(row['sha256']+'  '+row['name']+'\n').encode()
        expected.extend([row,dict(name=row['name']+'.sha256',bytes=len(side),sha256=sha(side))])
    selected={}
    for row in expected:
        matches=[a for a in release['assets'] if a['name']==row['name']]
        require(len(matches)==1, 'Missing/duplicate Release asset: '+row['name'])
        a=matches[0]
        require(a['state']=='uploaded' and a['size']==row['bytes'] and a['digest']=='sha256:'+row['sha256'], 'Fresh Release size/digest differs')
        selected[row['name']]=a
    result.update(tag=args.tag,expected_tag_commit=args.expected_tag_commit,source_commit=args.source_commit,
        release_url=release['html_url'],release_id=release['id'])
    for row in assets:
        run(['gh','release','download',args.tag,'--repo',REPO,'--pattern',row['name'],
            '--pattern',row['name']+'.sha256','--dir',str(out)],timeout=300)
        require((out/(row['name']+'.sha256')).read_bytes()==(row['sha256']+'  '+row['name']+'\n').encode(), 'Downloaded sidecar differs')
    result['downloaded_assets']=[dict(name=r['name'],remote_asset_id=selected[r['name']]['id'],
        bytes=(out/r['name']).stat().st_size,sha256=digest(out/r['name']),remote_digest=selected[r['name']]['digest']) for r in expected]
    require(all(r['sha256']==next(e['sha256'] for e in expected if e['name']==r['name'])
        and r['bytes']==next(e['bytes'] for e in expected if e['name']==r['name']) for r in result['downloaded_assets']), 'Actual downloaded asset differs')
    return release,selected

def end_release(args, release, selected, result):
    require(api('commits/'+args.tag)['sha']==args.expected_tag_commit, 'Release tag changed')
    final=api('releases/tags/'+args.tag)
    require(final['id']==release['id'] and final['tag_name']==args.tag and final['draft'] is False, 'Release changed')
    for name,before in selected.items():
        matches=[a for a in final['assets'] if a['name']==name]
        require(len(matches)==1 and all(matches[0][k]==before[k] for k in ('id','size','digest','state')), 'Asset identity changed during readback')
    result['release_tag_and_assets_unchanged_before_after']=True

def cli(description):
    p=argparse.ArgumentParser(description=description)
    p.add_argument('--local-inspect',action='store_true')
    p.add_argument('--tag',default='master-run-storage-20261009-v1')
    p.add_argument('--expected-tag-commit',default='46c7089f906cce59afabaa4449b05df36ee124de')
    p.add_argument('--source-commit')
    a=p.parse_args()
    require(a.local_inspect or (a.source_commit and re.fullmatch('[a-f0-9]{40}',a.source_commit)), 'Immutable --source-commit required')
    require(re.fullmatch('[a-f0-9]{40}',a.expected_tag_commit) is not None, 'Invalid expected tag commit')
    return a

def execute_readback(args, kind, body):
    out=WORK/(kind+'_readback_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    out.mkdir(exist_ok=False); receipt=out/'receipt.json'
    result=dict(schema='MASTER_'+kind.upper()+'_INDEPENDENT_READBACK_V1',state='STARTED',started_utc=utc(),
        verifier_source_sha256=digest(sys.argv[0]),mode='LOCAL_INSPECTION' if args.local_inspect else 'FRESH_REMOTE',
        biological_acceptance='NONE_RECOVERY_PRESERVATION_ONLY',source_deletions=0,wsl_starts=0,g_writes=0,
        payload_execution=0,cleanup_authority='NONE_REQUIRES_SEPARATE_LIVE_EXACT_LEAF_GATE')
    try: body(args,out,result)
    except BaseException as error:
        result.update(state='FAILED_READBACK_NO_CLEANUP_AUTHORITY',error=dict(kind=type(error).__name__,message=str(error)))
        raise
    finally:
        result['finished_utc']=utc()
        with receipt.open('x',encoding='utf-8',newline='\n') as stream: json.dump(result,stream,indent=2,sort_keys=True); stream.write('\n')
        print(json.dumps(dict(state=result['state'],receipt=str(receipt)),indent=2))

def verify_components(args,out,result):
    controls=get_controls(args,CONTROL_HASHES,CODE_HASHES,PREFIX,WORK/'master_public_components01',out,result)
    read=lambda n:json.loads(controls[PREFIX+n])
    build,binding,manifest,source_map=(read(n) for n in ('build_receipt.json','source_binding.json','original_source_manifest.json','component_source_map.json'))
    require(build['schema']=='MASTER_PUBLIC_COMPONENTS_LOCAL_BUILD_V1' and build['zip_members']==29
        and build['source_files']==17 and build['source_bytes']==244870939 and build['payload_members']==28
        and build['sha256']==ASSETS[0]['sha256'] and build['bytes']==ASSETS[0]['bytes'], 'Components build contract differs')
    for key in ('source_manifest_sha256','source_binding_sha256','component_source_map_sha256'):
        name={'source_manifest_sha256':'original_source_manifest.json','source_binding_sha256':'source_binding.json',
            'component_source_map_sha256':'component_source_map.json'}[key]
        require(build[key]==CONTROL_HASHES[name], 'Components cross-control pin differs')
    require(manifest['schema']=='MASTER_PUBLIC_COMPONENT_ORIGINAL_SOURCE_MANIFEST_V1'
        and manifest['source_files']==len(manifest['files'])==17 and manifest['image_excluded'] is True
        and manifest['private_or_unrelated_inputs_selected'] is False and manifest['original_tools_modified'] is False,
        'Original source scope differs')
    require(binding['schema']=='MASTER_PUBLIC_COMPONENT_SOURCE_BINDING_V1' and binding['original_sources']==17
        and binding['original_live_exe_pin']==EXE_SHA and binding['source_original_identity_hash_stability_verified'] is True,
        'Source binding differs')
    for key in ('standalone_intel_runtime_notice_gap','full_iqtree_corresponding_source_not_in_selected_inputs'):
        require(binding[key] is True and build[key] is True, 'Notice/source limitation silently removed')
    require(source_map['schema']=='MASTER_PUBLIC_COMPONENT_ATTRIBUTION_MAP_V1'
        and source_map['package_artifacts_included'] is False and source_map['installed_toolchain_image_included'] is False
        and source_map['notices_preserved_unchanged'] is True and len(source_map['components'])==3
        and source_map['iqtree']['exe_sha256']==EXE_SHA
        and source_map['iqtree']['full_corresponding_source_archive_included'] is False
        and source_map['iqtree']['standalone_intel_runtime_license_in_retained_distribution'] is False, 'Attribution coverage differs')
    release=selected=None
    if not args.local_inspect: release,selected=begin_release(args,ASSETS,out,result)
    archive=(WORK/'master_public_components01' if args.local_inspect else out)/ASSETS[0]['name']
    z,observed=verify_zip(archive,ASSETS[0],member_table(build['members']))
    with z:
        for n in ('source_binding.json','original_source_manifest.json','component_source_map.json'):
            require(z.read('control/'+n)==controls[PREFIX+n], 'Outer versus archived control differs: '+n)
        for n in ('README.txt','SHA256SUMS.txt'):
            require(z.read(n)==controls[PREFIX+n], 'Outer versus archive text differs')
        require(set(observed)==set(binding['payload_inputs'])|{'control/source_binding.json','SHA256SUMS.txt'}, 'Exhaustive source binding differs')
        bind_inputs(binding['payload_inputs'],observed)
        originals={r['member']:r for r in manifest['files']}
        require(len(originals)==17 and sum(r['bytes'] for r in originals.values())==244870939, '17 original byte join differs')
        for name,row in originals.items():
            require(observed[name]['sha256']==row['sha256'] and observed[name]['bytes']==row['bytes']
                and row['source_identity']['bytes']==row['bytes']
                and row['source_handle_share']=='READ_ONLY_DENY_WRITES_AND_DELETE_DURING_CAPTURE'
                and (row['known_sha256_pin'] is None or row['known_sha256_pin']==row['sha256']), 'Original identity/pin differs')
        require(observed['native/iqtree-3.1.4-Windows/bin/iqtree3.exe']['sha256']==EXE_SHA, 'Live native exe pin differs')
        packages=[]
        for n,count in [('detector_package_manifest.json',255),('host_package_manifest.json',142)]:
            rows=json.loads(z.read('manifests/'+n))['packages']; require(len(rows)==count, 'Package record count differs')
            for row in rows:
                u=urlsplit(row['url'])
                require(u.scheme=='https' and u.hostname=='conda.anaconda.org' and not u.username and not u.password
                    and not u.query and not u.fragment and is_sha(row['sha256']) and row['license'], 'Public package source/license pin differs')
            packages.extend(rows)
        require(len({r['sha256'] for r in packages})==source_map['distinct_original_package_sha256']==339
            and len(packages)==source_map['original_package_records']==397, 'Package provenance accounting differs')
        notice_rows=[]
        for component in source_map['components']:
            n=component['source_archive_member']; require(observed[n]['sha256']==component['source_archive_sha256'], 'Model archive pin differs')
            count=0; found={}; wanted={r['original_tar_member']:r for r in component['original_notices'].values()}
            # Streaming through retained source archives; no extraction or native execution.
            with z.open(n) as raw,tarfile.open(fileobj=raw,mode='r|gz') as tar:
                for entry in tar:
                    count+=1
                    require(entry.name==component['embedded_source_root'] or entry.name.startswith(component['embedded_source_root']+'/'), 'Declared archive source root differs')
                    if entry.name in wanted:
                        row=wanted[entry.name]; require(entry.isfile() and entry.size==row['bytes'] and entry.name not in found, 'Original notice entry differs')
                        with tar.extractfile(entry) as stream: actual=hashlib.file_digest(stream,'sha256').hexdigest()
                        require(actual==row['sha256']==observed[row['member']]['sha256'] and entry.size==observed[row['member']]['bytes'], 'Readable notice differs from original archive')
                        found[entry.name]=actual
            require(count==component['archive_entries'] and set(found)==set(wanted), 'Original notice/archive accounting differs')
            notice_rows.append(dict(source_archive=n,entries=count,original_notices=found))
        result.update(members=list(observed.values()),zip_members=29,payload_members=28,original_sources=17,
            original_source_bytes=244870939,package_records=397,distinct_package_sha256=339,original_notice_readback=notice_rows,
            source_manifest_sha256=CONTROL_HASHES['original_source_manifest.json'],standalone_intel_runtime_notice_gap=True,
            full_iqtree_corresponding_source_not_in_selected_inputs=True,installed_toolchain_image_included=False,
            package_artifacts_included=False,original_payload_bytes_reread=False,
            limitations=['Retained source archive bytes pinned; upstream byte equivalence not newly fetched',
                'Full IQ-TREE corresponding source archive and standalone Intel runtime license not included',
                'No installed toolchain image, package payloads, or complete host restore claim'])
    if not args.local_inspect: end_release(args,release,selected,result)
    result['state']='PASS_LOCAL_COMPONENTS29_MEMBERS_REMOTE_NOT_RUN' if args.local_inspect else 'PASS_FRESH_REMOTE_COMPONENTS29_MEMBERS_17_ORIGINALS_EXPLICIT_NOTICE_GAPS'

if __name__=='__main__':
    execute_readback(cli(__doc__),'public_components01',verify_components)
