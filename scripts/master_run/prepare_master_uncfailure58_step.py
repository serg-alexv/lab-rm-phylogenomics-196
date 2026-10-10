"""Publish preserved FAILED UNC03 scope and reviewed inactive diagnostic/cold sources."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def main():
    name='master_uncfailure58'
    peer='stage5_unc03_failed_scope_independent_review01.json'
    raw=(W/peer).read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='a3beba2bddf24c460c61dfe395caa680a600ffdc7314f06d3219bc8c457561cd'
    assert json.loads(raw)['state'].startswith('PASS_')
    result=json.loads((W/'stage5_unc_bind_actual_postiq_03/result.json').read_bytes())
    assert result['state']=='FAILED'
    extras=[peer+'=reports/master_run/20261009/postboot01/'+peer,
      'review_stage5_unc03_failed_scope01.py=scripts/master_run/review_stage5_unc03_failed_scope01.py',
      'master_runtime57_remote_readback.json=reports/master_run/20261009/publication/master_runtime57_remote_readback.json',
      Path(__file__).name+'=scripts/master_run/'+Path(__file__).name,
      'stage5_first_genome_curation_path01.md=reports/master_run/20261009/postboot01/stage5_first_genome_curation_path01.md',
      'stage5_first_genome_curation_path01.json=reports/master_run/20261009/postboot01/stage5_first_genome_curation_path01.json']
    packets=[('stage05_cold_owner_source_preparation02/PUBLIC_MAPPING.json','d6017a52e7a4616ff1a1670ffa4ba0b44799ed4687ae989eb5040a76388e83cc'),
      ('stage05_unc03_diagnostic_source_preparation01/PUBLIC_MAPPING.json','7ba1d751e7c0c985a2bdb100c00f576037a6b76f2c13ad9a2446aa0852651578')]
    for packet,pin in packets:
        mapping=W/packet;assert hashlib.sha256(mapping.read_bytes()).hexdigest()==pin
        for row in json.loads(mapping.read_bytes())['files']:
            path=Path(row['local_path']).resolve();assert path.is_relative_to(W)
            data=path.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
            extras.append(path.relative_to(W).as_posix()+'='+row['repository_path'])
        extras.append(packet+'=reports/master_run/20261009/preparation/'+mapping.parent.name+'_PUBLIC_MAPPING.json')
    patch={'stage5_unc_current':'FAILED03_CLOSED_SCOPE; LINUX_PREPARED_PASS; WINDOWS_WORKER_EXIT1_EMPTY_JOB; EXACT_CAUSE_UNRECORDED; DIAGNOSTIC_REQUIRED',
      'stage5_unc03_failed_scope_independent_review_sha256':hashlib.sha256(raw).hexdigest(),
      'stage5_current_stop_sha256':None,
      'stage5_unc03_diagnostic_source_current':'PASS_REVIEWED_SOURCE_ONLY_c0458522; ACTUAL_READONLY_DIAGNOSIS_NOT_RUN',
      'stage5_cold_owner_current':'PASS_CORRECTED_SOURCE_ONLY_V2; ACTUAL_COLD_CAPTURE_RESTORE_SPLIT_NOT_RUN',
      'stage5_cold_owner_v2_source_independent_review_sha256':'0546f2cbdd8f1fc4b25be8bb9faf1725b15ac038bf00eaed7b2796475203b0b9'}
    paragraph='Stage5 current execution: UNC03 FAILED after a successful current-boot Linux sentinel preparation. The Windows worker exited1; retained terminal, empty named Job and original explicit unlock prove the failed scope closed. Independent review PASS confirms closure only; the unrecorded worker cause and possible partial Windows sentinel remain unresolved. Toolchain07, runtime08, interop05, storage06 and DriveFS04 passed; no detector or production curation ran. Exact read-only diagnosis is next. Corrected cold source v2 passed pure/source review only; no installed-runtime/VM capture, splitting or restore ran. Accepted Stage4 is unchanged; the host is not wipe-ready.\n'
    for suffix,value in [('patch.json',patch),('extras.json',extras)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','a8219fb7a8821769e740840276e02b1f13e597aa','--previous','master_runtime57',
      '--phase','UNC03 failed scope independently closed; corrected cold v2 source only',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json',
      '--spool','stage5_unc_bind_actual_postiq_03'],check=True)
if __name__=='__main__':main()
