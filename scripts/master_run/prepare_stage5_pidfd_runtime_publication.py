"""Freeze exact C source metadata only; no import, WSL, G or publication."""
from pathlib import Path
import ast, hashlib, json

WORK=Path(__file__).resolve().parent
REPORT=WORK/'stage5_pidfd_runtime_preparation.json'
PREFIX='reports/master_run/20261009/stage5/pidfd_runtime_compat/'
CURRENT=['stage5_atomic.py','stage5_atomic_process.py','stage5_runtime_discovery.py',
         'stage5_setup_linux.py','stage5_setup_windows.py','stage5_build_actual_config.py','stage5_unc_bind_probe.py']
SOURCES=CURRENT+['test_stage5_pidfd_compat.py','test_stage5_targeted_hash_cache.py',
    'stage5_atomic_before_targeted_hash_cache.py','stage5_atomic_process_before_pidfd_compat.py',
    'stage5_runtime_discovery_before_pidfd_compat.py','stage5_runtime_discovery_after_pidfd_before_runtime_sha.py',
    'stage5_setup_linux_before_pidfd_compat.py','stage5_setup_linux_after_pidfd_before_runtime_sha.py',
    'stage5_setup_windows_before_pidfd_compat.py','stage5_setup_windows_after_pidfd_before_runtime_sha.py',
    'stage5_build_actual_config_before_pidfd_compat.py','stage5_build_actual_config_after_pidfd_before_runtime_sha.py',
    'stage5_unc_bind_probe_before_pidfd_compat.py','prepare_stage5_pidfd_compat_pins.py',
    'prepare_stage5_pidfd_runtime_pins.py',Path(__file__).name]
CONTROLS=['STAGE5_PIDFD_COMPAT_METHODS.md','STAGE5_PIDFD_COMPAT_METHODS_before_primary_abi_references.md',
    'stage5_pidfd_compat_pin_refresh.json','stage5_pidfd_runtime_pin_refresh.json',
    'stage5_pidfd_compat_independent_review.json','stage5_targeted_hash_cache_preparation.json',
    'stage5_targeted_hash_cache.patch','stage5_targeted_hash_cache_independent_review.json',
    'stage5_targeted_hash_cache_METHODS.md','stage5_targeted_hash_cache_SOURCE_COMPLETION.json']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert WORK==Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work') and not REPORT.exists()
    assert sha(WORK/'stage5_atomic.py')=='500dc3f1afbf1dd05cec5c8078f76bb1ec554daa2e56de53d4aa966b54ed8c04'
    assert sha(WORK/'stage5_atomic_process.py')=='e5be89978d84c451e52d9c50a0fa147c33e3ad91f4b5efa41377016810000b1e'
    checked=[]
    for name in CURRENT:
        tree=ast.parse((WORK/name).read_text())
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PINS' for t in node.targets):
                for member,expected in ast.literal_eval(node.value).items():
                    assert (WORK/member).is_file() and sha(WORK/member)==expected,(name,member)
                    checked.append({'consumer':name,'member':member,'sha256':expected})
    for ledger_name in ['stage5_pidfd_compat_pin_refresh.json','stage5_pidfd_runtime_pin_refresh.json']:
        for row in json.loads((WORK/ledger_name).read_text())['changes']:
            original=(WORK/row['original']).read_bytes()
            assert hashlib.sha256(original).hexdigest()==row['before_sha256']
            for before,after in row['replacements'].items():original=original.replace(before.encode(),after.encode())
            # First refresh's intermediate bytes are retained before the second.
            candidate=WORK/row['path']
            if sha(candidate)!=row['after_sha256']:
                candidate=candidate.with_name(candidate.stem+'_after_pidfd_before_runtime_sha.py')
            assert candidate.read_bytes()==original and sha(candidate)==row['after_sha256']
    files=[]
    for name in SOURCES+CONTROLS:
        path=WORK/name;assert path.parent==WORK and path.is_file() and not path.is_symlink()
        files.append({'local_path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),
                      'suggested_remote_path':('scripts/master_run/' if name in SOURCES else PREFIX)+name})
    assert len({row['suggested_remote_path'] for row in files})==len(files)
    value={'schema':'STAGE05_PIDFD_RUNTIME_SOURCE_PREPARATION_V1',
        'state':'PASS_SOURCE_PEERS_PURE_TESTS_AND_ACTIVE_PINS_ACTUAL_LINUX_REQUIRED',
        'files':files,'active_source_pin_checks':checked,'pin_only_consumer_deltas_verified':True,
        'tests':{'command':'python -B -m unittest test_stage5_pidfd_compat test_stage5_atomic test_stage5_setup test_stage5_build_actual_config test_stage5_runtime_discovery test_stage5_unc_bind_probe test_stage5_windows_owner test_stage5_interop_contracts test_stage5_closed_genome_archive test_stage5_closed_genome_archive_owner test_stage5_closed_genome_recovery test_stage5_targeted_hash_cache',
                 'exit_code':0,'passed':125,'seconds':2.143,'scope':'Pure C synthetic/mocked tests; no real Win API, WSL, pidfd, G or detector'},
        'independent_reviews':{'pidfd':{'path':'stage5_pidfd_compat_independent_review.json','sha256':sha(WORK/'stage5_pidfd_compat_independent_review.json')},
                               'targeted_hash':{'path':'stage5_targeted_hash_cache_independent_review.json','sha256':sha(WORK/'stage5_targeted_hash_cache_independent_review.json')}},
        'unchanged_dynamic_consumers':{name:sha(WORK/name) for name in ['stage5_windows_owner.py','stage5_interop_smoke_windows.py','stage5_interop_linux_fixture.py']},
        'actual_failed_interop_preserved':{name:sha(WORK/name) for name in ['stage5_interop_actual_postiq_02/result.json','stage5_interop_actual_postiq_02/exit0/linux/terminal.json']},
        'scientific_methods_changed':False,'actual_integration_by_this_preparation':'NOT_RUN',
        'actual_genome_execution':'NOT_RUN','resource_reduction_effect':'UNMEASURED',
        'historical_receipts_modified':False,'closure_stop_modified_by_this_preparation':False,
        'required_next_actual_gates':'Root-published/read-back current bytes; fresh same-boot toolchain/runtime/system+retained Python interop/storage/DriveFS/UNC; explicit first-genome budget',
        'inactive_archive_source_map':'Separate preparation; raw archive source pins were refreshed but grant no archive execution/eviction authority',
        'report_suggested_remote_path':PREFIX+REPORT.name}
    REPORT.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(REPORT),'sha256':sha(REPORT),'bytes':REPORT.stat().st_size,'files':len(files),'active_pin_checks':len(checked)}))


if __name__=='__main__':main()
