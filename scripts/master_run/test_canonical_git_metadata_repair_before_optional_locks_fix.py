"""Pure negative guards plus a tiny new C-only nonscientific Git fixture.

The fixture deliberately corrupts only cached stat sizes in its OWN v2 index,
recomputes the index checksum, and proves `git add --refresh -- one-path`
changes that cached entry only, preserving every indexed object and dirty byte.
Never accesses the canonical G checkout or original workflow.lock.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import unittest
import uuid

W = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('repair_test_subject', W/'repair_canonical_git_metadata.py')
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)


class Contracts(unittest.TestCase):
    def test_plan_exact_scope(self):
        self.assertEqual(R.sha(W/'canonical_git_metadata_repair_plan.json'), R.PLAN_SHA)
        a, b = R.validate_plan(json.loads((W/'canonical_git_metadata_repair_plan.json').read_bytes()))
        self.assertEqual((len(a), len(b)), (122, 6))

    def test_bad_relative_paths(self):
        for n in ('../x', '/x', 'C:/x', 'x\\y', 'x//y', 'x/./y', '.git/index', 'x*'):
            with self.subTest(n=n), self.assertRaises(ValueError): R.relpath(n)

    def test_plan_duplicate_scope_rejected(self):
        v = json.loads((W/'canonical_git_metadata_repair_plan.json').read_bytes())
        v['refresh_paths'][1]['path'] = v['refresh_paths'][0]['path']
        with self.assertRaises(ValueError): R.validate_plan(v)

    def test_unmerged_index_rejected(self):
        with self.assertRaises(ValueError): R.parse_index(b'100644 '+b'a'*40+b' 1\tx\0')

    def test_dirty_committed_blob_change_rejected(self):
        with self.assertRaises(ValueError):
            R.target_scope({'d': {'mode':'100644','oid':'a'*40}}, {'d': {'mode':'100644','oid':'b'*40}}, {'d'})

    def test_target_change_scope(self):
        self.assertEqual(R.target_scope({'same':1,'old':2}, {'same':1,'new':3}, {'same'}), ['new','old'])


def index_entries(raw):
    if raw[:8] != b'DIRC\0\0\0\2': raise ValueError('Fixture requires v2 index')
    count = struct.unpack('>I', raw[8:12])[0]; offset = 12; result = {}
    for _ in range(count):
        end = raw.index(b'\0', offset+62); name = raw[offset+62:end].decode()
        length = ((end-offset+1+7)//8)*8
        result[name] = {'offset':offset,'raw':raw[offset:offset+length],
                        'size':struct.unpack('>I',raw[offset+36:offset+40])[0]}
        offset += length
    return result


def fixture():
    if os.name != 'nt' or W != R.DEPLOY: raise ValueError('Actual C fixture requires exact Windows work path')
    if R.sha(W/'atomic_iqtree_windows.py') != R.API_SHA: raise ValueError('Pinned API differs')
    spec = importlib.util.spec_from_file_location('fixture_pinned_api', W/'atomic_iqtree_windows.py')
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    out = W/('canonical_stat_refresh_synthetic_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    out.mkdir(); repo = out/'synthetic_repo'; repo.mkdir()
    spool = out/'command_io'; spool.mkdir()
    g = R.OwnedGit(A.Win(), spool, repo)
    receipt = {'schema':'MASTER_SCOPED_GIT_STAT_REFRESH_SYNTHETIC_FIXTURE_V1',
        'dataset_kind':'SYNTHETIC_NONBIOLOGICAL','state':'FAILED_PRESERVED',
        'source_sha256':R.sha(__file__),'subject_sha256':R.sha(W/'repair_canonical_git_metadata.py'),
        'G_accesses':0,'original_lock_accesses':0,'git_repository':str(repo)}
    try:
        g.run('-c','init.templateDir=','init','--initial-branch=main')
        for n in ('scoped.txt','untouched.txt','dirty.txt'): (repo/n).write_bytes((n+'\n').encode()*500)
        g.run('-c','core.autocrlf=false','add','--','scoped.txt','untouched.txt','dirty.txt')
        g.run('-c','user.name=Synthetic fixture','-c','user.email=synthetic@example.invalid',
              '-c','commit.gpgSign=false','commit','--no-verify','-m','Nonscientific scoped-stat fixture')
        g.run('update-index','--index-version=2')
        index = repo/'.git/index'; raw = bytearray(index.read_bytes()); initial = index_entries(raw)
        for n in ('scoped.txt','untouched.txt'):
            offset = initial[n]['offset']; raw[offset+36:offset+40] = struct.pack('>I',1)
        raw[-20:] = hashlib.sha1(raw[:-20]).digest(); index.write_bytes(raw)
        (repo/'dirty.txt').write_bytes(b'ACTUAL DIRTY SYNTHETIC BYTES\n')
        objects = R.parse_index(g.run('ls-files','--stage','-z'))
        stale = index_entries(index.read_bytes()); dirty_before = R.proof(repo/'dirty.txt')
        receipt['before_status'] = g.run('status','--porcelain=v1','--untracked-files=no').decode()
        g.run('add','--refresh','--','scoped.txt')
        refreshed = index_entries(index.read_bytes())
        if R.parse_index(g.run('ls-files','--stage','-z')) != objects: raise ValueError('Scoped refresh changed OIDs')
        if R.proof(repo/'dirty.txt') != dirty_before: raise ValueError('Dirty bytes changed')
        if refreshed['scoped.txt']['size'] != (repo/'scoped.txt').stat().st_size: raise ValueError('Scoped cached size not refreshed')
        for n in ('untouched.txt','dirty.txt'):
            if refreshed[n]['raw'] != stale[n]['raw']: raise ValueError('Out-of-scope cached entry changed')
        receipt.update(state='PASS_SCOPED_STAT_ONLY_REFRESH_EXACT_OUT_OF_SCOPE_PRESERVATION',
            after_status=g.run('status','--porcelain=v1','--untracked-files=no').decode(),
            all_index_modes_oids_unchanged=True,out_of_scope_index_entry_bytes_unchanged=True,
            genuine_dirty_file_bytes_unchanged=True,scoped_cache_size_before=stale['scoped.txt']['size'],
            scoped_cache_size_after=refreshed['scoped.txt']['size'],
            out_of_scope_stale_size_still=refreshed['untouched.txt']['size'],
            installed_git_version=g.run('--version').decode().strip(),
            official_installed_document=r'C:\Program Files\Git\mingw64\share\doc\git-doc\git-add.html',
            documented_option='--refresh: Do not add the file(s), but only refresh their stat() information in the index.')
    except BaseException as e:
        receipt.update(error_kind=type(e).__name__,error_message=str(e)); raise
    finally:
        receipt['commands']=g.rows
        receipt['all_created_git_jobs_closed']=all(x.get('owned_closure_proven') is True for x in g.rows)
        R.save(out/'receipt.json',receipt)
        print(json.dumps({'receipt':str(out/'receipt.json'),'sha256':R.sha(out/'receipt.json'),'state':receipt['state']}))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--fixture',action='store_true');args,rest=p.parse_known_args()
    if args.fixture: fixture()
    else: unittest.main(argv=[__file__,*rest])
