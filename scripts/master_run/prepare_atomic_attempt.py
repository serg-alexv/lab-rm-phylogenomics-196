from pathlib import Path
import datetime as dt
import hashlib
import json
import msvcrt
import shutil
import subprocess
import publish_bootstrap as B

report = B.ROOT / 'reports/stage04/atomic_resume_20261009'
copies = {
    B.CHAT/'work/atomic_iqtree_windows.py': B.ROOT/'scripts/atomic_iqtree_windows.py',
    B.CHAT/'work/test_atomic_iqtree_windows.py': B.ROOT/'scripts/test_atomic_iqtree_windows.py',
    B.CHAT/'work/smoke_atomic_iqtree_windows.py': B.ROOT/'scripts/smoke_atomic_iqtree_windows.py',
    B.CHAT/'work/independent_inputs/model_cache_compatibility.json': report/'model_cache_compatibility.json',
    B.CHAT/'work/independent_inputs/fallback_memory_evidence.json': report/'fallback_memory_evidence.json',
    B.CHAT/'work/native_smoke_01/synthetic_validation.json': report/'short_native_lifecycle_validation.json',
    B.CHAT/'work/native_smoke_01/exit.json': report/'short_native_lifecycle_exit.json',
}
lock = (B.HISTORY / '.work/workflow.lock').open('r+b')
lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
try:
    expected = 'a7563923c58d877fde98e10a3ca8e68348a60f63'
    assert B.git('rev-parse','HEAD') == expected
    assert B.git('ls-remote','origin','refs/heads/main').split()[0] == expected
    assert B.sha(B.CHAT/'work/atomic_iqtree_windows.py') == '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
    for src, dest in copies.items():
        assert not dest.exists(), str(dest)
        shutil.copyfile(src,dest)
    review = {'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'state':'PREPARED_NOT_SCIENTIFICALLY_EXECUTED',
        'source_review':'Independent Win32 lifecycle review; closure fixes included; native cache input compatibility certified separately',
        'runner_sha256':B.sha(B.ROOT/'scripts/atomic_iqtree_windows.py'),
        'focused_guard_tests_passed':12,
        'short_native_lifecycle':'PASS_REAL_CMD_EXIT0_EMPTY_OWNED_JOB_UNLOCK_POWER_RESTORE_NO_BIOLOGY',
        'scientific_jobs_launched':0,
        'cache':'Exact original partial .model.gz bytecopy to new unique prefix; native restoration must be observed; no general .ckp.gz imported',
        'storage':'Bounded local C temporary inference spool; accepted outputs will be copied/hash-verified to canonical G data root after native closure',
        'preferred':'Same196x17456AA/100partitions/MFP/B1000/alrt1000/seed1961008/T2/keep-ident/boot-trees;4.5GiB hard commitcap plus1.5GiB hostreserve',
        'fallback':'Same matrix,unpartitioned MFP with supported --mem2G --thread-site;3.5GiB hardcap plus1.5GiB reserve, independently source-estimated and not a peak guarantee',
        'power':'Transient ES_SYSTEM_REQUIRED while owned native runs; restored on exit; no manual-power/logoff survival claim',
        'file_sha256':{p.relative_to(B.ROOT).as_posix():B.sha(p) for p in copies.values()},
    }
    B.save(report/'atomic_runner_review.json',review)
    allow = [p.relative_to(B.ROOT).as_posix() for p in copies.values()] + [(report/'atomic_runner_review.json').relative_to(B.ROOT).as_posix()]
    subprocess.run(['git','-C',str(B.ROOT),'add','--',*allow],check=True)
    assert set(B.git('diff','--cached','--name-only').splitlines()) == set(allow)
    subprocess.run(['git','-C',str(B.ROOT),'-c','core.whitespace=cr-at-eol,-blank-at-eol','diff','--cached','--check'],check=True)
    subprocess.run(['git','-C',str(B.ROOT),'commit','-m','Prepare reviewed atomic IQ-TREE job and cache-preserving recovery'],check=True)
    subprocess.run(['git','-C',str(B.ROOT),'push','origin','main'],check=True)
    commit = B.git('rev-parse','HEAD')
    assert B.git('ls-remote','origin','refs/heads/main').split()[0] == commit
    tree = json.loads(subprocess.check_output(['gh','api',f'repos/serg-alexv/lab-rm-phylogenomics-196/git/trees/{commit}?recursive=1'],text=True,encoding='utf-8'))
    assert not tree.get('truncated')
    blobs = {x['path']:x['sha'] for x in tree['tree'] if x['type']=='blob'}
    for name in allow:
        assert blobs.get(name) == B.git('hash-object','--',name), name
    base = B.ROOT/'.work/stage04_phylogeny_v2/analyses/primary196'
    def pin(path):
        return {'path':str(path),'sha256':B.sha(path)}
    tasks = json.loads((B.CHAT/'work/bootstrap/scheduled_tasks.json').read_text(encoding='utf-8-sig'))
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    cfg = {'schema':'LAB_RM_ATOMIC_IQTREE_V1','mode':'partitioned',
        'canonical_commit':commit,'repository_path':str(B.ROOT),
        'run_control_state':'ACTIVE_DIRECT_USER_CONTINUATION','run_control':pin(B.ROOT/'status/run_control.json'),
        'threads':2,'seed':1961008,'budget':{'cap_bytes':9*1024**3//2,'reserve_bytes':3*1024**3//2},
        'runtime_seconds':86400,'admission_seconds':1800,
        'expected_disabled_tasks':[x['Name'] for x in tasks],
        'output_directory':str(B.CHAT/'work/iqtree_attempts'/('partitioned_'+stamp)),
        'powershell':r'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe',
        'executable':pin(B.HISTORY/'.tools/iqtree_windows_3_1_4/extracted/iqtree-3.1.4-Windows/bin/iqtree3.exe'),
        'alignment':pin(base/'concatenated.faa'),'partitions':pin(base/'partitions.nex'),
        'approved_accessions':pin(B.ROOT/'config/approved_accessions.txt'),
        'cache_import':pin(B.ROOT/'.work/stage04_inference_windows_v10/analyses/primary196/iqtree/host.model.gz'),
        'cache_compatibility_evidence':pin(report/'model_cache_compatibility.json'),
    }
    target = B.CHAT/'work/stage04_partitioned_config.json'
    B.save(target,cfg)
    B.save(B.CHAT/'work/bootstrap/atomic_preparation_publication.json',{'state':'UPLOAD_VERIFIED_GIT_BLOBS','commit':commit,'files':allow,'config':str(target),'config_sha256':B.sha(target)})
    print(json.dumps({'published_commit':commit,'config':str(target),'output':cfg['output_directory'],'verified_files':len(allow)}))
finally:
    lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1); lock.close()
