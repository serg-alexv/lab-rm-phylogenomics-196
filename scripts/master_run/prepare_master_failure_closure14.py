"""Publish accepted remote tree proof, exact missing recovery sources, and failed setup evidence."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/';extras={}
def declared(row):
 p=Path(row['path']);raw=p.read_bytes()
 if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Declared recovery source drift')
 extras[p.relative_to(W).as_posix()]=row['suggested_repository_path']
for row in json.loads((W/'directory_prune_execution_archive_completion.json').read_bytes())['public_source_and_review_mapping']:declared(row)
for row in json.loads((W/'stage05_curation/SINGLE_GENOME_AUDIT_PREPARATION.json').read_bytes())['files']:declared(row)
extras.update({
 'stage05_curation/SINGLE_GENOME_AUDIT_PREPARATION.json':B+'stage05_curation/SINGLE_GENOME_AUDIT_PREPARATION.json',
 'stage05_curation_closed_genome_handoff.md':B+'stage05_curation/CLOSED_GENOME_HANDOFF.md',
 'diagnose_failed_stage5_scope.py':'scripts/master_run/diagnose_failed_stage5_scope.py',
 'diagnose_failed_stage5_scope_independent_review.json':B+'stage5/failed_scope_diagnostic01/INDEPENDENT_SOURCE_REVIEW.json',
 'diagnose_directory_remote_attempt01_mapping.py':'scripts/master_run/diagnose_directory_remote_attempt01_mapping.py',
 'directory_prune_execution_remote_attempt01_diagnosis.json':B+'cleanup/directory_prune_execution01/REMOTE_ATTEMPT01_DIAGNOSIS.json',
 'directory_prune_execution01_readback_20261009T221909Z_534f476f/receipt.json':B+'cleanup/directory_prune_execution01/REMOTE_ATTEMPT01_FAILED.json',
 'directory_prune_execution01_readback_20261009T221909Z_534f476f/command_io/000.stdout.txt':B+'cleanup/directory_prune_execution01/REMOTE_ATTEMPT01_PUBLIC_GIT_TREE.txt',
 'stage04_primary196_independent_readback_20261009T221654Z_2262b4ce/receipt.json':B+'stage04/INDEPENDENT_FRESH_REMOTE_READBACK.json',
 'wsl_idle_repair13/execution_receipt.json':B+'stage5/idle_repair13/ACTUAL_EXECUTION_RECEIPT.json',
 'wsl_idle_repair13/failed_preexec_stop_preserved.json':B+'stage5/idle_repair13/ORIGINAL_PREEXEC_STOP_PRESERVED.json',
 'master_idle_readers13_git_objects.json':B+'publication/master_idle_readers13_git_objects.json',
 'master_idle_readers13_remote_readback.json':B+'publication/master_idle_readers13_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name,
})
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','5e911e4b6606e6bd3709bd9e85a195b00b558bbb',
 '--name','master_failure_closure14','--previous-status',str(W/'master_idle_readers13/status.json'),
 '--previous-markdown',str(W/'master_idle_readers13/STATUS.md'),
 '--phase','Independent full Stage4 GitHub readback PASS; add omitted eight recovery source files; preserve Stage5 resource failure and closure stop',
 '--independent-tree-receipt',str(W/'stage04_primary196_independent_readback_20261009T221654Z_2262b4ce/receipt.json'),
 '--spool','stage5_setup_diagnose_actual_postiq_01']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
