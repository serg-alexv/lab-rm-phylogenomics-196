"""Inventory only deleted-file ancestors in the six original cold directory groups."""
from pathlib import Path
import datetime,hashlib,json,stat

WORK=Path(__file__).resolve().parent
INITIAL=WORK/'cleanup_inventory_plan.json'
DELETED=WORK/'master_purge_01_02_receipt.json'
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
inventory=json.loads(INITIAL.read_text(encoding='utf-8-sig'))
receipt=json.loads(DELETED.read_text(encoding='utf-8-sig'))
assert receipt['state']=='PASS_EXACT_224_VERIFIED_INACTIVE_FILES_REMOVED'
deleted={Path(row['path']):row for row in receipt['deleted']}
assert len(deleted)==224
roots=[Path(group['path']) for group in inventory['candidate_groups'][:6]]
assert all(root.is_dir() for root in roots)
derived={}
for index,group in enumerate(inventory['candidate_groups'][:6]):
    root=roots[index]
    for row in group['files']:
        file=Path(row['path'])
        assert file in deleted and deleted[file]['sha256']==row['sha256'] and deleted[file]['bytes']==row['bytes']
        assert root in file.parents and not file.exists()
        parent=file.parent
        while True:
            derived[parent]=index
            if parent==root:break
            parent=parent.parent
rows=[];excluded=[]
for path,index in sorted(derived.items(),key=lambda item:(-len(item[0].parts),str(item[0]).casefold())):
    if not path.exists():
        excluded.append({'path':str(path),'reason':'ALREADY_ABSENT'});continue
    safe=True
    for ancestor in (path,*path.parents):
        info=ancestor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:safe=False;break
    if not safe or not path.is_dir() or path.resolve()!=path:
        excluded.append({'path':str(path),'reason':'UNEXPECTED_KIND_ALIAS_OR_REPARSE'});continue
    info=path.stat()
    children=[]
    # One immediate-directory enumeration only. No broad recursion or link follow.
    for child in path.iterdir():
        entry=child.lstat()
        children.append({'name':child.name,'directory':stat.S_ISDIR(entry.st_mode),
                         'reparse':bool(getattr(entry,'st_file_attributes',0)&0x400) or stat.S_ISLNK(entry.st_mode),
                         'listed_derived_ancestor':child in derived})
    empty=not children
    planned_only=all(c['directory'] and not c['reparse'] and c['listed_derived_ancestor'] for c in children)
    if not empty and not planned_only:
        excluded.append({'path':str(path),'reason':'NONEMPTY_WITH_UNEXPECTED_CONTENT','children':children});continue
    rows.append({'path':str(path),'group_root':str(roots[index]),'initial_group_index':index,
        'depth':len(path.parts),'creation_filetime':info.st_birthtime_ns//100+116444736000000000,
        'empty_at_inventory':empty,'observed_children':sorted(children,key=lambda c:c['name'].casefold()),
        'deletion_rule':'SKIP_UNLESS_SAME_PLAIN_DIRECTORY_AND_ACTUALLY_EMPTY_AT_REMOVAL'})
plan={'schema':'MASTER_EXACT_EMPTY_DIRECTORY_PRUNE_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'state':'PREPARED_NO_DIRECTORY_DELETION','remote_plan_path':'reports/master_run/20261009/cleanup/EMPTY_DIRECTORIES_PROPOSED.json',
      'initial_inventory_sha256':sha(INITIAL),'completed_file_purge_receipt_sha256':sha(DELETED),
      'completed_file_purge_commit':'114a7249b10008430f03a27cee16d2356013b624',
      'scope_roots':list(map(str,roots)),'directories':rows,'excluded':excluded,
      'directory_count':len(rows),'empty_now_count':sum(r['empty_at_inventory'] for r in rows),
      'parent_only_contains_derived_child_directories_count':sum(not r['empty_at_inventory'] for r in rows),
      'candidate_derivation':'Only ancestors of the142 deleted initial candidates, bounded by original groups0..5; single-level observations only.',
      'recursive_delete':False,'files_to_delete':0,'biological_jobs':0,'g_mutations':0,'wsl_starts':0}
output=WORK/'master_emptydir_prune_proposed.json'
output.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'plan':str(output),'sha256':sha(output),'directories':len(rows),'empty_now':plan['empty_now_count'],
                  'parents_with_only_planned_children':plan['parent_only_contains_derived_child_directories_count'],
                  'excluded':excluded},indent=2))
