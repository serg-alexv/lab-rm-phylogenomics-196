"""Native Windows ZIP readback and exact failure-byte publication bindings."""
from pathlib import Path
import json,sys
import stage04_controller as C
import production_resume as w
from workflow_publication import commit
R=Path(__file__).resolve().parents[1]
P=R/'reports/stage04b'
w.LOG=P/'windows_verification_commands.jsonl'
with C.WorkflowLock(R/'.work/workflow.lock'):
 C.reconcile(R)
 receipt=C.load(P/'publication_receipt.json')
 C.check(receipt['status']=='UPLOAD_VERIFIED' and len(receipt['assets'])==1,'Verified Stage04b readback required')
 asset=receipt['assets'][0]
 C.check(all(asset[k] is True for k in ('download_readback_verified','all_zip_member_hashes_verified','sidecar_readback_verified')),'Incomplete published bytes')
 proof_path=P/'windows_portability_check.json'
 if not proof_path.exists():
  argv=['pwsh','-NoProfile','-File','scripts/validate_windows_zip.ps1',
   '-ZipPath','release_staging/stage04b/readback/'+asset['asset_name'],'-ExpectedSha256',asset['sha256'],
   '-Destination','.work/stage04b_windows_evidence_v1']
  proof=json.loads(w.run(argv,timeout=60));proof.update(actual_argv=argv,actual_exit_code=0,publication_payload_commit=receipt['payload_commit'])
  C.check(proof['status']=='PASS_NATIVE_WINDOWS_EXTRACTION_AND_ALL_MEMBER_HASHES'
   and proof['payload_members_hash_verified']==asset['payload_members'],'Native Windows member extraction check failed')
  w.js(proof_path,proof)
 evidence=C.load(P/'failure_evidence_validation.json')
 base=R/'.work/stage04_inference_v3'
 state=C.load(R/'.work/stage04_inference_controller_v3/state.json')
 phase=R/state['current']['receipt_directory']
 native=base/'analyses/primary196/iqtree/attempt_0001'
 bindings={'failed_native_attempt_sha256':C.digest(native/'iqtree3.command.json'),
  'failed_native_stderr_sha256':C.digest(native/'iqtree3.stderr.txt'),
  'previous_inference_freeze_sha256':C.digest(base/'inference_freeze.json'),
  'failed_phase_exit_sha256':C.digest(phase/'linux_exit_receipt.json'),
  'failure_evidence_validation_sha256':C.digest(P/'failure_evidence_validation.json')}
 C.check(bindings['failed_native_attempt_sha256']==evidence['native_command_receipt_sha256']
  and bindings['failed_phase_exit_sha256']==evidence['actual_phase_exit_receipt_sha256'],'Failure evidence source binding changed')
 receipt.update(bindings,native_windows_extraction_validation='PASS_NATIVE_WINDOWS_EXTRACTION_AND_ALL_MEMBER_HASHES')
 w.js(P/'publication_receipt.json',receipt)
 print(commit(['scripts/verify_stage04b_windows_and_bind_receipt.py','reports/stage04b/publication_receipt.json',
  'reports/stage04b/windows_portability_check.json','reports/stage04b/windows_verification_commands.jsonl'],
  'Verify Windows failure-evidence ZIP extraction and bind actual failed inference bytes'))
