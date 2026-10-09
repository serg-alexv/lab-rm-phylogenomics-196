"""Pure acceptance predicates for a future scoped Stage5 logical recovery.

No discovery, archive creation, extraction, subprocess, network or live-runtime
read occurs here. These predicates do not establish installed equivalence.
"""
from pathlib import PurePosixPath
import base64
import hashlib
import json
import posixpath
import re
import unicodedata

PREFIX = '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux'
ROOTS = {'environment_dir': PREFIX + '/detector_env',
         'models_dir': PREFIX + '/defense_models', 'padloc_db': PREFIX + '/padloc_db'}
SHARD_LIMIT = 448 * 1024**2
CHUNK_BYTES = 256 * 1024
ENTRY_FIELDS = {'role', 'path', 'kind', 'mode', 'uid', 'gid', 'mtime_ns',
                'bytes', 'sha256', 'link_target', 'xattrs',
                'source_dev', 'source_ino', 'source_nlink', 'source_ctime_ns'}
PRIVATE_COMPONENTS = {'.git', '.ssh', '.aws', '.azure', '.config/gcloud',
                      '.netrc', '.pypirc', '.npmrc', '.env', 'credentials',
                      'credentials.json', 'token', 'tokens.json', 'id_rsa', 'id_ed25519'}
PRIVATE_BYTES = {
    'PRIVATE_KEY': re.compile(rb'-----BEGIN (?:[A-Z0-9 ]{0,40})PRIVATE KEY-----'),
    'AWS_ACCESS_KEY': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'BEARER_VALUE': re.compile(rb'\b(?:Authorization\s*:\s*)?Bearer\s+[A-Za-z0-9._~+/-]{20,}', re.I),
    'URL_USER_PASSWORD': re.compile(rb'https?://[^\s/@:]{1,128}:[^\s/@]{1,512}@', re.I),
    'ASSIGNED_SECRET': re.compile(rb'\b(?:password|passwd|access_token|refresh_token|api_key|client_secret)\s*[=:]\s*[\"\']?[A-Za-z0-9_./+~-]{20,}', re.I),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


def relative(value):
    require(isinstance(value, str) and value and '\\' not in value
            and not any(ord(c) < 32 or ord(c) == 127 for c in value)
            and unicodedata.normalize('NFC', value) == value, 'Unsafe/non-UTF8-canonical relative path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and str(p) == value and '..' not in p.parts
            and (value == '.' or '.' not in p.parts), 'Noncanonical relative path')
    return value


def absolute(row):
    require(row['role'] in ROOTS, 'Unknown runtime root role')
    relative(row['path'])
    return ROOTS[row['role']] + ('' if row['path'] == '.' else '/' + row['path'])


def link_destination(row):
    target = row['link_target']
    require(isinstance(target, str) and target and '\\' not in target
            and not any(ord(c) < 32 or ord(c) == 127 for c in target), 'Unsafe symlink target')
    result = posixpath.normpath(target if target.startswith('/') else
                               posixpath.dirname(absolute(row)) + '/' + target)
    require(any(result == root or result.startswith(root + '/') for root in ROOTS.values()),
            'Symlink escapes exact selected runtime roots')
    return result


def resolve_node(path, nodes):
    """Resolve a complete captured link graph; never consult the host filesystem."""
    for _ in range(41):
        parts = PurePosixPath(path).parts
        changed = False
        for i in range(1, len(parts) + 1):
            prefix = str(PurePosixPath(*parts[:i]))
            row = nodes.get(prefix)
            if row and row['kind'] == 'symlink':
                tail = '/'.join(parts[i:])
                path = posixpath.normpath(link_destination(row) + ('/' + tail if tail else ''))
                changed = True
                break
        if not changed:
            require(path in nodes, 'Dangling/unselected link dependency needs explicit resolution')
            return nodes[path]
    raise ValueError('Symlink cycle/depth exceeds40')


def entry(row):
    require(isinstance(row, dict) and set(row) == ENTRY_FIELDS, 'Exact manifest entry schema required')
    absolute(row)
    require(row['kind'] in {'directory', 'regular', 'symlink', 'hardlink'}, 'Special file is not public runtime payload')
    require(all(type(row[k]) is int and row[k] >= 0 for k in ['mode', 'uid', 'gid', 'mtime_ns', 'bytes'])
            and row['mode'] <= 0o7777, 'Invalid POSIX metadata')
    require(all(type(row[k]) is int and row[k] >= 0 for k in
                ['source_dev', 'source_ino', 'source_nlink', 'source_ctime_ns'])
            and row['source_ino'] > 0 and row['source_nlink'] > 0,
            'Actual source inode/device/link/ctime witness required')
    require(isinstance(row['xattrs'], dict), 'Explicit complete xattr map required')
    for key, value in row['xattrs'].items():
        require(isinstance(key, str) and key and '\0' not in key and isinstance(value, str), 'Invalid xattr')
        base64.b64decode(value, validate=True)
    if row['kind'] == 'regular':
        require(sha(row['sha256']) and row['link_target'] is None, 'Regular file bytes/SHA required')
    elif row['kind'] == 'hardlink':
        require(sha(row['sha256']) and isinstance(row['link_target'], str), 'Hardlink byte witness required')
        relative(row['link_target'].split('/', 1)[1] if '/' in row['link_target'] else '')
    elif row['kind'] == 'directory':
        require(row['bytes'] == 0 and row['sha256'] is None and row['link_target'] is None, 'Directory metadata only')
    else:
        require(row['bytes'] == 0 and row['sha256'] is None, 'Symlink stores exact target, never dereferenced bytes')
        link_destination(row)
    return row


def validate_manifest(rows, runtime):
    """Validate a candidate reviewed full-tree manifest and scientific subset.

    This in-memory predicate is for bounded metadata contracts/tests. A production
    inventory must use streamed JSONL/disk indexing if its measured memory needs
    exceed admission; this function does not claim a fixed process-memory bound.
    """
    require(runtime.get('schema') == 'STAGE05_PINNED_RUNTIME_V1' and runtime.get('roots') == ROOTS,
            'Actual pinned scientific runtime and exact roots required')
    require(set(runtime.get('files', {})) == set(ROOTS), 'All three scientific runtime roles required')
    require(isinstance(rows, list), 'Reiterable bounded metadata rows required')
    nodes, keys, key_set, inodes = {}, [], set(), {}
    for row in rows:
        entry(row)
        key = row['role'] + '/' + row['path']
        require(key not in key_set, 'Duplicate runtime entry')
        keys.append(key)
        path = absolute(row)
        if row['path'] != '.':
            parent = posixpath.dirname(path)
            require(parent in nodes and nodes[parent]['kind'] == 'directory', 'Missing/nonplain parent')
        else:
            require(row['kind'] == 'directory', 'Each root is a plain directory')
        if row['kind'] == 'hardlink':
            target = row['link_target']
            require(target in key_set, 'Hardlink must name a prior captured file')
            role, rel = target.split('/', 1)
            require(role in ROOTS, 'Hardlink root role')
            other = nodes[ROOTS[role] + ('' if rel == '.' else '/' + rel)]
            require(other['kind'] == 'regular' and all(row[k] == other[k] for k in
                    ['mode', 'uid', 'gid', 'mtime_ns', 'bytes', 'sha256', 'xattrs',
                     'source_dev', 'source_ino', 'source_nlink', 'source_ctime_ns']), 'Hardlink bytes/metadata differ')
        inode = (row['source_dev'], row['source_ino'])
        require(inode not in inodes or row['kind'] == 'hardlink',
                'Repeated source inode requires an explicit prior regular hardlink')
        if row['kind'] == 'hardlink':
            require(inodes.get(inode) == row['link_target'], 'Hardlink original inode graph differs')
        else:
            inodes[inode] = key
        nodes[path] = row
        key_set.add(key)
    require(keys == sorted(keys), 'Canonical role/path order required')
    require(all(root in nodes for root in ROOTS.values()), 'Full three-root inventory required')
    for row in rows:
        if row['kind'] == 'symlink':
            resolve_node(absolute(row), nodes)
    for role, files in runtime['files'].items():
        for rel, expected in files.items():
            relative(rel)
            require(sha(expected), 'Scientific subset SHA required')
            node = resolve_node(ROOTS[role] + '/' + rel, nodes)
            require(node['kind'] in {'regular', 'hardlink'} and node['sha256'] == expected,
                    'Scientific runtime file omitted/excluded/changed')
    return {'entry_count': len(rows), 'scientific_roles': 3, 'scientific_subset_covered': True}


def private_path_reason(value):
    relative(value)
    parts = [p.casefold() for p in PurePosixPath(value).parts]
    if any(p in PRIVATE_COMPONENTS for p in parts) or '.config/gcloud' in value.casefold():
        return 'PRIVATE_OR_AMBIGUOUS_PATH_REQUIRES_WHOLE_FILE_HOLD'
    return None


def scan_secret_blocks(blocks):
    """Return reason codes only; never disclose matched bytes. Screening is not review."""
    tail, found = b'', set()
    for block in blocks:
        require(isinstance(block, bytes) and len(block) <= CHUNK_BYTES, 'Bounded byte blocks required')
        window = tail + block
        for name, pattern in PRIVATE_BYTES.items():
            if pattern.search(window):
                found.add(name)
        tail = window[-8192:]
    return sorted(found)


def shard_lengths(total, limit=SHARD_LIMIT):
    require(type(total) is int and total > 0 and type(limit) is int and 0 < limit <= SHARD_LIMIT,
            'Positive stream and maximum448MiB shards required')
    return [min(limit, total - start) for start in range(0, total, limit)]


def capture_gate(inputs):
    require(inputs.get('schema') == 'STAGE05_INSTALLED_RUNTIME_CAPTURE_INPUTS_V1'
            and inputs.get('state') == 'REVIEWED_COLD_CAPTURE_READY', 'Pending recovery inputs cannot authorize capture')
    for name in ['actual_runtime_manifest_sha256', 'complete_inventory_sha256',
                 'whole_file_public_review_sha256', 'cold_exclusive_capture_receipt_sha256',
                 'license_source_notice_review_sha256', 'published_capture_source_sha256']:
        require(sha(inputs.get(name)), 'Unfilled mandatory actual pin: ' + name)
    require(inputs.get('roots') == ROOTS and inputs.get('original_prefix_required') is True,
            'Exact original installation prefixes required')
    require(inputs.get('all_required_runtime_files_public_and_covered') is True
            and inputs.get('all_special_metadata_resolved') is True,
            'Required private/unresolved files or metadata block complete public recovery')
    require(inputs.get('installed_build_equivalence') == 'NOT_ESTABLISHED',
            'Capture preparation must not claim cold restoration equivalence')
    return True
