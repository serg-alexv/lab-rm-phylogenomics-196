"""Fast-forward canonical checkout under original lock, preserving exact dirty bytes."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess
import atomic_iqtree_windows as A
W=Path(__file__).resolve().parent
ROOT=Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
 r=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,timeout=180,check=True)
 return r.stdout.decode('utf-8-sig').strip()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-main',required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert len(a.expected_main)==40 and all(c in '0123456789abcdef' for c in a.expected_main)
 assert not a.output.exists()
 assert sha(W/'atomic_iqtree_windows.py')=='80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
 closed=json.loads((W/'iqtree_controller_closure_actual01/receipt.json').read_bytes())
 assert closed['state']=='PASS_CONTROLLER_RETAINED_HANDLE_EXIT0' and closed['terminal']['exit_code']==0
 post=json.loads((W/'directory_prune_postverify_20261009T213844Z_e301284e/receipt.json').read_bytes())
 pins=post['six_dirty_g_files_unchanged'];assert len(pins)==6
 lock=A.WorkflowLock(A.Win());record={'schema':'MASTER_CANONICAL_POST_NATIVE_FAST_FORWARD_V1',
  'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':sha(__file__),
  'expected_main':a.expected_main,'state':'FAILED_PRESERVED','git_resets':0,'git_clean_calls':0}
 try:
  with lock as owned:
   record['lock_identity']=owned.identity
   assert git('branch','--show-current')=='main'
   assert git('remote','get-url','origin') in ('https://github.com/serg-alexv/lab-rm-phylogenomics-196.git','https://github.com/serg-alexv/lab-rm-phylogenomics-196')
   assert not git('diff','--cached','--name-only'),'Unexpected staged changes'
   expected={Path(r['path']).relative_to(ROOT).as_posix() for r in pins}
   assert set(git('diff','--name-only').splitlines())==expected,'Unexpected dirty tracked scope'
   for r in pins:assert Path(r['path']).stat().st_size==r['bytes'] and sha(r['path'])==r['sha256']
   record['before_head']=git('rev-parse','HEAD')
   record['fetch_stdout']=git('fetch','--no-tags','origin','main')
   assert git('rev-parse','origin/main')==a.expected_main
   record['merge_stdout']=git('merge','--ff-only','origin/main')
   record['after_head']=git('rev-parse','HEAD');assert record['after_head']==a.expected_main
   assert not git('diff','--cached','--name-only')
   assert set(git('diff','--name-only').splitlines())==expected
   for r in pins:assert Path(r['path']).stat().st_size==r['bytes'] and sha(r['path'])==r['sha256']
   record['six_dirty_files_unchanged']=[{k:r[k] for k in ('path','bytes','sha256')} for r in pins]
   record['state']='PASS_FAST_FORWARD_SIX_DIRTY_FILES_UNCHANGED'
 except BaseException as e:
  record.update(error_kind=type(e).__name__,error_message=str(e));raise
 finally:
  record['original_lock_explicitly_released']=lock.released
  with a.output.open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
 print(json.dumps({'state':record['state'],'head':record['after_head']}))
if __name__=='__main__':main()
