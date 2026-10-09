"""Bind one SHA-pinned local archive build receipt and original sidecar to a public commit."""
from pathlib import Path
import argparse,hashlib,json,re
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-receipt',required=True,type=Path)
    p.add_argument('--build-sha256',required=True);p.add_argument('--source-controls-commit',required=True)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',a.source_controls_commit) and re.fullmatch('[0-9a-f]{64}',a.build_sha256)
    work=Path(__file__).resolve().parent;receipt=a.build_receipt.resolve()
    assert receipt.is_relative_to(work) and not receipt.is_symlink()
    raw=receipt.read_bytes();assert hashlib.sha256(raw).hexdigest()==a.build_sha256
    build=json.loads(raw);name=build['archive']
    assert re.fullmatch('master_[a-zA-Z0-9_.-]+[.]zip',name) and Path(name).name==name
    archive=receipt.parent/name;assert archive.is_file() and not archive.is_symlink()
    assert archive.stat().st_size==build['bytes'] and digest(archive)==build['sha256']
    side=archive.with_name(archive.name+'.sha256');side_raw=side.read_bytes()
    assert side_raw in [(build['sha256']+'  '+name+ending).encode('ascii') for ending in ('\n','\r\n')]
    rows=[{'name':archive.name,'bytes':build['bytes'],'sha256':build['sha256'],'local_absolute_path':str(archive)},
        {'name':side.name,'bytes':len(side_raw),'sha256':hashlib.sha256(side_raw).hexdigest(),'local_absolute_path':str(side)}]
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump({'repository':'serg-alexv/lab-rm-phylogenomics-196','tag':'master-run-storage-20261009-v1',
            'source_controls_commit':a.source_controls_commit,'build_receipt_sha256':a.build_sha256,'assets':rows},stream,indent=2);stream.write('\n')
    print(json.dumps({'assets':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
if __name__=='__main__':main()
