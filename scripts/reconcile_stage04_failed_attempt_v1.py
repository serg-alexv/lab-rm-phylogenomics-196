"""Negative historical evidence only: never manufacture ordinary V6 closure."""
from pathlib import Path
import gzip, hashlib, json, shutil
import stage04_controller as C
import stage04_recovery_support_v9 as S

OBSERVER=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\referenced-chatgpt-conversation-this-is-an\outputs\native_v6_process_observer\exit.json')
KNOWN=[(8264,134359651662914448,'original_controller'),(29132,134359651870883542,'original_native'),
 (27464,134359641403414121,'original_cli'),(22176,134359754592961172,'original_publication_worker'),
 (29352,None,'native_observer'),(25952,None,'controller_observer'),(30700,None,'original_job_conhost')]

def reconcile(lock):
    S.pins();identity=S.lock_identity(lock);directory=S.OLD/'analyses/primary196/iqtree'
    observation=C.load(OBSERVER);launch=C.load(directory/'attempt_0001/launch.json')
    C.check(observation['status']=='ACTUAL_BOUND_WINDOWS_PROCESS_EXIT_OBSERVED' and observation['target_pid']==launch['child_pid']==29132 and
      observation['target_creation_filetime']==launch['child_creation_filetime']==134359651870883542 and observation['exit_code_dword']==1 and
      observation['process_times']['exit_filetime']==134359758026498313,'Independent actual native exit1 proof differs')
    C.check(observation['on_disk_executable_sha256']==launch['actual_executable_sha256']==C.digest(launch['argv'][0]),'Native tool identity differs')
    missing=['attempt_0001/exit.json','tree_complete.json','host.ckp.gz']
    C.check(all(not (directory/x).exists() for x in missing),'Original missing evidence changed; new reconciliation revision required')
    rows=[{**S.process_identity(pid,token),'role':role,'recorded_creation_token_available':token is not None} for pid,token,role in KNOWN]
    C.check(all(r['state'] in ('ABSENT_WIN32_ERROR_INVALID_PARAMETER','EXITED','PID_REUSED_DIFFERENT_CREATION') for r in rows),'Old bound process still alive; retry blocked')
    # Bounded Windows process inventory: scientific project runner candidates only.
    ps=['powershell.exe','-NoProfile','-NonInteractive','-Command',
      "$ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'iqtree|python|wsl|bash|Rscript|hmmscan|hmmsearch' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine) | ConvertTo-Json -Depth 4 -Compress"]
    candidates=json.loads(S.command(ps).decode('utf-8-sig') or '[]')
    if isinstance(candidates,dict):candidates=[candidates]
    live=[]
    for row in candidates:
        text=(row.get('CommandLine') or '').lower();pid=row['ProcessId']
        match=('iqtree' in row['Name'].lower() or ('lab-rm-phylogenomics-196' in text and any(x in text for x in
          ('stage04_native','recovery_controller','stage05_detectors','continue_stage04','hmmscan','hmmsearch'))))
        if match and pid!=__import__('os').getpid():live.append({**S.process_identity(pid),'role':'matching_runner'})
    C.check(not live,'Matching live project runner found; no duplicate launch')
    target=S.RUNTIME/'negative_history_v1';target.mkdir(parents=True,exist_ok=True)
    saved={}
    for f in sorted(directory.rglob('*')):
        if not f.is_file():continue
        rel=f.relative_to(directory).as_posix();dest=target/'original_primary196'/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():C.check(C.digest(dest)==C.digest(f),'Preserved copy collision')
        else:shutil.copy2(f,dest)
        C.check(C.digest(dest)==C.digest(f),'Preserved failed artifact copy differs');saved[rel]={'sha256':C.digest(f),'bytes':f.stat().st_size}
    copy=target/'actual_native_observer_exit.json'
    if copy.exists():C.check(C.digest(copy)==C.digest(OBSERVER),'Observer preservation collision')
    else:shutil.copy2(OBSERVER,copy)
    cache=gzip.decompress((directory/'host.model.gz').read_bytes()).decode('utf-8')
    certificate={'schema':'failed_attempt_reconciliation_v1','utc':C.now(),'status':'NEGATIVE_HISTORY_ACTUAL_NATIVE_EXIT1_OLD_CLOSURE_UNKNOWN',
      'ordinary_success_receipt':False,'scientific_validation':'FAILED_INCOMPLETE','termination_cause':'NOT_ESTABLISHED',
      'original_controller_outcome':'UNKNOWN','original_final_job_accounting':'UNKNOWN','original_job_closure':'UNKNOWN',
      'old_guard':'UNCHANGED_B2_STILL_REJECTS_MISSING_ORDINARY_RECEIPTS','original_freeze_sha256':S.FREEZE_SHA,
      'original_adoption_sha256':C.digest(S.ROOT/'reports/stage04/native_windows_v6/adoption.json'),
      'frozen_source_sha256':S.FROZEN,'original_launch_sha256':C.digest(directory/'attempt_0001/launch.json'),
      'actual_native_observer_exit_sha256':C.digest(copy),'actual_native_exit':observation,
      'recorded_old_process_reconciliation':rows,'recorded_token_missing_roles':[r['role'] for r in rows if not r['recorded_creation_token_available']],
      'missing_original_files':missing,'exclusive_writer_boundary':identity,'matching_live_project_runners':live,
      'original_artifacts':saved,'preserved_artifacts_root':str(target),
      'input_and_tool_binding':C.load(S.OLD/'inference_freeze.json'),
      'cache':{'sha256':C.digest(directory/'host.model.gz'),'bytes':(directory/'host.model.gz').stat().st_size,
        'best_model_BIC_records':cache.count('best_model_BIC:'),'finishedFastMLTree_true':'finishedFastMLTree: true' in cache,
        'general_checkpoint':'ABSENT','compatible_cache_reuse':'REQUIRES_NEW_OBSERVED_TOOL_EVIDENCE'},
      'retry_protocol':'V9 may admit a separately reviewed retry from actual native failure and exclusive reconciled boundary; UNKNOWN old closure remains UNKNOWN',
      'limitations':['Creation tokens for the observer/helper/conhost are missing in retained records; their PID absence is explicitly recorded, never ordinary job closure.',
        'No cause of native exit1 is established by temporal correlation.','No tree or scientific PASS is established by this certificate.']}
    # Keep the large immutable original freeze separate rather than duplicate 196-tip metadata in a public negative certificate.
    binding=certificate.pop('input_and_tool_binding');certificate['input_file_sha256']=binding['source_identity']['file_sha256']
    certificate['tool_identity']=binding['tool_identity'];certificate['original_argv']=launch['argv']
    path=S.REPORT/'failed_attempt_reconciliation_v1.json';C.check(not path.exists(),'Negative certificate is immutable; existing revision must be read, not rewritten')
    C.atomic(path,certificate);C.atomic(target/'certificate.json',certificate)
    C.check(S.lock_identity(lock)==identity,'Stable lock file identity changed')
    return certificate

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        head=C.reconcile(S.ROOT);value=reconcile(lock)
        rows=(S.ROOT/'status/stages.tsv').read_text().splitlines()
        rows=[('4_phylogeny\tFAILED_INCOMPLETE_NATIVE_EXIT1\tPASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE\tSTAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING' if r.startswith('4_phylogeny\t') else r) for r in rows]
        (S.ROOT/'status/stages.tsv').write_text('\n'.join(rows)+'\n',encoding='utf-8',newline='\n')
        detail='IQ-TREE primary196 exited1 at2026-10-08T23:30:02.6498313Z, independently observed for PID29132 and exact creation token. Native CPU16131.484375s. Original controller outcome and final JobObject closure remain UNKNOWN; ordinary exit/tree-complete receipts are absent. Model cache and all original outputs are preserved. No termination cause is established. V9 recovery preparation requires an actual one-shot Scheduler lifetime fixture and hash-bound parent acceptance before production. Stages05–07 remain NOT_RUN.'
        table='\n'.join('| '+' | '.join(r.split('\t'))+' |' for r in rows[1:])
        (S.ROOT/'STATUS.md').write_text('# Current execution status\n\nUpdated '+C.now()+'. Full approved196 production cohort; no pilot.\n\n'+detail+'\n\n| Stage | Execution | Validation | Publication |\n|---|---|---|---|\n'+table+'\n\nSee reports/stage04/recovery_v9/failed_attempt_reconciliation_v1.json. Private session traces are excluded.\n',encoding='utf-8',newline='\n')
        C.atomic(S.ROOT/'status/stage04_execution.json',{'utc':C.now(),'execution':'FAILED_INCOMPLETE_NATIVE_EXIT1','negative_history_certificate_sha256':C.digest(S.REPORT/'failed_attempt_reconciliation_v1.json'),'original_controller_outcome':'UNKNOWN','original_job_closure':'UNKNOWN','recovery':'PREPARATION_NOT_ADOPTED_NOT_LAUNCHED','stages05_07':'NOT_RUN'})
        files=['STATUS.md','status/stages.tsv','status/stage04_execution.json','reports/stage04/recovery_v9/failed_attempt_reconciliation_v1.json','scripts/reconcile_stage04_failed_attempt_v1.py','scripts/stage04_recovery_support_v9.py']
        receipt=S.publish(files,'Record independently observed IQ-TREE failure and preserve unknown historical closure')
        C.atomic(S.RUNTIME/'negative_history_publication.json',receipt)
        print(json.dumps({'status':receipt['status'],'commit':receipt['commit'],'negative_certificate_sha256':C.digest(S.REPORT/'failed_attempt_reconciliation_v1.json')}))

if __name__=='__main__':main()
