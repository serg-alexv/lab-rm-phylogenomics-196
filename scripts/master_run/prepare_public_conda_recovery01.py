"""Prepare the exact one-time resource-stop continuation; no network/payload copy."""
from pathlib import Path
import hashlib,importlib.util,json,os,stat

WORK=Path(__file__).resolve().parent
OLD=WORK/'public_conda_packages01_20261009T203038Z_f8ac9b61'
BASE_SHA='e94e2d59e6d4b91353916db7bdf8485ecff0eba181f644e534a7e742e1e5bffc'
FAILURE_SHA='001442792f652547bf79a85f8dee7ab0b5e3fddefdcbf5de47882b2b97b85c4b'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    base=WORK/'acquire_public_conda_packages01.py';assert sha(base)==BASE_SHA
    spec=importlib.util.spec_from_file_location('base',base);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    _,_,packages=A.selected_packages();receipt=OLD/'build_receipt.json';assert sha(receipt)==FAILURE_SHA
    failed=json.loads(receipt.read_text());assert failed['state']=='FAILED_PRESERVED_PARTIALS_NO_AUTOMATIC_RETRY'
    assert failed['verified_packages']==95 and failed['verified_package_bytes']==237225880
    assert failed['error']['message']=='Resource reserve or C disk gate failed; preserved partials, no automatic resume'
    ledger=OLD/'downloaded_packages.jsonl';completed=[json.loads(x) for x in ledger.read_text().splitlines()]
    assert len(completed)==95
    for row,pin in zip(completed,packages):
        assert row['state']=='PASS_EXACT_ORIGINAL_PACKAGE' and row['sha256']==pin['sha256'] and row['bytes']==pin['bytes'] and row['url']==pin['url']
        path=Path(row['path']);assert path==OLD/'packages'/pin['sha256']/pin['filename']
        s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not s.st_file_attributes&1024
        assert A.signature(s)==tuple(row['original_identity'])
    errors=OLD/'download_errors.jsonl';err=[json.loads(x) for x in errors.read_text().splitlines()];assert len(err)==1
    partial=Path(err[0]['partial']);pin=packages[95]
    assert err[0]['sha256']==pin['sha256'] and partial==OLD/'packages'/pin['sha256']/(pin['filename']+'.partial')
    ps=partial.lstat();assert stat.S_ISREG(ps.st_mode) and ps.st_nlink==1 and not ps.st_file_attributes&1024
    controls={}
    for n in ('build_receipt.json','downloaded_packages.jsonl','download_errors.jsonl','resources.jsonl','package_index.json',
              'detector_package_manifest.json','host_package_manifest.json','acquire_public_conda_packages01.py','ATTRIBUTION_AND_RESTORE.txt','progress.json'):
        p=OLD/n;controls[n]={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    value={'schema':'MASTER_PUBLIC_CONDA_RESOURCE_STOP_RECOVERY_PLAN_V1','state':'PREPARED_NOT_RUN_FRESH_RESOURCE_ADMISSION_REQUIRED',
        'original_namespace':str(OLD),'failure_sha256':FAILURE_SHA,'base_source_sha256':BASE_SHA,'controls':controls,
        'completed':completed,'completed_count':95,'completed_bytes':237225880,'expected_package_count':339,'expected_package_bytes':660114049,
        'original_partial':{'path':str(partial),'sha256':sha(partial),'bytes':ps.st_size,'identity':A.signature(ps),
            'policy':'PRESERVE_UNCHANGED_NEVER_ADOPT;REDOWNLOAD_PINNED_PACKAGE_FROM_ZERO_IN_NEW_NAMESPACE'},
        'no_automatic_resume':True,'automatic_retries':0,'new_namespace_required':True,'http_range_requests':0,
        'source_payload_rehash_at_preparation':False,'fresh_full_source_SHA_required_before_reuse':True,
        'resource_reserve_bytes':A.RESERVE,'C_free_required_bytes':A.MIN_DISK,'streaming_readers':1,
        'package_installations':0,'package_extractions':0,'wsl_starts':0,'g_writes':0,'deletions':0}
    out=WORK/'public_conda_packages01_recovery_plan.json'
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'state':value['state'],'plan':str(out),'sha256':sha(out),'completed':95,'partial_preserved_bytes':ps.st_size}))
if __name__=='__main__':main()
