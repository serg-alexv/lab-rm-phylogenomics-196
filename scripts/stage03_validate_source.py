"""Execute independent all196 source-locus validation with one writer lock."""
from pathlib import Path
import json,msvcrt,os,subprocess,time
import production_resume as w
from workflow_publication import commit

R=w.R;w.LOG=R/'reports/stage03/commands.jsonl'

def main():
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    w.status('3_markers','VALIDATING_SOURCE_LOCUS_INPUTS','RUNNING','PROGRESS_PUBLISHED',
             'All196 source-locus inputs constructed (398537 protein targets,2120 replicons). Independent raw-source, exact-sequence, locus, coordinate, topology and detector-order validation is RUNNING. Marker searches remain not run.')
    commit(['scripts/validate_locus_inputs.py','scripts/stage03_validate_source.py','reports/stage03/source_locus_validator_synthetic_tests.json',
            'reports/stage03/source_process_resource_snapshot.json','reports/stage02/windows_portability_check.json',
            'config/host_primary_stage03_v1.json','STATUS.md','status/stages.tsv'],
           'Start independent full196 source-locus validation; retain explicit marker denominator rules')
    command=[str(R/'.tools/validation_env/Scripts/python.exe'),'-u',str(R/'scripts/validate_locus_inputs.py'),
             '--root',str(R),'--inputs',str(R/'.work/source_locus_inputs_v1'),'--stage02-dir',str(R/'.work/stage02_validated'),
             '--output-dir',str(R/'.work/stage03_source_validation'),'--builder-script',str(R/'scripts/build_locus_inputs.py')]
    stdout=R/'.work/stage03_source_validation_stdout.log';stderr=R/'.work/stage03_source_validation_stderr.log'
    started=w.now();clock=time.monotonic()
    with stdout.open('ab') as out,stderr.open('ab') as err:
        p=subprocess.Popen(command,cwd=R,stdout=out,stderr=err)
        w.js(R/'status/stage03_source_validation_execution.json',{'status':'RUNNING','utc':started,'workflow_pid':os.getpid(),
              'child_pid':p.pid,'argv':command,'stdout_log':str(stdout.relative_to(R)),'stderr_log':str(stderr.relative_to(R))})
        print('INDEPENDENT_SOURCE_VALIDATOR_PID',p.pid,flush=True);code=p.wait()
    with w.LOG.open('a',encoding='utf-8') as f:
        f.write(json.dumps({'utc':started,'argv':command,'pid':p.pid,'exit_code':code,'elapsed_seconds':time.monotonic()-clock,
                           'stdout':stdout.read_text(),'stderr':stderr.read_text()})+'\n')
    output=R/'.work/stage03_source_validation'
    summary=json.loads((output/'validation_summary.json').read_text())
    w.js(R/'reports/stage03/source_locus_validation_summary.json',summary)
    if code or summary['status']!='PASS_SOURCE_LOCUS_INPUT_TRACEABILITY':
        raise RuntimeError('Independent source-locus validator failed; see preserved output: '+str(summary))
    w.js(R/'status/stage03_source_validation_execution.json',{'status':summary['status'],'utc':w.now(),
         'workflow_pid':os.getpid(),'child_pid':p.pid,'exit_code':code,'argv':command})
    w.status('3_markers','SOURCE_LOCUS_INPUTS_VALIDATED',summary['status'],'PROGRESS_PUBLISHED',
             'Independent source-locus mapping validation passed for all196,398537 protein targets and2120 replicons. Actual GToTree+HMMER marker searches are next; no alignment or topology has run.')
    commit(['reports/stage03/source_locus_validation_summary.json','status/stage03_source_validation_execution.json','STATUS.md','status/stages.tsv'],
           'Verify full196 exact source-locus sequences, replicon boundaries and detector input order')
    print('FULL196_SOURCE_LOCUS_VALIDATION_PASS',flush=True)

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),'scope':'independent Stage03 source-locus validation'})
    try:main()
    except Exception as e:
        w.js(R/'status/stage03_source_validation_failure.json',{'utc':w.now(),'error':str(e),'outputs_preserved':True})
        w.status('3_markers','BLOCKED_SOURCE_LOCUS_VALIDATION','FAIL_OR_INCOMPLETE','EVIDENCE_PUBLISHED',str(e)+'. All source and derived evidence preserved; no dependent search permitted.')
        commit(['status/stage03_source_validation_failure.json','STATUS.md','status/stages.tsv'],'Record explicit independent source-locus validation failure')
        raise
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
