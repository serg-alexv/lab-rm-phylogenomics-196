"""Bind source-readiness remote PASS and reviewed recovery proposals to master main."""
from pathlib import Path
import argparse, datetime, hashlib, json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-head',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    work=Path(__file__).resolve().parent;out=work/'master_recovery_progress02';out.mkdir(exist_ok=False)
    now=datetime.datetime.now(datetime.timezone.utc);files=[]
    def add(local,target,pin=None):
        path=Path(local)
        if not path.is_absolute():path=work/path
        raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        assert 0<len(raw)<5*1024*1024 and (pin is None or sha==pin),str(path)
        files.append({'local_absolute_path':str(path),'target':target,'bytes':len(raw),'sha256':sha})
    base='reports/master_run/20261009/'
    completion=json.loads((work/'master_old_scientific_emptydirs01/completion.json').read_bytes())
    for name,row in completion['compact_publication_controls'].items():
        if name.endswith('.py'):target='scripts/master_run/'+Path(name).name
        elif name.startswith('master_old_scientific_emptydirs01/'):target=base+'cleanup/emptydirs01/'+Path(name).name
        else:target=base+'cleanup/emptydirs01/'+Path(name).name
        add(name,target,row['sha256'])
    add('master_old_scientific_emptydirs01/completion.json',base+'cleanup/emptydirs01/completion.json',
        '08a83e6761aca488f1f631df4d87400e01074bb809bdcd9a0562107739f8d66d')
    add('master_old_scientific_emptydirs_archive_independent_local_readback.json',base+'cleanup/emptydirs01/INDEPENDENT_LOCAL_READBACK.json',
        '7094996c15576d9d16148d796af2a33c5a402cdeb9085921b8e2685be4414c4b')
    handoff=json.loads((work/'public_conda_packages01_handoff.json').read_bytes())
    for row in handoff['source_controls']:add(row['local_path'],row['remote_path'],row['sha256'])
    add('public_conda_packages01_handoff.json',base+'cleanup/public_conda_packages01/PREPARATION_HANDOFF.json',
        '062a3d8e2bc06e15adde70b8543942e01e61a72820ae034bbe5f4efb3f14dd5c')
    for name in [Path(__file__).name,'verify_master_emptydir_metadata_remote.py','verify_master_original_sidecars.py',
                 'acquire_iqtree314_source01.py','diagnose_iqtree_source_archive01.py']:
        add(name,'scripts/master_run/'+name)
    pairs={
        'stage5_source_readiness01_readback_20261009T203525Z_f4163602/receipt.json':'preparation/source_readiness01/REMOTE_READBACK.json',
        'master_readiness_readback_fix_git_objects.json':'publication/READINESS_FIX_GIT_OBJECTS.json',
        'master_readiness_readback_fix_remote_readback.json':'publication/READINESS_FIX_REMOTE_READBACK.json',
        'old_scientific_emptydirs01_readback_20261009T204618Z_4747655c/receipt.json':'cleanup/emptydirs01/LOCAL_READBACK.json',
        'iqtree314_source01_independent_review.json':'cleanup/iqtree314_source01/SOURCE_REVIEW.json',
        'iqtree314_source01_20261009T204525Z_40601c75/receipt.json':'cleanup/iqtree314_source01/ATTEMPT01_FAILURE.json',
        'iqtree314_source01_20261009T204525Z_40601c75/metadata_diagnosis.json':'cleanup/iqtree314_source01/ATTEMPT01_METADATA_DIAGNOSIS.json',
    }
    for local,target in pairs.items():add(local,base+target)
    raw=(work/'iqtree_attempts/partitioned_20261009T162904Z/progress.json').read_bytes();native=json.loads(raw)
    assert 0<=(now-datetime.datetime.fromisoformat(native['utc'])).total_seconds()<60
    assert native['exited'] is False and native['job_active_processes']==2
    (out/'native_progress.json').write_bytes(raw)
    status=json.loads((work/'master_source_ready_progress01/status.json').read_bytes())
    status.update(updated_utc=now.isoformat(),native_process=native,
        latest_progress_snapshot=base+'snapshots/recovery_progress02/native_progress.json')
    status['stage5_light_queue']['evidence_archive_remote_readback']='PASS_FRESH_REMOTE26_MEMBERS_196_SOURCE_LEDGERS_NATIVE_NOT_RUN'
    status['stage5_light_queue']['remote_receipt']=base+'preparation/source_readiness01/REMOTE_READBACK.json'
    status['cleanup']['empty_directory_proposal']={'proposed':5542,'currently_empty':3736,'planned_child_parents':1806,
        'held':6,'pruning':'NOT_RUN','local_archive':'PASS19_MEMBERS','remote_readback':'PENDING',
        'completion':base+'cleanup/emptydirs01/completion.json'}
    status['recovery_preparation']={'conda_originals':{'expected':339,'expected_bytes':660114049,
        'first_attempt':'RESOURCE_STOP95_VERIFIED_PARTIAL_PRESERVED','continuation':'ONE_EXPLICIT_GATED_PASS_STARTED',
        'remote_payload_recovery':'NOT_VERIFIED'},'iqtree_full_source':{'state':'FIRST_ARCHIVE_VALID_GZIP_STRICT_GIT_SIZE_GATE_FAILED',
        'difference':'One appveyor.yml export has264bytes versus249byte Gitblob; diagnosis only; no source acceptance',
        'submodules':'Two fixed gitlinks identified; acquisition not complete'}}
    (out/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    md=(work/'master_source_ready_progress01/STATUS.md').read_text(encoding='utf-8')
    md=md.replace('Updated '+json.loads((work/'master_source_ready_progress01/status.json').read_bytes())['updated_utc'],
                  'Updated '+now.isoformat()).replace('iteration70','iteration80')
    md=md.replace('The26-member evidence ZIP passed independent\nlocal integrity/accounting checks; its remote upload/readback is pending.',
        'The26-member evidence ZIP passed independent fresh GitHub download/full-member\nCRC/SHA and exact196-ledger verification. The original104-byte CRLF sidecar is\npreserved and verified. The initial LF-assuming reader failure and correction\nremain public. Remote proof: `reports/master_run/20261009/preparation/source_readiness01/REMOTE_READBACK.json`.')
    md=md.replace('snapshots/source_ready_progress01/native_progress.json','snapshots/recovery_progress02/native_progress.json')
    md+='\nRecovery preparation: a metadata-only proposal identifies5,542 old scientific\ndirectories, with six holds; no pruning has run. Its19-member ZIP passes local\nindependent checks; remote readback is pending. The original Conda package\nacquisition stopped at its reserve after95 verified packages; a single explicitly\nauthorized continuation passed two fresh admission probes and started. No\npackage recovery is yet declared remotely verified. Full IQ-TREE source archival\nidentified both pinned submodules; its first strict Git-size check found one\nexported YAML size mismatch, preserved for diagnosis. No source equivalence or\ncomplete runtime restoration is inferred from these preparation steps.\n'
    (out/'STATUS.md').write_text(md,encoding='utf-8')
    ledger=(work/'master_source_ready_progress01/STORAGE_LEDGER.md').read_text(encoding='utf-8')
    ledger=ledger.replace('Evidence ZIP local checks PASS; remote readback pending.',
        'Evidence ZIP fresh GitHub download/all26 members and exact196-ledger checks PASS.')
    ledger+='\nAdditional directory metadata:5,542 proposals/six holds, local19-member ZIP\nverified, no pruning. Changed old-checkout source/history coverage is being\nreviewed separately; Git status metadata alone does not preserve changed bytes.\nConda original acquisition is incomplete/not remotely verified; the first\nresource stop and one explicit gated continuation retain distinct receipts.\n'
    (out/'STORAGE_LEDGER.md').write_text(ledger,encoding='utf-8')
    add(out/'native_progress.json',base+'snapshots/recovery_progress02/native_progress.json')
    add(out/'status.json','status/master_run_20261009.json');add(out/'STATUS.md','STATUS.md')
    add(out/'STORAGE_LEDGER.md','docs/master_run/STORAGE_LEDGER.md')
    assert len({r['target'] for r in files})==len(files)
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump({'expected_head':a.expected_head,
            'message':'Verify source-readiness recovery; preserve exact directory proposal and bounded dependency acquisition history',
            'files':files},stream,indent=2);stream.write('\n')
    print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))

if __name__=='__main__':main()
