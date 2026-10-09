"""Record independently verified cleanup and tested Stage4 publication boundary."""
from pathlib import Path
import datetime,hashlib,json
work=Path(__file__).resolve().parent;out=work/'master_verified_directory_and_publication09';out.mkdir(exist_ok=False)
base='reports/master_run/20261009/';files=[]
def add(local,target,pin=None):
 path=Path(local)
 if not path.is_absolute():path=work/path
 raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
 assert 0<len(raw)<5*1024**2 and (pin is None or digest==pin),str(path)
 files.append({'local_absolute_path':str(path),'target':target,'bytes':len(raw),'sha256':digest})
for name,pin in {
 'observe_iqtree_controller_exit.py':'483b5165d015dcea659d5e850187c79ff5e99c4c0efff1c9fb108cc9a59ab78a',
 'observe_iqtree_controller_exit_attempt01.py':None,
 'publish_stage4_primary.py':'6663aac3a01a01b1d35d93c5b1b3cae96f55d279a98b2d755cdfce1790c47624',
 'publish_stage4_primary_before_text_fix.py':None,
 'prepare_stage4_publication.py':None,'prepare_stage4_publication_before_text_test.py':None,
 'test_stage4_publication_text.py':None,Path(__file__).name:None,
}.items():add(name,'scripts/master_run/'+name,pin)
for name,(target,pin) in {
 'observe_iqtree_controller_exit_independent_source_review.json':('preparation/observe_iqtree_controller_exit_independent_source_review.json','d4cf9598eee483febf19810878565b18f7da79c019373086a214ec9a407c8a88'),
 'observe_iqtree_controller_exit_source_review_attempt01.json':('preparation/observe_iqtree_controller_exit_source_review_attempt01.json',None),
 'stage04_publication_text_independent_source_review.json':('preparation/stage04_publication_text_independent_source_review.json','635a361722b351656ce524ceb1cfe6c63043b08945cb0c22929c11e83db29912'),
 'stage04_publication_text_regression.json':('preparation/stage04_publication_text_regression.json',None),
 'directory_prune_postverify_20261009T213844Z_e301284e/receipt.json':('cleanup/emptydirs_prune01/INDEPENDENT_POSTVERIFY.json',None),
 'master_directory_provider_correction08_git_objects.json':('publication/DIRECTORY_PROVIDER_CORRECTION08_GIT_OBJECTS.json',None),
 'master_directory_provider_correction08_remote_readback.json':('publication/DIRECTORY_PROVIDER_CORRECTION08_REMOTE_READBACK.json',None),
}.items():add(name,base+target,pin)
post=json.loads((work/'directory_prune_postverify_20261009T213844Z_e301284e/receipt.json').read_bytes())
assert post['state']=='PASS_EXACT5542_REMOVED_AND_PROTECTED_IDENTITIES_UNCHANGED' and post['complete_prune_verified'] is True
assert post['documented_removed_directories']==5542 and post['held_directories_preserved']==6
assert len(post['protected_files'])==12 and len(post['six_dirty_g_files_unchanged'])==6
now=datetime.datetime.now(datetime.timezone.utc)
raw=(work/'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_bytes();native=json.loads(raw)
assert 0<=(now-datetime.datetime.fromisoformat(native['utc'])).total_seconds()<60 and native['exited'] is False
(out/'native_progress.json').write_bytes(raw)
status=json.loads((work/'master_source_recovery_result07/status.json').read_bytes())
status.update(updated_utc=now.isoformat(),native_process=native,latest_progress_snapshot=base+'snapshots/verified_directory_publication09/native_progress.json')
status['cleanup']['empty_directories_removed']=5557
status['cleanup']['empty_directory_proposal'].update(pruning='PASS_EXACT5542_REMOVED_AND_PROTECTED_IDENTITIES_UNCHANGED',
 independent_postverify='PASS_ACTUAL_5542_ABSENT_6_HELD_12_PROTECTED_6_DIRTY_G_ORIGINAL_LOCK_AND_OWNER_IDENTITIES',
 postverify_receipt=base+'cleanup/emptydirs_prune01/INDEPENDENT_POSTVERIFY.json',
 g_single_link_exclusion='NOT_ESTABLISHED_PROVIDER_REPORTED_ZERO; ONLY_EXACT9_PINNED_G_PATHS_QUALIFIED',
 full_journal_remote_recovery='PENDING_BOUNDED_EXECUTION_ARCHIVE')
status['stage04_publication_preparation']={'state':'CORRECTED_TEXT_JSON_BOUNDARY_13_SYNTHETIC_TESTS_AND_PEER_REVIEW_PASS_ACTUAL_NOT_RUN',
 'native_runner_unchanged':True,'native_stage':'FINAL_PARAMETER_OPTIMIZATION_NO_ACCEPTED_TREE'}
(out/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
md=(work/'master_source_recovery_result07/STATUS.md').read_text(encoding='utf-8')
md=md.replace(json.loads((work/'master_source_recovery_result07/status.json').read_bytes())['updated_utc'],now.isoformat())
md=md.replace('snapshots/source_recovery_result07/native_progress.json','snapshots/verified_directory_publication09/native_progress.json')
md=md.replace('15 exact empty directories','5,557 exact empty directories')
old='The independent filesystem checker stopped at a protected regular-file metadata guard; its exact failed receipt is preserved and diagnosis is pending. No deletion is being repeated. Full journal remote recovery and independent acceptance remain pending.'
new='The corrected independent filesystem checker PASS: all 5,542 planned directories absent, six holds and the vendor fragment preserved, protected12/six dirty G hashes and exact owner/original-lock identities unchanged. Nine exact G files qualify for observed provider zero-link metadata with full identity and SHA checks; single-link exclusion is explicitly NOT_ESTABLISHED. The first failed checker/source/receipt and actual diagnosis are preserved. No deletion was repeated. Full journal remote recovery remains pending.'
assert old in md;md=md.replace(old,new)
md+='\nPublication preflight corrected three text outputs passed to the JSON writer. The new exact-byte writer and actual local status-format regression pass 13 tests and independent source review. Native producer/checker scientific gates remain unchanged. Actual Stage4 closure, independent tree acceptance and publication remain pending.\n'
(out/'STATUS.md').write_text(md,encoding='utf-8')
ledger=(work/'master_source_recovery_result07/STORAGE_LEDGER.md').read_text(encoding='utf-8')
ledger+='\nCorrected actual independent directory post-check PASS for all 5,542 planned removals, six holds, fragment, 12 protected hashes, six dirty G files, exact owners and stable lock identity. Verified cumulative cleanup is 48,490 files / 9,756,853,507 logical bytes plus 5,557 directories; physical reclaimed bytes NOT_MEASURED. Nine exact DriveFS zero-link paths retain full identity/SHA guards; single-link exclusion NOT_ESTABLISHED. Full journal execution-recovery archive pending. Stage4 text/JSON publication boundary fix passes 13 local tests and independent review; scientific acceptance still pending.\n'
(out/'STORAGE_LEDGER.md').write_text(ledger,encoding='utf-8')
add(out/'native_progress.json',base+'snapshots/verified_directory_publication09/native_progress.json')
add(out/'status.json','status/master_run_20261009.json');add(out/'STATUS.md','STATUS.md');add(out/'STORAGE_LEDGER.md','docs/master_run/STORAGE_LEDGER.md')
with (work/'master_verified_directory_publication09_git_plan.json').open('x',encoding='utf-8') as stream:
 json.dump({'expected_head':'006b3c2fdf3556b238950d1b0a737f288f26c67d','message':'Verify5542 exact directory removals independently; fix Stage4 publication text formats before actual use','files':files},stream,indent=2);stream.write('\n')
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
