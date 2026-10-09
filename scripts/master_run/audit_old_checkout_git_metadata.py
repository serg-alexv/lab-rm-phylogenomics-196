"""Fixed old-checkout Git metadata audit; no network, contents, mutation or recursion."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import os
import stat
import subprocess

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
OLD = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
PRIVATE = {'.codex', '.private_run', '.private', '.git'}


def signature(info):
    return dict(device=str(info.st_dev), file_id=str(info.st_ino), bytes=info.st_size,
                mtime_ns=str(info.st_mtime_ns), link_count=info.st_nlink)


def run(*arguments):
    result = subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', *arguments],
                            cwd=OLD, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=45, check=True, env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
    return result.stdout


def parse_status(raw):
    fields = raw.split(b'\0')
    records = []
    index = 0
    while index < len(fields) and fields[index]:
        item = fields[index]; index += 1
        if len(item) < 4 or item[2:3] != b' ':
            raise ValueError('Unexpected porcelain-v1 status record')
        status = item[:2].decode('ascii')
        path = item[3:].decode('utf-8')
        row = dict(status=status, path=path)
        if 'R' in status or 'C' in status:
            row['original_path'] = fields[index].decode('utf-8'); index += 1
        records.append(row)
    if any(fields[index:]):
        raise ValueError('Unparsed porcelain status fields')
    return records


def metadata(relative):
    if any(part.casefold() in PRIVATE for part in Path(relative).parts):
        return dict(state='PRESERVE_PRIVATE_PATH_NOT_INSPECTED')
    path = OLD / relative
    try:
        info = path.lstat()
    except FileNotFoundError:
        return dict(state='MISSING_CURRENT_LEAF')
    if info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return dict(state='PRESERVE_REPARSE_NOT_FOLLOWED', **signature(info))
    return dict(state='METADATA_ONLY_DIRECTORY_CONTENTS_NOT_ENUMERATED' if stat.S_ISDIR(info.st_mode)
                else 'METADATA_ONLY_FILE_CONTENTS_NOT_READ', **signature(info))


def main():
    if os.name != 'nt' or Path(__file__).resolve().parent != WORK:
        raise ValueError('Exact C audit namespace required')
    output = WORK / 'old_checkout_git_preservation_metadata.json'
    if output.exists():
        raise ValueError('Preserve existing metadata audit')
    index_path = OLD / '.git/index'
    before = signature(index_path.stat())
    identity = run('rev-parse', '--show-toplevel', '--git-dir', 'HEAD').decode().splitlines()
    if Path(identity[0]).resolve() != OLD or identity[1] != '.git':
        raise ValueError('Unexpected old checkout identity')
    raw = run('status', '--porcelain=v1', '-z', '--untracked-files=normal')
    changes = parse_status(raw)
    indexed = []
    for record in run('ls-files', '--stage', '-z').split(b'\0'):
        if not record:
            continue
        descriptor, path = record.split(b'\t', 1)
        mode, blob, stage = descriptor.decode('ascii').split()
        indexed.append(dict(path=path.decode('utf-8'), mode=mode, index_blob=blob, stage=int(stage)))
    refs = []
    for line in run('for-each-ref', '--format=%(refname)%09%(objectname)',
                    'refs/heads', 'refs/remotes', 'refs/tags').decode().splitlines():
        ref, sha = line.split('\t')
        refs.append(dict(ref=ref, sha=sha))
    ahead = int(run('rev-list', '--all', '--not', '--remotes', '--count').strip())
    status_after = run('status', '--porcelain=v1', '-z', '--untracked-files=normal')
    after = signature(index_path.stat())
    if before != after or raw != status_after:
        raise ValueError('Git index/status drift during metadata snapshot; preserve checkout')
    for row in changes:
        row['metadata'] = metadata(row['path'])
        path = row['path'].casefold()
        row['preservation_risk'] = ('UNTRACKED_SOURCE_OR_HISTORY_RECOVERY_NOT_PROVEN_BY_GIT' if row['status'] == '??'
                                    else 'MODIFIED_TRACKED_BYTES_NOT_PRESERVED_BY_COMMITTED_BLOB')
        if path.endswith('/'):
            row['contents'] = 'UNKNOWN_NOT_ENUMERATED_PRESERVE_DIRECTORY'
    report = dict(schema='MASTER_OLD_CHECKOUT_GIT_PRESERVATION_METADATA_V1', state='PASS_METADATA_ONLY_NO_WIPE_AUTHORITY',
                  utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), old_root=str(OLD), head=identity[2],
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  commands_use_no_optional_locks=True, fsmonitor=False, network_calls=0,
                  source_contents_dumped=0, source_payloads_explicitly_opened_by_python=0,
                  source_hashes_explicitly_computed_by_python=0, source_deletions=0, g_writes=0, wsl_starts=0,
                  git_index_before=before, git_index_after=after, status_identical_before_after=True,
                  indexed_paths=len(indexed), status_counts=dict(collections.Counter(r['status'] for r in changes)),
                  changes=changes, indexed_path_metadata=indexed, local_refs=refs,
                  commits_not_reachable_from_local_remote_tracking_refs=ahead,
                  limitations=['Remote-tracking refs are local metadata and may be stale; no fresh remote equivalence is claimed.',
                               'Untracked directories remain collapsed and unenumerated; their content/recovery status stays unknown.',
                               'No modified or untracked file contents or Git object payloads were dumped or packaged.',
                               'Git may internally read tracked file bytes to determine status; internal Git reads are not instrumented here.',
                               'This report identifies preservation risks only and never authorizes checkout, .git or host deletion.'])
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps(dict(output=str(output), head=identity[2], indexed_paths=len(indexed), status_counts=report['status_counts'],
                          local_only_commits=ahead, state=report['state'])))


if __name__ == '__main__':
    main()
