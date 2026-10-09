"""C-only preparation receipt; never invokes production pruning or a fixture."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
from types import SimpleNamespace

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PINS = {
    'prune_old_scientific_directories.py': '9b64d17bb2612ce35051b87d77863709d875c1f910865fd6a4db2f6ddd265381',
    'test_directory_handle_prune_fixture.py': 'c0c62e1aa3bf7b6d7b011b6afbddf07c8827e6af54729961b955eda703a0031a',
    'prune_old_scientific_directories_attempt01.py': '2f608bd1f11b3aac9223c7c751b9a9d8f5cb5c02568861bd6cfeadfff9304604',
    'test_directory_handle_prune_fixture_attempt01.py': '72e3a86e28f08e845cb37a9ef62f6ea056d220902e7074b4fdc63dbcb8e4d0c7',
    'directory_handle_fixture_20261009T211154Z_9cf77be3.json': '348ee7030d49d14524290f0ec27302e67d67d216f342c97a1fb44e83526cc0ac',
    'directory_handle_fixture_20261009T211154Z_9cf77be3.jsonl': '73a0978d42e5f106d60888187611eb0218314b9aeb016d5b47e4f3cfb48b0a23',
    'directory_handle_fixture_20261009T211310Z_843dbf82.json': 'eebac12d62403b273713ee0f4aaad17955a4c6b7d33631e63ee1f86dc4e47ba1',
    'directory_handle_fixture_20261009T211310Z_843dbf82.jsonl': '0109e6d8ae71bef6e465931a52510e8cd627e3ebda92a148caca42f8ab4cac4c',
    'directory_handle_pruner_independent_source_review.json': '2c6d1d5126e8cd2ee89bc3f26ab652eeb7ce283e6940ae474e93d58418310d52',
    'directory_handle_pruner_corrected_independent_review.json': 'c0bc38628a140885211a397af9e23bbe10f9f432b2c682c13d44c03cd1d1b20b',
    'prepare_old_scientific_emptydirs.py': '7287809f47f912eddb21ba9f05d927872ef710d45ac6857837ae6689c320b21f',
    'old_scientific_emptydirs01_readback_20261009T205057Z_9c38bcce/receipt.json': 'e71b02889d5443017ef5ab8be206b1fc4e5f9f81c3de14c602eeaeef70c68063',
    'master_history02_postverify_20261009T201921Z_f90337c5/receipt.json': 'a20c9c87d42816355434eb3abbd9ffd082c8c1b73557d773901bb3eb1329a082',
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('.', '_'), WORK / name)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    assert Path(__file__).resolve().parent == WORK
    for name, expected in PINS.items():
        assert sha(WORK / name) == expected, name
    final = json.loads((WORK / 'directory_handle_fixture_20261009T211310Z_843dbf82.json').read_text())
    assert final['state'] == 'PASS_NINE_ACTUAL_WINDOWS_DIRECTORY_HANDLE_FIXTURES'
    assert len(final['results']) == 9 and final['old_c_directories_removed'] == final['files_deleted'] == 0
    P = load('prune_old_scientific_directories.py')
    plan, protection = P.controls()  # C control bytes only; no protected payload hash/open.
    assert (len(plan['directories']), len(plan['held']), len(protection['protected_files'])) == (5542, 6, 12)
    guards = [{'name': 'pinned_plan_fresh_remote_and_protection_controls', 'status': 'PASS'}]
    for name in ('prune_old_scientific_directories.py', 'test_directory_handle_prune_fixture.py'):
        candidate = P if name.startswith('prune_') else load(name)
        prior = sys.argv
        try:
            sys.argv = [name]
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert candidate.main() == 0
            assert json.loads(output.getvalue())['state'].startswith('PREPARED_NO_')
        finally:
            sys.argv = prior
        guards.append({'name': name + '_default_no_operation', 'status': 'PASS'})
    template = WORK / 'directory_handle_pruner_authority_TEMPLATE_FALSE.json'
    journal = WORK / 'DIRECTORY_FALSE_AUTHORITY_TEST_MUST_NOT_CREATE.jsonl'
    assert not journal.exists()
    try:
        P.execute(SimpleNamespace(source_sha256=PINS['prune_old_scientific_directories.py'],
                                  authorization=str(template), authorization_sha256=sha(template), journal=str(journal)))
    except ValueError as error:
        assert str(error) == 'Separate exact root review/publication authority absent'
        assert not journal.exists()
    else:
        raise AssertionError('FALSE authority accepted')
    guards.append({'name': 'false_root_authority_rejected_before_journal_timer_native_handles', 'status': 'PASS'})
    example = {key: 'x' for key in P.IDENTITY}
    assert P.same_identity(example, example)
    for key in P.IDENTITY:
        changed = {**example, key: 'changed'}
        assert not P.same_identity(changed, example)
    guards.append({'name': 'each_full_identity_birth_type_field_is_required', 'status': 'PASS'})
    guards.append({'name': 'actual_nine_case_receipt_source_and_journal_pins', 'status': 'PASS'})
    assert len(guards) == 6
    output = WORK / 'directory_handle_pruner_preparation_completion_02.json'
    assert not output.exists()
    names = list(PINS) + ['directory_handle_pruner_METHODS.md',
                         'directory_handle_pruner_authority_TEMPLATE_FALSE.json', Path(__file__).name,
                         'directory_handle_pruner_preparation_completion.json',
                         'finalize_directory_handle_pruner_prep_mapping_attempt01.py']
    assert len({name.replace('/', '__') for name in names}) == len(names)
    receipt = {'schema': 'MASTER_DIRECTORY_HANDLE_PRUNER_PREPARATION_V1',
               'state': 'PASS_PREPARATION_SIX_GUARDS_NINE_ACTUAL_FIXTURES_PRODUCTION_NOT_RUN',
               'production_execution_authorized': False, 'production_execution': 'NOT_RUN',
               'proposed_directories': 5542, 'original_empty_directories': 3736,
               'planned_child_only_parents': 1806, 'held_directories': 6,
               'guards': guards, 'actual_fixture_cases': final['results'],
               'old_c_directories_removed': 0, 'files_deleted': 0,
               'removed_synthetic_empty_directories': 3,
               'actual_fixture_owner_or_protected_payload_checks': 'NOT_RUN_NOT_NEEDED_FOR_NEW_C_FIXTURE',
               'workflow_lock': 'UNTOUCHED_NOT_OPENED', 'g_writes': 0, 'wsl_starts': 0,
               'failed_attempt_preserved': True,
               'failed_attempt_cause': 'READ_ATTRIBUTES-only ancestor handle allowed actual rename; corrected LIST_DIRECTORY access produced actual ERROR_SHARING_VIOLATION 32.',
               'metadata_mapping_correction': 'First compact completion retained; two nested receipt.json names now have unique public names. Pruner, fixtures, guards and original evidence unchanged.',
               'frozen_plan_sha256': P.PLAN_SHA, 'fresh_remote_proof_sha256': P.REMOTE_SHA,
               'later_execution_requires': ['root-only separately pinned exact authority', 'final source/fixture review and remote publication/readback',
                                            'unchanged exact native/controller birth+liveness and12protected source hashes',
                                            'actual same-directory ID/birth/plain type and emptiness at each disposition',
                                            'separate independent post-verification after any real run'],
               'public_control_mapping': [{'local_path': str(WORK / name),
                                           'relative_control_name': name,
                                           'suggested_public_name': name.replace('/', '__'),
                                           'bytes': (WORK / name).stat().st_size,
                                           'sha256': sha(WORK / name)} for name in names]}
    output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'receipt': str(output), 'sha256': sha(output), 'small_public_controls': len(names), 'state': receipt['state']}))


if __name__ == '__main__':
    main()
