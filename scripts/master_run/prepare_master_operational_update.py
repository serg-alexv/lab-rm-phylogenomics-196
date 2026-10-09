"""Prepare explicit public operational evidence plans; no Git ref or checkout mutation."""
from pathlib import Path
import argparse,datetime,hashlib,json,re
W=Path(__file__).resolve().parent;B='reports/master_run/20261009/'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-head',required=True)
 p.add_argument('--name',required=True);p.add_argument('--previous-status',type=Path,required=True)
 p.add_argument('--previous-markdown',type=Path,required=True);p.add_argument('--phase',required=True)
 p.add_argument('--spool',action='append',default=[]);p.add_argument('--extra',action='append',default=[])
 p.add_argument('--independent-tree-receipt',type=Path)
 a=p.parse_args();assert re.fullmatch('[a-z0-9_]+',a.name) and re.fullmatch('[0-9a-f]{40}',a.expected_head)
 O=W/a.name;O.mkdir(exist_ok=False);files=[]
 def add(local,target):
  q=Path(local).resolve();assert q.is_relative_to(W) and not q.is_symlink() and q.is_file()
  raw=q.read_bytes();assert len(raw)<5*1024**2 and q.suffix in ('.py','.md','.json','.jsonl','.txt','.tsv')
  files.append(dict(local_absolute_path=str(q),target=target,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
 add(__file__,'scripts/master_run/'+Path(__file__).name)
 states={}
 for name in a.spool:
  assert re.fullmatch('stage5_[a-zA-Z0-9_]+',name)
  scope=W/name;assert scope.is_dir() and not scope.is_symlink()
  for q in sorted(scope.rglob('*')):
   if q.is_file():add(q,B+'stage5/actual/'+name+'/'+q.relative_to(scope).as_posix())
  states[name]=json.loads((scope/'result.json').read_bytes())['state']
 for pair in a.extra:
  local,target=pair.split('=',1);add(W/local,target)
 s=json.loads(a.previous_status.read_bytes());now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 s['updated_utc']=now;s['stage04_publication']='UPLOAD_VERIFIED_FULL_PRODUCER_READBACK_INDEPENDENT_REMOTE_REVIEW_PENDING'
 s['stage04_release']='https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/tag/stage04-primary196-atomic-v1'
 s['stage04_publication_preparation']['state']='UPLOAD_VERIFIED'
 if a.independent_tree_receipt:
  tree=json.loads(a.independent_tree_receipt.read_bytes())
  if not (tree['state']=='PASS_FRESH_REMOTE_ACCEPTED_PRIMARY196_FULL_PAYLOAD'
   and tree['independent_remote_gate_passed'] is True and tree['unique_tips']==196 and tree['ufboot_replicates']==1000):
   raise ValueError('Actual independent full196 remote receipt required')
  s['stage04_independent_remote_gate']='PASS_FRESH_REMOTE_ACCEPTED_PRIMARY196_FULL_PAYLOAD'
  s['stage04_independent_remote_receipt_sha256']=hashlib.sha256(a.independent_tree_receipt.read_bytes()).hexdigest()
 if s.get('stage04_independent_remote_gate')=='PASS_FRESH_REMOTE_ACCEPTED_PRIMARY196_FULL_PAYLOAD':
  s['stage04_publication']='UPLOAD_VERIFIED_AND_INDEPENDENT_FRESH_FULL_PAYLOAD_PASS'
 s['stage5_operational_phase']=a.phase;s.setdefault('stage5_actual_setup',{}).update(states)
 (O/'status.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
 md=a.previous_markdown.read_text(encoding='utf-8')
 md=md.replace(json.loads(a.previous_status.read_bytes())['updated_utc'],now)
 md=md.replace('Portable Release upload and fresh payload readback are next; publication is a separate gate.',
  'Portable Release upload and full producer readback PASS. A separate independent fresh remote inspection is pending. Release: '+s['stage04_release']+'.')
 md=md.replace('|4|COMPLETE_VALIDATED; portable Release/readback pending|','|4|COMPLETE_VALIDATED; Release UPLOAD_VERIFIED|')
 md=md.replace('Actual WSL/runtime/storage/interop/UNC setup and detectors remain NOT_RUN.',
  'Setup is progressing through the actual gates recorded below. Detector execution and production curation remain NOT_RUN.')
 if s.get('stage04_independent_remote_gate')=='PASS_FRESH_REMOTE_ACCEPTED_PRIMARY196_FULL_PAYLOAD':
  md=md.replace('A separate independent fresh remote inspection is pending.',
   'Separate independent fresh GitHub verification PASS: all56ZIP members/55SUMS,25controls,196tips/389branches/193support pairs/1000bootstrap trees and exact unrooted NEXUS, with native closure and duplicate-group limitations preserved.')
 md+='\nActual operational update: '+a.phase+'\n'
 for name,state in states.items():md+='- `'+name+'`: '+state+'; exact command, closure, resources and lock-release receipts are retained.\n'
 (O/'STATUS.md').write_text(md,encoding='utf-8')
 add(O/'status.json','status/master_run_20261009.json');add(O/'STATUS.md','STATUS.md')
 assert len(files)==len({r['target'] for r in files})
 with (W/(a.name+'_git_plan.json')).open('x',encoding='utf-8') as f:
  json.dump(dict(expected_head=a.expected_head,message=a.phase,files=files),f,indent=2);f.write('\n')
 print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
if __name__=='__main__':main()
