"""Read-only scoped reconciliation observations; never clear stops or stop WSL."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,uuid
W=Path(__file__).resolve().parent
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def linux(nonce):
 if os.name!='posix':raise RuntimeError('Linux observation requires POSIX')
 rows=[];errors=[]
 for p in sorted(Path('/proc').iterdir(),key=lambda p:p.name):
  if not p.name.isdigit():continue
  if len(rows)>=4096:raise RuntimeError('Bounded proc observation exceeded')
  try:
   raw=(p/'stat').read_text();end=raw.rfind(')');tail=raw[end+2:].split()
   status=(p/'status').read_text();uids=[r for r in status.splitlines() if r.startswith('Uid:')]
   try:exe=os.readlink(p/'exe')
   except FileNotFoundError:exe=None
   rows.append(dict(pid=int(p.name),comm=raw[raw.index('(')+1:end],state=tail[0],ppid=int(tail[1]),
    start_ticks=tail[19],uid_record=uids[0] if uids else None,executable=exe))
  except FileNotFoundError:errors.append({'pid':int(p.name),'state':'VANISHED_DURING_OBSERVATION'})
  except PermissionError:errors.append({'pid':int(p.name),'state':'UNREADABLE_PRESERVE_UNCERTAINTY'})
 image=Path('/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux')
 probe=image/'detector_env/bin/python'
 value={'schema':'MASTER_READ_ONLY_LINUX_SCOPE_OBSERVATION_V1','nonce':nonce,'source_sha256':sha(__file__),
  'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'self_pid':os.getpid(),
  'self_mount_namespace':os.readlink('/proc/self/ns/mnt'),'pid1_mount_namespace':os.readlink('/proc/1/ns/mnt'),
  'meminfo':Path('/proc/meminfo').read_text(),'mountinfo':Path('/proc/self/mountinfo').read_text(),
  'processes':rows,'process_observation_races':errors,'retained_interpreter_exists':probe.exists(),
  'retained_interpreter_is_file':probe.is_file(),'scientific_or_install_commands_launched':0,
  'stop_markers_changed':0,'vm_shutdowns':0,'acceptance_or_closure_created':False}
 print(json.dumps(value,sort_keys=True));return 0
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--linux-observe',action='store_true')
 p.add_argument('--nonce');p.add_argument('--run',action='store_true');a=p.parse_args()
 if a.linux_observe:
  if not a.nonce or len(a.nonce)!=32:raise RuntimeError('Exact owner nonce required')
  return linux(a.nonce)
 if not a.run:print('PREPARED_READ_ONLY_NO_LINUX_OR_LOCK');return 0
 import atomic_iqtree_windows as A
 A.require(os.name=='nt' and W==Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'),'Exact C source required')
 A.require(sha(W/'atomic_iqtree_windows.py')=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827','Existing Windows API source differs')
 out=W/'stage5_failed_scope_diagnostic01';out.mkdir(exist_ok=False);nonce=uuid.uuid4().hex
 api=A.Win();lock=A.WorkflowLock(api);child=None
 owner=api.identity(api.current(),os.getpid());wsl=r'C:\Windows\System32\wsl.exe'
 stop=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
 record={'schema':'MASTER_READ_ONLY_FAILED_STAGE5_SCOPE_DIAGNOSTIC_V1','utc':A.utc(),'state':'FAILED_PRESERVED',
  'source_sha256':sha(__file__),'nonce':nonce,'stop_markers_changed':0,'signals_sent':0,'vm_shutdowns':0,
  'prior_retained_windows_terminal':'NOT_RECONSTRUCTED; current population/boot observation is separate evidence',
  'scientific_acceptance_created':False,'known_prior_failure_spool':'stage5_setup_diagnose_actual_postiq_01'}
 try:
  with lock as owned:
   record['workflow_lock']=owned.identity;record['stop_sha256_before']=sha(stop)
   resources=api.resources([out]);record['actual_admission']=resources
   A.require(resources['physical_available_bytes']>=1610612736 and resources['commit_headroom_bytes']>=1610612736,
    'Read-only diagnostic retains actual1.5GiB Windows reserve')
   path='/mnt/c/Users/wheel/Documents/Codex/2026-10-09/new-chat/work/'+Path(__file__).name
   argv=[wsl,'-d','Ubuntu','-u','root','--exec','/usr/bin/python3','-B',path,'--linux-observe','--nonce',nonce]
   with (out/'stdout.json').open('xb') as stdout,(out/'stderr.txt').open('xb') as stderr:
    child=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
    born=api.identity(int(child._handle),child.pid,wsl,owner['session_id']);record['launch']={'argv':argv,'retained_wsl_client':born}
    child.wait(timeout=20)
    record['terminal']=api.identity(int(child._handle),child.pid,born['executable'],born['session_id'])
   A.require(record['terminal']['exited'] and record['terminal']['exit_code']==0
    and record['terminal']['creation_filetime']==born['creation_filetime']
    and record['terminal']['exit_filetime']>born['creation_filetime'],'Actual read-only client exit required')
   A.require((out/'stdout.json').stat().st_size<2*1024**2,'Bounded diagnostic stdout exceeded')
   observed=A.read_json(out/'stdout.json')
   A.require(observed['nonce']==nonce and observed['source_sha256']==sha(__file__),'Actual Linux observation binding differs')
   record.update(state='PASS_READ_ONLY_OBSERVATION_NO_PRIOR_CLOSURE_CLAIM',stdout_sha256=sha(out/'stdout.json'),
    stderr_sha256=sha(out/'stderr.txt'),observed_boot=observed['boot_id'],process_count=len(observed['processes']))
   record['stop_sha256_after']=sha(stop);A.require(record['stop_sha256_before']==record['stop_sha256_after'],'Stop changed during observation')
 except BaseException as e:
  record.update(state='FAILED_PRESERVED',error_kind=type(e).__name__,error_message=str(e))
  if child is not None:
   record['client_poll_after_error']=child.poll()
   if child.poll() is not None:record['terminal_after_error']=api.identity(int(child._handle),child.pid,wsl,owner['session_id'])
  raise
 finally:
  record['original_lock_explicitly_released']=lock.released
  with (out/'receipt.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
 print(json.dumps({'state':record['state'],'receipt':str(out/'receipt.json')}));return 0
if __name__=='__main__':raise SystemExit(main())
