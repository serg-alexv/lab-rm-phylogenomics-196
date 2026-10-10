"""Separate C-only capacity booking revision; no native/WSL/lock action."""
from pathlib import Path
import argparse,copy,hashlib,json,os
W=Path(__file__).resolve().parent
BASE='stage5_actual_request_backing_01.json'
BASE_SHA='96fc9e6a9893fb56122f701378aa49eb3f50773b797d6cdf4c9130548be3cb44'
OUTPUT='stage5_actual_request_backing_capacity_02.json'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepare',action='store_true');a=p.parse_args()
    if not a.prepare:
        print(json.dumps({'state':'PREPARED_NOT_RUN','Linux_booking_bytes':1476395008,'native_actions':0}));return
    raw=(W/BASE).read_bytes();assert hashlib.sha256(raw).hexdigest()==BASE_SHA
    before=json.loads(raw);value=copy.deepcopy(before)
    assert value['native_resource_bytes']['linux_job_requirement_bytes']==1610612736
    value['native_resource_bytes']['linux_job_requirement_bytes']=1476395008
    old='allocate 1.5GiB incremental Windows and Linux job memory'
    new='allocate 1.5GiB incremental Windows and 1.375GiB Linux job memory'
    assert value['resource_basis'].count(old)==1
    value['resource_basis']=value['resource_basis'].replace(old,new)+(
      ' Separate capacity revision02 follows observed guest MemAvailable about2.42GiB below the original2.5GiB admission requirement. '
      'This is an explicit unmeasured capacity booking above the unchanged1.25GiB sampled aggregate RSS stop, '
      'with the unchanged1GiB Linux reserve. Fresh repeated admission remains mandatory; no further booking reduction '
      'is planned if preparation or execution does not fit. A guest-capacity change with fresh boot gates is the bounded fallback.')
    assert {k:v for k,v in value.items() if k not in ('native_resource_bytes','resource_basis')}=={
      k:v for k,v in before.items() if k not in ('native_resource_bytes','resource_basis')}
    assert {k:v for k,v in value['native_resource_bytes'].items() if k!='linux_job_requirement_bytes'}=={
      k:v for k,v in before['native_resource_bytes'].items() if k!='linux_job_requirement_bytes'}
    output=W/OUTPUT;assert not output.exists()
    with output.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    print(json.dumps({'state':'PREPARED_EXPLICIT_CAPACITY_REVISION_ONLY','path':str(output),
      'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'config_build_and_actual_native_admission':'PENDING_AFTER_WAITING01_CLOSURE'}))
if __name__=='__main__':main()
