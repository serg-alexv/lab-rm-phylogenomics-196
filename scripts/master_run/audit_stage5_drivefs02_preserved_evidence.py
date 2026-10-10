"""C-only readback of preserved DriveFS02 evidence; no live OS/G/WSL queries."""
from pathlib import Path
import datetime, hashlib, json

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
SPOOL = WORK / 'stage5_setup_drivefs_actual_postiq_02'
OUT = WORK / 'stage5_drivefs02_preserved_evidence_independent_review.json'
PINS = {
    'stage5_unc_bind_probe_before_windows_job_drain.py': '17eb6df098b01089e5919df1982fb047539385e07c69f9eba64060e61db24ed7',
    'stage5_setup_windows_before_windows_job_drain.py': 'b5826e46af71ad2353fef4a2c1ab28fe009f02411f9ab0b22032d46026755b33',
    'atomic_iqtree_windows.py': '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
    'diagnose_windows_owned_job_fixture.py': 'ef9410807f484c82fa542a1f8313ed64e333655df8a01548c3a33c3295ceccc2',
}
RESULT_SHA = '6c7595ddbcd5847e1ad311ae922bb9f95d483764f9faec5625659723e1f42b68'
FIXTURE = WORK / 'windows_owned_job_diagnosis_a0bdc60fe3de47348119e6161403b2cd' / 'receipt.json'
FIXTURE_SHA = '99be443a5dcda0b4f1791ba8e7a457b16f9a390cc0ba4637b626ad31bbc7f245'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def main():
    assert Path(__file__).resolve().parent == WORK
    assert not OUT.exists(), 'Never overwrite earlier audit'
    for name, expected in PINS.items():
        assert sha(WORK / name) == expected, name
    assert sha(SPOOL / 'result.json') == RESULT_SHA
    files = [{'path': p.relative_to(SPOOL).as_posix(), 'bytes': p.stat().st_size,
              'sha256': sha(p)} for p in sorted(SPOOL.rglob('*')) if p.is_file()]
    assert len(files) == 22
    result = read(SPOOL / 'result.json')
    linux = read(SPOOL / 'linux_terminal.json')
    command = read(SPOOL / 'commands/drivefs.command.json')
    launch = read(SPOOL / 'commands/drivefs.launch.json')
    closure = read(SPOOL / 'commands/drivefs.closure.json')
    wsl = read(SPOOL / 'wsl_exit.json')
    request = read(SPOOL / 'drivefs_readback_request.json')
    windows = read(SPOOL / 'drivefs_windows_readback.json')
    assert result['state'] == 'FAILED' and result['error']['kind'] == 'OwnedClosureFailure'
    assert result['owned_closure_proven'] is False and result['unknown_closure_stop_preserved'] is True
    nonce = result['owner_nonce']
    assert all(v['owner_nonce'] == nonce for v in [linux, wsl, request, windows])
    assert windows['source_sha256'] == request['source_sha256'] == result['source_sha256']
    assert windows['request_sha256'] == sha(SPOOL / 'drivefs_readback_request.json')
    assert windows['readback']['state'] == 'PASS_INDEPENDENT_WINDOWS_DRIVEFS_EXACT_BYTES'
    assert sha(SPOOL / 'linux_terminal.json') == result['linux_terminal_sha256']
    assert sha(SPOOL / 'wsl_exit.json') == result['wsl_exit_receipt_sha256']
    assert wsl['terminal'] == result['actual_wsl_exit']
    assert wsl['terminal']['creation_filetime'] == wsl['birth']['creation_filetime']
    assert wsl['terminal']['exited'] and wsl['terminal']['exit_code'] == 0
    assert wsl['terminal']['exit_filetime'] > wsl['birth']['creation_filetime']
    assert linux['owned_closure_proven'] and linux['owned_command_count'] == 1
    assert linux['remaining_direct_children'] == []
    assert linux['bootstrap']['boot_id'] == command['boot_id'] == closure['boot_id'] == launch['boot_id']
    for field in ['command_nonce', 'child_pid', 'child_start_ticks', 'pgid', 'sid', 'runner_pid', 'argv', 'identity']:
        assert command[field] == launch[field], field
    assert command['command_nonce'] == closure['command_nonce']
    assert command['execution'] == 'PROCESS_EXITED' and command['exit_code'] == closure['root_exit_code'] == 0
    assert closure['group_empty'] and closure['tracked_descendants_empty']
    assert closure['survivors'] == closure['unexplained_pgid_members'] == []
    for field, name in [('stdout_sha256', 'drivefs.stdout.txt'), ('stderr_sha256', 'drivefs.stderr.txt')]:
        assert command[field] == sha(SPOOL / 'commands' / name)
    native = result['native_commands'][0]
    for field, name in [('launch_sha256', 'drivefs.launch.json'), ('closure_sha256', 'drivefs.closure.json'), ('command_sha256', 'drivefs.command.json')]:
        assert native[field] == sha(SPOOL / 'commands' / name)
    assert command['group_closure_sha256'] == sha(SPOOL / 'commands/drivefs.closure.json')
    assert read(SPOOL / 'lock_released.json')['released'] is True
    assert 'windows_readback_worker' not in result
    assert not any('worker' in v['path'] for v in files)
    assert sha(FIXTURE) == FIXTURE_SHA
    fixture = read(FIXTURE)
    assert fixture['source_sha256'] == PINS['diagnose_windows_owned_job_fixture.py']
    assert fixture['api_sha256'] == PINS['atomic_iqtree_windows.py']
    assert fixture['birth']['creation_filetime'] == fixture['terminal']['creation_filetime']
    assert fixture['terminal']['exited'] and fixture['terminal']['exit_code'] == 0
    assert fixture['queries'][0]['A_job_state']['job_active_processes'] == 1
    assert fixture['queries'][0]['A_job_state']['job_pids'] == [21836]
    assert fixture['queries'][1]['A_job_state']['job_active_processes'] == 0
    assert fixture['queries'][1]['A_job_state']['job_pids'] == []
    report = {
        'schema': 'STAGE05_DRIVEFS02_PRESERVED_EVIDENCE_INDEPENDENT_REVIEW_V1',
        'state': 'PASS_C_EVIDENCE_READBACK_OLD_WINDOWS_WORKER_CLOSURE_UNPROVEN',
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'audit_source_sha256': sha(Path(__file__)), 'source_pins': PINS,
        'spool': str(SPOOL), 'spool_file_count': len(files), 'files': files,
        'result_sha256': RESULT_SHA, 'owner_nonce': nonce,
        'established': ['Recorded retained WSL client exit0 and exact Linux native closed scope bind across actual C receipts.',
                        'Windows exact-file readback finished and binds the same request/owner/source.',
                        'Original stable OS byte-lock release is recorded; no live lock query was performed.',
                        'Separate benign fixture records root exit0, then a job member, then full job emptiness after a25ms sample interval.'],
        'not_established': ['Original Windows worker PID/birth/terminal/job-empty state: no durable evidence in all22 spool files.',
                            'Exact original exception beneath windows_job finally: erased by17eb; root wait, job accounting, or query error remain possible.',
                            'The benign fixture does not identify the original failure or close its scope.',
                            'Current live Windows population, EventLog coverage, enclosing job emptiness and old-owner kernel terminal were not queried.'],
        'source_finding': '17eb windows_job finalizer overwrites underlying failure and can cancel its normal return; setup assignment therefore discards local birth/exit/job variables. Linux evidence cannot prove Windows worker closure.',
        'future_fix_rationale': 'Persist owned worker birth before resume, retained terminal before finite actual job-empty drain, and preserve primary plus closure errors before closing handles.',
        'separate_fixture_receipt': {'path': str(FIXTURE), 'sha256': FIXTURE_SHA},
        'stop_reconciliation_authorized': False, 'scientific_adoption_authorized': False,
        'actual_actions': 'C evidence/source reads and one new C review receipt only; no native/WSL/G/STOP/lock/process query or signal.'
    }
    with OUT.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': report['state'], 'path': str(OUT), 'bytes': OUT.stat().st_size, 'sha256': sha(OUT), 'source_sha256': sha(Path(__file__))}))


if __name__ == '__main__':
    main()
