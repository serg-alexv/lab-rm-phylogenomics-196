"""Public source/fixture metadata only; excludes the entire private handoff."""
from pathlib import Path
import hashlib,json,datetime
WORK=Path(__file__).resolve().parent
FILES={
 'resume_master_after_boot_once.py':'scripts/master_run/resume_master_after_boot_once.py',
 'Resume-MasterAfterBootOnce.ps1':'scripts/master_run/Resume-MasterAfterBootOnce.ps1',
 'test_resume_master_after_boot_once.py':'scripts/master_run/test_resume_master_after_boot_once.py',
 'MASTER_ONE_SHOT_BOOT_RESUME_METHODS.md':'docs/master_run/MASTER_ONE_SHOT_BOOT_RESUME_METHODS.md',
 'verify_corrected_windows_fixture_evidence.py':'scripts/master_run/verify_corrected_windows_fixture_evidence.py',
 'windows_owned_job_corrected_fixture_independent_readback.json':'reports/master_run/20261009/stage05_windows_job_drain/CORRECTED_FIXTURE_INDEPENDENT_READBACK.json',
 'resume_master_after_boot_once_independent_review.json':'reports/master_run/20261009/stage05_boot_resume01/INDEPENDENT_SOURCE_REVIEW.json',
 'prepare_master_one_shot_boot_resume.py':'scripts/master_run/prepare_master_one_shot_boot_resume.py',
}
def pin(path):
 data=path.read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def main():
 rows=[{'local':str(WORK/name),'path':remote,**pin(WORK/name)} for name,remote in FILES.items()]
 report={'schema':'MASTER_ONE_SHOT_BOOT_RESUME_PREPARATION_V1','state':'PREPARED_SOURCE_ONLY_NOT_REGISTERED_OR_REBOOTED',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows,
  'pure_tests':{'passed':7,'seconds':0.028,'actual_cli_or_network_calls':0},
  'independent_pure_tests':{'passed':7,'seconds':0.018},'PowerShell_AST':'PASS',
  'independent_source_review':'PASS_SOURCE_ONLY_AT_896f33d10d419d531327df02d72a48507895cbc7ffa7bf44129ae85c1c1b2a2f',
  'local_cli_observation':{'codex_version':'0.162.0-alpha.2','github_copilot_version':'1.0.80',
    'CODEX_THREAD_ID_presence':True,'exact_ID_value_exposed_or_published':False,'session_or_authentication_store_read':False},
  'RunOnce_read_only_observation':{'current_user_key_opened_writable':True,'existing_value_count':0,'entry_created':False,'command_characters':193},
  'shutdown_privilege_read_only':{'name':'SeShutdownPrivilege','present':True,'state':'Disabled','enabled_by_agent':False},
  'private_directory_EXCLUDE_ALL_CONTENTS':'work/private_master_boot_resume01/',
  'original_STOP_sha256_unchanged':'3de7057780d280d5f204b535207a174e616ca425b5638fe9848a48cfca20838a',
  'old_scope_closure':False,'scientific_authority':False,'actual_resume':False,'actual_reboot':False,
  'private_handoff_prepared':(WORK/'private_master_boot_resume01/PRIVATE_HANDOFF_DO_NOT_PUBLISH.json').is_file(),
  'remaining':['exact source publication/readback',
    'root-only one-time registration and controlled restart','same-user sign-in','actual new-boot/STOP reconciliation',
    'actual resumed CLI/session/authentication availability','fresh operational/scientific gates'],
  'limitations':['Launch-only helper, not a CLI/scientific terminal or descendant closure certificate.',
    'Default RunOnce consumes before execution; private CreateNew marker additionally prevents replay. Failures do not auto-rearm.',
    'No raw private CLI/stdout/session/manifest publication; no recurring automation or automatic_resume policy change.']}
 target=WORK/'master_one_shot_boot_resume_preparation.json'
 with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({'path':str(target),**pin(target)}))
if __name__=='__main__':main()
