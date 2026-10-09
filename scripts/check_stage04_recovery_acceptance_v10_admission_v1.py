"""Read hash-bound parent acceptance; does not launch or redeem anything."""
import argparse,json
from pathlib import Path
import stage04_controller as C
import stage04_recovery_controller_v10_admission_v1 as P

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--observer-request',required=True);args=parser.parse_args()
    proposal,review=P.acceptance()
    for supplied,key in [(args.request,'production_task'),(args.observer_request,'production_readonly_observer_task')]:
        expected=proposal[key];path=Path(supplied)
        C.check(path==Path(expected['runtime'])/'task_request.json' and C.load(path)==expected,'Caller supplied task request is not the accepted exact role/request')
        C.check('historical:'+path.relative_to(P.S.HISTORY).as_posix() in proposal['required_review_artifacts'],'Supplied request bytes are not in accepted artifact map')
    print(json.dumps({'status':'ALL_EXACT_PARENT_ADOPTION_HASHES_VERIFIED','production_task':proposal['production_task']['task_name']}))
