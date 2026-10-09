"""Delegated Git writer inside a bounded owned publisher JobObject, never science."""
import argparse, json, os, sys
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v10 as S

def state(row):
    C.check(type(row['process_exited']) is bool,'Actual process-exited flag required')
    if not row['process_exited']:return 'V10_ACTUAL_NATIVE_RUNNING_INCOMPLETE'
    code=row.get('exit_code',row.get('actual_exit_code'))
    C.check(type(code) is int,'Terminal observation requires actual integer exit; None is never completed')
    return 'V10_NATIVE_EXIT0_OUTPUT_VALIDATION_PENDING' if code==0 else 'V10_NATIVE_EXIT_NONZERO_FAILED_INCOMPLETE'

def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--scope',required=True);p.add_argument('--fixture-fail',action='store_true')
    p.add_argument('--observation',required=True);p.add_argument('--observation-sha256',required=True);a=p.parse_args()
    runtime=Path(a.runtime);C.check(runtime.is_relative_to(S.RUNTIME),'Publisher runtime role differs')
    binding=C.load(runtime/'controller_binding.json');owner=binding['controller'];actual=S.process_identity(owner['pid'],owner['creation_filetime'])
    C.check(actual['state']=='RUNNING' and actual['creation_filetime']==owner['creation_filetime'],'Delegated owner identity absent/reused')
    observation=Path(a.observation);C.check(observation.is_relative_to(runtime/'observations') and C.digest(observation)==a.observation_sha256,
      'Immutable observation input hash differs')
    row=C.load(observation);C.check(row['scope']==a.scope,'Observation scope differs');execution=state(row['measurement'])
    if a.fixture_fail:
        C.atomic(runtime/'fixture_publisher_failure.json',{'utc':C.now(),'status':'INTENTIONAL_OPTIONAL_G_GIT_PUBLICATION_FAILURE',
          'effect':'NONZERO_PUBLISHER_EXIT_ONLY','scientific_jobs':0,'simulated_error':'OSError: unavailable G publication destination',
          'observation_sha256':a.observation_sha256,'native_observed_state':execution})
        sys.exit(23)
    # Science owner holds workflow byte0; this distinct short-lived writer mutex
    # serializes only its delegated Git publisher. Parent is not a second writer.
    with C.WorkflowLock(S.RUNTIME/'git_writer.lock'):
        C.reconcile(S.ROOT)
        C.atomic(S.REPORT/'progress.json',{'utc':C.now(),'status':execution,'observation_as_of_utc':row['measurement']['utc'],
          'observation_sha256':a.observation_sha256,'controller':owner,'scope':a.scope,'measurement':row['measurement'],'release':'PENDING','stages05_07':'NOT_RUN'})
        C.atomic(S.ROOT/'status/stage04_execution.json',{'utc':C.now(),'execution':execution,'observation_sha256':a.observation_sha256,
          'observation_as_of_utc':row['measurement']['utc'],'native_pid':row['measurement']['child_pid'],
          'native_creation_filetime':row['measurement']['creation_filetime'],
          'scope':a.scope,'controller':owner,'negative_history_preserved':True,'scientific_validation':'INCOMPLETE','stages05_07':'NOT_RUN'})
        import csv,io
        source=list(csv.DictReader(io.StringIO((S.ROOT/'status/stages.tsv').read_text()),delimiter='\t'))
        fields=list(source[0])+[k for k in ('observation_as_of_utc','native_pid','native_creation_filetime') if k not in source[0]]
        for record in source:
            if record['stage']=='4_phylogeny':record.update(execution=execution,validation='PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
              publication='STAGE04A_STAGE04B_STAGE04C_FAILURE_UPLOAD_VERIFIED_FULL_STAGE04_PENDING',
              observation_as_of_utc=row['measurement']['utc'],native_pid=str(row['measurement']['child_pid']),
              native_creation_filetime=str(row['measurement']['creation_filetime']))
        buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=fields,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(source)
        rows=buffer.getvalue().splitlines()
        (S.ROOT/'status/stages.tsv').write_text('\n'.join(rows)+'\n',encoding='utf-8',newline='\n')
        table='\n'.join('| '+' | '.join(r.split('\t'))+' |' for r in rows[1:])
        (S.ROOT/'STATUS.md').write_text('# Current execution status\n\nUpdated '+C.now()+'. Full approved196; no pilot.\n\n'+execution+
          ': '+a.scope+'. Observation as of '+row['measurement']['utc']+'; native PID'+str(row['measurement']['child_pid'])+
          ', creation FILETIME'+str(row['measurement']['creation_filetime'])+'. Actual Scheduler-bound controller and native JobObject measurements are in reports/stage04/recovery_v10/progress.json. '
          'V6 exit1 and UNKNOWN old controller/job closure remain preserved. Scientific acceptance and verified full Stage04 Release remain pending.\n\n'
          '| '+' | '.join(fields)+' |\n|'+'|'.join('---' for _ in fields)+'|\n'+table+'\n',encoding='utf-8',newline='\n')
        paths=['reports/stage04/recovery_v10/progress.json','status/stage04_execution.json','STATUS.md','status/stages.tsv']
        receipt=S.publish(paths,'Record actual isolated V10 native process measurements; scientific validation pending')
        C.atomic(runtime/'publication_acknowledgements'/(a.observation_sha256+'.json'),{**receipt,'observation_sha256':a.observation_sha256,
          'published_native_state':execution,'observation_as_of_utc':row['measurement']['utc'],'remote_bytes_verified':True})

if __name__=='__main__':main()
