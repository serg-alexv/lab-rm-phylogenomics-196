"""Register one exact current-user continuation; default no-op, never reboot."""
from pathlib import Path
import argparse, hashlib, json, os, uuid, winreg

W=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PRIVATE=W/'private_master_boot_resume01'
NAME='LAB_RM_MasterBootResume_20261010'
KEY=r'Software\Microsoft\Windows\CurrentVersion\RunOnce'
COMMAND=(r'"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" '
         r'-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass '
         r'-File "C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work\Resume-MasterAfterBootOnce.ps1" -Run')
PINS={'resume_master_after_boot_once.py':'896f33d10d419d531327df02d72a48507895cbc7ffa7bf44129ae85c1c1b2a2f',
      'Resume-MasterAfterBootOnce.ps1':'a356bc02b46fa3c56a93e3ead38b3db669219ba9a3adcbabace8343b47356493',
      'master_boot_resume_preboot_baseline.json':'621fd2f2dc7b5afd695ae3e9c60a8fff4144b7f55a54f4907d040df53140b265',
      'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'}
STOP=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\stage05_owned_closure_unproven.json')
STOP_SHA='3de7057780d280d5f204b535207a174e616ca425b5638fe9848a48cfca20838a'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true');a=p.parse_args()
    if not a.run:
        print(json.dumps({'state':'PREPARED_NOT_REGISTERED','name':NAME,'command_characters':len(COMMAND)}));return
    assert os.name=='nt' and os.environ.get('COMPUTERNAME','').upper()=='WD'
    assert Path(__file__).resolve().parent==W and len(COMMAND)<=260 and not NAME.startswith('!')
    for name,pin in PINS.items():assert sha(W/name)==pin,name
    assert sha(STOP)==STOP_SHA and not (PRIVATE/'CONSUMED_SINGLE_USE.json').exists()
    manifest=json.loads((PRIVATE/'PRIVATE_HANDOFF_DO_NOT_PUBLISH.json').read_bytes())
    thread=os.environ['CODEX_THREAD_ID'];assert str(uuid.UUID(thread))==thread.lower()
    assert manifest['thread_id']==thread,'Must register from the human master root context'
    assert manifest['baseline']==json.loads((W/'master_boot_resume_preboot_baseline.json').read_bytes())
    receipt=W/'master_boot_resume_registration_actual01.json';assert not receipt.exists()
    import atomic_iqtree_windows as A
    api=A.Win();record={'schema':'MASTER_RUNONCE_REGISTRATION_V1','state':'FAILED_NOT_REGISTERED',
        'name':NAME,'key':'HKCU\\'+KEY,'command':COMMAND,'command_characters':len(COMMAND),
        'root_human_thread_verified_privately':True,'private_session_identity_disclosed':False,
        'source_sha256':sha(Path(__file__)),'source_pins':PINS,'STOP_sha256':STOP_SHA,
        'reboot_performed':False,'actual_resume_proven':False,'science_authority':False}
    lock=A.WorkflowLock(api)
    try:
        with lock:
            record['workflow_lock']=lock.identity
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,KEY,0,winreg.KEY_QUERY_VALUE|winreg.KEY_SET_VALUE) as key:
                names=[];i=0
                while True:
                    try:names.append(winreg.EnumValue(key,i)[0]);i+=1
                    except OSError as e:
                        if e.winerror!=259:raise
                        break
                assert NAME not in names,'Preserve existing startup value'
                record['preexisting_value_names']=names
                assert sha(STOP)==STOP_SHA
                winreg.SetValueEx(key,NAME,0,winreg.REG_SZ,COMMAND);winreg.FlushKey(key)
                value,kind=winreg.QueryValueEx(key,NAME)
                assert value==COMMAND and kind==winreg.REG_SZ
                record.update(state='REGISTERED_EXACT_READBACK_SINGLE_USE_NEXT_SIGNIN_ONLY',
                    registry_readback_exact=True,registration_utc=A.utc(),STOP_unchanged=sha(STOP)==STOP_SHA)
    except BaseException as error:
        record['error_kind']=type(error).__name__
        raise
    finally:
        record['original_lock_released']=lock.released;A.atomic(receipt,record)
    print(json.dumps({'state':record['state'],'receipt':str(receipt),'sha256':sha(receipt)}))

if __name__=='__main__':main()
