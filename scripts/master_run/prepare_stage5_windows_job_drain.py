"""C-only source/pin/history audit and public mapping; no process/WSL/G actions."""
from pathlib import Path
import ast, datetime as dt, hashlib, json

W=Path(__file__).resolve().parent
STEMS=('stage5_unc_bind_probe','stage5_setup_windows','stage5_build_actual_config',
       'stage5_closed_genome_archive_windows','stage5_gdrive_view')
SUFFIXES=('_before_windows_job_drain','_before_windows_job_peer_proof_checks',
          '_before_failed_root_terminal_persistence')
ACTIVE=('stage5_runtime_discovery.py','stage5_setup_linux.py','stage5_setup_windows.py',
        'stage5_build_actual_config.py','stage5_unc_bind_probe.py','stage5_windows_owner.py',
        'stage5_interop_smoke_windows.py','stage5_interop_linux_fixture.py',
        'stage5_closed_genome_archive_linux.py','stage5_closed_genome_archive_windows.py',
        'stage5_gdrive_view.py','verify_windows_owned_job_drain_fixture.py')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def pin(path):return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)}
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')

def main():
    assert str(W)==r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work'
    checks=[]
    for name in ACTIVE:
        tree=ast.parse((W/name).read_bytes())
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PINS' for t in node.targets):
                try:pins=ast.literal_eval(node.value)
                except ValueError:continue
                for member,expected in pins.items():
                    if isinstance(expected,str) and len(expected)==64 and (W/member).is_file():
                        assert sha(W/member)==expected,(name,member)
                        checks.append({'consumer':name,'member':member,'sha256':expected})
    assert len(checks)==47
    assert sha(W/'atomic_iqtree_windows.py')=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
    assert sha(W/'stage5_setup_linux.py')=='24aab72b74dd0aab6c58cac4951c30e6b1bfc9462460486748b546e50ec92e27'
    u=sha(W/'stage5_unc_bind_probe.py');s=sha(W/'stage5_setup_windows.py')
    old_u=sha(W/'stage5_unc_bind_probe_before_windows_job_drain.py')
    old_s=sha(W/'stage5_setup_windows_before_windows_job_drain.py')
    replacements={old_u:u,old_s:s};delta=[]
    for name in STEMS[2:]:
        before=(W/(name+SUFFIXES[0]+'.py')).read_bytes();expected=before
        for old,new in replacements.items():expected=expected.replace(old.encode(),new.encode())
        assert expected==(W/(name+'.py')).read_bytes(),name
        delta.append({'consumer':name+'.py','change':'EXACT_SOURCE_PIN_REPLACEMENTS_ONLY',
                      'before_sha256':hashlib.sha256(before).hexdigest(),'sha256':sha(W/(name+'.py'))})
    def nodes(path):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    before=nodes(W/'stage5_unc_bind_probe_before_windows_job_drain.py');after=nodes(W/'stage5_unc_bind_probe.py')
    assert all(after[k]==v for k,v in before.items() if k not in {'windows_job','windows_owner'})
    assert set(after)==set(before)|{'drain_windows_job'}
    before=nodes(W/'stage5_setup_windows_before_windows_job_drain.py');after=nodes(W/'stage5_setup_windows.py')
    assert all(after[k]==v for k,v in before.items() if k!='main')
    failed=W/'stage5_setup_drivefs_actual_postiq_02'
    failure=json.loads((failed/'result.json').read_bytes())
    assert failure['state']=='FAILED' and failure['owned_closure_proven'] is False and failure['unknown_closure_stop_preserved'] is True
    fixture=W/'windows_owned_job_diagnosis_a0bdc60fe3de47348119e6161403b2cd/receipt.json'
    assert sha(fixture)=='99be443a5dcda0b4f1791ba8e7a457b16f9a390cc0ba4637b626ad31bbc7f245'
    observed=json.loads(fixture.read_bytes())
    assert observed['terminal']['exit_code']==0 and observed['queries'][0]['A_job_state']['job_active_processes']==1
    assert observed['queries'][1]['A_job_state']['job_active_processes']==0 and observed['queries'][1]['A_job_state']['job_pids']==[]
    names=[name+'.py' for name in STEMS]
    names += [name+suffix+'.py' for name in STEMS for suffix in SUFFIXES]
    names += ['test_stage5_windows_job_drain.py','verify_windows_owned_job_drain_fixture.py',
              'diagnose_windows_owned_job_fixture.py','STAGE5_WINDOWS_JOB_DRAIN_METHODS.md',
              'stage5_windows_job_drain_independent_review.json','prepare_stage5_windows_job_drain.py']
    paths=[W/name for name in names]+[fixture]
    report={'schema':'STAGE05_WINDOWS_JOB_DRAIN_SOURCE_PREPARATION_V1','state':'SOURCE_AND_PURE_TESTS_PASS_OLD_FAILURE_UNRESOLVED',
        'recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'files':[pin(p) for p in paths],
        'active_static_PINS_checks':checks,'pin_only_consumer_deltas':delta,
        'unchanged_implementation':{'atomic_iqtree_windows.py':sha(W/'atomic_iqtree_windows.py'),'stage5_setup_linux.py':sha(W/'stage5_setup_linux.py')},
        'actual_old_failure_files':{name:pin(failed/name) for name in ('result.json','linux_terminal.json','wsl_exit.json','drivefs_windows_readback.json','lock_released.json')},
        'actual_benign_original_API_fixture':{'state':'ROOT_EXIT0_PRECEDES_DESCENDANT_JOB_EMPTY','root_pid':22928,'first_surviving_job_pid':21836,'next_sample_delay_seconds':0.025,'receipt_sha256':sha(fixture)},
        'actual_final_pure_tests':{'command':'python -B -m unittest test_stage5_setup test_stage5_build_actual_config test_stage5_gdrive_view test_stage5_closed_genome_archive_owner test_stage5_unc_bind_probe test_stage5_windows_job_drain -v','tests':55,'passed':55,'exit_code':0,'seconds':1.121},
        'draft_history_note':'115499 intermediate U source was reconstructed from retained exact2a02 plus exact reviewed resume/exit-time edits, then verified against its previously observed actual SHA before saving; other snapshots are original captured bytes.',
        'actual_corrected_worker_fixture':'NOT_RUN','old_worker_exact_cause':'NOT_RECORDED_NOT_RECONSTRUCTED',
        'STOP_reconciliation_authority':False,'WSL_or_G_or_actual_project_process_actions':0,
        'remaining_gates':['Root publication and actual immutable source readback','One root-authorized benign corrected-worker fixture on retained Windows Python','Separate independently reviewed old STOP/current-quiescence reconciliation','Fresh actual setup receipts matching current source pins before configuration acceptance'],
        'one_off_G_helper':'PIN_CONSISTENCY_ONLY_NOT_TO_BE_RERUN_WITH_CANONICAL_NESTED_STORAGE_BIND',
        'scientific_methods_change':False,'resource_reserve_change':False}
    report_path=W/'stage5_windows_job_drain_preparation.json';write(report_path,report)
    paths.append(report_path)
    mappings=[]
    for p in paths:
        relative='scripts/master_run/'+p.name if p.suffix=='.py' else 'reports/master_run/20261009/preparation/windows_job_drain01/'+p.name
        if p==fixture:relative='reports/master_run/20261009/preparation/windows_job_drain01/benign_original_API_fixture.json'
        mappings.append(dict(pin(p),suggested_repository_path=relative))
    target=W/'stage5_windows_job_drain_public_mapping.json'
    write(target,{'schema':'STAGE05_WINDOWS_JOB_DRAIN_PUBLIC_MAPPING_V1','state':'PENDING_ROOT_PUBLICATION_NOT_EXECUTED','files':mappings,
                  'old_failed_scope_unproven':True,'actual_corrected_worker_fixture':'NOT_RUN'})
    print(json.dumps({'preparation':pin(report_path),'mapping':pin(target),'members':len(mappings)}))

if __name__=='__main__':main()
