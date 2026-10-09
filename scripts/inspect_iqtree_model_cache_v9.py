"""Read retained cache and version-tagged official implementation, no inference."""
import gzip, hashlib, json, re, urllib.request
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v9 as S

URL='https://raw.githubusercontent.com/iqtree/iqtree3/v3.1.4/main/phylotesting.cpp'

def main():
    with C.WorkflowLock(S.LOCK):
        S.pins();target=S.RUNTIME/'official_source/phylotesting_v3_1_4.cpp';target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with urllib.request.urlopen(URL,timeout=30) as response:raw=response.read(2*1024*1024)
            C.check(len(raw)<2*1024*1024,'Unexpected official source size');target.write_bytes(raw)
        text=target.read_text(encoding='utf-8');cache_path=S.OLD/'analyses/primary196/iqtree/host.model.gz'
        cache=gzip.decompress(cache_path.read_bytes()).decode('utf-8')
        lines=text.splitlines();patterns=['model_info.setFileName((string)params.out_prefix + ".model.gz")',
          'ok_model_file = model_info.load()','finishedFastMLTree','CandidateModelSet::test','restoreCheckpoint(&model_info)']
        refs={p:[i+1 for i,line in enumerate(lines) if p in line] for p in patterns}
        C.check(all(refs.values()),'Official version source semantic landmark missing')
        keys=re.findall(r'^\s*best_model_BIC:\s*(.+)$',cache,re.M)
        value={'utc':C.now(),'status':'OFFICIAL_SOURCE_AND_RETAINED_CACHE_INSPECTED_NO_NATIVE_REUSE_YET',
          'official_source_url':URL,'official_source_sha256':C.digest(target),'official_source_bytes':target.stat().st_size,
          'source_line_references':refs,'retained_cache_sha256':C.digest(cache_path),'retained_cache_bytes':cache_path.stat().st_size,
          'best_model_BIC_records':len(keys),'best_model_BIC_values':keys,
          'finishedFastMLTree_true':bool(re.search(r'^finishedFastMLTree:\s*true\s*$',cache,re.M)),
          'general_checkpoint':'ABSENT','native_cache_reuse':'NOT_OBSERVED_NEW_PRODUCTION_NOT_STARTED',
          'new_required_runtime_evidence':['Exact tool message restoring model checkpoint at the new prefix','Fast-ML checkpoint tree-restoration message',
            'New real native exit0 and unchanged four-scope scientific audit'],
          'interpretation':'Separate model cache loads independently of host.ckp.gz. Saved fast-ML tree state can restore the initial tree. Per-candidate model checkpoint restoration must be inspected; completed partition counts alone do not prove all per-partition work is skipped.',
          'scientific_jobs':0}
        C.atomic(S.REPORT/'model_cache_semantics.json',value)
        print(json.dumps({'status':value['status'],'best_model_BIC_records':len(keys),'source_sha256':value['official_source_sha256']}))

if __name__=='__main__':main()
