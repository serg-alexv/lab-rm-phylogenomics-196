"""Read-only local Git/byte diagnosis. No index refresh, Git writes or network."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess

W = Path(__file__).resolve().parent
ROOT = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
TARGET = '24e2299ae5a118e99aeb9b52d8cf6f973127d9bb'
OUT = W/'canonical_failed_ff_readonly_audit02'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(*args, config_only=False):
    command = ['git', '--no-optional-locks']
    if not config_only:
        command += ['-c', 'core.fsmonitor=false']
    command += list(args)
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    value = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=90)
    number = len(COMMANDS)
    (OUT/f'{number:02d}.stdout.bin').write_bytes(value.stdout)
    (OUT/f'{number:02d}.stderr.bin').write_bytes(value.stderr)
    COMMANDS.append(dict(argv=command, exit_code=value.returncode,
                         stdout_sha256=hashlib.sha256(value.stdout).hexdigest(),
                         stderr_sha256=hashlib.sha256(value.stderr).hexdigest()))
    if value.returncode:
        raise RuntimeError(f'Read-only Git failed: {args!r}: {value.stderr.decode(errors="replace")}')
    return value.stdout


def parse_tree(raw):
    result = {}
    for entry in raw.split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            result[path.decode('utf-8')] = dict(mode=mode, kind=kind, oid=oid)
    return result


def main():
    OUT.mkdir(exist_ok=False)
    gitdir = ROOT/'.git'
    index = gitdir/'index'
    before = dict(index_sha256=digest(index), index_bytes=index.stat().st_size,
                  head_bytes=(gitdir/'HEAD').read_text())
    head = git('rev-parse', 'HEAD').decode().strip()
    remote = git('rev-parse', 'origin/main').decode().strip()
    branch = git('branch', '--show-current').decode().strip()
    status = git('status', '--porcelain=v2', '--untracked-files=no').decode()
    unstaged = git('diff', '--no-ext-diff', '--no-textconv', '--name-status').decode()
    staged = git('diff', '--cached', '--no-ext-diff', '--no-textconv', '--name-status').decode()
    numstat = git('diff', '--no-ext-diff', '--no-textconv', '--numstat').decode()
    changes = git('diff', '--no-ext-diff', '--no-textconv', '--name-status', head, TARGET).decode()
    configuration = git('config', '--show-origin', '--get-regexp',
        r'^(core\.(autocrlf|eol|safecrlf|filemode|ignorecase|longpaths|fsmonitor|symlinks|sparsecheckout)|index\.version|merge\.ff)$',
        config_only=True).decode()
    old, target = (parse_tree(git('ls-tree', '-r', '-z', rev)) for rev in (head, TARGET))
    indexed = {}
    for entry in git('ls-files', '--stage', '-z').split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t', 1)
            mode, oid, stage = meta.decode().split()
            indexed[path.decode('utf-8')] = dict(mode=mode, oid=oid, stage=int(stage))
    changed_paths = {line.split('\t')[-1] for line in unstaged.splitlines()}
    status_paths = {line.split(' ', 8)[8] for line in status.splitlines() if line.startswith('1 ')}
    baseline = json.loads((W/'directory_prune_postverify_20261009T213844Z_e301284e/receipt.json').read_bytes())['six_dirty_g_files_unchanged']
    baseline_by_name = {Path(row['path']).relative_to(ROOT).as_posix(): row for row in baseline}
    rows = []
    selected = changed_paths | status_paths | set(baseline_by_name)
    if sum(ROOT.joinpath(*name.split('/')).stat().st_size for name in selected) > 256*1024**2:
        raise RuntimeError('Bounded public tracked-file read exceeds256MiB')
    for relative in sorted(selected):
        path = ROOT.joinpath(*relative.split('/'))
        raw = path.read_bytes()
        oid = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        normalized = raw.replace(b'\r\n', b'\n')
        lf_oid = hashlib.sha1(b'blob '+str(len(normalized)).encode()+b'\0'+normalized).hexdigest()
        value = dict(path=relative, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
            status_modified=relative in status_paths, content_diff_modified=relative in changed_paths,
            actual_blob_oid=oid, crlf_to_lf_blob_oid=lf_oid, crlf_pairs=raw.count(b'\r\n'),
            head=old.get(relative), index=indexed.get(relative), target=target.get(relative))
        for label, source in [('head', old), ('target', target), ('index', indexed)]:
            expected = source.get(relative, {}).get('oid')
            value['exact_'+label+'_blob'] = oid == expected
            value['crlf_to_lf_'+label+'_blob'] = lf_oid == expected
        if relative in baseline_by_name:
            pin = baseline_by_name[relative]
            value['preexisting_dirty_pin'] = {k:pin[k] for k in ('bytes','sha256')}
            value['preexisting_dirty_unchanged'] = len(raw) == pin['bytes'] and value['sha256'] == pin['sha256']
        rows.append(value)
    after = dict(index_sha256=digest(index), index_bytes=index.stat().st_size,
                 head_bytes=(gitdir/'HEAD').read_text())
    markers = {}
    for name in ('ORIG_HEAD','MERGE_HEAD','MERGE_MSG','AUTO_MERGE','index.lock'):
        path = gitdir/name
        markers[name] = dict(exists=path.exists())
        if path.is_file() and path.stat().st_size < 65536:
            markers[name].update(bytes=path.stat().st_size,sha256=digest(path))
            if name != 'index.lock': markers[name]['text'] = path.read_text(errors='replace')
    value = dict(schema='MASTER_CANONICAL_FAILED_FF_READONLY_AUDIT_V1',
        state='OBSERVATIONS_ONLY_NO_REPAIR', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        root=str(ROOT), source_sha256=digest(Path(__file__)), HEAD=head, origin_main=remote,
        requested_target=TARGET, branch=branch, status=status, unstaged=unstaged, staged=staged,
        numstat=numstat, planned_commit_changes=changes, configuration=configuration,
        before=before, after=after, index_and_HEAD_bytes_unchanged_by_audit=before==after,
        git_markers=markers, changed_tracked_count=len(changed_paths), status_modified_count=len(status_paths), rows=rows,
        six_preexisting_dirty_files_unchanged=all(r.get('preexisting_dirty_unchanged',True) for r in rows),
        tracked_index_diff_from_HEAD=[p for p,v in indexed.items() if v['stage'] or v['oid'] != old.get(p,{}).get('oid')],
        commands=COMMANDS, G_writes=0, Git_mutations=0, WSL_starts=0, network_calls=0)
    (OUT/'receipt.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(path=str(OUT/'receipt.json'),sha256=digest(OUT/'receipt.json'),
                         HEAD=head,changed_count=len(changed_paths),
                         exact_target_nonbaseline=sum(r['exact_target_blob'] for r in rows if 'preexisting_dirty_pin' not in r),
                         lf_target_nonbaseline=sum(r['crlf_to_lf_target_blob'] for r in rows if 'preexisting_dirty_pin' not in r),
                         baseline_unchanged=value['six_preexisting_dirty_files_unchanged'],
                         index_unchanged=before==after)))


COMMANDS = []
if __name__ == '__main__':
    main()
