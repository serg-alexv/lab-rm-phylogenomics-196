"""Root binds already authorized, recoverable 5,542-directory-only cleanup."""
from pathlib import Path
import datetime,hashlib,json

work=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
proof=work/'master_recovery_verified04_remote_readback.json'
receipt=json.loads(proof.read_bytes())
assert receipt['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED'
assert receipt['expected_commit']==receipt['final_remote_main']=='eb724eb1a88ebd691face390d34d392ef2a0393e'
source=work/'prune_old_scientific_directories.py'
source_sha='9b64d17bb2612ce35051b87d77863709d875c1f910865fd6a4db2f6ddd265381'
assert digest(source)==source_sha
assert any(r['path']=='scripts/master_run/'+source.name and r['sha256']==source_sha
           and r['actual_remote_bytes_read'] for r in receipt['files'])
for name,pin in {
 'directory_handle_fixture_20261009T211310Z_843dbf82.json':'eebac12d62403b273713ee0f4aaad17955a4c6b7d33631e63ee1f86dc4e47ba1',
 'directory_handle_pruner_corrected_independent_review.json':'c0bc38628a140885211a397af9e23bbe10f9f432b2c682c13d44c03cd1d1b20b',
 'master_old_scientific_emptydirs_proposed_02.json':'be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5',
 'old_scientific_emptydirs01_readback_20261009T205057Z_9c38bcce/receipt.json':'e71b02889d5443017ef5ab8be206b1fc4e5f9f81c3de14c602eeaeef70c68063',
}.items():assert digest(work/name)==pin,name
authority={'schema':'MASTER_DIRECTORY_HANDLE_PRUNE_ROOT_AUTHORITY_V1',
 'execution_authorized':True,'root_only':True,'source_sha256':source_sha,
 'plan_sha256':'be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5',
 'fresh_remote_proof_sha256':'e71b02889d5443017ef5ab8be206b1fc4e5f9f81c3de14c602eeaeef70c68063',
 'deadline_seconds':900,'source_fixture_independent_review_and_publication_complete':True}
out=work/'master_directory_prune_root_authority01.json'
with out.open('x',encoding='utf-8') as stream:json.dump(authority,stream,indent=2);stream.write('\n')
review={'schema':'MASTER_DIRECTORY_ROOT_REVIEW_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'state':'ROOT_EXACT_SCOPE_AUTHORIZED_PRODUCTION_NOT_RUN',
 'authorization_basis':'Direct user authorization for recoverable obsolete project cleanup; no expanded scope',
 'proposed_directories':5542,'scope_roots':7,'held_directories':6,
 'recovery':'Exact metadata archive independently fresh-remote verified before any pruning',
 'source_publication_commit':receipt['expected_commit'],'source_publication_readback_sha256':digest(proof),
 'authority_sha256':digest(out),'root_source_review':'Read final source and methods; exact retained-directory-handle disposition, kernel nonempty veto, no recursive/path/file deletion; exact source/owner/protected-file/deadline guards',
 'actual_fixture_cases_passed':9,'first_failed_fixture_and_source':'PRESERVED',
 'workflow_lock':'No acquisition, replacement or mutation authorized',
 'protected':'Live inference/code/config/inputs, six dirty G files, installed toolchain and vendor fragment remain protected',
 'required_after_execution':'Independent actual absence/journal/protected-identity verification and remote evidence publication',
 'native_jobs_or_wsl_starts_authorized':0,'host_wipe_authorized':False}
review_path=work/'master_directory_prune_root_review01.json'
with review_path.open('x',encoding='utf-8') as stream:json.dump(review,stream,indent=2);stream.write('\n')
files=[]
for path,target in [(Path(__file__),'scripts/master_run/'+Path(__file__).name),
 (out,'reports/master_run/20261009/cleanup/emptydirs_prune01/ROOT_AUTHORITY.json'),
 (review_path,'reports/master_run/20261009/cleanup/emptydirs_prune01/ROOT_REVIEW.json'),
 (proof,'reports/master_run/20261009/publication/RECOVERY_VERIFIED04_REMOTE_READBACK.json'),
 (work/'master_recovery_verified04_git_objects.json','reports/master_run/20261009/publication/RECOVERY_VERIFIED04_GIT_OBJECTS.json')]:
 files.append({'local_absolute_path':str(path),'target':target,'bytes':path.stat().st_size,'sha256':digest(path)})
plan=work/'master_directory_authority01_git_plan.json'
with plan.open('x',encoding='utf-8') as stream:
 json.dump({'expected_head':receipt['expected_commit'],'message':'Authorize exact recovered empty-directory cleanup after actual Windows fixtures and remote source readback','files':files},stream,indent=2);stream.write('\n')
print(json.dumps({'authority_sha256':digest(out),'files':len(files)}))
