"""Independent exact C-byte readback. No producer import or native/live query."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import stat
import struct

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
SPOOL=WORK/'stage5_process_census_62165165c82c4a5d9149d55894f426e8'
RECEIPT_SHA='b8b8a2d46bc6b31c2d54e1b5ed6f681e4e45ce5937b77d1a78d7d11a0d6f8a61'
SOURCE_SHA='16524b8ec20a46ab8ef787d679827d5a0c603be3c54855f8a2074b6c88fec710'
PS_SHA='7bdc78b789d330e52c56d27f685b84940cc1e3824a5fa1c4aa98d93e32f96853'
PUBLIC_NAMES={'started.json','receipt.json','before.spi_metadata.json','after.spi_metadata.json',
              'supplemental.json','supplemental_worker_birth.json','supplemental_worker_terminal.json',
              'supplemental_worker_result.json'}
RAW_NAMES={'before.spi.bin','after.spi.bin'}


def need(ok,message):
    if not ok:raise ValueError(message)


def read(path,limit=8*1024**2):
    path=Path(path);before=path.lstat()
    need(path.parent in (SPOOL,WORK) and stat.S_ISREG(before.st_mode) and before.st_nlink==1
         and not path.is_symlink() and not getattr(before,'st_file_attributes',0)&0x400,
         'Exact plain one-link C evidence required')
    need(before.st_size<=limit,'Bounded evidence size exceeded')
    with path.open('rb') as f:raw=f.read(limit+1)
    after=path.lstat()
    need(len(raw)<=limit and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'Evidence identity/size/mtime drift')
    return raw,dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def decode(raw):
    def unique(items):
        value={}
        for key,item in items:
            need(key not in value,'Duplicate JSON key');value[key]=item
        return value
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))


def native_rows(raw,base):
    """Literal official x64 field layout; no ctypes/producer/parser import."""
    rows=[];seen=set();pos=0
    while True:
        need(pos+256<=len(raw) and len(rows)<4096,'Native header/count invalid')
        step,threads=struct.unpack_from('<II',raw,pos)
        end=pos+step if step else len(raw)
        need((not step or step>=256 and step%8==0) and end<=len(raw),'Native linked extent invalid')
        thread_end=pos+256+threads*80
        need(threads<=65536 and thread_end<=end,'Native thread extent invalid')
        pid=struct.unpack_from('<Q',raw,pos+80)[0]
        need(pid<=0xffffffff and pid not in seen,'Native duplicate/invalid PID');seen.add(pid)
        for index in range(threads):
            need(struct.unpack_from('<Q',raw,pos+256+index*80+40)[0]==pid,'Native thread ownership mismatch')
        length,maximum,address=struct.unpack_from('<HH4xQ',raw,pos+56)
        need(length%2==maximum%2==0 and length<=maximum<=65534,'Native name length invalid')
        name=None
        if maximum:
            start=address-base
            need(thread_end<=start and start+maximum<=end,'Native name outside admitted record')
            name=raw[start:start+length].decode('utf-16-le')
        handles,session=struct.unpack_from('<II',raw,pos+96)
        rows.append(dict(pid=pid,image_name=name,session_id=session,threads=threads,handles=handles,
                         record_offset=pos,record_bytes=end-pos,creation_filetime=None,
                         native_birth_status='UNSUPPORTED_OPAQUE_RESERVED_FIELDS'))
        if not step:break
        pos=end
    return rows


def iso_ft(value):
    value=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    need(value.utcoffset()==dt.timedelta(0),'UTC timestamp required')
    delta=value-dt.datetime(1601,1,1,tzinfo=dt.timezone.utc)
    return (delta.days*86400+delta.seconds)*10000000+delta.microseconds*10


def verify():
    need(Path(__file__).resolve().parent==WORK,'Exact current C checker deployment required')
    need({p.name for p in SPOOL.iterdir()}==PUBLIC_NAMES|RAW_NAMES,'Exact ten-file census spool differs')
    raw_json={};pins=[]
    for name in sorted(PUBLIC_NAMES):
        raw,pin=read(SPOOL/name);raw_json[name]=decode(raw);pins.append(pin)
    receipt=raw_json['receipt.json'];need(next(p['sha256'] for p in pins if Path(p['path']).name=='receipt.json')==RECEIPT_SHA,'Pinned actual receipt differs')
    for name,expected in [('stage5_process_census.py',SOURCE_SHA),('stage5_process_census_cim_query.ps1',PS_SHA)]:
        _,pin=read(WORK/name);need(pin['sha256']==expected,'Exact operative source differs');pins.append(pin)
    need(receipt['source_sha256']==SOURCE_SHA and receipt['state']=='READ_ONLY_DIAGNOSTIC_COMPLETED_NO_CLOSURE_ACCEPTANCE',
         'Diagnostic terminal state/source differs')
    need(receipt['closure_acceptance'] is False and receipt['STOP_removal_authorized'] is False
         and receipt['historical_terminal_reconstructed'] is False and receipt['original_owner_exit_proven'] is False
         and receipt['owner_absence_is_exit_proof'] is False and receipt['historical_clock_continuity_proven'] is False,
         'Unsupported old-scope acceptance/clock/terminal claim')
    need(receipt['original_STOP_unchanged'] is True and receipt['original_lock_released'] is True
         and receipt['original_stop_sha256']=='3de7057780d280d5f204b535207a174e616ca425b5638fe9848a48cfca20838a'
         and receipt['handle_close_errors']==[],'STOP/unlock/handle observation differs')
    lock=receipt['workflow_lock']
    need((lock['volume_serial'],lock['file_index'],lock['creation_filetime'],lock['locked_byte'])==
         (2430728143,844424932784519,134359335921635133,0),'Original lock identity differs')
    started=raw_json['started.json']
    need(started['state']=='FAILED_OR_PARTIAL_DIAGNOSTIC','Started state misclassified')
    for key,value in started.items():
        if key!='state':need(receipt[key]==value,'Started/current bound field differs:'+key)
    exclusions=[];native_sets=[]
    for label in ('before','after'):
        metadata=raw_json[label+'.spi_metadata.json'];native=receipt['native_'+label]
        raw,pin=read(SPOOL/(label+'.spi.bin'));pins.append(pin)
        need(metadata['raw_file']==str(SPOOL/(label+'.spi.bin')) and metadata['raw_bytes']==len(raw)
             and metadata['raw_sha256']==pin['sha256'],'Native raw metadata pin mismatch')
        for key in ('raw_file','raw_sha256','raw_bytes','captured_base_address','attempts'):
            need(native[key]==metadata[key],'Native receipt/raw metadata differs:'+key)
        recomputed=native_rows(raw,metadata['captured_base_address'])
        need(recomputed==native['records'],'Independent raw record reconstruction differs')
        pids={row['pid'] for row in recomputed};native_sets.append(pids)
        need(len(pids)==425 and pids==set(receipt['enum_'+label]),'Native/Enum425 PID accounting differs')
        rows=receipt['retained_processes' if label=='before' else 'retained_after']
        need(len(rows)==425 and {row['pid'] for row in rows}==pids,'Retained birth coverage differs')
        unknown=[row for row in rows if row['pid']!=0 and row.get('creation_filetime') is None]
        need(unknown==receipt['unknown_births'][label] and len(unknown)==168,'Unknown kernel birth accounting differs')
        window=receipt['candidate_window'];candidates=[row for row in rows if row.get('creation_filetime') is not None
            and window['inclusive_lower_filetime']<=row['creation_filetime']<=window['inclusive_upper_filetime']]
        need(candidates==receipt['kernel_birth_candidates'][label]==[],'Accessible candidate accounting differs')
        need(21672 not in pids and receipt['original_owner_observations'][label]==[],
             'Original owner observation differs; absence must remain qualified')
        exclusions.append(dict(**pin,reason='LOCAL_ONLY_RAW_NATIVE_BUFFER_INCLUDES_OPAQUE_RESERVED_BYTES_AND_ADDRESSES',
                               publicly_preserved_metadata=label+'.spi_metadata.json',public_payload_included=False))
    need(native_sets[0]==native_sets[1] and not any(receipt['pid_sets'].values()) and receipt['pid_birth_changes']==[],
         'Native before/after PID or retained birth stability differs')
    window=receipt['candidate_window'];need(window['inclusive_lower_filetime']==134360636630302864-600000000
        and window['inclusive_upper_filetime']==iso_ft('2026-10-09T23:54:25.561454+00:00')+600000000,
        'Conservative original candidate window differs')
    supplemental=receipt['supplemental'];worker=raw_json['supplemental_worker_result.json']
    need(supplemental['state']=='OPTIONAL_QUERY_RETURNED' and supplemental['lifecycle']==worker
         and supplemental['data']==raw_json['supplemental.json'],'Supplement file/receipt join differs')
    for name in ('supplemental_worker_birth.json','supplemental_worker_terminal.json'):
        for key,value in raw_json[name].items():need(worker[key]==value,'Worker phase/result join differs:'+key)
    birth=worker['birth'];terminal=worker['terminal'];final=worker['final_kernel_terminal']
    need(birth['pid']==terminal['pid']==final['pid']==23152
         and birth['creation_filetime']==terminal['creation_filetime']==final['creation_filetime']==134360651533170249
         and terminal==final and terminal['exited'] is True and terminal['exit_code']==0
         and terminal['exit_filetime']>terminal['creation_filetime'] and birth['exited'] is False,
         'New query worker retained terminal differs')
    need(worker['source_sha256']==PS_SHA and worker['owned_query_closure_proven'] is True
         and worker['owned_job_state']['job_active_processes']==0 and worker['owned_job_state']['job_pids']==[]
         and worker['drain_query_errors']==worker['handle_close_errors']==[],'New query job closure differs')
    data=supplemental['data'];cim=data['process_census'];need(len(cim['rows'])==427 and cim['truncated'] is False,'CIM row accounting differs')
    need(data['observer_pid']==birth['pid'] and data['historical_clock_continuity']=='NOT_ESTABLISHED'
         and data['process_universe_completeness']=='NOT_ESTABLISHED_BY_CIM' and data['stop_clear_authorized'] is False,
         'Supplement qualifications differ')
    before={row['pid']:row for row in receipt['retained_processes']};cross=[]
    for row in cim['rows']:
        kernel=before.get(row['pid']);birth_value=row.get('birth_filetime');state='NO_RETAINED_KERNEL_BIRTH_FOR_CROSSCHECK'
        if birth_value is not None and kernel and kernel.get('creation_filetime') is not None:
            state='MATCH_WITHIN_CIM_MICROSECOND_PRECISION' if abs(int(birth_value)-kernel['creation_filetime'])<=10 else 'MISMATCH_OR_PID_REUSE'
        cross.append(dict(pid=row['pid'],state=state,cim_creation_filetime=birth_value,
                          kernel_creation_filetime=kernel.get('creation_filetime') if kernel else None))
    need(cross==receipt['cim_crossvalidation'] and len({r['pid'] for r in cim['rows']})==427,'CIM crossvalidation differs')
    need(receipt['cim_pid_differences']==dict(native_before_missing=[],native_after_missing=[],cim_only=[23152,24048]),
         'CIM transient extras differ')
    need(data['clock_events']['coverage']=='NOT_ESTABLISHED' and data['clock_events']['rows']==[],
         'Empty clock events are not historical continuity')
    need('INACCESSIBLE_OR_UNKNOWN_KERNEL_BIRTHS' in receipt['vetoes']
         and 'HISTORICAL_CLOCK_CONTINUITY_NOT_ESTABLISHED' in receipt['vetoes']
         and 'ORIGINAL_OWNER_KERNEL_TERMINAL_NOT_BOUND' in receipt['vetoes'],'Required old-scope veto missing')
    for pin in pins:
        _,again=read(Path(pin['path']));need(again==pin,'Final evidence byte drift')
    return dict(schema='STAGE05_CENSUS_ACTUAL_INDEPENDENT_EVIDENCE_REVIEW_V1',
        state='PASS_RETAINED_DIAGNOSTIC_EVIDENCE_NOT_OLD_SCOPE_CLOSURE',pins=pins,
        native_before_after_enum_pid_count=425,unknown_kernel_births_each_snapshot=168,
        accessible_birth_candidates_each_snapshot=0,CIM_rows=427,CIM_extra_transient_PIDs=[23152,24048],
        new_query_worker_retained_exit0_and_empty_job=True,original_STOP_unchanged_receipt_verified=True,
        original_lock_identity_and_release_receipt_verified=True,
        original_owner_missing_is_exit_proof=False,historical_worker_terminal_recovered=False,
        original_scope_closure_accepted=False,historical_clock_continuity_proven=False,
        closure_acceptance=False,STOP_removal_authorized=False,raw_native_exclusions=exclusions,
        next_step='ROOT_SEPARATELY_AUTHORIZED_VERIFIED_WINDOWS_BOOT_TRANSITION_FALLBACK',
        live_process_queries=0,WSL_launches=0,G_access=0,process_mutations=0,
        interpretation='The actual census cannot establish necessary old-scope premises. Preserve STOP and original failure; no further census design.',
        utc=dt.datetime.now(dt.timezone.utc).isoformat())


if __name__=='__main__':
    value=verify();value['checker_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    target=WORK/'stage5_process_census_actual_independent_review.json'
    with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(dict(state=value['state'],receipt=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest())))
