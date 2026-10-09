"""Archive screened original scientific history in bounded deterministic shards.

Public preservation only. No source deletion, upload, G/WSL/native execution or
historical closure inference. Every archived source byte must match the fixed
original hash and identity; any packing drift stops with no accepted index.
"""
from pathlib import Path
import ctypes,datetime,hashlib,importlib.util,json,os,re,stat,zipfile

WORK=Path(__file__).resolve().parent;SCOPE=WORK/'master_public_history02_inspection'
OUT=WORK/'master_public_history02'
SCOPE_SHA='dec1dfb957965ca293180efba04f43498105fc0a46056aff1d7e551f72686032'
INSPECTOR_SHA='671b20fc3f8b89c214d9fc50a3b793275caafce72bac03bee4379468793dcfc0'
FINALIZER_SHA='a8068ac628d8249e02af65954694dd8f3f2a19aef0441657a55f4756f388f1b4'
CHUNK=1024**2;LOGICAL_LIMIT=320*1024**2;ASSET_LIMIT=500*1024**2

def must(ok,message):
    if not ok:raise ValueError(message)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
def pack_json(value):return(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()

def main():
    must(os.name=='nt','Windows C-only preservation namespace required');must(not OUT.exists(),'Preserve prior archive namespace')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    kernel.GetPriorityClass.argtypes=[ctypes.c_void_p];kernel.GetPriorityClass.restype=ctypes.c_uint32
    handle=kernel.GetCurrentProcess();must(kernel.SetPriorityClass(handle,0x4000),'Own below-normal CPU priority request failed')
    must(kernel.GetPriorityClass(handle)==0x4000,'Own below-normal CPU priority readback failed')
    own_sha=sha(__file__);must(sha(SCOPE/'public_scope.json')==SCOPE_SHA,'Frozen public scope differs')
    scope=read(SCOPE/'public_scope.json')
    must(scope['state']=='SCOPED_ORIGINAL_BYTES_READY_FOR_LOCAL_ARCHIVE_ONLY' and scope['public_files']==837
         and scope['public_bytes']==983926424 and scope['excluded_files']==1 and scope['excluded_bytes']==1025,
         'Exact837public/1excluded scope differs')
    pins={**scope['initial_inspection_pins'],'public_scope.json':SCOPE_SHA,
        'manual_scope_review.json':scope['manual_scope_review_sha256'],'public_payloads.jsonl':scope['public_payloads_sha256'],
        'excluded_files.json':scope['excluded_files_sha256']}
    for name,digest in pins.items():must(sha(SCOPE/name)==digest,'Frozen source-scope control differs: '+name)
    for name,digest in [('inspect_public_history02.py',INSPECTOR_SHA),('finalize_public_history02_scope.py',FINALIZER_SHA)]:
        must(sha(WORK/name)==digest,'Executed source-scope code differs')
    spec=importlib.util.spec_from_file_location('history02_pinned_read_guards',WORK/'inspect_public_history02.py')
    I=importlib.util.module_from_spec(spec);spec.loader.exec_module(I)
    selected=read(SCOPE/'selection.json')['files'];selected_by={r['path']:r for r in selected}
    decisions=[json.loads(line) for line in(SCOPE/'public_payloads.jsonl').read_text().splitlines()]
    sources=[r['source'] for r in decisions]
    must(len(sources)==len({r['path'] for r in sources})==837 and sum(r['bytes'] for r in sources)==983926424
         and all(selected_by.get(r['path'])==r for r in sources),'Exact screened selected-source bindings differ')
    for r in decisions:
        must(r['decision'].startswith('PUBLIC_SCIENTIFIC_SCOPE') and r['sha256_observed']==r['source']['sha256']
             and r['bytes_screened']==r['source']['bytes'] and r['identity_rechecked_before_handle_after'] is True
             and r['private_signature_scan']=='FULL_BYTES_NO_MATCH','Incomplete or private screened file cannot be archived')
        I.permitted_row(r['source'])
    groups=[];current=[];size=0
    for source in sorted(sources,key=lambda r:r['relative_path']):
        must(source['bytes']<=LOGICAL_LIMIT,'Individual source exceeds bounded shard budget')
        if current and size+source['bytes']>LOGICAL_LIMIT:groups.append(current);current=[];size=0
        current.append(source);size+=source['bytes']
    if current:groups.append(current)
    must(len(groups)==3,'Expected safe three-shard split differs')
    OUT.mkdir();began=utc();assets=[];mapping=[]
    result={'schema':'MASTER_PUBLIC_HISTORY02_LOCAL_BUILD_V1','state':'IN_PROGRESS_NO_PURGE','started_utc':began,
        'builder_sha256':own_sha,'source_scope_sha256':SCOPE_SHA,'selection_files':838,'selection_bytes':983927449,
        'public_files':837,'public_bytes':983926424,'excluded_files':1,'excluded_bytes':1025,
        'source_deletions':0,'network_calls':0,'g_writes':0,'wsl_starts':0,'native_launches':0,
        'historical_native_closure':'NOT_INFERRED_UNKNOWN_REMAINS_UNKNOWN','scientific_acceptance':'NONE_HISTORY_PRESERVATION_ONLY',
        'whole_file_exclusion_no_redaction':True,'actual_remote_export':'NOT_RUN','shards':assets,
        'bounded_block_bytes':CHUNK,'maximum_logical_source_bytes_per_shard':LOGICAL_LIMIT,
        'maximum_asset_bytes_exclusive':ASSET_LIMIT,'observed_own_priority_class':kernel.GetPriorityClass(handle)}
    try:
        attribution=('Public scientific history, original bytes and states.\n\n'
            'Retained project checker/review/test sources and shims are preserved unchanged. Generated native/profile outputs retain their original headers.\n'
            'The headerless MacSyFinder TsvRejectedCandidatesSerializer fragment is entirely excluded and remains local. Exact package COPYRIGHT/COPYING notices were not available in the loose retained evidence. The separate scope review records Sophie Abby, Bertrand Neron, Institut Pasteur/CNRS2014-2024 and GPLv3-or-later from the exact retained vendor header; it does not relabel or redistribute the excluded fragment.\n'
            'Model/profile names and hashes identify PADLOC2.0 database5027 and DefenseFinder3/MacSyFinder2.1.4 scientific evidence. No model package or toolchain executable is copied by this history archive.\n'
            'Source scripts and fixtures are archival data. No archived code is executed. Native historical exit/closure fields remain exactly as recorded; this archive establishes neither closure nor scientific completion.\n')
        (OUT/'ATTRIBUTION_AND_SCOPE.txt').write_text(attribution,encoding='utf-8',newline='\n')
        mapping=[{'original_path':r['path'],'original_identity':{k:r[k] for k in('device','file_id','mtime_ns','link_count')},
            'relative_path':r['relative_path'],'bytes':r['bytes'],'sha256':r['sha256'],
            'asset_name':f'master_public_history02-{index:03d}.zip','member':'old_C_repo/'+r['relative_path'],
            'original_selection_origin':r['selection_origin']} for index,group in enumerate(groups,1) for r in group]
        global_map={'schema':'MASTER_PUBLIC_HISTORY02_ORIGINAL_MEMBER_MAPPING_V1','state':'PRESERVATION_ONLY_NO_PURGE',
            'source_scope_sha256':SCOPE_SHA,'files':mapping,'excluded_source_file_count':1,'source_deletions':0,
            'historical_native_closure':'NOT_INFERRED','original_bytes_unchanged':True}
        write(OUT/'original_member_mapping.json',global_map)
        common={**{'control/'+name:SCOPE/name for name in pins},
            'control/original_member_mapping.json':OUT/'original_member_mapping.json',
            'ATTRIBUTION_AND_SCOPE.txt':OUT/'ATTRIBUTION_AND_SCOPE.txt',
            **{'code/'+name:WORK/name for name in('inspect_public_history02.py','finalize_public_history02_scope.py','build_public_history02.py','test_public_history02_screen.py')}}
        common_pins={name:{'bytes':p.stat().st_size,'sha256':sha(p)} for name,p in common.items()}
        source_binding={'schema':'MASTER_PUBLIC_HISTORY02_BUILD_SOURCE_BINDING_V1','state':'LOCAL_BUILD_ONLY_NO_PURGE',
            'builder_sha256':own_sha,'inspector_sha256':INSPECTOR_SHA,'scope_finalizer_sha256':FINALIZER_SHA,
            'scope_sha256':SCOPE_SHA,'common_payload_inputs':common_pins,'source_input_controls':I.INPUTS,
            'copied_third_party_source':False,'included_source_file_count':837,'excluded_source_file_count':1,
            'historical_native_closure':'NOT_INFERRED','raw_private_events_prompts_usage_exported':False,
            'redaction':'NONE_WHOLE_FILES_EXCLUDED','source_deletions':0,'network_calls':0,'g_writes':0,'wsl_starts':0,'native_launches':0}
        write(OUT/'source_binding.json',source_binding);common['control/source_binding.json']=OUT/'source_binding.json'
        common_pins['control/source_binding.json']={'bytes':(OUT/'source_binding.json').stat().st_size,'sha256':sha(OUT/'source_binding.json')}
        for index,group in enumerate(groups,1):
            name=f'master_public_history02-{index:03d}.zip';partial=OUT/(name+'.unverified');final=OUT/name
            expected={**common_pins,**{'old_C_repo/'+r['relative_path']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in group}}
            sums=''.join(pin['sha256']+'  '+member+'\n' for member,pin in sorted(expected.items())).encode()
            expected['SHA256SUMS.txt']={'bytes':len(sums),'sha256':hashlib.sha256(sums).hexdigest()}
            scientific={r['relative_path']:r for r in group}
            with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
                for member in sorted(expected):
                    zi=zipfile.ZipInfo(member,(2026,10,9,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16
                    if member=='SHA256SUMS.txt':z.writestr(zi,sums);continue
                    r=scientific.get(member[len('old_C_repo/'):]) if member.startswith('old_C_repo/') else None
                    path=I.permitted_row(r) if r else common[member]
                    I.plain(path);before=path.lstat()
                    if r:must(I.signature(before)==I.row_signature(r),'Original scientific source identity drift before copy: '+member)
                    h=hashlib.sha256();count=0
                    with path.open('rb') as source,z.open(zi,'w',force_zip64=True) as target:
                        must(I.signature(os.fstat(source.fileno()))==I.signature(before),'Retained exact source handle changed before copy')
                        for block in iter(lambda:source.read(CHUNK),b''):target.write(block);h.update(block);count+=len(block)
                        must(I.signature(os.fstat(source.fileno()))==I.signature(before),'Retained source handle changed during copy')
                    must(I.signature(path.lstat())==I.signature(before) and count==expected[member]['bytes']
                         and h.hexdigest()==expected[member]['sha256'],'Actual copied source byte drift; shard remains unverified: '+member)
            must(partial.stat().st_size<ASSET_LIMIT,'Actual shard exceeds stagewise asset bound')
            verified=[]
            with zipfile.ZipFile(partial) as z:
                must(len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(expected),'Actual shard member set differs')
                for member,pin in sorted(expected.items()):
                    info=z.getinfo(member)
                    must(stat.S_IFMT(info.external_attr>>16)==stat.S_IFREG and not info.flag_bits&1,'Nonregular or encrypted archive member')
                    with z.open(member) as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
                    must(digest==pin['sha256'] and info.file_size==pin['bytes'],'Actual ZIP member differs from exact original/captured input')
                    verified.append({'member':member,**pin,'crc32':f'{info.CRC:08x}','crc_verified':True})
            partial.rename(final)
            asset={'name':name,'path':str(final),'sha256':sha(final),'bytes':final.stat().st_size,
                'original_source_files':len(group),'original_source_bytes':sum(r['bytes'] for r in group),
                'members':verified,'all_member_crc_sha256_and_expected_source_pins_verified':True}
            assets.append(asset);(OUT/(name+'.sha256')).write_text(asset['sha256']+'  '+name+'\n',encoding='ascii',newline='\n')
            print(json.dumps({k:asset[k] for k in('name','sha256','bytes','original_source_files','original_source_bytes')}),flush=True)
        must(sha(__file__)==own_sha,'Loaded builder source drift')
        for member,pin in common_pins.items():must(sha(common[member])==pin['sha256'],'Common control/source code changed while packing')
        for source in sources:must(I.signature(Path(source['path']).lstat())==I.row_signature(source),'Source path identity changed after archival copy')
        result.update(state='LOCAL_THREE_SHARDS_ALL837_ORIGINALS_CRC_SHA_VERIFIED_NO_PURGE',finished_utc=utc(),
            original_member_mapping_sha256=sha(OUT/'original_member_mapping.json'),source_binding_sha256=sha(OUT/'source_binding.json'),
            all_shards_under500MiB=True,all_original_source_identities_stable=True,
            focused_synthetic_screen_tests={'tests':4,'passed':4,'scope':'Privacy event, cross-block credential, byte drift, UNKNOWN historical state preservation'},
            total_compressed_asset_bytes=sum(a['bytes'] for a in assets))
        write(OUT/'build_receipt.json',result)
        write(OUT/'asset_index.json',{'schema':'MASTER_PUBLIC_HISTORY02_ASSET_INDEX_V1','state':'LOCAL_VERIFIED_REMOTE_NOT_RUN',
            'build_receipt_sha256':sha(OUT/'build_receipt.json'),'source_binding_sha256':sha(OUT/'source_binding.json'),
            'original_member_mapping_sha256':sha(OUT/'original_member_mapping.json'),'source_scope_sha256':SCOPE_SHA,
            'assets':[{k:a[k] for k in('name','bytes','sha256','original_source_files','original_source_bytes')} for a in assets],
            'public_files':837,'excluded_files':1,'source_deletions':0,'scientific_acceptance':'NONE_HISTORY_PRESERVATION_ONLY'})
        print(json.dumps({k:result[k] for k in('state','public_files','public_bytes','excluded_files','excluded_bytes','total_compressed_asset_bytes')},indent=2),flush=True)
    except BaseException as error:
        result.update(state='FAILED_HISTORY02_BUILD_NO_PUBLIC_ACCEPTANCE_OR_PURGE',finished_utc=utc(),
            error={'kind':type(error).__name__,'message':str(error)})
        write(OUT/'failed_build_receipt.json',result);raise

if __name__=='__main__':main()
