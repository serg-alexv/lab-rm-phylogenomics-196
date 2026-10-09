"""Opt-in, preserve-first scoped index-stat refresh and one canonical fast-forward.

No reset/restore/clean/force or automatic retry. The 122 refreshed paths must
already equal HEAD as raw bytes. Six genuine dirty files are preserved in C.
Native command ownership/closure declarations reuse the pinned LAB R-M helper;
this does not launch biology, WSL, a scheduler, or an additional controller.
"""
from __future__ import annotations
import argparse
import ctypes as c
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import time
import uuid

W = Path(__file__).resolve().parent
DEPLOY = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
HEAD = '80331d535d622517adf7921be42fc9931cdc23ee'
INDEX_SHA = '8cc1fbd9651748cd3e57fdb20f87240d9da42a647ab0b54f55e42c3ff5a259fe'
PLAN_SHA = '7f3a3f9e09fc1fdfdaa19d81589ce362a20a079e3bf40c2c7cdac68e4c6def03'
API_SHA = '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
OID = re.compile(r'^[0-9a-f]{40}$')
SHA = re.compile(r'^[0-9a-f]{64}$')
MAX_BYTES = 256 * 1024**2


def need(ok, message):
    if not ok:
        raise ValueError(message)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(path, value):
    # Only a new unique C evidence namespace; no original files are overwritten.
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())


def relpath(name):
    need(isinstance(name, str) and name and '\\' not in name and ':' not in name,
         'Unsafe project-relative path')
    parts = PurePosixPath(name).parts
    need(not name.startswith('/') and all(p not in ('.', '..', '') for p in parts)
         and '/'.join(parts) == name and parts[0].casefold() != '.git', 'Unsafe path components')
    need(not any('*' in p or '?' in p or '[' in p or '\x00' in p for p in parts),
         'Pathspec metacharacter forbidden')
    return name


def plain(path, directory=False):
    s = Path(path).lstat()
    need(not getattr(s, 'st_file_attributes', 0) & 0x400, 'Reparse path forbidden')
    need(stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode),
         'Unexpected file type')
    return s


def rooted(name, allow_absent=False, root=ROOT):
    name = relpath(name)
    path = root
    plain(root, True)
    for i, part in enumerate(PurePosixPath(name).parts):
        path /= part
        if not path.exists() and not path.is_symlink():
            need(allow_absent, 'Expected path absent')
            return root.joinpath(*PurePosixPath(name).parts)
        plain(path, i != len(PurePosixPath(name).parts) - 1)
    return path


def proof(path):
    path = Path(path); before = plain(path)
    need(before.st_size <= MAX_BYTES, 'Individual bounded file size exceeded')
    h = hashlib.sha256(); g = hashlib.sha1(b'blob '+str(before.st_size).encode()+b'\0')
    with path.open('rb') as f:
        while block := f.read(1024**2):
            h.update(block); g.update(block)
    after = plain(path)
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'File changed while hashing')
    return {'bytes': before.st_size, 'sha256': h.hexdigest(), 'blob_oid': g.hexdigest()}


def parse_tree(raw):
    values = {}
    for row in raw.split(b'\0'):
        if row:
            meta, name = row.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            name = relpath(name.decode('utf-8'))
            need(name not in values and kind == 'blob' and mode in ('100644', '100755'),
                 'Unsupported or duplicate tracked entry')
            values[name] = {'mode': mode, 'oid': oid}
    return values


def parse_index(raw):
    values = {}
    for row in raw.split(b'\0'):
        if row:
            meta, name = row.split(b'\t', 1)
            mode, oid, stage = meta.decode().split()
            name = relpath(name.decode('utf-8'))
            need(name not in values and stage == '0', 'Unmerged or duplicate index entry')
            values[name] = {'mode': mode, 'oid': oid}
    return values


def validate_plan(v):
    need(v['schema'] == 'MASTER_CANONICAL_EXACT_SCOPED_STAT_REFRESH_PLAN_V1'
         and v['expected_original_head'] == HEAD
         and v['expected_original_index_sha256'] == INDEX_SHA and v['root'] == str(ROOT),
         'Plan original authority differs')
    a, b = v['refresh_paths'], v['six_dirty_files']
    names = [relpath(r['path']) for r in a+b]
    need(len(a) == 122 and len(b) == 6 and len(set(names)) == 128
         and sum(r['bytes'] for r in a) == 26237726, 'Plan exact scope differs')
    for r in a+b:
        need(type(r['bytes']) is int and 0 < r['bytes'] <= MAX_BYTES
             and SHA.fullmatch(r['sha256']) and OID.fullmatch(r['head']['oid'])
             and r['head']['mode'] == r['index']['mode'] and r['head']['oid'] == r['index']['oid']
             and r['index']['stage'] == 0, 'Plan pin invalid')
    return a, b


def target_scope(old, target, dirty):
    need(all(target.get(p) == old.get(p) for p in dirty), 'Target changes a preserved dirty committed blob')
    return sorted(p for p in old.keys() | target.keys() if old.get(p) != target.get(p))


class OwnedGit:
    """One suspended git, assigned before resume; exact retained exit + empty job."""
    def __init__(self, api, spool, cwd=ROOT):
        self.api, self.spool, self.cwd, self.rows = api, Path(spool), Path(cwd), []
        self.hooks = self.spool/'empty_hooks'; self.hooks.mkdir()
        self.exe = str(Path(shutil.which('git')).resolve())
        self.exe_sha256 = sha(self.exe)

    def run(self, *args, timeout=180):
        import msvcrt
        api = self.api; number = len(self.rows)
        row = {'utc': utc(), 'args': list(args), 'timeout_seconds': timeout,
               'state': 'FAILED_PRESERVED', 'git_exe_sha256': self.exe_sha256}
        stat_refresh = len(args) >= 3 and args[:3] == ('add', '--refresh', '--')
        # Git treats this stat-only write as optional. The read-only global
        # flag suppresses its persistence even though `add --refresh` exits0.
        optional = os.environ.get('GIT_OPTIONAL_LOCKS')
        need(not stat_refresh or optional in (None, '1'), 'Ambient optional-lock suppression forbids authorized refresh')
        row['optional_index_refresh_enabled'] = stat_refresh
        argv = [self.exe, *([] if stat_refresh else ['--no-optional-locks']), '-c', 'core.fsmonitor=false',
                '-c', 'core.hooksPath='+str(self.hooks), '-c', 'gc.auto=0',
                '-c', 'maintenance.auto=false', *args]
        row['argv'] = argv; row['cwd'] = str(self.cwd)
        outpath, errpath = (self.spool/f'{number:02d}.{s}.bin' for s in ('stdout', 'stderr'))
        job = api.create_job(None, None); api.ok(job, 'Create owned Git job')
        proc = api.PROCESS(); born = None; start = time.monotonic()
        try:
            limits = api.EXTENDED(); limits.BasicLimitInformation.LimitFlags = 0x2000
            api.ok(api.set_job(job, 9, c.byref(limits), c.sizeof(limits)), 'Git kill-on-close')
            with open(os.devnull, 'rb') as null, outpath.open('xb') as out, errpath.open('xb') as err:
                handles = [msvcrt.get_osfhandle(f.fileno()) for f in (null, out, err)]
                try:
                    for h in handles: os.set_handle_inheritable(h, True)
                    si = api.STARTUP(); si.cb = c.sizeof(si); si.dwFlags = 0x100
                    si.hStdInput, si.hStdOutput, si.hStdError = handles
                    command = c.create_unicode_buffer(subprocess.list2cmdline(argv))
                    api.ok(api.create(self.exe, command, None, None, True, 0x4 | 0x4000 | 0x08000000,
                                      None, str(self.cwd), c.byref(si), c.byref(proc)), 'Create suspended Git')
                finally:
                    for h in handles: os.set_handle_inheritable(h, False)
                born = api.identity(proc.hProcess, proc.dwProcessId)
                need(not born['exited'] and Path(born['executable']).resolve() == Path(self.exe), 'Git identity differs')
                row['launch'] = born
                api.ok(api.assign(job, proc.hProcess), 'Assign Git before resume')
                need(api.resume(proc.hThread) == 1, 'Resume Git exactly once')
                api.close(proc.hThread); proc.hThread = None
                while True:
                    wait = api.wait(proc.hProcess, 1000)
                    need(wait in (0, 258), 'Git retained wait failed')
                    need(outpath.stat().st_size <= 64*1024**2 and errpath.stat().st_size <= 64*1024**2,
                         'Git command log bound exceeded')
                    if wait == 0: break
                    if time.monotonic()-start >= timeout: raise TimeoutError('Owned Git deadline')
                end = api.identity(proc.hProcess, proc.dwProcessId, born['executable'], born['session_id'])
                stop = time.monotonic()+5
                remaining = api.job_state(job)
                while remaining['job_active_processes'] and time.monotonic() < stop:
                    time.sleep(.05); remaining = api.job_state(job)
                row.update(terminal=end, owned_job=remaining)
                need(end['exited'] and end['creation_filetime'] == born['creation_filetime']
                     and end['exit_filetime'] > end['creation_filetime']
                     and remaining['job_active_processes'] == 0 and not remaining['job_pids'], 'Git closure unproven')
                row['owned_closure_proven'] = True
                need(end['exit_code'] == 0, 'Git command nonzero; inspect retained stderr')
                row['state'] = 'EXIT0_OWNED_JOB_EMPTY'
        except BaseException as e:
            row.update(error_kind=type(e).__name__, error_message=str(e))
            if proc.hProcess and not row.get('owned_closure_proven'):
                row['terminate_owned_job'] = bool(api.terminate_job(job, 125))
                row['terminate_exact_child'] = bool(api.terminate(proc.hProcess, 125))
                row['cleanup_wait_result'] = api.wait(proc.hProcess, 5000)
                try:
                    end = api.identity(proc.hProcess, proc.dwProcessId,
                        born['executable'] if born else self.exe, born['session_id'] if born else None)
                    remaining = api.job_state(job); stop = time.monotonic()+5
                    while remaining['job_active_processes'] and time.monotonic() < stop:
                        time.sleep(.05); remaining = api.job_state(job)
                    row.update(cleanup_terminal=end, cleanup_job=remaining)
                    row['owned_closure_proven'] = bool(born and row['cleanup_wait_result'] == 0
                        and end['exited'] and end['creation_filetime'] == born['creation_filetime']
                        and end['exit_filetime'] > end['creation_filetime']
                        and remaining['job_active_processes'] == 0 and not remaining['job_pids'])
                except BaseException as query:
                    row.update(owned_closure_proven=False, closure_query_error=type(query).__name__)
            raise
        finally:
            if proc.hThread: api.close(proc.hThread)
            if proc.hProcess: api.close(proc.hProcess)
            api.close(job)
            for label, path in (('stdout', outpath), ('stderr', errpath)):
                if path.exists(): row[label] = {'path': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path)}
            row['elapsed_seconds'] = time.monotonic()-start
            self.rows.append(row); save(self.spool/f'{number:02d}.command.json', row)
        return outpath.read_bytes()


def names(raw):
    return {relpath(x.decode('utf-8')) for x in raw.split(b'\0') if x}


def check_dirty(rows, root=ROOT):
    result = []
    for r in rows:
        v = proof(rooted(r['path'], root=root))
        need(v['bytes'] == r['bytes'] and v['sha256'] == r['sha256'], 'Preserved dirty bytes drifted')
        result.append({'path': r['path'], **v})
    return result


def check_false(rows, tree, root=ROOT):
    for r in rows:
        need(tree.get(r['path']) == {'mode': r['head']['mode'], 'oid': r['head']['oid']}, 'Refresh HEAD binding drifted')
        v = proof(rooted(r['path'], root=root))
        need(v['bytes'] == r['bytes'] and v['sha256'] == r['sha256']
             and v['blob_oid'] == r['head']['oid'], 'Refresh path raw bytes drifted')


def preserve(path, destination):
    before = proof(path)
    with Path(path).open('rb') as src, destination.open('xb') as dst:
        shutil.copyfileobj(src, dst, 1024**2); dst.flush(); os.fsync(dst.fileno())
    need(proof(path) == before and proof(destination) == before, 'Preserve-first copy mismatch')
    return {'source': str(path), 'backup': str(destination), **before}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', action='store_true')
    p.add_argument('--expected-main')
    p.add_argument('--expected-source-sha256')
    args = p.parse_args()
    if not args.run:
        print(json.dumps({'state': 'PREPARED_NOT_RUN', 'G_writes': 0, 'plan_sha256': PLAN_SHA})); return
    need(os.name == 'nt' and W == DEPLOY, 'Exact Windows C-work deployment required')
    need(OID.fullmatch(args.expected_main or '') and SHA.fullmatch(args.expected_source_sha256 or ''), 'Explicit immutable main/source pins required')
    need(sha(__file__) == args.expected_source_sha256, 'Executing source pin differs')
    need(sha(W/'canonical_git_metadata_repair_plan.json') == PLAN_SHA, 'Plan bytes differ')
    need(sha(W/'atomic_iqtree_windows.py') == API_SHA, 'Original lock/API source differs')
    need(not any(k in os.environ for k in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE',
        'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_CONFIG_COUNT', 'GIT_CONFIG_PARAMETERS')),
        'Ambient Git redirection forbidden')
    plan = json.loads((W/'canonical_git_metadata_repair_plan.json').read_bytes())
    refresh, dirty = validate_plan(plan); dirty_names = {r['path'] for r in dirty}
    spec = importlib.util.spec_from_file_location('metadata_repair_pinned_api', W/'atomic_iqtree_windows.py')
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    api = A.Win(); lock = A.WorkflowLock(api)
    out = W/('canonical_git_metadata_repair_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    out.mkdir(); record = {'schema': 'MASTER_CANONICAL_PRESERVE_FIRST_METADATA_REPAIR_V1',
        'utc': utc(), 'state': 'FAILED_PRESERVED', 'source_sha256': sha(__file__), 'plan_sha256': PLAN_SHA,
        'expected_main': args.expected_main, 'original_merge_stderr': 'NOT_RECORDED',
        'backup_scope': 'C-only index and original six dirty files; never auto-restore', 'automatic_retry': False}
    g = None
    try:
        with lock as held:
            record['workflow_lock'] = held.identity
            plain(ROOT, True); plain(ROOT/'.git', True)
            for marker in ('index.lock', 'MERGE_HEAD', 'MERGE_MSG', 'AUTO_MERGE', 'rebase-apply', 'rebase-merge'):
                need(not (ROOT/'.git'/marker).exists(), 'Unexpected Git operation marker')
            need(sha(ROOT/'.git/index') == INDEX_SHA, 'Original raw index pin differs')
            admission = api.resources([ROOT, out])
            need(admission['physical_available_bytes'] >= 1536*1024**2
                 and admission['commit_headroom_bytes'] >= 1536*1024**2
                 and len(admission['disk_available_bytes']) == 2
                 and all(v >= 10*1024**3 for v in admission['disk_available_bytes'].values()),
                 'Fresh physical/commit/disk reserve gate failed')
            record['admission'] = admission
            g = OwnedGit(api, out)
            text = lambda *x: g.run(*x).decode('utf-8-sig').strip()
            need(text('rev-parse', 'HEAD') == HEAD and text('branch', '--show-current') == 'main', 'Original checkout differs')
            need(text('remote', 'get-url', 'origin') in (
                'https://github.com/serg-alexv/lab-rm-phylogenomics-196.git',
                'https://github.com/serg-alexv/lab-rm-phylogenomics-196'), 'Canonical origin differs')
            old = parse_tree(g.run('ls-tree', '-r', '-z', HEAD))
            need(parse_index(g.run('ls-files', '--stage', '-z')) == old, 'Index content differs from HEAD')
            need(not g.run('diff', '--cached', '--no-ext-diff', '--no-textconv', '--name-only', '-z'), 'Staged changes forbidden')
            need(names(g.run('diff', '--no-ext-diff', '--no-textconv', '--name-only', '-z')) == dirty_names, 'Genuine dirty scope differs')
            check_false(refresh, old); check_dirty(dirty)
            record['preserved'] = [preserve(ROOT/'.git/index', out/'original.index.bin')]
            backup = out/'original_six_dirty'; backup.mkdir()
            for i, r in enumerate(dirty):
                record['preserved'].append(preserve(rooted(r['path']), backup/f'{i:02d}.bin'))
            save(out/'preserve_first.json', {'files': record['preserved'], 'private_original_bytes_not_for_automatic_publication': True})
            # Repeat immediately before the only pre-merge index-stat mutation.
            need(sha(ROOT/'.git/index') == INDEX_SHA, 'Index drift after backup')
            check_false(refresh, old); check_dirty(dirty)
            g.run('add', '--refresh', '--', *(r['path'] for r in refresh))
            record['scoped_refresh_complete'] = True
            need(parse_index(g.run('ls-files', '--stage', '-z')) == old, 'Refresh changed indexed content')
            check_false(refresh, old); check_dirty(dirty)
            need(not g.run('diff', '--cached', '--no-ext-diff', '--no-textconv', '--name-only', '-z'), 'Refresh staged content')
            need(names(g.run('diff', '--no-ext-diff', '--no-textconv', '--name-only', '-z')) == dirty_names, 'Post-refresh content scope differs')
            g.run('fetch', '--no-tags', 'origin', 'main')
            need(text('rev-parse', 'origin/main') == args.expected_main, 'Fetched main differs from explicit publication pin')
            g.run('merge-base', '--is-ancestor', HEAD, args.expected_main)
            target = parse_tree(g.run('ls-tree', '-r', '-z', args.expected_main))
            changes = target_scope(old, target, dirty_names)
            need(sum(rooted(n).stat().st_size for n in changes if n in old) <= MAX_BYTES, 'Existing target-change byte bound')
            for n in changes:
                path = rooted(n, allow_absent=n not in old)
                if n not in old: need(not path.exists() and not path.is_symlink(), 'Target-added path already exists')
                else: need(proof(path)['blob_oid'] == old[n]['oid'], 'Target-change existing bytes differ from old HEAD')
            record['target_change_count'] = len(changes)
            check_dirty(dirty)
            need(parse_index(g.run('ls-files', '--stage', '-z')) == old, 'Index drift before merge')
            g.run('merge', '--ff-only', args.expected_main)
            record['fast_forward_command_exit0'] = True
            need(text('rev-parse', 'HEAD') == args.expected_main, 'Final HEAD differs')
            need(parse_index(g.run('ls-files', '--stage', '-z')) == target, 'Final index objects differ from target')
            checked = []
            for n in changes:
                path = ROOT.joinpath(*PurePosixPath(n).parts)
                if n not in target: need(not path.exists() and not path.is_symlink(), 'Target-deleted path remains')
                else:
                    v = proof(rooted(n)); need(v['blob_oid'] == target[n]['oid'], 'Fresh checkout raw bytes differ from target')
                    checked.append({'path': n, **v})
            record['target_changed_files_actual_raw_bytes'] = checked
            record['six_dirty_files_unchanged'] = check_dirty(dirty)
            need(not g.run('diff', '--cached', '--no-ext-diff', '--no-textconv', '--name-only', '-z'), 'Final staged changes')
            need(names(g.run('diff', '--no-ext-diff', '--no-textconv', '--name-only', '-z')) == dirty_names, 'Final genuine dirty scope differs')
            status = g.run('status', '--porcelain=v1', '-z', '--untracked-files=no')
            record['final_status_utf8'] = status.decode('utf-8')
            status_names = {relpath(x[3:].decode('utf-8')) for x in status.split(b'\0') if x}
            need(status_names == dirty_names, 'Additional status paths after FF; preserved, no automatic scope expansion')
            record.update(state='PASS_SCOPED_STAT_REFRESH_FAST_FORWARD_SIX_DIRTY_UNCHANGED', after_head=args.expected_main,
                final_index_sha256=sha(ROOT/'.git/index'))
    except BaseException as e:
        record.update(error_kind=type(e).__name__, error_message=str(e))
        raise
    finally:
        record['original_lock_explicitly_released'] = lock.released
        record['commands'] = g.rows if g else []
        record['all_created_git_scopes_closed'] = all(r.get('owned_closure_proven') is True for r in record['commands'])
        save(out/'receipt.json', record)
        print(json.dumps({'receipt': str(out/'receipt.json'), 'sha256': sha(out/'receipt.json'), 'state': record['state']}))


if __name__ == '__main__':
    main()
