"""Download and independently verify cold batch01; never extract, delete or execute it."""
from pathlib import Path,PurePosixPath,PureWindowsPath
import base64,datetime,hashlib,json,re,stat,subprocess,unicodedata,uuid,zipfile

WORK=Path(__file__).resolve().parent
REPO='serg-alexv/lab-rm-phylogenomics-196'
TAG='master-run-storage-20261009-v1'
COMMIT='46c7089f906cce59afabaa4449b05df36ee124de'
ASSET='master_cleanup_batch01.zip'
ASSET_SHA='0e7d888f9464acac4500a1f54516c9e9ee7094279a48fbaaec00be24fa85cf19'
INITIAL_SHA='0836bf9540e86126d8ac3aaa10187ca7e74e3e0bff483e721f5f31fd6acab382'
MAP_SHA='85955929650bbf5563e99461a8e70e6b35d6c6abd5db5b41524ea48f25158452'
PLAN_SHA='d518ce3305e3c36c8e5831bd84c9d48fc87faf1870e811d627594337363832d8'
LICENSE_SHA='c03cea027b4b40e4402fabd08557736727ec3d5bc54ad64ab6472de432198cad'
HELPER_SHA='d587bd9342a85837e6875f7c90c1bac3e8d751053932383fcae568550926d5ad'
OUT=WORK/('cleanup_batch01_independent_readback_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
OUT.mkdir()
RECEIPT=WORK/'master_cleanup_batch01_remote_readback.json'
result={'schema':'MASTER_COLD_CLEANUP_INDEPENDENT_REMOTE_READBACK_V1','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'state':'IN_PROGRESS_NO_PURGE','tag':TAG,'expected_tag_commit':COMMIT,'fresh_download_directory':str(OUT),
        'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'network_operations':'READ_AND_DOWNLOAD_ONLY',
        'source_deletions':0,'g_writes':0,'wsl_starts':0,'biological_jobs':0,'scientific_acceptance':'NONE_HISTORY_RECOVERY_ONLY'}
def require(value,message):
    if not value:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def run(argv,timeout=60):return subprocess.run(argv,capture_output=True,timeout=timeout,check=True).stdout
def api(endpoint):return json.loads(run(['gh','api','repos/'+REPO+'/'+endpoint]))
def save():RECEIPT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')

def safe_names(names):
    require(len(names)==len(set(names)),'Duplicate literal ZIP names')
    aliases=set();directories=set();spellings={}
    reserved={'con','prn','aux','nul','clock$'}|{prefix+n for prefix in ('com','lpt') for n in '123456789¹²³'}
    for name in names:
        p=PurePosixPath(name)
        require(name and not p.is_absolute() and p.as_posix()==name and not name.endswith('/'),'Unsafe/noncanonical ZIP name')
        for component in p.parts:
            require(component not in ('.','..') and not component.endswith(('.', ' '))
                and not any(ord(x)<32 or ord(x)==127 for x in component)
                and re.search(r'[<>:"\\|?*]',component) is None
                and unicodedata.normalize('NFC',component)==component
                and component.split('.')[0].casefold() not in reserved,'Unsafe Windows ZIP component')
        key=name.casefold()
        require(key not in aliases and key not in directories,'Case/file-directory ZIP collision')
        prefixes=['/'.join(p.parts[:i]).casefold() for i in range(1,len(p.parts))]
        require(not any(prefix in aliases for prefix in prefixes),'ZIP ancestor is a file')
        for i in range(1,len(p.parts)+1):
            literal='/'.join(p.parts[:i]);folded=literal.casefold()
            require(folded not in spellings or spellings[folded]==literal,'ZIP spelling alias')
            spellings[folded]=literal
        aliases.add(key);directories.update(prefixes)

save()
try:
    initial_bytes=(WORK/'cleanup_inventory_plan.json').read_bytes()
    map_bytes=(WORK/'master_cleanup_batch01_manifest.json').read_bytes()
    require(sha(initial_bytes)==INITIAL_SHA and sha(map_bytes)==MAP_SHA,'Initial/frozen manifest source drift')
    inventory=json.loads(initial_bytes);mapping=json.loads(map_bytes)
    require(inventory['schema']=='MASTER_LOCAL_ARCHIVE_PURGE_PREPARATION_V1'
        and mapping['schema']=='MASTER_COLD_CLEANUP_ARCHIVE_MAP_V1'
        and mapping['inventory_sha256']==INITIAL_SHA and mapping['plan_sha256']==PLAN_SHA
        and len(inventory['candidate_groups'])==14 and mapping['scope_roots']==inventory['scope_roots'],
        'Initial inventory/frozen archive scope differs')
    initial={}
    for index,group in enumerate(inventory['candidate_groups']):
        for item in group['files']:
            key=str(PureWindowsPath(item['path']))
            require(key not in initial,'Initial candidate duplicated')
            initial[key]=(item,index,group)
    require(len(initial)==142 and sum(x[0]['bytes'] for x in initial.values())==16194617,'Initial142 scope differs')
    require(mapping['initial_candidate_count']==142 and mapping['initial_source_bytes']==16194617,'Archive map scope differs')
    expected_payload={};seen=set()
    roots=[PureWindowsPath(value) for value in inventory['scope_roots']]
    for item in mapping['files']:
        key=str(PureWindowsPath(item['original_absolute_path']))
        require(key in initial and key not in seen,'Frozen archive repeats or invents candidate')
        seen.add(key);original,index,group=initial[key]
        require(item['sha256']==original['sha256'] and item['bytes']==original['bytes']
            and item['candidate_group_index']==index and item['classification']==group['classification']
            and item['required_gate']==group['required_gate'],'Frozen archive/initial candidate mismatch')
        matches=[]
        for root_index,root in enumerate(roots):
            try:matches.append((root_index,PureWindowsPath(key).relative_to(root)))
            except ValueError:pass
        require(len(matches)==1,'Candidate outside/ambiguous scope')
        root_index,relative=matches[0]
        member='payload/'+('current_chat_work','retained_20261008')[root_index]+'/'+relative.as_posix()
        require(item['portable_member']==member and member not in expected_payload,'Portable initial mapping differs')
        expected_payload[member]=item
    require(seen==set(initial) and len(expected_payload)==142,'Initial candidate coverage incomplete')
    release=api('releases/tags/'+TAG)
    tag_commit=api('commits/'+TAG)['sha']
    require(tag_commit==COMMIT,'Immutable release tag target differs')
    assets={item['name']:item for item in release['assets']}
    require(ASSET in assets and ASSET+'.sha256' in assets,'Required Release assets missing')
    require(assets[ASSET]['size']==6373127 and assets[ASSET]['digest']=='sha256:'+ASSET_SHA,'Remote ZIP size/digest differs')
    side_bytes=(ASSET_SHA+'  '+ASSET+'\n').encode()
    require(assets[ASSET+'.sha256']['size']==len(side_bytes)
        and assets[ASSET+'.sha256']['digest']=='sha256:'+sha(side_bytes),'Remote sidecar metadata differs')
    run(['gh','release','download',TAG,'--repo',REPO,'--pattern',ASSET,'--pattern',ASSET+'.sha256','--dir',str(OUT)],timeout=120)
    archive_path=OUT/ASSET;side_path=OUT/(ASSET+'.sha256')
    require(archive_path.stat().st_size==6373127 and digest(archive_path)==ASSET_SHA,'Actual fresh downloaded ZIP differs')
    require(side_path.read_bytes()==side_bytes,'Actual fresh downloaded sidecar differs')
    result.update(tag_commit=tag_commit,release_url=release['html_url'],assets=[{
        'name':name,'remote_asset_id':assets[name]['id'],'remote_digest':assets[name]['digest'],
        'bytes':assets[name]['size'],'downloaded_path':str(OUT/name),'sha256':digest(OUT/name)} for name in (ASSET,ASSET+'.sha256')])
    controls={'control/initial_cleanup_inventory_plan.json':INITIAL_SHA,
        'control/proposed_deletion_plan.md':PLAN_SHA,'control/member_mapping.json':MAP_SHA,
        'control/sourcepins.json':digest(WORK/'master_cleanup_batch01_metadata/sourcepins.json'),
        'code/build_master_cleanup_batch01.py':digest(WORK/'build_master_cleanup_batch01.py'),
        'code/portable_release.py':HELPER_SHA,
        'notices/IQTREE-3.1.4-source-pin.json':digest(WORK/'iqtree_3_1_4_source_review/source_pin.json'),
        'notices/IQTREE-3.1.4-LICENSE.txt':LICENSE_SHA,
        'control/NO_PURGE_notes.md':digest(WORK/'master_cleanup_batch01_notes.md')}
    with zipfile.ZipFile(archive_path) as archive:
        names=archive.namelist();safe_names(names)
        require(len(names)==153 and set(names)==set(expected_payload)|set(controls)|{'README.txt','SHA256SUMS.txt'},'Exact153 ZIP membership differs')
        require(archive.testzip() is None,'ZIP CRC failure')
        for info in archive.infolist():
            require(not info.is_dir() and stat.S_IFMT(info.external_attr>>16) in (0,stat.S_IFREG),'ZIP symlink/nonregular member')
            require(info.date_time==(2026,10,8,0,0,0),'Frozen deterministic timestamp differs')
        checks={}
        for line in archive.read('SHA256SUMS.txt').decode('utf-8').splitlines():
            match=re.fullmatch(r'([a-f0-9]{64})  (.+)',line)
            require(match is not None and match[2] not in checks,'Internal SHA256 manifest invalid/duplicate')
            checks[match[2]]=match[1]
        require(len(checks)==152 and set(checks)==set(names)-{'SHA256SUMS.txt'},'Internal SHA manifest is not exhaustive')
        verified=[]
        for name in names:
            with archive.open(name) as stream:observed=hashlib.file_digest(stream,'sha256').hexdigest()
            if name!='SHA256SUMS.txt':require(observed==checks[name],'Internal member SHA256 differs: '+name)
            if name in expected_payload:
                row=expected_payload[name]
                require(observed==row['sha256'] and archive.getinfo(name).file_size==row['bytes'],'ZIP bytes differ from initial/frozen candidate: '+name)
            if name in controls:require(observed==controls[name],'Frozen control/source/license bytes differ: '+name)
            verified.append({'member':name,'bytes':archive.getinfo(name).file_size,'sha256':observed,
                'bound_to_initial_candidate':name in expected_payload,'internal_sha256_manifest_covered':name in checks})
        require(archive.read('control/initial_cleanup_inventory_plan.json')==initial_bytes
            and archive.read('control/member_mapping.json')==map_bytes,'Embedded control bytes differ')
        pins=json.loads(archive.read('control/sourcepins.json'))
        require(pins['source_inventory']['sha256']==INITIAL_SHA and pins['proposed_deletion_plan']['sha256']==PLAN_SHA
            and pins['builder_sha256']==controls['code/build_master_cleanup_batch01.py']
            and pins['portable_release_sha256']==HELPER_SHA and pins['iqtree_license']['sha256']==LICENSE_SHA
            and pins['iqtree_source_pin_sha256']==controls['notices/IQTREE-3.1.4-source-pin.json']
            and pins['initial_source_files']==142 and pins['initial_source_bytes']==16194617,'Source pin cross-bindings differ')
        require(b'GNU GENERAL PUBLIC LICENSE' in archive.read('notices/IQTREE-3.1.4-LICENSE.txt'),'Original license text missing')
        source_pin=json.loads(archive.read('notices/IQTREE-3.1.4-source-pin.json'))
        require(source_pin['commit']=='63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de'
            and source_pin['tag']=='v3.1.4' and source_pin['repository']=='https://github.com/iqtree/iqtree3','Pinned IQTREE source identity differs')
        # Independently reopen authoritative published mapping/builder bytes at
        # the tag commit; local C copies alone cannot establish remote provenance.
        tree=api('git/trees/'+COMMIT+'?recursive=1')
        require(tree['truncated'] is False,'Published source tree truncated')
        objects={item['path']:item['sha'] for item in tree['tree'] if item['type']=='blob'}
        remote_controls=[]
        for path,digest_expected in {
            'reports/master_run/20261009/cleanup/BATCH01_ARCHIVE_MANIFEST.json':MAP_SHA,
            'reports/master_run/20261009/cleanup/INITIAL_INVENTORY.md':PLAN_SHA,
            'scripts/master_run/build_master_cleanup_batch01.py':controls['code/build_master_cleanup_batch01.py']}.items():
            blob=api('git/blobs/'+objects[path]);data=base64.b64decode(blob['content'])
            require(sha(data)==digest_expected,'Published authoritative control bytes differ')
            remote_controls.append({'path':path,'remote_blob':objects[path],'bytes':len(data),'sha256':sha(data),'actual_remote_bytes_read':True})
    require(api('commits/'+TAG)['sha']==COMMIT,'Release tag changed during readback')
    final_assets={item['name']:item for item in api('releases/tags/'+TAG)['assets']}
    require(all(final_assets[name]['id']==assets[name]['id'] and final_assets[name]['digest']==assets[name]['digest']
                and final_assets[name]['size']==assets[name]['size'] for name in (ASSET,ASSET+'.sha256')),'Release assets changed during verification')
    result.update(state='PASS_FRESH_REMOTE_ARCHIVE_ALL142_INITIAL_AND153_ZIP_MEMBERS_VERIFIED',
        initial_inventory_sha256=INITIAL_SHA,frozen_manifest_sha256=MAP_SHA,initial_candidate_files=142,
        initial_candidate_bytes=16194617,zip_members=153,manifest_covered_payload_members=152,
        initial_and_frozen_exact_join=True,crc='ALL_PASS',safe_windows_member_names=True,
        no_duplicates_aliases_symlinks=True,all_zip_member_sha256_verified=True,
        original_iqtree_license_and_source_pin_verified=True,unchanged_portable_helper_and_builder_verified=True,
        authoritative_remote_control_readback=remote_controls,members=verified,
        cleanup_authority='RECOVERY_GATE_EVIDENCE_ONLY_PARENT_MUST_RECHECK_ACTUAL_INACTIVE_TARGETS_AND_CURRENT_BYTES')
except Exception as error:
    result.update(state='FAILED_REMOTE_RECOVERY_GATE_NO_PURGE',error={'kind':type(error).__name__,'message':str(error)})
    raise
finally:
    result['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
print(json.dumps({key:result[key] for key in ('state','tag_commit','initial_candidate_files','initial_candidate_bytes','zip_members','manifest_covered_payload_members','fresh_download_directory')},indent=2))
