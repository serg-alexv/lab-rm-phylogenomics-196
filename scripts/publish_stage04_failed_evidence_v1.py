"""Portable actual V6 failed-attempt payload; download/hash/member Windows readback."""
import hashlib, json, os, subprocess, zipfile
from pathlib import Path
import stage04_controller as C
import stage04_recovery_support_v9 as S

TAG='stage04c-native-failure196-v1'

def run(argv,timeout=180):return S.command(argv,timeout=timeout)

def main():
    with C.WorkflowLock(S.LOCK) as lock:
        C.reconcile(S.ROOT);S.held_lock_matches_negative(lock) if hasattr(S,'held_lock_matches_negative') else S.pins()
        target=S.RUNTIME/'negative_history_v1';saved=C.load(target/'certificate.json')
        work=S.HISTORY/'.work/stage04c_failed_evidence_publication_v1';work.mkdir(parents=True,exist_ok=True)
        payload=work/'stage04c_native_failure196_v1.zip';C.check(not payload.exists(),'Preserve existing immutable failure payload; no overwrite')
        sources={}
        for name,record in saved['original_artifacts'].items():
            path=target/'original_primary196'/name;C.check(C.digest(path)==record['sha256'],'Preserved original failed artifact changed')
            sources['original_primary196/'+name]=path
        sources['actual_native_observer_exit.json']=target/'actual_native_observer_exit.json'
        sources['failed_attempt_reconciliation_v1.json']=S.REPORT/'failed_attempt_reconciliation_v1.json'
        sources['original_inference_freeze.json']=S.OLD/'inference_freeze.json'
        for name in S.FROZEN:sources['preserved_sources/'+name]=S.ROOT/name
        sources['RECOVERY_V9.md']=S.REPORT/'RECOVERY_V9.md'
        manifest={name:{'sha256':C.digest(path),'bytes':path.stat().st_size} for name,path in sources.items()}
        with zipfile.ZipFile(payload,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for name,path in sorted(sources.items()):z.write(path,name)
            z.writestr('payload_hash_manifest.json',json.dumps({'schema':'IMMUTABLE_FAILED_NATIVE_PAYLOAD_V1','files':manifest},indent=2)+'\n')
            z.writestr('README.txt','Actual failed V6 native attempt. Native exit1 is observed; original controller outcome/final job closure are UNKNOWN. This archive establishes no scientific PASS. Open/extract with Windows Explorer or PowerShell/.NET; no WSL is needed. Hash manifest covers immutable payload, separate from publication receipt.\n')
        value={'schema':'STAGE04C_FAILED_NATIVE_RELEASE_ASSET_V1','tag':TAG,'name':payload.name,'bytes':payload.stat().st_size,'sha256':C.digest(payload),
          'payload_files':manifest,'scientific_validation':'FAILED_INCOMPLETE_NOT_UPGRADED','old_controller_outcome':'UNKNOWN','old_final_job_closure':'UNKNOWN'}
        C.atomic(S.ROOT/'reports/stage04/recovery_v9/failure_asset_manifest.json',value)
        # Native Windows/.NET reads all payload member bytes and hashes, no Linux.
        ps="$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.IO.Compression.FileSystem; $z=[IO.Compression.ZipFile]::OpenRead('"+str(payload)+"'); try {$rows=@(); foreach($e in $z.Entries){$s=$e.Open(); try{$h=[Security.Cryptography.SHA256]::Create(); $b=$h.ComputeHash($s); $rows+=[pscustomobject]@{name=$e.FullName;bytes=$e.Length;sha256=([BitConverter]::ToString($b).Replace('-','').ToLowerInvariant())}} finally{$s.Dispose()}}; $rows | ConvertTo-Json -Depth 5 -Compress} finally{$z.Dispose()}"
        rows=json.loads(run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps]).decode('utf-8-sig'))
        C.check(all(next(r for r in rows if r['name']==name)['sha256']==record['sha256'] for name,record in manifest.items()),'Windows native archive member readback failed')
        available=subprocess.run(['gh','release','view',TAG,'--repo','serg-alexv/lab-rm-phylogenomics-196'],capture_output=True)
        if available.returncode!=0:
            note=work/'release_notes.md';note.write_text('Actual native primary196 IQ-TREE exit1 evidence with original retained model cache/logs, exact launch/tool/input/freeze hashes and independent process exit observation. Original controller outcome and final old job closure remain UNKNOWN. All accepted earlier stages and four alignment matrices remain unchanged. This release is failure evidence; it is not scientific completion or recovery adoption. Portable ZIP/member hashes and native Windows readback accompany the asset.\n',encoding='utf-8')
            run(['gh','release','create',TAG,'--repo','serg-alexv/lab-rm-phylogenomics-196','--title','Stage04 native failure evidence: full196 incomplete','--notes-file',str(note)])
        run(['gh','release','upload',TAG,str(payload),'--repo','serg-alexv/lab-rm-phylogenomics-196'])
        readback=work/'remote_readback';readback.mkdir(exist_ok=False)
        run(['gh','release','download',TAG,'--pattern',payload.name,'--dir',str(readback),'--repo','serg-alexv/lab-rm-phylogenomics-196'])
        downloaded=readback/payload.name;C.check(downloaded.stat().st_size==value['bytes'] and C.digest(downloaded)==value['sha256'],'Remote release bytes differ')
        with zipfile.ZipFile(downloaded) as z:
            C.check(all(hashlib.sha256(z.read(name)).hexdigest()==record['sha256'] for name,record in manifest.items()),'Remote payload member hashes differ')
        receipt={'utc':C.now(),'status':'UPLOAD_VERIFIED_REMOTE_BYTES_AND_ALL_PAYLOAD_MEMBERS','tag':TAG,'release_url':'https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/tag/'+TAG,
          'asset':value['name'],'asset_sha256':value['sha256'],'asset_bytes':value['bytes'],'payload_members_verified':len(manifest),
          'windows_native_dotnet_archive_member_readback':True,'scientific_validation':'FAILED_INCOMPLETE','old_controller_outcome':'UNKNOWN','old_final_job_closure':'UNKNOWN'}
        C.atomic(S.ROOT/'reports/stage04/recovery_v9/failure_publication_receipt.json',receipt)
        published=S.publish(['scripts/publish_stage04_failed_evidence_v1.py','reports/stage04/recovery_v9/failure_asset_manifest.json',
          'reports/stage04/recovery_v9/failure_publication_receipt.json'],'Publish verified portable native failure evidence without upgrading missing closure')
        print(json.dumps({'status':receipt['status'],'tag':TAG,'asset_sha256':value['sha256'],'bytes':value['bytes'],'commit':published['commit']}))

if __name__=='__main__':main()
