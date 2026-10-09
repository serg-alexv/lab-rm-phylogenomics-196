"""Bind two original-package recovery shards and unchanged sidecars to public controls."""
from pathlib import Path
import argparse,hashlib,json,re
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-controls-commit',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',a.source_controls_commit)
    work=Path(__file__).resolve().parent;raw=(work/'public_conda_packages01_final_index.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='f0b6f3a43909a43d5e409afb2f1edd5c04db6fc6f1eba00843534ac3ad9e503c'
    index=json.loads(raw);rows=[]
    for r in index['archive_shards']:
        for name,size,sha,path in [(r['name'],r['bytes'],r['sha256'],r['local_path']),
            (r['sidecar_name'],r['sidecar_bytes'],r['sidecar_sha256'],r['sidecar_local_path'])]:
            local=Path(path);assert local.is_file() and local.name==name and local.stat().st_size==size
            rows.append({'name':name,'bytes':size,'sha256':sha,'local_absolute_path':str(local)})
    assert len(rows)==4 and len({r['name'] for r in rows})==4
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump({'repository':'serg-alexv/lab-rm-phylogenomics-196','tag':'master-run-storage-20261009-v1',
            'source_controls_commit':a.source_controls_commit,'assets':rows},stream,indent=2);stream.write('\n')
    print(json.dumps({'assets':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
if __name__=='__main__':main()
