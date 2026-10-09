"""Screen exact838 retained history leaves; preserve bytes and exclude ambiguity.

No archive, upload, deletion, WSL, native launch, or historical closure inference.
Full source bytes are streamed with a1MiB block; JSON parsing is bounded to8MiB.
"""
from pathlib import Path,PurePosixPath
from collections import Counter
import ast,codecs,ctypes,datetime,hashlib,io,json,os,re,stat,zipfile

WORK=Path(__file__).resolve().parent
ROOT=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=WORK/'master_public_history02_inspection'
INPUTS={'yesterday_inventory/batch03/preserve_unmatched_or_excluded.jsonl':'bca12c16ff092b2e2fb612608186db728518d0ebf07fad80e1b401ed43ff0593',
        'yesterday_inventory/batch03/file_allowlist.jsonl':'df770f9e49e869c64f61db5720030aceff3b3282d53ee964aae02d228d7c3f64',
        'master_batch03_mapping01/conservative_leaf_assessment.json':'13d89bbfdd2b768501426493c8de0eac8a4076ed1aca789ab87ea1df759b7f1e'}
SCOPES={'.work/review2','.work/source_locus_inputs_v1','.work/stage03_markers_v1','.work/stage04_phylogeny_v2'}
CHUNK=1024**2;JSON_LIMIT=8*1024**2;NESTED_LIMIT=16*1024**2
PRIVATE_NAMES=('codex_events','codex_stderr','continuation_events','continuation_stderr','usage_reset',
    'session_prompt','continuation_prompt','session_transcript','raw_prompt','raw_codex','reasoning_text','hidden_reasoning','token_cache')
PATTERNS={
 'RAW_CODEX_EVENT_OR_HIDDEN_REASONING':re.compile(rb'(?im)^\s*\{[^\r\n]{0,2000}"(?:type|channel)"\s*:\s*"(?:session_meta|turn_context|event_msg|response_item|analysis|reasoning|reasoning_text)"|(?im:^\s*<(?:think|analysis)>)'),
 'RAW_ROLE_PROMPT_RECORD':re.compile(rb'(?im)^\s*\{\s*"role"\s*:\s*"(?:system|developer|user|assistant)"'),
 'PRIVATE_PROMPT_USAGE_OR_SECRET_FIELD':re.compile(rb'(?i)"(?:session_prompt|continuation_prompt|raw_prompt|prompt|messages|token_usage|total_token_usage|rate_limits|api_key|access_token|refresh_token|client_secret|password)"\s*:'),
 'CREDENTIAL_SHAPED_PAYLOAD':re.compile(rb'gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{24,}|sk-[A-Za-z0-9]{32,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?i:Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/-]{12,})')}

def must(ok,message):
    if not ok:raise ValueError(message)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def signature(s):return(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
def row_signature(r):return(r['device'],r['file_id'],r['bytes'],r['mtime_ns'],r['link_count'])
def plain(path):
    must(path.absolute()==path.resolve(),'Resolved source alias outside literal path')
    for p in [path,*path.parents]:
        s=p.lstat();must(not s.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT,'Reparse path not read')
    must(stat.S_ISREG(path.lstat().st_mode),'Nonregular source not read')
def permitted_row(r):
    pp=PurePosixPath(r['relative_path']);scope=r['scope']
    must(pp.as_posix()==r['relative_path'] and not pp.is_absolute() and '..' not in pp.parts
         and scope in SCOPES and r['relative_path'].startswith(scope+'/')
         and str(ROOT.joinpath(*pp.parts))==r['path'],'Candidate path/scope differs')
    must(not {'.private_run','.git','.codex'}.intersection(pp.parts)
         and not any(x in pp.name.casefold() for x in PRIVATE_NAMES),'Private path excluded')
    return Path(r['path'])

def selected_rows():
    for relative,digest in INPUTS.items():must(sha(WORK/relative)==digest,'Exact838 source-control drift: '+relative)
    keep=read(WORK/'master_batch03_mapping01/conservative_leaf_assessment.json')['files_preserved']
    held={r['path']:r for r in keep};must(len(held)==219,'Exact219holdset required')
    rows=[];manifest_hash=hashlib.sha256()
    with (WORK/'yesterday_inventory/batch03/file_allowlist.jsonl').open('rb') as f:
        for line in f:
            manifest_hash.update(line);r=json.loads(line)
            if r['path'] in held:
                must(all(r[k]==held[r['path']][k] for k in ('relative_path','bytes','sha256')),'Held original byte binding differs')
                rows.append(r|{'selection_origin':'CONSERVATIVE_219_HOLD','selection_reason':held[r['path']]['reason']})
    must(manifest_hash.hexdigest()==INPUTS['yesterday_inventory/batch03/file_allowlist.jsonl'] and len(rows)==219,'Full original hold identity lookup differs')
    with (WORK/'yesterday_inventory/batch03/preserve_unmatched_or_excluded.jsonl').open(encoding='utf-8') as f:
        rows += [json.loads(line)|{'selection_origin':'UNMATCHED_619_PRESERVE'} for line in f]
    must(len(rows)==len({r['path'].casefold() for r in rows})==838 and sum(r['bytes'] for r in rows)==983927449,'Exact838selection/accounting differs')
    for r in rows:permitted_row(r)
    return sorted(rows,key=lambda r:r['relative_path'])

def schema(data,relative):
    suffix=PurePosixPath(relative).suffix.casefold();text=data.decode('utf-8-sig')
    if suffix=='.json':
        value=json.loads(text)
        if isinstance(value,dict):
            keys=sorted(value)
            must(bool(set(keys)&{'status','schema','assembly_accession','identity','summary','cases','checks','results','sha256','test','tests','phase','execution','argv','stage04_identity','pid','scientific_state'}),
                 'Unestablished JSON public scientific schema')
            state={k:value[k] for k in ('schema','status','execution','scientific_validation','biological_validation','process_closure_state')
                   if isinstance(value.get(k),str) and re.fullmatch('[A-Za-z0-9_ .:/-]{1,180}',value[k])}
            return {'kind':'SCIENTIFIC_JSON_OR_REVIEW_RECEIPT','top_level_keys':keys,'historical_state_fields':state}
        must(isinstance(value,list) and (not value or isinstance(value[0],dict) and
             bool(set(value[0])&{'profile','profile_name','assembly_accession','locus_key','name','case'})),
             'Unestablished JSON list public scientific schema')
        return {'kind':'SCIENTIFIC_JSON_ROW_ARRAY','rows':len(value),'first_row_keys':sorted(value[0]) if value else []}
    if suffix=='.jsonl':
        count=0;keys=set()
        for line in text.splitlines():
            value=json.loads(line);must(isinstance(value,dict) and isinstance(value.get('argv'),list)
                 and isinstance(value.get('utc'),str),'Unestablished JSONL command-log schema')
            keys.update(value);count+=1
        return {'kind':'HISTORICAL_SCIENTIFIC_COMMAND_JSONL_NO_CLOSURE_INFERENCE','rows':count,'keys':sorted(keys)}
    if suffix=='.py':
        ast.parse(text)
        return {'kind':'PROJECT_SCIENTIFIC_REVIEW_OR_CHECKER_SOURCE','syntax':'AST_PARSE_ONLY_NO_EXECUTION'}
    if suffix=='':
        must(relative.startswith('.work/stage03_markers_v1/shims/') and text.startswith('#!/bin/sh')
             and 'exec /mnt/c/' in text,'Unestablished extensionless public source')
        return {'kind':'PROJECT_SCIENTIFIC_TOOL_SHIM_SOURCE'}
    if suffix in ('.md','.patch','.diff'):
        must(relative.startswith('.work/review2/'),'Document outside scientific review scope')
        return {'kind':'SCIENTIFIC_REVIEW_DOCUMENT_OR_SOURCE_PATCH'}
    if suffix=='.txt':return {'kind':'HISTORICAL_SCIENTIFIC_NATIVE_LOG_OR_PIN_TEXT'}
    if suffix in ('.domtbl','.res_hmm_extract'):return {'kind':'HISTORICAL_SYNTHETIC_NATIVE_PROFILE_PARSER_FIXTURE'}
    raise ValueError('Unsupported or unestablished payload type')

def nested_zip(data):
    members=[];total=0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        must(len(z.infolist())<=1000,'Nested scientific fixture member bound exceeded')
        for i in z.infolist():
            if i.is_dir():continue
            total+=i.file_size;must(total<=NESTED_LIMIT and not i.flag_bits&1,'Nested fixture binary/decompression scope unproven')
            payload=z.read(i);payload.decode('utf-8-sig')
            must(b'\x00' not in payload,'Nested nontext fixture public scope unproven')
            for code,pattern in PATTERNS.items():must(not pattern.search(payload),'Nested fixture excluded: '+code)
            must(not any(x in i.filename.casefold() for x in PRIVATE_NAMES),'Nested private-shaped member name')
            members.append({'member':i.filename,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),
                            'crc32':f'{i.CRC:08x}','crc_verified':True})
    return {'kind':'SCIENTIFIC_NEGATIVE_OR_SYNTHETIC_ZIP_FIXTURE_ORIGINAL_CONTAINER_ONLY',
            'members':members,'uncompressed_bytes':total,'nested_extraction':'NOT_RUN',
            'native_validation_or_test_rerun':'NOT_RUN'}

def inspect_one(r):
    path=permitted_row(r);plain(path);before=path.lstat()
    must(signature(before)==row_signature(r),'Original source identity/size/mtime/link count drift')
    suffix=path.suffix.casefold();small=suffix not in ('.tsv','.tmp')
    must(not small or r['bytes']<=JSON_LIMIT,'Bounded content-schema review unavailable for this file')
    digest=hashlib.sha256();decoder=codecs.getincrementaldecoder('utf-8-sig')('strict')
    full=bytearray();prefix=bytearray();tail=b'';reasons=set();count=0;lines=0
    with path.open('rb') as f:
        must(signature(os.fstat(f.fileno()))==signature(before),'Retained source handle identity differs')
        for block in iter(lambda:f.read(CHUNK),b''):
            digest.update(block);count+=len(block);lines+=block.count(b'\n')
            if small:full.extend(block)
            if len(prefix)<65536:prefix.extend(block[:65536-len(prefix)])
            if suffix!='.zip':
                try:decoder.decode(block)
                except UnicodeDecodeError:reasons.add('NON_UTF8_PUBLIC_SCOPE_UNPROVEN')
                if b'\x00' in block:reasons.add('BINARY_OR_NUL_PUBLIC_SCOPE_UNPROVEN')
                window=tail+block
                for code,pattern in PATTERNS.items():
                    if pattern.search(window):reasons.add(code)
                tail=window[-8192:]
        if suffix!='.zip':
            try:decoder.decode(b'',final=True)
            except UnicodeDecodeError:reasons.add('NON_UTF8_PUBLIC_SCOPE_UNPROVEN')
        must(signature(os.fstat(f.fileno()))==signature(before),'Retained source handle changed during screening')
    must(signature(path.lstat())==signature(before) and count==r['bytes'] and digest.hexdigest()==r['sha256'],
         'Source changed or differs from exact original hash during screening')
    must(not reasons,';'.join(sorted(reasons)))
    if suffix in ('.tsv','.tmp'):
        header=bytes(prefix).splitlines()[0].decode('utf-8-sig') if prefix else ''
        must(not header or '\t' in header or path.name in ('skipped.tsv',),'Unestablished scientific tabular header')
        detail={'kind':'HISTORICAL_SCIENTIFIC_TABULAR_OR_INTERRUPTED_PARTIAL_TABLE','header':header,
                'newline_count':lines,'row_validation':'ORIGINAL_FAILURE_OR_PARTIAL_STATE_PRESERVED_NO_NORMALIZATION'}
    elif suffix=='.zip':detail=nested_zip(bytes(full))
    else:detail=schema(bytes(full),r['relative_path'])
    return {'decision':'PUBLIC_SCIENTIFIC_SCOPE_SCREENED_ORIGINAL_BYTES','content':detail,
            'sha256_observed':digest.hexdigest(),'bytes_screened':count,
            'identity_rechecked_before_handle_after':True,'private_signature_scan':'FULL_BYTES_NO_MATCH',
            'license_review':'PENDING_SEPARATE_SOURCE_ATTRIBUTION_REVIEW' if suffix in ('.py','.txt','') else 'REVIEW_WITH_CODE_ATTRIBUTION_WHERE_APPLICABLE'}

def main():
    must(os.name=='nt','Bounded Windows C source inspection required')
    must(not OUT.exists(),'Preserve previous inspection namespace')
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)
    source_sha=sha(__file__);rows=selected_rows();OUT.mkdir();save(OUT/'selection.json',{'schema':'MASTER_PUBLIC_HISTORY02_EXACT_SELECTION_V1','files':rows})
    began=utc();counts=Counter();kinds=Counter();screened=0
    with (OUT/'decisions.jsonl').open('x',encoding='utf-8',newline='\n') as report:
        for index,r in enumerate(rows,1):
            decision={'source':r}
            try:
                decision.update(inspect_one(r));counts['screened_public_files']+=1;counts['screened_public_bytes']+=r['bytes'];kinds[decision['content']['kind']]+=1
            except (OSError,ValueError,UnicodeError,zipfile.BadZipFile,SyntaxError) as error:
                decision.update(decision='PRESERVE_LOCAL_EXCLUDED_FROM_PUBLIC_ARCHIVE',reason=str(error),reason_kind=type(error).__name__)
                counts['excluded_files']+=1;counts['excluded_bytes']+=r['bytes']
            report.write(json.dumps(decision,sort_keys=True)+'\n');report.flush();screened+=r['bytes']
            if index%50==0:print(json.dumps({'screened_files':index,'scope_bytes':screened,'excluded':counts['excluded_files']}),flush=True)
    must(sha(__file__)==source_sha,'Loaded inspection source bytes changed during run')
    result={'schema':'MASTER_PUBLIC_HISTORY02_SCOPE_INSPECTION_V1','state':'COMPLETE_SCOPE_SCREENING_NO_ARCHIVE_OR_PURGE',
            'started_utc':began,'finished_utc':utc(),'inspector_sha256':source_sha,'input_pins':INPUTS,'selection_files':838,
            'selection_bytes':983927449,'counts':dict(counts),'content_kinds':dict(kinds),'selection_sha256':sha(OUT/'selection.json'),
            'decisions_sha256':sha(OUT/'decisions.jsonl'),'source_deletions':0,'archive_creation':'NOT_RUN','network_calls':0,
            'g_writes':0,'wsl_starts':0,'native_launches':0,'historical_native_closure':'NOT_INFERRED','maximum_block_bytes':CHUNK,
            'maximum_json_or_source_payload_buffer_bytes':JSON_LIMIT,'maximum_nested_zip_uncompressed_bytes':NESTED_LIMIT,
            'whole_file_exclusion_no_redaction':True,'license_attribution_review':'PENDING_BEFORE_ARCHIVE'}
    save(OUT/'inspection.json',result);print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
