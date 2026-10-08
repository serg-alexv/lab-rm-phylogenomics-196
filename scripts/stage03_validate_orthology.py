"""Independently validate the stricter curated host view under one writer lock."""
from pathlib import Path
import json,msvcrt,os,subprocess,time
import production_resume as w
from workflow_publication import commit

R=w.R;w.LOG=R/'reports/stage03/commands.jsonl'

def main():
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    w.status('3_markers','VALIDATING_CURATED_ORTHOLOGY','RUNNING','PROGRESS_PUBLISHED',
             'Original119-profile search evidence and fixed-filter proof preserved. Independent exact-row/sequence/whole-locus/QC/recovery checks of the pre-topology100-marker projection are running; all196 remain required.')
    commit(['scripts/validate_stage03_orthology.py','scripts/stage03_validate_orthology.py',
            'scripts/test_stage03_orthology.py','reports/stage03/orthology_validator_synthetic_tests.json',
            'STATUS.md','status/stages.tsv'],'Start independent exact-source orthology projection validation')
    argv=[str(R/'.tools/validation_env/Scripts/python.exe'),'-u',str(R/'scripts/validate_stage03_orthology.py')]
    started=w.now();clock=time.monotonic();out=R/'.work/stage03_orthology_validation_stdout.log';err=R/'.work/stage03_orthology_validation_stderr.log'
    with out.open('ab') as stdout,err.open('ab') as stderr:
        p=subprocess.Popen(argv,cwd=R,stdout=stdout,stderr=stderr)
        receipt={'execution':'RUNNING','utc':started,'workflow_pid':os.getpid(),'child_pid':p.pid,'argv':argv,
                 'stdout_log':str(out.relative_to(R)),'stderr_log':str(err.relative_to(R))}
        w.js(R/'status/stage03_orthology_validation_execution.json',receipt)
        print('INDEPENDENT_ORTHOLOGY_VALIDATOR_PID',p.pid,flush=True);code=p.wait()
    path=R/'.work/stage03_curated_validation/validation_summary.json'
    if code or not path.exists():raise RuntimeError('Independent curated view validator failed; preserve outputs and inspect stderr')
    v=json.loads(path.read_text())
    if v['status']!='PASS_MARKER_SOURCE_AND_FIXED_FILTERS' or v['scientific_stage_status']!='PASS_HOST_MARKER_INVENTORY' \
       or v['curation_status']!='PASS_TOPOLOGY_BLIND_ORTHOLOGY_DEDUPLICATION':raise ValueError('Independent scientific curation gate failed')
    w.js(R/'reports/stage03/curated_marker_validation_summary.json',v)
    receipt.update(execution=v['scientific_stage_status'],completed_utc=w.now(),exit_code=code,
                   elapsed_seconds=time.monotonic()-clock,validator_summary_sha256=w.digest(path))
    w.js(R/'status/stage03_orthology_validation_execution.json',receipt)
    with w.LOG.open('a',encoding='utf-8') as f:f.write(json.dumps(receipt)+'\n')
    w.status('3_markers','VALIDATED','PASS_HOST_MARKER_INVENTORY','PROGRESS_PUBLISHED',
             'Independent all196 source/HMM/fixed-filter checks and stricter pre-topology orthology projection passed.100 markers/19359 exact source sequences retained; zero duplicate full-protein loci. Stage03 portable publication/readback is next; no alignment/tree has run.')
    commit(['reports/stage03/curated_marker_validation_summary.json','status/stage03_orthology_validation_execution.json',
            'reports/stage03/commands.jsonl','STATUS.md','status/stages.tsv'],
           'Verify all196 host marker orthology projection with unchanged quality gates')
    print('FULL196_CURATED_HOST_INVENTORY_INDEPENDENT_PASS',flush=True)

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),
                                     'scope':'Independent pre-topology orthology projection validation'})
    try:main()
    except Exception as e:
        w.js(R/'status/stage03_orthology_validation_failure.json',{'utc':w.now(),'error':str(e),'outputs_preserved':True})
        w.status('3_markers','STOPPED_ORTHOLOGY_VALIDATION','FAIL_OR_INCOMPLETE','EVIDENCE_PUBLISHED',
                 str(e)+'. No dependent topology permitted; original and curated outputs preserved.')
        commit(['status/stage03_orthology_validation_failure.json','STATUS.md','status/stages.tsv'],
               'Record explicit independent curated orthology validation failure')
        raise
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
