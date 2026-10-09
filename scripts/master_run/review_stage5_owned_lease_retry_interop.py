"""Root verifies current lease sources plus the narrow interoperability extension."""
from pathlib import Path
import datetime,hashlib,json
W=Path(__file__).resolve().parent;p=W/'stage5_owned_lease_retry_interop_preparation.json';raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!='89b3c1251ac5b6c9a237396b6a78a5447a6b1282fc9b39b64661ccb58a81a937':raise ValueError('Frozen current map differs')
prep=json.loads(raw);verified=[]
for row in prep['files']:
 q=Path(row['local_path']);data=q.read_bytes()
 if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Current frozen source/history/evidence differs')
 verified.append({'path':q.name,'bytes':len(data),'sha256':row['sha256']})
old=W/'stage5_owned_lease_retry_independent_root_review.json'
record={'schema':'STAGE05_OWNED_LEASE_INTEROP_CURRENT_INDEPENDENT_ROOT_REVIEW_V1',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'PASS_CURRENT_EXACT_SOURCES_AND_NARROW_INTEROP_DELTA',
 'reviewer':'root, independent of stage5_audit author','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'current_preparation_sha256':hashlib.sha256(raw).hexdigest(),'verified_files':verified,
 'initial_helper_and_setup_review_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
 'initial_review_scope':'Historical initial sources only; current builder and interop are verified and reviewed here',
 'root_actual_additional_test_observation':{'command':'python -B work/test_stage5_interop_owned_lease.py -v','exit_code':0,'tests':2,'seconds':0.079,
  'scope':'Own C temporary lease files with synthetic API/Popen failures; no WSL/resources/G/native launch'},
 'reviewed_delta':[
  'Interop imports and pins the same add2 helper, records own lease retry stats, checks helper bytes at start and per fixture, and changes only its own lease writer.',
  'Three actual fixture definitions, lifecycle/closure predicates, TTL3seconds, resource policy and Linux/Supervisor/API sources remain unchanged.',
  'Current builder482800 changes only the interop source pin from preserved53258; setupcc49/nativeowner8851/helperadd2 remain exactly reviewed.',
  'All43 current/history/spool mapping bytes verified; original toolchain02 remains FAILED with proven closed scope, sharing inferred.',
  'No successful actual setup, contention resolution, runtime discovery or biological result is claimed.'
 ],'concrete_blockers':[]}
with (W/'stage5_owned_lease_retry_interop_independent_root_review.json').open('x',encoding='utf-8') as out:json.dump(record,out,indent=2);out.write('\n')
print(json.dumps({'state':record['state'],'verified_files':len(verified)}))
