"""Publish only closed current G diagnosis/mount receipts, no actual effects."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def main():
    name='master_gview55'
    review='stage5_gdrive_postprofile_actual_pair_independent_review01.json'
    raw=(W/review).read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='0b0fefaeb774b3514a00d294eff461780f0acc22c25e30acd6499d3931afcd69'
    assert json.loads(raw)['state'].startswith('PASS_')
    patch={'stage5_gdrive_current':'PASS_CURRENT_BOOT_SEPARATE_DIAGNOSIS_AND_EXACT_MOUNT; 1ec2380d; original unlock and no STOP',
      'stage5_gdrive_actual_independent_review_sha256':hashlib.sha256(raw).hexdigest(),
      'stage5_current_stop_sha256':None,
      'stage5_current_linux_boot_id':'f0ffcebc-4901-479d-9559-89d45e9cfa38'}
    extras=[review+'=reports/master_run/20261009/postboot01/'+review,
      'review_stage5_gdrive_postprofile_actual_pair01.py=scripts/master_run/review_stage5_gdrive_postprofile_actual_pair01.py',
      'master_storage54_remote_readback.json=reports/master_run/20261009/publication/master_storage54_remote_readback.json',
      Path(__file__).name+'=scripts/master_run/'+Path(__file__).name]
    paragraph='Stage5 current execution: current-boot G visibility PASS after a separate missing-drive diagnosis and one exact mount. Both actual scopes retain native/WSL closure, original explicit unlock and unchanged controls; independent C byte/lifecycle review PASS. Storage06 is separately accepted. Runtime08 and DriveFS04 actual checks passed and await their publication checkpoints; UNC03 precedes the first full-method genome. Detector execution and production curation remain NOT_RUN. Accepted Stage4 is unchanged. Installed-runtime/VM capture, splitting and cold restoration remain pending; the host is not wipe-ready.\n'
    for suffix,value in [('patch.json',patch),('extras.json',extras)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','5351838deceebfa81326eae200d62b63c67af6b8','--previous','master_storage54',
      '--phase','current boot G diagnosis and exact mount independently closed PASS',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json',
      '--spool','stage5_gdrive_view_ca28ad9a9d8d4e668881dd168fcc0f60',
      '--spool','stage5_gdrive_view_c5848c89d3804d8cabe407d7dd354da0'],check=True)
if __name__=='__main__':main()
