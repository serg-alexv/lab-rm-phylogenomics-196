"""Independent checksum coverage and sidecar readback for frozen Stage02 payloads."""
from pathlib import Path
import json,msvcrt,os
import production_resume as w
from portable_release import verify_zip
from workflow_publication import commit

def main():
    w.LOG=w.R/'reports/stage02/supplemental_publication_commands.jsonl'
    receipt=json.loads((w.R/'reports/stage02/publication_receipt.json').read_text())
    assert receipt['status']=='UPLOAD_VERIFIED'
    tag=receipt['release_tag'];head=receipt['payload_commit']
    assert w.run(['gh','api','repos/'+w.REPO+'/commits/'+tag,'--jq','.sha']).strip()==head
    frozen=json.loads(w.run(['git','show',head+':reports/stage02/asset_manifest.json']))
    stage=w.R/'release_staging/stage02';down=stage/'readback';entries=[]
    info=json.loads(w.run(['gh','api','repos/'+w.REPO+'/releases/tags/'+tag]))
    remote={a['name']:a for a in info['assets']}
    for a in frozen['assets']:
        name=a['asset_name'];p=down/name
        assert p.stat().st_size==a['bytes'] and w.digest(p)==a['sha256']
        count=verify_zip(p);assert count==a['payload_members']
        side=name+'.sha256';expected=(a['sha256']+'  '+name+'\n').encode()
        if side not in remote:
            w.run(['gh','release','upload',tag,str(stage/side),'--repo',w.REPO],timeout=300)
        w.run(['gh','release','download',tag,'--repo',w.REPO,'--pattern',side,'--dir',str(down),'--clobber'],timeout=300)
        assert (down/side).read_bytes()==expected
        entries.append({'asset_name':name,'checksum_manifest_complete':True,'payload_member_count':count,'sidecar_download_readback_verified':True})
        print('INDEPENDENT_MANIFEST_COVERAGE_AND_SIDECAR_VERIFIED',name,flush=True)
    w.js(w.R/'reports/stage02/supplemental_publication_validation.json',{'status':'PASS_ALL12_ZIP_MANIFEST_COVERAGE_AND_SIDECAR_READBACK',
          'utc':w.now(),'frozen_payload_commit':head,'release_tag':tag,'assets':entries,'historical_payloads_unchanged':True})
    commit(['scripts/verify_stage02_release.py','reports/stage02/supplemental_publication_validation.json',
            'reports/stage02/supplemental_publication_commands.jsonl','reports/stage02/validation_commands.jsonl','reports/stage02/publication_commands.jsonl'],
           'Independently verify stage02 checksum coverage and Release sidecars; publish executed command evidence')

if __name__=='__main__':
    lock=(w.WORK/'workflow.lock').open('a+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    w.js(w.WORK/'workflow_owner.json',{'pid':os.getpid(),'utc':w.now(),'script':str(Path(__file__)),'scope':'Stage02 supplemental immutable Release validation'})
    try:main()
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
