"""Screen exact changed-file metadata plus two bounded scientific directories.

No archive, deletion, G, WSL, network, or execution of retained project source.
Private or ambiguous whole files stay local; historical states are not upgraded.
"""
from pathlib import Path, PurePosixPath
import ast
import codecs
import ctypes
import hashlib
import importlib.util
import json
import os
import re
import stat

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
ROOT = Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
OUT = WORK / 'old_checkout_changed_history_inspection01'
META = WORK / 'old_checkout_git_preservation_metadata.json'
META_SHA = '2d7698c6a9b26a39c2e2bd511ff39b8816b9e142b93d8c16457573b507d8e8b0'
INSPECTOR = WORK / 'inspect_public_history02.py'
INSPECTOR_SHA = '671b20fc3f8b89c214d9fc50a3b793275caafce72bac03bee4379468793dcfc0'
COLLAPSED = ('docs/', 'reports/stage05/')
CHUNK = 256 * 1024
MAX_FILE = 16 * 1024**2
MAX_TOTAL = 128 * 1024**2
DENY_PARTS = {'.git', '.tools', '.work', '.private_run', '.codex', '__pycache__'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def signature(info):
    return (str(info.st_dev), str(info.st_ino), info.st_size, str(info.st_mtime_ns), info.st_nlink)


def from_metadata(row):
    return (row['device'], row['file_id'], row['bytes'], row['mtime_ns'], row['link_count'])


def metadata(info):
    return {'device': str(info.st_dev), 'file_id': str(info.st_ino), 'bytes': info.st_size,
            'mtime_ns': str(info.st_mtime_ns), 'link_count': info.st_nlink,
            'birthtime_ns': str(getattr(info, 'st_birthtime_ns', 'UNAVAILABLE')),
            'attributes': info.st_file_attributes}


def literal(relative):
    pure = PurePosixPath(relative.rstrip('/'))
    require(pure.as_posix() == relative.rstrip('/') and not pure.is_absolute() and '..' not in pure.parts
            and not DENY_PARTS.intersection(part.casefold() for part in pure.parts)
            and pure.parts[0] in {'docs', 'reports', 'scripts', 'status'}, 'Private/outside candidate path held')
    path = ROOT.joinpath(*pure.parts)
    require(path.resolve() == path, 'Resolved candidate alias held')
    for part in (path, *path.parents):
        require(not part.lstat().st_file_attributes & 0x400, 'Reparse candidate or ancestor held')
    return path


def save(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


def selection():
    require(sha(META) == META_SHA, 'Frozen changed-file metadata differs')
    prior = json.loads(META.read_text(encoding='utf-8'))
    require(prior['old_root'] == str(ROOT) and len(prior['changes']) == 195, 'Exact old checkout selection differs')
    rows, held, directories = [], [], []
    for row in prior['changes']:
        if row['path'] not in COLLAPSED:
            require(row['metadata']['state'] == 'METADATA_ONLY_FILE_CONTENTS_NOT_READ', 'Unexpected initial changed kind')
            rows.append({'relative_path': row['path'], 'metadata': row['metadata'],
                         'selection_origin': 'EXACT193_VISIBLE_CHANGED_FILES', 'git_status': row['status']})
            continue
        path = literal(row['path'])
        require(signature(path.lstat()) == from_metadata(row['metadata']), 'Frozen collapsed-directory identity drift')
        stack = [path]
        visited = 0
        while stack:
            parent = stack.pop()
            before = parent.lstat()
            require(stat.S_ISDIR(before.st_mode) and not before.st_file_attributes & 0x400, 'Plain collapsed directory required')
            children = []
            with os.scandir(parent) as entries:
                for entry in entries:
                    child = parent / entry.name
                    relative = child.relative_to(ROOT).as_posix()
                    info = child.lstat()
                    visited += 1
                    require(visited <= 1000 and len(child.relative_to(path).parts) <= 8, 'Collapsed scientific scope bound exceeded')
                    children.append(relative)
                    try:
                        literal(relative)
                        require(not info.st_file_attributes & 0x400, 'Reparse child held')
                    except (ValueError, OSError) as error:
                        held.append({'relative_path': relative, 'reason': str(error), 'read': False})
                        continue
                    if stat.S_ISDIR(info.st_mode):
                        stack.append(child)
                    elif stat.S_ISREG(info.st_mode):
                        rows.append({'relative_path': relative, 'metadata': metadata(info),
                                     'selection_origin': 'BOUNDED_NOFOLLOW_COLLAPSED_DIRECTORY', 'git_status': '??'})
                    else:
                        held.append({'relative_path': relative, 'reason': 'NONREGULAR_CHILD_HELD', 'read': False})
            require(signature(before) == signature(parent.lstat()), 'Collapsed-directory metadata changed during enumeration')
            directories.append({'relative_path': parent.relative_to(ROOT).as_posix(), 'metadata': metadata(before), 'children': sorted(children)})
    require(sum(row['selection_origin'] == 'EXACT193_VISIBLE_CHANGED_FILES' for row in rows) == 193
            and len(rows) == len({row['relative_path'].casefold() for row in rows}), 'Visible-file selection count/uniqueness differs')
    require(sum(row['metadata']['bytes'] for row in rows) <= MAX_TOTAL, 'Bounded source total exceeded')
    return sorted(rows, key=lambda row: row['relative_path']), held, directories


def inspect_one(row, patterns, private_names):
    path = literal(row['relative_path'])
    before = path.lstat()
    require(signature(before) == from_metadata(row['metadata']) and stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1 and before.st_size <= MAX_FILE, 'Changed/linked/nonregular/oversize source held')
    require(not any(name in path.name.casefold() for name in private_names), 'Private-shaped filename held')
    content = bytearray()
    digest = hashlib.sha256()
    flags = set()
    tail = b''
    decoder = codecs.getincrementaldecoder('utf-8-sig')('strict')
    with path.open('rb') as stream:
        require(signature(os.fstat(stream.fileno())) == signature(before), 'Opened source identity differs')
        for block in iter(lambda: stream.read(CHUNK), b''):
            content.extend(block)
            digest.update(block)
            require(len(content) <= MAX_FILE, 'Growing source exceeds bounded review')
            try:
                decoder.decode(block)
            except UnicodeDecodeError:
                flags.add('NON_UTF8_WHOLE_FILE_HELD')
            if b'\x00' in block:
                flags.add('BINARY_NUL_WHOLE_FILE_HELD')
            window = tail + block
            for code, pattern in patterns.items():
                if pattern.search(window):
                    flags.add(code)
            tail = window[-8192:]
        try:
            decoder.decode(b'', final=True)
        except UnicodeDecodeError:
            flags.add('NON_UTF8_WHOLE_FILE_HELD')
        require(signature(os.fstat(stream.fileno())) == signature(before), 'Source identity changed during privacy read')
    require(signature(path.lstat()) == signature(before) and len(content) == before.st_size, 'Source drifted during screen')
    result = {**row, 'absolute_path': str(path), 'sha256': digest.hexdigest(), 'bytes_screened': len(content),
              'identity_rechecked': True, 'private_signature_scan': 'FULL_BYTES_NO_MATCH' if not flags else 'FLAGGED_WHOLE_FILE_HELD'}
    if flags:
        return result | {'decision': 'EXCLUDE_WHOLE_PRESERVE_LOCAL', 'reasons': sorted(flags)}
    text = content.decode('utf-8-sig')
    suffix = path.suffix.casefold()
    detail = {}
    try:
        if suffix == '.py':
            ast.parse(text)
            detail = {'kind': 'PROJECT_SCIENTIFIC_SOURCE_SYNTAX_ONLY_NO_EXECUTION',
                      'notice_lines': [line for line in text.splitlines()[:80] if re.search('copyright|license|SPDX|authors?', line, re.I)]}
        elif suffix in {'.json', '.tmp', '.replace-probe'}:
            value = json.loads(text)
            require(isinstance(value, dict), 'Non-dictionary JSON held for scientific schema review')
            detail = {'kind': 'JSON_SCIENTIFIC_SCHEMA_REVIEW_REQUIRED', 'top_level_keys': sorted(value),
                      'value_kinds': {key: type(item).__name__ for key, item in value.items()}}
        elif suffix == '.jsonl':
            values = [json.loads(line) for line in text.splitlines()]
            require(all(isinstance(value, dict) and isinstance(value.get('argv'), list) and isinstance(value.get('utc'), str)
                        for value in values), 'Non-scientific command JSONL schema held')
            detail = {'kind': 'SCIENTIFIC_COMMAND_JSONL_NO_CLOSURE_INFERENCE', 'rows': len(values),
                      'keys': sorted({key for value in values for key in value})}
        elif suffix == '.tsv':
            lines = text.splitlines()
            require(lines and '\t' in lines[0], 'Unestablished TSV header held')
            width = len(lines[0].split('\t'))
            require(all(len(line.split('\t')) == width for line in lines[1:]), 'Inconsistent scientific table held')
            detail = {'kind': 'SCIENTIFIC_TABLE_SCHEMA_REVIEW_REQUIRED', 'header': lines[0], 'rows': len(lines) - 1, 'columns': width}
        elif suffix == '.md':
            detail = {'kind': 'SCIENTIFIC_DOCUMENT_MANUAL_REVIEW_REQUIRED', 'lines': len(text.splitlines()),
                      'headings': [line for line in text.splitlines() if line.startswith('#')][:50]}
        else:
            raise ValueError('Unsupported scientific payload type held')
    except (ValueError, SyntaxError) as error:
        return result | {'decision': 'EXCLUDE_WHOLE_PRESERVE_LOCAL', 'reasons': [str(error)]}
    return result | {'decision': 'PRIVACY_SCREENED_PENDING_SCIENTIFIC_SCHEMA_AND_ATTRIBUTION_REVIEW', 'content': detail}


def main():
    require(os.name == 'nt' and Path(__file__).resolve().parent == WORK and not OUT.exists(), 'Exact new C inspection namespace required')
    require(sha(INSPECTOR) == INSPECTOR_SHA, 'Retained privacy helper drift')
    spec = importlib.util.spec_from_file_location('retained_public_history_privacy', INSPECTOR)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    require(Path(helper.__file__).resolve() == INSPECTOR and sha(INSPECTOR) == INSPECTOR_SHA, 'Privacy helper import binding differs')
    patterns = dict(helper.PATTERNS)
    patterns['AWS_ACCESS_KEY_SHAPE'] = re.compile(rb'(?:AKIA|ASIA)[A-Z0-9]{16}')
    patterns['URL_USERINFO_SHAPE'] = re.compile(rb'https?://[^\s/<>:]{1,100}:[^\s/<>@]{1,200}@')
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    source_sha = sha(Path(__file__))
    rows, held, directories = selection()
    OUT.mkdir()
    save('selection.json', {'schema': 'MASTER_OLD_CHECKOUT_CHANGED_HISTORY_SELECTION_V1', 'metadata_sha256': META_SHA,
                            'files': rows, 'held_unread_paths': held, 'collapsed_directory_observations': directories})
    decisions = []
    with (OUT / 'decisions.jsonl').open('x', encoding='utf-8', newline='\n') as target:
        for row in rows:
            try:
                decision = inspect_one(row, patterns, helper.PRIVATE_NAMES)
            except (ValueError, OSError) as error:
                decision = row | {'decision': 'EXCLUDE_WHOLE_PRESERVE_LOCAL', 'reasons': [str(error)], 'readiness_or_closure_claim': 'NONE'}
            decisions.append(decision)
            target.write(json.dumps(decision, sort_keys=True) + '\n')
            target.flush()
    require(sha(META) == META_SHA and sha(INSPECTOR) == INSPECTOR_SHA and sha(Path(__file__)) == source_sha, 'Control/source drift')
    save('inspection.json', {'schema': 'MASTER_OLD_CHECKOUT_CHANGED_HISTORY_INSPECTION_V1',
         'state': 'COMPLETE_PRIVACY_SCREEN_ONLY_PUBLIC_SCOPE_AND_ARCHIVE_PENDING',
         'source_sha256': source_sha, 'metadata_sha256': META_SHA, 'privacy_helper_sha256': INSPECTOR_SHA,
         'candidate_files': len(rows), 'candidate_bytes': sum(row['metadata']['bytes'] for row in rows),
         'screened_files': sum('sha256' in row for row in decisions),
         'screened_bytes': sum(row.get('bytes_screened', 0) for row in decisions),
         'excluded_whole_files': sum(row['decision'] == 'EXCLUDE_WHOLE_PRESERVE_LOCAL' for row in decisions),
         'unread_held_paths': held, 'privacy_screen_not_public_scope_acceptance': True,
         'files': {name: sha(OUT / name) for name in ('selection.json', 'decisions.jsonl')},
         'parallel_readers': 1, 'stream_chunk_bytes': CHUNK, 'source_deletions': 0,
         'g_writes': 0, 'wsl_starts': 0, 'network_calls': 0, 'scientific_jobs': 0,
         'historical_unknown_closure': 'PRESERVED_NO_INFERENCE', 'archive_build': 'NOT_RUN'})
    print(json.dumps({'files': len(rows), 'bytes': sum(row['metadata']['bytes'] for row in rows),
                      'excluded': sum(row['decision'] == 'EXCLUDE_WHOLE_PRESERVE_LOCAL' for row in decisions), 'output': str(OUT)}))


if __name__ == '__main__':
    main()
