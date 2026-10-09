"""Publish actual package recovery and directory execution checkpoints without acceptance inflation."""
from pathlib import Path
from collections import Counter
import datetime,hashlib,json

work=Path(__file__).resolve().parent;out=work/'master_recovery_receipts05';out.mkdir(exist_ok=False)
base='reports/master_run/20261009/';files=[]
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def add(local,target,pin=None):
    path=Path(local)
    if not path.is_absolute():path=work/path
    digest=sha(path);assert pin is None or digest==pin,str(path)
    assert 0<path.stat().st_size<5*1024**2
    files.append({'local_absolute_path':str(path),'target':target,'bytes':path.stat().st_size,'sha256':digest})
conda='public_conda_packages01_readback_20261009T212013Z_9326e9e6/receipt.json'
add(conda,base+'cleanup/conda_packages01/REMOTE_READBACK.json','02d56dc933db94af3b93a737e55ffd4463cdc88e9e96cb885c02bc6311b6ea6a')
add('iqtree314_source_recovery_local_inspection_20261009T212142Z_68402681.json',base+'cleanup/iqtree314_source01/INDEPENDENT_LOCAL_INSPECTION.json',
    '650b199cc1f13a46a925eae6ace7219727ff867ad7492cd73ee310e238188964')
add('inspect_iqtree314_source_recovery_local.py','scripts/master_run/inspect_iqtree314_source_recovery_local.py',
    'd0944378ea204a986ed512b35838a5c554266bb88201ad20076e8d857e514df9')
for local,target in {
 'master_iqtree_source_assets_upload_plan.json':'cleanup/iqtree314_source01/UPLOAD_PLAN.json',
 'master_iqtree_source_assets_upload_receipt.json':'cleanup/iqtree314_source01/UPLOAD_RECEIPT.json',
 'master_directory_authority01_git_objects.json':'publication/DIRECTORY_AUTHORITY01_GIT_OBJECTS.json',
 'master_directory_authority01_remote_readback.json':'publication/DIRECTORY_AUTHORITY01_REMOTE_READBACK.json',
}.items():add(local,base+target)
for name in (Path(__file__).name,'accept_stage4_after_native_closure.py','accept_stage4_after_native_closure_pre_diagnostic_review.py'):
    add(name,'scripts/master_run/'+name)
journal=work/'master_directory_prune01_execution.jsonl';before=sha(journal);counts=Counter();first=last=None
with journal.open(encoding='utf-8') as stream:
    for line in stream:
        row=json.loads(line);counts[row['event']]+=1
        if first is None:first=row
        last=row
assert before==sha(journal)
assert dict(counts)=={'BEGIN':1,'BEFORE_DISPOSITION':5542,'DISPOSITION_MARKED_ON_EXACT_DIRECTORY_HANDLE':5542,'AFTER_REMOVED':5542,'COMPLETE':1}
assert last['state']=='PASS_EXACT5542_EMPTY_DIRECTORY_HANDLES_REMOVED'
summary={'schema':'MASTER_DIRECTORY_PRUNE_EXECUTION_CHECKPOINT_V1','state':'EXECUTION_EXIT0_INDEPENDENT_POSTVERIFY_PENDING',
 'unified_exec_session':9980,'actual_tool_reported_exit_code':0,'journal':{'bytes':journal.stat().st_size,'sha256':before,'record_counts':dict(counts)},
 'begin':first,'terminal':last,'full_journal_remote_recovery':'PENDING','independent_filesystem_postverify':'PENDING',
 'host_wipe_authorized':False}
(out/'directory_execution_checkpoint.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
add(out/'directory_execution_checkpoint.json',base+'cleanup/emptydirs_prune01/EXECUTION_CHECKPOINT.json')
now=datetime.datetime.now(datetime.timezone.utc)
raw=(work/'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_bytes();native=json.loads(raw)
assert 0<=(now-datetime.datetime.fromisoformat(native['utc'])).total_seconds()<60 and native['exited'] is False
(out/'native_progress.json').write_bytes(raw)
status=json.loads((work/'master_recovery_verified04/status.json').read_bytes())
status.update(updated_utc=now.isoformat(),native_process=native,latest_progress_snapshot=base+'snapshots/recovery_receipts05/native_progress.json')
status['recovery_preparation']['conda_originals'].update(remote_payload_recovery='PASS_FRESH_REMOTE339_ORIGINALS_397_ROLES_363_MEMBERS',
    remote_receipt=base+'cleanup/conda_packages01/REMOTE_READBACK.json',owned_download_commands=26,owned_download_command_closure='ALL_EXIT0')
status['recovery_preparation']['iqtree_full_source'].update(independent_local_inspection='PASS_ALL1938_ORIGINAL_GITBLOBS_AND31_MEMBERS',
    uploaded_assets=2,remote_recovery='PENDING_INDEPENDENT_FRESH_READBACK')
status['cleanup']['empty_directory_proposal'].update(pruning='EXECUTION_EXIT0_5542_REMOVED_INDEPENDENT_POSTVERIFY_PENDING',
    execution_checkpoint=base+'cleanup/emptydirs_prune01/EXECUTION_CHECKPOINT.json',full_journal_remote_recovery='PENDING')
status['cleanup']['empty_directory_proposal']['execution_preparation'].update(production_execution='EXIT0_POSTVERIFY_PENDING',authority_created=True)
(out/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
md=(work/'master_recovery_verified04/STATUS.md').read_text(encoding='utf-8')
md=md.replace('snapshots/recovery_verified04/native_progress.json','snapshots/recovery_receipts05/native_progress.json')
md=md.replace('Production directory pruning has NOT_RUN.','Actual pruning exited 0 and records all 5,542 exact directories removed; both owners stayed alive and all 12 protected hashes matched. Independent filesystem post-verification and full journal remote recovery remain pending.')
md=md.replace('Its actual\nfresh remote payload check remains pending.','Its actual fresh remote payload check now PASS: all 339 originals / 397 role joins / 363 archive members / 361 SUMS; all 26 owned downloader commands exited 0 and closed.')
md=md.replace('Release upload and independent fresh source recovery readback remain pending.','An independent local inspector also streamed all 1,938 original Gitblob joins and gzip EOF checks successfully. Both Release assets are uploaded; independent fresh source recovery readback remains pending.')
md=md.replace('Updated '+json.loads((work/'master_recovery_verified04/status.json').read_bytes())['updated_utc'], 'Updated '+now.isoformat())
(out/'STATUS.md').write_text(md,encoding='utf-8')
ledger=(work/'master_recovery_verified04/STORAGE_LEDGER.md').read_text(encoding='utf-8')
ledger+='\nActual fresh Conda remote recovery PASS: 339 original packages / 397 role joins / 363 members / 361 SUMS, all 26 owned downloader commands closed exit 0. IQ-TREE source independent local recovery PASS for all 1,938 original Gitblob joins; both assets uploaded, fresh remote pending. Directory execution exit 0 records 5,542 removals / 16,628 journal records with protected hashes/owners unchanged; independent filesystem post-check and full journal recovery pending. Accepted cleanup directory total remains 15 until that check passes.\n'
(out/'STORAGE_LEDGER.md').write_text(ledger,encoding='utf-8')
add(out/'native_progress.json',base+'snapshots/recovery_receipts05/native_progress.json')
add(out/'status.json','status/master_run_20261009.json');add(out/'STATUS.md','STATUS.md');add(out/'STORAGE_LEDGER.md','docs/master_run/STORAGE_LEDGER.md')
assert len({r['target'] for r in files})==len(files)
with (work/'master_recovery_receipts05_git_plan.json').open('x',encoding='utf-8') as stream:
 json.dump({'expected_head':'8939f93dd8506bf7174aa5f487a3fbe2f6430565','message':'Confirm339 original packages from fresh GitHub payloads and record exact empty-directory execution checkpoint','files':files},stream,indent=2);stream.write('\n')
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
