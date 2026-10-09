"""Verify exact public historical bytes; no scientific adoption or purge authority."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
WORK=Path(__file__).resolve().parent
def load(name,pin):
    path=WORK/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=pin:raise ValueError('Independent helper differs')
    spec=importlib.util.spec_from_file_location(name[:-3],path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
COMMON='6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691'
SIDE='090e8068d9f2ee0a21631541681a835de5f97bd1cf695b06537aabeb4bf24841'
A=load('verify_master_public_components01_remote.py',COMMON);S=load('verify_master_original_sidecars.py',SIDE)
PREFIX='reports/master_run/20261009/cleanup/changed_history01/'
ASSETS=[dict(name='master_old_checkout_changed_history01.zip',bytes=1687039,
    sha256='0fc8e7f1e6ee8d3ba4327df49b6e2b055ef6118ca7fc4a623d23ad9a3edc8226')]
SIDECARS=[dict(name='master_old_checkout_changed_history01.zip.sha256',bytes=109,
    sha256='1a93b8d40e7fd204985d3060420aa0e2014889f90e5c2081c8e79517cf024856',newline='\r\n')]
CONTROLS={'build_receipt.json':'799ba81f16bf0bd523a450a065d94ced878d5faf1b96decc8212675f2ebd8ee9',
    'original_mapping.json':'765794bdb20fbb085cbeb7b87968ac84247e2e1ea160c8ebe77520f3ad958f91',
    'completion.json':'8c27d33a058a42a711cc78c5b9f25f0825d944a34b0e1fe807cd9cf415a61233'}
PUBLIC_SHA='fb80c41a18c9055a5c1c9748ad083e419b61a0919e7813a497f5ca8441aa1796'
EXCLUDED_SHA='5f551aadad4f627a9a319044e84ddb358e467efd3308544e7eb0230b90139645'
CODE={'verify_master_public_components01_remote.py':COMMON,'verify_master_original_sidecars.py':SIDE,
    'build_old_checkout_changed_history_archive.py':'f8cd2e2567d6082b43c4c8031ad191856a73262f0e34de097b3e4aa6087a078d'}
def verify(args,out,result):
    extras={PREFIX+'scope02/public_files.json':(WORK/'old_checkout_changed_history_scope02/public_files.json',PUBLIC_SHA),
        PREFIX+'scope02/excluded_files.json':(WORK/'old_checkout_changed_history_scope02/excluded_files.json',EXCLUDED_SHA)}
    raw=A.get_controls(args,CONTROLS,{**CODE,Path(__file__).name:A.digest(__file__)},PREFIX,
        WORK/'master_old_checkout_changed_history01',out,result,extras)
    build=json.loads(raw[PREFIX+'build_receipt.json']);mapping=json.loads(raw[PREFIX+'original_mapping.json'])
    completion=json.loads(raw[PREFIX+'completion.json']);public=json.loads(raw[PREFIX+'scope02/public_files.json'])
    excluded=json.loads(raw[PREFIX+'scope02/excluded_files.json'])
    A.require(build['state']=='PASS_LOCAL_EXACT194_PUBLIC_HISTORY_CRC_SHA_NO_PURGE' and build['public_original_files']==194
        and build['public_original_bytes']==18622099 and build['control_source_files']==19
        and build['source_deletions']==0 and build['scientific_acceptance_created'] is False,'Historical build scope differs')
    release=selected=None
    if not args.local_inspect:release,selected=S.begin(A,args,ASSETS,SIDECARS,out,result)
    path=(WORK/'master_old_checkout_changed_history01' if args.local_inspect else out)/ASSETS[0]['name']
    archive,observed=A.verify_zip(path,ASSETS[0],A.member_table(build['members']))
    with archive:
        originals={r['member']:r for r in mapping['files']};approved={r['archive_member']:r for r in public['files']}
        A.require(len(originals)==len(mapping['files'])==len(approved)==194 and set(originals)==set(approved)
            and mapping['count']==194 and mapping['bytes']==18622099,'Exact194 public mapping differs')
        A.require(observed['ORIGINAL_MAPPING.json']['sha256']==CONTROLS['original_mapping.json'],'Archived original mapping differs')
        for member,row in originals.items():
            declaration=approved[member]
            A.require(member in observed and observed[member]['sha256']==row['sha256']==declaration['sha256']
                and observed[member]['bytes']==row['bytes']==declaration['bytes_screened']
                and row['original_path']==declaration['absolute_path'],'Original public byte binding differs')
        A.require({n for n in observed if n.startswith('originals/')}==set(originals)
            and len(observed)==216 and sum(r['bytes'] for r in originals.values())==18622099,'Exact historical ZIP membership differs')
        A.require(len(excluded['files'])==5 and sum(r['original_bytes'] for r in excluded['files'])==4795
            and all(r['original_path'] not in {v['original_path'] for v in originals.values()}
                and not r['payload_archived'] for r in excluded['files']),'Private exclusions differ')
        A.require(completion['public_original_files']==194 and completion['whole_private_excluded_files']==5
            and completion['scientific_acceptance_created'] is False and completion['source_deletions']==0,'Completion scope differs')
        result.update(zip_members=216,internal_sum_entries=215,public_original_files=194,public_original_bytes=18622099,
            whole_private_excluded_files=5,whole_private_excluded_bytes=4795,members=list(observed.values()),
            scientific_acceptance_created=False,historical_native_closure='NOT_INFERRED',
            source_payloads_reread=False,privacy_screen_rerun=False,pruning='NOT_RUN',wipe_authority=False)
    if not args.local_inspect:A.end_release(args,release,selected,result)
    result['state']='PASS_LOCAL_HISTORY216_MEMBERS194_ORIGINALS_NO_PURGE' if args.local_inspect else 'PASS_FRESH_REMOTE_HISTORY216_MEMBERS194_ORIGINALS_NO_PURGE'
if __name__=='__main__':A.execute_readback(A.cli(__doc__),'old_checkout_changed_history01',verify)
