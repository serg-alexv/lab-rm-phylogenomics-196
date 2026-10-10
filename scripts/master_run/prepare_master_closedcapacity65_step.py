"""Publish closed wait, failed control, capacity02 config and reviewed fixture source."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    name='master_closedcapacity65'
    expected={
      'stage5_actual_backing_capacity_02.json':'4c2d9812afd2dbabaa6ba3177395dee17511946966fb3b7491f579cfd3602d63',
      'stage5_cancel_control_failed_actual01_independent_review.json':'6fdb48bd610dd68046bd313b9acd254630ebc35a38d12a345a45f97c2d636f9b',
      'stage05_disposable_cold_fixture_source_preparation01/PUBLIC_MAPPING.json':'07448cc7b5988f3efcdffd458af40df4203450950311fdac207a49f702245f50'}
    for n,p in expected.items():assert digest(W/n)==p
    extras=[]
    for n in ('stage5_first_waiting01_closed_independent_review.json','stage5_first_backing_capacity02_actual_config_independent_review01.json'):
        assert json.loads((W/n).read_bytes())['state'].startswith('PASS_')
    for n in ('stage5_actual_backing_capacity_02.json','stage5_actual_backing_capacity_02_build_receipt.json','stage5_first_waiting01_closed_independent_review.json','stage5_first_backing_capacity02_actual_config_independent_review01.json','stage5_cancel_control_failed_actual01_independent_review.json'):
        extras.append(n+'=reports/master_run/20261009/closed_capacity02/'+n)
    for n in ('copy_stage5_waiting01_closed_evidence.py','review_stage5_first_waiting01_closed.py','review_stage5_first_backing_capacity02_actual_config01.py','review_stage5_cancel_control_failed_actual01.py',Path(__file__).name):
        extras.append(n+'=scripts/master_run/'+n)
    extras.append('master_capacityprep64_remote_readback.json=reports/master_run/20261009/publication/master_capacityprep64_remote_readback.json')
    for rel in ('stage5_waiting01_closed_native_copy',):
        for p in sorted((W/rel).rglob('*')):
            if p.is_file():extras.append(p.relative_to(W).as_posix()+'=reports/master_run/20261009/'+p.relative_to(W).as_posix())
    mapping=W/'stage05_disposable_cold_fixture_source_preparation01/PUBLIC_MAPPING.json'
    for r in json.loads(mapping.read_bytes())['files']:
        p=Path(r.get('local_path',r.get('path'))).resolve();assert p.is_relative_to(W) and digest(p)==r['sha256'] and p.stat().st_size==r['bytes']
        target=r.get('repository_path',r.get('suggested_repository_path'));assert target
        extras.append(p.relative_to(W).as_posix()+'='+target)
    extras.append(mapping.relative_to(W).as_posix()+'=reports/master_run/20261009/preparation/disposable_cold_fixture_PUBLIC_MAPPING.json')
    patch={'stage5_waiting01':'DEFERRED_RESOURCE_CLOSED_NO_NATIVE_NO_SCIENTIFIC_IDENTITY_ORIGINAL_UNLOCKED',
      'stage5_waiting01_cancellation':'FAILED_CONTROL_EXIT1_WINDOWS_SCOPE_CLOSED_NO_ESTABLISHED_LINUX_SIGNAL_RECEIPT_NO_RETRY',
      'stage5_first_full_method_genome':'CAPACITY02_ACTUAL_CONFIG_REVIEWED_AND_WINDOWS_ADMISSION_PASSED; NATIVE_PENDING',
      'stage5_disposable_cold_fixture':'PASS_SOURCE_ONLY_ACTUAL_NOT_RUN',
      'stage5_unc03_exact_cleanup':'ACTUAL_TWO_OBJECT_CLEANUP_PASS; PUBLIC_BACKUP_AND_PEER_PENDING_NEXT_STEP'}
    paragraph='Stage5 current execution: waiting01 naturally expired after1800s with DEFERRED_RESOURCE, retained WSLexit75, explicit no-native/closure proof, null scientific identity and original workflow unlock. The attempted cancellation control failed with WSLexit1 and a closed empty Windows Job; no established Linux signal receipt exists and no retry was made. The separate capacity02 config changes only Linux capacity booking to1.375GiB while retaining sampledRSSstop1.25GiB, Linuxreserve1GiB, all Windows budgets, full methods and six qualified current-boot gates. It passed actual Windows build admission and independent joins; native execution remains pending. Reviewed disposable64MiB cold-fixture sources are published as NOT_RUN. Failed03 exact sentinel cleanup has completed with its116B backup, retained workerexit0/emptyJob/originalunlock; its complete backup and independent actual review follow in the next step. Accepted Stage4 is unchanged;196-genome raw, curation, final figures and VM recovery are incomplete.\n'
    for suffix,value in [('patch.json',patch),('extras.json',extras)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,'--head','bd7cc38fdc494a5e00f8381b669e59df6ea5edec','--previous','master_capacityprep64','--phase','Close initial resource wait and publish reviewed capacity02 actual configuration','--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json','--spool','stage5_owner_GCF_000009425_1_backing_01','--spool','stage5_cancel_exact_waiting_windows_01'],check=True)
if __name__=='__main__':main()
