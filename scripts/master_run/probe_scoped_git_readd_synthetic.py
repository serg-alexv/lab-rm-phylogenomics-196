"""Read/write ONLY the preserved tiny nonscientific C Git fixture; no G access."""
from pathlib import Path
import importlib.util
import json

W=Path(__file__).resolve().parent
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
T=module('synthetic_fixture',W/'test_canonical_git_metadata_repair.py')
A=module('pinned_win_api',W/'atomic_iqtree_windows.py')
base=W/'canonical_stat_refresh_synthetic_20261009T225627Z_7a04b6d3'
repo=base/'synthetic_repo';out=base/'exact_readd_probe';out.mkdir()
g=T.R.OwnedGit(A.Win(),out,repo)
before=T.index_entries((repo/'.git/index').read_bytes())
objects=T.R.parse_index(g.run('ls-files','--stage','-z'))
dirty=T.R.proof(repo/'dirty.txt')
g.run('add','--','scoped.txt')
after=T.index_entries((repo/'.git/index').read_bytes())
assert T.R.parse_index(g.run('ls-files','--stage','-z'))==objects
assert T.R.proof(repo/'dirty.txt')==dirty
assert after['scoped.txt']['size']==(repo/'scoped.txt').stat().st_size
assert all(before[n]['raw']==after[n]['raw'] for n in ('untouched.txt','dirty.txt'))
receipt={'schema':'MASTER_SCOPED_UNCHANGED_READD_SYNTHETIC_PROBE_V1','state':'PASS_EXACT_UNCHANGED_READD_FIXED_STAT_PRESERVED_ALL_INDEX_OIDS',
 'dataset_kind':'SYNTHETIC_NONBIOLOGICAL','source_sha256':T.R.sha(__file__),'subject_sha256':T.R.sha(W/'repair_canonical_git_metadata.py'),
 'before_sizes':{k:x['size'] for k,x in before.items()},'after_sizes':{k:x['size'] for k,x in after.items()},
 'all_index_oids_modes_unchanged':True,'out_of_scope_entry_bytes_unchanged':True,'dirty_bytes_unchanged':True,
 'commands':g.rows,'all_owned_jobs_closed':all(x.get('owned_closure_proven') for x in g.rows),'G_accesses':0}
T.R.save(out/'receipt.json',receipt)
print(json.dumps({'path':str(out/'receipt.json'),'sha256':T.R.sha(out/'receipt.json'),'state':receipt['state'],'sizes':receipt['after_sizes']}))
