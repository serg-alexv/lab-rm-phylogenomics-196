"""Publish actual reviewed WSL fallback and its unchanged exact retained receipts."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    name='master_profile70';m=W/'stage05_host_profile_fallback_actual01/PUBLIC_MAPPING.json'
    assert sha(m)=='8d50efc5dc86207a3fefc47936d4f4a55acfa2422e98012a50a4cf0e2738b7dc'
    extras=[Path(__file__).name+'=scripts/master_run/'+Path(__file__).name,
      'master_previewclosed69_v2_remote_readback.json=reports/master_run/20261009/publication/master_previewclosed69_v2_remote_readback.json']
    binary=[]
    for r in json.loads(m.read_bytes())['files']:
        p=Path(r.get('local_path',r.get('path'))).resolve()
        assert p.is_relative_to(W) and sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
        target=r.get('repository_path',r.get('suggested_repository_path',r.get('suggested_remote_path',r.get('target'))));assert target
        try:p.read_bytes().decode('utf-8');istext=p.suffix in ('.py','.ps1','.md','.json','.jsonl','.txt','.tsv')
        except UnicodeDecodeError:istext=False
        if istext:extras.append(p.relative_to(W).as_posix()+'='+target)
        else:binary.append({'local_absolute_path':str(p),'target':target,'bytes':r['bytes'],'sha256':r['sha256'],'transport_encoding':'base64'})
    extras.append(m.relative_to(W).as_posix()+'=reports/master_run/20261009/preparation/host_profile_fallback_actual_PUBLIC_MAPPING.json')
    patch={'stage5_wsl_fallback':'PASS_ACTUAL_3584MB_GUI_OFF_RETAINED_SHUTDOWN_ALL_DISTROS_STOPPED_CHECKED_UNLOCK_THEN_STOP_CLEAR_INDEPENDENT_PEER',
      'stage5_postfallback_boot':'NOT_OBSERVED; ALL_SIX_FRESH_BOOT_GATES_REQUIRED; PREPARED_NATIVE_DATA_PRESERVED'}
    paragraph='Stage5 current execution: the reviewed WSL fallback actually passed. The exact host profile changes memory3GB to3584MB and guiApplications true tofalse, retaining all other bytes; currentSHAe48eaf30b4da7cf75ec717f7a643235efbb9561f5e1680480ae14314f046d6e4. Five fixed retained Windows clients exited0, all18legacytasks remainedDisabled, Ubuntu registration/rootUID0 was preserved, the actual running-distro query was empty, and all distros stopped. The original checked unlock/readback precedes exact ownedSTOP removal and finalPASS. Independent C-only review joins the unchanged prior capacity02 closed/prepared evidence and all actualclientreceipts. No fresh Linux boot or native capacity benefit is yet claimed; toolchain, interop, Gsession/storage, DriveFS, runtime and backingUNC are qualified afresh next, preserving the7.3MiB prepared accession bundle and scientificidentity. The accepted Stage4 and actual provisional196tip/784NA circularfigure are published. Final biology/figure and VM cold recovery remain incomplete.\n'
    for suffix,val in [('extras.json',extras),('patch.json',patch)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(val,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','13a847843077b9f399f76f86e734ce7720debe9d','--previous','master_previewclosed69_v2',
      '--phase','Verify actual3584MiB WSL profile and all-distro shutdown before fresh runtime boot',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json'],check=True)
    q=W/(name+'_git_plan.json');doc=json.loads(q.read_bytes());doc['files']+=binary
    assert len(doc['files'])==len({r['target'] for r in doc['files']})
    q.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
