"""Publish exact closed setup attempts and inactive recovery preparations; no refs."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
NAME='master_operational25'
HEAD='464c039770e0c9a3440d2bbb8fe9fcd0287426a8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    extras=[]
    packets=[('stage5_closed_genome_archive_preparation.json','de3dce11c0f517e24619641dda48f99df295c58eb453c10fc1e2db074e281de2','local_path','suggested_remote_path'),
             ('stage5_runtime_recovery_preparation01/PUBLIC_MAPPING.json','6b27b8435920b271797158b8314831750295d05b3c867c810902547a06e18546','path','suggested_repository_path')]
    for rel,pin,localkey,remotekey in packets:
        p=W/rel;assert sha(p)==pin
        packet=json.loads(p.read_bytes())
        for row in packet['files']:
            q=Path(row[localkey]);assert q.is_relative_to(W) and q.is_file() and not q.is_symlink()
            assert len(q.read_bytes())==row['bytes'] and sha(q)==row['sha256']
            extras.extend(['--extra',str(q.relative_to(W)).replace('\\','/')+'='+row[remotekey]])
        extras.extend(['--extra',rel+'=reports/master_run/20261009/preparation/'+p.name])
    for rel,target in [('master_runtime_compat24c_git_objects.json','prior_source_objects24c.json'),
                       ('master_runtime_compat24c_remote_readback.json','prior_source_remote_readback24c.json'),
                       (Path(__file__).name,Path(__file__).name)]:
        extras.extend(['--extra',str(rel)+'='+('scripts/master_run/' if str(rel).endswith('.py') else 'reports/master_run/20261009/publication/')+target])
    cmd=[sys.executable,'-B',str(W/'prepare_master_operational_update.py'),'--expected-head',HEAD,
         '--name',NAME,'--previous-status',str(W/'master_runtime_compat24c/status.json'),
         '--previous-markdown',str(W/'master_runtime_compat24c/STATUS.md'),
         '--phase','Record actual toolchain04 and libc pidfd interop03 PASS; preserve closed runtime05 resource and storage02 prelaunch failures; publish inactive recovery preparations']
    for spool in ['stage5_setup_toolchain_actual_postiq_04','stage5_setup_runtime_actual_postiq_05',
                  'stage5_interop_actual_postiq_03','stage5_setup_storage_actual_postiq_02']:
        cmd.extend(['--spool',spool])
    subprocess.run(cmd+extras,check=True)
    out=W/NAME;sp=out/'status.json';s=json.loads(sp.read_bytes())
    s.update(stage5_setup_preparation='CURRENT_PEER_REVIEWED_PINS_ACTUAL_TOOLCHAIN04_AND_INTEROP03_PASS',
             stage5_runtime_discovery='ACTUAL05_FAILED_WINDOWS_COMMIT_RESERVE_FULLY_CLOSED_NO_CANDIDATE; targeted hash hints did not prevent failure; phase/cause unmeasured',
             stage5_resource_pressure='Latest actual runtime05 commit1844224000 below unchanged1879048192 setup gate. User now explicitly authorizes nonessential app/service cleanup. Source preparation before exact app closure; reserves unchanged.',
             stage5_interop='ACTUAL03_PASS_ALL_THREE_REAL_RETAINED_CONDA_PIDFD_FIXTURES_WINDOWS_LEASE_EXPIRY_AND_ESCAPED_DESCENDANT_CLOSURE',
             stage5_pidfd_compatibility='ACTUAL_RETAINED_CONDA_INTEROP03_PASS_e5be8997',
             stage5_storage='ACTUAL02_FAILED_BEFORE_NATIVE_LAUNCH_G_UNDERLAY_NOT_VISIBLE_FROM_LINUX; Windows empty underlay recorded; G mount cause pending actual diagnosis; fully closed',
             stage5_current_stop_sha256='NO_UNPROVEN_STANDARD_OR_INTEROP_STOP_AFTER_CLOSED_ACTUAL04_05_03_02',
             host_resource_authority='Direct user authorization: adjust, reconfigure, cleanup and service control; nonessential app closure authorized. Preserve current execution control and remote-unverified scientific artifacts.',
             host_wipe_ready=False)
    s['stage5_inactive_recovery_preparations']={
        'closed_genome_archive':'SOURCE_AND_SYNTHETIC_PEER_PASS_ONLY; actual capture/readback/canonical rehydration NOT_RUN; eviction not enabled',
        'installed_runtime':'SOURCE_AND_SYNTHETIC_PEER_PASS_ONLY; actual inventory/public audit/capture/remote/cold restore NOT_RUN; base OS/bootstrap equivalence pending'}
    sp.write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
    mdp=out/'STATUS.md';md=mdp.read_text(encoding='utf-8')
    md=md.replace('The latest setup finalizer and current configuration source pins pass independent review and19pure checks. Actual replacement setup remains pending; previous failed scopes and their lost terminal uncertainty are preserved.',
                  'Current reviewed setup pins produced actual toolchain04 PASS and all three retained Conda interop03 fixtures PASS. Runtime05 failed the unchanged Windows commit reserve and storage02 failed before native launch because the Windows G underlay was not visible in Linux. Both scopes are fully closed; diagnosis and host resource cleanup are underway. Earlier lost-terminal uncertainty remains preserved.')
    marker='\nCurrent gates: toolchain04 and interop03 PASS; runtime05 FAILED at commit1,844,224,000B below1,879,048,192B, with no runtime candidate; storage02 FAILED before native launch with Windows-empty/Linux-missing G underlay. All four scopes have retained closure and original unlock. The actual hash phase and host-cache cause are unmeasured; targeted cache hints did not prevent this failure. User authorizes nonessential host app/service cleanup; reserve gates remain unchanged.\n\nClosed-genome and installed-runtime recovery packets are inactive source preparations. No actual runtime capture, cold restoration, genome archive or eviction gate has passed. Scientific detector/curation/figure execution remains NOT_RUN and the host is not wipe-ready.\n'
    mdp.write_text(md+marker,encoding='utf-8')
    pp=W/(NAME+'_git_plan.json');plan=json.loads(pp.read_bytes())
    for row in plan['files']:
        q=Path(row['local_absolute_path']);row['bytes']=q.stat().st_size;row['sha256']=sha(q)
    assert len(plan['files'])==len({r['target'] for r in plan['files']})
    pp.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(plan['files']),'bytes':sum(r['bytes'] for r in plan['files'])}))
if __name__=='__main__':main()
