"""Prepare C publication52 inputs; only root --prepare-plan calls the existing planner.

No WSL, locks, native runtime, process effects, Git/ref or remote calls.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, subprocess, sys

W=Path(__file__).resolve().parent
NAME='master_interop52'
HEAD='903b86b344c421720d3b6ab3d6361a649b872ce6'
PREVIOUS='master_toolchain51'
SPOOL='stage5_interop_actual_postiq_05'
REVIEW='stage5_interop05_postprofile_independent_review.json'
READBACK='master_toolchain51_remote_readback.json'
MAPPING='stage05_chrome_cleanup_source_preparation01/PUBLIC_MAPPING.json'
PHASE='postprofile interop05 closed PASS; inactive reviewed G and contingent Chrome source; cold owner remains blocked including STOP/unlock order'
PINS={
 'prepare_master_postboot_gate_step.py':'e41e66a34df98935a32b05f0aabe9f23e8ef21155600ab463c4eff2fe0bb1c74',
 REVIEW:'d1edbd9970f7f2427ce3abae563231e1b0c7e5a8421420ddba35cec8fe18a07a',
 READBACK:'53df57b263ca144c29630d34c25d9b28a4a4ece383fe818381ec53525f5f0e15',
 'stage5_gdrive_view_postprofile.py':'1ec2380d218128e325954552057ed1215268297862e2910550b2eb7c46a112e9',
 'test_stage5_gdrive_view_postprofile.py':'a3c06bc75e69f802b3b11de9400d35c3fee3b0cfae5e82e4df6ce6fbdeb7e413',
 'stage5_gdrive_view_postprofile_METHODS.md':'93ce1db7145598f626846014619a8fee166442d9c9b29a035fc26645294cad01',
 'stage5_gdrive_view_postprofile_preparation01.json':'7d9259672beb9032ed84f9d5e172f5c8522cf84b50bf710f007843a54330b446',
 'stage5_gdrive_postprofile_source_independent_review01.json':'8ad1436371e1329011aa9ae405409a4767b6109bda5b1eb16fe9606c10be2283',
 'review_stage5_gdrive_postprofile_source01.py':'1722accaa3abc44c177395c1c6a0d52ea658a9b242f7353f0b4fe635bc4817e8',
 'stage5_interop05_actual_closed_derived_receipt01.json':'7537cafac088e68194f5cb220f2999019f6740959accbc3bb979c693440adf7a',
 'derive_stage5_interop05_actual_closed_receipt01.py':'90ae054b1528079218c43eaf70f9dab03ad7b04487b81d941033f72d8d4b283c',
 MAPPING:'aaafdefc05c28dc1f3e657172bfc1d0cb581020359f3bf8c917e09543c12c7b4',
 'stage05_cold_owner_unlock_order_addendum01.json':'6f3d7989f08f957a8465d9b995777d853618a6ad078f46c2cc2af1ec8c0c741f',
 'review_stage05_cold_owner_unlock_addendum01.py':'793a9f806e3b03c7dc047a2b0f4912f8cdb194c484218ab4d87588fad81279db',
 'stage5_gdrive_view_postrepair.py':'a69a755dd044d72cfdfc49d85c150a43057ad69e9b4d70253792222410e41125',
 'stage5_gdrive_view_session.py':'42db8fe44fb2e6c4b8300c2415dc45a6aec20b115449bf76ad002eda34354fb8'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-plan',action='store_true');args=parser.parse_args()
    checked={}
    def verify(name,pin,size=None):
        path=(W/name).resolve();assert path.is_relative_to(W) and not path.is_symlink()
        raw=path.read_bytes();actual=hashlib.sha256(raw).hexdigest()
        assert actual==pin and (size is None or len(raw)==size),(name,'Frozen bytes changed')
        checked[path.relative_to(W).as_posix()]={'bytes':len(raw),'sha256':actual}
        return raw
    for name,pin in PINS.items():verify(name,pin)
    readback=json.loads(verify(READBACK,PINS[READBACK]))
    assert readback['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and readback['expected_commit']==HEAD
    assert readback['required_files']==readback['verified_files']==32
    review=json.loads(verify(REVIEW,PINS[REVIEW]));assert review['kind']=='interop' and review['state']=='PASS_COMPLETED_POSTBOOT_GATE_EXACT_SOURCE_CLOSURE_AND_BYTES'
    for name in [REVIEW,'stage5_gdrive_postprofile_source_independent_review01.json','stage05_cold_owner_unlock_order_addendum01.json']:
        record=json.loads(verify(name,PINS[name]))
        for path,row in record.get('checked_files',{}).items():verify(path,row['sha256'],row['bytes'])
    mapping=json.loads(verify(MAPPING,PINS[MAPPING]));assert mapping['file_count']==len(mapping['files'])==6
    assert mapping['state']=='PASS_SOURCE_ONLY_INDEPENDENT_REVIEW_ACTUAL_NOT_RUN' and mapping['actual_runtime_actions'] is False and mapping['cleanup_performed'] is False
    extras=[]
    for name in ['stage5_gdrive_view_postprofile.py','test_stage5_gdrive_view_postprofile.py','review_stage5_gdrive_postprofile_source01.py','derive_stage5_interop05_actual_closed_receipt01.py',Path(__file__).name]:
        extras.append(name+'=scripts/master_run/'+name)
    for name in ['stage5_gdrive_view_postprofile_METHODS.md','stage5_gdrive_view_postprofile_preparation01.json','stage5_gdrive_postprofile_source_independent_review01.json','stage05_cold_owner_unlock_order_addendum01.json','stage5_interop05_actual_closed_derived_receipt01.json']:
        extras.append(name+'=reports/master_run/20261009/postprofile52/'+name)
    extras.append('review_stage05_cold_owner_unlock_addendum01.py=scripts/master_run/review_stage05_cold_owner_unlock_addendum01.py')
    for row in mapping['files']:
        path=Path(row['local_path']).resolve();assert path.is_relative_to(W)
        name=path.relative_to(W).as_posix();verify(name,row['sha256'],row['bytes'])
        remote=row['repository_path'];assert not remote.startswith('/') and '..' not in Path(remote).parts
        extras.append(name+'='+remote)
    extras.append(MAPPING+'=reports/master_run/20261009/stage05_chrome_cleanup_preparation01/PUBLIC_MAPPING.json')
    assert all(READBACK not in row and REVIEW not in row for row in extras),'Generic owner adds readback/review exactly once'
    assert len({row.split('=',1)[0] for row in extras})==len(extras)==len({row.split('=',1)[1] for row in extras})
    status={
      'stage5_gdrive_current':'REVIEWED_SOURCE_ONLY_POSTPROFILE_1ec2380d; INACTIVE; ACTUAL_DIAGNOSIS_AND_MOUNT_NOT_RUN',
      'stage5_gdrive_source_independent_review_sha256':PINS['stage5_gdrive_postprofile_source_independent_review01.json'],
      'stage5_chrome_cleanup_current':'REVIEWED_CONTINGENT_SOURCE_ONLY_85c46761; INACTIVE; ACTUAL_CLEANUP_NOT_RUN',
      'stage5_chrome_cleanup_public_mapping_sha256':PINS[MAPPING],
      'stage5_cold_owner_current':'BLOCKED_SOURCE_ONLY; EXT4_STATE_PARENT_BUDGET_EXACT_INTEGER_AND_STOP_UNLOCK_ORDER_CORRECTIONS_REQUIRED; ACTUAL_VM_OPERATIONS_NOT_RUN',
      'stage5_cold_owner_unlock_order_addendum_sha256':PINS['stage05_cold_owner_unlock_order_addendum01.json']}
    status_name=NAME+'_additional_status.json';(W/status_name).write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    extras_name=NAME+'_prepared_extras.json';(W/extras_name).write_text(json.dumps(extras,indent=2)+'\n',encoding='utf-8')
    receipt={'schema':'MASTER_INTEROP52_FROZEN_INPUT_PREPARATION_V1','state':'PASS_C_INPUTS_ONLY_ROOT_PLANNER_NOT_RUN',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'name':NAME,'base_head':HEAD,'previous':PREVIOUS,
      'spool':SPOOL,'review':REVIEW,'phase':PHASE,'checked_files':checked,'explicit_extras_count':len(extras),
      'previous_readback_added_only_by_generic_owner':True,'G_Chrome_cold_actual_operations':'NOT_RUN',
      'Git_ref_remote_lock_WSL_native_actions':'NOT_RUN','generic_planner_execution':'ROOT_EXPLICIT_ONLY'}
    receipt_name=NAME+'_input_preparation01.json';(W/receipt_name).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    if args.prepare_plan:
        command=[sys.executable,'-B',str(W/'prepare_master_postboot_gate_step.py'),'--name',NAME,'--head',HEAD,
          '--previous',PREVIOUS,'--phase',PHASE,'--spool',SPOOL,'--review',REVIEW,'--previous-readback',READBACK,
          '--additional-status-file',status_name]
        for item in extras:command+=['--extra',item]
        command+=['--extra',receipt_name+'=reports/master_run/20261009/publication/'+receipt_name]
        subprocess.run(command,check=True)
    print(json.dumps({'state':receipt['state'],'checked_files':len(checked),'extras':extras_name,'status':status_name,'generic_planner_run':args.prepare_plan}))


if __name__=='__main__':main()
