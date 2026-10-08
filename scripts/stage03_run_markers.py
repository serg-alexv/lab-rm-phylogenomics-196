"""Actual full196 marker execution, single Windows workflow lock and bounded WSL."""
from pathlib import Path
import json,msvcrt,os,subprocess,time
import production_resume as w
from workflow_publication import commit

R=w.R;w.LOG=R/'reports/stage03/commands.jsonl'

def main():
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    source=json.loads((R/'.work/stage03_source_validation/validation_summary.json').read_text())
    assert source['status']=='PASS_SOURCE_LOCUS_INPUT_TRACEABILITY' and source['assemblies_passed']==196
    ps="$o=Get-CimInstance Win32_OperatingSystem; [pscustomobject]@{utc=[DateTime]::UtcNow.ToString('o');free_ram_bytes=([int64]$o.FreePhysicalMemory*1024);free_disk_bytes=(Get-PSDrive C).Free;threads=2;job_limit=1;process_address_space_limit_bytes=2147483648} | ConvertTo-Json -Compress"
    resource=json.loads(w.run(['powershell','-NoProfile','-Command',ps]));resource['workflow_pid']=os.getpid()
    if resource['free_ram_bytes']<800*1024**2:raise RuntimeError('Insufficient measured Windows headroom for bounded marker job')
    w.js(R/'reports/stage03/marker_start_resources.json',resource)
    w.status('3_markers','RUNNING_FULL196_GTOTREE_HMMER','RUNNING','PROGRESS_PUBLISHED',
             'Independent full196 source mapping passed. Actual GToTree1.8.10+HMMER3.4 marker search is RUNNING for all196, serial per-assembly checkpoints, two CPU cores/threads and2GiB per-process address-space cap. All profile hits/domains/source joins are preserved. No alignment or topology has run.')
    paths=['scripts/stage03_markers.py','scripts/gtotree_evidence.py','scripts/run_stage03_host.sh','scripts/stage03_run_markers.py',
           'scripts/wsl_project.sh','config/host_primary_stage03_v1.json','reports/stage03/marker_filter_synthetic_tests.json',
           'reports/stage03/hmm_evidence_wrapper_synthetic_tests.txt','reports/stage03/marker_start_resources.json','STATUS.md','status/stages.tsv']
    commit(paths,'Start actual full196 GToTree and HMMER marker extraction with frozen filters and bounded resources')
    command=['wsl','-d','Ubuntu','--','bash','scripts/wsl_project.sh','host','bash','scripts/run_stage03_host.sh']
    stdout=R/'.work/stage03_markers_stdout.log';stderr=R/'.work/stage03_markers_stderr.log';started=w.now();clock=time.monotonic()
    with stdout.open('ab') as out,stderr.open('ab') as err:
        p=subprocess.Popen(command,cwd=R,stdout=out,stderr=err)
        w.js(R/'status/stage03_marker_execution.json',{'execution':'RUNNING','utc':started,'workflow_pid':os.getpid(),'wsl_launcher_pid':p.pid,
             'argv':command,'stdout_log':str(stdout.relative_to(R)),'stderr_log':str(stderr.relative_to(R)),
             'linux_pid_evidence':'.work/stage03_markers_v1/runner_launch_receipt.json','scientific_validation':'NOT_RUN'})
        print('ACTUAL_WSL_MARKER_LAUNCHER_PID',p.pid,flush=True);code=p.wait()
    with w.LOG.open('a',encoding='utf-8') as f:
        f.write(json.dumps({'utc':started,'argv':command,'pid':p.pid,'exit_code':code,'elapsed_seconds':time.monotonic()-clock,
                           'stdout':stdout.read_text(),'stderr':stderr.read_text()})+'\n')
    inventory=R/'.work/stage03_markers_v1/inventory_summary.json'
    if inventory.exists():
        summary=json.loads(inventory.read_text());w.js(R/'reports/stage03/inventory_summary.json',summary)
    else:summary={}
    if code:raise RuntimeError('Actual marker execution stopped, exit='+str(code)+'; inventory='+str(summary.get('inventory'))+'; '+stderr.read_text()[-1400:])
    assert summary['successful_searches']==196 and summary['profiles_searched']==119
    w.js(R/'status/stage03_marker_execution.json',{'execution':'ALL196_SEARCHES_COMPLETED','utc':w.now(),'workflow_pid':os.getpid(),
         'wsl_launcher_pid':p.pid,'argv':command,'exit_code':code,'scientific_validation':'INDEPENDENT_REVIEW_PENDING'})
    w.status('3_markers','ALL196_SEARCHES_COMPLETED','PENDING_INDEPENDENT_MARKER_AND_FUNCTION_SCOPE_REVIEW','PROGRESS_PUBLISHED',
             'Actual all196 GToTree+HMMER searches completed. Copy/length/occupancy inventory is constructed; independent source-to-marker validation and function-scope review are next. No alignment or tree has run; no Stage03 PASS is claimed yet.')
    commit(['reports/stage03/inventory_summary.json','status/stage03_marker_execution.json','STATUS.md','status/stages.tsv'],
           'Record completed full196 marker searches; independent scientific review remains pending')
    print('ALL196_ACTUAL_MARKER_SEARCHES_COMPLETED',flush=True)

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),'scope':'actual full196 GToTree+HMMER searches'})
    try:main()
    except Exception as e:
        w.js(R/'status/stage03_marker_failure.json',{'utc':w.now(),'error':str(e),'outputs_preserved':True})
        w.status('3_markers','STOPPED_MARKER_EXECUTION','FAIL_OR_SCIENTIFIC_BLOCKER_PENDING_REVIEW','EVIDENCE_PUBLISHED',str(e)+'. All completed search evidence preserved; no dependent alignment/tree permitted.')
        paths=['status/stage03_marker_failure.json','STATUS.md','status/stages.tsv']
        if (R/'reports/stage03/inventory_summary.json').exists():paths.append('reports/stage03/inventory_summary.json')
        commit(paths,'Record explicit full196 marker execution/check failure; preserve outputs')
        raise
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
