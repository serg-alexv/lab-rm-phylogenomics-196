"""Build exact completed setup-step publication; no scientific/ref mutation."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('name','head','previous','phase','spool','review','previous-readback'):p.add_argument('--'+k,required=True)
    p.add_argument('--extra',action='append',default=[])
    p.add_argument('--packet');p.add_argument('--packet-sha256');a=p.parse_args()
    review=json.loads((W/a.review).read_bytes());assert review['state'].startswith('PASS_')
    result=json.loads((W/a.spool/'result.json').read_bytes());assert result['state'].startswith('PASS_')
    root=json.loads((W/'master_newboot_reconciliation_actual01.json').read_bytes())
    patch={'stage5_latest_postboot_gate':{'spool':a.spool,'state':result['state'],
      'independent_review_sha256':hashlib.sha256((W/a.review).read_bytes()).hexdigest()},
      'stage5_current_stop_sha256':None}
    if review.get('detail',{}).get('linux_boot_id'):patch['stage5_current_linux_boot_id']=review['detail']['linux_boot_id']
    if result.get('step')=='storage':
        patch['stage5_storage_current']='PASS_CURRENT_BOOT_EXACT_EXT4_BIND; '+a.spool
    if result.get('step')=='drivefs':
        patch['stage5_drivefs_current']='PASS_CURRENT_BOOT_OWNED_FILESYSTEM_WORKER_AND_WINDOWS_READBACK; '+a.spool
    if result.get('state')=='PASS_NONSCIENTIFIC_EXACT_EXT4_BIND_UNC_VISIBILITY':
        patch['stage5_unc_current']='PASS_CURRENT_BOOT_EXACT_BIND_NATIVE_WINDOWS_UNC_AND_CLEANUP; '+a.spool
    (W/(a.name+'_patch.json')).write_text(json.dumps(patch,indent=2)+'\n')
    extras=[a.review+'=reports/master_run/20261009/postboot01/'+Path(a.review).name,
      a.previous_readback+'=reports/master_run/20261009/publication/'+Path(a.previous_readback).name,
      Path(__file__).name+'=scripts/master_run/'+Path(__file__).name]+a.extra
    if a.packet:
        mapping=W/a.packet;assert hashlib.sha256(mapping.read_bytes()).hexdigest()==a.packet_sha256
        for row in json.loads(mapping.read_bytes())['files']:
            q=Path(row.get('path',row.get('local_path'))).resolve()
            assert q.is_relative_to(W) and q.stat().st_size==row['bytes'] and hashlib.sha256(q.read_bytes()).hexdigest()==row['sha256']
            extras.append(q.relative_to(W).as_posix()+'='+row.get('suggested_repository_path',row.get('suggested_remote_path')))
        extras.append(a.packet+'=reports/master_run/20261009/preparation/'+Path(a.packet).parent.name+'_PUBLIC_MAPPING.json')
    (W/(a.name+'_extras.json')).write_text(json.dumps(extras,indent=2)+'\n')
    paragraph='Stage5 current execution: '+a.phase+'. Actual setup result '+result['state']+' and independent source/closure/byte joins PASS. The new Windows boot is verified, old STOP reconciled and original failed worker evidence preserved; all18legacy tasks remain disabled. Remaining setup gates precede the first full-method approved genome. Detector execution and production curation remain NOT_RUN. Accepted Stage4 is unchanged. Installed-runtime/VM capture and cold restoration are pending; the host is not wipe-ready.\n'
    (W/(a.name+'_paragraph.md')).write_text(paragraph)
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',a.name,'--head',a.head,
      '--previous',a.previous,'--phase',a.phase,'--paragraph-file',a.name+'_paragraph.md',
      '--patch-file',a.name+'_patch.json','--extras-file',a.name+'_extras.json','--spool',a.spool],check=True)
if __name__=='__main__':main()
