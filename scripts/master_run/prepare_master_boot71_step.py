"""Publish actual fresh toolchain boot and independent closed-scope acceptance."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def main():
    name='master_boot71';peer=W/'stage5_toolchain08_postfallback_independent_review.json'
    assert hashlib.sha256(peer.read_bytes()).hexdigest()=='af62d67c86aa3cfa42a1b24dd82ee2fc4aaa3ce7ae876aadd8a1fe60d078a742'
    mem=W/'stage5_postfallback_boot08_meminfo.txt';raw=Path(r'\\wsl.localhost\Ubuntu\proc\meminfo').read_bytes()
    with mem.open('xb') as stream:stream.write(raw)
    extras=[Path(__file__).name+'=scripts/master_run/'+Path(__file__).name,
      'master_profile70_remote_readback.json=reports/master_run/20261009/publication/master_profile70_remote_readback.json',
      peer.name+'=reports/master_run/20261009/stage5_postfallback_boot/'+peer.name,
      mem.name+'=reports/master_run/20261009/stage5_postfallback_boot/'+mem.name]
    patch={'stage5_postfallback_boot':'TOOLCHAIN08_PASS_INDEPENDENT_EXACT_SOURCE_CLOSURE; BOOT8cca020a-71b2-4163-92dc-6087df12dd45; FIVE_MORE_GATE_ACCEPTANCES_PENDING',
      'stage5_toolchain08_proof_sha256':'2c306c3d2dab65cc4da996118ff521506e028cf3fdc0a8ff5d0a891d24b74cdf'}
    paragraph='Stage5 current execution: first postfallback toolchain08 gate actually passed with the unchanged reviewed6aa/24aa sources. The fresh Linuxboot is8cca020a-71b2-4163-92dc-6087df12dd45; exact toolchainproof2c306c3d2dab65cc4da996118ff521506e028cf3fdc0a8ff5d0a891d24b74cdf joins the same8GiB ext4 toolchain UUID and actual loop mount. Retained native/client exit0, owned descendant closure and original unlock independently pass. The fresh proc/meminfo snapshot is published as an observation, not detector acceptance. Interop, qualified Gsession/preserved storage rebind, DriveFS, runtime and backingUNC remain to qualify on this boot. First full-method genome is prepared and closed DEFERRED_RESOURCE with no accepted detector result; preserve its scientificidentity and52object backing snapshot. Accepted Stage4 and actual provisional196tip/784NA SVG/PDF are durable. Finalbiology/figure andVM recovery remain incomplete.\n'
    for suffix,value in [('extras.json',extras),('patch.json',patch)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','2b8fd58ff9a18d183ae7d69482e3f36aba5a8a8c','--previous','master_profile70',
      '--phase','Verify fresh postfallback toolchain boot and exact retained native closure',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json',
      '--spool','stage5_setup_toolchain_actual_postiq_08'],check=True)
if __name__=='__main__':main()
