"""Bounded, measured resource diagnostic; never admits or starts inference."""
from pathlib import Path
from unittest.mock import patch
import json, os, subprocess, sys, time
import stage04_controller as C
import stage04_inference_controller_v5 as K
import production_resume as w
from workflow_publication import commit

ROOT=Path(__file__).resolve().parents[1]
HISTORY=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT=ROOT/'reports/stage04/repair_admission_v1'

def publish(paths,message):
    head=commit(paths,message)
    C.command(ROOT,['git','fetch','origin','main'])
    for name in paths:
        actual=subprocess.run(['git','show','origin/main:'+name],cwd=ROOT,capture_output=True,check=True).stdout
        import hashlib
        C.check(hashlib.sha256(actual).hexdigest()==C.digest(ROOT/name),'Remote bytes differ: '+name)
    print('REMOTE_BYTES_VERIFIED '+head,flush=True)

def main():
    with C.WorkflowLock(HISTORY/'.work/workflow.lock'):
        head=C.reconcile(ROOT)
        OUT.mkdir(parents=True,exist_ok=True)
        authority={'utc':C.now(),'remote_reconciled_commit':head,'execution':'REPAIR_AND_PLATFORM_ADAPTER_AUTHORIZED_INFERENCE_NOT_RUN',
          'authority':'Direct human instruction to close, kill, reconfigure and delete what is necessary for the main goal; scoped repair preserves scientific data, accepted outputs, provenance, checkpoints, current control/remote connections and credentials.',
          'manual_resets_only':True,'recurring_automation':False,'paid_compute':False,'security_disabling':False,
          'stopped_owner_receipt':C.load(Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\referenced-chatgpt-conversation-this-is-an\outputs\WD_V2_CONTROL_OWNER_STOP_20261008.json')),
          'resource_diagnostic_pid':os.getpid(),'scientific_process_started':False}
        C.atomic(OUT/'authority.json',authority)
        order=ROOT/'WORK_ORDER.md'
        text=order.read_text(encoding='utf-8')
        heading='## User-authorized resource repair amendment, 2026-10-08'
        if heading not in text:
            order.write_text(text+'\n\n'+heading+'\nThe latest direct human instruction authorizes necessary scoped process, configuration and temporary-storage repair to achieve the existing full196 scientific goal. This supersedes the earlier keep-waiting-only and unrelated-termination restrictions within that necessary repair scope. Preserve source data, accepted outputs, provenance, checkpoints, current Codex control/remote connection and credentials. Do not weaken scientific requirements, disable security, use paid cloud compute, redeem token resets automatically or recreate recurring automation. A documented native Windows IQ-TREE3.1.4 adapter with honest platform-specific resource controls is authorized if measured WSL overhead prevents admission. Preserve all historical source identities and failures.\n',encoding='utf-8')
        w.status('4_phylogeny','DIAGNOSING_BOUNDED_RESOURCE_ADMISSION_OR_NATIVE_WINDOWS_ADAPTER','PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
                 'STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING',
                 'Old waiter8200 and CLI28288 stopped with no scientific process interrupted. Actual G source/bootstrap/argv checks passed. No inference freeze/tree or production detector run exists. Scoped repair and native Windows IQ-TREE adapter authorized; unchanged full196 scientific requirements and manual resets only.')
        publish(['WORK_ORDER.md','STATUS.md','status/stages.tsv','scripts/diagnose_stage04_probe_settling_v1.py',
                 'reports/stage04/repair_admission_v1/authority.json'],'Record direct resource repair authority and stopped execution owners')
        with patch.object(sys,'argv',['diagnostic','--failed-attempt','.work/stage04_phylogeny_v2/analyses/primary196/iqtree/attempt_0001/iqtree3.command.json']):args=K.parse()
        before=C.windows_snapshot(ROOT)
        probe=K.bounded_wsl(args,[C.linux_path(args.host_env/'bin/python'),'-u',C.linux_path(args.linux_launcher),'--mode','resources'])
        start=time.monotonic()
        linux=json.loads(C.command(ROOT,probe,timeout=60))
        samples=[]
        for index in range(13):
            if index:time.sleep(5)
            samples.append({'seconds_since_probe_exit':time.monotonic()-start,'windows':C.windows_snapshot(ROOT)})
            print('ACTUAL_POST_PROBE '+str(samples[-1]['windows']['available_bytes']),flush=True)
        # Fresh inexpensive Linux evidence after settling; actual current meminfo and boot, no reuse of pre-probe values.
        fresh_command=['wsl','-d','Ubuntu','--','sh','-c','cat /proc/sys/kernel/random/boot_id; cat /proc/meminfo']
        fresh=C.command(HISTORY,fresh_command,timeout=30)
        post_fresh=C.windows_snapshot(ROOT)
        value={'utc':C.now(),'status':'MEASUREMENT_ONLY_NO_ADMISSION_OR_SCIENTIFIC_PASS','actual_pid':os.getpid(),
               'required_windows_bytes':4831838208,'required_linux_bytes':4294967296,'windows_before':before,
               'actual_probe_argv':probe,'linux_probe':linux,'post_probe_samples':samples,'actual_fresh_linux_argv':fresh_command,
               'fresh_linux_boot_and_meminfo':fresh,'windows_after_fresh_linux':post_fresh,'scientific_process_started':False}
        C.atomic(OUT/'settling_diagnostic.json',value)
        publish(['reports/stage04/repair_admission_v1/settling_diagnostic.json'],'Publish actual bounded WSL probe settling measurements')

if __name__=='__main__':main()
