"""Read-only first-owner wait snapshot and reviewed source publication plan."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
W=Path(__file__).resolve().parent
N=Path(r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1\GCF_000009425.1')
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',action='append',required=True);a=p.parse_args()
    name='master_firstwait63';output=W/'stage5_first_owner_resource_observation01';output.mkdir(exist_ok=False)
    extras=[];manifest=[]
    sources={'native_latest_admission.json':N/'transactions/attempt_0001/latest_admission.json',
      'linux_meminfo.txt':Path(r'\\wsl.localhost\Ubuntu\proc\meminfo'),
      'linux_boot_id.txt':Path(r'\\wsl.localhost\Ubuntu\proc\sys\kernel\random\boot_id'),
      'windows_owner.json':W/'stage5_owner_GCF_000009425_1_backing_01/owner.json',
      'windows_launch.json':W/'stage5_owner_GCF_000009425_1_backing_01/GCF_000009425.1.launch.json'}
    for target,source in sources.items():
        raw=source.read_bytes();assert len(raw)<=65536
        with (output/target).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        manifest.append({'source':str(source),'file':target,'bytes':len(raw),'sha256':sha(raw)})
    admission=json.loads((output/'native_latest_admission.json').read_bytes())
    assert admission['admitted'] is False
    assert (output/'linux_boot_id.txt').read_text().strip()=='f0ffcebc-4901-479d-9559-89d45e9cfa38'
    value={'schema':'STAGE05_ACTIVE_FIRST_OWNER_RESOURCE_OBSERVATION_V1',
      'state':'OBSERVED_INITIAL_RESOURCE_ADMISSION_WAIT_ONLY','observation_utc':admission['utc'],
      'linux_available_bytes':admission['linux_available_bytes'],
      'linux_required_bytes':admission['policy']['linux_job_requirement_bytes']+admission['policy']['linux_reserve_bytes'],
      'native_execution_directory_observed':(N/'execution').exists(),
      'scope_terminal_claim':False,'owned_closure_claim':False,'biological_result_claim':'NONE',
      'files':manifest,'capture_method':'Read existing exact Windows/UNC files only; no WSL process or workflow lock/effect'}
    assert value['native_execution_directory_observed'] is False
    (output/'observation.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    for file in output.iterdir():extras.append(file.relative_to(W).as_posix()+'=reports/master_run/20261009/first_owner_resource_observation01/'+file.name)
    for item in a.packet:
        relative,pin=item.rsplit('=',1);q=(W/relative).resolve();raw=q.read_bytes()
        assert q.is_relative_to(W) and sha(raw)==pin
        packet=json.loads(raw);assert packet['state'].startswith('PASS_')
        for row in packet['files']:
            path=Path(row.get('local_path',row.get('path'))).resolve();data=path.read_bytes()
            assert path.is_relative_to(W) and len(data)==row['bytes'] and sha(data)==row['sha256']
            target=row.get('repository_path',row.get('suggested_repository_path'))
            assert target and '..' not in Path(target).parts
            extras.append(path.relative_to(W).as_posix()+'='+target)
        extras.append(relative+'=reports/master_run/20261009/preparation/'+q.parent.name+'_PUBLIC_MAPPING.json')
    extras += [Path(__file__).name+'=scripts/master_run/'+Path(__file__).name,
      'master_firstconfig62_remote_readback.json=reports/master_run/20261009/publication/master_firstconfig62_remote_readback.json']
    assert len({x.split('=',1)[1] for x in extras})==len(extras)
    patch={'stage5_first_full_method_genome':'OWNER_ACTIVE_INITIAL_RESOURCE_WAIT; NO_NATIVE_EXECUTION_DIRECTORY_AT_OBSERVATION',
      'stage5_first_genome_resource_observation':value,
      'stage5_unc03_cleanup_source':'PASS_CORRECTED_V2_SOURCE_ONLY; ACTUAL_EXACT_CLEANUP_NOT_RUN',
      'stage5_raw_archive_owner_source':'PASS_CHECKED_UNLOCK_AND_EXACT_OWNED_STOP_V2_SOURCE_ONLY; ACTUAL_ARCHIVE_NOT_RUN'}
    paragraph='Stage5 current execution: the first GCF_000009425.1 owner is active under the original lock but its initial resource guard has not admitted a detector. The exact observed Linux MemAvailable is below the2.5GiB threshold; Windows RAM/commit/disk pass. No native execution directory existed at the read-only observation, no biological result or closure is claimed, and current resource remediation is under review. Corrected exact failed03 sentinel cleanup and raw archive owner sources passed focused independent review only; their actual effects are pending until the scientific scope is closed. Accepted Stage4 is unchanged. VM capture/splitting/restore remain pending; the public repository must contain reviewed project/runtime material only. The host is not wipe-ready.\n'
    for suffix,content in [('patch.json',patch),('extras.json',extras)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(content,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','8458cfca75b0d43404e2fd7e87237c228e0029b0','--previous','master_firstconfig62',
      '--phase','first owner observed waiting initial Linux resource admission; reviewed cleanup and archive sources only',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json'],check=True)
if __name__=='__main__':main()
