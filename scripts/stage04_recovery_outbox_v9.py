"""Optional bounded progress outbox. No synchronous native Git/G I/O callback.

One daemon worker, one-slot in-memory queue, one bounded contained publisher at
a time. G/Git/report exceptions are recorded on C and cannot reach native wait.
Stopping this worker does not own or close the native JobObject.
"""
import json, queue, threading, time
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v9 as S
import stage04_windows_job_v9 as J

class Outbox:
    def __init__(self,runtime,scope,fixture=False):
        self.runtime=Path(runtime);self.scope=scope;self.fixture=fixture;self.queue=queue.Queue(maxsize=1)
        self.stop=threading.Event();self.thread=threading.Thread(target=self.work,daemon=True);self.drops=0
    def __enter__(self):self.thread.start();return self
    def offer(self,row):
        try:self.queue.put_nowait(dict(row))
        except queue.Full:self.drops+=1
    def work(self):
        index=0;next_publish=0
        while not self.stop.is_set() or not self.queue.empty():
            try:row=self.queue.get(timeout=.3)
            except queue.Empty:continue
            try:
                C.atomic(self.runtime/'outbox_latest.json',{'scope':self.scope,'measurement':row,'dropped_measurements':self.drops})
                if time.monotonic()<next_publish:continue
                index+=1
                argv=[str(S.PYTHON),str(S.ROOT/'scripts/stage04_recovery_publisher_v9.py'),'--runtime',str(self.runtime),'--scope',self.scope]
                if self.fixture:argv+=['--fixture-fail']
                result=J.run_job(argv,S.ROOT,self.runtime/'publishers'/('attempt_'+str(index).zfill(4)),
                  cap_bytes=256*1024**2,deadline_seconds=90,role='BOUNDED_PROGRESS_PUBLISHER')
                C.atomic(self.runtime/'outbox_publication_latest.json',{'utc':C.now(),'publisher_exit_code':result['exit_code'],
                  'actual_empty_publisher_job':result['job_active_processes']==0 and result['actual_job_process_ids']==[],
                  'fixture_injected_failure':self.fixture,'native_lifecycle_affected':False})
                next_publish=time.monotonic()+300
            except Exception as error:
                J.best_effort(self.runtime/'outbox_error.json',{'utc':C.now(),'kind':type(error).__name__,'message':str(error),
                  'effect':'OPTIONAL_PROGRESS_PUBLICATION_FAILED_NATIVE_MONITOR_CONTINUES'})
                next_publish=time.monotonic()+300
    def __exit__(self,*args):
        self.stop.set();self.thread.join(timeout=95)
        C.check(not self.thread.is_alive(),'Bounded publisher worker did not close; no next scope')
