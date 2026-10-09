"""Optional outbox with immutable observations and exact remote acknowledgements."""
import json, queue, threading, time, uuid
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S
import stage04_windows_job_v10 as J

def publish_observation(runtime,scope,row,fixture=False,terminal=False):
    runtime=Path(runtime);token=uuid.uuid4().hex;path=runtime/'observations'/(token+'.json')
    C.atomic(path,{'schema':'V10_IMMUTABLE_NATIVE_OBSERVATION','scope':scope,'terminal':terminal,'measurement':row})
    sha=C.digest(path)
    argv=[str(S.PYTHON),str(S.ROOT/'scripts/stage04_recovery_publisher_v10.py'),'--runtime',str(runtime),'--scope',scope,
      '--observation',str(path),'--observation-sha256',sha]
    if fixture:argv+=['--fixture-fail']
    result=J.run_job(argv,S.ROOT,runtime/'publishers'/token,cap_bytes=256*1024**2,deadline_seconds=90,role='BOUNDED_PROGRESS_PUBLISHER')
    ack_path=runtime/'publication_acknowledgements'/(sha+'.json')
    if result['exit_code']==0:
        ack=C.load(ack_path)
        C.check(ack['status']=='REMOTE_MAIN_BYTES_VERIFIED' and ack['observation_sha256']==sha,'Exact remote observation acknowledgement missing')
    else:
        ack={'utc':C.now(),'status':'PUBLICATION_UNVERIFIED_FAILED','observation_sha256':sha,'publisher_exit_code':result['exit_code'],
          'remote_bytes_verified':False,'native_lifecycle_affected':False}
        C.atomic(ack_path,ack)
    record={**ack,'actual_empty_publisher_job':result['job_active_processes']==0 and result['actual_job_process_ids']==[],
      'fixture_injected_failure':fixture,'terminal':terminal,'observation_path':str(path)}
    C.atomic(runtime/('terminal_publication.json' if terminal else 'last_publication_attempt.json'),record);return record

def terminal_publication(runtime,scope,receipt,fixture=False):
    try:return publish_observation(runtime,scope,receipt,fixture,terminal=True)
    except Exception as error:
        J.best_effort(Path(runtime)/'terminal_publication_failure.json',{'utc':C.now(),'status':'PUBLICATION_UNVERIFIED_FAILED',
          'kind':type(error).__name__,'message':str(error),'actual_native_exit_code':receipt['exit_code'],
          'native_lifecycle_affected':False,'effect':'MANDATORY_NATIVE_C_RECEIPT_PRESERVED_OPTIONAL_REMOTE_TERMINAL_STATE_UNVERIFIED'})

class Outbox:
    def __init__(self,runtime,scope,fixture=False):
        self.runtime=Path(runtime);self.scope=scope;self.fixture=fixture;self.queue=queue.Queue(maxsize=1)
        self.stop=threading.Event();self.thread=threading.Thread(target=self.work,daemon=True);self.drops=0
    def __enter__(self):self.thread.start();return self
    def offer(self,row):
        try:self.queue.put_nowait(dict(row))
        except queue.Full:self.drops+=1
    def work(self):
        next_publish=0
        while not self.stop.is_set() or not self.queue.empty():
            try:row=self.queue.get(timeout=.3)
            except queue.Empty:continue
            try:
                C.atomic(self.runtime/'outbox_latest_observed.json',{'scope':self.scope,'measurement':row,'dropped_measurements':self.drops})
                if time.monotonic()>=next_publish:
                    publish_observation(self.runtime,self.scope,row,self.fixture);next_publish=time.monotonic()+300
            except Exception as error:
                J.best_effort(self.runtime/'outbox_error.json',{'utc':C.now(),'kind':type(error).__name__,'message':str(error),
                  'effect':'OPTIONAL_PROGRESS_PUBLICATION_FAILED_NATIVE_MONITOR_CONTINUES'})
                next_publish=time.monotonic()+300
    def __exit__(self,*args):
        self.stop.set();self.thread.join(timeout=95)
        C.check(not self.thread.is_alive(),'Bounded publisher worker did not close; no next scope')
