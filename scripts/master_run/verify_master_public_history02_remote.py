"""Independent three-shard public-history readback; no extraction/execution/purge.

The adjacent independently reviewed readback primitive module is byte-pinned before
import. All archive/source controls are reopened at an explicit immutable commit.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
import collections, hashlib, importlib.util, json, re

WORK=Path(__file__).resolve().parent
HELPER_SHA='6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691'
helper=WORK/'verify_master_public_components01_remote.py'
if hashlib.sha256(helper.read_bytes()).hexdigest()!=HELPER_SHA:
    raise RuntimeError('Pinned independent readback helper source differs')
spec=importlib.util.spec_from_file_location('independent_public_readback_primitives',helper)
H=importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
require=H.require
PREFIX='reports/master_run/20261009/cleanup/history02/'
OLD=PureWindowsPath(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
CONTROL_HASHES={
 'asset_index.json':'83465f4096bdcc921ef60d9a25fbd2101d87f26708607dd5f9f564e6ba5b8248',
 'build_receipt.json':'6c24aca7edaf790b740bc55626c08d8e2f7e42c9695378b9e571053f2a24d64a',
 'source_binding.json':'bb867f65c594bce5771ebc068768678b5bf1e30d1a8d02fe0070d9e10bc09294',
 'original_member_mapping.json':'014a540f8bfb11a31c9ea5d709562ea3669894b70fa2d300999b0a3df450c6cf',
 'PUBLICATION_CONTROL_SHA256.json':'aeb61030387db598639e42477d6fe196477ad8ef814ab3b451b9b08e3f8c642a',
 'REVIEW.md':'4aac907d0640e1601b89093b63a82296e9e9cb638a8d0cbae6e19d5205bd3c4b',
 'ATTRIBUTION_AND_SCOPE.txt':'8766ff4b5ffbf19ee2a659eb8749c8d6e05af5acd9e369a55cf4f96480d6f48c'}
INSPECTION_HASHES={
 'inspection.json':'dc911094cae2057c264bd4e30e4c2d701d6e0a1dbf140b551cb71f89dd3a8fc5',
 'manual_scope_review.json':'f88fab6380b6c3a4dd4339b3a4d1c12af3974f86080ec1d540e424b475dd86cb',
 'excluded_files.json':'ee5e538127fac8676e1390cae79e0126072c13326ce6a6f3fdadf6e623c20fab',
 'public_scope.json':'dec1dfb957965ca293180efba04f43498105fc0a46056aff1d7e551f72686032'}
CODE_HASHES={
 'build_public_history02.py':'896b132325cc442ffb010c3e332f667a5f899a575ee69a782256127ea59e0de8',
 'inspect_public_history02.py':'671b20fc3f8b89c214d9fc50a3b793275caafce72bac03bee4379468793dcfc0',
 'finalize_public_history02_scope.py':'a8068ac628d8249e02af65954694dd8f3f2a19aef0441657a55f4756f388f1b4',
 'test_public_history02_screen.py':'a0611cee8bb2842be19a25e5f5f26023d93a72316622e29ebf45113e7bf5d8e3',
 'verify_master_public_components01_remote.py':HELPER_SHA}
SOURCE_INPUTS={
 'master_batch03_mapping01/conservative_leaf_assessment.json':'13d89bbfdd2b768501426493c8de0eac8a4076ed1aca789ab87ea1df759b7f1e',
 'yesterday_inventory/batch03/file_allowlist.jsonl':'df770f9e49e869c64f61db5720030aceff3b3282d53ee964aae02d228d7c3f64',
 'yesterday_inventory/batch03/preserve_unmatched_or_excluded.jsonl':'bca12c16ff092b2e2fb612608186db728518d0ebf07fad80e1b401ed43ff0593'}
ASSETS=[
 dict(name='master_public_history02-001.zip',bytes=37717209,sha256='ecb1856f1d95a80c20c57877588d77079a4ac0dce317c57162f9e2460ad3eb96',original_source_files=174,original_source_bytes=333229043),
 dict(name='master_public_history02-002.zip',bytes=48197997,sha256='f593ce812029aa9feb01150cdd70d5c9d3686339ac2e8ed1d8ae5dbb92e533a9',original_source_files=231,original_source_bytes=332796032),
 dict(name='master_public_history02-003.zip',bytes=34759291,sha256='8016055d11942baa9e8b236acc32a6f58d3f8bb37f03d929402f0e027671fafd',original_source_files=432,original_source_bytes=317901349)]

def jsonlines(data):
    rows=[json.loads(line) for line in data.decode('utf-8').splitlines()]
    require(all(isinstance(r,dict) for r in rows), 'Invalid JSONL control row')
    return rows

def source_key(row):
    rel=row['relative_path']; p=PurePosixPath(rel)
    require(p.as_posix()==rel and not p.is_absolute() and '..' not in p.parts
        and row['scope'] in ('.work/review2','.work/source_locus_inputs_v1','.work/stage04_phylogeny_v2','.work/stage03_markers_v1')
        and rel.startswith(row['scope']+'/') and str(OLD.joinpath(*p.parts))==row['path']
        and not {'.private_run','.codex','.git'}.intersection(p.parts)
        and row['selection_origin'] in ('UNMATCHED_619_PRESERVE','CONSERVATIVE_219_HOLD')
        and H.is_sha(row['sha256']) and type(row['bytes']) is int and row['bytes']>=0
        and row['link_count']==1 and all(type(row[k]) is int and row[k]>0 for k in ('device','file_id','mtime_ns')), 'Original source scope/identity differs')
    return row['path']

def verify_history(args,out,result):
    extras={PREFIX+'inspection/'+n:(WORK/'master_public_history02_inspection'/n,h) for n,h in INSPECTION_HASHES.items()}
    controls=H.get_controls(args,CONTROL_HASHES,CODE_HASHES,PREFIX,WORK/'master_public_history02',out,result,extras)
    read=lambda n:json.loads(controls[PREFIX+n])
    index,build,binding,mapping=(read(n) for n in ('asset_index.json','build_receipt.json','source_binding.json','original_member_mapping.json'))
    scope,review,exclusions,inspection=(read('inspection/'+n) for n in ('public_scope.json','manual_scope_review.json','excluded_files.json','inspection.json'))
    require(index['schema']=='MASTER_PUBLIC_HISTORY02_ASSET_INDEX_V1' and index['assets']==ASSETS
        and index['public_files']==837 and index['excluded_files']==1, 'Independent shard/index pins differ')
    for obj in (index,build):
        require(obj['build_receipt_sha256']==CONTROL_HASHES['build_receipt.json'] if obj is index else True, 'Build receipt pin differs')
        require(obj['original_member_mapping_sha256']==CONTROL_HASHES['original_member_mapping.json']
            and obj['source_binding_sha256']==CONTROL_HASHES['source_binding.json']
            and obj['source_scope_sha256']==INSPECTION_HASHES['public_scope.json'], 'History cross-control binding differs')
    require(build['schema']=='MASTER_PUBLIC_HISTORY02_LOCAL_BUILD_V1' and build['selection_files']==838
        and build['selection_bytes']==983927449 and build['public_files']==837 and build['public_bytes']==983926424
        and build['excluded_files']==1 and build['excluded_bytes']==1025 and build['all_original_source_identities_stable'] is True
        and len(build['shards'])==3 and build['total_compressed_asset_bytes']==120674497
        and build['historical_native_closure']=='NOT_INFERRED_UNKNOWN_REMAINS_UNKNOWN', 'History build accounting differs')
    require(binding['schema']=='MASTER_PUBLIC_HISTORY02_BUILD_SOURCE_BINDING_V1'
        and binding['source_input_controls']==SOURCE_INPUTS and binding['included_source_file_count']==837
        and binding['excluded_source_file_count']==1 and binding['raw_private_events_prompts_usage_exported'] is False
        and binding['copied_third_party_source'] is False and binding['historical_native_closure']=='NOT_INFERRED'
        and binding['redaction']=='NONE_WHOLE_FILES_EXCLUDED', 'History source/privacy/closure binding differs')
    require(scope['schema']=='MASTER_PUBLIC_HISTORY02_PUBLIC_SCOPE_V1' and scope['public_files']==837
        and scope['excluded_files']==1 and scope['public_bytes']==983926424 and scope['excluded_bytes']==1025
        and scope['whole_file_exclusions_no_redaction'] is True and scope['historical_native_closure']=='NOT_INFERRED'
        and scope['current_biological_acceptance']=='NONE_HISTORY_PRESERVATION_ONLY', 'Final public scope differs')
    require(review['schema']=='MASTER_PUBLIC_HISTORY02_MANUAL_SCOPE_AND_ATTRIBUTION_REVIEW_V1'
        and review['private_payloads_exported']==0 and len(review['manual_schema_resolutions'])==9
        and len(review['nested_fixture_metadata_screen'])==24 and len(review['third_party_source_exclusions'])==1
        and review['third_party_source_exclusions']==exclusions['files'], 'Manual source/privacy resolution differs')
    require(mapping['schema']=='MASTER_PUBLIC_HISTORY02_ORIGINAL_MEMBER_MAPPING_V1'
        and mapping['original_bytes_unchanged'] is True and len(mapping['files'])==837
        and mapping['excluded_source_file_count']==1 and mapping['historical_native_closure']=='NOT_INFERRED', 'Original837 mapping differs')
    release=selected=None
    if not args.local_inspect: release,selected=H.begin_release(args,ASSETS,out,result)
    common_data=None; observations={}; receipt_shards=[]
    for asset,declared in zip(ASSETS,build['shards']):
        require(all(declared[k]==asset[k] for k in asset) and declared['all_member_crc_sha256_and_expected_source_pins_verified'] is True,
            'Build shard pin/count differs')
        path=(WORK/'master_public_history02' if args.local_inspect else out)/asset['name']
        z,observed=H.verify_zip(path,asset,H.member_table(declared['members']))
        with z:
            require(len(observed)==asset['original_source_files']+15, '15 common entries per shard differ')
            require(set(observed)==set(binding['common_payload_inputs'])|{'control/source_binding.json','SHA256SUMS.txt'}
                |{r['member'] for r in mapping['files'] if r['asset_name']==asset['name']}, 'Exact shard source membership differs')
            H.bind_inputs(binding['common_payload_inputs'],observed)
            current={n:z.read(n) for n in set(binding['common_payload_inputs'])|{'control/source_binding.json'}}
            require(common_data is None or current==common_data, 'Common control bytes differ between shards')
            common_data=current
            for n in ('source_binding.json','original_member_mapping.json'):
                require(z.read('control/'+n)==controls[PREFIX+n], 'Outer/inner history control differs')
            for n in INSPECTION_HASHES:
                require(z.read('control/'+n)==controls[PREFIX+'inspection/'+n], 'Published scope control differs from shard')
            require(z.read('ATTRIBUTION_AND_SCOPE.txt')==controls[PREFIX+'ATTRIBUTION_AND_SCOPE.txt'], 'Attribution bytes differ')
            observations[asset['name']]=observed
            receipt_shards.append(dict(name=asset['name'],bytes=asset['bytes'],sha256=asset['sha256'],members=list(observed.values())))
    data=common_data
    selection=json.loads(data['control/selection.json'])
    require(selection['schema']=='MASTER_PUBLIC_HISTORY02_EXACT_SELECTION_V1' and len(selection['files'])==838, 'Original838 selection differs')
    original={source_key(r):r for r in selection['files']}
    require(len(original)==838 and sum(r['bytes'] for r in original.values())==983927449
        and collections.Counter(r['selection_origin'] for r in original.values())=={'UNMATCHED_619_PRESERVE':619,'CONSERVATIVE_219_HOLD':219}, 'Selection count/origins differ')
    public=jsonlines(data['control/public_payloads.jsonl']); decisions=jsonlines(data['control/decisions.jsonl'])
    require(len(public)==837 and len(decisions)==838, 'Public/screening control row count differs')
    final_public={}; initial={}
    for rows,target in ((public,final_public),(decisions,initial)):
        for row in rows:
            source=row['source']; key=source_key(source)
            require(key in original and key not in target and source==original[key], 'Screening original/source identity join differs')
            if target is initial and row['decision']=='PRESERVE_LOCAL_EXCLUDED_FROM_PUBLIC_ARCHIVE':
                require(set(row)=={'decision','reason','reason_kind','source'} and row['reason_kind']=='ValueError'
                    and row['reason'], 'Initial schema exclusion differs')
            else:
                require(row['identity_rechecked_before_handle_after'] is True and row['sha256_observed']==source['sha256']
                    and row['bytes_screened']==source['bytes'], 'Actual screening byte/identity receipt differs')
            target[key]=row
    require(set(initial)==set(original), 'Initial screening selection incomplete')
    for row in public:
        require(row['private_signature_scan']=='FULL_BYTES_NO_MATCH'
            and row['decision'] in ('PUBLIC_SCIENTIFIC_SCOPE_SCREENED_ORIGINAL_BYTES','PUBLIC_SCIENTIFIC_SCOPE_EXACT_SCHEMA_REVIEWED'), 'Public screening decision differs')
    resolved={r['relative_path']:r for r in review['manual_schema_resolutions']}
    exact={r['source']['relative_path']:r for r in public if r['decision']=='PUBLIC_SCIENTIFIC_SCOPE_EXACT_SCHEMA_REVIEWED'}
    initial_excluded={r['source']['relative_path'] for r in decisions if r['decision']=='PRESERVE_LOCAL_EXCLUDED_FROM_PUBLIC_ARCHIVE'}
    require(set(resolved)==set(exact)==initial_excluded and all(r['sha256']==exact[n]['source']['sha256'] and r['bytes']==exact[n]['source']['bytes'] for n,r in resolved.items()), 'Nine exact schema resolutions differ')
    excluded=exclusions['files']; require(len(excluded)==1 and exclusions['schema']=='MASTER_PUBLIC_HISTORY02_PUBLIC_EXCLUSIONS_V1', 'Explicit exclusion schema/count differs')
    ex=excluded[0]; ex_source=ex['source']; ex_key=source_key(ex_source)
    require(ex_source==original[ex_key] and ex_key not in final_public and ex_source['bytes']==1025
        and ex_source['relative_path']=='.work/review2/stage05_raw_review/installed_rejected_serializer.txt'
        and ex_source['sha256']=='574547f9584dafce870492810ab02be990fe022939edd5a797292c473625027b'
        and ex['whole_file_exclusion_no_redaction'] is True and ex['private_content_match'] is False
        and ex['decision']=='PRESERVE_LOCAL_EXCLUDED_FROM_PUBLIC_ARCHIVE'
        and ex['reason']=='COPIED_MACSYFINDER_SOURCE_FRAGMENT_PACKAGE_COPYRIGHT_AND_COPYING_NOT_AVAILABLE_IN_RETAINED_LOOSE_EVIDENCE'
        and set(final_public)|{ex_key}==set(original), 'Explicit source-notice exclusion differs')
    seen=set(); per_asset=collections.Counter(); per_bytes=collections.Counter()
    for row in mapping['files']:
        key=row['original_path']; require(key in final_public and key not in seen, 'Invented/duplicate837 original mapping')
        seen.add(key); source=original[key]; name='old_C_repo/'+source['relative_path']; asset=row['asset_name']
        require(row['member']==name and row['relative_path']==source['relative_path']
            and row['original_selection_origin']==source['selection_origin'] and row['bytes']==source['bytes']
            and row['sha256']==source['sha256'] and row['original_identity']=={k:source[k] for k in ('device','file_id','link_count','mtime_ns')}
            and asset in observations and observations[asset][name]['sha256']==source['sha256']
            and observations[asset][name]['bytes']==source['bytes'], 'Actual original mapped member differs')
        per_asset[asset]+=1; per_bytes[asset]+=source['bytes']
    require(seen==set(final_public) and sum(per_bytes.values())==983926424
        and all(per_asset[a['name']]==a['original_source_files'] and per_bytes[a['name']]==a['original_source_bytes'] for a in ASSETS), '837 source/per-shard join incomplete')
    for asset in ASSETS:
        require('old_C_repo/'+ex_source['relative_path'] not in observations[asset['name']], 'Excluded source fragment leaked into archive')
    for n,h in scope['initial_inspection_pins'].items(): require(H.sha(data['control/'+n])==h, 'Initial scope control pin differs')
    require(scope['initial_inspection_pins']==review['initial_inspection_pins']
        and scope['public_payloads_sha256']==H.sha(data['control/public_payloads.jsonl'])
        and scope['excluded_files_sha256']==INSPECTION_HASHES['excluded_files.json']
        and scope['manual_scope_review_sha256']==INSPECTION_HASHES['manual_scope_review.json']
        and inspection['input_pins']==SOURCE_INPUTS, 'Original source proof/scope pin chain differs')
    publication=read('PUBLICATION_CONTROL_SHA256.json')
    for n,row in publication.items():
        require(n in CONTROL_HASHES and H.sha(controls[PREFIX+n])==row['sha256'] and len(controls[PREFIX+n])==row['bytes'], 'Publication control byte join differs')
    result.update(shards=receipt_shards,zip_members=882,sha256_manifest_payload_members=879,original_source_files=837,
        original_source_bytes=983926424,original_selection_files=838,documented_whole_file_exclusions=excluded,
        selection_origins={'UNMATCHED_619_PRESERVE':619,'CONSERVATIVE_219_HOLD':219},
        included_origins={'UNMATCHED_619_PRESERVE':618,'CONSERVATIVE_219_HOLD':219},
        screening_evidence_bound_not_rerun=True,original_source_payloads_reread=False,
        nested_fixture_screening_records_bound=24,manual_exact_schema_resolutions_bound=9,
        historical_native_closure='NOT_INFERRED_UNKNOWN_REMAINS_UNKNOWN',
        limitations=['Preservation of original history bytes does not certify historical execution or biological acceptance',
            'One headerless source fragment is excluded because retained package notices were unavailable',
            'Original privacy and nested-container screening evidence is pinned; screening is not rerun by this byte verifier'])
    if not args.local_inspect: H.end_release(args,release,selected,result)
    result['state']='PASS_LOCAL_HISTORY02_882_MEMBERS_837_ORIGINALS_REMOTE_NOT_RUN' if args.local_inspect else 'PASS_FRESH_REMOTE_HISTORY02_3_SHARDS_882_MEMBERS_837_ORIGINALS_1_EXPLICIT_EXCLUSION'

if __name__=='__main__':
    H.execute_readback(H.cli(__doc__),'public_history02',verify_history)
