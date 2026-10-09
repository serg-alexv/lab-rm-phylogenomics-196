"""Independent source-aware IQ-TREE recovery readback; never extract or execute.

The fixed three raw source archives and one original Git supplement are streamed
against all captured upstream commit/tree/blob identities. No adoption authority.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import importlib.util
import json
import os
import re
import sys
import tarfile
import time
import zipfile

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parent
EXACT_WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
LOCAL = WORK / 'master_iqtree314_source_recovery01'
PREFIX = 'reports/master_run/20261009/cleanup/iqtree314_source01/'
OLD = WORK / 'iqtree314_source01_20261009T204525Z_40601c75'
NEW = WORK / 'iqtree314_source01_20261009T205427Z_7d051710'
CODE = {
    'verify_master_public_components01_remote.py': '6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691',
    'verify_master_original_sidecars.py': '090e8068d9f2ee0a21631541681a835de5f97bd1cf695b06537aabeb4bf24841',
    'verify_public_conda_packages01_remote.py': 'cadeda01183522be585b0f42f240fcaab8bc7a5335937e03b209a04e5ff216ed',
    'build_iqtree314_source_recovery01.py': '236eb2cd7c949decff5336978ab5cc965f115262c59ec65fb4ff25f293332242',
    'test_iqtree314_source_recovery.py': '4337684b02bd462eb3a78528d942fe1077fc579048574fd31ac4d4e1e8cd37cd',
    'acquire_iqtree314_source01.py': 'de29dc79d9001cd00104a6287c4be556bcf1715967b2a5ae574c99d0c92ba662',
    'acquire_iqtree314_source01_attempt01.py': '86d824c0ad6b8a6972ec9b6557109c4af64205875d2909a703e11c6114878568',
    'atomic_iqtree_windows.py': '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827',
}
CONTROLS = {
    'build_receipt.json': '32efdc9d2da0ec2b96ea85f5b1d4900810033020df8c238c2cbc3c4f829b48d9',
    'original_source_manifest.json': '7c9cebc2b78b6f5ce6c8facb67b3b86f668a40061425dbb09d2a54409594370b',
    'source_binding.json': '80a30ce62ba5f73176ad11787c271c58a0c5791e5e059168b9fc4c58750e2243',
    'README.txt': '6aaea8937bb7c2342ad492aaeca0c2ee6dc1dd01adf2dfc7ef46751a9339741d',
    'SHA256SUMS.txt': '2b4719435da60c0aeaed42a62c1e0d58e8324a0d7d16267cb77f34d946db5a41',
}
EXTRAS = {
    'iqtree314_source01_independent_review.json': (WORK / 'iqtree314_source01_independent_review.json', 'cfdd6225f09ec2d3f3bdc839273b83a8d63cf857ef4a1664f08be9c0fb962ef3'),
    'iqtree314_source02_independent_review.json': (WORK / 'iqtree314_source02_independent_review.json', 'f8c40ee9dcb8ded5099c519e286cf47b76d5322dbf53a566f9ee5ad4f10ffcec'),
    'iqtree314_source_recovery_builder_source_review.json': (WORK / 'iqtree314_source_recovery_builder_source_review.json', '64fca1164354ba603eb4d5f471a93b84c47ff060bdb3cf83d4c8d706b7a78712'),
    'ACQUISITION_RECEIPT.json': (NEW / 'receipt.json', '46d1ac0eaa4b72bc935b4c2bb27303f6ee121b8ea24018b97691753b6a8635d6'),
    'FIRST_FAILURE_RECEIPT.json': (OLD / 'receipt.json', 'c8291a1a496bdff08fe5c2197896b9d781f7c166e358c8a2c37729581415035e'),
    'metadata_diagnosis.json': (OLD / 'metadata_diagnosis.json', '93ba1e42932f03400561d780196d9e701a35e01c7f23f0fc97f2df86ad819dd2'),
    'export_diagnosis.json': (OLD / 'export_diagnosis.json', 'b512ef3b277cfd203b5fd5c29d62ec12d02b48d52c9a9434a77dad6c8e025ba1'),
}
ASSETS = [dict(name='master_iqtree314_source_recovery01.zip', bytes=41054085,
               sha256='4b4d123a2d901e03806136eb27a38bdc3a4d8da2dc5c0438afc4eb303d96a564')]
SIDECARS = [dict(name=ASSETS[0]['name'] + '.sha256', bytes=105, newline='\n',
                 sha256='ea3baff1e98b6ef358a611ba47dca303422d5f37478b484b2980ec50fd585635')]
REPOS = [
    ('iqtree3', 'iqtree/iqtree3', '63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de', '4605e2cff872f408e5174efecb4715122f9582d9', 1077, 81595459),
    ('cmaple', 'trongnhanuit/cmaple', '3d45b1ab68e2d68a2825bf17a531e22200578cd6', '58f3347daf5803388375277896e3e08b2fa87b9c', 820, 25117159),
    ('lsd2', 'tothuhien/lsd2', 'c61110f3a4fa05325b45c97b2134792ff9d55d4c', '39662489fd879fca80e166f26c797a8a1024d7e6', 41, 5845352),
]
EXCEPTION_PATH = 'terraphast/appveyor.yml'
ORIGINAL_GIT = '4b5d6aa580496004b342d8d49cbe8f6629e835f8'
ORIGINAL_SHA = '6a22862d34ecc3e5a11e59c29726711016ad6a66f3b9283603e46cae77358797'
EXPORTED_SHA = '65991b0d98a7003ec9b0ae5ee821287b4c7e0c7294c0ed47b502e97f3b6085e4'
MAX_EXPANDED_TAR_BYTES = 320 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(name):
    path = WORK / name
    require(hashlib.sha256(path.read_bytes()).hexdigest() == CODE[name], 'Pinned independent helper differs')
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


A = load('verify_master_public_components01_remote.py')
S = load('verify_master_original_sidecars.py')
B = load('verify_public_conda_packages01_remote.py')  # Only independent resource/owned-command/ZIP primitives.


def exception_bytes(original):
    require(len(original) == 249 and original.count(b'\n') == 15 and b'\r' not in original
            and hashlib.sha256(original).hexdigest() == ORIGINAL_SHA
            and hashlib.sha1(b'blob 249\0' + original).hexdigest() == ORIGINAL_GIT, 'Exact original supplemental Git blob differs')
    exported = original.replace(b'\n', b'\r\n')
    require(len(exported) == 264 and hashlib.sha256(exported).hexdigest() == EXPORTED_SHA,
            'Exact qualified CRLF export differs')
    return exported


class ExpandedReader:
    """Bound actual decompression, including headers, padding and post-tar tail."""
    def __init__(self, source):
        self.source = source
        self.bytes_read = 0

    def read(self, size):
        require(0 <= size <= B.BLOCK, 'Source decompression read must be bounded')
        B.guard()
        data = self.source.read(min(size, MAX_EXPANDED_TAR_BYTES - self.bytes_read + 1))
        self.bytes_read += len(data)
        require(self.bytes_read <= MAX_EXPANDED_TAR_BYTES, 'Expanded source tar exceeds 320MiB bound')
        return data


def source_tar(stream, name, commit, expected, allowed_directories, original=None):
    """Read to gzip EOF, verify Git payloads and reject unknown/nonzero tar tail."""
    prefix = name + '-' + commit
    observed = set(); names = set(); git_bytes = 0; exceptions = 0; links = 0
    with gzip.GzipFile(fileobj=stream, mode='rb') as decoded:
        expanded = ExpandedReader(decoded)
        with tarfile.open(fileobj=expanded, mode='r|') as archive:
            for member in archive:
                B.guard()
                spelling = member.name.rstrip('/') if member.isdir() else member.name
                pure = PurePosixPath(spelling)
                require(pure.parts and pure.parts[0] == prefix and not pure.is_absolute()
                        and pure.as_posix() == spelling and '..' not in pure.parts and '.' not in pure.parts
                        and spelling not in names, 'Unsafe/duplicate source tar member')
                names.add(spelling); relative = '/'.join(pure.parts[1:])
                if member.isdir():
                    require(relative in allowed_directories and member.size == 0, 'Unknown source directory')
                    continue
                require(relative in expected and relative not in observed, 'Unexpected/duplicate source blob')
                pin = expected[relative]
                if name == 'iqtree3' and relative == EXCEPTION_PATH:
                    require(original is not None and member.isfile() and member.size == 264
                            and pin['mode'] == '100644' and pin['git_blob'] == ORIGINAL_GIT
                            and pin['bytes'] == 249 and pin['sha256'] == ORIGINAL_SHA
                            and pin['archive_bytes'] == 264 and pin['archive_sha256'] == EXPORTED_SHA
                            and pin['original_recovery_supplement'] == 'original_git_blobs/' + ORIGINAL_GIT + '.blob',
                            'Unapproved source export exception')
                    with archive.extractfile(member) as source:
                        exported = source.read(265)
                    require(exported == exception_bytes(original), 'Actual exact source export/supplement bytes differ')
                    exceptions += 1
                else:
                    require(set(pin) == {'bytes', 'sha256', 'git_blob', 'mode'}, 'Unexpected blob exception metadata')
                    h1 = hashlib.sha1(b'blob ' + str(pin['bytes']).encode('ascii') + b'\0'); h2 = hashlib.sha256(); count = 0
                    if member.issym():
                        require(pin['mode'] == '120000' and member.size == 0, 'Source symlink mode differs')
                        payload = member.linkname.encode('utf-8', errors='surrogateescape')
                        h1.update(payload); h2.update(payload); count = len(payload); links += 1
                    else:
                        require(member.isfile() and pin['mode'] in ('100644', '100755') and member.size == pin['bytes']
                                and bool(member.mode & 0o111) == (pin['mode'] == '100755'), 'Source regular size/mode differs')
                        with archive.extractfile(member) as source:
                            for payload in iter(lambda: source.read(B.BLOCK), b''):
                                B.guard(); h1.update(payload); h2.update(payload); count += len(payload)
                    require(count == pin['bytes'] and h1.hexdigest() == pin['git_blob'] and h2.hexdigest() == pin['sha256'],
                            'Actual source Git SHA1/SHA256/size differs: ' + relative)
                observed.add(relative); git_bytes += pin['bytes']
            # Drain the tar stream, including its buffered bytes, through gzip EOF.
            # This triggers gzip trailer CRC/length checks and rejects concatenated hidden tar payloads.
            tail_bytes = 0
            for tail in iter(lambda: archive.fileobj.read(B.BLOCK), b''):
                B.guard(); tail_bytes += len(tail)
                require(tail_bytes <= B.BLOCK and not tail.strip(b'\0'), 'Unexpected nonzero/oversized source tar tail')
    require(observed == set(expected), 'Exact source blob membership incomplete')
    return dict(blob_count=len(observed), original_git_blob_bytes=git_bytes, symbolic_links=links,
                exact_export_exceptions=exceptions, gzip_crc_and_length_verified=True,
                expanded_tar_bytes=expanded.bytes_read, maximum_expanded_tar_bytes=MAX_EXPANDED_TAR_BYTES,
                filesystem_extractions=0, payload_executions=0)


def verify(args, out, result):
    B.COMMAND_OUT = out / 'command_io'; B.COMMAND_OUT.mkdir(exist_ok=False)
    result.update(owned_commands=B.COMMANDS, resource_minimum_bytes=B.RESOURCE_MIN,
                  maximum_aggregate_seconds=1800, maximum_owned_command_cleanup_seconds=5,
                  hard_kernel_io_cancellation_claim=False, filesystem_extractions=0, payload_executions=0)
    B.guard()
    extras = {PREFIX + name: row for name, row in EXTRAS.items()}
    raw = A.get_controls(args, CONTROLS, {**CODE, Path(__file__).name: B.file_sha(__file__)}, PREFIX, LOCAL, out, result, extras)
    build = json.loads(raw[PREFIX + 'build_receipt.json']); manifest = json.loads(raw[PREFIX + 'original_source_manifest.json'])
    binding = json.loads(raw[PREFIX + 'source_binding.json']); acquired = json.loads(raw[PREFIX + 'ACQUISITION_RECEIPT.json'])
    require(build['schema'] == 'MASTER_IQTREE314_SOURCE_RECOVERY_LOCAL_BUILD_V1'
            and build['state'] == 'PASS_LOCAL_THREE_ORIGINAL_SOURCE_ARCHIVES_ONE_GIT_SUPPLEMENT_31_MEMBERS'
            and build['builder_sha256'] == CODE['build_iqtree314_source_recovery01.py']
            and build['sha256'] == ASSETS[0]['sha256'] and build['bytes'] == ASSETS[0]['bytes']
            and build['original_inputs'] == manifest['original_files'] == 27
            and build['zip_members'] == 31 and build['SUMS_entries'] == 30
            and build['original_git_blobs'] == binding['original_git_blobs'] == 1938
            and build['original_archives'] == binding['original_archives'] == 3
            and build['supplemental_original_git_blobs'] == binding['exact_supplemental_git_blobs'] == 1,
            'Exact source-recovery build accounting differs')
    require(binding['all_archive_files_equal_git_bytes'] is False and binding['original_archives_modified'] is False
            and binding['installed_binary_equivalence'] == build['installed_binary_equivalence'] == 'NOT_PROVEN_BY_SOURCE_ARCHIVAL'
            and binding['scientific_acceptance'] == 'NONE_SOURCE_RECOVERY_ONLY'
            and acquired['source_sha256'] == CODE['acquire_iqtree314_source01.py']
            and acquired['state'] == 'PASS_THREE_PUBLIC_SOURCE_ARCHIVES_PLUS_ONE_EXACT_GIT_BLOB_ALL_ORIGINALS_RECOVERABLE'
            and binding['repositories'] == acquired['repositories'], 'Source/export/acquisition boundary differs')
    for key in ('g_writes', 'wsl_starts', 'source_deletions', 'payload_execution', 'payload_extraction', 'network_calls'):
        require(build[key] == 0, 'Builder source-only boundary differs')
    release = selected = None
    if not args.local_inspect:
        release, selected = S.begin(A, args, ASSETS, SIDECARS, out, result)
    path = (LOCAL if args.local_inspect else out) / ASSETS[0]['name']
    side = (ASSETS[0]['sha256'] + '  ' + ASSETS[0]['name'] + '\n').encode('ascii')
    require(len(side) == SIDECARS[0]['bytes'] and A.sha(side) == SIDECARS[0]['sha256'], 'Original LF sidecar pin differs')
    if args.local_inspect:
        require((LOCAL / SIDECARS[0]['name']).read_bytes() == side, 'Actual local original LF sidecar differs')
    observed = B.verify_zip(path, ASSETS[0], A.member_table(build['members']))
    originals = {row['member']: row for row in manifest['files']}
    require(len(originals) == len(manifest['files']) == 27
            and set(observed) == set(originals) | {'ORIGINAL_SOURCE_MANIFEST.json', 'SOURCE_BINDING.json', 'README.txt', 'SHA256SUMS.txt'},
            'Exact27 originals/31 outer members differ')
    for member, row in originals.items():
        require(observed[member]['bytes'] == row['bytes'] and observed[member]['sha256'] == row['sha256']
                and row['retained_access'] == 'READ_DENY_WRITE_DELETE' and row['links'] == 1, 'Captured original byte binding differs')
    for name, pin in CODE.items():
        if 'control/' + name in observed:
            require(observed['control/' + name]['sha256'] == pin, 'Archived actual producer source differs')
    for name, (_, pin) in EXTRAS.items():
        member = ('success/receipt.json' if name == 'ACQUISITION_RECEIPT.json' else 'first_failure/receipt.json'
                  if name == 'FIRST_FAILURE_RECEIPT.json' else 'first_failure/' + name
                  if name in ('metadata_diagnosis.json', 'export_diagnosis.json') else 'control/' + name)
        if member in observed:
            require(observed[member]['sha256'] == pin, 'Archived original review/failure control differs')
    repo_results = []
    with zipfile.ZipFile(path) as archive:
        for name, member in (('original_source_manifest.json', 'ORIGINAL_SOURCE_MANIFEST.json'), ('source_binding.json', 'SOURCE_BINDING.json'),
                             ('README.txt', 'README.txt'), ('SHA256SUMS.txt', 'SHA256SUMS.txt')):
            require(archive.read(member) == raw[PREFIX + name], 'Actual archived/published source control differs')
        require(json.loads(archive.read('success/tag_commit.json'))['sha'] == REPOS[0][2], 'Pinned source tag target differs')
        first = json.loads(archive.read('first_failure/receipt.json'))
        require(first['source_sha256'] == CODE['acquire_iqtree314_source01_attempt01.py']
                and first['state'] == 'FAILED_SOURCE_ACQUISITION_PARTIALS_PRESERVED_NO_RETRY', 'Original failed strict source check not preserved')
        supplement = archive.read('success/original_git_blobs/' + ORIGINAL_GIT + '.blob'); exception_bytes(supplement)
        require(len(binding['repositories']) == 3, 'Exact source repositories differ')
        for (name, repository, commit, tree_sha, count, total), record in zip(REPOS, binding['repositories']):
            tree = json.loads(archive.read('success/' + name + '_git_tree.json'))
            commit_obj = json.loads(archive.read('success/' + name + '_git_commit.json'))
            blobs = json.loads(archive.read('success/' + name + '_actual_blobs.json'))
            expected = {row['path']: row for row in tree['tree'] if row['type'] == 'blob'}
            require(tree['truncated'] is False and tree['sha'] == commit_obj['tree']['sha'] == tree_sha and commit_obj['sha'] == commit
                    and len(expected) == len(blobs) == count and set(expected) == set(blobs)
                    and sum(row['size'] for row in expected.values()) == total
                    and record['commit'] == commit and record['tree_sha'] == tree_sha
                    and record['repository'] == 'https://github.com/' + repository
                    and record['archive'] == name + '-' + commit + '.tar.gz'
                    and record['blob_count'] == count and record['uncompressed_blob_bytes'] == total,
                    'Exact source commit/tree/blob identities differ')
            for relative, pin in blobs.items():
                require(pin['mode'] == expected[relative]['mode'] and pin['git_blob'] == expected[relative]['sha']
                        and pin['bytes'] == expected[relative]['size'] and re.fullmatch('[a-f0-9]{64}', pin['sha256']),
                        'Original source blob/Git tree metadata join differs')
            directories = {''}
            for row in tree['tree']:
                pure = PurePosixPath(row['path'])
                directories.update(str(p) for p in pure.parents if str(p) != '.')
                if row['type'] in ('tree', 'commit'):
                    directories.add(row['path'])
            gitlinks = [{key: row[key] for key in ('path', 'mode', 'type', 'sha')}
                        for row in tree['tree'] if row['type'] == 'commit']
            expected_links = [dict(path=n, mode='160000', type='commit', sha=c) for n, _, c, *_ in REPOS[1:]] if name == 'iqtree3' else []
            require(gitlinks == record['submodules'] == expected_links,
                    'Exact pinned submodule Gitlinks differ')
            archive_member = 'success/' + record['archive']
            require(observed[archive_member]['sha256'] == record['sha256'] and observed[archive_member]['bytes'] == record['bytes'],
                    'Original raw codeload archive differs')
            with archive.open(archive_member) as compressed:
                checked = source_tar(compressed, name, commit, blobs, directories, supplement if name == 'iqtree3' else None)
            require(checked['blob_count'] == count and checked['original_git_blob_bytes'] == total
                    and checked['exact_export_exceptions'] == (1 if name == 'iqtree3' else 0)
                    and all(path in blobs for path in record['original_notice_paths']) and record['original_notice_paths'],
                    'Independent all-blob/source-notice coverage differs')
            repo_results.append(dict(repository=repository, commit=commit, tree_sha=tree_sha, **checked))
    require(sum(r['blob_count'] for r in repo_results) == 1938 and sum(r['original_git_blob_bytes'] for r in repo_results) == 112557970,
            'Full original Git source coverage differs')
    if not args.local_inspect:
        A.end_release(args, release, selected, result)
    result.update(state='PASS_LOCAL_IQTREE_SOURCE31_MEMBERS_1938_GITBLOBS_REMOTE_NOT_RUN' if args.local_inspect else
                  'PASS_FRESH_REMOTE_IQTREE_SOURCE31_MEMBERS_1938_GITBLOBS_ONE_EXACT_SUPPLEMENT',
                  zip_members=31, internal_sum_entries=30, original_inputs=27, source_repositories=repo_results,
                  original_git_blobs=1938, original_git_blob_bytes=112557970, exact_supplemental_git_blobs=1,
                  original_archives_modified=False, all_archive_files_equal_git_bytes=False,
                  installed_binary_equivalence='NOT_PROVEN_BY_SOURCE_ARCHIVAL', standalone_intel_notice='NOT_ASSERTED',
                  scientific_acceptance='NONE_SOURCE_RECOVERY_ONLY', cleanup_authority='NONE', wipe_authority=False,
                  original_live_sources_reread=False, members=list(observed.values()))


def main():
    require(WORK == EXACT_WORK and os.name == 'nt', 'Exact current C Windows checker required')
    args = A.cli(__doc__)
    B.DEADLINE = time.monotonic() + 1800; B.RESOURCE = B.ResourceReader(); B.guard()
    A.run = B.monitored_run; A.digest = B.file_sha
    A.execute_readback(args, 'iqtree314_source_recovery01', verify)


if __name__ == '__main__':
    main()
