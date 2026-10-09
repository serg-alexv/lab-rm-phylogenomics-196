"""Recheck fixed historical scientific bytes and exclude whole private controls."""
from pathlib import Path
import ast
import csv
import hashlib
import importlib.util
import io
import json
import re

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
INITIAL = WORK / 'old_checkout_changed_history_inspection01'
OUT = WORK / 'old_checkout_changed_history_scope01'
PINS = {
    'inspection.json': 'f786c7b849bb98333aba18b4312706a2fbc2dd7447bbd0541ae4d0211c7181df',
    'selection.json': 'c73343901656721e52291e0b0f82b14efafbf7bd5358dd05b9e3dace288a79db',
    'decisions.jsonl': '2f5fadd494c6fc61affa77182674e260d7b2a9bb14e11798dfd0389a994e8d19',
}
INSPECTOR_SHA = 'fd93629536b432b9eead9f1d1607da2540e37f562367b01d267651dddab66814'
PRIVATE_WHOLE = {
    'status/attempt01_execution_receipt.json': 'CODEX_SESSION_CONTROL_RECEIPT_PRIVATE_SCOPE_PRESERVE_LOCAL',
    'status/continuation_execution_receipt.json': 'CODEX_SESSION_CONTROL_RECEIPT_PRIVATE_SCOPE_PRESERVE_LOCAL',
    'status/execution_receipt.json': 'CODEX_SESSION_CONTROL_RECEIPT_PRIVATE_SCOPE_PRESERVE_LOCAL',
    'status/parent_execution_update.json': 'CODEX_SESSION_CONTROL_RECEIPT_PRIVATE_SCOPE_PRESERVE_LOCAL',
    'docs/approved196_summaries/approved196_summary_readback.json': 'MIXED_SCIENTIFIC_READBACK_WITH_EXTERNAL_CLI_TOKEN_USAGE_PRESERVE_WHOLE_LOCAL',
}
PROGRESS_KEYS = {'approved', 'assemblies', 'elapsed_seconds', 'failed', 'input_sha256',
                 'remaining', 'retrieved', 'scientific_validation', 'utc', 'workflow_pid'}
PROVENANCE_KEYS = {'accessions', 'evidence_limit', 'evidence_roots', 'generated_at_utc', 'method',
                   'raw_path_base', 'raw_responses', 'references', 'schema'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def load_module(name, path, expected):
    require(sha(path) == expected, 'Pinned inspection helper differs')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(Path(module.__file__).resolve() == path and sha(path) == expected, 'Loaded helper binding differs')
    return module


def scientific_kind(relative, path):
    # This reopens only full-byte-screened original files; no retained code runs.
    text = path.read_text(encoding='utf-8-sig')
    if relative.startswith('reports/stage02/'):
        value = json.loads(text)
        require(set(value) == PROGRESS_KEYS and isinstance(value['assemblies'], list)
                and all(isinstance(item, dict) and re.fullmatch(r'GCF_\d+\.\d+', str(item.get('accession', '')))
                        for item in value['assemblies']), 'Historical retrieval progress scientific schema differs')
        return 'HISTORICAL_RETRIEVAL_PROGRESS_OR_ATOMIC_WRITE_PROBE_ORIGINAL_STATE'
    if relative == 'reports/stage00/commands.jsonl':
        rows = [json.loads(line) for line in text.splitlines()]
        require(len(rows) == 44 and all(set(row) == {'argv', 'elapsed_seconds', 'exit_code', 'stderr', 'stdout', 'utc'}
                                      and isinstance(row['argv'], list) for row in rows), 'Historical44 command log schema differs')
        return 'HISTORICAL44_SCIENTIFIC_COMMANDS_AND_OUTPUTS_NO_CLOSURE_INFERENCE'
    if relative == 'reports/stage04/resumed_inference_resource_failure_v4.json':
        value = json.loads(text)
        require(set(value) == {'linux', 'native_address_space_limit_bytes', 'outer_address_space_limit_bytes',
                               'required_linux_available_bytes', 'required_windows_available_bytes',
                               'scientific_validation', 'utc', 'windows_after_wsl', 'windows_before_wsl'}, 'Historical resource failure schema differs')
        return 'HISTORICAL_NATIVE_RESOURCE_FAILURE_ORIGINAL_STATE_NO_NEW_MEASUREMENT'
    if relative.startswith('scripts/') and relative.endswith('.py'):
        ast.parse(text)
        return 'PROJECT_SCIENTIFIC_STAGE4_CHECKER_PUBLISHER_OR_SYNTHETIC_TEST_SOURCE_NO_EXECUTION'
    if relative.startswith('scripts/') and relative.endswith('_synthetic_results.json'):
        value = json.loads(text)
        require({'biological_jobs_run', 'count', 'fixtures', 'status'} <= set(value)
                and isinstance(value['fixtures'], list), 'Historical synthetic result schema differs')
        return 'HISTORICAL_SYNTHETIC_RESULTS_ORIGINAL_STATE_NO_RERUN'
    if relative == 'docs/approved196_summaries/approved196_current_pipeline_readback.json':
        value = json.loads(text)
        require(set(value) == {'approved_genomes', 'boundary', 'enterococcus', 'files',
                               'marker_acceptance_summary_sha256', 'pipeline_words', 'ranked_genera', 'status', 'utc'}, 'Scientific pipeline readback schema differs')
        return 'HISTORICAL_APPROVED196_SCIENTIFIC_PIPELINE_READBACK'
    if relative == 'docs/approved196_summaries/approved196_LAB_genera.tsv':
        rows = list(csv.DictReader(io.StringIO(text), delimiter='\t'))
        require(len(rows) == 10 and all(set(row) == {'genus', 'genus_tax_id', 'genome_count', 'source_accessions',
                                                   'approved_accessions_sha256', 'taxonomy_status', 'provenance_json'} for row in rows), 'Ten-genera taxonomy table schema differs')
        require(all(set(json.loads(row['provenance_json'])) == PROVENANCE_KEYS for row in rows), 'Taxonomy provenance JSON schema differs')
        return 'HISTORICAL_TEN_GENERA_TAXONOMY_AND_RAW_RESPONSE_PROVENANCE_TABLE'
    if relative in {'docs/approved196_summaries/approved196_future_work_pipeline.md',
                    'docs/approved196_summaries/approved196_future_work_pipeline_current.md',
                    'reports/stage05/independent_model_review.md'}:
        require('196' in text and ('pipeline' in text.lower() or 'R-M detector' in text), 'Manually inspected scientific document content differs')
        return 'MANUALLY_INSPECTED_HISTORICAL_SCIENTIFIC_PIPELINE_OR_MODEL_REVIEW_ORIGINAL_BYTES'
    raise ValueError('No established scientific public scope for this file')


def main():
    require(Path(__file__).resolve().parent == WORK and not OUT.exists(), 'Exact new C scope namespace required')
    for name, expected in PINS.items():
        require(sha(INITIAL / name) == expected, 'Original199 privacy screen changed')
    inspection = load_module('changed_history_inspector', WORK / 'inspect_old_checkout_changed_history.py', INSPECTOR_SHA)
    helper = load_module('retained_privacy_patterns', inspection.INSPECTOR, inspection.INSPECTOR_SHA)
    rows = [json.loads(line) for line in (INITIAL / 'decisions.jsonl').read_text(encoding='utf-8').splitlines()]
    require(len(rows) == 199 and sum(row['metadata']['bytes'] for row in rows) == 18626894
            and all(row.get('sha256') and row.get('identity_rechecked') for row in rows), 'Exact199 inspected original bytes required')
    require(set(PRIVATE_WHOLE) <= {row['relative_path'] for row in rows}, 'Exact whole-file private exclusions missing')
    patterns = dict(helper.PATTERNS)
    patterns['EXTERNAL_CLI_TOKEN_USAGE_OR_CONTROL_FIELD'] = re.compile(
        rb'(?i)"(?:input_tokens|cached_input_tokens|output_tokens|reasoning_tokens|total_tokens|usage|external_cli|external_session_id|codex_pid|prompt_sha256)"\s*:')
    patterns['AWS_ACCESS_KEY_SHAPE'] = re.compile(rb'(?:AKIA|ASIA)[A-Z0-9]{16}')
    patterns['URL_USERINFO_SHAPE'] = re.compile(rb'https?://[^\s/<>:]{1,100}:[^\s/<>@]{1,200}@')
    public, excluded = [], []
    source_sha = sha(Path(__file__))
    OUT.mkdir()
    for prior in rows:
        relative = prior['relative_path']
        if relative in PRIVATE_WHOLE:
            excluded.append({'relative_path': relative, 'original_path': prior['absolute_path'],
                             'original_bytes': prior['metadata']['bytes'], 'original_sha256': prior['sha256'],
                             'reason': PRIVATE_WHOLE[relative], 'payload_archived': False, 'redaction': 'NONE_WHOLE_FILE_EXCLUDED',
                             'local_preservation': 'REQUIRED_NO_DELETE_AUTHORITY'})
            continue
        try:
            actual = inspection.inspect_one(prior, patterns, helper.PRIVATE_NAMES)
            require(actual.get('sha256') == prior['sha256'] and actual['decision'].startswith('PRIVACY_SCREENED'), 'Original SHA drift or expanded privacy signature flagged')
            kind = scientific_kind(relative, inspection.literal(relative))
            require(sha(inspection.literal(relative)) == prior['sha256'], 'Scientific scope read changed original bytes')
            public.append({**prior, 'decision': 'PUBLIC_SCIENTIFIC_HISTORY_ORIGINAL_BYTES_FOR_PRESERVATION_ONLY',
                           'scientific_kind': kind, 'expanded_privacy_scan': 'FULL_BYTES_NO_MATCH',
                           'historical_scientific_state': 'PRESERVED_VERBATIM_NO_NEW_ACCEPTANCE',
                           'historical_native_closure': 'NOT_INFERRED', 'archive_member': 'originals/' + relative})
        except (ValueError, OSError, SyntaxError) as error:
            excluded.append({'relative_path': relative, 'original_path': prior['absolute_path'],
                             'original_bytes': prior['metadata']['bytes'], 'original_sha256': prior['sha256'],
                             'reason': str(error), 'payload_archived': False, 'redaction': 'NONE_WHOLE_FILE_EXCLUDED',
                             'local_preservation': 'REQUIRED_NO_DELETE_AUTHORITY'})
    for name, expected in PINS.items():
        require(sha(INITIAL / name) == expected, 'Original screen control drift')
    require(sha(Path(__file__)) == source_sha and sha(WORK / 'inspect_old_checkout_changed_history.py') == INSPECTOR_SHA
            and sha(inspection.INSPECTOR) == inspection.INSPECTOR_SHA, 'Public scope source/helper drift')
    save('public_files.json', {'schema': 'MASTER_OLD_CHECKOUT_CHANGED_PUBLIC_HISTORY_ORIGINALS_V1', 'files': public})
    save('excluded_files.json', {'schema': 'MASTER_OLD_CHECKOUT_CHANGED_HISTORY_WHOLE_EXCLUSIONS_V1', 'files': excluded})
    notice = ('Historical LAB R-M project source and scientific records only. Original bytes and all embedded notices remain unchanged.\n'
              'Four selected scripts are project-specific Stage4 checker/publisher/test source; external packages are imported, not bundled. No vendor implementation or installed package source is selected.\n'
              'No LICENSE, LICENSE.md, LICENSE.txt, NOTICE, COPYING or CITATION.cff was present at the exact old checkout root during the bounded attribution check. No license is invented or substituted.\n'
              'The model-review document retains its original model authors/source links and primary-literature citations; these historical conclusions are not re-certified.\n'
              'Whole Codex control receipts and the mixed scientific readback containing CLI token usage are excluded and preserved locally without redaction. No prompt, raw Codex event, usage payload, credential, hidden reasoning or private-control bytes are included.\n'
              'Historical pipeline variants, partial/failure/resource records and synthetic outcomes remain unchanged. UNKNOWN native closure is not promoted; preservation is not scientific acceptance, tool readiness, remote recovery or deletion authority.\n')
    (OUT / 'ATTRIBUTION_AND_LIMITS.txt').write_text(notice, encoding='utf-8', newline='\n')
    save('scope_review.json', {'schema': 'MASTER_OLD_CHECKOUT_CHANGED_HISTORY_PUBLIC_SCOPE_V1',
         'state': 'PUBLIC_SCIENTIFIC_BYTES_SCOPED_READY_FOR_LOCAL_ARCHIVE_ONLY',
         'source_sha256': source_sha, 'inspector_sha256': INSPECTOR_SHA, 'initial_screen_pins': PINS,
         'initial_candidate_files': 199, 'initial_candidate_bytes': 18626894,
         'public_files': len(public), 'public_bytes': sum(row['metadata']['bytes'] for row in public),
         'whole_excluded_files': len(excluded), 'whole_excluded_bytes': sum(row['original_bytes'] for row in excluded),
         'expanded_privacy_recheck': 'FULL_BYTES_EVERY_PUBLIC_CANDIDATE', 'manual_scientific_documents_reviewed': 3,
         'private_initial_pattern_gap': 'Original screen lacked explicit input/output/cached token-count keys; schema review found mixed readback, whole file excluded, expanded patterns rerun.',
         'files': {name: sha(OUT / name) for name in ('public_files.json', 'excluded_files.json', 'ATTRIBUTION_AND_LIMITS.txt')},
         'scientific_acceptance_created': False, 'historical_unknown_closure_promoted': False,
         'source_deletions': 0, 'g_writes': 0, 'wsl_starts': 0, 'network_calls': 0, 'native_jobs': 0,
         'archive': 'NOT_RUN', 'remote_publication': 'NOT_RUN'})
    print(json.dumps({'public_files': len(public), 'public_bytes': sum(row['metadata']['bytes'] for row in public),
                      'excluded_files': len(excluded), 'output': str(OUT)}))


if __name__ == '__main__':
    main()
