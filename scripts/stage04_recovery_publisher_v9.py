"""Delegated Git writer inside a bounded owned publisher JobObject, never science."""
import argparse, json, os, sys
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v9 as S

def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--scope',required=True);p.add_argument('--fixture-fail',action='store_true');a=p.parse_args()
    runtime=Path(a.runtime);C.check(runtime.is_relative_to(S.RUNTIME),'Publisher runtime role differs')
    binding=C.load(runtime/'controller_binding.json');owner=binding['controller'];actual=S.process_identity(owner['pid'],owner['creation_filetime'])
    C.check(actual['state']=='RUNNING' and actual['creation_filetime']==owner['creation_filetime'],'Delegated owner identity absent/reused')
    if a.fixture_fail:
        C.atomic(runtime/'fixture_publisher_failure.json',{'utc':C.now(),'status':'INTENTIONAL_OPTIONAL_G_GIT_PUBLICATION_FAILURE',
          'effect':'NONZERO_PUBLISHER_EXIT_ONLY','scientific_jobs':0,'simulated_error':'OSError: unavailable G publication destination'})
        sys.exit(23)
    # Science owner holds workflow byte0; this distinct short-lived writer mutex
    # serializes only its delegated Git publisher. Parent is not a second writer.
    with C.WorkflowLock(S.RUNTIME/'git_writer.lock'):
        C.reconcile(S.ROOT)
        row=C.load(runtime/'outbox_latest.json')
        C.atomic(S.REPORT/'progress.json',{'utc':C.now(),'status':'ACTUAL_V9_NATIVE_INFERENCE_RUNNING_SCIENTIFIC_VALIDATION_PENDING',
          'controller':owner,'scope':a.scope,'measurement':row['measurement'],'release':'PENDING','stages05_07':'NOT_RUN'})
        C.atomic(S.ROOT/'status/stage04_execution.json',{'utc':C.now(),'execution':'V9_ACTUAL_NATIVE_RUNNING_INCOMPLETE',
          'scope':a.scope,'controller':owner,'negative_history_preserved':True,'scientific_validation':'INCOMPLETE','stages05_07':'NOT_RUN'})
        rows=(S.ROOT/'status/stages.tsv').read_text().splitlines()
        state='V9_NATIVE_SCOPE_EXITED_OUTPUT_CHECK_PENDING' if row['measurement']['process_exited'] else 'V9_ACTUAL_NATIVE_RUNNING_INCOMPLETE'
        rows=[(r.split('\t')[0]+'\t'+state+'\tPASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE\tSTAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING'
          if r.startswith('4_phylogeny\t') else r) for r in rows]
        (S.ROOT/'status/stages.tsv').write_text('\n'.join(rows)+'\n',encoding='utf-8',newline='\n')
        table='\n'.join('| '+' | '.join(r.split('\t'))+' |' for r in rows[1:])
        (S.ROOT/'STATUS.md').write_text('# Current execution status\n\nUpdated '+C.now()+'. Full approved196; no pilot.\n\n'+state+
          ': '+a.scope+'. Actual Scheduler-bound controller and native JobObject measurements are in reports/stage04/recovery_v9/progress.json. '
          'V6 exit1 and UNKNOWN old controller/job closure remain preserved. Scientific acceptance and verified full Stage04 Release remain pending.\n\n'
          '| Stage | Execution | Validation | Publication |\n|---|---|---|---|\n'+table+'\n',encoding='utf-8',newline='\n')
        paths=['reports/stage04/recovery_v9/progress.json','status/stage04_execution.json','STATUS.md','status/stages.tsv']
        receipt=S.publish(paths,'Record actual isolated V9 native process measurements; scientific validation pending')
        C.atomic(runtime/'publisher_remote_readback.json',receipt)

if __name__=='__main__':main()
