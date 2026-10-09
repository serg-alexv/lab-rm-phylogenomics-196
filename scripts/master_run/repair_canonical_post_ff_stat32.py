"""Opt-in exact32 identical-object reindex after the already completed fast-forward.

No fetch, merge, ref write, reset, clean, restore, force, or automatic expansion.
Preserve original index and six dirty bytes in C before the only `git add`.
Reuses the separately reviewed retained Git-job lifecycle, no new controller.
"""
from pathlib import Path
import argparse
import datetime as dt
import importlib.util
import json
import os
import uuid

W=Path(__file__).resolve().parent
HELPER_SHA='17010d4b173c5f543bf42652409e09a6e94a7306afd28be7585840d13a066eb5'
PLAN_SHA='00718bae82458ae0c238ac276e4fae134799c2f77d9caffd0da1f0ad7af7fb83'
PRIOR_SHA='a147c8121b36897676f59c18cb7ad085dc75841c8e47c376dfa85902e5834ff8'
HEAD='c76a46163af8b26057a113599f0524dfa0b0e94e'


def helper():
    import hashlib
    p=W/'repair_canonical_git_metadata.py'
    if hashlib.sha256(p.read_bytes()).hexdigest()!=HELPER_SHA:
        raise ValueError('Reviewed lifecycle/source helper differs')
    s=importlib.util.spec_from_file_location('post_ff_pinned_helper',p)
    R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
    R.need(R.sha(p)==HELPER_SHA,'Helper changed during import')
    return R


def status_scope(raw,R):
    rows=[x for x in raw.split(b'\0') if x]
    R.need(all(x.startswith(b' M ') for x in rows),'Only documented unstaged modified status allowed')
    paths=[R.relpath(x[3:].decode('utf-8')) for x in rows]
    R.need(len(set(paths))==len(paths),'Duplicate status path')
    return set(paths)


def validate_controls(plan,prior,R):
    R.need(plan['schema']=='MASTER_CANONICAL_POST_FF_EXACT32_METADATA_PLAN_V1'
           and plan['expected_head']==HEAD and plan['source_receipt_sha256']==PRIOR_SHA
           and plan['source_helper_sha256']==HELPER_SHA,'Exact one-off authority differs')
    R.need(prior['state']=='FAILED_PRESERVED' and prior['expected_main']==HEAD
           and prior['source_sha256']==HELPER_SHA and prior['fast_forward_command_exit0'] is True
           and prior['all_created_git_scopes_closed'] is True
           and prior['original_lock_explicitly_released'] is True
           and prior['error_message']=='Additional status paths after FF; preserved, no automatic scope expansion',
           'Prior source must prove closed FF exit0 with status-only terminal rejection')
    rows,dirty=plan['refresh_paths'],plan['six_dirty_files']
    names=[R.relpath(x['path']) for x in rows];dirty_names={R.relpath(x['path']) for x in dirty}
    R.need(len(names)==len(set(names))==32 and len(dirty)==len(dirty_names)==6
           and not set(names)&dirty_names and sum(x['bytes'] for x in rows)==1820806,
           'Exact32+six scope differs')
    R.need(status_scope(prior['final_status_utf8'].encode('utf-8'),R)==set(names)|dirty_names,
           'Plan does not equal actual prior38 status entries')
    proofs={x['path']:x for x in prior['target_changed_files_actual_raw_bytes']}
    for row in rows:
        p=proofs[row['path']]
        R.need(row['bytes']==p['bytes'] and row['sha256']==p['sha256']
               and row['head']['oid']==p['blob_oid'] and row['head']=={k:row['index'][k] for k in ('mode','oid')}
               and row['index']['stage']==0,'New32 pin not bound to actual prior raw proof')
    old_dirty={x['path']:x for x in prior['six_dirty_files_unchanged']}
    R.need(all(x['bytes']==old_dirty[x['path']]['bytes'] and x['sha256']==old_dirty[x['path']]['sha256']
               for x in dirty),'Six original dirty pins differ')
    return rows,dirty


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true')
    p.add_argument('--expected-source-sha256');args=p.parse_args()
    if not args.run:
        print(json.dumps({'state':'PREPARED_NOT_RUN','G_writes':0,'fetches':0,'merges':0,'plan_sha256':PLAN_SHA}));return
    R=helper()
    R.need(os.name=='nt' and W==R.DEPLOY,'Exact Windows C deployment required')
    R.need(R.SHA.fullmatch(args.expected_source_sha256 or '') and R.sha(__file__)==args.expected_source_sha256,
           'Explicit executed-source pin required')
    R.need(R.sha(W/'canonical_post_ff_stat32_plan.json')==PLAN_SHA,'Exact32 plan bytes differ')
    prior_path=W/'canonical_git_metadata_repair_20261009T230357Z_7bd50c6d/receipt.json'
    R.need(R.sha(prior_path)==PRIOR_SHA,'Original FF/status-failure receipt differs')
    plan=json.loads((W/'canonical_post_ff_stat32_plan.json').read_bytes())
    rows,dirty=validate_controls(plan,json.loads(prior_path.read_bytes()),R)
    names=[x['path'] for x in rows];dirty_names={x['path'] for x in dirty}
    R.need(R.sha(W/'atomic_iqtree_windows.py')==R.API_SHA,'Original lock/API source differs')
    R.need(not any(k in os.environ for k in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY',
           'GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_CONFIG_COUNT','GIT_CONFIG_PARAMETERS')),'Ambient Git redirection forbidden')
    s=importlib.util.spec_from_file_location('post_ff_original_api',W/'atomic_iqtree_windows.py')
    A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
    api=A.Win();lock=A.WorkflowLock(api);g=None
    out=W/('canonical_post_ff_stat32_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    record={'schema':'MASTER_CANONICAL_POST_FF_EXACT32_REINDEX_V1','state':'FAILED_PRESERVED','utc':R.utc(),
        'source_sha256':R.sha(__file__),'helper_sha256':HELPER_SHA,'plan_sha256':PLAN_SHA,'prior_receipt_sha256':PRIOR_SHA,
        'expected_head':HEAD,'fetches':0,'merges':0,'ref_writes':0,'automatic_retry':False,'refresh_path_count':32}
    try:
        with lock as owned:
            record['workflow_lock']=owned.identity
            R.plain(R.ROOT,True);R.plain(R.ROOT/'.git',True)
            for marker in ('index.lock','MERGE_HEAD','MERGE_MSG','AUTO_MERGE','rebase-apply','rebase-merge'):
                R.need(not (R.ROOT/'.git'/marker).exists(),'Unexpected Git operation marker')
            resources=api.resources([R.ROOT,out]);record['admission']=resources
            R.need(resources['physical_available_bytes']>=1536*1024**2
                   and resources['commit_headroom_bytes']>=1536*1024**2
                   and len(resources['disk_available_bytes'])==2
                   and all(x>=10*1024**3 for x in resources['disk_available_bytes'].values()),'Fresh reserve admission failed')
            g=R.OwnedGit(api,out)
            R.need(g.run('rev-parse','HEAD').decode().strip()==HEAD
                   and g.run('branch','--show-current').decode().strip()=='main','Canonical HEAD/branch differs')
            tree=R.parse_tree(g.run('ls-tree','-r','-z',HEAD))
            R.need(R.parse_index(g.run('ls-files','--stage','-z'))==tree,'Whole index modes/OIDs differ from HEAD')
            R.need(status_scope(g.run('status','--porcelain=v1','-z','--untracked-files=no'),R)==set(names)|dirty_names,
                   'Fresh exact38 status scope differs')
            R.need(R.names(g.run('diff','--no-ext-diff','--no-textconv','--name-only','-z'))==dirty_names,
                   'Genuine content differences exceed original six')
            for row in dirty:
                R.need(tree.get(row['path'])=={k:row['head'][k] for k in ('mode','oid')},'Dirty committed blob changed')
            R.check_false(rows,tree);R.check_dirty(dirty)
            index=R.ROOT/'.git/index';index_before=R.sha(index)
            record['index_sha256_before']=index_before
            record['preserved']=[R.preserve(index,out/'original.index.bin')]
            private=out/'original_six_dirty';private.mkdir()
            for i,row in enumerate(dirty):record['preserved'].append(R.preserve(R.rooted(row['path']),private/f'{i:02d}.bin'))
            R.save(out/'preserve_first.json',{'files':record['preserved'],'private_originals_not_for_automatic_publication':True})
            R.need(R.sha(index)==index_before,'Raw index changed before exact reindex')
            R.check_false(rows,tree);R.check_dirty(dirty)
            record['attributes']=R.check_attributes(g.run('check-attr','-z','text','filter',
                'working-tree-encoding','ident','--',*names),set(names))
            g.run('add','--',*names)
            R.need(R.parse_index(g.run('ls-files','--stage','-z'))==tree,'Reindex changed whole indexed content/modes')
            R.need(g.run('rev-parse','HEAD').decode().strip()==HEAD,'HEAD changed')
            R.check_false(rows,tree);record['six_dirty_files_unchanged']=R.check_dirty(dirty)
            R.need(not g.run('diff','--cached','--no-ext-diff','--no-textconv','--name-only','-z'),'Staged changes introduced')
            R.need(R.names(g.run('diff','--no-ext-diff','--no-textconv','--name-only','-z'))==dirty_names,'Final genuine dirty scope differs')
            final=g.run('status','--porcelain=v1','-z','--untracked-files=no')
            record['final_status_utf8']=final.decode('utf-8')
            R.need(status_scope(final,R)==dirty_names,'Final status exceeds original six; no scope expansion')
            record.update(state='PASS_EXACT32_REINDEX_HEAD_AND_SIX_DIRTY_UNCHANGED',
                          index_sha256_after=R.sha(index),all32_actual_raw_bytes_unchanged=True,whole_index_modes_oids_unchanged=True)
    except BaseException as e:
        record.update(error_kind=type(e).__name__,error_message=str(e));raise
    finally:
        record['original_lock_explicitly_released']=lock.released;record['commands']=g.rows if g else []
        record['all_created_git_scopes_closed']=all(x.get('owned_closure_proven') is True for x in record['commands'])
        R.save(out/'receipt.json',record)
        print(json.dumps({'state':record['state'],'path':str(out/'receipt.json'),'sha256':R.sha(out/'receipt.json')}))


if __name__=='__main__':main()
