"""C-only exact completed UNC03 diagnostic and retained Job review."""
from pathlib import Path, PureWindowsPath
import datetime, hashlib, json
import review_stage5_postboot_gate as R
W=Path(__file__).resolve().parent
D=W/'stage5_unc03_diagnostic_actual01'
SOURCE='c0458522ca5483670f008049d1a4457ad27531b003b8397893ee5b0d05b31697'
REQUEST='7f28e209707483d1a50e25c7d35e5804f2b9ebb8ecf9bcc110714849228ce27d'
PINS={'atomic_iqtree_windows.py':'80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827','stage5_unc_bind_probe.py':'0664a9e93c095232c25d052331d2243b49d5fe5e064b7794df5c5f4b010cc35d'}

def main():
    out=W/'stage5_unc03_diagnostic_actual01_independent_review.json';R.require(not out.exists(),'Fresh actual review required')
    report={'schema':'STAGE05_UNC03_DIAGNOSTIC_ACTUAL_INDEPENDENT_V1','state':'FAILED_INDEPENDENT_READBACK','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_source_sha256':R.sha(Path(__file__)),'method':'C-only decoded actual bytes/lifecycle and exact SHA256; no UNC, WSL, producer imports, registry, lock, process effect, network or Git ref action','original_UNC03_gate':'FAILED_PRESERVED','scientific_adoption':False}
    try:
        R.require(R.sha(W/'stage5_unc03_readonly_diagnostic.py')==SOURCE,'Actual diagnostic source drift')
        for name,pin in PINS.items():R.require(R.sha(W/name)==pin,'Exact unchanged U/A dependency differs')
        peer=R.pinned(W/'stage5_unc03_readonly_diagnostic_source_independent_review01.json','8e8d15081ee34c67a1b538d402e4ab6ba82d74b32d449f25679f2a8cf9901e54');R.require(peer['state'].startswith('PASS_'),'Source peer not PASS')
        pub=R.read(W/'master_uncfailure58_remote_readback.json');R.require(pub['state']=='PASS_ALL_REMOTE_BYTES_SHA256_VERIFIED' and pub['expected_commit']=='b98e1d905d4f23654cbef2264881b5ca6fa0147b' and pub['verified_files']==pub['required_files'],'Source publication readback differs')
        rows=[r for r in pub['files'] if r['path'].endswith('/stage5_unc03_readonly_diagnostic.py')];R.require(len(rows)==1 and rows[0]['sha256']==SOURCE and rows[0]['actual_remote_bytes_read'] is True and rows[0]['sha256_verified'] is True,'Exact diagnostic source not verified remotely')
        original=R.pinned(W/'stage5_unc_bind_actual_postiq_03/request.json',REQUEST);prepared=R.read(W/'stage5_unc_bind_actual_postiq_03/prepared.json');failed=R.read(W/'stage5_unc_bind_actual_postiq_03/result.json');R.require(failed['state']=='FAILED' and prepared['request_sha256']==REQUEST and prepared['storage_before']['boot_id']=='f0ffcebc-4901-479d-9559-89d45e9cfa38','Original failed scope/current preparation drift')
        q=R.read(D/'diagnostic_request.json');v=R.read(D/'result.json');l=R.pinned(D/'worker_result.json',v['worker_result_sha256'])
        for value in (q,v,l):R.require(value['source_sha256']==SOURCE and value['original_request_sha256']==REQUEST,'Exact diagnostic/source/original request differs')
        R.require(q['source_pins']==v['source_pins']==PINS and l['diagnostic_request_sha256']==R.sha(D/'diagnostic_request.json'),'Diagnostic dependency/request bytes differ')
        R.require(v['state']=='PASS_READONLY_DIAGNOSTIC_AND_EXACT_OWNED_WINDOWS_CLOSURE' and l['state']=='PASS_READONLY_DIAGNOSTIC_COMPLETE_NO_PROBE_ADOPTION','Actual diagnostic not closed PASS')
        R.lock(q['workflow_lock']);R.lock(v['workflow_lock']);R.require(q['workflow_lock']==v['workflow_lock'] and q['actual_windows_owner']==v['actual_windows_owner'],'Actual diagnostic original owner/lock differs')
        R.require(q['authority_sha256']==v['authority_sha256']=='c4184e2af9ea0ef81f652d4d1baed00b9742fa2a3efdb9fe87491911ab2242cd','Current control bytes differ')
        registration={'DistributionName':'Ubuntu','Version':2,'DefaultUid':0,'Flags':15,'BasePath':r'C:\Users\wheel\AppData\Local\wsl\{d58ba874-ce79-4d09-aa37-9d9d8539a6a7}'}
        R.require(q['Ubuntu_registration']==v['Ubuntu_registration']==l['Ubuntu_registration']==registration,'Actual exact Ubuntu UID0 registration differs')
        canonical=PureWindowsPath(original['unc'])/original['sentinel_name'];backing=PureWindowsPath(r'\\wsl.localhost\Ubuntu\var\tmp\lab_rm_stage05_atomic_v1')/original['sentinel_name']
        targets=[{'role':role+'_'+leaf[:-4],'path':str(root/leaf),'expected_bytes':len(bytes.fromhex(original[key])),'expected_sha256':hashlib.sha256(bytes.fromhex(original[key])).hexdigest()} for role,root in (('canonical',canonical),('backing',backing)) for leaf,key in (('linux.bin','linux_payload_hex'),('windows.bin','windows_payload_hex'))]
        dirs=[{'role':role+'_directory','path':str(root)} for role,root in (('canonical',canonical),('backing',backing))]
        R.require(q['targets']==targets and q['directories']==dirs and len(l['observations'])==4 and len(l['directory_observations'])==2,'Four exact leaves/two directories differ')
        for row,expected in zip(l['observations'],targets):
            R.require(all(row[k]==val for k,val in expected.items()),'Actual observed leaf role differs')
            if row['role']!='backing_linux':
                code,kind=(5,'PermissionError') if row['role'].startswith('canonical') else (2,'FileNotFoundError')
                for key in ('metadata_error','tiny_read_error','readonly_payload_error','metadata_after_error'):R.require(row[key]['winerror']==code and row[key]['kind']==kind,'Recorded leaf error differs')
                R.require('readonly_payload_observation' not in row,'Unexpected denied/missing leaf read')
            else:
                R.require(row['matches_original_request_payload'] is True and row['payload_bytes']==116 and row['payload_sha256']==prepared['linux_file']['sha256']==expected['expected_sha256'],'Backing exact Linux sentinel payload differs')
                R.require(row['metadata_before']==row['metadata_after'] and row['metadata_before']['inode']==prepared['linux_file']['inode'] and row['metadata_before']['nlink']==1 and row['metadata_before']['regular'] is True and row['metadata_before']['reparse_point'] is False,'Backing before/after inode/nlink/shape differs')
                R.require(row['tiny_read_receipt']['inode']==prepared['linux_file']['inode'] and row['tiny_read_receipt']['sha256']==expected['expected_sha256'],'Unchanged U.tiny_read actual success differs')
                obs=row['readonly_payload_observation'];R.require(obs['metadata_before']==obs['metadata_opened']==obs['metadata_after_open']==row['metadata_before'] and obs['matches_original_request_payload'] is True and obs['payload_sha256']==expected['expected_sha256'] and obs['scientific_or_UNC_adoption'] is False,'Independent bounded readonly observation differs')
        for row,expected in zip(l['directory_observations'],dirs):
            R.require(all(row[k]==val for k,val in expected.items()),'Actual directory role differs')
            if row['role']=='canonical_directory':R.require(row['metadata_error']['winerror']==5,'Canonical directory denial differs')
            else:R.require(row['metadata']['directory'] is True and row['metadata']['reparse_point'] is False and row['metadata']['inode']==prepared['directory_inode'],'Backing exact Linux directory inode differs')
        for value in (v,l):R.require(value['UNC_writes']==value['WSL_launches']==0 and value['cleanup_performed'] is False and value['scientific_adoption_authorized'] is False,'Read-only diagnostic crossed action scope')
        boot=R.pinned(W/'master_newboot_reconciliation_actual01.json','07a6546d3100bd979884b5a1e4d0c44952a4fc3cdd5a020087d4bbbc5e6d8cf3');stamp=datetime.datetime.fromisoformat(boot['current_boot']['last_boot_utc']);ft=int((stamp-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10_000_000)
        R.windows_job(D/'windows_readonly_worker',v['windows_worker'],ft,PINS['stage5_unc_bind_probe.py'],PINS['atomic_iqtree_windows.py'])
        job=v['windows_worker'];R.require(job['owner']==v['actual_windows_owner'] and job['argv']==[R.PYTHON,'-B',str(W/'stage5_unc03_readonly_diagnostic.py'),'--worker','--diagnostic-request',str(D/'diagnostic_request.json'),'--diagnostic-request-sha256',R.sha(D/'diagnostic_request.json'),'--source-sha256',SOURCE],'Retained exact diagnostic worker argv/owner differs')
        elapsed=(job['exit']['exit_filetime']-job['birth']['creation_filetime'])/10000000;R.require(0<elapsed<=20,'Diagnostic exceeded reviewed named Job bound')
        R.require(v['original_lock_released'] is True and v['unknown_closure_STOP_present'] is False,'Actual unlock/no STOP differs')
        for key in ('resources','resources_after'):
            resources=v[key];R.require(resources['physical_available_bytes']>=1879048192 and resources['commit_headroom_bytes']>=1879048192 and all(n>=10737418240 for n in resources['disk_available_bytes'].values()),'Diagnostic resource admission differs')
        for path in sorted(D.rglob('*')):
            if path.is_file():R.data(path)
        report.update(state='PASS_EXACT_UNC03_DIAGNOSTIC_BYTES_AND_RETAINED_CLOSURE_UNC_GATE_STILL_FAILED',source_sha256=SOURCE,source_publication_commit=pub['expected_commit'],original_request_sha256=REQUEST,diagnostic_request_sha256=R.sha(D/'diagnostic_request.json'),worker_result_sha256=v['worker_result_sha256'],retained_worker_birth=job['birth'],retained_worker_exit=job['exit'],worker_elapsed_seconds=elapsed,owned_job_empty=True,owned_closure_proven=True,original_lock_release_recorded=True,unknown_closure_STOP_absent_recorded=True,Ubuntu_registration=registration,findings=['Canonical directory and both leaves return WinError5 ACCESS_DENIED at every read phase.','Native-backing UNC directory is readable and has prepared Linux sentinel-directory inode33554454.','Native-backing linux.bin passes unchanged U.tiny_read:116B SHA4a90f5d4c9fa4130234bfc121f1e1dd47cde726546840a3085d9e4b5875a0ff5, inode33554461 matches Linux prepared. All before/open/after Windows metadata is stable and nlink1.','Native-backing windows.bin returns WinError2 FILE_NOT_FOUND at all four phases; its current absence is proved, historical never-write is not.','UID0 is recorded consistently. The current canonical transport denial cannot be explained solely by the former DefaultUid1000 versus0700 mismatch.','The diagnostic locates a usable read-only native-backing view while canonical traversal is denied; it does not establish bidirectional write/cleanup, an adopted transport alias, or the exact original worker exception.'],projection_limit='Windows UNC device0/mode/100ns timestamp projection differs from Linux device2096/POSIX metadata; exact bytes and inode joins are recorded without pretending all cross-platform stat fields are equal.',next_gate_requirement='Any fixed backing UNC transport alias needs separate source review, pinned current ext4 canonical-to-backing identity, complete actual bidirectional sentinel I/O and exact cleanup before science; preserve original failed UNC03 and do not weaken tiny_read guards.',reviewer_actual_UNC_reads=0,reviewer_WSL_launches=0,reviewer_lock_acquisitions=0)
    except BaseException as error:report['error']={'kind':type(error).__name__,'message':str(error)}
    report['checked_files']=R.CHECKED
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'state':report['state'],'error':report.get('error'),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checked_files':len(R.CHECKED)}))
    return 0 if report['state'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
