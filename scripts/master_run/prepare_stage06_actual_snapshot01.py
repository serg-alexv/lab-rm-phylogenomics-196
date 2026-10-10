"""Copy accepted remote-readback tree inputs into one explicit real provisional snapshot."""
from pathlib import Path
import hashlib,json,zipfile
W=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    remote=W/'stage04_primary196_independent_readback_20261009T221654Z_2262b4ce'
    receipt=(remote/'receipt.json').read_bytes();assert sha(receipt)=='f14b097aac1705c2632307eaadf423febdc3154cafe370aace78dd8196044d49'
    out=W/'stage06_actual_snapshot01';out.mkdir();inputs={}
    with zipfile.ZipFile(remote/'stage04-primary196-accepted.zip') as archive:
        for role,member,pin in [('tree','accepted/host.treefile','f886c0134ab662a05aae2b1c1a26ed364749af250400f769ce6e63f1f7a8ba19'),
          ('approved','accepted/accepted_approved_accessions.txt','85a0ada99ed980f0cf787410735389b6b0b553d456c47509a4a8d8b6e8efebd6')]:
            raw=archive.read(member);assert sha(raw)==pin
            p=out/Path(member).name
            with p.open('xb') as stream:stream.write(raw)
            inputs[role]={'path':str(p),'sha256':pin}
    p=out/'accepted_stage04_readback.json'
    with p.open('xb') as stream:stream.write(receipt)
    inputs['tree_acceptance']={'path':str(p),'sha256':sha(receipt)}
    snapshot={'schema':'RM_LIVE_PREVIEW_SNAPSHOT_V1',**inputs,'accepted_genomes':[],
      'pending':[{'accession':'GCF_000009425.1','execution_state':'RUNNING',
        'reason':'Prepared inputs; bounded first PADLOC admission pending at snapshot creation; no native search accepted.'}]}
    p=out/'snapshot.json'
    with p.open('x',encoding='utf-8') as stream:json.dump(snapshot,stream,indent=2);stream.write('\n')
    print(json.dumps({'snapshot':str(p),'sha256':sha(p.read_bytes()),'accepted_genomes':0,'final_figure_acceptance':False}))
if __name__=='__main__':main()
