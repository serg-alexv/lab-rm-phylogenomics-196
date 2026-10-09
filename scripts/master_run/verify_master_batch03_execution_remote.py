"""Fresh remote readback of completed cleanup history; never grants deletion authority."""
from pathlib import Path
import hashlib, importlib.util, json, sys

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parent
HELPER_SHA = '6825690d52292b8bbb2f9d5aa0cfcb1fbd8d8863601d890559a05adf3c3d7691'
helper = WORK / 'verify_master_public_components01_remote.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest() == HELPER_SHA
spec = importlib.util.spec_from_file_location('cleanup_readback_primitives', helper)
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
PREFIX = 'reports/master_run/20261009/cleanup/batch03_execution01/'
CONTROLS = {
    'manifest.json': '50819c81868069f0176dbc6134ff029620beb32de1b03ef9b667929ea1bb45a4',
    'source_bindings.json': 'd76781caae16bcca791484768eb14c816301e5edda3c109fcedc5466eb34f477',
    'build_receipt.json': '27045ae12fd0761f9c0f44d463390931dc15d163cd5638bb194331263f48d3eb',
}
CODE = {'build_master_batch03_execution_archive.py':
        '7c066912b10611eb78fa15ec0cd3c3944f85f98f98c553b62b31685a3d3af864',
        helper.name: HELPER_SHA}
ASSETS = [{'name': 'master_batch03_cleanup_execution01.zip', 'bytes': 11319474,
           'sha256': '80b1bea0ee2dd1f7944ffa2f09abc488a5266247a61fc96dc5e092f1e82e95bb'}]
POST_SHA = '84cb29ebcc04b444ea90ca0e10d5f7e6832d09f14f8f8285f1241b4cf3e71868'
JOURNAL_SHA = '3331af8009aa7a9dbbb9d49d8cb044cd59dc60a78452c233b109e531497a717e'

def journal_check(stream):
    begin = json.loads(next(stream))
    A.require(begin['event'] == 'BEGIN' and begin['proposal_commit'] ==
              '2b0edf16fe3224d33155ac67f2a8a0d2177d78a5', 'Journal authority differs')
    files = size = records = 0
    seen = set()
    pending = None
    terminal = None
    for line in stream:
        event = json.loads(line)
        records += 1
        A.require(terminal is None, 'Rows after terminal completion')
        kind = event['event']
        if kind == 'VERIFIED_INTENT':
            A.require(pending is None and event['path'] not in seen, 'Duplicate or unpaired intent')
            pending = event
        elif kind == 'REMOVED':
            A.require(pending is not None and all(event[k] == pending[k]
                      for k in ('line', 'path', 'bytes', 'sha256')), 'Intent/outcome binding differs')
            files += 1
            size += event['bytes']
            A.require(event['deleted'] == files and event['deleted_bytes'] == size, 'Cumulative accounting differs')
            seen.add(event['path'])
            pending = None
        elif kind == 'COMPLETE':
            A.require(pending is None and event['state'] == 'PASS_EXACT_47429_COLD_LEAVES_REMOVED'
                      and event['deleted'] == files == 47429 and event['deleted_bytes'] == size == 6565902818
                      and event['held_files'] == 219 and event['unmatched_preserved'] == 619
                      and event['recursive_deletes'] == 0, 'Terminal accounting differs')
            terminal = event
        else:
            raise ValueError('Unexpected public journal event')
    A.require(terminal is not None and records == 2 * files + 1, 'Incomplete public journal')
    return {'removed_files': files, 'logical_removed_bytes': size, 'records_including_begin': records + 1,
            'terminal_utc': terminal['utc'], 'physical_disk_reclaimed_bytes': 'NOT_MEASURED'}

def verify(args, out, result):
    raw = A.get_controls(args, CONTROLS, CODE, PREFIX,
                         WORK / 'master_batch03_cleanup_execution01_metadata', out, result)
    manifest, binding, build = [json.loads(raw[PREFIX + n]) for n in
                               ('manifest.json', 'source_bindings.json', 'build_receipt.json')]
    A.require(manifest['sha256'] == build['sha256'] == ASSETS[0]['sha256']
              and manifest['bytes'] == build['bytes'] == ASSETS[0]['bytes']
              and build['members'] == len(manifest['members']) == 23
              and build['manifest_sha256'] == CONTROLS['manifest.json']
              and manifest['source_binding_sha256'] == CONTROLS['source_bindings.json'], 'Outer controls differ')
    for value in (binding, build):
        A.require(value['postverify_sha256'] == POST_SHA
                  and value['physical_disk_reclaimed_bytes'] == 'NOT_MEASURED'
                  and value['logical_removed_bytes'] == 6565902818
                  and value['raw_codex_events_prompts_usage_archived'] is False
                  and value['scientific_acceptance'] == 'NONE_EXECUTION_HISTORY_ONLY', 'Evidence scope differs')
    if args.local_inspect:
        archive = WORK / ASSETS[0]['name']
    else:
        release, selected = A.begin_release(args, ASSETS, out, result)
        archive = out / ASSETS[0]['name']
    A.require(archive.stat().st_size == ASSETS[0]['bytes'] and A.digest(archive) == ASSETS[0]['sha256'], 'Actual ZIP differs')
    table = A.member_table(manifest['members'])
    z, observed = A.verify_zip(archive, ASSETS[0], table)
    with z:
        A.require(z.read('control/source_bindings.json') == raw[PREFIX + 'source_bindings.json'], 'Embedded binding differs')
        A.require(set(observed) == set(binding['inputs']) | {'SHA256SUMS.txt', 'control/source_bindings.json'}, 'Input coverage differs')
        A.bind_inputs({name: {k: row[k] for k in ('bytes', 'sha256')}
                       for name, row in binding['inputs'].items()}, observed)
        A.require(observed['execution/independent_postverify.json']['sha256'] == POST_SHA
                  and observed['execution/full_public_cleanup_journal.jsonl']['sha256'] == JOURNAL_SHA,
                  'Exact completed execution proof differs')
        post = json.loads(z.read('execution/independent_postverify.json'))
        A.require(post['state'] == 'PASS_EXACT47429_REMOVED_838_ORIGINALS_AND12_PROTECTED_UNCHANGED'
                  and post['removed_files'] == 47429 and post['removed_bytes'] == 6565902818
                  and len(post['retained_originals']) == 838 and len(post['protected_files']) == 12
                  and post['journal_sha256'] == JOURNAL_SHA, 'Postverify contract differs')
        with z.open('execution/full_public_cleanup_journal.jsonl') as stream:
            result['journal'] = journal_check(stream)
        result.update(zip_members=23, internal_sum_entries=22,
                      members=list(observed.values()), postverify_sha256=POST_SHA,
                      retained_originals_verified_at_original_postcheck=838,
                      protected_files_verified_at_original_postcheck=12,
                      current_original_filesystem_checks_rerun=False,
                      residual_leaf_race=binding['residual_leaf_race'])
    if not args.local_inspect:
        A.end_release(args, release, selected, result)
    result['state'] = 'PASS_LOCAL_EXECUTION23_MEMBERS_REMOTE_NOT_RUN' if args.local_inspect else \
        'PASS_FRESH_REMOTE_EXECUTION23_MEMBERS_47429_ORDERED_REMOVAL_PAIRS'

if __name__ == '__main__':
    A.execute_readback(A.cli(__doc__), 'batch03_execution01', verify)
