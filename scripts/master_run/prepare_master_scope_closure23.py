"""Publish exact32 actual metadata success and reviewed VM scope reconciliation."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/';extras={};binary=[]
g=W/'canonical_post_ff_stat32_20261009T232323Z_9def54b7'
assert hashlib.sha256((g/'receipt.json').read_bytes()).hexdigest()=='7795de12314f1bcf5aa13d680ccbc125963f86669d10797866dfb5cc46bc42d4'
for p in sorted(g.iterdir()):
 if not p.is_file() or p.name=='original.index.bin':continue
 assert p.name in ('receipt.json','preserve_first.json') or p.name.endswith(('.command.json','.stdout.bin','.stderr.bin'))
 target=B+'git_post_ff_stat32/actual/'+p.name
 if p.suffix=='.bin':binary.append(dict(local_absolute_path=str(p),target=target,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),transport_encoding='base64'))
 else:extras[p.relative_to(W).as_posix()]=target
pins={'reconcile_stage5_interop_vm_scope.py':'57df35951cce440896aa1b9792154249cd0924f10690cf8fb935a6e7c79b4aaf',
 'reconcile_stage5_interop_vm_scope_independent_review.json':'3e5d84cf4ae6ea6deb216ce64ffcfe0501a97f28a41ec0657fb6a99ff0d341a9'}
for n,pin in pins.items():
 assert hashlib.sha256((W/n).read_bytes()).hexdigest()==pin
 extras[n]='scripts/master_run/'+n if n.endswith('.py') else B+'stage5/interop_scope23/'+n
extras.update({'master_paired_memory22_git_objects.json':B+'publication/master_paired_memory22_git_objects.json',
 'master_paired_memory22_remote_readback.json':B+'publication/master_paired_memory22_remote_readback.json',
 Path(__file__).name:'scripts/master_run/'+Path(__file__).name})
argv=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head','9d098c57f32a07a1f901ae04be962d58cb8f1481',
 '--name','master_scope_closure23','--previous-status',str(W/'master_paired_memory22/status.json'),
 '--previous-markdown',str(W/'master_paired_memory22/STATUS.md'),
 '--phase','Publish exact32 byte-identical metadata correction PASS and reviewed shutdown-only reconciliation of failed interop scope']
for local,target in extras.items():argv+=['--extra',local+'='+target]
subprocess.run(argv,check=True)
O=W/'master_scope_closure23';s=json.loads((O/'status.json').read_bytes())
s['local_checkout_note']='Exact32 post-FF metadata repair actualPASS; GHEADc76 and entire indexed modes/OIDs unchanged, all32 raw bytes unchanged, finalstatus exactlysix genuine files with preserved identical raw hashes. Gcheckout intentionally has not fetched later documentation-only publications during setup.'
s['stage5_interop_scope_reconciliation']='Source57df peer3e5d reviewed; exact authorized one-VM shutdown preserves4GiB config, twoStopped observations then only its localSTOP removal. ActualNOT_RUN.'
(O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
with (O/'STATUS.md').open('a',encoding='utf-8') as f:
 f.write('\nExact32 metadata correction actualPASS7795: fixed GHEADc76, whole indexed modes/OIDs unchanged, all32 byte-identical raw files, finalstatus exactly the original six genuine dirty files with unchanged hashes, all retained Git jobs closed and original byte lock released. No fetch/merge/ref mutation. Private index/six originals excluded from public logs. Shutdown-only failedinterop scope reconciliation57df/peer3e5d is reviewed and published before actual execution; no WSLconfig edit is proposed.\n')
pp=W/'master_scope_closure23_git_plan.json';plan=json.loads(pp.read_bytes());plan['files']+=binary
for row in plan['files']:
 raw=Path(row['local_absolute_path']).read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
assert len({r['target'] for r in plan['files']})==len(plan['files'])
pp.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
