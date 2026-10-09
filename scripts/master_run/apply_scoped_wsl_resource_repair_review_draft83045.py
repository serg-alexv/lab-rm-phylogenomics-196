"""Apply authorized4GiB WSL ceiling after a fresh guarded observation; preserve failures."""
from pathlib import Path
import argparse,hashlib,json,os,re,stat,subprocess,tempfile,uuid
import atomic_iqtree_windows as A
W=Path(__file__).resolve().parent;O=W/'wsl_resource_repair15';CONFIG=Path(r'C:\Users\wheel\.wslconfig')
STOP=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json');WSL=r'C:\Windows\System32\wsl.exe'
PINS={CONFIG:'6c1f518719def3826ff78d03329e54cb7e3f23745f6bd25b0b0b3ffd1d600022',
 O/'wslconfig.after.txt':'31b59c84adf6bf7b0fdf0cd42ee6298cd9dc7c20032ab30d97c3f22dbb3b6982',
 STOP:'ef5e47644dc961ed1945d707c3dd993fe9f0370980f094ff741a3d1253d13462',
 W/'diagnose_failed_stage5_scope.py':'c97d6008a7492642d899365d8a1a9c8678c2c07b2b6f6dba9ac08dd2375564e6',
 W/'stage5_failed_scope_diagnostic01/stdout.json':'a39811f90050007245a057f40ae207db2d769e18cda2ed41da95c2fee431cded',
 W/'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true');a=p.parse_args()
 if not a.run:print('PREPARED_NO_CONFIG_CHANGE_SHUTDOWN_OR_STOP_REMOVAL');return 0
 A.require(W==Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'),'Exact C work required')
 for path,pin in PINS.items():A.require(A.sha256(path)==pin,'Pinned repair evidence differs: '+str(path))
 for path in (CONFIG,*CONFIG.parents,STOP):
  info=path.lstat();A.require(not path.is_symlink() and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,'Alias in exact configuration scope')
 A.require(stat.S_ISREG(CONFIG.stat().st_mode) and stat.S_ISREG(STOP.stat().st_mode),'Regular original files required')
 A.require(not (O/'execution_receipt.json').exists(),'Preserve previous actual repair')
 api=A.Win();owner=api.identity(api.current(),os.getpid());lock=A.WorkflowLock(api);nonce=uuid.uuid4().hex
 record={'schema':'MASTER_SCOPED_WSL_RESOURCE_REPAIR_V1','utc':A.utc(),'state':'FAILED_PRESERVED',
  'source_sha256':A.sha256(__file__),'commands':[],'host_reboots':0,'scientific_launches':0,
  'authority':'Direct user authorized entire WSL reconfiguration if needed; current setup resource failure is preserved',
  'prior_lost_windows_terminal':'NOT_RECONSTRUCTED; actual authorized VM stop supplies separate aggregate Linux closure',
  'population_observation':'Racing observation; no atomic exclusivity claim. Unknown/racing processes veto this scoped repair.'}
 def command(argv,stem,timeout=20):
  with (O/(stem+'.stdout.txt')).open('xb') as stdout,(O/(stem+'.stderr.txt')).open('xb') as stderr:
   child=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
   born=api.identity(int(child._handle),child.pid,WSL,owner['session_id'])
   row={'argv':argv,'retained_birth':born};record['commands'].append(row)
   try:child.wait(timeout=timeout)
   finally:
    if child.poll() is not None:row['retained_terminal']=api.identity(int(child._handle),child.pid,WSL,owner['session_id'])
   terminal=row['retained_terminal'];A.require(terminal['exit_code']==0 and terminal['exited']
    and terminal['creation_filetime']==born['creation_filetime'] and terminal['exit_filetime']>born['creation_filetime'],'Actual owned WSL command exit0 required')
  return O/(stem+'.stdout.txt')
 def registered(stopped=False,stem='registered_before'):
  path=command([WSL,'--list','--verbose'],stem);text=path.read_bytes().decode('utf-16-le').lstrip('\ufeff')
  lines=[x.strip().lstrip('*').strip() for x in text.splitlines() if x.strip()]
  A.require(len(lines)==2 and re.fullmatch(r'Ubuntu\s+'+('Stopped' if stopped else '(Running|Stopped)')+r'\s+2',lines[1]),'Only the exact registered Ubuntu WSL2 scope is allowed')
  return text
 try:
  with lock as owned:
   record['original_lock_identity']=owned.identity;record['registered_before']=registered()
   res=api.resources([O]);record['actual_admission']=res
   A.require(res['physical_available_bytes']>=1610612736 and res['commit_headroom_bytes']>=1610612736,'Preserve1.5GiB reserve for read-only repair')
   diag=command([WSL,'-d','Ubuntu','-u','root','--exec','/usr/bin/python3','-B',
    '/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/diagnose_failed_stage5_scope.py','--linux-observe','--nonce',nonce],'fresh_observation')
   A.require(diag.stat().st_size<2*1024**2,'Bounded observation exceeded');fresh=A.read_json(diag)
   prior=A.read_json(W/'stage5_failed_scope_diagnostic01/stdout.json')
   A.require(fresh['nonce']==nonce and fresh['source_sha256']==PINS[W/'diagnose_failed_stage5_scope.py']
    and fresh['boot_id']==prior['boot_id'] and not fresh['process_observation_races'],'Fresh exact-boot observation required')
   previous={r['pid']:r for r in prior['processes']}
   for row in fresh['processes']:
    if row['pid']==fresh['self_pid']:continue
    if row['executable']=='/init' and (row['comm']=='SessionLeader' or row['comm'].startswith('Relay(')):continue
    if row['executable']=='/usr/bin/udevadm' and row['comm']=='(udev-worker)':continue
    old=previous.get(row['pid']);A.require(old is not None and all(row[k]==old[k] for k in ('start_ticks','comm','executable','uid_record')),'Unknown process; preserve scope rather than restart')
   A.require(A.sha256(CONFIG)==PINS[CONFIG] and A.sha256(STOP)==PINS[STOP],'Original control changed')
   fd,tmp=tempfile.mkstemp(prefix='.wslconfig-master-',dir=CONFIG.parent)
   try:
    with os.fdopen(fd,'wb') as f:f.write((O/'wslconfig.after.txt').read_bytes());f.flush();os.fsync(f.fileno())
    os.replace(tmp,CONFIG)
   finally:
    if os.path.exists(tmp):os.unlink(tmp)
   record['actual_config_sha256']=A.sha256(CONFIG);A.require(record['actual_config_sha256']==PINS[O/'wslconfig.after.txt'],'Configuration readback differs')
   command([WSL,'--shutdown'],'authorized_shutdown',30)
   record['registered_stopped01']=registered(True,'registered_stopped01')
   record['registered_stopped02']=registered(True,'registered_stopped02')
   A.require(A.sha256(STOP)==PINS[STOP] and A.sha256(O/'original_failed_stop.json')==PINS[STOP],'Original failed stop backup differs')
   STOP.unlink();record.update(state='PASS_AUTHORIZED_VM_STOP_4GIB_CONFIG_AGGREGATE_SCOPE_CLOSED',owned_stop_removed=not STOP.exists(),wsl_vm_shutdowns=1)
 except BaseException as error:record.update(state='FAILED_PRESERVED',error_kind=type(error).__name__,error_message=str(error));raise
 finally:
  record['original_lock_explicitly_released']=lock.released
  with (O/'execution_receipt.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
 print(json.dumps({'state':record['state'],'config_sha256':record['actual_config_sha256']}));return 0
if __name__=='__main__':raise SystemExit(main())
