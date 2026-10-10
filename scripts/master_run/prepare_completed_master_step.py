"""Prepare an exact completed-step Git plan; no ref or scientific mutation."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys
W=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('name','head','previous','phase','paragraph-file','patch-file','extras-file'):p.add_argument('--'+n,required=True)
    p.add_argument('--spool',action='append',default=[]);a=p.parse_args()
    cmd=[sys.executable,'-B',str(W/'prepare_master_packet_publication.py'),'--name',a.name,'--head',a.head,
         '--previous',a.previous,'--phase',a.phase,'--status-patch',str(W/a.patch_file)]
    for item in json.loads((W/a.extras_file).read_bytes()):cmd+=['--extra',item]
    cmd+=['--extra',Path(__file__).name+'=scripts/master_run/'+Path(__file__).name]
    for item in a.spool:cmd+=['--spool',item]
    subprocess.run(cmd,check=True)
    md=W/a.name/'STATUS.md';parts=md.read_text(encoding='utf-8').split('\n\n')
    paragraph=(W/a.paragraph_file).read_text(encoding='utf-8').strip()
    matches=[i for i,x in enumerate(parts) if x.startswith('Stage5 detector execution') or x.startswith('Stage5 current execution')]
    assert len(matches)==1
    parts[matches[0]]=paragraph
    for i,x in enumerate(parts):
        if x.startswith('The G DriveFS view repair'):
            parts[i]='Historical preboot setup receipts remain preserved. Boot-sensitive runtime, topology, storage and interop checks are refreshed in new spools; their current states appear in the completed-step records below.'
    md.write_text('\n\n'.join(parts),encoding='utf-8')
    plan=W/(a.name+'_git_plan.json');value=json.loads(plan.read_bytes())
    for row in value['files']:
        q=Path(row['local_absolute_path']);row.update(bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest())
    plan.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
