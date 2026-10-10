"""Default-noop exact old STOP reconciliation using an independently observed new boot.

Preserves the old failed scope. Cancels only our exact pending RunOnce value and
consumes its private one-shot latch before STOP removal. No WSL/process signaling.
"""
from pathlib import Path
import argparse, ctypes, datetime, hashlib, json, os, subprocess, winreg
import atomic_iqtree_windows as A
import resume_master_after_boot_once as B
import register_master_boot_resume_once as R

W=Path(__file__).resolve().parent
REVIEW=W/'newboot_independent_review01.json'
AUTH=W/'postboot_authority_review01.json'
OUT=W/'master_newboot_reconciliation_actual01.json'
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
      'resume_master_after_boot_once.py':'896f33d10d419d531327df02d72a48507895cbc7ffa7bf44129ae85c1c1b2a2f',
      'register_master_boot_resume_once.py':'92996842ac877a9056c8f6ea0946e623d9da2a9ac826a77a0abe16b829740a2c'}
PS=r'''$ErrorActionPreference='Stop'; $rows=@(Get-CimInstance Win32_Process); $selected=@(); $helpers=@();
foreach($row in $rows){if($row.ProcessId -eq $PID){continue}; $n=$row.Name.ToLowerInvariant(); $a=$row.CommandLine;
 if(($n -in @('python.exe','pythonw.exe','wsl.exe','bash.exe','sh.exe')) -and
   (($a -match '(?i)(stage0[45]_|stage5_(setup|windows_owner|unc_bind|archive|interop|closed_genome_archive_windows|gdrive_view)|atomic_iqtree_windows\.py)') -or $null -eq $a)){
   $selected += [pscustomobject]@{pid=$row.ProcessId;name=$row.Name;born=$row.CreationDate.ToUniversalTime().ToString('o');unreadable_argv=($null -eq $a)}}
 if($n -in @('iqtree.exe','iqtree2.exe','iqtree3.exe','hmmsearch.exe','hmmscan.exe','padloc.exe','defense-finder.exe')){
   $selected += [pscustomobject]@{pid=$row.ProcessId;name=$row.Name;born=$row.CreationDate.ToUniversalTime().ToString('o');unreadable_argv=($null -eq $a)}}
 if((($n -in @('python.exe','pythonw.exe')) -and ($a -match '(?i)resume_master_after_boot_once\.py')) -or
    (($n -in @('powershell.exe','pwsh.exe')) -and ($a -match '(?i)-File\s+"?C:[^\r\n"]+Resume-MasterAfterBootOnce\.ps1')) -or
    (($n -eq 'codex.exe') -and ($a -match '(?i)\bexec\b.*\bresume\b'))){
   $helpers += [pscustomobject]@{pid=$row.ProcessId;name=$row.Name;born=$row.CreationDate.ToUniversalTime().ToString('o')}}
}
$tasks=@(Get-ScheduledTask | Where-Object TaskName -like 'LAB_RM_*' | ForEach-Object {[pscustomobject]@{name=$_.TaskName;state=[string]$_.State}});
[pscustomobject]@{rows=$rows.Count;selected=$selected;helpers=$helpers;tasks=$tasks;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 6 -Compress'''

def snapshot():
    done=subprocess.run([str(B.POWERSHELL),'-NoLogo','-NoProfile','-NonInteractive','-Command',PS],
        capture_output=True,check=True,timeout=25,creationflags=0x08000000)
    value=json.loads(done.stdout.decode('utf-8-sig'))
    A.require(value['selected']==[] and value['helpers']==[],'Current project owner or resume helper still present')
    A.require(len(value['tasks'])==18 and all(x['state']=='Disabled' for x in value['tasks']),'Legacy LAB tasks not all disabled')
    return value

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true')
    p.add_argument('--review-sha256');p.add_argument('--authority-sha256');a=p.parse_args()
    if not a.run:print(json.dumps({'state':'PREPARED_DEFAULT_NOOP'}));return
    A.require(os.name=='nt' and os.environ.get('COMPUTERNAME','').upper()=='WD'
              and os.environ.get('USERNAME','').lower()=='wheel' and W==B.WORK,'Exact WD wheel workspace required')
    A.require(not OUT.exists(),'Preserve prior reconciliation receipt')
    for name,pin in PINS.items():A.require(A.sha256(W/name)==pin,'Pinned helper differs')
    A.require(A.sha256(REVIEW)==a.review_sha256 and A.sha256(AUTH)==a.authority_sha256,'Independent evidence changed')
    peer=A.read_json(REVIEW);authority=A.read_json(AUTH)
    A.require(peer['current_boot']['advanced_last_boot'] and peer['current_boot']['reset_uptime']
              and peer['original_lock_identity_matches'] and peer['original_stop']['exact_original_bytes']
              and peer['process_snapshot']['helper_candidates']==0 and peer['process_snapshot']['exec_resume_candidates']==0,
              'Independent new-boot predicates failed')
    A.require(authority['state']=='PASS_CURRENT_AUTHORITY_AND_LOCAL_PUBLISHED_SOURCES'
              and authority['initial_remote_main']==authority['final_remote_main'],'Remote authority not reconciled')
    A.require(A.sha256(W/'master_boot_resume_preboot_baseline.json')==peer['baseline_sha256'],
              'Exact independently pinned preboot baseline required')
    baseline=A.read_json(W/'master_boot_resume_preboot_baseline.json');current=B.boot_observation();B.new_boot(baseline,current)
    A.require(datetime.datetime.fromisoformat(current['last_boot_utc'])==datetime.datetime.fromisoformat(peer['current_boot']['last_boot_utc']),
              'Independent boot witness differs')
    api=A.Win();lock=A.WorkflowLock(api)
    record={'schema':'MASTER_NEW_BOOT_STOP_RECONCILIATION_V1','state':'FAILED_STOP_PRESERVED',
      'source_sha256':A.sha256(__file__),'source_pins':PINS,'utc':A.utc(),'current_boot':current,'baseline':baseline,
      'independent_review_sha256':a.review_sha256,'authority_review_sha256':a.authority_sha256,
      'authority_commit':authority['final_remote_main'],'old_terminal_receipt':'UNRECORDED_PRESERVED_FAILURE',
      'old_scope_retroactively_passed':False,'current_scope_basis':'VERIFIED_NEW_WINDOWS_KERNEL_BOOT_AND_FRESH_EXCLUSIVITY',
      'WSL_started':False,'process_signals':0,'private_session_identity_read_or_published':False}
    try:
        with lock:
            record['workflow_lock']=lock.identity
            A.require(A.sha256(B.STOP)==B.EXPECTED_STOP,'Exact original STOP required')
            saved=W/'drivefs_actual02_original_STOP.json'
            A.require(A.sha256(saved)==B.EXPECTED_STOP,'Original STOP preserved copy differs')
            record['original_STOP_sha256']=B.EXPECTED_STOP
            record['before']=snapshot()
            latch=B.PRIVATE/'CONSUMED_SINGLE_USE.json'
            A.require(not latch.exists(),'One-time helper has already consumed; reconcile its actual scope')
            # Exclusive creation races safely with the launcher's own exclusive latch.
            B.write_new(latch,{'schema':'PRIVATE_MASTER_RUNONCE_CONSUMED_V1',
                'state':'CANCELLED_BY_HUMAN_MASTER_POSTBOOT_CONTINUATION_NO_CLI_LAUNCH','utc':A.utc(),
                'rearm_authorized':False,'private_thread_id_included':False})
            record['one_shot_latch_consumed_without_launch']=True
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,R.KEY,0,winreg.KEY_QUERY_VALUE|winreg.KEY_SET_VALUE) as key:
                names=[]
                for i in range(winreg.QueryInfoKey(key)[1]):names.append(winreg.EnumValue(key,i)[0])
                matches=[n for n in names if n.casefold()==R.NAME.casefold()]
                A.require(matches==[R.NAME],'Pending exact startup value changed or absent')
                value,kind=winreg.QueryValueEx(key,R.NAME)
                A.require(value==R.COMMAND and kind==winreg.REG_SZ,'Only exact reviewed own startup may be cancelled')
                record['cancelled_startup']={'key':'HKCU\\'+R.KEY,'name':R.NAME,'command':value,'kind':kind}
                winreg.DeleteValue(key,R.NAME);winreg.FlushKey(key)
                try:winreg.QueryValueEx(key,R.NAME);raise ValueError('Own RunOnce still exists')
                except FileNotFoundError:record['startup_value_absent_readback']=True
            record['after_startup_cancellation']=snapshot()
            A.require(A.sha256(B.STOP)==B.EXPECTED_STOP and A.sha256(saved)==B.EXPECTED_STOP,'Preserved STOP drift')
            record['resources']=api.resources([W,Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')])
            record.update(state='QUALIFIED_NEW_BOOT_STOP_REMOVAL_INTENT',old_failure_preserved=True)
            A.atomic(OUT,record)
            B.STOP.unlink()
            A.require(not B.STOP.exists(),'Exact old STOP remains')
            record.update(state='PASS_NEW_BOOT_CURRENT_SCOPE_RECONCILED_OLD_FAILURE_PRESERVED',old_STOP_removed=True,utc=A.utc())
    finally:
        record['original_lock_released']=lock.released
        A.atomic(OUT,record)
    print(json.dumps({'state':record['state'],'receipt':str(OUT),'sha256':A.sha256(OUT)}))

if __name__=='__main__':main()
