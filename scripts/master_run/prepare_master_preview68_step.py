"""Publish independently reviewed provisional figure adapter before actual rendering."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    name='master_preview68';m=W/'stage06_live_preview_source_preparation01/PUBLIC_MAPPING.json'
    assert sha(m)=='ba4dd803866823c5e43fa2106eda6fd9ebcdbc660a17ff074116ef92021047d6'
    extras=[Path(__file__).name+'=scripts/master_run/'+Path(__file__).name,
      'master_readiness67_remote_readback.json=reports/master_run/20261009/publication/master_readiness67_remote_readback.json']
    for r in json.loads(m.read_bytes())['files']:
        p=Path(r.get('local_path',r.get('path'))).resolve()
        assert p.is_relative_to(W) and sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
        target=r.get('repository_path',r.get('suggested_repository_path',r.get('suggested_remote_path',r.get('target'))));assert target
        extras.append(p.relative_to(W).as_posix()+'='+target)
    extras.append(m.relative_to(W).as_posix()+'=reports/master_run/20261009/preparation/stage06_live_preview_PUBLIC_MAPPING.json')
    patch={'stage6_live_preview':'PASS_INDEPENDENT_SOURCE_REVIEW_EXACT196_TREE_OPTIONAL_ACCEPTED_CLOSED4CELLS_PENDING_NA_WATERMARK_ACTUAL_RENDER_NOT_RUN',
      'incremental_stage5_stage6_decision':'IMPLEMENT_EXISTING_PER_GENOME_CLOSED_RAW_AND_INDEPENDENT_CURATION_SNAPSHOTS; FINAL196_784_GATE_PRESERVED'}
    paragraph='Incremental downstream decision: use the existing one-genome Stage5 owner, independently closed raw search and independently accepted four-cell curation snapshots to update a separate provisional Stage6 figure. This does not require waiting for unrelated queue leaves; the accepted full196 Stage4 tree is already complete. The new adapter reuses unchanged geometry and vector/iTOL exporters, pins the accepted tree/panel/readback, and accepts only genuine independently accepted closed four-cell snapshots. Every missing genome remains NOT_RUN/NA with separate execution metadata, explicit PREVIEW_PENDING_SCIENTIFIC_COMPLETION watermark and all final acceptance flagsfalse. Six focused tests and14 independent checks passed; actual master rendering has not run. The unchanged final196/784 curation and figure gates remain required. Current first genome remains prepared in pre-search resource wait; accepted native results, final biology and VM recovery are incomplete.\n'
    for suffix,val in [('extras.json',extras),('patch.json',patch)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(val,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','fd0a30e46bd9e64f17a4b00c7dcdd76852bf04b6','--previous','master_readiness67',
      '--phase','Publish reviewed incremental provisional Stage6 adapter preserving final scientific gates',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json'],check=True)
if __name__=='__main__':main()
