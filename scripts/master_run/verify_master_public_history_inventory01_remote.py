"""Independent bounded history-archive readback. Never extract or execute payloads.

Local inspection proves only local bytes. Remote mode downloads new Release bytes,
reopens published controls at an explicit immutable source commit, and produces a
fresh receipt. Historical batch02 validation records are evidence, not rerun jobs.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse, base64, collections, datetime, gzip, hashlib, io, json, re, stat
import subprocess, sys, unicodedata, uuid, zipfile

WORK = Path(__file__).resolve().parent
REPO = 'serg-alexv/lab-rm-phylogenomics-196'
ASSET = 'master_public_history_inventory01.zip'
ZIP_SHA = '0016ea66132ccd257462899bf2ee74a05b1f7d73e0fb0e6e330f1ed3515d6842'
ZIP_BYTES = 5529652
MAP_SHA = '661989add3916e83bb7682e43efa1a1cfcac2a4af9a816f1dbbe8dc9587166fa'
BUILD_SHA = '39c7be3ff046ecab97b3ea455553f5b06db0984d7761d85af71a566c667931c3'
BUILDER_SHA = 'a8c9283e33939247143471a8dafc07f9b1c596510ed7776651cdb6ab778c113d'
PINS_SHA = '3891641cd58bb4fa535001c62511f4b5fb93fd393b7ae3c30d02be93248f046e'
PUBLIC_SHA = '4b279eebe6b842fc79cb9be6dd71a151a0a7890b525de32b1634ea99d8bc89da'
BATCH_SHA = 'fa3737d7bd1799dc29e069c3862fbee5e3ec1c59eaeca99b68e79f05bcc3a74d'
COLD_SHA = '0e7d888f9464acac4500a1f54516c9e9ee7094279a48fbaaec00be24fa85cf19'
COLD_MAP_SHA = '85955929650bbf5563e99461a8e70e6b35d6c6abd5db5b41524ea48f25158452'
HELPER_SHA = 'd587bd9342a85837e6875f7c90c1bac3e8d751053932383fcae568550926d5ad'
OLD = PureWindowsPath(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
CODE = {'build_master_cleanup_batch01.py':'b2f78af411e1ab3e751892578e9213485ebeca408882f264a1afaf5fd25c7a85',
        'finalize_yesterday_inventory_review.py':'99f878cc22334e6a59cf551d8c0b3b4d55a7592e59da1598649c6aa333805471',
        'inventory_yesterday_lab_rm.py':'6df81fd78bc53ff8f35680ff353cd5f3f26dc082f7661230d3e6d8093f5de068',
        'verify_yesterday_release_batch02.py':'656b63638ea12784356b47a79a4a1eb69e802eef263998255e255a348725e6de'}
PUBLIC_NAMES = {'REVIEW.md','critical_public_history_pins.json','current_dependency_evidence.json',
    'files_public_metadata.jsonl','public_inventory_observation.json','remote_main_tree.json',
    'remote_observation.json','remote_releases.json','retained_publication_receipts.json'}
BATCH_NAMES = {'file_allowlist.json','remote_assets_after.json','remote_assets_before.json','summary.json','zip_member_validation.jsonl'}
CONTROL = {'control/member_mapping.json':MAP_SHA,'control/sourcepins.json':PINS_SHA,
    'control/exclusions.json':'4b7df7907fb10a5b250a6f00c824578bc0cd1dedb7f58e4ac952ff9d63614bcb',
    'control/NO_PURGE_notes.md':'d3bf738cf4cd1652cd3d64dcbeec9b3b4270b36d08fe3c6c5b018697a5255bff'}
RAW = re.compile(rb'(?im)^\s*\{[^\n]{0,2000}"(?:type|channel)"\s*:\s*"(?:session_meta|turn_context|event_msg|response_item|analysis|reasoning|reasoning_text)"'
    rb'|(?im:^\s*<(?:think|analysis)>)|(?im:^\s*\{[^\n]{0,2000}"(?:rate_limits|total_token_usage|token_usage)"\s*:)'
    rb'|gh[pousr]_[A-Za-z0-9]{24,}|sk-[A-Za-z0-9]{32,}')
PRIVATE = ('codex_events','codex_stderr','continuation_events','continuation_stderr','usage_reset',
    'session_prompt','continuation_prompt','session_transcript','raw_prompt','raw_codex',
    'reasoning_text','chain_of_thought','hidden_reasoning','token_cache')
AZURE = '.tools/mamba/pkgs/https/conda.anaconda.org/conda-forge/linux-64/azure-identity-cpp-1.13.3-h71f81a8_2/include/azure/identity/detail/token_cache.hpp'

def require(value, message):
    if not value: raise ValueError(message)

def sha(data): return hashlib.sha256(data).hexdigest()
def digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(argv, timeout=60):
    return subprocess.run(argv, capture_output=True, check=True, timeout=timeout).stdout
def api(endpoint): return json.loads(run(['gh','api','repos/'+REPO+'/'+endpoint]))
def is_sha(value): return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None

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

def private(relative):
    p=PurePosixPath(relative.replace('\\','/').casefold())
    return bool({'.private_run','.git','.codex'}.intersection(p.parts)) or any(x in p.name for x in PRIVATE)

def metadata_exception(row):
    rel, kind=row['relative_path'],row['classification']
    if row['scope']!='historical_repo': return None
    if rel.startswith('.git/') and kind=='PROTECTED_HISTORICAL_GIT_STORE': return 'GIT_METADATA_ONLY'
    if rel.startswith('.tools/padloc_db/.git/') and kind=='PROTECTED_TOOLCHAIN_AND_RUNTIME': return 'PADLOC_GIT_METADATA_ONLY'
    if rel==AZURE and kind=='PROTECTED_TOOLCHAIN_AND_RUNTIME': return 'AZURE_SDK_HEADER_METADATA_ONLY'
    return None

def verify_archive(path, result):
    require(path.stat().st_size==ZIP_BYTES and digest(path)==ZIP_SHA,'Archive bytes/size differ from independently pinned build')
    with zipfile.ZipFile(path) as z:
        names=z.namelist(); safe_names(names)
        require(len(names)==320 and sum(i.file_size for i in z.infolist())==66601368, 'Archive member count/uncompressed bound differs')
        for i in z.infolist():
            require(not i.is_dir() and stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG)
                and not(i.flag_bits&1) and i.date_time==(2026,10,8,0,0,0), 'Nonregular/encrypted/nondeterministic ZIP entry')
        checks={}
        for line in z.read('SHA256SUMS.txt').decode('utf-8').splitlines():
            m=re.fullmatch(r'([a-f0-9]{64})  (.+)',line)
            require(m is not None and m[2] not in checks,'Invalid/duplicate SHA256SUMS row')
            checks[m[2]]=m[1]
        require(len(checks)==319 and set(checks)==set(names)-{'SHA256SUMS.txt'},'SHA256SUMS is not exhaustive')
        observed={}; members=[]
        for name in names:
            with z.open(name) as stream: actual=hashlib.file_digest(stream,'sha256').hexdigest()
            require(name=='SHA256SUMS.txt' or actual==checks[name],'Internal SHA differs: '+name)
            if name in CONTROL: require(actual==CONTROL[name],'Pinned control differs: '+name)
            observed[name]=actual
            members.append(dict(member=name,bytes=z.getinfo(name).file_size,sha256=actual,
                crc32=f'{z.getinfo(name).CRC:08x}',crc_verified=True,internal_sha256_manifest_covered=name in checks))
        # Reading every member through EOF above verifies every ZIP CRC as well as SHA.
        read=lambda name:json.loads(z.read(name))
        mapping,pins=read('control/member_mapping.json'),read('control/sourcepins.json')
        public,batch=read('inventory/PUBLIC_EVIDENCE_SHA256.json'),read('inventory/batch02/evidence_sha256.json')
        require(observed['inventory/PUBLIC_EVIDENCE_SHA256.json']==PUBLIC_SHA
            and observed['inventory/batch02/evidence_sha256.json']==BATCH_SHA and set(public)==PUBLIC_NAMES
            and set(batch)==BATCH_NAMES,'Original evidence root pins or selection differ')
        for prefix,table in [('inventory/',public),('inventory/batch02/',batch)]:
            for rel,row in table.items():
                require(set(row)=={'bytes','sha256'} and type(row['bytes']) is int and is_sha(row['sha256'])
                    and observed[prefix+rel]==row['sha256'] and z.getinfo(prefix+rel).file_size==row['bytes'], 'Evidence pin binding differs: '+rel)
        critical=read('inventory/critical_public_history_pins.json')
        require(critical['scope']=='PUBLIC_SCIENTIFIC_SOURCE_AND_RETAINED_MODEL_CHECKPOINTS_ONLY'
            and critical['private_content_copied'] is False and critical['bytes_read']==1656660
            and len(critical['files'])==291,'Original scientific selection differs')
        initial={}
        for row in critical['files']:
            rel=row['relative_path']; p=PurePosixPath(rel)
            require(set(row)=={'path','relative_path','bytes','sha256'} and rel==p.as_posix()
                and not p.is_absolute() and '..' not in p.parts and str(OLD.joinpath(*p.parts))==row['path']
                and row['path'] not in initial and is_sha(row['sha256']) and type(row['bytes']) is int
                and row['bytes']>=0 and not private(rel) and p.parts[0]!='.tools','Invalid/private scientific selection')
            initial[row['path']]=row
        require(sum(r['bytes'] for r in initial.values())==1656660,'Original scientific byte count differs')
        require(mapping['schema']=='MASTER_PUBLIC_HISTORY_ARCHIVE_MAP_V1' and mapping['state']=='NO_PURGE'
            and mapping['public_inventory_pin_sha256']==PUBLIC_SHA and mapping['batch02_evidence_pin_sha256']==BATCH_SHA
            and mapping['initial_critical_files']==mapping['included_critical_files']==291
            and mapping['initial_critical_bytes']==mapping['included_critical_bytes']==1656660
            and mapping['excluded_critical_files']==0 and len(mapping['files'])==291,'Frozen291 mapping differs')
        require(observed['inventory/cold_batch01_member_mapping.json']==COLD_MAP_SHA,'Cold recovery map differs')
        cold={r['original_absolute_path']:r for r in read('inventory/cold_batch01_member_mapping.json')['files']}
        seen=set(); origins=collections.Counter(); scientific_names=set()
        for row in mapping['files']:
            key=row['original_absolute_path']; require(key in initial and key not in seen,'Scientific mapping repeats/invents original')
            seen.add(key); original=initial[key]; member='historical_repo/'+original['relative_path']; scientific_names.add(member)
            require(row['portable_member']==member and row['sha256']==original['sha256'] and row['bytes']==original['bytes']
                and observed[member]==row['sha256'] and z.getinfo(member).file_size==row['bytes']
                and row['privacy_review']=='SCOPED_SCIENTIFIC_KIND_AND_NO_RAW_PRIVATE_PAYLOAD_SIGNATURE','Actual scientific member/pin mismatch')
            origins[row['payload_origin']]+=1; recovery=row['recovery']
            if recovery is None: require(row['payload_origin']=='REOPENED_ORIGINAL_SOURCE','Wrong original-origin declaration')
            else:
                witness=cold.get(key)
                require(row['payload_origin']=='EXACT_COLD_BATCH01_MEMBER' and witness is not None
                    and witness['sha256']==row['sha256'] and witness['bytes']==row['bytes']
                    and recovery=={'asset_sha256':COLD_SHA,'map_sha256':COLD_MAP_SHA,'member':witness['portable_member'],
                        'original_path_absent_at_build':True,'source_restoration':False},'Exact recovered-member witness differs')
            # Bounded review of actual scientific payload bytes, never source execution.
            data=z.read(member)
            if PurePosixPath(member).name in ('host.model.gz','host.ckp.gz'):
                with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream: data=stream.read(16*1024**2+1)
                require(len(data)<=16*1024**2,'Scientific decompression exceeds reviewed bound')
            require(RAW.search(data) is None,'Private raw-event/credential-shaped scientific payload')
        require(seen==set(initial) and origins=={'REOPENED_ORIGINAL_SOURCE':277,'EXACT_COLD_BATCH01_MEMBER':14}
            and mapping['critical_originals_reopened']==277 and mapping['critical_exact_cold_members_recovered']==14,'291 scientific/origin join incomplete')
        code={**CODE,'build_master_public_history_inventory01.py':BUILDER_SHA,'portable_release.py':HELPER_SHA}
        require(all(observed['code/'+n]==s for n,s in code.items()),'Unchanged builder/helper/inventory code binding differs')
        require(pins['schema']=='MASTER_PUBLIC_HISTORY_BUILD_SOURCE_PINS_V1' and pins['state']=='BUILD_ONLY_NO_PURGE'
            and pins['builder_sha256']==BUILDER_SHA and pins['code']==CODE and pins['portable_release_sha256']==HELPER_SHA
            and pins['input_roots']=={'PUBLIC_EVIDENCE_SHA256.json':PUBLIC_SHA,'batch02/evidence_sha256.json':BATCH_SHA}
            and pins['scientific_acceptance_changes'] is False,'Build source pin bindings differ')
        expected_inputs=scientific_names|{'code/'+n for n in code}|{'inventory/'+n for n in PUBLIC_NAMES}
        expected_inputs|={'inventory/batch02/'+n for n in BATCH_NAMES}|{'inventory/PUBLIC_EVIDENCE_SHA256.json',
            'inventory/batch02/evidence_sha256.json','inventory/cold_batch01_member_mapping.json'}
        input_seen=set()
        for row in pins['payload_inputs']:
            n=row['portable_member']; require(set(row)=={'portable_member','sha256','bytes'} and n in expected_inputs
                and n not in input_seen and observed[n]==row['sha256'] and z.getinfo(n).file_size==row['bytes'],'Exhaustive source input binding differs')
            input_seen.add(n)
        require(input_seen==expected_inputs and len(input_seen)==314
            and set(names)==expected_inputs|set(CONTROL)|{'README.txt','SHA256SUMS.txt'},'Exact320 archive membership differs')
        exclusions,observation=read('control/exclusions.json'),read('inventory/public_inventory_observation.json')
        require(exclusions['schema']=='MASTER_PUBLIC_HISTORY_EXCLUSIONS_V1'
            and exclusions['private_metadata_rows_not_exported']==800 and exclusions['private_payload_files_read_or_copied']==0
            and exclusions['critical_history_exclusions']==[] and exclusions['source_files_deleted']==0
            and observation['private_metadata_rows_excluded']==800 and observation['public_metadata_rows']==88441
            and observation['focused_extra_source_files']==291 and observation['focused_extra_bytes']==1656660,'Exclusion/observation contract differs')
        classifications,exceptions=collections.Counter(),collections.Counter(); metadata_seen=set(); count=0
        base={'path','relative_path','scope','bytes','classification','hash_state','mtime_ns','sha256'}
        with z.open('inventory/files_public_metadata.jsonl') as stream:
            for line in stream:
                row=json.loads(line); count+=1
                require(set(row) in (base,base|{'actual_git_blob_sha1','remote_recovery'},base|{'actual_git_blob_sha1','remote_recovery','remote_commit'})
                    and all(isinstance(row[k],str) for k in ('path','relative_path','scope','classification','hash_state'))
                    and type(row['bytes']) is int and row['bytes']>=0 and type(row['mtime_ns']) is int
                    and (row['sha256'] is None or is_sha(row['sha256'])),'Invalid public metadata row')
                key=sha((row['scope']+'\0'+row['relative_path']).encode()); require(key not in metadata_seen,'Duplicate public metadata row')
                metadata_seen.add(key)
                if private(row['relative_path']):
                    exception=metadata_exception(row); require(exception is not None,'Unreviewed private public metadata row'); exceptions[exception]+=1
                classifications[row['classification']]+=1
        require(count==mapping['public_metadata_rows']==88441 and dict(classifications)==mapping['public_metadata_classifications']
            and dict(exceptions)==mapping['reviewed_metadata_only_path_exceptions']=={'GIT_METADATA_ONLY':1118,'PADLOC_GIT_METADATA_ONLY':20,'AZURE_SDK_HEADER_METADATA_ONLY':1},'Metadata count/classification/privacy evidence differs')
        # These are retained historical validation records; original ZIPs are NOT redownloaded by this verifier.
        summary=read('inventory/batch02/summary.json'); allow=read('inventory/batch02/file_allowlist.json')['files']
        require(len(allow)==summary['files']==82 and sum(r['bytes'] for r in allow)==summary['bytes']==2190829648
            and summary['status']=='PASS_CURRENT_REMOTE_SHA256_AND_ALL_LOCAL_ZIP_MEMBERS','Historical batch02 file accounting differs')
        zip_rows={r['relative_path']:r for r in allow if r['relative_path'].endswith('.zip')}
        require(len(zip_rows)==summary['zip_copies']==28 and len({r['remote_asset_id'] for r in zip_rows.values()})==summary['distinct_zip_assets']==27,'Historical ZIP accounting differs')
        record_count=record_bytes=0; historical_names=collections.defaultdict(list); flags=collections.Counter()
        with z.open('inventory/batch02/zip_member_validation.jsonl') as stream:
            for line in stream:
                row=json.loads(line)
                require(set(row)=={'archive_relative_path','bytes','crc32','crc_verified','internal_sha256_verified','member','sha256'}
                    and row['archive_relative_path'] in zip_rows and type(row['bytes']) is int and row['bytes']>=0
                    and is_sha(row['sha256']) and re.fullmatch('[a-f0-9]{8}',row['crc32'])
                    and row['crc_verified'] is True and row['internal_sha256_verified'] is (row['member']!='SHA256SUMS.txt'),'Historical validation record schema/flags differ')
                historical_names[row['archive_relative_path']].append(row['member']); record_count+=1; record_bytes+=row['bytes']
                flags['sha_manifest' if row['member']=='SHA256SUMS.txt' else 'sha_covered']+=1
        require(set(historical_names)==set(zip_rows) and record_count==summary['zip_members_streamed']==45955
            and record_bytes==summary['uncompressed_bytes_streamed']==6512011781
            and flags=={'sha_manifest':28,'sha_covered':45927},'Historical45955 record accounting differs')
        for historical in historical_names.values(): safe_names(historical)
        result.update(zip_members=320,manifest_covered_payload_members=319,uncompressed_bytes=66601368,
            actual_scientific_file_copies_verified=291,scientific_copy_bytes=1656660,original_origin_declarations=277,
            exact_cold_member_recovery_bindings=14,public_metadata_rows_verified=88441,private_metadata_rows_excluded_as_pinned=800,
            historical_validation_records_verified=45955,historical_original_archives_revalidated_now=False,
            exhaustive_source_input_bindings=314,crc='ALL320_PASS',all_zip_member_sha256_verified=True,
            safe_windows_member_names=True,no_duplicates_aliases_symlinks=True,members=members)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag'); parser.add_argument('--expected-tag-commit'); parser.add_argument('--source-commit')
    parser.add_argument('--local-inspect',action='store_true',help='No network; never produces a remote recovery PASS')
    prefix='reports/master_run/20261009/cleanup/'
    parser.add_argument('--remote-manifest-path',default=prefix+'master_public_history_inventory01_manifest.json')
    parser.add_argument('--remote-build-receipt-path',default=prefix+'master_public_history_inventory01_build_receipt.json')
    parser.add_argument('--remote-builder-path',default='scripts/master_run/build_master_public_history_inventory01.py')
    parser.add_argument('--remote-public-pin-path',default=prefix+'yesterday_inventory/PUBLIC_EVIDENCE_SHA256.json')
    parser.add_argument('--remote-build-source-pins-path',default=prefix+'HISTORY01_BUILD_SOURCE_PINS.json')
    parser.add_argument('--remote-batch02-pins-path',default=prefix+'HISTORY01_BATCH02_EVIDENCE_SHA256.json')
    args=parser.parse_args()
    require(sys.platform=='win32','Use the bounded Windows C readback namespace')
    require(args.local_inspect or (args.tag and all(re.fullmatch('[a-f0-9]{40}',v or '') for v in (args.expected_tag_commit,args.source_commit))),'Remote mode requires tag and exact tag/source commits')
    out=WORK/('public_history01_'+('local_inspection_' if args.local_inspect else 'remote_readback_')+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    out.mkdir(exist_ok=False); receipt=out/'receipt.json'
    result=dict(schema='MASTER_PUBLIC_HISTORY_INDEPENDENT_READBACK_V1',state='IN_PROGRESS_NO_PURGE',started_utc=utc(),
        verifier_sha256=digest(__file__),fresh_namespace=str(out),source_deletions=0,g_writes=0,wsl_starts=0,biological_jobs=0,
        scientific_acceptance='NONE_HISTORY_RECOVERY_ONLY',mode='LOCAL_INSPECTION' if args.local_inspect else 'FRESH_REMOTE_DOWNLOAD')
    def save():
        partial=out/'receipt.json.next'
        with partial.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(result,stream,indent=2);stream.write('\n');stream.flush()
        partial.replace(receipt)
    save()
    try:
        local_manifest=(WORK/'master_public_history_inventory01_manifest.json').read_bytes()
        local_build=(WORK/'master_public_history_inventory01_build_receipt.json').read_bytes()
        require(sha(local_manifest)==MAP_SHA and sha(local_build)==BUILD_SHA,'Local frozen manifest/build receipt pins changed')
        build=json.loads(local_build)
        require(build['schema']=='MASTER_PUBLIC_HISTORY_LOCAL_BUILD_V1' and build['state']=='LOCAL_ZIP_VERIFIED_NO_PURGE'
            and build['sha256']==ZIP_SHA and build['bytes']==ZIP_BYTES and build['manifest_sha256']==MAP_SHA
            and build['builder_sha256']==BUILDER_SHA and build['payload_members']==319
            and build['included_critical_files']==291 and build['public_metadata_rows']==88441
            and build['private_metadata_rows_excluded']==800 and build['all_zip_crc_and_sha_verified'] is True
            and all(build[k]==0 for k in ('source_deletions','network_calls','wsl_starts','canonical_mutations')),'Build receipt contract differs')
        assets=None;side_bytes=(ZIP_SHA+'  '+ASSET+'\n').encode()
        if args.local_inspect: archive=WORK/ASSET
        else:
            require(api('commits/'+args.tag)['sha']==args.expected_tag_commit,'Release tag target differs')
            release=api('releases/tags/'+args.tag)
            require(all(sum(a['name']==n for a in release['assets'])==1 for n in (ASSET,ASSET+'.sha256')),'Assets missing/duplicated')
            assets={a['name']:a for a in release['assets']}
            for n,size,digest_expected in [(ASSET,ZIP_BYTES,ZIP_SHA),(ASSET+'.sha256',len(side_bytes),sha(side_bytes))]:
                require(assets[n]['size']==size and assets[n]['digest']=='sha256:'+digest_expected,'Fresh GitHub asset digest/size differs')
            # New empty namespace, no --clobber, and fresh digest checks after download.
            run(['gh','release','download',args.tag,'--repo',REPO,'--pattern',ASSET,'--pattern',ASSET+'.sha256','--dir',str(out)],timeout=120)
            archive=out/ASSET; require((out/(ASSET+'.sha256')).read_bytes()==side_bytes,'Downloaded sidecar differs')
            result.update(tag=args.tag,expected_tag_commit=args.expected_tag_commit,source_commit=args.source_commit,
                release_url=release['html_url'],assets=[dict(name=n,remote_asset_id=assets[n]['id'],remote_digest=assets[n]['digest'],
                    bytes=assets[n]['size'],downloaded_path=str(out/n),sha256=digest(out/n)) for n in (ASSET,ASSET+'.sha256')])
        verify_archive(archive,result)
        if args.local_inspect:
            result['state']='PASS_LOCAL_ARCHIVE_INSPECTION_ONLY_REMOTE_NOT_RUN'
        else:
            tree=api('git/trees/'+args.source_commit+'?recursive=1');require(tree['truncated'] is False,'Published source tree truncated')
            objects={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'}; remote=[]
            for path,expected in [(args.remote_manifest_path,MAP_SHA),(args.remote_build_receipt_path,BUILD_SHA),
                    (args.remote_builder_path,BUILDER_SHA),(args.remote_public_pin_path,PUBLIC_SHA),
                    (args.remote_build_source_pins_path,PINS_SHA),(args.remote_batch02_pins_path,BATCH_SHA)]:
                require(path in objects,'Published control missing: '+path)
                blob=api('git/blobs/'+objects[path]); require(blob['encoding']=='base64','Unexpected GitHub blob encoding')
                data=base64.b64decode(blob['content']);require(sha(data)==expected,'Actual published control differs: '+path)
                require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==objects[path],'Git blob identity differs')
                remote.append(dict(path=path,commit=args.source_commit,remote_blob=objects[path],bytes=len(data),sha256=sha(data),actual_remote_bytes_read=True))
            require(api('commits/'+args.tag)['sha']==args.expected_tag_commit,'Release tag changed during readback')
            last=api('releases/tags/'+args.tag)
            require(all(sum(a['name']==n for a in last['assets'])==1 for n in (ASSET,ASSET+'.sha256')),'Final Release asset selection differs')
            final={a['name']:a for a in last['assets']}
            require(all(final[n]['id']==assets[n]['id'] and final[n]['digest']==assets[n]['digest'] and final[n]['size']==assets[n]['size'] for n in (ASSET,ASSET+'.sha256')),'Release asset identity changed')
            result.update(state='PASS_FRESH_REMOTE_HISTORY_ARCHIVE_ALL320_MEMBERS_AND291_SCIENTIFIC_COPIES_VERIFIED',
                authoritative_remote_control_readback=remote,release_tag_and_assets_unchanged_before_after=True,
                source_commit_newer_than_release_tag_is_explicit=True)
        result.update(frozen_manifest_sha256=MAP_SHA,build_receipt_sha256=BUILD_SHA,archive_sha256=ZIP_SHA,archive_bytes=ZIP_BYTES,
            cleanup_authority='RECOVERY_EVIDENCE_ONLY_NO_DELETION_AUTHORITY')
    except Exception as error:
        result.update(state='FAILED_HISTORY_READBACK_NO_PURGE',error=dict(kind=type(error).__name__,message=str(error)));raise
    finally:
        result['finished_utc']=utc();save(); print(json.dumps(dict(state=result['state'],receipt=str(receipt)),indent=2))

if __name__=='__main__': main()
