"""Content labels for immutable logical shards; never changes capture format.

Pure plans/bindings plus one caller-guarded streaming verifier. An existing owned
uploader sends canonical files under remote_name. An existing owned downloader
saves the asset ID's bytes under local_name. Original LF sidecar bytes stay
unchanged. This module performs no network, subprocess, rename, copy or removal.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

LIMIT = 448 * 1024**2
BLOCK = 256 * 1024
CAPTURE_SHA = '21b33abc389efe9bbfdcf8048737f2d7f10ce60b52d6e1c6f3678b24568b8220'
PREFIX = '/mnt/c/Users/wheel/Documents/Codex/2026-10-08/lab-rm-phylogenomics-196/.tools/linux'
ROOTS = {'environment_dir': PREFIX+'/detector_env', 'models_dir': PREFIX+'/defense_models', 'padloc_db': PREFIX+'/padloc_db'}
LABEL = 'stage05-runtime-detector-env-defense-models-padloc-db'


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


def strict_json(raw):
    require(isinstance(raw, bytes) and len(raw) < 5*1024**2, 'Bounded exact JSON bytes required')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def index_contract(raw, expected_sha):
    require(sha(expected_sha) and digest(raw) == expected_sha, 'Externally pinned logical index required')
    value = strict_json(raw)
    require(value.get('schema') == 'STAGE05_RUNTIME_LOGICAL_ARCHIVE_INDEX_V1'
            and value.get('source_sha256') == CAPTURE_SHA and value.get('roots') == ROOTS
            and value.get('maximum_asset_bytes') == LIMIT
            and value.get('installed_build_equivalence') == 'NOT_ESTABLISHED'
            and value.get('cleanup_authority') is False, 'Exact existing archive contract required')
    rows = value.get('shards')
    require(isinstance(rows, list) and 1 <= len(rows) <= 64, 'Bounded ordered shard count required')
    for number, row in enumerate(rows, 1):
        require(set(row) == {'name', 'bytes', 'sha256'}
                and row['name'] == 'stage5-installed-runtime-01.part'+str(number).zfill(4)
                and type(row['bytes']) is int and 0 < row['bytes'] <= LIMIT and sha(row['sha256'])
                and (number == len(rows) or row['bytes'] == LIMIT), 'Invalid canonical shard order or size')
    require(value.get('compressed_bytes') == sum(row['bytes'] for row in rows)
            and sha(value.get('compressed_stream_sha256')), 'Exact ordered stream totals required')
    return value


def make_plan(index_raw, expected_index_sha, snapshot):
    """Plan alias upload/download names. No actual payload/recovery claim."""
    index = index_contract(index_raw, expected_index_sha)
    require(re.fullmatch(r'[0-9]{8}-v[1-9][0-9]{0,2}', snapshot or ''), 'Bounded date-version snapshot required')
    assets = []
    for number, row in enumerate(index['shards'], 1):
        remote_name = LABEL+'-'+snapshot+'.part'+str(number).zfill(4)
        assets.append({'local_name': row['name'], 'remote_name': remote_name,
                       'bytes': row['bytes'], 'sha256': row['sha256'], 'kind': 'PAYLOAD'})
        sidecar = (row['sha256']+'  '+row['name']+'\n').encode('ascii')
        assets.append({'local_name': row['name']+'.sha256', 'remote_name': remote_name+'.sha256',
                       'bytes': len(sidecar), 'sha256': digest(sidecar), 'kind': 'ORIGINAL_LF_SIDECAR'})
    return {'schema': 'STAGE05_RUNTIME_TRANSPORT_ALIAS_PLAN_V1', 'snapshot': snapshot,
            'index_sha256': expected_index_sha, 'compressed_stream_sha256': index['compressed_stream_sha256'],
            'canonical_reader_names_unchanged': True, 'original_sidecar_bytes_unchanged': True,
            'content_scope': ['detector_env', 'defense_models', 'padloc_db'],
            'compressed_parts_independently_extractable': False, 'assets': assets,
            'actual_upload': 'NOT_RUN', 'actual_download': 'NOT_RUN', 'cleanup_authority': False}


def validate_plan(alias_raw, expected_alias_sha, index_raw, expected_index_sha):
    require(sha(expected_alias_sha) and digest(alias_raw) == expected_alias_sha, 'External exact alias-map pin required')
    value = strict_json(alias_raw)
    require(value == make_plan(index_raw, expected_index_sha, value.get('snapshot')), 'Alias map differs from exact canonical index')
    return value


def bind_assets(alias_raw, expected_alias_sha, index_raw, expected_index_sha, before, after):
    """Bind actual selected Release asset witnesses to canonical download names.

    Caller normalizes metadata to id/name/bytes/sha256. Returned witnesses retain
    BOTH actual remote and canonical local names; never relabel raw API evidence.
    Metadata acceptance alone is not full remote payload verification.
    """
    plan = validate_plan(alias_raw, expected_alias_sha, index_raw, expected_index_sha)
    require(before == after and isinstance(before, list) and len(before) == len(plan['assets']), 'Exact stable selected metadata set required')
    table = {}; ids = set()
    for row in before:
        require(set(row) == {'id', 'name', 'bytes', 'sha256'} and type(row['id']) is int and row['id'] > 0
                and row['name'] not in table and row['id'] not in ids, 'Unique actual asset names/IDs required')
        table[row['name']] = row; ids.add(row['id'])
    require(set(table) == {row['remote_name'] for row in plan['assets']}, 'Missing/extra selected remote assets')
    bound = []
    for row in plan['assets']:
        actual = table[row['remote_name']]
        require(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], 'Remote asset digest/size differs')
        bound.append({**row, 'remote_asset_id': actual['id']})
    return bound


def verify_stream(stream, row, admission):
    """Verify fresh downloaded bytes while copying is owned by the caller.

    Each read is bounded; admission must enforce deadline/resources/ownership.
    Does not write files or mint a remote-recovery/eviction receipt.
    """
    require(callable(admission) and set(row) == {'local_name', 'remote_name', 'bytes', 'sha256', 'kind', 'remote_asset_id'}
            and type(row['bytes']) is int and 0 < row['bytes'] <= LIMIT and sha(row['sha256'])
            and type(row['remote_asset_id']) is int and row['remote_asset_id'] > 0
            and row['kind'] in {'PAYLOAD', 'ORIGINAL_LF_SIDECAR'}, 'Exact bound alias row and owner guard required')
    total = 0; hasher = hashlib.sha256()
    while True:
        admission(); block = stream.read(BLOCK)
        require(isinstance(block, bytes) and len(block) <= BLOCK, 'Bounded binary source required')
        if not block:
            break
        total += len(block); require(total <= row['bytes'], 'Downloaded asset exceeds exact size')
        hasher.update(block)
    admission()
    require(total == row['bytes'] and hasher.hexdigest() == row['sha256'], 'Full downloaded asset size/SHA differs')
    return {'remote_asset_id': row['remote_asset_id'], 'remote_name': row['remote_name'],
            'local_name': row['local_name'], 'bytes': total, 'sha256': hasher.hexdigest(),
            'full_stream_verified': True, 'fresh_download_proven_by_this_function': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--index'); parser.add_argument('--index-sha256')
    parser.add_argument('--snapshot'); parser.add_argument('--output')
    args = parser.parse_args()
    if not args.plan:
        print(json.dumps({'state': 'NO_OP_USE_PLAN_FOR_PURE_MAPPING_ONLY'})); return 0
    require(all([args.index, args.index_sha256, args.snapshot, args.output]), 'All exact plan inputs required')
    source = Path(args.index); output = Path(args.output); work = Path(__file__).resolve().parent
    require(source.resolve() == source and source.is_relative_to(work) and not source.is_symlink()
            and source.is_file() and source.stat().st_size < 5*1024**2, 'Bounded current-work exact index required')
    require(output.parent == work and not output.exists() and not output.is_symlink(), 'Fresh direct work map required')
    value = make_plan(source.read_bytes(), args.index_sha256, args.snapshot)
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'state': 'PASS_ALIAS_MAPPING_ONLY', 'output': str(output), 'sha256': digest(output.read_bytes())}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
