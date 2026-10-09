"""Freeze bounded reader corrections, actual fixture evidence and recovery controls."""
from pathlib import Path
import argparse, datetime, hashlib, json

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); work=Path(__file__).resolve().parent
    out=work/'master_recovery_verified04'; out.mkdir(exist_ok=False)
    base='reports/master_run/20261009/'; files={}
    def add(local,target,pin=None):
        path=Path(local)
        if not path.is_absolute():path=work/path
        raw=path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
        assert 0<len(raw)<5*1024*1024 and (pin is None or pin==sha),str(path)
        row={'local_absolute_path':str(path),'target':target,'bytes':len(raw),'sha256':sha}
        if target in files:assert files[target]==row,target
        files[target]=row
    fixed={
      'verify_public_conda_packages01_remote.py':'cadeda01183522be585b0f42f240fcaab8bc7a5335937e03b209a04e5ff216ed',
      'test_verify_public_conda_packages01_remote.py':'763dcd64720a0c54251da3ca34ac86a47592e437b46422d95e793517d96fc896',
      'verify_public_conda_packages01_remote_before_owned_monitor.py':'c436cafb8154bad608fd0ecde24964acf0339b70c1572c833429702437ec46da',
      'prepare_master_single_archive_assets_plan.py':None,
      Path(__file__).name:None,
    }
    for local,pin in fixed.items():add(local,'scripts/master_run/'+local,pin)
    pairs={
      'verify_public_conda_packages01_remote.md':'cleanup/conda_packages01/REMOTE_READBACK_METHODS.md',
      'verify_public_conda_packages01_remote_preparation_v2.json':'cleanup/conda_packages01/REMOTE_READBACK_PREPARATION_V2.json',
      'verify_public_conda_packages01_remote_preparation_final.json':'cleanup/conda_packages01/REMOTE_READBACK_PREPARATION_FINAL.json',
      'public_conda_remote_verifier_independent_review.json':'cleanup/conda_packages01/REMOTE_READER_INDEPENDENT_REVIEW.json',
      'master_changed_history_remote_source_review.json':'cleanup/changed_history01/REMOTE_READER_INDEPENDENT_REVIEW.json',
      'old_checkout_changed_history01_readback_20261009T210725Z_112ba511/receipt.json':'cleanup/changed_history01/REMOTE_READBACK.json',
      'master_changed_history_assets_upload_plan.json':'cleanup/changed_history01/UPLOAD_PLAN.json',
      'master_changed_history_assets_upload_receipt.json':'cleanup/changed_history01/UPLOAD_RECEIPT.json',
      'master_cold_recovery03_git_objects.json':'publication/COLD_RECOVERY03_GIT_OBJECTS.json',
      'master_cold_recovery03_remote_readback.json':'publication/COLD_RECOVERY03_REMOTE_READBACK.json',
    }
    for local,target in pairs.items():add(local,base+target)
    iq=json.loads((work/'iqtree314_source_recovery01_publication_plan.json').read_bytes())
    for r in iq['files']:add(r['local_path'],r['remote_path'],r['sha256'])
    add('iqtree314_source_recovery01_publication_plan.json',base+'cleanup/iqtree314_source01/PUBLICATION_PLAN.json',
        '1049b4c93a7e0e06477e9a75ec2918427c5a1cad9790ac6c33d385d91dedf243')
    dc=work/'directory_handle_pruner_preparation_completion_02.json'
    d=json.loads(dc.read_bytes())
    for r in d['public_control_mapping']:
        name=r['suggested_public_name']
        target=('scripts/master_run/' if name.endswith('.py') else base+'cleanup/emptydirs_pruner01/')+name
        add(r['local_path'],target,r['sha256'])
    add(dc,base+'cleanup/emptydirs_pruner01/PREPARATION_COMPLETION_02.json',
        'ee0a5516641e21d2c16e60c4acdd11f60c2569a0e42308c8086a00a9cccd211a')
    now=datetime.datetime.now(datetime.timezone.utc)
    raw=(work/'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_bytes()
    native=json.loads(raw)
    assert 0<=(now-datetime.datetime.fromisoformat(native['utc'])).total_seconds()<60
    assert native['exited'] is False and native['job_active_processes']==2
    (out/'native_progress.json').write_bytes(raw)
    status=json.loads((work/'master_cold_recovery03_attempt02/status.json').read_bytes())
    status.update(updated_utc=now.isoformat(),native_process=native,
        latest_progress_snapshot=base+'snapshots/recovery_verified04/native_progress.json')
    status['recovery_preparation']['old_changed_history']['remote_recovery']='PASS_FRESH_REMOTE216_MEMBERS_194_ORIGINALS_NO_PURGE'
    status['recovery_preparation']['old_changed_history']['remote_receipt']=base+'cleanup/changed_history01/REMOTE_READBACK.json'
    status['recovery_preparation']['conda_originals']['remote_reader']='CORRECTED_OWNED_DOWNLOAD_MONITOR_13_PURE_TESTS_AND_PEER_REVIEW_PASS_ACTUAL_PENDING'
    status['recovery_preparation']['iqtree_full_source'].update(local_recovery_archive='PASS_31_MEMBERS_30_SUMS_1938_ORIGINAL_GITBLOBS',
        archive_sha256=iq['archive']['sha256'],remote_recovery='PENDING_UPLOAD_AND_INDEPENDENT_FRESH_READBACK')
    status['cleanup']['empty_directory_proposal']['execution_preparation']={
        'source_sha256':'9b64d17bb2612ce35051b87d77863709d875c1f910865fd6a4db2f6ddd265381',
        'actual_windows_fixtures':9,'preparation_guards':6,'independent_review':'PASS',
        'first_failed_ancestor_rename_fixture':'PRESERVED_THEN_CORRECTED',
        'production_execution':'NOT_RUN','authority_created':False}
    (out/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    md=f'''# Current execution status

Updated {now.isoformat()}. Direct user continuation remains active. GitHub main
and verified Release assets are the durable project authority. Automatic
continuation remains disabled.

Stage4: the sole partitioned IQ-TREE 3.1.4 worker is advancing at iteration 90
on all 196 approved genomes, 100 accepted partitions and 17,456 AA columns.
The final tree and support are not yet accepted; historical V10 closure is
UNKNOWN. The fresh native snapshot is
`reports/master_run/20261009/snapshots/recovery_verified04/native_progress.json`.

Stage5 dependency split V2 is implemented in addf594d. Detection and per-genome
curation can queue fixed approved accessions independently of the host tree,
preserving complete genomic context. All 196 source bundles match accepted
pins (12,812 payload files / 1,893,101,586 bytes); nine support modules also
match. The evidence archive passes fresh GitHub readback of all 26 members and
the full 196-accession ledger. This proves source readiness only. Actual
detectors, runtime discovery, WSL lifecycle/storage/UNC proofs and production
curation remain NOT_RUN. WD retains one native owner, so detector execution
awaits exact current process/job/descendant closure and original-lock release.
Final Stage6 requires the accepted, separately published full host tree and
independent 196-by-4 curation. Failed/unresolved/not-run cells never mean absence.
See `docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md`.

Completed cleanup remains 48,490 exact files / 9,756,853,507 logical bytes plus
15 exact empty directories, with recovery and independent protected-hash and
absence checks. Physical reclaimed bytes are NOT_MEASURED. The additional
5,542-directory metadata proposal has fresh remote readback PASS. Its corrected
handle-based pruner passes nine actual Windows fixtures, six preparation guards
and independent review. The first ancestor-rename failure and exact sources
are preserved. Production directory pruning has NOT_RUN.

Recovery: the 194 public changed-history originals (18,622,099 bytes) now pass
fresh GitHub download and all 216 ZIP-member checks. Five whole private files
remain excluded and local; no changed-history originals have been purged.
All 339 exact original Conda packages (660,114,049 bytes) pass local checks;
both shards and sidecars are uploaded. The independent reader's owned-download
resource monitor correction passes 13 pure tests and peer review. Its actual
fresh remote payload check remains pending. The superseded reader was never
executed against remote payloads and is preserved as source history.

Full IQ-TREE and both pinned submodule source snapshots have 1,938 exact
original Gitblob bindings in a locally verified 31-member recovery ZIP. Three
upstream archives remain unchanged; one separate 249-byte LF Gitblob restores
a diagnosed 264-byte CRLF export. No binary-build equivalence is inferred.
Release upload and independent fresh source recovery readback remain pending.

Active tools, original lock, live inputs/checkpoints, six dirty G files and
installed toolchain remain protected. G stays at launch 160498a6 until exact
native closure permits reconciliation. The host is not ready to wipe.

| Stage | Scientific state |
|---|---|
|0–3|Accepted upstream results preserved|
|4|Running; Stage4a accepted; final host tree pending|
|5|Source readiness PASS; actual detectors and curation NOT_RUN|
|6|Production figure NOT_RUN; synthetic proofs only|
|7|Final scientific review NOT_RUN|

Evidence: `status/master_run_20261009.json` and
`docs/master_run/STORAGE_LEDGER.md`. Private sessions/prompts/usage, credentials
and unrelated data are excluded from public recovery assets.
'''
    (out/'STATUS.md').write_text(md,encoding='utf-8')
    ledger=(work/'master_cold_recovery03_attempt02/STORAGE_LEDGER.md').read_text(encoding='utf-8')
    ledger+='\nVerified recovery update: changed-history fresh remote PASS for all 216 members / 194 public originals; no purge. IQ-TREE recovery ZIP local PASS for all 31 members / 1,938 original Gitblob bindings; upload/readback pending. Corrected Conda remote reader has 13 pure tests and independent review PASS; actual remote check pending. Corrected directory pruner has nine actual Windows fixtures PASS; production NOT_RUN. Prior failures and sources are preserved.\n'
    (out/'STORAGE_LEDGER.md').write_text(ledger,encoding='utf-8')
    add(out/'native_progress.json',base+'snapshots/recovery_verified04/native_progress.json')
    add(out/'status.json','status/master_run_20261009.json');add(out/'STATUS.md','STATUS.md')
    add(out/'STORAGE_LEDGER.md','docs/master_run/STORAGE_LEDGER.md')
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump({'expected_head':a.expected_head,'message':'Verify194 remote history originals; preserve tested directory pruner and bounded Conda reader correction',
                   'files':list(files.values())},stream,indent=2);stream.write('\n')
    print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files.values())}))
if __name__=='__main__':main()
