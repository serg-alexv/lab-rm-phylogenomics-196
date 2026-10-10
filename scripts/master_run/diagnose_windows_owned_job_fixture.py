"""One benign C-only Python exit0; retained Win32 job query diagnostics.

No WSL/G/project/native-science/app cleanup. Exact A80 API remains unchanged.
"""
from pathlib import Path
import ctypes, hashlib, importlib.util, json, os, subprocess, sys, time, uuid

W=Path(__file__).resolve().parent
P=W/'atomic_iqtree_windows.py'
assert hashlib.sha256(P.read_bytes()).hexdigest()=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
spec=importlib.util.spec_from_file_location('owned_fixture_api',P);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)

def main():
    assert os.name=='nt'
    out=W/('windows_owned_job_diagnosis_'+uuid.uuid4().hex);out.mkdir()
    api=A.Win();name='Local\\LAB_RM_DIAGNOSTIC_'+uuid.uuid4().hex
    job=api.create_job(None,name);api.ok(job,'Create benign diagnostic job')
    proc=api.PROCESS();created=False
    record={'scope':'C_ONLY_BENIGN_OWNED_WINDOWS_PYTHON_EXIT0','named_job':name,'source_sha256':A.sha256(__file__),'api_sha256':A.sha256(P),'queries':[]}
    try:
        limits=api.EXTENDED();limits.BasicLimitInformation.LimitFlags=0x2000|0x8;limits.BasicLimitInformation.ActiveProcessLimit=1
        api.ok(api.set_job(job,9,ctypes.byref(limits),ctypes.sizeof(limits)),'Configure benign job')
        startup=api.STARTUP();startup.cb=ctypes.sizeof(startup)
        argv=[sys.executable,'-B','-c','pass'];cmd=ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        api.ok(api.create(sys.executable,cmd,None,None,False,0x4|0x08000000,None,str(W),ctypes.byref(startup),ctypes.byref(proc)),'Create benign suspended Python')
        created=True;birth=api.identity(proc.hProcess,proc.dwProcessId);record['birth']=birth;record['argv']=argv
        api.ok(api.assign(job,proc.hProcess),'Assign exact benign child');assert api.resume(proc.hThread)!=0xffffffff
        assert api.wait(proc.hProcess,5000)==0
        record['terminal']=api.identity(proc.hProcess,proc.dwProcessId,birth['executable'],birth['session_id'])
        for sample in range(4):
            row={'sample':sample,'raw_queries':[]}
            for kind,klass in [(9,api.EXTENDED),(1,api.ACCOUNTING),(3,api.PIDS)]:
                obj=klass();ctypes.set_last_error(0)
                okay=api.query_job(job,kind,ctypes.byref(obj),ctypes.sizeof(obj),None)
                item={'class':kind,'okay':bool(okay),'winerror':ctypes.get_last_error(),'size':ctypes.sizeof(obj)}
                if kind==3:item.update(assigned=obj.assigned,listed=obj.listed,pids=list(obj.ids[:min(obj.listed,64)]))
                if kind==1:item.update(active=obj.ActiveProcesses,total=obj.TotalProcesses)
                row['raw_queries'].append(item)
            try:row['A_job_state']=api.job_state(job)
            except BaseException as error:row['A_job_state_error']={'kind':type(error).__name__,'message':str(error),'winerror':getattr(error,'winerror',None)}
            record['queries'].append(row);time.sleep(.025)
        record['state']='RECORDED_ACTUAL_BENIGN_WINDOWS_JOB_QUERIES'
    finally:
        if created:
            if api.wait(proc.hProcess,0)!=0:api.terminate_job(job,2);api.wait(proc.hProcess,5000)
            record['final_root_wait']=api.wait(proc.hProcess,0)
            api.close(proc.hThread);api.close(proc.hProcess)
        api.close(job);A.atomic(out/'receipt.json',record)
    print(json.dumps({'receipt':str(out/'receipt.json'),'sha256':A.sha256(out/'receipt.json')}))

if __name__=='__main__':main()
