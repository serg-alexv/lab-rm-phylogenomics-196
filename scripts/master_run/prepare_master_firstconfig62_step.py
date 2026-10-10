"""Publish exact first-genome backing config and independent acceptance only."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys
W=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--review',required=True);p.add_argument('--review-sha256',required=True)
    p.add_argument('--checker',required=True);a=p.parse_args()
    raw=(W/a.review).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==a.review_sha256
    assert json.loads(raw)['state'].startswith('PASS_')
    pins={'stage5_actual_request_backing_01.json':'96fc9e6a9893fb56122f701378aa49eb3f50773b797d6cdf4c9130548be3cb44',
      'stage5_actual_backing_01.json':'30a86eb18cddc69eb0cfbdd3ae93473ec54812cd5a859ededd25af01fb737dfa'}
    for file,pin in pins.items():assert hashlib.sha256((W/file).read_bytes()).hexdigest()==pin
    receipt=json.loads((W/'stage5_actual_backing_01_build_receipt.json').read_bytes())
    assert receipt['state']=='PASS_CONFIG_AND_WINDOWS_ADMISSION_ONLY' and receipt['explicit_original_byte_unlock'] is True
    name='master_firstconfig62'
    extras=[file+'=reports/master_run/20261009/first_genome01/'+file for file in
      [*pins,'stage5_actual_backing_01_build_receipt.json',a.review]]
    extras += [a.checker+'=scripts/master_run/'+Path(a.checker).name,
      Path(__file__).name+'=scripts/master_run/'+Path(__file__).name,
      'master_backingactual61_remote_readback.json=reports/master_run/20261009/publication/master_backingactual61_remote_readback.json']
    patch={'stage5_first_full_method_genome':'PASS_FRESH_EXACT_CONFIG_AND_WINDOWS_ADMISSION; ACTUAL_NATIVE_RUN_PENDING_GCF_000009425.1',
      'stage5_actual_first_genome_config_sha256':pins['stage5_actual_backing_01.json'],
      'stage5_actual_first_genome_config_independent_review_sha256':a.review_sha256,
      'stage5_current_stop_sha256':None}
    paragraph='Stage5 current execution: all six current-boot setup gates passed, including the fresh two-way backing UNC qualification with exact cleanup and independent acceptance. The first full-method config for GCF_000009425.1 was built under the original workflow lock and passed fresh Windows admission. Two threads, one serial genome, full PADLOC5027 and DefenseFinder, accepted runtime f64edf and storage06 are unchanged. The explicit bounded resource wait is1800s with unchanged reserve/admission thresholds. Actual native admission/peak measurement and production curation remain pending. Accepted Stage4 is unchanged. Installed-runtime and VM capture/splitting/restore are pending; the host is not wipe-ready.\n'
    for suffix,value in [('patch.json',patch),('extras.json',extras)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','2aa249403738f61ef67b2f52d29cb3ca209fe78f','--previous','master_backingactual61',
      '--phase','first full-method genome actual config and fresh Windows admission independently accepted',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json'],check=True)
if __name__=='__main__':main()
