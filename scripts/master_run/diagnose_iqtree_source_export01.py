"""Recover and compare one exact original Git blob with its codeload export."""
from pathlib import Path
import base64,hashlib,json,subprocess,tarfile
work=Path(__file__).resolve().parent;out=work/'iqtree314_source01_20261009T204525Z_40601c75'
blob='4b5d6aa580496004b342d8d49cbe8f6629e835f8'
reply=json.loads(subprocess.run(['gh','api','repos/iqtree/iqtree3/git/blobs/'+blob],
    capture_output=True,check=True,timeout=60).stdout)
original=base64.b64decode(reply['content']);assert reply['encoding']=='base64'
assert len(original)==reply['size']==249
assert hashlib.sha1(b'blob 249\0'+original).hexdigest()==blob
with tarfile.open(out/'iqtree3-63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de.tar.gz','r:gz') as archive:
    exported=archive.extractfile('iqtree3-63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de/terraphast/appveyor.yml').read()
assert len(exported)==264 and original.count(b'\r\n')==0 and exported.count(b'\r\n')==15
assert exported.replace(b'\r\n',b'\n')==original
directory=out/'original_git_blobs';directory.mkdir(exist_ok=False)
with (directory/(blob+'.blob')).open('xb') as stream:stream.write(original)
record={'state':'ONE_EXACT_GIT_BLOB_RECOVERED_EXPORT_CRLF_DIFFERENCE_CONFIRMED',
    'repository':'https://github.com/iqtree/iqtree3','commit':'63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de',
    'path':'terraphast/appveyor.yml','git_blob':blob,'original_bytes':249,'exported_bytes':264,
    'original_sha256':hashlib.sha256(original).hexdigest(),'exported_sha256':hashlib.sha256(exported).hexdigest(),
    'exact_difference':'15 original LF line endings exported as CRLF',
    'original_blob_file':str(directory/(blob+'.blob')),'archive_edited':False,
    'full_source_acceptance':'NOT_CREATED','payload_execution':0}
with (out/'export_diagnosis.json').open('x',encoding='utf-8') as stream:
    json.dump(record,stream,indent=2);stream.write('\n')
print(json.dumps(record))
