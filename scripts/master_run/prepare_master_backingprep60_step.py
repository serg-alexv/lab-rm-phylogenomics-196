"""Pin reviewed backing transport source packets only; no WSL/native effects."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',action='append',required=True);a=p.parse_args()
    name='master_backingprep60';extras=[]
    for item in a.packet:
        rel,pin=item.rsplit('=',1);q=(W/rel).resolve()
        assert q.is_relative_to(W) and hashlib.sha256(q.read_bytes()).hexdigest()==pin
        mapping=json.loads(q.read_bytes());assert mapping['state'].startswith('PASS_')
        for row in mapping['files']:
            path=Path(row.get('local_path',row.get('path'))).resolve();assert path.is_relative_to(W)
            data=path.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
            target=row.get('repository_path',row.get('suggested_repository_path'))
            assert isinstance(target,str) and not target.startswith('/') and '..' not in Path(target).parts
            extras.append(path.relative_to(W).as_posix()+'='+target)
        extras.append(rel+'=reports/master_run/20261009/preparation/'+q.parent.name+'_PUBLIC_MAPPING.json')
    for file in ['stage5_unc_backing_architecture01.md','stage5_unc_backing_architecture01.json','master_uncdiagnosis59_remote_readback.json']:
        extras.append(file+'=reports/master_run/20261009/postboot01/'+file)
    extras.append(Path(__file__).name+'=scripts/master_run/'+Path(__file__).name)
    assert len({x.split('=',1)[1] for x in extras})==len(extras)
    patch={'stage5_windows_backing_alias_current':'PASS_REVIEWED_SOURCE_ONLY; ACTUAL_BIDIRECTIONAL_GATE_AND_SCIENCE_NOT_RUN',
      'stage5_unc_current':'FAILED03_PRESERVED; BACKING04_BIDIRECTIONAL_QUALIFICATION_PENDING',
      'stage5_resource_wait_policy':'ORIGINAL_BUILDER_WAIT0_PRESERVED; REVIEWED_BACKING_BUILDER_EXPLICIT_WAIT1800_WITH_UNCHANGED_ADMISSION_THRESHOLDS',
      'stage5_current_stop_sha256':None}
    paragraph='Stage5 current execution: the exact read-only diagnostic passed with canonical UNC Access denied and the same116B ext4 backing sentinel readable by unchanged tiny_read. Separate reviewed sources select only that fixed backing UNC for Windows evidence transport; Linux canonical output, full detector method, runtime f64edf, native supervisor and reserves remain unchanged. A fresh bidirectional backing04 gate is still required before any detector. The new builder explicitly permits1800s guarded resource admission waiting; the original builder forced0s and the earlier memory assessment is corrected without rewriting it. Accepted Stage4 and original failed UNC03 are preserved. No detector, production curation, VM capture/splitting/restore or eviction has run.\n'
    for suffix,value in [('patch.json',patch),('extras.json',extras)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','0540bbd67274c6a2134eee238ef30acff505b137','--previous','master_uncdiagnosis59',
      '--phase','reviewed fixed backing UNC transport and explicit bounded wait; source only before actual qualification',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json'],check=True)
if __name__=='__main__':main()
