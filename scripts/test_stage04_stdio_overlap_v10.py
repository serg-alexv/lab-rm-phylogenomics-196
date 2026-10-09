"""Two simultaneous synthetic spawn preparations; probe foreign exact file handles."""
import argparse, ctypes as c, json, os, threading, uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_windows_job_v10 as J

def file_identity(handle):
    info=S.FILEINFO()
    if not S.file_info(handle,c.byref(info)):return None
    return {'volume':info.volume,'file_index':(info.indexHigh<<32)|info.indexLow}

def child(directory,branch):
    pair=C.load(directory/'prepared_handles.json');other='b' if branch=='a' else 'a';probes=[]
    for item in pair[other]:
        actual=file_identity(item['handle']);probes.append({'foreign_handle':item['handle'],'expected_foreign_file':item['identity'],'actual_child_object':actual})
        C.check(actual!=item['identity'],'Foreign thread stdout/stderr was inherited by this synthetic child')
    C.atomic(directory/(branch+'_probe.json'),{'utc':C.now(),'status':'NO_FOREIGN_STDIO_FILE_OBJECT_INHERITED','pid':os.getpid(),'probes':probes})

def main():
    p=argparse.ArgumentParser();p.add_argument('--child',choices=['a','b']);p.add_argument('--directory');a=p.parse_args()
    if a.child:return child(Path(a.directory),a.child)
    with C.WorkflowLock(S.LOCK) as lock:
        S.held_lock_matches_negative(lock)
        directory=S.RUNTIME/'stdio_overlap'/uuid.uuid4().hex;directory.mkdir(parents=True,exist_ok=False)
        ready=threading.Barrier(2);prepared={};mutex=threading.Lock()
        def task(branch):
            def callback(handles):
                entries=[{'handle':h,'identity':file_identity(h)} for h in handles[1:]]
                C.check(all(x['identity'] is not None for x in entries),'Parent stdout file identities not queryable')
                C.check(all(not os.get_handle_inheritable(h) for h in handles),'Prepared stdio must start non-inheritable')
                with mutex:
                    prepared[branch]=entries
                    if len(prepared)==2:C.atomic(directory/'prepared_handles.json',prepared)
                ready.wait(timeout=10)
            return J.run_job([str(S.PYTHON),str(Path(__file__).resolve()),'--child',branch,'--directory',str(directory)],S.ROOT,
              directory/branch,cap_bytes=128*1024**2,deadline_seconds=20,role='SYNTHETIC_STDIO_OVERLAP',fixture_stdio_barrier=callback)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(task,x) for x in ('a','b')];results=[f.result() for f in futures]
        C.check(all(r['exit_code']==0 and r['job_active_processes']==0 and r['actual_job_process_ids']==[] for r in results),'Concurrent fixture ordinary exit/empty jobs failed')
        C.atomic(S.REPORT/'stdio_overlap_fixture.json',{'utc':C.now(),'status':'PASS_OVERLAPPING_PREPARATION_SERIALIZED_INHERITANCE_NO_FOREIGN_STDIO',
          'biological_jobs':0,'runtime':str(directory),'helper_sha256':C.digest(S.ROOT/'scripts/stage04_windows_job_v10.py'),
          'source_sha256':C.digest(__file__),'actual_jobs':results,'child_probes':{x:C.load(directory/(x+'_probe.json')) for x in ('a','b')},
          'prepared_handle_objects_sha256':C.digest(directory/'prepared_handles.json')})
        print('PASS_OVERLAPPING_PREPARATION_SERIALIZED_INHERITANCE_NO_FOREIGN_STDIO')

if __name__=='__main__':main()
