"""Read hash-bound parent acceptance; does not launch or redeem anything."""
import json
import stage04_recovery_controller_v10 as P

if __name__=='__main__':
    proposal,review=P.acceptance()
    print(json.dumps({'status':'ALL_EXACT_PARENT_ADOPTION_HASHES_VERIFIED','production_task':proposal['production_task']['task_name']}))
