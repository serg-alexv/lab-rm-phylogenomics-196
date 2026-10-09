"""Resolve exact known scientific schema flags; exclude unlicensed source fragment."""
from pathlib import Path
import hashlib,importlib.util,io,json,os,zipfile

WORK=Path(__file__).resolve().parent;OUT=WORK/'master_public_history02_inspection'
PINS={'inspection.json':'dc911094cae2057c264bd4e30e4c2d701d6e0a1dbf140b551cb71f89dd3a8fc5',
      'selection.json':'49437f5106183ec0530b252c85cdaa32f9a3a6e4f7ae17a8217e86549c0f9478',
      'decisions.jsonl':'ac944622cdccd6b9ff67bf6676b92fcd1298d92fb7918692538e98068e16d013'}
INSPECTOR_SHA='671b20fc3f8b89c214d9fc50a3b793275caafce72bac03bee4379468793dcfc0'
OVERRIDES={
 '.work/review2/cached_review_summary.json':('8e96a003862a7d88d0aa5849d23d6d79581274332bdf0a8987cd344428a7f4fe','ASSEMBLY_VALIDATION_SNAPSHOT_SUMMARY'),
 '.work/review2/repaired/cached_review_summary.json':('6700a70fd55b91315110c96fcfe4d258ab26fd45e6bbec20f6ec2ef4c272aa33','ASSEMBLY_VALIDATION_SNAPSHOT_SUMMARY'),
 '.work/review2/repaired_final/cached_review_summary.json':('ae42450518b76127d8c261f9b37fe06b98b3fd65680a82f260bbbcda6a09cd54','ASSEMBLY_VALIDATION_SNAPSHOT_SUMMARY'),
 '.work/review2/cds_exception_summary.json':('c5bc7b43d3b859f661aeb941259a95d7fdc183d5a79aa6ceb07e05414cc1eecf','CDS_EXCEPTION_COUNTS'),
 '.work/review2/omitted_partial_terminal_analysis.json':('16fb98fe13c0e2b96523b642debc72627dcebcd7a60e84d17ae69fa882638bf0','PARTIAL_CDS_TERMINAL_TRANSLATION_ROWS'),
 '.work/review2/review_evidence.json':('0ddb77c421cf90cfd320e0f9c2c54aa44eaa13db1e581b8db2a0954c71dfbc92','SCIENTIFIC_PARSER_AND_RESOURCE_REVIEW_LIMITS'),
 '.work/review2/stage05_raw_review/native_posttreatment_fixture/installed_source_sha256.json':('2c422572a19e9a7388ec9b72b8798e27e554e894394b7aad51eb38783891a9d5','INSTALLED_NATIVE_SOURCE_PATH_HASH_METADATA_ONLY'),
 '.work/review2/detector_parser_review/explicit_empty.tsv':('3026e567547840038ddc80c8ddb144b59c9f01b05fcf5a8a6ead62b674086c6c','EXPLICIT_NO_SYSTEMS_NATIVE_PARSER_FIXTURE'),
 '.work/review2/stage05_raw_review/native_rejected_positive_fixture.tsv':('c36489c67b20ea99d0662c930dc91306dd9bc21c54170b85fcb1e2282313ab6c','COMMENTED_SYNTHETIC_REJECTED_ROW_FIXTURE')}
EXCLUDED='.work/review2/stage05_raw_review/installed_rejected_serializer.txt'

def must(ok,message):
    if not ok:raise ValueError(message)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')

def verify_schema(data,kind):
    if kind=='EXPLICIT_NO_SYSTEMS_NATIVE_PARSER_FIXTURE':must(data==b'# No Systems found\r\n','Exact explicit native empty fixture differs');return
    if kind=='COMMENTED_SYNTHETIC_REJECTED_ROW_FIXTURE':
        must(data.startswith(b'# SYNTHETIC serializer-only fixture; no biological search\n')
             and b'candidate_id\treplicon\tmodel_fqn\tcluster_id\thit_id' in data,'Exact commented native rejected fixture differs');return
    value=json.loads(data)
    if kind=='ASSEMBLY_VALIDATION_SNAPSHOT_SUMMARY':
        must(isinstance(value,dict) and {'assemblies','cached_package_count','status_counts','errors','reviews'}<=set(value)
             and isinstance(value['assemblies'],list),'Scientific cached validation snapshot shape differs')
    elif kind=='CDS_EXCEPTION_COUNTS':must(isinstance(value,dict) and {'issue_count','cds_mismatch_count','partial_difference_patterns'}<=set(value),'CDS count summary shape differs')
    elif kind=='PARTIAL_CDS_TERMINAL_TRANSLATION_ROWS':must(isinstance(value,list) and all({'key','three_prime_partial','terminal_nt','virtual_terminal_aa','complete_codons_match'}<=set(r) for r in value),'Partial CDS terminal review row shape differs')
    elif kind=='SCIENTIFIC_PARSER_AND_RESOURCE_REVIEW_LIMITS':must(isinstance(value,dict) and {'review_status','cached_package_error_count','streaming_io_checks','measured_resource_snapshot','evidence_limit'}<=set(value),'Scientific parser snapshot/limits shape differs')
    elif kind=='INSTALLED_NATIVE_SOURCE_PATH_HASH_METADATA_ONLY':must(isinstance(value,dict) and all(k.startswith('/mnt/c/') and k.endswith('.py') and len(v)==64 for k,v in value.items()),'Installed scientific source path/hash shape differs')
    else:raise ValueError('Unknown manual scientific review kind')

def main():
    must(not(OUT/'public_scope.json').exists(),'Preserve prior scope finalization')
    for name,digest in PINS.items():must(sha(OUT/name)==digest,'Frozen initial inspection changed')
    inspector=WORK/'inspect_public_history02.py';must(sha(inspector)==INSPECTOR_SHA,'Inspection source drift')
    spec=importlib.util.spec_from_file_location('history02_pinned_inspector',inspector);I=importlib.util.module_from_spec(spec);spec.loader.exec_module(I)
    original=[json.loads(s) for s in(OUT/'decisions.jsonl').read_text().splitlines()]
    must(len(original)==838,'Exact838 decisions required');approved=[];excluded=[];manual=[];zip_metadata=[];project_sources=[]
    for r in original:
        source=r['source'];rel=source['relative_path'];path=I.permitted_row(source)
        if rel==EXCLUDED:
            must(source['sha256']=='574547f9584dafce870492810ab02be990fe022939edd5a797292c473625027b','Exact copied-source fragment differs')
            excluded.append({'source':source,'decision':'PRESERVE_LOCAL_EXCLUDED_FROM_PUBLIC_ARCHIVE',
                'reason':'COPIED_MACSYFINDER_SOURCE_FRAGMENT_PACKAGE_COPYRIGHT_AND_COPYING_NOT_AVAILABLE_IN_RETAINED_LOOSE_EVIDENCE',
                'private_content_match':False,'whole_file_exclusion_no_redaction':True});continue
        if rel in OVERRIDES:
            expected,kind=OVERRIDES[rel];must(source['sha256']==expected and source['bytes']<=I.JSON_LIMIT,'Exact bounded manual schema selection differs')
            I.plain(path);before=path.lstat();must(I.signature(before)==I.row_signature(source),'Manual-review source identity changed')
            with path.open('rb') as f:
                must(I.signature(os.fstat(f.fileno()))==I.signature(before),'Manual-review retained handle differs')
                data=f.read(I.JSON_LIMIT+1);must(I.signature(os.fstat(f.fileno()))==I.signature(before),'Manual-review handle changed')
            must(I.signature(path.lstat())==I.signature(before) and len(data)==source['bytes'] and hashlib.sha256(data).hexdigest()==expected,'Manual-review exact source bytes changed')
            data.decode('utf-8-sig')
            must(not any(pattern.search(data) for pattern in I.PATTERNS.values()),'Manual-review private signature matched; whole file remains excluded')
            verify_schema(data,kind)
            r={'source':source,'decision':'PUBLIC_SCIENTIFIC_SCOPE_EXACT_SCHEMA_REVIEWED',
               'content':{'kind':kind,'scope_basis':'Exact original source hash, complete-byte privacy screen, inspected scientific count/row/fixture schema; original states preserved'},
               'sha256_observed':expected,'bytes_screened':len(data),'identity_rechecked_before_handle_after':True,
               'private_signature_scan':'FULL_BYTES_NO_MATCH','initial_schema_filter_reason':r.get('reason')}
            manual.append({'relative_path':rel,'sha256':expected,'bytes':len(data),'reviewed_kind':kind})
        must(r['decision'].startswith('PUBLIC_SCIENTIFIC_SCOPE'),'Unresolved file remains excluded rather than silently archived: '+rel)
        if path.suffix=='.zip':
            data=path.read_bytes();must(hashlib.sha256(data).hexdigest()==source['sha256'],'Nested fixture bytes changed')
            must(not any(p.search(data) for p in I.PATTERNS.values()),'Nested compressed container/comment private signature')
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                must(not z.comment and all(not i.comment and not i.extra for i in z.infolist()),'Nested nonpayload metadata requires a separate review')
                zip_metadata.append({'relative_path':rel,'sha256':source['sha256'],'bytes':len(data),
                    'raw_container_signature_scan':'NO_MATCH','archive_comment_bytes':0,'all_member_comments_and_extra_bytes':0})
        if path.suffix=='.py':project_sources.append({'relative_path':rel,'sha256':source['sha256'],
            'basis':'Retained project scientific checker/review/test source under exact review2; original module purpose/AST reviewed; no vendor source directory or third-party copyright/license header identified'})
        approved.append(r)
    must(len(manual)==9 and len(zip_metadata)==24 and len(project_sources)==45 and len(approved)==837 and len(excluded)==1,'Exact scope resolution/count differs')
    vendor=I.ROOT/'.work/detector_review/vendor_stage05_sources/11_macsypy_report.py'
    review={'schema':'MASTER_PUBLIC_HISTORY02_MANUAL_SCOPE_AND_ATTRIBUTION_REVIEW_V1',
        'execution':'EXECUTED_EXACT_SOURCE_SCHEMA_AND_FULL_BYTE_SCREEN','reviewer_id':'input_validation',
        'initial_inspection_pins':PINS,'inspector_sha256':INSPECTOR_SHA,'manual_schema_resolutions':manual,
        'nested_fixture_metadata_screen':zip_metadata,'project_source_scope_reviews':project_sources,
        'third_party_source_exclusions':excluded,'third_party_notice_evidence':{
            'path':str(vendor),'sha256':sha(vendor),'header_authors':['Sophie Abby','Bertrand Neron'],
            'header_copyright':'2014-2024 Institut Pasteur (Paris) and CNRS','header_license':'GPL version3 or later',
            'package_notices_required_by_original_header':['COPYRIGHT','COPYING'],
            'exact_retained_package_notices_available':False,'copied_third_party_source_archived':False},
        'private_payloads_exported':0,'redaction':'NONE_WHOLE_FILES_EXCLUDED','historical_native_closure':'NOT_INFERRED'}
    write(OUT/'manual_scope_review.json',review)
    with(OUT/'public_payloads.jsonl').open('x',encoding='utf-8',newline='\n') as f:
        for r in approved:f.write(json.dumps(r,sort_keys=True)+'\n')
    write(OUT/'excluded_files.json',{'schema':'MASTER_PUBLIC_HISTORY02_PUBLIC_EXCLUSIONS_V1','files':excluded})
    final={'schema':'MASTER_PUBLIC_HISTORY02_PUBLIC_SCOPE_V1','state':'SCOPED_ORIGINAL_BYTES_READY_FOR_LOCAL_ARCHIVE_ONLY',
        'selection_files':838,'selection_bytes':983927449,'public_files':837,'public_bytes':sum(r['source']['bytes'] for r in approved),
        'excluded_files':1,'excluded_bytes':1025,'initial_inspection_pins':PINS,'inspector_sha256':INSPECTOR_SHA,
        'scope_finalizer_sha256':sha(__file__),'manual_scope_review_sha256':sha(OUT/'manual_scope_review.json'),
        'public_payloads_sha256':sha(OUT/'public_payloads.jsonl'),'excluded_files_sha256':sha(OUT/'excluded_files.json'),
        'whole_file_exclusions_no_redaction':True,'original_bytes_and_scientific_states_preserved':True,
        'historical_native_closure':'NOT_INFERRED','current_biological_acceptance':'NONE_HISTORY_PRESERVATION_ONLY',
        'network_calls':0,'source_deletions':0,'g_writes':0,'wsl_starts':0,'native_launches':0}
    write(OUT/'public_scope.json',final);print(json.dumps(final,indent=2))

if __name__=='__main__':main()
