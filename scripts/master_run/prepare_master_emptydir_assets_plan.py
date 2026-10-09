"""Bind the frozen metadata-only directory proposal archive to its public controls."""
from pathlib import Path
import argparse,hashlib,json,re
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-controls-commit',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',a.source_controls_commit)
    work=Path(__file__).resolve().parent;directory=work/'master_old_scientific_emptydirs01'
    pins={'master_old_scientific_emptydirs01.zip':(438572,'656f515d069338e132a9c2ec46497e7388a55faaeb4c1e4aecca06ab37dfbd8d'),
        'master_old_scientific_emptydirs01.zip.sha256':(105,'f2ab2b9ec783f4658797d15873dd97f52a4bec27820a8daeb4eea899b26fe467')}
    rows=[]
    for name,(size,sha) in pins.items():
        path=directory/name;raw=path.read_bytes()
        assert len(raw)==size and hashlib.sha256(raw).hexdigest()==sha
        rows.append({'name':name,'bytes':size,'sha256':sha,'local_absolute_path':str(path)})
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump({'repository':'serg-alexv/lab-rm-phylogenomics-196','tag':'master-run-storage-20261009-v1',
            'source_controls_commit':a.source_controls_commit,'assets':rows},stream,indent=2);stream.write('\n')
    print(json.dumps({'assets':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
if __name__=='__main__':main()
