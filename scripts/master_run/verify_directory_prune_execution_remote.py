"""Read back exact directory-cleanup recovery bytes; default no operation.

No producer import, extraction, current old-C/G rescan, owner or lock query,
cleanup or scientific execution. Remote mode uses retained owned-gh monitoring.
"""
from pathlib import Path, PureWindowsPath
import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
import time
import zipfile

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parent
EXACT_WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
LOCAL = WORK / 'master_directory_prune_execution01'
PREFIX = 'reports/master_run/20261009/cleanup/directory_prune_execution01/'
ASSET = dict(name='master_directory_prune_execution01.zip', bytes=1296741,
             sha256='2154a6bfdc2ea74dc6a18312032e4ff45812c5cabdb7ffb29b1cb5c323da7815')
SIDECAR = dict(name=ASSET['name'] + '.sha256', bytes=105, newline='\n',
               sha256='959995eeae411432db1269e35a2e98ed48d3289b92853da441a2f9374e630b88')
HELPERS = {
    'verify_master_public_components01_remote.py': '6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691',
    'verify_master_original_sidecars.py': '090e8068d9f2ee0a21631541681a835de5f97bd1cf695b06537aabeb4bf24841',
    'verify_public_conda_packages01_remote.py': 'cadeda01183522be585b0f42f240fcaab8bc7a5335937e03b209a04e5ff216ed',
}
CONTROLS = {
    'build_receipt.json': '2deb1c11d4b0e8170fe5f098e8567a8feb13d2a6aee71e76fcc28a67cf5a3a30',
    'index.json': '00ce955aa08315ec53510375c0b323000126a01e9ffd9837b0a6e037fe93d780',
    'execution_summary.json': 'a9d07e7deb974f5ad0da406b0966fd1f1c84722660de1c49a9dbec8070a3c365',
    'SHA256SUMS.txt': '9869a9e397fe48bd279a033ffae679f7585ae3caf262562944f3600642654179',
    SIDECAR['name']: SIDECAR['sha256'],
    'completion.json': '5c7ba15b4aac144ae4ef54372daee95e20d617544c9cc057021ca1bcaa68b62b',
}
CODE = {
    **HELPERS,
    'build_directory_prune_execution_archive.py': '37108a35b4c0ed7df91de478e36365aff76440d3ffddfd345648217fc09c661a',
    'test_build_directory_prune_execution_archive.py': 'de061b5201f061abd8b55a689199eb365dd54a7cee723867c043b64d40402973',
    'build_directory_prune_execution_archive_draft150e.py': '150e6c4f46f2f13325cb28f163bfbfa82291c4fb65cd0e12eabf9495bc74f421',
    'test_build_directory_prune_execution_archive_draft2fe5.py': '2fe5ec14bc870a1b8b163a94a387802fc2536d68e157976f32ae441d4b65a124',
}
EXTRAS = {
    'directory_prune_execution_archive_METHODS.md': (WORK / 'directory_prune_execution_archive_METHODS.md', '633afb31bd6a36c8aaddab32d98cd0a068a4648a940305bac2c5027bd3f7a56c'),
    'directory_prune_execution_archive_builder_independent_review.json': (WORK / 'directory_prune_execution_archive_builder_independent_review.json', '87545d3c70fc3e7f8826adff49811cf474d16f5b4f730337db3c1c32099846d2'),
    'directory_prune_execution_archive_preparation.json': (WORK / 'directory_prune_execution_archive_preparation.json', '87bc8a6d61cb9b9eda3f49cb84b0aeeed50dfcb951dd1cc92aa8e77ade64dc43'),
    'directory_prune_execution_archive_METHODS_draft_e5e6.md': (WORK / 'directory_prune_execution_archive_METHODS_draft_e5e6.md', 'e5e6f927997a16d58ae100ad97b7e7623f76925a8939e25d59bf8b2d65e5555a'),
    'PUBLIC_COMPLETION.json': (WORK / 'directory_prune_execution_archive_completion.json', 'c14ab736f0dbe841919e1efca89b9d5405f8f79ff0daba0c78cbf868a5aaefe3'),
}
ORIGINAL_PINS = {'build_directory_prune_execution_archive.py': '37108a35b4c0ed7df91de478e36365aff76440d3ffddfd345648217fc09c661a',
 'build_directory_prune_execution_archive_draft150e.py': '150e6c4f46f2f13325cb28f163bfbfa82291c4fb65cd0e12eabf9495bc74f421',
 'diagnose_directory_postverify_provider.py': 'a6267a18461fbe06e9d7732cdc3e4d8166a860e10b16645b6333cb62a6940f3d',
 'directory_handle_fixture_20261009T211154Z_9cf77be3.json': '348ee7030d49d14524290f0ec27302e67d67d216f342c97a1fb44e83526cc0ac',
 'directory_handle_fixture_20261009T211154Z_9cf77be3.jsonl': '73a0978d42e5f106d60888187611eb0218314b9aeb016d5b47e4f3cfb48b0a23',
 'directory_handle_fixture_20261009T211310Z_843dbf82.json': 'eebac12d62403b273713ee0f4aaad17955a4c6b7d33631e63ee1f86dc4e47ba1',
 'directory_handle_fixture_20261009T211310Z_843dbf82.jsonl': '0109e6d8ae71bef6e465931a52510e8cd627e3ebda92a148caca42f8ab4cac4c',
 'directory_handle_postverifier_independent_source_review.json': '5a537805072cd07d1f23e7d681309ba4b70a2607dbe65cc4747e0d51929437c6',
 'directory_handle_postverifier_provider_corrected_independent_review.json': '66b047a1ad3b86cc609e4bdb094e4cfb32e8c0164c130808012099950e068840',
 'directory_handle_postverify_METHODS.md': '3a03f5449f38c28b964987f5321b9785656a3da8dbc37be8aad093971440c648',
 'directory_handle_postverify_METHODS_02.md': '81592902eb00cca198e7db48b428cfd6fd4a68ea1352eb7e61c9fb269b760abf',
 'directory_handle_postverify_preparation.json': '9aee97a33bc9aaecf6dc53846105d6b7044e87d5d3d0079dc31510d17534dbc4',
 'directory_handle_postverify_preparation_02.json': '747a792f0a37b425fb9af017dd8dfbec5e9fdee2dfeade432f0dd27dc29afe23',
 'directory_handle_pruner_METHODS.md': 'e4d9b5836742fda28fd10a5eac8a20c6098ec4120602ce0ae1f190d61c6497b4',
 'directory_handle_pruner_authority_TEMPLATE_FALSE.json': '7b89156403bd19567b5753e8974c2c08332576b60f78fad0d588210ee2e945da',
 'directory_handle_pruner_corrected_independent_review.json': 'c0bc38628a140885211a397af9e23bbe10f9f432b2c682c13d44c03cd1d1b20b',
 'directory_handle_pruner_independent_source_review.json': '2c6d1d5126e8cd2ee89bc3f26ab652eeb7ce283e6940ae474e93d58418310d52',
 'directory_handle_pruner_preparation_completion.json': 'a71ad508fc8744ec2be5f9b45fa9204e1eeb66d4919bf4b96a3e27776d10cb9a',
 'directory_handle_pruner_preparation_completion_02.json': 'ee0a5516641e21d2c16e60c4acdd11f60c2569a0e42308c8086a00a9cccd211a',
 'directory_postverify_provider_diagnostic01.json': '202bb1e18ea0ee91a55fb382b342233c1f2b87cad24c62d6d1750ee135da0b6a',
 'directory_prune_execution_archive_METHODS.md': '633afb31bd6a36c8aaddab32d98cd0a068a4648a940305bac2c5027bd3f7a56c',
 'directory_prune_execution_archive_METHODS_draft_e5e6.md': 'e5e6f927997a16d58ae100ad97b7e7623f76925a8939e25d59bf8b2d65e5555a',
 'directory_prune_execution_archive_builder_independent_review.json': '87545d3c70fc3e7f8826adff49811cf474d16f5b4f730337db3c1c32099846d2',
 'directory_prune_postverify_20261009T212934Z_35de2767/receipt.json': '9253109026a3faaf66758ae71c6f570644b1e63d3743dd81a8a170d3593edbea',
 'directory_prune_postverify_20261009T212934Z_35de2767/started.json': '1179c3a3eb84767b3a087c4e5f2fa94b301a74055fed6f394229e84966259ec5',
 'directory_prune_postverify_20261009T213844Z_e301284e/receipt.json': '7820c5048722f517c291f7eab74ea7199197c1ed354b90f3bdfe4df5a35889dd',
 'directory_prune_postverify_20261009T213844Z_e301284e/started.json': '42d79f6eef296cf14bc2a9d7586cff459578301bf37035fa9d0fd98206112565',
 'finalize_directory_handle_pruner_prep.py': 'fe0fce80376ac26e419c0fd4321d8462ef583e11fbc9161176120f267fec057c',
 'finalize_directory_handle_pruner_prep_mapping_attempt01.py': 'd339168a1fe082d8ac8ee270e96e61c7789a381de425036283edc9531692a2e0',
 'master_directory_authority01_remote_readback.json': '1e58f75d5c4183f7fafdce237be3c07775d023c5cc092c8b09de9dc471f6b7e3',
 'master_directory_provider_correction08_remote_readback.json': '6e25f14055234f4f7fceb72b2139b5ac84d9980bad71e2d4cceceb2dee819f0f',
 'master_directory_prune01_execution.jsonl': '5ff92323b29af9a6620a251825ea6531e95bbf14ef2ff6c3d36279beb891f4a5',
 'master_directory_prune_root_authority01.json': '0afeb4c2a06b4920765466474f354ed0638a228c450eb17a1c1acc9ee7bfbe63',
 'master_directory_prune_root_review01.json': '9203c29e478620a430e75f121508eb87dc2eeb90f55f670bb9312b9ba070f50a',
 'master_history02_postverify_20261009T201921Z_f90337c5/receipt.json': 'a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082',
 'master_old_scientific_emptydirs_proposed_02.json': 'be2ae1939e1c81d54c63b1fd949928506e2f2251a3e5e9d341b122ac4f72bdf5',
 'master_recovery_receipts05/directory_execution_checkpoint.json': 'b287cd8a1d18e206c212fe65709b569d10027eacfefc9000871631b99a9a5232',
 'master_recovery_verified04_remote_readback.json': '393abb637ce96ced1155c66001184004dfcc09dd578ed083d19769366b6279f6',
 'old_scientific_emptydirs01_readback_20261009T205057Z_9c38bcce/receipt.json': 'e71b02889d5443017ef5ab8be206b1fc4e5f9f81c3de14c602eeaeef70c68063',
 'prepare_old_scientific_emptydirs.py': '7287809f47f912eddb21ba9f05d927872ef710d45ac6857837ae6689c320b21f',
 'prune_old_scientific_directories.py': '9b64d17bb2612ce35051b87d77863709d875c1f910865fd6a4db2f6ddd265381',
 'prune_old_scientific_directories_attempt01.py': '2f608bd1f11b3aac9223c7c751b9a9d8f5cb5c02568861bd6cfeadfff9304604',
 'test_build_directory_prune_execution_archive.py': 'de061b5201f061abd8b55a689199eb365dd54a7cee723867c043b64d40402973',
 'test_build_directory_prune_execution_archive_draft2fe5.py': '2fe5ec14bc870a1b8b163a94a387802fc2536d68e157976f32ae441d4b65a124',
 'test_directory_handle_prune_fixture.py': 'c0c62e1aa3bf7b6d7b011b6afbddf07c8827e6af54729961b955eda703a0031a',
 'test_directory_handle_prune_fixture_attempt01.py': '72e3a86e28f08e845cb37a9ef62f6ea056d220902e7074b4fdc63dbcb8e4d0c7',
 'test_verify_directory_handle_prune.py': '1b78956bc935cce8de952f6f855f1f31af9471bcaf41e5d58ea6898898b41f4a',
 'test_verify_directory_handle_prune_attempt01.py': '46c059fb90a76c17d11d810b128cd8e06c56b006741dd4a94f29fdae54376d42',
 'verify_directory_handle_prune.py': '00db7e85b734743f6bf0cf7c107d271878425ec9b7494df5688a93319cc559f2',
 'verify_directory_handle_prune_attempt01.py': '130e7eca3a784d069b4033858c04faebbe2b4765c7942cdd0b9bb35a624cda0c'}
OLD = PureWindowsPath(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
ROOTS = [OLD / p for p in ('data', '.work/review2', '.work/stage02_validated', '.work/source_locus_inputs_v1',
                         '.work/stage03_markers_v1', '.work/stage04a_windows_alignments_v1', '.work/stage04_phylogeny_v2')]
KEEP = OLD / '.work/review2/stage05_raw_review/installed_rejected_serializer.txt'
OWNERS = {(4768, 134360369876207076), (27048, 134360369803845506)}
PLAN = 'master_old_scientific_emptydirs_proposed_02.json'
JOURNAL = 'master_directory_prune01_execution.jsonl'
POST = 'directory_prune_postverify_20261009T213844Z_e301284e/receipt.json'
BASELINE = 'master_history02_postverify_20261009T201921Z_f90337c5/receipt.json'
AUTHORITY = 'master_directory_prune_root_authority01.json'
REMOTE_PROPOSAL = 'old_scientific_emptydirs01_readback_20261009T205057Z_9c38bcce/receipt.json'


def require(value, message):
    if not value:
        raise ValueError(message)


def load_helper(name):
    path = WORK / name
    require(hashlib.sha256(path.read_bytes()).hexdigest() == HELPERS[name], 'Pinned independent helper differs')
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


A = load_helper('verify_master_public_components01_remote.py')
S = load_helper('verify_master_original_sidecars.py')
B = load_helper('verify_public_conda_packages01_remote.py')


def bytes_sha(stream):
    count, digest = 0, hashlib.sha256()
    for chunk in iter(lambda: stream.read(256 * 1024), b''):
        B.guard()
        count += len(chunk)
        digest.update(chunk)
    B.guard()
    return count, digest.hexdigest()


def strict_zip(path, expected):
    require(path.stat().st_size == ASSET['bytes'] and B.file_sha(path) == ASSET['sha256'], 'Whole archive pin differs')
    observed = {}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        A.safe_names(names)
        require(names == sorted(expected) and len(names) == 54 and not archive.comment, 'Exact sorted54 member set differs')
        require(sum(info.file_size for info in archive.infolist()) == sum(row['bytes'] for row in expected.values())
                < 64 * 1024**2, 'Expanded archive cap differs')
        checks = {}
        for line in archive.read('SHA256SUMS.txt').decode('ascii').splitlines():
            match = re.fullmatch(r'([a-f0-9]{64})  (.+)', line)
            require(match and match[2] not in checks, 'Invalid/duplicate internal SUMS')
            checks[match[2]] = match[1]
        require(set(checks) == set(names) - {'SHA256SUMS.txt'}, 'Exact exhaustive53 SUMS differs')
        for info in archive.infolist():
            require(info.compress_type == zipfile.ZIP_DEFLATED and not info.flag_bits & 1
                    and stat.S_IFMT(info.external_attr >> 16) == stat.S_IFREG
                    and info.date_time == (2026, 10, 9, 0, 0, 0) and not info.extra and not info.comment,
                    'Unexpected ZIP type/compression/metadata')
            with archive.open(info) as stream:
                size, digest = bytes_sha(stream)  # EOF validates actual ZIP CRC.
            row = expected[info.filename]
            require(size == info.file_size == row['bytes'] and digest == row['sha256']
                    and row['crc_verified'] is True and f'{info.CRC:08x}' == row['crc32'], 'Actual member CRC/SHA/size differs')
            require(info.filename == 'SHA256SUMS.txt' or checks[info.filename] == digest, 'Internal SUMS SHA differs')
            observed[info.filename] = dict(member=info.filename, bytes=size, sha256=digest,
                                          crc32=f'{info.CRC:08x}', crc_verified=True)
    return observed


def validate_plan(plan):
    rows = plan['directories']
    require(len(rows) == len({row['path'] for row in rows}) == plan['directory_count'] == 5542
            and plan['scope_roots'] == list(map(str, ROOTS)) and len(plan['held']) == 6
            and plan['always_preserved_fragment'] == str(KEEP)
            and plan['empty_now_count'] == 3736 and plan['planned_children_only_count'] == 1806
            and plan['execution_authorized'] is False, 'Original proposal scope differs')
    held, seen = {row['path'] for row in plan['held']}, set()
    for row in rows:
        path = PureWindowsPath(row['path'])
        require(path.is_absolute() and str(path) == row['path'] and '..' not in path.parts
                and (path in ROOTS or any(root in path.parents for root in ROOTS))
                and path not in {KEEP, *KEEP.parents} and row['path'] not in held
                and row['attributes'] & 0x10 and not row['attributes'] & 0x400, 'Protected/unsafe original path')
        require(all(child['kind'] == 'DIRECTORY' and child['path'] in seen
                    and PureWindowsPath(child['path']).parent == path for child in row['observed_children']),
                'Original postorder child binding differs')
        seen.add(row['path'])
    return rows


def journal_rows(stream):
    count = 0
    while True:
        B.guard()
        line = stream.readline(1024 * 1024 + 1)
        if not line:
            break
        count += 1
        require(count <= 16628 and len(line) <= 1024 * 1024 and line.endswith(b'\n'), 'Journal record cap/termination differs')
        yield json.loads(line)
    require(count == 16628, 'Exact16628 actual journal records required')


def owner_identity(rows, post=False):
    require(len(rows) == 2 and {(r['pid'], int(r['creation_filetime'])) for r in rows} == OWNERS
            and all(r.get('alive') is True if post else r.get('exited') is False for r in rows),
            'Historical exact owner birth/liveness records differ')


def check_journal(events, rows, protected):
    events = iter(events)
    first = next(events)
    require(first['event'] == 'BEGIN' and first['state'] == 'ROOT_AUTHORIZED_EXACT_DIRECTORY_HANDLES_ONLY'
            and first['source_sha256'] == ORIGINAL_PINS['prune_old_scientific_directories.py']
            and first['plan_sha256'] == ORIGINAL_PINS[PLAN] and first['authorization_sha256'] == ORIGINAL_PINS[AUTHORITY]
            and first['fresh_remote_proof_sha256'] == ORIGINAL_PINS[REMOTE_PROPOSAL]
            and first['intended_directories'] == len(rows) and first['protected_before'] == protected
            and first['files_deleted'] == first['recursive_deletes'] == 0
            and first['workflow_lock'] == 'UNTOUCHED_NOT_OPENED' and first['deadline_seconds'] == 900,
            'Historical BEGIN authority/source/protected binding differs')
    owner_identity(first['owners_before'])
    removed = set()
    core = ('path', 'volume_serial', 'file_id_128', 'creation_filetime', 'legacy_file_id', 'attributes', 'links', 'final_handle_path')
    for row in rows:
        before, mark, after = next(events), next(events), next(events)
        actual = before['actual']
        require(before['event'] == 'BEFORE_DISPOSITION' and before['path'] == row['path'] and before['expected'] == row
                and all(actual[k] == row[k] for k in core) and before['directory_only'] is True
                and before['disposition_class'] == 4 and before['delete_on_close_flag'] is False, 'Ordered BEFORE identity differs')
        children = [r['path'] for r in row['observed_children']]
        changed = any(actual[k] != row[k] for k in ('last_write_filetime', 'change_filetime'))
        require(before['prior_planned_children_removed'] == children and all(child in removed for child in children)
                and before['parent_time_change_allowed'] is changed and (not changed or bool(children)),
                'Parent timestamp allowance/postorder differs')
        require(mark['event'] == 'DISPOSITION_MARKED_ON_EXACT_DIRECTORY_HANDLE' and mark['path'] == row['path']
                and mark['file_id_128'] == row['file_id_128'], 'Exact marked-handle join differs')
        require(after['event'] == 'AFTER_REMOVED' and after['path'] == row['path']
                and after['file_id_128'] == row['file_id_128'] and after['creation_filetime'] == row['creation_filetime']
                and after['files_deleted'] == after['recursive_deletes'] == 0, 'Ordered AFTER identity differs')
        removed.add(row['path'])
    terminal = next(events)
    require(terminal['event'] == 'COMPLETE' and terminal['state'] == 'PASS_EXACT5542_EMPTY_DIRECTORY_HANDLES_REMOVED'
            and terminal['removed_directories'] == len(rows) and terminal['protected_after'] == protected
            and terminal['fragment_unchanged'] is True and terminal['workflow_lock'] == 'UNTOUCHED_NOT_OPENED'
            and all(terminal[k] == 0 for k in ('files_deleted', 'recursive_deletes', 'g_writes', 'wsl_starts', 'native_jobs_started')),
            'Historical COMPLETE accounting/protection differs')
    owner_identity(terminal['owners_after'])
    require(next(events, None) is None, 'Trailing/duplicate terminal journal records')
    return terminal


def check_post(post, rows, protected, terminal):
    require(post['state'] == 'PASS_EXACT5542_REMOVED_AND_PROTECTED_IDENTITIES_UNCHANGED'
            and post['complete_prune_verified'] is True and post['all5542_accounted'] is True
            and post['documented_removed_directories'] == 5542 and post['retained_planned_directories'] == 0
            and post['held_directories_preserved'] == 6 and post['unproven_absences'] == [] and post['pending_disposition'] is None
            and post['journal_sha256'] == ORIGINAL_PINS[JOURNAL] and post['journal_records'] == 16628
            and post['journal_terminal'] == terminal and post['verifier_sha256'] == ORIGINAL_PINS['verify_directory_handle_prune.py'],
            'Accepted historical postcheck accounting differs')
    require(len(post['directory_states']) == 5542
            and [r['path'] for r in post['directory_states']] == [r['path'] for r in rows]
            and all(r['state'] == 'DOCUMENTED_REMOVED_AND_CURRENTLY_ABSENT' and r['presence_evidence']['present'] is False
                    for r in post['directory_states']), 'Exact postcheck5542 absence join differs')
    observed = [{k:row[k] for k in ('path', 'bytes', 'sha256', 'unchanged')} for row in post['protected_files']]
    require(observed == protected and len(observed) == 12
            and post['six_dirty_g_files_unchanged'] == post['protected_files'][2:8], 'Protected12/six dirtyG pin join differs')
    owner_identity(post['owners_before'], True)
    owner_identity(post['owners_after'], True)
    lock = post['workflow_lock_identity_before']
    require(lock == post['workflow_lock_identity_after'] and lock['creation_filetime'] == '134359335921635133'
            and lock['file_id_128'] == '87792800000003000000000000000000' and lock['legacy_file_id'] == 844424932784519
            and lock['volume_serial'] == '17766949232488609743' and lock['native_link_count'] == 1
            and post['workflow_lock_metadata_only'] is True and post['lock_acquired'] is False
            and post['lock_contents_read'] is False, 'Historical original lock metadata differs')
    require(post['g_provider_single_link_exclusion'] == 'NOT_ESTABLISHED_PROVIDER_REPORTED_ZERO_FOR_EXACT_NINE_PINNED_FILES'
            and sum(r['identity']['native_link_count'] == 0 for r in post['protected_files']) == 9
            and post['excluded_fragment_sha256'] == '574547f9584dafce870492810ab02be990fe022939edd5a797292c473625027b'
            and post['preserved_first_fixture_failure'] is True, 'Provider/fragment/failure qualification differs')


def verify(args, out, result):
    B.COMMAND_OUT = out / 'command_io'
    B.COMMAND_OUT.mkdir(exist_ok=False)
    result.update(owned_commands=B.COMMANDS, resource_minimum_bytes=B.RESOURCE_MIN,
                  maximum_aggregate_seconds=1800, maximum_owned_command_cleanup_seconds=5,
                  hard_kernel_io_cancellation_claim=False, producer_imports=False,
                  current_old_c_g_rescan=False, current_owner_or_lock_query=False)
    extras = {PREFIX + name: row for name, row in EXTRAS.items()}
    raw = A.get_controls(args, CONTROLS, {**CODE, Path(__file__).name: B.file_sha(__file__)}, PREFIX, LOCAL, out, result, extras)
    read = lambda name: json.loads(raw[PREFIX + name])
    build, index, summary, completion = (read(n) for n in ('build_receipt.json', 'index.json', 'execution_summary.json', 'completion.json'))
    require(build['state'] == 'PASS_LOCAL_EXECUTION_RECOVERY_ARCHIVE_ALL_CRC_SHA_NO_NEW_DELETE'
            and build['original_count'] == 50 and build['member_count'] == 54
            and build['sha256'] == ASSET['sha256'] and build['bytes'] == ASSET['bytes']
            and build['builder_sha256'] == CODE['build_directory_prune_execution_archive.py']
            and build['minimum_physical_and_commit_headroom_bytes'] == 1536 * 1024**2,
            'Exact actual build/1536MiB resource policy differs')
    require(index['originals'] == build['originals'] and index['summary'] == build['summary'] == summary == completion['summary'],
            'Build/index/summary/completion cross-binding differs')
    expected = A.member_table(build['members'])
    release = selected = None
    if not args.local_inspect:
        release, selected = S.begin(A, args, [ASSET], [SIDECAR], out, result)
    path = (LOCAL if args.local_inspect else out) / ASSET['name']
    require((path.parent / SIDECAR['name']).read_bytes() == (ASSET['sha256'] + '  ' + ASSET['name'] + '\n').encode('ascii'),
            'Actual sidecar original bytes differ')
    observed = strict_zip(path, expected)
    originals = build['originals']
    require(set(originals) == {'evidence/' + name for name in ORIGINAL_PINS} and len(originals) == 50
            and set(observed) == set(originals) | {'INDEX.json', 'EXECUTION_SUMMARY.json', 'ATTRIBUTION_AND_LIMITS.md', 'SHA256SUMS.txt'},
            'Exact independently pinned50 originals/54 members differ')
    for member, row in originals.items():
        name = member.removeprefix('evidence/')
        require(row['sha256'] == ORIGINAL_PINS[name] == observed[member]['sha256']
                and row['bytes'] == observed[member]['bytes'] and row['member'] == member
                and row['source_relative_path'] == name and row['original_path'] == str(EXACT_WORK / name)
                and row['links'] == 1 and row['retained_access'] == 'READ_DENY_WRITE_DELETE'
                and re.fullmatch(r'\d+', row['file_id']) and re.fullmatch(r'\d+', row['birthtime_ns']),
                'Original source pin/identity/byte join differs')
    with zipfile.ZipFile(path) as archive:
        archived = lambda name: json.loads(archive.read('evidence/' + name))
        for inner, outer in (('INDEX.json', 'index.json'), ('EXECUTION_SUMMARY.json', 'execution_summary.json'), ('SHA256SUMS.txt', 'SHA256SUMS.txt')):
            require(archive.read(inner) == raw[PREFIX + outer], 'Archived/published generated control differs')
        for name, row in {**CODE, **{n:p for n,(_,p) in EXTRAS.items()}}.items():
            if name in ORIGINAL_PINS:
                require(observed['evidence/' + name]['sha256'] == row, 'Published original source differs from archive')
        rows = validate_plan(archived(PLAN))
        protected = [{k:r[k] for k in ('path', 'bytes', 'sha256', 'unchanged')} for r in archived(BASELINE)['protected_files']]
        with archive.open('evidence/' + JOURNAL) as stream:
            terminal = check_journal(journal_rows(stream), rows, protected)
        post = archived(POST)
        check_post(post, rows, protected, terminal)
        require(archived('directory_handle_fixture_20261009T211154Z_9cf77be3.json')['state'] == 'FAILED_FIXTURE_PRESERVED'
                and archived('directory_prune_postverify_20261009T212934Z_35de2767/receipt.json')['state']
                    == 'FAILED_INDEPENDENT_DIRECTORY_POST_VERIFY_NO_NEW_CLEANUP_AUTHORITY'
                and archived('master_recovery_receipts05/directory_execution_checkpoint.json')['state']
                    == 'EXECUTION_EXIT0_INDEPENDENT_POSTVERIFY_PENDING', 'Historical failure/pending state upgraded')
    if not args.local_inspect:
        A.end_release(args, release, selected, result)
    result.update(state='PASS_LOCAL54_MEMBERS_5542_JOURNAL_POSTCHECK_JOIN_REMOTE_NOT_RUN' if args.local_inspect else
                  'PASS_FRESH_REMOTE54_MEMBERS_5542_JOURNAL_POSTCHECK_JOIN', members=list(observed.values()),
                  original_count=50, zip_members=54, internal_sum_entries=53, journal_records=16628,
                  historical_removed_directories=5542, historical_held_directories=6, historical_protected_files=12,
                  historical_dirty_g_files=6, historical_postverify_sha256=ORIGINAL_PINS[POST],
                  provider_single_link_exclusion='NOT_ESTABLISHED_PROVIDER_REPORTED_ZERO',
                  live_scientific_closure_or_acceptance_created=False, new_deletion_authority=False,
                  first_fixture_and_postverify_failures_preserved=True, original_source_payloads_reread=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--local-inspect', action='store_true')
    modes.add_argument('--verify-remote', action='store_true')
    parser.add_argument('--tag', default='master-run-storage-20261009-v1')
    parser.add_argument('--expected-tag-commit', default='46c7089f906cce59afabaa4449b05df36ee124de')
    parser.add_argument('--source-commit')
    args = parser.parse_args()
    if not args.local_inspect and not args.verify_remote:
        print(json.dumps({'state': 'PREPARED_NO_READBACK_NO_NETWORK_NO_DELETE'}))
        return 0
    require(WORK == EXACT_WORK and os.name == 'nt', 'Exact C Windows readback source required')
    require(args.local_inspect or (args.source_commit and re.fullmatch('[a-f0-9]{40}', args.source_commit)), 'Immutable source commit required')
    require(re.fullmatch('[a-f0-9]{40}', args.expected_tag_commit) and re.fullmatch('[A-Za-z0-9_.-]+', args.tag), 'Invalid Release identity')
    B.DEADLINE = time.monotonic() + 1800
    B.RESOURCE = B.ResourceReader()
    B.guard()
    A.run, A.digest = B.monitored_run, B.file_sha
    A.execute_readback(args, 'directory_prune_execution01', verify)


if __name__ == '__main__':
    main()
