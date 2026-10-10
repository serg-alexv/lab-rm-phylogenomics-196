"""Publish fresh interop closure and exact independently reviewed G08 source."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    name='master_interopg72';maps={
      'stage5_gdrive_checked_unlock_source_preparation01/PUBLIC_MAPPING.json':'8e012e8b1563dc55549606d4e79d2497322d1ba1ae2d8c023fa0ed376844581d',
      'stage05_gdrive_postfallback_derived_source01/PUBLIC_MAPPING.json':'7c2e102ebefa148117299218b4962b311908e8ad5476b34267fa4b6fca5a595f'}
    assert sha(W/'stage5_interop06_postfallback_independent_review.json')=='4ab673abf3d4e73b555d1a91e19c93477fb9a7893313702e31cc656f5a68e856'
    extra={}
    def add(p,t):
        p=Path(p).resolve();assert p.is_relative_to(W)
        if t in extra:assert sha(p)==sha(extra[t])
        extra[t]=p
    add(__file__,'scripts/master_run/'+Path(__file__).name)
    add(W/'master_boot71_remote_readback.json','reports/master_run/20261009/publication/master_boot71_remote_readback.json')
    add(W/'stage5_interop06_postfallback_independent_review.json','reports/master_run/20261009/stage5_postfallback_boot/stage5_interop06_postfallback_independent_review.json')
    for rel,pin in maps.items():
        m=W/rel;assert sha(m)==pin
        for r in json.loads(m.read_bytes())['files']:
            p=Path(r.get('local_path',r.get('path'))).resolve();assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
            t=r.get('repository_path',r.get('suggested_repository_path',r.get('suggested_remote_path',r.get('target'))));assert t
            add(p,t)
        add(m,'reports/master_run/20261009/preparation/'+m.parent.name+'_PUBLIC_MAPPING.json')
    extras=[p.relative_to(W).as_posix()+'='+t for t,p in extra.items()]
    patch={'stage5_interop06':'PASS_ACTUAL_THREE_FIXTURES_AND_INDEPENDENT_CURRENT_BOOT_CLOSURE',
      'stage5_gdrive08_source':'PASS_ACTUAL08_SIX_PIN_REFRESH_AND_CHECKED_UNLOCK_VARIANT_INDEPENDENT_SOURCE_REVIEW; ACTUAL_G_NOT_RUN',
      'stage5_postfallback_boot':'TOOLCHAIN08_INTEROP06_PASS; G_STORAGE_DRIVEFS_RUNTIME_BACKING_UNC_PENDING'}
    paragraph='Stage5 current execution: fresh toolchain08 and interop06 gates actually pass on Linuxboot8cca020a-71b2-4163-92dc-6087df12dd45. All three interoperability fixtures(normalexit, leaseexpiry and escapeddescendant) independently prove native/kernel/retainedclient closure and originalunlock. The exact G08 source has now been generated from six actual accepted toolchain08 receipt hashes, with the reviewed checked-unlock/receipt-beforeSTOP-clear finalizer. Independent source review passes byte recipes, unchanged non-WindowsG ASTs, currentboot proof and defaultNOOP; operativeSHAa5efd24a17655324b8a03d13bf74e06f77195cb401ca9db8a3f73f94e1ab8ada. Actual Gdiagnosis/mount has not run. The prepared52object accession namespace is preserved for a narrowly reviewed storage rebind; remaining boot-sensitive gates must pass before the first search. Guest memory observation exceeds the former admission threshold, but native capacity is not yet measured. Accepted Stage4 and provisional196tip/784NA figure remain durable; finalbiology/figure andVM recovery incomplete.\n'
    for suffix,v in [('extras.json',extras),('patch.json',patch)]: (W/(name+'_'+suffix)).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','3492c0fc83cbfe2b527f9e58aac1fb711e4a3603','--previous','master_boot71',
      '--phase','Verify fresh interop closure and publish exact checked-unlock G08 source',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json',
      '--spool','stage5_interop_actual_postiq_06'],check=True)
if __name__=='__main__':main()
