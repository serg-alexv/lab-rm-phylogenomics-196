"""Explicit project allowlist, credential/private-file scan, verified normal Git push."""
from pathlib import Path
import hashlib, re, subprocess
R=Path(__file__).resolve().parents[1]
PATTERNS=[rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{30,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'(?i)authorization\s*[:=]\s*[\"\x27]?bearer\s+[A-Za-z0-9._-]{20,}']
FORBIDDEN=['.private_run/','.tools/','.work/','data/raw_ncbi/','release_staging/']
def run(a):
    p=subprocess.run(a,cwd=R,capture_output=True,check=True)
    return p.stdout.decode('utf-8',errors='replace').strip()
def check(paths):
    items=[]
    for name in paths:
        if any(name.startswith(x) for x in FORBIDDEN):raise ValueError('Forbidden publication path '+name)
        p=R/name
        if not p.exists():raise ValueError('Absent publication path '+name)
        for f in ([p] if p.is_file() else p.rglob('*')):
            if not f.is_file():continue
            rel=f.relative_to(R).as_posix()
            if any(rel.startswith(x) for x in FORBIDDEN) or any(x in rel for x in ['codex_events','session_prompt','session_transcript','token_cache']):raise ValueError('Private artifact '+rel)
            if f.stat().st_size>20*1024*1024:raise ValueError('Large file belongs in Release: '+rel)
            b=f.read_bytes()
            if any(re.search(x,b) for x in PATTERNS):raise ValueError('Credential pattern in '+rel)
            items.append(rel)
    return items
def commit(paths,message):
    allowed=set(check(paths))
    existing=run(['git','diff','--cached','--name-only']).splitlines()
    if set(existing)-allowed:raise ValueError('Pre-existing staged paths outside current allowlist')
    run(['git','add','--']+paths)
    staged=set(run(['git','diff','--cached','--name-only']).splitlines())
    if staged-allowed:raise ValueError('Staged paths outside allowlist')
    if staged:run(['git','commit','-m',message])
    run(['git','push','origin','main']);head=run(['git','rev-parse','HEAD'])
    if run(['git','ls-remote','origin','refs/heads/main']).split()[0]!=head:raise ValueError('Remote main mismatch')
    return head
