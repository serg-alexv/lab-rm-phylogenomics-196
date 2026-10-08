"""Execute independent marker checks; preserve unresolved scientific gates."""
from pathlib import Path
import json,msvcrt,os,subprocess,time
import production_resume as w
from workflow_publication import commit

R=w.R;w.LOG=R/'reports/stage03/commands.jsonl'

def main():
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    inventory=json.loads((R/'.work/stage03_markers_v1/inventory_summary.json').read_text())
    if inventory['successful_searches']!=196:raise RuntimeError('All196 successful searches required')
    w.status('3_markers','VALIDATING_FULL196_MARKERS','RUNNING','PROGRESS_PUBLISHED',
             'All196 actual marker searches completed. Independent raw-source/HMM/domain/copy/length/occupancy checks and executed function-scope review are running; no Stage03 scientific PASS or dependent topology is claimed.')
    commit(['scripts/validate_stage03_markers.py','scripts/stage03_validate_markers.py',
            'reports/stage03/marker_validator_synthetic_tests.json','reports/stage03/host_profile_scope_review.json',
            'STATUS.md','status/stages.tsv'],'Start independent full196 source-to-marker and fixed-filter validation')
    command=[str(R/'.tools/validation_env/Scripts/python.exe'),'-u',str(R/'scripts/validate_stage03_markers.py'),
             '--output-dir',str(R/'.work/stage03_marker_validation'),
             '--host-profile-review',str(R/'reports/stage03/host_profile_scope_review.json')]
    stdout=R/'.work/stage03_marker_validation_stdout.log';stderr=R/'.work/stage03_marker_validation_stderr.log'
    started=w.now();clock=time.monotonic()
    with stdout.open('ab') as out,stderr.open('ab') as err:
        p=subprocess.Popen(command,cwd=R,stdout=out,stderr=err)
        receipt={'status':'RUNNING','utc':started,'workflow_pid':os.getpid(),'child_pid':p.pid,'argv':command,
                 'stdout_log':str(stdout.relative_to(R)),'stderr_log':str(stderr.relative_to(R))}
        w.js(R/'status/stage03_marker_validation_execution.json',receipt)
        print('INDEPENDENT_MARKER_VALIDATOR_PID',p.pid,flush=True)
        while p.poll() is None:
            time.sleep(10)
        code=p.returncode
    with w.LOG.open('a',encoding='utf-8') as f:
        f.write(json.dumps({'utc':started,'argv':command,'pid':p.pid,'exit_code':code,
                           'elapsed_seconds':time.monotonic()-clock,'stdout_log':str(stdout.relative_to(R)),
                           'stderr_log':str(stderr.relative_to(R))})+'\n')
    output=R/'.work/stage03_marker_validation/validation_summary.json'
    if not output.exists() or output.stat().st_mtime<time.time()-(time.monotonic()-clock)-5:
        raise RuntimeError('No current independent marker summary; inspect preserved validator stderr')
    summary=json.loads(output.read_text())
    w.js(R/'reports/stage03/marker_validation_summary.json',summary)
    if summary['status']!='PASS_MARKER_SOURCE_AND_FIXED_FILTERS':
        raise RuntimeError('Independent marker integrity failed')
    scientific=summary['scientific_stage_status'];passed=scientific=='PASS_HOST_MARKER_INVENTORY'
    if passed and code:raise RuntimeError('Independent PASS summary accompanied by failed checker exit')
    receipt.update(status=scientific,completed_utc=w.now(),exit_code=code,elapsed_seconds=time.monotonic()-clock,
                   validator_summary_sha256=w.digest(output),outputs_preserved=True)
    w.js(R/'status/stage03_marker_validation_execution.json',receipt)
    w.status('3_markers','VALIDATED' if passed else 'SCIENTIFIC_REVIEW_REQUIRED',scientific,'PROGRESS_PUBLISHED',
             'Independent source/fixed-filter integrity checks completed for all196. Scientific outcome: '+scientific+
             '. Scientific gates and source-function evidence remain distinct from GitHub upload; no dependent topology starts before scientific PASS and verified Stage03 publication.')
    commit(['reports/stage03/marker_validation_summary.json','status/stage03_marker_validation_execution.json',
            'reports/stage03/commands.jsonl','STATUS.md','status/stages.tsv'],'Record independently executed full196 marker checks and actual scientific gates')
    print('INDEPENDENT_MARKER_OUTCOME',scientific,flush=True)

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),
                                     'scope':'Independent all196 marker validation'})
    try:main()
    except Exception as e:
        w.js(R/'status/stage03_marker_validation_failure.json',{'utc':w.now(),'error':str(e),'outputs_preserved':True})
        w.status('3_markers','STOPPED_INDEPENDENT_VALIDATION','FAIL_OR_INCOMPLETE','EVIDENCE_PUBLISHED',
                 str(e)+'. Actual outputs and logs preserved; no dependent topology permitted.')
        commit(['status/stage03_marker_validation_failure.json','STATUS.md','status/stages.tsv'],
               'Record explicit independent marker validation failure')
        raise
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
