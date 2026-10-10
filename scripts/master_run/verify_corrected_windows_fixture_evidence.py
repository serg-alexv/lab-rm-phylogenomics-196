"""Independent C receipt-only verification; never queries/launches a process."""
from pathlib import Path
import hashlib, json, datetime

WORK = Path(__file__).resolve().parent
SPOOL = WORK / 'windows_owned_job_corrected_fixture_cae42dc3ab134bbd8eb725e2e445a957'
STOP = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196\.work\stage05_owned_closure_unproven.json')
EXPECTED_STOP = '3de7057780d280d5f204b535207a174e616ca425b5638fe9848a48cfca20838a'
PINS = {
    'receipt.json':'d3268cb12df98b462ac631f39f57a88c0cd9a15d86980e9741f14794f005efa2',
    'worker/result.json':'a6a56452eb165a2efb61336799955e58f93cc856b75a5852a6bfc713c26fe1b6',
}
SOURCE_PINS = {
    'verify_windows_owned_job_drain_fixture.py':'45c0da6f4eaf016bc215722dd3804eba7f63c9a2608d60d9bc8574742b24f81c',
    'stage5_unc_bind_probe.py':'0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d',
    'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(ok, message):
    if not ok: raise ValueError(message)

def check(records):
    receipt, launch, terminal, result = records
    require(receipt['state']=='PASS_NEW_BENIGN_RETAINED_ROOT_EXIT0_AND_EMPTY_JOB_ONLY', 'Outer state')
    require(receipt['scope']=='C_ONLY_NEW_PYTHON_PASS_JOB', 'Scope')
    for key in ('old_scope_closure_authority','original_STOP_or_lock_mutation','WSL_or_G_access'):
        require(receipt[key] is False, key)
    require(receipt['source_sha256']==SOURCE_PINS['verify_windows_owned_job_drain_fixture.py'], 'Fixture source')
    require(receipt['source_pins']=={k:v for k,v in SOURCE_PINS.items() if k!='verify_windows_owned_job_drain_fixture.py'}, 'Fixture dependencies')
    require(receipt['worker_result_sha256']==PINS['worker/result.json'], 'Outer result pin')
    python=r'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    for row in (launch, terminal, result):
        require(row['schema']=='STAGE05_OWNED_WINDOWS_IO_JOB_V2', 'Worker schema')
        require(row['argv']==[python,'-B','-c','pass'], 'Exact benign argv')
        require(row['source_sha256']==SOURCE_PINS['stage5_unc_bind_probe.py'], 'Worker source')
        require(row['api_sha256']==SOURCE_PINS['atomic_iqtree_windows.py'], 'API source')
        require(row['owner']==launch['owner'] and row['job_name']==launch['job_name'], 'Owner/job join')
        require(row['birth']==launch['birth'], 'Root birth join')
        require(row['created'] is True, 'Created root')
    owner=launch['owner']; birth=launch['birth']; final=result['exit']
    require(owner['pid']==4348 and owner['creation_filetime']==134360646915162736
            and owner['executable']==python and owner['session_id']==1 and owner['exited'] is False, 'Exact recorded owner')
    require(birth['pid']==8740 and birth['creation_filetime']==134360646916679609
            and birth['executable']==python and birth['session_id']==1 and birth['exited'] is False, 'Exact recorded root birth')
    require(launch['job_name']=='Local\\LAB_RM_STAGE5_IO_00610fdde71144fb8fd7b2061585fecb', 'Exact new named job')
    require(launch['assigned'] is False and launch['owned_closure_proven'] is False, 'Preassignment launch snapshot')
    require(terminal['assigned'] is True and terminal['exit']==final, 'Actual terminal join')
    for key in ('pid','creation_filetime','executable','session_id'):
        require(final[key]==birth[key], 'Retained root identity '+key)
    require(final['exited'] is True and final['exit_code']==0
            and final['exit_filetime']==134360646917457432
            and final['exit_filetime']>birth['creation_filetime'], 'Actual root exit0')
    require(result['state']=='PASS_EXACT_RETAINED_ROOT_EXIT0_AND_EMPTY_NAMED_JOB'
            and result['assigned'] is True and result['owned_closure_proven'] is True, 'Closed success')
    require(result['drain_samples'] and result['drain_samples'][-1]['root_wait']==0, 'Signalled retained root')
    empty=result['drain_samples'][-1]['job']
    require(empty==result['owned_job'] and empty['job_active_processes']==0 and empty['job_pids']==[], 'Exact empty complete named job')
    require(not any(k in result for k in ('original_error','closure_error','handle_close_errors','result_write_error')), 'No recorded failure')
    return {'recorded_owner_pid':owner['pid'],'recorded_owner_birth':owner['creation_filetime'],
            'recorded_root_pid':birth['pid'],'recorded_root_birth':birth['creation_filetime'],
            'recorded_root_exit_filetime':final['exit_filetime'],'recorded_root_exit_code':0,
            'named_job':launch['job_name'],'active_processes':0,'job_pids':[]}

def main():
    paths=[SPOOL/name for name in ('receipt.json','worker/launch.json','worker/root_exit.json','worker/result.json')]
    captured={str(p.relative_to(WORK)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths}
    for name, expected in PINS.items():require(sha(SPOOL/name)==expected, 'Actual supplied receipt hash '+name)
    for name, expected in SOURCE_PINS.items():require(sha(WORK/name)==expected, 'Actual implementation source '+name)
    require(sha(STOP)==EXPECTED_STOP, 'Original standard STOP changed/absent; no adoption')
    records=[json.loads(p.read_bytes()) for p in paths]
    facts=check(records)
    # Meaningful independent negative joins using copied in-memory receipts only.
    import copy
    for label,mutate in (
        ('root_birth_replacement',lambda rs:rs[-1]['exit'].__setitem__('creation_filetime',1)),
        ('root_exit_without_job_empty',lambda rs:rs[-1]['owned_job'].__setitem__('job_active_processes',1)),
    ):
        changed=copy.deepcopy(records);mutate(changed)
        try:check(changed)
        except ValueError:pass
        else:raise ValueError('Negative case accepted '+label)
    require(sha(STOP)==EXPECTED_STOP, 'STOP changed during read-only check')
    for path in paths:require(sha(path)==captured[str(path.relative_to(WORK))]['sha256'], 'Captured receipt changed')
    report={'schema':'MASTER_CORRECTED_WINDOWS_FIXTURE_INDEPENDENT_READBACK_V1',
        'state':'PASS_NEW_BENIGN_RETAINED_ROOT_EXIT0_AND_EMPTY_NAMED_JOB_ONLY',
        'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'publication_commit_supplied_by_root':'e4f0fd84932f9a414abfb7b1439ee21b97a1a571',
        'independent_source_sha256':sha(Path(__file__)), 'source_pins':SOURCE_PINS,
        'actual_files':captured, 'joins':facts,
        'original_standard_STOP_sha256_before_and_after':EXPECTED_STOP,
        'original_STOP_read_only':True,'negative_join_tests_passed':2,
        'old_scope_closure_proven':False,'scientific_acceptance':False,
        'limitations':['Receipt byte/semantic verification; no reconstruction of old DriveFS02 worker closure.',
            'No fresh process query, signal, WSL, G, lock or STOP mutation.',
            'Same STOP hash as the published prior status plus equal before/after reads; no claim of continuous file-handle observation since old failure.']}
    target=WORK/'windows_owned_job_corrected_fixture_independent_readback.json'
    with target.open('x',encoding='utf-8',newline='\n') as out:json.dump(report,out,indent=2);out.write('\n')
    print(json.dumps({'state':report['state'],'receipt':str(target),'sha256':sha(target),'bytes':target.stat().st_size}))

if __name__=='__main__':main()
