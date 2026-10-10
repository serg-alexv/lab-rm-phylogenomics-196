"""Publish real provisional vector figure and actual closed first-search deferral."""
from pathlib import Path
import base64,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    name='master_previewclosed69_v2';maps={
      'stage06_actual_preview01_publication01/PUBLIC_MAPPING.json':'97c2238ab8016e791208af5ae289d1bb60fef2a26db572f4fba5fa63a88e22e2',
      'stage05_postfallback_gate_route_source_preparation01/PUBLIC_MAPPING.json':'4e63b41049cf3429c1786d65d1e06ab39f8a513f90907dff49f08aab8c6b26e4'}
    extras=[Path(__file__).name+'=scripts/master_run/'+Path(__file__).name,
      'master_preview68_remote_readback.json=reports/master_run/20261009/publication/master_preview68_remote_readback.json',
      'stage5_first_capacity02_closed_independent_review.json=reports/master_run/20261009/stage5_capacity02_closure/stage5_first_capacity02_closed_independent_review.json',
      'review_stage5_first_capacity02_closed.py=scripts/master_run/review_stage5_first_capacity02_closed.py',
      'copy_stage5_capacity02_closed_evidence.py=scripts/master_run/copy_stage5_capacity02_closed_evidence.py']
    assert sha(W/'stage5_first_capacity02_closed_independent_review.json')=='e7cb6737c50e35c3119fe443d820b77174b2e0b8f3560c5303837b95e42ac2e9'
    binary=[]
    for rel,pin in maps.items():
        m=W/rel;assert sha(m)==pin
        for r in json.loads(m.read_bytes())['files']:
            p=Path(r.get('local_path',r.get('path'))).resolve()
            assert p.is_relative_to(W) and sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
            target=r.get('repository_path',r.get('suggested_repository_path',r.get('suggested_remote_path',r.get('target'))));assert target
            if p.suffix not in ('.py','.ps1','.md','.json','.jsonl','.txt','.tsv'):
                if 'content_base64' in r:assert base64.b64decode(r['content_base64'],validate=True)==p.read_bytes()
                binary.append({'local_absolute_path':str(p),'target':target,'bytes':r['bytes'],'sha256':r['sha256'],'transport_encoding':'base64'})
            else:extras.append(p.relative_to(W).as_posix()+'='+target)
        extras.append(rel+'=reports/master_run/20261009/preparation/'+m.parent.name+'_PUBLIC_MAPPING.json')
    for p in sorted((W/'stage5_capacity02_closed_native_copy').rglob('*')):
        if p.is_file():extras.append(p.relative_to(W).as_posix()+'=reports/master_run/20261009/stage5_capacity02_closure/'+p.relative_to(W/'stage5_capacity02_closed_native_copy').as_posix())
    patch={'stage5_first_full_method_genome':'DEFERRED_RESOURCE_NATURAL_CLOSURE_EXIT75_NO_NATIVE; SCIENTIFIC_IDENTITY_AND_PREPARED_BUNDLE_PRESERVED',
      'stage6_live_preview':'PASS_ACTUAL_PROVISIONAL_VECTOR_PDF_SVG_ITOL_INDEPENDENT_ARTIFACT_REVIEW_196TIPS_784NA_ZERO_CURATED_NO_FINAL_ACCEPTANCE',
      'stage5_wsl_fallback':'SOURCE_REVIEW_PASS_ACTUAL_CAPACITY02_CLOSURE_PUBLISHED_READY_EXPLICIT_RUN; FRESH_BOOT_GATES_REQUIRED'}
    paragraph='Stage5 current execution: capacity02 naturally expired its1800-second first-search admission and closed DEFERRED_RESOURCE at04:38:43UTC. Retained WSL exit75, inactive original lease, exact prepared scientific identity/full5027 execution freeze and original checked unlock independently pass; no detector launched. A C-only snapshot pins all52 backing objects/50 accession members and every regular payload SHA, with Windows UNC metadata explicitly projection-only. The reviewed3584MB/GUI-off WSL fallback is ready for root execution, followed by fresh boot-sensitive gates and preservation-checked rebind. Actual provisional Stage6 rendering now independently passes: accepted196-tip tree/389branches, four rings,784greyNOT_RUN/NA cells, genuine zeroaccepted-genome snapshot, matching vectorSVG/PDF scene, iTOL full-state strips and pending watermark. Visual inspection found no evident clipping. This is an actual provisional figure, never final biological acceptance. Incremental accepted closed-genome curations can update it while the queue proceeds. Final196searches/784curations, finalfigure and VM cold recovery remain incomplete.\n'
    for suffix,val in [('extras.json',extras),('patch.json',patch)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(val,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','13d34c9725bc9a852eac063c8a6b11f9561d7f37','--previous','master_preview68',
      '--phase','Publish actual provisional circular figure and independently closed prepared Stage5 resource deferral',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json',
      '--spool','stage5_owner_GCF_000009425_1_backing_capacity_02'],check=True)
    q=W/(name+'_git_plan.json');doc=json.loads(q.read_bytes());doc['files']+=binary
    assert len(doc['files'])==len({r['target'] for r in doc['files']})
    q.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(doc['files']),'binary_files':len(binary)}))
if __name__=='__main__':main()
