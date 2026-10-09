"""Publish source/history recovery and remaining real Stage5 endpoint prerequisites."""
from pathlib import Path
import argparse,datetime,hashlib,json
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-head',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    work=Path(__file__).resolve().parent;out=work/'master_cold_recovery03_attempt02';out.mkdir(exist_ok=False)
    files=[];base='reports/master_run/20261009/'
    def add(local,target,pin=None):
        path=Path(local)
        if not path.is_absolute():path=work/path
        raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        assert 0<len(raw)<5*1024*1024 and (pin is None or pin==sha),str(path)
        files.append({'local_absolute_path':str(path),'target':target,'bytes':len(raw),'sha256':sha})
    completion=json.loads((work/'master_old_checkout_changed_history01/completion.json').read_bytes())
    for name,row in completion['compact_publication_controls'].items():
        if name.endswith('.py'):target='scripts/master_run/'+Path(name).name
        else:
            rel=name
            for old,new in [('master_old_checkout_changed_history01/',''),
                ('old_checkout_changed_history_scope01/','scope01/'),('old_checkout_changed_history_scope02/','scope02/'),
                ('old_checkout_changed_history_inspection01/','inspection01/')]:
                if rel.startswith(old):rel=new+rel[len(old):];break
            target=base+'cleanup/changed_history01/'+rel
        add(name,target,row['sha256'])
    add('master_old_checkout_changed_history01/completion.json',base+'cleanup/changed_history01/completion.json',
        '8c27d33a058a42a711cc78c5b9f25f0825d944a34b0e1fe807cd9cf415a61233')
    for name in [Path(__file__).name,'verify_master_changed_history_remote.py','verify_public_conda_packages01_remote.py',
        'test_verify_public_conda_packages01_remote.py','stage5_unc_bind_probe.py','test_stage5_unc_bind_probe.py',
        'acquire_iqtree314_source01.py','acquire_iqtree314_source01_attempt01.py','diagnose_iqtree_source_export01.py']:
        add(name,'scripts/master_run/'+name)
    pairs={
        'master_cold_recovery03/PREPARATION_FAILURE.json':'publication/COLD_RECOVERY03_PREPARATION_FAILURE.json',
        'verify_public_conda_packages01_remote_preparation.json':'cleanup/conda_packages01/REMOTE_READBACK_PREPARATION.json',
        'verify_public_conda_packages01_remote.md':'cleanup/conda_packages01/REMOTE_READBACK_METHODS.md',
        'master_old_checkout_changed_history_independent_local_readback.json':'cleanup/changed_history01/INDEPENDENT_LOCAL_READBACK.json',
        'old_checkout_changed_history01_readback_20261009T210118Z_35eb1aed/receipt.json':'cleanup/changed_history01/LOCAL_READBACK.json',
        'stage5_unc_bind_probe.md':'preparation/stage5_unc_bind_probe.md',
        'stage5_unc_bind_probe_independent_source_review.json':'preparation/stage5_unc_bind_probe_independent_source_review.json',
        'stage5_unc_bind_probe_preparation_checks.json':'preparation/stage5_unc_bind_probe_preparation_checks.json',
        'master_conda_assets_upload_plan.json':'cleanup/conda_packages01/UPLOAD_PLAN.json',
        'master_conda_assets_upload_receipt.json':'cleanup/conda_packages01/UPLOAD_RECEIPT.json',
        'master_conda_controls_git_objects.json':'publication/CONDA_CONTROLS_GIT_OBJECTS.json',
        'master_conda_controls_remote_readback.json':'publication/CONDA_CONTROLS_REMOTE_READBACK.json',
        'iqtree314_source01_20261009T205427Z_7d051710/receipt.json':'cleanup/iqtree314_source01/ATTEMPT02_ACQUISITION_RECEIPT.json',
        'iqtree314_source01_20261009T204525Z_40601c75/export_diagnosis.json':'cleanup/iqtree314_source01/EXACT_EXPORT_DIAGNOSIS.json',
        'iqtree314_source01_20261009T205427Z_7d051710/original_git_blobs/4b5d6aa580496004b342d8d49cbe8f6629e835f8.blob':'cleanup/iqtree314_source01/original_git_blobs/4b5d6aa580496004b342d8d49cbe8f6629e835f8.blob',
    }
    for local,target in pairs.items():add(local,base+target)
    now=datetime.datetime.now(datetime.timezone.utc)
    raw=(work/'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_bytes();native=json.loads(raw)
    assert 0<=(now-datetime.datetime.fromisoformat(native['utc'])).total_seconds()<60
    assert native['exited'] is False and native['job_active_processes']==2
    (out/'native_progress.json').write_bytes(raw)
    status=json.loads((work/'master_recovery_progress02/status.json').read_bytes())
    status.update(updated_utc=now.isoformat(),native_process=native,
        latest_progress_snapshot=base+'snapshots/cold_recovery03/native_progress.json')
    status['cleanup']['empty_directory_proposal']['remote_readback']='PASS_FRESH_REMOTE19_MEMBERS_5542_PROPOSED_NO_PRUNE'
    status['stage5_unc_endpoint_preparation']={'source':'70bbd9b0ae04ad90f3b1595d49d844ba899b93aefad6d2edf37ec675a99c9830',
        'pure_tests':7,'independent_source_review':'PASS','actual_endpoint_or_lifecycle_execution':'NOT_RUN'}
    status['recovery_preparation']['conda_originals'].update(state='PASS_LOCAL339_ORIGINALS_363_CRC_SHA_MEMBERS',
        uploaded_assets=4,remote_payload_recovery='PENDING_INDEPENDENT_FRESH_DOWNLOAD',
        continuation='ACTUAL_EXIT0_AFTER_TWO_FRESH_ADMISSION_PROBES',shard_bytes=662834628)
    status['recovery_preparation']['iqtree_full_source']={'state':'PASS_LOCAL_THREE_ORIGINAL_TARS_PLUS_ONE_GITBLOB_SUPPLEMENT',
        'original_git_blobs':1938,'native_binary_build_equivalence':'NOT_PROVEN',
        'exact_export_difference':'One249B originalLF Gitblob retained beside264B CRLF export; source tar unmodified',
        'remote_recovery':'NOT_RUN'}
    status['recovery_preparation']['old_changed_history']={'public_originals':194,'public_bytes':18622099,
        'whole_private_exclusions':5,'excluded_bytes':4795,'local_archive_members':216,
        'remote_recovery':'PENDING','pruning':'NOT_RUN','wipe_authority':False}
    (out/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    md=f'''# Current execution status

Updated {now.isoformat()}. Direct user continuation remains active. GitHub main
and Release assets are the durable project authority. Scheduled automatic
continuation remains disabled.

Stage4: one partitioned IQ-TREE3.1.4 worker remains active on all196 approved
genomes,100 accepted marker partitions and17,456 amino-acid columns. Global
search has reached iteration80; CPU progress continues. No final tree/supports
are accepted. Historical V10 closure remains UNKNOWN. Fresh snapshot:
`reports/master_run/20261009/snapshots/cold_recovery03/native_progress.json`.

Stage5: accession-source dependency split V2 is implemented in addf594d.
All196 canonical source bundles match accepted SHA/size pins:12,812 payload
files/1,893,101,586 bytes; nine support modules/182,212 bytes also match.
The26-member evidence ZIP passes independent fresh GitHub/full-member and
exact196-ledger readback. This is source readiness only. Actual detectors,
runtime discovery, WSL lifecycle/storage/UNC endpoint proofs and production
curation remain NOT_RUN. The new bounded UNC probe source has seven pure tests
and independent source review PASS; actual execution awaits exact current
native closure/unlock and the real runtime/mount/resource prerequisites.

Detection/per-genome curation need no host tree. Queue fixed approved accessions,
preserving complete genomic context. Live Stage4 leaves are not final work
units. WD retains one native owner. Final Stage6 joins/SVG/PDF require accepted,
separately published host tree, independent curation and exact196-by4 coverage.
Failed, unresolved and not-run cells are never absence. See
`docs/master_run/STAGE5_STAGE6_DEPENDENCY_DECISION.md`.

Completed cleanup:48,490 exact files/9,756,853,507 logical bytes plus15 exact
empty directories. Recovery and independent absence/protected-hash checks PASS.
Physical reclaimed bytes are NOT_MEASURED. An additional5,542-directory proposal
has fresh GitHub/all19-member metadata readback PASS; no further pruning has run.

Recovery: all339 pinned original Conda packages/660,114,049 bytes pass local
download and two-shard/all363-member checks. Both ZIPs and both original LF
sidecars are uploaded; independent fresh download verification is pending.
Full IQ-TREE source plus both pinned submodules pass local original-Git-blob
checks (1,938 blobs), using three unchanged upstream tar archives and one exact
249-byte Gitblob supplement for a diagnosed CRLF export. No native binary-build
equivalence is inferred. Its source archive remote recovery remains pending.

An additional194 old changed/untracked scientific source/history originals,
18,622,099 bytes, pass local216-member ZIP checks. Five whole private operational
files/4,795 bytes remain excluded and local. Historical failures/UNKNOWN states
are preserved. Remote history readback and any later exact purge are pending.
Active tools, original lock, live inputs/checkpoints, six dirty G files and the
installed toolchain remain protected. G stays at launch160498a6 until exact
native closure permits reconciliation. The host is not ready to wipe.

| Stage | Scientific state |
|---|---|
|0–3|Accepted upstream acquisition/panel/sequence/marker results preserved|
|4|Running; Stage4a accepted; final host tree pending|
|5|Detectors/curation not run; current source readiness PASS|
|6|Production figure not run; synthetic proofs only|
|7|Final scientific review not run|

Detailed evidence: `status/master_run_20261009.json` and
`docs/master_run/STORAGE_LEDGER.md`. Raw private sessions/prompts/usage,
credentials and unrelated data are excluded from public recovery assets.
'''
    (out/'STATUS.md').write_text(md,encoding='utf-8')
    ledger=(work/'master_recovery_progress02/STORAGE_LEDGER.md').read_text(encoding='utf-8')
    ledger+='\nCurrent cold-recovery observations: all339 exact Conda originals/660,114,049\nbytes are locally verified and both shards/sidecars uploaded; fresh readback\npending. Directory metadata19-member archive has fresh remote PASS, no pruning.\nOld changed history194 originals/18,622,099 bytes has local216-member PASS; five\nwhole private records remain local/excluded. Full IQ-TREE and both submodule\nsource snapshots have1,938 original Gitblob bindings with one explicit249B\noriginal-source supplement; local only, no compiled-binary equivalence claim.\n'
    (out/'STORAGE_LEDGER.md').write_text(ledger,encoding='utf-8')
    add(out/'native_progress.json',base+'snapshots/cold_recovery03/native_progress.json')
    add(out/'status.json','status/master_run_20261009.json');add(out/'STATUS.md','STATUS.md')
    add(out/'STORAGE_LEDGER.md','docs/master_run/STORAGE_LEDGER.md')
    assert len({r['target'] for r in files})==len(files)
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump({'expected_head':a.expected_head,
            'message':'Preserve194 public changed-history originals and exact IQ-TREE source; prepare bounded Stage5 endpoint proof',
            'files':files},stream,indent=2);stream.write('\n')
    print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
if __name__=='__main__':main()
