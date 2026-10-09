"""Build the bounded metadata-only batch03 leaf proposal. Never deletes or contacts GitHub."""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse, hashlib, json, re, zipfile

HERE = Path(__file__).resolve().parent
OLD = PureWindowsPath(r'C:\Users\wheel\Documents\Codex\2026-10-08\lab-rm-phylogenomics-196')
SCOPES = ('data', '.work/review2', '.work/stage02_validated', '.work/source_locus_inputs_v1',
          '.work/stage03_markers_v1', '.work/stage04a_windows_alignments_v1', '.work/stage04_phylogeny_v2')
ARCHIVE_SHA = 'f6d7e0558953d2542ca085552a6cd8219a4ec1acde4072ce6f03d12dd953178e'
ASSESS_SHA = '13d89bbfdd2b768501426493c8de0eac8a4076ed1aca789ab87ea1df759b7f1e'
BIND_SHA = '6e47a982ffb8eee6135f80d6e64089cf60399232918474909c032938d8976ae2'
MAPPING_SHA = 'df770f9e49e869c64f61db5720030aceff3b3282d53ee964aae02d228d7c3f64'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def validate_row(row):
    rel = row['relative_path']; p = PurePosixPath(rel)
    if p.is_absolute() or str(p) != rel or '\\' in rel or ':' in rel or any(
            x in ('', '.', '..') or x.endswith((' ', '.')) for x in rel.split('/')):
        raise ValueError('Noncanonical path')
    if any(x.casefold() in ('.git', '.tools', '.private_run', '.codex') for x in p.parts):
        raise ValueError('Protected component')
    if p.name.casefold().endswith(('.lock', '.guard')):
        raise ValueError('Protected lock/guard')
    scope = row['scope']
    if scope not in SCOPES or not rel.startswith(scope + '/'):
        raise ValueError('Scope mismatch')
    expected = str(OLD.joinpath(*p.parts))
    if row['path'] != expected or row['link_count'] != 1:
        raise ValueError('Alias or hard link')
    if not isinstance(row['bytes'], int) or row['bytes'] < 0 or not re.fullmatch('[a-f0-9]{64}', row['sha256']):
        raise ValueError('Invalid content pin')
    r = row['recovery']
    if r['member_bytes'] != row['bytes'] or r['member_sha256'] != row['sha256']:
        raise ValueError('Restoration mismatch')
    if not re.fullmatch('[a-f0-9]{64}', r['remote_zip_sha256']) or r['remote_zip_bytes'] <= 0:
        raise ValueError('Invalid whole-asset pin')
    url = 'https://github.com/serg-alexv/lab-rm-phylogenomics-196/releases/download/'
    if not r['remote_asset_url'].startswith(url + r['release_tag'] + '/'):
        raise ValueError('Wrong remote recovery origin')
    return expected.casefold()

def build(recovery_path):
    recovery_path = Path(recovery_path).resolve()
    recovery = json.loads(recovery_path.read_bytes())
    if recovery.get('schema') != 'MASTER_BATCH03_MAPPING_INDEPENDENT_READBACK_V1' or recovery.get('state') != 'PASS_FRESH_REMOTE_MAPPING19_MEMBERS_47648_ROWS_219_HOLDS_619_PRESERVED' \
            or recovery.get('archive_sha256') != ARCHIVE_SHA or recovery.get('archive_bytes') != 6921443:
        raise ValueError('Actual independent remote recovery PASS required')
    archive = HERE / 'master_batch03_mapping01/master_batch03_scientific_cache_mapping01.zip'
    if archive.is_symlink() or sha(archive) != ARCHIVE_SHA: raise ValueError('Archive changed')
    assets = {}; seen = set(); count = size = kept_count = kept_size = 0
    with zipfile.ZipFile(archive) as z:
        if len(z.namelist()) != len(set(z.namelist())): raise ValueError('Duplicate ZIP entries')
        assess_bytes = z.read('control/conservative_leaf_assessment.json')
        bind_bytes = z.read('control/source_binding.json')
        if hashlib.sha256(assess_bytes).hexdigest() != ASSESS_SHA or hashlib.sha256(bind_bytes).hexdigest() != BIND_SHA:
            raise ValueError('Control changed')
        assess = json.loads(assess_bytes); binding = json.loads(bind_bytes)
        holds = {x['path'].casefold() for x in assess['files_preserved']}
        if len(holds) != 219: raise ValueError('Wrong holds')
        h = hashlib.sha256()
        with z.open('mapping/batch03/file_allowlist.jsonl') as stream:
            for line in stream:
                h.update(line); row = json.loads(line); key = validate_row(row)
                if key in seen: raise ValueError('Duplicate target')
                seen.add(key); count += 1; size += row['bytes']
                if key in holds: kept_count += 1; kept_size += row['bytes']; continue
                r = row['recovery']; asset_id = str(r['remote_asset_id'])
                a = {'id': r['remote_asset_id'], 'name': r['remote_asset_url'].rsplit('/', 1)[1],
                     'bytes': r['remote_zip_bytes'], 'sha256': r['remote_zip_sha256'],
                     'release_tag': r['release_tag'], 'url': r['remote_asset_url']}
                if assets.setdefault(asset_id, a) != a: raise ValueError('Conflicting remote asset')
        if h.hexdigest() != MAPPING_SHA or (count, size, kept_count, kept_size) != (47648, 6568632074, 219, 2729256):
            raise ValueError('Wrong exact proposal accounting')
        members = []
        for info in z.infolist():
            # Archive SHA is fixed and this read proves all members/CRC without deserializing the mapping.
            h = hashlib.sha256()
            with z.open(info) as f:
                for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
            members.append({'member': info.filename, 'bytes': info.file_size, 'sha256': h.hexdigest()})
    script = HERE / 'Invoke-MasterBatch03LeafPurge.ps1'
    p = {'schema': 'MASTER_BATCH03_STREAMING_LEAF_PURGE_PROPOSAL_V1', 'state': 'BUILD_ONLY_NO_DELETE',
         'host': 'WD', 'old_root': str(OLD), 'allowed_scopes': list(SCOPES),
         'script_sha256': sha(script), 'builder_sha256': sha(Path(__file__)),
         'archive': {'path': str(archive), 'sha256': ARCHIVE_SHA, 'bytes': archive.stat().st_size, 'members': members},
         'mapping_member': 'mapping/batch03/file_allowlist.jsonl', 'mapping_sha256': MAPPING_SHA,
         'assessment_sha256': ASSESS_SHA, 'source_binding_sha256': BIND_SHA,
         'remote_plan_path': 'reports/master_run/20261009/cleanup/batch03_purge01/proposed.json',
         'recovery_receipt': {'path': str(recovery_path), 'sha256': sha(recovery_path),
                              'source_commit': recovery['source_commit'], 'tag': recovery['tag']},
         'assets': list(assets.values()), 'mapped_files': count, 'mapped_bytes': size,
         'held_files': kept_count, 'held_bytes': kept_size, 'unmatched_preserved': 619,
         'candidate_files': count-kept_count, 'candidate_bytes': size-kept_size,
         'owners': [{'pid': 4768, 'creation_filetime': '134360369876207076'},
                    {'pid': 27048, 'creation_filetime': '134360369803845506'}],
         'maximum_runtime_seconds': 3600, 'recursive_deletes': 0,
         'required_recovery': 'Independent actual remote mapping-archive download/member readback PASS; receipt hash and actual proposal commit required at invocation',
         'leaf_race': 'FileShare.None hash handle closes immediately before literal Remove-Item. Retained ancestor handles prevent parent replacement, but leaf replacement interval is not atomic; unexpected drift/contention stops and preserves remainder.'}
    out = HERE / 'master_batch03_leaf_purge_proposed.json'
    with out.open('x', encoding='utf-8', newline='\n') as f: json.dump(p, f, indent=2, sort_keys=True); f.write('\n')
    print(json.dumps({'proposal': str(out), 'sha256': sha(out), 'candidates': p['candidate_files'], 'bytes': p['candidate_bytes'], 'delete': 'NOT_RUN'}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recovery-receipt', required=True)
    build(parser.parse_args().recovery_receipt)
