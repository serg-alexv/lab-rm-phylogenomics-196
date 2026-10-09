"""Reconcile one failed pre-exec setup against a stopped distro; preserve mounts longer."""
from pathlib import Path
import argparse,ctypes,hashlib,json,os,re,subprocess,tempfile
import atomic_iqtree_windows as A
W=Path(__file__).resolve().parent;O=W/'wsl_idle_repair13'
FAILED=W/'stage5_setup_runtime_actual_postiq_01'
CONFIG=Path(r'C:\Users\wheel\.wslconfig')
STOP=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
def listing():
 r=subprocess.run([r'C:\Windows\System32\wsl.exe','--list','--verbose'],capture_output=True,timeout=15,check=True)
 t=r.stdout.decode('utf-16-le').lstrip('\ufeff')
 lines=[line.strip().lstrip('*').strip() for line in t.splitlines() if line.strip()]
 assert len(lines)==2 and re.fullmatch(r'Ubuntu\s+Stopped\s+2',lines[1]),'All registered distributions must actually be stopped'
 return {'argv':['wsl.exe','--list','--verbose'],'exit_code':r.returncode,'actual_stdout':t,
         'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true');a=p.parse_args()
 if not a.run:print('PREPARED_NO_CONFIGURATION_OR_STOP_CHANGE');return
 assert A.sha256(W/'atomic_iqtree_windows.py')=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
 prep=A.read_json(O/'preparation.json');assert A.sha256(CONFIG)==prep['before_sha256']
 assert A.sha256(O/'wslconfig.before.txt')==prep['before_sha256'] and A.sha256(O/'wslconfig.after.txt')==prep['after_sha256']
 launch=A.read_json(FAILED/'launch.json');failure=A.read_json(FAILED/'result.json');old_stop=A.read_json(STOP)
 assert failure['state']=='FAILED' and failure['error']['kind']=='FileNotFoundError'
 assert failure['owned_closure_proven'] is False and old_stop['owner_nonce']==launch['owner_nonce']==failure['owner_nonce']
 assert old_stop['evidence']==str(FAILED) and not (FAILED/'linux_terminal.json').exists()
 argv=launch['argv'];expected='/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux/detector_env/bin/python'
 assert argv[5:8]==['--exec',expected,'-B']
 assert launch['native_wsl_client']['pid']==25136 and launch['native_wsl_client']['creation_filetime']==134360571824152279
 assert (FAILED/'wsl.stdout.txt').stat().st_size==0 and not (FAILED/'commands').exists()
 error=(FAILED/'wsl.stderr.txt').read_text(encoding='utf-8').strip()
 assert len(error)<1024 and re.fullmatch(r'<3>WSL \(\d+ - Relay\) ERROR: CreateProcessCommon:\d+: execvpe\('+re.escape(expected)+r'\) failed: No such file or directory',error)
 assert A.read_json(FAILED/'lock_released.json')['released'] is True
 assert not (O/'execution_receipt.json').exists()
 before_stop=STOP.read_bytes();saved=O/'failed_preexec_stop_preserved.json'
 with saved.open('xb') as f:f.write(before_stop)
 lock=A.WorkflowLock(A.Win());record={'schema':'MASTER_WSL_IDLE_PREEXEC_RECONCILIATION_V1','utc':A.utc(),
  'state':'FAILED_PRESERVED','source_sha256':A.sha256(__file__),
  'preexec_error_sha256':A.sha256(FAILED/'wsl.stderr.txt'),'failed_launch_sha256':A.sha256(FAILED/'launch.json'),
  'stop_sha256':hashlib.sha256(before_stop).hexdigest(),'wsl_shutdown_commands':0,'signals_sent':0,'detector_launches':0,
  'original_retained_windows_terminal_receipt':'NOT_RECONSTRUCTED; original wrapper lost local terminal before missing Linux receipt read',
  'closure_basis':'Exact execvpe failure before Linux helper execution plus two actual aggregate all-distro STOPPED observations under original lock; absence of a PID alone is insufficient',
  'idle_shutdown_diagnosis':'CONSISTENT_WITH_OLD_TOOLCHAIN_PROOF_AND_ACTUAL_STOPPED_DISTRO; reset/idle cause inferred, not directly instrumented'}
 try:
  with lock as owned:
   record['original_lock_identity']=owned.identity;record['stopped_before']=listing()
   assert STOP.read_bytes()==before_stop and A.sha256(CONFIG)==prep['before_sha256']
   fd,tmp=tempfile.mkstemp(prefix='.wslconfig-master-',dir=CONFIG.parent)
   try:
    with os.fdopen(fd,'wb') as f:f.write((O/'wslconfig.after.txt').read_bytes());f.flush();os.fsync(f.fileno())
    os.replace(tmp,CONFIG)
   finally:
    if os.path.exists(tmp):os.unlink(tmp)
   assert A.sha256(CONFIG)==prep['after_sha256'];record['actual_config_sha256']=A.sha256(CONFIG)
   record['stopped_after']=listing();assert STOP.read_bytes()==before_stop
   STOP.unlink();record['owned_stop_removed']=not STOP.exists()
   record['state']='PASS_PREEXEC_FAILURE_RECONCILED_AGGREGATE_STOPPED_FINITE_IDLE_CONFIG_APPLIED'
 finally:
  record['original_lock_explicitly_released']=lock.released
  with (O/'execution_receipt.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
 print(json.dumps({'state':record['state'],'config_sha256':record.get('actual_config_sha256')}))
if __name__=='__main__':main()
