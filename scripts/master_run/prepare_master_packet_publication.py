"""Prepare one exact source/evidence packet publication without changing Git refs."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('name','head','previous','phase'):p.add_argument('--'+name,required=True)
    p.add_argument('--packet',action='append',default=[],help='work-relative mapping=SHA256; exact mapped files only')
    p.add_argument('--spool',action='append',default=[])
    p.add_argument('--extra',action='append',default=[])
    p.add_argument('--status-patch',type=Path)
    a=p.parse_args();extras=list(a.extra)
    for item in a.packet:
        rel,pin=item.rsplit('=',1);q=(W/rel).resolve()
        assert q.is_relative_to(W) and sha(q)==pin and not q.is_symlink()
        for row in json.loads(q.read_bytes())['files']:
            local=Path(row.get('local_path',row.get('path',row.get('local_absolute_path','')))).resolve()
            target=row.get('suggested_remote_path',row.get('suggested_repository_path',row.get('target')))
            assert local.is_relative_to(W) and not local.is_symlink() and local.is_file() and isinstance(target,str)
            assert local.stat().st_size==row['bytes'] and sha(local)==row['sha256']
            extras.append(local.relative_to(W).as_posix()+'='+target)
        extras.append(q.relative_to(W).as_posix()+'=reports/master_run/20261009/preparation/'+q.name)
    extras.append(Path(__file__).name+'=scripts/master_run/'+Path(__file__).name)
    if a.status_patch:
        patch=a.status_patch.resolve();assert patch.is_relative_to(W) and not patch.is_symlink()
        edits=json.loads(patch.read_bytes());assert isinstance(edits,dict)
        assert not set(edits)&{'authority','stage04_acceptance','stage04_tree_sha256','stage04_independent_remote_gate'}
        extras.append(patch.relative_to(W).as_posix()+'=reports/master_run/20261009/publication/'+patch.name)
    cmd=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head',a.head,'--name',a.name,
         '--previous-status',str(W/a.previous/'status.json'),'--previous-markdown',str(W/a.previous/'STATUS.md'),'--phase',a.phase]
    for spool in a.spool:cmd+=['--spool',spool]
    for extra in extras:cmd+=['--extra',extra]
    subprocess.run(cmd,check=True)
    if a.status_patch:
        status=W/a.name/'status.json';value=json.loads(status.read_bytes());value.update(edits)
        status.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    plan=W/(a.name+'_git_plan.json');value=json.loads(plan.read_bytes())
    for row in value['files']:
        local=Path(row['local_absolute_path']);row.update(bytes=local.stat().st_size,sha256=sha(local))
    assert len(value['files'])==len({r['target'] for r in value['files']})
    plan.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(value['files']),'bytes':sum(r['bytes'] for r in value['files'])}))
if __name__=='__main__':main()
