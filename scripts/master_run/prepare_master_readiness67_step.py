"""Publish frozen operational readiness and current transport recovery evidence."""
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    name='master_readiness67'
    maps={
      'stage05_wsl_host_profile_fallback_source_preparation01/PUBLIC_MAPPING.json':'8330a1203a323a266985ed603e9ae4b6aa3937b127628e7cb99316facfc954f4',
      'postcleanup_sidefolder_inventory_publication01/PUBLIC_MAPPING.json':'7f69641ff4803404b1ba538acdf09c8bc715b242271b7526c28b7d90a69b4d12',
      'transport30_current_requalification_publication01/PUBLIC_MAPPING.json':'1f90244a8580173c7cae6ccebd312fde3aac3df327d79dc8bda54fa851aed578',
      'stage5_serial196_readiness_packet03/PUBLIC_MAPPING.json':'2b7cebf0cb7269f39f06839e391646303fce07dd16c72e534ca0474899f24978'}
    extras=[Path(__file__).name+'=scripts/master_run/'+Path(__file__).name,
      'master_cleanup66_remote_readback.json=reports/master_run/20261009/publication/master_cleanup66_remote_readback.json']
    for rel,pin in maps.items():
        m=W/rel;assert sha(m)==pin
        for r in json.loads(m.read_bytes())['files']:
            p=Path(r.get('local_path',r.get('path'))).resolve()
            assert p.is_relative_to(W) and sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
            target=r.get('repository_path',r.get('suggested_repository_path',r.get('suggested_remote_path',r.get('target'))));assert target
            extras.append(p.relative_to(W).as_posix()+'='+target)
        extras.append(rel+'=reports/master_run/20261009/preparation/'+m.parent.name+'_PUBLIC_MAPPING.json')
    patch={'stage5_wsl_fallback':'PASS_REVIEWED_SOURCE_ONLY_3584MB_GUI_OFF_ACTUAL_PENDING_CAPACITY02_NATURAL_CLOSURE',
      'local_transport30_recovery':'PASS_CURRENT_LOCAL_SHA_IDENTITY_AND_GITHUB_ASSET_ID_SIZE_SHA256_DIGEST_METADATA_2048507163_BYTES_NO_PURGE',
      'stage5_serial196_readiness':'SOURCE_PROCEDURE_READY_ONE_APPROVED_GENOME_PER_OWNER_MEASURE_FIRST_RAW_SCOPE_NO_NATIVE_ETA'}
    paragraph='Stage5 capacity02 has preserved scientific identity and its first full-method genome bundle; the first search is still at pre-command resource admission, without an accepted native result. The reviewed fallback changes only the WSL maximum to3584MB and disables GUI applications. Actual fallback requires capacity02 natural DEFERRED_RESOURCE closure, retained owner/client exit, inactive lease, independent exact evidence and original checked unlock; all boot-sensitive gates must pass afresh before resumption. The current metadata scan identified 30 redundant recovery transport ZIP/sidecar copies totaling2048507163 bytes. Every current local hash/identity matches prior verified recovery evidence; current GitHub tag and all16 asset IDs, sizes and API SHA256 digests match. No new downloads or deletions occurred. The serial196 procedure uses the existing one-genome owner, closed-raw archive/publication/recovery and independent four-cell curation path, measuring the first actual search before any ETA. Accepted Stage4 remains preserved. Native196 searches, curation784, final figures and VM cold capture/restore remain incomplete.\n'
    for suffix,val in [('extras.json',extras),('patch.json',patch)]:
        (W/(name+'_'+suffix)).write_text(json.dumps(val,indent=2)+'\n',encoding='utf-8')
    (W/(name+'_paragraph.md')).write_text(paragraph,encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(W/'prepare_completed_master_step.py'),'--name',name,
      '--head','3bdcfc93bf03631e8e1691daccc9d0655f7e0841','--previous','master_cleanup66',
      '--phase','Publish reviewed WSL fallback and current recovery transport verification',
      '--paragraph-file',name+'_paragraph.md','--patch-file',name+'_patch.json','--extras-file',name+'_extras.json'],check=True)
if __name__=='__main__':main()
