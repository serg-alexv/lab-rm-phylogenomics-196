"""Publish separate capacity request and reviewed exact cancellation sources."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def digest(raw):return hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',required=True);p.add_argument('--packet-sha256',required=True);a=p.parse_args()
    name='master_capacityprep64'
    review='stage5_first_capacity02_request_independent_review01.json'
    assert digest((W/review).read_bytes())=='48d18021fc0fed39f6a4d8f4e4bcb403000f1a6ef990f0ad95bc7450c4cdeef6'
    assert json.loads((W/review).read_bytes())['state'].startswith('PASS_')
    request='stage5_actual_request_backing_capacity_02.json'
    assert digest((W/request).read_bytes())=='13cdeba557bf0042a4fe2e95bf0905734cdd4735b0c333f255838b3fdb7e9ccb'
    extras=[f+'=reports/master_run/20261009/first_capacity02/'+f for f in (request,review)]
    extras += [f+'=scripts/master_run/'+f for f in ('prepare_stage5_first_capacity02_request.py','review_stage5_first_capacity02_request01.py',Path(__file__).name)]
    extras += ['master_firstwait63_remote_readback.json=reports/master_run/20261009/publication/master_firstwait63_remote_readback.json']
    packet=(W/a.packet).resolve();raw=packet.read_bytes()
    assert packet.is_relative_to(W) and digest(raw)==a.packet_sha256
    mapping=json.loads(raw);assert mapping['state'].startswith('PASS_')
    for row in mapping['files']:
        path=Path(row.get('local_path',row.get('path'))).resolve();data=path.read_bytes()
        assert path.is_relative_to(W) and len(data)==row['bytes'] and digest(data)==row['sha256']
        target=row.get('repository_path',row.get('suggested_repository_path'));assert target and '..' not in Path(target).parts
        extras.append(path.relative_to(W).as_posix()+'='+target)
    extras.append(a.packet+'=reports/master_run/20261009/preparation/'+packet.parent.name+'_PUBLIC_MAPPING.json')
    assert len({x.split('=',1)[1] for x in extras})==len(extras)
    patch={'stage5_first_capacity_revision02':'PASS_REVIEWED_REQUEST_ONLY; LINUX_BOOKING1.375GiB_WITH_UNCHANGED_RSS_STOP_RESERVES_AND_WINDOWS_BUDGETS',
      'stage5_waiting01_exact_cancellation':'PASS_REVIEWED_SOURCE_ONLY; ACTUAL_SIGNAL_TERMINAL_AND_UNLOCK_PENDING',
      'stage5_first_full_method_genome':'WAITING01_ORIGINAL_OWNER_ACTIVE; CAPACITY02_ACTUAL_CONFIG_AND_NATIVE_ADMISSION_PENDING_CLOSURE'}
    paragraph='Stage5 current execution: waiting01 remains an active initial-resource wait with no adopted native result. A separate reviewed request02 changes only the unmeasured Linux job capacity booking from1.5GiB to1.375GiB and its rationale; sampledRSSstop1.25GiB, Linuxreserve1GiB, Windows thresholds, all six current-boot gates and full scientific methods stay fixed. The exact pidfd cancellation sources are reviewed only and will request graceful termination of this one verified waiting Linux bootstrap, leaving its original Windows owner to establish terminal closure and unlock. No second scientific launch occurs before those receipts. If preparation or execution still does not fit, no further booking reduction is planned; a guest-capacity change with fresh boot gates is the bounded fallback. Accepted Stage4 is unchanged; VM recovery and actual cleanup remain pending.\n'
    for suffix,value in [('patch.json',patch),('extras.json',extras)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','5e0d53b04398fd11ba3f0d901ad964b9ddcecbb8','--previous','master_firstwait63',
      '--phase','reviewed separate Linux capacity booking revision and exact waiting-bootstrap cancellation sources only',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json'],check=True)
if __name__=='__main__':main()
