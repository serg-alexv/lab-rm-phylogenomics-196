"""Byte readback of source-readiness evidence; never rereads genome/runtime payloads.

The 1.89GB source hashes are retained actual checker evidence, not a new payload
verification or scientific/native-execution acceptance by this archive verifier.
"""
from pathlib import Path, PureWindowsPath
import collections, hashlib, importlib.util, json, re, sys

sys.dont_write_bytecode=True
WORK=Path(__file__).resolve().parent
HELPER_SHA='6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691'
helper=WORK/'verify_master_public_components01_remote.py'
if hashlib.sha256(helper.read_bytes()).hexdigest()!=HELPER_SHA:raise RuntimeError('Readback primitive source pin differs')
spec=importlib.util.spec_from_file_location('readiness_readback_primitives',helper)
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
PREFIX='reports/master_run/20261009/preparation/source_readiness01/'
BUILD_SHA='952ad1da9a4d623045e7f1d871ce70578569d1a276f0f5a9e3abf6eb9175e77b'
COMPLETION_SHA='0827820b33285a6f40e9ed5fa62970202f175228035189486f2183c21edc675e'
ASSETS=[dict(name='master_stage5_source_readiness01.zip',bytes=853741,
    sha256='b06723bf684d76084072d710a0573b34137bc097b5a21f1069077ec69dc6a447')]
CODE={'build_stage5_readiness_archive.py':'8d6561407aeb525ce7ddbe0d9085f5f803a8f288c6cb9e4f89f880bf13c5d97c',
    'stage5_source_readiness.py':'60fb6863ec593f422a42a8a23e0e6303a5f7891700adc5237aa116c8c8763071',
    'stage5_source_readiness_attempt01.py':'126c2012271a86217179384d42d1980afc531b094f9a0fdbf553bf400826a16e',helper.name:HELPER_SHA}
ANCHORS={
 'stage5_source_readiness_actual_02/receipt.json':'400b37a260676f373a627bec66d2004c19fd7ec191961b7228f69b3d63984fb1',
 'stage5_source_readiness_actual_02/actual_file_hashes.jsonl':'6fe8267c7ee7305e2768530f84703401d2bcaa5433e2c6f542bc367a048cc7f1',
 'stage5_source_readiness_actual_02/per_accession.jsonl':'faa3060d08d7646ab4913108a28ac868699a0bc62fd9f337fc131c98dc9997c8',
 'stage5_accepted_source_pins.json':'a63e9c2b987ecabaa7457d4ab26ad0d6e086cc2488066a92647e72207542de84',
 'stage5_source_readiness_actual_01/receipt.json':'10cb41419f60c4c19ecfddfa74b437fd619f2f2d9e21da159d1cee9e4ee7b90f',
 'stage5_support_code_readback_01.json':'b69abf3b05547af575b0b6badd97d870cc077b73a3a3697444ce14efe49db28c'}
ROOT=PureWindowsPath(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
PIN_CONTROL=PureWindowsPath(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\stage5_accepted_source_pins.json')

def lines(z,name):
    with z.open(name) as stream:
        return [json.loads(line) for line in stream]

def verify(args,out,result):
    extras={PREFIX+'completion.json':(WORK/'stage5_source_readiness_completion.json',COMPLETION_SHA)}
    codes={**CODE,Path(__file__).name:A.digest(__file__)}
    raw=A.get_controls(args,{'build_receipt.json':BUILD_SHA},codes,PREFIX,
        WORK/'stage5_source_readiness01',out,result,extras)
    build=json.loads(raw[PREFIX+'build_receipt.json']);completion=json.loads(raw[PREFIX+'completion.json'])
    A.require(build['schema']=='STAGE05_SOURCE_READINESS_AUDIT_ARCHIVE_V1'
        and build['state']=='PASS_LOCAL_ARCHIVE_CRC_SHA_ONLY' and build['bytes']==ASSETS[0]['bytes']
        and build['sha256']==ASSETS[0]['sha256'] and build['scientific_acceptance_created'] is False
        and build['native_execution']=='NOT_RUN', 'Readiness archive build contract differs')
    A.require(completion['schema']=='STAGE05_SOURCE_READINESS_COMPLETION_V1'
        and completion['state']=='PASS_CURRENT_SOURCE_BYTES_AND_SUPPORT_CODE_ONLY'
        and completion['source_accessions']==196 and completion['source_files']==12812
        and completion['source_bytes']==1893101586 and completion['source_failures']==0
        and completion['source_reader_execution']['actual_terminal_exit_code']==0
        and completion['source_reader_execution']['child_processes_spawned']==0
        and completion['source_reader_execution']['scope']=='READ_ONLY_SOURCE_CHECKER_PROCESS_ONLY_NOT_NATIVE_SCIENTIFIC_CLOSURE'
        and completion['detector_execution']==completion['curation']==completion['runtime_discovery']=='NOT_RUN'
        and completion['new_upstream_acceptance_created'] is False, 'Actual source-checker completion scope differs')
    release=selected=None
    if not args.local_inspect:release,selected=A.begin_release(args,ASSETS,out,result)
    path=(WORK/'stage5_source_readiness01' if args.local_inspect else out)/ASSETS[0]['name']
    z,observed=A.verify_zip(path,ASSETS[0],A.member_table(build['members']))
    with z:
        A.require(len(observed)==26 and set(observed)==set(build['original_controls'])|{'SHA256SUMS.txt'}, 'Exact26 evidence member scope differs')
        A.bind_inputs({n:{k:r[k] for k in ('bytes','sha256')} for n,r in build['original_controls'].items()},observed)
        for n,h in ANCHORS.items():A.require(observed[n]['sha256']==h,'Independent readiness evidence anchor differs: '+n)
        for n,h in CODE.items():
            if n!=helper.name:A.require(observed[n]['sha256']==h,'Archived source checker/builder differs')
        for name,row in completion['files'].items():
            if name=='stage5_source_readiness01/build_receipt.json':A.require(row['sha256']==BUILD_SHA,'Completion build pin differs')
            elif name=='stage5_source_readiness01/master_stage5_source_readiness01.zip':A.require(row['sha256']==ASSETS[0]['sha256'] and row['bytes']==ASSETS[0]['bytes'],'Completion outer pin differs')
            else:A.require(name in observed and observed[name]['sha256']==row['sha256'] and observed[name]['bytes']==row['bytes'],'Completion source/control member differs')
        read=lambda n:json.loads(z.read(n))
        final=read('stage5_source_readiness_actual_02/receipt.json');failed=read('stage5_source_readiness_actual_01/receipt.json')
        pins=read('stage5_accepted_source_pins.json');support=read('stage5_support_code_readback_01.json')
        A.require(final['schema']=='STAGE05_CURRENT_SOURCE_BYTE_READINESS_V1'
            and final['status']=='PASS_CURRENT_CANONICAL_SOURCE_BYTES_ONLY' and final['accessions_checked']==final['passed']==196
            and final['failed']==0 and final['declared_source_files']==12812 and final['declared_source_bytes']==1893101586
            and final['stage4_tree_consumed'] is False and final['upstream_acceptance_created'] is False
            and final['detector_execution']==final['runtime_discovery']==final['curation']=='NOT_RUN'
            and final['source_checker_sha256']==CODE['stage5_source_readiness.py'], 'Final196 byte-check contract differs')
        for n,h in final['files'].items():A.require(observed['stage5_source_readiness_actual_02/'+n]['sha256']==h,'Final hash ledger pin differs')
        A.require(pins['schema']=='STAGE05_ACCEPTED_SOURCE_PINS_V1' and len(pins['source_receipts'])==196
            and pins['approved_accessions_sha256']==final['approved_accessions_sha256'], 'Exact approved source panel differs')
        rows=lines(z,'stage5_source_readiness_actual_02/per_accession.jsonl')
        records=lines(z,'stage5_source_readiness_actual_02/actual_file_hashes.jsonl')
        per={r['accession']:r for r in rows};group=collections.defaultdict(list)
        A.require(len(rows)==len(per)==196 and set(per)==set(pins['source_receipts']), 'Exact196 accession ledger differs')
        for r in records:
            A.require(r['accession'] in per and type(r['bytes']) is int and r['bytes']>=0 and A.is_sha(r['sha256'])
                and all(type(r[k]) is int and r[k]>0 for k in ('device','inode','mtime_ns')), 'Invalid retained actual hash record')
            group[r['accession']].append(r)
        source_files=source_bytes=control_records=0
        for accession,row in per.items():
            witness=pins['source_receipts'][accession];rs=group[accession]
            A.require(row['status']=='PASS_CURRENT_ACCEPTED_SOURCE_BYTES_ONLY' and row['source_receipt_sha256']==witness['sha256']
                and len(rs)==row['source_files']+9, 'Per-accession PASS/source control accounting differs')
            panel=rs[0];active=rs[1]
            A.require(panel['path']==str(ROOT/'config'/'approved_accessions.txt') and panel['sha256']==pins['approved_accessions_sha256']
                and panel['role']=='CANONICAL_G_SOURCE' and active['path']==str(PIN_CONTROL)
                and active['role']=='ACTIVE_C_ACCEPTED_SOURCE_PIN_CONTROL' and active['sha256']==ANCHORS['stage5_accepted_source_pins.json']
                and active['bytes']==observed['stage5_accepted_source_pins.json']['bytes'], 'Canonical panel/activeC source-control roles differ')
            for actual,(rel,expected) in zip(rs[2:8],sorted(pins['accepted_files'].items())):
                A.require(actual['path']==str(ROOT.joinpath(*rel.split('/'))) and actual['sha256']==expected
                    and actual['role']=='CANONICAL_G_SOURCE','Six accepted canonical control pins differ')
            receipt=rs[8];base=ROOT/'.work'/'source_locus_inputs_v1'/'assemblies'/accession
            A.require(receipt['path']==str(base/'build_receipt.json') and receipt['sha256']==witness['sha256']
                and receipt['bytes']==witness['bytes'] and receipt['role']=='CANONICAL_G_SOURCE', 'Actual source receipt differs from released witness')
            payloads=rs[9:];seen=set()
            for r in payloads:
                p=PureWindowsPath(r['path'])
                A.require(p.is_relative_to(base) and p!=base and '..' not in p.parts and str(p)==r['path']
                    and r['path'] not in seen and r['role']=='CANONICAL_G_SOURCE', 'Declared payload source scope/uniqueness differs')
                seen.add(r['path'])
            A.require(len(payloads)==row['source_files'] and sum(r['bytes'] for r in payloads)==row['source_bytes'], 'Declared payload totals differ')
            source_files+=len(payloads);source_bytes+=row['source_bytes'];control_records+=9
        A.require((source_files,source_bytes,control_records,len(records))==(12812,1893101586,1764,14576), 'Full196 source/control record accounting differs')
        A.require(support['status']=='PASS_CURRENT_NINE_CANONICAL_SUPPORT_SOURCE_BYTES' and len(support['expected'])==len(support['files'])==9
            and support['actual_bytes']==sum(r['bytes'] for r in support['files'])==182212
            and support['runner_sha256']==final['input_code_sha256']['stage5_atomic.py'], 'Nine canonical support-source accounting differs')
        for r in support['files']:
            p=PureWindowsPath(r['path']);A.require(p.is_relative_to(ROOT) and '..' not in p.parts and r['role']=='CANONICAL_G_SOURCE'
                and support['expected'][p.relative_to(ROOT).as_posix()]==r['sha256'], 'Support-source actual hash/pin differs')
        A.require(failed.get('status')!='PASS_CURRENT_CANONICAL_SOURCE_BYTES_ONLY' and failed.get('upstream_acceptance_created') is False,
            'Initial failed checker attempt must remain distinguishable')
        result.update(zip_members=26,internal_sum_entries=25,members=list(observed.values()),
            source_accessions=196,declared_payload_files=12812,declared_payload_bytes=1893101586,
            actual_hash_records=14576,control_hash_records=1764,activeC_pin_control_records=196,
            canonical_support_modules=9,canonical_support_bytes=182212,source_checker_actual_exit_code=0,
            failed_initial_attempt_preserved=True,failed_initial_attempt_status=failed.get('status'),
            original_genome_payloads_reread=False,source_check_execution_rerun=False,
            detector_execution='NOT_RUN',runtime_discovery='NOT_RUN',curation='NOT_RUN',
            stage4_tree_consumed=False,remaining_actual_gates=completion['remaining_actual_gates'])
    if not args.local_inspect:A.end_release(args,release,selected,result)
    result['state']='PASS_LOCAL_READINESS26_MEMBERS_196_SOURCE_LEDGERS_REMOTE_NOT_RUN' if args.local_inspect else 'PASS_FRESH_REMOTE_READINESS26_MEMBERS_196_SOURCE_LEDGERS_NATIVE_NOT_RUN'

if __name__=='__main__':A.execute_readback(A.cli(__doc__),'stage5_source_readiness01',verify)
