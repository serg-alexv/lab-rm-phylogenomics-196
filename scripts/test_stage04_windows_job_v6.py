"""Actual Windows API controls and pinned IQ-TREE version, no biological job."""
from pathlib import Path
import json, sys, time
import stage04_controller as C
import stage04_windows_job_v6 as J
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/stage04/native_windows_v6_review'
EXE=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.tools\iqtree_windows_3_1_4\extracted\iqtree-3.1.4-Windows\bin\iqtree3.exe')

def main():
    stamp=C.now().replace(':','').replace('+','_');target=OUT/stamp
    version=J.run_job([str(EXE),'--version'],ROOT,target/'official_version',128*1024**2)
    C.check(version['exit_code']==0 and 'IQ-TREE version 3.1.4 for Windows 64-bit' in (target/'official_version/stdout.txt').read_text(),'Actual pinned native version failed')
    fixture=target/'allocation_fixture.py';fixture.write_text('import ctypes, json\nfrom ctypes import wintypes\nk=ctypes.WinDLL("kernel32",use_last_error=True)\nk.GetCurrentProcess.restype=wintypes.HANDLE\nk.GetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]\na,b=ctypes.c_size_t(),ctypes.c_size_t()\nassert k.GetProcessAffinityMask(k.GetCurrentProcess(),ctypes.byref(a),ctypes.byref(b))\nassert a.value.bit_count()==2\ntry:\n x=bytearray(512*1024**2)\nexcept MemoryError:\n print(json.dumps({"actual_affinity_mask":a.value,"denied_allocation_bytes":512*1024**2}));raise SystemExit(0)\nraise SystemExit(99)\n',encoding='utf-8')
    limited=J.run_job([sys.executable,str(fixture)],ROOT,target/'allocation_denial',64*1024**2)
    actual=json.loads((target/'allocation_denial/stdout.txt').read_text())
    C.check(limited['exit_code']==0 and actual['actual_affinity_mask']==limited['affinity_mask'] and actual['denied_allocation_bytes']>limited['aggregate_job_committed_memory_cap_bytes'] and limited['peak_job_committed_bytes']<=64*1024**2,'Actual memory denial/affinity proof failed')
    receipt={'status':'PASS_ACTUAL_WINDOWS_JOB_ASSIGN_BEFORE_RESUME_QUERYBACK_MEMORY_DENIAL_AND_AFFINITY',
             'utc':C.now(),'helper_sha256':C.digest(ROOT/'scripts/stage04_windows_job_v6.py'),'test_source_sha256':C.digest(__file__),
             'official_version':version,'allocation_denial':limited,'fixtures':2,'biological_jobs_run':0,
             'fixture_source':fixture.relative_to(ROOT).as_posix(),'native_functional_scope':'Windows API control validation only; no scientific outputs'}
    C.atomic(OUT/'review.json',receipt);print(receipt['status'],flush=True)

if __name__=='__main__':main()
