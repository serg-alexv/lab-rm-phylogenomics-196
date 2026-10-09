"""Publish exact original-package recovery controls and completed directory readback."""
from pathlib import Path
import argparse,hashlib,json
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-head',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    work=Path(__file__).resolve().parent;files=[]
    def add(local,target,pin=None):
        path=Path(local)
        if not path.is_absolute():path=work/path
        raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        assert 0<len(raw)<5*1024*1024 and (pin is None or pin==sha)
        files.append({'local_absolute_path':str(path),'target':target,'bytes':len(raw),'sha256':sha})
    raw=(work/'public_conda_packages01_final_index.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='f0b6f3a43909a43d5e409afb2f1edd5c04db6fc6f1eba00843534ac3ad9e503c'
    index=json.loads(raw)
    for row in index['controls'].values():add(row['local_path'],row['remote_path'],row['sha256'])
    base='reports/master_run/20261009/'
    add('public_conda_packages01_final_index.json',base+'cleanup/conda_packages01/final_index.json')
    for name in [Path(__file__).name,'prepare_master_conda_assets_plan.py','prepare_master_emptydir_assets_plan.py']:
        add(name,'scripts/master_run/'+name)
    pairs={
        'public_conda_continuation01_source_review.json':'cleanup/conda_packages01/CONTINUATION_SOURCE_REVIEW.json',
        'old_scientific_emptydirs01_readback_20261009T205057Z_9c38bcce/receipt.json':'cleanup/emptydirs01/REMOTE_READBACK.json',
        'master_emptydir_metadata_remote_source_review.json':'cleanup/emptydirs01/REMOTE_VERIFIER_SOURCE_REVIEW.json',
        'master_emptydir_assets_upload_plan.json':'cleanup/emptydirs01/UPLOAD_PLAN.json',
        'master_emptydir_assets_upload_receipt.json':'cleanup/emptydirs01/UPLOAD_RECEIPT.json',
        'master_recovery_progress02_git_objects.json':'publication/RECOVERY_PROGRESS02_GIT_OBJECTS.json',
        'master_recovery_progress02_remote_readback.json':'publication/RECOVERY_PROGRESS02_REMOTE_READBACK.json',
    }
    for name,target in pairs.items():add(name,base+target)
    assert len({r['target'] for r in files})==len(files)
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump({'expected_head':a.expected_head,
            'message':'Preserve all339 exact original Conda packages in two verified local shards; record fresh directory-proposal recovery',
            'files':files},stream,indent=2);stream.write('\n')
    print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
if __name__=='__main__':main()
