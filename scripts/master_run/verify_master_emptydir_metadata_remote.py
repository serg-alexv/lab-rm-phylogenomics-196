"""Fresh byte readback of an empty-directory proposal; grants no prune authority."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
WORK=Path(__file__).resolve().parent
def load(name,pin):
    path=WORK/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=pin:raise ValueError('Readback helper source differs: '+name)
    spec=importlib.util.spec_from_file_location(name[:-3],path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
COMMON='6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691'
SIDE='090e8068d9f2ee0a21631541681a835de5f97bd1cf695b06537aabeb4bf24841'
A=load('verify_master_public_components01_remote.py',COMMON)
S=load('verify_master_original_sidecars.py',SIDE)
PREFIX='reports/master_run/20261009/cleanup/emptydirs01/'
ASSETS=[dict(name='master_old_scientific_emptydirs01.zip',bytes=438572,
    sha256='656f515d069338e132a9c2ec46497e7388a55faaeb4c1e4aecca06ab37dfbd8d')]
SIDECARS=[dict(name='master_old_scientific_emptydirs01.zip.sha256',bytes=105,
    sha256='f2ab2b9ec783f4658797d15873dd97f52a4bec27820a8daeb4eea899b26fe467',newline='\r\n')]
CONTROLS={'build_receipt.json':'6729df70a06247d59ff844700ccaeeb997916e82e210c57026fde1c039f70381',
    'completion.json':'08a83e6761aca488f1f631df4d87400e01074bb809bdcd9a0562107739f8d66d',
    'counts_holds.json':'71930cd27f3cb0ba064629329cae82e59ac3d655f9d60e2c120f9d22a611c0ea'}
CODE={'verify_master_public_components01_remote.py':COMMON,'verify_master_original_sidecars.py':SIDE,
    'build_old_scientific_emptydirs_archive.py':'00d144480ad83967b3f6dba270fbbfca5d5cad48fea33c6b17974d91f1ab97fe',
    'prepare_old_scientific_emptydirs.py':'7287809f47f912eddb21ba9f05d927872ef710d45ac6857837ae6689c320b21f'}

def verify(args,out,result):
    raw=A.get_controls(args,CONTROLS,{**CODE,Path(__file__).name:A.digest(__file__)},PREFIX,
                       WORK/'master_old_scientific_emptydirs01',out,result)
    build=json.loads(raw[PREFIX+'build_receipt.json']);completion=json.loads(raw[PREFIX+'completion.json'])
    counts=json.loads(raw[PREFIX+'counts_holds.json'])
    A.require(build['state']=='PASS_LOCAL_EXACT_METADATA_ARCHIVE_CRC_SHA_NO_DELETE'
        and build['member_count']==19 and build['original_count']==16 and build['execution_authorized'] is False
        and build['scientific_acceptance_created'] is False and build['counts_holds']==counts,'Build scope differs')
    A.require(counts['directory_count']==5542 and counts['empty_now_count']==3736
        and counts['planned_children_only_count']==1806 and counts['held_count']==6
        and counts['execution_authorized'] is False and counts['files_deleted']==counts['directories_deleted']==0,
        'Metadata-only count/hold scope differs')
    release=selected=None
    if not args.local_inspect:release,selected=S.begin(A,args,ASSETS,SIDECARS,out,result)
    path=(WORK/'master_old_scientific_emptydirs01' if args.local_inspect else out)/ASSETS[0]['name']
    archive,observed=A.verify_zip(path,ASSETS[0],A.member_table(build['members']))
    with archive:
        A.require(len(observed)==19 and set(observed)==set(build['originals'])|{'INDEX.json','COUNTS_HOLDS.json','SHA256SUMS.txt'},'Exact metadata members differ')
        A.bind_inputs({name:{k:row[k] for k in ('bytes','sha256')} for name,row in build['originals'].items()},observed)
        for name,pin in CODE.items():
            if name in observed:A.require(observed[name]['sha256']==pin,'Original builder/scanner source differs')
        A.require(observed['COUNTS_HOLDS.json']['sha256']==CONTROLS['counts_holds.json'],'Archived count/hold control differs')
        plan=json.loads(archive.read('master_old_scientific_emptydirs_proposed_02.json'))
        A.require(observed['master_old_scientific_emptydirs_proposed_02.json']['sha256']==counts['plan_sha256']
            == 'be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5','Exact original proposal pin differs')
        rows=plan['directories'];paths=[r['path'] for r in rows]
        A.require(len(rows)==len(set(paths))==5542 and sum(r['empty_at_observation'] is True for r in rows)==3736
            and plan['files_to_delete']==plan['recursive_deletes']==plan['g_writes']==plan['wsl_starts']==0
            and plan['execution_authorized'] is False and len(plan['held'])==6,'Proposal accounting/scope differs')
        A.require(completion['archive_sha256']==ASSETS[0]['sha256'] and completion['proposed_directories']==5542
            and completion['directories_deleted']==completion['files_deleted']==0,'Completion metadata scope differs')
        result.update(zip_members=19,internal_sum_entries=18,original_controls=16,members=list(observed.values()),
            proposed_directories=5542,empty_at_observation=3736,planned_child_parents=1806,held_directories=6,
            directories_deleted=0,pruning='NOT_RUN',execution_authorized=False,
            live_directory_rescan=False,independent_semantic_plan_review='SEPARATE_PRESERVED_REVIEW3891047E')
    if not args.local_inspect:A.end_release(args,release,selected,result)
    result['state']='PASS_LOCAL_METADATA19_MEMBERS_NO_PRUNE' if args.local_inspect else 'PASS_FRESH_REMOTE_METADATA19_MEMBERS_5542_PROPOSED_NO_PRUNE'

if __name__=='__main__':A.execute_readback(A.cli(__doc__),'old_scientific_emptydirs01',verify)
