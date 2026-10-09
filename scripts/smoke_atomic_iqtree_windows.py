"""One <5second synthetic native lifecycle check; never uses biological inputs.

Default prints the exact proposed operation. --execute-synthetic-only explicitly
runs Windows cmd.exe /d /c exit0 with128MiB owned commit cap, mask5, original
workflow lock and the production lifecycle helper. No IQ-TREE invocation occurs.
"""
import argparse
import ctypes
import json
from pathlib import Path
import sys

import atomic_iqtree_windows as runner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--execute-synthetic-only',action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    argv = [r'C:\Windows\System32\cmd.exe','/d','/c','exit','0']
    proposal = {'operation':'SHORT_SYNTHETIC_NATIVE_LIFECYCLE_ONLY','scientific_jobs':0,'argv':argv,
                'output':str(output),'cap_bytes':128*1024**2,'affinity_mask':5,'runtime_seconds':5,
                'tests':'Suspended creation, queried job controls, handle birth/image/session, real exit, empty job, OS unlock'}
    if not args.execute_synthetic_only:
        print(json.dumps(proposal)); return 0
    runner.require(output.is_absolute() and output.drive.lower() == 'c:' and not output.exists(), 'New local C synthetic output required')
    api = runner.Win()
    expected_sizes = {'BASIC':64,'EXTENDED':144,'STARTUP':104,'PROCESS':24,'ACCOUNTING':48,'MEMORY':80,'PERF':104,'FILEINFO':52}
    actual_sizes = {name:ctypes.sizeof(getattr(api,name)) for name in expected_sizes}
    runner.require(actual_sizes == expected_sizes,'Actual Windows64 ctypes layout differs')
    output.mkdir(parents=True,exist_ok=False)
    runner.atomic(output/'proposal.json',proposal)
    cfg = {'budget':{'cap_bytes':128*1024**2,'reserve_bytes':0},'runtime_seconds':5,
           '_config_sha256':runner.sha256(output/'proposal.json'),'alignment':{'path':str(Path(__file__).resolve())}}
    lock = runner.WorkflowLock(api)
    try:
        with lock:
            result = runner.run_native(cfg,api,output,argv,
                {'scope':'SYNTHETIC_ONLY_NO_BIOLOGICAL_AUTHORITY_USED'},lock.identity)
            runner.require(result['native']['exit_code'] == 0 and result['native']['exited'] and
                           result['native']['exit_filetime'] > result['native']['creation_filetime'] and
                           result['job_active_processes'] == 0 and result['job_pids'] == [],
                           'Synthetic actual terminal/job proof differs')
        power = runner.read_json(output/'execution_state_restored.json')
        runner.require(lock.released and power['actual_api_success'],'Actual unlock/transient-power release missing')
        receipt = {'utc':runner.utc(),'status':'PASS_SHORT_SYNTHETIC_NATIVE_LIFECYCLE','scientific_jobs':0,
                   'argv':argv,'ctypes_sizes':actual_sizes,'native_exit_sha256':runner.sha256(output/'exit.json'),
                   'runner_sha256':runner.sha256(runner.__file__),'workflow_lock_released':lock.released,
                   'power_request_restored':True,'elapsed_seconds':result['elapsed_seconds']}
        runner.atomic(output/'synthetic_validation.json',receipt)
        print(json.dumps(receipt)); return 0
    finally:
        if lock.released:
            runner.atomic(output/'lock_released.json',{'utc':runner.utc(),'state':'EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'})


if __name__ == '__main__':
    sys.exit(main())
