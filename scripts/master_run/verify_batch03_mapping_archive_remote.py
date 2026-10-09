"""Fresh independent recovery-mapping archive readback; no source-payload reads.

Only metadata/ZIP bytes are read. No extraction, archived code execution, deletion,
WSL, or scientific acceptance. The 47,429 candidates remain a later live-check
proposal. Historical source hashes and ZIP checks are explicitly retained evidence.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse, base64, collections, datetime, hashlib, json, re, stat
import subprocess, sys, unicodedata, uuid, zipfile

WORK=Path(__file__).resolve().parent
BUILD=WORK/'master_batch03_mapping01'
REPO='serg-alexv/lab-rm-phylogenomics-196'
ASSET='master_batch03_scientific_cache_mapping01.zip'
ZIP_SHA='f6d7e0558953d2542ca085552a6cd8219a4ec1acde4072ce6f03d12dd953178e'
ZIP_BYTES=6921443
RECEIPT_SHA='592be11a4fcff86616b5aa00f3c0201a08a064c14a162d97964bf36066babc0d'
BINDING_SHA='6e47a982ffb8eee6135f80d6e64089cf60399232918474909c032938d8976ae2'
ASSESSMENT_SHA='13d89bbfdd2b768501426493c8de0eac8a4076ed1aca789ab87ea1df759b7f1e'
BUILDER_SHA='68437b5b2cb60746dd804e46bcc7c39c59ad0c4afc005497f1f7c3922aef1708'
MAPPER_SHA='2b4c59634f4bf54cbd6f02e69cf980631f61611ccc36759314e9475f8d9564db'
SOURCE_SHA='a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84'
B2_SHA='fa3737d7bd1799dc29e069c3862fbee5e3ec1c59eaeca99b68e79f05bcc3a74d'
B3_SHA='c990e6875e93795a831942bd70108ff037efda0e6b3c7a6d16d80e2450f443d9'
ALLOW_SHA='df770f9e49e869c64f61db5720030aceff3b3282d53ee964aae02d228d7c3f64'
KEEP_SHA='bca12c16ff092b2e2fb612608186db728518d0ebf07fad80e1b401ed43ff0593'
PROOF_SHA='67087f8bbed012fb8ec3741ea35fd22f1fbb4801f3d0b7d6661e7d22f279ff5d'
OLD=PureWindowsPath(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
SCOPES={'data','.work/review2','.work/stage02_validated','.work/source_locus_inputs_v1',
        '.work/stage03_markers_v1','.work/stage04a_windows_alignments_v1','.work/stage04_phylogeny_v2'}
PRIVATE={'.git','.private_run','.codex'}
PRIVATE_NAMES=('codex_events','codex_stderr','continuation_events','continuation_stderr','usage_reset',
    'session_prompt','continuation_prompt','session_transcript','raw_prompt','raw_codex','reasoning_text','hidden_reasoning')

def require(value,message):
    if not value:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def is_sha(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None
def run(argv,timeout=60):return subprocess.run(argv,capture_output=True,timeout=timeout,check=True).stdout
def api(endpoint):return json.loads(run(['gh','api','repos/'+REPO+'/'+endpoint]))

def safe_names(names):
    require(len(names)==len(set(names)),'Duplicate ZIP names')
    files,dirs,spellings=set(),set(),{}
    reserved={'con','prn','aux','nul','clock$'}|{p+n for p in ('com','lpt') for n in '123456789¹²³'}
    for name in names:
        p=PurePosixPath(name)
        require(name and not p.is_absolute() and p.as_posix()==name and not name.endswith('/'),'Unsafe/noncanonical ZIP name')
        for part in p.parts:
            require(part not in ('.','..') and not part.endswith(('.', ' '))
                and not any(ord(c)<32 or ord(c)==127 for c in part)
                and re.search(r'[<>:"\\|?*]',part) is None and unicodedata.normalize('NFC',part)==part
                and part.split('.')[0].casefold() not in reserved,'Unsafe Windows ZIP component')
        key=name.casefold();prefixes=['/'.join(p.parts[:i]).casefold() for i in range(1,len(p.parts))]
        require(key not in files and key not in dirs and not any(k in files for k in prefixes),'ZIP alias/file-directory collision')
        for i in range(1,len(p.parts)+1):
            literal='/'.join(p.parts[:i]);folded=literal.casefold()
            require(folded not in spellings or spellings[folded]==literal,'ZIP spelling alias')
            spellings[folded]=literal
        files.add(key);dirs.update(prefixes)

def validate_row(row,seen):
    rel=row['relative_path'];p=PurePosixPath(rel);scope=row['scope']
    require(p.as_posix()==rel and not p.is_absolute() and '..' not in p.parts and not PRIVATE.intersection(p.parts)
        and not any(x in p.name.casefold() for x in PRIVATE_NAMES)
        and scope in SCOPES and rel.startswith(scope+'/')
        and row['path']==str(OLD.joinpath(*p.parts)) and row['path'].casefold() not in seen,'Mapping path escape/private/duplicate')
    safe_names([rel])
    require(type(row['bytes']) is int and row['bytes']>=0 and is_sha(row['sha256'])
        and all(type(row[k]) is int and row[k]>0 for k in ('device','file_id','mtime_ns','link_count')),'Mapping identity/byte fields invalid')
    seen.add(row['path'].casefold())
    return p

def verify_archive(path,receipt,result):
    require(path.stat().st_size==ZIP_BYTES and digest(path)==ZIP_SHA,'Actual archive differs from pinned bytes/size')
    with zipfile.ZipFile(path) as z:
        names=z.namelist();safe_names(names);require(len(names)==19,'Exact19 ZIP count differs')
        expected={r['member']:r for r in receipt['members']}
        require(len(expected)==19 and set(expected)==set(names),'Build receipt/member set differs')
        sums={}
        for line in z.read('SHA256SUMS.txt').decode('utf-8').splitlines():
            m=re.fullmatch(r'([a-f0-9]{64})  (.+)',line)
            require(m is not None and m[2] not in sums,'Invalid/duplicate SHA256SUMS row');sums[m[2]]=m[1]
        require(len(sums)==18 and set(sums)==set(names)-{'SHA256SUMS.txt'},'SHA256SUMS not exhaustive')
        observed={};members=[]
        for name in names:
            i=z.getinfo(name);require(not i.is_dir() and stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG)
                and not(i.flag_bits&1) and i.date_time==(2026,10,9,0,0,0),'ZIP nonregular/encrypted/timestamp differs')
            with z.open(name) as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            e=expected[name];require(actual==e['sha256'] and i.file_size==e['bytes']
                and f'{i.CRC:08x}'==e['crc32'] and e['crc_verified'] is True,'Actual member differs from captured build bytes')
            require(name=='SHA256SUMS.txt' or actual==sums[name],'Actual member SHA differs from internal sums')
            observed[name]=actual;members.append(dict(member=name,bytes=i.file_size,sha256=actual,crc32=f'{i.CRC:08x}',crc_verified=True,internal_sha256_covered=name in sums))
        read=lambda n:json.loads(z.read(n))
        binding=read('control/source_binding.json');assessment=read('control/conservative_leaf_assessment.json')
        sources=read('control/accepted_source_pins.json')
        require(observed['control/source_binding.json']==BINDING_SHA and observed['control/conservative_leaf_assessment.json']==ASSESSMENT_SHA
            and observed['control/accepted_source_pins.json']==SOURCE_SHA and observed['code/build_batch03_mapping_archive.py']==BUILDER_SHA
            and observed['code/map_yesterday_scientific_batch03.py']==MAPPER_SHA,'Independent control/source SHA differs')
        require(binding['schema']=='MASTER_BATCH03_MAPPING_ARCHIVE_SOURCE_BINDING_V1' and binding['state']=='LOCAL_BUILD_ONLY_NO_PURGE'
            and binding['builder_sha256']==BUILDER_SHA and binding['mapper_sha256']==MAPPER_SHA
            and binding['accepted_source_pins_sha256']==SOURCE_SHA and binding['mapped_files']==47648
            and binding['unmatched_payloads_archived'] is False
            and all(binding[k]==0 for k in ('old_payload_files_read','network_calls','g_writes','wsl_starts','source_deletions')),'Source binding contract differs')
        require(len(binding['payload_inputs'])==17 and set(binding['payload_inputs'])==set(names)-{'control/source_binding.json','SHA256SUMS.txt'},'Source inputs not exhaustive')
        for name,pin in binding['payload_inputs'].items():
            require(set(pin)=={'sha256','bytes'} and observed[name]==pin['sha256'] and z.getinfo(name).file_size==pin['bytes'],'Captured source input differs')
        b2,b3=read('mapping/batch02/evidence_sha256.json'),read('mapping/batch03/evidence_sha256.json')
        require(observed['mapping/batch02/evidence_sha256.json']==B2_SHA and observed['mapping/batch03/evidence_sha256.json']==B3_SHA,'Original input root pin differs')
        require(set(b2)=={'file_allowlist.json','remote_assets_after.json','remote_assets_before.json','summary.json','zip_member_validation.jsonl'}
            and set(b3)=={'file_allowlist.jsonl','preserve_unmatched_or_excluded.jsonl','source_proof.json','summary.json'},'Pinned input selection differs')
        for prefix,pins in [('mapping/batch02/',b2),('mapping/batch03/',b3)]:
            for n,pin in pins.items():require(observed[prefix+n]==pin['sha256'] and z.getinfo(prefix+n).file_size==pin['bytes'],'Original proof pin differs')
        require(observed['mapping/batch03/file_allowlist.jsonl']==ALLOW_SHA and observed['mapping/batch03/preserve_unmatched_or_excluded.jsonl']==KEEP_SHA
            and observed['mapping/batch03/source_proof.json']==PROOF_SHA,'Frozen mapping proof differs')
        proof=read('mapping/batch03/source_proof.json')
        require(proof['schema']=='LAB_RM_VERIFIED_REMOTE_MEMBER_SOURCE_V1' and proof['actual_verified_member_rows']==45955
            and proof['byte_restoration_only_not_new_scientific_acceptance'] is True
            and proof['proof_sha256']=={n:b2[n]['sha256'] for n in ('file_allowlist.json','summary.json','zip_member_validation.jsonl')},'Source proof bindings differ')
        old_assets=read('mapping/batch02/file_allowlist.json')['files'];archives={r['relative_path']:r for r in old_assets if r['relative_path'].endswith('.zip')}
        require(len(old_assets)==82 and len(archives)==28 and len({r['remote_asset_id'] for r in archives.values()})==27,'Historical source archive accounting differs')
        witnesses={};multiplicity=collections.Counter();historical=collections.defaultdict(list);record_count=record_bytes=0
        with z.open('mapping/batch02/zip_member_validation.jsonl') as f:
            for line in f:
                r=json.loads(line);a=archives[r['archive_relative_path']]
                require(r['crc_verified'] is True and r['internal_sha256_verified'] is (r['member']!='SHA256SUMS.txt')
                    and is_sha(r['sha256']) and type(r['bytes']) is int and r['bytes']>=0 and re.fullmatch('[a-f0-9]{8}',r['crc32']),'Historical witness schema/flags differ')
                key=(a['remote_asset_id'],r['member'],r['sha256'],r['bytes'],r['crc32'])
                value=(a['sha256'],a['bytes'],a['remote_url'],a['release_tag'])
                require(key not in witnesses or witnesses[key]==value,'Historical witness collision');witnesses[key]=value
                multiplicity[(r['sha256'],r['bytes'])]+=1;historical[r['archive_relative_path']].append(r['member']);record_count+=1;record_bytes+=r['bytes']
        require(record_count==45955 and record_bytes==6512011781,'Historical45955 proof accounting differs')
        for nameset in historical.values():safe_names(nameset)
        seen=set();count=total=eligible_count=eligible_bytes=0;holds={};groups=collections.defaultdict(collections.Counter);used_sources={}
        base={'path','relative_path','bytes','mtime_ns','device','file_id','link_count','scope','sha256'}
        with z.open('mapping/batch03/file_allowlist.jsonl') as f:
            for line in f:
                r=json.loads(line);require(set(r)==base|{'recovery','matching_member_witness_count','validation_scope'},'Mapped row schema differs')
                p=validate_row(r,seen);recovery=r['recovery']
                require(set(recovery)=={'release_tag','remote_asset_id','remote_asset_url','remote_zip_sha256','remote_zip_bytes','member','member_sha256','member_bytes','member_crc32'}
                    and recovery['member_sha256']==r['sha256'] and recovery['member_bytes']==r['bytes']
                    and type(recovery['remote_asset_id']) is int and recovery['remote_asset_id']>0
                    and r['matching_member_witness_count']==multiplicity[(r['sha256'],r['bytes'])]
                    and r['validation_scope']=='EXACT_BYTE_RESTORATION_ONLY_NOT_BIOLOGICAL_IDENTITY_OR_NEW_ACCEPTANCE','Mapped exact-byte validation binding differs')
                key=(recovery['remote_asset_id'],recovery['member'],r['sha256'],r['bytes'],recovery['member_crc32'])
                require(witnesses.get(key)==(recovery['remote_zip_sha256'],recovery['remote_zip_bytes'],recovery['remote_asset_url'],recovery['release_tag']),'Mapped row lacks exact historical ZIP witness')
                used_sources[recovery['remote_asset_id']]={k:recovery[k] for k in ('release_tag','remote_asset_id','remote_asset_url','remote_zip_sha256','remote_zip_bytes')}
                reason=None
                if r['scope']=='.work/review2':reason='PRESERVE_ALL_REVIEW2_PENDING_HISTORY_AND_CURRENT_POLICY_RECONCILIATION'
                elif r['relative_path'] in sources['accepted_files']:reason='PRESERVE_CURRENT_ACCEPTED_SOURCE_CONTROL_PATH'
                elif r['scope']=='.work/source_locus_inputs_v1' and p.name=='build_receipt.json':
                    require(p.parent.name in sources['source_receipts'] and sources['source_receipts'][p.parent.name]['sha256']==r['sha256'],'Mapped source receipt differs from fixed accepted pin')
                    reason='PRESERVE_OLD_C_SOURCE_RECEIPT_UNTIL_CANONICAL_G_AND_STANDALONE_GATE_RECONCILED'
                count+=1;total+=r['bytes'];groups[r['scope']]['matched_files']+=1;groups[r['scope']]['matched_bytes']+=r['bytes']
                if reason:holds[r['path']]={k:r[k] for k in ('path','relative_path','bytes','sha256')}|{'reason':reason}
                else:eligible_count+=1;eligible_bytes+=r['bytes']
        require((count,total,eligible_count,eligible_bytes)==(47648,6568632074,47429,6565902818),'Exact47648/47429 accounting differs')
        preserved_count=preserved_bytes=0
        with z.open('mapping/batch03/preserve_unmatched_or_excluded.jsonl') as f:
            for line in f:
                r=json.loads(line);require(set(r)==base|{'preserve_reason'} and r['preserve_reason']=='NO_EXACT_VERIFIED_REMOTE_MEMBER_SHA256_SIZE_MATCH','Preserved row schema/reason differs')
                validate_row(r,seen);preserved_count+=1;preserved_bytes+=r['bytes'];groups[r['scope']]['unmatched_files']+=1;groups[r['scope']]['unmatched_bytes']+=r['bytes']
        require((preserved_count,preserved_bytes)==(619,981198193) and len(seen)==48267,'619 preserved rows or complete file accounting differs')
        saved_holds={r['path']:r for r in assessment['files_preserved']}
        reasons=collections.Counter(r['reason'] for r in holds.values())
        require(len(saved_holds)==len(assessment['files_preserved'])==len(holds)==219 and saved_holds==holds
            and reasons=={'PRESERVE_ALL_REVIEW2_PENDING_HISTORY_AND_CURRENT_POLICY_RECONCILIATION':23,
                         'PRESERVE_OLD_C_SOURCE_RECEIPT_UNTIL_CANONICAL_G_AND_STANDALONE_GATE_RECONCILED':196}
            and sum(r['bytes'] for r in holds.values())==2729256,'Fixed conservative219 hold set differs')
        require(assessment['schema']=='MASTER_BATCH03_CONSERVATIVE_LEAF_ASSESSMENT_V1' and assessment['state']=='PROPOSAL_ONLY_NO_PURGE'
            and assessment['mapped_files']==count and assessment['mapped_bytes']==total
            and assessment['conservative_candidate_files']==eligible_count and assessment['conservative_candidate_bytes']==eligible_bytes
            and assessment['additionally_preserved_files']==219 and assessment['additionally_preserved_bytes']==2729256
            and assessment['unmatched_preserved_files']==619 and assessment['unmatched_preserved_bytes']==981198193
            and assessment['accepted_source_pins_sha256']==SOURCE_SHA and assessment['actual_purge']=='NOT_RUN','Assessment accounting/state differs')
        summary=read('mapping/batch03/summary.json')
        require(summary['schema']=='LAB_RM_OLD_SCIENTIFIC_CACHE_RELEASE_MEMBER_MAPPING_V1'
            and summary['status']=='PASS_EXACT_MATCHES_ONLY_UNMATCHED_PRESERVED' and summary['root']==str(OLD)
            and set(summary['scopes'])==SCOPES and summary['script_sha256']==MAPPER_SHA
            and summary['allowlist_sha256']==ALLOW_SHA and summary['preserve_manifest_sha256']==KEEP_SHA
            and summary['source_proof_sha256']==PROOF_SHA and summary['source_file_payload_passes']==1
            and summary['source_logical_bytes']==summary['payload_bytes_read_one_pass']==7549830267
            and summary['counts']=={'candidate_files':48267,'hashed_files':48267,'matched_bytes':6568632074,'matched_files':47648,'unmatched_bytes':981198193,'unmatched_files':619}
            and summary['actual_cleanup']=='NOT_RUN' and summary['scientific_status_changes'] is False,'Original mapping summary differs')
        for scope,values in groups.items():
            original=summary['groups'][scope]
            require(all(values[k]==original.get(k,0) for k in ('matched_files','matched_bytes','unmatched_files','unmatched_bytes'))
                and original['files']==values['matched_files']+values['unmatched_files']
                and original['bytes']==values['matched_bytes']+values['unmatched_bytes'],'Per-scope accounting differs')
        result.update(zip_members=19,manifest_covered_payload_members=18,all_zip_crc_sha_verified=True,source_input_bindings=17,
            mapped_rows=47648,mapped_bytes=6568632074,unmatched_preserved_rows=619,unmatched_preserved_bytes=981198193,
            conservative_hold_rows=219,conservative_hold_bytes=2729256,conservative_candidate_rows=47429,conservative_candidate_bytes=6565902818,
            actual_old_payload_files_read=0,scientific_acceptance='NONE_EXACT_BYTE_RESTORATION_EVIDENCE_ONLY',
            historical_zip_witness_rows_verified=45955,historical_archives_redownloaded_now=False,
            safe_paths_and_exact_7_scope_root_binding=True,conservative_hold_set_independently_recomputed=True,members=members)
        return used_sources

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag');parser.add_argument('--expected-tag-commit');parser.add_argument('--source-commit')
    parser.add_argument('--local-inspect',action='store_true')
    prefix='reports/master_run/20261009/cleanup/batch03_mapping01/'
    parser.add_argument('--remote-build-receipt-path',default=prefix+'build_receipt.json')
    parser.add_argument('--remote-source-binding-path',default=prefix+'source_binding.json')
    parser.add_argument('--remote-assessment-path',default=prefix+'conservative_leaf_assessment.json')
    parser.add_argument('--remote-accepted-source-pins-path',default='scripts/master_run/stage5_accepted_source_pins.json')
    parser.add_argument('--remote-batch03-pins-path',default=prefix+'evidence_sha256.json')
    parser.add_argument('--remote-builder-path',default='scripts/master_run/build_batch03_mapping_archive.py')
    parser.add_argument('--remote-mapper-path',default='scripts/master_run/map_yesterday_scientific_batch03.py')
    args=parser.parse_args();require(sys.platform=='win32','Windows C-only bounded verifier required')
    require(args.local_inspect or (args.tag and all(re.fullmatch('[a-f0-9]{40}',v or '') for v in (args.expected_tag_commit,args.source_commit))),'Remote mode requires exact tag/source commits')
    out=WORK/('batch03_mapping01_'+('local_inspection_' if args.local_inspect else 'remote_readback_')+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(exist_ok=False)
    result=dict(schema='MASTER_BATCH03_MAPPING_INDEPENDENT_READBACK_V1',state='IN_PROGRESS_NO_PURGE',started_utc=utc(),fresh_namespace=str(out),verifier_sha256=digest(__file__),
        mode='LOCAL_INSPECTION' if args.local_inspect else 'FRESH_REMOTE_DOWNLOAD',source_deletions=0,g_writes=0,wsl_starts=0,scientific_jobs=0,old_source_payload_reads=0)
    receipt_path=out/'receipt.json'
    def save():
        temporary=out/'receipt.json.next'
        with temporary.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n');f.flush()
        temporary.replace(receipt_path)
    save()
    try:
        raw=(BUILD/'build_receipt.json').read_bytes();require(sha(raw)==RECEIPT_SHA,'Frozen local build receipt differs');receipt=json.loads(raw)
        require(receipt['schema']=='MASTER_BATCH03_MAPPING_ARCHIVE_LOCAL_BUILD_V1' and receipt['state']=='LOCAL_ZIP_ALL_MEMBERS_VERIFIED_NO_PURGE'
            and receipt['sha256']==ZIP_SHA and receipt['bytes']==ZIP_BYTES and receipt['payload_members']==18
            and receipt['builder_sha256']==BUILDER_SHA and receipt['source_binding_sha256']==BINDING_SHA
            and receipt['mapped_files']==47648 and receipt['unmatched_preserved_files']==619 and receipt['conservative_candidate_files']==47429
            and receipt['all_member_crc_sha256_and_captured_input_bytes_verified'] is True and receipt['scientific_acceptance_changes'] is False
            and all(receipt[k]==0 for k in ('source_deletions','network_calls','g_writes','wsl_starts')),'Build receipt contract differs')
        side=(ZIP_SHA+'  '+ASSET+'\n').encode();assets=None
        if args.local_inspect:archive=BUILD/ASSET
        else:
            require(api('commits/'+args.tag)['sha']==args.expected_tag_commit,'Release tag target differs')
            release=api('releases/tags/'+args.tag)
            require(all(sum(a['name']==n for a in release['assets'])==1 for n in (ASSET,ASSET+'.sha256')),'Remote assets missing/duplicated')
            assets={a['name']:a for a in release['assets']}
            for n,size,pin in [(ASSET,ZIP_BYTES,ZIP_SHA),(ASSET+'.sha256',len(side),sha(side))]:require(assets[n]['size']==size and assets[n]['digest']=='sha256:'+pin,'Fresh Release asset digest/size differs')
            run(['gh','release','download',args.tag,'--repo',REPO,'--pattern',ASSET,'--pattern',ASSET+'.sha256','--dir',str(out)],timeout=120)
            archive=out/ASSET;require((out/(ASSET+'.sha256')).read_bytes()==side,'Actual downloaded sidecar differs')
            result.update(tag=args.tag,expected_tag_commit=args.expected_tag_commit,source_commit=args.source_commit,release_url=release['html_url'],
                assets=[dict(name=n,remote_asset_id=assets[n]['id'],remote_digest=assets[n]['digest'],bytes=assets[n]['size'],downloaded_path=str(out/n),sha256=digest(out/n)) for n in (ASSET,ASSET+'.sha256')])
        used_sources=verify_archive(archive,receipt,result)
        if args.local_inspect:result['state']='PASS_LOCAL_MAPPING_ARCHIVE_ONLY_REMOTE_NOT_RUN'
        else:
            tree=api('git/trees/'+args.source_commit+'?recursive=1');require(tree['truncated'] is False,'Published source tree truncated');objects={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'};remote=[]
            controls=[(args.remote_build_receipt_path,RECEIPT_SHA),(args.remote_source_binding_path,BINDING_SHA),(args.remote_assessment_path,ASSESSMENT_SHA),
                (args.remote_accepted_source_pins_path,SOURCE_SHA),(args.remote_batch03_pins_path,B3_SHA),(args.remote_builder_path,BUILDER_SHA),(args.remote_mapper_path,MAPPER_SHA)]
            for path,pin in controls:
                require(path in objects,'Published control absent: '+path);blob=api('git/blobs/'+objects[path]);require(blob['encoding']=='base64','Unexpected blob encoding');data=base64.b64decode(blob['content'])
                require(sha(data)==pin and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==objects[path],'Actual published control differs')
                remote.append(dict(path=path,commit=args.source_commit,remote_blob=objects[path],bytes=len(data),sha256=sha(data),actual_remote_bytes_read=True))
            # Fresh metadata proves referenced recovery assets remain present;
            # their scientific payloads are not downloaded/re-read here.
            current={};source_checks=[]
            for row in used_sources.values():
                tag=row['release_tag']
                if tag not in current:current[tag]=api('releases/tags/'+tag)['assets']
                matching=[a for a in current[tag] if a['id']==row['remote_asset_id']]
                require(len(matching)==1,'Referenced recovery asset missing');a=matching[0]
                require(a['size']==row['remote_zip_bytes'] and a['digest']=='sha256:'+row['remote_zip_sha256'] and a['browser_download_url']==row['remote_asset_url'],'Referenced current recovery asset identity differs')
                source_checks.append(dict(release_tag=tag,remote_asset_id=a['id'],bytes=a['size'],digest=a['digest'],metadata_only=True))
            require(api('commits/'+args.tag)['sha']==args.expected_tag_commit,'Release tag changed during readback');last=api('releases/tags/'+args.tag)
            require(all(sum(a['name']==n for a in last['assets'])==1 for n in (ASSET,ASSET+'.sha256')),'Final remote asset selection differs');final={a['name']:a for a in last['assets']}
            require(all(final[n]['id']==assets[n]['id'] and final[n]['digest']==assets[n]['digest'] and final[n]['size']==assets[n]['size'] for n in (ASSET,ASSET+'.sha256')),'Release asset identity changed during readback')
            result.update(state='PASS_FRESH_REMOTE_MAPPING19_MEMBERS_47648_ROWS_219_HOLDS_619_PRESERVED',authoritative_remote_control_readback=remote,
                referenced_recovery_asset_metadata=source_checks,release_tag_and_assets_unchanged_before_after=True)
        result.update(archive_sha256=ZIP_SHA,archive_bytes=ZIP_BYTES,local_build_receipt_sha256=RECEIPT_SHA,
            cleanup_authority='MAPPING_RECOVERY_EVIDENCE_ONLY_REQUIRES_SEPARATE_EXACT_LIVE_LEAF_GATE')
    except Exception as error:
        result.update(state='FAILED_MAPPING_READBACK_NO_PURGE',error=dict(kind=type(error).__name__,message=str(error)));raise
    finally:
        result['finished_utc']=utc();save();print(json.dumps(dict(state=result['state'],receipt=str(receipt_path)),indent=2))

if __name__=='__main__':main()
