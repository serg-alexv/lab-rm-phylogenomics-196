"""Publish actual paired memory evidence and frozen metadata exception-state fix."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/';extras={}
mapping=W/'canonical_post_ff_stat32_publication_files.json'
assert hashlib.sha256(mapping.read_bytes()).hexdigest()=='61d0dffb9fe986dcf66a68a058f6cbc8abbcd475cc0874bff702f3d46a5d7a03'
for row in json.loads(mapping.read_bytes())['files']:
 p=Path(row['local']);raw=p.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 extras[p.relative_to(W).as_posix()]=row['target']
actual=W/'stage5_paired_memory_observation_0174a1b96e094f8faafacad84b6200b0'
assert hashlib.sha256((actual/'receipt.json').read_bytes()).hexdigest()=='532373ea7de9317ba6c0827a5f3be70a6cf7ffc049666c7e4126ea2194712474'
for p in sorted(actual.iterdir()):
 assert p.is_file() and p.suffix in ('.json','.txt');extras[p.relative_to(W).as_posix()]=B+'stage5/paired_memory22/'+p.name
extras.update({'canonical_post_ff_stat32_publication_files.json':B+'git_post_ff_stat32/PUBLICATION_FILES.json',
 'stage5_memory_observation_independent_source_review.json':B+'stage5/paired_memory22/OBSERVATION_SOURCE_PEER.json',
 'master_memory_stat21_git_objects.json':B+'publication/master_memory_stat21_git_objects.json',
 'master_memory_stat21_remote_readback.json':B+'publication/master_memory_stat21_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name})
# Root already read all f8b source; the final db73 change only makes any outer
# exception (including unlock failure) reset the receipt state to FAILED.
old=(W/'repair_canonical_post_ff_stat32_before_exception_state_fix.py').read_text()
new=(W/'repair_canonical_post_ff_stat32.py').read_text()
assert new==old.replace("record.update(error_kind=type(e).__name__,error_message=str(e));raise",
                       "record.update(state='FAILED_PRESERVED',error_kind=type(e).__name__,error_message=str(e));raise")
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','80fac5c5d98aef9ce677f916bb22165139ea70e1',
 '--name','master_paired_memory22','--previous-status',str(W/'master_memory_stat21/status.json'),
 '--previous-markdown',str(W/'master_memory_stat21/STATUS.md'),
 '--phase','Publish actual retained paired memory observation; hold unsupported3GiB remedy and prepare exact large-file cache hints with pidfd ABI compatibility']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
O=W/'master_paired_memory22';s=json.loads((O/'status.json').read_bytes())
s['stage5_paired_memory']='PASS_READ_ONLY_RETAINED_CLIENT_EXIT0_ORIGINAL_UNLOCK; guest_current260825088_peak1743339520_Cached117792768_noOOM_noSwap; Windows_commit_after3459862528'
s['stage5_resource_pressure']='No causal attribution from idle snapshot.3GiB ceiling held because observed peak1.74GB is already lower. Exact large runtime-file chunked SHA256 and completed-page DONTNEED hints source preparation pending; unchanged reserve gates.'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
with (O/'STATUS.md').open('a',encoding='utf-8') as f:
 f.write('\nActual paired memory observation PASS: retained WSL client exit0, nonce/source-bound full Linux output, Windows before/after, original unlock. Guest cgroup current260,825,088B/peak1,743,339,520B; Cached117,792,768B; no OOM/swap. Host commit after3,459,862,528B. This idle snapshot does not attribute the historical growth. A3GiB WSL ceiling is held because it exceeds the already observed peak; targeted bounded cache hints for exact large runtime hash reads are in preparation. No cache/config action has run and reserves remain unchanged. Exact32 helper final exception-state-only change db73 is reviewed against prior f8b; actualG32 execution is next.\n')
pp=W/'master_paired_memory22_git_plan.json';plan=json.loads(pp.read_bytes())
for row in plan['files']:
 raw=Path(row['local_absolute_path']).read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
pp.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
