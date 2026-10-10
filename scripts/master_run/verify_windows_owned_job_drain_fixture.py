"""Default-noop C-only benign fixture of the corrected Windows I/O worker.

Root may explicitly execute after source publication. Never queries WSL/G,
project lock/STOP or original process scopes. Only a new Python `pass` job.
"""
from pathlib import Path
import argparse, hashlib, importlib, json, os, sys, uuid

WORK=Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PYTHON=Path(r'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
      'stage5_unc_bind_probe.py':'0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if not args.run:print(json.dumps({'state':'PREPARED_NOT_RUN','actual_Windows_workers':0}));return 0
    assert os.name=='nt' and Path(__file__).resolve().parent==WORK and Path(sys.executable)==PYTHON
    for name,expected in PINS.items():assert hashlib.sha256((WORK/name).read_bytes()).hexdigest()==expected
    A=importlib.import_module('atomic_iqtree_windows');U=importlib.import_module('stage5_unc_bind_probe')
    assert Path(A.__file__).resolve()==WORK/'atomic_iqtree_windows.py' and Path(U.__file__).resolve()==WORK/'stage5_unc_bind_probe.py'
    api=A.Win();out=WORK/('windows_owned_job_corrected_fixture_'+uuid.uuid4().hex);out.mkdir()
    record={'schema':'MASTER_BENIGN_WINDOWS_OWNED_JOB_FIXTURE_V1','state':'FAILED','source_sha256':A.sha256(__file__),
        'source_pins':PINS,'scope':'C_ONLY_NEW_PYTHON_PASS_JOB','old_scope_closure_authority':False,
        'original_STOP_or_lock_mutation':False,'WSL_or_G_access':False,'before':api.resources([WORK])}
    try:
        owner=api.identity(api.current(),os.getpid())
        result=U.windows_job(api,[sys.executable,'-B','-c','pass'],owner,out/'worker')
        assert result['owned_closure_proven'] is True and result['owned_job']['job_active_processes']==0 and result['owned_job']['job_pids']==[]
        record.update(state='PASS_NEW_BENIGN_RETAINED_ROOT_EXIT0_AND_EMPTY_JOB_ONLY',worker_result_sha256=A.sha256(out/'worker/result.json'))
    except BaseException as error:record['error']={'kind':type(error).__name__,'message':str(error)}
    finally:
        record['after']=api.resources([WORK]);A.atomic(out/'receipt.json',record)
    print(json.dumps({'state':record['state'],'receipt':str(out/'receipt.json'),'sha256':A.sha256(out/'receipt.json')}))
    return 0 if record['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
