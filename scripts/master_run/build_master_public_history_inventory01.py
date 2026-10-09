"""One bounded C-only public-history ZIP; no network, deletion or scientific jobs."""
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import ast, collections, datetime, gzip, hashlib, json, os, re, sys, unicodedata, zipfile, zlib
import build_master_cleanup_batch01 as B

WORK = Path(__file__).resolve().parent
INVENTORY = WORK/'yesterday_inventory'
OLD = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
ASSET = WORK/'master_public_history_inventory01.zip'
META = WORK/'master_public_history_inventory01_metadata'
PUBLIC_SHA = '4b279eebe6b842fc79cb9be6dd71a151a0a7890b525de32b1634ea99d8bc89da'
BATCH_SHA = 'fa3737d7bd1799dc29e069c3862fbee5e3ec1c59eaeca99b68e79f05bcc3a74d'
COLD_SHA = '0e7d888f9464acac4500a1f54516c9e9ee7094279a48fbaaec00be24fa85cf19'
COLD_MAP_SHA = '85955929650bbf5563e99461a8e70e6b35d6c6abd5db5b41524ea48f25158452'
CODE = {'inventory_yesterday_lab_rm.py': '6df81fd78bc53ff8f35680ff353cd5f3f26dc082f7661230d3e6d8093f5de068',
        'finalize_yesterday_inventory_review.py': '99f878cc22334e6a59cf551d8c0b3b4d55a7592e59da1598649c6aa333805471',
        'verify_yesterday_release_batch02.py': '656b63638ea12784356b47a79a4a1eb69e802eef263998255e255a348725e6de',
        'build_master_cleanup_batch01.py': 'b2f78af411e1ab3e751892578e9213485ebeca408882f264a1afaf5fd25c7a85'}
PRIVATE_PARTS = {'.private_run', '.git', '.codex'}
PRIVATE_NAMES = ('codex_events','codex_stderr','continuation_events','continuation_stderr','usage_reset',
                 'session_prompt','continuation_prompt','session_transcript','raw_prompt','raw_codex',
                 'reasoning_text','chain_of_thought','hidden_reasoning','token_cache')
AZURE_HEADER = '.tools/mamba/pkgs/https/conda.anaconda.org/conda-forge/linux-64/azure-identity-cpp-1.13.3-h71f81a8_2/include/azure/identity/detail/token_cache.hpp'
RAW = re.compile(rb'(?im)^\s*\{[^\n]{0,2000}"(?:type|channel)"\s*:\s*"(?:session_meta|turn_context|event_msg|response_item|analysis|reasoning|reasoning_text)"'
                 rb'|(?im:^\s*<(?:think|analysis)>)|(?im:^\s*\{[^\n]{0,2000}"(?:rate_limits|total_token_usage|token_usage)"\s*:)'
                 rb'|gh[pousr]_[A-Za-z0-9]{24,}|sk-[A-Za-z0-9]{32,}')


def private(relative):
    value = PurePosixPath(relative.replace('\\','/').casefold())
    return bool(PRIVATE_PARTS.intersection(value.parts)) or any(token in value.name for token in PRIVATE_NAMES)


def metadata_exception(row):
    # Metadata paths are not file payloads. Only independently reviewed exact
    # historical Git-store paths and the SDK header-name collision are allowed.
    rel, classification = row['relative_path'], row['classification']
    if row['scope'] != 'historical_repo': return None
    if rel.startswith('.git/') and classification == 'PROTECTED_HISTORICAL_GIT_STORE': return 'GIT_METADATA_ONLY'
    if rel.startswith('.tools/padloc_db/.git/') and classification == 'PROTECTED_TOOLCHAIN_AND_RUNTIME': return 'PADLOC_GIT_METADATA_ONLY'
    if rel == AZURE_HEADER and classification == 'PROTECTED_TOOLCHAIN_AND_RUNTIME': return 'AZURE_SDK_HEADER_METADATA_ONLY'
    return None


def pin(path, expected):
    path = B.plain(path)
    B.require(type(expected['bytes']) is int and path.stat().st_size == expected['bytes']
              and re.fullmatch('[a-f0-9]{64}', expected['sha256']) and B.sha(path) == expected['sha256'],
              'Missing or changed pinned public file: '+str(path))
    return path


def scan_payload(path):
    # A raw transcript/usage/secret-shaped payload is excluded intact, never redacted.
    opener = gzip.open if path.name in ('host.model.gz','host.ckp.gz') else Path.open
    tail, total = b'', 0
    with opener(path, 'rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            total += len(block)
            if total > 16*1024**2: return 'AMBIGUOUS_DECOMPRESSED_CONTENT_EXCEEDS_BOUNDED_REVIEW'
            if RAW.search(tail+block): return 'PRIVATE_RAW_EVENT_USAGE_REASONING_OR_CREDENTIAL_SHAPED_CONTENT'
            tail = block[-4096:]
    return None


def main():
    B.require(sys.platform == 'win32', 'Use exact Windows C archival scopes')
    B.plain(INVENTORY, True); B.plain(OLD, True)
    B.require(not META.exists() and not any(path.exists() for path in
              (ASSET, ASSET.with_suffix('.zip.partial'), ASSET.with_suffix('.zip.sha256'))), 'New archive namespace required')
    B.require(B.sha(INVENTORY/'PUBLIC_EVIDENCE_SHA256.json') == PUBLIC_SHA
              and B.sha(INVENTORY/'batch02/evidence_sha256.json') == BATCH_SHA, 'Public evidence root pins changed')
    public = json.loads((INVENTORY/'PUBLIC_EVIDENCE_SHA256.json').read_text(encoding='utf-8-sig'))
    batch = json.loads((INVENTORY/'batch02/evidence_sha256.json').read_text(encoding='utf-8-sig'))
    B.require(set(public) == {'REVIEW.md','critical_public_history_pins.json','current_dependency_evidence.json',
              'files_public_metadata.jsonl','public_inventory_observation.json','remote_main_tree.json',
              'remote_observation.json','remote_releases.json','retained_publication_receipts.json'}, 'Unexpected public evidence selection')
    B.require(set(batch) == {'file_allowlist.json','remote_assets_after.json','remote_assets_before.json',
                            'summary.json','zip_member_validation.jsonl'}, 'Unexpected batch02 evidence selection')
    sources = []
    for relative, row in sorted(public.items()):
        sources.append((pin(INVENTORY/relative, row), 'inventory/'+relative))
    for relative, row in sorted(batch.items()):
        sources.append((pin(INVENTORY/'batch02'/relative, row), 'inventory/batch02/'+relative))
    sources += [(INVENTORY/'PUBLIC_EVIDENCE_SHA256.json','inventory/PUBLIC_EVIDENCE_SHA256.json'),
                (INVENTORY/'batch02/evidence_sha256.json','inventory/batch02/evidence_sha256.json')]
    observation = json.loads((INVENTORY/'public_inventory_observation.json').read_text())
    B.require(observation['private_metadata_rows_excluded'] == 800 and observation['public_metadata_rows'] == 88441,
              'Public metadata exclusion/count contract differs')
    metadata_rows, classifications, metadata_exceptions = 0, collections.Counter(), collections.Counter()
    base_keys = {'path','relative_path','scope','bytes','classification','hash_state','mtime_ns','sha256'}
    with (INVENTORY/'files_public_metadata.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line); metadata_rows += 1
            B.require(isinstance(row, dict) and set(row) in (base_keys,
                      base_keys|{'actual_git_blob_sha1','remote_recovery'},
                      base_keys|{'actual_git_blob_sha1','remote_recovery','remote_commit'})
                      and all(isinstance(row[key],str) for key in ('path','relative_path','scope','classification','hash_state'))
                      and type(row['bytes']) is int and row['bytes'] >= 0 and type(row['mtime_ns']) is int
                      and (row['sha256'] is None or re.fullmatch('[a-f0-9]{64}',row['sha256'])),
                      'Public metadata schema differs')
            if private(row['relative_path']):
                reviewed = metadata_exception(row)
                B.require(reviewed is not None, 'Ambiguous/private public metadata row; preserve whole manifest locally')
                metadata_exceptions[reviewed] += 1
            classifications[row['classification']] += 1
    B.require(metadata_rows == 88441 and dict(metadata_exceptions) == {'GIT_METADATA_ONLY':1118,
              'PADLOC_GIT_METADATA_ONLY':20,'AZURE_SDK_HEADER_METADATA_ONLY':1},
              'Actual public metadata row count or reviewed exception count differs')
    critical = json.loads((INVENTORY/'critical_public_history_pins.json').read_text())
    B.require(set(critical) == {'scope','files','bytes_read','private_content_copied'}
              and critical['scope'] == 'PUBLIC_SCIENTIFIC_SOURCE_AND_RETAINED_MODEL_CHECKPOINTS_ONLY'
              and critical['private_content_copied'] is False and len(critical['files']) == 291
              and critical['bytes_read'] == 1656660, 'Critical public history schema/count differs')
    cold_asset = B.plain(WORK/'master_cleanup_batch01.zip')
    cold_map = B.plain(WORK/'master_cleanup_batch01_manifest.json')
    B.require(B.sha(cold_asset) == COLD_SHA and B.sha(cold_map) == COLD_MAP_SHA, 'Cold history recovery asset/map changed')
    cold_rows = {row['original_absolute_path']:row for row in json.loads(cold_map.read_text())['files']}
    eligible, excluded, seen, recovered = [], [], set(), []
    for row in critical['files']:
        B.require(set(row) == {'path','relative_path','bytes','sha256'}, 'Critical history file schema differs')
        path = Path(row['path']); relative = row['relative_path']; pure = PurePosixPath(relative)
        B.require(not pure.is_absolute() and pure.as_posix() == relative and '..' not in pure.parts
                  and path == OLD.joinpath(*pure.parts) and path not in seen, 'Critical source path escapes/repeats')
        seen.add(path)
        reason = 'PRIVATE_OR_UNREVIEWED_PATH_PRESERVED' if private(relative) or pure.parts[0] == '.tools' else None
        if not (path.suffix.casefold() in ('.py','.ps1','.sh','.md') or path.name in ('host.model.gz','host.ckp.gz')):
            reason = 'AMBIGUOUS_FILE_KIND_PRESERVED'
        recovery = None
        if reason is None and not path.exists():
            # Already-purged cold duplicates remain recoverable from exact local
            # bytes of the separately verified batch01 asset. Never restore the
            # original namespace or substitute another same-named file.
            witness = cold_rows.get(str(path))
            B.require(witness is not None and witness['sha256'] == row['sha256']
                      and witness['bytes'] == row['bytes'] and row['bytes'] <= 1024**2,
                      'Missing source lacks exact bounded cold-archive witness')
            with zipfile.ZipFile(cold_asset) as archive: data = archive.read(witness['portable_member'])
            B.require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'],
                      'Recovered cold source differs from original critical pin')
            reason = 'PRIVATE_RAW_EVENT_USAGE_REASONING_OR_CREDENTIAL_SHAPED_CONTENT' if RAW.search(data) else None
            recovery = {'asset_sha256':COLD_SHA,'map_sha256':COLD_MAP_SHA,'member':witness['portable_member'],
                        'original_path_absent_at_build':True,'source_restoration':False}
        elif reason is None:
            path = pin(path, row); reason = scan_payload(path)
        if reason:
            excluded.append({'selection': 'critical_history', 'path_identifier_sha256': hashlib.sha256(str(path).encode()).hexdigest(),
                             'sha256': row['sha256'], 'bytes': row['bytes'], 'reason': reason, 'local_preserved': True})
            continue
        member = 'historical_repo/'+relative
        eligible.append({'original_absolute_path': str(path), 'portable_member': member, 'bytes': row['bytes'],
                         'sha256': row['sha256'], 'privacy_review': 'SCOPED_SCIENTIFIC_KIND_AND_NO_RAW_PRIVATE_PAYLOAD_SIGNATURE',
                         'payload_origin':'EXACT_COLD_BATCH01_MEMBER' if recovery else 'REOPENED_ORIGINAL_SOURCE',
                         'recovery':recovery})
        if recovery: recovered.append((member,data))
        else: sources.append((path, member))
    B.require(sum(row['bytes'] for row in critical['files']) == 1656660, 'Critical initial byte total differs')
    for name, digest in CODE.items():
        path = B.plain(WORK/name); B.require(B.sha(path) == digest, 'Verifier/inventory source drift')
        sources.append((path, 'code/'+name))
    helper = B.plain(WORK/'master_cleanup_batch01_metadata/portable_release.py')
    B.require(B.sha(helper) == B.PINS['portable_release'], 'Retained pure ZIP helper drift')
    sources += [(helper,'code/portable_release.py'), (Path(__file__),'code/'+Path(__file__).name),
                (cold_map,'inventory/cold_batch01_member_mapping.json')]
    META.mkdir()
    for index,(member,data) in enumerate(recovered):
        path = META/f'recovered_critical_{index:03d}.bin'; B.write_new(path,data); sources.append((path,member))
    exclusion = {'schema': 'MASTER_PUBLIC_HISTORY_EXCLUSIONS_V1', 'state': 'LOCAL_PRESERVATION_NO_PURGE',
                 'private_metadata_rows_not_exported': 800, 'private_payload_files_read_or_copied': 0,
                 'excluded_inputs': [
                     {'selection':'yesterday_inventory/files.jsonl','reason':'UNFILTERED_PRIVATE_PATH_METADATA_NOT_EXPORTED'},
                     {'selection':'historical .private_run and raw Codex/prompt/event/usage/reasoning content', 'reason':'PRIVATE_CONTENT_NOT_SELECTED'},
                     {'selection':'other inventory outputs absent from PUBLIC_EVIDENCE_SHA256.json','reason':'UNREVIEWED_NOT_PUBLIC_PINNED_INPUT'},
                     {'selection':'batch03 mapping still in preparation','reason':'MUTABLE_SEPARATE_EVIDENCE_NOT_SELECTED'},
                     {'selection':'large runtime/images/data and remaining source payloads named only in metadata','reason':'NOT_PAYLOAD_ARCHIVED_BY_THIS_BOUNDED_BATCH'}],
                 'critical_history_exclusions': excluded, 'source_files_deleted': 0}
    mapping = {'schema':'MASTER_PUBLIC_HISTORY_ARCHIVE_MAP_V1','state':'NO_PURGE',
               'public_inventory_pin_sha256': PUBLIC_SHA,'batch02_evidence_pin_sha256': BATCH_SHA,
               'initial_critical_files':291,'initial_critical_bytes':1656660,
               'included_critical_files':len(eligible),'included_critical_bytes':sum(row['bytes'] for row in eligible),
               'critical_originals_reopened':len(eligible)-len(recovered),'critical_exact_cold_members_recovered':len(recovered),
               'excluded_critical_files':len(excluded),'public_metadata_rows':metadata_rows,
               'reviewed_metadata_only_path_exceptions':dict(metadata_exceptions),
               'public_metadata_classifications':dict(sorted(classifications.items())), 'files':eligible}
    manifest = WORK/'master_public_history_inventory01_manifest.json'; B.write_new(manifest, B.json_bytes(mapping))
    exclusions = META/'exclusions.json'; B.write_new(exclusions, B.json_bytes(exclusion))
    pins = {'schema':'MASTER_PUBLIC_HISTORY_BUILD_SOURCE_PINS_V1','state':'BUILD_ONLY_NO_PURGE',
            'builder_sha256':B.sha(__file__),'code':CODE,'portable_release_sha256':B.sha(helper),
            'input_roots':{'PUBLIC_EVIDENCE_SHA256.json':PUBLIC_SHA,'batch02/evidence_sha256.json':BATCH_SHA},
            'cold_recovery':{'asset_sha256':COLD_SHA,'map_sha256':COLD_MAP_SHA,'files':len(recovered),
                             'network_download':'NOT_RUN','original_namespace_restoration':'NOT_RUN'},
            'python':sys.version,'zlib_runtime_version':zlib.ZLIB_RUNTIME_VERSION,
            'executed_original_zip_functions_only':['hash_stream','validate_member_names','verify_zip','make_zip'],
            'source_headers_and_notices':'Original selected bytes copied unchanged; NCBI provider READMEs preserved',
            'scientific_acceptance_changes':False,'remote_archive_readback':'NOT_RUN',
            'payload_inputs':[{'portable_member':member,'sha256':B.sha(path),'bytes':path.stat().st_size} for path,member in sources]}
    pinfile = META/'sourcepins.json'; B.write_new(pinfile,B.json_bytes(pins))
    guide = ('Public LAB R-M history/inventory archive01, NO_PURGE.\n'
             'Pinned filtered metadata and batch02 recovery evidence; selected291 small scientific source/checkpoint candidates independently reopened.\n'
             'See control/member_mapping.json for actual included/excluded counts and control/exclusions.json for retained private/ambiguous scopes.\n'
             'Raw private Codex/prompt/event/usage/reasoning content is not selected;800 private metadata rows remain excluded.\n'
             'All selected source/header/provider notices remain byte-identical. Metadata-only paths do not mean their payloads are archived.\n'
             'The strict metadata schema permits 1118 historical Git paths,20 PADLOC Git paths and one Azure token_cache.hpp header path as metadata only.\n'
             'Already-purged cold duplicates are recovered only from the exact batch01 ZIP member and original initial SHA256/size; the mapping identifies those files.\n'
             'Historical failure/UNKNOWN/NOT_RUN labels remain unchanged; this is no new scientific acceptance or whole-project completion.\n'
             'No download, upload, source deletion, WSL or scientific job is performed by this builder. Independent remote readback precedes any purge.\n')
    notes = WORK/'master_public_history_inventory01_notes.md'; B.write_new(notes,guide.encode())
    sources += [(manifest,'control/member_mapping.json'),(exclusions,'control/exclusions.json'),
                (pinfile,'control/sourcepins.json'),(notes,'control/NO_PURGE_notes.md')]
    names = {'hash_stream','validate_member_names','verify_zip','make_zip'}
    selected = [node for node in ast.parse(helper.read_text()).body if isinstance(node,ast.FunctionDef) and node.name in names]
    B.require({node.name for node in selected} == names, 'Pure ZIP interface differs')
    namespace = dict(Path=Path,PurePosixPath=PurePosixPath,hashlib=hashlib,json=json,os=os,re=re,
                     unicodedata=unicodedata,zipfile=zipfile,w=SimpleNamespace(digest=B.sha,atomic=B.write_new))
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(helper),'exec'),namespace)
    result = namespace['make_zip'](ASSET,sources,guide)
    with zipfile.ZipFile(ASSET) as archive:
        B.require(archive.testzip() is None and len(archive.namelist()) == len(set(archive.namelist())) == len(sources)+2,
                  'CRC/duplicate/member count failure')
        for path,member in sources:
            with archive.open(member) as stream: actual = namespace['hash_stream'](stream)
            B.require(actual == B.sha(B.plain(path)) and archive.getinfo(member).file_size == path.stat().st_size,
                      'Actual ZIP/source bytes differ: '+member)
        B.require(all(info.date_time == (2026,10,8,0,0,0) for info in archive.infolist()), 'ZIP timestamp nondeterminism')
    B.require(namespace['verify_zip'](ASSET) == result['payload_members'], 'Full SHA member manifest differs')
    # Bind final source bytes back to the original scientific/evidence pins,
    # rather than accepting mutually changed live source and ZIP bytes.
    for relative,row in public.items(): pin(INVENTORY/relative,row)
    for relative,row in batch.items(): pin(INVENTORY/'batch02'/relative,row)
    actual_sources = {member:path for path,member in sources}
    for row in eligible: pin(actual_sources[row['portable_member']],row)
    B.require(B.sha(INVENTORY/'PUBLIC_EVIDENCE_SHA256.json') == PUBLIC_SHA
              and B.sha(INVENTORY/'batch02/evidence_sha256.json') == BATCH_SHA,
              'Initial public evidence root pins changed during build')
    receipt = dict(result,schema='MASTER_PUBLIC_HISTORY_LOCAL_BUILD_V1',state='LOCAL_ZIP_VERIFIED_NO_PURGE',
                   asset_path=str(ASSET),sidecar_path=str(ASSET.with_suffix('.zip.sha256')),
                   included_critical_files=len(eligible),excluded_critical_files=len(excluded),
                   critical_originals_reopened=len(eligible)-len(recovered),critical_exact_cold_members_recovered=len(recovered),
                   included_critical_bytes=sum(row['bytes'] for row in eligible),public_metadata_rows=metadata_rows,
                   private_metadata_rows_excluded=800,all_zip_crc_and_sha_verified=True,
                   builder_sha256=B.sha(__file__),manifest_sha256=B.sha(manifest),
                   network_calls=0,wsl_starts=0,canonical_mutations=0,source_deletions=0,
                   remote_readback='NOT_RUN',completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    B.write_new(WORK/'master_public_history_inventory01_build_receipt.json',B.json_bytes(receipt))
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__': main()
