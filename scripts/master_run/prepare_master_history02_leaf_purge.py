"""Prepare exact837 already-recovered history leaves. Never deletes or contacts GitHub.

Missing actual batch03 postverify produces a blocked draft, never an executable plan.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse, collections, hashlib, json, os, stat, zipfile

WORK=Path(__file__).resolve().parent
OLD=PureWindowsPath(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
SCOPES=('data','.work/review2','.work/stage02_validated','.work/source_locus_inputs_v1',
 '.work/stage03_markers_v1','.work/stage04a_windows_alignments_v1','.work/stage04_phylogeny_v2')
RECOVERY='public_history02_readback_20261009T195508Z_1f99201e/receipt.json'
RECOVERY_SHA='d83aaff2695920d475742ace6c710255a326642222a5db771b95ec2d809b0ecb'
MAP_SHA='014a540f8bfb11a31c9ea5d709562ea3669894b70fa2d300999b0a3df450c6cf'
PROTECTED_SHA='22d307f5bba8a98dbd060e3d1d091e22c7f70dc85b40e77ada04c0eef36ce1a7'
SOURCE_COMMIT='2ad42f8c3d78a974f22533a4f21ef1b5e8562a8b'
POST_VERIFIER_SHA='dbb0140fe2fac41940fa8d4838ffcbf1f6b72933d6d14a2011137ef4c401c56f'
BATCH03_ZIP_SHA='f6d7e0558953d2542ca085552a6cd8219a4ec1acde4072ce6f03d12dd953178e'

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')

def validate_row(row):
    rel=row['relative_path'];p=PurePosixPath(rel)
    require(p.as_posix()==rel and not p.is_absolute() and '..' not in p.parts and '\\' not in rel and ':' not in rel
        and all(x not in ('','.','..') and not x.endswith((' ','.')) for x in rel.split('/')),'Noncanonical original path')
    require(not {'.tools','.git','.codex','.private_run'}.intersection(x.casefold() for x in p.parts)
        and not p.name.casefold().endswith(('.lock','.guard')),'Protected source path')
    require(str(OLD.joinpath(*p.parts))==row['path'] and row['scope'] in SCOPES
        and rel.startswith(row['scope']+'/') and row['link_count']==1,'Wrong original root/scope/link')
    return row['path'].casefold()

def validate_post(post,rows,excluded):
    require(post.get('schema')=='MASTER_BATCH03_INDEPENDENT_POST_PURGE_VERIFY_V1'
        and post.get('state')=='PASS_EXACT47429_REMOVED_838_ORIGINALS_AND12_PROTECTED_UNCHANGED'
        and post.get('verifier_sha256')==POST_VERIFIER_SHA
        and post.get('removed_files')==47429 and post.get('removed_bytes')==6565902818
        and post.get('held_files')==219 and post.get('unmatched_files')==619
        and post.get('remaining_after_stop')==0 and post.get('unreceipted_absences')==[], 'Actual successful batch03 postverify required')
    expected={r['path']:(r['bytes'],r['sha256']) for r in rows+[excluded]}
    observed={r['path']:(r['bytes'],r['sha256']) for r in post['retained_originals']}
    require(len(expected)==len(observed)==838 and observed==expected
        and all(r.get('identity_equal') is True for r in post['retained_originals'])
        and len(post['protected_files'])==12 and all(r.get('unchanged') is True for r in post['protected_files']), 'Postverify exact838/12 proofs differ')

def build(post_path=None,post_sha=None):
    require(os.name=='nt' and WORK==Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work').resolve(),'Exact C-work build namespace required')
    receipt_path=WORK/RECOVERY;require(sha(receipt_path)==RECOVERY_SHA,'Actual fresh recovery receipt changed')
    recovery=json.loads(receipt_path.read_bytes())
    require(recovery['state']=='PASS_FRESH_REMOTE_HISTORY02_3_SHARDS_882_MEMBERS_837_ORIGINALS_1_EXPLICIT_EXCLUSION'
        and recovery['source_commit']==SOURCE_COMMIT and recovery['original_source_files']==837
        and recovery['original_source_bytes']==983926424 and recovery['release_tag_and_assets_unchanged_before_after'] is True,'Independent remote recovery required')
    mp=WORK/'master_public_history02/original_member_mapping.json';require(sha(mp)==MAP_SHA,'Original837 mapping changed')
    mapping=json.loads(mp.read_bytes());rows=[];seen=set()
    source_zip=WORK/'master_public_history02/master_public_history02-001.zip'
    require(sha(source_zip)=='ecb1856f1d95a80c20c57877588d77079a4ac0dce317c57162f9e2460ad3eb96','Frozen source control archive changed')
    with zipfile.ZipFile(source_zip) as z:
        selection=json.loads(z.read('control/selection.json'))['files'];source={r['path']:r for r in selection}
    archived={a['name']:{r['member']:r for r in a['members']} for a in recovery['shards']}
    for m in mapping['files']:
        s=source[m['original_path']];key=validate_row(s);require(key not in seen,'Duplicate original candidate');seen.add(key)
        r={k:s[k] for k in ('path','relative_path','scope','bytes','sha256','link_count')}
        r.update({k:str(s[k]) for k in ('device','file_id','mtime_ns')})
        r.update(asset_name=m['asset_name'],member=m['member'])
        witness=archived[r['asset_name']][r['member']]
        require(m['member']=='old_C_repo/'+r['relative_path'] and m['sha256']==r['sha256']==witness['sha256']
            and m['bytes']==r['bytes']==witness['bytes'] and witness['crc_verified'] is True
            and m['original_identity']=={k:s[k] for k in ('device','file_id','mtime_ns','link_count')},'Exact recovered member/original identity differs')
        current=Path(r['path']).lstat()
        require(stat.S_ISREG(current.st_mode) and not current.st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT
            and (str(current.st_dev),str(current.st_ino),str(current.st_mtime_ns),current.st_size,current.st_nlink)==
                (r['device'],r['file_id'],r['mtime_ns'],r['bytes'],1),'Current original leaf identity changed; hold/reconcile')
        rows.append(r)
    require(len(rows)==837 and sum(r['bytes'] for r in rows)==983926424,'837 recovered candidate accounting differs')
    excluded=recovery['documented_whole_file_exclusions'][0]['source'];validate_row(excluded)
    excluded={k:excluded[k] for k in ('path','relative_path','scope','bytes','sha256','link_count')}|{k:str(excluded[k]) for k in ('device','file_id','mtime_ns')}
    require(excluded['bytes']==1025 and excluded['path'].casefold() not in seen
        and excluded['sha256']=='574547f9584dafce870492810ab02be990fe022939edd5a797292c473625027b','Excluded fragment must stay preserved')
    # Prove disjointness against the previous candidate set using frozen metadata only.
    archive=WORK/'master_batch03_mapping01/master_batch03_scientific_cache_mapping01.zip'
    require(sha(archive)==BATCH03_ZIP_SHA,'Previous candidate proof changed')
    with zipfile.ZipFile(archive) as z:
        holds={r['path'].casefold() for r in json.loads(z.read('control/conservative_leaf_assessment.json'))['files_preserved']}
        prior_count=0
        with z.open('mapping/batch03/file_allowlist.jsonl') as stream:
            for line in stream:
                r=json.loads(line);key=r['path'].casefold()
                if key not in holds:require(key not in seen,'Overlap with previous47429 candidates');prior_count+=1
    require(prior_count==47429,'Previous candidate accounting differs')
    protected=WORK/'master_batch03_protected_before.json';require(sha(protected)==PROTECTED_SHA,'Protected12 baseline changed')
    post_pin=None
    if post_path is not None:
        p=Path(post_path).resolve();require(p.parent.parent==WORK and sha(p)==post_sha
            and post_sha=='84cb29ebcc04b444ea90ca0e10d5f7e6832d09f14f8f8285f1241b4cf3e71868','Wrong actual postverify pin/namespace')
        post=json.loads(p.read_bytes());validate_post(post,rows,excluded);post_pin={'path':str(p),'sha256':post_sha,'verifier_sha256':POST_VERIFIER_SHA}
    require((post_path is None)==(post_sha is None),'Both postverify arguments required')
    plan={'schema':'MASTER_HISTORY02_EXACT837_LEAF_PURGE_PROPOSAL_V1','state':'BUILD_ONLY_NO_DELETE' if post_pin else 'BLOCKED_ACTUAL_BATCH03_POSTVERIFY_PIN_REQUIRED',
        'host':'WD','old_root':str(OLD),'allowed_scopes':list(SCOPES),'candidate_files':837,'candidate_bytes':983926424,
        'candidates':rows,'excluded_preserved':[excluded],'excluded_files':1,'excluded_bytes':1025,
        'script_sha256':sha(WORK/'Invoke-MasterHistory02LeafPurge.ps1'),'builder_sha256':sha(__file__),
        'remote_plan_path':'reports/master_run/20261009/cleanup/history02_purge01/proposed.json',
        'remote_recovery_receipt_path':'reports/master_run/20261009/cleanup/history02/REMOTE_READBACK.json',
        'remote_postverify_receipt_path':'reports/master_run/20261009/cleanup/batch03_purge01/INDEPENDENT_POSTVERIFY.json',
        'recovery_receipt':{'path':str(receipt_path),'sha256':RECOVERY_SHA,'source_commit':SOURCE_COMMIT,'tag':recovery['tag'],'tag_commit':recovery['expected_tag_commit']},
        'recovery_assets':recovery['downloaded_assets'],'remote_source_controls':recovery['authoritative_control_readback'],
        'local_archives':[{'path':str(receipt_path.parent/a['name']),'name':a['name'],'bytes':a['bytes'],'sha256':a['sha256'],'members':a['members']} for a in recovery['shards']],
        'batch03_postverify':post_pin,'protected_baseline':{'path':str(protected),'sha256':PROTECTED_SHA,'files':json.loads(protected.read_bytes())['files']},
        'owners':[{'pid':4768,'creation_filetime':'134360369876207076'},{'pid':27048,'creation_filetime':'134360369803845506'}],
        'maximum_runtime_seconds':900,'recursive_deletes':0,'previous47429_candidates_disjoint':True,
        'original_stable_workflow_lock':'UNTOUCHED_NO_OPEN_OR_WRITE','source_namespace_payload_hashing':'REQUIRED_PER_LEAF_AT_EXECUTION_NOT_CLAIMED_BY_METADATA_PREPARATION',
        'leaf_race':'Exclusive hash handle closes immediately before literal Remove-Item. Retained ancestors prevent parent rename/delete; short leaf replacement interval remains and is not an atomic-delete claim.'}
    # Drop 882 redundant member rows from the proposal; the pinned receipt is the member authority.
    for a in plan['local_archives']:a.pop('members')
    name='master_history02_leaf_purge_proposed.json' if post_pin else 'master_history02_leaf_purge_preparation_draft.json'
    out=WORK/name;write(out,plan)
    print(json.dumps({'plan':str(out),'sha256':sha(out),'bytes':out.stat().st_size,'state':plan['state'],'candidate_files':837,'candidate_bytes':983926424,'deletion':'NOT_RUN'}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--postverify');p.add_argument('--postverify-sha256')
    a=p.parse_args();build(a.postverify,a.postverify_sha256)
