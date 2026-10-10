"""Prepare exact fresh gate pins and explicit capacity budgets; no execution."""
from pathlib import Path
import argparse,hashlib,json,re
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--unc-spool',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    assert re.fullmatch(r'stage5_unc_bind_actual_postiq_[0-9]+',a.unc_spool)
    assert re.fullmatch(r'stage5_actual_request_[A-Za-z0-9_]+\.json',a.output)
    request=json.loads((W/'stage5_actual_config_request.template.json').read_bytes())
    for key,name in [('runtime_manifest','stage5_runtime_actual_postiq_06.json'),('storage_proof','stage5_storage_actual_postiq_05.json')]:
        q=W/name;request[key]={'path':str(q),'sha256':sha(q)}
    spools={'toolchain':'stage5_setup_toolchain_actual_postiq_05','runtime':'stage5_setup_runtime_actual_postiq_06',
            'interop':'stage5_interop_actual_postiq_04','storage':'stage5_setup_storage_actual_postiq_05',
            'drivefs':'stage5_setup_drivefs_actual_postiq_03','unc':a.unc_spool}
    for kind,name in spools.items():
        q=W/name/'result.json';result=json.loads(q.read_bytes())
        assert result['state'].startswith('PASS_'),kind+' gate has not passed'
        request['gates'][kind]={'path':str(q),'sha256':sha(q),'unlock_sha256':sha(q.parent/'lock_released.json')}
    request['native_resource_bytes']={
        'incremental_windows_requirement_bytes':1610612736,
        'commit_requirement_bytes':3221225472,
        'linux_job_requirement_bytes':1610612736,
        'process_address_space_limit_bytes':4294967296,
        'sampled_rss_stop_bytes':1342177280}
    request['resource_basis']=(
        'Explicit conservative capacity allocation for the first complete approved genome GCF_000009425.1, '
        'using the unchanged full PADLOC5027 and complete DefenseFinder native method, two threads and one serial owner. '
        'These values are not measured detector requirements: allocate 1.5GiB incremental Windows and Linux job memory, '
        'retain the existing 1.5GiB Windows and 1GiB Linux reserves, require 3GiB Windows commit headroom, '
        'stop at sampled aggregate descendant RSS 1.25GiB and cap each process address space at 4GiB. '
        'Keep the WSL global 4GB memory setting. Fresh admission is required before native commands; insufficient capacity '
        'defers execution, and an exceeded limit is a preserved execution failure, never biological absence. '
        'Measure elapsed time, CPU and descendant RSS on this full genome before increasing concurrency or changing capacity. '
        'Accepted Stage4 and the approved196 panel are unchanged.')
    q=W/a.output
    with q.open('x',encoding='utf-8',newline='\n') as f:json.dump(request,f,indent=2);f.write('\n')
    print(json.dumps({'request':str(q),'sha256':sha(q),'scientific_execution':'NOT_RUN'}))
if __name__=='__main__':main()
