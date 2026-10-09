"""Declare failed runtime evidence, scoped repair proposal and independently reviewed readers."""
from pathlib import Path
import subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/'
extras={
 'repair_wsl_idle_after_preexec_failure.py':'scripts/master_run/repair_wsl_idle_after_preexec_failure.py',
 'repair_wsl_idle_after_preexec_failure_draft839.py':'scripts/master_run/repair_wsl_idle_after_preexec_failure_draft839.py',
 'repair_wsl_idle_after_preexec_failure_independent_review.json':B+'stage5/idle_repair13/INDEPENDENT_SOURCE_REVIEW.json',
 'verify_directory_prune_execution_remote.py':'scripts/master_run/verify_directory_prune_execution_remote.py',
 'test_verify_directory_prune_execution_remote.py':'scripts/master_run/test_verify_directory_prune_execution_remote.py',
 'directory_prune_execution_remote_reader_METHODS.md':B+'cleanup/directory_prune_execution01/REMOTE_READER_METHODS.md',
 'directory_prune_execution_remote_reader_preparation.json':B+'cleanup/directory_prune_execution01/REMOTE_READER_PREPARATION.json',
 'directory_prune_execution_remote_reader_independent_review.json':B+'cleanup/directory_prune_execution01/REMOTE_READER_INDEPENDENT_SOURCE_REVIEW.json',
 'directory_prune_execution01_readback_20261009T220430Z_e4a905e0/receipt.json':B+'cleanup/directory_prune_execution01/INDEPENDENT_LOCAL_READBACK.json',
 'stage04_remote_expected.json':B+'preparation/stage04_remote_expected.json',
 'stage04_primary196_remote_reader_preparation.json':B+'preparation/stage04_primary196_remote_reader_preparation.json',
 'stage04_remote_reader_independent_source_review.json':B+'preparation/stage04_remote_reader_independent_source_review.json',
 'stage5_setup_preexec_delta_independent_source_review.json':B+'stage5/post_iq_setup/PREEXEC_DELTA_INDEPENDENT_SOURCE_REVIEW.json',
 'stage5_setup_failure01_preparation.json':B+'stage5/setup_failure01/PREPARATION.json',
 'stage5_setup_failure01_publication_files.json':B+'stage5/setup_failure01/PUBLICATION_FILES.json',
 'STAGE5_SETUP_FAILURE01_METHODS.md':B+'stage5/setup_failure01/METHODS.md',
 'master_toolchain12_git_objects_final.json':B+'publication/master_toolchain12_git_objects_final.json',
 'master_toolchain12_remote_readback.json':B+'publication/master_toolchain12_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name,
}
for name in ('verify_stage04_primary196_remote.py','test_verify_stage04_primary196_remote.py',
 'verify_stage04_primary196_remote_METHODS.md','stage5_setup_windows.py','stage5_setup_linux.py','test_stage5_setup.py',
 'stage5_setup_windows_attempt01.py','stage5_setup_linux_attempt01.py','test_stage5_setup_attempt01.py'):
 extras[name]='scripts/master_run/'+name
for name in ('preparation.json','wslconfig.before.txt','wslconfig.after.txt','failed_stop_observation.json','wsl_version_observation.json'):
 extras['wsl_idle_repair13/'+name]=B+'stage5/idle_repair13/'+name
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),
 '--expected-head','2992ce15c96da52bc5e4a4f28c3a45def185e538','--name','master_idle_readers13',
 '--previous-status',str(W/'master_toolchain12/status.json'),'--previous-markdown',str(W/'master_toolchain12/STATUS.md'),
 '--phase','Preserve Stage5 pre-exec failure and closure stop; publish reviewed finite WSL idle repair and independent tree/journal readers',
 '--spool','stage5_setup_runtime_actual_postiq_01']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
