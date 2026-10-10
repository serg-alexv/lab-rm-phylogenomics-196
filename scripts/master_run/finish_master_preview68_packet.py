"""Finish the unadopted publication packet after its paragraph selector failed closed."""
from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent
def main():
    p=W/'master_preview68/STATUS.md';parts=p.read_text(encoding='utf-8').split('\n\n')
    matches=[i for i,x in enumerate(parts) if x.startswith('Stage5 capacity02 has preserved scientific identity')]
    assert len(matches)==1
    parts[matches[0]]='Stage5 current execution: '+(W/'master_preview68_paragraph.md').read_text(encoding='utf-8').strip()
    p.write_text('\n\n'.join(parts),encoding='utf-8')
    q=W/'master_preview68_git_plan.json';doc=json.loads(q.read_bytes())
    own=Path(__file__).resolve();doc['files'].append({'local_absolute_path':str(own),'target':'scripts/master_run/'+own.name})
    for r in doc['files']:
        raw=Path(r['local_absolute_path']).read_bytes();r.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    assert len(doc['files'])==len({r['target'] for r in doc['files']})
    q.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'state':'REPAIRED_UNADOPTED_PACKET_STATUS_ONLY','files':len(doc['files']),
      'prior_git_objects':'master_preview68_git_objects.json; never adopted; paragraph-selector failure retained locally'}))
if __name__=='__main__':main()
