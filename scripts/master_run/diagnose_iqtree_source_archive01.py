"""Inspect source-archive metadata differences; extract and execute nothing."""
from pathlib import Path
import json, tarfile
work=Path(__file__).resolve().parent
out=work/'iqtree314_source01_20261009T204525Z_40601c75'
tree=json.loads((out/'iqtree3_git_tree.json').read_bytes())
blobs={r['path']:r for r in tree['tree'] if r['type']=='blob'}
rows=[]
with tarfile.open(out/'iqtree3-63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de.tar.gz','r:gz') as archive:
    for item in archive:
        if item.isdir():continue
        rel=item.name.split('/',1)[1];expected=blobs.get(rel)
        if expected is None or (not item.issym() and (not item.isfile() or item.size!=expected['size'])):
            rows.append({'path':rel,'tar_type':item.type.decode('ascii'),'tar_bytes':item.size,
                         'git':expected,'tar_link':item.linkname})
require_bound=len(rows)<30
if not require_bound:raise ValueError('Unexpected mismatch bound')
receipt={'state':'METADATA_ONLY_SOURCE_SIZE_TYPE_DIAGNOSIS','mismatches':rows,
         'extraction':0,'payload_execution':0}
with (out/'metadata_diagnosis.json').open('x',encoding='utf-8') as stream:
    json.dump(receipt,stream,indent=2);stream.write('\n')
print(json.dumps(receipt))
