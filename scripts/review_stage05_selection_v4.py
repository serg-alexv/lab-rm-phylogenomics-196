"""Execute a bounded synthetic installed-native selection oracle on WD."""
from pathlib import Path
import json, os, subprocess, sys, time
import stage04_controller as C
import production_resume as w
ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=ROOT/'reports/stage05/preparation_selection_v4'
FIXTURE=ROOT/'.work/stage05_selection_v3_review'

def main():
    C.check(sys.platform=='win32' and Path.cwd().resolve()==ROOT,'Dedicated WD G preparation owner required')
    with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
        C.reconcile(ROOT)
        OUT.mkdir(parents=True,exist_ok=True)
        before=C.windows_snapshot(ROOT)
        C.check(before['available_bytes']>=1073741824,'One GiB measured Windows reserve required for bounded synthetic R review')
        wrapper=HISTORY/'scripts/wsl_project.sh'
        bootstrap=HISTORY/'.private_run/migration_runtime_v5/stage04_migration_wsl_v5.sh'
        bridge=ROOT/'scripts/stage05_detector_env_v5.sh'
        C.check(C.digest(bootstrap)==C.digest(ROOT/'scripts/stage04_migration_wsl_v5.sh')=='d0a2129a4667b70370116b83907944ab2eb4193b658bfbbc32015de1e15b3ab1','Exact reviewed G-mount bootstrap required')
        C.check(C.digest(wrapper)==C.digest(ROOT/'scripts/wsl_project.sh')=='459c33d5edd186836ba8079ee6204221b79cfe70160f3f5ec7f9503286f28d12','Retained tool wrapper differs')
        python_result=C.load(FIXTURE/'python_test_results.json')
        C.check(python_result['status']=='PASS_SYNTHETIC_ONLY' and python_result['tests']==24 and not python_result['errors'] and not python_result['failures'],'Python selection regressions incomplete')
        probe=['wsl','-d','Ubuntu','--','bash',C.linux_path(bootstrap),'bash',C.linux_path(bridge),'cat','/proc/meminfo']
        probe_result=subprocess.run(probe,cwd=HISTORY,capture_output=True,check=True)
        available=int([v for v in probe_result.stdout.decode().splitlines() if v.startswith('MemAvailable:')][0].split()[1])*1024
        after=C.windows_snapshot(ROOT)
        C.check(available>=1073741824 and after['available_bytes']>=1073741824,'Measured synthetic R review headroom insufficient')
        command=['wsl','-d','Ubuntu','--','bash',C.linux_path(bootstrap),'bash',C.linux_path(bridge),
                 '/usr/bin/time','-v','-o',C.linux_path(OUT/'native_r.time.txt'),
                 '/usr/bin/prlimit','--as=1073741824','--',
                 C.linux_path(HISTORY/'.tools/linux/detector_env/bin/Rscript'),
                 C.linux_path(ROOT/'scripts/check_stage05_padloc_selection_native_v3.R'),
                 C.linux_path(HISTORY/'.tools/linux/detector_env/bin/padloc.R'),
                 C.linux_path(FIXTURE/'native_oracle_fixtures.json'),C.linux_path(OUT/'native_oracle_results.json')]
        started=C.now();clock=time.monotonic()
        result=subprocess.run(command,cwd=HISTORY,capture_output=True,timeout=120)
        (OUT/'native_r.stdout.txt').write_bytes(result.stdout);(OUT/'native_r.stderr.txt').write_bytes(result.stderr)
        C.atomic(OUT/'native_command.json',{'started_utc':started,'finished_utc':C.now(),'controller_pid':os.getpid(),
            'actual_argv':command,'actual_windows_launch_cwd':str(HISTORY),'elapsed_seconds':time.monotonic()-clock,
            'exit_code':result.returncode,'outer_memory_budget':'One GiB address-space cap on R only; synthetic selection evaluation',
            'windows_before_wsl':before,'windows_after_wsl':after,'linux_available_bytes':available,
            'biological_HMM_searches':0,'production_inference_admission':'NOT_EVALUATED_NOT_WAIVED'})
        C.check(result.returncode==0,'Actual installed-native R selection oracle failed; outputs preserved')
        native=C.load(OUT/'native_oracle_results.json');fixtures=C.load(FIXTURE/'native_oracle_fixtures.json')
        C.check(native['status']=='PASS_ALL_INSTALLED_PADLOC_SELECTION_EXPRESSIONS_SYNTHETIC_ONLY'
                and native['biological_HMM_searches']==0 and len(native['cases'])==len(fixtures['cases']), 'Native oracle exit alone is insufficient')
        for actual,expected in zip(native['cases'],fixtures['cases']):
            selected=actual['selected_hit_ids'];selected=[selected] if isinstance(selected,str) else selected
            C.check(actual['case_id']==expected['case_id'] and sorted(selected)==sorted(expected['expected_hit_ids']),'Native and Python selection disagree')
        for name in ['native_oracle_fixtures.json','python_test_results.json']:
            (OUT/name).write_bytes((FIXTURE/name).read_bytes())
        sources=['scripts/stage05_padloc_selection_v3.py','scripts/test_stage05_padloc_selection_v3.py',
                 'scripts/check_stage05_padloc_selection_native_v3.R','scripts/review_stage05_selection_v4.py',
                 'scripts/stage05_detector_env_v5.sh']
        C.atomic(OUT/'review.json',{'status':'PASS_SYNTHETIC_NATIVE_SELECTION_EQUIVALENCE_PREPARATION_ONLY',
            'utc':C.now(),'python_negative_and_regression_tests':24,'installed_native_R_cases':len(native['cases']),
            'native_source_sha256':native['native_source_sha256'],'biological_HMM_searches':0,
            'production_adoption':'NOT_ADOPTED; role-aware adapter/controller and independent full196 evidence gates remain required',
            'sources':[{'path':n,'sha256':C.digest(ROOT/n)} for n in sources],
            'fixture_sha256':C.digest(OUT/'native_oracle_fixtures.json'),'native_result_sha256':C.digest(OUT/'native_oracle_results.json'),
            'actual_command_sha256':C.digest(OUT/'native_command.json')})
        print('ACTUAL_INSTALLED_NATIVE_SELECTION_EQUIVALENCE_COMPLETE_SYNTHETIC_ONLY',flush=True)

if __name__=='__main__':main()
