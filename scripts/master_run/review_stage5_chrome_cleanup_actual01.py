"""C-only exact Chrome cleanup actual receipt reader; no process/WSL actions."""
from pathlib import Path
import argparse, datetime, hashlib, json
import review_stage5_postboot_gate as R
WORK=Path(__file__).resolve().parent
SOURCE='85c46761991c657ecc86f2dad8bcd5d75e40e29d37dc14d234cfed19806836bf'
EXE=r'C:\Program Files\Google\Chrome\Application\chrome.exe'

def ft(iso):return int((datetime.datetime.fromisoformat(iso)-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10000000)
def target(value,session):
    R.require(type(value['pid']) is int and value['pid']>0 and type(value['creation_filetime']) is int
      and value['creation_filetime']>0 and type(value['session_id']) is int and value['session_id']==session
      and value['executable'].casefold()==EXE.casefold(),'Exact current-session Chrome target identity differs')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spool',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--publication-readback',type=Path);args=p.parse_args();spool=args.spool
    R.require(spool.parent==WORK and spool.name.startswith('stage5_chrome_cleanup_') and args.output.parent==WORK
      and not args.output.exists(),'Exact completed C spool and fresh report required')
    result={'schema':'STAGE05_EXACT_CHROME_CLEANUP_ACTUAL_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_READBACK',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),
      'method':'Only bounded explicit C source/receipt SHA256 and decoded lifecycle joins; no process handles/enumeration/effects/WSL/UNC/lock/ref operations'}
    try:
        R.require(R.sha(WORK/'stage5_chrome_resource_cleanup.py')==SOURCE,'Frozen Chrome source differs')
        peer=R.pinned(WORK/'stage5_chrome_resource_cleanup_independent_review01.json','a57dc36d091a63c913d5cee0e4298a4fca5264fb65de41e283385be6c31f1477')
        R.require(peer['state']=='PASS_FROZEN_SOURCE_PURE_GUARDS_DEFAULT_NOOP_ACTUAL_NOT_RUN','Source peer differs')
        value=R.read(spool/'result.json');unlock=R.read(spool/'lock_released.json');intent=R.read(spool/'intent.json');snapshot=R.read(spool/'target_snapshot.json')
        R.require(value['schema']=='STAGE05_EXACT_CHROME_RESOURCE_CLEANUP_WINDOWS_V1'
          and value['state']=='PASS_EXACT_CHROME_SNAPSHOT_EFFECTS_AND_HANDLES_CLOSED' and value['source_sha256']==SOURCE
          and value['api_source_sha256']==R.sha(WORK/'atomic_iqtree_windows.py')
          and value['scope']=='NONSCIENTIFIC_CURRENT_SESSION_EXACT_CHROME_RETAINED_HANDLE_CLEANUP_ONLY'
          and value['owned_closure_proven'] is True and value['original_lock_explicitly_released'] is True
          and value['unknown_closure_stop_preserved'] is False and value['retained_handles_unresolved']==0
          and value['scientific_adoption_authorized'] is False and value['finalizer_evidence']==[],'Actual Chrome source/state/closure differs')
        R.lock(value['workflow_lock']);R.require(unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED' and unlock['released'] is True
          and ft(unlock['utc'])<=ft(value['utc']),'Explicit unlock before finalPASS differs')
        nonce=value['owner_nonce'];owner=value['actual_owner'];session=owner['session_id']
        R.require(value['allowlist']==[EXE] and value['target_session_id']==session and value['snapshot_targets_only'] is True
          and value['process_payload_or_argv_read'] is False and value['process_tree_or_name_kill'] is False
          and value['wsl']==value['services']==value['git_mutation']=='NOT_RUN' and value['elapsed_seconds']<180
          and value['maximum_enumeration']==4096 and value['maximum_targets']==128 and value['deadline_seconds']==180,'Actual scope/cap/finite boundary differs')
        R.require(intent['state']=='PRE_ENUMERATION_INTENT_NO_PROCESS_EFFECT' and intent['owner_nonce']==nonce
          and intent['source_sha256']==SOURCE and snapshot['scope']==value['scope'] and snapshot['owner_nonce']==nonce
          and snapshot['no_argv_urls_profiles_read'] is True,'Actual intent/snapshot differs')
        targets=snapshot['targets'];effects=value['effects'];R.require(type(value['target_count']) is int and value['target_count']==len(targets)==len(effects)<=128
          and type(value['enumerated_pid_count']) is int and value['target_count']<=value['enumerated_pid_count']<4096,'Exact snapshot/effect cardinality differs')
        R.require(len({(v['pid'],v['creation_filetime']) for v in targets})==len(targets),'Duplicate retained target identity')
        closed=[];expected={'intent.json','result.json','lock_released.json','target_snapshot.json'}
        for ordinal,(birth,effect) in enumerate(zip(targets,effects),1):
            target(birth,session);R.require(birth['exited'] is False,'Initial snapshot target was already terminal')
            ip=spool/f'effect_{ordinal:04d}.intent.json';rp=spool/f'effect_{ordinal:04d}.result.json'
            expected.update((ip.name,rp.name));item=R.read(rp);before=R.read(ip)
            R.require(item==effect and effect['ordinal']==before['ordinal']==ordinal and effect['birth']==before['birth']==birth
              and effect['owner_nonce']==before['owner_nonce']==nonce and effect['source_sha256']==before['source_sha256']==SOURCE
              and before['state']=='INTENT_BEFORE_EFFECT' and before['effect']==effect['effect']=='TERMINATE_RETAINED_CHROME_HANDLE_ONLY'
              and before['requested_exit_code']==effect['requested_exit_code']==1223
              and effect['actual_checked_close_handle_succeeded'] is True,'Exact per-target intent/result/source/close differs')
            end=effect['terminal'];target(end,session)
            R.require(all(end[k]==birth[k] and type(end[k]) is type(birth[k]) for k in ('pid','creation_filetime','session_id'))
              and end['exited'] is True and type(end['exit_code']) is int and type(end['exit_filetime']) is int
              and end['exit_filetime']>birth['creation_filetime'] and end['exit_filetime']<ft(unlock['utc']),'Positive retained target exit before unlock differs')
            if effect['state']=='TERMINATED_EXACT_HANDLE_AND_TERMINAL_VERIFIED':
                R.require(effect['actual_terminate_process_called'] is True and end['exit_code']==1223,'Actual exact termination exit differs')
            else:R.require(effect['state']=='NO_EFFECT_ALREADY_CLOSED' and effect['actual_terminate_process_called'] is False,'Unrecognized target effect state')
            closed.append({'ordinal':ordinal,'pid':birth['pid'],'creation_filetime':birth['creation_filetime'],
              'state':effect['state'],'exit_code':end['exit_code'],'intent_sha256':R.sha(ip),'result_sha256':R.sha(rp)})
        for item in value['prior_closed_owner_evidence']:
            prior=R.pinned(Path(item['result_path']),item['result_sha256']);prior_unlock=R.pinned(Path(item['unlock_path']),item['unlock_sha256'])
            R.require(prior['owned_closure_proven'] is True and prior['unknown_closure_stop_preserved'] is False
              and prior['state']==item['prior_state_preserved'] and prior_unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'
              and prior_unlock['released'] is True,'Actual root-supplied prior closed evidence differs')
        R.require({p.name for p in spool.iterdir()}==expected,'Unexpected completed Chrome spool membership')
        for path in spool.iterdir():R.data(path)
        for key in ('windows_before','windows_after','latest_actual_resources'):
            resource=value[key];R.require(resource['physical_available_bytes']>=256*1024**2 and resource['commit_headroom_bytes']>=256*1024**2,'Fresh bounded maintenance reserve differs')
        publication=None
        if args.publication_readback:
            publication=R.read(args.publication_readback)
            R.require(publication['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and publication['failures']==[]
              and publication['required_files']==publication['verified_files'] and ft(publication['finished_utc'])<owner['creation_filetime'],'Full source publication must precede actual owner')
            rows=[x for x in publication['files'] if x['path']=='scripts/master_run/stage5_chrome_resource_cleanup.py']
            R.require(len(rows)==1 and rows[0]['sha256']==SOURCE and rows[0]['actual_remote_bytes_read'] is True,'Published cleanup source bytes differ')
        result.update(state='PASS_EXACT_CHROME_SNAPSHOT_RETAINED_TERMINALS_CHECKED_HANDLES_UNLOCK_AND_BYTES',
          actual_result_sha256=R.sha(spool/'result.json'),source_sha256=SOURCE,
          source_publication_commit=publication['expected_commit'] if publication else 'NOT_SUPPLIED_TO_THIS_REVIEWER',
          target_count=len(targets),effects=closed,owner_elapsed_seconds=value['elapsed_seconds'],
          original_unlock_sha256=R.sha(spool/'lock_released.json'),original_lock_identity=value['workflow_lock'],
          owned_STOP_absent_in_closed_result=True,retained_owned_handles_unresolved=0,
          observed_windows_before=value['windows_before'],observed_windows_after=value['windows_after'],
          snapshot_scope='Only original retained snapshot targets; no assertion that Chrome remains absent or resource gain persists.',
          scientific_admission='NONE_KEEP_FRESH_RESOURCES_AND_ALL_STAGE5_GATE_REQUIREMENTS',
          source_and_receipt_payload_scope='Chrome executable/birth/session/terminal metadata only; no argv/URL/profile payloads',
          actual_operations_by_reviewer='NONE_READONLY_C_RECEIPTS_ONLY')
    except BaseException as error:result['error']={'kind':type(error).__name__,'message':str(error)}
    result['checked_files']=R.CHECKED
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':result['state'],'output':str(args.output),'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
      'checked_files':len(R.CHECKED),'error':result.get('error')}))
    return 0 if result['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
