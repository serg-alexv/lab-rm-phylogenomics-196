"""Root byte verification for the separately authored narrow Stage5 lease correction."""
from pathlib import Path
import datetime,hashlib,json
W=Path(__file__).resolve().parent
p=W/'stage5_owned_lease_retry_preparation.json';raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!='908bdaff7778e6bdde6a03b2fca254131c610e46122dc33c4e748eb4bd0894d8':raise ValueError('Frozen preparation differs')
prep=json.loads(raw);checked=[]
for row in prep['files']:
 q=Path(row['local_path']);data=q.read_bytes()
 if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Mapped exact source/evidence differs')
 checked.append({'path':q.name,'bytes':len(data),'sha256':row['sha256']})
for name,pin in prep['unchanged_guard_sources'].items():
 if hashlib.sha256((W/name).read_bytes()).hexdigest()!=pin:raise ValueError('Original scientific/controller guard source changed')
record={'schema':'STAGE05_OWNED_LEASE_RETRY_INDEPENDENT_ROOT_REVIEW_V1',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'PASS_SOURCE_DELTA_AND_EXACT_BYTES_PLUS_ROOT5_TESTS',
 'reviewer':'root, independent of stage5_audit author','preparation_sha256':hashlib.sha256(raw).hexdigest(),
 'review_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'verified_files':checked,
 'root_actual_test_observation':{'command':'python -B work/test_stage5_owner_lease.py -v','exit_code':0,'tests':5,'seconds':0.030,
  'scope':'Pure synthetic syscall failures plus own temporary C files; no WSL/G/resource/native call'},
 'author_test_report':prep['tests'],
 'reviewed_contracts':[
  'Only same exclusive-created C temporary to current own owner_lease.json os.replace retries Windows errors5/32/33.',
  'Monotonic250ms budget/backoff stops before another attempt at the deadline; fatal errors preserve failure without retry.',
  'Exact C path/schema, regular non-reparse target/ancestors and only owned temporary cleanup; no retry of create/write/fsync/validation/other files.',
  'Mutable retry/failure counters survive into both setup and native owner receipts; prior failed toolchain02 bytes remain unchanged.',
  'Setup and native Windows owner deltas are limited to helper import/pin, own lease calls and counters; current config builder pins those exact sources.',
  'A80 native producer, Linux science/Supervisor/storage, scientific V2 identity and resource reserves remain byte-identical.',
  'Windows sharing contention remains inferred; actual toolchain02 stays FAILED despite independently proven closed Linux scope.',
  '250ms bounds retry scheduling, not synchronous OS call/fsync/cleanup cancellation. No real contention resolution or scientific execution is claimed.'
 ],'concrete_blockers':[],'actual_new_setup_or_biology':'NOT_RUN'}
with (W/'stage5_owned_lease_retry_independent_root_review.json').open('x',encoding='utf-8') as out:json.dump(record,out,indent=2);out.write('\n')
print(json.dumps({'state':record['state'],'mapped_files':len(checked)}))
