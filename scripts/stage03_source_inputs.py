"""Resume Stage3 source-locus construction, under the single workflow lock."""
from pathlib import Path
import json,msvcrt,os,subprocess,time
import production_resume as w
from workflow_publication import commit

R=w.R;w.LOG=R/'reports/stage03/commands.jsonl'

def main():
    receipt=json.loads((R/'reports/stage02/publication_receipt.json').read_text())
    assert receipt['status']=='UPLOAD_VERIFIED' and receipt['approved_assemblies']==196
    w.run(['git','fetch','origin','main']);w.run(['git','pull','--ff-only','origin','main'])
    ps="$o=Get-CimInstance Win32_OperatingSystem; [pscustomobject]@{utc=[DateTime]::UtcNow.ToString('o');host=(hostname);free_ram_bytes=([int64]$o.FreePhysicalMemory*1024);total_ram_bytes=([int64]$o.TotalVisibleMemorySize*1024);free_disk_bytes=(Get-PSDrive C).Free;compute_thread_limit=2;biological_job_limit=1} | ConvertTo-Json -Compress"
    resource=json.loads(w.run(['powershell','-NoProfile','-Command',ps]));resource['workflow_pid']=os.getpid()
    w.js(R/'reports/stage03/start_resources.json',resource)
    assert resource['host'].lower()=='wd' and resource['free_ram_bytes']>600*1024**2
    config=json.loads((R/'config/host_primary_stage03_v1.json').read_text())
    assert config['frozen_before_marker_search_and_topology'] and config['profile_count_independently_measured']==119
    w.status('3_markers','PREPARING_SOURCE_LOCUS_INPUTS','RUNNING','PROGRESS_PUBLISHED',
             'Stage02 all196 sequence validation and Release byte verification completed. Stage03 is constructing exact primary-protein locus inputs for all196; fixed119/196 marker filters and MAFFT/trimAl alignment method are frozen before searches/topology. No marker result is claimed yet.')
    commit(['scripts/build_locus_inputs.py','scripts/stage03_source_inputs.py','scripts/portable_release.py','scripts/test_portable_release.py',
            'config/host_primary_stage03_v1.json','reports/stage03/source_locus_synthetic_tests.json','reports/stage03/portable_archive_synthetic_tests.json',
            'reports/stage03/start_resources.json','STATUS.md','status/stages.tsv'],
           'Start full196 source-locus preparation and freeze host marker filters before searches')
    command=[str(R/'.tools/validation_env/Scripts/python.exe'),'-u',str(R/'scripts/build_locus_inputs.py'),
             '--root',str(R),'--output',str(R/'.work/source_locus_inputs_v1'),'--validated-stage02-dir',str(R/'.work/stage02_validated')]
    stdout=R/'.work/stage03_source_builder_stdout.log';stderr=R/'.work/stage03_source_builder_stderr.log'
    started=w.now();clock=time.monotonic()
    with stdout.open('ab') as out,stderr.open('ab') as err:
        p=subprocess.Popen(command,cwd=R,stdout=out,stderr=err)
        w.js(R/'status/stage03_source_execution.json',{'status':'RUNNING','utc':started,'workflow_pid':os.getpid(),'child_pid':p.pid,
             'argv':command,'stdout_log':str(stdout.relative_to(R)),'stderr_log':str(stderr.relative_to(R)),
             'scope':'One full196 source parser, no duplicated biological search','peak_ram_bytes':None,'measurement_limit':'Live process snapshots; peak not monitored'})
        print('SOURCE_BUILDER_PID',p.pid,flush=True)
        code=p.wait()
    with w.LOG.open('a',encoding='utf-8') as f:
        f.write(json.dumps({'utc':started,'argv':command,'pid':p.pid,'exit_code':code,'elapsed_seconds':time.monotonic()-clock,
                           'stdout':stdout.read_text(),'stderr':stderr.read_text()})+'\n')
    if code:raise RuntimeError('Source-locus builder failed: '+stderr.read_text()[-1800:])
    summary=json.loads((R/'.work/source_locus_inputs_v1/construction_summary.json').read_text())
    assert summary['constructed_assemblies']==196
    w.js(R/'reports/stage03/source_construction_summary.json',summary)
    w.js(R/'status/stage03_source_execution.json',{'status':'CONSTRUCTED_PENDING_INDEPENDENT_VALIDATION','utc':w.now(),
          'workflow_pid':os.getpid(),'child_pid':p.pid,'exit_code':code,'argv':command})
    w.status('3_markers','SOURCE_INPUTS_CONSTRUCTED','PENDING_INDEPENDENT_SOURCE_MAPPING_VALIDATION','PROGRESS_PUBLISHED',
             'All196 primary-protein locus inputs constructed from independently validated raw NCBI evidence. Independent source/sequence/replicon/order validation is next; marker searches remain not run.')
    commit(['reports/stage03/source_construction_summary.json','status/stage03_source_execution.json','STATUS.md','status/stages.tsv'],
           'Record full196 source-locus construction; independent mapping validation remains pending')
    print('FULL196_SOURCE_INPUTS_CONSTRUCTED',flush=True)

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),'scope':'stage03 source locus construction'})
    try:main()
    except Exception as e:
        w.js(R/'status/stage03_source_failure.json',{'utc':w.now(),'error':str(e),'outputs_preserved':True})
        w.status('3_markers','BLOCKED_SOURCE_INPUT_CHECK','FAIL_OR_INCOMPLETE','EVIDENCE_PUBLISHED',str(e)+'; source inputs and all196 raw packages preserved. No dependent search permitted until resolved.')
        commit(['status/stage03_source_failure.json','STATUS.md','status/stages.tsv'],'Record explicit Stage03 source-input check failure')
        raise
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
