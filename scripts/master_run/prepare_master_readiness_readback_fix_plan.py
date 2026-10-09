"""Preserve the first remote-reader failure and exact original-sidecar correction."""
from pathlib import Path
import argparse, hashlib, json

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); work=Path(__file__).resolve().parent; rows=[]
    pairs={
        'verify_stage5_source_readiness_remote.py':'scripts/master_run/verify_stage5_source_readiness_remote.py',
        'verify_stage5_source_readiness_remote_attempt01.py':'scripts/master_run/verify_stage5_source_readiness_remote_attempt01.py',
        'prepare_master_readiness_assets_plan.py':'scripts/master_run/prepare_master_readiness_assets_plan.py',
        Path(__file__).name:'scripts/master_run/'+Path(__file__).name,
        'audit_old_checkout_git_metadata.py':'scripts/master_run/audit_old_checkout_git_metadata.py',
        'old_checkout_git_preservation_metadata.json':'reports/master_run/20261009/cleanup/old_checkout_git/METADATA.json',
        'old_checkout_git_preservation_summary.json':'reports/master_run/20261009/cleanup/old_checkout_git/SUMMARY.json',
        'master_readiness_assets_upload_plan.json':'reports/master_run/20261009/preparation/source_readiness01/UPLOAD_PLAN.json',
        'master_readiness_assets_upload_receipt.json':'reports/master_run/20261009/preparation/source_readiness01/UPLOAD_RECEIPT.json',
        'stage5_source_readiness01_readback_20261009T203136Z_1299975c/receipt.json':'reports/master_run/20261009/preparation/source_readiness01/REMOTE_ATTEMPT01_FAILURE.json',
        'stage5_source_readiness_remote_source_review.json':'reports/master_run/20261009/preparation/source_readiness01/REMOTE_FIX_REVIEW.json',
        'master_source_ready_git_objects.json':'reports/master_run/20261009/publication/SOURCE_READY_GIT_OBJECTS.json',
        'master_source_ready_remote_readback.json':'reports/master_run/20261009/publication/SOURCE_READY_REMOTE_READBACK.json',
    }
    for name,target in pairs.items():
        path=work/name; raw=path.read_bytes()
        assert 0<len(raw)<5*1024*1024
        rows.append({'local_absolute_path':str(path),'target':target,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump({'expected_head':a.expected_head,
            'message':'Bind original CRLF readiness sidecar without asset replacement; preserve failed check and old-checkout metadata',
            'files':rows},stream,indent=2);stream.write('\n')
    print(json.dumps({'files':len(rows),'bytes':sum(r['bytes'] for r in rows)}))

if __name__=='__main__':main()
