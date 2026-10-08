from pathlib import Path
import json,urllib.request,hashlib,time
import sys
kind=sys.argv[1] if len(sys.argv)>1 else 'host'
r=Path.cwd();j=json.loads((r/('.work/'+kind+'_solve.json')).read_text(encoding='utf-8-sig'));assert j['success']
packages=j['actions']['LINK'];cache=r/'.tools/mamba/pkgs';cache.mkdir(parents=True,exist_ok=True)
print('packages',len(packages),'total_bytes',sum(x['size'] for x in packages),flush=True)
lines=['@EXPLICIT'];start=time.monotonic()
for i,p in enumerate(packages,1):
    dest=cache/p['fn'];expected=p['sha256']
    if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest()!=expected:
        tmp=dest.with_suffix(dest.suffix+'.partial')
        for attempt in range(3):
            try:
                with urllib.request.urlopen(p['url'],timeout=120) as src,tmp.open('wb') as out:
                    while b:=src.read(1024*1024):out.write(b)
                assert hashlib.sha256(tmp.read_bytes()).hexdigest()==expected,p['fn']
                tmp.replace(dest);break
            except Exception:
                if attempt==2:raise
                time.sleep(3*(attempt+1))
    lines.append(p['url']+'#'+p['md5'])
    print(i,len(packages),p['fn'],flush=True)
(r/('.work/'+kind+'_explicit.txt')).write_bytes(('\n'.join(lines)+'\n').encode())
(r/('.work/'+kind+'_package_manifest.json')).write_bytes((json.dumps({'packages':packages,'elapsed_seconds':time.monotonic()-start,'route':'Official HTTPS package URLs downloaded on WD Windows; SHA256 verified; offline WSL linking'},indent=2)+'\n').encode())
