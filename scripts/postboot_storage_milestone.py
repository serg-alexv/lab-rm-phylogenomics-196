"""Publish independently verified copy/restart facts; no scientific launch."""
from pathlib import Path
import os, json
import stage04_controller as C
import production_resume as w
from workflow_publication import commit
R=Path(__file__).resolve().parents[1]
H=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
E=Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\referenced-chatgpt-conversation-this-is-an\outputs')
P=R/'reports/storage'
w.LOG=P/'postboot_continuation_commands.jsonl'

def main():
    with C.WorkflowLock(H/'.work/workflow.lock'):
        prior=C.reconcile(R)
        receipt=C.load(E/'WD_GOOGLE_DRIVE_COPY_VERIFICATION_20261008.json')
        C.check(receipt['status']=='PASS_SOURCE_TO_DRIVE_COPY_HASH_VERIFIED'
                and Path(receipt['source_root'])==H and Path(receipt['target_root'])==R
                and receipt['error_count']==0 and receipt['source_files_hash_and_size_verified']==52744,
                'Full verified directional copy gate required')
        manifest=Path(receipt['file_manifest']['path'])
        C.check(C.digest(manifest)==receipt['file_manifest']['sha256']
                and manifest.stat().st_size==receipt['file_manifest']['bytes'],'Copy source manifest changed')
        snapshot=C.windows_snapshot(R)
        w.js(P/'20261008_completed_copy_gate.json',receipt)
        update={'utc':w.now(),'status':'COPY_HASH_VERIFIED_NEW_WD_CONTINUATION_ACTIVE_V5_NOT_ADOPTED',
                'canonical_prior_commit':prior,'data_root':str(R),'historical_tools_runtime_root':str(H),
                'copy_receipt_sha256':C.digest(E/'WD_GOOGLE_DRIVE_COPY_VERIFICATION_20261008.json'),
                'copy_manifest_sha256':C.digest(manifest),'actual_milestone_command_pid':os.getpid(),
                'actual_windows_snapshot':snapshot,'scientific_inference_started':False,
                'stage04':'INCOMPLETE','stage05_stage06_stage07':'NOT_RUN',
                'remaining_migration_gate':'Actual G-to-WSL bootstrap and source/producer/checker integration before adoption',
                'native_workflow_lock':str(H/'.work/workflow.lock'),
                'private_events':'Remain at original C private runtime; not copied to Drive or GitHub',
                'usage_resets':'MANUAL_USER_ONLY; none consumed by continuation',
                'drive_durability':'Exact local size/hash gate only; Drive is streamed/cache-backed, remote synchronization not verified'}
        w.js(P/'20261008_active_continuation.json',update)
        migration=C.load(R/'status/storage_migration.json');migration.update(latest_continuation=update)
        w.js(R/'status/storage_migration.json',migration)
        w.atomic(P/'20261008_active_continuation.md',
            ('# Verified storage recovery and active continuation\n\n'
             'Canonical main was reconciled before writing. The completed parent copy gate independently read52744 included source files (9852158003bytes) and verified their exact sizes/hashes on G. Two previously verified target-only ZIPs were retained. No cloud synchronization or independent physical capacity is inferred from Drive.\n\n'
             'The new WD continuation runs from G. Historical receipts, pinned tool prefix, native byte lock and private raw session logs remain at their original physical C locations. Old scientific stages and argv are preserved. WSL capacity/cleanup evidence already published by the parent remains valid; no additional cleanup/restart was performed.\n\n'
             'V5 candidates passed independent synthetic/path reviews, but actual G-to-WSL bootstrap/source integration and root adoption are pending. No native inference or downstream biological work has started. Actual resource snapshot and provenance are in20261008_active_continuation.json. Resource gates and both detectors remain mandatory. Usage resets are manual only.\n').encode())
        w.status('4_phylogeny','PREPARING_V5_EXPLICIT_STORAGE_MIGRATION','PASS_ALIGNMENTS_PHYLOGENY_INCOMPLETE',
                 'STAGE04A_AND_STAGE04B_UPLOAD_VERIFIED_FULL_STAGE04_PENDING',
                 'Full Drive copy/hash gate passed for52744 included files. New WD continuation active from G; historical C tools/receipts/native lock preserved. Canonical main reconciled. Actual V5 bridge/source integration and adoption pending; no new ML or downstream biological result claimed.')
        paths=['scripts/postboot_storage_milestone.py','reports/storage/20261008_completed_copy_gate.json',
               'reports/storage/20261008_active_continuation.json','reports/storage/20261008_active_continuation.md',
               'status/storage_migration.json','STATUS.md','status/stages.tsv']
        head=commit(paths,'Verify completed Drive copy and active WD continuation before migration adoption')
        C.command(R,['git','fetch','origin','main'])
        C.check(C.command(R,['git','rev-parse','origin/main'])==head,'Remote milestone differs')
        import subprocess,hashlib
        for name in paths:
            data=subprocess.run(['git','show','origin/main:'+name],cwd=R,capture_output=True,check=True).stdout
            C.check(hashlib.sha256(data).hexdigest()==C.digest(R/name),'Remote milestone bytes differ: '+name)
        print('VERIFIED_STORAGE_CONTINUATION_MILESTONE '+head,flush=True)

if __name__=='__main__':main()
