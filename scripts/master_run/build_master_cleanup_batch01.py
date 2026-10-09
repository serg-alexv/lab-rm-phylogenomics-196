"""Build this exact cold-history batch locally. No network, publication or purge."""
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import ast, datetime, hashlib, json, os, re, shutil, stat, sys, unicodedata, zipfile, zlib

WORK = Path(__file__).resolve().parent
INVENTORY = WORK / 'cleanup_inventory_plan.json'
PLAN = WORK / 'cleanup_inventory_plan.md'
METADATA = WORK / 'master_cleanup_batch01_metadata'
ASSET = WORK / 'master_cleanup_batch01.zip'
ROOTS = (WORK, Path(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196'))
PREFIXES = ('current_chat_work', 'retained_20261008')
PINS = {'inventory': '0836bf9540e86126d8ac3aaa10187ca7e74e3e0bff483e721f5f31fd6acab382',
        'plan': 'd518ce3305e3c36c8e5831bd84c9d48fc87faf1870e811d627594337363832d8',
        'portable_release': 'd587bd9342a85837e6875f7c90c1bac3e8d751053932383fcae568550926d5ad',
        'license': 'c03cea027b4b40e4402fabd08557736727ec3d5bc54ad64ab6472de432198cad'}
PORTABLE = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196\scripts\portable_release.py')
LICENSE_URL = 'https://raw.githubusercontent.com/iqtree/iqtree3/63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de/LICENSE'


def require(value, message):
    if not value: raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def plain(path, directory=False):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve(strict=True), 'Noncanonical source path')
    for item in (path, *path.parents):
        entry = item.lstat()
        require(not stat.S_ISLNK(entry.st_mode) and not getattr(entry, 'st_file_attributes', 0) & 0x400,
                'Source or ancestor is a symlink/reparse point: ' + str(item))
    require(path.is_dir() if directory else path.is_file(), 'Wrong source kind: ' + str(path))
    return path


def write_new(path, data):
    path = Path(path)
    require(WORK in path.resolve().parents, 'Output escapes current C work directory')
    with path.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


def main():
    require(sys.platform == 'win32', 'This batch reads only the two actual Windows C scopes')
    for path in ROOTS: plain(path, True)
    require(sha(plain(INVENTORY)) == PINS['inventory'] and sha(plain(PLAN)) == PINS['plan'], 'Initial inventory/plan drift')
    inventory = json.loads(INVENTORY.read_text(encoding='utf-8-sig'))
    require(inventory['schema'] == 'MASTER_LOCAL_ARCHIVE_PURGE_PREPARATION_V1'
            and inventory['scope_roots'] == list(map(str, ROOTS)) and len(inventory['candidate_groups']) == 14,
            'Unexpected cleanup scope/schema')
    require(not any(path.exists() for path in (ASSET, ASSET.with_suffix('.zip.partial'), ASSET.with_suffix('.zip.sha256'))),
            'Preserve existing archive/partial/sidecar; no overwrite')
    records, seen, files = [], set(), []
    for index, group in enumerate(inventory['candidate_groups']):
        group_path = plain(group['path'], Path(group['path']).is_dir())
        expected_paths = {Path(row['path']) for row in group['files']}
        observed_paths = {path for path in group_path.rglob('*') if path.is_file()} if group_path.is_dir() else {group_path}
        require(expected_paths == observed_paths, 'Candidate group membership changed: ' + str(group_path))
        require(group['remote_coverage_verified'] is False and group['deletion_authorized_now'] is False,
                'Do not silently promote a proposed deletion gate')
        for row in group['files']:
            path = plain(row['path'])
            require(path not in seen, 'Initial candidate repeated')
            seen.add(path)
            scopes = [i for i, root in enumerate(ROOTS) if root in path.parents]
            require(len(scopes) == 1, 'Candidate escapes or ambiguously matches named scopes')
            scope = scopes[0]
            member = 'payload/' + PREFIXES[scope] + '/' + path.relative_to(ROOTS[scope]).as_posix()
            require(not PurePosixPath(member).is_absolute() and '..' not in PurePosixPath(member).parts, 'Unsafe portable member')
            require(type(row['bytes']) is int and path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
                    'Source differs from initial size/SHA: ' + str(path))
            records.append({'original_absolute_path': str(path), 'portable_member': member, 'bytes': row['bytes'],
                            'sha256': row['sha256'], 'candidate_group_index': index,
                            'classification': group['classification'], 'required_gate': group['required_gate']})
            files.append((path, member))
    require(len(records) == 142 and sum(row['bytes'] for row in records) == 16194617, 'Initial142/16194617 scope differs')
    require(sha(plain(PORTABLE)) == PINS['portable_release'], 'Retained portable-release implementation changed')
    license_path = plain(METADATA / 'IQTREE-3.1.4-LICENSE.txt')
    require(sha(license_path) == PINS['license'], 'Official pinned IQTREE license differs')
    helper_copy = METADATA / 'portable_release.py'
    write_new(helper_copy, PORTABLE.read_bytes())
    # Execute only the four unchanged local ZIP functions, not module imports,
    # controllers, Git/network publication or deletion functions.
    names = ('hash_stream', 'validate_member_names', 'verify_zip', 'make_zip')
    tree = ast.parse(helper_copy.read_text(encoding='utf-8-sig'))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require({node.name for node in selected} == set(names), 'Retained pure ZIP interface differs')
    namespace = dict(Path=Path, PurePosixPath=PurePosixPath, hashlib=hashlib, json=json, os=os, re=re,
                     unicodedata=unicodedata, zipfile=zipfile, w=SimpleNamespace(digest=sha, atomic=write_new))
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(helper_copy), 'exec'), namespace)
    namespace['validate_member_names']([member for _, member in files])
    mapping = {'schema': 'MASTER_COLD_CLEANUP_ARCHIVE_MAP_V1', 'state': 'NO_PURGE', 'initial_candidate_count': 142,
               'initial_source_bytes': 16194617, 'inventory_sha256': PINS['inventory'],
               'plan_sha256': PINS['plan'], 'scope_roots': list(map(str, ROOTS)),
               'files': sorted(records, key=lambda row: row['portable_member']),
               'remote_readback': 'NOT_RUN', 'biological_jobs': 0, 'wsl_starts': 0, 'source_deletions': 0}
    map_path = WORK / 'master_cleanup_batch01_manifest.json'; write_new(map_path, json_bytes(mapping))
    sourcepins = {'schema': 'MASTER_COLD_CLEANUP_SOURCE_PINS_V1', 'state': 'BUILD_ONLY_NO_PURGE',
                  'source_inventory': {'path': str(INVENTORY), 'sha256': PINS['inventory']},
                  'proposed_deletion_plan': {'path': str(PLAN), 'sha256': PINS['plan']},
                  'builder_sha256': sha(__file__), 'portable_release_sha256': PINS['portable_release'],
                  'executed_original_functions_only': list(names), 'controller_or_publication_imports': False,
                  'python': sys.version, 'zlib_compile_version': zlib.ZLIB_VERSION,
                  'zlib_runtime_version': zlib.ZLIB_RUNTIME_VERSION,
                  'iqtree_source_pin_sha256': sha(WORK/'iqtree_3_1_4_source_review/source_pin.json'),
                  'iqtree_license': {'source_url': LICENSE_URL, 'sha256': PINS['license'],
                                     'read_only_fetch_exception': 'Explicit parent authorization; no publication network calls'},
                  'initial_source_files': 142, 'initial_source_bytes': 16194617}
    pins_path = METADATA/'sourcepins.json'; write_new(pins_path, json_bytes(sourcepins))
    guide = ('MASTER cold cleanup batch01: historical preparations and exact copies, NO_PURGE.\n'
             'All142 original candidates occur once under payload/, preserving16194617 original bytes.\n'
             'Original absolute paths map to safe portable members in control/member_mapping.json.\n'
             'SYNTHETIC/NOT_RUN/failed historical labels remain evidence, never scientific acceptance.\n'
             'Original IQTREE copyright/header notices are unchanged; its pinned GPLv2 LICENSE is included.\n'
             'SHA256SUMS.txt covers every other ZIP member; CRC and initial SHA/size are independently reopened locally.\n'
             'No source deletion, GitHub upload/readback, WSL or biology occurred. Remote readback is required before any purge.\n')
    notes_path = WORK/'master_cleanup_batch01_notes.md'; write_new(notes_path, guide.encode())
    files += [(INVENTORY, 'control/initial_cleanup_inventory_plan.json'), (PLAN, 'control/proposed_deletion_plan.md'),
              (map_path, 'control/member_mapping.json'), (pins_path, 'control/sourcepins.json'),
              (Path(__file__), 'code/build_master_cleanup_batch01.py'), (helper_copy, 'code/portable_release.py'),
              (WORK/'iqtree_3_1_4_source_review/source_pin.json', 'notices/IQTREE-3.1.4-source-pin.json'),
              (license_path, 'notices/IQTREE-3.1.4-LICENSE.txt'), (notes_path, 'control/NO_PURGE_notes.md')]
    result = namespace['make_zip'](ASSET, files, guide)
    with zipfile.ZipFile(ASSET) as archive:
        require(archive.testzip() is None, 'ZIP CRC failed')
        require(len(archive.namelist()) == len(set(archive.namelist())) == len(files) + 2, 'ZIP duplicate/unexpected count')
        require({name for _, name in files} | {'README.txt', 'SHA256SUMS.txt'} == set(archive.namelist()), 'ZIP coverage differs')
        for row in records:
            info = archive.getinfo(row['portable_member'])
            with archive.open(info) as stream: digest = namespace['hash_stream'](stream)
            require(info.file_size == row['bytes'] and digest == row['sha256'], 'ZIP differs from initial inventory')
            require(sha(plain(row['original_absolute_path'])) == row['sha256'], 'Source changed during archive build')
        require(all(info.date_time == (2026, 10, 8, 0, 0, 0) for info in archive.infolist()), 'Nondeterministic ZIP timestamps')
    require(namespace['verify_zip'](ASSET) == result['payload_members'] and ASSET.stat().st_size < 500 * 1024**2,
            'Portable SHA manifest/size verification failed')
    receipt = dict(result, schema='MASTER_COLD_CLEANUP_LOCAL_BUILD_V1', state='LOCAL_ZIP_VERIFIED_NO_PURGE',
                   asset_path=str(ASSET), sidecar_path=str(ASSET.with_suffix('.zip.sha256')),
                   initial_source_files=142, initial_source_bytes=16194617, initial_source_recheck='ALL_MATCH',
                   zip_members=len(files)+2, crc='ALL_PASS', all_initial_member_hashes_and_sizes_verified=True,
                   all_zip_member_sha256_verified=True, deterministic_order_and_timestamps=True,
                   remote_readback='NOT_RUN', network_publications=0, wsl_starts=0, biological_jobs=0, source_deletions=0,
                   builder_sha256=sha(__file__), manifest_sha256=sha(map_path),
                   completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write_new(WORK/'master_cleanup_batch01_build_receipt.json', json_bytes(receipt))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__': main()
