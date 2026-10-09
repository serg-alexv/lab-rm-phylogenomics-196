"""Resolve one exact manually read scientific MD; preserve prior scope evidence."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re

WORK = Path(r'C:\Users\wheel\Documents\Codex\2026-10-09\new-chat\work')
PRIOR = WORK / 'old_checkout_changed_history_scope01'
OUT = WORK / 'old_checkout_changed_history_scope02'
PINS = {'scope_review.json': 'f3689f2f7fe543eb47e282b3bf6b0abe14839811e52fccf2ab9e2395f83ef71d',
        'public_files.json': '3738dd30ea17273164e30dc26d49a9be05031870fe00d1c38d6b4fb2fe598be7',
        'excluded_files.json': 'ea5c3dd3b9b3c5ae7ad160c4f572e40da4af48f7dba171c0a2c2df80da3e1216',
        'ATTRIBUTION_AND_LIMITS.txt': 'a2d88884134a9e97ef21d9ae527bbd6cb62b85f725e6706662ecb16a34b1c213'}
RELATIVE = 'docs/approved196_summaries/approved196_future_work_pipeline.md'
DOC_SHA = 'ef8cb5541ac53d4fc55c40d439decad57ebf67a77eba9f536dda1ac1b58ea586'
INSPECTOR_SHA = 'fd93629536b432b9eead9f1d1607da2540e37f562367b01d267651dddab66814'
DECISIONS_SHA = '2f5fadd494c6fc61affa77182674e260d7b2a9bb14e11798dfd0389a994e8d19'


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


def load(name, path, pin):
    require(sha(path) == pin, 'Inspection helper drift')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(Path(module.__file__).resolve() == path and sha(path) == pin, 'Loaded helper identity drift')
    return module


def main():
    require(Path(__file__).resolve().parent == WORK and not OUT.exists(), 'New exact C resolution namespace required')
    for name, pin in PINS.items():
        require(sha(PRIOR / name) == pin, 'Original193/6 scope evidence differs')
    decisions = WORK / 'old_checkout_changed_history_inspection01/decisions.jsonl'
    require(sha(decisions) == DECISIONS_SHA, 'Original199 full-byte screen differs')
    originals = [json.loads(line) for line in decisions.read_text().splitlines()]
    selected = [row for row in originals if row['relative_path'] == RELATIVE]
    require(len(selected) == 1 and selected[0]['sha256'] == DOC_SHA and selected[0]['metadata']['bytes'] == 4497,
            'Exact one reviewed document required')
    inspector = load('changed_history_inspector_for_document', WORK / 'inspect_old_checkout_changed_history.py', INSPECTOR_SHA)
    helper = load('retained_privacy_for_document', inspector.INSPECTOR, inspector.INSPECTOR_SHA)
    patterns = dict(helper.PATTERNS)
    patterns['EXTERNAL_CLI_TOKEN_USAGE_OR_CONTROL_FIELD'] = re.compile(
        rb'(?i)"(?:input_tokens|cached_input_tokens|output_tokens|reasoning_tokens|total_tokens|usage|external_cli|external_session_id|codex_pid|prompt_sha256)"\s*:')
    patterns['AWS_ACCESS_KEY_SHAPE'] = re.compile(rb'(?:AKIA|ASIA)[A-Z0-9]{16}')
    patterns['URL_USERINFO_SHAPE'] = re.compile(rb'https?://[^\s/<>:]{1,100}:[^\s/<>@]{1,200}@')
    actual = inspector.inspect_one(selected[0], patterns, helper.PRIVATE_NAMES)
    require(actual['sha256'] == DOC_SHA and actual['decision'].startswith('PRIVACY_SCREENED'), 'One-document expanded privacy recheck failed')
    public = json.loads((PRIOR / 'public_files.json').read_text())['files']
    excluded = json.loads((PRIOR / 'excluded_files.json').read_text())['files']
    matched = [row for row in excluded if row['relative_path'] == RELATIVE]
    require(len(public) == 193 and len(excluded) == 6 and len(matched) == 1
            and matched[0]['original_sha256'] == DOC_SHA
            and matched[0]['reason'] == 'Manually inspected scientific document content differs', 'Exact conservative word-filter rejection required')
    public.append({**selected[0], 'decision': 'PUBLIC_SCIENTIFIC_HISTORY_ORIGINAL_BYTES_FOR_PRESERVATION_ONLY',
                   'scientific_kind': 'MANUALLY_INSPECTED_EXACT_HASH_HISTORICAL_SCIENTIFIC_PIPELINE_DOCUMENT',
                   'expanded_privacy_scan': 'FULL_BYTES_NO_MATCH', 'historical_scientific_state': 'PRESERVED_VERBATIM_NO_NEW_ACCEPTANCE',
                   'historical_native_closure': 'NOT_INFERRED', 'archive_member': 'originals/' + RELATIVE})
    public.sort(key=lambda row: row['relative_path'])
    excluded = [row for row in excluded if row['relative_path'] != RELATIVE]
    require(len(public) == len({row['relative_path'] for row in public}) == 194 and len(excluded) == 5
            and sum(row['metadata']['bytes'] for row in public) == 18622099
            and sum(row['original_bytes'] for row in excluded) == 4795, 'Exact194/5 accounting differs')
    source_sha = sha(Path(__file__))
    OUT.mkdir()
    save('public_files.json', {'schema': 'MASTER_OLD_CHECKOUT_CHANGED_PUBLIC_HISTORY_ORIGINALS_V1', 'files': public})
    save('excluded_files.json', {'schema': 'MASTER_OLD_CHECKOUT_CHANGED_HISTORY_WHOLE_EXCLUSIONS_V1', 'files': excluded})
    (OUT / 'ATTRIBUTION_AND_LIMITS.txt').write_bytes((PRIOR / 'ATTRIBUTION_AND_LIMITS.txt').read_bytes())
    review = json.loads((PRIOR / 'scope_review.json').read_text())
    review.update({'public_files': 194, 'public_bytes': 18622099, 'whole_excluded_files': 5, 'whole_excluded_bytes': 4795,
                   'prior_scope_pins': PINS, 'document_resolution_source_sha256': source_sha,
                   'manual_document_resolution': {'relative_path': RELATIVE, 'sha256': DOC_SHA, 'bytes': 4497,
                       'basis': 'Full original document read: approved cohort, dated pipeline state, six scientific future-work steps and provenance; no private session content. Original filter required a literal word absent from this scientific document.',
                       'expanded_privacy_full_byte_recheck': 'PASS', 'scientific_acceptance_created': False},
                   'files': {name: sha(OUT / name) for name in ('public_files.json', 'excluded_files.json', 'ATTRIBUTION_AND_LIMITS.txt')}})
    save('scope_review.json', review)
    for name, pin in PINS.items():
        require(sha(PRIOR / name) == pin, 'Original scope evidence drifted')
    require(sha(decisions) == DECISIONS_SHA and sha(Path(__file__)) == source_sha, 'Resolution control/source drift')
    print(json.dumps({'public_files': 194, 'public_bytes': 18622099, 'whole_excluded_files': 5, 'whole_excluded_bytes': 4795,
                      'output': str(OUT)}))


if __name__ == '__main__':
    main()
