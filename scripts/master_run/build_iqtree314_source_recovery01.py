"""Package the three retained public IQ-TREE source exports and exact Git supplement.

No extraction, source modification, installation, scientific job, network or deletion.
Retained read-handle discipline follows the independently reviewed history builder;
the byte-pinned atomic Windows module supplies only its GetPerformanceInfo reader.
"""
from pathlib import Path, PurePosixPath
import argparse, ctypes, hashlib, importlib.util, json, msvcrt, os, re, stat, time, zipfile
from ctypes import wintypes as W

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
NEW = 'iqtree314_source01_20261009T205427Z_7d051710'
OLD = 'iqtree314_source01_20261009T204525Z_40601c75'
OUT = WORK / 'master_iqtree314_source_recovery01'
NAME = 'master_iqtree314_source_recovery01.zip'
CHUNK = 256 * 1024
HELPER = '80a202540920547087ad851483e238e31d1ea9b88b2fdc24511eda908f37d827'
CURRENT = 'de29dc79d9001cd00104a6287c4be556bcf1715967b2a5ae574c99d0c92ba662'
FIRST = '86d824c0ad6b8a6972ec9b6557109c4af64205875d2909a703e11c6114878568'
GIT = '4b5d6aa580496004b342d8d49cbe8f6629e835f8'
ORIGINAL = '6a22862d34ecc3e5a11e59c29726711016ad6a66f3b9283603e46cae77358797'
EXPORTED = '65991b0d98a7003ec9b0ae5ee821287b4c7e0c7294c0ed47b502e97f3b6085e4'
REPOS = [
    ('iqtree3', 'iqtree/iqtree3', '63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de', '4605e2cff872f408e5174efecb4715122f9582d9', 1077, 81595459),
    ('cmaple', 'trongnhanuit/cmaple', '3d45b1ab68e2d68a2825bf17a531e22200578cd6', '58f3347daf5803388375277896e3e08b2fa87b9c', 820, 25117159),
    ('lsd2', 'tothuhien/lsd2', 'c61110f3a4fa05325b45c97b2134792ff9d55d4c', '39662489fd879fca80e166f26c797a8a1024d7e6', 41, 5845352),
]
# These are previously captured public inputs, never a directory-wide selection.
SUCCESS = {
    'iqtree3-63c330d90dd02241dbbbaf1e9f9e9cc6dadbd1de.tar.gz': '2bd03d26a581ee566f4c9977d6fadf08e00ea553030fc625e27f4d12051c5e20',
    'cmaple-3d45b1ab68e2d68a2825bf17a531e22200578cd6.tar.gz': 'b8b4d6da2b8571f5a469d1d7154e15135893dc3b5b74876b1131bfdb031a29a9',
    'lsd2-c61110f3a4fa05325b45c97b2134792ff9d55d4c.tar.gz': '9bbeaa0f8f35783c1d8dec74df6c93a804dbca808fa04484f9123de4e7258b53',
    'iqtree3_actual_blobs.json': 'ff258205da93456d0c345449c507b1d2113ca5fd7d974b2d0f549d990bc41209',
    'iqtree3_git_commit.json': '13d5d086637bf5e3fc7bb8f49db3ab833a16cad8b809484c78d588696e3ef36e',
    'iqtree3_git_tree.json': '13bc8e7085008a83a36705827b56f078880a84399bf7a585e2d5f6c4a388ac1b',
    'cmaple_actual_blobs.json': 'a66d7596baf8b2fe389a73f260f67cabcdee6a4eaa91792a2fdf185f3fc41088',
    'cmaple_git_commit.json': '9eec11eae3564111037de5e49fa165b978aac9214530bb21ecbe58cfb45f3ef7',
    'cmaple_git_tree.json': 'cf068acb811d3256c3f22419a61bd2069cb048a3d3c875eccb996f148b785704',
    'lsd2_actual_blobs.json': '49e87a8d99e209b7d106c65492c33c1ede1bb4caffee72864459946fbb11be65',
    'lsd2_git_commit.json': '63798c8770f0315d8a6b83cb107e8d97d2ad056f19b53b08329c2aad68785a2a',
    'lsd2_git_tree.json': 'b2494b86c605dbbfabf8dbdc4663222e76e0d7c7ecc6c9134397f798c0b06ee5',
    'receipt.json': '46d1ac0eaa4b72bc935b4c2bb27303f6ee121b8ea24018b97691753b6a8635d6',
    'tag_commit.json': '484f59c0af1a9cef20d02a6d03da605f190eb016baa1d5394d1dc4a17f2e633a',
    'original_git_blobs/' + GIT + '.blob': ORIGINAL,
}
FAILURE = {
    'receipt.json': 'c8291a1a496bdff08fe5c2197896b9d781f7c166e358c8a2c37729581415035e',
    'tag_commit.json': '484f59c0af1a9cef20d02a6d03da605f190eb016baa1d5394d1dc4a17f2e633a',
    'iqtree3_git_commit.json': '13d5d086637bf5e3fc7bb8f49db3ab833a16cad8b809484c78d588696e3ef36e',
    'iqtree3_git_tree.json': '13bc8e7085008a83a36705827b56f078880a84399bf7a585e2d5f6c4a388ac1b',
    'metadata_diagnosis.json': '93ba1e42932f03400561d780196d9e701a35e01c7f23f0fc97f2df86ad819dd2',
    'export_diagnosis.json': 'b512ef3b277cfd203b5fd5c29d62ec12d02b48d52c9a9434a77dad6c8e025ba1',
}
CONTROLS = {
    'acquire_iqtree314_source01.py': CURRENT,
    'acquire_iqtree314_source01_attempt01.py': FIRST,
    'atomic_iqtree_windows.py': HELPER,
    'iqtree314_source01_independent_review.json': 'cfdd6225f09ec2d3f3bdc839273b83a8d63cf857ef4a1664f08be9c0fb962ef3',
    'iqtree314_source02_independent_review.json': 'f8c40ee9dcb8ded5099c519e286cf47b76d5322dbf53a566f9ee5ad4f10ffcec',
}
DEADLINE = float('inf')
API = None
MINIMUM = {}

def require(ok, message):
    if not ok: raise ValueError(message)

def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')

def identity(s):
    return (str(s.st_dev), str(s.st_ino), s.st_size, str(s.st_mtime_ns), s.st_nlink,
            str(s.st_birthtime_ns), s.st_file_attributes)

def guard():
    require(time.monotonic() < DEADLINE, '600-second serial packaging deadline exceeded')
    if API is not None:
        row = API.resources([WORK])
        values = {k: row[k] for k in ('physical_available_bytes', 'commit_headroom_bytes')}
        values['c_disk_free_bytes'] = min(row['disk_available_bytes'].values())
        require(values['physical_available_bytes'] >= 3 * 1024**3 // 2
                and values['commit_headroom_bytes'] >= 3 * 1024**3 // 2
                and values['c_disk_free_bytes'] >= 10 * 1024**3, 'Live RAM/commit/C reserve failed; preserve partials')
        for k, v in values.items(): MINIMUM[k] = min(v, MINIMUM.get(k, v))

def digest(stream):
    value = hashlib.sha256()
    for block in iter(lambda: stream.read(CHUNK), b''):
        guard(); value.update(block)
    guard(); return value.hexdigest()

class Capture:
    def __init__(self, path, member, expected):
        require(path.resolve() == path and WORK in path.parents, 'Input outside exact C work or aliased')
        for p in (path, *path.parents):
            require(not p.lstat().st_file_attributes & 0x400, 'Reparse input or ancestor')
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size < 64 * 1024**2,
                'Nonregular/linked/oversize input')
        self.path, self.member, self.birth = path, member, identity(before)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
        kernel.CreateFileW.restype = W.HANDLE; kernel.CloseHandle.argtypes = [W.HANDLE]
        handle = kernel.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x00200000, None)
        require(handle != ctypes.c_void_p(-1).value, 'Retained read/deny-write/delete source open failed')
        try: descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException: kernel.CloseHandle(handle); raise
        self.stream = os.fdopen(descriptor, 'rb')
        try:
            self.check(); value = digest(self.stream)
            require(expected is None or value == expected, 'Previously captured input SHA differs: ' + member)
            self.stream.seek(0); self.check()
            self.record = dict(member=member, original_path=str(path), bytes=before.st_size, sha256=value,
                device=self.birth[0], file_id=self.birth[1], mtime_ns=self.birth[3], links=self.birth[4],
                birthtime_ns=self.birth[5], attributes=self.birth[6], retained_access='READ_DENY_WRITE_DELETE')
        except BaseException: self.stream.close(); raise

    def check(self):
        require(identity(self.path.lstat()) == self.birth and identity(os.fstat(self.stream.fileno())) == self.birth,
                'Retained source/path identity drift')

    def bytes(self):
        require(self.record['bytes'] < 4 * 1024**2, 'Small control bound exceeded')
        self.check(); self.stream.seek(0); data = self.stream.read(); self.stream.seek(0); self.check()
        require(hashlib.sha256(data).hexdigest() == self.record['sha256'], 'Small control drift'); return data

def validate_controls(captures):
    read = lambda name: json.loads(captures['success/' + name].bytes())
    receipt = read('receipt.json')
    require(receipt['source_sha256'] == CURRENT and receipt['state'] ==
        'PASS_THREE_PUBLIC_SOURCE_ARCHIVES_PLUS_ONE_EXACT_GIT_BLOB_ALL_ORIGINALS_RECOVERABLE', 'Actual acquisition not complete')
    require(read('tag_commit.json')['sha'] == REPOS[0][2] and len(receipt['repositories']) == 3, 'Exact source tag/repositories differ')
    for flag in ('payload_execution', 'g_writes', 'wsl_starts', 'source_deletions'):
        require(receipt[flag] == 0, 'Source-only boundary differs')
    for (name, repository, commit, tree_sha, count, byte_count), actual in zip(REPOS, receipt['repositories']):
        tree = read(name + '_git_tree.json'); obj = read(name + '_git_commit.json'); blobs = read(name + '_actual_blobs.json')
        require(obj['sha'] == commit and obj['tree']['sha'] == tree['sha'] == tree_sha and tree['truncated'] is False,
                'Captured commit/root-tree binding differs')
        expected = {row['path']: row for row in tree['tree'] if row['type'] == 'blob'}
        require(len(blobs) == len(expected) == actual['blob_count'] == count
                and set(blobs) == set(expected) and sum(row['size'] for row in expected.values()) == byte_count,
                'Exact original source-blob accounting differs')
        for path, row in blobs.items():
            pure = PurePosixPath(path)
            require(pure.as_posix() == path and not pure.is_absolute() and '..' not in pure.parts
                    and row['git_blob'] == expected[path]['sha'] and row['mode'] == expected[path]['mode']
                    and row['bytes'] == expected[path]['size'] and re.fullmatch('[a-f0-9]{64}', row['sha256']),
                    'Original blob-map/Git-tree join differs')
            if 'original_recovery_supplement' in row:
                require(name == 'iqtree3' and path == 'terraphast/appveyor.yml' and row['git_blob'] == GIT
                    and row['bytes'] == 249 and row['sha256'] == ORIGINAL and row['archive_bytes'] == 264
                    and row['archive_sha256'] == EXPORTED and row['original_recovery_supplement'] == 'original_git_blobs/' + GIT + '.blob',
                    'Unapproved source export exception')
        archive = captures['success/' + actual['archive']].record
        require(actual['repository'] == 'https://github.com/' + repository and actual['commit'] == commit
                and actual['tree_sha'] == tree_sha and actual['uncompressed_blob_bytes'] == byte_count
                and actual['url'] == 'https://codeload.github.com/' + repository + '/tar.gz/' + commit
                and archive['sha256'] == actual['sha256'] and archive['bytes'] == actual['bytes']
                and actual['all_original_git_blob_hashes_verified'] is True and actual['gzip_crc_verified'] is True
                and actual['original_codeload_archive_edited'] is False and actual['original_notice_paths']
                and all(path in blobs for path in actual['original_notice_paths']), 'Acquisition/archive/notice binding differs')
    require(sum(len(read(n + '_actual_blobs.json')) for n, *_ in REPOS) == 1938, 'All1938 source count differs')
    iq = receipt['repositories'][0]
    require(iq['submodules'] == [dict(path=n, mode='160000', type='commit', sha=c) for n, _, c, *_ in REPOS[1:]]
            and len(iq['source_export_supplements']) == 1
            and not any(r['source_export_supplements'] or r['submodules'] for r in receipt['repositories'][1:]), 'Exact submodule/supplement scope differs')
    original = captures['success/original_git_blobs/' + GIT + '.blob'].bytes()
    require(len(original) == 249 and hashlib.sha256(original).hexdigest() == ORIGINAL
            and hashlib.sha1(b'blob 249\0' + original).hexdigest() == GIT, 'Exact original supplemental Git blob differs')
    failure = json.loads(captures['first_failure/receipt.json'].bytes())
    require(failure['source_sha256'] == FIRST and failure['state'] == 'FAILED_SOURCE_ACQUISITION_PARTIALS_PRESERVED_NO_RETRY',
            'First actual failure not preserved')
    return dict(schema='MASTER_IQTREE314_SOURCE_RECOVERY_BINDING_V1', repositories=receipt['repositories'],
        original_git_blobs=1938, original_archives=3, exact_supplemental_git_blobs=1,
        first_failure_preserved=True, duplicate_first_main_archive_selected=False, original_archives_modified=False,
        all_archive_files_equal_git_bytes=False, installed_binary_equivalence='NOT_PROVEN_BY_SOURCE_ARCHIVAL',
        standalone_intel_notice='NOT_ASSERTED', scientific_acceptance='NONE_SOURCE_RECOVERY_ONLY')

def info(name):
    value = zipfile.ZipInfo(name, (2026, 10, 9, 0, 0, 0)); value.compress_type = zipfile.ZIP_STORED
    value.create_system = 3; value.external_attr = 0o100644 << 16; return value

README = b'''IQ-TREE 3.1.4 public corresponding-source recovery, with explicit source-export qualification.
Three complete original codeload tar.gz archives are retained unchanged, including their authors, copyright and notices.
Repositories and exact commits, notice paths, Git trees and all1938 original Git-blob SHA1/SHA256 records are in success/ and SOURCE_BINDING.json.
The original export contains exactly one249-byte Git blob as a264-byte CRLF export: IQ-TREE terraphast/appveyor.yml.
The exact original249-byte LF Git blob is retained at success/original_git_blobs/4b5d6aa580496004b342d8d49cbe8f6629e835f8.blob.
For a separately authorized restoration: extract IQ-TREE into a new tree; populate cmaple/ and lsd2/ from their pinned submodule archives.
Then replace ONLY terraphast/appveyor.yml with that original Git blob; SHA2566a22862d34ecc3e5a11e59c29726711016ad6a66f3b9283603e46cae77358797.
This builder does not extract, alter, install or execute source. Original archives are never edited; no broad line-ending normalization is authorized.
First failed strict verification, its two diagnoses, both executed acquisition sources and independent source reviews are preserved.
No compiled Windows-binary/build equivalence, standalone Intel-runtime notice completeness, installed-runtime completeness or scientific acceptance is claimed.
No credentials, private Codex events, machine image, unrelated payloads, G-drive writes, WSL starts or source deletions are selected.
'''

def build():
    global API, DEADLINE
    require(os.name == 'nt' and Path(__file__).resolve().parent == WORK and not OUT.exists(), 'Exact new C-only output required')
    DEADLINE = time.monotonic() + 600
    helper = WORK / 'atomic_iqtree_windows.py'
    require(hashlib.sha256(helper.read_bytes()).hexdigest() == HELPER, 'Reviewed resource-reader source differs')
    spec = importlib.util.spec_from_file_location('iqtree_source_resource_reader', helper)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); API = module.Win()
    kernel = ctypes.WinDLL('kernel32', use_last_error=True); kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.SetPriorityClass.argtypes = [W.HANDLE, W.DWORD]; kernel.SetPriorityClass.restype = W.BOOL
    kernel.GetPriorityClass.argtypes = [W.HANDLE]; kernel.GetPriorityClass.restype = W.DWORD
    own = kernel.GetCurrentProcess()
    require(kernel.SetPriorityClass(own, 0x4000) and kernel.GetPriorityClass(own) == 0x4000, 'Own below-normal reader required')
    guard(); OUT.mkdir(); captures = {}; result = dict(schema='MASTER_IQTREE314_SOURCE_RECOVERY_LOCAL_BUILD_V1', state='STARTED')
    try:
        selections = [(WORK / NEW / n, 'success/' + n, p) for n, p in SUCCESS.items()]
        selections += [(WORK / OLD / n, 'first_failure/' + n, p) for n, p in FAILURE.items()]
        selections += [(WORK / n, 'control/' + n, p) for n, p in CONTROLS.items()]
        selections += [(Path(__file__).resolve(), 'control/' + Path(__file__).name, None)]
        for path, member, pin in selections:
            require(member not in captures, 'Duplicate input member'); captures[member] = Capture(path, member, pin)
        require(len(captures) == 27 and sum(c.record['bytes'] for c in captures.values()) < 64 * 1024**2, 'Fixed27 input/64MiB bound differs')
        binding = validate_controls(captures)
        original_manifest = dict(schema='MASTER_IQTREE314_SOURCE_RECOVERY_ORIGINAL_MANIFEST_V1', original_files=27,
            files=[c.record for _, c in sorted(captures.items())], three_original_archives=True,
            first_main_archive_duplicate_excluded=True, privacy_scope='PUBLIC_OFFICIAL_SOURCE_AND_PROJECT_SOURCE_CONTROLS_ONLY')
        generated = {'SOURCE_BINDING.json': encoded(binding), 'ORIGINAL_SOURCE_MANIFEST.json': encoded(original_manifest), 'README.txt': README}
        table = {name: dict(bytes=c.record['bytes'], sha256=c.record['sha256']) for name, c in captures.items()}
        table.update({n: dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for n, data in generated.items()})
        sums = ''.join(r['sha256'] + '  ' + n + '\n' for n, r in sorted(table.items())).encode('ascii')
        generated['SHA256SUMS.txt'] = sums; table['SHA256SUMS.txt'] = dict(bytes=len(sums), sha256=hashlib.sha256(sums).hexdigest())
        archive = OUT / NAME
        with zipfile.ZipFile(archive, 'x') as bundle:
            for name in sorted(table):
                if name in generated: bundle.writestr(info(name), generated[name]); continue
                capture = captures[name]; capture.check(); capture.stream.seek(0); copied = hashlib.sha256()
                with bundle.open(info(name), 'w') as destination:
                    for block in iter(lambda: capture.stream.read(CHUNK), b''):
                        guard(); copied.update(block); destination.write(block)
                capture.check(); require(copied.hexdigest() == table[name]['sha256'], 'Copied original bytes differ')
        require(archive.stat().st_size < 500 * 1024**2, '500MiB release-asset bound exceeded')
        verified = []
        with zipfile.ZipFile(archive) as bundle:
            require(bundle.namelist() == sorted(table) and len(table) == 31 and not bundle.comment, 'Exact31 deterministic member set differs')
            for member in bundle.infolist():
                require(not member.extra and not member.comment and not member.flag_bits & 1
                        and member.compress_type == zipfile.ZIP_STORED and member.date_time == (2026, 10, 9, 0, 0, 0), 'Unexpected ZIP metadata')
                with bundle.open(member) as source: value = digest(source)
                require(value == table[member.filename]['sha256'] and member.file_size == table[member.filename]['bytes'], 'Actual EOF CRC/SHA differs')
                verified.append(dict(member=member.filename, **table[member.filename], crc32=f'{member.CRC:08x}', crc_verified=True))
        for capture in captures.values():
            capture.check(); capture.stream.seek(0); require(digest(capture.stream) == capture.record['sha256'], 'Final retained original SHA drift')
        with archive.open('rb') as source: archive_sha = digest(source)
        side = (archive_sha + '  ' + NAME + '\n').encode('ascii')
        with (OUT / (NAME + '.sha256')).open('xb') as stream: stream.write(side)
        result.update(state='PASS_LOCAL_THREE_ORIGINAL_SOURCE_ARCHIVES_ONE_GIT_SUPPLEMENT_31_MEMBERS', archive=NAME,
            bytes=archive.stat().st_size, sha256=archive_sha, sidecar_bytes=len(side), sidecar_sha256=hashlib.sha256(side).hexdigest(), sidecar_line_ending='LF',
            builder_sha256=captures['control/' + Path(__file__).name].record['sha256'], original_inputs=27, zip_members=31, SUMS_entries=30,
            original_git_blobs=1938, original_archives=3, supplemental_original_git_blobs=1, members=verified,
            source_manifest_sha256=table['ORIGINAL_SOURCE_MANIFEST.json']['sha256'], source_binding_sha256=table['SOURCE_BINDING.json']['sha256'],
            first_failure_preserved=True, original_source_hash_stability_verified=True, stream_chunk_bytes=CHUNK, streaming_readers=1,
            observed_own_priority_class=kernel.GetPriorityClass(own), resource_minimum_bytes=MINIMUM,
            source_blob_payload_validation='PRIOR_ACTUAL_ACQUISITION_RECEIPT_BOUND_NOT_RERUN_BY_BUILDER',
            installed_binary_equivalence='NOT_PROVEN_BY_SOURCE_ARCHIVAL', standalone_intel_notice='NOT_ASSERTED',
            remote_publication='NOT_RUN', remote_readback='NOT_RUN', payload_extraction=0, payload_execution=0,
            source_deletions=0, g_writes=0, wsl_starts=0, network_calls=0)
        for name, data in generated.items():
            with (OUT / {'SOURCE_BINDING.json': 'source_binding.json', 'ORIGINAL_SOURCE_MANIFEST.json': 'original_source_manifest.json'}.get(name, name)).open('xb') as stream: stream.write(data)
    except BaseException as error:
        result.update(state='FAILED_BUILD_PARTIALS_PRESERVED', error=dict(kind=type(error).__name__, message=str(error))); raise
    finally:
        for capture in captures.values(): capture.stream.close()
        with (OUT / 'build_receipt.json').open('xb') as stream: stream.write(encoded(result))
        print(json.dumps({k: result[k] for k in ('state', 'archive', 'bytes', 'sha256', 'zip_members') if k in result}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--build', action='store_true'); args = parser.parse_args()
    if args.build: build()
    else: print(json.dumps(dict(state='PREPARED_SOURCE_ONLY', original_inputs=27, expected_zip_members=31)))
