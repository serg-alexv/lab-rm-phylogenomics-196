"""Invoke the existing independent checker under the original lock after actual closure."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,subprocess

WORK=Path(__file__).resolve().parent
ATTEMPT=WORK/'iqtree_attempts/partitioned_20261009T162904Z'
ROOT=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
      'independent_tree_check.py':'eda8d80824fb5be11e7f7366dfd8af90e7cdbd99bf9508e384c194ed95acaa3c',
      'stage04_partitioned_config.json':'c70b267b04f9fa9c19a2bf0671deabcfd0959545d90a48a912ea463e220be314'}
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true');a=p.parse_args()
    for name,pin in PINS.items():assert sha(WORK/name)==pin,name
    if not a.run:
        print(json.dumps({'state':'PREPARED_NO_VALIDATION','requires':'Actual root-observed controller session terminal plus exact native/job/unlock/power receipts'}));return 0
    result=load(ATTEMPT/'result.json');closed=load(ATTEMPT/'exit.json')
    launch=load(ATTEMPT/'launch.json');unlock=load(ATTEMPT/'lock_released.json')
    power=load(ATTEMPT/'execution_state_restored.json')
    assert result['state']==closed['state']=='VALIDATION_REQUIRED'
    assert closed['native']['exited'] is True and closed['native']['exit_code']==0
    assert closed['native']['pid']==launch['native']['pid']==4768
    assert closed['native']['creation_filetime']==launch['native']['creation_filetime']==134360369876207076
    assert closed['native']['exit_filetime']>closed['native']['creation_filetime']
    assert closed['job_active_processes']==0 and closed['job_pids']==[]
    assert unlock['state']=='EXPLICIT_OS_BYTE_UNLOCK_COMPLETED'
    assert power['actual_api_success'] is True and power['requested_flags']==0x80000000
    out=WORK/'stage04_acceptance_actual01';out.mkdir(exist_ok=False)
    cfg=load(WORK/'stage04_partitioned_config.json')
    argv=[str(HISTORY/'.tools/validation_env/Scripts/python.exe'),'-B',str(WORK/'independent_tree_check.py'),
          '--attempt',str(ATTEMPT),'--approved',cfg['approved_accessions']['path'],
          '--config-source',str(WORK/'stage04_partitioned_config.json'),
          '--report',str(out/'independent_validation.json'),
          '--freeze',str(ROOT/'.work/stage04_primary196_atomic_20261009')]
    spec=importlib.util.spec_from_file_location('unchanged_atomic_lock_only',WORK/'atomic_iqtree_windows.py')
    A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':sha(Path(__file__)),
            'state':'INDEPENDENT_CHECK_REQUIRED','argv':argv,'closure_files':{name:sha(ATTEMPT/name) for name in
                ('result.json','exit.json','launch.json','lock_released.json','execution_state_restored.json')}}
    lock=A.WorkflowLock(A.Win())
    try:
        with lock as owned:
            record['original_lock_identity']=owned.identity
            child=subprocess.run(argv,capture_output=True,timeout=600,check=False)
            (out/'stdout.txt').write_bytes(child.stdout);(out/'stderr.txt').write_bytes(child.stderr)
            record['checker_exit_code']=child.returncode
            record['state']='CHECKER_EXIT0_REVIEW_CERTIFICATE' if child.returncode==0 else 'CHECKER_FAILED_PRESERVED_NO_RETRY'
            return child.returncode
    except BaseException as error:
        record.update(state='CHECKER_FAILED_PRESERVED_NO_RETRY',error_kind=type(error).__name__,error_message=str(error))
        if isinstance(error,subprocess.TimeoutExpired):
            (out/'stdout.txt').write_bytes(error.output or b'')
            (out/'stderr.txt').write_bytes(error.stderr or b'')
        raise
    finally:
        record['original_lock_explicitly_released']=lock.released
        (out/'driver_receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':raise SystemExit(main())
