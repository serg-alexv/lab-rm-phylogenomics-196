"""Read-only retained-handle audit of the one existing IQ-TREE controller."""
from pathlib import Path
from ctypes import wintypes as W
import argparse,datetime,hashlib,importlib.util,json,time
WORK=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true');args=p.parse_args()
 if not args.run:print('{"state":"PREPARED_QUERY_ONLY_NOT_RUN"}');return 0
 source=WORK/'atomic_iqtree_windows.py'
 assert hashlib.sha256(source.read_bytes()).hexdigest()=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
 spec=importlib.util.spec_from_file_location('unchanged_process_queries_only',source)
 A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);api=A.Win()
 api.K.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];api.K.OpenProcess.restype=W.HANDLE
 handle=api.K.OpenProcess(0x1000|0x100000,False,27048);assert handle
 out=WORK/'iqtree_controller_closure_actual01';out.mkdir(exist_ok=False)
 record={'schema':'MASTER_IQTREE_CONTROLLER_RETAINED_EXIT_V1','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'state':'RETAINED_CONTROLLER_LIVE','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'process_signals_sent':0,'locks_or_jobs_opened':0,'native_or_wsl_launches':0,'maximum_wait_seconds':1800}
 try:
  birth=api.identity(handle,27048)
  assert birth['creation_filetime']==134360369803845506 and not birth['exited']
  assert Path(birth['executable'])==Path(r'C:\Users\wheel\AppData\Local\Python\pythoncore-3.14-64\python.exe')
  record['retained_live_identity']=birth
  (out/'retained_live.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
  began=time.monotonic()
  while time.monotonic()-began<1800:
   state=api.wait(handle,10000);assert state in (0,258)
   if state==0:
    ended=api.identity(handle,27048,birth['executable'],birth['session_id'])
    assert ended['creation_filetime']==birth['creation_filetime'] and ended['exited'] and ended['exit_filetime']>birth['creation_filetime']
    record.update(terminal=ended,state='PASS_CONTROLLER_RETAINED_HANDLE_EXIT0' if ended['exit_code']==0 else 'FAILED_CONTROLLER_ACTUAL_NONZERO_EXIT')
    return 0 if ended['exit_code']==0 else 2
  record['state']='WAIT_EXPIRED_NO_CONTROLLER_CLOSURE_CLAIM';return 3
 except BaseException as error:
  record.update(state='FAILED_QUERY_AUDIT_NO_CLOSURE_CLAIM',error_kind=type(error).__name__,error_message=str(error));raise
 finally:
  api.close(handle);record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  (out/'receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':raise SystemExit(main())
