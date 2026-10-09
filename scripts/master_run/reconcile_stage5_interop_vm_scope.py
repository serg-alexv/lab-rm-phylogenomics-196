"""One authorized WSL shutdown closes a failed interop scope; no config edit.

Default is a no-op. Does not reconstruct the previous lost retained terminal.
No inference, installation, payload deletion, unrelated Windows app signalling,
or resource-reserve weakening. Only Ubuntu WSL2 may be registered.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,stat,subprocess,time,uuid
W=Path(__file__).resolve().parent
EXACT=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
CONFIG=Path(r'C:\Users\wheel\.wslconfig')
WSL=r'C:\Windows\System32\wsl.exe'
API_SHA='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
CONFIG_SHA='31b59c84adf6bf7b0fdf0cd42ee6298cd9dc7c20032ab30d97c3f22dbb3b6982'
PRIOR=W/'stage5_interop_actual_postiq_02'
PINS={'INTEROP_UNPROVEN_STOP.json':'bc5a55a954a1ff84734c123f6e42eeabd4a014fca73461da251062eec86c28b6',
 'result.json':'9b39819272890796054dd12dfde2985b8510b1978b99d1143a3683a260a42ef3',
 'lock_released.json':'0becb7e52d3c18a82d442c9cc79a4467ca14a26bd28a6a752481c6f6144dc78e',
 'exit0/linux/terminal.json':'25ca0a7f7c5162895e10e3a9504ae59c037172273a7858656eb66972a962b29e'}

def need(ok,message):
 if not ok:raise ValueError(message)

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def absent(p):
 try:p.lstat()
 except FileNotFoundError:return True
 return False

def plain(p):
 s=p.lstat();need(stat.S_ISREG(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Plain exact control required')

def registered_text(raw,stopped=False):
 text=raw.decode('utf-16-le').lstrip('\ufeff')
 rows=[x.strip().lstrip('*').strip() for x in text.splitlines() if x.strip()]
 need(len(rows)==2 and re.fullmatch(r'Ubuntu\s+'+('Stopped' if stopped else '(Running|Stopped)')+r'\s+2',rows[1]),
      'Only exact registered Ubuntu WSL2 scope allowed')
 return text

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true');p.add_argument('--expected-source-sha256');a=p.parse_args()
 if not a.run:print(json.dumps({'state':'PREPARED_NOT_RUN','shutdowns':0,'config_edits':0,'stop_removals':0}));return 0
 need(os.name=='nt' and W==EXACT and re.fullmatch('[a-f0-9]{64}',a.expected_source_sha256 or '') and sha(__file__)==a.expected_source_sha256,'Exact reviewed Windows source required')
 need(sha(W/'atomic_iqtree_windows.py')==API_SHA,'Original lock/API source differs')
 spec=importlib.util.spec_from_file_location('interop_vm_original_api',W/'atomic_iqtree_windows.py')
 A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
 api=A.Win();lock=A.WorkflowLock(api);owner=api.identity(api.current(),os.getpid())
 out=W/('stage5_interop_vm_scope_'+uuid.uuid4().hex);out.mkdir();global_stop=A.ORIGINAL_LOCK.with_name('stage05_owned_closure_unproven.json')
 record={'schema':'STAGE05_AUTHORIZED_INTEROP_VM_SCOPE_CLOSURE_V1','state':'FAILED_PRESERVED','utc':A.utc(),
  'source_sha256':a.expected_source_sha256,'prior_pins':PINS,'commands':[],'config_edits':0,'payload_deletions':0,
  'host_reboots':0,'scientific_launches':0,'old_retained_client_terminal':'NOT_RECONSTRUCTED',
  'authority':'Direct user authorized entire WSL reconfiguration if needed; exact shutdown closes this failed prelaunch interop scope.'}
 def command(args,stem):
  argv=[WSL,*args];row={'argv':argv};record['commands'].append(row);child=None;birth=None
  try:
   with (out/(stem+'.stdout.txt')).open('xb') as stdout,(out/(stem+'.stderr.txt')).open('xb') as stderr:
    child=subprocess.Popen(argv,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
    birth=api.identity(int(child._handle),child.pid,WSL,owner['session_id']);row['retained_birth']=birth
    child.wait(timeout=30)
    terminal=api.identity(int(child._handle),child.pid,WSL,owner['session_id']);row['retained_terminal']=terminal
    need(terminal['pid']==birth['pid'] and terminal['creation_filetime']==birth['creation_filetime']
     and terminal['executable']==birth['executable']==WSL and terminal['session_id']==birth['session_id']
     and terminal['exited'] and terminal['exit_filetime']>terminal['creation_filetime'],'Retained WSL command closure required')
    row['retained_closure_proven']=True;need(terminal['exit_code']==0,'Actual WSL command nonzero')
   need((out/(stem+'.stdout.txt')).stat().st_size<1024**2 and (out/(stem+'.stderr.txt')).stat().st_size<1024**2,'Bounded WSL logs exceeded')
   return (out/(stem+'.stdout.txt')).read_bytes()
  finally:
   if child is not None:
    if not row.get('retained_closure_proven') and birth is not None and child.poll() is not None:
     terminal=api.identity(int(child._handle),child.pid,WSL,owner['session_id']);row['terminal_after_error']=terminal
     row['retained_closure_proven']=bool(terminal['exited'] and terminal['pid']==birth['pid'] and terminal['creation_filetime']==birth['creation_filetime'] and terminal['exit_filetime']>terminal['creation_filetime'])
    if row.get('retained_closure_proven'):child._handle.Close()
   for kind in ('stdout','stderr'):
    q=out/(stem+'.'+kind+'.txt')
    if q.is_file():row[kind+'_sha256']=sha(q)
 try:
  with lock as held:
   record['workflow_lock']=held.identity;need(absent(global_stop),'Existing standard closure stop vetoes this exact reconciliation')
   plain(CONFIG);need(sha(CONFIG)==CONFIG_SHA,'Existing4GiB config changed; no edits permitted')
   for name,pin in PINS.items():plain(PRIOR/name);need(sha(PRIOR/name)==pin,'Actual prior interop evidence changed')
   control=A.read_json(ROOT/'status/run_control.json');need(control['state']=='ACTIVE_DIRECT_USER_CONTINUATION' and control['automatic_resume'] is False,'Current direct continuation authority absent')
   result=A.read_json(PRIOR/'result.json');terminal=A.read_json(PRIOR/'exit0/linux/terminal.json')
   need(result['state']=='FAILED_NONSCIENTIFIC_INTEROP' and terminal['state']=='FAILED_NONSCIENTIFIC_FIXTURE'
    and terminal['error']=='Fatal: Kernel-backed pidfd process signalling is required'
    and set(terminal['files'])=={'initial_actual_windows_lease.json'},'Exact prior capability failure differs')
   need(A.read_json(PRIOR/'lock_released.json')['released'] is True,'Prior original lock release missing')
   resources=api.resources([out]);record['admission']=resources
   need(resources['physical_available_bytes']>=1536*1024**2 and resources['commit_headroom_bytes']>=1536*1024**2,'Keep1.5GiB physical and commit reserve')
   original=(PRIOR/'INTEROP_UNPROVEN_STOP.json').read_bytes();backup=out/'original_interop_stop.json'
   with backup.open('xb') as f:f.write(original);f.flush();os.fsync(f.fileno())
   need(sha(backup)==PINS['INTEROP_UNPROVEN_STOP.json'],'Preserved exact stop backup differs')
   record['registered_before']=registered_text(command(['--list','--verbose'],'registered_before'))
   command(['--shutdown'],'authorized_shutdown');record['actual_shutdowns']=1
   record['registered_stopped01']=registered_text(command(['--list','--verbose'],'registered_stopped01'),True)
   record['registered_stopped02']=registered_text(command(['--list','--verbose'],'registered_stopped02'),True)
   need(sha(CONFIG)==CONFIG_SHA and all(sha(PRIOR/n)==pin for n,pin in PINS.items())
    and absent(global_stop) and sha(__file__)==a.expected_source_sha256,'Controls changed during owned shutdown')
   record['windows_after']=api.resources([out]);record['aggregate_ubuntu_scope_closed']=True
   # Only this exact local failure marker; every failed receipt remains intact.
   (PRIOR/'INTEROP_UNPROVEN_STOP.json').unlink()
   record.update(state='PASS_AUTHORIZED_VM_SHUTDOWN_INTEROP_SCOPE_CLOSED_CONFIG_UNCHANGED',owned_local_stop_removed=absent(PRIOR/'INTEROP_UNPROVEN_STOP.json'),config_sha256=sha(CONFIG))
 except BaseException as error:
  record.update(state='FAILED_PRESERVED',error_kind=type(error).__name__,error_message=str(error))
 finally:
  record['original_lock_explicitly_released']=lock.released
  record['all_created_retained_clients_closed']=all(x.get('retained_closure_proven') is True for x in record['commands'])
  A.atomic(out/'receipt.json',record)
 print(json.dumps({'state':record['state'],'receipt':str(out/'receipt.json'),'sha256':sha(out/'receipt.json')}))
 return 0 if record['state'].startswith('PASS_') and lock.released else 2

if __name__=='__main__':raise SystemExit(main())
