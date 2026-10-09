"""Publish actual full-source recovery and the preserved metadata-guard failure."""
from pathlib import Path
import datetime,hashlib,json
work=Path(__file__).resolve().parent;out=work/'master_source_recovery_result07';out.mkdir(exist_ok=False)
base='reports/master_run/20261009/';files=[]
def add(local,target,pin=None):
 path=Path(local)
 if not path.is_absolute():path=work/path
 raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
 assert 0<len(raw)<5*1024**2 and (pin is None or pin==digest),str(path)
 files.append({'local_absolute_path':str(path),'target':target,'bytes':len(raw),'sha256':digest})
add('iqtree314_source_recovery01_readback_20261009T212934Z_4f7a5760/receipt.json',base+'cleanup/iqtree314_source01/REMOTE_READBACK.json',
 '016bda9871a4b30e6808d03dad4f9ea60670b3191f167edc15ac5da94d55949e')
add('directory_prune_postverify_20261009T212934Z_35de2767/receipt.json',base+'cleanup/emptydirs_prune01/POSTVERIFY_ATTEMPT01_FAILED.json')
for local,target in {
 'directory_handle_postverify_preparation.json':'cleanup/emptydirs_prune01/POSTVERIFY_PREPARATION_ATTEMPT01.json',
 'directory_handle_postverify_METHODS.md':'cleanup/emptydirs_prune01/POSTVERIFY_METHODS_ATTEMPT01.md',
 'master_validation_readers06_git_objects.json':'publication/VALIDATION_READERS06_GIT_OBJECTS.json',
 'master_validation_readers06_remote_readback.json':'publication/VALIDATION_READERS06_REMOTE_READBACK.json',
}.items():add(local,base+target)
add(Path(__file__),'scripts/master_run/'+Path(__file__).name)
now=datetime.datetime.now(datetime.timezone.utc)
raw=(work/'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_bytes();native=json.loads(raw)
assert 0<=(now-datetime.datetime.fromisoformat(native['utc'])).total_seconds()<60 and native['exited'] is False
(out/'native_progress.json').write_bytes(raw)
status=json.loads((work/'master_recovery_receipts05/status.json').read_bytes())
status.update(updated_utc=now.isoformat(),native_process=native,latest_progress_snapshot=base+'snapshots/source_recovery_result07/native_progress.json')
status['recovery_preparation']['iqtree_full_source'].update(remote_recovery='PASS_FRESH_REMOTE31_MEMBERS_1938_ORIGINAL_GITBLOBS_ONE_EXACT_SUPPLEMENT',
 remote_receipt=base+'cleanup/iqtree314_source01/REMOTE_READBACK.json',owned_download_commands=27,owned_download_command_closure='ALL_EXIT0')
status['cleanup']['empty_directory_proposal'].update(independent_postverify='ATTEMPT01_METADATA_GUARD_FAILED_PRESERVED_DIAGNOSIS_PENDING',
 pruning='EXECUTION_EXIT0_5542_REMOVED_INDEPENDENT_ACCEPTANCE_PENDING',deletion_rerun_authorized=False,
 failed_postverify_receipt=base+'cleanup/emptydirs_prune01/POSTVERIFY_ATTEMPT01_FAILED.json')
(out/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
md=(work/'master_recovery_receipts05/STATUS.md').read_text(encoding='utf-8')
md=md.replace(json.loads((work/'master_recovery_receipts05/status.json').read_bytes())['updated_utc'],now.isoformat())
md=md.replace('iteration 90','iteration 100').replace('snapshots/recovery_receipts05/native_progress.json','snapshots/source_recovery_result07/native_progress.json')
md=md.replace('Independent filesystem post-verification and full journal remote recovery remain pending.',
 'The independent filesystem checker stopped at a protected regular-file metadata guard; its exact failed receipt is preserved and diagnosis is pending. No deletion is being repeated. Full journal remote recovery and independent acceptance remain pending.')
md=md.replace('Both Release assets are uploaded; independent fresh source recovery readback remains pending.',
 'Fresh GitHub readback now PASS for all 31 archive members / 30 SUMS and all 1,938 original Gitblob bindings; all 27 owned downloader commands closed exit 0. Installed-binary equivalence remains unproved.')
(out/'STATUS.md').write_text(md,encoding='utf-8')
ledger=(work/'master_recovery_receipts05/STORAGE_LEDGER.md').read_text(encoding='utf-8')
ledger+='\nActual fresh IQ-TREE full-source recovery PASS: all 31 members / 30 SUMS / 1,938 original Gitblob bindings with one exact 249-byte supplement; all 27 owned commands closed exit 0. Directory post-check attempt01 failed a protected-file metadata guard and is preserved; diagnosis pending, no deletion rerun. Accepted directory cleanup total remains 15 pending independent post-check. Stage4 search iteration 100 is provisional and not yet accepted.\n'
(out/'STORAGE_LEDGER.md').write_text(ledger,encoding='utf-8')
add(out/'native_progress.json',base+'snapshots/source_recovery_result07/native_progress.json')
add(out/'status.json','status/master_run_20261009.json');add(out/'STATUS.md','STATUS.md');add(out/'STORAGE_LEDGER.md','docs/master_run/STORAGE_LEDGER.md')
with (work/'master_source_recovery_result07_git_plan.json').open('x',encoding='utf-8') as stream:
 json.dump({'expected_head':'09d0092aa19431234db6b7a55a449b7d887ccb2d','message':'Confirm fresh GitHub recovery of all1938 IQ-TREE source blobs; preserve directory metadata-check failure for diagnosis','files':files},stream,indent=2);stream.write('\n')
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
