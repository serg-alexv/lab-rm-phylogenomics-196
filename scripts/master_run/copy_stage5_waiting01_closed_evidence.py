"""Read-only exact native receipt snapshot after retained owner termination."""
from pathlib import Path
import datetime,hashlib,json
W=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    owner=W/'stage5_owner_GCF_000009425_1_backing_01'
    result=json.loads((owner/'result.json').read_bytes())
    assert result['state']=='DEFERRED_RESOURCE'
    exit=result['genome_results'][0]
    assert exit['actual_wsl_client_exit']['exited'] and exit['actual_wsl_client_exit']['exit_code']==75
    assert (owner/'lock_released.json').exists()
    root=Path(r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1\GCF_000009425.1')
    out=W/'stage5_waiting01_closed_native_copy';out.mkdir()
    members=sorted(p.relative_to(root).as_posix() for p in root.rglob('*'))
    assert not any('execution' in p or 'inventory' in p for p in members)
    rows={}
    for relative in ('status.json','transactions/attempt_0001/status.json','transactions/attempt_0001/latest_admission.json','transactions/attempt_0001/initial_owner_lease.json','transactions/attempt_0001/work_storage_proof.json'):
        raw=(root/relative).read_bytes();dest=out/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as stream:stream.write(raw)
        assert dest.read_bytes()==raw
        rows[relative]={'bytes':len(raw),'sha256':sha(raw)}
    status=json.loads((out/'status.json').read_bytes())
    assert sha((out/'status.json').read_bytes())==exit['status_sha256']
    assert status['state']=='DEFERRED_RESOURCE' and status['owned_closure_proven'] is True and status['no_native_launch_in_this_invocation'] is True
    assert status['scientific_identity'] is None
    value={'state':'PASS_EXACT_C_COPY_OF_CLOSED_INITIAL_RESOURCE_WAIT','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':sha(Path(__file__).read_bytes()),'members':members,'files':rows,'owner_result_sha256':sha((owner/'result.json').read_bytes()),'no_execution_or_inventory_paths_observed':True}
    with (out/'snapshot.json').open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps(value))
if __name__=='__main__':main()
